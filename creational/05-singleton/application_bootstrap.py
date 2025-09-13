import inspect
import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional, Protocol
from unittest.mock import Mock

# ====================
# SINGLETON ANTI-PATTERNS AND ALTERNATIVES
# ====================

# ====================
# PART 1: PROBLEMATIC SINGLETON (Anti-pattern Example)
# ====================


class ProblematicLogger:
    """
    A poorly designed singleton that demonstrates common anti-patterns

    PROBLEMS IDENTIFIED:
    1. Resource Leak: File handle never properly closed in destructor
    2. Thread Safety Issues: File operations not thread-safe
    3. Hard-coded Dependencies: Cannot change log file without modifying code
    4. Testing Nightmare: Always writes to real files
    5. Global State: Shared mutable state across entire application
    6. Hidden Dependencies: Classes using it don't show they need logging
    7. Tight Coupling: Impossible to swap logging implementations
    8. Error Handling: No exception handling for file operations
    9. Configuration Issues: Log level and file path hard-coded
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.log_file = "app.log"
            self.log_level = "INFO"
            self.file_handle = open(self.log_file, "a")
            self._initialized = True

    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.file_handle.write(log_entry)
        self.file_handle.flush()

    def change_log_file(self, new_file: str):
        self.file_handle.close()
        self.log_file = new_file
        self.file_handle = open(self.log_file, "a")

    def __del__(self):
        self.file_handle.close()


# ====================
# PART 2: DEPENDENCY INJECTION ALTERNATIVE
# ====================


class LoggerInterface(Protocol):
    """
    TODO: Define the logger interface using Protocol
    - Define method signatures that any logger should implement
    - Think about what methods a logger needs
    """

    def log(self, message: str, level: str = "INFO") -> None: ...

    def close(self) -> None: ...


class FileLogger(LoggerInterface):
    """
    TODO: Implement a concrete file logger
    - Should implement LoggerInterface
    - Should be easily testable and configurable
    - Should handle file operations safely
    """

    def __init__(self, log_file: str, log_level: str = "INFO"):
        # TODO: Initialize the file logger
        self.log_file = log_file
        self.log_level = log_level
        self.file_handle = None
        self.lock = threading.Lock()

        try:
            self.file_handle = open(self.log_file, "a")
        except Exception as e:
            raise IOError(f"Failed to open log file {self.log_file}: {e}")

    def log(self, message: str, level: str = "INFO"):
        # TODO: Implement logging to file
        if self.file_handle and not self.file_handle.closed:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"
            with self.lock:
                try:
                    self.file_handle.write(log_entry)
                    self.file_handle.flush()
                except Exception as e:
                    raise IOError(f"Failed to write to log file {self.log_file}: {e}")

    def close(self):
        # TODO: Safely close file handles
        if self.file_handle and not self.file_handle.closed:
            with self.lock:
                self.file_handle.close()


class ConsoleLogger(LoggerInterface):
    """
    TODO: Implement a console logger
    - Should implement LoggerInterface
    - Should be useful for development/testing
    """

    def __init__(self, log_level: str = "INFO"):
        # TODO: Initialize console logger
        self.log_level = log_level
        self.lock = threading.Lock()

    def log(self, message: str, level: str = "INFO"):
        # TODO: Implement logging to console
        with self.lock:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {level}: {message}")

    def close(self):
        # TODO: No-op for console logger
        pass


class DatabaseLogger(LoggerInterface):
    """Logger that writes logs to a database (simulated)"""

    def __init__(self, connection_string: str, log_level: str = "INFO"):
        self.connection_string = connection_string
        self.log_level = log_level
        self.lock = threading.Lock()
        self.log_entries = []  # Simulate a database table

    def log(self, message: str, level: str = "INFO"):
        with self.lock:
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": level,
                "message": message,
            }
            self.log_entries.append(log_entry)
            # Simulate database write delay
            time.sleep(0.01)

    def close(self):
        # Simulate closing database connection
        pass


@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str
    max_connections: int = 10


@dataclass
class LoggingConfig:
    level: str = "INFO"
    type: str = "file"  # 'file', 'console', 'database'
    file_path: Optional[str] = "app.log"
    database_connection: Optional[str] = None


@dataclass
class AppConfig:
    debug: bool
    logging: LoggingConfig
    database: DatabaseConfig
    api_key: Optional[str] = None


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""

    pass


class ConfigurationManager:
    """TODO: Implement configuration manager
    - Load configuration from file/environment
    - Validate configuration
    - Provide configuration to other components
    """

    def __init__(self, config_source: Optional[str] = None):
        self.config_source = config_source
        self.config = None

    def load_config(self) -> AppConfig:
        try:
            with open(self.config_source, "r") as f:
                data = json.load(f)

            logging_config = LoggingConfig(**data.get("logging", {}))
            database_config = DatabaseConfig(**data.get("database", {}))

            config = AppConfig(
                debug=data.get("debug", False),
                logging=logging_config,
                database=database_config,
                api_key=data.get("api_key"),
            )

            self.validate_config(config)
            self.config = config

            return self.config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def validate_config(self, config: AppConfig) -> None:
        if config.logging.type == "file" and not config.logging.file_path:
            raise ConfigurationError("File path must be provided for file logger.")
        if config.logging.type == "database" and not config.logging.database_connection:
            raise ConfigurationError(
                "Database connection string must be provided for database logger."
            )
        if not config.database.host or not config.database.port:
            raise ConfigurationError("Database host and port must be specified.")


class DatabaseService:
    """
    TODO: Example service that depends on a logger
    - Should accept logger via dependency injection
    - Should NOT create its own logger singleton
    """

    def __init__(self, logger: LoggerInterface, config: DatabaseConfig):
        self.logger = logger
        self.config = config

    def save_user(self, user_data: dict) -> bool:
        """
        TODO: Simulate saving user data
        - Log the operation
        - Return success/failure
        - Handle exceptions properly
        """
        try:
            self.logger.log(
                f"Saving user data: {user_data} to {self.config.host}:{self.config.port}",
                level="DEBUG",
            )
            # Simulate saving to database
            time.sleep(0.1)  # Simulate delay
            self.logger.log("User data saved successfully.", level="INFO")
            return True
        except Exception as e:
            self.logger.log(f"Error saving user data: {e}", level="ERROR")
            return False

    def get_user(self, user_id: int) -> Optional[dict]:
        """
        TODO: Simulate getting user data
        - Log the operation
        - Return user data or None
        """
        try:
            self.logger.log(
                f"Fetching user data for user_id: {user_id} from {self.config.host}:{self.config.port}",
                level="DEBUG",
            )
            # Simulate fetching from database
            time.sleep(0.1)  # Simulate delay
            user_data = {"id": user_id, "name": "John Doe"}  # Dummy data
            self.logger.log(f"User data retrieved: {user_data}", level="INFO")
            return user_data
        except Exception as e:
            self.logger.log(f"Error fetching user data: {e}", level="ERROR")
            return None


# ====================
# PART 3: DEPENDENCY INJECTION CONTAINER
# ====================


class DIError(Exception):
    """Custom exception for DI container errors"""

    pass


class DIContainer:
    """
    TODO: Implement a simple dependency injection container
    - Should register services and their dependencies
    - Should resolve dependencies automatically
    - Should support singleton and transient lifetimes
    """

    def __init__(self):
        self._services = (
            {}
        )  # interface_type -> (implementation_type, args, kwargs, is_singleton)
        self._singletons = {}  # interface_type -> instance
        self._lock = threading.Lock()

    def register_singleton(self, interface_type, implementation_type, *args, **kwargs):
        """
        TODO: Register a service as singleton
        - Store the implementation type and its constructor args
        - Create instance only when first requested
        """
        with self._lock:
            self._services[interface_type] = (implementation_type, args, kwargs, True)
            self._singletons[interface_type] = None

    def register_transient(self, interface_type, implementation_type, *args, **kwargs):
        """
        TODO: Register a service as transient (new instance each time)
        """
        with self._lock:
            self._services[interface_type] = (implementation_type, args, kwargs, False)

    def register_instance(self, interface_type, instance):
        """
        TODO: Register an existing instance
        - Useful for mock instances in testing
        """
        with self._lock:
            self._services[interface_type] = (lambda: instance, (), {}, True)
            self._singletons[interface_type] = instance

    def resolve(self, interface_type):
        """
        TODO: Resolve a service from the container
        - Return singleton instance if registered as singleton
        - Create new instance if registered as transient
        - Resolve dependencies recursively
        """
        if interface_type not in self._services:
            raise DIError(f"Service {interface_type} not registered.")

        implementation_type, args, kwargs, is_singleton = self._services[interface_type]

        if is_singleton:
            if self._singletons[interface_type] is None:
                if implementation_type is None:
                    raise DIError(
                        f"No implementation type for singleton {interface_type}"
                    )

                with self._lock:
                    if self._singletons[interface_type] is None:
                        # Resolve constructor dependencies
                        resolved_args, resolved_kwargs = self._resolve_dependencies(
                            implementation_type, args, kwargs
                        )
                        self._singletons[interface_type] = implementation_type(
                            *resolved_args, **resolved_kwargs
                        )
            return self._singletons[interface_type]

        if implementation_type is None:
            raise DIError(f"No implementation type for transient {interface_type}")

        # Resolve constructor dependencies
        resolved_args, resolved_kwargs = self._resolve_dependencies(
            implementation_type, args, kwargs
        )
        return implementation_type(*resolved_args, **resolved_kwargs)

    def _resolve_dependencies(self, implementation_type, args, kwargs):
        """Resolve constructor dependencies"""
        resolved_args = list(args)
        resolved_kwargs = dict(kwargs)

        # Get constructor signature
        try:
            sig = inspect.signature(implementation_type.__init__)
            params = list(sig.parameters.values())[1:] if sig else []  # Skip 'self'

            # Resolve dependency for params that have type anotations
            for i, param in enumerate(params):
                # Skip if already provided
                if i < len(resolved_args) or param.name in resolved_kwargs:
                    continue

                # Try to resolve by type annotation
                if param.annotation != inspect.Parameter.empty:
                    try:
                        dependency = self.resolve(param.annotation)
                        if len(resolved_args) <= i:
                            resolved_args.extend([None] * (i - len(resolved_args) + 1))
                        resolved_args[i] = dependency
                    except DIError:
                        # If dependency can't be resolved and no default, raise error
                        if param.default == inspect.Parameter.empty:
                            raise DIError(
                                f"Cannot resolve dependency for parameter '{param.annotation.__name__}' in {implementation_type.__name__}"
                            )
        except Exception as e:
            # If inspection fails, just return original args/kwargs
            pass

        return resolved_args, resolved_kwargs

    def is_registered(self, interface_type) -> bool:
        """Check if a service is registered"""
        return interface_type in self._services

    def clear(self):
        """Clear all registrations and instances"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()


