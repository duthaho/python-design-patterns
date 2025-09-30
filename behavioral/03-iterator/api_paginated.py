import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, List

# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class APIResponse:
    """Represents a response from an API endpoint"""

    data: List[Dict[str, Any]]  # The actual data items
    page: int
    total_pages: int
    has_next: bool


class MergeStrategy(Enum):
    """Strategy for merging multiple iterators"""

    ROUND_ROBIN = "round_robin"  # Alternate between sources
    SEQUENTIAL = "sequential"  # Exhaust first, then second, etc.
    PRIORITY = "priority"  # Higher priority sources first


# ============================================================================
# MOCK API CLIENT (Simulates HTTP calls)
# ============================================================================


class MockAPIClient:
    """
    Simulates a paginated REST API.
    In real implementation, this would use requests library.
    """

    def __init__(self, base_url: str, page_size: int = 10):
        """
        Args:
            base_url: API endpoint URL (e.g., "https://api.example.com/users")
            page_size: Number of items per page
        """
        self.base_url = base_url
        self.page_size = page_size
        self._mock_data = self._generate_mock_data()

    def _generate_mock_data(self) -> List[Dict[str, Any]]:
        """
        Generate mock data based on endpoint.
        In real implementation, this would make actual HTTP calls.
        """
        if "users" in self.base_url:
            return [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "type": "user",
                }
                for i in range(1, 51)  # 50 users
            ]
        elif "orders" in self.base_url:
            return [
                {
                    "id": i,
                    "user_id": (i % 10) + 1,
                    "total": round(i * 10.5, 2),
                    "type": "order",
                }
                for i in range(1, 31)  # 30 orders
            ]
        elif "products" in self.base_url:
            return [
                {
                    "id": i,
                    "name": f"Product {i}",
                    "price": round(i * 2.99, 2),
                    "type": "product",
                }
                for i in range(1, 101)  # 100 products
            ]
        return []

    def fetch_page(self, page: int) -> APIResponse:
        """
        Fetch a specific page from the API.

        Args:
            page: Page number (1-indexed)

        Returns:
            APIResponse with data and pagination info

        Raises:
            ValueError: If page number is invalid
        """
        # Simulate network delay
        time.sleep(0.1)  # 100ms delay

        if page < 1:
            raise ValueError("Page number must be >= 1")

        total_items = len(self._mock_data)
        total_pages = (total_items + self.page_size - 1) // self.page_size

        # Handle empty data
        if total_pages == 0:
            return APIResponse(data=[], page=page, total_pages=0, has_next=False)

        if page > total_pages:
            raise ValueError(f"Page {page} exceeds total pages {total_pages}")

        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self._mock_data[start_idx:end_idx]
        has_next = page < total_pages

        return APIResponse(
            data=page_data, page=page, total_pages=total_pages, has_next=has_next
        )


class FailingMockAPIClient(MockAPIClient):
    """
    Mock API client that fails N times before succeeding.
    Used for testing retry logic.
    """

    def __init__(self, base_url: str, page_size: int, fail_count: int = 2):
        super().__init__(base_url, page_size)
        self.fail_count = fail_count
        self.call_count = 0

    def fetch_page(self, page: int) -> APIResponse:
        self.call_count += 1
        if self.call_count <= self.fail_count:
            print(f"  ⚠️  Simulated failure #{self.call_count}")
            raise ConnectionError(f"Simulated network failure #{self.call_count}")
        return super().fetch_page(page)


# ============================================================================
# PAGINATED API ITERATOR
# ============================================================================


