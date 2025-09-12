from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from enum import Enum
import time
from dataclasses import dataclass
import importlib
import inspect
import os
import sys
import random
from contextlib import contextmanager
import psutil


class ProcessingEngine(Enum):
    PANDAS = "pandas"
    SPARK = "spark"
    DASK = "dask"


class DataFormat(Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    AVRO = "avro"


@dataclass
class ProcessingMetrics:
    """Metrics for tracking processing performance"""

    start_time: float = 0.0
    end_time: float = 0.0
    memory_usage: float = 0.0
    rows_processed: int = 0

    @property
    def execution_time(self) -> float:
        return self.end_time - self.start_time

    def start_timer(self) -> None:
        self.start_time = time.time()

    def end_timer(self) -> None:
        self.end_time = time.time()


@dataclass
class ProcessingConfig:
    """Configuration for data processing operations"""

    engine: str = "pandas"
    batch_size: int = 1000
    parallel_workers: int = 1
    memory_limit_mb: int = 1024
    error_handling: str = "strict"  # strict, ignore, coerce
    optimization_level: int = 1  # 1=basic, 2=aggressive


class DataReader(ABC):
    """Abstract interface for reading data from various sources"""

    @abstractmethod
    def read_file(self, file_path: str, format: DataFormat, **kwargs) -> Any:
        """Read data from file"""
        pass

    @abstractmethod
    def read_database(self, connection_string: str, query: str) -> Any:
        """Read data from database"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[DataFormat]:
        """Return list of supported data formats"""
        pass

    @abstractmethod
    def estimate_memory_usage(self, source: str) -> float:
        """Estimate memory usage for reading source"""
        pass


class DataProcessor(ABC):
    """Abstract interface for data processing operations"""

    @abstractmethod
    def filter_data(self, data: Any, condition: str) -> Any:
        """Filter data based on condition"""
        pass

    @abstractmethod
    def aggregate_data(
        self, data: Any, group_by: List[str], aggregations: Dict[str, str]
    ) -> Any:
        """Aggregate data with grouping"""
        pass

    @abstractmethod
    def join_data(
        self, left_data: Any, right_data: Any, join_key: str, join_type: str = "inner"
    ) -> Any:
        """Join two datasets"""
        pass

    @abstractmethod
    def transform_columns(self, data: Any, transformations: Dict[str, str]) -> Any:
        """Apply transformations to columns"""
        pass

    @abstractmethod
    def get_data_info(self, data: Any) -> Dict[str, Any]:
        """Get information about the dataset"""
        pass


class DataWriter(ABC):
    """Abstract interface for writing data to various destinations"""

    @abstractmethod
    def write_file(
        self, data: Any, file_path: str, format: DataFormat, **kwargs
    ) -> bool:
        """Write data to file"""
        pass

    @abstractmethod
    def write_database(
        self, data: Any, connection_string: str, table_name: str
    ) -> bool:
        """Write data to database"""
        pass

    @abstractmethod
    def write_stream(self, data: Any, stream_config: Dict[str, Any]) -> bool:
        """Write data to streaming platform"""
        pass


class DataProcessingFactory(ABC):
    """Abstract factory for creating data processing components"""

    @abstractmethod
    def create_reader(self) -> DataReader:
        """Create a data reader for this engine"""
        pass

    @abstractmethod
    def create_processor(self) -> DataProcessor:
        """Create a data processor for this engine"""
        pass

    @abstractmethod
    def create_writer(self) -> DataWriter:
        """Create a data writer for this engine"""
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """Get the name of this processing engine"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities and limitations of this engine"""
        pass

    @abstractmethod
    def validate_config(self, config: ProcessingConfig) -> List[str]:
        """Validate configuration for this engine"""
        pass


class PandasDataReader(DataReader):
    def read_file(self, file_path: str, format: DataFormat, **kwargs) -> Any:
        # TODO: Implement file reading with pandas
        # Handle CSV, JSON, Parquet formats
        # Include error handling and memory optimization
        print(f"Reading {format.value} file from {file_path} with pandas.")
        return {"data": "sample"}  # Placeholder return

    def read_database(self, connection_string: str, query: str) -> Any:
        # TODO: Implement database reading with pandas
        print(
            f"Reading data from database with connection {connection_string} using query: {query}"
        )
        return {"data": "sample"}  # Placeholder return

    def get_supported_formats(self) -> List[DataFormat]:
        # TODO: Return supported formats for pandas
        return [DataFormat.CSV, DataFormat.JSON, DataFormat.PARQUET]

    def estimate_memory_usage(self, source: str) -> float:
        # TODO: Estimate memory usage
        return random.uniform(50.0, 500.0)  # Placeholder implementation


class PandasDataProcessor(DataProcessor):
    def filter_data(self, data: Any, condition: str) -> Any:
        # TODO: Implement pandas filtering
        print(f"Filtering data with condition: {condition}")
        return data  # Placeholder return

    def aggregate_data(
        self, data: Any, group_by: List[str], aggregations: Dict[str, str]
    ) -> Any:
        # TODO: Implement pandas aggregation
        print(f"Aggregating data by {group_by} with aggregations: {aggregations}")
        return data  # Placeholder return

    def join_data(
        self, left_data: Any, right_data: Any, join_key: str, join_type: str = "inner"
    ) -> Any:
        # TODO: Implement pandas joins
        print(f"Joining data on key {join_key} with join type {join_type}")
        return left_data  # Placeholder return

    def transform_columns(self, data: Any, transformations: Dict[str, str]) -> Any:
        # TODO: Implement column transformations
        print(f"Transforming columns with: {transformations}")
        return data  # Placeholder return

    def get_data_info(self, data: Any) -> Dict[str, Any]:
        # TODO: Return dataset information
        return dict(
            num_rows=1000, num_columns=10, estimated_memory_mb=1024
        )  # Placeholder return


class PandasDataWriter(DataWriter):
    def write_file(
        self, data: Any, file_path: str, format: DataFormat, **kwargs
    ) -> bool:
        # TODO: Implement file writing with pandas
        print(f"Writing data to {format.value} file at {file_path} with pandas.")
        return True

    def write_database(
        self, data: Any, connection_string: str, table_name: str
    ) -> bool:
        # TODO: Implement database writing
        print(
            f"Writing data to database table {table_name} with connection {connection_string}."
        )
        return True

    def write_stream(self, data: Any, stream_config: Dict[str, Any]) -> bool:
        # TODO: Implement streaming output
        print(f"Writing data to stream with config: {stream_config}")
        return True


class PandasFactory(DataProcessingFactory):
    def create_reader(self) -> DataReader:
        return PandasDataReader()

    def create_processor(self) -> DataProcessor:
        return PandasDataProcessor()

    def create_writer(self) -> DataWriter:
        return PandasDataWriter()

    def get_engine_name(self) -> str:
        return "Pandas"

    def get_capabilities(self) -> Dict[str, Any]:
        # TODO: Return pandas capabilities
        return {
            "max_memory_gb": 16,
            "supports_distributed": False,
            "supports_streaming": False,
            "supported_formats": ["csv", "json", "parquet"],
            "performance_tier": "medium",
        }

    def validate_config(self, config: ProcessingConfig) -> List[str]:
        # TODO: Validate configuration for pandas
        errors = []

        if config.memory_limit_mb > 16384:
            errors.append("Pandas engine supports up to 16GB memory limit.")
        if config.parallel_workers > 1:
            errors.append("Pandas engine does not support parallel workers.")

        return errors


class SparkDataReader(DataReader):
    """TODO: Implement Spark data reader"""

    # Similar structure to PandasDataReader
    pass


class SparkDataProcessor(DataProcessor):
    """TODO: Implement Spark data processor"""

    # Similar structure to PandasDataProcessor
    pass


class SparkDataWriter(DataWriter):
    """TODO: Implement Spark data writer"""

    # Similar structure to PandasDataWriter
    pass


class SparkFactory(DataProcessingFactory):
    """TODO: Implement Spark factory"""

    def create_reader(self) -> DataReader:
        return SparkDataReader()

    def create_processor(self) -> DataProcessor:
        return SparkDataProcessor()

    def create_writer(self) -> DataWriter:
        return SparkDataWriter()

    def get_engine_name(self) -> str:
        return "Spark"

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "max_memory_gb": 1000,
            "supports_distributed": True,
            "supports_streaming": True,
            "supported_formats": ["csv", "json", "parquet", "avro"],
            "performance_tier": "high",
        }

    def validate_config(self, config: ProcessingConfig) -> List[str]:
        # TODO: Spark-specific validation
        return []


