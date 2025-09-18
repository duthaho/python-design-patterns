"""
Intent:
Use sharing to support large numbers of fine-grained objects efficiently.

Problem:
When an application uses a large number of objects, it can lead to high memory consumption and
reduced performance. The Flyweight pattern addresses this issue by sharing common parts of object
state among multiple objects, thereby minimizing memory usage.

Solution:
The Flyweight pattern involves creating a factory that manages a pool of shared objects. When a client
requests an object, the factory checks if an existing instance with the same intrinsic state is
available. If so, it returns the shared instance; otherwise, it creates a new one. The intrinsic
state is the state that is shared among objects, while the extrinsic state is unique to each object
and is not shared.

This pattern is particularly useful in scenarios where many objects are similar and can share common data.

When to Use:
- When an application needs to support a large number of similar objects.
- When memory usage is a concern and you want to reduce the number of object instances.
- When objects can be divided into intrinsic (shared) and extrinsic (unique) states.
- When you want to improve performance by reducing the overhead of object creation.

How to Implement:
1. Identify the intrinsic and extrinsic states of the objects you want to share.
2. Create a Flyweight interface that defines methods for operating on the intrinsic state.
3. Implement concrete Flyweight classes that store the intrinsic state and implement the Flyweight
    interface.
4. Create a Flyweight Factory that manages a pool of Flyweight objects. The factory should provide
a method to get a Flyweight object based on its intrinsic state, creating a new one if necessary.
5. In the client code, use the Flyweight Factory to obtain Flyweight objects and pass the extrinsic
    state as needed.
6. Ensure that the Flyweight objects are immutable to prevent unintended side effects when shared.
7. Optionally, implement a mechanism to manage the lifecycle of Flyweight objects, such as reference
    counting or caching strategies.

Pros and Cons:
+ Reduces memory consumption by sharing common state among multiple objects.
+ Improves performance by minimizing object creation overhead.
+ Promotes a clear separation between intrinsic and extrinsic state.
- Can introduce complexity in managing shared state and ensuring immutability.
- May lead to increased complexity in the client code due to the need to manage extrinsic state.
- Not suitable for all scenarios, especially when objects have a lot of unique state.

Real-world use cases:
- Text editors often use the Flyweight pattern to manage character formatting, where characters
    share font and size information.
- In graphical applications, the Flyweight pattern can be used to manage shapes or icons that share
    common properties like color or style.
- In game development, the Flyweight pattern can be used to manage game entities that share common
    attributes, such as textures or models.
- In web applications, the Flyweight pattern can be used to manage UI components that share common
    styles or behaviors.
- In document processing systems, the Flyweight pattern can be used to manage elements like
    paragraphs or sections that share formatting attributes.
- In caching systems, the Flyweight pattern can be used to manage frequently accessed data that can
    be shared among multiple users or sessions.
- In network protocols, the Flyweight pattern can be used to manage protocol headers that share
    common fields across multiple messages.
"""

# Link: https://refactoring.guru/design-patterns/flyweight


from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CharacterFlyweight:
    char: str  # Intrinsic state
    font: str  # Intrinsic state
    size: int  # Intrinsic state

    def display(self, position: Tuple[int, int]) -> None:
        # Extrinsic state is passed as a parameter
        print(
            f"Character: {self.char}, Font: {self.font}, Size: {self.size}, Position: {position}"
        )


class CharacterFactory:
    _flyweights: Dict[Tuple[str, str, int], CharacterFlyweight] = {}

    @classmethod
    def get_flyweight(cls, char: str, font: str, size: int) -> CharacterFlyweight:
        key = (char, font, size)
        if key not in cls._flyweights:
            cls._flyweights[key] = CharacterFlyweight(char, font, size)
        return cls._flyweights[key]

    @classmethod
    def get_total_characters(cls) -> int:
        return len(cls._flyweights)


class Paragraph:
    def __init__(self, alignment: str, indentation: int):
        self.alignment = alignment  # Extrinsic state
        self.indentation = indentation  # Extrinsic state
        self.characters: list[CharacterFlyweight] = []

    def add_character(self, char: CharacterFlyweight) -> None:
        self.characters.append(char)

    def display(self, position: Tuple[int, int] = (0, 0)) -> None:
        print(
            f"Paragraph (Alignment: {self.alignment}, Indentation: {self.indentation})"
        )
        for idx, char in enumerate(self.characters):
            x = position[0] + idx * 10  # Example position calculation
            y = position[1]
            char.display((x, y))


class Document:
    def __init__(self):
        self.paragraphs: list[Paragraph] = []

    def add_paragraph(self, paragraph: Paragraph) -> None:
        self.paragraphs.append(paragraph)

    def display(self) -> None:
        for paragraph in self.paragraphs:
            x = 0
            y = self.paragraphs.index(paragraph) * 20  # Example position calculation
            paragraph.display((x, y))


if __name__ == "__main__":
    document = Document()

    para1 = Paragraph(alignment="left", indentation=5)
    para1.add_character(CharacterFactory.get_flyweight("H", "Arial", 12))
    para1.add_character(CharacterFactory.get_flyweight("e", "Arial", 12))
    para1.add_character(CharacterFactory.get_flyweight("l", "Arial", 12))
    para1.add_character(CharacterFactory.get_flyweight("l", "Arial", 12))
    para1.add_character(CharacterFactory.get_flyweight("o", "Arial", 12))

    para2 = Paragraph(alignment="right", indentation=10)
    para2.add_character(CharacterFactory.get_flyweight("W", "Arial", 12))
    para2.add_character(CharacterFactory.get_flyweight("o", "Arial", 12))
    para2.add_character(CharacterFactory.get_flyweight("r", "Arial", 12))
    para2.add_character(CharacterFactory.get_flyweight("l", "Arial", 12))
    para2.add_character(CharacterFactory.get_flyweight("d", "Arial", 12))

    document.add_paragraph(para1)
    document.add_paragraph(para2)

    document.display()

    print(
        f"Total unique CharacterFlyweight instances: {CharacterFactory.get_total_characters()}"
    )
