"""
Intent:
Iterator is a behavioral design pattern that provides a way to access the elements of a
collection (like a list or a set) sequentially without exposing the underlying representation of
the collection.

Problem:
Imagine you have a collection of items, and you want to traverse through them without exposing
the internal structure of the collection. You want to be able to iterate over the items in a
consistent way, regardless of how the collection is implemented (e.g., array, linked list, tree).
Additionally, you want to be able to support multiple types of collections and provide a uniform
way to access their elements. The Iterator pattern addresses these issues by providing a standard way to
traverse different types of collections without exposing their internal details.

Solution:
The Iterator pattern suggests creating an iterator object that encapsulates the logic for
traversing a collection. The iterator provides methods to access the elements of the collection
sequentially, such as `next()` to get the next element and `has_next()` to check if there are more
elements to iterate over. The collection itself provides a method to create an iterator, allowing
clients to obtain an iterator without needing to know the details of the collection's structure.

When to Use:
- When you want to provide a standard way to traverse different types of collections.
- When you want to decouple the traversal logic from the collection itself.
- When you want to support multiple types of collections with a uniform interface.
- When you want to allow multiple iterators to traverse the same collection independently.
- When you want to provide a way to traverse a collection without exposing its internal structure.
- When you want to implement custom traversal algorithms for specific collections.
- When you want to simplify the client code by providing a consistent way to access collection
    elements.

How to Implement:
1. Define an iterator interface with methods for traversing the collection, such as `next()` and
    `has_next()`.
2. Create concrete iterator classes that implement the iterator interface for specific types of
    collections. Each iterator should maintain a reference to the collection and track the current position
    in the traversal.
3. Define a collection interface with a method to create an iterator.
4. Create concrete collection classes that implement the collection interface. Each collection
    should provide a method to create an instance of its corresponding iterator.
5. In the client code, use the collection's method to obtain an iterator and use the iterator's
    methods to traverse the collection.
6. Optionally, implement different types of iterators for various traversal strategies (e.g.,
    depth-first, breadth-first).
7. Ensure that the iterator can handle modifications to the collection during traversal, if
    necessary.
8. Consider implementing a way to reset the iterator to the beginning of the collection, if
    needed.

Pros and Cons:
+ Provides a standard way to traverse different types of collections.
+ Decouples the traversal logic from the collection itself.
+ Supports multiple types of collections with a uniform interface.
+ Allows multiple iterators to traverse the same collection independently.
+ Simplifies client code by providing a consistent way to access collection elements.
- May introduce additional complexity with the creation of iterator classes.
- Can lead to performance overhead due to the additional layer of abstraction.
- May require careful design to ensure that the iterator and collection interfaces are
    compatible.
- Can lead to issues if the collection is modified during iteration, depending on the
    implementation.

Real-world use cases:
- Implementing custom data structures (e.g., trees, graphs) that require specific traversal
    algorithms.
- Providing a way to traverse collections in libraries or frameworks (e.g., Java's `Iterable` and
    `Iterator` interfaces).
- Implementing pagination in applications, where data is fetched and displayed in chunks.
- Creating user interfaces that allow users to navigate through lists or grids of items.
- Implementing file system traversal, where directories and files need to be accessed in a
    specific order.
- Implementing database result set traversal, where query results need to be accessed sequentially.
- Implementing composite structures, where a tree-like structure needs to be traversed in a
    specific order.
- Implementing event handling systems, where events need to be processed in a specific order.
"""

# Link: https://refactoring.guru/design-patterns/iterator


class Book:
    def __init__(self, title: str, author: str) -> None:
        self.title = title
        self.author = author

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class BookShelf:
    def __init__(self) -> None:
        self._books = []

    def add_book(self, book: Book) -> None:
        self._books.append(book)

    def __iter__(self) -> "BookShelfIterator":
        return BookShelfIterator(self._books)


class BookShelfIterator:
    def __init__(self, books: list[Book]) -> None:
        self._books = books.copy()
        self._index = 0

    def __next__(self) -> Book:
        if self._index < len(self._books):
            book = self._books[self._index]
            self._index += 1
            return book
        raise StopIteration

    def __iter__(self) -> "BookShelfIterator":
        return self


def client_code(book_shelf: BookShelf) -> None:
    for book in book_shelf:
        print(book)


if __name__ == "__main__":
    book_shelf = BookShelf()
    book_shelf.add_book(Book("The Great Gatsby", "F. Scott Fitzgerald"))
    book_shelf.add_book(Book("To Kill a Mockingbird", "Harper Lee"))
    book_shelf.add_book(Book("1984", "George Orwell"))
    book_shelf.add_book(Book("Pride and Prejudice", "Jane Austen"))

    client_code(book_shelf)