# ====================
# PART 4: MODERN PATTERNS (Factory + DI)
# ====================


class LoggerFactory:
    """
    TODO: Implement a logger factory
    - Create appropriate logger based on configuration
    - Support multiple logger types
    - Return logger instances, not singletons
    """

    @staticmethod
    def create_logger(config: LoggingConfig) -> LoggerInterface:
        """
        TODO: Create logger based on configuration
        - Support 'file', 'console', 'database' types
        - Configure based on provided settings
        """
        if config.type == "file":
            if not config.file_path:
                raise ConfigurationError("File path must be provided for file logger.")
            return FileLogger(config.file_path, config.level)
        elif config.type == "console":
            return ConsoleLogger(config.level)
        elif config.type == "database":
            if not config.database_connection:
                raise ConfigurationError(
                    "Database connection string must be provided for database logger."
                )
            return DatabaseLogger(config.database_connection, config.level)
        raise ConfigurationError(f"Unknown logger type: {config.type}")


class ApplicationBootstrap:
    """
    TODO: Application bootstrap that sets up dependency injection
    - Replace singleton pattern with proper DI
    - Show how to structure application startup
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_manager = ConfigurationManager(config_path)
        self.container = DIContainer()
        self.app_config = None

    def setup_container(self) -> DIContainer:
        """
        TODO: Configure the DI container
        - Register all services
        - Set up dependency graph
        - Configure lifetimes (singleton vs transient)
        """
        # Load configuration first
        self.app_config = self.config_manager.load_config()

        # Register config as singleton instance
        self.container.register_instance(AppConfig, self.app_config)
        self.container.register_instance(DatabaseConfig, self.app_config.database)

        # Register logger factory and logger
        logger = LoggerFactory.create_logger(self.app_config.logging)
        self.container.register_instance(LoggerInterface, logger)

        # Register services as transient
        self.container.register_transient(DatabaseService, DatabaseService)

        # Register factory as singleton
        self.container.register_singleton(LoggerFactory, LoggerFactory)

        return self.container

    def create_application(self) -> "Application":
        """Create the main application instance with dependencies injected"""
        if self.app_config is None:
            self.setup_container()

        # Resolve main services
        logger = self.container.resolve(LoggerInterface)
        database_service = self.container.resolve(DatabaseService)
        config = self.container.resolve(AppConfig)

        return Application(logger, database_service, config, self.container)

    def shutdown(self):
        """Properly shutdown the application and its services"""
        logger = self.container.resolve(LoggerInterface)
        logger.close()
        # Close other services if needed


class Application:
    """Main application class that uses DI"""

    def __init__(
        self,
        logger: LoggerInterface,
        database_service: DatabaseService,
        config: AppConfig,
        container: DIContainer,
    ):
        self.logger = logger
        self.database_service = database_service
        self.config = config
        self.container = container
        self.running = False

    def start(self):
        self.running = True
        self.logger.log("Application started.", level="INFO")

        if self.config.debug:
            self.logger.log("Debug mode is enabled.", level="DEBUG")

    def process_users(self, users: list):
        for user in users:
            success = self.database_service.save_user(user)
            if success:
                self.logger.log(f"Processed user: {user}", level="INFO")
            else:
                self.logger.log(f"Failed to process user: {user}", level="ERROR")

    def stop(self):
        self.running = False
        self.logger.log("Application stopped.", level="INFO")
        self.logger.close()
        # Close other services if needed


# ====================
# PART 5: MAIN EXECUTION & DEMONSTRATIONS
# ====================


def demonstrate_singleton_problems():
    """
    Demonstrate problems with singleton pattern
    - Show hidden dependencies
    - Show testing difficulties
    - Show tight coupling
    """
    print("\n=== DEMONSTRATING SINGLETON PROBLEMS ===")

    print("\n1. Hidden Dependencies:")

    # This class looks like it has no dependencies, but it does!
    class UserService:
        def create_user(self, name: str):
            logger = ProblematicLogger()  # Hidden dependency!
            logger.log(f"Creating user: {name}")
            return {"id": 1, "name": name}

    # You can't tell from the constructor that UserService needs logging
    service = UserService()
    print("UserService created - but what does it depend on? 🤔")

    print("\n2. Global State Problems:")
    logger1 = ProblematicLogger()
    logger2 = ProblematicLogger()
    print(f"Same instance? {logger1 is logger2}")

    logger1.change_log_file("test1.log")
    print(f"Logger2 file changed too: {logger2.log_file}")

    print("\n3. Testing Nightmare:")
    print("Every test that uses ProblematicLogger writes to real files!")
    print("Tests can't run in parallel safely!")
    print("State leaks between tests!")


def demonstrate_di_solution():
    """
    Demonstrate dependency injection solution
    - Show explicit dependencies
    - Show easy testing
    - Show loose coupling
    """
    print("\n=== DEMONSTRATING DEPENDENCY INJECTION SOLUTION ===")

    print("\n1. Explicit Dependencies:")
    # Clear what this service needs!
    console_logger = ConsoleLogger("DEBUG")
    file_logger = FileLogger("app.log", "INFO")
    database_config = DatabaseConfig(
        host="localhost", port=5432, username="user", password="pass", database="appdb"
    )

    # Dependencies are explicit and visible
    service1 = DatabaseService(console_logger, database_config)
    service2 = DatabaseService(file_logger, database_config)

    print("Dependencies are clear and explicit! ✅")

    print("\n2. Easy Testing:")
    # Create a mock logger for testing
    mock_logger = Mock(spec=LoggerInterface)
    test_service = DatabaseService(mock_logger, database_config)

    test_service.save_user({"name": "Test User"})
    print("Mock logger calls:", mock_logger.log.call_count)

    print("\n3. Flexible Configuration:")
    container = DIContainer()
    container.register_singleton(LoggerInterface, ConsoleLogger, "DEBUG")
    container.register_instance(DatabaseConfig, database_config)
    container.register_transient(DatabaseService, DatabaseService)

    # Automatic dependency injection!
    service = container.resolve(DatabaseService)
    service.save_user({"name": "DI User"})

    # Clean up
    console_logger.close()
    file_logger.close()


def demonstrate_factory_pattern():
    """Demonstrate the logger factory pattern"""
    print("\n🏭 FACTORY PATTERN DEMONSTRATION")
    print("=" * 60)

    # Create different logger configurations
    console_config = LoggingConfig(level="DEBUG", type="console")
    file_config = LoggingConfig(level="INFO", type="file", file_path="app.log")
    db_config = LoggingConfig(
        level="ERROR", type="database", database_connection="sqlite://logs.db"
    )

    # Create loggers using factory
    console_logger = LoggerFactory.create_logger(console_config)
    file_logger = LoggerFactory.create_logger(file_config)
    db_logger = LoggerFactory.create_logger(db_config)

    # Demonstrate usage
    test_message = "Factory pattern demonstration"

    print("Creating loggers via factory...")
    console_logger.log(test_message, "INFO")
    file_logger.log(test_message, "INFO")
    db_logger.log(test_message, "ERROR")

    # Clean up
    console_logger.close()
    file_logger.close()
    db_logger.close()

    print("✅ Factory pattern allows flexible logger creation!")


def demonstrate_application_bootstrap():
    """Demonstrate proper application bootstrapping with DI"""
    print("\n🚀 APPLICATION BOOTSTRAP DEMONSTRATION")
    print("=" * 60)

    # Create sample configuration
    sample_config = {
        "debug": True,
        "api_key": "demo-key-123",
        "logging": {"level": "DEBUG", "type": "console"},
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "demo_app",
            "username": "demo_user",
            "password": "demo_pass",
            "max_connections": 15,
        },
    }

    # Write config to temporary file
    config_file = "demo_config.json"
    try:
        with open(config_file, "w") as f:
            json.dump(sample_config, f, indent=2)

        # Bootstrap the application
        print("1. Bootstrapping application...")
        bootstrap = ApplicationBootstrap(config_file)

        print("2. Setting up DI container...")
        container = bootstrap.setup_container()

        print("3. Creating application...")
        app = bootstrap.create_application()

        print("4. Starting application...")
        app.start()

        print("5. Processing sample users...")
        sample_users = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
            {"name": "Charlie", "email": "charlie@example.com"},
        ]
        app.process_users(sample_users)

        print("6. Stopping application...")
        app.stop()

        print("7. Cleaning up...")
        bootstrap.shutdown()

        print("✅ Application lifecycle complete!")

    finally:
        # Clean up
        if os.path.exists(config_file):
            os.remove(config_file)
        if os.path.exists("app.log"):
            os.remove("app.log")


if __name__ == "__main__":
    print("Singleton Anti-patterns and Alternatives")
    print("=" * 60)

    # TODO: Add your demonstration calls here
    demonstrate_singleton_problems()
    demonstrate_di_solution()
    demonstrate_factory_pattern()
    demonstrate_application_bootstrap()
