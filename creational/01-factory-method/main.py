"""
Intent:
Define an interface for creating an object, but let subclasses alter the type of objects that 
will be created.

Problem:
Imagine that you’re creating a logistics management application. The first version of your app 
can only handle transportation by trucks, so the bulk of your code lives inside the Truck class.

Later, you decide to add support for ships. You create a Ship class and start adding code to
your app to handle it. But the more you work on this, the more you realize that you’re
constantly changing the same parts of your code every time you add a new transport type.
This is a sign that your code needs some refactoring. You need to find a way to make your app
more flexible and easier to extend.

Solution:
The Factory Method pattern suggests that you define a separate method for creating objects,
which subclasses can override to specify the type of objects that will be created.
This way, the core logic of your app can remain unchanged, while the subclasses take care of
the specifics of object creation.
This approach adheres to the Open/Closed Principle, which states that software entities should
be open for extension but closed for modification.

When to use:
- Your code needs to work with various types of objects, but you don’t want it to depend on
  the concrete classes of those objects.
- You want to provide a library of products, but you want to leave the choice of their
  implementation to the client code.
- You want to localize the knowledge of which helper subclass is the delegate.
- You want to share the code between several projects, but the products they work with are
  different.

How to implement:
1. Define a Creator class that declares the factory method, which returns an object of a
   Product class. The Creator may also define a default implementation of the factory method
   that returns a default ConcreteProduct object.
2. Create ConcreteCreator subclasses that override the factory method to return different
   ConcreteProduct objects.
3. Define a Product interface that declares the operations that all concrete products must
   implement.
4. Create ConcreteProduct classes that implement the Product interface.
5. The client code should work with the Creator class and its subclasses, using the factory
   method to create Product objects without being concerned about their concrete classes.

Pros and Cons:
+ You can introduce new product types without breaking existing client code.
- The code may become more complex due to the additional classes and interfaces.
- The indirection may make the code harder to understand for those unfamiliar with the pattern.

Real-world use cases:
- GUI frameworks often use the Factory Method pattern to create UI components like buttons,
    text fields, and menus, allowing for different look-and-feel implementations.
- Document management systems may use the Factory Method pattern to create different types of
    documents (e.g., Word, PDF, Excel) based on user input or configuration.
- Game development engines may use the Factory Method pattern to create various game objects
    (e.g., characters, weapons, power-ups) based on the game level or player choices.
- Database connection libraries may use the Factory Method pattern to create connections to
    different types of databases (e.g., MySQL, PostgreSQL, SQLite) based on configuration settings.
- Logging frameworks may use the Factory Method pattern to create different types of loggers
    (e.g., console logger, file logger, remote logger) based on the logging configuration.
- Content Management Systems (CMS) may use the Factory Method pattern to create different
    types of content blocks (e.g., text, image, video) based on user selection.
- Notification systems may use the Factory Method pattern to create different types of
    notifications (e.g., email, SMS, push) based on user preferences or system events.
- Serialization libraries may use the Factory Method pattern to create different serializers
    (e.g., JSON, XML, YAML) based on the desired output format.
- Payment processing systems may use the Factory Method pattern to create different payment
    gateways (e.g., PayPal, Stripe, Square) based on user choice or configuration.
"""

# Link: https://refactoring.guru/design-patterns/factory-method


from abc import ABC, abstractmethod


# Product Interface
class Transport(ABC):
    @abstractmethod
    def deliver(self) -> None:
        pass


# Concrete Products
class Truck(Transport):
    def deliver(self) -> None:
        print("Delivering by land in a box.")


class Ship(Transport):
    def deliver(self) -> None:
        print("Delivering by sea in a container.")


# Creator
class Logistics(ABC):
    @abstractmethod
    def create_transport(self) -> Transport:
        pass

    def plan_delivery(self) -> None:
        transport = self.create_transport()
        transport.deliver()


# Concrete Creators
class RoadLogistics(Logistics):
    def create_transport(self) -> Transport:
        return Truck()
    

class SeaLogistics(Logistics):
    def create_transport(self) -> Transport:
        return Ship()
    

# Client Code
def client_code(logistics: Logistics) -> None:
    logistics.plan_delivery()


if __name__ == "__main__":
    print("App: Launched with the RoadLogistics.")
    client_code(RoadLogistics())

    print("\nApp: Launched with the SeaLogistics.")
    client_code(SeaLogistics())
