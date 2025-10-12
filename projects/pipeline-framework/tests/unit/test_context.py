"""Unit tests for PipelineContext."""

from pipeline_framework.core.context import PipelineContext


class TestPipelineContext:
    """Test suite for PipelineContext."""

    def test_context_initialization_empty(self):
        """Test creating an empty context."""
        context = PipelineContext()
        assert context.get_all() == {}

    def test_context_initialization_with_data(self):
        """Test creating a context with initial data."""
        initial_data = {"key1": "value1", "key2": 42}
        context = PipelineContext(initial_data)

        assert context.get("key1") == "value1"
        assert context.get("key2") == 42
        assert context.get_all() == initial_data

    def test_context_initialization_with_none(self):
        """Test creating context with None initializer."""
        context = PipelineContext(None)
        assert context.get_all() == {}

    def test_set_and_get(self):
        """Test setting and getting values."""
        context = PipelineContext()

        context.set("name", "Alice")
        context.set("age", 30)

        assert context.get("name") == "Alice"
        assert context.get("age") == 30

    def test_set_various_types(self):
        """Test setting different data types."""
        context = PipelineContext()

        context.set("string", "hello")
        context.set("integer", 42)
        context.set("float", 3.14)
        context.set("list", [1, 2, 3])
        context.set("dict", {"nested": "value"})
        context.set("bool", True)
        context.set("none", None)

        assert context.get("string") == "hello"
        assert context.get("integer") == 42
        assert context.get("float") == 3.14
        assert context.get("list") == [1, 2, 3]
        assert context.get("dict") == {"nested": "value"}
        assert context.get("bool") is True
        assert context.get("none") is None

    def test_get_with_default(self):
        """Test getting a non-existent key returns default."""
        context = PipelineContext()

        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default_value") == "default_value"
        assert context.get("nonexistent", 42) == 42

    def test_get_existing_key_ignores_default(self):
        """Test that get returns stored value even when default is provided."""
        context = PipelineContext({"key": "stored_value"})

        assert context.get("key", "default") == "stored_value"

    def test_has_key(self):
        """Test checking if a key exists."""
        context = PipelineContext({"existing": "value"})

        assert context.has("existing") is True
        assert context.has("nonexistent") is False

    def test_has_key_with_none_value(self):
        """Test that has() returns True even if value is None."""
        context = PipelineContext()
        context.set("key_with_none", None)

        assert context.has("key_with_none") is True
        assert context.get("key_with_none") is None

    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy, not the original."""
        context = PipelineContext({"original": "value"})

        # Get all data
        all_data = context.get_all()

        # Modify the returned dict
        all_data["original"] = "modified"
        all_data["new_key"] = "new_value"

        # Original context should be unchanged
        assert context.get("original") == "value"
        assert context.has("new_key") is False

    def test_get_all_returns_current_state(self):
        """Test that get_all returns the current state of the context."""
        context = PipelineContext({"initial": "data"})

        context.set("added", "value")
        all_data = context.get_all()

        assert "initial" in all_data
        assert "added" in all_data
        assert all_data == {"initial": "data", "added": "value"}

    def test_overwrite_existing_key(self):
        """Test that setting an existing key overwrites it."""
        context = PipelineContext()

        context.set("key", "first_value")
        assert context.get("key") == "first_value"

        context.set("key", "second_value")
        assert context.get("key") == "second_value"

    def test_multiple_operations(self):
        """Test multiple operations in sequence."""
        context = PipelineContext({"initial": 100})

        context.set("a", 1)
        context.set("b", 2)
        context.set("c", 3)

        assert context.has("initial")
        assert context.has("a")
        assert context.get("b") == 2

        context.set("a", 10)  # Overwrite
        assert context.get("a") == 10

        all_data = context.get_all()
        assert len(all_data) == 4

    def test_context_initialization_copies_data(self):
        """Test that initial_data is copied, not referenced."""
        original = {"key": "value"}
        context = PipelineContext(original)
        
        # Modify original
        original["key"] = "modified"
        
        # Context should be unaffected
        assert context.get("key") == "value"  # Would FAIL with your code
