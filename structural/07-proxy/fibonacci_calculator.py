import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, OrderedDict


class CalculatorInterface(ABC):
    @abstractmethod
    def calculate(self, n: int) -> int:
        pass


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def __str__(self) -> str:
        return f"Cache Stats - Hits: {self.hits}, Misses: {self.misses}, Evictions: {self.evictions}, Hit Rate: {self.hit_rate:.2%}"


class FibonacciCalculator(CalculatorInterface):
    def calculate(self, n: int) -> int:
        print(f"Computing fibonacci({n})...")
        time.sleep(0.1)  # Simulate delay

        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b


class CachingFibonacciProxy(CalculatorInterface):
    def __init__(self, wrapped: CalculatorInterface, max_cache_size: int = 100):
        self._wrapped = wrapped
        self._cache: OrderedDict[int, int] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._stats = CacheStats()

    def calculate(self, n: int) -> int:
        if n in self._cache:
            # Cache hit - move to end (most recently used)
            self._stats.hits += 1
            print(f"Cache HIT for fibonacci({n})")
            # Move to end for LRU
            self._cache.move_to_end(n)
            return self._cache[n]

        # Cache miss - compute result
        self._stats.misses += 1
        print(f"Cache MISS for fibonacci({n})")
        result = self._wrapped.calculate(n)

        # Add to cache with LRU eviction if needed
        self._add_to_cache(n, result)
        return result

    def _add_to_cache(self, key: int, value: int) -> None:
        """Add item to cache, evicting LRU item if cache is full"""
        if len(self._cache) >= self._max_cache_size and key not in self._cache:
            # Evict least recently used (first item)
            evicted_key, _ = self._cache.popitem(last=False)
            self._stats.evictions += 1
            print(f"Evicted fibonacci({evicted_key}) from cache")

        self._cache[key] = value
        # Move to end (most recently used)
        self._cache.move_to_end(key)

    def clear_cache(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        print("Cache cleared")

    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        return self._stats

    def get_cache_size(self) -> int:
        """Get current cache size"""
        return len(self._cache)

    def get_cached_keys(self) -> list[int]:
        """Get list of currently cached keys (most recent first)"""
        return list(reversed(self._cache.keys()))


def main() -> None:
    calculator = FibonacciCalculator()
    # Small cache size to demonstrate eviction
    cached_calculator = CachingFibonacciProxy(calculator, max_cache_size=3)

    print("=== Testing Cache Functionality ===")

    # Test cache hits and misses
    test_numbers = [10, 20, 30, 10, 40, 50, 20, 10]  # Will trigger evictions

    for i, n in enumerate(test_numbers):
        print(f"\n--- Request {i+1}: fibonacci({n}) ---")
        result = cached_calculator.calculate(n)
        print(f"Result: {result}")
        print(f"Cache size: {cached_calculator.get_cache_size()}")
        print(f"Cached keys: {cached_calculator.get_cached_keys()}")

    print(f"\n=== Final Statistics ===")
    print(cached_calculator.get_stats())

    print(f"\n=== Testing Cache Clear ===")
    cached_calculator.clear_cache()
    print(f"Cache size after clear: {cached_calculator.get_cache_size()}")


if __name__ == "__main__":
    main()
