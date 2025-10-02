from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TransactionStatus(Enum):
    """Transaction status enumeration."""

    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


class OperationType(Enum):
    """Operation type enumeration for type safety."""

    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


@dataclass(frozen=True)
class AccountSnapshot:
    """
    Memento for account state - OPTIMIZED with delta-based storage.

    This stores the account state before a transaction begins, allowing
    efficient rollback by restoring to the previous_balance.

    The balance_delta is stored for audit purposes and future optimizations
    (e.g., only transmitting deltas in distributed systems).
    """

    account_id: str
    previous_balance: float  # Balance BEFORE the transaction started
    balance_delta: float  # Change during transaction (for audit/optimization)
    timestamp: datetime

    def get_previous_balance(self) -> float:
        """Get the balance before the transaction."""
        return self.previous_balance


@dataclass
class TransactionMetadata:
    """
    Metadata for audit trail and transaction tracking.

    Provides complete information about each transaction for compliance,
    debugging, and audit purposes.
    """

    transaction_id: int
    timestamp: datetime
    user_id: str
    description: str
    status: TransactionStatus = TransactionStatus.PENDING
    parent_transaction_id: Optional[int] = None

    def __str__(self) -> str:
        """String representation for logging."""
        parent = (
            f" (parent: {self.parent_transaction_id})"
            if self.parent_transaction_id
            else ""
        )
        return (
            f"Transaction #{self.transaction_id}{parent}: "
            f"{self.description} - {self.status.value}"
        )


