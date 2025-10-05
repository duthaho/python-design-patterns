from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, List, Type


class ShippingStrategy(ABC):
    """Abstract base class for shipping cost calculation strategies."""

    @abstractmethod
    def calculate_cost(self, weight: float, **kwargs) -> float:
        """Calculate shipping cost.

        Args:
            weight: Package weight in kilograms
            **kwargs: Additional parameters (e.g., declared_value, distance)

        Returns:
            Shipping cost in dollars
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class StandardShipping(ShippingStrategy):
    """Standard shipping: $5 base + $0.5 per kg"""

    def calculate_cost(self, weight: float, **kwargs) -> float:
        if weight < 0:
            raise ValueError("Weight cannot be negative")
        return 5 + (0.5 * weight)


class ExpressShipping(ShippingStrategy):
    """Express shipping: $10 base + $1 per kg"""

    def calculate_cost(self, weight: float, **kwargs) -> float:
        if weight < 0:
            raise ValueError("Weight cannot be negative")
        return 10 + (1.0 * weight)


class OvernightShipping(ShippingStrategy):
    """Overnight shipping: $20 base + $2 per kg"""

    def calculate_cost(self, weight: float, **kwargs) -> float:
        if weight < 0:
            raise ValueError("Weight cannot be negative")
        return 20 + (2.0 * weight)


class InsuranceShipping(ShippingStrategy):
    """Decorator strategy that adds insurance to base shipping."""

    def __init__(self, base_strategy: ShippingStrategy, insurance_rate: float = 0.02):
        if insurance_rate < 0 or insurance_rate > 1:
            raise ValueError("Insurance rate must be between 0 and 1")
        self.base_strategy = base_strategy
        self.insurance_rate = insurance_rate

    def calculate_cost(
        self, weight: float, declared_value: float = 0, **kwargs
    ) -> float:
        base_cost = self.base_strategy.calculate_cost(weight, **kwargs)
        insurance_cost = declared_value * self.insurance_rate
        return base_cost + insurance_cost

    def __repr__(self) -> str:
        return (
            f"InsuranceShipping(base={self.base_strategy}, rate={self.insurance_rate})"
        )


class CompositeOperation(Enum):
    """Operations for combining multiple strategy results."""

    SUM = ("sum", sum)
    MIN = ("min", min)
    MAX = ("max", max)
    AVERAGE = ("average", lambda costs: sum(costs) / len(costs) if costs else 0)

    def __init__(self, name: str, func: Callable):
        self.operation_name = name
        self.func = func


class CompositeShipping(ShippingStrategy):
    """Composite strategy to combine multiple shipping strategies."""

    def __init__(
        self,
        strategies: List[ShippingStrategy],
        operation: CompositeOperation = CompositeOperation.SUM,
    ):
        if not strategies:
            raise ValueError("CompositeShipping requires at least one strategy")
        self.strategies = strategies
        self.operation = operation

    def calculate_cost(self, weight: float, **kwargs) -> float:
        costs = [
            strategy.calculate_cost(weight, **kwargs) for strategy in self.strategies
        ]
        return self.operation.func(costs)

    def __repr__(self) -> str:
        strategies_repr = ", ".join(repr(s) for s in self.strategies)
        return (
            f"CompositeShipping([{strategies_repr}], operation={self.operation.name})"
        )


class ShippingCalculator:
    """Context class for calculating shipping costs using different strategies."""

    def __init__(self, strategy: ShippingStrategy):
        self._strategy = strategy

    @property
    def strategy(self) -> ShippingStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: ShippingStrategy):
        if not isinstance(strategy, ShippingStrategy):
            raise TypeError("Strategy must be a ShippingStrategy instance")
        self._strategy = strategy

    def calculate_cost(self, weight: float, **kwargs) -> float:
        """Calculate shipping cost using the current strategy."""
        return self._strategy.calculate_cost(weight, **kwargs)


class ShippingFactory:
    """Factory to create shipping strategies from configuration."""

    STRATEGIES: Dict[str, Type[ShippingStrategy]] = {
        "standard": StandardShipping,
        "express": ExpressShipping,
        "overnight": OvernightShipping,
    }

    @staticmethod
    def create_strategies(config: List[dict]) -> List[ShippingStrategy]:
        """Create multiple strategies from configuration list."""
        return [ShippingFactory.from_config(conf) for conf in config]

    @staticmethod
    def from_config(conf: dict) -> ShippingStrategy:
        """Create a strategy from configuration dictionary.

        Args:
            conf: Configuration dict with 'type' and optional parameters

        Returns:
            Configured ShippingStrategy instance

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(conf, dict):
            raise ValueError("Configuration must be a dictionary")

        if "type" not in conf:
            raise ValueError("Configuration must include 'type' field")

        strategy_type = conf["type"].lower()

        # Handle composite strategies
        if strategy_type == "composite":
            if "value" not in conf:
                raise ValueError(
                    "Composite strategy requires 'value' field with sub-strategies"
                )

            if not conf["value"]:
                raise ValueError(
                    "Composite strategy requires at least one sub-strategy"
                )

            sub_strategies = [
                ShippingFactory.from_config(sub_conf) for sub_conf in conf["value"]
            ]

            # Parse operation type
            operation_name = conf.get("operation", "sum").upper()
            try:
                operation = CompositeOperation[operation_name]
            except KeyError:
                valid_ops = ", ".join(op.name for op in CompositeOperation)
                raise ValueError(
                    f"Invalid operation: {operation_name}. Valid: {valid_ops}"
                )

            return CompositeShipping(sub_strategies, operation)

        # Handle insurance decorator
        if strategy_type == "insurance":
            rate = conf.get("rate", 0.02)
            base_conf = conf.get("base_strategy", {"type": "standard"})
            base_strategy = ShippingFactory.from_config(base_conf)
            return InsuranceShipping(base_strategy, rate)

        # Handle basic strategies
        strategy_class = ShippingFactory.STRATEGIES.get(strategy_type)
        if not strategy_class:
            raise ValueError(
                f"Unknown strategy type: '{strategy_type}'. "
                f"Available: {', '.join(ShippingFactory.STRATEGIES.keys())}"
            )

        return strategy_class()


