from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class _ConfigMemento:
    """
    TODO: Store configuration state
    Hint: You'll need to store the entire configuration dictionary
    Remember: Make it immutable and encapsulated!
    """

    state: Dict[str, Any]

    def get_state(self) -> Dict[str, Any]:
        """
        Returns a deep copy of the stored state to prevent external modification.
        """
        return deepcopy(self.state)


class ConfigManager:
    """
    Manages application configuration with snapshot capabilities.

    TODO: Implement the following:
    1. Store configuration as a nested dictionary
    2. Provide methods to get/set config values using dot notation
    3. Create mementos for saving state
    4. Restore from mementos
    5. Validate configuration before creating snapshots
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Example: set("database.host", "localhost")
        This should create: {"database": {"host": "localhost"}}

        Args:
            key: Dot-separated path (e.g., "database.host")
            value: Configuration value
        """
        if not key:
            raise ValueError("Key cannot be empty")

        keys = [k for k in key.split(".") if k]
        if not keys:
            raise ValueError("Key cannot be empty or just dots")

        d = self._config
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Dot-separated path
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        if not key:
            return default

        keys = [k for k in key.split(".") if k]
        if not keys:
            return default

        d = self._config
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return default
        return d

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.

        Returns:
            Copy of the configuration
        """
        return deepcopy(self._config)

    def validate(self) -> bool:
        """
        Validate the current configuration.

        Rules to implement:
        - If "database.port" exists, it must be an integer between 1 and 65535
        - If "database.host" exists, it must be a non-empty string
        - If "cache.ttl" exists, it must be a positive integer

        Returns:
            True if valid, False otherwise
        """
        db_port = self.get("database.port")
        if db_port is not None:
            if not (isinstance(db_port, int) and 1 <= db_port <= 65535):
                return False

        db_host = self.get("database.host")
        if db_host is not None:
            if not (isinstance(db_host, str) and db_host):
                return False

        cache_ttl = self.get("cache.ttl")
        if cache_ttl is not None:
            if not (isinstance(cache_ttl, int) and cache_ttl > 0):
                return False

        return True

    def save(self) -> _ConfigMemento:
        """
        Create a memento of current configuration.

        Returns:
            Memento containing configuration snapshot
        """
        if not self.validate():
            raise ValueError("Cannot save invalid configuration")

        return _ConfigMemento(state=deepcopy(self._config))

    def restore(self, memento: _ConfigMemento) -> None:
        """
        Restore configuration from a memento.

        Args:
            memento: Previously saved configuration state
        """
        self._config = memento.get_state()


class SnapshotManager:
    """
    Manages named configuration snapshots.

    TODO: Implement the following:
    1. Store mementos with string names
    2. Save snapshots only if configuration is valid
    3. Restore snapshots by name
    4. List available snapshots
    5. Handle missing snapshots gracefully
    """

    def __init__(self) -> None:
        self._snapshots: Dict[str, _ConfigMemento] = {}

    def save_snapshot(self, config: ConfigManager, name: str) -> bool:
        """
        Save a named snapshot of the configuration.

        Args:
            config: ConfigManager instance
            name: Snapshot name (e.g., "production", "staging")

        Returns:
            True if saved successfully, False if validation failed
        """
        if not name:
            raise ValueError("Snapshot name cannot be empty")
        
        memento = config.save()
        self._snapshots[name] = memento
        return True

    def restore_snapshot(self, config: ConfigManager, name: str) -> bool:
        """
        Restore configuration from a named snapshot.

        Args:
            config: ConfigManager instance
            name: Snapshot name to restore

        Returns:
            True if restored successfully, False if snapshot doesn't exist
        """
        if not name:
            raise ValueError("Snapshot name cannot be empty")
        
        memento = self._snapshots.get(name)
        if not memento:
            return False
        config.restore(memento)
        return True

    def list_snapshots(self) -> list[str]:
        """
        Get list of available snapshot names.

        Returns:
            List of snapshot names
        """
        return list(self._snapshots.keys())

    def delete_snapshot(self, name: str) -> bool:
        """
        Delete a named snapshot.

        Args:
            name: Snapshot name to delete

        Returns:
            True if deleted, False if snapshot didn't exist
        """
        if name in self._snapshots:
            del self._snapshots[name]
            return True
        return False


if __name__ == "__main__":
    config = ConfigManager()
    snapshots = SnapshotManager()

    # Test 1: Basic set/get
    print("=== Test 1: Basic Operations ===")
    config.set("database.host", "localhost")
    config.set("database.port", 5432)
    print(f"Database host: {config.get('database.host')}")
    print(f"Database port: {config.get('database.port')}")
    print(f"All config: {config.get_all()}")

    # Test 2: Save valid snapshot
    print("\n=== Test 2: Save Valid Snapshot ===")
    success = snapshots.save_snapshot(config, "initial")
    print(f"Saved 'initial' snapshot: {success}")
    print(f"Available snapshots: {snapshots.list_snapshots()}")

    # Test 3: Modify and save another snapshot
    print("\n=== Test 3: Modify and Save ===")
    config.set("database.port", 3306)
    config.set("cache.enabled", True)
    config.set("cache.ttl", 300)
    snapshots.save_snapshot(config, "with-cache")
    print(f"Modified config: {config.get_all()}")
    print(f"Available snapshots: {snapshots.list_snapshots()}")

    # Test 4: Restore to previous snapshot
    print("\n=== Test 4: Restore Snapshot ===")
    snapshots.restore_snapshot(config, "initial")
    print(f"After restoring 'initial': {config.get_all()}")

    # Test 5: Invalid configuration
    print("\n=== Test 5: Invalid Configuration ===")
    config.set("database.port", 99999)  # Invalid port
    success = snapshots.save_snapshot(config, "invalid")
    print(f"Saved invalid config: {success}")

    # Test 6: Restore non-existent snapshot
    print("\n=== Test 6: Restore Non-existent ===")
    success = snapshots.restore_snapshot(config, "non-existent")
    print(f"Restored non-existent: {success}")

    # Test 7: Delete snapshot
    print("\n=== Test 7: Delete Snapshot ===")
    success = snapshots.delete_snapshot("with-cache")
    print(f"Deleted 'with-cache': {success}")
    print(f"Remaining snapshots: {snapshots.list_snapshots()}")
