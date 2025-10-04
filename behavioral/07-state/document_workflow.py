from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================
class InvalidStateTransition(Exception):
    """Custom exception for invalid state transitions"""

    pass


# ============================================================================
# ENUMS FOR BETTER TYPE SAFETY
# ============================================================================
class ActionType(Enum):
    """Enumeration of possible document actions"""

    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PUBLISHED = "Published"


# ============================================================================
# HISTORY ENTRY CLASS
# ============================================================================
@dataclass(frozen=True)
class HistoryEntry:
    """Represents a single state transition in the document's history"""

    timestamp: datetime
    from_state: str
    to_state: str
    action: ActionType
    actor: Optional[str] = None
    reason: Optional[str] = None

    def __str__(self) -> str:
        """Format: 2025-10-04 10:00:00 | Submitted: Draft → UnderReview by Bob"""
        actor_str = f" by {self.actor}" if self.actor else ""
        reason_str = f" | Reason: {self.reason}" if self.reason else ""
        return (
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{self.action.value}: {self.from_state} → {self.to_state}"
            f"{actor_str}{reason_str}"
        )


# ============================================================================
# ABSTRACT STATE CLASS
# ============================================================================
class DocumentState(ABC):
    """Abstract base class for all document states"""

    # Define allowed transitions for validation
    ALLOWED_TRANSITIONS = {
        "Draft": ["UnderReview"],
        "UnderReview": ["Approved", "Draft"],
        "Approved": ["Published", "Draft"],
        "Published": [],
    }

    @abstractmethod
    def get_state_name(self) -> str:
        """Return the name of this state"""
        pass

    @abstractmethod
    def submit(self, context: "Document", reviewer: Optional[str] = None) -> None:
        """Submit document for review"""
        pass

    @abstractmethod
    def approve(self, context: "Document", approver: Optional[str] = None) -> None:
        """Approve the document"""
        pass

    @abstractmethod
    def reject(
        self, context: "Document", reason: str, actor: Optional[str] = None
    ) -> None:
        """Reject the document with a reason"""
        pass

    @abstractmethod
    def publish(self, context: "Document", publisher: Optional[str] = None) -> None:
        """Publish the document"""
        pass

    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """Return list of available actions in this state"""
        pass

    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is allowed"""
        current = self.get_state_name()
        return target_state in self.ALLOWED_TRANSITIONS.get(current, [])

    def __str__(self) -> str:
        return self.get_state_name()


# ============================================================================
# CONCRETE STATE CLASSES
# ============================================================================
class DraftState(DocumentState):
    """Initial state - document is being written"""

    def get_state_name(self) -> str:
        return "Draft"

    def submit(self, context: "Document", reviewer: Optional[str] = None) -> None:
        """Transition from Draft to UnderReview"""
        context.transition_to(
            new_state=UnderReviewState(), action=ActionType.SUBMITTED, actor=reviewer
        )

    def approve(self, context: "Document", approver: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot approve a document in Draft state. "
            "Document must be submitted for review first."
        )

    def reject(
        self, context: "Document", reason: str, actor: Optional[str] = None
    ) -> None:
        raise InvalidStateTransition(
            "Cannot reject a document in Draft state. "
            "Document must be submitted for review first."
        )

    def publish(self, context: "Document", publisher: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot publish a document in Draft state. "
            "Document must go through review and approval process."
        )

    def get_available_actions(self) -> List[str]:
        return ["submit"]


class UnderReviewState(DocumentState):
    """Document is being reviewed"""

    def get_state_name(self) -> str:
        return "UnderReview"

    def submit(self, context: "Document", reviewer: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Document is already under review. "
            "Cannot submit again until approved or rejected."
        )

    def approve(self, context: "Document", approver: Optional[str] = None) -> None:
        """Transition from UnderReview to Approved"""
        context.transition_to(
            new_state=ApprovedState(), action=ActionType.APPROVED, actor=approver
        )

    def reject(
        self, context: "Document", reason: str, actor: Optional[str] = None
    ) -> None:
        """Transition from UnderReview back to Draft with reason"""
        if not reason or not reason.strip():
            raise ValueError("Rejection reason is required")

        context.transition_to(
            new_state=DraftState(),
            action=ActionType.REJECTED,
            actor=actor,
            reason=reason,
        )

    def publish(self, context: "Document", publisher: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot publish a document under review. "
            "Document must be approved first."
        )

    def get_available_actions(self) -> List[str]:
        return ["approve", "reject"]


class ApprovedState(DocumentState):
    """Document is approved and ready to publish"""

    def get_state_name(self) -> str:
        return "Approved"

    def submit(self, context: "Document", reviewer: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot submit an approved document. "
            "Document is already approved and ready to publish."
        )

    def approve(self, context: "Document", approver: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Document is already approved. " "You can now publish it."
        )

    def reject(
        self, context: "Document", reason: str, actor: Optional[str] = None
    ) -> None:
        """Transition from Approved back to Draft (rare case)"""
        if not reason or not reason.strip():
            raise ValueError("Rejection reason is required")

        context.transition_to(
            new_state=DraftState(),
            action=ActionType.REJECTED,
            actor=actor,
            reason=reason,
        )

    def publish(self, context: "Document", publisher: Optional[str] = None) -> None:
        """Transition from Approved to Published"""
        # Use provided publisher or default to document author
        actor = publisher or context.author
        context.transition_to(
            new_state=PublishedState(), action=ActionType.PUBLISHED, actor=actor
        )

    def get_available_actions(self) -> List[str]:
        return ["publish", "reject"]


class PublishedState(DocumentState):
    """Final state - document is published and immutable"""

    def get_state_name(self) -> str:
        return "Published"

    def submit(self, context: "Document", reviewer: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot submit a published document. " "Published documents are immutable."
        )

    def approve(self, context: "Document", approver: Optional[str] = None) -> None:
        raise InvalidStateTransition(
            "Cannot approve a published document. " "Document is already published."
        )

    def reject(
        self, context: "Document", reason: str, actor: Optional[str] = None
    ) -> None:
        raise InvalidStateTransition(
            "Cannot reject a published document. " "Published documents are immutable."
        )

    def publish(self, context: "Document", publisher: Optional[str] = None) -> None:
        raise InvalidStateTransition("Document is already published.")

    def get_available_actions(self) -> List[str]:
        return []  # No actions available in final state


# ============================================================================
# DOCUMENT CONTEXT CLASS
# ============================================================================
class Document:
    """Context class representing a document with workflow state"""

    def __init__(self, title: str, author: str, content: str):
        self.title = title
        self.author = author
        self.content = content
        self._state: DocumentState = DraftState()
        self._history: List[HistoryEntry] = []

        print(
            f"📄 Document '{title}' created by {author} "
            f"in {self._state.get_state_name()} state"
        )

    @property
    def state(self) -> DocumentState:
        """Get current state (read-only)"""
        return self._state

    def transition_to(
        self,
        new_state: DocumentState,
        action: ActionType,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Transition to a new state and record in history

        Args:
            new_state: The state to transition to
            action: The action that caused this transition
            actor: Who performed the action
            reason: Reason for the action (required for rejections)
        """
        from_state_name = self._state.get_state_name()
        to_state_name = new_state.get_state_name()

        # Validate transition is allowed
        if not self._state.can_transition_to(to_state_name):
            raise InvalidStateTransition(
                f"Invalid transition from {from_state_name} to {to_state_name}"
            )

        timestamp = datetime.now()

        # Create history entry
        entry = HistoryEntry(
            timestamp=timestamp,
            from_state=from_state_name,
            to_state=to_state_name,
            action=action,
            actor=actor,
            reason=reason,
        )
        self._history.append(entry)

        # Update state
        self._state = new_state

        # Print transition message
        action_str = action.value
        actor_str = f" by {actor}" if actor else ""
        reason_str = f" | Reason: {reason}" if reason else ""
        print(
            f"✅ {action_str}: {from_state_name} → {to_state_name}"
            f"{actor_str}{reason_str}"
        )

    # Delegate actions to current state
    def submit(self, reviewer: Optional[str] = None) -> None:
        """Submit document for review"""
        self._state.submit(self, reviewer)

    def approve(self, approver: Optional[str] = None) -> None:
        """Approve the document"""
        self._state.approve(self, approver)

    def reject(self, reason: str, actor: Optional[str] = None) -> None:
        """Reject the document with a reason"""
        self._state.reject(self, reason, actor)

    def publish(self, publisher: Optional[str] = None) -> None:
        """Publish the document"""
        self._state.publish(self, publisher)

    # Query methods
    def get_available_actions(self) -> List[str]:
        """Get list of actions available in current state"""
        return self._state.get_available_actions()

    def get_current_state(self) -> str:
        """Get current state name"""
        return self._state.get_state_name()

    def is_published(self) -> bool:
        """Check if document is published"""
        return isinstance(self._state, PublishedState)

    def is_draft(self) -> bool:
        """Check if document is in draft state"""
        return isinstance(self._state, DraftState)

    # History methods
    def print_history(self) -> None:
        """Print complete state transition history"""
        print("\n" + "=" * 70)
        print(f"📋 History for: {self.title}")
        print("=" * 70)

        if not self._history:
            print("No transitions yet.")
        else:
            for entry in self._history:
                print(entry)

        print("=" * 70)

    def get_history(self) -> List[HistoryEntry]:
        """Return history for programmatic access"""
        return self._history.copy()

    def get_history_by_state(self, state_name: str) -> List[HistoryEntry]:
        """Get history entries involving a specific state"""
        return [
            entry
            for entry in self._history
            if entry.from_state == state_name or entry.to_state == state_name
        ]

    def get_rejections(self) -> List[HistoryEntry]:
        """Get all rejection history"""
        return [entry for entry in self._history if entry.action == ActionType.REJECTED]

    def get_transition_count(self) -> int:
        """Get total number of state transitions"""
        return len(self._history)

    def __str__(self) -> str:
        return f"Document('{self.title}', state={self._state.get_state_name()})"

    def __repr__(self) -> str:
        return (
            f"Document(title='{self.title}', author='{self.author}', "
            f"state={self._state.get_state_name()}, "
            f"transitions={self.get_transition_count()})"
        )


