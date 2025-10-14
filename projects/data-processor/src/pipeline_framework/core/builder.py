"""Pipeline builder (Builder pattern)."""

from typing import List, Optional

from pipeline_framework.core.models import PipelineConfig
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.core.processor import Processor
from pipeline_framework.strategies.state import (InMemoryStateStorage,
                                                 StateStorage)
from pipeline_framework.utils.exceptions import BuilderException


class PipelineBuilder:
    """
    Builder for constructing pipelines with a fluent interface.
    Demonstrates the Builder pattern.
    """

    def __init__(self, pipeline_id: str):
        """
        Initialize builder with a pipeline ID.

        Args:
            pipeline_id: Unique identifier for the pipeline
        """
        self._pipeline_id = pipeline_id
        self._processors: List[Processor] = []
        self._state_storage: Optional[StateStorage] = None
        self._pipeline_config: Optional[PipelineConfig] = None

    def add_processor(self, processor: Processor) -> "PipelineBuilder":
        """
        Add a processor to the pipeline.

        Args:
            processor: Processor to add

        Returns:
            Self for method chaining
        """
        self._processors.append(processor)
        return self

    def with_state_storage(self, storage: StateStorage) -> "PipelineBuilder":
        """
        Set the state storage strategy.

        Args:
            storage: State storage strategy

        Returns:
            Self for method chaining
        """
        self._state_storage = storage
        return self
    
    def with_config(self, config: PipelineConfig) -> "PipelineBuilder":
        """
        Set the pipeline configuration.

        Args:
            config: Pipeline configuration

        Returns:
            Self for method chaining
        """
        self._pipeline_config = config
        return self

    def build(self) -> Pipeline:
        """
        Build the final pipeline.

        Returns:
            Configured Pipeline instance

        Raises:
            BuilderException: If no processors were added

        Example chaining:
            processors[0].set_next(processors[1]).set_next(processors[2])
        """
        if not self._processors:
            raise BuilderException("Pipeline must have at least one processor.")

        if self._state_storage is None:
            self._state_storage = InMemoryStateStorage()

        for i in range(len(self._processors) - 1):
            self._processors[i].set_next(self._processors[i + 1])

        return Pipeline(
            pipeline_id=self._pipeline_id,
            processor_chain=self._processors[0],
            state_storage=self._state_storage,
            pipeline_config=self._pipeline_config,
        )

    def reset(self) -> "PipelineBuilder":
        """
        Reset the builder to start fresh.
        Useful for building multiple similar pipelines.
        """
        self._processors = []
        self._state_storage = None
        return self