class PluginRegistry:
    """Registry for managing data processing plugins"""

    _factories: Dict[str, Type[DataProcessingFactory]] = {}
    _loaded_plugins: Dict[str, DataProcessingFactory] = {}

    @classmethod
    def register_plugin(
        cls, engine_name: str, factory_class: Type[DataProcessingFactory]
    ) -> None:
        """Register a new processing engine plugin"""
        cls._factories[engine_name] = factory_class

    @classmethod
    def discover_plugins(cls, plugin_directory: str = "plugins/") -> List[str]:
        """Automatically discover and load plugins from directory"""
        if not plugin_directory.endswith("/"):
            plugin_directory += "/"

        if not os.path.isdir(plugin_directory):
            return []

        sys.path.insert(0, plugin_directory)
        discovered = []

        for file in os.listdir(plugin_directory):
            if file.endswith(".py") and not file.startswith("_"):
                module_name = file[:-3]
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, DataProcessingFactory)
                            and obj is not DataProcessingFactory
                        ):
                            engine_name = obj().get_engine_name().lower()
                            cls.register_plugin(engine_name, obj)
                            discovered.append(engine_name)
                except Exception as e:
                    print(f"Error loading plugin {module_name}: {e}")

        sys.path.pop(0)
        return discovered

    @classmethod
    def get_factory(cls, engine_name: str) -> DataProcessingFactory:
        """Get factory instance for specified engine"""
        engine_name = engine_name.lower()
        if engine_name in cls._loaded_plugins:
            return cls._loaded_plugins[engine_name]

        if engine_name in cls._factories:
            factory_instance = cls._factories[engine_name]()
            cls._loaded_plugins[engine_name] = factory_instance
            return factory_instance

        raise ValueError(f"Processing engine '{engine_name}' not found.")

    @classmethod
    def list_available_engines(cls) -> List[str]:
        """List all available processing engines"""
        return list(cls._factories.keys())

    @classmethod
    def get_engine_capabilities(cls, engine_name: str) -> Dict[str, Any]:
        """Get capabilities of specified engine"""
        factory = cls.get_factory(engine_name)
        return factory.get_capabilities()


