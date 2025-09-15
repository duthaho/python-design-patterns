import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Set up structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# SUBSYSTEM CLASSES (Microservices) - PROVIDED
# ============================================================================


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class ServiceResponse:
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    status_code: int = 200
    response_time_ms: float = 0


class UserService:
    def __init__(self):
        self.status = ServiceStatus.HEALTHY
        self.failure_rate = 0.0  # Simulate failures
        self.response_delay = 0.1  # Simulate latency

    def authenticate(self, token: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        if self.failure_rate > 0 and time.time() % 10 < self.failure_rate * 10:
            return ServiceResponse(
                False, error="Authentication service unavailable", status_code=503
            )

        if token == "valid_token":
            return ServiceResponse(
                True,
                {
                    "user_id": "user_123",
                    "email": "user@example.com",
                    "role": "customer",
                },
            )
        return ServiceResponse(False, error="Invalid token", status_code=401)

    def get_user_profile(self, user_id: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        if self.failure_rate > 0 and time.time() % 10 < self.failure_rate * 10:
            return ServiceResponse(
                False, error="User service unavailable", status_code=503
            )

        return ServiceResponse(
            True,
            {
                "user_id": user_id,
                "name": "John Doe",
                "email": "john@example.com",
                "tier": "premium",
            },
        )

    def update_user_profile(self, user_id: str, data: Dict) -> ServiceResponse:
        time.sleep(self.response_delay)

        return ServiceResponse(True, {"user_id": user_id, "updated": True})


class OrderService:
    def __init__(self):
        self.status = ServiceStatus.HEALTHY
        self.failure_rate = 0.0  # Simulate failures
        self.response_delay = 0.1  # Simulate latency

    def create_order(self, user_id: str, items: List[Dict]) -> ServiceResponse:
        time.sleep(self.response_delay)

        if self.failure_rate > 0 and time.time() % 10 < self.failure_rate * 10:
            return ServiceResponse(
                False, error="Order service unavailable", status_code=503
            )

        order_id = f"order_{uuid.uuid4().hex[:8]}"
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

        return ServiceResponse(
            True,
            {
                "order_id": order_id,
                "user_id": user_id,
                "items": items,
                "total": total,
                "status": "pending",
            },
        )

    def get_order(self, order_id: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        return ServiceResponse(
            True, {"order_id": order_id, "status": "completed", "total": 99.99}
        )

    def cancel_order(self, order_id: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        return ServiceResponse(True, {"order_id": order_id, "status": "cancelled"})


class PaymentService:
    def __init__(self):
        self.status = ServiceStatus.HEALTHY
        self.failure_rate = 0.0  # Simulate failures
        self.response_delay = 0.2  # Simulate latency

    def process_payment(
        self, order_id: str, amount: float, payment_method: Dict
    ) -> ServiceResponse:
        time.sleep(self.response_delay)

        if self.failure_rate > 0 and time.time() % 10 < self.failure_rate * 10:
            return ServiceResponse(
                False, error="Payment service unavailable", status_code=503
            )

        # Simulate payment failure for large amounts
        if amount > 1000:
            return ServiceResponse(False, error="Payment declined", status_code=402)

        return ServiceResponse(
            True,
            {
                "payment_id": f"pay_{uuid.uuid4().hex[:8]}",
                "order_id": order_id,
                "amount": amount,
                "status": "completed",
            },
        )

    def refund_payment(self, payment_id: str, amount: float) -> ServiceResponse:
        time.sleep(self.response_delay)

        return ServiceResponse(
            True,
            {
                "refund_id": f"ref_{uuid.uuid4().hex[:8]}",
                "payment_id": payment_id,
                "amount": amount,
                "status": "processed",
            },
        )


class NotificationService:
    def __init__(self):
        self.status = ServiceStatus.HEALTHY
        self.failure_rate = 0.0  # Simulate failures
        self.response_delay = 0.05  # Simulate latency

    def send_email(self, user_id: str, subject: str, body: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        if self.failure_rate > 0 and time.time() % 10 < self.failure_rate * 10:
            return ServiceResponse(
                False, error="Notification service unavailable", status_code=503
            )

        return ServiceResponse(
            True,
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "email",
                "status": "sent",
            },
        )

    def send_sms(self, user_id: str, message: str) -> ServiceResponse:
        time.sleep(self.response_delay)

        return ServiceResponse(
            True,
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "sms",
                "status": "sent",
            },
        )


# ============================================================================
# HELPER CLASSES FOR YOUR IMPLEMENTATION
# ============================================================================


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""

    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    timeout_seconds: int = 60


@dataclass
class RateLimitState:
    """Rate limiting state per user"""

    request_count: int = 0
    window_start: datetime = field(default_factory=datetime.now)
    max_requests: int = 100
    window_seconds: int = 60


@dataclass
class APIRequest:
    """Standardized API request"""

    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Optional[Dict] = None
    user_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class APIResponse:
    """Standardized API response"""

    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    status_code: int = 200
    request_id: Optional[str] = None
    response_time_ms: float = 0


@dataclass
class Metrics:
    """Simple metrics tracking"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0
    circuit_breaker_trips: int = 0
    rate_limit_violations: int = 0


# ============================================================================
# YOUR IMPLEMENTATION TASK
# ============================================================================


class APIGatewayFacade:
    """
    API Gateway Facade providing unified interface to microservices with:
    - Authentication & Authorization
    - Rate Limiting
    - Circuit Breaking
    - Request Orchestration
    - Metrics & Monitoring

    TODO: Implement all methods below
    """

    def __init__(self):
        # Microservices
        self.user_service = UserService()
        self.order_service = OrderService()
        self.payment_service = PaymentService()
        self.notification_service = NotificationService()

        # Circuit breakers for each service
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {
            "user_service": CircuitBreakerState(),
            "order_service": CircuitBreakerState(),
            "payment_service": CircuitBreakerState(),
            "notification_service": CircuitBreakerState(),
        }

        # Rate limiting per user
        self.rate_limits: Dict[str, RateLimitState] = {}

        # Metrics
        self.metrics = Metrics()

        self.request_history = []

    # ========================================================================
    # TODO: Implement these core methods
    # ========================================================================

    def authenticate_request(self, request: APIRequest) -> tuple[bool, Optional[Dict]]:
        """
        Authenticate incoming request and extract user info.

        Args:
            request: The incoming API request

        Returns:
            Tuple of (is_authenticated, user_info)

        TODO:
        - Extract auth token from headers
        - Call user service to validate
        - Handle circuit breaker for user service
        - Return user info if valid
        """
        logger.info(
            f"🔐 Authenticating request {request.request_id} for endpoint {request.endpoint}"
        )

        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.warning(
                    f"❌ Missing or invalid auth header for request {request.request_id}"
                )
                return False, None

            token = auth_header.split(" ")[1]

            response = self.call_with_circuit_breaker(
                "user_service", lambda: self.user_service.authenticate(token)
            )

            if response.success:
                user_id = response.data.get("user_id")
                logger.info(f"✅ Authentication successful for user {user_id}")
                return True, response.data
            else:
                logger.warning(f"❌ Authentication failed: {response.error}")
                return False, None

        except Exception as e:
            logger.error(
                f"❌ Authentication error for request {request.request_id}: {str(e)}"
            )
            return False, None

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User identifier

        Returns:
            True if request allowed, False if rate limited

        TODO:
        - Implement sliding window rate limiting
        - Track requests per user per time window
        - Reset counters when window expires
        """
        now = datetime.now()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = RateLimitState()
        rate_limit = self.rate_limits[user_id]
        if (now - rate_limit.window_start).total_seconds() > rate_limit.window_seconds:
            rate_limit.request_count = 0
            rate_limit.window_start = now
        rate_limit.request_count += 1
        if rate_limit.request_count > rate_limit.max_requests:
            self.metrics.rate_limit_violations += 1
            return False
        return True

    def call_with_circuit_breaker(
        self, service_name: str, service_call
    ) -> ServiceResponse:
        """
        Execute service call with circuit breaker protection.

        Args:
            service_name: Name of the service
            service_call: Function to execute

        Returns:
            ServiceResponse from the service or circuit breaker

        TODO:
        - Check circuit breaker state (CLOSED/OPEN/HALF_OPEN)
        - Execute call if allowed
        - Update failure counts and state
        - Return fallback response if circuit is open
        """
        breaker = self.circuit_breakers[service_name]
        now = datetime.now()

        if breaker.state == "OPEN":
            if (
                breaker.last_failure_time
                and (now - breaker.last_failure_time).total_seconds()
                > breaker.timeout_seconds
            ):
                breaker.state = "HALF_OPEN"
                logger.info(
                    f"🔄 Circuit breaker for {service_name} transitioning to HALF_OPEN"
                )
            else:
                self.metrics.circuit_breaker_trips += 1
                logger.warning(
                    f"⚡ Circuit breaker for {service_name} is OPEN - failing fast"
                )
                return ServiceResponse(
                    False,
                    error=f"{service_name} circuit breaker is OPEN",
                    status_code=503,
                )

        try:
            start_time = time.time()
            response = service_call()
            call_duration = (time.time() - start_time) * 1000

            if response.success:
                if breaker.state != "CLOSED":
                    logger.info(
                        f"✅ Circuit breaker for {service_name} reset to CLOSED"
                    )
                breaker.failure_count = 0
                breaker.state = "CLOSED"
                logger.debug(
                    f"🎯 {service_name} call succeeded in {call_duration:.2f}ms"
                )
            else:
                breaker.failure_count += 1
                breaker.last_failure_time = now

                if breaker.failure_count >= breaker.failure_threshold:
                    breaker.state = "OPEN"
                    logger.error(
                        f"💥 Circuit breaker for {service_name} tripped to OPEN state"
                    )
                else:
                    logger.warning(
                        f"⚠️ {service_name} failure {breaker.failure_count}/{breaker.failure_threshold}"
                    )

            return response

        except Exception as e:
            breaker.failure_count += 1
            breaker.last_failure_time = now

            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = "OPEN"
                logger.error(
                    f"💥 Circuit breaker for {service_name} tripped due to exception"
                )

            logger.error(f"❌ {service_name} call failed: {str(e)}")
            return ServiceResponse(
                False, error=f"{service_name} call failed: {str(e)}", status_code=500
            )

    def place_order_workflow(self, request: APIRequest) -> APIResponse:
        """
        Complex workflow: authenticate -> create order -> process payment -> send notification

        Args:
            request: API request containing order details

        Returns:
            APIResponse with order result

        TODO:
        - Authenticate user
        - Check rate limits
        - Create order via order service
        - Process payment via payment service
        - Send confirmation via notification service
        - Handle partial failures gracefully
        - Implement compensating transactions if needed
        """
        try:
            start_time = time.time()
            self.metrics.total_requests += 1

            # Step 1: Authenticate
            is_auth, user_info = self.authenticate_request(request)
            if not is_auth or not user_info:
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error="Authentication failed",
                    status_code=401,
                    request_id=request.request_id,
                )
            user_id = user_info["user_id"]

            # Step 2: Rate limiting
            if not self.check_rate_limit(user_id):
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error="Rate limit exceeded",
                    status_code=429,
                    request_id=request.request_id,
                )

            # Step 3: Create order
            items = request.body.get("items", [])
            if not items:
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error="Order items are required",
                    status_code=400,
                    request_id=request.request_id,
                )

            order_response = self.call_with_circuit_breaker(
                "order_service",
                lambda: self.order_service.create_order(user_id, items),
            )
            if not order_response.success:
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error=f"Order creation failed: {order_response.error}",
                    status_code=order_response.status_code,
                    request_id=request.request_id,
                )
            order_data = order_response.data
            order_id = order_data["order_id"]
            total_amount = order_data["total"]

            # Step 4: Process payment
            payment_method = request.body.get("payment_method", {})
            payment_response = self.call_with_circuit_breaker(
                "payment_service",
                lambda: self.payment_service.process_payment(
                    order_id, total_amount, payment_method
                ),
            )
            if not payment_response.success:
                # Compensating transaction: cancel order
                self.call_with_circuit_breaker(
                    "order_service",
                    lambda: self.order_service.cancel_order(order_id),
                )
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error=f"Payment failed: {payment_response.error}",
                    status_code=payment_response.status_code,
                    request_id=request.request_id,
                )
            payment_data = payment_response.data

            # Step 5: Send notification
            notification_response = self.call_with_circuit_breaker(
                "notification_service",
                lambda: self.notification_service.send_email(
                    user_id,
                    "Order Confirmation",
                    f"Your order {order_id} has been placed successfully!",
                ),
            )
            if not notification_response.success:
                # Log but do not fail the whole workflow
                print(f"Warning: Notification failed: {notification_response.error}")
            self.metrics.successful_requests += 1
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time = (
                self.metrics.avg_response_time * (self.metrics.total_requests - 1)
                + response_time
            ) / self.metrics.total_requests
            return APIResponse(
                True,
                data={
                    "order": order_data,
                    "payment": payment_data,
                    "notification": (
                        notification_response.data
                        if notification_response.success
                        else None
                    ),
                },
                status_code=200,
                request_id=request.request_id,
                response_time_ms=response_time,
            )
        except Exception as e:
            self.metrics.failed_requests += 1
            return APIResponse(
                False,
                error=f"Internal server error: {str(e)}",
                status_code=500,
                request_id=request.request_id,
            )

    def get_user_dashboard(self, request: APIRequest) -> APIResponse:
        """
        Aggregate data from multiple services for user dashboard.

        Args:
            request: API request for user dashboard

        Returns:
            APIResponse with aggregated user data

        TODO:
        - Authenticate user
        - Get user profile from user service
        - Get recent orders from order service
        - Combine data into dashboard response
        - Handle partial service failures gracefully
        """
        try:
            start_time = time.time()
            self.metrics.total_requests += 1

            logger.info(f"📊 Building dashboard for request {request.request_id}")

            # Step 1: Authenticate
            is_auth, user_info = self.authenticate_request(request)
            if not is_auth or not user_info:
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error="Authentication failed",
                    status_code=401,
                    request_id=request.request_id,
                )
            user_id = user_info["user_id"]

            # Step 2: Rate limiting
            if not self.check_rate_limit(user_id):
                self.metrics.failed_requests += 1
                return APIResponse(
                    False,
                    error="Rate limit exceeded",
                    status_code=429,
                    request_id=request.request_id,
                )

            # Step 3: Get user profile
            profile_response = self.call_with_circuit_breaker(
                "user_service", lambda: self.user_service.get_user_profile(user_id)
            )

            profile_data = None
            if profile_response.success:
                profile_data = profile_response.data
                logger.info(f"✅ Profile loaded for user {user_id}")
            else:
                logger.warning(
                    f"⚠️ Profile unavailable for user {user_id}: {profile_response.error}"
                )

            # Step 4: Get recent orders with fallback
            recent_orders = []
            try:
                # Try to get actual orders (simulated here)
                order_response = self.call_with_circuit_breaker(
                    "order_service",
                    lambda: self.order_service.get_order("recent"),  # Simulated call
                )
                if order_response.success:
                    recent_orders = [order_response.data]
                    logger.info(f"✅ Orders loaded for user {user_id}")
                else:
                    logger.warning(f"⚠️ Orders unavailable: {order_response.error}")
                    # Fallback data
                    recent_orders = [{"message": "Orders temporarily unavailable"}]
            except:
                logger.warning("⚠️ Order service call failed, using fallback data")
                recent_orders = [{"message": "Orders temporarily unavailable"}]

            # Combine data with partial failure handling
            dashboard_data = {
                "profile": profile_data
                or {"message": "Profile temporarily unavailable"},
                "recent_orders": recent_orders,
                "service_status": {
                    "profile_available": profile_data is not None,
                    "orders_available": len(recent_orders) > 0
                    and "message" not in recent_orders[0],
                },
            }

            self.metrics.successful_requests += 1
            response_time = (time.time() - start_time) * 1000
            self._update_avg_response_time(response_time)

            logger.info(
                f"✅ Dashboard built successfully for user {user_id} in {response_time:.2f}ms"
            )

            return APIResponse(
                True,
                data=dashboard_data,
                status_code=200,
                request_id=request.request_id,
                response_time_ms=response_time,
            )

        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(
                f"❌ Dashboard error for request {request.request_id}: {str(e)}"
            )
            return APIResponse(
                False,
                error=f"Internal server error: {str(e)}",
                status_code=500,
                request_id=request.request_id,
            )

    def handle_request(self, request: APIRequest) -> APIResponse:
        """
        Main entry point for all API requests.

        Args:
            request: The incoming API request

        Returns:
            APIResponse

        TODO:
        - Route requests to appropriate methods based on endpoint
        - Update metrics
        - Add request/response logging
        - Handle global error cases
        """
        # Simple routing based on endpoint
        if request.endpoint == "/api/orders" and request.method == "POST":
            return self.place_order_workflow(request)
        elif request.endpoint == "/api/user/profile" and request.method == "GET":
            return self.get_user_dashboard(request)
        else:
            self.metrics.failed_requests += 1
            return APIResponse(
                False,
                error="Endpoint not found",
                status_code=404,
                request_id=request.request_id,
            )

    def _update_avg_response_time(self, response_time: float):
        """Helper method to properly calculate rolling average"""
        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time = response_time
        else:
            # Weighted moving average
            weight = 0.1  # Give more weight to recent requests
            self.metrics.avg_response_time = (
                1 - weight
            ) * self.metrics.avg_response_time + weight * response_time

    # ========================================================================
    # TODO: Implement these utility methods
    # ========================================================================

    def get_service_health(self) -> Dict[str, str]:
        """Return health status of all services"""
        health_status = {}
        for service_name, breaker in self.circuit_breakers.items():
            health_status[service_name] = breaker.state
        return health_status

    def get_metrics(self) -> Dict[str, Any]:
        """Return current metrics"""
        return self.metrics.__dict__
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Enhanced metrics with additional insights"""
        base_metrics = self.get_metrics()
        
        # Calculate success rate
        total = self.metrics.total_requests
        success_rate = (self.metrics.successful_requests / total * 100) if total > 0 else 0
        
        # Circuit breaker status
        cb_status = {}
        for service, breaker in self.circuit_breakers.items():
            cb_status[service] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
            }
        
        return {
            **base_metrics,
            "success_rate_percent": round(success_rate, 2),
            "circuit_breakers": cb_status,
            "active_rate_limits": len(self.rate_limits),
        }

    def reset_circuit_breaker(self, service_name: str) -> bool:
        """Manually reset a circuit breaker"""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreakerState()
            return True
        return False

    def update_rate_limits(
        self, user_id: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Update rate limits for a specific user"""
        if user_id in self.rate_limits:
            rate_limit = self.rate_limits[user_id]
            rate_limit.max_requests = max_requests
            rate_limit.window_seconds = window_seconds
            return True
        else:
            self.rate_limits[user_id] = RateLimitState(
                max_requests=max_requests, window_seconds=window_seconds
            )
            return True


