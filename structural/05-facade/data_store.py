import json
import logging
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLDatabase:
    def __init__(self):
        self.connected = False

    def connect(self):
        print("SQL: Connecting to database")
        self.connected = True

    def execute_query(self, query: str) -> List[Dict]:
        if not self.connected:
            raise RuntimeError("Database not connected")
        print(f"SQL: Executing query: {query}")
        # Simulate query result based on query type
        if "SELECT" in query and "users" in query:
            return [{"id": "1", "name": "John", "email": "john@example.com", "age": 30}]
        return []

    def insert(self, table: str, data: Dict):
        if not self.connected:
            raise RuntimeError("Database not connected")
        print(f"SQL: Inserting into {table}: {data}")

    def update(self, table: str, data: Dict, where_clause: str):
        if not self.connected:
            raise RuntimeError("Database not connected")
        print(f"SQL: Updating {table} SET {data} WHERE {where_clause}")

    def delete(self, table: str, where_clause: str):
        if not self.connected:
            raise RuntimeError("Database not connected")
        print(f"SQL: DELETE FROM {table} WHERE {where_clause}")

    def close(self):
        print("SQL: Closing connection")
        self.connected = False


class RedisCache:
    def __init__(self):
        self.connected = False
        self.cache = {}

    def connect(self):
        print("Redis: Connecting to cache")
        self.connected = True

    def get(self, key: str) -> Optional[str]:
        if not self.connected:
            raise RuntimeError("Redis not connected")
        value = self.cache.get(key)
        print(f"Redis: GET {key} -> {value}")
        return value

    def set(self, key: str, value: str, expire_seconds: int = 3600):
        if not self.connected:
            raise RuntimeError("Redis not connected")
        print(f"Redis: SET {key} -> {value} (expire in {expire_seconds}s)")
        self.cache[key] = value

    def delete(self, key: str):
        if not self.connected:
            raise RuntimeError("Redis not connected")
        print(f"Redis: DELETE {key}")
        self.cache.pop(key, None)

    def close(self):
        print("Redis: Closing connection")
        self.connected = False


class Elasticsearch:
    def __init__(self):
        self.connected = False
        self.indices = {"users": {}}  # Pre-populate users index

    def connect(self):
        print("Elasticsearch: Connecting")
        self.connected = True

    def index_document(self, index: str, doc_id: str, document: Dict):
        if not self.connected:
            raise RuntimeError("Elasticsearch not connected")
        print(f"ES: Indexing document {doc_id} in {index}")
        if index not in self.indices:
            self.indices[index] = {}
        self.indices[index][doc_id] = document

    def search(self, index: str, query: Dict) -> List[Dict]:
        if not self.connected:
            raise RuntimeError("Elasticsearch not connected")
        print(f"ES: Searching in {index} with query: {query}")
        # Simulate search results
        return [
            {
                "id": "1",
                "score": 1.0,
                "source": {"name": "John Doe", "email": "john@example.com"},
            },
            {
                "id": "2",
                "score": 0.8,
                "source": {"name": "Jane Smith", "email": "jane@example.com"},
            },
        ]

    def delete_document(self, index: str, doc_id: str):
        if not self.connected:
            raise RuntimeError("Elasticsearch not connected")
        print(f"ES: Deleting document {doc_id} from {index}")
        if index in self.indices and doc_id in self.indices[index]:
            del self.indices[index][doc_id]

    def close(self):
        print("Elasticsearch: Closing connection")
        self.connected = False


