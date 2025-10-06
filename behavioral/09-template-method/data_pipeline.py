import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class DataPipeline(ABC):
    """
    Template for data processing pipelines.
    Defines the ETL workflow with required and optional steps.
    """

    def process(self, source: Any) -> Optional[List[Dict]]:
        """
        Template method - DO NOT OVERRIDE.
        Executes the complete data pipeline.

        Returns:
            Processed data if successful, None if failed
        """
        pipeline_name = self._get_pipeline_name()
        start_time = time.time()

        print(f"\n{'='*60}")
        print(
            f"[{pipeline_name}] Starting pipeline at {datetime.now().strftime('%H:%M:%S')}"
        )
        print(f"{'='*60}")

        try:
            # Required: Input validation
            self._validate_input(source)

            # Hook: Pre-processing
            self._pre_process(source)

            # Required: Extract
            data = self._extract(source)
            print(f"[{pipeline_name}] Extracted {len(data)} records")

            # Required: Transform
            data = self._transform(data)

            # Conditional: Custom filtering
            if self._needs_filtering():
                data = self._apply_custom_filter(data)
                print(f"[{pipeline_name}] Filtered to {len(data)} records")

            # Conditional: Output validation
            if self._should_validate_output():
                self._validate_output(data)

            # Required: Load
            self._load(data)

            # Hook: Post-processing
            self._post_process()

            # Conditional: Notifications
            if self._should_send_notifications():
                self._send_notification(data)

            elapsed = time.time() - start_time
            self._track_metrics(elapsed, len(data), success=True)

            print(f"[{pipeline_name}] ✓ Pipeline completed successfully")
            print(f"[{pipeline_name}] Total time: {elapsed:.2f}s")

            return data

        except Exception as e:
            elapsed = time.time() - start_time
            self._handle_error(e)
            self._track_metrics(elapsed, 0, success=False)
            print(f"[{pipeline_name}] ✗ Pipeline failed after {elapsed:.2f}s")
            raise

    # ==================== REQUIRED ABSTRACT METHODS ====================

    @abstractmethod
    def _validate_input(self, source: Any) -> None:
        """Validate the input source. Raise exception if invalid."""
        pass

    @abstractmethod
    def _extract(self, source: Any) -> List[Dict]:
        """Extract data from the source."""
        pass

    @abstractmethod
    def _transform(self, data: List[Dict]) -> List[Dict]:
        """Transform the extracted data."""
        pass

    @abstractmethod
    def _load(self, data: List[Dict]) -> None:
        """Load the transformed data to the destination."""
        pass

    # ==================== HOOK METHODS (OPTIONAL) ====================

    def _pre_process(self, source: Any) -> None:
        """Hook: Override to add pre-processing before extraction."""
        pass

    def _post_process(self) -> None:
        """Hook: Override to add post-processing after loading."""
        pass

    def _apply_custom_filter(self, data: List[Dict]) -> List[Dict]:
        """Hook: Override to apply custom filtering logic."""
        return data

    def _validate_output(self, data: List[Dict]) -> None:
        """Hook: Override to validate output data."""
        pass

    def _send_notification(self, data: List[Dict]) -> None:
        """Hook: Override to send notifications."""
        pass

    def _track_metrics(
        self, execution_time: float, record_count: int, success: bool
    ) -> None:
        """Hook: Override to track pipeline metrics."""
        pass

    def _handle_error(self, error: Exception) -> None:
        """Hook: Override to customize error handling."""
        print(f"❌ Error: {type(error).__name__}: {error}")

    def _get_pipeline_name(self) -> str:
        """Hook: Override to provide custom pipeline name."""
        return self.__class__.__name__

    # ==================== CONDITIONAL CHECKS ====================

    def _needs_filtering(self) -> bool:
        """Hook: Return True to enable custom filtering."""
        return False

    def _should_validate_output(self) -> bool:
        """Hook: Return True to enable output validation."""
        return False

    def _should_send_notifications(self) -> bool:
        """Hook: Return True to enable notifications."""
        return False


class APIDataPipeline(DataPipeline):
    """
    REST API data source pipeline.
    - Input validation: URL format
    - Pre-processing: Rate limiting
    - Output validation: Enabled
    - Notifications: Enabled
    - Metrics tracking: Enabled
    """

    def __init__(self, rate_limit_delay: float = 0.5):
        self.rate_limit_delay = rate_limit_delay
        self.api_calls_count = 0

    def _validate_input(self, source: Any) -> None:
        if not isinstance(source, str):
            raise TypeError(f"Expected string URL, got {type(source).__name__}")
        if not source.startswith(("http://", "https://")):
            raise ValueError(f"Invalid API URL: {source}")
        print(f"✓ Input validated: {source}")

    def _pre_process(self, source: Any) -> None:
        print(f"⏱ Applying rate limiting ({self.rate_limit_delay}s delay)...")
        time.sleep(self.rate_limit_delay)

    def _extract(self, source: str) -> List[Dict]:
        print(f"📡 Calling API: {source}")
        time.sleep(0.8)  # Simulate API call
        self.api_calls_count += 1
        return [
            {"id": 1, "value": "user_data", "timestamp": time.time()},
            {"id": 2, "value": "event_data", "timestamp": time.time()},
        ]

    def _transform(self, data: List[Dict]) -> List[Dict]:
        print("🔄 Transforming API data (uppercase conversion)")
        for item in data:
            item["value"] = item["value"].upper()
            item["source"] = "API"
        return data

    def _validate_output(self, data: List[Dict]) -> None:
        print("✓ Validating output data...")
        if not data:
            raise ValueError("Output validation failed: No data to load")
        for item in data:
            if "id" not in item or "value" not in item:
                raise ValueError(f"Output validation failed: Invalid record structure")

    def _load(self, data: List[Dict]) -> None:
        print(f"💾 Loading {len(data)} records to data warehouse...")
        time.sleep(0.5)

    def _send_notification(self, data: List[Dict]) -> None:
        print(f"📧 Notification sent: Processed {len(data)} records from API")

    def _track_metrics(
        self, execution_time: float, record_count: int, success: bool
    ) -> None:
        status = "SUCCESS" if success else "FAILED"
        print(
            f"📊 Metrics: {status} | Records: {record_count} | "
            f"Time: {execution_time:.2f}s | API Calls: {self.api_calls_count}"
        )

    def _should_validate_output(self) -> bool:
        return True

    def _should_send_notifications(self) -> bool:
        return True


