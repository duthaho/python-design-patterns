"""
Intent:
Attach additional responsibilities to an object dynamically. Decorators provide a flexible
alternative to subclassing for extending functionality.

Problem:
Imagine you’re developing a text editor application that allows users to format text. You have a
basic Text class that represents plain text. However, users want to apply various formatting options
like bold, italic, and underline to the text. If you were to create subclasses for each
combination of formatting options (e.g., BoldText, ItalicText, UnderlineText, BoldItalicText, etc.),
the number of subclasses would grow exponentially, leading to a complex and unmanageable class
hierarchy.

Solution:
The Decorator pattern suggests that you create a base interface or abstract class for the text
objects. Then, you create concrete classes for the basic text and for each formatting option as
decorators. Each decorator class wraps a text object and adds its specific formatting behavior. This
way, you can combine multiple decorators to achieve the desired formatting without creating a
proliferation of subclasses.

When to use:
- When you want to add responsibilities to individual objects dynamically and transparently, without
    affecting other objects.
- When you want to avoid a large number of subclasses for every possible combination of
    functionalities.
- When you want to adhere to the Single Responsibility Principle by separating concerns into
    different classes.
- When you want to add or remove functionalities at runtime.
- When you want to extend the behavior of a class without modifying its source code.
- When you want to create a flexible and reusable design that can adapt to changing requirements.
- When you want to enhance the functionality of an object in a way that is transparent to the client
    code.
- When you want to implement cross-cutting concerns (e.g., logging, caching, security) in a modular
    way.

How to implement:
1. Define a common interface or abstract class for both the core component and the decorators,
    declaring methods for operations that can be performed on the component.
2. Implement the core component class (e.g., Text) that represents the basic functionality and
    implements the common interface.
3. Implement decorator classes (e.g., BoldDecorator, ItalicDecorator) that also implement the common
    interface. Each decorator class should have a reference to a component object and implement the
    methods by delegating to the component and adding its specific behavior.
4. In the client code, create instances of the core component and wrap them with the desired
    decorators to achieve the desired functionality.
5. Use the common interface in your client code to interact with both the core component and the
    decorated objects uniformly.

Pros and Cons:
+ Provides a flexible and reusable way to extend the functionality of objects.
+ Adheres to the Single Responsibility Principle by separating concerns into different classes.
+ Avoids a large number of subclasses for every possible combination of functionalities.
+ Allows for dynamic addition and removal of functionalities at runtime.
- Can introduce additional complexity and indirection in the codebase.
- May lead to a proliferation of small classes if not managed carefully.
- Can be harder to debug due to the layers of wrapping.
- Requires careful design to ensure that decorators and core components share a common interface.
- Can lead to performance overhead due to multiple layers of wrapping and delegation.
- Can make the code harder to understand for developers unfamiliar with the pattern.
- Can complicate the object lifecycle management, especially when dealing with multiple decorators.
- Can lead to issues with identity and equality checks, as decorated objects may not be
    directly comparable to their core components.

Real-world use cases:
- In graphical user interfaces, the Decorator pattern is often used to add visual effects or
    behaviors to UI components, such as borders, scrollbars, or tooltips.
- In input/output streams, the Decorator pattern is used to add functionalities like buffering,
    compression, or encryption to data streams.
- In logging frameworks, the Decorator pattern can be used to add different logging behaviors,
    such as formatting, filtering, or outputting to different destinations.
- In web development, the Decorator pattern can be used to add functionalities like authentication,
    caching, or rate limiting to web requests and responses.
- In text processing applications, the Decorator pattern can be used to add formatting options like
    bold, italic, or underline to text objects.
"""

# Link: https://refactoring.guru/design-patterns/decorator


from abc import ABC, abstractmethod


class Text(ABC):
    @abstractmethod
    def render(self) -> str:
        pass


class PlainText(Text):
    def __init__(self, content: str) -> None:
        self.content = content

    def render(self) -> str:
        return self.content


class TextDecorator(Text):
    def __init__(self, wrapped_text: Text) -> None:
        self.wrapped_text = wrapped_text

    @abstractmethod
    def render(self) -> str:
        pass


class BoldDecorator(TextDecorator):
    def render(self) -> str:
        return f"<b>{self.wrapped_text.render()}</b>"


class ItalicDecorator(TextDecorator):
    def render(self) -> str:
        return f"<i>{self.wrapped_text.render()}</i>"


class UnderlineDecorator(TextDecorator):
    def render(self) -> str:
        return f"<u>{self.wrapped_text.render()}</u>"


if __name__ == "__main__":
    simple_text = PlainText("Hello, World!")
    print("Plain Text:", simple_text.render())

    bold_text = BoldDecorator(simple_text)
    print("Bold Text:", bold_text.render())

    italic_bold_text = ItalicDecorator(bold_text)
    print("Italic Bold Text:", italic_bold_text.render())

    underline_italic_bold_text = UnderlineDecorator(italic_bold_text)
    print("Underline Italic Bold Text:", underline_italic_bold_text.render())
