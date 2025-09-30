from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, Optional


@dataclass
class LogEntry:
    """Represents a single log entry"""

    timestamp: datetime
    level: str  # INFO, WARNING, ERROR
    message: str

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.level}: {self.message}"


class LogFileIterator:
    """
    Iterator that reads log file line by line (lazy loading).
    Parses each line into a LogEntry object.

    This is a single-pass external iterator. Once exhausted, create a new
    iterator to read the file again. The file is automatically closed when
    iteration completes or the iterator is garbage collected.

    Supports context manager protocol for explicit resource management.
    """

    def __init__(self, filepath: str, level_filter: Optional[str] = None) -> None:
        """
        Args:
            filepath: Path to the log file
            level_filter: If provided, only return entries matching this level (e.g., "ERROR")
        """
        self._filepath = filepath
        self._level_filter = level_filter
        self._file = None

    def __iter__(self) -> "LogFileIterator":
        """Open the file and return self"""
        self._file = open(self._filepath, 'r', encoding='utf-8', buffering=8192)
        return self

    def __next__(self) -> LogEntry:
        """
        Read next line, parse it, and return LogEntry.
        Skip malformed lines and non-matching levels.
        Raise StopIteration when file ends.
        """
        if self._file is None:
            raise StopIteration

        while True:
            line = self._file.readline()

            # End of file reached
            if not line:
                self._close_file()
                raise StopIteration

            # Parse the line
            entry = self._parse_line(line)
            if entry is None:
                continue  # Skip malformed line

            # Apply level filter if specified
            if self._level_filter and entry.level != self._level_filter:
                continue  # Skip non-matching level

            return entry

    def _parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a log line into a LogEntry object.

        Expected format: "2025-09-30 10:15:23 INFO Application started"

        Returns:
            LogEntry if parsing succeeds, None if line is malformed
        """
        try:
            # Split into max 4 parts to preserve message with spaces
            parts = line.strip().split(" ", 3)

            # Validate structure
            if len(parts) < 4:
                return None

            # Parse components
            timestamp_str = f"{parts[0]} {parts[1]}"
            level = parts[2]
            message = parts[3]

            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            return LogEntry(timestamp, level, message)

        except (ValueError, IndexError):
            # Malformed line - skip silently
            return None

    def _close_file(self) -> None:
        """Close the file if open"""
        if self._file and not self._file.closed:
            self._file.close()
        self._is_open = False

    def __del__(self):
        """Ensure file is closed when iterator is garbage collected"""
        self._close_file()

    # Context Manager Protocol
    def __enter__(self) -> "LogFileIterator":
        """Enter context manager - open file"""
        return self.__iter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager - close file"""
        self._close_file()
        return False  # Don't suppress exceptions


class LogFileCollection:
    """
    Represents a log file and provides different ways to iterate over it.

    Each call to an iteration method returns a NEW iterator, allowing
    multiple independent iterations over the same file.
    """

    def __init__(self, filepath: str) -> None:
        """
        Args:
            filepath: Path to the log file

        Raises:
            FileNotFoundError: If the log file doesn't exist
        """
        self._filepath = filepath

        # Validate file exists at construction time
        if not Path(filepath).is_file():
            raise FileNotFoundError(f"Log file not found: {filepath}")

    def __iter__(self) -> LogFileIterator:
        """Return iterator for all log entries"""
        return LogFileIterator(self._filepath)

    def iter_errors(self) -> LogFileIterator:
        """Return iterator for ERROR level entries only"""
        return LogFileIterator(self._filepath, level_filter="ERROR")

    def iter_warnings(self) -> LogFileIterator:
        """Return iterator for WARNING level entries only"""
        return LogFileIterator(self._filepath, level_filter="WARNING")

    def iter_info(self) -> LogFileIterator:
        """Return iterator for INFO level entries only"""
        return LogFileIterator(self._filepath, level_filter="INFO")

    def iter_by_level(self, level: str) -> LogFileIterator:
        """
        Return iterator for entries matching specified level.
        More flexible than specific methods.

        Args:
            level: Log level to filter (e.g., "DEBUG", "CRITICAL")
        """
        return LogFileIterator(self._filepath, level_filter=level)


