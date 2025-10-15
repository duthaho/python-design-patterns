# Pipeline Framework

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, extensible data pipeline framework for Python that demonstrates 11 design patterns in action. Built for learning, flexibility, and production use.

## 🌟 Features

- **🔗 Flexible Pipeline Construction** - Chain processors with ease using the Builder pattern
- **📊 Multiple Data Sources** - CSV, JSON, Memory, Streaming support
- **💾 Multiple Data Sinks** - File, Console, Memory outputs
- **🎯 Smart Caching** - Built-in caching decorator with automatic eviction
- **🔄 Automatic Retry** - Configurable retry logic with exponential backoff
- **📈 Comprehensive Metrics** - Track throughput, success rates, and performance
- **📝 Event-Driven Observability** - Real-time monitoring with customizable observers
- **⏮️ Undo/Redo Support** - Command pattern for operation rollback
- **🎨 Decorator Stacking** - Compose behaviors with retry, logging, caching, and timing
- **⚙️ Configuration-Driven** - Build pipelines from YAML/JSON configs
- **🧪 Fully Tested** - 95%+ test coverage

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install pipeline-framework

# Using pip
pip install pipeline-framework
```

### Basic Usage

```python
from pipeline_framework import PipelineBuilder
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import UpperCaseTransform

# Build a simple pipeline
pipeline = (
    PipelineBuilder("my-first-pipeline")
    .with_source_config({
        "type": "csv_file",
        "file_path": "input.csv"
    })
    .add_processor(TransformProcessor(UpperCaseTransform()))
    .add_processor(CounterProcessor())
    .with_sink_config({
        "type": "json_file",
        "file_path": "output.json"
    })
    .build_and_run()
)

print(f"Processed {len(pipeline)} items!")
```

## 📖 Table of Contents

- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Usage Examples](#usage-examples)
- [Design Patterns](#design-patterns)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Contributing](#contributing)
- [License](#license)

## 🏗️ Core Concepts

### Processors

Processors are the building blocks of your pipeline. They transform, filter, or enrich data as it flows through.

```python
from pipeline_framework.core.processor import Processor
from pipeline_framework.core.models import ProcessingContext

class MyCustomProcessor(Processor):
    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        # Your processing logic here
        context.data.set_payload_value("processed", True)
        return context
```

### Sources and Sinks

Sources read data into the pipeline, sinks write results out.

```python
# Available Sources
- MemorySource - In-memory data
- ListSource - Python lists/dicts
- CSVFileSource - CSV files
- JSONFileSource - JSON files
- CSVStreamSource - Large CSV files (streaming)

# Available Sinks
- MemorySink - Store in memory
- ConsoleSink - Print to console
- CSVFileSink - Write CSV files
- JSONFileSink - Write JSON files
```

### State Management

Pipelines maintain state across runs, enabling stateful operations like deduplication and aggregation.

```python
from pipeline_framework.processors.stateful import DeduplicationProcessor

pipeline = (
    PipelineBuilder("stateful-pipeline")
    .add_processor(DeduplicationProcessor())  # Skips duplicate IDs
    .build()
)
```

## 💡 Usage Examples

### Example 1: Data Transformation Pipeline

```python
from pipeline_framework import PipelineBuilder
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import (
    UpperCaseTransform,
    FilterFieldsTransform
)

pipeline = (
    PipelineBuilder("transform-pipeline")
    .with_source_config({
        "type": "csv_file",
        "file_path": "users.csv",
        "adapter": {"id_field": "user_id"}
    })
    .add_processor(TransformProcessor(
        FilterFieldsTransform(fields=["user_id", "name", "email"])
    ))
    .add_processor(TransformProcessor(UpperCaseTransform()))
    .with_sink_config({
        "type": "json_file",
        "file_path": "users_clean.json",
        "json_lines": True
    })
    .build_and_run()
)
```

### Example 2: Pipeline with Retry and Logging

```python
from pipeline_framework.decorators.retry import RetryDecorator
from pipeline_framework.decorators.logging import LoggingDecorator
from pipeline_framework.processors.stateful import CounterProcessor