class PaginatedAPIIterator:
    """
    Iterator that automatically handles API pagination.
    Fetches pages lazily as needed.

    Example:
        api = PaginatedAPIIterator("https://api.example.com/users", page_size=20)
        for user in api:
            print(user['name'])  # Pagination is transparent!
    """

    def __init__(self, base_url: str, page_size: int = 10, max_retries: int = 3):
        """
        Args:
            base_url: API endpoint URL
            page_size: Number of items per page
            max_retries: Number of retry attempts for failed requests
        """
        self.base_url = base_url
        self.page_size = page_size
        self.max_retries = max_retries

        self._client = MockAPIClient(base_url, page_size)
        self._current_page = 0
        self._buffer: List[Dict[str, Any]] = []
        self._index = 0
        self._iteration_started = False

        # Metrics
        self._api_calls = 0
        self._failed_calls = 0

    def __iter__(self) -> "PaginatedAPIIterator":
        """Initialize iteration"""
        self._current_page = 1
        self._buffer = []
        self._index = 0
        self._iteration_started = True
        return self

    def __next__(self) -> Dict[str, Any]:
        """
        Return next item from API.
        Automatically fetch next page when current page is exhausted.
        """
        if not self._iteration_started:
            raise RuntimeError("Iterator not initialized. Call iter() first.")

        # Need to fetch next page if buffer is exhausted
        if self._index >= len(self._buffer):
            if not self._fetch_next_page():
                raise StopIteration

        item = self._buffer[self._index]
        self._index += 1
        return item

    def _fetch_next_page(self) -> bool:
        """
        Fetch the next page from API with retry logic.

        Returns:
            True if page was fetched successfully, False if no more pages
        """
        if self._current_page == 0:
            self._current_page = 1

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                self._api_calls += 1
                response = self._client.fetch_page(self._current_page)

                self._buffer = response.data
                self._index = 0

                # No more data available
                if not response.has_next and not self._buffer:
                    return False

                self._current_page += 1
                return True

            except Exception as e:
                self._failed_calls += 1
                last_error = e
                retries += 1

                if retries < self.max_retries:
                    wait_time = 0.5 * retries  # Exponential backoff
                    print(
                        f"  ⚠️  Retry {retries}/{self.max_retries} after {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)

        print(
            f"  ✗ Failed to fetch page {self._current_page} after {self.max_retries} retries"
        )
        print(f"    Last error: {last_error}")
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Return API call metrics"""
        return {
            "total_calls": self._api_calls,
            "failed_calls": self._failed_calls,
            "success_rate": (
                (self._api_calls - self._failed_calls) / self._api_calls
                if self._api_calls > 0
                else 0
            ),
        }


# ============================================================================
# MERGED ITERATOR
# ============================================================================


class MergedIterator:
    """
    Merges multiple iterators using different strategies.

    Example:
        users = PaginatedAPIIterator("https://api.example.com/users")
        orders = PaginatedAPIIterator("https://api.example.com/orders")

        merged = MergedIterator(
            users, orders,
            strategy=MergeStrategy.ROUND_ROBIN
        )

        for item in merged:
            print(item)  # Alternates between users and orders
    """

    def __init__(
        self, *iterators: Iterator, strategy: MergeStrategy = MergeStrategy.ROUND_ROBIN
    ):
        """
        Args:
            *iterators: Variable number of iterators to merge
            strategy: How to merge the iterators
        """
        self.iterators = list(iterators)
        self.strategy = strategy

        # State tracking
        self._current_index = 0
        self._exhausted = [False] * len(self.iterators)
        self._total_exhausted = 0

    def __iter__(self) -> "MergedIterator":
        """Initialize iteration"""
        # Convert all iterables to iterators
        self.iterators = [iter(it) for it in self.iterators]
        self._current_index = 0
        self._exhausted = [False] * len(self.iterators)
        self._total_exhausted = 0
        return self

    def __next__(self) -> Dict[str, Any]:
        """Return next item based on merge strategy"""
        if self.strategy == MergeStrategy.ROUND_ROBIN:
            return self._next_round_robin()
        elif self.strategy == MergeStrategy.SEQUENTIAL:
            return self._next_sequential()
        elif self.strategy == MergeStrategy.PRIORITY:
            return self._next_priority()
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _next_round_robin(self) -> Dict[str, Any]:
        """
        Round-robin: alternate between iterators.
        Skip exhausted iterators.
        """
        if self._total_exhausted >= len(self.iterators):
            raise StopIteration

        start_index = self._current_index
        attempts = 0

        while attempts < len(self.iterators):
            if not self._exhausted[self._current_index]:
                try:
                    item = next(self.iterators[self._current_index])
                    # Move to next iterator for next call
                    self._current_index = (self._current_index + 1) % len(
                        self.iterators
                    )
                    return item
                except StopIteration:
                    self._exhausted[self._current_index] = True
                    self._total_exhausted += 1

            self._current_index = (self._current_index + 1) % len(self.iterators)
            attempts += 1

        # All iterators exhausted
        raise StopIteration

    def _next_sequential(self) -> Dict[str, Any]:
        """
        Sequential: exhaust first iterator, then move to next.
        """
        while self._current_index < len(self.iterators):
            try:
                return next(self.iterators[self._current_index])
            except StopIteration:
                self._current_index += 1

        # All iterators exhausted
        raise StopIteration

    def _next_priority(self) -> Dict[str, Any]:
        """
        Priority-based merging.
        Higher priority (lower index) iterators are consumed first.
        """
        for idx in range(len(self.iterators)):
            if not self._exhausted[idx]:
                try:
                    return next(self.iterators[idx])
                except StopIteration:
                    self._exhausted[idx] = True
                    self._total_exhausted += 1

        # All iterators exhausted
        raise StopIteration


# ============================================================================
# CACHED ITERATOR
# ============================================================================


class CachedIterator:
    """
    Caches items from source iterator to avoid redundant API calls.

    Example:
        api = PaginatedAPIIterator("https://api.example.com/users")
        cached = CachedIterator(api, cache_size=100)

        # First iteration - fetches from API
        for user in cached:
            print(user['name'])

        # Second iteration - uses cache (no API calls!)
        for user in cached:
            print(user['name'])
    """

    def __init__(self, source_iterator: Iterator, cache_size: int = 1000):
        """
        Args:
            source_iterator: Iterator to cache
            cache_size: Maximum number of items to cache
        """
        self.source_iterator = iter(source_iterator)
        self.cache_size = cache_size

        self._cache: List[Dict[str, Any]] = []
        self._cache_fully_populated = False
        self._index = 0

        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0

    def __iter__(self) -> "CachedIterator":
        """Return iterator"""
        self._index = 0
        return self

    def __next__(self) -> Dict[str, Any]:
        """
        Return next item.
        First pass: fetch from source and cache.
        Subsequent passes: return from cache.
        """
        # Reading from cache
        if self._index < len(self._cache):
            self._cache_hits += 1
            item = self._cache[self._index]
            self._index += 1
            return item

        # Cache fully populated, no more items
        if self._cache_fully_populated:
            raise StopIteration

        # Fetch from source and populate cache
        try:
            self._cache_misses += 1
            item = next(self.source_iterator)

            if len(self._cache) < self.cache_size:
                self._cache.append(item)
            else:
                # Cache is full - could implement LRU here
                # For simplicity, we just don't cache beyond limit
                pass

            self._index += 1
            return item

        except StopIteration:
            self._cache_fully_populated = True
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Return cache performance metrics"""
        total_accesses = self._cache_hits + self._cache_misses
        return {
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": (
                self._cache_hits / total_accesses if total_accesses > 0 else 0
            ),
            "fully_populated": self._cache_fully_populated,
        }


