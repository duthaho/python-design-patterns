from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import copy
import json
import logging
import re
import os


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration with connection details."""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    timeout: int = 30
    ssl_enabled: bool = False
    connection_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # TODO: Add validation logic here
        # Validate port range, required fields, etc.
        errors = []
        if not self.host.strip():
            errors.append("Host cannot be empty.")
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535).")
        if not self.database.strip():
            errors.append("Database name cannot be empty.")
        if not self.username.strip():
            errors.append("Username cannot be empty.")
        if self.pool_size <= 0:
            errors.append("Pool size must be greater than 0.")
        if self.timeout <= 0:
            errors.append("Timeout must be greater than 0 seconds.")
        if errors:
            raise ValueError("Invalid DatabaseConfig: " + "; ".join(errors))


@dataclass
class CacheConfig:
    """Cache configuration for Redis/Memcached."""
    provider: str  # "redis" or "memcached"
    host: str
    port: int
    ttl: int = 3600  # Time to live in seconds
    max_memory: str = "100mb"
    eviction_policy: str = "allkeys-lru"
    cluster_nodes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # TODO: Add validation logic here
        # Validate provider, port range, ttl, memory format, etc.
        errors = []
        if self.provider not in ("redis", "memcached"):
            errors.append(f"Provider '{self.provider}' is not supported. Use 'redis' or 'memcached'.")
        if not self.host.strip():
            errors.append("Host cannot be empty.")
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535).")
        if self.ttl <= 0:
            errors.append("TTL must be greater than 0 seconds.")
        # Validate memory format (e.g., "100mb", "1gb")
        if not re.match(r'^\d+[kmg]?b$', self.max_memory.lower()):
            errors.append(f"Invalid memory format '{self.max_memory}'. Use format like '100mb', '1gb'.")
        if errors:
            raise ValueError("Invalid CacheConfig: " + "; ".join(errors))


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers: List[str] = field(default_factory=lambda: ["console"])
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5
    
    def __post_init__(self):
        # TODO: Add validation logic here
        # Validate log level, handlers, file path if provided, etc.
        errors = []
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            errors.append(f"Log level '{self.level}' is not valid. Choose from {valid_levels}.")
        if not self.handlers:
            errors.append("At least one log handler must be specified.")
        if "file" in self.handlers and not self.file_path:
            errors.append("File handler specified but file_path is missing.")
        if self.backup_count < 0:
            errors.append("Backup count cannot be negative.")
        if errors:
            raise ValueError("Invalid LoggingConfig: " + "; ".join(errors))


class ConfigurationPrototype(ABC):
    """Abstract base class for all configuration prototypes."""
    
    def __init__(self, name: str, environment: Environment):
        self.name = name
        self.environment = environment
        self.created_at = None  # TODO: Set timestamp
        self.version = "1.0.0"
    
    @abstractmethod
    def clone(self) -> 'ConfigurationPrototype':
        """Create a deep copy of this configuration."""
        # TODO: Implement cloning logic
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the configuration."""
        # TODO: Implement validation
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        # TODO: Implement serialization
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationPrototype':
        """Create configuration from dictionary."""
        # TODO: Implement deserialization
        pass