# Stack decorators for enterprise features
processor = RetryDecorator(
    LoggingDecorator(
        CounterProcessor()
    ),
    max_retries=3,
    retry_delay=1.0,
    backoff_multiplier=2.0
)

pipeline = (
    PipelineBuilder("resilient-pipeline")
    .add_processor(processor)
    .build()
)
```

### Example 3: Observable Pipeline with Metrics

```python
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.observers import ConsoleObserver
from pipeline_framework.observability.metrics import MetricsCollector

# Setup observability
event_bus = EventBus()
metrics = MetricsCollector()

event_bus.subscribe(ConsoleObserver(verbose=True))
event_bus.subscribe(metrics)

pipeline = (
    PipelineBuilder("monitored-pipeline")
    .add_processor(CounterProcessor())
    .with_event_bus(event_bus)
    .build()
)

# Execute
results = pipeline.execute(data)

# View metrics
pipeline_metrics = metrics.get_metrics("monitored-pipeline")
print(f"Success rate: {pipeline_metrics.success_rate:.2%}")
print(f"Throughput: {pipeline_metrics.items_per_second:.2f} items/sec")
```

### Example 4: Command Pattern with Undo

```python
from pipeline_framework.commands.base import CommandHistory
from pipeline_framework.commands.pipeline_commands import ExecutePipelineCommand

history = CommandHistory()

# Execute pipeline through command
cmd = ExecutePipelineCommand(pipeline, data)
results = history.execute(cmd)

# Oops, made a mistake? Undo it!
history.undo()

# Changed your mind? Redo!
history.redo()
```

### Example 5: Configuration-Driven Pipeline

```python
import yaml

# Load config from file
with open("pipeline_config.yaml") as f:
    config = yaml.safe_load(f)

# Build pipeline from config
pipeline = (
    PipelineBuilder(config["pipeline_id"])
    .with_source_config(config["source"])
    .with_sink_config(config["sink"])
)

# Add processors from config
for proc_config in config["processors"]:
    processor = create_processor_from_config(proc_config)
    pipeline.add_processor(processor)

results = pipeline.build_and_run()
```

**Example config file (`pipeline_config.yaml`):**

```yaml
pipeline_id: "data-etl-pipeline"

source:
  type: "csv_file"
  file_path: "input.csv"
  adapter:
    id_field: "user_id"

processors:
  - type: "transform"
    strategy: "uppercase"
  - type: "deduplicate"
  - type: "counter"

sink:
  type: "json_file"
  file_path: "output.json"
  json_lines: true
```

## 🎨 Design Patterns

This framework demonstrates 11 classic design patterns:

| Pattern                     | Usage                  | Location                             |
| --------------------------- | ---------------------- | ------------------------------------ |
| **Builder**                 | Pipeline construction  | `PipelineBuilder`                    |
| **Factory**                 | Source/Sink creation   | `SourceFactory`, `SinkFactory`       |
| **Adapter**                 | Data format conversion | `CSVAdapter`, `JSONAdapter`          |
| **Strategy**                | Pluggable algorithms   | `TransformStrategy`, `StateStorage`  |
| **Chain of Responsibility** | Processor pipeline     | `Processor` chain                    |
| **Template Method**         | Processing flow        | `Processor.process()`                |
| **Iterator**                | Streaming data         | `StreamSource`                       |
| **Observer**                | Event notifications    | `EventBus`, `Observer`               |
| **Decorator**               | Add behaviors          | `RetryDecorator`, `CachingDecorator` |
| **Command**                 | Encapsulate operations | `ExecutePipelineCommand`             |
| **Memento**                 | State snapshots        | Command undo/redo                    |

### Pattern Examples

#### Builder Pattern

```python
pipeline = (
    PipelineBuilder("my-pipeline")
    .with_source_config(...)
    .add_processor(...)
    .with_sink_config(...)
    .with_observers(...)
    .build()
)
```

#### Factory Pattern

```python
# Create sources dynamically
source = SourceFactory.create("csv_file", "data.csv")

