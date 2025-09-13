import csv
import io
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Iterator, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataRecord:
    """Standardized data record for analytics processing"""

    id: str
    timestamp: datetime
    category: str
    value: float
    metadata: Dict[str, Any]


class DataSourceError(Exception):
    """Custom exception for data source errors"""

    pass


class DataValidationError(Exception):
    """Custom exception for data validation errors"""

    pass


# Decorator for retry logic
def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.warning(f"Attempt {attempts} failed: {e}")
                    if attempts >= max_attempts:
                        logger.error(f"All {max_attempts} attempts failed.")
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator


# Your unified data processing interface
class DataSource(ABC):
    def __init__(self):
        self._cache: Optional[List[DataRecord]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # Cache time-to-live in seconds

    @abstractmethod
    def _fetch_raw_data(self) -> List[DataRecord]:
        """Fetch raw data from the source"""
        pass

    @abstractmethod
    def _parse_record(self, raw_record: Any) -> DataRecord:
        """Parse a raw record into a DataRecord"""
        pass

    def get_records(
        self, limit: Optional[int] = None, use_cache: bool = True
    ) -> Iterator[DataRecord]:
        """Get standardized data records, with optional caching and limit"""
        if use_cache and self._is_cache_valid():
            logger.info("Using cached data")
            records = self._cache[:limit] if limit is not None else self._cache
            yield from records
            return

        try:
            raw_data = self._fetch_raw_data()
            records = []
            count = 0

            for raw_record in self._get_raw_records(raw_data):
                if limit is not None and count >= limit:
                    break

                try:
                    record = self._parse_record(raw_record)
                    self._validate_record(record)
                    records.append(record)
                    yield record
                    count += 1
                except DataValidationError as ve:
                    logger.error(f"Data validation error: {ve}")
                    continue
                except Exception as e:
                    logger.error(f"Error parsing record: {e}")
                    raise DataSourceError(f"Error parsing record: {e}") from e

            if use_cache:
                self._cache = records
                self._cache_timestamp = datetime.now()
                logger.info(f"Cached {len(records)} records")

        except Exception as e:
            logger.error(f"Error processing data from {self.__class__.__name__}: {e}")
            raise DataSourceError(f"Error fetching or processing data: {e}") from e

    @abstractmethod
    def _get_raw_records(self, raw_data: Any) -> Iterator[Any]:
        """Extract raw records from the fetched data"""
        pass

    def _validate_record(self, record: DataRecord) -> None:
        """Validate a DataRecord"""
        if not record.id or not isinstance(record.id, str):
            raise DataValidationError("Invalid ID")
        if not isinstance(record.timestamp, datetime):
            raise DataValidationError("Invalid timestamp")
        if not record.category or not isinstance(record.category, str):
            raise DataValidationError("Invalid category")
        if not isinstance(record.value, (int, float)):
            raise DataValidationError("Invalid value")

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return (
            datetime.now() - self._cache_timestamp
        ).total_seconds() < self._cache_ttl

    def clear_cache(self) -> None:
        """Clear the cached data"""
        self._cache = None
        self._cache_timestamp = None
        logger.info("Cache cleared")

    @abstractmethod
    def get_record_count(self) -> int:
        """Get total number of records available in the source"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the data source is available"""
        pass


# Different third-party data sources with incompatible interfaces
class CSVFileReader:
    """Legacy CSV file reader with specific format"""

    def __init__(self, file_content: str):
        self.file_content = file_content
        self._parsed_data = None

    def load_data(self) -> List[Dict[str, str]]:
        if self._parsed_data is None:
            reader = csv.DictReader(io.StringIO(self.file_content))
            self._parsed_data = list(reader)
        return self._parsed_data

    def get_row_count(self) -> int:
        return len(self.load_data())


class JSONAPIClient:
    """REST API client returning JSON data"""

    def __init__(self, api_data: List[Dict[str, Any]]):
        self.api_data = api_data  # Simulated API response
        self.is_online = True

    def fetch_data(self, page_size: int = 100) -> Dict[str, Any]:
        return {
            "status": "success" if self.is_online else "error",
            "data": self.api_data[:page_size],
            "total_count": len(self.api_data),
            "meta": {"api_version": "v2", "format": "json"},
        }

    def health_check(self) -> bool:
        return self.is_online


class XMLFeedParser:
    """XML feed parser with nested structure"""

    def __init__(self, xml_data: List[Dict[str, Any]]):
        self.xml_data = xml_data  # Simulated parsed XML
        self.connection_status = "active"

    def parse_feed(self) -> Dict[str, Any]:
        return {
            "feed": {
                "items": self.xml_data,
                "item_count": len(self.xml_data),
                "last_updated": "2024-01-15T10:30:00Z",
            },
            "status": self.connection_status,
        }

    def check_connection(self) -> str:
        return self.connection_status


class DatabaseResultSet:
    """Database query result with cursor-like interface"""

    def __init__(self, query_results: List[tuple]):
        self.results = query_results
        self.position = 0
        self.columns = ["record_id", "created_at", "type", "amount", "details"]

    def fetch_batch(self, batch_size: int = 50) -> List[tuple]:
        start = self.position
        end = min(start + batch_size, len(self.results))
        batch = self.results[start:end]
        self.position = end
        return batch

    def get_total_rows(self) -> int:
        return len(self.results)

    def reset_cursor(self):
        self.position = 0

    def has_more_data(self) -> bool:
        return self.position < len(self.results)


# TODO: Implement adapters for each data source
# Requirements:
# 1. CSVAdapter - Convert CSV rows to DataRecord objects
#    - Handle date parsing from string format "YYYY-MM-DD HH:MM:SS"
#    - Map CSV columns: id->id, timestamp->timestamp, category->category, value->value
#    - Put remaining columns in metadata dict


class CSVAdapter(DataSource):
    def __init__(
        self, csv_reader: CSVFileReader, date_formats: Optional[List[str]] = None
    ):
        super().__init__()
        self.csv_reader = csv_reader
        self.date_formats = date_formats or ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]
        self._required_fields = {"id", "timestamp", "category", "value"}

    @retry(max_attempts=3)
    def _fetch_raw_data(self) -> List[Dict[str, str]]:
        return self.csv_reader.load_data()

    def _get_raw_records(
        self, raw_data: List[Dict[str, str]]
    ) -> Iterator[Dict[str, str]]:
        for row in raw_data:
            missing_fields = self._required_fields - row.keys()
            if missing_fields:
                raise DataValidationError(f"Missing required fields: {missing_fields}")
            yield row

    def _parse_record(self, raw_record: Dict[str, str]) -> DataRecord:
        timestamp = None
        for fmt in self.date_formats:
            try:
                timestamp = datetime.strptime(raw_record["timestamp"], fmt)
                break
            except ValueError:
                continue

        if timestamp is None:
            raise DataValidationError(
                f"Invalid timestamp format: {raw_record['timestamp']}"
            )

        metadata = {
            k: v for k, v in raw_record.items() if k not in self._required_fields
        }
        return DataRecord(
            id=raw_record["id"],
            timestamp=timestamp,
            category=raw_record["category"],
            value=float(raw_record["value"]),
            metadata=metadata,
        )

    def get_record_count(self) -> int:
        return self.csv_reader.get_row_count()

    def is_available(self) -> bool:
        return True  # Assuming file is always available for this example


