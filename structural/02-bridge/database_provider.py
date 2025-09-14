import random
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# Configuration and Data Classes
@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    max_connections: int = 10
    timeout: int = 30


@dataclass
class QueryResult:
    data: List[Dict[str, Any]]
    execution_time: float
    rows_affected: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class HealthMetrics:
    response_time_ms: float
    active_connections: int
    error_rate: float
    cpu_usage: float
    memory_usage: float
    last_updated: datetime = field(default_factory=datetime.now)


class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"
    CACHE_GET = "CACHE_GET"
    CACHE_SET = "CACHE_SET"


class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


# ===== IMPLEMENTATION LAYER (Bridge Implementation Side) =====


class DatabaseProvider(ABC):
    """Abstract database provider - the Implementation interface in Bridge pattern"""

    def __init__(self, config: DatabaseConfig, provider_id: str):
        self.config = config
        self.provider_id = provider_id
        self.status = ProviderStatus.OFFLINE
        self.metrics = HealthMetrics(0, 0, 0, 0, 0)
        self.connection_pool = []  # Simulate connection pool

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to database"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        """Execute a database query"""
        pass

    @abstractmethod
    def health_check(self) -> HealthMetrics:
        """Check provider health and return metrics"""
        pass

    @abstractmethod
    def get_optimal_query_types(self) -> List[QueryType]:
        """Return query types this provider handles best"""
        pass

    def get_connection_count(self) -> int:
        """Get current active connection count"""
        return len([c for c in self.connection_pool if c.get("active", False)])


class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL implementation - Concrete Implementation"""

    def connect(self) -> bool:
        # TODO: Implement PostgreSQL connection logic
        # Simulate connection establishment
        print(f"🐘 PostgreSQL connecting to {self.config.host}:{self.config.port}")
        time.sleep(0.1)  # Simulate connection time

        # TODO: Set up connection pool
        # TODO: Update status based on connection success
        # TODO: Return connection success status
        self.connection_pool = [
            {"id": i, "active": False} for i in range(self.config.max_connections)
        ]
        self.status = ProviderStatus.HEALTHY
        return True

    def disconnect(self) -> bool:
        # TODO: Close PostgreSQL connections
        self.connection_pool.clear()
        self.status = ProviderStatus.OFFLINE
        return True

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Execute PostgreSQL query
        # TODO: Handle different query types appropriately
        # TODO: Simulate realistic execution times
        # TODO: Return QueryResult with appropriate data
        execution_time = random.uniform(10, 100) / 1000  # Simulate 10-100ms
        time.sleep(execution_time)
        if "SELECT" in query.upper():
            data = [{"id": 1, "name": "Sample"}]
            return QueryResult(data, execution_time, len(data), True)
        elif any(qt in query.upper() for qt in ["INSERT", "UPDATE", "DELETE"]):
            return QueryResult([], execution_time, 1, True)
        else:
            return QueryResult([], execution_time, 0, False, "Unsupported query type")

    def health_check(self) -> HealthMetrics:
        # TODO: Check PostgreSQL health
        # TODO: Measure response time, connections, etc.
        # TODO: Update self.metrics
        # TODO: Return current metrics
        self.metrics = HealthMetrics(
            response_time_ms=random.uniform(10, 50),
            active_connections=self.get_connection_count(),
            error_rate=random.uniform(0, 0.05),
            cpu_usage=random.uniform(10, 70),
            memory_usage=random.uniform(20, 80),
            last_updated=datetime.now(),
        )
        return self.metrics

    def get_optimal_query_types(self) -> List[QueryType]:
        # TODO: Return query types PostgreSQL handles well
        # Hint: PostgreSQL is good for OLTP operations
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]


