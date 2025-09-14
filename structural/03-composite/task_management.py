from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskComponent(ABC):
    """Abstract base class for all task components"""

    def __init__(self, name: str):
        self._name = name
        self._is_complete = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @abstractmethod
    def get_total_tasks(self) -> int:
        """Return total number of tasks in this component"""
        pass

    @abstractmethod
    def get_completed_tasks(self) -> int:
        """Return number of completed tasks in this component"""
        pass

    @abstractmethod
    def get_progress(self) -> float:
        """Return completion percentage as float between 0.0 and 1.0"""
        pass

    @abstractmethod
    def get_priority_summary(self) -> Dict[Priority, int]:
        """Return dictionary with count of tasks at each priority level"""
        pass

    @abstractmethod
    def display(self, indent: int = 0) -> None:
        """Display the component hierarchy with indentation"""
        pass

    @abstractmethod
    def mark_complete(self) -> None:
        """Mark this component as complete"""
        pass

    @abstractmethod
    def find_task_by_name(self, name: str) -> Optional["TaskComponent"]:
        """Find and return a task by name, or None if not found"""
        pass


class SimpleTask(TaskComponent):
    """Leaf component representing a basic task"""

    def __init__(self, name: str, priority: Priority = Priority.MEDIUM):
        super().__init__(name)
        self._priority = priority

    @property
    def priority(self) -> Priority:
        return self._priority

    def get_total_tasks(self) -> int:
        return 1

    def get_completed_tasks(self) -> int:
        return 1 if self.is_complete else 0

    def get_progress(self) -> float:
        return 1.0 if self.is_complete else 0.0

    def get_priority_summary(self) -> Dict[Priority, int]:
        summary = {priority: 0 for priority in Priority}
        summary[self.priority] = 1
        return summary

    def display(self, indent: int = 0) -> None:
        completed_symbol = "✓" if self.is_complete else "✗"
        return (
            f"  " * indent
            + f"Task: {self.name} [{self.priority.name}] [{completed_symbol}]"
        )

    def mark_complete(self) -> None:
        self._is_complete = True

    def find_task_by_name(self, name: str) -> Optional["TaskComponent"]:
        return self if self.name == name else None


class TaskGroup(TaskComponent):
    """Composite component that can contain other tasks and task groups"""

    def __init__(self, name: str):
        super().__init__(name)
        self._children: List[TaskComponent] = []

    def add(self, component: TaskComponent) -> None:
        self._children.append(component)

    def remove(self, component: TaskComponent) -> None:
        self._children.remove(component)

    @property
    def children(self) -> List[TaskComponent]:
        return self._children.copy()

    def get_total_tasks(self) -> int:
        return sum(child.get_total_tasks() for child in self._children)

    def get_completed_tasks(self) -> int:
        return sum(child.get_completed_tasks() for child in self._children)

    def get_progress(self) -> float:
        completed_tasks = self.get_completed_tasks()
        total_tasks = self.get_total_tasks()
        return completed_tasks / total_tasks if total_tasks > 0 else 1.0

    def get_priority_summary(self) -> Dict[Priority, int]:
        summary = {priority: 0 for priority in Priority}
        for child in self._children:
            child_summary = child.get_priority_summary()
            for priority, count in child_summary.items():
                summary[priority] += count
        return summary

    @property
    def is_complete(self) -> bool:
        return len(self._children) == 0 or all(
            child.is_complete for child in self._children
        )

    def display(self, indent: int = 0) -> None:
        completed_tasks = self.get_completed_tasks()
        total_tasks = self.get_total_tasks()

        print(
            " " * indent
            + f"Group: {self.name} ({completed_tasks}/{total_tasks} tasks complete)"
        )
        for child in self._children:
            child.display(indent + 2)

    def mark_complete(self) -> None:
        for child in self._children:
            child.mark_complete()

    def find_task_by_name(self, name: str) -> Optional["TaskComponent"]:
        if self.name == name:
            return self
        for child in self._children:
            result = child.find_task_by_name(name)
            if result:
                return result
        return None