# ============================================================================
# TEST SCENARIOS
# ============================================================================
def test_happy_path():
    """Test normal workflow: Draft → UnderReview → Approved → Published"""
    print("\n" + "=" * 70)
    print("TEST 1: Happy Path Workflow")
    print("=" * 70)

    doc = Document(
        title="Design Patterns Guide",
        author="Alice",
        content="Comprehensive guide to design patterns...",
    )

    print(f"\n📊 Available actions: {doc.get_available_actions()}")

    doc.submit(reviewer="Bob")
    print(f"📊 Available actions: {doc.get_available_actions()}")

    doc.approve(approver="Charlie")
    print(f"📊 Available actions: {doc.get_available_actions()}")

    doc.publish(publisher="Diana")
    print(f"📊 Available actions: {doc.get_available_actions()}")
    print(f"📊 Is published? {doc.is_published()}")

    doc.print_history()


def test_rejection_workflow():
    """Test rejection and resubmission"""
    print("\n" + "=" * 70)
    print("TEST 2: Rejection and Resubmission")
    print("=" * 70)

    doc = Document(
        title="State Pattern Tutorial",
        author="Dave",
        content="Introduction to State pattern...",
    )

    doc.submit(reviewer="Eve")
    doc.reject(reason="Needs more examples and diagrams", actor="Eve")

    print(f"\n📊 Document is back in Draft: {doc.is_draft()}")
    print(f"📊 Total rejections: {len(doc.get_rejections())}")

    # Resubmit after improvements
    doc.submit(reviewer="Eve")
    doc.approve(approver="Frank")
    doc.publish()

    doc.print_history()

    # Show only rejections
    print("\n🔴 Rejection History:")
    for rejection in doc.get_rejections():
        print(f"  - {rejection}")


