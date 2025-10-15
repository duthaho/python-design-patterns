"""Tests for metrics collection."""

from pipeline_framework.core.models import PipelineData
from pipeline_framework.observability.events import (EventBus, EventType,
                                                     PipelineEvent)
from pipeline_framework.observability.metrics import (MetricsCollector,
                                                      PipelineMetrics)


class TestPipelineMetrics:
    """Test PipelineMetrics dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        from datetime import datetime

        metrics = PipelineMetrics(
            pipeline_id="test",
            start_time=datetime.now(),
            total_items=10,
            successful_items=8,
            failed_items=2,
        )

        assert metrics.success_rate == 0.8
        assert metrics.error_rate == 0.2

    def test_throughput_calculation(self):
        """Test items per second calculation."""
        from datetime import datetime, timedelta

        start = datetime.now()
        end = start + timedelta(seconds=5)

        metrics = PipelineMetrics(
            pipeline_id="test", start_time=start, end_time=end, total_items=100
        )

        assert metrics.items_per_second == 20.0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        from datetime import datetime

        metrics = PipelineMetrics(
            pipeline_id="test", start_time=datetime.now(), total_items=5, successful_items=5
        )

        result = metrics.to_dict()

        assert result["pipeline_id"] == "test"
        assert result["total_items"] == 5
        assert result["successful_items"] == 5


class TestMetricsCollector:
    """Test MetricsCollector observer."""

    def test_collect_pipeline_metrics(self):
        """Test collecting metrics throughout pipeline execution."""
        collector = MetricsCollector()
        bus = EventBus()
        bus.subscribe(collector)

        # Simulate pipeline execution
        bus.publish(
            PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_id="test-pipeline")
        )

        for i in range(3):
            bus.publish(
                PipelineEvent(
                    event_type=EventType.ITEM_COMPLETED,
                    pipeline_id="test-pipeline",
                    data=PipelineData.create(payload={"id": i}),
                )
            )

        bus.publish(
            PipelineEvent(
                event_type=EventType.ITEM_FAILED,
                pipeline_id="test-pipeline",
                error=ValueError("Test error"),
            )
        )

        bus.publish(
            PipelineEvent(event_type=EventType.PIPELINE_COMPLETED, pipeline_id="test-pipeline")
        )

        metrics = collector.get_metrics("test-pipeline")

        assert metrics is not None
        assert metrics.total_items == 4
        assert metrics.successful_items == 3
        assert metrics.failed_items == 1

    def test_clear_specific_metrics(self):
        """Test clearing metrics for specific pipeline."""
        collector = MetricsCollector()
        bus = EventBus()
        bus.subscribe(collector)

        # Create metrics for two pipelines
        bus.publish(PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_id="pipeline-1"))
        bus.publish(PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_id="pipeline-2"))

        collector.clear_metrics("pipeline-1")

        assert collector.get_metrics("pipeline-1") is None
        assert collector.get_metrics("pipeline-2") is not None

    def test_processor_usage_tracking(self):
        """Test tracking processor usage."""
        collector = MetricsCollector()
        bus = EventBus()
        bus.subscribe(collector)

        bus.publish(PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_id="test"))

        # Simulate processor executions
        for proc_name in ["ProcessorA", "ProcessorB", "ProcessorA"]:
            bus.publish(
                PipelineEvent(
                    event_type=EventType.PROCESSOR_COMPLETED,
                    pipeline_id="test",
                    processor_name=proc_name,
                )
            )

        metrics = collector.get_metrics("test")

        assert metrics.processor_counts["ProcessorA"] == 2
        assert metrics.processor_counts["ProcessorB"] == 1