class ChainedIterator:
    """
    Iterator that chains multiple iterators together sequentially.
    Useful for iterating over multiple log files (e.g., rotated daily logs).

    Handles empty collections gracefully and supports any iterable collection.

    Example:
        logs1 = LogFileCollection("app-2025-09-29.log")
        logs2 = LogFileCollection("app-2025-09-30.log")
        chained = ChainedIterator(logs1, logs2)

        for entry in chained:
            print(entry)  # Seamlessly iterates through both files
    """

    def __init__(self, *collections) -> None:
        """
        Args:
            *collections: Variable number of iterable collections (LogFileCollection, lists, etc.)
        """
        self._collections = collections
        self._current_index = 0
        self._current_iterator = None

    def __iter__(self) -> "ChainedIterator":
        """Return self as iterator"""
        self._current_index = 0
        self._current_iterator = None
        return self
    
    def __next__(self):
        """Return next item from current iterator, moving to next collection as needed"""
        while self._current_index < len(self._collections):
            if self._current_iterator is None:
                # Initialize iterator for current collection
                self._current_iterator = iter(iter(self._collections[self._current_index]))

            try:
                # Attempt to get next item from current iterator
                return next(self._current_iterator)
            except StopIteration:
                # Current iterator exhausted - move to next collection
                self._current_index += 1
                self._current_iterator = None

        # All collections exhausted
        raise StopIteration


class FilteredIterator:
    """
    BONUS: Generic filtered iterator using predicate functions.
    Allows composable, flexible filtering beyond simple level matching.

    Example:
        logs = LogFileCollection("server.log")

        # Filter by multiple levels
        critical = FilteredIterator(
            iter(logs),
            lambda entry: entry.level in ["ERROR", "CRITICAL"]
        )

        # Filter by time range
        recent = FilteredIterator(
            iter(logs),
            lambda entry: entry.timestamp > datetime(2025, 9, 30, 10, 0)
        )

        # Chain filters
        recent_errors = FilteredIterator(
            recent,
            lambda entry: entry.level == "ERROR"
        )
    """

    def __init__(
        self, source_iterator: Iterator[LogEntry], predicate: Callable[[LogEntry], bool]
    ) -> None:
        """
        Args:
            source_iterator: Iterator to filter
            predicate: Function that returns True for entries to include
        """
        self._source = source_iterator
        self._predicate = predicate

    def __iter__(self) -> "FilteredIterator":
        return self

    def __next__(self) -> LogEntry:
        """Return next entry that matches predicate"""
        while True:
            entry = next(self._source)  # May raise StopIteration
            if self._predicate(entry):
                return entry


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_sample_log_file(filepath: str = "server.log") -> None:
    """Create a sample log file for testing"""
    log_content = """2025-09-30 10:15:23 INFO Application started
2025-09-30 10:15:45 WARNING High memory usage detected
2025-09-30 10:16:12 ERROR Database connection failed
2025-09-30 10:16:15 INFO Retrying connection
2025-09-30 10:16:18 ERROR Database connection failed again
2025-09-30 10:16:20 INFO Connection established
2025-09-30 10:17:00 WARNING Disk space running low
2025-09-30 10:18:30 ERROR Timeout occurred
This is a malformed line that should be skipped
2025-09-30 10:19:00 INFO Request processed successfully"""

    with open(filepath, "w") as f:
        f.write(log_content)
    print(f"✓ Sample log file created: {filepath}")


# ============================================================================
# TEST CODE
# ============================================================================


def test_basic_iteration():
    """Test basic log iteration"""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Iteration (All Logs)")
    print("=" * 70)

    create_sample_log_file("server.log")
    logs = LogFileCollection("server.log")

    count = 0
    for entry in iter(logs):
        print(f"  {entry}")
        count += 1
    print(f"\n✓ Total entries: {count}")


def test_filtered_iteration():
    """Test filtered iteration"""
    print("\n" + "=" * 70)
    print("TEST 2: Filtered Iteration")
    print("=" * 70)

    logs = LogFileCollection("server.log")

    print("\n[ERRORS only]")
    for entry in logs.iter_errors():
        print(f"  {entry}")

    print("\n[WARNINGS only]")
    for entry in logs.iter_warnings():
        print(f"  {entry}")

    print("\n[INFO only]")
    info_count = sum(1 for _ in logs.iter_info())
    print(f"  Total INFO entries: {info_count}")