def test_invalid_transitions():
    """Test that invalid transitions are handled properly"""
    print("\n" + "=" * 70)
    print("TEST 3: Invalid Transitions")
    print("=" * 70)

    doc = Document(
        title="Invalid Transitions Test",
        author="Grace",
        content="Testing error handling...",
    )

    # Try to publish from Draft
    print("\n🔍 Attempting to publish from Draft state...")
    try:
        doc.publish()
    except InvalidStateTransition as e:
        print(f"✅ Caught expected exception: {e}")

    # Try to approve from Draft
    print("\n🔍 Attempting to approve from Draft state...")
    try:
        doc.approve(approver="Heidi")
    except InvalidStateTransition as e:
        print(f"✅ Caught expected exception: {e}")

    # Proper workflow
    doc.submit(reviewer="Ivan")
    doc.approve(approver="Judy")
    doc.publish()

    # Try to modify published document
    print("\n🔍 Attempting to submit a published document...")
    try:
        doc.submit(reviewer="Kevin")
    except InvalidStateTransition as e:
        print(f"✅ Caught expected exception: {e}")

    print(f"\n📊 Final state: {doc.get_current_state()}")


def test_available_actions():
    """Test that available actions change with state"""
    print("\n" + "=" * 70)
    print("TEST 4: Available Actions")
    print("=" * 70)

    doc = Document(
        title="Available Actions Demo",
        author="Laura",
        content="Demonstrating state-specific actions...",
    )

    states_and_actions = []

    # Draft state
    states_and_actions.append((doc.get_current_state(), doc.get_available_actions()))

    # UnderReview state
    doc.submit(reviewer="Mallory")
    states_and_actions.append((doc.get_current_state(), doc.get_available_actions()))

    # Approved state
    doc.approve(approver="Niaj")
    states_and_actions.append((doc.get_current_state(), doc.get_available_actions()))

    # Published state
    doc.publish()
    states_and_actions.append((doc.get_current_state(), doc.get_available_actions()))

    # Display results
    print("\n📊 State-Specific Available Actions:")
    print("-" * 70)
    for state, actions in states_and_actions:
        actions_str = ", ".join(actions) if actions else "None"
        print(f"  {state:15} → [{actions_str}]")


