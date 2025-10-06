# Design Patterns Repository

Welcome to the **Design Patterns Repository**! This repository serves as a comprehensive guide and reference for understanding and implementing various software design patterns.

## Table of Contents
1. [Introduction](#introduction)
2. [What are Design Patterns?](#what-are-design-patterns)
3. [Categories of Design Patterns](#categories-of-design-patterns)
    - [Creational Patterns](#creational-patterns)
    - [Structural Patterns](#structural-patterns)
    - [Behavioral Patterns](#behavioral-patterns)
4. [How to Use This Repository](#how-to-use-this-repository)
5. [Contributing](#contributing)
6. [License](#license)

---

## Introduction

Design patterns are proven solutions to common software design problems. They provide a template for writing code that is reusable, maintainable, and scalable. This repository contains examples and explanations of various design patterns to help developers improve their coding practices.

---

## What are Design Patterns?

Design patterns are typical solutions to recurring problems in software design. They are not finished designs but templates that can be adapted to solve specific problems in different contexts.

---

## Categories of Design Patterns

### Creational Patterns
Creational patterns deal with object creation mechanisms, trying to create objects in a manner suitable to the situation. Examples include:
- Factory Method
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./creational/01-factory-method/main.py)                                          |
    | Message Queue         | [message_queue.py](./creational/01-factory-method/message_queue.py)                        |
    | Document Exporter     | [document_exporter.py](./creational/01-factory-method/document_exporter.py)                |
    | Data Exporter         | [data_exporter.py](./creational/01-factory-method/exporter/data_exporter.py)               |
- Abstract Factory
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./creational/02-abstract-factory/main.py)                                        |
    | Cloud Provisioning    | [cloud_provisioning.py](./creational/02-abstract-factory/cloud_provisioning.py)            |
    | Data Processing       | [data_processing.py](./creational/02-abstract-factory/data_processing.py)                  |
- Builder
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./creational/03-builder/main.py)                                                 |
    | Query Builder         | [query_builder.py](./creational/03-builder/query_builder.py)                               |
    | API Request Builder   | [api_request_builder.py](./creational/03-builder/api_request_builder.py)                   |
    | Server Config Builder | [server_configuration_builder.py](./creational/03-builder/server_configuration_builder.py) |
- Prototype
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./creational/04-prototype/main.py)                                               |
    | Template BluePrint    | [template_blueprint.py](./creational/04-prototype/template_blueprint.py)                   |
    | Service Configuration | [service_configuration.py](./creational/04-prototype/service_configuration.py)             |
    | Lazy Configuration    | [lazy_configuration.py](./creational/04-prototype/lazy_configuration.py)                   |
- Singleton
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./creational/05-singleton/main.py)                                               |
    | Log Bus               | [log_bus.py](./creational/05-singleton/log_bus.py)                                         |
    | Connection Pool       | [connection_pool.py](./creational/05-singleton/connection_pool.py)                         |
    | Application Bootstrap | [application_bootstrap.py](./creational/05-singleton/application_bootstrap.py)             |

### Structural Patterns
Structural patterns focus on the composition of classes and objects. Examples include:
- Adapter
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/01-adapter/main.py)                                                 |
    | Data Processing       | [data_processing.py](./structural/01-adapter/data_processing.py)                           |
- Bridge
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/02-bridge/main.py)                                                  |
    | Payment Gateway       | [payment_gateway.py](./structural/02-bridge/payment_gateway.py)                            |
    | Notification Sender   | [notification_sender.py](./structural/02-bridge/notification_sender.py)                    |
    | Database Provider     | [database_provider.py](./structural/02-bridge/database_provider.py)                        |
- Composite
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/03-composite/main.py)                                               |
    | Math Expression       | [mathematical_expression.py](./structural/03-composite/mathematical_expression.py)         |
    | Task Management       | [task_management.py](./structural/03-composite/task_management.py)                         |
- Decorator
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/04-decorator/main.py)                                               |
    | Service Decorator     | [service_decorator.py](./structural/04-decorator/service_decorator.py)                     |
    | Request Client        | [request_client.py](./structural/04-decorator/request_client.py)                           |
    | Payment Processor     | [payment_processor.py](./structural/04-decorator/payment_processor.py)                     |
    | Logging System        | [logging_system.py](./structural/04-decorator/logging_system.py)                           |
- Facade
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/05-facade/main.py)                                                  |
    | System Deployment     | [system_deployment.py](./structural/05-facade/system_deployment.py)                        |
    | Data Store            | [data_store.py](./structural/05-facade/data_store.py)                                      |
    | API Gateway           | [api_gateway.py](./structural/05-facade/api_gateway.py)                                    |
- Flyweight
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/06-flyweight/main.py)                                               |
    | Particle System       | [partical_system.py](./structural/06-flyweight/partical_system.py)                         |
    | Cache Manager         | [cache_manager.py](./structural/06-flyweight/cache_manager.py)                             |