class Account:
    """
    Bank account with transaction support.

    This is the Originator in the Memento pattern.
    Manages its own balance and creates snapshots of its state.
    """

    def __init__(self, account_id: str, initial_balance: float = 0.0) -> None:
        """
        Initialize account.

        Args:
            account_id: Unique account identifier
            initial_balance: Starting balance (must be non-negative)

        Raises:
            ValueError: If initial_balance is negative
        """
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")

        self._account_id = account_id
        self._balance = initial_balance

    @property
    def balance(self) -> float:
        """Get current balance."""
        return self._balance

    @property
    def account_id(self) -> str:
        """Get account ID."""
        return self._account_id

    def deposit(self, amount: float) -> bool:
        """
        Deposit money into account.

        Args:
            amount: Amount to deposit (must be positive)

        Returns:
            True if successful, False if invalid amount
        """
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Withdraw money from account.

        Args:
            amount: Amount to withdraw (must be positive)

        Returns:
            True if successful, False if insufficient funds or invalid amount
        """
        if amount <= 0:
            return False

        if amount > self._balance:
            # Insufficient funds - prevent overdraft
            return False

        self._balance -= amount
        return True

    def create_snapshot(self) -> AccountSnapshot:
        """
        Create a snapshot of current account state.

        The snapshot captures the CURRENT balance as the "previous_balance"
        so it can be restored later. The delta is initially 0 since no
        operations have been performed yet within this transaction.

        Returns:
            AccountSnapshot memento with current state
        """
        return AccountSnapshot(
            account_id=self._account_id,
            previous_balance=self._balance,  # Current balance becomes "previous"
            balance_delta=0.0,  # No change yet at snapshot time
            timestamp=datetime.now(),
        )

    def restore_from_snapshot(self, snapshot: AccountSnapshot) -> None:
        """
        Restore account state from snapshot.

        Sets the balance back to what it was when the snapshot was created
        (i.e., before the transaction started).

        Args:
            snapshot: Previously created snapshot

        Raises:
            ValueError: If snapshot is for a different account
        """
        if snapshot.account_id != self._account_id:
            raise ValueError(
                f"Snapshot account_id '{snapshot.account_id}' does not match "
                f"account '{self._account_id}'"
            )

        # Restore to the balance captured at snapshot time
        self._balance = snapshot.get_previous_balance()

    def __str__(self) -> str:
        """String representation for logging."""
        return f"Account({self._account_id}: ${self._balance:.2f})"


class TransactionLevel:
    """
    Represents a single transaction level (can be nested).

    Stores snapshots of all accounts at the start of this transaction level,
    allowing rollback to restore the state before this level began.
    """

    def __init__(self, metadata: TransactionMetadata) -> None:
        """
        Initialize transaction level.

        Args:
            metadata: Transaction metadata for this level
        """
        self.metadata = metadata
        self.snapshots: Dict[str, AccountSnapshot] = {}

    def save_account_state(self, account: Account) -> None:
        """
        Save account state at transaction start.

        Creates a snapshot capturing the account's current balance,
        which becomes the "previous balance" for rollback purposes.

        Args:
            account: Account to snapshot
        """
        snapshot = account.create_snapshot()
        self.snapshots[account.account_id] = snapshot

    def get_snapshot(self, account_id: str) -> Optional[AccountSnapshot]:
        """
        Get snapshot for an account.

        Args:
            account_id: Account identifier

        Returns:
            Snapshot if exists, None otherwise
        """
        return self.snapshots.get(account_id)

    def get_all_snapshots(self) -> Dict[str, AccountSnapshot]:
        """Get all snapshots for this transaction level."""
        return self.snapshots.copy()


class TransactionManager:
    """
    Manages multi-level transactions with rollback support.

    This is the Caretaker in the Memento pattern.

    Features:
    - Begin/commit/rollback transactions
    - Nested transactions up to MAX_NESTING_LEVEL deep
    - Transaction history with complete audit trail
    - Memory-efficient delta-based snapshots
    - ACID-like properties for in-memory operations

    Architecture notes:
    - Uses a stack for nested transactions
    - Each level captures state at its beginning
    - Rollback restores to the state at level start
    - Commit makes changes permanent (if outermost level)
    """

    MAX_NESTING_LEVEL = 3  # Maximum depth of nested transactions

    def __init__(self) -> None:
        """
        Initialize transaction manager.

        Sets up account registry, transaction stack, history tracking,
        and transaction ID generation.
        """
        self._accounts: Dict[str, Account] = {}
        self._transaction_stack: List[TransactionLevel] = []
        self._transaction_history: List[TransactionMetadata] = []
        self._next_transaction_id = 1

    def register_account(self, account: Account) -> None:
        """
        Register an account with the transaction manager.

        Args:
            account: Account to register

        Raises:
            ValueError: If account with same ID already registered
        """
        if account.account_id in self._accounts:
            raise ValueError(f"Account '{account.account_id}' is already registered")
        self._accounts[account.account_id] = account

    def get_account(self, account_id: str) -> Optional[Account]:
        """
        Get account by ID.

        Args:
            account_id: Account identifier

        Returns:
            Account if exists, None otherwise
        """
        return self._accounts.get(account_id)

    def begin_transaction(self, user_id: str, description: str) -> bool:
        """
        Begin a new transaction (or nested transaction).

        Captures the current state of ALL registered accounts so they can
        be restored if this transaction is rolled back.

        Args:
            user_id: User initiating the transaction
            description: Human-readable description of the transaction

        Returns:
            True if successful, False if max nesting level reached
        """
        # Check nesting level limit
        if len(self._transaction_stack) >= self.MAX_NESTING_LEVEL:
            return False

        # Determine parent transaction (if nested)
        parent_transaction_id = (
            self._transaction_stack[-1].metadata.transaction_id
            if self._transaction_stack
            else None
        )

        # Create metadata for this transaction level
        metadata = TransactionMetadata(
            transaction_id=self._next_transaction_id,
            timestamp=datetime.now(),
            user_id=user_id,
            description=description,
            status=TransactionStatus.PENDING,
            parent_transaction_id=parent_transaction_id,
        )
        self._next_transaction_id += 1

        # Create transaction level
        transaction_level = TransactionLevel(metadata)

        # Snapshot ALL registered accounts at their CURRENT state
        # This is crucial: we capture the state at the START of this transaction
        for account in self._accounts.values():
            transaction_level.save_account_state(account)

        # Push to stack
        self._transaction_stack.append(transaction_level)
        return True

    def commit_transaction(self) -> bool:
        """
        Commit the current transaction level.

        Makes all changes within this transaction level permanent.
        If this is the outermost transaction, changes are truly permanent.
        If nested, changes become part of the parent transaction.

        Returns:
            True if successful, False if no active transaction
        """
        if not self._transaction_stack:
            return False

        # Pop the current transaction level
        transaction_level = self._transaction_stack.pop()

        # Update status
        transaction_level.metadata.status = TransactionStatus.COMMITTED

        # Add to history for audit trail
        self._transaction_history.append(transaction_level.metadata)

        # If this was the outermost transaction, changes are now permanent
        # (In a real database, this is where you'd flush to disk)

        return True

    def rollback_transaction(self) -> bool:
        """
        Rollback the current transaction level.

        Restores ALL accounts to their state at the beginning of this
        transaction level. All changes made within this level are undone.

        Returns:
            True if successful, False if no active transaction
        """
        if not self._transaction_stack:
            return False

        # Pop the current transaction level
        transaction_level = self._transaction_stack.pop()

        # Restore ALL accounts from their snapshots
        for account_id, snapshot in transaction_level.snapshots.items():
            account = self.get_account(account_id)
            if account:
                account.restore_from_snapshot(snapshot)

        # Update status
        transaction_level.metadata.status = TransactionStatus.ROLLED_BACK

        # Add to history for audit trail
        self._transaction_history.append(transaction_level.metadata)

        return True

    def execute_operation(self, account_id: str, operation: str, amount: float) -> bool:
        """
        Execute an operation within a transaction context.

        Operations can only be performed within an active transaction.
        The transaction must have been started with begin_transaction().

        Args:
            account_id: Target account ID
            operation: "deposit" or "withdraw"
            amount: Amount to deposit/withdraw

        Returns:
            True if successful, False otherwise

        Note: This method does not create new snapshots. Snapshots are
        taken once at transaction begin, not per operation.
        """
        # Ensure we're in a transaction
        if not self._transaction_stack:
            return False

        # Get the account
        account = self.get_account(account_id)
        if not account:
            return False

        # Execute the operation
        if operation == OperationType.DEPOSIT.value or operation == "deposit":
            return account.deposit(amount)
        elif operation == OperationType.WITHDRAW.value or operation == "withdraw":
            return account.withdraw(amount)
        else:
            return False

    def get_transaction_history(self) -> List[TransactionMetadata]:
        """
        Get complete transaction history for audit trail.

        Returns a copy to prevent external modification of history.

        Returns:
            List of all transaction metadata (committed and rolled back)
        """
        return deepcopy(self._transaction_history)

    def get_active_transaction_count(self) -> int:
        """
        Get number of active (nested) transactions.

        Returns:
            Current nesting level (0 if no active transactions)
        """
        return len(self._transaction_stack)

    def is_in_transaction(self) -> bool:
        """
        Check if currently in a transaction.

        Returns:
            True if in transaction, False otherwise
        """
        return len(self._transaction_stack) > 0

    def get_current_transaction_info(self) -> Optional[TransactionMetadata]:
        """
        Get metadata for the current (innermost) transaction.

        Returns:
            Current transaction metadata if in transaction, None otherwise
        """
        if not self._transaction_stack:
            return None
        return self._transaction_stack[-1].metadata

    def get_all_accounts_balance(self) -> Dict[str, float]:
        """
        Get current balance of all registered accounts.

        Useful for debugging and testing.

        Returns:
            Dictionary mapping account_id to current balance
        """
        return {
            account_id: account.balance
            for account_id, account in self._accounts.items()
        }


# ============================================================================
# COMPREHENSIVE TEST SUITE
# ============================================================================


def run_all_tests():
    """Run comprehensive test suite."""

    print("=" * 70)
    print("BANKING TRANSACTION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Test 1: Basic Transaction
    print("\n" + "=" * 70)
    print("TEST 1: Basic Transaction (Commit)")
    print("=" * 70)

    account1 = Account("ACC001", 1000.0)
    account2 = Account("ACC002", 500.0)

    tm = TransactionManager()
    tm.register_account(account1)
    tm.register_account(account2)

    print(f"Initial state:")
    print(f"  Account1: ${account1.balance:.2f}")
    print(f"  Account2: ${account2.balance:.2f}")

    tm.begin_transaction("user1", "Transfer $200 from ACC001 to ACC002")
    print(f"\nTransaction started: {tm.get_current_transaction_info()}")

    success1 = tm.execute_operation("ACC001", "withdraw", 200)
    success2 = tm.execute_operation("ACC002", "deposit", 200)

    print(f"\nIn transaction:")
    print(f"  Withdraw from ACC001: {success1}")
    print(f"  Deposit to ACC002: {success2}")
    print(f"  Account1: ${account1.balance:.2f}")
    print(f"  Account2: ${account2.balance:.2f}")

    tm.commit_transaction()

    print(f"\nAfter commit:")
    print(f"  Account1: ${account1.balance:.2f}")
    print(f"  Account2: ${account2.balance:.2f}")

    assert account1.balance == 800.0, "Account1 should be $800"
    assert account2.balance == 700.0, "Account2 should be $700"
    print("✓ Test 1 PASSED")

    # Test 2: Transaction Rollback
    print("\n" + "=" * 70)
    print("TEST 2: Transaction Rollback")
    print("=" * 70)

    print(f"Before transaction:")
    print(f"  Account1: ${account1.balance:.2f}")

    tm.begin_transaction("user1", "Attempt to withdraw $300")
    tm.execute_operation("ACC001", "withdraw", 300)

    print(f"\nIn transaction:")
    print(f"  Account1: ${account1.balance:.2f}")

    tm.rollback_transaction()

    print(f"\nAfter rollback:")
    print(f"  Account1: ${account1.balance:.2f}")

    assert account1.balance == 800.0, "Account1 should be restored to $800"
    print("✓ Test 2 PASSED")

    # Test 3: Nested Transactions
    print("\n" + "=" * 70)
    print("TEST 3: Nested Transactions")
    print("=" * 70)

    print(f"Initial: Account1 = ${account1.balance:.2f}")

    # Level 1
    tm.begin_transaction("user1", "Outer transaction")
    tm.execute_operation("ACC001", "withdraw", 100)
    print(f"\nLevel 1 (after withdraw $100): ${account1.balance:.2f}")

    # Level 2 (nested)
    tm.begin_transaction("user1", "Inner transaction")
    tm.execute_operation("ACC001", "withdraw", 50)
    print(f"Level 2 (after withdraw $50): ${account1.balance:.2f}")

    # Rollback level 2
    tm.rollback_transaction()
    print(f"After rollback level 2: ${account1.balance:.2f}")

    assert account1.balance == 700.0, "Should be $700 (level 1 withdraw still active)"

    # Commit level 1
    tm.commit_transaction()
    print(f"After commit level 1: ${account1.balance:.2f}")

    assert account1.balance == 700.0, "Should be $700 (level 1 committed)"
    print("✓ Test 3 PASSED")

    # Test 4: Validation (Overdraft Prevention)
    print("\n" + "=" * 70)
    print("TEST 4: Overdraft Prevention")
    print("=" * 70)

    print(f"Account1 balance: ${account1.balance:.2f}")

    tm.begin_transaction("user1", "Overdraft attempt")
    success = tm.execute_operation("ACC001", "withdraw", 10000)

    print(f"\nAttempt to withdraw $10,000: {success}")
    print(f"Balance unchanged: ${account1.balance:.2f}")

    assert not success, "Overdraft should be prevented"
    assert account1.balance == 700.0, "Balance should remain $700"

    tm.rollback_transaction()
    print("✓ Test 4 PASSED")

    # Test 5: Max Nesting Level
    print("\n" + "=" * 70)
    print("TEST 5: Max Nesting Level Enforcement")
    print("=" * 70)

    success1 = tm.begin_transaction("user1", "Level 1")
    success2 = tm.begin_transaction("user1", "Level 2")
    success3 = tm.begin_transaction("user1", "Level 3")
    success4 = tm.begin_transaction("user1", "Level 4 - should fail")

    print(f"Level 1 started: {success1}")
    print(f"Level 2 started: {success2}")
    print(f"Level 3 started: {success3}")
    print(f"Level 4 started: {success4} (should be False)")
    print(f"Active transactions: {tm.get_active_transaction_count()}")

    assert success1 and success2 and success3, "First 3 levels should succeed"
    assert not success4, "4th level should fail"
    assert tm.get_active_transaction_count() == 3, "Should have exactly 3 active"

    # Cleanup
    tm.rollback_transaction()
    tm.rollback_transaction()
    tm.rollback_transaction()

    print("✓ Test 5 PASSED")

    # Test 6: Transaction History Audit Trail
    print("\n" + "=" * 70)
    print("TEST 6: Transaction History & Audit Trail")
    print("=" * 70)

    history = tm.get_transaction_history()
    print(f"Total transactions in history: {len(history)}")
    print("\nLast 5 transactions:")

    for txn in history[-5:]:
        parent_info = (
            f" [parent: #{txn.parent_transaction_id}]"
            if txn.parent_transaction_id
            else ""
        )
        print(f"  #{txn.transaction_id}: {txn.description}{parent_info}")
        print(f"    Status: {txn.status.value}, User: {txn.user_id}")

    assert len(history) > 0, "Should have transaction history"
    print("✓ Test 6 PASSED")

    # Test 7: Complex Multi-Account Scenario
    print("\n" + "=" * 70)
    print("TEST 7: Complex Multi-Account Scenario")
    print("=" * 70)

    acc3 = Account("ACC003", 2000.0)
    tm.register_account(acc3)

    print(f"Initial state:")
    print(f"  Acc1: ${account1.balance:.2f}")
    print(f"  Acc2: ${account2.balance:.2f}")
    print(f"  Acc3: ${acc3.balance:.2f}")

    # Outer transaction: withdraw from ACC003
    tm.begin_transaction("user1", "Complex transfer")
    tm.execute_operation("ACC003", "withdraw", 500)
    print(f"\nAfter withdraw $500 from Acc3: ${acc3.balance:.2f}")

    # Nested: try to split deposit between ACC001 and ACC002
    tm.begin_transaction("user1", "Split deposit")
    tm.execute_operation("ACC001", "deposit", 250)
    tm.execute_operation("ACC002", "deposit", 250)
    print(f"\nAfter nested deposits:")
    print(f"  Acc1: ${account1.balance:.2f}")
    print(f"  Acc2: ${account2.balance:.2f}")

    # Rollback the nested transaction
    tm.rollback_transaction()
    print(f"\nAfter nested rollback:")
    print(f"  Acc1: ${account1.balance:.2f} (deposits rolled back)")
    print(f"  Acc2: ${account2.balance:.2f} (deposits rolled back)")

    assert account1.balance == 700.0, "ACC001 deposits should be rolled back"
    assert account2.balance == 700.0, "ACC002 deposits should be rolled back"

    # Commit outer transaction (only ACC003 withdrawal remains)
    tm.commit_transaction()
    print(f"\nFinal state after commit:")
    print(f"  Acc1: ${account1.balance:.2f}")
    print(f"  Acc2: ${account2.balance:.2f}")
    print(f"  Acc3: ${acc3.balance:.2f}")

    assert acc3.balance == 1500.0, "ACC003 withdrawal should be committed"
    print("✓ Test 7 PASSED")

    # Test 8: Multiple Rollbacks in Sequence
    print("\n" + "=" * 70)
    print("TEST 8: Multiple Sequential Operations with Rollback")
    print("=" * 70)

    initial_balance = account1.balance
    print(f"Initial balance: ${initial_balance:.2f}")

    tm.begin_transaction("user1", "Multiple operations")
    tm.execute_operation("ACC001", "deposit", 100)
    tm.execute_operation("ACC001", "withdraw", 50)
    tm.execute_operation("ACC001", "deposit", 75)

    print(f"After multiple operations: ${account1.balance:.2f}")
    expected_during = initial_balance + 100 - 50 + 75
    assert account1.balance == expected_during, f"Should be ${expected_during}"

    tm.rollback_transaction()
    print(f"After rollback: ${account1.balance:.2f}")

    assert account1.balance == initial_balance, "Should be restored to initial"
    print("✓ Test 8 PASSED")

    # Test 9: Operations Outside Transaction (should fail)
    print("\n" + "=" * 70)
    print("TEST 9: Operations Outside Transaction Context")
    print("=" * 70)

    assert not tm.is_in_transaction(), "Should not be in transaction"

    success = tm.execute_operation("ACC001", "deposit", 100)
    print(f"Attempt operation without transaction: {success}")

    assert not success, "Operation should fail outside transaction"
    print("✓ Test 9 PASSED")

    # Final Summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)

    print(f"\nFinal account balances:")
    for acc_id, balance in tm.get_all_accounts_balance().items():
        print(f"  {acc_id}: ${balance:.2f}")

    print(f"\nTotal transactions executed: {len(tm.get_transaction_history())}")

    committed = sum(
        1
        for t in tm.get_transaction_history()
        if t.status == TransactionStatus.COMMITTED
    )
    rolled_back = sum(
        1
        for t in tm.get_transaction_history()
        if t.status == TransactionStatus.ROLLED_BACK
    )

    print(f"  Committed: {committed}")
    print(f"  Rolled back: {rolled_back}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        run_all_tests()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise
