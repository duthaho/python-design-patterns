"""
Intent:
Ensure a class has only one instance, and provide a global point of access to it.

Problem:
Sometimes, you want to have exactly one instance of a class, and you want to provide a global
access point to that instance. This is useful when exactly one object is needed to coordinate
actions across the system. Examples include a configuration manager, a logging class, or a
connection pool.

Solution:
The Singleton pattern restricts the instantiation of a class to one "single" instance. This
is done by making the class itself responsible for keeping track of its sole instance. The class
provides a static method that allows clients to access the instance. If the instance does not
exist yet, the class creates it. On subsequent calls, the class returns the existing instance.
The Singleton pattern can be implemented in several ways, including lazy initialization,
eager initialization, and using a static inner class. The choice of implementation depends on
the specific requirements of the application, such as thread safety and performance.

When to use:
- When exactly one instance of a class is needed, and it must be accessible to clients from
    a well-known access point.
- When the sole instance should be extensible by subclassing, and clients should be able to
    use an extended instance without modifying their code.
- When you want to control access to a shared resource, such as a database or a file.

How to implement:
1. Make the class constructor private to prevent direct instantiation.
2. Create a static method that returns the sole instance of the class. This method should
    create the instance if it does not already exist.
3. Ensure that the instance is stored in a static variable within the class.
4. If the class is intended to be used in a multi-threaded environment, ensure that the
    instance creation is thread-safe.
5. Optionally, implement a method to reset or destroy the instance if needed.

Pros and Cons:
+ Controlled access to the sole instance.
+ Reduced namespace pollution since the singleton instance is accessed through a
    well-known access point.
+ Can be extended by subclassing.
- Can introduce global state into an application, making it harder to reason about.
- Can make unit testing difficult due to the global state.
- Can lead to issues in multi-threaded environments if not implemented correctly.
- Can be overused, leading to unnecessary complexity in the codebase.

Real-world use cases:
- The logging class in many applications is often implemented as a singleton to ensure that
    all log messages are written to the same log file.
- Configuration managers are typically singletons to provide a single source of configuration
    settings throughout an application.
- Connection pools are often implemented as singletons to manage a shared pool of database
    connections.
- The Java Runtime Environment (JRE) uses the Singleton pattern for the `Runtime` class,
    which provides a single instance to interact with the Java runtime system.
- The `java.lang.System` class in Java is a singleton that provides access to system
    properties and standard input/output streams.
"""

# Link: https://refactoring.guru/design-patterns/singleton

import threading, time


# Using a metaclass to implement Singleton pattern
class SingletonMeta(type):
    _instance = None
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Logger(metaclass=SingletonMeta):
    def log(self, message: str) -> None:
        print(f"[LOG]: {message}")


# Using __new__ method to implement Singleton pattern
class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance


class Logger(Singleton):
    def log(self, message: str) -> None:
        print(f"[LOG]: {message}")


# Decorator-based Singleton
def singleton(cls):
    instances = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Logger:
    def log(self, message: str) -> None:
        print(f"[LOG]: {message}")


if __name__ == "__main__":
    # The client code.
    def create_logger_instance(index: int) -> None:
        logger = Logger()
        logger.log(f"Logger instance from thread {index}: {id(logger)}")
        time.sleep(0.1)

    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_logger_instance, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Verify that all instances are the same
    print("\nVerifying singleton instances:")
    print(
        "All logger instances are the same:",
        all(Logger() is Logger() for _ in range(5)),
    )
