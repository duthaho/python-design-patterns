import hashlib
import json
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueType(Enum):
    """Enumeration of supported queue types."""

    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    AWS_SQS = "aws_sqs"
    REDIS = "redis"

    @classmethod
    def to_list() -> list[str]:
        return [qt.value for qt in QueueType]


@dataclass
class QueueConfig:
    """Configuration object for message queues with validation."""

    queue_type: str
    host: str
    port: int
    username: str
    password: str
    ssl_enabled: bool = False
    timeout: int = 30
    max_connections: int = 10
    additional_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        # TODO: Implement validation logic
        # - Validate port is in valid range (1-65535)
        # - Validate required fields are not empty
        # - Validate queue_type is supported
        errors = []
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535).")
        if not self.host:
            errors.append("Host cannot be empty.")
        if self.queue_type not in QueueType.to_list():
            errors.append(
                f"Unsupported queue type: {self.queue_type}. Supported types: {QueueType.to_list()}"
            )
        if errors:
            raise ConfigurationError("Invalid QueueConfig: " + "; ".join(errors))

    def get_connection_key(self) -> str:
        """Generate unique key for connection pooling."""
        # TODO: Create a unique hash key based on connection parameters
        # Hint: Use relevant config fields to create a unique identifier
        # Consider: host, port, username, queue_type, ssl_enabled
        key_data = {
            "queue_type": self.queue_type,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "ssl_enabled": self.ssl_enabled,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()


class ConnectionError(Exception):
    """Custom exception for connection failures."""

    pass


class ConfigurationError(Exception):
    """Custom exception for configuration issues."""

    pass


class MessageQueue(ABC):
    """Abstract base class for all message queue implementations."""

    def __init__(self, config: QueueConfig):
        self.config = config
        self._connected = False
        self._connection_attempts = 0
        self.max_retries = 3

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the message queue."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the message queue."""
        pass

    @abstractmethod
    def send_message(self, message: str, queue_name: str = "default") -> bool:
        """Send message to specified queue."""
        pass

    @abstractmethod
    def receive_message(self, queue_name: str = "default") -> Optional[str]:
        """Receive message from specified queue."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the connection is healthy."""
        pass

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._connected

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "queue_type": self.config.queue_type,
            "host": self.config.host,
            "port": self.config.port,
            "connected": self._connected,
            "ssl_enabled": self.config.ssl_enabled,
        }


class RabbitMQQueue(MessageQueue):
    """RabbitMQ implementation."""

    def connect(self) -> None:
        # TODO: Implement RabbitMQ connection logic
        # - Log connection attempt
        # - Simulate connection (print connection details)
        # - Set _connected = True on success
        # - Handle connection failures with retries
        logger.info(
            f"Connecting to RabbitMQ at {self.config.host}:{self.config.port} with user {self.config.username}"
        )
        while self._connection_attempts < self.max_retries:
            self._connection_attempts += 1
            if random.choice([True, False]):  # Simulate random success/failure
                self._connected = True
                logger.info("Successfully connected to RabbitMQ")
                return
            else:
                logger.warning(f"Connection attempt {self._connection_attempts} failed")
        raise ConnectionError("Failed to connect to RabbitMQ after multiple attempts")

    def disconnect(self) -> None:
        # TODO: Implement disconnection
        if self._connected:
            logger.info("Disconnecting from RabbitMQ")
            self._connected = False
        else:
            logger.warning("Attempted to disconnect when not connected")

    def send_message(self, message: str, queue_name: str = "default") -> bool:
        # TODO: Implement message sending
        # - Check if connected first
        # - Log message sending
        # - Return success/failure
        if not self._connected:
            logger.error("Cannot send message: Not connected to RabbitMQ")
            return False
        logger.info(f"Sending message to RabbitMQ queue '{queue_name}': {message}")
        return True  # Simulate success

    def receive_message(self, queue_name: str = "default") -> Optional[str]:
        # TODO: Implement message receiving
        if not self._connected:
            logger.error("Cannot receive message: Not connected to RabbitMQ")
            return None
        logger.info(f"Receiving message from RabbitMQ queue '{queue_name}'")
        return "Simulated message from RabbitMQ"  # Simulate received message

    def health_check(self) -> bool:
        # TODO: Implement health check
        # - Check connection status
        # - Maybe simulate a ping operation
        return self._connected and random.choice(
            [True, False]
        )  # Simulate occasional failure


class KafkaQueue(MessageQueue):
    """Kafka implementation."""

    def connect(self) -> None:
        # TODO: Similar to RabbitMQ but with Kafka-specific logic
        pass

    def disconnect(self) -> None:
        # TODO: Implement
        pass

    def send_message(self, message: str, queue_name: str = "default") -> bool:
        # TODO: Implement
        pass

    def receive_message(self, queue_name: str = "default") -> Optional[str]:
        # TODO: Implement
        pass

    def health_check(self) -> bool:
        # TODO: Implement
        pass


class AWSQueueSQS(MessageQueue):
    """AWS SQS implementation."""

    def connect(self) -> None:
        # TODO: Implement AWS SQS connection
        pass

    def disconnect(self) -> None:
        # TODO: Implement
        pass

    def send_message(self, message: str, queue_name: str = "default") -> bool:
        # TODO: Implement
        pass

    def receive_message(self, queue_name: str = "default") -> Optional[str]:
        # TODO: Implement
        pass

    def health_check(self) -> bool:
        # TODO: Implement
        pass


