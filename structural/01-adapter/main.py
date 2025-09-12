"""
Intent:
Convert the interface of a class into another interface clients expect. Adapter lets classes work
together that couldn't otherwise because of incompatible interfaces.
Also known as Wrapper.

Problem:
Imagine that you’re creating a stock market monitoring app. The app downloads the stock data from
multiple sources in XML format and then displays nice-looking charts and diagrams for the user.

At some point, you decide to improve the app by integrating a smart 3rd-party analytics library. But there’s a catch: the analytics library only works with data in JSON format.

You could change the library to work with XML. However, this might break some existing code that relies on the library. And worse, you might not have access to the library’s source code in the first place, making this approach impossible.

Solution:
The Adapter pattern suggests that you create a special adapter class that converts the interface of the XML data source into the interface expected by the analytics library.

The adapter class contains a reference to an instance of the XML data source and implements the interface expected by the analytics library. When the analytics library calls methods on the adapter, the adapter translates those calls into calls to the XML data source, converting the data from XML to JSON format as needed.

This way, the analytics library can work with the XML data source without any changes to either the library or the data source. The adapter acts as a bridge between the two incompatible interfaces, allowing them to work together seamlessly.

When to use:
- When you want to use an existing class, and its interface does not match the one you need.
- When you want to create a reusable class that cooperates with unrelated or unforeseen classes,
    that is, classes that don't necessarily have compatible interfaces.
- When you need to use several existing subclasses, but it's impractical to adapt their
    interfaces by subclassing every one. An object adapter can adapt the interface of its parent
    class.

How to implement:
1. Identify the incompatible interfaces that need to work together.
2. Create an adapter class that implements the interface expected by the client.
3. Inside the adapter class, hold a reference to an instance of the class with the incompatible
    interface.
4. Implement the methods of the expected interface in the adapter class by translating calls
    into calls to the methods of the incompatible class, performing any necessary data conversion.
5. Use the adapter class in place of the incompatible class when interacting with the client.
6. Test the adapter to ensure that it correctly translates calls and data between the two interfaces.
7. Optionally, consider using composition or inheritance for the adapter class, depending on
    the specific requirements and constraints of your application.

Pros and Cons:
+ Allows classes with incompatible interfaces to work together.
+ Promotes code reusability by enabling the use of existing classes without modification.
+ Can simplify complex interfaces by providing a more straightforward interface to the client.
- Can introduce additional complexity and indirection in the codebase.
- May lead to performance overhead due to the additional layer of abstraction.
- Can result in a proliferation of adapter classes if many incompatible interfaces need to be
    adapted.

Real-world use cases:
- In software development, adapters are often used to integrate third-party libraries or APIs
    that have different interfaces than the rest of the application.
- In hardware, adapters are used to connect devices with different interfaces, such as a
    USB-to-Ethernet adapter that allows a computer to connect to a wired network using a USB port.
- In user interface design, adapters can be used to convert data from one format to another,
    such as converting XML data to JSON format for use in a web application.
- The Java I/O library uses the Adapter pattern extensively. For example, the `InputStreamReader`
    class acts as an adapter that converts byte streams to character streams.
- In the .NET framework, the `StreamReader` and `StreamWriter` classes serve as adapters that
    convert byte streams to character streams and vice versa.
- The `javax.servlet` package in Java uses the Adapter pattern to allow different types of
    servlets to work with the same interface, enabling interoperability between various servlet
    implementations.
- In web development, libraries like jQuery can act as adapters to provide a consistent interface
    for DOM manipulation across different browsers, abstracting away the differences in their
    native APIs.
"""

# Link: https://refactoring.guru/design-patterns/adapter


from abc import ABC, abstractmethod


class Duck(ABC):
    @abstractmethod
    def quack(self) -> None:
        pass

    @abstractmethod
    def fly(self) -> None:
        pass


class MallardDuck(Duck):
    def quack(self) -> None:
        print("Quack")

    def fly(self) -> None:
        print("I'm flying")


class Turkey(ABC):
    @abstractmethod
    def gobble(self) -> None:
        pass

    @abstractmethod
    def fly(self) -> None:
        pass


class WildTurkey(Turkey):
    def gobble(self) -> None:
        print("Gobble gobble")

    def fly(self) -> None:
        print("I'm flying a short distance")


class TurkeyAdapter(Duck):
    def __init__(self, turkey: Turkey) -> None:
        self.turkey = turkey

    def quack(self) -> None:
        self.turkey.gobble()

    def fly(self) -> None:
        for _ in range(5):
            self.turkey.fly()


def test_duck(duck: Duck) -> None:
    duck.quack()
    duck.fly()


def main() -> None:
    duck = MallardDuck()

    turkey = WildTurkey()
    turkey_adapter = TurkeyAdapter(turkey)

    print("The Turkey says...")
    turkey.gobble()
    turkey.fly()

    print("\nThe Duck says...")
    test_duck(duck)

    print("\nThe TurkeyAdapter says...")
    test_duck(turkey_adapter)


if __name__ == "__main__":
    main()