class MongoDBProvider(DatabaseProvider):
    """MongoDB implementation - Concrete Implementation"""

    def connect(self) -> bool:
        # TODO: Implement MongoDB connection logic
        print(f"🍃 MongoDB connecting to {self.config.host}:{self.config.port}")
        time.sleep(0.1)
        self.connection_pool = [
            {"id": i, "active": False} for i in range(self.config.max_connections)
        ]
        self.status = ProviderStatus.HEALTHY
        return True

    def disconnect(self) -> bool:
        # TODO: Close MongoDB connections
        self.connection_pool.clear()
        self.status = ProviderStatus.OFFLINE
        return True

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Execute MongoDB query
        # TODO: Handle document operations
        # TODO: Return appropriate QueryResult
        execution_time = random.uniform(20, 150) / 1000  # Simulate 20-150ms
        time.sleep(execution_time)
        if "find" in query.lower():
            data = [{"_id": "abc123", "field": "value"}]
            return QueryResult(data, execution_time, len(data), True)
        elif any(op in query.lower() for op in ["insert", "update", "delete"]):
            return QueryResult([], execution_time, 1, True)
        else:
            return QueryResult([], execution_time, 0, False, "Unsupported query type")

    def health_check(self) -> HealthMetrics:
        # TODO: Check MongoDB health
        self.metrics = HealthMetrics(
            response_time_ms=random.uniform(20, 70),
            active_connections=self.get_connection_count(),
            error_rate=random.uniform(0, 0.1),
            cpu_usage=random.uniform(15, 75),
            memory_usage=random.uniform(25, 85),
            last_updated=datetime.now(),
        )
        return self.metrics

    def get_optimal_query_types(self) -> List[QueryType]:
        # TODO: Return query types MongoDB handles well
        # Hint: MongoDB is good for aggregations and flexible queries
        return [
            QueryType.SELECT,
            QueryType.INSERT,
            QueryType.UPDATE,
            QueryType.AGGREGATE,
        ]


class RedisProvider(DatabaseProvider):
    """Redis implementation - Concrete Implementation"""

    def connect(self) -> bool:
        # TODO: Implement Redis connection logic
        print(f"🔴 Redis connecting to {self.config.host}:{self.config.port}")
        time.sleep(0.05)  # Redis is faster

        self.connection_pool = [
            {"id": i, "active": False} for i in range(self.config.max_connections)
        ]
        self.status = ProviderStatus.HEALTHY
        return True

    def disconnect(self) -> bool:
        # TODO: Close Redis connections
        self.connection_pool.clear()
        self.status = ProviderStatus.OFFLINE
        return True

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Execute Redis operations
        # TODO: Handle key-value operations
        # TODO: Simulate TTL operations
        execution_time = random.uniform(1, 20) / 1000  # Simulate 1-20ms
        time.sleep(execution_time)
        if any(op in query.lower() for op in ["get", "set", "del"]):
            return QueryResult([], execution_time, 1, True)
        else:
            return QueryResult([], execution_time, 0, False, "Unsupported query type")

    def health_check(self) -> HealthMetrics:
        # TODO: Check Redis health
        self.metrics = HealthMetrics(
            response_time_ms=random.uniform(1, 10),
            active_connections=self.get_connection_count(),
            error_rate=random.uniform(0, 0.02),
            cpu_usage=random.uniform(5, 50),
            memory_usage=random.uniform(10, 60),
            last_updated=datetime.now(),
        )
        return self.metrics

    def get_optimal_query_types(self) -> List[QueryType]:
        # TODO: Return query types Redis handles well
        # Hint: Redis excels at cache operations
        return [QueryType.CACHE_GET, QueryType.CACHE_SET]


# ===== ABSTRACTION LAYER (Bridge Abstraction Side) =====


class DatabaseConnection(ABC):
    """Abstract database connection - the Abstraction in Bridge pattern"""

    def __init__(self, provider: DatabaseProvider):
        self.provider = provider
        self.transaction_active = False

    @abstractmethod
    def query(self, sql: str, params: Dict[str, Any] = None) -> QueryResult:
        """Execute a query appropriate for this connection type"""
        pass

    @abstractmethod
    def batch_operation(
        self, operations: List[Tuple[str, Dict[str, Any]]]
    ) -> List[QueryResult]:
        """Execute multiple operations efficiently"""
        pass

    def get_provider_metrics(self) -> HealthMetrics:
        """Get current provider health metrics"""
        return self.provider.health_check()