class RedisQueue(MessageQueue):
    """Redis implementation."""

    def connect(self) -> None:
        # TODO: Implement Redis connection
        pass

    def disconnect(self) -> None:
        # TODO: Implement
        pass

    def send_message(self, message: str, queue_name: str = "default") -> bool:
        # TODO: Implement
        pass

    def receive_message(self, queue_name: str = "default") -> Optional[str]:
        # TODO: Implement
        pass

    def health_check(self) -> bool:
        # TODO: Implement
        pass


class MessageQueueFactory:
    """Advanced factory with connection pooling and health monitoring."""

    def __init__(self):
        self._pool: Dict[str, MessageQueue] = {}
        self._registry: Dict[str, Type[MessageQueue]] = {}
        self._health_status: Dict[str, bool] = {}
        self._initialize_default_queues()

    def _initialize_default_queues(self) -> None:
        """Register default queue implementations."""
        # TODO: Register all queue types
        # self.register_queue(QueueType.RABBITMQ.value, RabbitMQQueue)
        # etc...
        self.register_queue(QueueType.RABBITMQ.value, RabbitMQQueue)
        self.register_queue(QueueType.KAFKA.value, KafkaQueue)
        self.register_queue(QueueType.AWS_SQS.value, AWSQueueSQS)
        self.register_queue(QueueType.REDIS.value, RedisQueue)

    def register_queue(self, queue_type: str, queue_class: Type[MessageQueue]) -> None:
        """Register a new queue type."""
        # TODO: Implement registration with validation
        # - Validate queue_class is subclass of MessageQueue
        # - Log registration
        # - Store in registry
        if not issubclass(queue_class, MessageQueue):
            raise ValueError(f"{queue_class} is not a subclass of MessageQueue")
        self._registry[queue_type] = queue_class
        logger.info(
            f"Registered queue type '{queue_type}' with class {queue_class.__name__}"
        )

    def create_queue(self, config: QueueConfig) -> MessageQueue:
        """Create or retrieve queue from pool."""
        # TODO: Implement advanced pooling logic
        # - Validate configuration
        # - Generate connection key
        # - Check if already exists in pool
        # - Create new instance if needed
        # - Update health status
        # - Return queue instance
        if config.queue_type not in self._registry:
            raise ConfigurationError(
                f"Queue type '{config.queue_type}' is not registered."
            )
        key = config.get_connection_key()
        if key in self._pool:
            logger.info(f"Reusing existing connection for key {key}")
            return self._pool[key]
        queue_class = self._registry[config.queue_type]
        queue_instance = queue_class(config)
        queue_instance.connect()
        self._pool[key] = queue_instance
        self._health_status[key] = queue_instance.health_check()
        return queue_instance

    def get_queue_health(self, config: QueueConfig) -> bool:
        """Get health status of a queue."""
        # TODO: Implement health status retrieval
        key = config.get_connection_key()
        return self._health_status.get(key, False)

    def cleanup_unhealthy_connections(self) -> None:
        """Remove unhealthy connections from pool."""
        # TODO: Implement cleanup logic
        # - Check health of all pooled connections
        # - Remove unhealthy ones
        # - Log cleanup actions
        unhealthy_keys = [
            key for key, queue in self._pool.items() if not queue.health_check()
        ]
        for key in unhealthy_keys:
            logger.warning(f"Removing unhealthy connection for key {key}")
            self._pool[key].disconnect()
            del self._pool[key]
            del self._health_status[key]

    def get_pool_status(self) -> Dict[str, Any]:
        """Get status of connection pool."""
        # TODO: Return pool statistics
        # - Number of active connections
        # - Health status summary
        # - Connection details
        status = {
            "total_connections": len(self._pool),
            "healthy_connections": sum(
                1 for healthy in self._health_status.values() if healthy
            ),
            "connections": {
                key: queue.get_connection_info() for key, queue in self._pool.items()
            },
        }
        return status

    def shutdown(self) -> None:
        """Gracefully shutdown all connections."""
        # TODO: Implement graceful shutdown
        # - Disconnect all pooled connections
        # - Clear pool
        # - Log shutdown
        for key, queue in self._pool.items():
            logger.info(f"Shutting down connection for key {key}")
            queue.disconnect()
        self._pool.clear()
        self._health_status.clear()


def main():
    """Demonstration of the enhanced factory pattern."""

    # TODO: Implement comprehensive test cases:

    # 1. Test configuration builder
    config = QueueConfig(
        queue_type=QueueType.RABBITMQ.value,
        host="localhost",
        port=5672,
        username="guest",
        password="guest",
        ssl_enabled=False,
    )

    # 2. Test factory with pooling
    factory = MessageQueueFactory()

    # 3. Test queue creation and operations
    queue = factory.create_queue(config)

    # 4. Test health monitoring
    health = factory.get_queue_health(config)
    print(f"Queue health: {health}")

    # 5. Test connection pooling (same config should return same instance)
    same_queue = factory.create_queue(config)
    print(f"Same instance: {queue is same_queue}")

    # 6. Test error handling
    try:
        bad_config = QueueConfig(
            queue_type="unsupported_queue",
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
        )
        factory.create_queue(bad_config)
    except ConfigurationError as e:
        print(f"Caught expected configuration error: {e}")

    # 7. Test sending and receiving messages
    if queue.is_connected():
        sent = queue.send_message("Hello, World!", "test_queue")
        print(f"Message sent: {sent}")
        message = queue.receive_message("test_queue")
        print(f"Message received: {message}")

    # 8. Print pool status
    status = factory.get_pool_status()
    print(f"Pool status: {status}")

    # 9. Cleanup unhealthy connections
    factory.cleanup_unhealthy_connections()

    # 10. Shutdown factory
    factory.shutdown()

    print("All tests completed!")


if __name__ == "__main__":
    main()