class ProcessingPipeline:
    """Pipeline for chaining data processing operations"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.factory: Optional[DataProcessingFactory] = None
        self.current_data: Any = None
        self.metrics: ProcessingMetrics = ProcessingMetrics()
        self.operation_history: List[Dict[str, Any]] = []
        self.auto_optimized: bool = True
        self.performance_history: List[ProcessingMetrics] = []

    @contextmanager
    def performance_monitor(self, operation: str):
        """Context manager to monitor performance of operations"""
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / (
            1024 * 1024
        )  # in MB
        yield
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / (
            1024 * 1024
        )  # in MB
        memory_used = end_memory - start_memory
        duration = end_time - start_time
        self.performance_history.append(
            dict(operation=operation, duration=duration, memory_used=memory_used)
        )
        print(
            f"Operation '{operation}' took {duration:.2f}s and used {memory_used:.2f}MB memory."
        )

    def auto_optimize_engine(self) -> "ProcessingPipeline":
        """Automatically select the best engine based on data size and operations"""
        if not self.auto_optimized or self.current_data is None:
            return self

        data_info = self.factory.create_processor().get_data_info(self.current_data)
        row_count = data_info.get("num_rows", 0)
        memory_usage = data_info.get("estimated_memory_mb", 0)
        optimal_engine = self._select_optimal_engine(row_count, memory_usage)

        if optimal_engine and optimal_engine != self.config.engine:
            print(
                f"Switching processing engine from {self.config.engine} to {optimal_engine} based on optimization."
            )
            self.set_engine(optimal_engine)

        return self

    def _select_optimal_engine(self, row_count: int, memory_usage: int) -> str:
        """Select the optimal engine based on data size and operation complexity"""
        available_engines = PluginRegistry.list_available_engines()
        best_engine = self.config.engine
        best_score = float("inf")

        for engine in available_engines:
            capabilities = PluginRegistry.get_engine_capabilities(engine)
            score = 0

            if capabilities["max_memory_gb"] * 1024 < memory_usage:
                continue
            if capabilities["supports_distributed"]:
                score -= 10
            if capabilities["performance_tier"] == "high":
                score -= 5
            score += memory_usage / (capabilities["max_memory_gb"] * 1024)
            score += row_count / 1000000  # Assume 1 million rows is a baseline
            if score < best_score:
                best_score = score
                best_engine = engine

        return best_engine

    def set_engine(self, engine_name: str) -> "ProcessingPipeline":
        """Set the processing engine for this pipeline"""
        self.factory = PluginRegistry.get_factory(engine_name)
        errors = self.factory.validate_config(self.config)
        if errors:
            raise ProcessingError(
                f"Configuration errors: {errors}",
                engine_name,
                "set_engine",
                recoverable=False,
            )

        return self

    def load_data(
        self, source: str, format: DataFormat, **kwargs
    ) -> "ProcessingPipeline":
        """Load data from source"""
        with self.performance_monitor("load_data"):
            try:
                reader = self.factory.create_reader()
                self.current_data = reader.read_file(source, format, **kwargs)
                self.metrics.rows_processed = (
                    len(self.current_data)
                    if hasattr(self.current_data, "__len__")
                    else 0
                )
                self.metrics.memory_usage = reader.estimate_memory_usage(source)
                self.metrics.start_timer()
                self.operation_history.append(
                    {"operation": "load_data", "source": source, "format": format.name}
                )

                self.auto_optimize_engine()
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.load_data(source, format, **kwargs)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "load_data", recoverable=False
                )

        return self

    def filter(self, condition: str) -> "ProcessingPipeline":
        """Filter data based on condition"""
        with self.performance_monitor("filter"):
            try:
                if not self.factory:
                    raise ProcessingError(
                        "Processing engine not set. Call set_engine() first.",
                        self.config.engine,
                        "filter",
                        recoverable=False,
                    )
                if self.current_data is None:
                    raise ProcessingError(
                        "No data loaded. Call load_data() first.",
                        self.config.engine,
                        "filter",
                        recoverable=False,
                    )

                processor = self.factory.create_processor()
                self.current_data = processor.filter_data(self.current_data, condition)
                self.operation_history.append(
                    {"operation": "filter", "condition": condition}
                )
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.filter(condition)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "filter", recoverable=False
                )

        return self

    def aggregate(
        self, group_by: List[str], aggregations: Dict[str, str]
    ) -> "ProcessingPipeline":
        """Aggregate data"""
        with self.performance_monitor("aggregate"):
            try:
                if not self.factory:
                    raise ProcessingError(
                        "Processing engine not set. Call set_engine() first.",
                        self.config.engine,
                        "aggregate",
                        recoverable=False,
                    )
                if self.current_data is None:
                    raise ProcessingError(
                        "No data loaded. Call load_data() first.",
                        self.config.engine,
                        "aggregate",
                        recoverable=False,
                    )

                processor = self.factory.create_processor()
                self.current_data = processor.aggregate_data(
                    self.current_data, group_by, aggregations
                )
                self.operation_history.append(
                    {
                        "operation": "aggregate",
                        "group_by": group_by,
                        "aggregations": aggregations,
                    }
                )
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.aggregate(group_by, aggregations)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "aggregate", recoverable=False
                )
        return self

    def join(
        self, other_data: Any, join_key: str, join_type: str = "inner"
    ) -> "ProcessingPipeline":
        """Join with another dataset"""
        with self.performance_monitor("join"):
            try:
                if not self.factory:
                    raise ProcessingError(
                        "Processing engine not set. Call set_engine() first.",
                        self.config.engine,
                        "join",
                        recoverable=False,
                    )
                if self.current_data is None:
                    raise ProcessingError(
                        "No data loaded. Call load_data() first.",
                        self.config.engine,
                        "join",
                        recoverable=False,
                    )

                processor = self.factory.create_processor()
                self.current_data = processor.join_data(
                    self.current_data, other_data, join_key, join_type
                )
                self.operation_history.append(
                    {"operation": "join", "join_key": join_key, "join_type": join_type}
                )
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.join(other_data, join_key, join_type)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "join", recoverable=False
                )

        return self

    def transform(self, transformations: Dict[str, str]) -> "ProcessingPipeline":
        """Transform columns"""
        with self.performance_monitor("transform"):
            try:
                if not self.factory:
                    raise ProcessingError(
                        "Processing engine not set. Call set_engine() first.",
                        self.config.engine,
                        "transform",
                        recoverable=False,
                    )
                if self.current_data is None:
                    raise ProcessingError(
                        "No data loaded. Call load_data() first.",
                        self.config.engine,
                        "transform",
                        recoverable=False,
                    )

                processor = self.factory.create_processor()
                self.current_data = processor.transform_columns(
                    self.current_data, transformations
                )
                self.operation_history.append(
                    {"operation": "transform", "transformations": transformations}
                )
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.transform(transformations)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "transform", recoverable=False
                )

        return self

    def save(self, destination: str, format: DataFormat, **kwargs) -> Dict[str, Any]:
        """Save processed data to destination"""
        # TODO: Implement data saving
        # - Use factory's writer
        # - Save with error handling
        # - Return final metrics and summary
        with self.performance_monitor("save"):
            try:
                if not self.factory:
                    raise ProcessingError(
                        "Processing engine not set. Call set_engine() first.",
                        self.config.engine,
                        "save",
                        recoverable=False,
                    )
                if self.current_data is None:
                    raise ProcessingError(
                        "No data loaded. Call load_data() first.",
                        self.config.engine,
                        "save",
                        recoverable=False,
                    )

                writer = self.factory.create_writer()
                success = writer.write_file(
                    self.current_data, destination, format, **kwargs
                )
                if not success:
                    raise ProcessingError(
                        "Failed to write data.",
                        self.config.engine,
                        "save",
                        recoverable=False,
                    )

                self.metrics.end_timer()
                self.operation_history.append(
                    {
                        "operation": "save",
                        "destination": destination,
                        "format": format.name,
                    }
                )

                return {
                    "rows_processed": self.metrics.rows_processed,
                    "execution_time_sec": self.metrics.execution_time,
                    "memory_usage_mb": self.metrics.memory_usage,
                    "engine_used": self.config.engine,
                }
            except ProcessingError as e:
                if ErrorRecoveryManager.handle_engine_failure(self, e):
                    return self.save(destination, format, **kwargs)
                else:
                    raise
            except Exception as e:
                raise ProcessingError(
                    str(e), self.config.engine, "save", recoverable=False
                )

    def get_metrics(self) -> ProcessingMetrics:
        """Get processing metrics"""
        return self.metrics

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of all operations performed"""
        return self.operation_history

    def get_performance_history(self) -> List[ProcessingMetrics]:
        """Get detailed performance metrics for each operation"""
        return self.performance_history

    def rollback_to_step(self, step_index: int) -> "ProcessingPipeline":
        """Rollback pipeline to a previous step"""
        # TODO: Implement rollback functionality
        if step_index < 0 or step_index >= len(self.operation_history):
            raise ValueError("Invalid step index for rollback.")
        # For simplicity, just clear operations after step_index
        self.operation_history = self.operation_history[: step_index + 1]

        return self


