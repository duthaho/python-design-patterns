"""Exceptions for the factory system."""


class FactoryException(Exception):
    """Base exception for factory errors."""

    pass


class TaskNotRegisteredException(FactoryException):
    """Raised when trying to create an unregistered task type."""

    def __init__(self, task_type: str):
        self.task_type = task_type
        super().__init__(f"Task type '{task_type}' is not registered")


class TaskRegistrationException(FactoryException):
    """Raised when task registration fails."""

    pass


class InvalidTaskConfigException(FactoryException):
    """Raised when task configuration is invalid."""

    pass
