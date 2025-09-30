from collections.abc import Iterator
from typing import Any, Callable, List


class Book:
    def __init__(self, title: str, author: str, published_year: int) -> None:
        self.title = title
        self.author = author
        self.published_year = published_year

    def __str__(self) -> str:
        return f"{self.title} by {self.author} ({self.published_year})"


class BookShelf:
    def __init__(self) -> None:
        self._books = []

    def add_book(self, book: Book) -> None:
        self._books.append(book)

    def __iter__(self) -> "BookShelfIterator":
        return BookShelfIterator(self._books)

    def iter_by_title(self, reverse: bool = False) -> "BookSortingIterator":
        return BookSortingIterator(
            self._books, key=lambda book: book.title, reverse=reverse
        )

    def iter_by_author(self, reverse: bool = False) -> "BookSortingIterator":
        return BookSortingIterator(
            self._books, key=lambda book: book.author, reverse=reverse
        )

    def iter_by_year(self, reverse: bool = False) -> "BookSortingIterator":
        return BookSortingIterator(
            self._books, key=lambda book: book.published_year, reverse=reverse
        )


class BookShelfIterator(Iterator[Book]):
    def __init__(self, books: List[Book]) -> None:
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


class BookSortingIterator(Iterator[Book]):
    def __init__(
        self, books: list[Book], key: Callable[[Book], Any], reverse: bool = False
    ) -> None:
        self._books = sorted(books.copy(), key=key, reverse=reverse)
        self._index = 0

    def __next__(self) -> Book:
        if self._index < len(self._books):
            book = self._books[self._index]
            self._index += 1
            return book
        raise StopIteration

    def __iter__(self) -> "BookSortingIterator":
        return self


def client_code(book_shelf: BookShelf) -> None:
    print("Books in insertion order:")
    for book in book_shelf:
        print(book)

    print("\nBooks sorted by title:")
    for book in book_shelf.iter_by_title():
        print(book)

    print("\nBooks sorted by author:")
    for book in book_shelf.iter_by_author():
        print(book)

    print("\nBooks sorted by published year:")
    for book in book_shelf.iter_by_year():
        print(book)


if __name__ == "__main__":
    book_shelf = BookShelf()
    book_shelf.add_book(Book("The Great Gatsby", "F. Scott Fitzgerald", 1925))
    book_shelf.add_book(Book("To Kill a Mockingbird", "Harper Lee", 1960))
    book_shelf.add_book(Book("1984", "George Orwell", 1949))
    book_shelf.add_book(Book("Pride and Prejudice", "Jane Austen", 1813))

    client_code(book_shelf)