if __name__ == "__main__":
    print("=" * 60)
    print("SHIPPING STRATEGY PATTERN DEMONSTRATION")
    print("=" * 60)

    # Configuration examples
    SHIPPING_CONFIG = [
        {"type": "standard"},
        {"type": "express"},
        {"type": "overnight"},
        {
            "type": "composite",
            "operation": "sum",
            "value": [{"type": "standard"}, {"type": "express"}],
        },
        {
            "type": "composite",
            "operation": "min",
            "value": [{"type": "standard"}, {"type": "express"}, {"type": "overnight"}],
        },
        {"type": "insurance", "rate": 0.03, "base_strategy": {"type": "express"}},
    ]

    strategies = ShippingFactory.create_strategies(SHIPPING_CONFIG)
    calculator = ShippingCalculator(strategies[0])

    package_weight = 10.0
    declared_value = 500.0

    strategy_descriptions = [
        "Standard Shipping",
        "Express Shipping",
        "Overnight Shipping",
        "Composite (Standard + Express) - SUM",
        "Composite (Best Price) - MIN",
        "Express + 3% Insurance",
    ]

    print(f"\nPackage: {package_weight}kg, Declared Value: ${declared_value}\n")

    for description, strategy in zip(strategy_descriptions, strategies):
        calculator.strategy = strategy
        cost = calculator.calculate_cost(package_weight, declared_value=declared_value)
        print(f"{description:40} ${cost:>7.2f}")
        print(f"  └─ Strategy: {strategy}")

    print("\n" + "=" * 60)

    # Demonstrate error handling
    print("\nError Handling Examples:")
    print("-" * 60)

    try:
        bad_config = {"type": "invalid_strategy"}
        ShippingFactory.from_config(bad_config)
    except ValueError as e:
        print(f"✓ Invalid strategy type caught: {e}")

    try:
        bad_config = {"type": "composite", "value": []}
        ShippingFactory.from_config(bad_config)
    except ValueError as e:
        print(f"✓ Empty composite caught: {e}")

    try:
        calculator.calculate_cost(-5)
    except ValueError as e:
        print(f"✓ Negative weight caught: {e}")