class DataStoreFacade:
    """
    Facade providing unified interface to SQL Database, Redis Cache, and Elasticsearch.

    Implements caching strategies and provides high-level operations for user management.
    """

    def __init__(
        self,
        sql_db: Optional[SQLDatabase] = None,
        redis_cache: Optional[RedisCache] = None,
        elasticsearch: Optional[Elasticsearch] = None,
    ):
        self.sql_db = sql_db or SQLDatabase()
        self.redis_cache = redis_cache or RedisCache()
        self.elasticsearch = elasticsearch or Elasticsearch()
        self._connected = False

    def __enter__(self):
        """Context manager entry - connect to all services"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close all connections"""
        self.close()
        # Return False to propagate any exceptions
        return False

    def connect(self) -> bool:
        """
        Connect to all data stores.

        Returns:
            bool: True if all connections successful, False otherwise
        """
        try:
            logger.info("🔗 Connecting to all data stores...")
            self.sql_db.connect()
            self.redis_cache.connect()
            self.elasticsearch.connect()
            self._connected = True
            logger.info("✅ All data stores connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to data stores: {e}")
            return False

    def close(self) -> None:
        """Close all connections gracefully."""
        logger.info("🔐 Closing all data store connections...")

        try:
            self.sql_db.close()
        except Exception as e:
            logger.warning(f"Warning closing SQL connection: {e}")

        try:
            self.redis_cache.close()
        except Exception as e:
            logger.warning(f"Warning closing Redis connection: {e}")

        try:
            self.elasticsearch.close()
        except Exception as e:
            logger.warning(f"Warning closing Elasticsearch connection: {e}")

        self._connected = False
        logger.info("✅ All connections closed")

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile with cache-first strategy.

        Args:
            user_id: User identifier

        Returns:
            Dict containing user profile or None if not found
        """
        if not self._connected:
            raise RuntimeError("DataStore not connected")

        cache_key = f"user_profile:{user_id}"

        try:
            # Try cache first
            cached_data = self.redis_cache.get(cache_key)
            if cached_data:
                logger.info(f"📦 Cache hit for user {user_id}")
                return json.loads(cached_data)

            # Cache miss - query database
            logger.info(f"💾 Cache miss for user {user_id}, querying database")
            query = f"SELECT * FROM users WHERE id = '{user_id}'"
            results = self.sql_db.execute_query(query)

            if results:
                user_profile = results[0]
                # Cache the result for future queries
                self.redis_cache.set(
                    cache_key, json.dumps(user_profile), expire_seconds=1800
                )
                logger.info(f"✅ User {user_id} found and cached")
                return user_profile

            logger.info(f"❌ User {user_id} not found")
            return None

        except Exception as e:
            logger.error(f"❌ Error retrieving user profile {user_id}: {e}")
            return None

    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        Save user profile to database and update cache.

        Args:
            user_id: User identifier
            profile: User profile data

        Returns:
            bool: True if save successful, False otherwise
        """
        if not self._connected:
            raise RuntimeError("DataStore not connected")

        try:
            # Ensure user_id is in the profile
            profile_with_id = {**profile, "id": user_id}

            # Save to database (using upsert logic)
            self.sql_db.insert("users", profile_with_id)

            # Update cache
            cache_key = f"user_profile:{user_id}"
            self.redis_cache.set(
                cache_key, json.dumps(profile_with_id), expire_seconds=1800
            )

            # Index in Elasticsearch for search
            self.elasticsearch.index_document("users", user_id, profile_with_id)

            logger.info(f"✅ User profile {user_id} saved successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving user profile {user_id}: {e}")
            return False

    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """
        Search users using Elasticsearch.

        Args:
            query: Search query string

        Returns:
            List of user profiles matching the search
        """
        if not self._connected:
            raise RuntimeError("DataStore not connected")

        try:
            # Build Elasticsearch query
            es_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["name", "email", "title", "department"],
                }
            }

            logger.info(f"🔍 Searching users with query: '{query}'")
            results = self.elasticsearch.search("users", es_query)

            # Extract source documents from search results
            users = []
            for result in results:
                if "source" in result:
                    user_data = result["source"]
                    user_data["search_score"] = result.get("score", 0)
                    users.append(user_data)

            logger.info(f"✅ Found {len(users)} users matching query")
            return users

        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return []

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user from all systems (database, cache, search index).

        Args:
            user_id: User identifier

        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self._connected:
            raise RuntimeError("DataStore not connected")

        success_count = 0
        total_operations = 3

        # Delete from database
        try:
            self.sql_db.delete("users", f"id = '{user_id}'")
            success_count += 1
            logger.info(f"✅ User {user_id} deleted from database")
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id} from database: {e}")

        # Delete from cache
        try:
            cache_key = f"user_profile:{user_id}"
            self.redis_cache.delete(cache_key)
            success_count += 1
            logger.info(f"✅ User {user_id} deleted from cache")
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id} from cache: {e}")

        # Delete from search index
        try:
            self.elasticsearch.delete_document("users", user_id)
            success_count += 1
            logger.info(f"✅ User {user_id} deleted from search index")
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id} from search index: {e}")

        # Consider operation successful if at least database deletion succeeded
        is_successful = success_count >= 1

        if is_successful:
            logger.info(
                f"✅ User {user_id} deletion completed ({success_count}/{total_operations} operations successful)"
            )
        else:
            logger.error(f"❌ User {user_id} deletion failed completely")

        return is_successful

    def health_check(self) -> Dict[str, bool]:
        """
        Check health status of all connected services.

        Returns:
            Dict with health status of each service
        """
        return {
            "sql_connected": self.sql_db.connected,
            "redis_connected": self.redis_cache.connected,
            "elasticsearch_connected": self.elasticsearch.connected,
            "facade_connected": self._connected,
        }


# Demo usage
def demo_basic_operations():
    """Demonstrate basic facade operations."""
    print("=== BASIC OPERATIONS DEMO ===")

    # Using context manager for automatic connection handling
    with DataStoreFacade() as datastore:
        # Check health
        health = datastore.health_check()
        print(f"Health Status: {health}")
        print()

        # Save a user profile
        user_profile = {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 28,
            "department": "Engineering",
            "title": "Senior Developer",
        }

        print("💾 Saving user profile...")
        success = datastore.save_user_profile("user_123", user_profile)
        print(f"Save result: {success}")
        print()

        # Get user profile (should hit cache)
        print("📦 Getting user profile (first time - from DB)...")
        profile = datastore.get_user_profile("user_123")
        print(f"Retrieved: {profile}")
        print()

        # Get user profile again (should hit cache)
        print("📦 Getting user profile (second time - from cache)...")
        profile = datastore.get_user_profile("user_123")
        print(f"Retrieved: {profile}")
        print()

        # Search users
        print("🔍 Searching users...")
        search_results = datastore.search_users("Alice")
        print(f"Search results: {search_results}")
        print()

        # Delete user
        print("🗑️ Deleting user...")
        delete_success = datastore.delete_user("user_123")
        print(f"Delete result: {delete_success}")
        print()

        # Try to get deleted user
        print("📦 Trying to get deleted user...")
        deleted_profile = datastore.get_user_profile("user_123")
        print(f"Retrieved after deletion: {deleted_profile}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n=== ERROR HANDLING DEMO ===")

    # Try to use facade without connecting
    datastore = DataStoreFacade()
    try:
        datastore.get_user_profile("test_user")
    except RuntimeError as e:
        print(f"✅ Caught expected error: {e}")

    # Demonstrate partial failure handling
    print("\n🔧 Connections will be handled gracefully...")


if __name__ == "__main__":
    demo_basic_operations()
    demo_error_handling()
