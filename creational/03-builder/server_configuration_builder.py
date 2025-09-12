from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================


class ServerType(Enum):
    WEB = "web"
    DATABASE = "database"
    CACHE = "cache"
    LOAD_BALANCER = "load_balancer"


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Protocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"


@dataclass(frozen=True)
class ServerSpecs:
    """Server hardware specifications"""

    cpu_cores: int
    ram_gb: int
    storage_gb: int

    def validate(self) -> List[str]:
        errors = []
        if self.cpu_cores <= 0:
            errors.append("CPU cores must be greater than 0")
        if self.ram_gb <= 0:
            errors.append("RAM must be greater than 0 GB")
        if self.storage_gb <= 0:
            errors.append("Storage must be greater than 0 GB")
        return errors


@dataclass(frozen=True)
class NetworkConfig:
    """Network configuration settings"""

    ports: tuple[int, ...] = field(default_factory=tuple)
    protocols: tuple[Protocol, ...] = field(default_factory=tuple)
    load_balancer_enabled: bool = False
    ssl_enabled: bool = False

    def validate(self) -> List[str]:
        errors = []
        if len(self.ports) != len(self.protocols):
            errors.append("Number of ports must match number of protocols")
        for port in self.ports:
            if port < 1 or port > 65535:
                errors.append(f"Port {port} is out of valid range (1-65535)")
        if self.ssl_enabled and Protocol.HTTPS not in self.protocols:
            errors.append("SSL is enabled but HTTPS protocol is not configured")
        return errors


