import threading
import time
import random
from typing import Optional, List
from enum import Enum


# ====================
# HELPER FUNCTIONS (Implement these too!)
# ====================

def create_mock_connection() -> str:
    """
    TODO: Create a mock database connection string
    - Generate unique connection ID
    - Return connection string like "conn_12345"
    """
    return f"conn_{random.randint(10000, 99999)}"


def simulate_database_work():
    """
    TODO: Simulate database work
    - Add small random delay
    """
    time.sleep(random.uniform(0.01, 0.1))
    

# ====================
# 1. DECORATOR-BASED SINGLETON
# ====================

def singleton(cls):
    """
    TODO: Implement decorator-based singleton
    - Use a dictionary to store instances per class
    - Implement thread-safe creation
    - Return the get_instance function
    """
    instances = {}
    lock = threading.Lock()
    
    def get_instance(*args, **kwargs):
        # TODO: Implement thread-safe singleton logic
        # Hint: Use double-checked locking pattern
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


@singleton
class DecoratorDatabasePool:
    """Database connection pool using decorator singleton"""
    
    def __init__(self):
        """
        TODO: Initialize the connection pool
        - Create empty connections list (max 5)
        - Initialize metrics (total_created, active_connections, etc.)
        - Add thread locks for connection management
        """
        self.connections: List[str] = []
        self.active_connections_set: set = set()
        self.max_connections = 5
        self.total_created = 0
        self.active_connections = 0
        self.lock = threading.Lock()

    @property
    def available_connections(self) -> int:
        return len(self.connections) - self.active_connections
            
    def get_connection(self) -> Optional[str]:
        """
        TODO: Borrow a connection from the pool
        - If available connection exists, return it
        - If pool not full, create new connection
        - If pool full and no available connections, return None
        - Update metrics
        """
        with self.lock:
            # Check for available connections
            if self.available_connections > 0:
                for conn in self.connections:
                    if conn not in self.active_connections_set:
                        self.active_connections_set.add(conn)
                        self.active_connections += 1
                        return conn
            
            # If no available connections, create new if pool not full
            if self.total_created < self.max_connections:
                conn = create_mock_connection()
                self.connections.append(conn)
                self.active_connections_set.add(conn)
                self.total_created += 1
                self.active_connections += 1
                return conn
            
            # Pool is full and no available connections
            return None

    def return_connection(self, connection: str) -> bool:
        """
        TODO: Return a connection to the pool
        - Mark connection as available
        - Update metrics
        - Return True if successful
        """
        with self.lock:
            if connection in self.active_connections_set:
                self.active_connections_set.remove(connection)
                self.active_connections -= 1
                return True
            return False
    
    def get_metrics(self) -> dict:
        """
        TODO: Return current pool metrics
        - total_connections_created
        - active_connections
        - available_connections
        """
        with self.lock:
            return {
                "total_connections_created": self.total_created,
                "active_connections": self.active_connections,
                "available_connections": self.available_connections,
                "total_connections_in_pool": len(self.connections)
            }


# ====================
# 2. MODULE-LEVEL SINGLETON (Pythonic)
# ====================

class _ModuleDatabasePool:
    """Private class for module-level singleton"""
    
    def __init__(self):
        """
        TODO: Same initialization as above
        """
        pass
    
    def get_connection(self) -> Optional[str]:
        """TODO: Same implementation as decorator version"""
        pass
    
    def return_connection(self, connection: str) -> bool:
        """TODO: Same implementation as decorator version"""
        pass
    
    def get_metrics(self) -> dict:
        """TODO: Same implementation as decorator version"""
        pass


# Create the singleton instance at module level
# TODO: Create the single instance here
module_db_pool = _ModuleDatabasePool()


# ====================
# 3. ENUM-BASED SINGLETON
# ====================

class EnumDatabasePool(Enum):
    """Database connection pool using enum singleton"""
    INSTANCE = "database_pool"
    
    def __init__(self, value):
        """
        TODO: Initialize the connection pool
        - Only initialize once (check if already initialized)
        - Same initialization as other versions
        """
        if not hasattr(self, 'initialized'):
            self.initialized = True
        pass
    
    def get_connection(self) -> Optional[str]:
        """TODO: Same implementation as other versions"""
        pass
    
    def return_connection(self, connection: str) -> bool:
        """TODO: Same implementation as other versions"""
        pass
    
    def get_metrics(self) -> dict:
        """TODO: Same implementation as other versions"""
        pass


# ====================
# 4. TESTING AND PERFORMANCE COMPARISON
# ====================

def simulate_database_usage(pool_getter, pool_name: str, num_operations: int = 10):
    """
    Simulate database connection usage
    TODO: Implement this function to:
    - Get connections from the pool
    - Simulate some work (time.sleep)
    - Return connections to the pool
    - Print metrics periodically
    """
    for i in range(num_operations):
        pool = pool_getter()
        conn = pool.get_connection()
        if conn:
            print(f"[{pool_name}] Borrowed {conn}")
            simulate_database_work()
            success = pool.return_connection(conn)
            if success:
                print(f"[{pool_name}] Returned {conn}")
            else:
                print(f"[{pool_name}] Failed to return {conn}")
        else:
            print(f"[{pool_name}] No available connection")
        
        if (i + 1) % 5 == 0:
            metrics = pool.get_metrics()
            print(f"[{pool_name}] Metrics after {i + 1} operations: {metrics}")
        time.sleep(0.1)  # Small delay between operations


