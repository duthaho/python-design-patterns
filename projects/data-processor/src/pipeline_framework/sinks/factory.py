"""Factory for creating data sinks."""

from typing import Any, Dict, Optional, Type

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.adapters.csv_adapter import CSVAdapter
from pipeline_framework.adapters.json_adapter import JSONAdapter
from pipeline_framework.sinks.base import Sink
from pipeline_framework.sinks.file import CSVFileSink, JSONFileSink
from pipeline_framework.sinks.memory import ConsoleSink, MemorySink


class SinkFactory:
    """
    Factory for creating data sinks.
    Demonstrates the Factory Pattern.
    """

    # Registry of sink types
    _sink_types: Dict[str, Type[Sink]] = {
        "memory": MemorySink,
        "console": ConsoleSink,
        "csv_file": CSVFileSink,
        "json_file": JSONFileSink,
    }

    @classmethod
    def register_sink_type(cls, name: str, sink_class: Type[Sink]) -> None:
        """
        Register a new sink type.
        """
        if name in cls._sink_types:
            raise ValueError(f"Sink type '{name}' is already registered.")
        cls._sink_types[name] = sink_class

    @classmethod
    def create(cls, sink_type: str, *args: Any, **kwargs: Any) -> Sink:
        """
        Create a sink with simple arguments.
        """
        if sink_type not in cls._sink_types:
            raise ValueError(f"Unknown sink type '{sink_type}'")
        sink_class = cls._sink_types[sink_type]
        return sink_class(*args, **kwargs)

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> Sink:
        """
        Create a sink from configuration dictionary.

        Config structure:
        {
            "type": "json_file",
            "file_path": "output.json",
            "json_lines": true,
            "indent": 2,
            "adapter": {
                "include_processing_info": true
            }
        }
        """
        if "type" not in config:
            raise ValueError("Config must include 'type' field")
        sink_type = config["type"]
        if sink_type not in cls._sink_types:
            raise ValueError(f"Unknown sink type '{sink_type}'")

        sink_class = cls._sink_types[sink_type]

        # Extract adapter config if present
        adapter_config = config.get("adapter")
        adapter = cls._create_adapter(adapter_config, sink_type)

        # Prepare arguments for sink constructor
        init_args = {k: v for k, v in config.items() if k != "type" and k != "adapter"}
        if adapter is not None:
            init_args["adapter"] = adapter

        return cls.create(sink_type, **init_args)

    @classmethod
    def _create_adapter(
        cls, adapter_config: Optional[Dict[str, Any]], sink_type: str
    ) -> Optional[DataAdapter]:
        """
        Create an adapter from configuration.
        """
        if adapter_config is None:
            return None

        if sink_type == "csv_file":
            return CSVAdapter(
                id_field=adapter_config.get("id_field", "id"),
                metadata_prefix=adapter_config.get("metadata_prefix", "_meta_"),
                include_metadata_fields=adapter_config.get("include_metadata_fields", True),
            )
        elif sink_type == "json_file":
            return JSONAdapter(
                id_field=adapter_config.get("id_field", "id"),
                include_processing_info=adapter_config.get("include_processing_info", False),
            )
        
        return None

    @classmethod
    def list_available_types(cls) -> list[str]:
        """
        List all registered sink types.
        """
        return list(cls._sink_types.keys())


class SinkConfigBuilder:
    """
    Builder for sink configurations.
    """

    def __init__(self, sink_type: str):
        """Initialize config builder."""
        self._config: Dict[str, Any] = {"type": sink_type}

    def with_path(self, path: str) -> "SinkConfigBuilder":
        """Set file path."""
        self._config["file_path"] = path
        return self

    def with_encoding(self, encoding: str) -> "SinkConfigBuilder":
        """Set file encoding."""
        self._config["encoding"] = encoding
        return self

    def with_adapter(self, **adapter_kwargs: Any) -> "SinkConfigBuilder":
        """Configure adapter settings."""
        self._config["adapter"] = adapter_kwargs
        return self

    def with_json_lines(self, json_lines: bool = True) -> "SinkConfigBuilder":
        """Enable JSON Lines format."""
        self._config["json_lines"] = json_lines
        return self

    def with_mode(self, mode: str) -> "SinkConfigBuilder":
        """Set file mode (w/a)."""
        self._config["mode"] = mode
        return self

    def build(self) -> Dict[str, Any]:
        """Build the configuration dictionary."""
        return self._config
