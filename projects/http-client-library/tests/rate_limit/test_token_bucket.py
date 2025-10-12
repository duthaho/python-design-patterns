"""
Tests for token bucket rate limiter.

Pattern: State (testing)
"""

import time

import pytest

from http_client.rate_limit.token_bucket import TokenBucket


class TestTokenBucket:
    """Test TokenBucket rate limiter"""

    def test_initialization(self):
        """Test token bucket initializes correctly"""
        bucket = TokenBucket(rate=10, capacity=20)
        assert bucket.rate == 10
        assert bucket.capacity == 20
        assert int(bucket.available_tokens()) == 20  # Starts full

    def test_initialization_with_invalid_rate_raises_error(self):
        """Test that invalid rate raises ValueError"""
        with pytest.raises(ValueError):
            TokenBucket(rate=0, capacity=10)

        with pytest.raises(ValueError):
            TokenBucket(rate=-1, capacity=10)

    def test_initialization_with_invalid_capacity_raises_error(self):
        """Test that invalid capacity raises ValueError"""
        with pytest.raises(ValueError):
            TokenBucket(rate=10, capacity=0)

        with pytest.raises(ValueError):
            TokenBucket(rate=10, capacity=-1)

    def test_acquire_single_token(self):
        """Test acquiring a single token"""
        bucket = TokenBucket(rate=10, capacity=10)

        assert bucket.acquire(tokens=1, blocking=False) is True
        assert int(bucket.available_tokens()) == 9

    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens"""
        bucket = TokenBucket(rate=10, capacity=10)

        assert bucket.acquire(tokens=3, blocking=False) is True
        assert int(bucket.available_tokens()) == 7

    def test_acquire_fails_when_insufficient_tokens(self):
        """Test acquire fails when not enough tokens"""
        bucket = TokenBucket(rate=10, capacity=5)

        # Drain tokens
        assert bucket.acquire(tokens=5, blocking=False) is True

        # Should fail now
        assert bucket.acquire(tokens=1, blocking=False) is False

    def test_tokens_refill_over_time(self):
        """Test that tokens refill based on rate"""
        bucket = TokenBucket(rate=10, capacity=10)  # 10 tokens per second

        # Drain all tokens
        bucket.acquire(tokens=10, blocking=False)
        assert int(bucket.available_tokens()) == 0

        # Wait for refill (0.5 seconds = 5 tokens at rate=10)
        time.sleep(0.5)

        tokens = bucket.available_tokens()
        assert 4 <= tokens <= 6  # Allow some timing variance

    def test_tokens_cap_at_capacity(self):
        """Test that tokens don't exceed capacity"""
        bucket = TokenBucket(rate=10, capacity=10)

        # Wait longer than needed to refill
        time.sleep(2)

        # Should still be capped at capacity
        assert int(bucket.available_tokens()) == 10

    def test_wait_time_calculation(self):
        """Test wait time calculation"""
        bucket = TokenBucket(rate=10, capacity=10)

        # Drain all tokens
        bucket.acquire(tokens=10, blocking=False)

        # Wait time for 1 token at rate=10 should be ~0.1 seconds
        wait = bucket.wait_time(tokens=1)
        assert 0.09 <= wait <= 0.11

    def test_wait_time_zero_when_tokens_available(self):
        """Test wait time is zero when tokens available"""
        bucket = TokenBucket(rate=10, capacity=10)

        wait = bucket.wait_time(tokens=1)
        assert wait == 0

    def test_reset(self):
        """Test reset refills bucket to capacity"""
        bucket = TokenBucket(rate=10, capacity=10)

        # Drain tokens
        bucket.acquire(tokens=10, blocking=False)
        assert int(bucket.available_tokens()) == 0

        # Reset
        bucket.reset()
        assert int(bucket.available_tokens()) == 10

    def test_thread_safety(self):
        """Test thread-safe token acquisition"""
        import threading

        bucket = TokenBucket(rate=100, capacity=100)
        acquired = []

        def acquire_tokens():
            if bucket.acquire(tokens=1, blocking=False):
                acquired.append(1)

        # Try to acquire 100 tokens from 200 threads
        threads = [threading.Thread(target=acquire_tokens) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should only successfully acquire 100 (capacity)
        assert len(acquired) < 200

    def test_acquire_blocking_waits(self):
        """Test that blocking acquire waits for tokens"""
        bucket = TokenBucket(rate=10, capacity=5)

        # Drain tokens
        bucket.acquire(tokens=5, blocking=False)

        start = time.time()
        # This should wait ~0.1 seconds for 1 token
        result = bucket.acquire(tokens=1, blocking=True, timeout=0.2)
        elapsed = time.time() - start

        assert result is True
        assert 0.05 <= elapsed <= 0.15  # Allow some variance

    def test_acquire_blocking_timeout(self):
        """Test that blocking acquire respects timeout"""
        bucket = TokenBucket(rate=1, capacity=1)  # Very slow refill

        # Drain tokens
        bucket.acquire(tokens=1, blocking=False)

        # Try to acquire with short timeout
        result = bucket.acquire(tokens=1, blocking=True, timeout=0.1)

        assert result is False  # Should timeout

    def test_repr(self):
        """Test string representation"""
        bucket = TokenBucket(rate=10, capacity=20)
        repr_str = repr(bucket)

        assert "TokenBucket" in repr_str
        assert "rate=10" in repr_str
        assert "capacity=20" in repr_str


class TestTokenBucketRefillAccuracy:
    """Test refill accuracy under various conditions"""

    def test_refill_accuracy_slow_rate(self):
        """Test refill with slow rate (1 token per second)"""
        bucket = TokenBucket(rate=1, capacity=10)
        bucket.acquire(tokens=10, blocking=False)

        time.sleep(1.0)

        tokens = bucket.available_tokens()
        assert 0.9 <= tokens <= 1.1

    def test_refill_accuracy_fast_rate(self):
        """Test refill with fast rate (100 tokens per second)"""
        bucket = TokenBucket(rate=100, capacity=100)
        bucket.acquire(tokens=50, blocking=False)

        time.sleep(0.5)  # Should refill ~50 tokens

        tokens = bucket.available_tokens()
        assert 100 <= tokens

    def test_partial_refill(self):
        """Test partial refill doesn't lose fractional tokens"""
        bucket = TokenBucket(rate=10, capacity=100)

        # Use some tokens
        bucket.acquire(tokens=50, blocking=False)

        # Wait for partial refill
        time.sleep(0.25)  # 2.5 tokens

        tokens1 = bucket.available_tokens()

        # Wait more
        time.sleep(0.25)  # 2.5 more tokens

        tokens2 = bucket.available_tokens()

        # Should have gained approximately 5 tokens total
        assert tokens2 > tokens1
        assert 4 <= (tokens2 - 50) <= 6


class TestTokenBucketEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_acquire_zero_tokens(self):
        """Test acquiring zero tokens"""
        bucket = TokenBucket(rate=10, capacity=10)

        assert bucket.acquire(tokens=0, blocking=False) is True
        assert int(bucket.available_tokens()) == 10

    def test_acquire_more_than_capacity(self):
        """Test acquiring more tokens than capacity"""
        bucket = TokenBucket(rate=10, capacity=5)

        # Should fail even with full bucket
        assert bucket.acquire(tokens=10, blocking=False) is False

    def test_fractional_tokens(self):
        """Test that bucket handles fractional tokens correctly"""
        bucket = TokenBucket(rate=10, capacity=10)

        # Use some tokens
        bucket.acquire(tokens=5, blocking=False)

        # Wait for fractional refill
        time.sleep(0.05)  # 0.5 tokens

        # Available tokens should include fractional part
        tokens = bucket.available_tokens()
        assert tokens > 5  # Should have partial refill
