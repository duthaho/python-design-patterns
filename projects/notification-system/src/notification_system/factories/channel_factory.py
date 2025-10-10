"""
Factory for creating notification channels.
Pattern: Abstract Factory + Registry
"""

import logging
from typing import Any, Dict, Optional, Type

from ..channels.base import NotificationChannel
from ..channels.console import ConsoleChannel
from ..channels.email import EmailChannel
from ..channels.webhook import WebhookChannel
from ..config.settings import ConfigurationError, Settings
from .decorator_factory import DecoratorFactory


class ChannelFactory:
    """
    Factory for creating fully configured notification channels.

    Features:
    - Channel registry (built-in + custom)
    - Automatic decorator application
    - Configuration-driven creation
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize channel factory."""
        self.settings = settings or Settings()
        self.decorator_factory = DecoratorFactory()
        self.logger = logging.getLogger(self.__class__.__name__)

        self._registry: Dict[str, Type[NotificationChannel]] = {}

        self._register_builtin_channels()

    def _register_builtin_channels(self) -> None:
        """Register built-in channel classes."""
        self._registry["ConsoleChannel"] = ConsoleChannel
        self._registry["EmailChannel"] = EmailChannel
        self._registry["WebhookChannel"] = WebhookChannel

    def register(self, name: str, channel_class: Type[NotificationChannel]) -> None:
        """Register a custom channel class."""
        if not isinstance(name, str) or not name:
            raise ValueError("Channel name must be a non-empty string")

        # Check if it's actually a class
        if not isinstance(channel_class, type):
            raise ValueError(
                f"channel_class must be a class, got {type(channel_class)}"
            )

        # Check if it's a subclass of NotificationChannel
        try:
            if not issubclass(channel_class, NotificationChannel):
                raise ValueError(
                    f"channel_class must be a subclass of NotificationChannel, "
                    f"got {channel_class}"
                )
        except TypeError:
            raise ValueError(f"channel_class must be a class, got {channel_class}")

        if name in self._registry:
            self.logger.warning(
                f"Overwriting existing channel registration for '{name}'"
            )

        self._registry[name] = channel_class
        self.logger.info(f"Registered channel '{name}': {channel_class.__name__}")

    def create(self, channel_name: str, **override_config) -> NotificationChannel:
        """Create a fully configured channel from config."""
        channel_config = self.settings.get_channel_config(channel_name)
        if not channel_config.get("enabled", True):
            raise ConfigurationError(f"Channel '{channel_name}' is disabled")

        channel_type = channel_config["type"]
        if channel_type not in self._registry:
            raise ValueError(f"Unknown channel type: {channel_type}")

        channel_class = self._registry[channel_type]
        config = {**channel_config.get("config", {}), **override_config}
        channel = channel_class(config=config)

        decorators = channel_config.get("decorators", [])
        if decorators:
            channel = self.decorator_factory.apply_decorators(channel, decorators)

        self.logger.info(f"Created channel: {channel_name} ({channel_type})")
        return channel

    def create_from_config(
        self,
        channel_type: str,
        config: Dict[str, Any],
        decorators: Optional[list] = None,
    ) -> NotificationChannel:
        """Create channel directly from config dict (without Settings)."""
        if channel_type not in self._registry:
            raise ValueError(f"Unknown channel type: {channel_type}")

        channel_class = self._registry[channel_type]
        channel = channel_class(config=config)

        if decorators:
            channel = self.decorator_factory.apply_decorators(channel, decorators)

        self.logger.info(f"Created channel from config: {channel_type}")
        return channel

    def list_channels(self) -> list:
        """List all available channel names from config."""
        channels = self.settings.config.get("channels", {})
        return [name for name, cfg in channels.items() if cfg.get("enabled", True)]

    def list_channel_types(self) -> list:
        """List all registered channel types."""
        return list(self._registry.keys())
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all configured channels.
        
        Returns:
            Dict mapping channel names to health status
        """
        results = {}
        for channel_name in self.list_channels():
            try:
                channel = self.create(channel_name)
                results[channel_name] = channel.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {channel_name}: {e}")
                results[channel_name] = False
        return results

    @classmethod
    def from_config(cls, config_path: str) -> "ChannelFactory":
        """Create factory from config file path."""
        settings = Settings(config_path=config_path)
        return cls(settings=settings)

    def __repr__(self) -> str:
        """String representation."""
        channels = self.list_channels() if hasattr(self, "settings") else []
        return f"ChannelFactory(channels={channels})"
