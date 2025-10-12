# Pipeline Framework

A Python framework for building configurable data processing pipelines with built-in support for design patterns.

## 🎯 Project Goals

This is a learning project designed to practice implementing design patterns in a real-world inspired context. The framework allows developers to:

- Build reusable data processing pipelines
- Chain tasks together with automatic data flow
- Handle errors gracefully with fail-fast behavior
- Extend functionality through well-defined patterns

## 🏗️ Architecture

### Design Patterns Implemented

#### Phase 1.1 (Current)
- **Command Pattern**: Tasks encapsulate operations as executable objects
- **Chain of Responsibility**: Pipeline passes context through sequential tasks
- **Fluent Interface**: Method chaining for readable pipeline configuration
- **Defensive Copying**: Protection of internal state from external mutation

#### Upcoming Phases
- **Observer Pattern**: Event notifications for pipeline lifecycle
- **Factory Pattern**: Dynamic task creation and registration
- **Strategy Pattern**: Pluggable execution strategies
- **Decorator Pattern**: Cross-cutting concerns (retry, logging, caching)
- **Builder Pattern**: Complex pipeline construction

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd pipeline_framework

# Setup with UV
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Basic Usage

```python
from pipeline_framework import Pipeline, Task, PipelineContext

# Define a custom task
class ProcessDataTask(Task):
    def __init__(self):
        super().__init__("process_data", "Process input data")
    
    def execute(self, context: PipelineContext) -> None:
        data = context.get("input", [])
        processed = [x * 2 for x in data]
        context.set("output", processed)

# Build and execute pipeline
pipeline = Pipeline("my_pipeline")
pipeline.add_task(ProcessDataTask())

result = pipeline.execute({"input": [1, 2, 3, 4, 5]})
print(result.get("output"))  # [2, 4, 6, 8, 10]
```

### Method Chaining

```python
pipeline = (
    Pipeline("data_processing")
    .add_task(LoadDataTask())
    .add_task(TransformDataTask())
    .add_task(ValidateDataTask())
    .add_task(SaveDataTask())
)

result = pipeline.execute()
```

## 📚 Core Components

### PipelineContext

Shared data container for inter-task communication.

```python
context = PipelineContext({"key": "value"})
context.set("result", 42)
print(context.get("result"))  # 42
print(context.has("result"))  # True
print(context.get_all())      # {"key": "value", "result": 42}
```

### Task (Abstract Base Class)

Base class for all executable tasks.

```python
class MyTask(Task):
    def __init__(self):
        super().__init__("my_task", "Description of my task")
    
    def execute(self, context: PipelineContext) -> None:
        # Your task logic here
        value = context.get("input")
        result = self.process(value)
        context.set("output", result)
    
    def process(self, value):
        return value * 2
```

### Pipeline

Orchestrates task execution in sequence.

```python
pipeline = Pipeline("my_pipeline", "A sample pipeline")
pipeline.add_task(task1)
pipeline.add_task(task2)
pipeline.add_task(task3)

# Execute with initial data
result = pipeline.execute({"input": 100})
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suite

```bash
pytest tests/unit/test_context.py -v
pytest tests/unit/test_task.py -v
pytest tests/unit/test_pipeline.py -v
```

### Coverage Report

```bash
pytest --cov=pipeline_framework --cov-report=html tests/
# Open htmlcov/index.html
```

### Continuous Testing

```bash
# Install pytest-watch
uv pip install pytest-watch

# Watch mode
ptw tests/unit/
```

## 🛠️ Development

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Lint
ruff check src/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ && mypy src/ && pytest tests/
```

### Project Structure

```
pipeline_framework/
├── src/
│   └── pipeline_framework/
│       ├── core/           # Core pipeline components
│       ├── events/         # Event system (Phase 1.2)
│       ├── factories/      # Task factories (Phase 1.3)
│       └── utils/          # Utilities and exceptions
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── examples/              # Usage examples
└── pyproject.toml         # Project configuration
```

## 📖 Examples

### Example 1: Data Processing Pipeline

