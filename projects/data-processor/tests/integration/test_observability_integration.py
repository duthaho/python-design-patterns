"""Integration tests for observability features."""

from pipeline_framework import PipelineBuilder
from pipeline_framework.core.models import PipelineData
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.metrics import MetricsCollector
from pipeline_framework.observability.observers import (ConsoleObserver,
                                                        FileObserver)
from pipeline_framework.processors.stateful import CounterProcessor


class TestObservabilityIntegration:
    """Test complete observability integration."""

    def test_pipeline_with_metrics_collection(self):
        """Test pipeline with metrics collector."""
        event_bus = EventBus()
        metrics_collector = MetricsCollector()
        event_bus.subscribe(metrics_collector)

        pipeline = (
            PipelineBuilder("metrics-test")
            .add_processor(CounterProcessor())
            .with_event_bus(event_bus)
            .build()
        )

        data = [PipelineData.create(payload={"value": i}) for i in range(10)]
        results = pipeline.execute(data)

        metrics = metrics_collector.get_metrics("metrics-test")

        assert metrics is not None
        assert metrics.total_items == 10
        assert metrics.successful_items == 10
        assert metrics.success_rate == 1.0

    def test_pipeline_with_file_logging(self, tmp_path):
        """Test pipeline with file observer."""
        log_file = tmp_path / "pipeline.log"

        event_bus = EventBus()
        file_observer = FileObserver(str(log_file), format="json")
        event_bus.subscribe(file_observer)

        pipeline = (
            PipelineBuilder("logging-test")
            .add_processor(CounterProcessor())
            .with_event_bus(event_bus)
            .build()
        )

        data = [PipelineData.create(payload={"value": 1})]
        pipeline.execute(data)

        file_observer.close()

        # Verify log file was created and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "pipeline_started" in content
        assert "pipeline_completed" in content

    def test_pipeline_with_multiple_observers(self, capsys):
        """Test pipeline with multiple observers."""
        event_bus = EventBus()

        console_observer = ConsoleObserver(verbose=False)
        metrics_collector = MetricsCollector()

        event_bus.subscribe(console_observer)
        event_bus.subscribe(metrics_collector)

        pipeline = (
            PipelineBuilder("multi-observer-test")
            .add_processor(CounterProcessor())
            .with_event_bus(event_bus)
            .build()
        )

        data = [PipelineData.create(payload={"value": i}) for i in range(5)]
        pipeline.execute(data)

        # Check console output
        captured = capsys.readouterr()
        assert "pipeline_started" in captured.out

        # Check metrics
        metrics = metrics_collector.get_metrics("multi-observer-test")
        assert metrics.total_items == 5

    def test_convenience_with_observers_method(self):
        """Test using with_observers convenience method."""
        metrics_collector = MetricsCollector()
        console_observer = ConsoleObserver()

        pipeline = (
            PipelineBuilder("convenience-test")
            .add_processor(CounterProcessor())
            .with_observers(metrics_collector, console_observer)
            .build()
        )

        data = [PipelineData.create(payload={})]
        pipeline.execute(data)

        metrics = metrics_collector.get_metrics("convenience-test")
        assert metrics is not None
