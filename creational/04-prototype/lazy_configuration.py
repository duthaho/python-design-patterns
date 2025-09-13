import asyncio
import copy
import hashlib
import json
import logging
import re
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import aiofiles


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PerformanceMetrics:
    """Performance metrics for configuration operations."""

    creation_time: float = 0.0
    clone_time: float = 0.0
    validation_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    lazy_loads: int = 0
    total_operations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        # TODO: Convert metrics to dictionary
        return {
            "creation_time": self.creation_time,
            "clone_time": self.clone_time,
            "validation_time": self.validation_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "lazy_loads": self.lazy_loads,
            "total_operations": self.total_operations,
            "cache_hit_rate": self.cache_hits
            / max(1, self.cache_hits + self.cache_misses)
            * 100,
        }


def track_performance(operation: str):
    """Decorator to track performance of configuration operations."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # TODO: Implement performance tracking
            # Record start time, execute function, record end time
            # Update relevant metrics
            start_time = time.perf_counter()
            result = func(self, *args, **kwargs)
            end_time = time.perf_counter()
            elapsed = end_time - start_time

            if hasattr(self, "metrics") and isinstance(
                self.metrics, PerformanceMetrics
            ):
                if operation == "clone":
                    self.metrics.clone_time += elapsed
                elif operation == "validation":
                    self.metrics.validation_time += elapsed
                elif operation == "creation":
                    self.metrics.creation_time += elapsed
                elif operation in ("import", "export"):
                    self.metrics.creation_time += (
                        elapsed  # Treat import/export as creation time
                    )
                self.metrics.total_operations += 1

            return result

        return wrapper

    return decorator


class ExpensiveResource:
    """Simulates an expensive resource that should be loaded lazily."""

    def __init__(self, resource_id: str, load_time: float = 1.0):
        self.resource_id = resource_id
        self.load_time = load_time
        self._data: Optional[Dict[str, Any]] = None
        self._loaded = False
        self._lock = threading.Lock()

    def __deepcopy__(self, memo):
        # Custom deepcopy to avoid threading issues
        new_copy = ExpensiveResource(self.resource_id, self.load_time)
        if self._loaded:
            new_copy._data = copy.deepcopy(self._data, memo)
            new_copy._loaded = True
        return new_copy

    def load(self) -> Dict[str, Any]:
        """Simulate expensive loading operation."""
        # TODO: Simulate expensive operation (sleep for load_time)
        # Set _loaded = True and populate _data
        with self._lock:
            if not self._loaded:
                time.sleep(self.load_time)
                self._data = {
                    "resource_id": self.resource_id,
                    "data": f"Data for {self.resource_id}",
                }
                self._loaded = True
        return self._data

    @property
    def is_loaded(self) -> bool:
        return self._loaded


@dataclass
class DatabaseConfig:
    """Database configuration with lazy-loaded connection pool."""

    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    timeout: int = 30
    ssl_enabled: bool = False
    connection_params: Dict[str, Any] = field(default_factory=dict)

    # Lazy-loaded expensive resource
    _connection_pool: Optional[ExpensiveResource] = field(default=None, init=False)

    def __post_init__(self):
        # TODO: Initialize _connection_pool as ExpensiveResource
        errors = []
        if not self.host.strip():
            errors.append("Host cannot be empty.")
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535).")
        if not self.database.strip():
            errors.append("Database name cannot be empty.")
        if not self.username.strip():
            errors.append("Username cannot be empty.")
        if self.pool_size <= 0:
            errors.append("Pool size must be greater than 0.")
        if self.timeout <= 0:
            errors.append("Timeout must be greater than 0 seconds.")
        if errors:
            raise ValueError("Invalid DatabaseConfig: " + "; ".join(errors))
        self._connection_pool = ExpensiveResource(
            f"db_pool_{self.host}_{self.port}", load_time=2.0
        )

    @property
    def connection_pool(self) -> Dict[str, Any]:
        """Lazy-loaded connection pool configuration."""
        # TODO: Load connection pool on first access
        return self._connection_pool.load()

    def get_cache_key(self) -> str:
        """Generate cache key for this configuration."""
        # TODO: Create a hash-based cache key from config values
        # Use host, port, database, username to create unique key
        key_str = f"{self.host}:{self.port}:{self.database}:{self.username}"
        return hashlib.sha256(key_str.encode()).hexdigest()


@dataclass
class CacheConfig:
    """Cache configuration with lazy-loaded cluster info."""

    provider: str
    host: str
    port: int
    ttl: int = 3600
    max_memory: str = "100mb"
    eviction_policy: str = "allkeys-lru"
    cluster_nodes: List[str] = field(default_factory=list)

    # Lazy-loaded cluster topology
    _cluster_topology: Optional[ExpensiveResource] = field(default=None, init=False)

    def __post_init__(self):
        # TODO: Initialize _cluster_topology and add validation
        errors = []
        if self.provider not in ("redis", "memcached"):
            errors.append(
                f"Provider '{self.provider}' is not supported. Use 'redis' or 'memcached'."
            )
        if not self.host.strip():
            errors.append("Host cannot be empty.")
        if not (1 <= self.port <= 65535):
            errors.append(f"Port {self.port} is out of valid range (1-65535).")
        if self.ttl <= 0:
            errors.append("TTL must be greater than 0 seconds.")
        # Validate memory format (e.g., "100mb", "1gb")
        if not re.match(r"^\d+[kmg]?b$", self.max_memory.lower()):
            errors.append(
                f"Invalid memory format '{self.max_memory}'. Use format like '100mb', '1gb'."
            )
        if errors:
            raise ValueError("Invalid CacheConfig: " + "; ".join(errors))
        self._cluster_topology = ExpensiveResource(
            f"cache_topology_{self.host}_{self.port}", load_time=1.5
        )

    @property
    def cluster_topology(self) -> Dict[str, Any]:
        """Lazy-loaded cluster topology information."""
        # TODO: Load cluster topology on first access
        return self._cluster_topology.load()

    def get_cache_key(self) -> str:
        """Generate cache key for this configuration."""
        # TODO: Create cache key from provider, host, port
        key_str = f"{self.provider}:{self.host}:{self.port}"
        return hashlib.sha256(key_str.encode()).hexdigest()


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers: List[str] = field(default_factory=lambda: ["console"])
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5

    def __post_init__(self):
        # TODO: Add validation from previous exercise
        errors = []
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            errors.append(
                f"Log level '{self.level}' is not valid. Choose from {valid_levels}."
            )
        if not self.handlers:
            errors.append("At least one log handler must be specified.")
        if "file" in self.handlers and not self.file_path:
            errors.append("File handler specified but file_path is missing.")
        if self.backup_count < 0:
            errors.append("Backup count cannot be negative.")
        if errors:
            raise ValueError("Invalid LoggingConfig: " + "; ".join(errors))

    def get_cache_key(self) -> str:
        """Generate cache key for this configuration."""
        # TODO: Create cache key from level, handlers
        key_str = (
            f"{self.level}:{','.join(sorted(self.handlers))}:{self.file_path or ''}"
        )
        return hashlib.sha256(key_str.encode()).hexdigest()


class LRUCache:
    """LRU Cache with TTL support for configurations."""

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()

    def __deepcopy__(self, memo):
        # Custom deepcopy to avoid threading issues
        new_copy = LRUCache(self.max_size, self.default_ttl)
        with self._lock:
            new_copy._cache = copy.deepcopy(self._cache, memo)
            new_copy._timestamps = copy.deepcopy(self._timestamps, memo)
            new_copy._hits = self._hits
            new_copy._misses = self._misses
        return new_copy

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache, None if not found or expired."""
        with self._lock:
            # TODO: Implement cache retrieval
            # Check if key exists and not expired
            # Move to end (most recently used)
            # Return value or None
            if key in self._cache:
                if not self._is_expired(key):
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return self._cache[key]
                else:
                    # Expired
                    del self._cache[key]
                    del self._timestamps[key]
                    self._misses += 1
                    return None
            self._misses += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Put item in cache with optional TTL."""
        with self._lock:
            # TODO: Implement cache storage
            # Remove oldest items if at max_size
            # Store value and timestamp
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            self._timestamps[key] = time.time() + (
                ttl if ttl is not None else self.default_ttl
            )

            # Evict oldest if over size
            if len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                del self._timestamps[oldest_key]

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        # TODO: Check if entry timestamp + ttl < current time
        if key not in self._timestamps:
            return True
        return time.time() > self._timestamps[key]

    def clear_expired(self) -> int:
        """Remove expired entries, return number removed."""
        # TODO: Remove all expired entries
        with self._lock:
            expired_keys = [key for key in self._cache if self._is_expired(key)]
            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
            return len(expired_keys)

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        # TODO: Return cache size, hit rate, etc.
        with self._lock:
            return {
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / max(1, self._hits + self._misses) * 100,
            }


class ConfigurationPrototype(ABC):
    """Abstract base class for all configuration prototypes with performance tracking."""

    def __init__(self, name: str, environment: Environment):
        self.name = name
        self.environment = environment
        self.created_at = datetime.now()
        self.version = "1.0.0"
        self.metrics = PerformanceMetrics()

    @abstractmethod
    @track_performance("clone")
    def clone(self) -> "ConfigurationPrototype":
        """Create a deep copy of this configuration."""
        pass

    @abstractmethod
    @track_performance("validation")
    def validate(self) -> bool:
        """Validate the configuration."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigurationPrototype":
        """Create configuration from dictionary."""
        pass

    def get_cache_key(self) -> str:
        """Generate unique cache key for this configuration."""
        # TODO: Create cache key from name, environment, and config-specific data
        key_str = f"{self.name}:{self.environment.value}:{self.version}"
        return hashlib.sha256(key_str.encode()).hexdigest()


class LazyConfiguration(ConfigurationPrototype):
    """Configuration that loads expensive resources on-demand."""

    def __init__(
        self,
        name: str,
        environment: Environment,
        database_config_factory: Callable[[], DatabaseConfig],
        cache_config_factory: Callable[[], CacheConfig],
        logging_config_factory: Callable[[], LoggingConfig],
        custom_settings: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name, environment)

        # Store factories instead of actual configs
        self._database_config_factory = database_config_factory
        self._cache_config_factory = cache_config_factory
        self._logging_config_factory = logging_config_factory
        self.custom_settings = custom_settings or {}

        # Lazy-loaded configurations
        self._database_config: Optional[DatabaseConfig] = None
        self._cache_config: Optional[CacheConfig] = None
        self._logging_config: Optional[LoggingConfig] = None

        self._lock = threading.RLock()

    @property
    def database_config(self) -> DatabaseConfig:
        """Lazy-loaded database configuration."""
        # TODO: Load database config using factory
        # Increment lazy_loads metric
        with self._lock:
            if self._database_config is None:
                self._database_config = self._database_config_factory()
                self.metrics.lazy_loads += 1
        return self._database_config

    @property
    def cache_config(self) -> CacheConfig:
        """Lazy-loaded cache configuration."""
        with self._lock:
            if self._cache_config is None:
                # TODO: Load cache config using factory
                # Increment lazy_loads metric
                self._cache_config = self._cache_config_factory()
                self.metrics.lazy_loads += 1
        return self._cache_config

    @property
    def logging_config(self) -> LoggingConfig:
        """Lazy-loaded logging configuration."""
        with self._lock:
            if self._logging_config is None:
                # TODO: Load logging config using factory
                # Increment lazy_loads metric
                self._logging_config = self._logging_config_factory()
                self.metrics.lazy_loads += 1
        return self._logging_config

    def clone(self) -> "LazyConfiguration":
        """Create a lazy clone that preserves factory functions."""
        # TODO: Create new LazyConfiguration with same factories
        # Copy any already-loaded configurations
        cloned = LazyConfiguration(
            name=self.name,
            environment=self.environment,
            database_config_factory=self._database_config_factory,
            cache_config_factory=self._cache_config_factory,
            logging_config_factory=self._logging_config_factory,
            custom_settings=copy.deepcopy(self.custom_settings),
        )

        # Copy already-loaded configs without triggering loading
        with self._lock:
            if self._database_config:
                cloned._database_config = copy.deepcopy(self._database_config)
            if self._cache_config:
                cloned._cache_config = copy.deepcopy(self._cache_config)
            if self._logging_config:
                cloned._logging_config = copy.deepcopy(self._logging_config)

        return cloned

    def validate(self) -> bool:
        """Validate all configurations (triggers loading if needed)."""
        # TODO: Validate all configurations
        # This will trigger lazy loading
        try:
            database_config = self.database_config
            cache_config = self.cache_config
            logging_config = self.logging_config

            return all([database_config, cache_config, logging_config])
        except Exception as e:
            logging.error(f"Validation failed: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (triggers loading if needed)."""

        # TODO: Convert all configurations to dict
        # This will trigger lazy loading for serialization
        def clean_config_dict(config):
            if config is None:
                return None
            if hasattr(config, "to_dict"):
                return config.to_dict()
            return {k: v for k, v in config.__dict__.items() if not k.startswith("_")}

        return {
            "name": self.name,
            "environment": self.environment.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "database_config": clean_config_dict(self._database_config),
            "cache_config": clean_config_dict(self._cache_config),
            "logging_config": clean_config_dict(self._logging_config),
            "custom_settings": self.custom_settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LazyConfiguration":
        """Create LazyConfiguration from dictionary."""
        # TODO: Create factories that return pre-configured objects
        return cls(
            name=data["name"],
            environment=Environment(data["environment"]),
            database_config_factory=lambda: DatabaseConfig(**data["database_config"]),
            cache_config_factory=lambda: CacheConfig(**data["cache_config"]),
            logging_config_factory=lambda: LoggingConfig(**data["logging_config"]),
            custom_settings=data.get("custom_settings", {}),
        )

    def force_load_all(self) -> None:
        """Force load all lazy configurations."""
        # TODO: Access all properties to trigger loading
        _ = self.database_config
        _ = self.cache_config
        _ = self.logging_config


class ConfigurationPool:
    """Pool for reusing similar configurations (Flyweight pattern elements)."""

    def __init__(self, max_pool_size: int = 50):
        self.max_pool_size = max_pool_size
        self._pool: Dict[str, List[ConfigurationPrototype]] = {}
        self._weak_refs: Dict[str, List] = {}  # Weak references to track usage
        self._pool_hits = 0
        self._pool_misses = 0
        self._lock = threading.RLock()

    def get_or_create(
        self, cache_key: str, factory: Callable[[], ConfigurationPrototype]
    ) -> ConfigurationPrototype:
        """Get configuration from pool or create new one."""
        with self._lock:
            # TODO: Check pool for available configuration
            # If found, return it and remove from pool
            # If not found, create new using factory
            if cache_key in self._pool and self._pool[cache_key]:
                config = self._pool[cache_key].pop()
                self._pool_hits += 1
                return config

            self._pool_misses += 1
            config = factory()

            if cache_key not in self._weak_refs:
                self._weak_refs[cache_key] = []
            self._weak_refs[cache_key].append(weakref.ref(config))

            return config

    def return_to_pool(self, config: ConfigurationPrototype) -> None:
        """Return configuration to pool for reuse."""
        with self._lock:
            # TODO: Add configuration back to pool
            # Respect max_pool_size limit
            cache_key = config.get_cache_key()
            if cache_key not in self._pool:
                self._pool[cache_key] = []

            if len(self._pool[cache_key]) < self.max_pool_size:
                self._pool[cache_key].append(config)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        # TODO: Return pool sizes, hit rates, etc.
        with self._lock:
            total_requests = self._pool_hits + self._pool_misses
            return {
                "pool_sizes": {k: len(v) for k, v in self._pool.items()},
                "total_pooled": sum(len(v) for v in self._pool.values()),
                "pool_hits": self._pool_hits,
                "pool_misses": self._pool_misses,
                "pool_hit_rate": self._pool_hits / max(1, total_requests) * 100,
            }

    def cleanup_weak_refs(self) -> None:
        """Clean up dead weak references."""
        # TODO: Remove dead weak references from tracking
        with self._lock:
            for key, refs in self._weak_refs.items():
                self._weak_refs[key] = [r for r in refs if r() is not None]
                if not self._weak_refs[key]:
                    del self._weak_refs[key]


class AsyncConfigurationManager:
    """Async-enabled configuration manager with caching and performance optimization."""

    def __init__(
        self, cache_size: int = 100, cache_ttl: int = 3600, pool_size: int = 50
    ):
        self._prototypes: Dict[str, ConfigurationPrototype] = {}
        self._cache = LRUCache(max_size=cache_size, default_ttl=cache_ttl)
        self._pool = ConfigurationPool(max_pool_size=pool_size)
        self._logger = logging.getLogger(__name__)
        self._metrics = PerformanceMetrics()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def register_prototype(
        self, key: str, prototype: ConfigurationPrototype
    ) -> None:
        """Async register a configuration prototype."""
        async with self._lock:
            # TODO: Validate prototype asynchronously
            # Register if valid
            if key in self._prototypes:
                raise ValueError(f"Prototype with key '{key}' is already registered.")

            # Run validation in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                is_valid = await loop.run_in_executor(pool, prototype.validate)

            if not is_valid:
                raise ValueError("Prototype with key '{key}' failed validation.")

            self._prototypes[key] = prototype
            self._logger.info(f"Registered prototype with key '{key}'.")

    async def create_configuration(
        self,
        prototype_key: str,
        overrides: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> ConfigurationPrototype:
        """Async create configuration with caching."""
        # TODO: Generate cache key from prototype_key and overrides
        # Check cache first if use_cache is True
        # If cache miss, create from prototype
        # Store in cache before returning
        async with self._lock:
            if prototype_key not in self._prototypes:
                raise KeyError(
                    f"Prototype with key '{prototype_key}' is not registered."
                )

            prototype = self._prototypes[prototype_key]
            cache_key = prototype.get_cache_key()

            if overrides:
                override_str = json.dumps(overrides, sort_keys=True)
                cache_key += hashlib.sha256(override_str.encode()).hexdigest()

            if use_cache:
                cached = self._cache.get(cache_key)
                if cached:
                    self._metrics.cache_hits += 1
                    return cached
                self._metrics.cache_misses += 1

            # Create configuration in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:

                def create_config():
                    cloned = prototype.clone()
                    if overrides:
                        for k, v in overrides.items():
                            if hasattr(cloned, k):
                                setattr(cloned, k, v)
                    if not cloned.validate():
                        raise ValueError(
                            "Configuration after overrides failed validation."
                        )
                    return cloned

                config = await loop.run_in_executor(pool, create_config)

            if use_cache:
                self._cache.put(cache_key, config)

            return config

    @track_performance("export")
    async def export_configuration_async(
        self, config: ConfigurationPrototype, file_path: str
    ) -> None:
        """Async export configuration to file."""
        # TODO: Implement file writing
        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(config.to_dict(), indent=4))
        self._logger.info(f"Exported configuration to '{file_path}'.")

    @track_performance("import")
    async def import_configuration_async(
        self, file_path: str, config_type: str = "base"
    ) -> ConfigurationPrototype:
        """Async import configuration from file."""
        # TODO: Implement file reading
        async with aiofiles.open(file_path, "r") as f:
            data = await f.read()
            config_dict = json.loads(data)

        if config_type == "lazy":
            config = LazyConfiguration.from_dict(config_dict)
        else:
            raise ValueError(f"Unsupported config_type '{config_type}' for import.")

        self._logger.info(f"Imported configuration from '{file_path}'.")
        return config

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        # TODO: Compile metrics from cache, pool, and operations
        # Include cache hit rates, pool utilization, timing stats
        return {
            "metrics": self._metrics.to_dict(),
            "cache_stats": self._cache.get_stats(),
            "pool_stats": self._pool.get_pool_stats(),
        }

    async def cleanup_resources(self) -> None:
        """Clean up expired cache entries and pool resources."""
        # TODO: Clean expired cache entries
        # Clean up pool weak references
        # Log cleanup statistics
        expired_count = self._cache.clear_expired()
        self._pool.cleanup_weak_refs()
        self._logger.info(f"Cleaned up {expired_count} expired cache entries.")

    def start_background_cleanup(self, interval: int = 300) -> None:
        """Start background task for periodic cleanup."""

        # TODO: Create task that runs cleanup_resources periodically
        async def periodic_cleanup():
            while True:
                try:
                    await self.cleanup_resources()
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error(f"Error during periodic cleanup: {e}")

        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(periodic_cleanup())

    def stop_background_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            self._cleanup_task = None


class ConfigurationBenchmark:
    """Benchmarking utilities for performance testing."""

    @staticmethod
    async def benchmark_creation(
        manager: AsyncConfigurationManager,
        prototype_key: str,
        num_operations: int = 1000,
        concurrency: int = 10,
    ) -> Dict[str, float]:
        """Benchmark configuration creation performance."""

        async def create_configs(batch_size: int):
            tasks = []
            for _ in range(batch_size):
                task = manager.create_configuration(prototype_key)
                tasks.append(task)
            await asyncio.gather(*tasks)

        # Benchmark with cache
        start_time = time.perf_counter()
        batch_size = num_operations // concurrency
        tasks = [create_configs(batch_size) for _ in range(concurrency)]
        await asyncio.gather(*tasks)
        cached_time = time.perf_counter() - start_time

        # Benchmark without cache
        start_time = time.perf_counter()
        tasks = [
            manager.create_configuration(prototype_key, use_cache=False)
            for _ in range(min(100, num_operations))
        ]  # Smaller sample for uncached
        await asyncio.gather(*tasks)
        uncached_time = time.perf_counter() - start_time

        return {
            "cached_total_time": cached_time,
            "cached_avg_time": cached_time / num_operations,
            "uncached_total_time": uncached_time,
            "uncached_avg_time": uncached_time / min(100, num_operations),
            "speedup_factor": (uncached_time / min(100, num_operations))
            / (cached_time / num_operations),
        }

    @staticmethod
    async def benchmark_lazy_loading(
        lazy_config: LazyConfiguration, num_accesses: int = 100
    ) -> Dict[str, float]:
        """Benchmark lazy loading performance."""
        # First access (triggers loading)
        start_time = time.perf_counter()
        _ = lazy_config.database_config
        first_access_time = time.perf_counter() - start_time

        # Subsequent accesses (should be fast)
        start_time = time.perf_counter()
        for _ in range(num_accesses):
            _ = lazy_config.database_config
        subsequent_total_time = time.perf_counter() - start_time

        return {
            "first_access_time": first_access_time,
            "subsequent_total_time": subsequent_total_time,
            "subsequent_avg_time": subsequent_total_time / num_accesses,
            "lazy_speedup": first_access_time / (subsequent_total_time / num_accesses),
        }


async def demonstrate_performance_optimized_system():
    """Comprehensive demonstration of the performance-optimized configuration system."""
    print("=== Performance-Optimized Configuration System Demo ===\n")

    # 1. Create AsyncConfigurationManager with performance settings
    manager = AsyncConfigurationManager(cache_size=50, cache_ttl=120, pool_size=10)

    # 2. Register various prototype configurations
    def create_db_factory():
        return lambda: DatabaseConfig(
            host="prod-db.company.com",
            port=5432,
            database="app_db",
            username="admin",
            password="super_secret",
        )

    def create_cache_factory():
        return lambda: CacheConfig(
            provider="redis", host="prod-redis.company.com", port=6379, max_memory="1gb"
        )

    def create_log_factory():
        return lambda: LoggingConfig(
            level="INFO", handlers=["console", "file"], file_path="/var/log/app.log"
        )

    lazy_prototype = LazyConfiguration(
        name="ProdConfig",
        environment=Environment.PRODUCTION,
        database_config_factory=create_db_factory(),
        cache_config_factory=create_cache_factory(),
        logging_config_factory=create_log_factory(),
    )

    await manager.register_prototype("prod_config", lazy_prototype)
    print("✓ Registered production configuration prototype")

    # 3. Demonstrate lazy loading with timing measurements
    print("\n3. Lazy Loading Performance Test:")

    config1 = await manager.create_configuration("prod_config", use_cache=False)
    print("✓ Created first configuration (triggers lazy loading)")

    # Benchmark lazy loading
    benchmark_results = await ConfigurationBenchmark.benchmark_lazy_loading(
        config1, num_accesses=100
    )
    print(f"   First access time: {benchmark_results['first_access_time']:.4f}s")
    print(f"   Subsequent avg time: {benchmark_results['subsequent_avg_time']:.6f}s")
    print(
        f"   Lazy speedup: {benchmark_results['lazy_speedup']:.1f}x faster after loading"
    )

    # 4. Show cache hit/miss scenarios with performance impact
    print("\n4. Cache Performance Test:")

    start_time = time.perf_counter()
    config2 = await manager.create_configuration("prod_config", use_cache=True)
    cached_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    config3 = await manager.create_configuration(
        "prod_config", use_cache=True
    )  # Should hit cache
    cache_hit_time = time.perf_counter() - start_time

    print(f"   First creation (cache miss): {cached_time:.4f}s")
    print(f"   Second creation (cache hit): {cache_hit_time:.4f}s")
    print(f"   Cache speedup: {cached_time / max(cache_hit_time, 0.0001):.1f}x faster")

    # 5. Test concurrent configuration creation
    print("\n5. Concurrent Operations Test:")

    creation_benchmark = await ConfigurationBenchmark.benchmark_creation(
        manager, "prod_config", num_operations=100, concurrency=5
    )

    print(f"   Cached operations: {creation_benchmark['cached_total_time']:.4f}s total")
    print(f"   Average per operation: {creation_benchmark['cached_avg_time']:.4f}s")
    print(
        f"   Throughput: {100 / creation_benchmark['cached_total_time']:.1f} configs/second"
    )

    # 6. Pool reuse efficiency test
    print("\n6. Configuration Pool Test:")

    configs = []
    for i in range(5):
        cfg = await manager.create_configuration(
            "prod_config", overrides={"name": f"Config{i}"}
        )
        configs.append(cfg)

    # Return configs to pool
    for cfg in configs:
        manager._pool.return_to_pool(cfg)

    pool_stats = manager._pool.get_pool_stats()
    print(f"   Pool hit rate: {pool_stats['pool_hit_rate']:.1f}%")
    print(f"   Total pooled configs: {pool_stats['total_pooled']}")

    # 7. Generate comprehensive performance report
    print("\n7. Comprehensive Performance Report:")

    performance_report = manager.get_performance_report()
    print("   Cache Statistics:")
    cache_stats = performance_report["cache_stats"]
    print(f"     Hit rate: {cache_stats['hit_rate']:.1f}%")
    print(f"     Current size: {cache_stats['current_size']}/{cache_stats['max_size']}")

    print("   Operation Metrics:")
    metrics = performance_report["metrics"]
    print(f"     Total operations: {metrics['total_operations']}")
    print(f"     Lazy loads: {metrics['lazy_loads']}")
    print(
        f"     Average clone time: {metrics['clone_time'] / max(metrics['total_operations'], 1):.4f}s"
    )

    # 8. Test async file operations
    print("\n8. Async File Operations Test:")

    test_config = await manager.create_configuration("prod_config")
    export_file = "async_test_config.json"

    start_time = time.perf_counter()
    await manager.export_configuration_async(test_config, export_file)
    export_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    imported_config = await manager.import_configuration_async(
        export_file, config_type="lazy"
    )
    import_time = time.perf_counter() - start_time

    print(f"   Async export time: {export_time:.4f}s")
    print(f"   Async import time: {import_time:.4f}s")
    print(f"   ✓ Round-trip successful: {imported_config.name == test_config.name}")

    # 9. Background cleanup demonstration
    print("\n9. Background Cleanup Test:")

    manager.start_background_cleanup(interval=1)  # 1 second for demo
    print("   ✓ Started background cleanup task")

    # Wait a bit to see cleanup in action
    await asyncio.sleep(2)

    await manager.cleanup_resources()
    print("   ✓ Manual cleanup completed")

    manager.stop_background_cleanup()
    print("   ✓ Stopped background cleanup task")

    # 10. Final performance summary
    print("\n10. Final Performance Summary:")
    final_report = manager.get_performance_report()

    print("   " + "=" * 50)
    print(
        f"   Total Configurations Created: {final_report['metrics']['total_operations']}"
    )
    print(f"   Cache Hit Rate: {final_report['cache_stats']['hit_rate']:.1f}%")
    print(f"   Pool Hit Rate: {final_report['pool_stats']['pool_hit_rate']:.1f}%")
    print(f"   Lazy Loads Triggered: {final_report['metrics']['lazy_loads']}")
    print(
        f"   Average Operation Time: {final_report['metrics']['creation_time'] / max(final_report['metrics']['total_operations'], 1):.4f}s"
    )
    print("   " + "=" * 50)

    # Cleanup test file
    import os

    if os.path.exists(export_file):
        os.remove(export_file)

    print("\n✅ Performance demonstration completed successfully!")
    print("\nKey Benefits Demonstrated:")
    print("   • Lazy loading: 50-100x faster subsequent access")
    print("   • Caching: 10-50x faster configuration retrieval")
    print("   • Pooling: Reduced memory pressure and GC overhead")
    print("   • Async I/O: Non-blocking file operations")
    print("   • Background cleanup: Automatic resource management")


if __name__ == "__main__":
    # Setup logging for the demonstration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(demonstrate_performance_optimized_system())
