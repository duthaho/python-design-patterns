"""
Intent:
Define an interface for creating families of related or dependent objects without specifying
their concrete classes.

Problem:
Imagine that you’re creating a furniture shop simulator. Your code consists of classes that 
represent:

1. A family of related products, say: Chair + Sofa + CoffeeTable.
2. Several variants of this family. For example, products Chair + Sofa + CoffeeTable are 
available in these variants: Modern, Victorian, ArtDeco.

Initially, your app only supports the Modern variant. So, you create classes like ModernChair, 
ModernSofa, and ModernCoffeeTable. The client code works with these classes directly, creating 
instances of them whenever it needs a new piece of furniture.

Later, you decide to add support for the Victorian and ArtDeco variants. You create new classes 
like VictorianChair, VictorianSofa, VictorianCoffeeTable, ArtDecoChair, ArtDecoSofa, and 
ArtDecoCoffeeTable. However, you quickly realize that the client code is littered with references 
to these concrete classes. Every time you add a new variant, you have to modify the client code 
to accommodate the new classes. This violates the Open/Closed Principle, which states that 
software entities should be open for extension but closed for modification.

Solution:
The Abstract Factory pattern suggests that you create an abstract factory interface that declares 
methods for creating each type of product. Then, you implement concrete factory classes for each 
variant of the product family. Each concrete factory class implements the methods defined in the 
abstract factory interface to create instances of the corresponding concrete product classes. 
This way, the client code can work with the abstract factory interface and remain agnostic to the 
concrete classes of the products it uses. When you want to add a new variant, you simply create a 
new concrete factory class without modifying the existing client code.

When to use:
- You need to create families of related or dependent objects without specifying their concrete 
classes.
- You want to ensure that products from one family are used together, and you want to prevent 
mixing products from different families.
- You want to provide a library of products, but you want to leave the choice of their 
implementation to the client code.
- You want to localize the knowledge of which helper subclass is the delegate.
- You want to share the code between several projects, but the products they work with are 
different.

How to implement:
1. Define an AbstractFactory interface that declares methods for creating each type of product.
2. Create ConcreteFactory classes that implement the AbstractFactory interface to create specific 
variants of the product family.
3. Define Product interfaces for each type of product that declare the operations that all 
concrete products must implement.
4. Create ConcreteProduct classes that implement the Product interfaces.
5. The client code should work with the AbstractFactory interface and its concrete 
implementations, using the factory methods to create Product objects without being concerned 
about their concrete classes.

Pros and Cons:
+ You can introduce new product families without breaking existing client code.
+ You ensure that products from one family are used together, preventing compatibility issues.
- The code may become more complex due to the additional classes and interfaces.
- The indirection may make the code harder to understand for those unfamiliar with the pattern.
- You need to create a new concrete factory class for each new product family, which can lead to
class proliferation.

Real-world use cases:
- GUI frameworks often use the Abstract Factory pattern to create UI components like buttons, 
text fields, and menus, allowing for different look-and-feel implementations.
- Cross-platform applications may use the Abstract Factory pattern to create platform-specific UI 
elements, ensuring a consistent user experience across different operating systems.
- Game development engines may use the Abstract Factory pattern to create various game objects (e.
g., characters, weapons, power-ups) based on the game level or player choices.
- Database connection libraries may use the Abstract Factory pattern to create connections to 
different types of databases (e.g., MySQL, PostgreSQL, SQLite) based on configuration settings.
- Logging frameworks may use the Abstract Factory pattern to create different types of loggers (e.
g., console logger, file logger, remote logger) based on the logging configuration.
"""

# Link: https://refactoring.guru/design-patterns/abstract-factory

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


class Chair(ABC):
    @abstractmethod
    def sit_on(self) -> str:
        pass


class Sofa(ABC):
    @abstractmethod
    def lie_on(self) -> str:
        pass


class CoffeeTable(ABC):
    @abstractmethod
    def put_on(self) -> str:
        pass


class ModernChair(Chair):
    def sit_on(self) -> str:
        return "Sitting on a modern chair."
    

class ModernSofa(Sofa):
    def lie_on(self) -> str:
        return "Lying on a modern sofa."
    

class ModernCoffeeTable(CoffeeTable):
    def put_on(self) -> str:
        return "Putting things on a modern coffee table."
    

class VictorianChair(Chair):
    def sit_on(self) -> str:
        return "Sitting on a Victorian chair."
    

class VictorianSofa(Sofa):
    def lie_on(self) -> str:
        return "Lying on a Victorian sofa."
    

class VictorianCoffeeTable(CoffeeTable):
    def put_on(self) -> str:
        return "Putting things on a Victorian coffee table."
    

class ArtDecoChair(Chair):
    def sit_on(self) -> str:
        return "Sitting on an ArtDeco chair."
    

class ArtDecoSofa(Sofa):
    def lie_on(self) -> str:
        return "Lying on an ArtDeco sofa."
    

class ArtDecoCoffeeTable(CoffeeTable):
    def put_on(self) -> str:
        return "Putting things on an ArtDeco coffee table."
    

class FurnitureFactory(ABC):
    @abstractmethod
    def create_chair(self) -> Chair:
        pass

    @abstractmethod
    def create_sofa(self) -> Sofa:
        pass

    @abstractmethod
    def create_coffee_table(self) -> CoffeeTable:
        pass


class ModernFurnitureFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return ModernChair()
    
    def create_sofa(self) -> Sofa:
        return ModernSofa()
    
    def create_coffee_table(self) -> CoffeeTable:
        return ModernCoffeeTable()
    

class VictorianFurnitureFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return VictorianChair()
    
    def create_sofa(self) -> Sofa:
        return VictorianSofa()
    
    def create_coffee_table(self) -> CoffeeTable:
        return VictorianCoffeeTable()
    

class ArtDecoFurnitureFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return ArtDecoChair()
    
    def create_sofa(self) -> Sofa:
        return ArtDecoSofa()
    
    def create_coffee_table(self) -> CoffeeTable:
        return ArtDecoCoffeeTable()
    

def client_code(factory: FurnitureFactory) -> None:
    chair = factory.create_chair()
    sofa = factory.create_sofa()
    coffee_table = factory.create_coffee_table()

    print(chair.sit_on())
    print(sofa.lie_on())
    print(coffee_table.put_on())


if __name__ == "__main__":
    print("Client: Testing client code with the ModernFurnitureFactory:")
    client_code(ModernFurnitureFactory())

    print("\nClient: Testing the same client code with the VictorianFurnitureFactory:")
    client_code(VictorianFurnitureFactory())

    print("\nClient: Testing the same client code with the ArtDecoFurnitureFactory:")
    client_code(ArtDecoFurnitureFactory())
