"""
Intent:
Separate the construction of a complex object from its representation so that the same 
construction process can create different representations.

Problem:
Imagine a complex object that requires laborious, step-by-step initialization of many fields and 
nested objects. Such initialization code is usually buried inside a monstrous constructor with 
lots of parameters. Or even worse: scattered all over the client code.

For example, let’s think about how to create a House object. To build a simple house, you need to 
construct four walls and a floor, install a door, fit a pair of windows, and build a roof. But 
what if you want a bigger, brighter house, with a backyard and other goodies (like a heating 
system, plumbing, and electrical wiring)?

The simplest solution is to extend the base House class and create a set of subclasses to cover 
all combinations of the parameters. But eventually you’ll end up with a considerable number of 
subclasses. Any new parameter, such as the porch style, will require growing this hierarchy even 
more.

There’s another approach that doesn’t involve breeding subclasses. You can create a giant constructor right in the base House class with all possible parameters that control the house object. While this approach indeed eliminates the need for subclasses, it creates another problem.

The client code that builds the house will be littered with long lists of parameters, many of 
which will be optional. It will be hard to read and maintain. What’s worse, the client code 
will be tightly coupled to the concrete class of the house, which is a violation of the
Dependency Inversion Principle.

Solution:
The Builder pattern suggests that you extract the object construction code out of its own class 
and move it to separate objects called builders.

The pattern organizes object construction into a set of steps (buildWalls, buildDoor, etc.). To 
create an object, you execute a series of these steps on a builder object. The important part is 
that you don’t need to call all of the steps. You can call only those steps that are necessary 
for producing a particular configuration of an object.

The Builder pattern is often combined with the Director pattern. A director is an object that
knows the order in which to execute the building steps. The client code only needs to pass a 
builder object to the director and then trigger the construction process. The director will call
the building steps in a particular sequence. The same director can be used with different builders
to produce different representations of the product.

The Builder pattern is also often used to construct composite trees. In this case, the building
steps involve creating and assembling different parts of the tree.

When to use:
- The algorithm for creating a complex object should be independent of the parts that make up
    the object and how they’re assembled.
- The construction process must allow different representations for the object that’s being
    built.

How to implement:
1. Identify the complex object that you want to build. This object is often referred to as
    the Product.
2. Create a Builder interface that declares all the steps required to build the complex object.
3. Implement ConcreteBuilder classes that implement the Builder interface and provide specific
    implementations for each step. Each ConcreteBuilder should maintain an instance of the
    Product it’s building.
4. Optionally, create a Director class that defines the order in which to execute the building
    steps. The Director should have a method that accepts a Builder object and calls the
    building steps in a specific sequence.
5. The client code should create a Builder object (or a ConcreteBuilder) and pass it to the
    Director (if you have one). Then, it should trigger the construction process and retrieve
    the final Product from the Builder.

Pros and Cons:
+ You can construct complex objects step by step, allowing for greater control over the
    construction process.
+ You can create different representations of the same complex object using the same
    construction process.
- The pattern can introduce additional complexity due to the extra classes and interfaces
    involved.
- The Director class is optional, and in some cases, it may add unnecessary complexity if
    the construction process is straightforward.

Real-world use cases:
- Building complex UI components, such as forms or dialogs, where the construction process
    involves multiple steps and configurations.
- Constructing complex documents, such as reports or invoices, where the document structure
    can vary based on user input or configuration.
- Creating complex data structures, such as trees or graphs, where the construction process
    involves creating and linking multiple nodes or elements.
- Configuring and initializing complex objects in a step-by-step manner, such as setting up
    a database connection or configuring a network request.
- Constructing complex game objects, such as characters or levels, where the construction
    process involves multiple attributes and components.
- Building complex meal orders in a restaurant application, where the order can include
    various combinations of dishes, sides, and drinks.
- Assembling computer systems, where the construction process involves selecting and
    configuring various hardware components and peripherals.
"""

# Link: https://refactoring.guru/design-patterns/builder


from abc import ABC, abstractmethod
from typing import List


# Product Interface
class House:
    def __init__(self) -> None:
        self.parts: List[str] = []

    def list_parts(self) -> None:
        print(f"House parts: {', '.join(self.parts)}", end="")


# Builder Interface
class HouseBuilder(ABC):
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._product = House()

    @abstractmethod
    def build_walls(self) -> None:
        pass

    @abstractmethod
    def build_doors(self) -> None:
        pass

    @abstractmethod
    def build_windows(self) -> None:
        pass

    @abstractmethod
    def build_roof(self) -> None:
        pass

    def get_product(self) -> House:
        product = self._product
        self.reset()
        return product


# Concrete Builders
class IglooHouseBuilder(HouseBuilder):
    def build_walls(self) -> None:
        self._product.parts.append("Ice Walls")

    def build_doors(self) -> None:
        self._product.parts.append("Ice Door")

    def build_windows(self) -> None:
        self._product.parts.append("Ice Windows")

    def build_roof(self) -> None:
        self._product.parts.append("Ice Dome Roof")
    

class WoodenHouseBuilder(HouseBuilder):
    def build_walls(self) -> None:
        self._product.parts.append("Wooden Walls")

    def build_doors(self) -> None:
        self._product.parts.append("Wooden Door")

    def build_windows(self) -> None:
        self._product.parts.append("Glass Windows")

    def build_roof(self) -> None:
        self._product.parts.append("Wooden Roof")


# Director
class Director:
    def __init__(self) -> None:
        self._builder: HouseBuilder = None

    def builder(self, builder: HouseBuilder) -> None:
        self._builder = builder

    def build_minimal_viable_product(self) -> None:
        self._builder.build_walls()
        self._builder.build_roof()

    def build_full_featured_product(self) -> None:
        self._builder.build_walls()
        self._builder.build_doors()
        self._builder.build_windows()
        self._builder.build_roof()


# Client Code
def client_code(director: Director) -> None:
    builder = WoodenHouseBuilder()
    director.builder(builder)

    print("Standard basic house:")
    director.build_minimal_viable_product()
    builder.get_product().list_parts()
    print("\n")

    print("Standard full featured house:")
    director.build_full_featured_product()
    builder.get_product().list_parts()
    print("\n")

    print("Custom house:")
    builder.reset()
    builder.build_walls()
    builder.build_windows()
    builder.get_product().list_parts()
    print("\n")


if __name__ == "__main__":
    director = Director()
    client_code(director)
    