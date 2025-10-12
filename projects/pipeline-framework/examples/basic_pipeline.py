"""Basic example of using the pipeline framework."""

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.core.task import Task


class LoadDataTask(Task):
    """Example task that loads data into context."""

    def __init__(self):
        super().__init__("load_data", "Load initial data")

    def execute(self, context: PipelineContext) -> None:
        # Simulate loading data
        context.set("raw_data", [1, 2, 3, 4, 5])
        print(f"[{self.name}] Loaded data: {context.get('raw_data')}")


class TransformDataTask(Task):
    """Example task that transforms data."""

    def __init__(self):
        super().__init__("transform_data", "Transform the data")

    def execute(self, context: PipelineContext) -> None:
        raw_data = context.get("raw_data", [])
        # Transform: square each number
        transformed = [x**2 for x in raw_data]
        context.set("transformed_data", transformed)
        print(f"[{self.name}] Transformed: {transformed}")


class SaveDataTask(Task):
    """Example task that saves the result."""

    def __init__(self):
        super().__init__("save_data", "Save the results")

    def execute(self, context: PipelineContext) -> None:
        result = context.get("transformed_data", [])
        # Simulate saving
        print(f"[{self.name}] Saved {len(result)} items")
        context.set("saved", True)


def main():
    """Run the example pipeline."""
    # Create pipeline
    pipeline = Pipeline("data_processing_pipeline")

    # Add tasks using fluent interface
    pipeline.add_task(LoadDataTask()).add_task(TransformDataTask()).add_task(
        SaveDataTask()
    )

    # Execute
    print("Starting pipeline execution...\n")
    final_context = pipeline.execute()

    print("\n=== Pipeline Results ===")
    print(f"Final context: {final_context.get_all()}")


if __name__ == "__main__":
    main()