# ============================================================================
# TEST SCENARIOS - Use these to test your implementation
# ============================================================================


def test_basic_authentication():
    """Test basic authentication flow"""
    gateway = APIGatewayFacade()

    request = APIRequest(
        endpoint="/api/user/profile",
        method="GET",
        headers={"Authorization": "Bearer valid_token"},
    )

    response = gateway.handle_request(request)
    print(f"Auth test response: {response}")


def test_order_workflow():
    """Test complex order placement workflow"""
    gateway = APIGatewayFacade()

    request = APIRequest(
        endpoint="/api/orders",
        method="POST",
        headers={"Authorization": "Bearer valid_token"},
        body={
            "items": [
                {"product_id": "123", "quantity": 2, "price": 25.99},
                {"product_id": "456", "quantity": 1, "price": 15.50},
            ],
            "payment_method": {"type": "credit_card", "number": "****1234"},
        },
    )

    response = gateway.handle_request(request)
    print(f"Order workflow response: {response}")


def test_rate_limiting():
    """Test rate limiting functionality"""
    gateway = APIGatewayFacade()

    # Simulate multiple requests from same user
    gateway.update_rate_limits("user_123", max_requests=3, window_seconds=10)
    for i in range(5):
        request = APIRequest(
            endpoint="/api/user/profile",
            method="GET",
            headers={"Authorization": "Bearer valid_token"},
        )
        response = gateway.handle_request(request)
        print(f"Request {i+1} response: {response.status_code}")


def test_circuit_breaker():
    """Test circuit breaker functionality"""
    gateway = APIGatewayFacade()

    # Simulate service failures
    gateway.user_service.failure_rate = 1.0  # 100% failure rate

    for i in range(10):
        request = APIRequest(
            endpoint="/api/user/profile",
            method="GET",
            headers={"Authorization": "Bearer valid_token"},
        )
        response = gateway.handle_request(request)
        print(f"Circuit breaker test {i+1}: {response.status_code} - {response.error}")


def demo_api_gateway():
    """Main demo function"""
    print("=== API Gateway Facade Demo ===")
    print("\n1. Testing Authentication...")
    test_basic_authentication()

    print("\n2. Testing Order Workflow...")
    test_order_workflow()

    print("\n3. Testing Rate Limiting...")
    test_rate_limiting()

    print("\n4. Testing Circuit Breaker...")
    test_circuit_breaker()


if __name__ == "__main__":
    demo_api_gateway()