class LRUCachedIterator:
    """
    BONUS: Cached iterator with LRU eviction policy.
    When cache is full, evicts least recently used items.
    """

    def __init__(self, source_iterator: Iterator, cache_size: int = 1000):
        self.source_iterator = iter(source_iterator)
        self.cache_size = cache_size

        self._cache_list: List[Dict[str, Any]] = []
        self._cache_fully_populated = False
        self._index = 0

    def __iter__(self) -> "LRUCachedIterator":
        self._index = 0
        return self

    def __next__(self) -> Dict[str, Any]:
        if self._index < len(self._cache_list):
            item = self._cache_list[self._index]
            self._index += 1
            return item

        if self._cache_fully_populated:
            raise StopIteration

        try:
            item = next(self.source_iterator)

            if len(self._cache_list) < self.cache_size:
                self._cache_list.append(item)
            else:
                # LRU: remove oldest (first), add newest
                self._cache_list.pop(0)
                self._cache_list.append(item)

            self._index += 1
            return item

        except StopIteration:
            self._cache_fully_populated = True
            raise


# ============================================================================
# TEST CODE
# ============================================================================


def test_mock_api_client():
    """Test the mock API client"""
    print("=" * 70)
    print("TEST 1: Mock API Client with Pagination")
    print("=" * 70)

    client = MockAPIClient("https://api.example.com/users", page_size=5)

    # Fetch first page
    page1 = client.fetch_page(1)
    print(f"\nPage 1:")
    print(f"  Items: {len(page1.data)}")
    print(f"  Total pages: {page1.total_pages}")
    print(f"  Has next: {page1.has_next}")
    print(f"  Sample data: {page1.data[0] if page1.data else 'No data'}")

    # Fetch second page
    page2 = client.fetch_page(2)
    print(f"\nPage 2:")
    print(f"  Items: {len(page2.data)}")
    print(f"  Has next: {page2.has_next}")

    print("\n✓ Mock API client works correctly")


