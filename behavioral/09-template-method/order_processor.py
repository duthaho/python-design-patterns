import random
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ==================== EXCEPTIONS ====================


class OrderProcessingError(Exception):
    """Base exception for order processing"""

    pass


class TransientError(OrderProcessingError):
    """Temporary error that can be retried"""

    pass


class PermanentError(OrderProcessingError):
    """Permanent error that should not be retried"""

    pass


class CircuitBreakerOpen(OrderProcessingError):
    """Circuit breaker is open, service unavailable"""

    pass


# ==================== ENUMS ====================


class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# ==================== STRATEGY PATTERN ====================


class PaymentStrategy(ABC):
    """Strategy for processing payments"""

    @abstractmethod
    def process(self, amount: float, order_id: str) -> Dict[str, Any]:
        """Process payment and return transaction details"""
        pass

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Refund a completed transaction"""
        pass


class CreditCardPayment(PaymentStrategy):
    def __init__(self, failure_rate: float = 0.2):
        self.failure_rate = failure_rate
        self.processed_transactions = set()

    def process(self, amount: float, order_id: str) -> Dict[str, Any]:
        # Idempotency check
        if order_id in self.processed_transactions:
            print(f"⚠️  Payment already processed for order {order_id}")
            return {
                "status": "success",
                "transaction_id": f"cc_{order_id}",
                "idempotent": True,
            }

        print(f"💳 Processing credit card payment: ${amount:.2f} for order {order_id}")
        time.sleep(0.3)

        if random.random() < self.failure_rate:
            raise TransientError("Credit card payment failed - network timeout")

        transaction_id = f"cc_{random.randint(10000, 99999)}"
        self.processed_transactions.add(order_id)

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "amount": amount,
            "timestamp": time.time(),
        }

    def refund(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        print(f"💳 Refunding ${amount:.2f} for transaction {transaction_id}")
        time.sleep(0.2)
        return {
            "status": "refunded",
            "refund_id": f"refund_{random.randint(10000, 99999)}",
            "amount": amount,
        }


class PayPalPayment(PaymentStrategy):
    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate
        self.processed_transactions = set()

    def process(self, amount: float, order_id: str) -> Dict[str, Any]:
        if order_id in self.processed_transactions:
            print(f"⚠️  PayPal payment already processed for order {order_id}")
            return {
                "status": "success",
                "transaction_id": f"pp_{order_id}",
                "idempotent": True,
            }

        print(f"💰 Processing PayPal payment: ${amount:.2f} for order {order_id}")
        time.sleep(0.3)

        if random.random() < self.failure_rate:
            raise TransientError(
                "PayPal payment failed - service temporarily unavailable"
            )

        transaction_id = f"pp_{random.randint(10000, 99999)}"
        self.processed_transactions.add(order_id)

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "amount": amount,
            "timestamp": time.time(),
        }

    def refund(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        print(f"💰 Refunding ${amount:.2f} via PayPal for transaction {transaction_id}")
        time.sleep(0.2)
        return {
            "status": "refunded",
            "refund_id": f"pp_refund_{random.randint(10000, 99999)}",
            "amount": amount,
        }


# ==================== OBSERVER PATTERN ====================


class OrderEventListener(ABC):
    """Observer for order processing events"""

    @abstractmethod
    def on_stage_complete(self, stage: str, order: Dict[str, Any]) -> None:
        """Called when a processing stage completes"""
        pass

    @abstractmethod
    def on_order_failed(self, order: Dict[str, Any], error: Exception) -> None:
        """Called when order processing fails"""
        pass


class EmailNotifier(OrderEventListener):
    def on_stage_complete(self, stage: str, order: Dict[str, Any]) -> None:
        if stage in ["validate_order", "finalize_order"]:
            print(f"📧 Email: Order {order['id']} - stage '{stage}' completed")

    def on_order_failed(self, order: Dict[str, Any], error: Exception) -> None:
        print(f"📧 Email: Order {order['id']} failed - {error}")


class AnalyticsTracker(OrderEventListener):
    def __init__(self):
        self.metrics = {
            "orders_processed": 0,
            "orders_failed": 0,
            "stages_completed": {},
        }

    def on_stage_complete(self, stage: str, order: Dict[str, Any]) -> None:
        self.metrics["stages_completed"][stage] = (
            self.metrics["stages_completed"].get(stage, 0) + 1
        )
        print(
            f"📊 Analytics: Stage '{stage}' completed (total: {self.metrics['stages_completed'][stage]})"
        )

    def on_order_failed(self, order: Dict[str, Any], error: Exception) -> None:
        self.metrics["orders_failed"] += 1
        print(
            f"📊 Analytics: Order {order['id']} failed (total failures: {self.metrics['orders_failed']})"
        )

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()


class InventoryUpdater(OrderEventListener):
    """Updates inventory system when reservations change"""

    def on_stage_complete(self, stage: str, order: Dict[str, Any]) -> None:
        if stage == "reserve_inventory" and order.get("inventory_reserved"):
            print(f"📦 Inventory System: Reserved items for order {order['id']}")


# ==================== CIRCUIT BREAKER ====================


class CircuitBreaker:
    """
    Circuit breaker for resilient service calls.
    Implements CLOSED -> OPEN -> HALF_OPEN state transitions.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def call(self, operation: Callable) -> Any:
        """Execute operation through circuit breaker"""
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.timeout
            ):
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. Will retry after "
                    f"{self.timeout - (time.time() - self.last_failure_time):.1f}s"
                )

        try:
            result = operation()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)  # Gradual recovery

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        print(
            f"⚠️  Circuit breaker OPENED (failures: {self.failure_count}/{self.failure_threshold})"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        print("🔄 Circuit breaker entering HALF_OPEN state (testing recovery)")

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        print("✅ Circuit breaker CLOSED (fully recovered)")

    def get_state(self) -> str:
        return self.state.value


# ==================== TEMPLATE METHOD ====================


class OrderProcessor(ABC):
    """
    Template for processing orders.
    Defines the order fulfillment workflow with error handling and rollback.
    """

    def __init__(
        self,
        payment_strategy: PaymentStrategy,
        listeners: Optional[List[OrderEventListener]] = None,
        max_retries: int = 3,
    ):
        self.payment_strategy = payment_strategy
        self.listeners = listeners or []
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30.0)
        self.max_retries = max_retries

    def process_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Template method - DO NOT OVERRIDE.
        Processes an order through the complete fulfillment workflow.
        """
        start_time = time.time()
        order["status"] = OrderStatus.PROCESSING.value
        completed_steps: List[str] = []

        print(f"\n{'='*70}")
        print(f"🛒 Processing Order {order['id']}")
        print(f"{'='*70}")

        try:
            # Step 1: Validate Order (required)
            self._validate_order(order)
            completed_steps.append("validate")
            self._notify_listeners("validate_order", order)

            # Step 2: Calculate Item Total
            self._calculate_item_total(order)

            # Step 3: Reserve Inventory (required, idempotent)
            self._execute_with_retry(
                lambda: self._reserve_inventory(order), "inventory_reservation"
            )
            completed_steps.append("reserve_inventory")
            self._notify_listeners("reserve_inventory", order)

            # Step 4: Calculate Shipping (conditional)
            if self._requires_shipping():
                shipping_cost = self._calculate_shipping(order)
                order["shipping_cost"] = shipping_cost
                print(f"📦 Shipping cost: ${shipping_cost:.2f}")
            else:
                order["shipping_cost"] = 0.0
                print("📦 No shipping required")
            completed_steps.append("calculate_shipping")

            # Step 5: Apply Promotions (hook)
            self._apply_promotions(order)
            completed_steps.append("apply_promotions")

            # Step 6: Calculate Final Total
            self._calculate_final_total(order)
            print(f"💵 Order total: ${order['total_amount']:.2f}")

            # Step 7: Process Payment (required, idempotent with retries)
            self._process_payment_with_retry(order)
            completed_steps.append("payment")
            self._notify_listeners("process_payment", order)

            # Step 8: Finalize Order (required)
            self._execute_with_retry(
                lambda: self._finalize_order(order), "order_finalization"
            )
            completed_steps.append("finalize")
            self._notify_listeners("finalize_order", order)

            # Step 9: Notify Customer (hook)
            self._notify_customer(order)

            # Step 10: Update Analytics (hook)
            self._update_analytics(order)

            # Success!
            order["status"] = OrderStatus.COMPLETED.value
            elapsed = time.time() - start_time
            print(f"\n✅ Order {order['id']} completed successfully in {elapsed:.2f}s")
            print(f"{'='*70}\n")

            return order

        except CircuitBreakerOpen as e:
            print(f"\n❌ Circuit breaker open: {e}")
            order["status"] = OrderStatus.FAILED.value
            order["error"] = str(e)
            self._notify_listeners_of_failure(order, e)
            return order

        except PermanentError as e:
            print(f"\n❌ Permanent error: {e}")
            self._rollback_order(order, completed_steps)
            order["status"] = OrderStatus.FAILED.value
            order["error"] = str(e)
            self._notify_listeners_of_failure(order, e)
            return order

        except Exception as e:
            print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
            self._rollback_order(order, completed_steps)
            order["status"] = OrderStatus.FAILED.value
            order["error"] = str(e)
            self._notify_listeners_of_failure(order, e)
            return order

    # ==================== REQUIRED ABSTRACT METHODS ====================

    @abstractmethod
    def _validate_order(self, order: Dict[str, Any]) -> None:
        """Validate order data, inventory availability, and prerequisites"""
        pass

    @abstractmethod
    def _reserve_inventory(self, order: Dict[str, Any]) -> None:
        """Reserve inventory for order items (must be idempotent)"""
        pass

    @abstractmethod
    def _calculate_shipping(self, order: Dict[str, Any]) -> float:
        """Calculate shipping cost based on order details"""
        pass

    @abstractmethod
    def _finalize_order(self, order: Dict[str, Any]) -> None:
        """Mark order as complete and update all systems"""
        pass

    # ==================== HOOK METHODS ====================

    def _apply_promotions(self, order: Dict[str, Any]) -> None:
        """Hook: Apply promotional discounts"""
        pass

    def _notify_customer(self, order: Dict[str, Any]) -> None:
        """Hook: Send customer notification"""
        pass

    def _update_analytics(self, order: Dict[str, Any]) -> None:
        """Hook: Track order metrics"""
        pass

    def _requires_shipping(self) -> bool:
        """Hook: Return True if physical shipping is needed"""
        return False

    # ==================== HELPER METHODS ====================

    def _calculate_item_total(self, order: Dict[str, Any]) -> None:
        """Calculate total from order items"""
        items = order.get("items", [])
        if not items:
            order["items_total"] = 0.0
            return

        total = sum(item.get("price", 0.0) * item.get("quantity", 1) for item in items)
        order["items_total"] = total
        print(f"💰 Items total: ${total:.2f}")

    def _calculate_final_total(self, order: Dict[str, Any]) -> None:
        """Calculate final order total including all fees and discounts"""
        items_total = order.get("items_total", 0.0)
        shipping = order.get("shipping_cost", 0.0)
        discount = order.get("discount", 0.0)
        tax = order.get("tax", 0.0)

        order["total_amount"] = items_total + shipping + tax - discount

    def _process_payment_with_retry(self, order: Dict[str, Any]) -> None:
        """Process payment with retry logic and circuit breaker"""
        amount = order.get("total_amount", 0.0)
        order_id = order.get("id", "unknown")

        def payment_operation():
            return self.circuit_breaker.call(
                lambda: self.payment_strategy.process(amount, order_id)
            )

        payment_result = self._execute_with_retry(
            payment_operation, f"payment for order {order_id}"
        )

        order["payment"] = payment_result
        print(f"✅ Payment successful: {payment_result.get('transaction_id')}")

    def _execute_with_retry(self, operation: Callable, operation_name: str) -> Any:
        """Execute operation with exponential backoff retry"""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result = operation()
                if attempt > 1:
                    print(f"✅ {operation_name} succeeded on attempt {attempt}")
                return result

            except TransientError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = (2**attempt) + random.uniform(0, 0.5)
                    print(
                        f"⚠️  {operation_name} failed (attempt {attempt}/{self.max_retries}): {e}"
                    )
                    print(f"   Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    print(
                        f"❌ {operation_name} failed after {self.max_retries} attempts"
                    )
                    raise PermanentError(
                        f"Max retries exceeded for {operation_name}: {e}"
                    ) from e

            except (PermanentError, CircuitBreakerOpen):
                raise

            except Exception as e:
                print(f"❌ Unexpected error in {operation_name}: {e}")
                raise PermanentError(f"Unexpected error in {operation_name}") from e

        # Should never reach here, but for type safety
        raise PermanentError(f"Failed to execute {operation_name}") from last_error

    def _rollback_order(
        self, order: Dict[str, Any], completed_steps: List[str]
    ) -> None:
        """Compensate for partial order processing (Saga pattern)"""
        if not completed_steps:
            return

        print(f"\n🔄 Rolling back order {order['id']}...")
        print(f"   Steps to compensate: {', '.join(reversed(completed_steps))}")

        for step in reversed(completed_steps):
            try:
                if step == "payment":
                    self._compensate_payment(order)
                elif step == "reserve_inventory":
                    self._compensate_inventory(order)
                elif step == "finalize":
                    self._compensate_finalization(order)

                print(f"   ↩️  Compensated: {step}")

            except Exception as e:
                print(f"   ⚠️  Compensation failed for {step}: {e}")

        order["status"] = OrderStatus.ROLLED_BACK.value
        print(f"✅ Rollback completed for order {order['id']}\n")

    def _compensate_payment(self, order: Dict[str, Any]) -> None:
        """Refund payment"""
        payment_info = order.get("payment", {})
        transaction_id = payment_info.get("transaction_id")
        amount = payment_info.get("amount", order.get("total_amount", 0.0))

        if transaction_id:
            refund_result = self.payment_strategy.refund(transaction_id, amount)
            order["refund"] = refund_result
            print(f"      💸 Refunded ${amount:.2f}")

    def _compensate_inventory(self, order: Dict[str, Any]) -> None:
        """Release reserved inventory"""
        if order.get("inventory_reserved"):
            reservation_id = order.get("reservation_id", "unknown")
            print(f"      📦 Released inventory reservation: {reservation_id}")
            order["inventory_reserved"] = False

    def _compensate_finalization(self, order: Dict[str, Any]) -> None:
        """Undo order finalization"""
        print(f"      🗑️  Reversed order finalization")

    def _notify_listeners(self, stage: str, order: Dict[str, Any]) -> None:
        """Notify all registered listeners of stage completion"""
        for listener in self.listeners:
            try:
                listener.on_stage_complete(stage, order)
            except Exception as e:
                print(f"⚠️  Listener notification failed: {e}")

    def _notify_listeners_of_failure(
        self, order: Dict[str, Any], error: Exception
    ) -> None:
        """Notify listeners of order failure"""
        for listener in self.listeners:
            try:
                listener.on_order_failed(order, error)
            except Exception as e:
                print(f"⚠️  Listener failure notification failed: {e}")


# ==================== CONCRETE IMPLEMENTATIONS ====================


class StandardOrderProcessor(OrderProcessor):
    """
    Processes standard physical product orders.
    - Full workflow with inventory and shipping
    - Sends customer notifications
    - Tracks analytics
    """

    def _validate_order(self, order: Dict[str, Any]) -> None:
        """Validate order has required fields and items"""
        if "id" not in order:
            raise PermanentError("Order missing ID")

        items = order.get("items", [])
        if not items:
            raise PermanentError("Order has no items")

        # Validate each item
        for item in items:
            if "price" not in item or "quantity" not in item:
                raise PermanentError(f"Invalid item structure: {item}")
            if item["quantity"] <= 0:
                raise PermanentError(f"Invalid quantity for item: {item}")

        print(f"✓ Order {order['id']} validated (Physical Products)")

    def _reserve_inventory(self, order: Dict[str, Any]) -> None:
        """Reserve inventory (idempotent operation)"""
        # Idempotency check
        if order.get("inventory_reserved"):
            print(f"✓ Inventory already reserved for order {order['id']}")
            return

        print(f"📦 Reserving inventory for order {order['id']}...")
        time.sleep(0.3)

        # Simulate 90% success rate
        if random.random() < 0.9:
            order["inventory_reserved"] = True
            order["reservation_id"] = f"RES-{random.randint(10000, 99999)}"
            print(f"✓ Inventory reserved: {order['reservation_id']}")
        else:
            raise TransientError("Inventory system temporarily unavailable")

    def _calculate_shipping(self, order: Dict[str, Any]) -> float:
        """Calculate shipping based on items"""
        items = order.get("items", [])

        # Simple calculation: $5.99 base + $1 per item
        base_shipping = 5.99
        per_item = sum(item.get("quantity", 1) for item in items)

        return base_shipping + per_item

    def _finalize_order(self, order: Dict[str, Any]) -> None:
        """Finalize order in database"""
        print(f"💾 Finalizing order {order['id']} in database...")
        time.sleep(0.4)

        # Simulate 95% success rate
        if random.random() < 0.95:
            order["finalized_at"] = time.time()
            print(f"✓ Order {order['id']} finalized")
        else:
            raise TransientError("Database temporarily unavailable")

    def _apply_promotions(self, order: Dict[str, Any]) -> None:
        """Apply promotional discounts"""
        promo_code = order.get("promo_code")
        if promo_code == "SAVE10":
            discount = order.get("items_total", 0.0) * 0.10
            order["discount"] = discount
            print(f"🎟️  Applied promo code '{promo_code}': -${discount:.2f}")
        else:
            order["discount"] = 0.0

    def _notify_customer(self, order: Dict[str, Any]) -> None:
        """Send order confirmation email"""
        print(f"📧 Sending confirmation email for order {order['id']}")
        print(f"   To: {order.get('customer_email', 'customer@example.com')}")

    def _update_analytics(self, order: Dict[str, Any]) -> None:
        """Track order in analytics system"""
        print(f"📊 Tracking order {order['id']} in analytics")
        print(
            f"   Total: ${order.get('total_amount', 0):.2f}, "
            f"Items: {len(order.get('items', []))}"
        )

    def _requires_shipping(self) -> bool:
        return True


class DigitalOrderProcessor(OrderProcessor):
    """
    Processes digital product orders (ebooks, software, licenses).
    - No physical inventory or shipping
    - Instant delivery via download link
    - Simplified workflow
    """

    def _validate_order(self, order: Dict[str, Any]) -> None:
        """Validate digital order"""
        if "id" not in order:
            raise PermanentError("Order missing ID")

        items = order.get("items", [])
        if not items:
            raise PermanentError("Order has no items")

        # Verify all items are digital
        for item in items:
            if not item.get("is_digital", True):
                raise PermanentError(f"Non-digital item in digital order: {item}")

        if "customer_email" not in order:
            raise PermanentError("Digital orders require customer email")

        print(f"✓ Digital order {order['id']} validated")

    def _reserve_inventory(self, order: Dict[str, Any]) -> None:
        """No inventory reservation needed for digital products"""
        if order.get("inventory_reserved"):
            return

        print(f"✓ Digital products - no inventory reservation needed")
        order["inventory_reserved"] = True  # Mark as done for workflow

    def _calculate_shipping(self, order: Dict[str, Any]) -> float:
        """No shipping for digital products"""
        return 0.0

    def _finalize_order(self, order: Dict[str, Any]) -> None:
        """Generate download links and finalize"""
        print(f"🔗 Generating download links for order {order['id']}...")
        time.sleep(0.2)

        # Simulate 98% success rate
        if random.random() < 0.98:
            download_links = []
            for item in order.get("items", []):
                link = f"https://downloads.example.com/{item.get('id', 'unknown')}/{random.randint(100000, 999999)}"
                download_links.append(link)

            order["download_links"] = download_links
            order["finalized_at"] = time.time()
            order["expires_at"] = time.time() + (7 * 24 * 3600)  # 7 days
            print(f"✓ Generated {len(download_links)} download link(s)")
        else:
            raise TransientError("Download link generation service unavailable")

    def _notify_customer(self, order: Dict[str, Any]) -> None:
        """Send download links to customer"""
        email = order.get("customer_email", "customer@example.com")
        links = order.get("download_links", [])

        print(f"📧 Sending download links to {email}")
        print(f"   {len(links)} download link(s) included")
        print(f"   Links expire in 7 days")

    def _update_analytics(self, order: Dict[str, Any]) -> None:
        """Track digital order metrics"""
        print(f"📊 Tracking digital order {order['id']}")
        print(f"   Revenue: ${order.get('total_amount', 0):.2f}")

    def _requires_shipping(self) -> bool:
        return False


class SubscriptionOrderProcessor(OrderProcessor):
    """
    Processes recurring subscription orders.
    - Different payment handling (save payment method)
    - Schedule recurring billing
    - Special promotional handling
    - Extended analytics tracking
    """

    def _validate_order(self, order: Dict[str, Any]) -> None:
        """Validate subscription order"""
        if "id" not in order:
            raise PermanentError("Order missing ID")

        if "subscription_plan" not in order:
            raise PermanentError("Subscription order missing plan")

        if "customer_email" not in order:
            raise PermanentError("Subscription orders require customer email")

        # Validate billing frequency
        valid_frequencies = ["monthly", "quarterly", "annual"]
        frequency = order.get("billing_frequency", "monthly")
        if frequency not in valid_frequencies:
            raise PermanentError(f"Invalid billing frequency: {frequency}")

        print(f"✓ Subscription order {order['id']} validated")
        print(f"   Plan: {order['subscription_plan']}")
        print(f"   Frequency: {frequency}")

    def _reserve_inventory(self, order: Dict[str, Any]) -> None:
        """No inventory reservation for subscriptions"""
        if order.get("inventory_reserved"):
            return

        print(f"✓ Subscription service - no inventory reservation needed")
        order["inventory_reserved"] = True

    def _calculate_shipping(self, order: Dict[str, Any]) -> float:
        """No shipping for subscriptions"""
        return 0.0

    def _apply_promotions(self, order: Dict[str, Any]) -> None:
        """Apply subscription-specific promotions"""
        promo_code = order.get("promo_code")

        # Special subscription promotions
        if promo_code == "ANNUAL20":
            if order.get("billing_frequency") == "annual":
                discount = order.get("items_total", 0.0) * 0.20
                order["discount"] = discount
                print(f"🎟️  Applied annual subscription discount: -${discount:.2f}")
            else:
                print(f"⚠️  Promo code '{promo_code}' only valid for annual plans")
                order["discount"] = 0.0
        elif promo_code == "FIRST_MONTH_FREE":
            # First month free
            plan_price = order.get("items_total", 0.0)
            order["discount"] = plan_price
            order["first_month_free"] = True
            print(f"🎟️  Applied first month free promotion: -${plan_price:.2f}")
        else:
            order["discount"] = 0.0

    def _finalize_order(self, order: Dict[str, Any]) -> None:
        """
        Finalize subscription:
        - Save payment method for recurring billing
        - Schedule next billing date
        - Activate subscription
        """
        print(f"🔄 Setting up recurring subscription for order {order['id']}...")
        time.sleep(0.3)

        # Simulate 97% success rate
        if random.random() < 0.97:
            frequency = order.get("billing_frequency", "monthly")

            # Calculate next billing date
            frequency_days = {"monthly": 30, "quarterly": 90, "annual": 365}
            next_billing = time.time() + (frequency_days[frequency] * 24 * 3600)

            order["subscription_id"] = f"SUB-{random.randint(100000, 999999)}"
            order["next_billing_date"] = next_billing
            order["subscription_status"] = "active"
            order["finalized_at"] = time.time()

            print(f"✓ Subscription {order['subscription_id']} activated")
            print(f"   Next billing: {frequency_days[frequency]} days")
        else:
            raise TransientError("Subscription service temporarily unavailable")

    def _notify_customer(self, order: Dict[str, Any]) -> None:
        """Send subscription welcome email"""
        email = order.get("customer_email", "customer@example.com")
        subscription_id = order.get("subscription_id", "unknown")

        print(f"📧 Sending subscription welcome email to {email}")
        print(f"   Subscription ID: {subscription_id}")
        print(f"   Includes: account setup, billing info, cancellation policy")

    def _update_analytics(self, order: Dict[str, Any]) -> None:
        """Track subscription metrics (LTV, churn prediction, etc.)"""
        plan = order.get("subscription_plan", "unknown")
        frequency = order.get("billing_frequency", "monthly")
        amount = order.get("total_amount", 0.0)

        # Calculate Lifetime Value estimate
        frequency_multiplier = {"monthly": 12, "quarterly": 4, "annual": 1}
        estimated_ltv = (
            amount * frequency_multiplier.get(frequency, 1) * 2
        )  # 2 year estimate

        print(f"📊 Tracking subscription metrics:")
        print(f"   Plan: {plan} ({frequency})")
        print(f"   MRR: ${amount:.2f}")
        print(f"   Estimated LTV: ${estimated_ltv:.2f}")

    def _requires_shipping(self) -> bool:
        return False


# ==================== DEMONSTRATION ====================


def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_order_summary(order: Dict[str, Any]):
    """Print a summary of order processing result"""
    status = order.get("status", "unknown")
    status_emoji = {"completed": "✅", "failed": "❌", "rolled_back": "🔄"}
    emoji = status_emoji.get(status, "❓")

    print(f"\n{emoji} ORDER SUMMARY")
    print(f"   Order ID: {order.get('id', 'unknown')}")
    print(f"   Status: {status.upper()}")
    print(f"   Total: ${order.get('total_amount', 0):.2f}")

    if status == "completed":
        if "payment" in order:
            print(f"   Transaction: {order['payment'].get('transaction_id', 'N/A')}")
    elif status in ["failed", "rolled_back"]:
        print(f"   Error: {order.get('error', 'Unknown error')}")
        if "refund" in order:
            print(f"   Refund: {order['refund'].get('refund_id', 'N/A')}")


def main():
    """Demonstrate all order processors with various scenarios"""

    print("\n" + "=" * 70)
    print("  🏪 E-COMMERCE ORDER FULFILLMENT SYSTEM DEMONSTRATION")
    print("=" * 70)

    # Setup observers
    email_notifier = EmailNotifier()
    analytics_tracker = AnalyticsTracker()
    inventory_updater = InventoryUpdater()
    listeners = [email_notifier, analytics_tracker, inventory_updater]

    # ==================== TEST 1: Successful Standard Order ====================
    print_section_header("TEST 1: Successful Standard Order (Physical Products)")

    standard_processor = StandardOrderProcessor(
        payment_strategy=CreditCardPayment(failure_rate=0.0),  # No failures
        listeners=listeners,
        max_retries=3,
    )

    order1 = {
        "id": "ORD-1001",
        "customer_email": "john@example.com",
        "items": [
            {"id": "WIDGET-A", "name": "Super Widget", "price": 29.99, "quantity": 2},
            {"id": "GADGET-B", "name": "Mega Gadget", "price": 49.99, "quantity": 1},
        ],
        "promo_code": "SAVE10",
    }

    result1 = standard_processor.process_order(order1)
    print_order_summary(result1)

    # ==================== TEST 2: Successful Digital Order ====================
    print_section_header("TEST 2: Successful Digital Order (Instant Delivery)")

    digital_processor = DigitalOrderProcessor(
        payment_strategy=PayPalPayment(failure_rate=0.0),
        listeners=listeners,
        max_retries=3,
    )

    order2 = {
        "id": "ORD-2001",
        "customer_email": "sarah@example.com",
        "items": [
            {
                "id": "EBOOK-001",
                "name": "Python Mastery",
                "price": 19.99,
                "quantity": 1,
                "is_digital": True,
            },
            {
                "id": "VIDEO-002",
                "name": "Design Patterns Course",
                "price": 49.99,
                "quantity": 1,
                "is_digital": True,
            },
        ],
    }

    result2 = digital_processor.process_order(order2)
    print_order_summary(result2)

    # ==================== TEST 3: Successful Subscription Order ====================
    print_section_header("TEST 3: Successful Subscription Order (Recurring)")

    subscription_processor = SubscriptionOrderProcessor(
        payment_strategy=CreditCardPayment(failure_rate=0.0),
        listeners=listeners,
        max_retries=3,
    )

    order3 = {
        "id": "SUB-3001",
        "customer_email": "alex@example.com",
        "subscription_plan": "Premium",
        "billing_frequency": "annual",
        "items": [
            {
                "id": "PLAN-PREMIUM",
                "name": "Premium Annual Plan",
                "price": 99.99,
                "quantity": 1,
            }
        ],
        "promo_code": "ANNUAL20",
    }

    result3 = subscription_processor.process_order(order3)
    print_order_summary(result3)

    # ==================== TEST 4: Order with Transient Errors (Retry Success) ====================
    print_section_header("TEST 4: Order with Transient Errors (Retry Succeeds)")

    # Use payment strategy with high failure rate (will trigger retries)
    retry_processor = StandardOrderProcessor(
        payment_strategy=CreditCardPayment(failure_rate=0.7),  # 70% failure rate
        listeners=listeners,
        max_retries=5,  # More retries to demonstrate exponential backoff
    )

    order4 = {
        "id": "ORD-4001",
        "customer_email": "retry@example.com",
        "items": [
            {
                "id": "WIDGET-C",
                "name": "Resilient Widget",
                "price": 39.99,
                "quantity": 1,
            }
        ],
    }

    result4 = retry_processor.process_order(order4)
    print_order_summary(result4)

    # ==================== TEST 5: Order Failure with Rollback ====================
    print_section_header("TEST 5: Order Failure with Rollback")

    failure_processor = StandardOrderProcessor(
        payment_strategy=CreditCardPayment(failure_rate=1.0),  # Always fail
        listeners=listeners,
        max_retries=2,
    )

    order5 = {
        "id": "ORD-5001",
        "customer_email": "failure@example.com",
        "items": [
            {"id": "WIDGET-D", "name": "Doomed Widget", "price": 19.99, "quantity": 1}
        ],
    }

    result5 = failure_processor.process_order(order5)
    print_order_summary(result5)

    # ==================== TEST 6: Invalid Order (Validation Failure) ====================
    print_section_header("TEST 6: Invalid Order (Validation Failure)")

    order6 = {"id": "ORD-6001", "items": []}  # Empty items - should fail validation

    result6 = standard_processor.process_order(order6)
    print_order_summary(result6)

    # ==================== TEST 7: Circuit Breaker Demonstration ====================
    print_section_header("TEST 7: Circuit Breaker (Multiple Failures)")

    # Process multiple failing orders to trigger circuit breaker
    circuit_breaker_processor = StandardOrderProcessor(
        payment_strategy=CreditCardPayment(failure_rate=1.0),
        listeners=listeners,
        max_retries=1,  # Fail fast
    )

    print("\nProcessing multiple failing orders to open circuit breaker...")
    for i in range(6):  # Trigger circuit breaker threshold
        test_order = {
            "id": f"ORD-700{i}",
            "customer_email": "test@example.com",
            "items": [{"id": "TEST", "name": "Test", "price": 10.0, "quantity": 1}],
        }
        result = circuit_breaker_processor.process_order(test_order)
        if i >= 3:  # Check if circuit opened
            circuit_state = circuit_breaker_processor.circuit_breaker.get_state()
            print(f"   Circuit breaker state: {circuit_state.upper()}")

    # ==================== FINAL ANALYTICS ====================
    print_section_header("FINAL ANALYTICS SUMMARY")

    metrics = analytics_tracker.get_metrics()
    print(f"\n📊 Processing Statistics:")
    print(f"   Total Orders Failed: {metrics['orders_failed']}")
    print(f"\n📈 Stages Completed:")
    for stage, count in sorted(metrics["stages_completed"].items()):
        print(f"   - {stage}: {count}")

    print("\n" + "=" * 70)
    print("  🎬 DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Set random seed for reproducible demo
    random.seed(42)
    main()