class Project(TaskGroup):
    """Special task group with additional project metadata"""

    def __init__(self, name: str, deadline: str, budget: float):
        super().__init__(name)
        self._deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        self._budget = budget

    @property
    def deadline(self) -> date:
        return self._deadline

    @property
    def budget(self) -> float:
        return self._budget

    def display(self, indent: int = 0) -> None:
        completed_tasks = self.get_completed_tasks()
        total_tasks = self.get_total_tasks()

        print(
            " " * indent
            + f"Project: {self.name} ({completed_tasks}/{total_tasks} tasks complete) - Deadline: {self.deadline}, Budget: ${self.budget:.2f}"
        )
        for child in self._children:
            child.display(indent + 2)


class Milestone(TaskGroup):
    """Special task group representing a milestone with a deadline"""

    def __init__(self, name: str, deadline: str):
        super().__init__(name)
        self._deadline = datetime.strptime(deadline, "%Y-%m-%d").date()

    @property
    def deadline(self) -> date:
        return self._deadline

    def display(self, indent: int = 0) -> None:
        completed_tasks = self.get_completed_tasks()
        total_tasks = self.get_total_tasks()

        print(
            " " * indent
            + f"Milestone: {self.name} ({completed_tasks}/{total_tasks} tasks complete) - Due: {self.deadline}"
        )
        for child in self._children:
            child.display(indent + 2)


if __name__ == "__main__":
    # Create a comprehensive project hierarchy
    mobile_app = Project("Mobile App Development", "2024-12-31", 100000)

    # Backend tasks
    backend = TaskGroup("Backend Development")
    backend.add(SimpleTask("Setup Database", Priority.HIGH))
    backend.add(SimpleTask("Create REST API", Priority.HIGH))
    backend.add(SimpleTask("Implement Authentication", Priority.CRITICAL))
    backend.add(SimpleTask("Write Unit Tests", Priority.MEDIUM))

    # Frontend tasks with milestone
    frontend = TaskGroup("Frontend Development")
    ui_milestone = Milestone("UI Complete", "2024-10-15")
    ui_milestone.add(SimpleTask("Design UI Mockups", Priority.HIGH))
    ui_milestone.add(SimpleTask("Implement Responsive Layout", Priority.MEDIUM))
    ui_milestone.add(SimpleTask("User Testing", Priority.MEDIUM))

    frontend.add(ui_milestone)
    frontend.add(SimpleTask("Performance Optimization", Priority.LOW))

    # Build the hierarchy
    mobile_app.add(backend)
    mobile_app.add(frontend)

    # Demonstrate functionality
    print("=== INITIAL PROJECT STATUS ===")
    mobile_app.display()
    print(f"\nProject progress: {mobile_app.get_progress():.1%}")
    print(f"Priority summary: {mobile_app.get_priority_summary()}")

    # Complete some tasks
    print(f"\n=== COMPLETING SOME TASKS ===")

    # Find and complete specific tasks
    tasks_to_complete = ["Setup Database", "Design UI Mockups", "User Testing"]
    for task_name in tasks_to_complete:
        task = mobile_app.find_task_by_name(task_name)
        if task:
            task.mark_complete()
            print(f"✓ Marked '{task.name}' as complete")

    print(f"\n=== UPDATED PROJECT STATUS ===")
    mobile_app.display()
    print(f"\nProject progress: {mobile_app.get_progress():.1%}")
    print(f"Priority summary: {mobile_app.get_priority_summary()}")

    # Test milestone completion
    print(f"\n=== MILESTONE STATUS ===")
    ui_milestone = mobile_app.find_task_by_name("UI Complete")
    print(f"UI Milestone complete: {ui_milestone.is_complete}")
    print(f"UI Milestone progress: {ui_milestone.get_progress():.1%}")
