import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TransactionSystem")


# ============================================================================
# ENUMS
# ============================================================================


class OperationType(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class TransactionStatus(Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


# ============================================================================
# RECEIVER - Simple In-Memory Database
# ============================================================================


class Database:
    """
    Simulates a simple in-memory database with tables.
    In real systems, this would be your actual database connection.
    """

    def __init__(self):
        self._tables: Dict[str, Dict[int, Dict[str, Any]]] = {}
        logger.info("Database initialized")

    def create_table(self, table_name: str):
        """Create a new table"""
        if table_name not in self._tables:
            self._tables[table_name] = {}
            logger.info(f"Table '{table_name}' created")

    def insert(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Insert a record into the table.
        Returns True if successful, False if record already exists.
        """
        # TODO: Implement insert logic
        # - Check if table exists
        # - Check if record_id already exists (should fail if it does)
        # - Insert the record
        # - Log the operation
        # - Return True on success, False on failure
        if table_name not in self._tables:
            self._tables[table_name] = {}
        if record_id in self._tables[table_name]:
            return False  # Record already exists
        self._tables[table_name][record_id] = data
        logger.info(f"Inserted record ID {record_id} into '{table_name}': {data}")
        return True

    def update(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing record.
        Returns True if successful, False if record doesn't exist.
        """
        # TODO: Implement update logic
        # - Check if table exists
        # - Check if record exists (should fail if it doesn't)
        # - Update the record
        # - Log the operation
        # - Return True on success, False on failure
        if table_name not in self._tables or record_id not in self._tables[table_name]:
            return False  # Record doesn't exist
        self._tables[table_name][record_id] = data
        logger.info(f"Updated record ID {record_id} in '{table_name}': {data}")
        return True

    def delete(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Delete a record and return its data (for undo purposes).
        Returns the deleted data if successful, None if record doesn't exist.
        """
        # TODO: Implement delete logic
        # - Check if table exists
        # - Check if record exists
        # - Remove and return the record data
        # - Log the operation
        # - Return the deleted data or None
        if table_name not in self._tables or record_id not in self._tables[table_name]:
            return None  # Record doesn't exist
        data = self._tables[table_name].pop(record_id)
        logger.info(f"Deleted record ID {record_id} from '{table_name}': {data}")
        return data

    def get_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a record"""
        if table_name in self._tables and record_id in self._tables[table_name]:
            return self._tables[table_name][record_id].copy()
        return None

    def show_table(self, table_name: str):
        """Display table contents"""
        print(f"\n{'='*60}")
        print(f"TABLE: {table_name}")
        print(f"{'='*60}")
        if table_name not in self._tables or not self._tables[table_name]:
            print("(empty)")
        else:
            for record_id, data in self._tables[table_name].items():
                print(f"ID {record_id}: {data}")
        print(f"{'='*60}\n")


# ============================================================================
# COMMAND INTERFACE
# ============================================================================


class Command(ABC):
    """Base command interface with transaction support"""

    def __init__(self):
        self.timestamp: Optional[datetime] = None
        self.executed = False
        self.success = False

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        """
        Validate if command can be executed.
        Check preconditions before execution.
        """
        pass

    def __str__(self) -> str:
        status = "✓" if self.success else "✗" if self.executed else "○"
        return f"{status} {self.__class__.__name__}"


# ============================================================================
# CONCRETE COMMANDS - Database Operations
# ============================================================================


class InsertCommand(Command):
    """Insert a record into the database"""

    def __init__(
        self, db: Database, table_name: str, record_id: int, data: Dict[str, Any]
    ):
        super().__init__()
        self._db = db
        self._table_name = table_name
        self._record_id = record_id
        self._data = data

    def can_execute(self) -> bool:
        """Check if record doesn't already exist"""
        # TODO: Implement validation
        # - Check if the record_id doesn't already exist in the table
        # - Return True if we can insert, False otherwise
        if self._table_name not in self._db._tables:
            return True  # Table doesn't exist yet, so we can insert
        return self._record_id not in self._db._tables[self._table_name]

    def execute(self) -> bool:
        """Execute the insert operation"""
        # TODO: Implement execution
        # - Check can_execute() first
        # - Call db.insert()
        # - Set self.executed = True
        # - Set self.success based on result
        # - Set self.timestamp
        # - Log appropriate message (INFO on success, ERROR on failure)
        # - Return self.success
        if not self.can_execute():
            logger.error(
                f"InsertCommand failed: Record ID {self._record_id} already exists in '{self._table_name}'"
            )
            self.executed = True
            self.success = False
            self.timestamp = datetime.now()
            return False
        result = self._db.insert(self._table_name, self._record_id, self._data)
        self.executed = True
        self.success = result
        self.timestamp = datetime.now()
        if result:
            logger.info(
                f"InsertCommand succeeded: Record ID {self._record_id} inserted into '{self._table_name}'"
            )
        else:
            logger.error(
                f"InsertCommand failed: Could not insert Record ID {self._record_id} into '{self._table_name}'"
            )
        return self.success

    def undo(self) -> bool:
        """Undo by deleting the inserted record"""
        # TODO: Implement undo
        # - Only undo if the command was successfully executed
        # - Call db.delete() to remove the record
        # - Log the operation
        # - Return True on success
        if not self.executed or not self.success:
            logger.warning(
                f"InsertCommand undo skipped: Command was not successfully executed"
            )
            return False
        deleted_data = self._db.delete(self._table_name, self._record_id)
        if deleted_data is not None:
            logger.info(
                f"InsertCommand undo succeeded: Record ID {self._record_id} deleted from '{self._table_name}'"
            )
            return True
        else:
            logger.error(
                f"InsertCommand undo failed: Record ID {self._record_id} could not be deleted from '{self._table_name}'"
            )
            return False

    def __str__(self) -> str:
        status = "✓" if self.success else "✗" if self.executed else "○"
        return f"{status} INSERT into {self._table_name} (ID: {self._record_id})"


class UpdateCommand(Command):
    """Update an existing record"""

    def __init__(
        self, db: Database, table_name: str, record_id: int, new_data: Dict[str, Any]
    ):
        super().__init__()
        self._db = db
        self._table_name = table_name
        self._record_id = record_id
        self._new_data = new_data
        self._old_data: Optional[Dict[str, Any]] = None  # For undo

    def can_execute(self) -> bool:
        """Check if record exists"""
        # TODO: Implement validation
        # - Check if the record exists in the table
        # - Return True if it exists, False otherwise
        return (
            self._table_name in self._db._tables
            and self._record_id in self._db._tables[self._table_name]
        )

    def execute(self) -> bool:
        """Execute the update operation"""
        # TODO: Implement execution
        # - Save current data to self._old_data (for undo)
        # - Check can_execute()
        # - Call db.update()
        # - Set flags and timestamp
        # - Log the operation
        # - Return success status
        if not self.can_execute():
            logger.error(
                f"UpdateCommand failed: Record ID {self._record_id} does not exist in '{self._table_name}'"
            )
            self.executed = True
            self.success = False
            self.timestamp = datetime.now()
            return False
        self._old_data = self._db.get_record(self._table_name, self._record_id)
        result = self._db.update(self._table_name, self._record_id, self._new_data)
        self.executed = True
        self.success = result
        self.timestamp = datetime.now()
        if result:
            logger.info(
                f"UpdateCommand succeeded: Record ID {self._record_id} updated in '{self._table_name}'"
            )
        else:
            logger.error(
                f"UpdateCommand failed: Could not update Record ID {self._record_id} in '{self._table_name}'"
            )
        return self.success

    def undo(self) -> bool:
        """Undo by restoring old data"""
        # TODO: Implement undo
        # - Check if we have old_data saved
        # - Restore the old data using db.update()
        # - Log the operation
        # - Return True on success
        if not self.executed or not self.success or self._old_data is None:
            logger.warning(
                f"UpdateCommand undo skipped: Command was not successfully executed or no old data"
            )
            return False
        result = self._db.update(self._table_name, self._record_id, self._old_data)
        if result:
            logger.info(
                f"UpdateCommand undo succeeded: Record ID {self._record_id} restored in '{self._table_name}'"
            )
            return True
        else:
            logger.error(
                f"UpdateCommand undo failed: Could not restore Record ID {self._record_id} in '{self._table_name}'"
            )
            return False

    def __str__(self) -> str:
        status = "✓" if self.success else "✗" if self.executed else "○"
        return f"{status} UPDATE {self._table_name} (ID: {self._record_id})"


class DeleteCommand(Command):
    """Delete a record from the database"""

    def __init__(self, db: Database, table_name: str, record_id: int):
        super().__init__()
        self._db = db
        self._table_name = table_name
        self._record_id = record_id
        self._deleted_data: Optional[Dict[str, Any]] = None  # For undo

    def can_execute(self) -> bool:
        """Check if record exists"""
        # TODO: Implement validation
        return (
            self._table_name in self._db._tables
            and self._record_id in self._db._tables[self._table_name]
        )

    def execute(self) -> bool:
        """Execute the delete operation"""
        # TODO: Implement execution
        # - Check can_execute()
        # - Call db.delete() and save the returned data to self._deleted_data
        # - Set flags and timestamp
        # - Log the operation
        # - Return success status
        if not self.can_execute():
            logger.error(
                f"DeleteCommand failed: Record ID {self._record_id} does not exist in '{self._table_name}'"
            )
            self.executed = True
            self.success = False
            self.timestamp = datetime.now()
            return False
        self._deleted_data = self._db.delete(self._table_name, self._record_id)
        self.executed = True
        self.success = self._deleted_data is not None
        self.timestamp = datetime.now()
        if self.success:
            logger.info(
                f"DeleteCommand succeeded: Record ID {self._record_id} deleted from '{self._table_name}'"
            )
        else:
            logger.error(
                f"DeleteCommand failed: Could not delete Record ID {self._record_id} from '{self._table_name}'"
            )
        return self.success

    def undo(self) -> bool:
        """Undo by re-inserting the deleted record"""
        # TODO: Implement undo
        # - Check if we have deleted_data saved
        # - Re-insert using db.insert()
        # - Log the operation
        # - Return True on success
        if not self.executed or not self.success or self._deleted_data is None:
            logger.warning(
                f"DeleteCommand undo skipped: Command was not successfully executed or no deleted data"
            )
            return False
        result = self._db.insert(
            self._table_name, self._record_id, self._deleted_data
        )
        if result:
            logger.info(
                f"DeleteCommand undo succeeded: Record ID {self._record_id} re-inserted into '{self._table_name}'"
            )
            return True
        else:
            logger.error(
                f"DeleteCommand undo failed: Could not re-insert Record ID {self._record_id} into '{self._table_name}'"
            )
            return False

    def __str__(self) -> str:
        status = "✓" if self.success else "✗" if self.executed else "○"
        return f"{status} DELETE from {self._table_name} (ID: {self._record_id})"


# ============================================================================
# TRANSACTION COMMAND - Atomic Operations
# ============================================================================


class TransactionCommand(Command):
    """
    Groups multiple commands into an atomic transaction.
    If any command fails, all previous commands are rolled back.
    """

    def __init__(self, name: str, commands: List[Command]):
        super().__init__()
        self.name = name
        self._commands = commands
        self._executed_commands: List[Command] = (
            []
        )  # Track successfully executed commands
        self.status = TransactionStatus.PENDING

    def can_execute(self) -> bool:
        """Check if all commands can be executed"""
        # TODO: Implement validation
        # - Check can_execute() for all commands
        # - Return True only if ALL commands can execute
        # - Log any validation failures
        for cmd in self._commands:
            if not cmd.can_execute():
                logger.error(
                    f"Transaction '{self.name}' cannot execute because command {cmd} failed validation"
                )
                return False
        return True

    def execute(self) -> bool:
        """
        Execute all commands in sequence.
        If any fails, rollback all previous commands.
        """
        logger.info(f"{'='*60}")
        logger.info(f"Starting Transaction: {self.name}")
        logger.info(f"{'='*60}")

        # TODO: Implement transaction execution
        # 1. Check can_execute() first
        # 2. Loop through each command:
        #    a. Execute the command
        #    b. If successful, add to self._executed_commands
        #    c. If any command fails:
        #       - Log the failure
        #       - Call self._rollback()
        #       - Set self.status = TransactionStatus.ROLLED_BACK
        #       - Return False
        # 3. If all succeed:
        #    - Set self.status = TransactionStatus.COMMITTED
        #    - Set self.success = True
        #    - Log success
        #    - Return True
        if not self.can_execute():
            self.status = TransactionStatus.FAILED
            self.executed = True
            self.success = False
            self.timestamp = datetime.now()
            logger.error(f"Transaction '{self.name}' validation failed")
            return False
        for cmd in self._commands:
            result = cmd.execute()
            if result:
                self._executed_commands.append(cmd)
            else:
                logger.error(
                    f"Transaction '{self.name}' failed during command: {cmd}"
                )
                self._rollback()
                self.status = TransactionStatus.ROLLED_BACK
                self.executed = True
                self.success = False
                self.timestamp = datetime.now()
                logger.info(f"Transaction '{self.name}' rolled back")
                return False
        self.status = TransactionStatus.COMMITTED
        self.executed = True
        self.success = True
        self.timestamp = datetime.now()
        logger.info(f"Transaction '{self.name}' committed successfully")
        return True

    def _rollback(self):
        """Rollback all successfully executed commands"""
        logger.warning(f"Rolling back transaction: {self.name}")

        # TODO: Implement rollback
        # - Loop through self._executed_commands in REVERSE order
        # - Call undo() on each command
        # - Log each rollback operation
        # - Clear self._executed_commands after rollback
        for cmd in reversed(self._executed_commands):
            undo_result = cmd.undo()
            if undo_result:
                logger.info(f"Rolled back command: {cmd}")
            else:
                logger.error(f"Failed to roll back command: {cmd}")
        self._executed_commands.clear()

    def undo(self) -> bool:
        """Undo the entire transaction"""
        # TODO: Implement transaction undo
        # - Check if transaction was committed
        # - Call _rollback()
        # - Set status to ROLLED_BACK
        # - Log the operation
        # - Return True
        if self.status != TransactionStatus.COMMITTED:
            logger.warning(
                f"Transaction '{self.name}' undo skipped: Not in COMMITTED state"
            )
            return False
        self._rollback()
        self.status = TransactionStatus.ROLLED_BACK
        logger.info(f"Transaction '{self.name}' undone successfully")
        return True

    def __str__(self) -> str:
        status_symbol = (
            "✓"
            if self.status == TransactionStatus.COMMITTED
            else "✗" if self.status == TransactionStatus.ROLLED_BACK else "○"
        )
        return f"{status_symbol} Transaction '{self.name}' ({self.status.value}) - {len(self._commands)} commands"


# ============================================================================
# RETRY COMMAND DECORATOR
# ============================================================================


class RetryCommand(Command):
    """
    Decorator that retries a command on failure with exponential backoff.
    """

    def __init__(
        self, command: Command, max_retries: int = 3, initial_delay: float = 0.5
    ):
        super().__init__()
        self._command = command
        self._max_retries = max_retries
        self._initial_delay = initial_delay
        self._attempts = 0

    def can_execute(self) -> bool:
        return self._command.can_execute()

    def execute(self) -> bool:
        """Execute with retry logic and exponential backoff"""
        # TODO: Implement retry logic
        # 1. Loop up to self._max_retries times:
        #    a. Increment self._attempts
        #    b. Log attempt number
        #    c. Try to execute self._command
        #    d. If successful:
        #       - Set self.success = True
        #       - Set self.executed = True
        #       - Log success
        #       - Return True
        #    e. If failed and not last retry:
        #       - Calculate delay = self._initial_delay * (2 ** (self._attempts - 1))
        #       - Log retry attempt with delay
        #       - Sleep for the delay
        # 2. If all retries failed:
        #    - Set self.executed = True
        #    - Set self.success = False
        #    - Log final failure
        #    - Return False
        while self._attempts < self._max_retries:
            self._attempts += 1
            logger.info(
                f"RetryCommand attempt {self._attempts} for command: {self._command}"
            )
            result = self._command.execute()
            if result:
                self.success = True
                self.executed = True
                self.timestamp = datetime.now()
                logger.info(
                    f"RetryCommand succeeded on attempt {self._attempts} for command: {self._command}"
                )
                return True
            else:
                if self._attempts < self._max_retries:
                    delay = self._initial_delay * (2 ** (self._attempts - 1))
                    logger.warning(
                        f"RetryCommand failed on attempt {self._attempts} for command: {self._command}. Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
        self.executed = True
        self.success = False
        self.timestamp = datetime.now()
        logger.error(
            f"RetryCommand failed after {self._max_retries} attempts for command: {self._command}"
        )
        return False

    def undo(self) -> bool:
        """Undo the wrapped command"""
        return self._command.undo()

    def __str__(self) -> str:
        status = "✓" if self.success else "✗" if self.executed else "○"
        return f"{status} Retry({self._attempts}/{self._max_retries}): {self._command}"


# ============================================================================
# TRANSACTION MANAGER - Invoker with History
# ============================================================================


class TransactionManager:
    """
    Manages transaction execution with history and rollback support.
    """

    def __init__(self, db: Database):
        self._db = db
        self._transaction_history: List[Command] = []

    def execute_transaction(self, transaction: Command) -> bool:
        """Execute a transaction and track it"""
        # TODO: Implement execution
        # - Execute the transaction
        # - If successful, add to history
        # - Return the result
        result = transaction.execute()
        if result:
            self._transaction_history.append(transaction)
        return result

    def rollback_last(self) -> bool:
        """Rollback the last transaction"""
        # TODO: Implement rollback
        # - Check if there's a transaction in history
        # - Pop the last transaction
        # - Call undo() on it
        # - Log the operation
        # - Return True on success
        if not self._transaction_history:
            logger.warning("No transactions to rollback")
            return False
        last_txn = self._transaction_history.pop()
        result = last_txn.undo()
        if result:
            logger.info(f"Rolled back transaction: {last_txn}")
            return True
        else:
            logger.error(f"Failed to roll back transaction: {last_txn}")
            return False

    def show_history(self):
        """Display transaction history"""
        print(f"\n{'='*60}")
        print("TRANSACTION HISTORY")
        print(f"{'='*60}")
        if not self._transaction_history:
            print("No transactions executed")
        else:
            for i, txn in enumerate(self._transaction_history, 1):
                print(f"{i}. {txn}")
        print(f"{'='*60}\n")


# ============================================================================
# CLIENT CODE - Test Scenarios
# ============================================================================


def main():
    """
    Test the transaction system with various scenarios.
    """

    # Initialize database
    db = Database()
    db.create_table("users")
    db.create_table("orders")

    # Initialize transaction manager
    manager = TransactionManager(db)

    print("\n" + "=" * 60)
    print("DATABASE TRANSACTION SYSTEM - DEMO")
    print("=" * 60 + "\n")

    # ========================================================================
    # Test 1: Successful Transaction
    # ========================================================================
    print("TEST 1: Successful Transaction")
    print("-" * 60)

    successful_txn = TransactionCommand(
        "Create User Profile",
        [
            InsertCommand(
                db, "users", 1, {"name": "Alice", "email": "alice@example.com"}
            ),
            InsertCommand(db, "users", 2, {"name": "Bob", "email": "bob@example.com"}),
            InsertCommand(
                db, "orders", 101, {"user_id": 1, "product": "Laptop", "amount": 1200}
            ),
        ],
    )

    manager.execute_transaction(successful_txn)
    db.show_table("users")
    db.show_table("orders")

    # ========================================================================
    # Test 2: Failed Transaction with Automatic Rollback
    # ========================================================================
    print("\nTEST 2: Failed Transaction (Duplicate Insert)")
    print("-" * 60)

    failed_txn = TransactionCommand(
        "Duplicate User Insert",
        [
            InsertCommand(
                db, "users", 3, {"name": "Charlie", "email": "charlie@example.com"}
            ),
            InsertCommand(
                db, "users", 1, {"name": "Duplicate", "email": "dup@example.com"}
            ),  # This will fail!
            InsertCommand(
                db, "orders", 102, {"user_id": 3, "product": "Mouse", "amount": 25}
            ),
        ],
    )

    manager.execute_transaction(failed_txn)
    db.show_table("users")  # User 3 should NOT be in the table (rolled back)
    db.show_table("orders")  # Order 102 should NOT be in the table

    # ========================================================================
    # Test 3: Update and Delete Operations
    # ========================================================================
    print("\nTEST 3: Update and Delete Operations")
    print("-" * 60)

    update_txn = TransactionCommand(
        "Update User Info",
        [
            UpdateCommand(
                db,
                "users",
                1,
                {"name": "Alice Smith", "email": "alice.smith@example.com"},
            ),
            DeleteCommand(db, "users", 2),
        ],
    )

    manager.execute_transaction(update_txn)
    db.show_table("users")

    # ========================================================================
    # Test 4: Manual Rollback
    # ========================================================================
    print("\nTEST 4: Manual Rollback")
    print("-" * 60)

    print("Rolling back last transaction...")
    manager.rollback_last()
    db.show_table("users")  # Should be back to original state

    # ========================================================================
    # Test 5: Retry Command (Bonus)
    # ========================================================================
    print("\nTEST 5: Retry Command")
    print("-" * 60)

    # Simulate a command that might fail
    retry_cmd = RetryCommand(
        InsertCommand(db, "users", 5, {"name": "Eve", "email": "eve@example.com"}),
        max_retries=3,
        initial_delay=0.1,
    )

    retry_cmd.execute()
    db.show_table("users")

    # ========================================================================
    # Summary
    # ========================================================================
    manager.show_history()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