class BaseConfiguration(ConfigurationPrototype):
    """Base configuration containing common settings for all services."""
    
    def __init__(
        self, 
        name: str, 
        environment: Environment,
        database_config: DatabaseConfig,
        cache_config: CacheConfig,
        logging_config: LoggingConfig,
        custom_settings: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, environment)
        self.database_config = database_config
        self.cache_config = cache_config
        self.logging_config = logging_config
        self.custom_settings = custom_settings or {}
    
    def clone(self) -> 'BaseConfiguration':
        """Create a deep copy of this configuration."""
        # TODO: Implement proper cloning
        # Consider which parts need deep copy vs shallow copy
        return copy.deepcopy(self)
        
    def validate(self) -> bool:
        """Validate all configuration components."""
        # TODO: Validate all nested configurations
        # Return True if valid, False otherwise
        database_errors = ConfigurationValidator.validate_database_config(self.database_config)
        cache_errors = ConfigurationValidator.validate_cache_config(self.cache_config)
        logging_errors = ConfigurationValidator.validate_logging_config(self.logging_config)
        all_errors = database_errors + cache_errors + logging_errors
        if all_errors:
            for error in all_errors:
                logging.error(error)
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # TODO: Convert all components to dict format
        return {
            "name": self.name,
            "environment": self.environment.value,
            "database_config": self.database_config.__dict__,
            "cache_config": self.cache_config.__dict__,
            "logging_config": self.logging_config.__dict__,
            "custom_settings": self.custom_settings,
            "created_at": self.created_at,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseConfiguration':
        """Create BaseConfiguration from dictionary."""
        config = cls(
            name=data["name"],
            environment=Environment(data["environment"]),
            database_config=DatabaseConfig(**data["database_config"]),
            cache_config=CacheConfig(**data["cache_config"]),
            logging_config=LoggingConfig(**data["logging_config"]),
            custom_settings=data.get("custom_settings", {})
        )
        config.created_at = data.get("created_at")
        config.version = data.get("version", "1.0.0")
        return config
    
    def merge_overrides(self, overrides: Dict[str, Any]) -> 'BaseConfiguration':
        """Create a new configuration by merging overrides."""
        # TODO: Implement configuration merging logic
        # This should clone the current config and apply overrides
        new_config = self.clone()
        
        # Handle nested config overrides
        for key, value in overrides.items():
            if key == "database_config" and isinstance(value, dict):
                for db_key, db_value in value.items():
                    if hasattr(new_config.database_config, db_key):
                        setattr(new_config.database_config, db_key, db_value)
            elif key == "cache_config" and isinstance(value, dict):
                for cache_key, cache_value in value.items():
                    if hasattr(new_config.cache_config, cache_key):
                        setattr(new_config.cache_config, cache_key, cache_value)
            elif key == "logging_config" and isinstance(value, dict):
                for log_key, log_value in value.items():
                    if hasattr(new_config.logging_config, log_key):
                        setattr(new_config.logging_config, log_key, log_value)
            elif key == "custom_settings" and isinstance(value, dict):
                new_config.custom_settings.update(value)
            elif hasattr(new_config, key):
                setattr(new_config, key, value)
            else:
                new_config.custom_settings[key] = value
        
        return new_config


class ServiceConfiguration(BaseConfiguration):
    """Service-specific configuration that extends base configuration."""
    
    def __init__(
        self,
        service_name: str,
        base_config: BaseConfiguration,
        service_port: int,
        health_check_endpoint: str = "/health",
        metrics_enabled: bool = True,
        service_dependencies: Optional[List[str]] = None
    ):
        # TODO: Initialize by copying from base_config and adding service-specific settings
        super().__init__(
            name=f"{base_config.name}-{service_name}",
            environment=base_config.environment,
            database_config=base_config.database_config,
            cache_config=base_config.cache_config,
            logging_config=base_config.logging_config,
            custom_settings=base_config.custom_settings.copy()
        )
        self.service_name = service_name
        self.service_port = service_port
        self.health_check_endpoint = health_check_endpoint
        self.metrics_enabled = metrics_enabled
        self.service_dependencies = service_dependencies or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including service-specific settings."""
        base_dict = super().to_dict()
        base_dict.update({
            "service_name": self.service_name,
            "service_port": self.service_port,
            "health_check_endpoint": self.health_check_endpoint,
            "metrics_enabled": self.metrics_enabled,
            "service_dependencies": self.service_dependencies
        })
        return base_dict


class ConfigurationValidator:
    """Validates configuration objects."""
    
    @staticmethod
    def validate_database_config(config: DatabaseConfig) -> List[str]:
        """Validate database configuration. Returns list of error messages."""
        # TODO: Implement validation rules
        # - Check port range (1-65535)
        # - Validate required fields are not empty
        # - Check pool_size > 0
        # - Validate timeout > 0
        errors = []
        if not config.host.strip():
            errors.append("Database host cannot be empty.")
        if not (1 <= config.port <= 65535):
            errors.append(f"Port {config.port} is out of valid range (1-65535).")
        if config.pool_size <= 0:
            errors.append("Pool size must be greater than 0.")
        if config.timeout <= 0:
            errors.append("Timeout must be greater than 0 seconds.")
        if config.ssl_enabled and not config.connection_params.get("ssl_cert"):
            errors.append("SSL is enabled but 'ssl_cert' is missing in connection_params.")
        return errors
    
    @staticmethod
    def validate_cache_config(config: CacheConfig) -> List[str]:
        """Validate cache configuration. Returns list of error messages."""
        # TODO: Implement validation rules
        # - Check provider is valid ("redis" or "memcached")
        # - Validate port range
        # - Check TTL > 0
        # - Validate memory format
        errors = []
        if config.provider not in ("redis", "memcached"):
            errors.append(f"Provider '{config.provider}' is not supported.")
        if not config.host.strip():
            errors.append("Cache host cannot be empty.")
        if not (1 <= config.port <= 65535):
            errors.append(f"Port {config.port} is out of valid range (1-65535).")
        if config.ttl <= 0:
            errors.append("TTL must be greater than 0 seconds.")
        return errors
    
    @staticmethod
    def validate_logging_config(config: LoggingConfig) -> List[str]:
        """Validate logging configuration. Returns list of error messages."""
        # TODO: Implement validation rules
        # - Check log level is valid
        # - Validate handlers list is not empty
        # - Check file path exists if specified
        errors = []
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if config.level not in valid_levels:
            errors.append(f"Log level '{config.level}' is not valid.")
        if not config.handlers:
            errors.append("At least one log handler must be specified.")
        if "file" in config.handlers and not config.file_path:
            errors.append("File handler specified but file_path is missing.")
        return errors


class ConfigurationManager:
    """Manages configuration prototypes and creates instances."""
    
    def __init__(self):
        self._prototypes: Dict[str, ConfigurationPrototype] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_prototype(self, key: str, prototype: ConfigurationPrototype) -> None:
        """Register a configuration prototype."""
        # TODO: Implement prototype registration
        # Add validation before registering
        if not prototype.validate():
            raise ValueError("Cannot register invalid configuration prototype.")
        if key in self._prototypes:
            raise KeyError(f"Prototype with key '{key}' is already registered.")
        self._prototypes[key] = prototype
        self._logger.info(f"Registered prototype with key '{key}'.")
    
    def create_configuration(self, prototype_key: str, overrides: Optional[Dict[str, Any]] = None) -> ConfigurationPrototype:
        """Create a new configuration from prototype with optional overrides."""
        # TODO: Implement configuration creation
        # 1. Get prototype by key
        # 2. Clone the prototype
        # 3. Apply overrides if provided
        # 4. Validate the result
        # 5. Return the new configuration
        if prototype_key not in self._prototypes:
            raise KeyError(f"Prototype with key '{prototype_key}' is not registered.")
        
        prototype = self._prototypes[prototype_key]
        new_config = prototype.clone()
        
        if overrides:
            if isinstance(new_config, BaseConfiguration):
                new_config = new_config.merge_overrides(overrides)
            else:
                for key, value in overrides.items():
                    if hasattr(new_config, key):
                        setattr(new_config, key, value)
                    else:
                        new_config.custom_settings[key] = value

        if not new_config.validate():
            raise ValueError("Created configuration is invalid.")
        
        return new_config
    
    def create_service_configuration(
        self, 
        base_prototype_key: str, 
        service_name: str,
        service_port: int,
        overrides: Optional[Dict[str, Any]] = None
    ) -> ServiceConfiguration:
        """Create service-specific configuration from base prototype."""
        # TODO: Implement service configuration creation
        base_config = self.create_configuration(base_prototype_key, overrides)
        if not isinstance(base_config, BaseConfiguration):
            raise TypeError("Base prototype must be of type BaseConfiguration.")
        
        return ServiceConfiguration(
            service_name=service_name,
            base_config=base_config,
            service_port=service_port
        )
    
    def list_prototypes(self) -> List[str]:
        """Return list of registered prototype keys."""
        return list(self._prototypes.keys())
    
    def export_configuration(self, config: ConfigurationPrototype, file_path: str) -> None:
        """Export configuration to JSON file."""
        # TODO: Implement JSON export
        with open(file_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=4)
    
    def import_configuration(self, file_path: str) -> ConfigurationPrototype:
        """Import configuration from JSON file."""
        # TODO: Implement JSON import
        with open(file_path, 'r') as f:
            data = json.load(f)
        # Determine the type of configuration and create appropriate instance
        # For simplicity, assume it's always BaseConfiguration here
        return BaseConfiguration.from_dict(data)


# TODO: Implement a demonstration function that shows:
def demonstrate_configuration_system():
    """Comprehensive demonstration of the configuration system."""
    print("=== Configuration Management System Demo ===\n")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    manager = ConfigurationManager()

    # Create base configurations for different environments
    print("1. Creating base configurations...")
    
    # Development configuration
    dev_config = BaseConfiguration(
        name="DevBaseConfig",
        environment=Environment.DEVELOPMENT,
        database_config=DatabaseConfig(
            host="localhost",
            port=5432,
            database="dev_db",
            username="dev_user",
            password="dev_pass"
        ),
        cache_config=CacheConfig(
            provider="redis",
            host="localhost",
            port=6379,
            ttl=1800
        ),
        logging_config=LoggingConfig(
            level="DEBUG",
            handlers=["console", "file"],
            file_path="dev.log"
        )
    )
    
    # Production configuration
    prod_config = BaseConfiguration(
        name="ProdBaseConfig",
        environment=Environment.PRODUCTION,
        database_config=DatabaseConfig(
            host="prod-db.company.com",
            port=5432,
            database="prod_db",
            username="prod_user",
            password="super_secret_pass",
            ssl_enabled=True,
            connection_params={"ssl_cert": "/path/to/cert"}
        ),
        cache_config=CacheConfig(
            provider="redis",
            host="prod-cache.company.com",
            port=6379,
            ttl=3600,
            max_memory="1gb"
        ),
        logging_config=LoggingConfig(
            level="ERROR",
            handlers=["file"],
            file_path="/var/log/app.log"
        )
    )
    
    # Register prototypes
    print("\n2. Registering prototypes...")
    manager.register_prototype("dev_base", dev_config)
    manager.register_prototype("prod_base", prod_config)
    print(f"Registered prototypes: {manager.list_prototypes()}")
    
    # Create service configurations
    print("\n3. Creating service configurations...")
    
    web_service = manager.create_service_configuration(
        base_prototype_key="dev_base",
        service_name="web_service",
        service_port=8080,
        overrides={
            "custom_settings": {"feature_flags": {"new_ui": True, "beta_features": False}},
            "logging_config": {"level": "INFO"}
        }
    )
    
    api_service = manager.create_service_configuration(
        base_prototype_key="dev_base",
        service_name="api_service",
        service_port=9090,
        overrides={
            "database_config": {"pool_size": 20},
            "custom_settings": {"rate_limit": 1000}
        }
    )
    
    print(f"Created web service on port: {web_service.service_port}")
    print(f"Created API service on port: {api_service.service_port}")
    
    # Demonstrate prototype independence
    print("\n4. Testing prototype independence...")
    original_custom_settings = dev_config.custom_settings.copy()
    web_service.custom_settings["modified"] = True
    
    print(f"Original config custom_settings: {dev_config.custom_settings}")
    print(f"Web service custom_settings: {web_service.custom_settings}")
    print(f"Independence verified: {dev_config.custom_settings == original_custom_settings}")
    
    # Validation demonstration
    print("\n5. Testing validation...")
    try:
        invalid_config = BaseConfiguration(
            name="Invalid",
            environment=Environment.DEVELOPMENT,
            database_config=DatabaseConfig(
                host="",  # Invalid empty host
                port=99999,  # Invalid port
                database="test",
                username="user",
                password="pass"
            ),
            cache_config=CacheConfig("redis", "localhost", 6379),
            logging_config=LoggingConfig()
        )
        print("This should not print - validation should fail")
    except ValueError as e:
        print(f"Validation correctly failed: {e}")
    
    # Export/Import demonstration
    print("\n6. Testing export/import...")
    export_file = "test_config.json"
    manager.export_configuration(web_service, export_file)
    imported_config = manager.import_configuration(export_file)
    
    print(f"Export/import successful: {imported_config.name == web_service.name}")
    
    # Clean up
    if os.path.exists(export_file):
        os.remove(export_file)
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    # TODO: Run the demonstration
    demonstrate_configuration_system()