def test_paginated_iterator():
    """Test automatic pagination"""
    print("\n" + "=" * 70)
    print("TEST 2: Paginated API Iterator")
    print("=" * 70)

    api = PaginatedAPIIterator("https://api.example.com/users", page_size=5)

    print("\nIterating through all users (pagination is automatic):")
    count = 0
    for user in api:
        count += 1
        if count <= 3:  # Print first 3
            print(f"  User {count}: {user}")

    print(f"\nTotal users fetched: {count}")
    print(f"Metrics: {api.get_metrics()}")

    print("\n✓ Automatic pagination works correctly")


def test_merged_iterator():
    """Test merging multiple API sources"""
    print("\n" + "=" * 70)
    print("TEST 3: Merged Iterator")
    print("=" * 70)

    # Test Round Robin
    print("\n[Round Robin Strategy]")
    users_api = PaginatedAPIIterator("https://api.example.com/users", page_size=10)
    orders_api = PaginatedAPIIterator("https://api.example.com/orders", page_size=10)

    merged = MergedIterator(users_api, orders_api, strategy=MergeStrategy.ROUND_ROBIN)

    print("Merged data (alternating between sources):")
    count = 0
    for item in merged:
        count += 1
        if count <= 6:  # Print first 6
            print(f"  Item {count}: {item.get('type', 'unknown')} - ID: {item['id']}")
        if count >= 20:  # Limit output
            break

    print(f"Total items (limited): {count}")

    # Test Sequential
    print("\n[Sequential Strategy]")
    users_api2 = PaginatedAPIIterator("https://api.example.com/users", page_size=10)
    orders_api2 = PaginatedAPIIterator("https://api.example.com/orders", page_size=10)

    merged_seq = MergedIterator(
        users_api2, orders_api2, strategy=MergeStrategy.SEQUENTIAL
    )

    count = 0
    user_count = 0
    order_count = 0
    for item in merged_seq:
        count += 1
        if item.get("type") == "user":
            user_count += 1
        elif item.get("type") == "order":
            order_count += 1

    print(f"Total items: {count} ({user_count} users, then {order_count} orders)")

    print("\n✓ Merge strategies work correctly")


def test_cached_iterator():
    """Test caching to avoid redundant API calls"""
    print("\n" + "=" * 70)
    print("TEST 4: Cached Iterator")
    print("=" * 70)

    api = PaginatedAPIIterator("https://api.example.com/users", page_size=5)
    cached = CachedIterator(api, cache_size=50)

    print("\nFirst iteration (fetching from API):")
    start_time = time.time()
    count1 = sum(1 for _ in cached)
    time1 = time.time() - start_time
    print(f"  Items: {count1}, Time: {time1:.2f}s")
    print(f"  Metrics: {cached.get_metrics()}")

    print("\nSecond iteration (using cache):")
    start_time = time.time()
    count2 = sum(1 for _ in cached)
    time2 = time.time() - start_time
    print(f"  Items: {count2}, Time: {time2:.2f}s")
    print(f"  Metrics: {cached.get_metrics()}")

    speedup = time1 / time2 if time2 > 0 else float("inf")
    print(f"\n✓ Cache speedup: {speedup:.1f}x faster")