- Proxy
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./structural/07-proxy/main.py)                                                   |
    | Fibonacci Calculator  | [fibonacci_calculator.py](./structural/07-proxy/fibonacci_calculator.py)                   |
    | Dynamic Proxies       | [dynamic_proxies.py](./structural/07-proxy/dynamic_proxies.py)                             |
    | Security Proxy        | [security_proxy.py](./structural/07-proxy/security_proxy.py)                               |

### Behavioral Patterns
Behavioral patterns are concerned with communication between objects. Examples include:
- Chain of Responsibility
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/01-chain-of-responsibility/main.py)                                 |
    | Payment Gateway       | [payment_gateway.py](./behavioral/01-chain-of-responsibility/payment_gateway.py)           |
    | Chain Builder         | [chain_builder.py](./behavioral/01-chain-of-responsibility/chain_builder.py)               |
    | Request Validator     | [request_validator.py](./behavioral/01-chain-of-responsibility/request_validator.py)       |
    | Content Processor     | [content_processor.py](./behavioral/01-chain-of-responsibility/content_processor.py)       |
- Command
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/02-command/main.py)                                                 |
    | Smart Home            | [smart_home.py](./behavioral/02-command/smart_home.py)                                     |
    | Scheduler             | [scheduler.py](./behavioral/02-command/scheduler.py)                                       |
    | Command Bus           | [command_bus.py](./behavioral/02-command/command_bus.py)                                   |
    | Database Transaction  | [database_transaction.py](./behavioral/02-command/database_transaction.py)                 |
- Iterator
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/03-iterator/main.py)                                                |
    | Book Shelf            | [book_shelf.py](./behavioral/03-iterator/book_shelf.py)                                    |
    | Binary Tree           | [binary_tree.py](./behavioral/03-iterator/binary_tree.py)                                  |
    | Log Analyzer          | [log_analyzer.py](./behavioral/03-iterator/log_analyzer.py)                                |
    | API Paginated         | [api_paginated.py](./behavioral/03-iterator/api_paginated.py)                              |
- Mediator
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/04-mediator/main.py)                                                |
    | Chat Room             | [chat_room.py](./behavioral/04-mediator/chat_room.py)                                      |
    | Smart Home            | [smart_home.py](./behavioral/04-mediator/smart_home.py)                                    |
    | Service Orchestrator  | [service_orchestrator.py](./behavioral/04-mediator/service_orchestrator.py)                |
- Memento
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/05-memento/main.py)                                                 |
    | Text Buffer           | [text_buffer.py](./behavioral/05-memento/text_buffer.py)                                   |
    | Config Manager        | [config_manager.py](./behavioral/05-memento/config_manager.py)                             |
    | Transaction Manager   | [transaction_manager.py](./behavioral/05-memento/transaction_manager.py)                   |
- Observer
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/06-observer/main.py)                                                |
    | Event Bus             | [event_bus.py](./behavioral/06-observer/event_bus.py)                                      |
    | Domain Event          | [domain_event.py](./behavioral/06-observer/domain_event.py)                                |
    | Stock Alert           | [stock_alert.py](./behavioral/06-observer/stock_alert.py)                                  |
    | Service Monitor       | [service_monitor.py](./behavioral/06-observer/service_monitor.py)                          |
- State
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/07-state/main.py)                                                   |
    | Order Workflow        | [order_workflow.py](./behavioral/07-state/order_workflow.py)                               |
    | Document Workflow     | [document_workflow.py](./behavioral/07-state/document_workflow.py)                         |
- Strategy
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/08-strategy/main.py)                                                |
    | Shipping Cost         | [shipping_cost.py](./behavioral/08-strategy/shipping_cost.py)                              |
    | Pricing Engine        | [pricing_engine.py](./behavioral/08-strategy/pricing_engine.py)                            |
- Template Method
    | Exercise              | Code                                                                                       |
    |-----------------------|--------------------------------------------------------------------------------------------|
    | Basic Example         | [main.py](./behavioral/09-template-method/main.py)                                         |
    | Data Pipeline         | [data_pipeline.py](./behavioral/09-template-method/data_pipeline.py)                       |
    | Order Processor       | [order_processor.py](./behavioral/09-template-method/order_processor.py)                   |
- Interpreter
- Visitor

---

## How to Use This Repository

1. Clone the repository:
    ```bash
    git clone https://github.com/duthaho/python-design-patterns.git
    ```
2. Navigate to the pattern of interest in the directory structure.
3. Read the explanation and review the code examples provided.
4. Experiment with the code to understand how the pattern works.

---

## Contributing

Contributions are welcome! If you have improvements or new patterns to add, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Commit your changes and push them to your fork.
4. Submit a pull request with a detailed description of your changes.

---

## License

This repository is licensed under the [MIT License](LICENSE). Feel free to use the code and examples in your own projects.

---

Happy coding!