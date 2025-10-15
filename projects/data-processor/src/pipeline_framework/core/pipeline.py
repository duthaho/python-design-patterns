"""Pipeline orchestrator."""

from typing import List, Optional

from pipeline_framework.core.models import (PipelineConfig, PipelineData,
                                            ProcessingContext)
from pipeline_framework.core.processor import Processor
from pipeline_framework.sinks.base import Sink
from pipeline_framework.sources.base import Source
from pipeline_framework.strategies.state import StateStorage
from pipeline_framework.utils.exceptions import PipelineException


class Pipeline:
    """
    Main pipeline orchestrator.
    Executes data through a chain of processors with state management.
    """

    def __init__(
        self,
        pipeline_id: str,
        processor_chain: Processor,
        state_storage: StateStorage,
        pipeline_config: Optional[PipelineConfig] = None,
    ):
        """
        Initialize pipeline.

        Args:
            pipeline_id: Unique identifier for this pipeline
            processor_chain: Head of the processor chain
            state_storage: State storage strategy
        """
        self.pipeline_id = pipeline_id
        self._config = pipeline_config or PipelineConfig()
        self._processor_chain = processor_chain
        self._state_storage = state_storage

    def execute(self, data_batch: List[PipelineData]) -> List[ProcessingContext]:
        """
        Execute pipeline on a batch of data.

        Args:
            data_batch: List of data items to process

        Returns:
            List of processing contexts (one per input item)
        """
        if not data_batch:
            return []

        state = self._state_storage.load(self.pipeline_id)

        results = []
        for data in data_batch:
            context = ProcessingContext(data=data, state=state, config=self._config)

            try:
                context = self._processor_chain.process(context)
            except Exception as e:
                raise PipelineException(f"Error processing data ID {data.id}") from e

            results.append(context)

        self._state_storage.save(self.pipeline_id, state)

        return results

    def execute_single(self, data: PipelineData) -> ProcessingContext:
        """
        Execute pipeline on a single data item.
        Convenience method that calls execute() with a single-item list.
        Args:
            data: Single data item to process

        Returns:
            Processing context for the input item
        """
        results = self.execute([data])
        return results[0] if results else None

    def execute_from_source(self, source: Source) -> List[ProcessingContext]:
        """
        Execute pipeline reading from a source.

        Args:
            source: Source to read data from

        Returns:
            List of ProcessingContext results

        Example:
            >>> from pipeline_framework.sources.file import CSVFileSource
            >>> source = CSVFileSource("data.csv")
            >>> results = pipeline.execute_from_source(source)
            >>> source.close()
        """
        with source:
            data_batch = source.read()
            return self.execute(data_batch)

    def execute_to_sink(self, data: List[PipelineData], sink: Sink) -> List[ProcessingContext]:
        """
        Execute pipeline and write results to sink.

        Args:
            data: Input data
            sink: Sink to write results to

        Returns:
            List of ProcessingContext results
        """
        results = self.execute(data)
        with sink:
            sink.write(results)
        return results

    def execute_source_to_sink(self, source: Source, sink: Sink) -> List[ProcessingContext]:
        """
        Execute complete pipeline: source → processors → sink.

        Args:
            source: Source to read from
            sink: Sink to write to

        Returns:
            List of ProcessingContext results

        Example:
            >>> source = CSVFileSource("input.csv")
            >>> sink = JSONFileSink("output.json")
            >>> results = pipeline.execute_source_to_sink(source, sink)
        """
        with source, sink:
            data_batch = source.read()
            results = self.execute(data_batch)
            sink.write(results)
            return results

    def get_state(self) -> dict:
        """Get current state from storage."""
        return self._state_storage.load(self.pipeline_id)

    def clear_state(self) -> None:
        """Clear state for this pipeline."""
        self._state_storage.clear(self.pipeline_id)
