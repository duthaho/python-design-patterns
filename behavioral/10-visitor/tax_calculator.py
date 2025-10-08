from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TaxVisitor(Protocol):
    """Protocol for tax calculation visitors."""

    def visit_book(self, book: "Book") -> float:
        """Calculate tax for a book."""
        ...

    def visit_electronics(self, electronics: "Electronics") -> float:
        """Calculate tax for electronics."""
        ...

    def visit_food(self, food: "Food") -> float:
        """Calculate tax for food."""
        ...


class Product(Protocol):
    """Protocol for taxable products."""

    def accept(self, visitor: TaxVisitor) -> float:
        """Accept a visitor for tax calculation."""
        ...


@dataclass(frozen=True)
class Book:
    """Represents a book product."""

    title: str
    price: float

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

    def accept(self, visitor: TaxVisitor) -> float:
        return visitor.visit_book(self)


@dataclass(frozen=True)
class Electronics:
    """Represents an electronics product."""

    name: str
    price: float

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

    def accept(self, visitor: TaxVisitor) -> float:
        return visitor.visit_electronics(self)


@dataclass(frozen=True)
class Food:
    """Represents a food product."""

    name: str
    price: float

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

    def accept(self, visitor: TaxVisitor) -> float:
        return visitor.visit_food(self)


class USTaxVisitor:
    """US tax calculation strategy.

    Tax rates:
    - Books: 0%
    - Electronics: 15%
    - Food: 5%
    """

    def visit_book(self, book: Book) -> float:
        return 0.0  # No tax on books in US

    def visit_electronics(self, electronics: Electronics) -> float:
        return electronics.price * 0.15

    def visit_food(self, food: Food) -> float:
        return food.price * 0.05


class EUTaxVisitor:
    """EU tax calculation strategy (VAT).

    Tax rates:
    - Books: 5%
    - Electronics: 20%
    - Food: 10%
    """

    def visit_book(self, book: Book) -> float:
        return book.price * 0.05

    def visit_electronics(self, electronics: Electronics) -> float:
        return electronics.price * 0.20

    def visit_food(self, food: Food) -> float:
        return food.price * 0.10


class CanadaTaxVisitor:
    """Canada tax calculation strategy (GST/PST).

    Tax rates:
    - Books: 0% (exempt)
    - Electronics: 13%
    - Food: 5% (basic groceries)
    """

    def visit_book(self, book: Book) -> float:
        return 0.0

    def visit_electronics(self, electronics: Electronics) -> float:
        return electronics.price * 0.13

    def visit_food(self, food: Food) -> float:
        return food.price * 0.05


def demo_tax_calculator():
    """Demonstrate the tax calculator example."""
    cart = [
        Book("Design Patterns", 45.00),
        Electronics("Laptop", 1200.00),
        Food("Coffee Beans", 15.00),
    ]

    # US Tax
    us_visitor = USTaxVisitor()
    us_taxes = [item.accept(us_visitor) for item in cart]
    total_us_tax = sum(us_taxes)

    print("\nUS Tax Calculation:")
    for item, tax in zip(cart, us_taxes):
        print(f"  {item}: ${tax:.2f}")
    print(f"Total US Tax: ${total_us_tax:.2f}")

    # EU Tax
    eu_visitor = EUTaxVisitor()
    eu_taxes = [item.accept(eu_visitor) for item in cart]
    total_eu_tax = sum(eu_taxes)

    print("\nEU Tax Calculation:")
    for item, tax in zip(cart, eu_taxes):
        print(f"  {item}: ${tax:.2f}")
    print(f"Total EU Tax: ${total_eu_tax:.2f}")

    # Canada Tax
    canada_visitor = CanadaTaxVisitor()
    canada_taxes = [item.accept(canada_visitor) for item in cart]
    total_canada_tax = sum(canada_taxes)

    print("\nCanada Tax Calculation:")
    for item, tax in zip(cart, canada_taxes):
        print(f"  {item}: ${tax:.2f}")
    print(f"Total Canada Tax: ${total_canada_tax:.2f}")


def main():
    """Run all demonstrations."""
    demo_tax_calculator()


if __name__ == "__main__":
    main()
