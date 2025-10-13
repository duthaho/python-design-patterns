"""Console logger listener for displaying pipeline events."""

from ..event import PipelineEvent
from ..listener import PipelineListener


class ConsoleListener(PipelineListener):
    """
    Listener that prints pipeline events to console.

    Useful for debugging and monitoring pipeline execution.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize console listener.

        Args:
            verbose: If True, print all events. If False, only errors.
        """
        self.verbose = verbose

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Print pipeline start message."""
        if self.verbose:
            print(f"🚀 Pipeline '{event.pipeline_name}' started")

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """Print pipeline completion message."""
        if self.verbose:
            print(f"✅ Pipeline '{event.pipeline_name}' completed successfully")

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """Print pipeline failure message."""
        print(
            f"❌ Pipeline '{event.pipeline_name}' failed with error: {event.metadata.get('error') if event.metadata else 'Unknown error'}"
        )

    def on_task_started(self, event: PipelineEvent) -> None:
        """Print task start message."""
        if self.verbose:
            print(f"  → Task '{event.task_name}' started")

    def on_task_completed(self, event: PipelineEvent) -> None:
        """Print task completion message."""
        if self.verbose:
            print(f"  ✓ Task '{event.task_name}' completed")

    def on_task_failed(self, event: PipelineEvent) -> None:
        """Print task failure message."""
        error = event.metadata.get("error", "Unknown error") if event.metadata else "Unknown error"
        print(f"  ✗ Task '{event.task_name}' failed: {error}")
