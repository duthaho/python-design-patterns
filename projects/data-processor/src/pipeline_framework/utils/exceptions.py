"""Custom exceptions for the pipeline framework."""


class PipelineException(Exception):
    """Base exception for pipeline errors."""

    pass


class ProcessorException(PipelineException):
    """Exception raised during processing."""

    pass


class BuilderException(PipelineException):
    """Exception raised during pipeline building."""

    pass


class StateException(PipelineException):
    """Exception raised during state operations."""

    pass


class ValidationException(PipelineException):
    """Exception raised during data validation."""

    pass
