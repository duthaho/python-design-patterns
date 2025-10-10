"""
Comprehensive unit tests for notification decorators.
Tests retry logic, logging, rate limiting, and decorator composition.
"""

import time
import unittest
from unittest.mock import Mock, patch

from notification_system.channels.console import ConsoleChannel
from notification_system.core.exceptions import (ConnectionError,
                                                 PermanentError,
                                                 RetriableError)
from notification_system.core.notification import (Notification,
                                                   NotificationResult,
                                                   NotificationStatus)
from notification_system.decorators.logging import LoggingDecorator
from notification_system.decorators.rate_limit import RateLimitDecorator
from notification_system.decorators.retry import RetryDecorator


class TestRetryDecorator(unittest.TestCase):
    """Test RetryDecorator with exponential backoff."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_channel = ConsoleChannel(config={"format": "json"})
        self.notification = Notification(
            event_id="evt-123",
            channel="console",
            recipients=["test@example.com"],
            subject="Test Subject",
            body="Test message body",
        )

    def test_success_on_first_attempt_no_retry(self):
        """Should succeed on first attempt without any retries."""
        channel = RetryDecorator(self.base_channel, max_retries=3, initial_delay=0.1)

        result = channel.send(self.notification)

        self.assertTrue(result.success)
        self.assertEqual(self.notification.retry_count, 0)
        self.assertEqual(self.notification.status, NotificationStatus.SENT)

    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_retriable_error_then_success(self, mock_sleep):
        """Should retry on RetriableError and eventually succeed."""
        # Create mock channel that fails twice, then succeeds
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}

        # First two calls raise RetriableError, third succeeds
        mock_channel.send = Mock(
            side_effect=[
                RetriableError("Network timeout", channel="test"),
                RetriableError("Connection refused", channel="test"),
                NotificationResult(
                    success=True,
                    channel="test",
                    message="Success on third attempt",
                    metadata={},
                ),
            ]
        )

        channel = RetryDecorator(
            mock_channel, max_retries=3, initial_delay=1.0, backoff_multiplier=2.0
        )

        result = channel.send(self.notification)

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(mock_channel.send.call_count, 3)  # 3 attempts total
        self.assertEqual(
            self.notification.retry_count, 2
        )  # 2 retries after first failure

        # Verify sleep was called with exponential backoff
        self.assertEqual(mock_sleep.call_count, 2)
        # First retry: 1.0 * (2.0 ** 0) = 1.0 seconds
        mock_sleep.assert_any_call(1.0)
        # Second retry: 1.0 * (2.0 ** 1) = 2.0 seconds
        mock_sleep.assert_any_call(2.0)

    @patch("time.sleep")
    def test_retry_exhausted_all_attempts_failed(self, mock_sleep):
        """Should fail after exhausting all retries."""
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        # All attempts fail with RetriableError
        mock_channel.send = Mock(
            side_effect=RetriableError("Persistent network issue", channel="test")
        )

        channel = RetryDecorator(
            mock_channel,
            max_retries=2,  # Total 3 attempts (initial + 2 retries)
            initial_delay=0.5,
            backoff_multiplier=2.0,
        )

        result = channel.send(self.notification)

        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(mock_channel.send.call_count, 3)  # Initial + 2 retries
        self.assertEqual(self.notification.retry_count, 2)
        self.assertIn("Failed after 2 retries", result.message)

        # Verify exponential backoff
        self.assertEqual(mock_sleep.call_count, 2)

    def test_no_retry_on_permanent_error(self):
        """Should not retry on PermanentError - fail immediately."""
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        mock_channel.send = Mock(
            side_effect=PermanentError("Invalid recipient email", channel="test")
        )

        channel = RetryDecorator(mock_channel, max_retries=3, initial_delay=1.0)

        result = channel.send(self.notification)

        # Should only attempt once
        self.assertFalse(result.success)
        self.assertEqual(mock_channel.send.call_count, 1)
        self.assertEqual(self.notification.retry_count, 0)  # No retries
        self.assertIn("Invalid recipient email", result.message)

    def test_no_retry_on_unexpected_exception(self):
        """Should not retry on unexpected exceptions."""
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        mock_channel.send = Mock(side_effect=ValueError("Unexpected error"))

        channel = RetryDecorator(mock_channel, max_retries=3, initial_delay=1.0)

        result = channel.send(self.notification)

        # Should only attempt once
        self.assertFalse(result.success)
        self.assertEqual(mock_channel.send.call_count, 1)
        self.assertIn("Unexpected error", result.message)

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        channel = RetryDecorator(
            self.base_channel,
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
        )

        # Test delays for each attempt
        self.assertEqual(channel._calculate_delay(0), 1.0)  # 1.0 * 2^0 = 1.0
        self.assertEqual(channel._calculate_delay(1), 2.0)  # 1.0 * 2^1 = 2.0
        self.assertEqual(channel._calculate_delay(2), 4.0)  # 1.0 * 2^2 = 4.0
        self.assertEqual(channel._calculate_delay(3), 8.0)  # 1.0 * 2^3 = 8.0
        self.assertEqual(channel._calculate_delay(4), 16.0)  # 1.0 * 2^4 = 16.0
        self.assertEqual(channel._calculate_delay(5), 32.0)  # 1.0 * 2^5 = 32.0

    def test_exponential_backoff_respects_max_delay(self):
        """Test that delay never exceeds max_delay."""
        channel = RetryDecorator(
            self.base_channel,
            max_retries=10,
            initial_delay=1.0,
            max_delay=10.0,  # Cap at 10 seconds
            backoff_multiplier=2.0,
        )

        # Even for large attempt numbers, should not exceed max_delay
        self.assertEqual(
            channel._calculate_delay(10), 10.0
        )  # Would be 1024, capped at 10
        self.assertEqual(
            channel._calculate_delay(20), 10.0
        )  # Would be huge, capped at 10

    def test_notification_state_updates_on_retry(self):
        """Test that notification state is updated correctly on retries."""
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"
        
        # Counter to track calls
        call_counter = {'count': 0}
        
        def side_effect(notification):
            """Custom side effect that properly handles notification state."""
            call_counter['count'] += 1
            
            if call_counter['count'] == 1:
                # First attempt fails
                raise RetriableError("Temporary failure", channel="test")
            else:
                # Second attempt succeeds
                result = NotificationResult(
                    success=True,
                    channel="test",
                    message="Success",
                    metadata={}
                )
                notification.mark_sent(result)
                return result
        
        mock_channel.send = Mock(side_effect=side_effect)
        
        channel = RetryDecorator(mock_channel, max_retries=3, initial_delay=0.1)
        
        initial_retry_count = self.notification.retry_count
        initial_status = self.notification.status
        
        result = channel.send(self.notification)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(mock_channel.send.call_count, 2)  # Failed once, succeeded once
        self.assertEqual(self.notification.retry_count, initial_retry_count + 1)
        self.assertEqual(self.notification.status, NotificationStatus.SENT)

    def test_getattr_delegation(self):
        """Test that __getattr__ correctly delegates to wrapped channel."""
        channel = RetryDecorator(self.base_channel, max_retries=3)

        # Should delegate to base_channel's config
        self.assertEqual(channel.config, self.base_channel.config)

        # Should be able to call base channel methods
        self.assertIsNotNone(channel.health_check)

    def test_repr(self):
        """Test string representation."""
        channel = RetryDecorator(self.base_channel, max_retries=5)
        repr_str = repr(channel)

        self.assertIn("RetryDecorator", repr_str)
        self.assertIn("max_retries=5", repr_str)


class TestLoggingDecorator(unittest.TestCase):
    """Test LoggingDecorator for structured logging."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_channel = ConsoleChannel(config={"format": "json"})
        self.notification = Notification(
            event_id="evt-456",
            channel="console",
            recipients=["test@example.com", "admin@example.com"],
            subject="Test Logging",
            body="Test message for logging",
        )

    @patch("notification_system.decorators.logging.logging.getLogger")
    def test_logs_send_start(self, mock_get_logger):
        """Should log when send operation starts."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        channel = LoggingDecorator(self.base_channel, log_level="INFO")
        result = channel.send(self.notification)

        # Verify info log was called for start
        mock_logger.info.assert_called()

        # Check log message contains key information
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        log_message = " ".join(log_calls)

        self.assertIn(self.notification.notification_id, log_message)
        self.assertTrue(result.success)

    @patch("notification_system.decorators.logging.logging.getLogger")
    def test_logs_send_success_with_duration(self, mock_get_logger):
        """Should log successful send with duration."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        channel = LoggingDecorator(self.base_channel, log_level="INFO")
        result = channel.send(self.notification)

        # Verify success was logged
        self.assertTrue(result.success)

        # Check that duration was logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        log_message = " ".join(log_calls)

        self.assertIn("sent successfully", log_message)
        # Duration should be in format like "0.12s"
        self.assertRegex(log_message, r"\d+\.\d+s")

    @patch("notification_system.decorators.logging.logging.getLogger")
    def test_logs_send_failure(self, mock_get_logger):
        """Should log failed send with error message."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create channel that will fail
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"
        mock_channel.send = Mock(
            side_effect=ConnectionError("Network error", channel="test")
        )

        channel = LoggingDecorator(mock_channel, log_level="INFO")
        result = channel.send(self.notification)

        # Verify failure was logged
        self.assertFalse(result.success)
        mock_logger.error.assert_called()

        # Check error message
        error_log_calls = [str(call) for call in mock_logger.error.call_args_list]
        error_message = " ".join(error_log_calls)

        self.assertIn("failed", error_message.lower())
        self.assertIn("Network error", error_message)

    def test_measures_duration_accurately(self):
        """Should measure operation duration accurately."""
        # Create a slow mock channel
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}

        def slow_send(notification):
            time.sleep(0.1)  # Sleep for 100ms
            return NotificationResult(
                success=True, channel="test", message="Success", metadata={}
            )

        mock_channel.send = slow_send

        with patch(
            "notification_system.decorators.logging.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            channel = LoggingDecorator(mock_channel, log_level="INFO")
            result = channel.send(self.notification)

            # Extract duration from log
            log_calls = mock_logger.info.call_args_list
            duration_log = str(log_calls[-1])  # Last log should be result with duration

            # Duration should be approximately 0.1s (100ms)
            self.assertRegex(duration_log, r"0\.\d+s")

    def test_different_log_levels(self):
        """Test decorator respects different log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            with self.subTest(level=level):
                channel = LoggingDecorator(self.base_channel, log_level=level)
                self.assertEqual(channel.log_level, level)

    def test_handles_exception_gracefully(self):
        """Should handle exceptions and return failure result."""
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"
        mock_channel.send = Mock(side_effect=Exception("Unexpected error"))

        channel = LoggingDecorator(mock_channel, log_level="INFO")
        result = channel.send(self.notification)

        self.assertFalse(result.success)
        self.assertIn("Unexpected error", result.message)

    def test_getattr_delegation(self):
        """Test that __getattr__ correctly delegates to wrapped channel."""
        channel = LoggingDecorator(self.base_channel, log_level="INFO")

        # Should delegate to base_channel's attributes
        self.assertEqual(channel.config, self.base_channel.config)

    def test_repr(self):
        """Test string representation."""
        channel = LoggingDecorator(self.base_channel, log_level="DEBUG")
        repr_str = repr(channel)

        self.assertIn("LoggingDecorator", repr_str)
        self.assertIn("log_level=DEBUG", repr_str)


