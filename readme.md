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
- Proxy

### Behavioral Patterns
Behavioral patterns are concerned with communication between objects. Examples include:
- Chain of Responsibility
- Command
- Interpreter
- Iterator
- Mediator
- Memento
- Observer
- State
- Strategy
- Template Method
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