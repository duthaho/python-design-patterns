"""
Intent:
Compose objects into tree structures to represent part-whole hierarchies. Composite lets clients
treat individual objects and compositions of objects uniformly.

Problem:
Imagine you’re building a file system application that needs to represent both files and
directories. A directory can contain both files and other directories, creating a hierarchical
structure. If you treat files and directories as separate entities, your code can become complex
and hard to manage, especially when performing operations like calculating the total size of a
directory or printing the structure.

Solution:
The Composite pattern suggests that you create a common interface for both files and directories.
This interface defines operations that can be performed on both individual objects (files) and
composite objects (directories). The composite objects can contain a collection of child components,
which can be either files or other directories. This way, you can treat both files and directories
uniformly, simplifying your code and making it easier to manage hierarchical structures.

When to use:
- When you need to represent part-whole hierarchies of objects.
- When you want to treat individual objects and compositions of objects uniformly.
- When you want to simplify client code that deals with complex tree structures.

How to implement:
1. Define a common interface or abstract class for both leaf and composite components, declaring
    methods for operations that can be performed on both.
2. Implement leaf classes that represent individual objects (e.g., File) and implement the common
    interface.
3. Implement composite classes that represent collections of objects (e.g., Directory) and implement
    the common interface. These classes should maintain a collection of child components and
    implement methods to add, remove, and access these children.
4. In the composite classes, implement the operations defined in the common interface by
    delegating the work to their child components.
5. Use the common interface in your client code to interact with both leaf and composite objects
    uniformly.

Pros and Cons:
+ Simplifies client code by allowing it to treat individual objects and compositions uniformly.
+ Makes it easier to add new types of components (both leaf and composite) without changing
    existing code.
+ Promotes the Single Responsibility Principle by separating concerns between leaf and composite
    components.
- Can introduce additional complexity and indirection in the codebase.
- May lead to a proliferation of classes if not managed carefully.
- Can be overkill for simple scenarios where a flat structure is sufficient.

Real-world use cases:
- In graphical user interfaces, the Composite pattern is often used to represent UI components
    like buttons, panels, and windows, where a panel can contain other components.
- In document editors, the Composite pattern can be used to represent elements like paragraphs,
    images, and tables, where a document can contain multiple elements.
- In file systems, the Composite pattern can be used to represent files and directories, where
    a directory can contain both files and other directories.
"""

# Link: https://refactoring.guru/design-patterns/composite


from abc import ABC, abstractmethod


class FileSystemComponent(ABC):
    @abstractmethod
    def display(self, indent: int = 0) -> None:
        pass


class File(FileSystemComponent):
    def __init__(self, name: str, size: int) -> None:
        self.name = name
        self.size = size

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"File: {self.name} ({self.size} KB)")


class Directory(FileSystemComponent):
    def __init__(self, name: str) -> None:
        self.name = name
        self.children: list[FileSystemComponent] = []

    def add(self, component: FileSystemComponent) -> None:
        self.children.append(component)

    def remove(self, component: FileSystemComponent) -> None:
        self.children.remove(component)

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"Directory: {self.name}")
        for child in self.children:
            child.display(indent + 2)


if __name__ == "__main__":
    root = Directory("root")
    file1 = File("file1.txt", 10)
    file2 = File("file2.txt", 20)
    sub_dir = Directory("sub_dir")
    file3 = File("file3.txt", 30)

    root.add(file1)
    root.add(file2)
    sub_dir.add(file3)
    root.add(sub_dir)

    root.display()