# Or from configuration
source = SourceFactory.create_from_config({
    "type": "csv_file",
    "file_path": "data.csv"
})
```

#### Decorator Pattern

```python
# Stack behaviors
processor = TimingDecorator(
    CachingDecorator(
        RetryDecorator(
            LoggingDecorator(
                MyProcessor()
            )
        )
    )
)
```

#### Observer Pattern

```python
event_bus = EventBus()
event_bus.subscribe(MetricsCollector())
event_bus.subscribe(ConsoleObserver())
event_bus.subscribe(FileObserver("events.log"))
```

## 📚 API Reference

### Core Classes

#### `PipelineBuilder`

Fluent interface for building pipelines.

```python
builder = PipelineBuilder(pipeline_id: str)
builder.add_processor(processor: Processor) -> PipelineBuilder
builder.with_source(source: Source) -> PipelineBuilder
builder.with_sink(sink: Sink) -> PipelineBuilder
builder.with_source_config(config: dict) -> PipelineBuilder
builder.with_sink_config(config: dict) -> PipelineBuilder
builder.with_event_bus(event_bus: EventBus) -> PipelineBuilder
builder.with_observers(*observers: Observer) -> PipelineBuilder
builder.with_config(config: PipelineConfig) -> PipelineBuilder
builder.build() -> Pipeline
builder.build_and_run() -> List[ProcessingContext]
```

#### `Pipeline`

Main pipeline orchestrator.

```python
pipeline = Pipeline(pipeline_id, processor_chain, state_storage, ...)
pipeline.execute(data: List[PipelineData]) -> List[ProcessingContext]
pipeline.execute_single(data: PipelineData) -> ProcessingContext
pipeline.execute_from_source(source: Source) -> List[ProcessingContext]
pipeline.execute_to_sink(data, sink: Sink) -> List[ProcessingContext]
pipeline.execute_source_to_sink(source, sink) -> List[ProcessingContext]
pipeline.get_state() -> dict
pipeline.clear_state() -> None
```

#### `Processor`

Base class for all processors.

```python
class MyProcessor(Processor):
    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        # Your logic here
        return context
```

### Built-in Processors

#### Transform Processors

```python
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import (
    UpperCaseTransform,
    LowerCaseTransform,
    FilterFieldsTransform,
    CustomFunctionTransform
)

processor = TransformProcessor(UpperCaseTransform())
```

#### Stateful Processors

```python
from pipeline_framework.processors.stateful import (
    CounterProcessor,
    DeduplicationProcessor,
    AggregatorProcessor
)

counter = CounterProcessor(counter_key="processed_count")
dedup = DeduplicationProcessor(seen_ids_key="seen_ids")
aggregator = AggregatorProcessor(field="price", aggregation_key="all_prices")
```

### Decorators

#### RetryDecorator

```python
from pipeline_framework.decorators.retry import RetryDecorator

retry_processor = RetryDecorator(
    wrapped=my_processor,
    max_retries=3,
    retry_delay=1.0,
    backoff_multiplier=2.0,
    retry_on=lambda e: isinstance(e, ConnectionError)
)
```

#### CachingDecorator

```python
from pipeline_framework.decorators.caching import CachingDecorator

cached_processor = CachingDecorator(
    wrapped=my_processor,
    max_cache_size=1000,
    cache_key_func=lambda data: data.id
)

# Get cache statistics
stats = cached_processor.cache_stats
# {'hits': 150, 'misses': 50, 'hit_rate': 0.75, 'cache_size': 200}
```

#### LoggingDecorator

```python
from pipeline_framework.decorators.logging import LoggingDecorator
import logging

logger = logging.getLogger("my_pipeline")
logging_processor = LoggingDecorator(
    wrapped=my_processor,
    logger=logger,
    log_input=True,
    log_output=True,
    log_errors=True
)
```

#### TimingDecorator

```python
from pipeline_framework.decorators.timing import TimingDecorator

timed_processor = TimingDecorator(my_processor)

# After execution, get timing stats
stats = timed_processor.timing_stats
# {'total_time': 5.2, 'call_count': 100, 'avg_time': 0.052, 'min_time': 0.01, 'max_time': 0.5}
```

### Observability

#### EventBus and Observers

```python
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.observers import (
    ConsoleObserver,
    FileObserver
)
from pipeline_framework.observability.metrics import MetricsCollector

event_bus = EventBus()
event_bus.subscribe(ConsoleObserver(verbose=True))
event_bus.subscribe(FileObserver("pipeline.log", format="json"))