```python
from pipeline_framework import Pipeline, Task, PipelineContext

class LoadCSVTask(Task):
    def __init__(self, filepath: str):
        super().__init__("load_csv", f"Load CSV from {filepath}")
        self.filepath = filepath
    
    def execute(self, context: PipelineContext) -> None:
        # Simulate loading CSV
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        context.set("raw_data", data)

class FilterAdultsTask(Task):
    def __init__(self):
        super().__init__("filter_adults", "Filter adults (age >= 18)")
    
    def execute(self, context: PipelineContext) -> None:
        data = context.get("raw_data", [])
        adults = [person for person in data if person["age"] >= 18]
        context.set("filtered_data", adults)

class ComputeStatsTask(Task):
    def __init__(self):
        super().__init__("compute_stats", "Compute statistics")
    
    def execute(self, context: PipelineContext) -> None:
        data = context.get("filtered_data", [])
        avg_age = sum(p["age"] for p in data) / len(data) if data else 0
        context.set("average_age", avg_age)
        context.set("count", len(data))

# Build pipeline
pipeline = (
    Pipeline("csv_processor")
    .add_task(LoadCSVTask("data.csv"))
    .add_task(FilterAdultsTask())
    .add_task(ComputeStatsTask())
)

# Execute
result = pipeline.execute()
print(f"Processed {result.get('count')} records")
print(f"Average age: {result.get('average_age')}")
```

### Example 2: Error Handling

```python
from pipeline_framework import Pipeline, Task
from pipeline_framework.utils import TaskExecutionError

class ValidateDataTask(Task):
    def __init__(self):
        super().__init__("validate", "Validate input data")
    
    def execute(self, context):
        data = context.get("data")
        if not data:
            raise ValueError("Data cannot be empty")
        context.set("validated", True)

pipeline = Pipeline("validation_pipeline")
pipeline.add_task(ValidateDataTask())

try:
    result = pipeline.execute({"data": None})
except TaskExecutionError as e:
    print(f"Task '{e.task_name}' failed: {e.original_error}")
    # Output: Task 'validate' failed: Data cannot be empty
```

## 🎓 Learning Resources

### Design Pattern Documentation

- **Command Pattern**: [Refactoring Guru](https://refactoring.guru/design-patterns/command)
- **Chain of Responsibility**: [Refactoring Guru](https://refactoring.guru/design-patterns/chain-of-responsibility)

### Architectural Decisions

**Q: Why use shared context instead of passing data between tasks?**

A: Shared context provides flexibility:
- Tasks can access any previous data, not just immediate predecessor
- New tasks can be inserted without changing interfaces
- Enables conditional data access based on task logic

**Q: Why fail-fast instead of collecting all errors?**

A: For Phase 1, fail-fast is simpler and sufficient:
- Easier to debug (first error is the problem)
- More predictable behavior
- Can be enhanced in future phases

**Q: Why return copies from get_all() and get_tasks()?**

A: Defensive copying prevents external mutation:
- Protects internal state
- Prevents subtle bugs from accidental modification
- Clear ownership semantics

## 🗺️ Roadmap

### Phase 1.1 ✅ (Current)
- [x] Core pipeline execution
- [x] Task abstraction
- [x] Context for data sharing
- [x] Basic error handling
- [x] Unit tests (51 tests, 100% coverage)

### Phase 1.2 (Next)
- [ ] Observer pattern for events
- [ ] Pipeline lifecycle notifications
- [ ] Example listeners (console, file)
- [ ] Event filtering and subscriptions

### Phase 1.3
- [ ] Factory pattern for task creation
- [ ] Task registry and discovery
- [ ] Configuration-based task instantiation

### Phase 1.4
- [ ] Strategy pattern for execution modes
- [ ] Decorator pattern for cross-cutting concerns
- [ ] Builder pattern for complex pipelines
- [ ] Integration tests and examples

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a learning project. Feel free to fork and experiment!

## 📬 Contact

[Your contact information]

---

**Built with ❤️ as a design patterns learning project**