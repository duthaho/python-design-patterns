"""Logging decorator for processors."""

import logging
from typing import Optional

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.decorators.base import ProcessorDecorator


class LoggingDecorator(ProcessorDecorator):
    """
    Decorator that adds logging to a processor.
    """

    def __init__(
        self,
        wrapped: Processor,
        logger: Optional[logging.Logger] = None,
        log_input: bool = True,
        log_output: bool = True,
        log_errors: bool = True,
        name: Optional[str] = None,
    ):
        """
        Initialize logging decorator.

        Args:
            wrapped: Processor to wrap
            logger: Logger instance (creates default if None)
            log_input: Whether to log input data
            log_output: Whether to log output data
            log_errors: Whether to log errors
            name: Optional decorator name
        """
        super().__init__(wrapped, name or f"Logging({wrapped.name})")
        self._logger = logger or logging.getLogger(self.name)
        self._log_input = log_input
        self._log_output = log_output
        self._log_errors = log_errors

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Process with logging.
        """
        if self._log_input:
            self._logger.info(f"Processing started for {context.data.id}")
            self._logger.debug(f"Input data: {context.data.payload}, Metadata: {context.data.metadata}")

        try:
            result_context = self.wrapped._do_process(context)

            if self._log_output:
                self._logger.info(f"Processing completed for {context.data.id}")
                self._logger.debug(f"Output data: {result_context.data.payload}, Metadata: {result_context.data.metadata}")

            return result_context

        except Exception as e:
            if self._log_errors:
                self._logger.error(f"Processing failed for {context.data.id}: {str(e)}", exc_info=True)
            raise
