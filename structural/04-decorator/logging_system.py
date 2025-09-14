import json
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logger(Protocol):
    """Base logger protocol that all loggers must implement"""

    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with the given level and optional metadata"""
        ...


class BaseLogger:
    """Simple base implementation that does nothing - just passes through"""

    def log(self, level: str, message: str, **kwargs) -> None:
        pass  # Base implementation does nothing


class LoggerDecorator:
    """Base decorator class that all logging decorators should inherit from"""

    def __init__(self, wrapped_logger: Logger):
        self._wrapped = wrapped_logger

    def log(self, level: str, message: str, **kwargs) -> None:
        # Default behavior: just delegate to wrapped logger
        self._wrapped.log(level, message, **kwargs)


# =============================================================================
# OUTPUT DECORATORS - Where the logs actually go
# =============================================================================


class ConsoleLogger(LoggerDecorator):
    """Outputs logs to console/stdout"""

    def __init__(self, wrapped_logger: Logger):
        super().__init__(wrapped_logger)

    def log(self, level: str, message: str, **kwargs) -> None:
        # Format kwargs for display if they exist
        kwargs_str = f" {kwargs}" if kwargs else ""
        print(f"[{level}] {message}{kwargs_str}")
        super().log(level, message, **kwargs)


class FileLogger(LoggerDecorator):
    """Outputs logs to a file"""

    def __init__(self, wrapped_logger: Logger, filename: str):
        super().__init__(wrapped_logger)
        self.filename = filename

    def log(self, level: str, message: str, **kwargs) -> None:
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                kwargs_str = f" {kwargs}" if kwargs else ""
                f.write(f"[{level}] {message}{kwargs_str}\n")
        except Exception as e:
            # If file writing fails, at least continue with the chain
            print(f"FileLogger error: {e}")

        super().log(level, message, **kwargs)


class DatabaseLogger(LoggerDecorator):
    """Simulates logging to a database"""

    def __init__(self, wrapped_logger: Logger, table_name: str = "logs"):
        super().__init__(wrapped_logger)
        self.table_name = table_name
        self._db_logs = []  # Simulate database with a list

    def log(self, level: str, message: str, **kwargs) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "table": self.table_name,
            "metadata": kwargs,
        }
        self._db_logs.append(log_entry)
        super().log(level, message, **kwargs)

    def get_logs(self) -> List[Dict]:
        """Helper method to retrieve stored logs"""
        return self._db_logs

    def clear_logs(self) -> None:
        """Helper method to clear stored logs"""
        self._db_logs.clear()


class SlackLogger(LoggerDecorator):
    """Simulates sending logs to Slack"""

    def __init__(self, wrapped_logger: Logger, channel: str = "#alerts"):
        super().__init__(wrapped_logger)
        self.channel = channel

    def log(self, level: str, message: str, **kwargs) -> None:
        # Only send ERROR and CRITICAL to Slack to avoid spam
        if level in {LogLevel.ERROR.value, LogLevel.CRITICAL.value}:
            kwargs_str = f" {kwargs}" if kwargs else ""
            print(f"🚨 SLACK ALERT to {self.channel}: [{level}] {message}{kwargs_str}")
        super().log(level, message, **kwargs)


# =============================================================================
# FORMATTING DECORATORS - How the logs look
# =============================================================================


class TimestampFormatter(LoggerDecorator):
    """Adds timestamp to log messages"""

    def __init__(self, wrapped_logger: Logger, format_str: str = "%Y-%m-%d %H:%M:%S"):
        super().__init__(wrapped_logger)
        self.format_str = format_str

    def log(self, level: str, message: str, **kwargs) -> None:
        timestamp = datetime.now().strftime(self.format_str)
        # Add timestamp to kwargs so it flows through the entire chain
        enhanced_kwargs = kwargs.copy()
        enhanced_kwargs["timestamp"] = timestamp
        super().log(level, message, **enhanced_kwargs)


class JSONFormatter(LoggerDecorator):
    """Formats log messages as JSON"""

    def __init__(self, wrapped_logger: Logger):
        super().__init__(wrapped_logger)

    def log(self, level: str, message: str, **kwargs) -> None:
        # Create complete log entry as JSON
        log_entry = {
            "level": level,
            "message": message,
            **kwargs,  # Include all metadata
        }
        json_message = json.dumps(
            log_entry, default=str
        )  # default=str handles datetime objects

        # Pass the JSON as the message, but keep original kwargs for other decorators
        super().log(level, json_message, **kwargs)


class StructuredFormatter(LoggerDecorator):
    """Formats logs in a structured way: [LEVEL] message key=value key=value"""

    def log(self, level: str, message: str, **kwargs) -> None:
        # Build structured format
        if kwargs:
            kwargs_str = " " + " ".join(f"{k}={v}" for k, v in kwargs.items())
            formatted_message = f"[{level}] {message}{kwargs_str}"
        else:
            formatted_message = f"[{level}] {message}"

        # Pass formatted message but keep original kwargs
        super().log(level, formatted_message, **kwargs)


# =============================================================================
# FILTER DECORATORS - Control what gets logged
# =============================================================================


class LevelFilter(LoggerDecorator):
    """Only allows certain log levels through"""

    def __init__(self, wrapped_logger: Logger, allowed_levels: List[str]):
        super().__init__(wrapped_logger)
        self.allowed_levels = set(allowed_levels)

    def log(self, level: str, message: str, **kwargs) -> None:
        if level in self.allowed_levels:
            super().log(level, message, **kwargs)
        # If level not allowed, completely block the log (don't call super)


class SamplingFilter(LoggerDecorator):
    """Only logs every Nth message (useful for high-volume logging)"""

    def __init__(self, wrapped_logger: Logger, sample_rate: int):
        super().__init__(wrapped_logger)
        self.sample_rate = sample_rate
        self.counter = 0

    def log(self, level: str, message: str, **kwargs) -> None:
        self.counter += 1
        if self.counter % self.sample_rate == 0:
            super().log(level, message, **kwargs)
        # If not sampled, don't call super() to block the log


# =============================================================================
# ENHANCEMENT DECORATORS - Add extra functionality
# =============================================================================


class MetricsCollector(LoggerDecorator):
    """Collects metrics about log levels and frequency"""

    def __init__(self, wrapped_logger: Logger):
        super().__init__(wrapped_logger)
        self.metrics = defaultdict(int)
        self.start_time = time.time()

    def log(self, level: str, message: str, **kwargs) -> None:
        # Collect metrics ONLY for logs that actually pass through
        self.metrics[level] += 1
        super().log(level, message, **kwargs)

    def get_metrics(self) -> Dict[str, Any]:
        """Return collected metrics"""
        return {
            "log_counts": dict(self.metrics),
            "total_logs": sum(self.metrics.values()),
            "uptime_seconds": round(time.time() - self.start_time, 2),
        }

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics.clear()
        self.start_time = time.time()


class AlertingDecorator(LoggerDecorator):
    """Triggers alerts for critical log levels"""

    def __init__(self, wrapped_logger: Logger, alert_levels: List[str] = None):
        super().__init__(wrapped_logger)
        self.alert_levels = set(alert_levels or ["ERROR", "CRITICAL"])
        self.alerts_sent = []

    def log(self, level: str, message: str, **kwargs) -> None:
        if level in self.alert_levels:
            alert_info = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "metadata": kwargs,
            }
            self.alerts_sent.append(alert_info)

            # Print internal alert (different from Slack alerts)
            print(f"🔔 INTERNAL ALERT: [{level}] {message}")

        super().log(level, message, **kwargs)

    def get_alerts(self) -> List[Dict]:
        """Return all alerts that were sent"""
        return self.alerts_sent

    def clear_alerts(self) -> None:
        """Clear alert history"""
        self.alerts_sent.clear()


class AsyncLogger(LoggerDecorator):
    """Simulates async logging with time delays"""

    def __init__(self, wrapped_logger: Logger, delay_seconds: float = 0.1):
        super().__init__(wrapped_logger)
        self.delay_seconds = delay_seconds

    def log(self, level: str, message: str, **kwargs) -> None:
        # Simulate async processing delay
        time.sleep(self.delay_seconds)
        super().log(level, message, **kwargs)


class RateLimitDecorator(LoggerDecorator):
    """Rate limits logging to prevent spam (logs per second)"""

    def __init__(self, wrapped_logger: Logger, max_logs_per_second: float = 10.0):
        super().__init__(wrapped_logger)
        self.max_logs_per_second = max_logs_per_second
        self.min_interval = 1.0 / max_logs_per_second
        self.last_log_time = 0
        self.dropped_count = 0

    def log(self, level: str, message: str, **kwargs) -> None:
        current_time = time.time()

        if current_time - self.last_log_time >= self.min_interval:
            # If we dropped logs, mention it
            if self.dropped_count > 0:
                super().log(
                    "WARNING", f"Rate limiter dropped {self.dropped_count} logs"
                )
                self.dropped_count = 0

            self.last_log_time = current_time
            super().log(level, message, **kwargs)
        else:
            self.dropped_count += 1


# =============================================================================
# ERROR HANDLING DECORATOR
# =============================================================================


class ErrorHandlingDecorator(LoggerDecorator):
    """Wraps other loggers to handle exceptions gracefully"""

    def __init__(
        self, wrapped_logger: Logger, fallback_logger: Optional[Logger] = None
    ):
        super().__init__(wrapped_logger)
        # Create a simple fallback that doesn't depend on other decorators
        self.fallback_logger = fallback_logger or ConsoleLogger(BaseLogger())
        self.error_count = 0
        self.last_error_time = None

    def log(self, level: str, message: str, **kwargs) -> None:
        try:
            super().log(level, message, **kwargs)
        except Exception as e:
            self.error_count += 1
            self.last_error_time = datetime.now()

            # Log the error using fallback logger
            self.fallback_logger.log(
                "ERROR",
                f"Logging system failure: {str(e)}",
                original_level=level,
                original_message=message,
                error_count=self.error_count,
                **kwargs,
            )

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": self.error_count,
            "last_error_time": (
                self.last_error_time.isoformat() if self.last_error_time else None
            ),
        }


# =============================================================================
# UTILITY FUNCTIONS FOR EASY LOGGER CREATION
# =============================================================================


def create_dev_logger() -> Logger:
    """Create a development logger: verbose, console-only, with metrics"""
    logger = BaseLogger()
    logger = ConsoleLogger(logger)
    logger = TimestampFormatter(logger)
    logger = MetricsCollector(logger)
    logger = ErrorHandlingDecorator(logger)
    return logger


def create_prod_logger(log_file: str = "prod.log") -> Logger:
    """Create a production logger: filtered, multiple outputs, alerting"""
    logger = BaseLogger()

    # Multiple outputs
    logger = SlackLogger(logger, "#prod-alerts")
    logger = DatabaseLogger(logger, "prod_logs")
    logger = FileLogger(logger, log_file)
    logger = ConsoleLogger(logger)

    # Formatting and enhancement
    logger = JSONFormatter(logger)
    logger = TimestampFormatter(logger)
    logger = AlertingDecorator(logger, ["ERROR", "CRITICAL"])
    logger = MetricsCollector(logger)

    # Filtering and protection
    logger = LevelFilter(logger, ["INFO", "WARNING", "ERROR", "CRITICAL"])
    logger = RateLimitDecorator(logger, max_logs_per_second=50.0)
    logger = ErrorHandlingDecorator(logger)

    return logger


def create_debug_logger(debug_file: str = "debug.log") -> Logger:
    """Create a debug logger: everything, with sampling to avoid spam"""
    logger = BaseLogger()
    logger = FileLogger(logger, debug_file)
    logger = SamplingFilter(logger, sample_rate=5)  # Every 5th message
    logger = StructuredFormatter(logger)
    logger = TimestampFormatter(logger)
    logger = ErrorHandlingDecorator(logger)
    return logger


# =============================================================================
# MAIN TESTING AND DEMONSTRATION
# =============================================================================


if __name__ == "__main__":
    print("🚀 Enterprise Logging System - Complete Implementation")
    print("=" * 60)

    # Test 1: Basic functionality
    print("\n📝 Test 1: Basic Logging")
    print("-" * 30)
    basic_logger = ConsoleLogger(BaseLogger())
    basic_logger.log("INFO", "Basic test message", component="test")

    # Test 2: Complex decorator chain with proper ordering
    print("\n⚙️  Test 2: Complex Decorator Chain (Proper Order)")
    print("-" * 30)
    logger = BaseLogger()

    # Build from inside out: Output → Format → Filter → Enhance → Protect
    logger = ConsoleLogger(logger)  # Output layer
    logger = StructuredFormatter(logger)  # Format layer
    logger = TimestampFormatter(logger)  # Add timestamps
    logger = LevelFilter(logger, ["INFO", "WARNING", "ERROR"])  # Filter layer
    logger = MetricsCollector(logger)  # Enhancement layer
    logger = ErrorHandlingDecorator(logger)  # Protection layer

    # Test the chain
    logger.log("INFO", "Application started", version="2.0.0", port=8080)
    logger.log("DEBUG", "This should be filtered out", debug_data="sensitive")
    logger.log("WARNING", "High memory usage", memory_pct=85, threshold=80)
    logger.log(
        "ERROR", "Database connection failed", db_host="prod-db-01", retry_count=3
    )

    # Get metrics (need to find the MetricsCollector in the chain)
    current = logger
    while hasattr(current, "_wrapped") and not isinstance(current, MetricsCollector):
        current = current._wrapped
    if isinstance(current, MetricsCollector):
        print("\n📊 Metrics:", current.get_metrics())

    # Test 3: Multiple outputs
    print("\n📤 Test 3: Multiple Output Destinations")
    print("-" * 30)
    multi_logger = BaseLogger()
    multi_logger = DatabaseLogger(multi_logger, "multi_test")
    multi_logger = FileLogger(multi_logger, "multi_test.log")
    multi_logger = ConsoleLogger(multi_logger)
    multi_logger = JSONFormatter(multi_logger)
    multi_logger = TimestampFormatter(multi_logger)

    multi_logger.log(
        "INFO", "Multi-output message", service="payment", transaction_id="TXN-123"
    )

    # Show database contents
    db_layer = (
        multi_logger._wrapped._wrapped._wrapped._wrapped
    )  # Navigate to DatabaseLogger
    print(f"💾 Database contains {len(db_layer.get_logs())} entries")

    # Test 4: Error handling
    print("\n🛡️  Test 4: Error Handling")
    print("-" * 30)

    class FailingLogger(LoggerDecorator):
        def log(self, level: str, message: str, **kwargs) -> None:
            raise Exception("Simulated logger failure!")

    safe_logger = ErrorHandlingDecorator(FailingLogger(BaseLogger()))
    safe_logger.log("INFO", "This should be handled gracefully", test=True)
    print(f"🔥 Error stats: {safe_logger.get_error_stats()}")

    # Test 5: Pre-configured loggers
    print("\n🏭 Test 5: Pre-configured Production Logger")
    print("-" * 30)
    prod_logger = create_prod_logger("demo_prod.log")

    prod_logger.log(
        "INFO",
        "Order processed successfully",
        order_id="ORD-456",
        customer_id="CUST-789",
        amount=149.99,
    )
    prod_logger.log(
        "ERROR",
        "Payment gateway timeout",
        order_id="ORD-456",
        gateway="stripe",
        timeout_ms=5000,
    )

    # Test 6: High-volume with sampling
    print("\n⚡ Test 6: High-Volume Logging with Sampling")
    print("-" * 30)
    volume_logger = BaseLogger()
    volume_logger = ConsoleLogger(volume_logger)
    volume_logger = SamplingFilter(volume_logger, sample_rate=7)  # Every 7th message
    volume_logger = MetricsCollector(volume_logger)

    print("Sending 20 messages, should only see every 7th one...")
    for i in range(20):
        volume_logger.log("INFO", f"High volume message {i}", batch_id=f"batch_{i//5}")

    # Find metrics collector
    print(f"📈 Volume test metrics: {volume_logger.get_metrics()}")

    # Test 7: Rate limiting
    print("\n🚦 Test 7: Rate Limiting")
    print("-" * 30)
    rate_limited_logger = RateLimitDecorator(
        ConsoleLogger(BaseLogger()), max_logs_per_second=2.0
    )

    print("Sending 5 rapid messages (max 2/second)...")
    for i in range(5):
        rate_limited_logger.log("INFO", f"Rapid message {i}")
        time.sleep(0.1)  # 10 messages per second - should be rate limited

    print("\n✅ All tests completed!")
    print("\n🎯 Key Features Demonstrated:")
    print("   • Multiple output destinations (Console, File, Database, Slack)")
    print("   • Flexible formatting (JSON, Structured, Timestamped)")
    print("   • Smart filtering (Level-based, Sampling, Rate limiting)")
    print("   • Enterprise features (Metrics, Alerting, Error handling)")
    print("   • Proper decorator ordering and composition")
    print("   • Pre-configured logger factories")