class DatabaseDataPipeline(DataPipeline):
    """
    SQL Database data source pipeline.
    - Custom filtering: SQL-based
    - Post-processing: Connection cleanup
    - Output validation: Disabled
    - Notifications: Disabled
    """

    def __init__(self):
        self.connection = None

    def _validate_input(self, source: Any) -> None:
        if not isinstance(source, str) or not source.startswith("db://"):
            raise ValueError(f"Invalid database connection string: {source}")
        print(f"✓ Connection string validated")

    def _extract(self, source: str) -> List[Dict]:
        print(f"🗄️  Connecting to database...")
        self.connection = f"Connection-{id(self)}"  # Simulate connection
        time.sleep(0.8)
        print(f"📊 Executing SELECT query...")
        time.sleep(0.5)
        return [
            {"id": 10, "value": "database record", "status": "active"},
            {"id": 11, "value": "archived data", "status": "archived"},
            {"id": 12, "value": "database entry", "status": "active"},
        ]

    def _transform(self, data: List[Dict]) -> List[Dict]:
        print("🔄 Transforming database data (lowercase conversion)")
        for item in data:
            item["value"] = item["value"].lower()
            item["source"] = "DATABASE"
        return data

    def _apply_custom_filter(self, data: List[Dict]) -> List[Dict]:
        print("🔍 Applying SQL filter: status='active'")
        return [item for item in data if item.get("status") == "active"]

    def _load(self, data: List[Dict]) -> None:
        print(f"💾 Bulk insert: {len(data)} records to data warehouse...")
        time.sleep(0.6)

    def _post_process(self) -> None:
        if self.connection:
            print(f"🔌 Closing database connection: {self.connection}")
            self.connection = None

    def _needs_filtering(self) -> bool:
        return True


class FileDataPipeline(DataPipeline):
    """
    CSV File data source pipeline.
    - Minimal configuration
    - Uses default implementations for optional steps
    - Only implements required abstract methods
    """

    def _validate_input(self, source: Any) -> None:
        if not isinstance(source, str):
            raise TypeError(f"Expected file path string, got {type(source).__name__}")
        if not source.endswith(".csv"):
            raise ValueError(f"Only CSV files supported, got: {source}")
        print(f"✓ File path validated: {source}")

    def _extract(self, source: str) -> List[Dict]:
        print(f"📁 Reading CSV file: {source}")
        time.sleep(0.6)
        return [
            {"id": 100, "value": "file data row 1"},
            {"id": 101, "value": "file data row 2"},
        ]

    def _transform(self, data: List[Dict]) -> List[Dict]:
        print("🔄 Transforming file data (title case conversion)")
        for item in data:
            item["value"] = item["value"].title()
            item["source"] = "FILE"
        return data

    def _load(self, data: List[Dict]) -> None:
        print(f"💾 Writing {len(data)} records to analytics platform...")
        time.sleep(0.4)


# ==================== DEMONSTRATION ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DATA PIPELINE DEMONSTRATION")
    print("=" * 60)

    # API Pipeline - Full featured
    print("\n🔷 TEST 1: API Data Pipeline (Full Features)")
    api_pipeline = APIDataPipeline(rate_limit_delay=0.3)
    try:
        result = api_pipeline.process("https://api.example.com/data")
    except Exception as e:
        print(f"Pipeline failed: {e}")

    # Database Pipeline - Selective features
    print("\n🔷 TEST 2: Database Data Pipeline (Filtering + Cleanup)")
    db_pipeline = DatabaseDataPipeline()
    try:
        result = db_pipeline.process("db://user:pass@localhost:5432/warehouse")
    except Exception as e:
        print(f"Pipeline failed: {e}")

    # File Pipeline - Minimal
    print("\n🔷 TEST 3: File Data Pipeline (Minimal Features)")
    file_pipeline = FileDataPipeline()
    try:
        result = file_pipeline.process("data/sales_report.csv")
    except Exception as e:
        print(f"Pipeline failed: {e}")

    # Error case
    print("\n🔷 TEST 4: Error Handling (Invalid Input)")
    api_pipeline_error = APIDataPipeline()
    try:
        result = api_pipeline_error.process("invalid-url")
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}")

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60 + "\n")