class ProcessingError(Exception):
    """Custom exception for processing errors"""

    def __init__(
        self, message: str, engine: str, operation: str, recoverable: bool = True
    ):
        super().__init__(message)
        self.engine = engine
        self.operation = operation
        self.recoverable = recoverable


class ErrorRecoveryManager:
    """Manages error recovery strategies"""

    @staticmethod
    def handle_engine_failure(
        pipeline: ProcessingPipeline, error: ProcessingError
    ) -> bool:
        """Handle engine failure with fallback strategies"""
        # TODO: Implement error recovery
        # - Try alternative engine
        # - Reduce batch size
        # - Switch to streaming mode
        # - Return success/failure status
        if not error.recoverable:
            return False

        available_engines = PluginRegistry.list_available_engines()
        for engine in available_engines:
            if engine != pipeline.config.engine:
                try:
                    # Attempt to switch engine and reconfigure
                    fallback_config = ProcessingConfig(
                        engine=engine,
                        batch_size=max(100, pipeline.config.batch_size // 2),
                        parallel_workers=pipeline.config.parallel_workers,
                        memory_limit_mb=pipeline.config.memory_limit_mb // 2,
                        error_handling=pipeline.config.error_handling,
                        optimization_level=pipeline.config.optimization_level,
                    )
                    pipeline.config = fallback_config
                    pipeline.set_engine(engine)
                    return True
                except Exception:
                    print("Fallback to engine", engine, "failed.")
                    continue

        return False

    @staticmethod
    def suggest_optimization(
        pipeline: ProcessingPipeline, error: ProcessingError
    ) -> List[str]:
        """Suggest optimizations based on error type"""
        suggestions = []

        if "memory" in str(error).lower():
            suggestions.append("Reduce memory limit in configuration.")
            suggestions.append("Switch to a more memory-efficient engine.")
            suggestions.append("Increase batch size to reduce memory overhead.")

        if "timeout" in str(error).lower():
            suggestions.append("Increase timeout settings if applicable.")
            suggestions.append("Optimize data source for faster reads.")
            suggestions.append("Switch to a distributed processing engine.")

        if error.operation == "load_data":
            suggestions.append("Check data source availability and format.")
            suggestions.append("Try loading a smaller subset of data.")

        if error.operation in ["filter", "aggregate", "join", "transform"]:
            suggestions.append(
                "Simplify the operation or reduce data size before processing."
            )
            suggestions.append("Break complex operations into smaller steps.")

        return suggestions


class ProductionConfigManager:
    @staticmethod
    def get_optimized_config(
        workload_type: str, data_size_gb: float
    ) -> ProcessingConfig:
        """Get optimized configuration based on workload type and data size"""
        if workload_type == "batch":
            if data_size_gb < 1:
                return ProcessingConfig(
                    engine="pandas",
                    batch_size=1000,
                    parallel_workers=1,
                    memory_limit_mb=2048,
                )
            if data_size_gb < 10:
                return ProcessingConfig(
                    engine="dask",
                    batch_size=5000,
                    parallel_workers=4,
                    memory_limit_mb=8192,
                )
            return ProcessingConfig(
                engine="spark",
                batch_size=10000,
                parallel_workers=8,
                memory_limit_mb=16384,
            )
        if workload_type == "streaming":
            return ProcessingConfig(
                engine="spark",
                batch_size=1000,
                parallel_workers=4,
                memory_limit_mb=8192,
            )
        raise ValueError(
            "Unknown workload type. Supported types: 'batch', 'streaming'."
        )


def demo_plugin_system():
    """Demonstrate the plugin architecture"""

    # Register built-in factories
    PluginRegistry.register_plugin("pandas", PandasFactory)
    PluginRegistry.register_plugin("spark", SparkFactory)

    # Discover external plugins
    discovered = PluginRegistry.discover_plugins("plugins/")
    print(f"Discovered plugins: {discovered}")

    # List available engines
    engines = PluginRegistry.list_available_engines()
    print(f"Available processing engines: {engines}")

    # Get optimized config for a sample workload
    config = ProductionConfigManager.get_optimized_config(
        "batch", 0.5
    )  # pandas for small data
    print(f"Optimized config: {config}")

    # Create processing pipeline
    pipeline = ProcessingPipeline(config)
    pipeline.set_engine(config.engine)

    try:
        # Load data
        pipeline.load_data("data/sample.csv", DataFormat.CSV)

        # Perform operations
        pipeline.filter("age > 30").aggregate(
            ["country"], {"salary": "mean"}
        ).transform({"salary": "salary * 1.1"})

        # Save results
        result = pipeline.save("data/output.csv", DataFormat.CSV)
        print(f"Processing result: {result}")
    except ProcessingError as e:
        print(f"Processing error: {e}")
        suggestions = ErrorRecoveryManager.suggest_optimization(pipeline, e)
        print("Optimization suggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")


def test_plugin_architecture():
    """Test suite for the plugin architecture"""
    # TODO: Implement tests
    # - Test plugin registration
    # - Test factory creation
    # - Test pipeline operations
    # - Test error scenarios
    # - Test performance with different engines
    pass


if __name__ == "__main__":
    # Initialize the system
    print("Initializing Plugin Architecture...")

    # Run demo
    demo_plugin_system()

    # Run tests
    test_plugin_architecture()
