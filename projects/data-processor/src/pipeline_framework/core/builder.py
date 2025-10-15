"""Pipeline builder (Builder pattern)."""

from typing import Any, Dict, List, Optional

from pipeline_framework.core.models import PipelineConfig
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.core.processor import Processor
from pipeline_framework.sinks.base import Sink
from pipeline_framework.sinks.factory import SinkFactory
from pipeline_framework.sources.base import Source
from pipeline_framework.sources.factory import SourceFactory
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
        self._source: Optional[Source] = None
        self._sink: Optional[Sink] = None

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

    def with_source(self, source: Source) -> "PipelineBuilder":
        """
        Set the data source for the pipeline.

        Args:
            source: Source instance to read data from

        Returns:
            Self for method chaining

        Example:
            >>> from pipeline_framework.sources.file import CSVFileSource
            >>> builder.with_source(CSVFileSource("data.csv"))
        """
        self._source = source
        return self

    def with_sink(self, sink: Sink) -> "PipelineBuilder":
        """
        Set the data sink for the pipeline.

        Args:
            sink: Sink instance to write results to

        Returns:
            Self for method chaining
        """
        self._sink = sink
        return self

    def with_source_config(self, config: Dict[str, Any]) -> "PipelineBuilder":
        """
        Configure source from dictionary.
        Uses SourceFactory internally.

        Args:
            config: Source configuration dictionary

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_source_config({
            ...     "type": "csv_file",
            ...     "path": "data.csv"
            ... })
        """
        self._source = SourceFactory.create_from_config(config)
        return self

    def with_sink_config(self, config: Dict[str, Any]) -> "PipelineBuilder":
        """
        Configure sink from dictionary.
        Uses SinkFactory internally.
        """
        self._sink = SinkFactory.create_from_config(config)
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

    def build_and_run(self) -> List:
        """
        Build pipeline, run with configured source, write to configured sink.

        This is a convenience method that:
        1. Builds the pipeline
        2. Reads data from source (if configured)
        3. Executes the pipeline
        4. Writes results to sink (if configured)
        5. Properly closes source and sink

        Returns:
            List of ProcessingContext results

        Raises:
            BuilderException: If source is not configured

        Example:
            >>> results = (PipelineBuilder("my-pipeline")
            ...     .with_source_config({"type": "csv_file", "path": "data.csv"})
            ...     .add_processor(CounterProcessor())
            ...     .with_sink_config({"type": "json_file", "path": "output.json"})
            ...     .build_and_run())
        """
        pipeline = self.build()

        if self._source is None:
            raise BuilderException("Source must be configured to run the pipeline.")

        results = pipeline.execute_source_to_sink(self._source, self._sink)

        return results

    def reset(self) -> "PipelineBuilder":
        """
        Reset the builder to start fresh.
        Useful for building multiple similar pipelines.
        """
        self._processors = []
        self._state_storage = None
        self._pipeline_config = None
        self._source = None
        self._sink = None
        return self
