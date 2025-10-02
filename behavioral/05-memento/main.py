"""
Intent:
Provide a way to capture and externalize an object's internal state so that the object can be
restored to that state later, without violating encapsulation.

Problem:
Imagine you’re developing a text editor application that allows users to write and edit documents. Users
often make changes to their documents, and they may want to undo or redo those changes. Implementing
this functionality can be complex, especially if you want to maintain the integrity of the document's
state without exposing its internal structure.

Solution:
The Memento pattern suggests creating a separate object, called a memento, that captures the internal
state of the document at a specific point in time. The document can then use this memento to restore its
state when needed, such as when the user wants to undo or redo changes. The memento object is typically
opaque to the rest of the application, meaning that only the document can access its internal state.

When to use:
- When you need to implement undo/redo functionality in an application.
- When you want to capture and restore an object's state without exposing its internal structure.
- When you want to maintain the integrity of an object's state while allowing for state changes.
- When you want to provide a way to save and restore an object's state at different points in time.
- When you want to avoid complex state management logic in the main object.

How to implement:
1. Identify the object whose state you want to capture and restore (the originator).
2. Create a memento class that will hold the internal state of the originator. This class should
    provide methods to get and set the state, but it should not expose the internal structure of
    the state.
3. In the originator class, implement methods to create a memento that captures its current state
    and to restore its state from a memento.
4. Create a caretaker class that will manage the mementos. This class should provide methods to
    save and retrieve mementos, allowing the originator to use them for undo/redo functionality.
5. Use the caretaker to manage the history of mementos, allowing users to undo and redo changes as needed.

Pros and Cons:
+ Provides a way to capture and restore an object's state without exposing its internal structure.
+ Simplifies the implementation of undo/redo functionality in applications.
+ Maintains the integrity of an object's state while allowing for state changes.
- Can introduce additional complexity by adding more classes (memento and caretaker).
- May lead to increased memory usage if many mementos are stored.
- Can make the code harder to understand if not implemented carefully, especially if the memento
    contains complex state.
- May require careful management of memento lifetimes to avoid memory leaks or excessive memory usage.
- Can lead to a proliferation of memento objects if the state changes frequently.
- May not be suitable for all types of objects, especially those with complex or large states.

Real-world use cases:
- In text editors, the Memento pattern is often used to implement undo/redo functionality,
    allowing users to revert to previous versions of their documents.
- In graphic design software, the Memento pattern can be used to capture the state of a design
    at different points in time, allowing users to experiment with changes and revert if needed.
- In games, the Memento pattern can be used to save the state of a game at specific checkpoints,
    allowing players to resume from those points if they fail or want to try different strategies.
- In database management systems, the Memento pattern can be used to implement transaction
    rollback functionality, allowing users to revert to a previous state of the database if an
    error occurs during a transaction.
- In configuration management systems, the Memento pattern can be used to save and restore
    different configurations of a system, allowing users to switch between them easily.
"""

# Link: https://refactoring.guru/design-patterns/memento


from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class ShapeMemento:
    x: int
    y: int
    color: str
    vertices: List[Tuple[int, int]]


@dataclass
class Shape:
    x: int
    y: int
    color: str
    vertices: List[Tuple[int, int]] = field(default_factory=list)

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def change_color(self, new_color: str):
        self.color = new_color

    def add_vertex(self, x: int, y: int):
        self.vertices.append((x, y))

    def save(self) -> ShapeMemento:
        return ShapeMemento(
            x=self.x, y=self.y, color=self.color, vertices=deepcopy(self.vertices)
        )

    def restore(self, memento: ShapeMemento):
        self.x = memento.x
        self.y = memento.y
        self.color = memento.color
        self.vertices = deepcopy(memento.vertices)

    def __str__(self):
        return f"Shape(x={self.x}, y={self.y}, color={self.color}, vertices={self.vertices})"


class History:
    def __init__(self):
        self._mementos: List[ShapeMemento] = []
        self._current_index = -1

    def save(self, memento: ShapeMemento):
        # Discard any mementos after the current index
        self._mementos = self._mementos[: self._current_index + 1]
        self._mementos.append(memento)
        self._current_index += 1

    def undo(self) -> ShapeMemento | None:
        if self._current_index <= 0:
            return None
        self._current_index -= 1
        return self._mementos[self._current_index]

    def redo(self) -> ShapeMemento | None:
        if self._current_index + 1 >= len(self._mementos):
            return None
        self._current_index += 1
        return self._mementos[self._current_index]


if __name__ == "__main__":
    shape = Shape(x=10, y=10, color="blue", vertices=[(0, 0), (5, 5)])
    history = History()

    print(f"Initial State: {shape}")
    history.save(shape.save())

    shape.move(5, -5)
    shape.change_color("red")
    print(f"After move/color: {shape}")
    history.save(shape.save())

    shape.add_vertex(10, 10)
    print(f"After adding vertex: {shape}")
    history.save(shape.save())

    # --- Perform Undo ---
    undo_memento = history.undo()
    if undo_memento:
        shape.restore(undo_memento)

    print(f"After Undo: {shape}")  # Should be red, at (15, 5)

    # --- Perform another Undo ---
    undo_memento = history.undo()
    if undo_memento:
        shape.restore(undo_memento)

    print(f"After Second Undo: {shape}")  # Should be blue, at (10, 10)
