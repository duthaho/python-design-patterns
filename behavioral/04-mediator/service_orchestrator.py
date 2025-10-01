import heapq
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class EventPriority(Enum):
    """Priority levels for event processing - higher value = higher priority"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SagaStatus(Enum):
    """States in the saga lifecycle"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class Event:
    """
    Represents an event in the system
    Uses __lt__ for priority queue ordering (higher priority value = processed first)
    """

    event_type: str
    data: dict
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other: "Event") -> bool:
        """Priority queue comparison - higher priority value comes first"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        # If same priority, older events first (FIFO)
        return self.timestamp < other.timestamp


@dataclass
class SagaState:
    """
    Tracks the state of a distributed transaction (saga)
    Maintains compensation steps for rollback capability
    """

    correlation_id: str
    status: SagaStatus
    steps_completed: list[str] = field(default_factory=list)
    compensation_steps: list[tuple[Callable, dict]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)

    def add_step(
        self,
        step_name: str,
        compensation_fn: Callable = None,
        compensation_args: dict = None,
    ):
        """Record a completed step with optional compensation"""
        self.steps_completed.append(step_name)
        if compensation_fn:
            self.compensation_steps.append((compensation_fn, compensation_args or {}))


# ============================================================================
# SERVICE ORCHESTRATOR (MEDIATOR) - THE HEART OF THE PATTERN
# ============================================================================


class ServiceOrchestrator:
    """
    Advanced mediator implementing:
    - Priority-based event queue (critical events jump the queue)
    - Saga pattern for distributed transactions with compensation
    - Circuit breaker to prevent cascade failures
    - Exponential backoff retry logic
    - Event sourcing for audit trail

    ARCHITECTURAL DECISION: All service communication goes through this mediator.
    Services never call each other directly, ensuring loose coupling.
    """

    def __init__(self):
        self.services: dict[str, "MicroService"] = {}
        self.event_queue: list[Event] = []  # Used as heap for priority queue
        self.event_history: list[Event] = []
        self.sagas: dict[str, SagaState] = {}

        # Circuit breaker state per service
        self.circuit_breaker: dict[str, dict] = {}
        self.circuit_breaker_threshold = 3  # Failures before opening circuit
        self.circuit_breaker_timeout = 10  # Seconds before attempting retry

        # Metrics tracking
        self.metrics = {
            "events_processed": 0,
            "sagas_completed": 0,
            "sagas_failed": 0,
            "compensations_triggered": 0,
        }

    def register_service(self, service: "MicroService") -> None:
        """
        Register a microservice with the orchestrator
        Initializes circuit breaker state for the service
        """
        self.services[service.service_name] = service
        self.circuit_breaker[service.service_name] = {
            "failures": 0,
            "last_failure": None,
            "is_open": False,
        }
        print(f"[Orchestrator] ✓ Registered service: {service.service_name}")

    def publish_event(self, event: Event) -> None:
        """
        Publish an event to the priority queue
        ARCHITECTURE: Uses heap for O(log n) insertion with automatic priority ordering
        Critical events (VIP orders) are processed before normal events
        """
        heapq.heappush(self.event_queue, event)
        self.event_history.append(event)

        priority_indicator = (
            "🔴"
            if event.priority == EventPriority.CRITICAL
            else "🟡" if event.priority == EventPriority.HIGH else "🟢"
        )
        print(
            f"[Orchestrator] {priority_indicator} Event queued: {event.event_type} (Priority: {event.priority.name}, Queue size: {len(self.event_queue)})"
        )

    def process_events(self) -> None:
        """
        Process all events in priority order
        Continues until queue is empty or max iterations reached (prevent infinite loops)
        """
        max_iterations = 1000  # Safety limit
        iterations = 0

        while self.event_queue and iterations < max_iterations:
            event = heapq.heappop(self.event_queue)
            iterations += 1
            self.metrics["events_processed"] += 1

            print(
                f"\n[Orchestrator] 🔄 Processing: {event.event_type} (Retry: {event.retry_count})"
            )

            try:
                self._route_event(event)
            except Exception as e:
                print(f"[Orchestrator] ❌ Error processing event: {e}")
                self._handle_service_failure("Orchestrator", event, e)

    def _route_event(self, event: Event) -> None:
        """
        Central routing logic - the orchestrator's "brain"
        Routes events to appropriate handlers based on event type

        ARCHITECTURE: This is where the saga workflow is defined.
        Each event type triggers the next step in the distributed transaction.
        """
        event_type = event.event_type

        # Saga workflow routing
        routing_map = {
            "ORDER_CREATED": self._handle_order_created,
            "INVENTORY_RESERVED": self._handle_inventory_reserved,
            "INVENTORY_FAILED": self._handle_inventory_failed,
            "PAYMENT_COMPLETED": self._handle_payment_completed,
            "PAYMENT_FAILED": self._handle_payment_failed,
            "SHIPPING_ARRANGED": self._handle_shipping_arranged,
            "SHIPPING_FAILED": self._handle_shipping_failed,
            "ORDER_COMPLETED": self._handle_order_completed,
        }

        handler = routing_map.get(event_type)
        if handler:
            handler(event)
        else:
            print(f"[Orchestrator] ⚠️ No handler for event type: {event_type}")

    def _handle_order_created(self, event: Event) -> None:
        """
        Step 1 of saga: Order created, reserve inventory

        SAGA PATTERN: Initialize saga state and start the distributed transaction.
        Each step records a compensation function for potential rollback.
        """
        order_id = event.data["order_id"]
        items = event.data["items"]

        # Initialize saga
        saga = SagaState(
            correlation_id=event.correlation_id,
            status=SagaStatus.IN_PROGRESS,
            data=event.data,
        )
        self.sagas[event.correlation_id] = saga
        saga.add_step("ORDER_CREATED")

        print(f"[Orchestrator] 📋 Starting saga for order {order_id}")

        # Call inventory service through circuit breaker
        inventory_service = self.services.get("InventoryService")
        if not inventory_service:
            print(f"[Orchestrator] ❌ InventoryService not available")
            self._trigger_compensation(event.correlation_id, "Service unavailable")
            return

        if not self._check_circuit_breaker("InventoryService"):
            print(f"[Orchestrator] 🔴 Circuit breaker OPEN for InventoryService")
            self._trigger_compensation(event.correlation_id, "Circuit breaker open")
            return

        try:
            success = inventory_service.reserve_inventory(
                order_id, items, event.correlation_id
            )
            if success:
                # Record compensation step
                saga.add_step(
                    "INVENTORY_RESERVED",
                    compensation_fn=inventory_service.rollback_reservation,
                    compensation_args={"order_id": order_id},
                )
                self._reset_circuit_breaker("InventoryService")
            # Note: If failed, service will publish INVENTORY_FAILED event
        except Exception as e:
            self._handle_service_failure("InventoryService", event, e)

    def _handle_inventory_reserved(self, event: Event) -> None:
        """
        Step 2 of saga: Inventory reserved, process payment
        """
        order_id = event.data["order_id"]

        saga = self.sagas.get(event.correlation_id)
        if not saga:
            print(
                f"[Orchestrator] ⚠️ No saga found for correlation_id: {event.correlation_id}"
            )
            return

        # Calculate total amount (simplified)
        items = event.data["items"]
        amount = sum(item.get("quantity", 1) * 99.99 for item in items)  # Mock pricing

        payment_service = self.services.get("PaymentService")
        if not payment_service or not self._check_circuit_breaker("PaymentService"):
            self._trigger_compensation(
                event.correlation_id, "Payment service unavailable"
            )
            return

        try:
            success = payment_service.process_payment(
                order_id, amount, event.correlation_id
            )
            if success:
                saga.add_step(
                    "PAYMENT_COMPLETED",
                    compensation_fn=payment_service.refund_payment,
                    compensation_args={"order_id": order_id},
                )
                self._reset_circuit_breaker("PaymentService")
        except Exception as e:
            self._handle_service_failure("PaymentService", event, e)

    def _handle_inventory_failed(self, event: Event) -> None:
        """Handle inventory reservation failure"""
        print(
            f"[Orchestrator] ❌ Inventory reservation failed for order {event.data['order_id']}"
        )
        self._trigger_compensation(event.correlation_id, "Inventory unavailable")

    def _handle_payment_completed(self, event: Event) -> None:
        """
        Step 3 of saga: Payment completed, arrange shipping
        """
        order_id = event.data["order_id"]

        saga = self.sagas.get(event.correlation_id)
        if not saga:
            return

        shipping_service = self.services.get("ShippingService")
        if not shipping_service or not self._check_circuit_breaker("ShippingService"):
            self._trigger_compensation(
                event.correlation_id, "Shipping service unavailable"
            )
            return

        try:
            items = saga.data.get("items", [])
            success = shipping_service.arrange_shipping(
                order_id, items, event.correlation_id
            )
            if success:
                saga.add_step(
                    "SHIPPING_ARRANGED",
                    compensation_fn=shipping_service.cancel_shipment,
                    compensation_args={"order_id": order_id},
                )
                self._reset_circuit_breaker("ShippingService")
        except Exception as e:
            self._handle_service_failure("ShippingService", event, e)

    def _handle_payment_failed(self, event: Event) -> None:
        """Handle payment failure"""
        print(f"[Orchestrator] ❌ Payment failed for order {event.data['order_id']}")
        self._trigger_compensation(event.correlation_id, "Payment declined")

    def _handle_shipping_arranged(self, event: Event) -> None:
        """
        Final step of saga: Shipping arranged, send completion notification
        """
        order_id = event.data["order_id"]

        saga = self.sagas.get(event.correlation_id)
        if not saga:
            return

        # Notify customer
        notification_service = self.services.get("NotificationService")
        if notification_service:
            customer_id = saga.data.get("customer_id", "UNKNOWN")
            notification_service.send_notification(
                customer_id,
                f"Your order {order_id} has been shipped! Tracking: {event.data.get('tracking', 'N/A')}",
                "SUCCESS",
            )

        # Complete saga
        saga.status = SagaStatus.SUCCESS
        saga.add_step("ORDER_COMPLETED")
        self.metrics["sagas_completed"] += 1

        print(f"[Orchestrator] ✅ Saga completed successfully for order {order_id}")

        # Publish final event
        self.publish_event(
            Event(
                event_type="ORDER_COMPLETED",
                data={"order_id": order_id},
                correlation_id=event.correlation_id,
                priority=event.priority,
            )
        )

    def _handle_shipping_failed(self, event: Event) -> None:
        """Handle shipping failure"""
        print(f"[Orchestrator] ❌ Shipping failed for order {event.data['order_id']}")
        self._trigger_compensation(event.correlation_id, "Shipping unavailable")

    def _handle_order_completed(self, event: Event) -> None:
        """Final handler - order fully completed"""
        order_id = event.data["order_id"]
        print(f"[Orchestrator] 🎉 Order {order_id} fully completed!")

    def _handle_service_failure(
        self, service_name: str, event: Event, error: Exception
    ) -> None:
        """
        Handle service failure with exponential backoff retry

        RESILIENCE PATTERN: Implements retry with exponential backoff
        - Retry 0: immediate
        - Retry 1: 1 second
        - Retry 2: 2 seconds
        - Retry 3: 4 seconds (then give up)
        """
        print(f"[Orchestrator] ⚠️ Service failure: {service_name} - {error}")

        # Update circuit breaker
        breaker = self.circuit_breaker.get(service_name)
        if breaker:
            breaker["failures"] += 1
            breaker["last_failure"] = datetime.now()

            if breaker["failures"] >= self.circuit_breaker_threshold:
                breaker["is_open"] = True
                print(f"[Orchestrator] 🔴 Circuit breaker OPENED for {service_name}")

        # Retry logic
        if event.retry_count < event.max_retries:
            event.retry_count += 1
            delay = 2 ** (event.retry_count - 1)  # Exponential backoff: 1s, 2s, 4s

            print(
                f"[Orchestrator] 🔄 Scheduling retry {event.retry_count}/{event.max_retries} in {delay}s"
            )

            # In production, would use actual delay. For demo, just re-queue
            # time.sleep(delay)  # Commented out for faster demo
            heapq.heappush(self.event_queue, event)
        else:
            print(f"[Orchestrator] ❌ Max retries exceeded for {event.event_type}")
            self._trigger_compensation(
                event.correlation_id, f"Max retries exceeded: {error}"
            )

    def _trigger_compensation(self, correlation_id: str, reason: str) -> None:
        """
        Execute compensating transactions (saga rollback)

        SAGA PATTERN: When a step fails, all previous steps must be undone
        in reverse order to maintain consistency across services.

        This is the "C" in SAGA - Compensating transactions.
        """
        saga = self.sagas.get(correlation_id)
        if not saga:
            print(f"[Orchestrator] ⚠️ No saga found for compensation: {correlation_id}")
            return

        if saga.status in [
            SagaStatus.COMPENSATING,
            SagaStatus.COMPENSATED,
            SagaStatus.FAILED,
        ]:
            print(f"[Orchestrator] ⚠️ Saga already in terminal state: {saga.status}")
            return

        print(f"\n[Orchestrator] 🔄 INITIATING COMPENSATION for {correlation_id}")
        print(f"[Orchestrator] Reason: {reason}")
        print(f"[Orchestrator] Steps to compensate: {len(saga.compensation_steps)}")

        saga.status = SagaStatus.COMPENSATING
        self.metrics["compensations_triggered"] += 1

        # Execute compensations in REVERSE order (undo last operations first)
        for i, (compensation_fn, args) in enumerate(
            reversed(saga.compensation_steps), 1
        ):
            try:
                print(
                    f"[Orchestrator] 🔄 Compensation step {i}/{len(saga.compensation_steps)}"
                )
                compensation_fn(**args)
            except Exception as e:
                print(f"[Orchestrator] ❌ Compensation failed: {e}")
                # In production, would need sophisticated error handling here

        saga.status = SagaStatus.COMPENSATED
        self.metrics["sagas_failed"] += 1

        # Notify customer of failure
        notification_service = self.services.get("NotificationService")
        if notification_service:
            customer_id = saga.data.get("customer_id", "UNKNOWN")
            order_id = saga.data.get("order_id", "UNKNOWN")
            notification_service.send_notification(
                customer_id,
                f"Order {order_id} could not be completed: {reason}",
                "FAILURE",
            )

        print(f"[Orchestrator] ✅ Compensation completed for {correlation_id}\n")

    def _check_circuit_breaker(self, service_name: str) -> bool:
        """
        Circuit breaker pattern implementation

        RESILIENCE PATTERN: Prevents cascading failures by "opening the circuit"
        when a service is unhealthy. After a timeout, allows retry attempts.

        States:
        - CLOSED: Normal operation
        - OPEN: Service is failing, block all requests
        - HALF-OPEN: Timeout passed, allow test request
        """
        breaker = self.circuit_breaker.get(service_name)
        if not breaker:
            return True

        if breaker["is_open"]:
            # Check if timeout has passed (half-open state)
            if breaker["last_failure"]:
                elapsed = (datetime.now() - breaker["last_failure"]).total_seconds()
                if elapsed > self.circuit_breaker_timeout:
                    print(
                        f"[Orchestrator] 🟡 Circuit breaker HALF-OPEN for {service_name} (test request)"
                    )
                    # Don't close yet, but allow one attempt
                    return True
                else:
                    remaining = self.circuit_breaker_timeout - elapsed
                    print(
                        f"[Orchestrator] 🔴 Circuit breaker OPEN for {service_name} ({remaining:.1f}s remaining)"
                    )
            return False

        return True

    def _reset_circuit_breaker(self, service_name: str) -> None:
        """Reset circuit breaker after successful operation"""
        breaker = self.circuit_breaker.get(service_name)
        if breaker:
            if breaker["failures"] > 0:
                print(f"[Orchestrator] 🟢 Circuit breaker CLOSED for {service_name}")
            breaker["failures"] = 0
            breaker["is_open"] = False
            breaker["last_failure"] = None

    def print_event_history(self) -> None:
        """Print formatted event history for debugging"""
        print("\n" + "=" * 70)
        print("EVENT HISTORY")
        print("=" * 70)
        for i, event in enumerate(self.event_history, 1):
            time_str = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
            priority_symbol = {
                EventPriority.CRITICAL: "🔴",
                EventPriority.HIGH: "🟡",
                EventPriority.NORMAL: "🟢",
                EventPriority.LOW: "⚪",
            }.get(event.priority, "🟢")

            print(
                f"  {i:2d}. [{time_str}] {priority_symbol} {event.event_type:25s} | {event.data}"
            )

    def print_metrics(self) -> None:
        """Print orchestrator metrics"""
        print("\n" + "=" * 70)
        print("ORCHESTRATOR METRICS")
        print("=" * 70)
        print(f"  Events Processed:      {self.metrics['events_processed']}")
        print(f"  Sagas Completed:       {self.metrics['sagas_completed']} ✅")
        print(f"  Sagas Failed:          {self.metrics['sagas_failed']} ❌")
        print(f"  Compensations:         {self.metrics['compensations_triggered']} 🔄")
        if self.metrics["events_processed"] > 0:
            success_rate = (
                self.metrics["sagas_completed"]
                / (self.metrics["sagas_completed"] + self.metrics["sagas_failed"])
            ) * 100
            print(f"  Success Rate:          {success_rate:.1f}%")

    def get_saga_status(self, correlation_id: str) -> Optional[SagaStatus]:
        """Query saga status"""
        saga = self.sagas.get(correlation_id)
        return saga.status if saga else None


# ============================================================================
# ABSTRACT MICROSERVICE
# ============================================================================


class MicroService(ABC):
    """
    Abstract base class for all microservices

    KEY PRINCIPLE: Services communicate ONLY through the orchestrator.
    No direct service-to-service calls allowed. This ensures:
    - Loose coupling
    - Centralized coordination logic
    - Easy monitoring and debugging
    - Simplified testing
    """

    def __init__(
        self,
        service_name: str,
        orchestrator: ServiceOrchestrator,
        failure_rate: float = 0.0,
    ):
        self.service_name = service_name
        self.orchestrator = orchestrator
        self.status = ServiceStatus.HEALTHY
        self.failure_rate = failure_rate  # For testing failure scenarios
        self.orchestrator.register_service(self)

    def _simulate_failure(self) -> None:
        """Randomly simulate failures for resilience testing"""
        if random.random() < self.failure_rate:
            raise Exception(f"{self.service_name} simulated failure")

    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """Health check endpoint"""
        pass

    def publish_event(
        self,
        event_type: str,
        data: dict,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: str = None,
    ) -> None:
        """Publish an event through the orchestrator"""
        event = Event(
            event_type=event_type,
            data=data,
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
        self.orchestrator.publish_event(event)


# ============================================================================
# CONCRETE MICROSERVICES
# ============================================================================


class OrderService(MicroService):
    """Manages order lifecycle"""

    def __init__(self, orchestrator: ServiceOrchestrator):
        super().__init__("OrderService", orchestrator)
        self.orders: dict[str, dict] = {}

    def create_order(
        self, customer_id: str, items: list[dict], is_vip: bool = False
    ) -> str:
        """
        Create a new order and initiate saga workflow
        VIP orders get CRITICAL priority for faster processing
        """
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": items,
            "is_vip": is_vip,
            "status": "PENDING",
            "created_at": datetime.now(),
        }
        self.orders[order_id] = order

        priority = EventPriority.CRITICAL if is_vip else EventPriority.NORMAL
        correlation_id = str(uuid.uuid4())

        vip_badge = "👑 VIP" if is_vip else ""
        print(
            f"\n[OrderService] 📝 Order {order_id} created for customer {customer_id} {vip_badge}"
        )

        self.publish_event(
            "ORDER_CREATED",
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "items": items,
                "is_vip": is_vip,
            },
            priority=priority,
            correlation_id=correlation_id,
        )

        return order_id

    def get_status(self) -> ServiceStatus:
        return self.status


class InventoryService(MicroService):
    """Manages product inventory with reservation/rollback capability"""

    def __init__(self, orchestrator: ServiceOrchestrator, failure_rate: float = 0.0):
        super().__init__("InventoryService", orchestrator, failure_rate)
        self.inventory: dict[str, int] = {
            "Widget": 100,
            "Gadget": 50,
            "Doohickey": 75,
            "Thingamajig": 25,
        }
        self.reservations: dict[str, list[dict]] = {}

    def reserve_inventory(
        self, order_id: str, items: list[dict], correlation_id: str
    ) -> bool:
        """
        Reserve inventory for an order
        Returns True if successful, publishes event either way
        """
        self._simulate_failure()

        print(f"[InventoryService] 📦 Checking inventory for order {order_id}")

        # Check availability
        for item in items:
            product = item["product"]
            quantity = item["quantity"]
            available = self.inventory.get(product, 0)

            if available < quantity:
                print(
                    f"[InventoryService] ❌ Insufficient stock: {product} (need {quantity}, have {available})"
                )
                self.publish_event(
                    "INVENTORY_FAILED",
                    {
                        "order_id": order_id,
                        "reason": f"Insufficient stock for {product}",
                    },
                    correlation_id=correlation_id,
                )
                return False

        # Reserve items
        for item in items:
            self.inventory[item["product"]] -= item["quantity"]
            print(
                f"[InventoryService]   ✓ Reserved {item['quantity']}x {item['product']}"
            )

        self.reservations[order_id] = items

        self.publish_event(
            "INVENTORY_RESERVED",
            {"order_id": order_id, "items": items},
            correlation_id=correlation_id,
        )

        return True

    def rollback_reservation(self, order_id: str) -> None:
        """
        Compensating transaction: Restore reserved inventory
        This is called during saga compensation
        """
        if order_id not in self.reservations:
            print(f"[InventoryService] ⚠️ No reservation found for {order_id}")
            return

        items = self.reservations[order_id]
        for item in items:
            self.inventory[item["product"]] += item["quantity"]
            print(
                f"[InventoryService] 🔄 Restored {item['quantity']}x {item['product']}"
            )

        del self.reservations[order_id]
        print(f"[InventoryService] ✅ Rollback completed for {order_id}")

    def get_status(self) -> ServiceStatus:
        return self.status


class PaymentService(MicroService):
    """Processes payments with refund capability"""

    def __init__(self, orchestrator: ServiceOrchestrator, failure_rate: float = 0.0):
        super().__init__("PaymentService", orchestrator, failure_rate)
        self.transactions: dict[str, dict] = {}

    def process_payment(
        self, order_id: str, amount: float, correlation_id: str
    ) -> bool:
        """Process payment for an order"""
        self._simulate_failure()

        print(
            f"[PaymentService] 💳 Processing payment ${amount:.2f} for order {order_id}"
        )

        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

        # Simulate payment processing delay
        time.sleep(0.05)

        self.transactions[order_id] = {
            "transaction_id": transaction_id,
            "amount": amount,
            "status": "COMPLETED",
            "timestamp": datetime.now(),
        }

        print(f"[PaymentService] ✅ Payment completed: {transaction_id}")

        self.publish_event(
            "PAYMENT_COMPLETED",
            {"order_id": order_id, "transaction_id": transaction_id, "amount": amount},
            correlation_id=correlation_id,
        )

        return True

    def refund_payment(self, order_id: str) -> None:
        """
        Compensating transaction: Refund payment
        Called during saga compensation
        """
        if order_id not in self.transactions:
            print(f"[PaymentService] ⚠️ No transaction found for {order_id}")
            return

        txn = self.transactions[order_id]
        txn["status"] = "REFUNDED"

        print(
            f"[PaymentService] 💰 Refunded ${txn['amount']:.2f} for order {order_id} (TXN: {txn['transaction_id']})"
        )

    def get_status(self) -> ServiceStatus:
        return self.status


class ShippingService(MicroService):
    """Manages shipping and logistics"""

    def __init__(self, orchestrator: ServiceOrchestrator, failure_rate: float = 0.0):
        super().__init__("ShippingService", orchestrator, failure_rate)
        self.shipments: dict[str, dict] = {}

    def arrange_shipping(
        self, order_id: str, items: list[dict], correlation_id: str
    ) -> bool:
        """Arrange shipping for an order"""
        self._simulate_failure()

        print(f"[ShippingService] 📮 Arranging shipping for order {order_id}")

        tracking_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        self.shipments[order_id] = {
            "tracking_number": tracking_number,
            "status": "PENDING",
            "items": items,
            "created_at": datetime.now(),
        }

        print(f"[ShippingService] ✅ Shipping arranged: {tracking_number}")

        self.publish_event(
            "SHIPPING_ARRANGED",
            {"order_id": order_id, "tracking": tracking_number},
            correlation_id=correlation_id,
        )

        return True

    def cancel_shipment(self, order_id: str) -> None:
        """
        Compensating transaction: Cancel shipment
        Called during saga compensation
        """
        if order_id not in self.shipments:
            print(f"[ShippingService] ⚠️ No shipment found for {order_id}")
            return

        shipment = self.shipments[order_id]
        shipment["status"] = "CANCELLED"

        print(
            f"[ShippingService] 📦 Cancelled shipment for {order_id} (Tracking: {shipment['tracking_number']})"
        )

    def get_status(self) -> ServiceStatus:
        return self.status


class NotificationService(MicroService):
    """Sends notifications to customers"""

    def __init__(self, orchestrator: ServiceOrchestrator):
        super().__init__("NotificationService", orchestrator)
        self.notifications_sent: list[dict] = []

    def send_notification(
        self, customer_id: str, message: str, notification_type: str = "INFO"
    ) -> None:
        """
        Send notification to customer
        In production: would send email/SMS/push notification
        """
        notification = {
            "customer_id": customer_id,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now(),
        }
        self.notifications_sent.append(notification)

        type_icon = {"SUCCESS": "✅", "FAILURE": "❌", "INFO": "ℹ️", "WARNING": "⚠️"}.get(
            notification_type, "ℹ️"
        )

        print(
            f"[NotificationService] {type_icon} Notification sent to {customer_id}: {message}"
        )

    def get_status(self) -> ServiceStatus:
        return self.status


# ============================================================================
# TEST SCENARIOS
# ============================================================================


def run_successful_order_scenario():
    """
    Test Case 1: Successful order processing (Happy Path)

    Flow: Order → Inventory → Payment → Shipping → Notification
    Expected: All steps complete successfully
    """
    print("\n" + "=" * 70)
    print("SCENARIO 1: SUCCESSFUL ORDER (HAPPY PATH)")
    print("=" * 70)

    orchestrator = ServiceOrchestrator()

    # Initialize services
    order_service = OrderService(orchestrator)
    inventory_service = InventoryService(orchestrator, failure_rate=0.0)
    payment_service = PaymentService(orchestrator, failure_rate=0.0)
    shipping_service = ShippingService(orchestrator, failure_rate=0.0)
    notification_service = NotificationService(orchestrator)

    # Create order
    order_id = order_service.create_order(
        customer_id="CUST-12345",
        items=[
            {"product": "Widget", "quantity": 2},
            {"product": "Gadget", "quantity": 1},
        ],
        is_vip=False,
    )

    # Process all events
    orchestrator.process_events()

    # Show results
    orchestrator.print_event_history()
    orchestrator.print_metrics()

    print("\n✅ Scenario 1 completed successfully!")


def run_payment_failure_scenario():
    """
    Test Case 2: Payment failure with compensation

    Flow: Order → Inventory (✓) → Payment (✗) → COMPENSATION
    Expected: Inventory is rolled back, customer notified
    """
    print("\n" + "=" * 70)
    print("SCENARIO 2: PAYMENT FAILURE WITH ROLLBACK")
    print("=" * 70)

    orchestrator = ServiceOrchestrator()

    # Initialize services with payment service that always fails
    order_service = OrderService(orchestrator)
    inventory_service = InventoryService(orchestrator, failure_rate=0.0)
    payment_service = PaymentService(
        orchestrator, failure_rate=1.0
    )  # 100% failure rate
    shipping_service = ShippingService(orchestrator, failure_rate=0.0)
    notification_service = NotificationService(orchestrator)

    print("\n⚠️  Note: PaymentService configured with 100% failure rate\n")

    # Create order
    order_id = order_service.create_order(
        customer_id="CUST-67890",
        items=[{"product": "Gadget", "quantity": 3}],
        is_vip=False,
    )

    # Process events
    orchestrator.process_events()

    # Show results
    orchestrator.print_event_history()
    orchestrator.print_metrics()

    print("\n✅ Scenario 2 completed - compensation executed!")


def run_vip_order_scenario():
    """
    Test Case 3: VIP order with priority processing

    Flow: Create regular order, then VIP order
    Expected: VIP order is processed first (priority queue)
    """
    print("\n" + "=" * 70)
    print("SCENARIO 3: VIP ORDER PRIORITY PROCESSING")
    print("=" * 70)

    orchestrator = ServiceOrchestrator()

    # Initialize services
    order_service = OrderService(orchestrator)
    inventory_service = InventoryService(orchestrator, failure_rate=0.0)
    payment_service = PaymentService(orchestrator, failure_rate=0.0)
    shipping_service = ShippingService(orchestrator, failure_rate=0.0)
    notification_service = NotificationService(orchestrator)

    print("\n📝 Creating multiple orders to demonstrate priority queue...\n")

    # Create regular order first
    regular_order = order_service.create_order(
        customer_id="CUST-11111",
        items=[{"product": "Widget", "quantity": 1}],
        is_vip=False,
    )

    # Create another regular order
    regular_order2 = order_service.create_order(
        customer_id="CUST-22222",
        items=[{"product": "Doohickey", "quantity": 1}],
        is_vip=False,
    )

    # Create VIP order (should jump to front of queue)
    vip_order = order_service.create_order(
        customer_id="VIP-99999",
        items=[{"product": "Gadget", "quantity": 5}],
        is_vip=True,  # CRITICAL priority
    )

    print(
        "\n🔍 Queue state: VIP order should be processed first despite being created last\n"
    )

    # Process events - VIP should be processed first
    orchestrator.process_events()

    # Show results
    orchestrator.print_event_history()
    orchestrator.print_metrics()

    print("\n✅ Scenario 3 completed - note VIP order processed first!")


def run_circuit_breaker_scenario():
    """
    Test Case 4: Circuit breaker prevents cascade failures

    Flow: Multiple failures trigger circuit breaker
    Expected: After threshold, circuit opens and blocks requests
    """
    print("\n" + "=" * 70)
    print("SCENARIO 4: CIRCUIT BREAKER PATTERN")
    print("=" * 70)

    orchestrator = ServiceOrchestrator()

    # Initialize services with inventory service that always fails
    order_service = OrderService(orchestrator)
    inventory_service = InventoryService(orchestrator, failure_rate=1.0)  # Always fails
    payment_service = PaymentService(orchestrator, failure_rate=0.0)
    shipping_service = ShippingService(orchestrator, failure_rate=0.0)
    notification_service = NotificationService(orchestrator)

    print(f"\n⚠️  Note: InventoryService configured with 100% failure rate")
    print(
        f"Circuit breaker threshold: {orchestrator.circuit_breaker_threshold} failures\n"
    )

    # Create multiple orders to trigger circuit breaker
    for i in range(5):
        order_service.create_order(
            customer_id=f"CUST-{i:05d}",
            items=[{"product": "Widget", "quantity": 1}],
            is_vip=False,
        )

    # Process events - should see circuit breaker open after threshold
    orchestrator.process_events()

    # Show results
    orchestrator.print_event_history()
    orchestrator.print_metrics()

    print("\n✅ Scenario 4 completed - circuit breaker prevented cascade failures!")


def run_mixed_scenario():
    """
    Test Case 5: Mixed scenario with various outcomes

    Realistic scenario with multiple orders, some succeed, some fail
    """
    print("\n" + "=" * 70)
    print("SCENARIO 5: MIXED REALITY - SUCCESS AND FAILURES")
    print("=" * 70)

    orchestrator = ServiceOrchestrator()

    # Initialize services with moderate failure rates
    order_service = OrderService(orchestrator)
    inventory_service = InventoryService(orchestrator, failure_rate=0.1)  # 10% failure
    payment_service = PaymentService(orchestrator, failure_rate=0.2)  # 20% failure
    shipping_service = ShippingService(orchestrator, failure_rate=0.1)  # 10% failure
    notification_service = NotificationService(orchestrator)

    print("\n⚠️  Services configured with realistic failure rates")
    print("Inventory: 10%, Payment: 20%, Shipping: 10%\n")

    # Create mix of regular and VIP orders
    orders = [
        ("CUST-001", [{"product": "Widget", "quantity": 2}], False),
        ("VIP-001", [{"product": "Gadget", "quantity": 1}], True),
        ("CUST-002", [{"product": "Doohickey", "quantity": 3}], False),
        ("VIP-002", [{"product": "Thingamajig", "quantity": 1}], True),
        ("CUST-003", [{"product": "Widget", "quantity": 1}], False),
    ]

    for customer_id, items, is_vip in orders:
        order_service.create_order(customer_id, items, is_vip)

    # Process all events
    orchestrator.process_events()

    # Show results
    orchestrator.print_event_history()
    orchestrator.print_metrics()

    print("\n✅ Scenario 5 completed - realistic mixed outcomes!")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print(
        """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║          MICROSERVICES ORCHESTRATOR - MEDIATOR PATTERN              ║
    ║                                                                      ║
    ║  Demonstrates:                                                       ║
    ║    • Saga Pattern (distributed transactions)                        ║
    ║    • Circuit Breaker (fault tolerance)                              ║
    ║    • Priority Queue (VIP customer handling)                         ║
    ║    • Exponential Backoff (retry logic)                              ║
    ║    • Compensating Transactions (rollback)                           ║
    ║    • Event Sourcing (audit trail)                                   ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    )

    try:
        # Run all test scenarios
        run_successful_order_scenario()

        input("\n\nPress Enter to continue to Scenario 2...")
        run_payment_failure_scenario()

        input("\n\nPress Enter to continue to Scenario 3...")
        run_vip_order_scenario()

        input("\n\nPress Enter to continue to Scenario 4...")
        run_circuit_breaker_scenario()

        input("\n\nPress Enter to continue to Scenario 5...")
        run_mixed_scenario()

        print("\n" + "=" * 70)
        print("🎉 ALL SCENARIOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(
            """
Key Architectural Patterns Demonstrated:

1. MEDIATOR PATTERN
   ✓ Centralized coordination through ServiceOrchestrator
   ✓ Services never communicate directly
   ✓ Loose coupling between components

2. SAGA PATTERN
   ✓ Distributed transaction management
   ✓ Compensating transactions for rollback
   ✓ Eventual consistency across services

3. CIRCUIT BREAKER
   ✓ Prevents cascade failures
   ✓ Automatic recovery attempts
   ✓ Graceful degradation

4. PRIORITY QUEUE
   ✓ VIP customers get preferential treatment
   ✓ Critical events processed first
   ✓ Fair scheduling for normal requests

5. EVENT SOURCING
   ✓ Complete audit trail
   ✓ Replay capability
   ✓ Debugging support

These patterns are essential for building resilient,
scalable microservices architectures in production systems.
        """
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
