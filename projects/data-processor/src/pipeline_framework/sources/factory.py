"""Factory for creating data sources."""

from pathlib import Path
from typing import Any, Dict, Optional, Type

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.adapters.csv_adapter import CSVAdapter
from pipeline_framework.adapters.json_adapter import JSONAdapter
from pipeline_framework.sources.base import Source
from pipeline_framework.sources.file import (CSVFileSource, CSVStreamSource,
                                             JSONFileSource)
from pipeline_framework.sources.memory import (ListSource, MemorySource,
                                               MemoryStreamSource)


class SourceFactory:
    """
    Factory for creating data sources.
    Demonstrates the Factory Pattern.
    """

    # Registry of source types
    _source_types: Dict[str, Type[Source]] = {
        "memory": MemorySource,
        "list": ListSource,
        "memory_stream": MemoryStreamSource,
        "csv_file": CSVFileSource,
        "json_file": JSONFileSource,
        "csv_stream": CSVStreamSource,
    }

    @classmethod
    def register_source_type(cls, name: str, source_class: Type[Source]) -> None:
        """
        Register a new source type.
        Allows extending the factory with custom sources.

        Args:
            name: Name to identify this source type
            source_class: Source class to register

        Example:
            >>> class MyCustomSource(Source):
            ...     pass
            >>> SourceFactory.register_source_type("custom", MyCustomSource)
        """
        if name in cls._source_types:
            raise ValueError(f"Source type '{name}' is already registered.")
        cls._source_types[name] = source_class

    @classmethod
    def create(cls, source_type: str, *args: Any, **kwargs: Any) -> Source:
        """
        Create a source with simple arguments.

        Args:
            source_type: Type of source to create
            *args: Positional arguments for source constructor
            **kwargs: Keyword arguments for source constructor

        Returns:
            Configured Source instance

        Raises:
            ValueError: If source_type is not registered

        Example:
            >>> source = SourceFactory.create("csv_file", "data.csv")
            >>> source = SourceFactory.create("json_file", "data.json", json_lines=True)
        """
        if source_type not in cls._source_types:
            raise ValueError(
                f"Unknown source type: {source_type}. "
                f"Available types: {', '.join(cls.list_available_types())}"
            )
        source_class = cls._source_types[source_type]
        return source_class(*args, **kwargs)

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> Source:
        """
        Create a source from configuration dictionary.

        Config structure:
        {
            "type": "csv_file",
            "file_path": "data.csv",
            "encoding": "utf-8",
            "adapter": {
                "id_field": "user_id",
                "metadata_prefix": "_meta_"
            }
        }

        Args:
            config: Configuration dictionary

        Returns:
            Configured Source instance

        Raises:
            ValueError: If required config fields are missing
            KeyError: If 'type' is not in config
        """
        if "type" not in config:
            raise KeyError("Configuration must include 'type' field.")

        source_type = config["type"]
        if source_type not in cls._source_types:
            raise ValueError(f"Source type '{source_type}' is not registered.")

        # Extract adapter config
        adapter_config = config.get("adapter")
        adapter = cls._create_adapter(adapter_config, source_type)

        # Build kwargs dynamically, excluding 'type' and 'adapter'
        kwargs = {k: v for k, v in config.items() if k not in ("type", "adapter")}

        # Add adapter if created
        if adapter is not None:
            kwargs["adapter"] = adapter

        # Create the source
        return cls.create(source_type, **kwargs)

    @classmethod
    def _create_adapter(
        cls, adapter_config: Optional[Dict[str, Any]], source_type: str
    ) -> Optional[DataAdapter]:
        """
        Create an adapter from configuration.

        Args:
            adapter_config: Adapter configuration dictionary
            source_type: Type of source (to determine default adapter)

        Returns:
            DataAdapter instance or None
        """
        if adapter_config is None:
            return None

        if source_type == "csv_file":
            return CSVAdapter(
                id_field=adapter_config.get("id_field"),
                include_metadata_fields=adapter_config.get("include_metadata_fields", False),
                metadata_prefix=adapter_config.get("metadata_prefix", "_meta_"),
            )
        elif source_type == "json_file":
            return JSONAdapter(
                id_field=adapter_config.get("id_field"),
                include_processing_info=adapter_config.get("include_processing_info", False),
            )

        return None

    @classmethod
    def list_available_types(cls) -> list[str]:
        """
        List all registered source types.

        Returns:
            List of available source type names
        """
        return list(cls._source_types.keys())


class SourceConfigBuilder:
    """
    Builder for source configurations.
    Makes it easier to create config dictionaries.
    """

    def __init__(self, source_type: str):
        """
        Initialize config builder.

        Args:
            source_type: Type of source
        """
        self._config: Dict[str, Any] = {"type": source_type}

    def with_path(self, path: str) -> "SourceConfigBuilder":
        """
        Set file path.
        """
        self._config["file_path"] = path
        return self

    def with_encoding(self, encoding: str) -> "SourceConfigBuilder":
        """
        Set file encoding.
        """
        self._config["encoding"] = encoding
        return self

    def with_adapter(self, **adapter_kwargs: Any) -> "SourceConfigBuilder":
        """
        Configure adapter settings.
        """
        self._config["adapter"] = adapter_kwargs
        return self

    def with_json_lines(self, json_lines: bool = True) -> "SourceConfigBuilder":
        """
        Enable JSON Lines format.
        """
        self._config["json_lines"] = json_lines
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the configuration dictionary.
        """
        return self._config