@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration settings"""

    firewall_rules: tuple[str, ...] = field(default_factory=tuple)
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    auth_method: str = "basic"  # basic, oauth, jwt

    def validate(self) -> List[str]:
        errors = []
        if self.ssl_cert_path and not self.ssl_key_path:
            errors.append("SSL certificate path is set but key path is missing")
        if self.ssl_key_path and not self.ssl_cert_path:
            errors.append("SSL key path is set but certificate path is missing")
        if self.auth_method not in {"basic", "oauth", "jwt"}:
            errors.append(f"Unsupported authentication method: {self.auth_method}")
        return errors


@dataclass(frozen=True)
class AppDeploymentConfig:
    """Application deployment configuration"""

    environment_vars: Dict[str, str] = field(default_factory=dict)
    health_check_path: str = ""
    health_check_interval_seconds: int = 30
    restart_policy: str = "always"  # always, on-failure, never

    def validate(self) -> List[str]:
        errors = []
        if self.health_check_interval_seconds <= 0:
            errors.append("Health check interval must be greater than 0 seconds")
        if self.restart_policy not in {"always", "on-failure", "never"}:
            errors.append(f"Unsupported restart policy: {self.restart_policy}")
        return errors


@dataclass(frozen=True)
class ServerConfiguration:
    """Final immutable server configuration"""

    server_type: ServerType
    environment: Environment
    specs: ServerSpecs
    network: NetworkConfig
    security: SecurityConfig
    deployment: AppDeploymentConfig

    def validate_complete_config(self) -> List[str]:
        """Perform final cross-component validation"""
        # TODO: Implement comprehensive validation that checks:
        # - All components are compatible with each other
        # - Server type requirements are met
        # - Environment-specific rules are followed
        # - Security requirements based on environment
        errors = []
        if (
            self.server_type == ServerType.WEB
            and Protocol.HTTP not in self.network.protocols
            and Protocol.HTTPS not in self.network.protocols
        ):
            errors.append("Web server must have HTTP or HTTPS protocol configured")
        if (
            self.environment == Environment.PRODUCTION
            and not self.security.ssl_cert_path
        ):
            errors.append("Production environment requires SSL certificate to be set")
        return errors


# ============================================================================
# BUILDER STATE MANAGEMENT
# ============================================================================


class BuilderState(Enum):
    """States that the builder can be in"""

    INITIAL = "initial"
    SPECS_SET = "specs_set"
    NETWORK_CONFIGURED = "network_configured"
    SECURITY_CONFIGURED = "security_configured"
    DEPLOYMENT_READY = "deployment_ready"
    READY_TO_BUILD = "ready_to_build"


@dataclass
class BuilderOperation:
    """Represents a single builder operation for rollback functionality"""

    operation_name: str
    old_state: BuilderState
    old_values: Dict[str, Any]

    # TODO: Add any additional data needed for rollback


# ============================================================================
# VALIDATION FRAMEWORK
# ============================================================================


class ValidationRule(ABC):
    """Abstract base class for validation rules"""

    @abstractmethod
    def validate(self, builder: "ServerConfigurationBuilder") -> List[str]:
        """Return list of validation error messages"""
        pass

    @abstractmethod
    def applies_to_state(self, state: BuilderState) -> bool:
        """Check if this rule applies to the given builder state"""
        pass


class SpecsValidationRule(ValidationRule):
    """Validates server specifications"""

    def validate(self, builder: "ServerConfigurationBuilder") -> List[str]:
        # TODO: Implement validation logic for server specs
        # Check things like:
        # - Minimum requirements for server type
        # - Environment-specific requirements
        # - Reasonable resource limits
        errors = []
        if builder._specs:
            errors.extend(builder._specs.validate())
        return errors

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Return True if validation should run in this state
        return state == BuilderState.SPECS_SET


class NetworkSecurityValidationRule(ValidationRule):
    """Validates that network and security configs are compatible"""

    def validate(self, builder: "ServerConfigurationBuilder") -> List[str]:
        # TODO: Implement validation logic such as:
        # - If SSL is enabled, HTTPS protocol should be used
        # - If load balancer is enabled, multiple ports might be needed
        # - Security rules should match enabled protocols
        errors = []
        if builder._network:
            errors.extend(builder._network.validate())
        if builder._security:
            errors.extend(builder._security.validate())
        return errors

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Return True if both network and security are configured
        return state in {
            BuilderState.NETWORK_CONFIGURED,
            BuilderState.SECURITY_CONFIGURED,
        }


class EnvironmentValidationRule(ValidationRule):
    """Validates environment-specific requirements"""

    def validate(self, builder: "ServerConfigurationBuilder") -> List[str]:
        # TODO: Implement environment-specific validation:
        # - Production requires SSL
        # - Production requires specific minimum specs
        # - Development allows more relaxed rules
        errors = []
        if builder._environment == Environment.PRODUCTION:
            if builder._specs:
                if builder._specs.cpu_cores < 2:
                    errors.append(
                        "Production environment requires at least 2 CPU cores"
                    )
                if builder._specs.ram_gb < 4:
                    errors.append("Production environment requires at least 4 GB RAM")
            if builder._security and not builder._security.ssl_cert_path:
                errors.append(
                    "Production environment requires SSL certificate to be set"
                )
        return errors

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Implement state check
        return state in {
            BuilderState.SPECS_SET,
            BuilderState.SECURITY_CONFIGURED,
            BuilderState.DEPLOYMENT_READY,
        }


# ============================================================================
# MAIN BUILDER CLASS
# ============================================================================


class ServerConfigurationBuilder:
    """
    Advanced builder with state management, validation, and rollback capability
    """

    def __init__(self):
        # Current state
        self._state: BuilderState = BuilderState.INITIAL

        # Configuration components (mutable during building)
        self._server_type: Optional[ServerType] = None
        self._environment: Optional[Environment] = None
        self._specs: Optional[ServerSpecs] = None
        self._network: Optional[NetworkConfig] = None
        self._security: Optional[SecurityConfig] = None
        self._deployment: Optional[AppDeploymentConfig] = None

        # Operation history for rollback
        self._operation_history: List[BuilderOperation] = []

        # Validation rules
        self._validation_rules: List[ValidationRule] = [
            SpecsValidationRule(),
            NetworkSecurityValidationRule(),
            EnvironmentValidationRule(),
        ]

    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================

    def _transition_to_state(self, new_state: BuilderState) -> None:
        """Transition to a new builder state"""
        # TODO: Implement state transition logic
        # - Check if transition is valid
        # - Update current state
        # - Run applicable validations
        if not self._validate_state_transition(self._state, new_state):
            raise ValueError(
                f"Invalid state transition from {self._state} to {new_state}"
            )
        self._state = new_state
        self._run_validations()

    def _validate_state_transition(
        self, from_state: BuilderState, to_state: BuilderState
    ) -> bool:
        """Check if state transition is allowed"""
        # TODO: Define valid state transitions
        # For example: INITIAL -> SPECS_SET -> NETWORK_CONFIGURED -> etc.
        if from_state == to_state:
            return True

        valid_transitions = {
            BuilderState.INITIAL: [BuilderState.SPECS_SET],
            BuilderState.SPECS_SET: [BuilderState.NETWORK_CONFIGURED],
            BuilderState.NETWORK_CONFIGURED: [BuilderState.SECURITY_CONFIGURED],
            BuilderState.SECURITY_CONFIGURED: [BuilderState.DEPLOYMENT_READY],
            BuilderState.DEPLOYMENT_READY: [BuilderState.READY_TO_BUILD],
            BuilderState.READY_TO_BUILD: [],
        }
        return to_state in valid_transitions.get(from_state, [])

    def _run_validations(self) -> None:
        """Run all applicable validation rules for current state"""
        # TODO: Implement validation running logic
        # - Get applicable rules for current state
        # - Run validations
        # - Collect and handle errors
        errors = []
        for rule in self._validation_rules:
            if rule.applies_to_state(self._state):
                errors.extend(rule.validate(self))
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

    # ========================================================================
    # ROLLBACK FUNCTIONALITY
    # ========================================================================

    def _save_operation(self, operation_name: str) -> None:
        """Save current state before making changes"""
        # TODO: Implement operation saving for rollback
        # - Capture current state
        # - Capture current values
        # - Add to operation history
        old_values = {
            "server_type": self._server_type,
            "environment": self._environment,
            "specs": self._specs,
            "network": self._network,
            "security": self._security,
            "deployment": self._deployment,
        }
        operation = BuilderOperation(
            operation_name=operation_name, old_state=self._state, old_values=old_values
        )
        self._operation_history.append(operation)

    def rollback(self, steps: int = 1) -> "ServerConfigurationBuilder":
        """Rollback the last N operations"""
        # TODO: Implement rollback logic
        # - Validate steps parameter
        # - Restore previous state and values
        # - Update operation history
        if steps < 1 or steps > len(self._operation_history):
            raise ValueError("Invalid number of steps to rollback")
        for _ in range(steps):
            operation = self._operation_history.pop()
            self._state = operation.old_state
            self._server_type = operation.old_values["server_type"]
            self._environment = operation.old_values["environment"]
            self._specs = operation.old_values["specs"]
            self._network = operation.old_values["network"]
            self._security = operation.old_values["security"]
            self._deployment = operation.old_values["deployment"]
        return self

    # ========================================================================
    # BUILDER METHODS - Phase 1: Basic Setup
    # ========================================================================

    def set_server_type(self, server_type: ServerType) -> "ServerConfigurationBuilder":
        """Set the server type - must be called first"""
        # TODO: Implement
        # - Check current state allows this operation
        # - Save operation for rollback
        # - Set server type
        # - Transition state if appropriate
        if self._state != BuilderState.INITIAL:
            raise ValueError("Server type can only be set in INITIAL state")
        self._save_operation("set_server_type")
        self._server_type = server_type
        return self

    def set_environment(self, environment: Environment) -> "ServerConfigurationBuilder":
        """Set the deployment environment"""
        # TODO: Implement similar to set_server_type
        if self._state != BuilderState.INITIAL:
            raise ValueError("Environment can only be set in INITIAL state")
        self._save_operation("set_environment")
        self._environment = environment
        self._transition_to_state(BuilderState.SPECS_SET)
        return self

    def set_specs(
        self, cpu_cores: int, ram_gb: int, storage_gb: int
    ) -> "ServerConfigurationBuilder":
        """Set server hardware specifications"""
        # TODO: Implement
        # - Validate current state
        # - Create ServerSpecs object
        # - Save operation and update state
        # - Transition to SPECS_SET state
        if self._state != BuilderState.SPECS_SET:
            raise ValueError("Specs can only be set in SPECS_SET state")
        self._save_operation("set_specs")
        self._specs = ServerSpecs(cpu_cores, ram_gb, storage_gb)
        self._transition_to_state(BuilderState.NETWORK_CONFIGURED)
        return self

    # ========================================================================
    # BUILDER METHODS - Phase 2: Network Configuration
    # ========================================================================

    def add_port(self, port: int, protocol: Protocol) -> "ServerConfigurationBuilder":
        """Add a port with associated protocol - only available after specs are set"""
        # TODO: Implement
        # - Check state allows network configuration
        # - Validate port number
        # - Add to network configuration
        if self._state != BuilderState.NETWORK_CONFIGURED:
            raise ValueError("Ports can only be added in NETWORK_CONFIGURED state")
        if port < 1 or port > 65535:
            raise ValueError("Port must be in range 1-65535")
        self._save_operation("add_port")
        if not self._network:
            self._network = NetworkConfig(ports=(port,), protocols=(protocol,))
        else:
            self._network = NetworkConfig(
                ports=self._network.ports + (port,),
                protocols=self._network.protocols + (protocol,),
                load_balancer_enabled=self._network.load_balancer_enabled,
                ssl_enabled=self._network.ssl_enabled,
            )
        return self

    def enable_load_balancer(self) -> "ServerConfigurationBuilder":
        """Enable load balancer - only for web servers"""
        # TODO: Implement with server type validation
        if self._state != BuilderState.NETWORK_CONFIGURED:
            raise ValueError(
                "Load balancer can only be enabled in NETWORK_CONFIGURED state"
            )
        if self._server_type != ServerType.WEB:
            raise ValueError("Load balancer can only be enabled for web servers")
        self._save_operation("enable_load_balancer")
        if not self._network:
            self._network = NetworkConfig(load_balancer_enabled=True)
        else:
            self._network = NetworkConfig(
                ports=self._network.ports,
                protocols=self._network.protocols,
                load_balancer_enabled=True,
                ssl_enabled=self._network.ssl_enabled,
            )
        return self

    def enable_ssl(self) -> "ServerConfigurationBuilder":
        """Enable SSL - affects security configuration requirements"""
        # TODO: Implement
        if self._state != BuilderState.NETWORK_CONFIGURED:
            raise ValueError("SSL can only be enabled in NETWORK_CONFIGURED state")
        self._save_operation("enable_ssl")
        if not self._network:
            self._network = NetworkConfig(ssl_enabled=True)
        else:
            self._network = NetworkConfig(
                ports=self._network.ports,
                protocols=self._network.protocols,
                load_balancer_enabled=self._network.load_balancer_enabled,
                ssl_enabled=True,
            )
        return self

    def finalize_network_config(self) -> "ServerConfigurationBuilder":
        """Finalize network configuration and move to security phase"""
        # TODO: Implement
        # - Create NetworkConfig object
        # - Validate network configuration
        # - Transition to NETWORK_CONFIGURED state
        if self._state != BuilderState.NETWORK_CONFIGURED:
            raise ValueError(
                "Network configuration can only be finalized in NETWORK_CONFIGURED state"
            )
        self._save_operation("finalize_network_config")
        self._transition_to_state(BuilderState.SECURITY_CONFIGURED)
        return self

    # ========================================================================
    # BUILDER METHODS - Phase 3: Security Configuration
    # ========================================================================

    def add_firewall_rule(self, rule: str) -> "ServerConfigurationBuilder":
        """Add firewall rule - only available after network is configured"""
        # TODO: Implement
        if self._state != BuilderState.SECURITY_CONFIGURED:
            raise ValueError(
                "Firewall rules can only be added in SECURITY_CONFIGURED state"
            )
        self._save_operation("add_firewall_rule")
        if not self._security:
            self._security = SecurityConfig(firewall_rules=(rule,))
        else:
            self._security = SecurityConfig(
                firewall_rules=self._security.firewall_rules + (rule,),
                ssl_cert_path=self._security.ssl_cert_path,
                ssl_key_path=self._security.ssl_key_path,
                auth_method=self._security.auth_method,
            )
        return self

    def set_ssl_certificates(
        self, cert_path: str, key_path: str
    ) -> "ServerConfigurationBuilder":
        """Set SSL certificate paths - only if SSL is enabled"""
        # TODO: Implement with SSL validation
        if self._state != BuilderState.SECURITY_CONFIGURED:
            raise ValueError(
                "SSL certificates can only be set in SECURITY_CONFIGURED state"
            )
        if not self._network or not self._network.ssl_enabled:
            raise ValueError(
                "SSL must be enabled in network configuration before setting certificates"
            )
        self._save_operation("set_ssl_certificates")
        if not self._security:
            self._security = SecurityConfig(
                ssl_cert_path=cert_path, ssl_key_path=key_path
            )
        else:
            self._security = SecurityConfig(
                firewall_rules=self._security.firewall_rules,
                ssl_cert_path=cert_path,
                ssl_key_path=key_path,
                auth_method=self._security.auth_method,
            )
        return self

    def set_auth_method(self, auth_method: str) -> "ServerConfigurationBuilder":
        """Set authentication method"""
        # TODO: Implement with validation of supported methods
        if self._state != BuilderState.SECURITY_CONFIGURED:
            raise ValueError(
                "Authentication method can only be set in SECURITY_CONFIGURED state"
            )
        if auth_method not in {"basic", "oauth", "jwt"}:
            raise ValueError(f"Unsupported authentication method: {auth_method}")
        self._save_operation("set_auth_method")
        if not self._security:
            self._security = SecurityConfig(auth_method=auth_method)
        else:
            self._security = SecurityConfig(
                firewall_rules=self._security.firewall_rules,
                ssl_cert_path=self._security.ssl_cert_path,
                ssl_key_path=self._security.ssl_key_path,
                auth_method=auth_method,
            )
        return self

    def finalize_security_config(self) -> "ServerConfigurationBuilder":
        """Finalize security configuration"""
        # TODO: Implement
        if self._state != BuilderState.SECURITY_CONFIGURED:
            raise ValueError(
                "Security configuration can only be finalized in SECURITY_CONFIGURED state"
            )
        self._save_operation("finalize_security_config")
        self._transition_to_state(BuilderState.DEPLOYMENT_READY)
        return self

    # ========================================================================
    # BUILDER METHODS - Phase 4: Deployment Configuration
    # ========================================================================

    def add_environment_variable(
        self, key: str, value: str
    ) -> "ServerConfigurationBuilder":
        """Add environment variable for application"""
        # TODO: Implement
        if self._state != BuilderState.DEPLOYMENT_READY:
            raise ValueError(
                "Environment variables can only be added in DEPLOYMENT_READY state"
            )
        self._save_operation("add_environment_variable")
        if not self._deployment:
            self._deployment = AppDeploymentConfig(environment_vars={key: value})
        else:
            new_env_vars = self._deployment.environment_vars.copy()
            new_env_vars[key] = value
            self._deployment = AppDeploymentConfig(
                environment_vars=new_env_vars,
                health_check_path=self._deployment.health_check_path,
                health_check_interval_seconds=self._deployment.health_check_interval_seconds,
                restart_policy=self._deployment.restart_policy,
            )
        return self

    def set_health_check(
        self, path: str, interval_seconds: int = 30
    ) -> "ServerConfigurationBuilder":
        """Configure health check settings"""
        # TODO: Implement
        if self._state != BuilderState.DEPLOYMENT_READY:
            raise ValueError("Health check can only be set in DEPLOYMENT_READY state")
        if interval_seconds <= 0:
            raise ValueError("Health check interval must be greater than 0 seconds")
        self._save_operation("set_health_check")
        if not self._deployment:
            self._deployment = AppDeploymentConfig(
                health_check_path=path, health_check_interval_seconds=interval_seconds
            )
        else:
            self._deployment = AppDeploymentConfig(
                environment_vars=self._deployment.environment_vars,
                health_check_path=path,
                health_check_interval_seconds=interval_seconds,
                restart_policy=self._deployment.restart_policy,
            )
        return self

    def set_restart_policy(self, policy: str) -> "ServerConfigurationBuilder":
        """Set container restart policy"""
        # TODO: Implement with policy validation
        if self._state != BuilderState.DEPLOYMENT_READY:
            raise ValueError("Restart policy can only be set in DEPLOYMENT_READY state")
        if policy not in {"always", "on-failure", "never"}:
            raise ValueError(f"Unsupported restart policy: {policy}")
        self._save_operation("set_restart_policy")
        if not self._deployment:
            self._deployment = AppDeploymentConfig(restart_policy=policy)
        else:
            self._deployment = AppDeploymentConfig(
                environment_vars=self._deployment.environment_vars,
                health_check_path=self._deployment.health_check_path,
                health_check_interval_seconds=self._deployment.health_check_interval_seconds,
                restart_policy=policy,
            )
        return self

    def finalize_deployment_config(self) -> "ServerConfigurationBuilder":
        """Finalize deployment configuration"""
        # TODO: Implement
        if self._state != BuilderState.DEPLOYMENT_READY:
            raise ValueError(
                "Deployment configuration can only be finalized in DEPLOYMENT_READY state"
            )
        self._save_operation("finalize_deployment_config")
        self._transition_to_state(BuilderState.READY_TO_BUILD)
        return self

    # ========================================================================
    # BUILD METHOD
    # ========================================================================

    def build(self) -> ServerConfiguration:
        """Build the final server configuration"""
        # TODO: Implement final build
        # - Check all required components are set
        # - Run final comprehensive validation
        # - Create immutable ServerConfiguration
        # - Reset builder state
        if self._state != BuilderState.READY_TO_BUILD:
            raise ValueError("Builder is not ready to build the configuration")
        if not all(
            [
                self._server_type,
                self._environment,
                self._specs,
                self._network,
                self._security,
                self._deployment,
            ]
        ):
            raise ValueError("All configuration components must be set before building")
        final_config = ServerConfiguration(
            server_type=self._server_type,
            environment=self._environment,
            specs=self._specs,
            network=self._network,
            security=self._security,
            deployment=self._deployment,
        )
        errors = final_config.validate_complete_config()
        if errors:
            raise ValueError(
                "Final configuration validation errors: " + "; ".join(errors)
            )
        self.reset()
        return final_config

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_current_state(self) -> BuilderState:
        """Get current builder state"""
        return self._state

    def get_operation_history(self) -> List[str]:
        """Get list of operations performed"""
        # TODO: Return list of operation names from history
        return [op.operation_name for op in self._operation_history]

    def reset(self) -> "ServerConfigurationBuilder":
        """Reset builder to initial state"""
        # TODO: Implement reset logic
        self._state = BuilderState.INITIAL
        self._server_type = None
        self._environment = None
        self._specs = None
        self._network = None
        self._security = None
        self._deployment = None
        self._operation_history.clear()
        return self


# ============================================================================
# DIRECTOR CLASS
# ============================================================================


class ServerConfigurationDirector:
    """Director for creating common server configurations"""

    def __init__(self, builder: ServerConfigurationBuilder):
        self._builder = builder

    def create_simple_web_server(self, environment: Environment) -> ServerConfiguration:
        """Create a basic web server configuration"""
        # TODO: Implement using the builder
        # - Set server type to WEB
        # - Set appropriate specs
        # - Configure HTTP/HTTPS ports
        # - Set basic security
        # - Configure for web deployment
        return (
            self._builder.set_server_type(ServerType.WEB)
            .set_environment(environment)
            .set_specs(cpu_cores=2, ram_gb=4, storage_gb=50)
            .add_port(80, Protocol.HTTP)
            .add_port(443, Protocol.HTTPS)
            .enable_ssl()
            .finalize_network_config()
            .set_ssl_certificates("/path/to/cert", "/path/to/key")
            .add_firewall_rule("allow port 80")
            .add_firewall_rule("allow port 443")
            .finalize_security_config()
            .add_environment_variable("APP_ENV", environment.value)
            .set_health_check("/health")
            .finalize_deployment_config()
            .build()
        )

    def create_production_database_server(self) -> ServerConfiguration:
        """Create a production-ready database server"""
        # TODO: Implement production database configuration
        # - Higher specs
        # - Strict security
        # - Database-specific ports
        # - Production environment settings
        return (
            self._builder.set_server_type(ServerType.DATABASE)
            .set_environment(Environment.PRODUCTION)
            .set_specs(cpu_cores=4, ram_gb=16, storage_gb=200)
            .add_port(5432, Protocol.TCP)
            .finalize_network_config()
            .set_ssl_certificates("/path/to/prod/cert", "/path/to/prod/key")
            .add_firewall_rule("allow port 5432")
            .finalize_security_config()
            .add_environment_variable("DB_ENV", "production")
            .set_health_check("/db-health")
            .finalize_deployment_config()
            .build()
        )

    def create_development_server(self, server_type: ServerType) -> ServerConfiguration:
        """Create a development server with relaxed settings"""
        # TODO: Implement development configuration
        return (
            self._builder.set_server_type(server_type)
            .set_environment(Environment.DEVELOPMENT)
            .set_specs(cpu_cores=1, ram_gb=2, storage_gb=20)
            .add_port(8080, Protocol.HTTP)
            .finalize_network_config()
            .finalize_security_config()
            .add_environment_variable("APP_ENV", "development")
            .set_health_check("/health")
            .finalize_deployment_config()
            .build()
        )


# ============================================================================
# EXAMPLE USAGE (for your testing)
# ============================================================================

if __name__ == "__main__":
    # Example of how the builder should work:

    builder = ServerConfigurationBuilder()
    director = ServerConfigurationDirector(builder)

    try:
        # This should work - step by step configuration
        config = (
            builder.set_server_type(ServerType.WEB)
            .set_environment(Environment.PRODUCTION)
            .set_specs(cpu_cores=4, ram_gb=8, storage_gb=100)
            .add_port(80, Protocol.HTTP)
            .add_port(443, Protocol.HTTPS)
            .enable_ssl()
            .finalize_network_config()
            .set_ssl_certificates("/path/to/cert", "/path/to/key")
            .add_firewall_rule("allow port 80")
            .add_firewall_rule("allow port 443")
            .finalize_security_config()
            .add_environment_variable("APP_ENV", "production")
            .set_health_check("/health")
            .finalize_deployment_config()
            .build()
        )

        print("✅ Configuration built successfully!")
        print(f"Server Type: {config.server_type}")
        print(f"Environment: {config.environment}")

    except Exception as e:
        print(f"❌ Configuration failed: {e}")

    # Test rollback functionality
    print("\n=== Testing Rollback ===")
    try:
        builder2 = ServerConfigurationBuilder()
        (
            builder2.set_server_type(ServerType.WEB)
            .set_environment(Environment.DEVELOPMENT)
            .set_specs(cpu_cores=2, ram_gb=4, storage_gb=50)
            .add_port(8080, Protocol.HTTP)
        )
        print(f"Current state: {builder2.get_current_state()}")
        print(f"Operations: {builder2.get_operation_history()}")

        # Rollback last operation
        builder2.rollback(1)
        print(f"After rollback: {builder2.get_current_state()}")

    except Exception as e:
        print(f"❌ Rollback test failed: {e}")

    # Test director patterns
    print("\n=== Testing Director ===")
    try:
        web_config = director.create_simple_web_server(Environment.STAGING)
        print("✅ Simple web server created via director")

    except Exception as e:
        print(f"❌ Director test failed: {e}")
