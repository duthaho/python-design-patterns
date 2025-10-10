"""
Factory for creating decorators.
Pattern: Factory Method
"""

import logging
from typing import Any, Dict, Type

from ..channels.base import ChannelProtocol
from ..decorators.logging import LoggingDecorator
from ..decorators.rate_limit import RateLimitDecorator
from ..decorators.retry import RetryDecorator


class DecoratorFactory:
    """
    Factory for creating channel decorators.
    
    Maintains a registry of available decorators and creates them
    from configuration.
    """
    
    def __init__(self):
        """Initialize decorator factory with built-in decorators."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._registry: Dict[str, Type] = {
            'retry': RetryDecorator,
            'logging': LoggingDecorator,
            'rate_limit': RateLimitDecorator,
        }
    
    def create(
        self,
        decorator_type: str,
        wrapped: ChannelProtocol,
        config: Dict[str, Any]
    ) -> ChannelProtocol:
        """Create a decorator wrapping the given channel."""
        if decorator_type not in self._registry:
            raise ValueError(f"Unknown decorator type: {decorator_type}")
        
        decorator_class = self._registry[decorator_type]
        
        try:
            decorator_instance = decorator_class(wrapped, **config)
        except TypeError as e:
            raise ValueError(f"Invalid config for {decorator_type} decorator: {e}")
        
        self.logger.debug(f"Created {decorator_type} decorator with config: {config}")
        
        return decorator_instance
    
    def register(self, name: str, decorator_class: Type) -> None:
        """Register a custom decorator."""
        if not isinstance(name, str) or not name:
            raise ValueError("Decorator name must be a non-empty string")
        
        if name in self._registry:
            self.logger.warning(f"Overwriting existing decorator registration for '{name}'")
        
        self._registry[name] = decorator_class
        self.logger.info(f"Registered decorator '{name}'")
    
    def apply_decorators(
        self,
        channel: ChannelProtocol,
        decorator_configs: list
    ) -> ChannelProtocol:
        """Apply multiple decorators to a channel in order."""
        result = channel
        for decorator_cfg in decorator_configs:
            if 'type' not in decorator_cfg:
                raise ValueError("Decorator config must include 'type' key")
            decorator_type = decorator_cfg['type']
            config = {k: v for k, v in decorator_cfg.items() if k != 'type'}
            result = self.create(decorator_type, result, config)
        return result
    
    def list_decorators(self) -> list:
        """List all registered decorator types."""
        return list(self._registry.keys())
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DecoratorFactory(decorators={list(self._registry.keys())})"