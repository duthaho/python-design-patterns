"""
Intent:
Represent an operation to be performed on the elements of an object structure. Visitor lets you
define a new operation without changing the classes of the elements on which it operates.

Problem:
You have a complex object structure (e.g., a composite pattern) and you want to perform
different operations on the elements of this structure without changing their classes.

Solution:
Define a visitor interface with a visit method for each type of element in the object structure.
Each element class implements an accept method that takes a visitor as an argument and calls the
appropriate visit method on the visitor. This way, you can add new operations by creating new
visitor classes without modifying the element classes.

When to use:
- When you have a complex object structure and want to perform different operations on its elements.
- When you want to add new operations without changing the classes of the elements.
- When the object structure is stable, but you need to add new operations frequently.
- When you want to separate algorithms from the object structure on which they operate.

How to implement:
1. Define a visitor interface with visit methods for each type of element in the object structure.
2. Implement concrete visitor classes that define specific operations by implementing the visit
    methods.
3. Define an element interface with an accept method that takes a visitor as an argument.
4. Implement concrete element classes that implement the accept method by calling the appropriate
    visit method on the visitor.
5. Use the visitor by creating an instance of a concrete visitor and passing it to the accept
    method of the elements in the object structure.

Pros and Cons:
+ Allows you to add new operations without changing the classes of the elements.
+ Promotes the Single Responsibility Principle by separating algorithms from the object structure.
+ Makes it easy to add new operations by creating new visitor classes.
- Can lead to a proliferation of visitor classes if not managed carefully.
- Can make the code more complex and harder to understand due to the indirection introduced by
    the visitor pattern.
- Requires all element classes to implement the accept method, which can be cumbersome if there
    are many element types.

Real-world use cases:
- Compilers often use the Visitor pattern to perform operations on abstract syntax trees (ASTs),
    such as type checking, code generation, and optimization.
- In document processing systems, the Visitor pattern can be used to perform operations on
    different types of document elements (e.g., text, images, tables) without changing their
    classes.
- In graphics applications, the Visitor pattern can be used to perform operations on different
    types of shapes (e.g., circles, rectangles, polygons) without changing their classes.
"""

# Link: https://refactoring.guru/design-patterns/visitor

from abc import ABC, abstractmethod


class DocumentElement(ABC):
    @abstractmethod
    def accept(self, visitor: "DocumentVisitor") -> None:
        pass


class Paragraph(DocumentElement):
    def __init__(self, text: str) -> None:
        self.text = text

    def accept(self, visitor: "DocumentVisitor") -> None:
        visitor.visit_paragraph(self)


class Heading(DocumentElement):
    def __init__(self, text: str, level: int) -> None:
        self.text = text
        self.level = level

    def accept(self, visitor: "DocumentVisitor") -> None:
        visitor.visit_heading(self)


class Section(DocumentElement):
    def __init__(self, heading: Heading, elements: list[DocumentElement]) -> None:
        self.heading = heading
        self.elements = elements

    def accept(self, visitor: "DocumentVisitor") -> None:
        visitor.visit_section(self)


class DocumentVisitor(ABC):
    @abstractmethod
    def visit_paragraph(self, paragraph: Paragraph) -> None:
        pass

    @abstractmethod
    def visit_heading(self, heading: Heading) -> None:
        pass

    @abstractmethod
    def visit_section(self, section: Section) -> None:
        pass


class TableOfContentsVisitor(DocumentVisitor):
    def __init__(self) -> None:
        self.toc = []

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        pass  # Paragraphs are not included in the TOC

    def visit_heading(self, heading: Heading) -> None:
        self.toc.append((heading.level, heading.text))

    def visit_section(self, section: Section) -> None:
        section.heading.accept(self)
        for element in section.elements:
            element.accept(self)

    def get_toc(self) -> str:
        result = "Table of Contents:\n"
        for level, text in self.toc:
            result += "  " * (level - 1) + f"- {text}\n"
        return result


if __name__ == "__main__":
    doc = Section(
        Heading("Document Title", 1),
        [
            Paragraph("This is the introduction."),
            Section(
                Heading("Chapter 1", 2),
                [
                    Paragraph("This is the first chapter."),
                    Section(
                        Heading("Section 1.1", 3),
                        [Paragraph("This is section 1.1.")],
                    ),
                ],
            ),
            Section(
                Heading("Chapter 2", 2),
                [Paragraph("This is the second chapter.")],
            ),
        ],
    )

    toc_visitor = TableOfContentsVisitor()
    doc.accept(toc_visitor)
    print(toc_visitor.get_toc())
