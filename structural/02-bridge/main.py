"""
Intent:
Decouple an abstraction from its implementation so that the two can vary independently.
Also known as Handle/Body.

Problem:
Imagine you’re developing a graphics application that needs to support multiple shapes (like
circles and squares) and multiple rendering engines (like vector and raster). If you implement
each shape with each rendering engine directly, you’ll end up with a combinatorial explosion of
classes (e.g., VectorCircle, RasterCircle, VectorSquare, RasterSquare).

This approach is not scalable and makes it hard to add new shapes or rendering engines in the
future.

Solution:
The Bridge pattern suggests that you separate the abstraction (shapes) from the implementation
(rendering engines) by creating two independent class hierarchies. The abstraction hierarchy
contains the shapes, while the implementation hierarchy contains the rendering engines. The
shapes hold a reference to a rendering engine and delegate the rendering work to it. This way,
you can mix and match shapes and rendering engines without creating a new class for each
combination.

When to use:
- When you want to avoid a permanent binding between an abstraction and its implementation.
- When both the abstractions and their implementations should be extensible by subclassing.
- When changes in the implementation of an abstraction should have no impact on clients.
- When you want to share an implementation among multiple objects and this fact should be hidden
    from the client.

How to implement:
1. Identify the abstraction and its implementation that need to be decoupled.
2. Create an interface or abstract class for the implementation hierarchy, defining the methods
    that concrete implementations must implement.
3. Create concrete implementation classes that implement the implementation interface.
4. Create an abstract class for the abstraction hierarchy that holds a reference to an instance
    of the implementation interface.
5. Implement concrete abstraction classes that extend the abstract class and use the implementation
    reference to perform their operations.
6. Use the abstraction classes in your client code, passing in different implementation instances
    as needed.

Pros and Cons:
+ Decouples the abstraction from its implementation, allowing them to vary independently.
+ Improves code maintainability and scalability by reducing the number of classes needed for
    combinations of abstractions and implementations.
+ Promotes the Single Responsibility Principle by separating concerns.
- Can introduce additional complexity and indirection in the codebase.
- May lead to a proliferation of classes if not managed carefully.
- Can be overkill for simple scenarios where a single implementation is sufficient.

Real-world use cases:
- In GUI frameworks, the Bridge pattern is often used to separate the abstraction of UI components
    (like buttons and text fields) from their platform-specific implementations (like Windows, macOS,
    or Linux).
- In database access layers, the Bridge pattern can be used to separate the abstraction of database
    operations from the specific database implementations (like MySQL, PostgreSQL, or SQLite).
- In graphics libraries, the Bridge pattern can be used to separate the abstraction of shapes and
    drawing operations from the specific rendering engines (like vector or raster).
"""

# Link: https://refactoring.guru/design-patterns/bridge


from abc import ABC, abstractmethod


class Renderer(ABC):
    @abstractmethod
    def render_shape(self, shape: str, **kwargs) -> None:
        pass


class RasterRenderer(Renderer):
    def render_shape(self, shape: str, **kwargs) -> None:
        if shape == "circle":
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            radius = kwargs.get("radius", 1)
            print(f"Drawing pixels for a circle of radius {radius} at ({x}, {y}).")
        elif shape == "square":
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            side = kwargs.get("side", 1)
            print(f"Drawing pixels for a square of side {side} at ({x}, {y}).")
        else:
            print(f"Raster rendering not supported for shape: {shape}")


class VectorRenderer(Renderer):
    def render_shape(self, shape: str, **kwargs) -> None:
        if shape == "circle":
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            radius = kwargs.get("radius", 1)
            print(f"Drawing a circle of radius {radius} at ({x}, {y}).")
        elif shape == "square":
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            side = kwargs.get("side", 1)
            print(f"Drawing a square of side {side} at ({x}, {y}).")
        else:
            print(f"Vector rendering not supported for shape: {shape}")


class Shape(ABC):
    def __init__(self, renderer: Renderer) -> None:
        self.renderer = renderer

    @abstractmethod
    def draw(self) -> None:
        pass

    @abstractmethod
    def resize(self, factor: float) -> None:
        pass


class Circle(Shape):
    def __init__(self, renderer: Renderer, x: float, y: float, radius: float) -> None:
        super().__init__(renderer)
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self) -> None:
        self.renderer.render_shape("circle", x=self.x, y=self.y, radius=self.radius)

    def resize(self, factor: float) -> None:
        self.radius *= factor


class Square(Shape):
    def __init__(self, renderer: Renderer, x: float, y: float, side: float) -> None:
        super().__init__(renderer)
        self.x = x
        self.y = y
        self.side = side

    def draw(self) -> None:
        self.renderer.render_shape("square", x=self.x, y=self.y, side=self.side)

    def resize(self, factor: float) -> None:
        self.side *= factor


if __name__ == "__main__":
    raster_renderer = RasterRenderer()
    vector_renderer = VectorRenderer()

    circle = Circle(raster_renderer, 5, 10, 15)
    circle.draw()
    circle.resize(2)
    circle.draw()

    circle = Circle(vector_renderer, 5, 10, 15)
    circle.draw()
    circle.resize(2)
    circle.draw()

    square = Square(vector_renderer, 20, 30, 10)
    square.draw()
    square.resize(3)
    square.draw()

    square = Square(raster_renderer, 20, 30, 10)
    square.draw()
    square.resize(3)
    square.draw()
