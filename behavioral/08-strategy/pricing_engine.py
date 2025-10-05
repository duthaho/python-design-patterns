"""
Enterprise Pricing Engine - Strategy Pattern Advanced Implementation
This module demonstrates advanced strategy pattern concepts including:
- Rule-based strategy selection
- Strategy chaining (middleware pattern)
- Performance monitoring
- Caching
- Async operations
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ============================================================================
# Custom Exceptions
# ============================================================================


class PricingEngineError(Exception):
    """Base exception for pricing engine errors."""

    pass


# ============================================================================
# Domain Models
# ============================================================================


class CustomerTier(Enum):
    """Customer subscription tiers."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class Customer:
    """Customer information."""

    id: str
    name: str
    tier: CustomerTier
    country: str
    total_lifetime_value: float = 0.0


@dataclass
class OrderItem:
    """Individual item in an order."""

    product_id: str
    name: str
    quantity: int
    unit_price: float
    weight: float  # in kg

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class PricingContext:
    """
    Context object that flows through the pricing pipeline.
    Contains all information needed for pricing decisions.
    """

    customer: Customer
    items: List[OrderItem]
    order_date: datetime = field(default_factory=datetime.now)

    # Calculated fields (populated by strategies)
    base_price: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    shipping_cost: float = 0.0
    final_price: float = 0.0

    # Metadata
    applied_strategies: List[str] = field(default_factory=list)
    execution_times: Dict[str, float] = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        """Total number of items in order."""
        return sum(item.quantity for item in self.items)

    @property
    def total_weight(self) -> float:
        """Total weight of all items."""
        return sum(item.weight * item.quantity for item in self.items)

    @property
    def subtotal(self) -> float:
        """Sum of all item subtotals."""
        return sum(item.subtotal for item in self.items)


# ============================================================================
# Strategy Interface
# ============================================================================


class PricingStrategy(ABC):
    """
    Abstract base class for pricing strategies.
    Each strategy modifies the PricingContext.
    """

    @abstractmethod
    def calculate(self, context: PricingContext) -> PricingContext:
        """
        Apply this pricing strategy to the context.

        Args:
            context: Current pricing context

        Returns:
            Modified pricing context
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable strategy name."""
        pass


# ============================================================================
# Concrete Strategies
# ============================================================================


class BasePriceStrategy(PricingStrategy):
    """
    Calculate base price from order items.
    Sets context.base_price to sum of all item subtotals.
    """

    def calculate(self, context: PricingContext) -> PricingContext:
        context.base_price = context.subtotal
        return context

    def get_name(self) -> str:
        return "Base Price Calculation"


class TierDiscountStrategy(PricingStrategy):
    """
    Apply discount based on customer tier.
    - Bronze: 0%
    - Silver: 5% if order > $100
    - Gold: 10% if order > $50
    - Platinum: 15% (always)
    """

    def calculate(self, context: PricingContext) -> PricingContext:
        discount_rate = 0.0
        tier = context.customer.tier
        base = context.base_price

        if tier == CustomerTier.BRONZE:
            discount_rate = 0.0
        elif tier == CustomerTier.SILVER:
            discount_rate = 0.05 if base > 100 else 0.0
        elif tier == CustomerTier.GOLD:
            discount_rate = 0.10 if base > 50 else 0.0
        elif tier == CustomerTier.PLATINUM:
            discount_rate = 0.15

        context.discount_amount = base * discount_rate
        return context

    def get_name(self) -> str:
        return "Tier-based Discount"


class TaxStrategy(PricingStrategy):
    """
    Calculate tax based on customer country.
    Simple implementation: US=8%, UK=20%, Other=10%
    """

    TAX_RATES = {
        "US": 0.08,
        "UK": 0.20,
        "DE": 0.19,
        "FR": 0.20,
    }
    DEFAULT_TAX_RATE = 0.10

    def calculate(self, context: PricingContext) -> PricingContext:
        country = context.customer.country.upper()
        tax_rate = self.TAX_RATES.get(country, self.DEFAULT_TAX_RATE)
        taxable_amount = context.base_price - context.discount_amount
        context.tax_amount = taxable_amount * tax_rate
        return context

    def get_name(self) -> str:
        return "Tax Calculation"


class ShippingStrategy(PricingStrategy):
    """
    Calculate shipping cost.
    - Free for Gold/Platinum customers
    - $5 base + $0.5 per kg for others
    """

    def calculate(self, context: PricingContext) -> PricingContext:
        if context.customer.tier in {CustomerTier.GOLD, CustomerTier.PLATINUM}:
            context.shipping_cost = 0.0
        else:
            context.shipping_cost = 5.0 + (0.5 * context.total_weight)
        return context

    def get_name(self) -> str:
        return "Shipping Cost"