def performance_test():
    """
    Performance comparison test
    - Test creation time for each singleton type
    - Test concurrent access performance
    - Test memory usage
    - Print comparison results
    """
    print("=== PERFORMANCE COMPARISON ===")
    
    # Test 1: Creation time
    print("\n1. Creation Time Test:")
    
    # Decorator Singleton
    print("\n--- Decorator Singleton ---")
    start = time.time()
    decorator_pool = DecoratorDatabasePool()
    end = time.time()
    print(f"DecoratorDatabasePool instance: {id(decorator_pool)}")
    print(f"Creation time: {end - start:.6f} seconds")
    
    # Module Singleton
    print("\n--- Module Singleton ---")
    start = time.time()
    module_pool = module_db_pool
    end = time.time()
    print(f"ModuleDatabasePool instance: {id(module_pool)}")
    print(f"Access time: {end - start:.6f} seconds")
    
    # Enum Singleton
    print("\n--- Enum Singleton ---")
    start = time.time()
    enum_pool = EnumDatabasePool.INSTANCE
    end = time.time()
    print(f"EnumDatabasePool instance: {id(enum_pool)}")
    print(f"Access time: {end - start:.6f} seconds")
    
    # Test 2: Concurrent access
    print("\n2. Concurrent Access Test:")
    threads = []
    for i in range(3):
        t1 = threading.Thread(target=simulate_database_usage, args=(lambda: DecoratorDatabasePool(), "Decorator", 5))
        t2 = threading.Thread(target=simulate_database_usage, args=(lambda: module_db_pool, "Module", 5))
        t3 = threading.Thread(target=simulate_database_usage, args=(lambda: EnumDatabasePool.INSTANCE, "Enum", 5))
        threads.extend([t1, t2, t3])
        t1.start()
        t2.start()
        t3.start()

    for t in threads:
        t.join()
    print("All threads completed.")
    
    # Test 3: Memory verification
    print("\n3. Memory/Identity Verification:")
    print("DecoratorDatabasePool instances are the same:", all(DecoratorDatabasePool() is DecoratorDatabasePool() for _ in range(5)))
    print("ModuleDatabasePool instances are the same:", all(module_db_pool is module_db_pool for _ in range(5)))
    print("EnumDatabasePool instances are the same:", all(EnumDatabasePool.INSTANCE is EnumDatabasePool.INSTANCE for _ in range(5)))


def stress_test():
    """
    Stress test all three implementations
    - Create multiple threads
    - Each thread performs database operations
    - Measure performance and correctness
    """
    print("=== STRESS TEST ===")
    
    def worker_thread(pool_getter, pool_name, thread_id, operations=20):
        for i in range(operations):
            pool = pool_getter()
            conn = pool.get_connection()
            if conn:
                print(f"[{pool_name}][Thread {thread_id}] Borrowed {conn}")
                simulate_database_work()
                success = pool.return_connection(conn)
                if success:
                    print(f"[{pool_name}][Thread {thread_id}] Returned {conn}")
                else:
                    print(f"[{pool_name}][Thread {thread_id}] Failed to return {conn}")
            else:
                print(f"[{pool_name}][Thread {thread_id}] No available connection")
            time.sleep(random.uniform(0.01, 0.1))
    
    threads = []
    for i in range(5):  # Reduced thread count for cleaner output
        t1 = threading.Thread(target=worker_thread, args=(lambda: DecoratorDatabasePool(), "Decorator", i, 10))
        t2 = threading.Thread(target=worker_thread, args=(lambda: module_db_pool, "Module", i, 10))
        t3 = threading.Thread(target=worker_thread, args=(lambda: EnumDatabasePool.INSTANCE, "Enum", i, 10))
        threads.extend([t1, t2, t3])
        t1.start()
        t2.start()
        t3.start()
    
    for t in threads:
        t.join()
    print("Stress test completed.")


# ====================
# 5. MAIN EXECUTION
# ====================

if __name__ == "__main__":
    print("Singleton Pattern Comparison")
    print("=" * 50)
    
    # Basic functionality test:
    print("\nBasic functionality test:")
    
    # Test decorator singleton
    print("\n--- Decorator Singleton ---")
    decorator_pool = DecoratorDatabasePool()
    print("DecoratorDatabasePool instance:", id(decorator_pool))
    conn1 = decorator_pool.get_connection()
    print(f"Got connection: {conn1}")
    print(f"Metrics: {decorator_pool.get_metrics()}")
    decorator_pool.return_connection(conn1)
    print(f"Returned connection. Metrics: {decorator_pool.get_metrics()}")
    
    # Test module singleton  
    print("\n--- Module Singleton ---")
    print("ModuleDatabasePool instance:", id(module_db_pool))
    conn2 = module_db_pool.get_connection()
    print(f"Got connection: {conn2}")
    print(f"Metrics: {module_db_pool.get_metrics()}")
    module_db_pool.return_connection(conn2)
    print(f"Returned connection. Metrics: {module_db_pool.get_metrics()}")
    
    # Test enum singleton
    print("\n--- Enum Singleton ---")
    enum_pool = EnumDatabasePool.INSTANCE
    print("EnumDatabasePool instance:", id(enum_pool))
    conn3 = enum_pool.get_connection()
    print(f"Got connection: {conn3}")
    print(f"Metrics: {enum_pool.get_metrics()}")
    enum_pool.return_connection(conn3)
    print(f"Returned connection. Metrics: {enum_pool.get_metrics()}")
    
    # Run performance tests
    print("\n" + "=" * 50)
    performance_test()
    
    print("\n" + "=" * 50)
    stress_test()
