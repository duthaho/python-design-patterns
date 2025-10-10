"""
Integration tests for decorators with real channels.
Tests the full decorator stack with actual channel implementations.
"""

import logging
import time
import unittest
from datetime import datetime

from notification_system.channels.console import ConsoleChannel
from notification_system.channels.webhook import WebhookChannel
from notification_system.core.notification import Notification
from notification_system.decorators.logging import LoggingDecorator
from notification_system.decorators.rate_limit import RateLimitDecorator
from notification_system.decorators.retry import RetryDecorator

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class TestRealWorldScenarios(unittest.TestCase):
    """Test decorators with real channels in realistic scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.console_config = {"format": "pretty", "colored": True}

    def test_console_with_full_decorator_stack(self):
        """Test ConsoleChannel with all decorators."""
        # Build the full stack
        channel = ConsoleChannel(config=self.console_config)
        channel = RetryDecorator(channel, max_retries=2, initial_delay=0.5)
        channel = LoggingDecorator(channel, log_level="INFO")
        channel = RateLimitDecorator(channel, rate_limit=10, time_window=5.0)

        # Create test notification
        notification = Notification(
            event_id="evt-integration-001",
            channel="console",
            recipients=["user@example.com", "admin@example.com"],
            subject="Integration Test",
            body="This is a full integration test with all decorators.",
        )

        # Send notification
        result = channel.send(notification)

        # Assertions
        self.assertTrue(result.success)
        self.assertIsNotNone(result.sent_at)

    def test_burst_traffic_with_rate_limiting(self):
        """Test handling burst traffic with rate limiting."""
        channel = ConsoleChannel(config={"format": "json"})
        channel = RateLimitDecorator(channel, rate_limit=5, time_window=2.0)
        channel = LoggingDecorator(channel, log_level="INFO")

        # Send burst of 10 notifications
        print("\n--- Testing Burst Traffic (10 notifications, limit 5 per 2s) ---")
        results = []

        for i in range(10):
            notification = Notification(
                event_id=f"evt-burst-{i:03d}",
                channel="console",
                recipients=[f"user{i}@example.com"],
                subject=f"Burst Test {i}",
                body=f"Message number {i}",
            )
            result = channel.send(notification)
            results.append(result.success)
            print(
                f"  Message {i+1}/10: {'✅ Sent' if result.success else '❌ Rate Limited'}"
            )

        # First 5 should succeed, next 5 should fail
        successful = sum(results)
        print(f"\n  Total successful: {successful}/10")

        self.assertEqual(successful, 5)
        self.assertTrue(all(results[:5]))  # First 5 succeed
        self.assertFalse(any(results[5:]))  # Next 5 fail

    def test_gradual_traffic_within_rate_limit(self):
        """Test gradual traffic that stays within rate limit."""
        channel = ConsoleChannel(config={"format": "json"})
        channel = RateLimitDecorator(channel, rate_limit=3, time_window=1.0)

        print("\n--- Testing Gradual Traffic (5 messages with delays) ---")
        results = []

        for i in range(5):
            notification = Notification(
                event_id=f"evt-gradual-{i:03d}",
                channel="console",
                recipients=["user@example.com"],
                body=f"Gradual message {i}",
            )
            result = channel.send(notification)
            results.append(result.success)
            print(f"  Message {i+1}: {'✅' if result.success else '❌'}")

            # Wait between sends to allow token refill
            if i < 4:
                time.sleep(0.4)  # 400ms between sends

        print(f"  Total successful: {sum(results)}/5")

        # Most should succeed because we're pacing the requests
        self.assertGreaterEqual(sum(results), 4)

    def test_retry_on_simulated_transient_failure(self):
        """Test retry behavior with simulated transient failures."""
        from unittest.mock import Mock, patch

        from notification_system.core.exceptions import RetriableError

        # Create a channel that fails twice then succeeds
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "SimulatedChannel"

        call_count = [0]

        def flaky_send(notification):
            call_count[0] += 1
            if call_count[0] <= 2:
                print(f"  Attempt {call_count[0]}: Simulated failure")
                raise RetriableError("Simulated transient failure", channel="test")
            else:
                print(f"  Attempt {call_count[0]}: Success!")
                from notification_system.core.notification import \
                    NotificationResult

                return NotificationResult(
                    success=True,
                    channel="SimulatedChannel",
                    message="Success after retries",
                    metadata={},
                )

        mock_channel.send = flaky_send

        print("\n--- Testing Retry with Simulated Failures ---")

        channel = RetryDecorator(mock_channel, max_retries=3, initial_delay=0.3)
        channel = LoggingDecorator(channel, log_level="INFO")

        notification = Notification(
            event_id="evt-retry-test",
            channel="console",
            recipients=["user@example.com"],
            body="Testing retry logic",
        )

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = channel.send(notification)

        print(f"  Final result: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"  Total attempts: {call_count[0]}")

        self.assertTrue(result.success)
        self.assertEqual(call_count[0], 3)  # Failed twice, succeeded on third

    def test_decorator_stack_performance(self):
        """Test performance impact of decorator stack."""
        # Test without decorators
        channel_base = ConsoleChannel(config={"format": "json"})

        notification = Notification(
            event_id="evt-perf",
            channel="console",
            recipients=["user@example.com"],
            body="Performance test",
        )

        # Baseline
        start = time.time()
        for _ in range(10):
            channel_base.send(notification)
        baseline_time = time.time() - start

        # With full decorator stack
        channel_decorated = ConsoleChannel(config={"format": "json"})
        channel_decorated = RetryDecorator(channel_decorated, max_retries=1)
        channel_decorated = LoggingDecorator(channel_decorated, log_level="WARNING")
        channel_decorated = RateLimitDecorator(
            channel_decorated, rate_limit=100, time_window=1.0
        )

        start = time.time()
        for _ in range(10):
            channel_decorated.send(notification)
        decorated_time = time.time() - start

        print(f"\n--- Performance Test (10 sends) ---")
        print(f"  Baseline time: {baseline_time:.4f}s")
        print(f"  Decorated time: {decorated_time:.4f}s")
        print(
            f"  Overhead: {(decorated_time - baseline_time):.4f}s ({(decorated_time/baseline_time - 1)*100:.1f}%)"
        )

        # Decorator overhead should be reasonable (< 50% for this test)
        self.assertLess(decorated_time, baseline_time * 1.5)

    def test_concurrent_sends_with_decorators(self):
        """Test thread safety of decorator stack."""
        import threading

        channel = ConsoleChannel(config={"format": "json"})
        channel = RetryDecorator(channel, max_retries=1, initial_delay=0.1)
        channel = RateLimitDecorator(channel, rate_limit=20, time_window=1.0)

        results = []
        lock = threading.Lock()

        def send_notification(thread_id):
            for i in range(3):
                notification = Notification(
                    event_id=f"evt-thread-{thread_id}-{i}",
                    channel="console",
                    recipients=[f"user{thread_id}@example.com"],
                    body=f"Thread {thread_id} message {i}",
                )
                result = channel.send(notification)
                with lock:
                    results.append((thread_id, i, result.success))

        print("\n--- Testing Concurrent Sends (5 threads, 3 messages each) ---")

        # Create 5 threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=send_notification, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        successful = sum(1 for _, _, success in results if success)
        print(f"  Total messages: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")

        # Most should succeed (within rate limit)
        self.assertGreater(successful, 10)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery scenarios."""

    def test_permanent_error_stops_retry(self):
        """Test that permanent errors don't trigger retries."""
        from unittest.mock import Mock

        from notification_system.core.exceptions import PermanentError

        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"
        mock_channel.send = Mock(
            side_effect=PermanentError("Invalid recipient", channel="test")
        )

        channel = RetryDecorator(mock_channel, max_retries=5, initial_delay=0.1)
        channel = LoggingDecorator(channel, log_level="INFO")

        notification = Notification(
            event_id="evt-permanent",
            channel="console",
            recipients=["invalid-email"],
            body="Test",
        )

        print("\n--- Testing Permanent Error (should not retry) ---")
        result = channel.send(notification)

        print(f"  Result: {'Success' if result.success else 'Failed'}")
        print(f"  Attempts: {mock_channel.send.call_count}")

        self.assertFalse(result.success)
        self.assertEqual(mock_channel.send.call_count, 1)  # Only one attempt

    def test_mixed_error_types(self):
        """Test handling of mixed error types."""
        from unittest.mock import Mock

        from notification_system.core.exceptions import (PermanentError,
                                                         RetriableError)

        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        # First call: retriable, second: permanent
        mock_channel.send = Mock(
            side_effect=[
                RetriableError("Temporary issue", channel="test"),
                PermanentError("Fatal error", channel="test"),
            ]
        )

        channel = RetryDecorator(mock_channel, max_retries=5, initial_delay=0.1)

        notification = Notification(
            event_id="evt-mixed",
            channel="console",
            recipients=["user@example.com"],
            body="Test",
        )

        print("\n--- Testing Mixed Errors (retriable then permanent) ---")

        import unittest.mock as mock

        with mock.patch("time.sleep"):
            result = channel.send(notification)

        print(f"  Total attempts: {mock_channel.send.call_count}")

        self.assertFalse(result.success)
        self.assertEqual(
            mock_channel.send.call_count, 2
        )  # Retry once, then permanent error


class TestLoggingOutput(unittest.TestCase):
    """Test logging output and formatting."""

    def test_structured_logging_format(self):
        """Test that logging produces structured, parseable output."""
        import io
        import sys

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        logger = logging.getLogger("LoggingDecorator")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            channel = ConsoleChannel(config={"format": "json"})
            channel = LoggingDecorator(channel, log_level="INFO")

            notification = Notification(
                event_id="evt-log-test",
                channel="console",
                recipients=["test@example.com"],
                subject="Log Test",
                body="Testing log output",
            )

            channel.send(notification)

            # Get log output
            log_output = log_capture.getvalue()

            print("\n--- Captured Log Output ---")
            print(log_output)

            # Verify key information is logged
            self.assertIn("evt-log-test", log_output)
            self.assertIn("test@example.com", log_output)
            self.assertIn("sent successfully", log_output.lower())

        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
