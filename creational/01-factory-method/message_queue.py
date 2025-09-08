from abc import ABC, abstractmethod
from typing import Dict, Type

import random


class QueueConfig:
    def __init__(self, queue_type: str, host: str, port: int, username: str, password: str):
        self.queue_type = queue_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class MessageQueue(ABC):
    def __init__(self, config: QueueConfig):
        self.config = config

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def send_message(self, message: str) -> None:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass


class RabbitMQ(MessageQueue):
    def connect(self) -> None:
        print(f"Connecting to RabbitMQ at {self.config.host}:{self.config.port}...")

    def send_message(self, message: str) -> None:
        print(f"Sending message to RabbitMQ: {message}")

    def health_check(self) -> bool:
        print("Performing RabbitMQ health check...")
        return random.choice([True, False])
    

class Kafka(MessageQueue):
    def connect(self) -> None:
        print(f"Connecting to Kafka at {self.config.host}:{self.config.port}...")

    def send_message(self, message: str) -> None:
        print(f"Sending message to Kafka: {message}")

    def health_check(self) -> bool:
        print("Performing Kafka health check...")
        return random.choice([True, False])
    

class AWSQueue(MessageQueue):
    def connect(self) -> None:
        print(f"Connecting to AWS SQS at {self.config.host}:{self.config.port}...")

    def send_message(self, message: str) -> None:
        print(f"Sending message to AWS SQS: {message}")

    def health_check(self) -> bool:
        print("Performing AWS SQS health check...")
        return random.choice([True, False])
    

class MessageQueueFactory:
    def __init__(self):
        self.pool: Dict[str, MessageQueue] = {}
        self.registry: Dict[str, Type[MessageQueue]] = {}

    def register_queue(self, queue_type: str, queue_cls: Type[MessageQueue]) -> None:
        self.registry[queue_type] = queue_cls
        
    def create_queue(self, config: QueueConfig) -> MessageQueue:
        config_key = f"{config.queue_type}:{config.host}:{config.port}:{config.username}:{config.password}"
        if config_key not in self.pool:
            queue_cls = self.registry.get(config.queue_type)
            if not queue_cls:
                available = ', '.join(self.registry.keys())
                raise ValueError(f"Queue type '{config.queue_type}' is not supported. Available types: {available}")
        
            self.pool[config_key] = queue_cls(config)
        return self.pool[config_key]
    
# Client code
def main() -> None:
    factory = MessageQueueFactory()
    
    # Register available queue types
    factory.register_queue("rabbitmq", RabbitMQ)
    factory.register_queue("kafka", Kafka)
    factory.register_queue("aws", AWSQueue)
    
    # Example configurations
    configs = [
        QueueConfig("rabbitmq", "localhost", 5672, "user", "pass"),
        QueueConfig("kafka", "localhost", 9092, "user", "pass"),
        QueueConfig("aws", "sqs.us-east-1.amazonaws.com", 443, "user", "pass"),
    ]
    
    for config in configs:
        try:
            queue = factory.create_queue(config)
            queue.connect()
            if queue.health_check():
                queue.send_message("Hello, World!")
            else:
                print(f"Health check failed for {config.queue_type}.")
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    main()