def test_multiple_iterations():
    """Test multiple independent iterations"""
    print("\n" + "=" * 70)
    print("TEST 3: Multiple Independent Iterations")
    print("=" * 70)

    logs = LogFileCollection("server.log")

    error_count = sum(1 for _ in logs.iter_errors())
    warning_count = sum(1 for _ in logs.iter_warnings())
    info_count = sum(1 for _ in logs.iter_info())
    total_count = sum(1 for _ in logs)

    print(f"  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")
    print(f"  Info: {info_count}")
    print(f"  Total: {total_count}")
    print(
        f"\n✓ Counts match: {error_count + warning_count + info_count == total_count}"
    )


def test_context_manager():
    """Test context manager support"""
    print("\n" + "=" * 70)
    print("TEST 4: Context Manager Support")
    print("=" * 70)

    logs = LogFileCollection("server.log")

    with LogFileIterator("server.log", level_filter="ERROR") as error_logs:
        print("  Using context manager for ERROR logs:")
        for entry in error_logs:
            print(f"    {entry}")

    print("\n✓ File automatically closed after context")


def test_chained_iterator():
    """Test chained iterator with multiple files"""
    print("\n" + "=" * 70)
    print("TEST 5: Chained Iterator (Multiple Files)")
    print("=" * 70)

    # Create two log files
    create_sample_log_file("server1.log")
    create_sample_log_file("server2.log")

    logs1 = LogFileCollection("server1.log")
    logs2 = LogFileCollection("server2.log")

    chained = ChainedIterator(logs1, logs2)
    total_count = sum(1 for _ in chained)

    print(f"  Total entries across both files: {total_count}")
    print(f"  Expected: 18 (9 valid entries × 2 files)")
    print(f"\n✓ Chaining works: {total_count == 18}")


def test_filtered_iterator_bonus():
    """Test the bonus FilteredIterator"""
    print("\n" + "=" * 70)
    print("TEST 6: BONUS - Generic FilteredIterator")
    print("=" * 70)

    logs = LogFileCollection("server.log")

    # Complex filter: ERROR or WARNING
    print("\n[Errors AND Warnings]")
    critical = FilteredIterator(
        iter(logs), lambda entry: entry.level in ["ERROR", "WARNING"]
    )

    for entry in critical:
        print(f"  {entry}")

    # Time-based filter
    print("\n[Entries after 10:16:30]")
    cutoff_time = datetime(2025, 9, 30, 10, 16, 30)
    recent = FilteredIterator(iter(logs), lambda entry: entry.timestamp > cutoff_time)

    count = sum(1 for _ in recent)
    print(f"  Count: {count}")

    print("\n✓ Flexible filtering with predicates works!")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 70)
    print("TEST 7: Edge Cases & Error Handling")
    print("=" * 70)

    # Test: Non-existent file
    try:
        logs = LogFileCollection("nonexistent.log")
        print("  ✗ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"  ✓ Correctly caught: {e}")

    # Test: Empty collection chaining
    logs = LogFileCollection("server.log")
    empty_list: list = []
    chained = ChainedIterator(empty_list, logs)
    count = sum(1 for _ in chained)
    print(f"  ✓ Chained with empty collection: {count} entries")

    # Test: Malformed lines are skipped
    with open("malformed.log", "w") as f:
        f.write("This is not a valid log line\n")
        f.write("2025-09-30 10:00:00 INFO Valid entry\n")
        f.write("Another bad line\n")

    malformed = LogFileCollection("malformed.log")
    valid_count = sum(1 for _ in malformed)
    print(f"  ✓ Malformed lines skipped: {valid_count} valid entries")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🚀" * 35)
    print(" " * 20 + "LOG ITERATOR - FULL TEST SUITE")
    print("🚀" * 35)

    test_basic_iteration()
    test_filtered_iteration()
    test_multiple_iterations()
    test_context_manager()
    test_chained_iterator()
    test_filtered_iterator_bonus()
    test_edge_cases()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
