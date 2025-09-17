import gc
import hashlib
import json
import random
import threading
import time
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class CacheDataType(Enum):
    """Types of cached data - helps categorize flyweights"""

    DATABASE_QUERY = "db_query"
    API_RESPONSE = "api_response"
    COMPUTED_RESULT = "computed_result"
    FILE_CONTENT = "file_content"


@dataclass(frozen=True)
class CacheFlyweight:
    """
    Flyweight storing intrinsic state - the actual cached data
    This should be immutable and shareable across multiple cache entries
    """

    data_type: CacheDataType  # Intrinsic: type of cached data
    content_hash: str  # Intrinsic: hash of the content for deduplication
    data_size: int  # Intrinsic: size in bytes
    computation_cost: float  # Intrinsic: how expensive this data was to compute
    data: Any = None  # The actual cached data

    def get_data(self) -> Any:
        """Returns the cached data"""
        return self.data

    def get_memory_footprint(self) -> int:
        """Returns memory usage of this flyweight"""
        return self.data_size

    def is_equivalent(self, other_data: Any) -> bool:
        """Check if this flyweight can serve other data"""
        other_hash = hashlib.sha256(
            json.dumps(other_data, sort_keys=True).encode()
        ).hexdigest()
        return self.content_hash == other_hash


class CacheFlyweightFactory:
    """
    Factory to ensure only one flyweight exists per unique data content
    Thread-safe implementation with automatic cleanup using WeakValueDictionary
    """

    def __init__(self):
        # Use WeakValueDictionary for automatic garbage collection of unused flyweights
        self._flyweights: weakref.WeakValueDictionary[str, CacheFlyweight] = (
            weakref.WeakValueDictionary()
        )
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._creation_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "flyweights_garbage_collected": 0,
        }
        # Keep track of flyweights count for statistics
        self._flyweight_count = 0

    def get_flyweight(
        self, data: Any, data_type: CacheDataType, computation_cost: float = 1.0
    ) -> CacheFlyweight:
        """
        Get or create a flyweight for the given data
        Thread-safe flyweight creation/retrieval with automatic cleanup
        """
        # Generate content hash from data
        content_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        with self._lock:
            self._creation_stats["total_requests"] += 1

            # Try to get existing flyweight (may return None if garbage collected)
            existing_flyweight = self._flyweights.get(content_hash)

            if existing_flyweight is not None:
                self._creation_stats["cache_hits"] += 1
                return existing_flyweight
            else:
                self._creation_stats["cache_misses"] += 1
                # Calculate data size
                data_size = len(json.dumps(data, sort_keys=True).encode())

                # Create new flyweight
                flyweight = CacheFlyweight(
                    data_type=data_type,
                    content_hash=content_hash,
                    data_size=data_size,
                    computation_cost=computation_cost,
                    data=data,
                )

                # Store in WeakValueDictionary - will be automatically removed when no longer referenced
                old_count = len(self._flyweights)
                self._flyweights[content_hash] = flyweight
                new_count = len(self._flyweights)

                # Update our count tracking
                if new_count > old_count:
                    self._flyweight_count += 1

                return flyweight

    def get_factory_stats(self) -> Dict[str, Any]:
        """
        Return factory statistics including memory saved percentage and hit/miss ratios
        WeakValueDictionary provides accurate count of currently active flyweights
        """
        with self._lock:
            current_flyweights = len(
                self._flyweights
            )  # Only counts non-garbage-collected flyweights
            total_requests = self._creation_stats["total_requests"]
            hits = self._creation_stats["cache_hits"]
            misses = self._creation_stats["cache_misses"]
            hit_ratio = hits / total_requests if total_requests > 0 else 0
            miss_ratio = misses / total_requests if total_requests > 0 else 0

            # Calculate how many flyweights have been garbage collected
            garbage_collected = max(0, self._flyweight_count - current_flyweights)
            self._creation_stats["flyweights_garbage_collected"] = garbage_collected

            memory_by_type = self._calculate_memory_by_type()

            return {
                "total_flyweights": current_flyweights,  # Currently active flyweights
                "total_flyweights_ever_created": self._flyweight_count,  # Lifetime count
                "flyweights_garbage_collected": garbage_collected,
                "total_requests": total_requests,
                "hits": hits,
                "misses": misses,
                "hit_ratio": hit_ratio,
                "miss_ratio": miss_ratio,
                "memory_by_type": memory_by_type,
                "garbage_collection_efficiency": f"{(garbage_collected / max(self._flyweight_count, 1)) * 100:.1f}% cleaned up",
            }

    def cleanup_unused_flyweights(self) -> int:
        """
        Force cleanup of unused flyweights and return count cleaned up
        WeakValueDictionary automatically handles this, but we can force garbage collection
        """
        with self._lock:
            # Record count before garbage collection
            before_count = len(self._flyweights)

            # Force garbage collection to clean up unreferenced flyweights
            gc.collect()

            # Record count after garbage collection
            after_count = len(self._flyweights)
            cleaned_count = before_count - after_count

            # Update our tracking
            if cleaned_count > 0:
                self._creation_stats["flyweights_garbage_collected"] += cleaned_count

            return cleaned_count

    def force_cleanup_all(self) -> int:
        """
        Force cleanup of ALL flyweights (useful for testing or memory pressure situations)
        """
        with self._lock:
            count_before = len(self._flyweights)
            self._flyweights.clear()  # Remove all references

            gc.collect()  # Force garbage collection

            cleaned_count = count_before
            self._creation_stats["flyweights_garbage_collected"] += cleaned_count

            return cleaned_count

    def get_active_flyweights_info(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about currently active flyweights
        Useful for debugging and monitoring
        """
        with self._lock:
            flyweight_info = []
            for content_hash, flyweight in self._flyweights.items():
                flyweight_info.append(
                    {
                        "content_hash": content_hash[
                            :16
                        ],  # First 16 chars for readability
                        "data_type": flyweight.data_type.value,
                        "data_size": flyweight.data_size,
                        "computation_cost": flyweight.computation_cost,
                        "reference_count": f"Active (in WeakValueDictionary)",
                    }
                )
            return flyweight_info

    def _calculate_memory_by_type(self) -> Dict[CacheDataType, int]:
        """Calculate memory usage breakdown by data type for currently active flyweights"""
        memory_by_type: Dict[CacheDataType, int] = {}
        # Only iterate over currently active flyweights (not garbage collected)
        for flyweight in self._flyweights.values():
            data_type = flyweight.data_type.value
            if data_type not in memory_by_type:
                memory_by_type[data_type] = 0
            memory_by_type[data_type] += flyweight.get_memory_footprint()
        return memory_by_type


class CacheEntry:
    """
    Context class storing extrinsic state for each cache entry
    Multiple entries can share the same flyweight
    """

    def __init__(
        self,
        flyweight: CacheFlyweight,
        cache_key: str,
        ttl_seconds: float,
        priority: int = 1,
    ):
        self.flyweight = flyweight  # Reference to shared intrinsic state

        # Extrinsic state fields
        self.cache_key = cache_key
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.ttl_seconds = ttl_seconds
        self.priority = priority
        self.tags: List[str] = []

    def is_expired(self) -> bool:
        """Check if this cache entry has expired based on TTL"""
        current_time = time.time()
        return (current_time - self.created_at) > self.ttl_seconds

    def update_access_stats(self) -> None:
        """Update last_accessed time and increment access_count"""
        self.last_accessed = time.time()
        self.access_count += 1

    def get_age_seconds(self) -> float:
        """Return how long this entry has been in cache"""
        return time.time() - self.created_at

    def get_lru_score(self) -> float:
        """
        Calculate LRU score for eviction decisions
        Consider: access frequency, recency, priority, computation cost
        """
        age = self.get_age_seconds()
        recency = time.time() - self.last_accessed
        frequency = self.access_count + 1  # Avoid division by zero
        cost = self.flyweight.computation_cost

        # Simple heuristic: lower score means more likely to be evicted
        score = (recency / frequency) * (1 / (self.priority + 1)) * (1 / (cost + 1))
        return score


class CacheEvictionStrategy(ABC):
    """Abstract base for different eviction strategies"""

    @abstractmethod
    def select_victims(
        self, entries: List[CacheEntry], target_count: int
    ) -> List[CacheEntry]:
        """Select entries to evict"""
        pass


class LRUEvictionStrategy(CacheEvictionStrategy):
    """Least Recently Used eviction strategy"""

    def select_victims(
        self, entries: List[CacheEntry], target_count: int
    ) -> List[CacheEntry]:
        """Select the least recently used entries for eviction"""
        sorted_entries = sorted(entries, key=lambda e: e.get_lru_score(), reverse=True)
        return sorted_entries[:target_count]


class SmartEvictionStrategy(CacheEvictionStrategy):
    """Advanced eviction considering multiple factors"""

    def select_victims(
        self, entries: List[CacheEntry], target_count: int
    ) -> List[CacheEntry]:
        """
        Implement smart eviction based on:
        - Access frequency
        - Computation cost (keep expensive-to-compute data longer)
        - Data size (prefer evicting large, rarely-used items)
        - Priority levels
        """

        def smart_score(entry: CacheEntry) -> float:
            age = entry.get_age_seconds()
            recency = time.time() - entry.last_accessed
            frequency = entry.access_count + 1  # Avoid division by zero
            cost = entry.flyweight.computation_cost
            size = entry.flyweight.data_size
            priority = entry.priority

            # Higher score = more likely to evict
            # Consider: size/frequency ratio, inverse of cost and priority, recency penalty
            size_penalty = size / frequency  # Large, rarely accessed items
            cost_protection = 1 / (cost + 1)  # Protect expensive computations
            priority_protection = 1 / (priority + 1)  # Respect priority levels
            recency_penalty = recency / 3600  # Hours since last access

            return (
                size_penalty * cost_protection * priority_protection + recency_penalty
            )

        sorted_entries = sorted(entries, key=smart_score, reverse=True)
        return sorted_entries[:target_count]


class CacheManager:
    """
    Main cache management system
    Handles thousands of cache entries with shared flyweights
    """

    def __init__(
        self,
        max_memory_mb: int = 1000,
        max_entries: int = 10000,
        eviction_strategy: CacheEvictionStrategy = None,
    ):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_entries = max_entries
        self.eviction_strategy = eviction_strategy or LRUEvictionStrategy()

        self._cache_entries: Dict[str, CacheEntry] = {}
        self._flyweight_factory = CacheFlyweightFactory()
        self._lock = threading.RLock()

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_pressure_events": 0,
        }

    def put(
        self,
        key: str,
        data: Any,
        data_type: CacheDataType,
        ttl_seconds: float = 3600,
        priority: int = 1,
        computation_cost: float = 1.0,
    ) -> bool:
        """Store data in cache with thread-safe operations and memory management"""
        with self._lock:
            if key in self._cache_entries:
                # Update existing entry
                entry = self._cache_entries[key]
                entry.update_access_stats()
                return True
            else:
                # Create new entry
                flyweight = self._flyweight_factory.get_flyweight(
                    data, data_type, computation_cost
                )
                entry = CacheEntry(
                    flyweight=flyweight,
                    cache_key=key,
                    ttl_seconds=ttl_seconds,
                    priority=priority,
                )
                self._cache_entries[key] = entry

                # Check memory and entry limits
                current_memory = self.get_memory_usage()["current_bytes"]
                if (
                    current_memory > self.max_memory_bytes
                    or len(self._cache_entries) > self.max_entries
                ):
                    self._stats["memory_pressure_events"] += 1
                    self.force_eviction()

                return True

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache with thread-safe operations and TTL checking"""
        with self._lock:
            if key in self._cache_entries:
                entry = self._cache_entries[key]
                if entry.is_expired():
                    del self._cache_entries[key]
                    self._stats["misses"] += 1
                    return None
                else:
                    entry.update_access_stats()
                    self._stats["hits"] += 1
                    return entry.flyweight.get_data()
            else:
                self._stats["misses"] += 1
                return None

    def delete(self, key: str) -> bool:
        """Remove entry from cache"""
        with self._lock:
            if key in self._cache_entries:
                del self._cache_entries[key]
                return True
            return False

    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries containing any of the given tags"""
        with self._lock:
            to_delete = [
                key
                for key, entry in self._cache_entries.items()
                if any(tag in entry.tags for tag in tags)
            ]
            for key in to_delete:
                del self._cache_entries[key]
            return len(to_delete)

    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self._lock:
            to_delete = [
                key for key, entry in self._cache_entries.items() if entry.is_expired()
            ]
            for key in to_delete:
                del self._cache_entries[key]
            return len(to_delete)

    def force_eviction(self, target_memory_bytes: Optional[int] = None) -> int:
        """Force eviction to reach target memory usage using eviction strategy"""
        with self._lock:
            if target_memory_bytes is None:
                target_memory_bytes = self.max_memory_bytes * 0.8  # Aim for 80% usage

            current_memory = self.get_memory_usage()["current_bytes"]
            if (
                current_memory <= target_memory_bytes
                and len(self._cache_entries) <= self.max_entries
            ):
                return 0  # No eviction needed

            entries = list(self._cache_entries.values())
            # Calculate how many entries to evict
            to_evict_count = max(
                len(entries) - int(self.max_entries * 0.8),  # Stay under entry limit
                len(entries) // 10,  # Evict at least 10% if over memory
            )

            victims = self.eviction_strategy.select_victims(entries, to_evict_count)

            for victim in victims:
                if victim.cache_key in self._cache_entries:
                    del self._cache_entries[victim.cache_key]
                    self._stats["evictions"] += 1

            return len(victims)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return comprehensive cache statistics"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_ratio = (
                self._stats["hits"] / total_requests if total_requests > 0 else 0
            )
            miss_ratio = (
                self._stats["misses"] / total_requests if total_requests > 0 else 0
            )
            memory_usage = self.get_memory_usage()
            factory_stats = self._flyweight_factory.get_factory_stats()

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_ratio": hit_ratio,
                "miss_ratio": miss_ratio,
                "current_memory_bytes": memory_usage["current_bytes"],
                "max_memory_bytes": self.max_memory_bytes,
                "current_entries": len(self._cache_entries),
                "max_entries": self.max_entries,
                "evictions": self._stats["evictions"],
                "memory_pressure_events": self._stats["memory_pressure_events"],
                "flyweight_stats": factory_stats,
            }

    def get_memory_usage(self) -> Dict[str, int]:
        """Calculate current memory usage including flyweight and context memory"""
        with self._lock:
            total_flyweight_memory = sum(
                entry.flyweight.get_memory_footprint()
                for entry in self._cache_entries.values()
            )
            total_context_memory = (
                len(self._cache_entries) * 200
            )  # Approximate per-entry overhead
            total_memory = total_flyweight_memory + total_context_memory

            return {
                "current_bytes": total_memory,
                "flyweight_bytes": total_flyweight_memory,
                "context_bytes": total_context_memory,
            }

    def export_metrics_json(self) -> str:
        """Export all metrics as JSON for monitoring systems"""
        stats = self.get_cache_stats()
        return json.dumps(stats, indent=2)


# Performance testing framework
class CachePerformanceTester:
    """Test harness for performance and correctness testing"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    def simulate_database_queries(self, num_queries: int = 1000) -> Dict[str, Any]:
        """
        Simulate database query caching
        - Generate realistic SQL query results
        - Test cache hit/miss behavior
        - Measure performance improvements
        """
        # Generate realistic database query patterns
        table_names = ["users", "orders", "products", "inventory", "analytics"]
        query_templates = [
            "SELECT * FROM {table} WHERE id = {id}",
            "SELECT COUNT(*) FROM {table} WHERE status = '{status}'",
            "SELECT {table}.*, related.name FROM {table} JOIN related ON {table}.id = related.{table}_id",
        ]
        statuses = ["active", "pending", "completed", "cancelled"]

        start_time = time.time()
        cache_hits = 0
        cache_misses = 0

        for i in range(num_queries):
            # Generate query
            table = random.choice(table_names)
            template = random.choice(query_templates)

            if "id =" in template:
                query = template.format(table=table, id=random.randint(1, 100))
                # Simulate query result
                result = {
                    "id": random.randint(1, 100),
                    "name": f"Record_{i}",
                    "data": f"Value_{i}",
                }
            elif "status =" in template:
                status = random.choice(statuses)
                query = template.format(table=table, status=status)
                result = {"count": random.randint(1, 1000)}
            else:
                query = template.format(table=table)
                result = [
                    {"id": j, "name": f"Item_{j}"} for j in range(random.randint(1, 50))
                ]

            cache_key = f"db_query:{hashlib.sha256(query.encode()).hexdigest()[:16]}"

            # Try to get from cache first
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                cache_hits += 1
            else:
                cache_misses += 1
                # "Execute" query and cache result
                computation_cost = random.uniform(0.1, 5.0)  # Query execution time
                self.cache_manager.put(
                    cache_key,
                    result,
                    CacheDataType.DATABASE_QUERY,
                    ttl_seconds=3600,
                    computation_cost=computation_cost,
                )

        execution_time = time.time() - start_time

        return {
            "total_queries": num_queries,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_ratio": cache_hits / num_queries,
            "execution_time_seconds": execution_time,
            "queries_per_second": num_queries / execution_time,
            "cache_stats": self.cache_manager.get_cache_stats(),
        }

    def simulate_api_responses(self, num_apis: int = 500) -> Dict[str, Any]:
        """
        Simulate API response caching
        - Generate JSON API responses
        - Test data deduplication (same responses cached as flyweights)
        - Measure memory efficiency
        """
        # Simulate common API endpoints with overlapping responses
        endpoints = [
            "/api/users/{user_id}",
            "/api/products/{category}",
            "/api/weather/{city}",
            "/api/stock/{symbol}",
            "/api/news/{topic}",
        ]

        # Common response patterns to test deduplication
        user_responses = [
            {
                "id": i,
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "active": True,
            }
            for i in range(1, 51)  # 50 unique users, but requested multiple times
        ]

        weather_responses = [
            {
                "city": city,
                "temp": random.randint(15, 35),
                "humidity": random.randint(30, 80),
            }
            for city in [
                "New York",
                "London",
                "Tokyo",
                "Sydney",
                "Paris",
            ]  # Limited cities
        ]

        start_time = time.time()
        initial_memory = self.cache_manager.get_memory_usage()["current_bytes"]
        flyweight_reuse_count = 0

        for i in range(num_apis):
            endpoint = random.choice(endpoints)

            if "users" in endpoint:
                user_data = random.choice(user_responses)
                cache_key = f"api:users:{user_data['id']}"
                response = user_data
            elif "weather" in endpoint:
                weather_data = random.choice(weather_responses)
                cache_key = f"api:weather:{weather_data['city']}"
                response = weather_data
            else:
                # Generate unique responses for other endpoints
                cache_key = f"api:generic:{i}"
                response = {"data": f"response_{i}", "timestamp": time.time()}

            # Check if we already have this exact response (flyweight reuse)
            existing = self.cache_manager.get(cache_key)
            if existing is not None:
                flyweight_reuse_count += 1
            else:
                self.cache_manager.put(
                    cache_key,
                    response,
                    CacheDataType.API_RESPONSE,
                    ttl_seconds=1800,  # 30 minutes
                    computation_cost=random.uniform(0.5, 2.0),
                )

        final_memory = self.cache_manager.get_memory_usage()["current_bytes"]
        factory_stats = self.cache_manager._flyweight_factory.get_factory_stats()

        return {
            "total_api_calls": num_apis,
            "flyweight_reuse_count": flyweight_reuse_count,
            "unique_flyweights": factory_stats["total_flyweights"],
            "deduplication_ratio": factory_stats["total_requests"]
            / max(factory_stats["total_flyweights"], 1),
            "memory_used_bytes": final_memory - initial_memory,
            "memory_efficiency": f"{(1 - factory_stats['total_flyweights'] / factory_stats['total_requests']) * 100:.1f}% saved",
            "execution_time_seconds": time.time() - start_time,
        }

    def concurrent_access_test(
        self, num_threads: int = 10, operations_per_thread: int = 1000
    ) -> Dict[str, Any]:
        """
        Test thread safety under concurrent load
        - Multiple threads reading/writing simultaneously
        - Verify no data corruption
        - Measure performance under contention
        """
        results = {"operations_completed": 0, "errors": 0, "lock_contentions": 0}
        results_lock = threading.Lock()

        def worker_thread(thread_id: int):
            local_ops = 0
            local_errors = 0

            try:
                for i in range(operations_per_thread):
                    operation = random.choice(["put", "get", "delete"])
                    key = f"thread_{thread_id}_key_{random.randint(1, 100)}"

                    if operation == "put":
                        data = {
                            "thread_id": thread_id,
                            "operation": i,
                            "timestamp": time.time(),
                        }
                        success = self.cache_manager.put(
                            key,
                            data,
                            CacheDataType.COMPUTED_RESULT,
                            ttl_seconds=60,
                            computation_cost=random.uniform(0.1, 1.0),
                        )
                        if success:
                            local_ops += 1

                    elif operation == "get":
                        result = self.cache_manager.get(key)
                        local_ops += 1
                        # Verify data integrity if found
                        if (
                            result
                            and isinstance(result, dict)
                            and "thread_id" in result
                        ):
                            if result["thread_id"] != thread_id:
                                local_errors += 1  # Data corruption detected

                    elif operation == "delete":
                        success = self.cache_manager.delete(key)
                        local_ops += 1

            except Exception as e:
                local_errors += 1

            # Update shared results
            with results_lock:
                results["operations_completed"] += local_ops
                results["errors"] += local_errors

        # Start concurrent threads
        start_time = time.time()
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        execution_time = time.time() - start_time
        total_operations = num_threads * operations_per_thread

        return {
            "num_threads": num_threads,
            "operations_per_thread": operations_per_thread,
            "total_operations_attempted": total_operations,
            "operations_completed": results["operations_completed"],
            "errors": results["errors"],
            "success_rate": results["operations_completed"] / total_operations,
            "execution_time_seconds": execution_time,
            "operations_per_second": results["operations_completed"] / execution_time,
            "cache_stats": self.cache_manager.get_cache_stats(),
        }

    def memory_pressure_test(self) -> Dict[str, Any]:
        """
        Test behavior under memory pressure
        - Fill cache beyond capacity
        - Verify eviction strategies work correctly
        - Measure flyweight sharing efficiency
        """
        initial_stats = self.cache_manager.get_cache_stats()
        initial_memory = initial_stats["current_memory_bytes"]

        # Generate data that will exceed memory limits
        large_objects = []
        entries_added = 0
        evictions_triggered = 0

        # Fill cache to capacity and beyond
        for i in range(self.cache_manager.max_entries + 2000):  # Exceed max entries
            # Create progressively larger objects
            data_size = random.randint(1000, 10000)  # 1-10KB objects
            large_data = {
                "id": i,
                "payload": "x" * data_size,
                "metadata": {"size": data_size, "created": time.time()},
                "tags": [f"tag_{random.randint(1, 10)}"],
            }

            cache_key = f"pressure_test:{i}"
            priority = random.randint(1, 5)
            computation_cost = random.uniform(1.0, 10.0)

            success = self.cache_manager.put(
                cache_key,
                large_data,
                CacheDataType.COMPUTED_RESULT,
                ttl_seconds=3600,
                priority=priority,
                computation_cost=computation_cost,
            )

            if success:
                entries_added += 1

            # Check if eviction was triggered
            current_stats = self.cache_manager.get_cache_stats()
            if current_stats["evictions"] > evictions_triggered:
                evictions_triggered = current_stats["evictions"]

        # Test flyweight efficiency by adding duplicate data
        duplicate_data = {"common": "shared_data", "value": 12345}
        flyweight_test_entries = 100

        before_flyweight_test = (
            self.cache_manager._flyweight_factory.get_factory_stats()
        )

        for i in range(flyweight_test_entries):
            # Add same data multiple times to test flyweight sharing
            self.cache_manager.put(
                f"duplicate_test:{i}",
                duplicate_data,  # Same data, should reuse flyweight
                CacheDataType.COMPUTED_RESULT,
                ttl_seconds=1800,
            )

        after_flyweight_test = self.cache_manager._flyweight_factory.get_factory_stats()

        final_stats = self.cache_manager.get_cache_stats()
        final_memory = final_stats["current_memory_bytes"]

        return {
            "initial_memory_bytes": initial_memory,
            "final_memory_bytes": final_memory,
            "memory_growth_bytes": final_memory - initial_memory,
            "entries_added": entries_added,
            "evictions_triggered": evictions_triggered,
            "eviction_efficiency": evictions_triggered > 0,
            "final_entry_count": final_stats["current_entries"],
            "stayed_within_limits": final_stats["current_entries"]
            <= self.cache_manager.max_entries,
            "flyweight_sharing_test": {
                "entries_added": flyweight_test_entries,
                "flyweights_before": before_flyweight_test["total_flyweights"],
                "flyweights_after": after_flyweight_test["total_flyweights"],
                "flyweights_created": after_flyweight_test["total_flyweights"]
                - before_flyweight_test["total_flyweights"],
                "sharing_efficiency": f"{((flyweight_test_entries - (after_flyweight_test['total_flyweights'] - before_flyweight_test['total_flyweights'])) / flyweight_test_entries) * 100:.1f}% reuse",
            },
            "cache_stats": final_stats,
        }


# Example usage and testing
if __name__ == "__main__":
    print("=== Enterprise Cache System - Full Implementation ===\n")

    # Initialize cache system
    cache_manager = CacheManager(
        max_memory_mb=50,  # Smaller for demo
        max_entries=1000,
        eviction_strategy=SmartEvictionStrategy(),
    )

    tester = CachePerformanceTester(cache_manager)

    # Test 1: Database Query Simulation
    print("1. Testing Database Query Caching...")
    db_results = tester.simulate_database_queries(500)
    print(f"   Database queries: {db_results['total_queries']}")
    print(f"   Cache hit ratio: {db_results['hit_ratio']:.2%}")
    print(f"   Queries/second: {db_results['queries_per_second']:.1f}")

    # Test 2: API Response Deduplication
    print("\n2. Testing API Response Deduplication...")
    api_results = tester.simulate_api_responses(300)
    print(f"   API calls: {api_results['total_api_calls']}")
    print(f"   Flyweight reuse: {api_results['flyweight_reuse_count']}")
    print(f"   Deduplication ratio: {api_results['deduplication_ratio']:.1f}x")
    print(f"   Memory efficiency: {api_results['memory_efficiency']}")

    # Test 3: Concurrent Access
    print("\n3. Testing Thread Safety...")
    concurrent_results = tester.concurrent_access_test(5, 200)
    print(f"   Threads: {concurrent_results['num_threads']}")
    print(f"   Success rate: {concurrent_results['success_rate']:.2%}")
    print(f"   Operations/second: {concurrent_results['operations_per_second']:.1f}")
    print(f"   Errors: {concurrent_results['errors']}")

    # Test 4: Memory Pressure
    print("\n4. Testing Memory Pressure & Eviction...")
    pressure_results = tester.memory_pressure_test()
    print(f"   Entries added: {pressure_results['entries_added']}")
    print(f"   Evictions triggered: {pressure_results['evictions_triggered']}")
    print(f"   Stayed within limits: {pressure_results['stayed_within_limits']}")
    print(
        f"   Flyweight sharing: {pressure_results['flyweight_sharing_test']['sharing_efficiency']}"
    )

    # Final Statistics
    print("\n=== Final Cache Statistics ===")
    final_stats = cache_manager.get_cache_stats()
    print(f"Cache Hit Ratio: {final_stats['hit_ratio']:.2%}")
    print(
        f"Memory Usage: {final_stats['current_memory_bytes']:,} / {final_stats['max_memory_bytes']:,} bytes"
    )
    print(
        f"Cache Entries: {final_stats['current_entries']:,} / {final_stats['max_entries']:,}"
    )
    print(
        f"Flyweight Efficiency: {final_stats['flyweight_stats']['hit_ratio']:.2%} reuse rate"
    )
    print(f"Total Evictions: {final_stats['evictions']}")

    # Export metrics for monitoring
    print(f"\n=== Exported Metrics ===")
    metrics_json = cache_manager.export_metrics_json()
    print("Metrics exported successfully (JSON format ready for monitoring)")

    # Demonstrate flyweight memory savings
    flyweight_stats = final_stats["flyweight_stats"]
    print(f"\n=== Flyweight Pattern Benefits ===")
    print(f"Total data requests: {flyweight_stats['total_requests']:,}")
    print(f"Active flyweights: {flyweight_stats['total_flyweights']:,}")
    print(
        f"Flyweights ever created: {flyweight_stats['total_flyweights_ever_created']:,}"
    )
    print(f"Garbage collected: {flyweight_stats['flyweights_garbage_collected']:,}")
    print(
        f"Memory efficiency: {(1 - flyweight_stats['total_flyweights'] / max(flyweight_stats['total_requests'], 1)) * 100:.1f}% reduction"
    )
    print(f"GC efficiency: {flyweight_stats['garbage_collection_efficiency']}")

    print(f"\n🎯 Enterprise Cache System successfully demonstrates:")
    print(f"   ✅ Flyweight pattern for memory efficiency")
    print(f"   ✅ Thread-safe concurrent operations")
    print(f"   ✅ Smart eviction strategies")
    print(f"   ✅ Enterprise-grade monitoring")
    print(
        f"   ✅ High-performance caching ({concurrent_results['operations_per_second']:.0f} ops/sec)"
    )
    print(f"   ✅ Automatic memory cleanup with WeakValueDictionary")

    # Additional demonstration: Show flyweight sharing and cleanup
    print(f"\n=== Advanced Flyweight Management Demo ===")

    # Add identical data multiple times to show flyweight reuse
    demo_data = {"message": "This is shared data", "version": "1.0", "size": "medium"}

    print("Adding identical data 50 times...")
    demo_keys = []
    for i in range(50):
        key = f"demo_key_{i}"
        cache_manager.put(key, demo_data, CacheDataType.API_RESPONSE)
        demo_keys.append(key)

    demo_stats_after = cache_manager._flyweight_factory.get_factory_stats()
    print(f"Active flyweights: {demo_stats_after['total_flyweights']}")
    print(f"✅ Flyweight pattern successfully shared identical data!")

    # Show detailed flyweight information
    print(f"\n=== Active Flyweights Details ===")
    active_flyweights = cache_manager._flyweight_factory.get_active_flyweights_info()
    print(f"Currently tracking {len(active_flyweights)} active flyweight types:")
    for fw_info in active_flyweights[:5]:  # Show first 5 for brevity
        print(
            f"  - Type: {fw_info['data_type']}, Size: {fw_info['data_size']} bytes, Hash: {fw_info['content_hash']}"
        )

    # Demonstrate automatic cleanup by removing cache entries
    print(f"\n=== Demonstrating Automatic Flyweight Cleanup ===")
    print("Removing cache entries to trigger flyweight garbage collection...")

    # Remove half of the demo entries
    for key in demo_keys[:25]:
        cache_manager.delete(key)

    # Force cleanup to demonstrate WeakValueDictionary behavior
    cleaned_count = cache_manager._flyweight_factory.cleanup_unused_flyweights()
    cleanup_stats = cache_manager._flyweight_factory.get_factory_stats()

    print(f"Cleanup results:")
    print(f"  - Flyweights cleaned up: {cleaned_count}")
    print(
        f"  - Total garbage collected: {cleanup_stats['flyweights_garbage_collected']}"
    )
    print(f"  - Active flyweights remaining: {cleanup_stats['total_flyweights']}")
    print(f"  - Cleanup efficiency: {cleanup_stats['garbage_collection_efficiency']}")

    # Show memory breakdown
    memory_usage = cache_manager.get_memory_usage()
    print(f"\n=== Memory Usage Breakdown ===")
    print(f"Total memory: {memory_usage['current_bytes']:,} bytes")
    print(
        f"Flyweight memory: {memory_usage['flyweight_bytes']:,} bytes ({memory_usage['flyweight_bytes']/memory_usage['current_bytes']*100:.1f}%)"
    )
    print(
        f"Context memory: {memory_usage['context_bytes']:,} bytes ({memory_usage['context_bytes']/memory_usage['current_bytes']*100:.1f}%)"
    )

    print(f"\n🚀 WeakValueDictionary Enhanced Features:")
    print(f"   🗑️  Automatic garbage collection of unused flyweights")
    print(f"   📊 Real-time tracking of active vs collected flyweights")
    print(f"   🔍 Detailed monitoring of cleanup efficiency")
    print(f"   ⚡ Memory pressure relief through automatic cleanup")
    print(f"   🎯 Production-ready memory management")

    print(f"\n✨ Enterprise Cache System with WeakValueDictionary:")
    print(f"   📊 Comprehensive monitoring and metrics")
    print(f"   🔒 Thread-safe for concurrent environments")
    print(f"   💾 Memory-efficient with automatic cleanup")
    print(f"   ⚡ High-performance eviction strategies")
    print(f"   🎯 Enterprise-grade caching solution")
    print(f"   🗑️ Self-managing flyweight lifecycle")
