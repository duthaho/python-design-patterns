"""
Tests for retry strategies.

Pattern: Strategy (testing)
"""

from unittest.mock import Mock

import pytest
import requests

from http_client.retry.base import RetryStrategy, get_status_code
from http_client.retry.exponential import ExponentialBackoff
from http_client.retry.jittered import JitteredBackoff


class TestRetryStrategyBase:
    """Test RetryStrategy base class"""

    def test_initialization_with_default_max_retries(self):
        """Test retry strategy initializes with default max_retries"""

        # Create a concrete implementation for testing
        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()
        assert strategy.max_retries == 3

    def test_initialization_with_custom_max_retries(self):
        """Test retry strategy initializes with custom max_retries"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy(max_retries=5)
        assert strategy.max_retries == 5

    def test_initialization_with_negative_retries_raises_error(self):
        """Test that negative max_retries raises ValueError"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        with pytest.raises(ValueError):
            TestStrategy(max_retries=-1)

    def test_should_retry_returns_false_when_attempts_exhausted(self):
        """Test should_retry returns False when attempts >= max_retries"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy(max_retries=3)

        # Create a retryable error
        error = requests.exceptions.ConnectionError()

        assert strategy.should_retry(0, error) is True
        assert strategy.should_retry(1, error) is True
        assert strategy.should_retry(2, error) is True
        assert strategy.should_retry(3, error) is False  # Exhausted

    def test_should_retry_with_connection_error(self):
        """Test should_retry returns True for ConnectionError"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy(max_retries=3)
        error = requests.exceptions.ConnectionError()

        assert strategy.should_retry(0, error) is True

    def test_should_retry_with_timeout_error(self):
        """Test should_retry returns True for Timeout"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy(max_retries=3)
        error = requests.exceptions.Timeout()

        assert strategy.should_retry(0, error) is True

    def test_is_retryable_error_with_connection_error(self):
        """Test is_retryable_error returns True for ConnectionError"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()
        error = requests.exceptions.ConnectionError()

        assert strategy.is_retryable_error(error) is True

    def test_is_retryable_error_with_timeout(self):
        """Test is_retryable_error returns True for Timeout"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()
        error = requests.exceptions.Timeout()

        assert strategy.is_retryable_error(error) is True

    def test_is_retryable_error_with_500_status(self):
        """Test is_retryable_error returns True for 5xx errors"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()

        # Create HTTPError with 500 status
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)

        assert strategy.is_retryable_error(error) is True

    def test_is_retryable_error_with_429_status(self):
        """Test is_retryable_error returns True for 429 (rate limit)"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()

        response = Mock()
        response.status_code = 429
        error = requests.exceptions.HTTPError(response=response)

        assert strategy.is_retryable_error(error) is True

    def test_is_retryable_error_with_404_status(self):
        """Test is_retryable_error returns False for 404"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()

        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError(response=response)

        assert strategy.is_retryable_error(error) is False

    def test_is_retryable_error_with_400_status(self):
        """Test is_retryable_error returns False for 400"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy()

        response = Mock()
        response.status_code = 400
        error = requests.exceptions.HTTPError(response=response)

        assert strategy.is_retryable_error(error) is False

    def test_repr(self):
        """Test __repr__ shows max_retries"""

        class TestStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        strategy = TestStrategy(max_retries=5)
        repr_str = repr(strategy)

        assert "max_retries=5" in repr_str


class TestGetStatusCode:
    """Test get_status_code helper function"""

    def test_get_status_code_from_http_error(self):
        """Test extracting status code from HTTPError"""
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)

        assert get_status_code(error) == 500

    def test_get_status_code_with_no_response(self):
        """Test get_status_code returns 0 when no response"""
        error = requests.exceptions.ConnectionError()

        assert get_status_code(error) == 0

    def test_get_status_code_with_none_response(self):
        """Test get_status_code handles None response"""
        error = Mock()
        error.response = None

        assert get_status_code(error) == 0


class TestExponentialBackoff:
    """Test ExponentialBackoff strategy"""

    def test_initialization_with_defaults(self):
        """Test exponential backoff initializes with defaults"""
        strategy = ExponentialBackoff()

        assert strategy.max_retries == 3
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0

    def test_initialization_with_custom_values(self):
        """Test exponential backoff with custom values"""
        strategy = ExponentialBackoff(max_retries=5, base_delay=2.0, max_delay=120.0)

        assert strategy.max_retries == 5
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 120.0

    def test_initialization_with_invalid_base_delay(self):
        """Test that zero or negative base_delay raises error"""
        with pytest.raises(ValueError):
            ExponentialBackoff(base_delay=0)

        with pytest.raises(ValueError):
            ExponentialBackoff(base_delay=-1)

    def test_initialization_with_max_delay_less_than_base(self):
        """Test that max_delay < base_delay raises error"""
        with pytest.raises(ValueError):
            ExponentialBackoff(base_delay=10.0, max_delay=5.0)

    def test_calculate_delay_first_attempt(self):
        """Test delay calculation for first retry (attempt 0)"""
        strategy = ExponentialBackoff(base_delay=1.0)
        delay = strategy.calculate_delay(0)

        # 1.0 * (2^0) = 1.0
        assert delay == 1.0

    def test_calculate_delay_second_attempt(self):
        """Test delay calculation for second retry (attempt 1)"""
        strategy = ExponentialBackoff(base_delay=1.0)
        delay = strategy.calculate_delay(1)

        # 1.0 * (2^1) = 2.0
        assert delay == 2.0

    def test_calculate_delay_third_attempt(self):
        """Test delay calculation for third retry (attempt 2)"""
        strategy = ExponentialBackoff(base_delay=1.0)
        delay = strategy.calculate_delay(2)

        # 1.0 * (2^2) = 4.0
        assert delay == 4.0

    def test_calculate_delay_exponential_growth(self):
        """Test that delays grow exponentially"""
        strategy = ExponentialBackoff(base_delay=1.0)

        delays = [strategy.calculate_delay(i) for i in range(5)]

        # Should be: 1, 2, 4, 8, 16
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_calculate_delay_respects_max_delay(self):
        """Test that delay is capped at max_delay"""
        strategy = ExponentialBackoff(base_delay=1.0, max_delay=10.0)

        # Attempt 4: 1.0 * (2^4) = 16.0, but should be capped at 10.0
        delay = strategy.calculate_delay(4)

        assert delay == 10.0

    def test_calculate_delay_with_custom_base(self):
        """Test delay calculation with custom base_delay"""
        strategy = ExponentialBackoff(base_delay=2.0)

        delays = [strategy.calculate_delay(i) for i in range(4)]

        # Should be: 2, 4, 8, 16
        assert delays == [2.0, 4.0, 8.0, 16.0]

    def test_repr(self):
        """Test __repr__ shows all parameters"""
        strategy = ExponentialBackoff(max_retries=5, base_delay=2.0, max_delay=30.0)
        repr_str = repr(strategy)

        assert "ExponentialBackoff" in repr_str
        assert "max_retries=5" in repr_str
        assert "base_delay=2.0" in repr_str
        assert "max_delay=30.0" in repr_str


class TestJitteredBackoff:
    """Test JitteredBackoff strategy"""

    def test_initialization_with_defaults(self):
        """Test jittered backoff initializes with defaults"""
        strategy = JitteredBackoff()

        assert strategy.max_retries == 3
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0
        assert strategy.jitter_factor == 0.3

    def test_initialization_with_custom_values(self):
        """Test jittered backoff with custom values"""
        strategy = JitteredBackoff(
            max_retries=5, base_delay=2.0, max_delay=120.0, jitter_factor=0.5
        )

        assert strategy.jitter_factor == 0.5

    def test_initialization_with_invalid_jitter_factor(self):
        """Test that invalid jitter_factor raises error"""
        with pytest.raises(ValueError):
            JitteredBackoff(jitter_factor=-0.1)

        with pytest.raises(ValueError):
            JitteredBackoff(jitter_factor=1.5)

    def test_calculate_delay_includes_jitter(self):
        """Test that delay includes random jitter"""
        strategy = JitteredBackoff(base_delay=1.0, jitter_factor=0.3)

        # Calculate delay multiple times
        delays = [strategy.calculate_delay(0) for _ in range(10)]

        # All delays should be >= base_delay (1.0)
        assert all(d >= 1.0 for d in delays)

        # At least some delays should be different (due to jitter)
        assert len(set(delays)) > 1

    def test_calculate_delay_range(self):
        """Test that delay falls within expected range"""
        strategy = JitteredBackoff(base_delay=10.0, jitter_factor=0.3)

        # For attempt 0: base = 10.0, jitter range = [0, 3.0]
        # So delay should be in [10.0, 13.0]
        delays = [strategy.calculate_delay(0) for _ in range(100)]

        assert all(10.0 <= d <= 13.0 for d in delays)

    def test_calculate_delay_respects_max_delay(self):
        """Test that delay is capped at max_delay even with jitter"""
        strategy = JitteredBackoff(base_delay=1.0, max_delay=10.0, jitter_factor=0.5)

        # Even with large jitter, should not exceed max_delay
        delays = [strategy.calculate_delay(10) for _ in range(100)]

        assert all(d <= 10.0 for d in delays)

    def test_calculate_delay_increases_with_attempts(self):
        """Test that average delay increases with attempts"""
        strategy = JitteredBackoff(base_delay=1.0, jitter_factor=0.1)

        # Calculate average delays for different attempts
        avg_delay_0 = sum(strategy.calculate_delay(0) for _ in range(100)) / 100
        avg_delay_1 = sum(strategy.calculate_delay(1) for _ in range(100)) / 100
        avg_delay_2 = sum(strategy.calculate_delay(2) for _ in range(100)) / 100

        # Averages should increase
        assert avg_delay_0 < avg_delay_1 < avg_delay_2

    def test_repr(self):
        """Test __repr__ shows all parameters"""
        strategy = JitteredBackoff(max_retries=5, base_delay=2.0, max_delay=30.0, jitter_factor=0.4)
        repr_str = repr(strategy)

        assert "JitteredBackoff" in repr_str
        assert "jitter_factor=0.4" in repr_str


class TestRetryStrategyComparison:
    """Compare different retry strategies"""

    def test_exponential_vs_jittered_base_values(self):
        """Test that exponential and jittered have similar base delays"""
        exp = ExponentialBackoff(base_delay=1.0)
        jit = JitteredBackoff(base_delay=1.0, jitter_factor=0.0)

        # With jitter_factor=0, should match exponential
        for attempt in range(5):
            exp_delay = exp.calculate_delay(attempt)
            jit_delay = jit.calculate_delay(attempt)

            # Should be very close (jitter=0 means no randomness)
            assert abs(exp_delay - jit_delay) < 0.01

    def test_both_respect_max_retries(self):
        """Test both strategies respect max_retries"""
        exp = ExponentialBackoff(max_retries=3)
        jit = JitteredBackoff(max_retries=3)

        error = requests.exceptions.ConnectionError()

        for strategy in [exp, jit]:
            assert strategy.should_retry(0, error) is True
            assert strategy.should_retry(2, error) is True
            assert strategy.should_retry(3, error) is False
