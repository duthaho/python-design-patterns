"""Factory for creating tasks from configuration."""

import inspect
import logging
import threading
from typing import Any, Dict, List, Optional, Type

import yaml

from ..core.pipeline import Pipeline
from ..core.task import Task
from .exceptions import InvalidTaskConfigException, TaskNotRegisteredException
from .task_registry import TaskRegistry

logger = logging.getLogger(__name__)


class TaskFactory:
    """
    Factory for creating tasks from configuration (Factory Pattern).

    Supports:
    - Creating tasks by type name
    - Building pipelines from configuration
    - Decorator-based registration
    """

    # Class variable for default global instance (Singleton-like)
    _default_instance: Optional["TaskFactory"] = None
    _lock = threading.Lock()

    def __init__(self, registry: Optional[TaskRegistry] = None):
        """
        Initialize task factory.

        Args:
            registry: Optional custom registry. If None, creates new registry.
        """
        self._registry = registry if registry else TaskRegistry()

    @classmethod
    def get_default(cls) -> "TaskFactory":
        """
        Get the default global factory instance (Singleton pattern).

        Returns:
            The default TaskFactory instance
        """
        if cls._default_instance is None:
            with cls._lock:
                if cls._default_instance is None:
                    cls._default_instance = TaskFactory()
        return cls._default_instance

    @classmethod
    def reset_default(cls) -> None:
        """Reset the default factory instance (useful for testing)."""
        cls._default_instance = None

    def register(self, task_type: str, task_class: Type[Task], override: bool = False) -> None:
        """
        Register a task class.

        Args:
            task_type: String identifier for the task
            task_class: The Task class to register
            override: Whether to override existing registration
        """
        self._registry.register(task_type, task_class, override)

    def register_decorator(self, task_type: str):
        """
        Decorator for registering task classes.

        Usage:
            @factory.register_decorator("my_task")
            class MyTask(Task):
                pass

        Args:
            task_type: The task type name

        Returns:
            Decorator function
        """

        def decorator(task_class: Type[Task]) -> Type[Task]:
            self.register(task_type, task_class)
            return task_class

        return decorator

    def create_task(self, task_type: str, task_name: Optional[str] = None, **kwargs) -> Task:
        """
        Create a task instance by type name.

        Args:
            task_type: The registered task type
            task_name: Optional name for the task (defaults to task_type)
            **kwargs: Additional parameters to pass to task constructor

        Returns:
            Created task instance

        Raises:
            TaskNotRegisteredException: If task_type not registered
            InvalidTaskConfigException: If task creation fails
        """
        task_class = self._registry.get(task_type)
        if task_class is None:
            raise TaskNotRegisteredException(task_type)

        if task_name is None:
            task_name = task_type

        try:
            task_instance = task_class(name=task_name, **kwargs)
        except Exception as e:
            raise InvalidTaskConfigException(
                f"Failed to create task '{task_name}' of type '{task_type}': {e}"
            ) from e

        return task_instance

    def create_task_from_config(self, config: Dict[str, Any]) -> Task:
        """
        Create a task from a configuration dictionary.

        Expected config format:
        {
            "type": "task_type_name",
            "name": "optional_task_name",
            "params": {
                "param1": value1,
                "param2": value2
            }
        }

        Args:
            config: Task configuration dictionary

        Returns:
            Created task instance

        Raises:
            InvalidTaskConfigException: If config is invalid
        """
        self.validate_task_config(config)

        task_type = config["type"]
        task_name = config.get("name")
        params = config.get("params", {})

        return self.create_task(task_type, task_name, **params)

    def create_pipeline_from_config(
        self, config: Dict[str, Any], pipeline_name: Optional[str] = None
    ) -> Pipeline:
        """
        Create a complete pipeline from configuration.

        Expected config format:
        {
            "name": "pipeline_name",
            "description": "optional description",
            "tasks": [
                {"type": "task1", "params": {...}},
                {"type": "task2", "params": {...}}
            ]
        }

        Args:
            config: Pipeline configuration dictionary
            pipeline_name: Optional override for pipeline name

        Returns:
            Configured Pipeline instance

        Raises:
            InvalidTaskConfigException: If config is invalid
        """
        name = pipeline_name or config.get("name", "default_pipeline")
        description = config.get("description", "")
        pipeline = Pipeline(name=name, description=description)

        for task_cfg in config["tasks"]:
            task = self.create_task_from_config(task_cfg)
            pipeline.add_task(task)

        return pipeline

    def create_pipeline_from_yaml(self, yaml_path: str) -> Pipeline:
        """
        Create a pipeline from a YAML configuration file.

        Args:
            yaml_path: Path to the YAML config file

        Returns:
            Configured Pipeline instance
        """
        try:
            with open(yaml_path, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            raise InvalidTaskConfigException(f"YAML file not found: {yaml_path}")
        except yaml.YAMLError as e:
            raise InvalidTaskConfigException(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise InvalidTaskConfigException(f"Error reading YAML: {e}")

        return self.create_pipeline_from_config(config)

    def get_registered_types(self) -> List[str]:
        """
        Get list of all registered task types.

        Returns:
            List of registered task type names
        """
        return self._registry.get_all_types()

    def is_registered(self, task_type: str) -> bool:
        """
        Check if a task type is registered.

        Args:
            task_type: Task type to check

        Returns:
            True if registered, False otherwise
        """
        return self._registry.has(task_type)

    def get_task_info(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the Task class associated with a task type.

        Args:
            task_type: The task type to look up

        Returns:
            The Task class if registered, None otherwise
        """
        task_class = self._registry.get(task_type)
        if task_class is None:
            return {}

        return {
            "name": task_class.__name__,
            "params": inspect.signature(task_class.__init__),
            "doc": task_class.__doc__,
        }

    def validate_task_config(self, config: Dict[str, Any]) -> None:
        """
        Validate a task configuration dictionary.

        Args:
            config: Task configuration dictionary

        Raises:
            InvalidTaskConfigException: If config is invalid
        """
        if not isinstance(config, dict):
            raise InvalidTaskConfigException("Task config must be a dictionary")

        if "type" not in config or not isinstance(config["type"], str):
            raise InvalidTaskConfigException("Task config must include a 'type' string field")

        if "name" in config and not isinstance(config["name"], str):
            raise InvalidTaskConfigException("If provided, 'name' field must be a string")

        if "params" in config and not isinstance(config["params"], dict):
            raise InvalidTaskConfigException("If provided, 'params' field must be a dictionary")
