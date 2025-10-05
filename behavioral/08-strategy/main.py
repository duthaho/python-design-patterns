"""
Intent:
Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.

Problem:
You have a class that uses different algorithms (strategies) to perform a specific task, and you want to switch between these algorithms at runtime without changing the class itself.

Solution:
Create a Strategy interface that defines a method for executing the algorithm. Implement concrete
strategy classes that implement this interface. The context class will use a strategy object to perform
the task, allowing the algorithm to be changed at runtime.

When to use:
- When you have multiple algorithms for a specific task and want to switch between them easily.
- When you want to avoid conditional statements for selecting algorithms.
- When you want to encapsulate algorithms to make them easier to maintain and extend.

How to implement:
1. Define a Strategy interface with a method for executing the algorithm.
2. Create concrete strategy classes that implement the Strategy interface.
3. Create a Context class that uses a Strategy object to perform the task.
4. Allow the Context to change the Strategy at runtime.

Pros and Cons:
+ Encapsulates algorithms, making them easier to maintain and extend.
+ Promotes the Open/Closed Principle by allowing new strategies to be added without modifying existing
    code.
- Increases the number of classes in the system, which can lead to complexity.
- Clients must be aware of different strategies to choose the appropriate one.

Real-world use cases:
- Sorting algorithms (e.g., quicksort, mergesort, bubblesort).
- Payment methods (e.g., credit card, PayPal, bank transfer).
- Compression algorithms (e.g., ZIP, RAR, TAR).
"""

# Link: https://refactoring.guru/design-patterns/strategy

from abc import ABC, abstractmethod
from typing import List


class DiscountStrategy(ABC):
    @abstractmethod
    def apply_discount(self, price: float) -> float:
        pass


class NoDiscount(DiscountStrategy):
    def apply_discount(self, price: float) -> float:
        return price


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float):
        self.percentage = percentage

    def apply_discount(self, price: float) -> float:
        return price * (1 - self.percentage / 100)


class FixedAmountDiscount(DiscountStrategy):
    def __init__(self, amount: float):
        self.amount = amount

    def apply_discount(self, price: float) -> float:
        return max(0, price - self.amount)


class CompositeDiscount(DiscountStrategy):
    def __init__(self, strategies: List[DiscountStrategy]):
        self.strategies = strategies

    def apply_discount(self, price: float) -> float:
        for strategy in self.strategies:
            price = strategy.apply_discount(price)
        return max(0, price)


class ShoppingCart:
    def __init__(self, discount_strategy: DiscountStrategy):
        self.items: List[float] = []
        self.discount_strategy = discount_strategy

    def add_item(self, price: float):
        self.items.append(price)

    def total(self) -> float:
        total_price = sum(self.items)
        return self.discount_strategy.apply_discount(total_price)

    def set_discount_strategy(self, discount_strategy: DiscountStrategy):
        self.discount_strategy = discount_strategy


class PromotionEngine:
    def __init__(self, discount_strategies: List[DiscountStrategy]):
        self.discount_strategies = discount_strategies

    def get_best_discount(self, price: float) -> tuple[float, DiscountStrategy]:
        best_price = price
        best_strategy = NoDiscount()
        for strategy in self.discount_strategies:
            discounted_price = strategy.apply_discount(price)
            if discounted_price < best_price:
                best_price = discounted_price
                best_strategy = strategy
        return best_price, best_strategy


class StrategyFactory:
    @staticmethod
    def create_strategies(config: List[dict]) -> List[DiscountStrategy]:
        return [StrategyFactory.from_config(conf) for conf in config]

    @staticmethod
    def from_config(conf: dict) -> DiscountStrategy:
        if conf["type"] == "percentage":
            return PercentageDiscount(conf["value"])
        elif conf["type"] == "fixed":
            return FixedAmountDiscount(conf["value"])
        elif conf["type"] == "composite":
            sub_strategies = [
                StrategyFactory.from_config(sub_conf) for sub_conf in conf["value"]
            ]
            return CompositeDiscount(sub_strategies)
        else:
            return NoDiscount()


PROMO_CONFIG = [
    {"type": "percentage", "value": 20},
    {"type": "fixed", "value": 75},
    {"type": "percentage", "value": 5},
    {
        "type": "composite",
        "value": [{"type": "percentage", "value": 10}, {"type": "fixed", "value": 30}],
    },
]


if __name__ == "__main__":
    strategies = StrategyFactory.create_strategies(PROMO_CONFIG)
    promo_engine = PromotionEngine(strategies)

    cart = ShoppingCart(NoDiscount())
    cart.add_item(100)
    cart.add_item(200)
    cart.add_item(300)

    total_price = cart.total()
    print(f"Total price without discount: {total_price}")

    best_price, best_strategy = promo_engine.get_best_discount(total_price)
    cart.set_discount_strategy(best_strategy)
    discounted_total = cart.total()
    print(f"Best discount applied. New total price: {discounted_total}")