# 2. JSONAdapter - Convert JSON API response to DataRecord objects
#    - Handle the nested response structure
#    - Map fields: record_id->id, event_time->timestamp, event_type->category, metric_value->value
#    - Include API metadata in each record's metadata


class JSONAdapter(DataSource):
    def __init__(self, api_client: JSONAPIClient):
        super().__init__()
        self.api_client = api_client
        self._data = None

    @retry(max_attempts=3)
    def _fetch_raw_data(self) -> Dict[str, Any]:
        response = self.api_client.fetch_data(page_size=100)
        if response["status"] != "success":
            raise DataSourceError("API returned error status")
        self._data = response
        return response

    def _get_raw_records(self, raw_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        for item in raw_data["data"]:
            yield item

    def _parse_record(self, raw_record: Dict[str, Any]) -> DataRecord:
        try:
            timestamp = datetime.strptime(
                raw_record["event_time"], "%Y-%m-%dT%H:%M:%SZ"
            )
        except ValueError as ve:
            raise DataValidationError(
                f"Invalid timestamp format: {raw_record['event_time']}"
            ) from ve

        metadata = {
            k: v
            for k, v in raw_record.items()
            if k not in {"record_id", "event_time", "event_type", "metric_value"}
        }
        metadata.update(self._data.get("meta", {}))

        return DataRecord(
            id=raw_record["record_id"],
            timestamp=timestamp,
            category=raw_record["event_type"],
            value=float(raw_record["metric_value"]),
            metadata=metadata,
        )

    def get_record_count(self) -> int:
        if self._data is None:
            self._fetch_raw_data()
        return self._data["total_count"]

    def is_available(self) -> bool:
        return self.api_client.health_check()


# 3. XMLAdapter - Convert XML feed items to DataRecord objects
#    - Handle the nested feed structure
#    - Map fields: item_id->id, published->timestamp, channel->category, score->value
#    - Include feed metadata


class XMLAdapter(DataSource):
    def __init__(self, xml_parser: XMLFeedParser):
        super().__init__()
        self.xml_parser = xml_parser
        self._data = None

    @retry(max_attempts=3)
    def _fetch_raw_data(self) -> Dict[str, Any]:
        response = self.xml_parser.parse_feed()
        if response["status"] != "active":
            raise DataSourceError("XML feed connection is not active")
        self._data = response
        return response

    def _get_raw_records(self, raw_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        for item in raw_data["feed"]["items"]:
            yield item

    def _parse_record(self, raw_record: Dict[str, Any]) -> DataRecord:
        try:
            timestamp = datetime.strptime(raw_record["published"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as ve:
            raise DataValidationError(
                f"Invalid timestamp format: {raw_record['published']}"
            ) from ve

        metadata = {
            k: v
            for k, v in raw_record.items()
            if k not in {"item_id", "published", "channel", "score"}
        }
        metadata.update({"feed_last_updated": self._data["feed"]["last_updated"]})

        return DataRecord(
            id=raw_record["item_id"],
            timestamp=timestamp,
            category=raw_record["channel"],
            value=float(raw_record["score"]),
            metadata=metadata,
        )

    def get_record_count(self) -> int:
        if self._data is None:
            self._fetch_raw_data()
        return self._data["feed"]["item_count"]

    def is_available(self) -> bool:
        return self.xml_parser.check_connection() == "active"


# 4. DatabaseAdapter - Convert database tuples to DataRecord objects
#    - Use column names to map tuple values
#    - Handle cursor-based iteration
#    - Parse timestamp from string format


class DatabaseAdapter(DataSource):
    def __init__(
        self, db_result_set: DatabaseResultSet, date_formats: Optional[List[str]] = None
    ):
        super().__init__()
        self.db_result_set = db_result_set
        self.date_formats = date_formats or ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]
        self._required_fields = {"record_id", "created_at", "type", "amount"}

    @retry(max_attempts=3)
    def _fetch_raw_data(self) -> List[tuple]:
        self.db_result_set.reset_cursor()
        all_data = []
        while self.db_result_set.has_more_data():
            batch = self.db_result_set.fetch_batch(batch_size=50)
            all_data.extend(batch)
        return all_data

    def _get_raw_records(self, raw_data: List[tuple]) -> Iterator[tuple]:
        for row in raw_data:
            if len(row) != len(self.db_result_set.columns):
                raise DataValidationError("Row does not match expected column count")
            yield row

    def _parse_record(self, raw_record: tuple) -> DataRecord:
        record_dict = dict(zip(self.db_result_set.columns, raw_record))

        timestamp = None
        for fmt in self.date_formats:
            try:
                timestamp = datetime.strptime(record_dict["created_at"], fmt)
                break
            except ValueError:
                continue

        if timestamp is None:
            raise DataValidationError(
                f"Invalid timestamp format: {record_dict['created_at']}"
            )

        metadata = {
            k: v for k, v in record_dict.items() if k not in self._required_fields
        }
        return DataRecord(
            id=record_dict["record_id"],
            timestamp=timestamp,
            category=record_dict["type"],
            value=float(record_dict["amount"]),
            metadata=metadata,
        )

    def get_record_count(self) -> int:
        return self.db_result_set.get_total_rows()

    def is_available(self) -> bool:
        return True  # Assuming DB connection is always available for this example


def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.2f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.2f} seconds: {e}"
            )
            raise

    return wrapper


class DataSourceFactory:
    """Factory to create data source adapters"""

    @staticmethod
    def create_csv_adapter(file_content: str, **kwargs) -> CSVAdapter:
        csv_reader = CSVFileReader(file_content)
        return CSVAdapter(csv_reader, **kwargs)

    @staticmethod
    def create_json_adapter(api_data: List[Dict[str, Any]], **kwargs) -> JSONAdapter:
        api_client = JSONAPIClient(api_data)
        return JSONAdapter(api_client, **kwargs)

    @staticmethod
    def create_xml_adapter(xml_data: List[Dict[str, Any]], **kwargs) -> XMLAdapter:
        xml_parser = XMLFeedParser(xml_data)
        return XMLAdapter(xml_parser, **kwargs)

    @staticmethod
    def create_database_adapter(
        query_results: List[tuple], **kwargs
    ) -> DatabaseAdapter:
        db_result_set = DatabaseResultSet(query_results)
        return DatabaseAdapter(db_result_set, **kwargs)

    @staticmethod
    def create_adapters_from_configs(config: Dict[str, Any]) -> List[DataSource]:
        adapters = []
        for source_cfg in config.get("data_sources", []):
            source_type = source_cfg.get("type")
            if source_type == "csv":
                adapter = DataSourceFactory.create_csv_adapter(
                    source_cfg["file_content"], **source_cfg.get("params", {})
                )
            elif source_type == "json":
                adapter = DataSourceFactory.create_json_adapter(
                    source_cfg["api_data"], **source_cfg.get("params", {})
                )
            elif source_type == "xml":
                adapter = DataSourceFactory.create_xml_adapter(
                    source_cfg["xml_data"], **source_cfg.get("params", {})
                )
            elif source_type == "database":
                adapter = DataSourceFactory.create_database_adapter(
                    source_cfg["query_results"], **source_cfg.get("params", {})
                )
            else:
                raise ValueError(f"Unknown data source type: {source_type}")
            adapters.append(adapter)
        return adapters


# Sample test data
CSV_DATA = """id,timestamp,category,value,source,region
1,2024-01-15 09:30:00,sales,150.50,online,US
2,2024-01-15 10:15:00,marketing,75.25,email,EU
3,2024-01-15 11:00:00,sales,200.00,store,US"""

JSON_DATA = [
    {
        "record_id": "json_1",
        "event_time": "2024-01-15T09:30:00Z",
        "event_type": "conversion",
        "metric_value": 89.5,
        "campaign": "winter_sale",
    },
    {
        "record_id": "json_2",
        "event_time": "2024-01-15T10:15:00Z",
        "event_type": "impression",
        "metric_value": 12.3,
        "campaign": "spring_promo",
    },
]

XML_DATA = [
    {
        "item_id": "xml_1",
        "published": "2024-01-15T09:30:00Z",
        "channel": "social",
        "score": 95.8,
        "content_type": "video",
    },
    {
        "item_id": "xml_2",
        "published": "2024-01-15T10:15:00Z",
        "channel": "blog",
        "score": 87.2,
        "content_type": "article",
    },
]

DB_DATA = [
    (
        "db_1",
        "2024-01-15 09:30:00",
        "transaction",
        299.99,
        '{"payment_method": "credit_card", "merchant": "store_a"}',
    ),
    (
        "db_2",
        "2024-01-15 10:15:00",
        "refund",
        -50.00,
        '{"reason": "defective", "original_transaction": "db_0"}',
    ),
]


def demonstrate_production_features():
    """Demonstrate production-ready features"""

    # COnfiguration-driven adapter creation
    config = {
        "data_sources": [
            {
                "type": "csv",
                "file_content": CSV_DATA,
                "params": {"date_formats": ["%Y-%m-%d %H:%M:%S"]},
            },
            {"type": "json", "api_data": JSON_DATA, "params": {}},
            {"type": "xml", "xml_data": XML_DATA, "params": {}},
            {
                "type": "database",
                "query_results": DB_DATA,
                "params": {"date_formats": ["%Y-%m-%d %H:%M:%S"]},
            },
        ]
    }

    # Create adapters from config
    adapters = DataSourceFactory.create_adapters_from_configs(config)

    # Monitor performance of data fetching
    for adapter in adapters:
        logger.info(f"Processing data from {adapter.__class__.__name__}")

        # Use caching and limit
        try:
            records = list(
                monitor_performance(adapter.get_records)(limit=5, use_cache=True)
            )
            logger.info(
                f"Fetched {len(records)} records from {adapter.__class__.__name__}"
            )

            cached_records = list(
                monitor_performance(adapter.get_records)(limit=5, use_cache=True)
            )
            logger.info(
                f"Fetched {len(cached_records)} records from cache in {adapter.__class__.__name__}"
            )
        except DataSourceError as dse:
            logger.error(f"Failed to fetch data: {dse}")


if __name__ == "__main__":
    demonstrate_production_features()