def test_rejection_validation():
    """Test that rejections require a reason"""
    print("\n" + "=" * 70)
    print("TEST 5: Rejection Validation")
    print("=" * 70)

    doc = Document(
        title="Rejection Validation Test",
        author="Oscar",
        content="Testing rejection validation...",
    )

    doc.submit(reviewer="Patricia")

    print("\n🔍 Attempting to reject without reason...")
    try:
        doc.reject(reason="", actor="Patricia")
    except ValueError as e:
        print(f"✅ Caught expected exception: {e}")

    print("\n🔍 Attempting to reject with whitespace-only reason...")
    try:
        doc.reject(reason="   ", actor="Patricia")
    except ValueError as e:
        print(f"✅ Caught expected exception: {e}")

    print("\n✅ Rejecting with proper reason...")
    doc.reject(reason="Content needs significant revision", actor="Patricia")
    print(f"📊 Successfully rejected. Current state: {doc.get_current_state()}")


def test_advanced_queries():
    """Test advanced history query methods"""
    print("\n" + "=" * 70)
    print("TEST 6: Advanced History Queries")
    print("=" * 70)

    doc = Document(
        title="Complex Workflow", author="Quinn", content="Testing complex workflows..."
    )

    # Complex workflow with multiple rejections
    doc.submit(reviewer="Rachel")
    doc.reject(reason="First draft needs work", actor="Rachel")

    doc.submit(reviewer="Rachel")
    doc.reject(reason="Still needs improvements", actor="Rachel")

    doc.submit(reviewer="Rachel")
    doc.approve(approver="Sam")
    doc.publish()

    # Query history
    print(f"\n📊 Total transitions: {doc.get_transition_count()}")
    print(f"📊 Total rejections: {len(doc.get_rejections())}")

    draft_history = doc.get_history_by_state("Draft")
    print(f"📊 Transitions involving Draft state: {len(draft_history)}")

    print("\n📋 All Rejections:")
    for rejection in doc.get_rejections():
        print(f"  - {rejection.reason}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    test_happy_path()
    test_rejection_workflow()
    test_invalid_transitions()
    test_available_actions()
    test_rejection_validation()
    test_advanced_queries()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