class FinalPriceStrategy(PricingStrategy):
    """
    Calculate final price by summing all components.
    final_price = base_price - discount + tax + shipping
    """

    def calculate(self, context: PricingContext) -> PricingContext:
        context.final_price = (
            context.base_price
            - context.discount_amount
            + context.tax_amount
            + context.shipping_cost
        )
        return context

    def get_name(self) -> str:
        return "Final Price"


# ============================================================================
# Strategy Chain (Pipeline Pattern)
# ============================================================================


class PricingPipeline:
    """
    Chains multiple pricing strategies together.
    Executes them in sequence, passing context between them.
    """

    def __init__(self, strategies: List[PricingStrategy]):
        self.strategies = strategies

    def execute(self, context: PricingContext) -> PricingContext:
        """
        Execute all strategies in sequence.
        Track execution time for each strategy.
        """
        for strategy in self.strategies:
            start_time = time.perf_counter()
            try:
                context = strategy.calculate(context)
                elapsed = time.perf_counter() - start_time
                context.applied_strategies.append(strategy.get_name())
                context.execution_times[strategy.get_name()] = elapsed
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                context.execution_times[strategy.get_name()] = elapsed
                raise PricingEngineError(
                    f"Strategy '{strategy.get_name()}' failed after {elapsed:.6f}s: {e}"
                ) from e

        return context


# ============================================================================
# Strategy Selector (Rule Engine)
# ============================================================================


class StrategySelector:
    """
    Selects appropriate pricing pipeline based on business rules.
    """

    @staticmethod
    def select_pipeline(customer: Customer) -> PricingPipeline:
        """
        Select pricing pipeline based on customer tier.

        All tiers get: Base → Discount → Tax → Shipping → Final
        (Discount strategy handles tier-specific logic)
        """
        strategies = [
            BasePriceStrategy(),
            TierDiscountStrategy(),
            TaxStrategy(),
            ShippingStrategy(),
            FinalPriceStrategy(),
        ]
        return PricingPipeline(strategies)


# ============================================================================
# Caching Decorator
# ============================================================================


class CachedStrategy(PricingStrategy):
    """
    Decorator that caches strategy results.
    Cache key is based on relevant context attributes.
    """

    def __init__(
        self,
        strategy: PricingStrategy,
        ttl_seconds: int = 300,
        cache_key_fn: Optional[Callable[[PricingContext], str]] = None,
    ):
        """
        Args:
            strategy: Strategy to cache
            ttl_seconds: Time-to-live for cache entries
            cache_key_fn: Function to generate cache key from context
        """
        self.strategy = strategy
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[PricingContext, datetime]] = {}
        self.cache_key_fn = cache_key_fn or self._default_cache_key

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0

    def _default_cache_key(self, context: PricingContext) -> str:
        """Generate cache key from context."""
        return (
            f"{context.customer.tier.value}-"
            f"{context.customer.country}-"
            f"{context.subtotal:.2f}-"
            f"{context.total_weight:.2f}"
        )

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid."""
        return (datetime.now() - timestamp) < timedelta(seconds=self.ttl_seconds)

    def calculate(self, context: PricingContext) -> PricingContext:
        """
        Check cache first, calculate if miss.
        Uses deep copy to prevent context mutation issues.
        """
        key = self.cache_key_fn(context)

        if key in self.cache:
            cached_context, timestamp = self.cache[key]
            if self._is_cache_valid(timestamp):
                self.cache_hits += 1
                # Return deep copy to prevent mutation
                return deepcopy(cached_context)
            else:
                # Remove expired entry
                del self.cache[key]

        self.cache_misses += 1
        result = self.strategy.calculate(context)
        # Cache deep copy to prevent mutation
        self.cache[key] = (deepcopy(result), datetime.now())
        return result

    def get_name(self) -> str:
        return f"Cached({self.strategy.get_name()})"

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache performance metrics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0.0

        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "size": len(self.cache),
            "hit_rate": hit_rate,
        }


# ============================================================================
# Monitoring Decorator
# ============================================================================


class MonitoredStrategy(PricingStrategy):
    """
    Decorator that monitors strategy execution.
    Logs execution time, errors, and results.
    """

    # Class-level metrics storage
    metrics: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"execution_count": 0, "total_time": 0.0, "avg_time": 0.0, "errors": 0}
    )

    def __init__(self, strategy: PricingStrategy, enable_logging: bool = False):
        self.strategy = strategy
        self.enable_logging = enable_logging

    def calculate(self, context: PricingContext) -> PricingContext:
        """
        Execute strategy with monitoring.
        """
        start_time = time.perf_counter()
        strategy_name = self.strategy.get_name()

        try:
            result = self.strategy.calculate(context)
            elapsed = time.perf_counter() - start_time

            # Update metrics
            metric = self.metrics[strategy_name]
            metric["execution_count"] += 1
            metric["total_time"] += elapsed
            metric["avg_time"] = metric["total_time"] / metric["execution_count"]

            if self.enable_logging:
                print(f"[{strategy_name}] Executed in {elapsed*1000:.3f}ms")

            return result

        except Exception as e:
            elapsed = time.perf_counter() - start_time

            # Update metrics even on error
            metric = self.metrics[strategy_name]
            metric["execution_count"] += 1
            metric["total_time"] += elapsed
            metric["avg_time"] = metric["total_time"] / metric["execution_count"]
            metric["errors"] += 1

            if self.enable_logging:
                print(f"[{strategy_name}] Error after {elapsed*1000:.3f}ms: {e}")

            raise

    def get_name(self) -> str:
        return self.strategy.get_name()

    @classmethod
    def get_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """Return all collected metrics."""
        return dict(cls.metrics)

    @classmethod
    def reset_metrics(cls):
        """Reset all metrics (useful for testing)."""
        cls.metrics.clear()


# ============================================================================
# Main Pricing Engine
# ============================================================================


class PricingEngine:
    """
    Main facade for the pricing system.
    Orchestrates strategy selection and execution.
    """

    def __init__(self, enable_caching: bool = True, enable_monitoring: bool = True):
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        self.cached_strategies: List[CachedStrategy] = []
        self.monitored_strategies: List[MonitoredStrategy] = []

    def _wrap_strategy(self, strategy: PricingStrategy) -> PricingStrategy:
        """Apply decorators to strategy in correct order."""
        current = strategy

        # Apply caching first (inner decorator)
        if self.enable_caching:
            cached = CachedStrategy(current)
            self.cached_strategies.append(cached)
            current = cached

        # Apply monitoring second (outer decorator)
        if self.enable_monitoring:
            monitored = MonitoredStrategy(current, enable_logging=False)
            self.monitored_strategies.append(monitored)
            current = monitored

        return current

    def calculate_price(
        self, customer: Customer, items: List[OrderItem]
    ) -> PricingContext:
        """
        Calculate final price for an order.

        Args:
            customer: Customer placing the order
            items: List of items in the order

        Returns:
            Complete pricing context with all calculations
        """
        context = PricingContext(customer=customer, items=items)
        pipeline = StrategySelector.select_pipeline(customer)

        # Wrap each strategy with decorators
        pipeline.strategies = [self._wrap_strategy(s) for s in pipeline.strategies]

        return pipeline.execute(context)

    def get_cache_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get cache statistics from all cached strategies."""
        return {
            cached.strategy.get_name(): cached.get_cache_stats()
            for cached in self.cached_strategies
        }

    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics from monitoring."""
        return MonitoredStrategy.get_metrics()


# ============================================================================
# Testing Utilities
# ============================================================================


def create_test_customer(
    tier: CustomerTier = CustomerTier.BRONZE, country: str = "US"
) -> Customer:
    """Helper to create test customers."""
    return Customer(
        id=f"CUST-{tier.value}",
        name=f"Test {tier.value.title()} Customer",
        tier=tier,
        country=country,
        total_lifetime_value=1000.0,
    )


def create_test_items(count: int = 3, unit_price: float = 25.0) -> List[OrderItem]:
    """Helper to create test order items."""
    return [
        OrderItem(
            product_id=f"PROD-{i}",
            name=f"Product {i}",
            quantity=2,
            unit_price=unit_price,
            weight=1.5,
        )
        for i in range(count)
    ]


# ============================================================================
# Main Demonstration
# ============================================================================


def print_pricing_details(context: PricingContext, tier_name: str):
    """Print formatted pricing details."""
    print(f"\nCustomer: {context.customer.name} ({tier_name})")
    print(f"Country: {context.customer.country}")
    print(f"Items: {context.total_items} items, {context.total_weight:.1f}kg total")
    print(f"\n{'Price Breakdown:':40}")
    print(f"  Base Price:        {context.base_price:>10.2f}")

    discount_pct = (
        (context.discount_amount / context.base_price * 100)
        if context.base_price > 0
        else 0
    )
    print(
        f"  Discount:          {-context.discount_amount:>10.2f} ({discount_pct:.0f}%)"
    )

    print(f"  Subtotal:          {context.base_price - context.discount_amount:>10.2f}")
    print(f"  Tax:               {context.tax_amount:>10.2f}")
    print(f"  Shipping:          {context.shipping_cost:>10.2f}")
    print(f"  {'-' * 40}")
    print(f"  Final Price:       ${context.final_price:>10.2f}")

    print(f"\nApplied Strategies: {len(context.applied_strategies)}")
    total_time = sum(context.execution_times.values())
    for i, strategy_name in enumerate(context.applied_strategies, 1):
        exec_time = context.execution_times[strategy_name]
        print(f"  {i}. {strategy_name:35} {exec_time*1000:>6.3f}ms")
    print(f"{'':>40} {'─' * 10}")
    print(f"{'Total Pipeline Time:':40} {total_time*1000:>6.3f}ms")


def main():
    """
    Demonstrate the pricing engine with various scenarios.
    """
    print("=" * 80)
    print("ENTERPRISE PRICING ENGINE - STRATEGY PATTERN DEMONSTRATION")
    print("=" * 80)

    # Create pricing engine with caching and monitoring
    engine = PricingEngine(enable_caching=True, enable_monitoring=True)

    # Test different customer tiers
    tiers = [
        CustomerTier.BRONZE,
        CustomerTier.SILVER,
        CustomerTier.GOLD,
        CustomerTier.PLATINUM,
    ]

    print("\n" + "=" * 80)
    print("SCENARIO 1: Testing All Customer Tiers (US, 3 items @ $25 each)")
    print("=" * 80)

    for tier in tiers:
        customer = create_test_customer(tier)
        items = create_test_items(3)
        context = engine.calculate_price(customer, items)
        print_pricing_details(context, tier.value.upper())

    # Test cache effectiveness by running same calculation again
    print("\n" + "=" * 80)
    print("SCENARIO 2: Testing Cache (Re-running same calculations)")
    print("=" * 80)

    for tier in tiers:
        customer = create_test_customer(tier)
        items = create_test_items(3)
        context = engine.calculate_price(customer, items)

    print("✓ Second run completed (should show cache hits)")

    # Test different scenarios
    print("\n" + "=" * 80)
    print("SCENARIO 3: Edge Cases")
    print("=" * 80)

    # Large order for Silver customer (triggers discount)
    print("\n--- Silver Customer with Large Order ($250) ---")
    customer = create_test_customer(CustomerTier.SILVER)
    items = create_test_items(5, unit_price=25.0)  # $250 total
    context = engine.calculate_price(customer, items)
    print_pricing_details(context, "SILVER (Large Order)")

    # International customer
    print("\n--- Platinum Customer in UK (20% tax) ---")
    customer = create_test_customer(CustomerTier.PLATINUM, country="UK")
    items = create_test_items(3)
    context = engine.calculate_price(customer, items)
    print_pricing_details(context, "PLATINUM (UK)")

    # Print cache statistics
    print("\n" + "=" * 80)
    print("CACHE STATISTICS")
    print("=" * 80)

    cache_stats = engine.get_cache_statistics()
    if cache_stats:
        print(
            f"\n{'Strategy':<40} {'Hits':<8} {'Misses':<8} {'Size':<8} {'Hit Rate':<10}"
        )
        print("-" * 80)
        for strategy_name, stats in cache_stats.items():
            print(
                f"{strategy_name:<40} "
                f"{stats['hits']:<8} "
                f"{stats['misses']:<8} "
                f"{stats['size']:<8} "
                f"{stats['hit_rate']:>6.1f}%"
            )
    else:
        print("No cache statistics available (caching disabled)")

    # Print monitoring metrics
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)

    metrics = engine.get_performance_metrics()
    if metrics:
        print(
            f"\n{'Strategy':<40} {'Executions':<12} {'Avg Time':<12} {'Total Time':<12} {'Errors':<8}"
        )
        print("-" * 80)
        for strategy_name, data in sorted(metrics.items()):
            print(
                f"{strategy_name:<40} "
                f"{data['execution_count']:<12} "
                f"{data['avg_time']*1000:>10.3f}ms "
                f"{data['total_time']*1000:>10.3f}ms "
                f"{data['errors']:<8}"
            )

        # Summary statistics
        total_executions = sum(m["execution_count"] for m in metrics.values())
        total_time = sum(m["total_time"] for m in metrics.values())
        total_errors = sum(m["errors"] for m in metrics.values())

        print("-" * 80)
        print(
            f"{'TOTALS':<40} {total_executions:<12} {'':<12} {total_time*1000:>10.3f}ms {total_errors:<8}"
        )
    else:
        print("No performance metrics available (monitoring disabled)")

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