metrics = MetricsCollector()
event_bus.subscribe(metrics)

# Get metrics after execution
pipeline_metrics = metrics.get_metrics("pipeline-id")
print(f"Success rate: {pipeline_metrics.success_rate:.2%}")
print(f"Items/sec: {pipeline_metrics.items_per_second:.2f}")
```

### Command Pattern

```python
from pipeline_framework.commands.base import CommandHistory
from pipeline_framework.commands.pipeline_commands import (
    ExecutePipelineCommand,
    ClearStateCommand
)

history = CommandHistory(max_history=100)

# Execute with undo support
cmd = ExecutePipelineCommand(pipeline, data)
results = history.execute(cmd)

# Undo/Redo
history.undo()
history.redo()

# Check status
if history.can_undo():
    history.undo()
```

## 🔧 Advanced Features

### Custom Processors

```python
from pipeline_framework.core.processor import Processor
from pipeline_framework.core.models import ProcessingContext

class ValidationProcessor(Processor):
    def __init__(self, required_fields: list[str]):
        super().__init__()
        self._required_fields = required_fields

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        for field in self._required_fields:
            if field not in context.data.payload:
                raise ValueError(f"Missing required field: {field}")

        context.data.add_metadata("validated", True)
        return context
```

### Custom Transform Strategies

```python
from pipeline_framework.strategies.transform import TransformStrategy
from pipeline_framework.core.models import PipelineData

class MultiplyNumbersTransform(TransformStrategy):
    def __init__(self, multiplier: int):
        self._multiplier = multiplier

    def transform(self, data: PipelineData, state: dict) -> PipelineData:
        for key, value in data.payload.items():
            if isinstance(value, (int, float)):
                data.payload[key] = value * self._multiplier
        return data
```

### Custom Observers

```python
from pipeline_framework.observability.events import Observer, PipelineEvent

class SlackObserver(Observer):
    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def on_event(self, event: PipelineEvent) -> None:
        # Send to Slack
        pass

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        # Send alert on failure
        self.send_alert(f"Pipeline {event.pipeline_id} failed!")
```

### Registering Custom Types

```python
from pipeline_framework.sources.factory import SourceFactory

# Register custom source
SourceFactory.register_source_type("my_source", MyCustomSource)

# Now use it
source = SourceFactory.create("my_source", custom_arg="value")
```

## 📊 Performance Tips

1. **Use Streaming for Large Files**

```python
   # Instead of CSVFileSource
   source = SourceFactory.create("csv_stream", "large_file.csv")
```

2. **Enable Caching for Expensive Operations**

```python
   processor = CachingDecorator(expensive_processor, max_cache_size=10000)
```

3. **Use Batch Processing**

```python
   # Process in chunks of 1000
   for batch in chunked(data, 1000):
       pipeline.execute(batch)
```

4. **Monitor Performance**

```python
   processor = TimingDecorator(my_processor)
   # Check stats to identify bottlenecks
   print(processor.timing_stats)
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pipeline_framework --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_pipeline.py -v

# Run specific test
uv run pytest tests/unit/test_pipeline.py::TestPipeline::test_execute -v
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Format code (`uv run black .`)
7. Lint code (`uv run ruff check .`)
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pipeline-framework.git
cd pipeline-framework

# Install dependencies with uv
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Apache Airflow, Luigi, and Prefect
- Built as a learning project to demonstrate design patterns
- Thanks to all contributors!

## 📧 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🗺️ Roadmap

- [ ] Async/await support for concurrent processing
- [ ] Web UI for pipeline monitoring
- [ ] More built-in sources (Database, Kafka, S3)
- [ ] More built-in sinks (Database, Elasticsearch, Redis)
- [ ] Distributed processing support
- [ ] DAG visualization
- [ ] Scheduling support (cron-like)
- [ ] Pipeline templates library

## 📖 Additional Resources

- [Documentation](https://pipeline-framework.readthedocs.io)
- [Examples](./examples/)
- [Design Patterns Explained](./docs/patterns.md)
- [Architecture Overview](./docs/architecture.md)
- [API Reference](./docs/api_reference.md)

---

**Built with ❤️ and 11 Design Patterns**
