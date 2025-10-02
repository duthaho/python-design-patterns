import json
import tempfile
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class _TextMemento:
    text: str
    cursor: int


class TextBuffer:
    def __init__(self, text: str = "") -> None:
        self._text = text
        self._cursor = len(text)

    def insert(self, s: str) -> None:
        # Insert at cursor
        before = self._text[: self._cursor]
        after = self._text[self._cursor :]
        self._text = before + s + after
        self._cursor += len(s)

    def delete(self, n: int) -> None:
        # Delete n chars before cursor
        n = max(0, min(n, self._cursor))
        before = self._text[: self._cursor - n]
        after = self._text[self._cursor :]
        self._text = before + after
        self._cursor -= n

    def move_cursor(self, pos: int) -> None:
        self._cursor = max(0, min(pos, len(self._text)))

    def save(self) -> _TextMemento:
        return _TextMemento(text=self._text, cursor=self._cursor)

    def restore(self, m: _TextMemento) -> None:
        self._text = m.text
        self._cursor = m.cursor

    def get_state(self) -> tuple[str, int]:
        return self._text, self._cursor


class EditorHistory:
    def __init__(self, capacity: int = 50) -> None:
        self._undo: list[_TextMemento] = []
        self._redo: list[_TextMemento] = []
        self._capacity = capacity

    def checkpoint(self, m: _TextMemento) -> None:
        self._undo.append(m)
        if len(self._undo) > self._capacity:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self) -> _TextMemento | None:
        if not self._undo:
            return None
        m = self._undo.pop()
        self._redo.append(m)
        return m

    def redo(self) -> _TextMemento | None:
        if not self._redo:
            return None
        m = self._redo.pop()
        self._undo.append(m)
        return m


@dataclass(frozen=True)
class _DiffMemento:
    # Represent a single edit operation for reversible application
    kind: str  # "insert" | "delete" | "cursor"
    pos: int  # position of operation
    text: str = ""  # inserted text (if any)
    length: int = 0  # deleted length (if any)
    prev_cursor: int = 0  # previous cursor for cursor moves
    next_cursor: int = 0  # next cursor for cursor moves


class TextBufferWithDiffs(TextBuffer):
    def apply_memento(self, m: _DiffMemento, reverse: bool = False) -> None:
        # Apply forward or reverse change based on `reverse`
        if m.kind == "insert":
            if reverse:
                self.move_cursor(m.pos + len(m.text))
                self.delete(len(m.text))
            else:
                self.move_cursor(m.pos)
                self.insert(m.text)
        elif m.kind == "delete":
            if reverse:
                self.move_cursor(m.pos)
                self.insert(m.text)  # text is the deleted segment
            else:
                self.move_cursor(m.pos + m.length)
                # Capture deleted text to store in memento externally
                self.delete(m.length)
        elif m.kind == "cursor":
            self.move_cursor(m.prev_cursor if reverse else m.next_cursor)


class SnapshotStore:
    def __init__(self, path: str) -> None:
        self._path = path

    def save(self, mementos: list[_DiffMemento]) -> None:
        payload = [asdict(m) for m in mementos]
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def load(self) -> list[_DiffMemento]:
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_DiffMemento(**item) for item in data]


def demonstrate_text_buffer():
    buffer = TextBufferWithDiffs("Hello World")
    history = EditorHistory()
    store = SnapshotStore(tempfile.gettempdir() + "/text_buffer_snapshot.json")

    print("Initial State:", buffer.get_state())
    history.checkpoint(buffer.save())

    # Insert " Beautiful"
    pos = 5
    text_to_insert = " Beautiful"
    buffer.move_cursor(pos)
    buffer.insert(text_to_insert)
    m_insert = _DiffMemento(kind="insert", pos=pos, text=text_to_insert)
    history.checkpoint(buffer.save())
    print("After Insert:", buffer.get_state())

    # Delete "World"
    pos = 16
    length_to_delete = 5
    buffer.move_cursor(pos + length_to_delete)
    deleted_text = buffer._text[pos : pos + length_to_delete]
    buffer.delete(length_to_delete)
    m_delete = _DiffMemento(
        kind="delete", pos=pos, text=deleted_text, length=length_to_delete
    )
    history.checkpoint(buffer.save())
    print("After Delete:", buffer.get_state())

    # Move cursor to start
    prev_cursor = buffer._cursor
    new_cursor = 0
    buffer.move_cursor(new_cursor)
    m_cursor = _DiffMemento(
        kind="cursor", pos=new_cursor, prev_cursor=prev_cursor, next_cursor=new_cursor
    )
    history.checkpoint(buffer.save())
    print("After Move Cursor:", buffer.get_state())

    # Undo operations
    for _ in range(3):
        m = history.undo()
        if m:
            buffer.restore(m)
            print("After Undo:", buffer.get_state())

    # Redo operations
    for _ in range(3):
        m = history.redo()
        if m:
            buffer.restore(m)
            print("After Redo:", buffer.get_state())

    # Save snapshot
    store.save([m_insert, m_delete, m_cursor])
    print(f"Snapshot saved to {store._path}")

    # Load snapshot and apply changes to a new buffer
    new_buffer = TextBufferWithDiffs("Hello World")
    loaded_mementos = store.load()
    for m in loaded_mementos:
        new_buffer.apply_memento(m)
        print("New Buffer After Applying Memento:", new_buffer.get_state())


if __name__ == "__main__":
    demonstrate_text_buffer()