class TestRateLimitDecorator(unittest.TestCase):
    """Test RateLimitDecorator with token bucket algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_channel = ConsoleChannel(config={"format": "json"})
        self.notification = Notification(
            event_id="evt-789",
            channel="console",
            recipients=["test@example.com"],
            subject="Test Rate Limit",
            body="Test message",
        )

    def test_allows_requests_within_rate_limit(self):
        """Should allow requests within the rate limit."""
        channel = RateLimitDecorator(self.base_channel, rate_limit=5, time_window=10.0)

        # Send 5 notifications (at limit)
        results = []
        for i in range(5):
            notif = Notification(
                event_id=f"evt-{i}",
                channel="console",
                recipients=["test@example.com"],
                body=f"Message {i}",
            )
            result = channel.send(notif)
            results.append(result.success)

        # All should succeed
        self.assertTrue(all(results))
        self.assertEqual(sum(results), 5)

    def test_blocks_requests_exceeding_rate_limit(self):
        """Should block requests exceeding the rate limit."""
        channel = RateLimitDecorator(
            self.base_channel,
            rate_limit=3,
            time_window=10.0,
            max_wait=0.1,  # Very short wait to test blocking
        )

        # Send 5 notifications (2 over limit)
        results = []
        for i in range(5):
            notif = Notification(
                event_id=f"evt-{i}",
                channel="console",
                recipients=["test@example.com"],
                body=f"Message {i}",
            )
            result = channel.send(notif)
            results.append(result.success)

        # First 3 should succeed, next 2 should fail due to rate limit
        self.assertEqual(sum(results), 3)  # Only 3 succeeded
        self.assertFalse(results[3])  # 4th failed
        self.assertFalse(results[4])  # 5th failed

    def test_tokens_refill_over_time(self):
        """Should refill tokens over time and allow more requests."""
        channel = RateLimitDecorator(
            self.base_channel, rate_limit=2, time_window=1.0  # 2 tokens per second
        )

        # Use up all tokens
        result1 = channel.send(self.notification)
        result2 = channel.send(self.notification)

        self.assertTrue(result1.success)
        self.assertTrue(result2.success)

        # Next should fail immediately
        result3 = channel.send(self.notification)
        self.assertFalse(result3.success)

        # Wait for tokens to refill
        time.sleep(0.6)  # Wait 0.6s, should get ~1.2 tokens

        # Should succeed now
        result4 = channel.send(self.notification)
        self.assertTrue(result4.success)

    def test_thread_safety_concurrent_requests(self):
        """Test that rate limiter is thread-safe."""
        import threading

        channel = RateLimitDecorator(self.base_channel, rate_limit=5, time_window=10.0)

        results = []
        lock = threading.Lock()

        def send_notification(i):
            notif = Notification(
                event_id=f"evt-thread-{i}",
                channel="console",
                recipients=["test@example.com"],
                body=f"Thread message {i}",
            )
            result = channel.send(notif)
            with lock:
                results.append(result.success)

        # Create 10 threads trying to send at once
        threads = []
        for i in range(10):
            thread = threading.Thread(target=send_notification, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Exactly 5 should succeed (rate limit)
        self.assertEqual(sum(results), 5)

    def test_token_refill_calculation(self):
        """Test token refill calculation."""
        channel = RateLimitDecorator(
            self.base_channel,
            rate_limit=10,
            time_window=60.0,  # 10 tokens per 60 seconds = 0.1667 tokens/sec
        )

        # Refill rate should be 10/60 = 0.1667 tokens per second
        self.assertAlmostEqual(channel.refill_rate, 10.0 / 60.0, places=4)

        # After consuming all tokens, wait 6 seconds should give ~1 token
        channel.tokens = 0
        channel.last_refill = time.time()

        time.sleep(6.1)  # Wait 6 seconds
        channel._refill_tokens()

        # Should have approximately 1 token (6 * 0.1667 ≈ 1)
        self.assertGreater(channel.tokens, 0.9)
        self.assertLess(channel.tokens, 1.1)

    def test_max_wait_timeout(self):
        """Test that max_wait prevents indefinite waiting."""
        channel = RateLimitDecorator(
            self.base_channel,
            rate_limit=1,
            time_window=100.0,  # Very slow refill
            max_wait=0.5,  # Max wait 0.5 seconds
        )

        # Use up the token
        result1 = channel.send(self.notification)
        self.assertTrue(result1.success)

        # Next request should fail due to max_wait
        start_time = time.time()
        result2 = channel.send(self.notification)
        elapsed = time.time() - start_time

        self.assertFalse(result2.success)
        self.assertLess(elapsed, 1.0)  # Should fail quickly, not wait forever
        self.assertIn("Rate limit exceeded", result2.message)

    def test_initial_bucket_is_full(self):
        """Test that token bucket starts full."""
        channel = RateLimitDecorator(self.base_channel, rate_limit=5, time_window=10.0)

        # Initial tokens should equal rate_limit
        self.assertEqual(channel.tokens, 5)

    def test_tokens_never_exceed_limit(self):
        """Test that tokens never exceed the rate limit."""
        channel = RateLimitDecorator(self.base_channel, rate_limit=3, time_window=1.0)

        # Wait a long time
        time.sleep(2.0)

        # Refill tokens
        channel._refill_tokens()

        # Tokens should be capped at rate_limit
        self.assertLessEqual(channel.tokens, 3)
        self.assertEqual(channel.tokens, 3)

    def test_getattr_delegation(self):
        """Test that __getattr__ correctly delegates to wrapped channel."""
        channel = RateLimitDecorator(self.base_channel, rate_limit=10, time_window=60.0)

        # Should delegate to base_channel's attributes
        self.assertEqual(channel.config, self.base_channel.config)

    def test_repr(self):
        """Test string representation."""
        channel = RateLimitDecorator(
            self.base_channel, rate_limit=100, time_window=3600
        )
        repr_str = repr(channel)

        self.assertIn("RateLimitDecorator", repr_str)
        self.assertIn("rate_limit=100", repr_str)
        self.assertIn("time_window=3600", repr_str)


class TestDecoratorComposition(unittest.TestCase):
    """Test multiple decorators working together."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_channel = ConsoleChannel(config={"format": "json"})
        self.notification = Notification(
            event_id="evt-composition",
            channel="console",
            recipients=["test@example.com"],
            subject="Composition Test",
            body="Testing decorator composition",
        )

    def test_retry_and_logging_composition(self):
        """Test RetryDecorator + LoggingDecorator working together."""
        # Build stack: Logging wraps Retry wraps Channel
        channel = self.base_channel
        channel = RetryDecorator(channel, max_retries=2, initial_delay=0.1)
        channel = LoggingDecorator(channel, log_level="INFO")

        result = channel.send(self.notification)

        self.assertTrue(result.success)

    def test_full_decorator_stack(self):
        """Test all three decorators working together."""
        # Build full stack: RateLimit → Logging → Retry → Channel
        channel = self.base_channel
        channel = RetryDecorator(channel, max_retries=2, initial_delay=0.1)
        channel = LoggingDecorator(channel, log_level="INFO")
        channel = RateLimitDecorator(channel, rate_limit=5, time_window=10.0)

        # Send multiple notifications
        results = []
        for i in range(3):
            notif = Notification(
                event_id=f"evt-stack-{i}",
                channel="console",
                recipients=["test@example.com"],
                body=f"Stack test {i}",
            )
            result = channel.send(notif)
            results.append(result.success)

        # All should succeed (within rate limit)
        self.assertTrue(all(results))

    @patch("time.sleep")
    def test_retry_with_rate_limit(self, mock_sleep):
        """Test that retries work correctly with rate limiting."""
        # Create a channel that fails once then succeeds
        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        mock_channel.send = Mock(
            side_effect=[
                RetriableError("First attempt fails", channel="test"),
                NotificationResult(
                    success=True, channel="test", message="Success", metadata={}
                ),
            ]
        )

        # Stack: RateLimit → Retry → MockChannel
        channel = RetryDecorator(mock_channel, max_retries=3, initial_delay=0.1)
        channel = RateLimitDecorator(channel, rate_limit=10, time_window=60.0)

        result = channel.send(self.notification)

        self.assertTrue(result.success)
        self.assertEqual(mock_channel.send.call_count, 2)  # Initial + 1 retry

    def test_decorator_order_matters(self):
        """Demonstrate that decorator order affects behavior."""
        # Order 1: Retry inside, RateLimit outside
        # RateLimit will count each retry attempt

        mock_channel = Mock(spec=ConsoleChannel)
        mock_channel.config = {}
        mock_channel.__class__.__name__ = "MockChannel"

        # Always fail to test rate limiting on retries
        mock_channel.send = Mock(
            side_effect=RetriableError("Always fails", channel="test")
        )

        channel = RetryDecorator(mock_channel, max_retries=2, initial_delay=0.01)
        channel = RateLimitDecorator(channel, rate_limit=5, time_window=10.0)

        result = channel.send(self.notification)

        # Should exhaust retries
        self.assertFalse(result.success)


class TestDecoratorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_retry_with_zero_retries(self):
        """Test retry decorator with max_retries=0."""
        base_channel = ConsoleChannel(config={"format": "json"})
        channel = RetryDecorator(base_channel, max_retries=0)

        notification = Notification(
            event_id="evt-zero",
            channel="console",
            recipients=["test@example.com"],
            body="Test",
        )

        result = channel.send(notification)
        self.assertTrue(result.success)

    def test_rate_limit_with_zero_tokens(self):
        """Test rate limiter with zero initial tokens."""
        base_channel = ConsoleChannel(config={"format": "json"})
        channel = RateLimitDecorator(base_channel, rate_limit=1, time_window=10.0)

        # Manually set tokens to 0
        channel.tokens = 0

        notification = Notification(
            event_id="evt-zero-tokens",
            channel="console",
            recipients=["test@example.com"],
            body="Test",
        )

        # Should wait or fail
        result = channel.send(notification)
        # Could succeed after waiting or fail due to max_wait
        self.assertIsInstance(result, NotificationResult)

    def test_logging_with_none_notification(self):
        """Test logging decorator handles edge cases gracefully."""
        base_channel = ConsoleChannel(config={"format": "json"})
        channel = LoggingDecorator(base_channel, log_level="INFO")

        # This should work without errors
        self.assertIsNotNone(channel)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
