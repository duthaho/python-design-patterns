"""
Intent:
Define the skeleton of an algorithm in a method, deferring some steps to subclasses. Template Method
lets subclasses redefine certain steps of an algorithm without changing the algorithm's structure.

Problem:
You have an algorithm that consists of several steps, and you want to allow subclasses to override
some of these steps without changing the overall structure of the algorithm.

Solution:
Create an abstract class that defines the template method, which contains the algorithm's structure.
The template method calls abstract methods that subclasses must implement to provide specific behavior
for the steps of the algorithm.

When to use:
- When you have an algorithm that consists of several steps, and you want to allow subclasses to
    override some of these steps.
- When you want to avoid code duplication by putting common behavior in a base class.
- When you want to enforce a specific sequence of steps in an algorithm.

How to implement:
1. Define an abstract class with a template method that outlines the algorithm's structure.
2. Define abstract methods for the steps of the algorithm that subclasses must implement.
3. Create concrete subclasses that implement the abstract methods to provide specific behavior for
    the steps of the algorithm.
4. Optionally, provide default implementations for some steps in the abstract class.

Pros and Cons:
+ Promotes code reuse by putting common behavior in a base class.
+ Enforces a specific sequence of steps in an algorithm.
+ Allows subclasses to override specific steps without changing the overall structure of the algorithm.
- Can lead to a rigid class hierarchy if not designed carefully.
- Subclasses may have to implement methods they don't need if the abstract class defines too many
    abstract methods.

Real-world use cases:
- Frameworks that provide a base class with a template method for common tasks (e.g., web request
    handling).
- Algorithms that consist of several steps, such as data processing pipelines or game AI behavior.
"""

# Link: https://refactoring.guru/design-patterns/template-method

from abc import ABC, abstractmethod


class CaffeineBeverage(ABC):
    def prepare_recipe(self) -> None:
        self.boil_water()
        self.brew()
        self.pour_in_cup()
        if self.customer_wants_condiments():
            self.add_condiments()

    def boil_water(self) -> None:
        print("Boiling water")

    @abstractmethod
    def brew(self) -> None:
        pass

    def pour_in_cup(self) -> None:
        print("Pouring into cup")

    @abstractmethod
    def add_condiments(self) -> None:
        pass

    def customer_wants_condiments(self) -> bool:
        return True


class Tea(CaffeineBeverage):
    def brew(self) -> None:
        print("Steeping the tea")

    def add_condiments(self) -> None:
        print("Adding lemon")


class Coffee(CaffeineBeverage):
    def brew(self) -> None:
        print("Dripping coffee through filter")

    def add_condiments(self) -> None:
        print("Adding sugar and milk")


class CoffeeWithHook(CaffeineBeverage):
    def brew(self) -> None:
        print("Dripping coffee through filter")

    def add_condiments(self) -> None:
        print("Adding sugar and milk")

    def customer_wants_condiments(self) -> bool:
        answer = input("Would you like milk and sugar with your coffee (y/n)? ")
        return answer.lower().startswith("y")


if __name__ == "__main__":
    tea = Tea()
    tea.prepare_recipe()

    print()

    coffee = Coffee()
    coffee.prepare_recipe()

    print()

    coffee_with_hook = CoffeeWithHook()
    coffee_with_hook.prepare_recipe()
