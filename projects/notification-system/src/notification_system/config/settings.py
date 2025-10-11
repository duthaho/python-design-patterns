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
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

        try:
            with open(path, "r") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {str(e)}")
        except FileNotFoundError:
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

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
            raise ConfigurationError(
                f"Channel '{channel_name}' not found in configuration"
            )
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
        pattern = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")

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
        if "channels" in config:
            self._validate_channel_config(config["channels"])
        elif "events" in config:
            self._validate_event_config(config["events"])
        else:
            raise ConfigurationError(
                "Configuration must contain either 'channels' or 'events' section"
            )

    def _validate_channel_config(self, config: Dict[str, Any]) -> None:
        """Validate individual channel configuration."""
        if not isinstance(config, dict):
            raise ConfigurationError("Channels configuration must be a dictionary")

        for name, channel_cfg in config.items():
            if not isinstance(channel_cfg, dict):
                raise ConfigurationError(
                    f"Channel '{name}' configuration must be a dictionary"
                )
            if "type" not in channel_cfg:
                raise ConfigurationError(f"Channel '{name}' missing required 'type'")
            if "enabled" in channel_cfg and not isinstance(
                channel_cfg["enabled"], bool
            ):
                raise ConfigurationError(
                    f"Channel '{name}' 'enabled' must be a boolean"
                )
            if "config" in channel_cfg and not isinstance(channel_cfg["config"], dict):
                raise ConfigurationError(
                    f"Channel '{name}' 'config' must be a dictionary"
                )
            if "decorators" in channel_cfg:
                if not isinstance(channel_cfg["decorators"], list) or not all(
                    isinstance(d, dict) for d in channel_cfg["decorators"]
                ):
                    raise ConfigurationError(
                        f"Channel '{name}' 'decorators' must be a list of dictionaries"
                    )

    def _validate_event_config(self, config: Dict[str, Any]) -> None:
        """Validate event configuration structure."""
        if not isinstance(config, dict):
            raise ConfigurationError("Events configuration must be a dictionary")

        for event_type, event_cfg in config.items():
            if not isinstance(event_cfg, dict):
                raise ConfigurationError(
                    f"Event '{event_type}' configuration must be a dictionary"
                )
            if "channels" in event_cfg:
                if not isinstance(event_cfg["channels"], list) or not all(
                    isinstance(c, str) for c in event_cfg["channels"]
                ):
                    raise ConfigurationError(
                        f"Event '{event_type}' 'channels' must be a list of strings"
                    )
            if "priority" in event_cfg:
                if event_cfg["priority"] not in {
                    "low",
                    "normal",
                    "medium",
                    "high",
                    "critical",
                }:
                    raise ConfigurationError(
                        f"Event '{event_type}' has invalid 'priority' value"
                    )
            if "template" in event_cfg:
                if not isinstance(event_cfg["template"], dict):
                    raise ConfigurationError(
                        f"Event '{event_type}' 'template' must be a dictionary"
                    )
                if "subject" not in event_cfg["template"]:
                    raise ConfigurationError(
                        f"Event '{event_type}' template missing required 'subject'"
                    )
                if "body" not in event_cfg["template"]:
                    raise ConfigurationError(
                        f"Event '{event_type}' template missing required 'body'"
                    )

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
