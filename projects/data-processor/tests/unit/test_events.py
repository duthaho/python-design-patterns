"""Tests for event system."""

import pytest
from pipeline_framework.core.models import PipelineData
from pipeline_framework.observability.events import (EventBus, EventType,
                                                     Observer, PipelineEvent)


class MockObserver(Observer):
    """Mock observer for testing."""

    def __init__(self):
        self.events = []

    def on_event(self, event: PipelineEvent):
        self.events.append(event)


class TestEventBus:
    """Test EventBus."""

    def test_subscribe_observer(self):
        """Test subscribing observers."""
        bus = EventBus()
        observer = MockObserver()

        bus.subscribe(observer)

        assert bus.observer_count == 1

    def test_unsubscribe_observer(self):
        """Test unsubscribing observers."""
        bus = EventBus()
        observer = MockObserver()

        bus.subscribe(observer)
        bus.unsubscribe(observer)

        assert bus.observer_count == 0

    def test_publish_event(self):
        """Test publishing events to observers."""
        bus = EventBus()
        observer1 = MockObserver()
        observer2 = MockObserver()

        bus.subscribe(observer1)
        bus.subscribe(observer2)

        event = PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_id="test")
        bus.publish(event)

        assert len(observer1.events) == 1
        assert len(observer2.events) == 1
        assert observer1.events[0] == event

    def test_clear_observers(self):
        """Test clearing all observers."""
        bus = EventBus()
        bus.subscribe(MockObserver())
        bus.subscribe(MockObserver())

        bus.clear()

        assert bus.observer_count == 0

    def test_publish_handles_observer_exceptions(self):
        """Test that exceptions in observers don't break the bus."""

        class FailingObserver(Observer):
            def on_event(self, event):
                raise ValueError("Test error")

        bus = EventBus()
        bus.subscribe(FailingObserver())

        good_observer = MockObserver()
        bus.subscribe(good_observer)

        event = PipelineEvent(event_type=EventType.ITEM_COMPLETED, pipeline_id="test")

        # Should not raise, and good observer should still get event
        bus.publish(event)

        assert len(good_observer.events) == 1
