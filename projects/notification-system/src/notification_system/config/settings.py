"""
Configuration loader with environment variable support.
Pattern: Configuration management with validation
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class Settings:
    """
    Loads and manages configuration from YAML files.

    Supports:
    - Environment variable substitution: ${VAR_NAME:default_value}
    - Nested configuration
    - Validation
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize settings."""
        self.config_path = config_path or "config/channels.yaml"
        self.config = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        path = Path(self.config_path)
        if not path.is_file():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")

        try:
            with open(path, "r") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {str(e)}")
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")

        if raw_config is None:
            raw_config = {}

        if not isinstance(raw_config, dict):
            raise ConfigurationError("Configuration root must be a dictionary")

        substituted_config = self._substitute_env_vars(raw_config)
        self._validate(substituted_config)
        self.config = substituted_config
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        parts = key.split(".")
        value = self.config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def get_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """Get full configuration for a specific channel."""
        channels = self.config.get("channels", {})
        if channel_name not in channels:
            raise ConfigurationError(f"Channel '{channel_name}' not found in configuration")
        return channels[channel_name]

    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config."""
        if isinstance(config, str):
            return self._parse_env_var(config)
        elif isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        else:
            return config

    def _parse_env_var(self, value: str) -> str:
        """Parse environment variable pattern and return value."""
        pattern = re.compile(r'\$\{([^}:]+)(?::([^}]+))?\}')
    
        def replace_match(match):
            var_name = match.group(1)
            default = match.group(2)
            env_value = os.getenv(var_name, default)
            if env_value is None:
                raise ConfigurationError(
                    f"Environment variable '{var_name}' not set and no default provided"
                )
            return env_value
        
        # Replace all ${...} patterns in the string
        return pattern.sub(replace_match, value)

    def _validate(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure."""
        if "channels" not in config or not isinstance(config["channels"], dict):
            raise ConfigurationError("Configuration must contain a 'channels' dictionary")
        valid_decorators = {"logging", "retry", "rate_limit"}
        for channel_name, channel_cfg in config["channels"].items():
            if not isinstance(channel_cfg, dict):
                raise ConfigurationError(f"Channel '{channel_name}' configuration must be a dictionary")
            if "type" not in channel_cfg or not isinstance(channel_cfg["type"], str):
                raise ConfigurationError(f"Channel '{channel_name}' must have a 'type' string")
            if "config" not in channel_cfg or not isinstance(channel_cfg["config"], dict):
                raise ConfigurationError(f"Channel '{channel_name}' must have a 'config' dictionary")
            decorators = channel_cfg.get("decorators", [])
            if not isinstance(decorators, list):
                raise ConfigurationError(f"Channel '{channel_name}' decorators must be a list")
            for decorator in decorators:
                decorator_type = decorator.get("type") if isinstance(decorator, dict) else decorator
                if decorator_type not in valid_decorators:
                    raise ConfigurationError(f"Invalid decorator '{decorator_type}' in channel '{channel_name}'")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Settings":
        """Create Settings from dictionary (for testing)."""
        instance = cls(config_path="")  # Bypass file loading
        instance._validate(config_dict)
        instance.config = config_dict
        return instance

    def __repr__(self) -> str:
        """String representation."""
        return f"Settings(config_path='{self.config_path}')"