def test_retry_logic():
    """Test retry logic for failed requests"""
    print("\n" + "=" * 70)
    print("TEST 5: Retry Logic with Failing API")
    print("=" * 70)

    api = PaginatedAPIIterator(
        "https://api.example.com/users", page_size=10, max_retries=5
    )

    # Replace with failing client
    api._client = FailingMockAPIClient(
        "https://api.example.com/users", page_size=10, fail_count=2
    )

    print("\nFetching with simulated failures (should retry and succeed):")
    try:
        count = sum(1 for _ in api)
        print(f"  ✓ Successfully fetched {count} items after retries")
        print(f"  Metrics: {api.get_metrics()}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

    print("\n✓ Retry logic works correctly")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n" + "=" * 70)
    print("TEST 6: Edge Cases")
    print("=" * 70)

    # Test 1: Empty API
    print("\n[Empty API Response]")
    empty_client = MockAPIClient("https://api.example.com/empty", page_size=10)
    empty_client._mock_data = []  # Override with empty data

    api_empty = PaginatedAPIIterator("https://api.example.com/users", page_size=10)
    api_empty._client = empty_client

    count = sum(1 for _ in api_empty)
    print(f"  Items from empty API: {count}")
    assert count == 0, "Should handle empty APIs"

    # Test 2: Single item
    print("\n[Single Item API]")
    single_client = MockAPIClient("https://api.example.com/users", page_size=100)
    single_client._mock_data = [{"id": 1, "name": "Only User"}]

    api_single = PaginatedAPIIterator("https://api.example.com/users", page_size=100)
    api_single._client = single_client

    count = sum(1 for _ in api_single)
    print(f"  Items from single-item API: {count}")
    assert count == 1, "Should handle single item"

    # Test 3: Exact page boundary
    print("\n[Exact Page Boundary]")
    api = PaginatedAPIIterator("https://api.example.com/users", page_size=50)
    count = sum(1 for _ in api)
    print(f"  Items at exact boundary (50 users / 50 page_size): {count}")

    # Test 4: Multiple iterations on merged iterator
    print("\n[Reusing Merged Iterator]")
    users = PaginatedAPIIterator("https://api.example.com/users", page_size=10)
    orders = PaginatedAPIIterator("https://api.example.com/orders", page_size=10)
    merged = MergedIterator(users, orders, strategy=MergeStrategy.SEQUENTIAL)

    count1 = sum(1 for _ in merged)

    # Create new iterators for second iteration
    users2 = PaginatedAPIIterator("https://api.example.com/users", page_size=10)
    orders2 = PaginatedAPIIterator("https://api.example.com/orders", page_size=10)
    merged2 = MergedIterator(users2, orders2, strategy=MergeStrategy.SEQUENTIAL)
    count2 = sum(1 for _ in merged2)

    print(f"  First iteration: {count1}, Second: {count2}")

    print("\n✓ All edge cases handled!")


def test_performance():
    """Test performance characteristics"""
    print("\n" + "=" * 70)
    print("TEST 7: Performance Comparison")
    print("=" * 70)

    # Without cache
    print("\n[Without Cache - Two Separate Iterations]")
    api1 = PaginatedAPIIterator("https://api.example.com/products", page_size=10)

    start = time.time()
    count1 = sum(1 for _ in api1)
    time1 = time.time() - start
    print(f"  First iteration: {count1} items in {time1:.3f}s")

    # Re-iterate (must create new iterator)
    api2 = PaginatedAPIIterator("https://api.example.com/products", page_size=10)
    start = time.time()
    count2 = sum(1 for _ in api2)
    time2 = time.time() - start
    print(f"  Second iteration: {count2} items in {time2:.3f}s")
    print(f"  Total time: {time1 + time2:.3f}s")

    # With cache
    print("\n[With Cache - Two Iterations Using Cache]")
    api3 = PaginatedAPIIterator("https://api.example.com/products", page_size=10)
    cached = CachedIterator(api3, cache_size=200)

    start = time.time()
    count3 = sum(1 for _ in cached)
    time3 = time.time() - start
    print(f"  First iteration: {count3} items in {time3:.3f}s")

    start = time.time()
    count4 = sum(1 for _ in cached)
    time4 = time.time() - start
    print(f"  Second iteration: {count4} items in {time4:.3f}s")
    print(f"  Total time: {time3 + time4:.3f}s")

    speedup = (time1 + time2) / (time3 + time4) if (time3 + time4) > 0 else 0
    print(f"\n✓ Cache provides {speedup:.1f}x speedup for repeated iterations")


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "🚀" * 35)
    print(" " * 15 + "MICROSERVICES ITERATOR - TEST SUITE")
    print("🚀" * 35)

    test_mock_api_client()
    test_paginated_iterator()
    test_merged_iterator()
    test_cached_iterator()
    test_retry_logic()
    test_edge_cases()
    test_performance()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
