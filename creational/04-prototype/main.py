"""
Intent:
Specify the kinds of objects to create using a prototypical instance, and create new objects by 
copying this prototype.

Problem:
Say you have an object, and you want to create an exact copy of it. How would you do it? First, 
you have to create a new object of the same class. Then you have to go through all the fields of 
the original object and copy their values over to the new object.

Nice! But there’s a catch. Not all objects can be copied that way because some of the object’s 
fields may be private and not visible from outside of the object itself.
Also, if an object contains references to other objects, you have to decide whether to copy these 
objects as well (deep copy) or just copy the references (shallow copy).

There’s one more problem with the direct approach. Since you have to know the object’s class to 
create a duplicate, your code becomes dependent on that class. If the extra dependency doesn’t 
scare you, there’s another catch. Sometimes you only know the interface that the object follows, 
but not its concrete class, when, for example, a parameter in a method accepts any objects that 
follow some interface.

Solution:
The Prototype pattern suggests that you make the original object responsible for copying itself.
This way, you don’t have to know the details of the object’s class. You just call a method on the 
object that returns a copy of itself.
The Prototype pattern is implemented with a base interface that declares a cloning method. This 
method is then implemented in concrete classes, which return a copy of themselves.
The cloning method can be implemented in two ways. The first approach is to create a new object 
and copy all the fields from the original object to the new one. The second approach is to use 
serialization to create a copy of the object.
The Prototype pattern is often combined with the Factory Method pattern. In this case, a factory 
class is responsible for creating new objects by cloning a prototype instance.

When to use:
- When the classes to instantiate are specified at runtime, for example, by dynamic loading.
- To avoid building a class hierarchy of factories that parallels the class hierarchy of products.
- When instances of a class can have one of only a few different combinations of state. It may be 
    more convenient to install a corresponding number of prototypes and clone them rather than 
    instantiating the class manually, each time with the appropriate state.

How to implement:
1. Declare an interface with a cloning method.
2. Implement the cloning method in concrete classes. The method should return a copy of the object.
3. Client code should call the cloning method on an existing object to create a new object.

Pros and Cons:
+ You can add and remove products at runtime.
+ You can reduce the number of classes in your code.
+ You can get rid of the dependency on concrete classes.
- The cloning method must be implemented in every class of the product hierarchy.
- The cloning process may be complicated if an object has circular references to other objects.

Real-world use cases:
- The JavaScript language uses the Prototype pattern to add properties and methods to objects.
- The Prototype pattern is used in the C++ Standard Template Library (STL) to implement the 
    clone() method for iterators.
- The Prototype pattern is used in the Unity game engine to create copies of game objects.
- The Prototype pattern is used in the .NET Framework to implement the ICloneable interface.
"""

# Link: https://refactoring.guru/design-patterns/prototype


from abc import ABC, abstractmethod
import copy
from typing import Self
import uuid


class Style:
    def __init__(self, border_width: int, border_color: str, fill_color: str) -> None:
        self.border_width = border_width
        self.border_color = border_color
        self.fill_color = fill_color

    def __str__(self) -> str:
        return f"Style [Border Width: {self.border_width}, Border Color: {self.border_color}, Fill Color: {self.fill_color}]"
    

class Prototype(ABC):
    id: str
    type: str

    @abstractmethod
    def clone(self, deep: bool = True) -> Self: ...


class Shape(Prototype):
    type: str = "Shape"

    def __init__(self) -> None:
        self.id = str(uuid.uuid4())

    def clone(self, deep = True) -> Self:
        try:
            if deep:
                cloned = copy.deepcopy(self)
            else:
                cloned = copy.copy(self)
            cloned.id = str(uuid.uuid4())
            return cloned
        except Exception as e:
            raise RuntimeError("Cloning failed.") from e
        

class Circle(Shape):
    type = "Circle"

    def __init__(self, radius: int, x: int, y: int, style: Style) -> None:
        super().__init__()
        self.radius = radius
        self.x = x
        self.y = y
        self.style = style
    
    def __str__(self):
        return f"Circle [Radius: {self.radius}, X: {self.x}, Y: {self.y}, {self.style}]"
    

class Square(Shape):
    type = "Square"

    def __init__(self, side: int, x: int, y: int, style: Style) -> None:
        super().__init__()
        self.side = side
        self.x = x
        self.y = y
        self.style = style
    
    def __str__(self):
        return f"Square [Side: {self.side}, X: {self.x}, Y: {self.y}, {self.style}]"
    

class PrototypeRegistry:
    def __init__(self) -> None:
        self._prototypes: dict[str, Prototype] = {}

    def register(self, type: str, prototype: Prototype) -> None:
        if type in self._prototypes:
            raise KeyError(f"Prototype of type '{type}' is already registered.")
        self._prototypes[type] = prototype

    def unregister(self, type: str) -> None:
        if type not in self._prototypes:
            raise KeyError(f"Prototype of type '{type}' is not registered.")
        del self._prototypes[type]

    def clone(self, type: str, deep: bool = True) -> Prototype:
        if type not in self._prototypes:
            raise KeyError(f"Prototype of type '{type}' is not registered.")
        return self._prototypes[type].clone(deep)
    
    def list_prototypes(self) -> list[str]:
        return list(self._prototypes.keys())


if __name__ == "__main__":
    registry = PrototypeRegistry()

    # Create some styles
    red_style = Style(2, "red", "pink")
    blue_style = Style(3, "blue", "lightblue")

    # Create some shapes
    circle1 = Circle(10, 5, 5, red_style)
    square1 = Square(20, 10, 10, blue_style)

    # Register prototypes
    registry.register(circle1.type, circle1)
    registry.register(square1.type, square1)

    print("Registered prototypes:", registry.list_prototypes())

    # Clone shapes
    cloned_circle = registry.clone("Circle", deep=True)
    cloned_square = registry.clone("Square", deep=False)

    print("\nOriginal Circle:", circle1)
    print("Cloned Circle:", cloned_circle)

    print("\nOriginal Square:", square1)
    print("Cloned Square:", cloned_square)

    # Modify the style of the original square to see if it affects the cloned one
    square1.style.fill_color = "yellow"
    print("\nAfter modifying original Square's style:")
    print("Original Square:", square1)
    print("Cloned Square:", cloned_square)