class TransactionalDatabase(DatabaseConnection):
    """OLTP database operations - Refined Abstraction"""

    def query(self, sql: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Handle transactional queries
        # TODO: Ensure ACID properties
        # TODO: Add transaction management
        if self.transaction_active:
            print("Transaction already active.")
        else:
            try:
                self.begin_transaction()
                result = self.provider.execute_query(sql, params)
                self.commit_transaction()
                return result
            except Exception as e:
                self.rollback_transaction()
                return QueryResult([], 0, 0, False, str(e))

    def batch_operation(
        self, operations: List[Tuple[str, Dict[str, Any]]]
    ) -> List[QueryResult]:
        # TODO: Execute operations in transaction
        # TODO: Handle rollback on failure
        results = []
        try:
            self.begin_transaction()
            for sql, params in operations:
                result = self.provider.execute_query(sql, params)
                results.append(result)
                if not result.success:
                    raise Exception(result.error_message)
            self.commit_transaction()
            return results
        except Exception as e:
            self.rollback_transaction()
            return [QueryResult([], 0, 0, False, str(e)) for _ in operations]

    def begin_transaction(self):
        # TODO: Start transaction
        self.transaction_active = True
        print("Transaction started.")

    def commit_transaction(self):
        # TODO: Commit transaction
        self.transaction_active = False
        print("Transaction committed.")

    def rollback_transaction(self):
        # TODO: Rollback transaction
        self.transaction_active = False
        print("Transaction rolled back.")


class AnalyticsDatabase(DatabaseConnection):
    """OLAP database operations - Refined Abstraction"""

    def query(self, sql: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Handle analytical queries
        # TODO: Optimize for read-heavy operations
        # TODO: Handle complex aggregations
        return self.provider.execute_query(sql, params)

    def batch_operation(
        self, operations: List[Tuple[str, Dict[str, Any]]]
    ) -> List[QueryResult]:
        # TODO: Execute batch analytics operations
        results = []
        for sql, params in operations:
            result = self.provider.execute_query(sql, params)
            results.append(result)
        return results

    def aggregate_query(self, collection: str, pipeline: List[Dict]) -> QueryResult:
        # TODO: Execute aggregation pipeline
        # TODO: Optimize for large datasets
        return self.provider.execute_query(f"AGGREGATE on {collection} with {pipeline}")


class CacheDatabase(DatabaseConnection):
    """Cache operations - Refined Abstraction"""

    def query(self, sql: str, params: Dict[str, Any] = None) -> QueryResult:
        # TODO: Handle cache queries (get/set/delete)
        return self.provider.execute_query(sql, params)

    def batch_operation(
        self, operations: List[Tuple[str, Dict[str, Any]]]
    ) -> List[QueryResult]:
        # TODO: Execute batch cache operations
        results = []
        for sql, params in operations:
            result = self.provider.execute_query(sql, params)
            results.append(result)
        return results

    def set_with_ttl(self, key: str, value: Any, ttl_seconds: int) -> bool:
        # TODO: Set cache value with TTL
        sql = f"SET {key} {value} EX {ttl_seconds}"
        result = self.provider.execute_query(sql)
        return result.success

    def get_or_default(self, key: str, default: Any = None) -> Any:
        # TODO: Get cache value or return default
        sql = f"GET {key}"
        result = self.provider.execute_query(sql)
        if result.success and result.data:
            return result.data[0]
        return default


# ===== ENTERPRISE FEATURES =====


class HealthMonitor:
    """Monitor database provider health"""

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.providers: List[DatabaseProvider] = []
        self.is_monitoring = False
        self.monitor_thread = None

    def add_provider(self, provider: DatabaseProvider):
        # TODO: Add provider to monitoring list
        self.providers.append(provider)

    def start_monitoring(self):
        # TODO: Start health check monitoring in background thread
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()
            print("Health monitoring started.")
        else:
            print("Health monitoring already running.")

    def stop_monitoring(self):
        # TODO: Stop monitoring thread
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
            print("Health monitoring stopped.")
        else:
            print("Health monitoring is not running.")

    def _monitor_loop(self):
        # TODO: Continuously monitor provider health
        # TODO: Update provider status based on metrics
        # TODO: Trigger alerts when thresholds exceeded
        while self.is_monitoring:
            for provider in self.providers:
                metrics = provider.health_check()
                print(f"[{provider.provider_id}] Health Check: {metrics}")
                # Simple status update logic
                if metrics.error_rate > 0.1 or metrics.response_time_ms > 200:
                    provider.status = ProviderStatus.DEGRADED
                else:
                    provider.status = ProviderStatus.HEALTHY
            time.sleep(self.check_interval)

    def get_provider_status(self, provider_id: str) -> ProviderStatus:
        # TODO: Return current status of specific provider
        for provider in self.providers:
            if provider.provider_id == provider_id:
                return provider.status
        return ProviderStatus.OFFLINE


class DatabaseCluster:
    """Manage cluster of database providers with failover"""

    def __init__(
        self, primary: DatabaseProvider, secondaries: List[DatabaseProvider] = None
    ):
        self.primary = primary
        self.secondaries = secondaries or []
        self.current_active = primary
        self.health_monitor = HealthMonitor()

        for provider in [self.primary] + self.secondaries:
            self.health_monitor.add_provider(provider)

    def add_secondary(self, provider: DatabaseProvider):
        # TODO: Add secondary provider
        self.secondaries.append(provider)
        self.health_monitor.add_provider(provider)

    def check_and_failover(self) -> bool:
        # TODO: Check primary health
        # TODO: Switch to secondary if primary unhealthy
        # TODO: Return True if failover occurred
        if self.current_active.status != ProviderStatus.HEALTHY:
            print(
                f"Failover: {self.current_active.provider_id} is {self.current_active.status}"
            )
            for secondary in self.secondaries:
                if secondary.status == ProviderStatus.HEALTHY:
                    self.current_active = secondary
                    print(f"Switched to secondary: {secondary.provider_id}")
                    return True
            print("No healthy secondary available for failover.")
        return False

    def get_active_provider(self) -> DatabaseProvider:
        # TODO: Return currently active provider
        return self.current_active

    def manual_failover(self, target_provider_id: str) -> bool:
        # TODO: Manually switch to specific provider
        for provider in [self.primary] + self.secondaries:
            if (
                provider.provider_id == target_provider_id
                and provider.status == ProviderStatus.HEALTHY
            ):
                self.current_active = provider
                print(f"Manually switched to: {provider.provider_id}")
                return True
        print(f"Provider {target_provider_id} not found or unhealthy.")
        return False


class DatabaseRouter:
    """Smart routing based on query types and provider performance"""

    def __init__(self):
        self.providers: Dict[str, DatabaseProvider] = {}
        self.routing_rules: Dict[QueryType, List[str]] = defaultdict(list)
        self.performance_history: Dict[str, List[float]] = defaultdict(list)

    def register_provider(self, provider: DatabaseProvider):
        # TODO: Register provider and its optimal query types
        self.providers[provider.provider_id] = provider
        for qt in provider.get_optimal_query_types():
            self.routing_rules[qt].append(provider.provider_id)

    def route_query(self, query_type: QueryType, query: str) -> DatabaseProvider:
        # TODO: Select best provider for query type
        # TODO: Consider current load and performance
        # TODO: Return optimal provider
        candidates = self.routing_rules.get(query_type, [])
        healthy_candidates = [
            p for p in candidates if self.providers[p].status == ProviderStatus.HEALTHY
        ]
        if healthy_candidates:
            selected_id = random.choice(healthy_candidates)
            return self.providers[selected_id]
        elif candidates:
            selected_id = random.choice(candidates)
            return self.providers[selected_id]
        else:
            raise Exception(f"No providers available for query type: {query_type}")

    def update_performance_metrics(self, provider_id: str, execution_time: float):
        # TODO: Track provider performance over time
        self.performance_history[provider_id].append(execution_time)

    def get_best_provider_for_type(
        self, query_type: QueryType
    ) -> Optional[DatabaseProvider]:
        # TODO: Analyze performance history
        # TODO: Return best performing provider for query type
        candidates = self.routing_rules.get(query_type, [])
        if not candidates:
            return None

        best_provider = min(
            candidates,
            key=lambda pid: (
                sum(self.performance_history[pid]) / len(self.performance_history[pid])
                if self.performance_history[pid]
                else float("inf")
            ),
        )
        return self.providers[best_provider]


# ===== DEMO SETUP =====


def create_sample_configs() -> Dict[str, DatabaseConfig]:
    """Create sample database configurations"""
    return {
        "postgres_primary": DatabaseConfig(
            host="postgres-primary.example.com",
            port=5432,
            database="financial_db",
            username="app_user",
            password="secure_pass",
            max_connections=20,
        ),
        "postgres_secondary": DatabaseConfig(
            host="postgres-secondary.example.com",
            port=5432,
            database="financial_db",
            username="app_user",
            password="secure_pass",
            max_connections=15,
        ),
        "mongodb": DatabaseConfig(
            host="mongodb.example.com",
            port=27017,
            database="analytics_db",
            username="mongo_user",
            password="mongo_pass",
            max_connections=25,
        ),
        "redis": DatabaseConfig(
            host="redis.example.com",
            port=6379,
            database="0",
            username="",
            password="redis_pass",
            max_connections=50,
        ),
    }


def main():
    """
    TODO: Implement comprehensive demo that shows:
    1. Setting up providers and connections
    2. Normal operations across different database types
    3. Health monitoring and metrics collection
    4. Failover scenarios
    5. Smart routing based on query types
    6. Performance metrics and optimization
    """

    print("=== Enterprise Database Bridge Pattern Demo ===\n")

    # TODO: Create providers
    configs = create_sample_configs()

    # TODO: Set up monitoring
    primary_pg = PostgreSQLProvider(configs["postgres_primary"], "PostgresPrimary")
    secondary_pg = PostgreSQLProvider(
        configs["postgres_secondary"], "PostgresSecondary"
    )
    mongo = MongoDBProvider(configs["mongodb"], "MongoDB")
    redis = RedisProvider(configs["redis"], "RedisCache")

    primary_pg.connect()
    secondary_pg.connect()
    mongo.connect()
    redis.connect()

    cluster = DatabaseCluster(primary_pg, [secondary_pg])
    monitor = cluster.health_monitor
    monitor.start_monitoring()
    time.sleep(1)  # Allow some time for initial health checks

    # TODO: Create database connections (Transactional, Analytics, Cache)
    transactional_db = TransactionalDatabase(cluster.get_active_provider())
    analytics_db = AnalyticsDatabase(mongo)
    cache_db = CacheDatabase(redis)

    # TODO: Demonstrate normal operations
    print("\n--- Normal Operations ---")
    result = transactional_db.query("SELECT * FROM accounts WHERE id = 1")
    print(f"Transactional Query Result: {result}")
    result = analytics_db.query("find users with age > 30")
    print(f"Analytics Query Result: {result}")
    cache_db.set_with_ttl("session_123", {"user_id": 1}, 300)
    cached_value = cache_db.get_or_default("session_123")
    print(f"Cached Value: {cached_value}")
    time.sleep(1)  # Allow some time for health checks

    # TODO: Simulate failover scenario
    print("\n--- Simulating Failover ---")
    primary_pg.status = ProviderStatus.UNHEALTHY  # Simulate primary failure
    cluster.check_and_failover()
    transactional_db.provider = cluster.get_active_provider()
    result = transactional_db.query("SELECT * FROM accounts WHERE id = 2")
    print(f"Post-Failover Transactional Query Result: {result}")
    time.sleep(1)  # Allow some time for health checks

    # TODO: Show smart routing in action
    print("\n--- Smart Routing ---")
    router = DatabaseRouter()
    for provider in [primary_pg, secondary_pg, mongo, redis]:
        router.register_provider(provider)

    for qt in [QueryType.SELECT, QueryType.INSERT, QueryType.CACHE_GET]:
        provider = router.route_query(qt, "Sample Query")
        print(f"Routed {qt.value} query to provider: {provider.provider_id}")
        result = provider.execute_query("Sample Query")
        router.update_performance_metrics(provider.provider_id, result.execution_time)
        print(f"Query Result: {result}")
    time.sleep(1)  # Allow some time for health checks

    # TODO: Display performance metrics
    print("\n--- Performance Metrics ---")
    for provider_id, times in router.performance_history.items():
        avg_time = sum(times) / len(times) if times else 0
        print(
            f"Provider {provider_id} - Avg Execution Time: {avg_time:.2f}s over {len(times)} queries"
        )

    # Cleanup
    monitor.stop_monitoring()
    primary_pg.disconnect()
    secondary_pg.disconnect()
    mongo.disconnect()
    redis.disconnect()


if __name__ == "__main__":
    main()
