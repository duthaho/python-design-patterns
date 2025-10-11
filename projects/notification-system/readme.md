# 🔔 Notification System

A production-ready, design pattern-driven notification framework built in Python. Send notifications across multiple channels (Email, Webhook, Console) with automatic retries, rate limiting, and structured logging.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](htmlcov/index.html)

## ✨ Features

- 🚀 **Multiple Channels**: Email (SMTP), Webhook (HTTP), Console (Development)
- 🔄 **Automatic Retry**: Exponential backoff with configurable retries
- ⚡ **Rate Limiting**: Token bucket algorithm prevents API overload
- 📊 **Structured Logging**: Full observability of notification flow
- 🎯 **Event-Driven**: Map events to notifications via configuration
- 🏗️ **Design Patterns**: 12+ patterns implemented for maintainability
- ⚙️ **Configuration-Driven**: YAML-based setup with environment variables
- 🧪 **Fully Tested**: 95%+ code coverage with unit and integration tests

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Architecture](#architecture)
- [Design Patterns](#design-patterns)
- [Extending the System](#extending-the-system)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- pip or uv package manager

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/notification-system.git
cd notification-system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file for sensitive configuration:

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

## ⚡ Quick Start

### Basic Usage

```python
from notification_system import NotificationManager

# Initialize from configuration
manager = NotificationManager.from_config()

# Send event-based notification
manager.send_event(
    'user.signup',
    username='Alice',
    email='alice@example.com'
)

# Send direct notification
manager.send_notification(
    channel='email',
    recipients=['user@example.com'],
    subject='Welcome!',
    body='Thank you for signing up!'
)

# Get statistics
stats = manager.get_statistics()
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### Example Output

```
2025-01-15 10:30:45 - EventProcessor - INFO - Processing event evt-123 of type user.signup
2025-01-15 10:30:45 - EventProcessor - INFO - Mapped event to 2 notifications
2025-01-15 10:30:45 - LoggingDecorator - INFO - Sending notification via EmailChannel
2025-01-15 10:30:46 - LoggingDecorator - INFO - Notification sent successfully in 0.85s
✅ 2/2 notifications sent successfully
```

## ⚙️ Configuration

### Channel Configuration (`config/channels.yaml`)

```yaml
channels:
  email:
    type: EmailChannel
    enabled: true
    config:
      smtp_host: ${SMTP_HOST:smtp.gmail.com}
      smtp_port: ${SMTP_PORT:587}
      username: ${SMTP_USERNAME}
      password: ${SMTP_PASSWORD}
      from_email: ${SMTP_FROM_EMAIL}
      use_tls: true
    decorators:
      - type: retry
        max_retries: 3
        initial_delay: 1.0
        backoff_multiplier: 2.0
      - type: logging
        log_level: INFO
      - type: rate_limit
        rate_limit: 100
        time_window: 3600

  webhook:
    type: WebhookChannel
    enabled: true
    config:
      timeout: 30
      verify_ssl: true
    decorators:
      - type: retry
        max_retries: 2
      - type: logging
      - type: rate_limit
        rate_limit: 50
        time_window: 60

  console:
    type: ConsoleChannel
    enabled: true
    config:
      format: pretty
      colored: true
    decorators:
      - type: logging
```

### Event Configuration (`config/events.yaml`)

```yaml
events:
  user.signup:
    description: "New user registration"
    channels:
      - email
      - webhook
    priority: high
    template:
      subject: "Welcome to {app_name}!"
      body: |
        Hello {username},
        
        Welcome to our platform!
        Your email: {email}
        Signup date: {signup_date}

  order.placed:
    description: "New order placed"
    channels:
      - email
    priority: high
    template:
      subject: "Order Confirmation #{order_id}"
      body: |
        Hello {customer_name},
        
        Order ID: {order_id}
        Total: {total_amount}
        Items: {item_count}
```

## 💡 Usage Examples

### Event-Based Notifications

```python
from notification_system import NotificationManager

manager = NotificationManager.from_config()

# User signup notification (mapped to email + webhook)
manager.send_event(
    'user.signup',
    username='Bob',
    email='bob@example.com',
    signup_date='2025-01-15'
)

# Order notification (mapped to email only)
manager.send_event(
    'order.placed',
    order_id='ORD-12345',
    customer_name='Bob',
    customer_email='bob@example.com',
    total_amount=149.99,
    item_count=3
)
```

### Direct Notifications

```python
# Send to specific channel without event mapping
manager.send_notification(
    channel='webhook',
    recipients=['https://hooks.slack.com/your-webhook'],
    body='System alert: High CPU usage detected'
)

# Send email with custom content
manager.send_notification(
    channel='email',
    recipients=['admin@example.com', 'ops@example.com'],
    subject='Critical Alert',
    body='Database backup failed at 2:30 AM'
)
```

### Using Concrete Event Classes

```python
from notification_system.events import UserSignupEvent, OrderPlacedEvent

# Create strongly-typed events
signup_event = UserSignupEvent(
    username='Charlie',
    email='charlie@example.com'
)

order_event = OrderPlacedEvent(
    order_id='ORD-67890',
    customer_name='Charlie',
    customer_email='charlie@example.com',
    total_amount=299.99,
    item_count=5
)

# Process events
manager.event_processor.process_event(signup_event)
manager.event_processor.process_event(order_event)
```

### Statistics and Monitoring

```python
# Get detailed statistics
stats = manager.get_statistics()
print(f"""
Notification Statistics:
  Total Sent: {stats['total_sent']}
  Successful: {stats['successful']}
  Failed: {stats['failed']}
  Success Rate: {stats['success_rate']:.1f}%
""")

# List available channels
channels = manager.list_available_channels()
print(f"Available channels: {channels}")

# List configured events
events = manager.list_configured_events()
print(f"Configured events: {events}")
```

## 🏗️ Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────┐
│              NotificationManager (Facade)                │
│  - Simple API for users                                  │
│  - Hides system complexity                               │
└─────────────┬───────────────────────┬────────────────────┘
              │                       │
     ┌────────▼────────┐    ┌─────────▼─────────┐
     │ EventProcessor  │    │  ChannelFactory   │
     │   (Observer)    │    │    (Factory)      │
     └────────┬────────┘    └────────┬──────────┘
              │                      │
     ┌────────▼──────────┐  ┌────────▼──────────┐
     │ NotificationMapper│  │ Channels          │
     │   (Strategy)      │  │ + Decorators      │
     └───────────────────┘  └───────────────────┘
                                     │
                          ┌──────────┼──────────┐
                          │          │          │
                     ┌────▼───┐ ┌────▼───┐ ┌────▼───┐
                     │ Email  │ │Webhook │ │Console │
                     │Channel │ │Channel │ │Channel │
                     └────────┘ └────────┘ └────────┘
```

### Component Responsibilities

- **NotificationManager**: High-level facade, user-facing API
- **EventProcessor**: Orchestrates event-to-notification flow
- **NotificationMapper**: Maps events to channels using templates
- **ChannelFactory**: Creates and configures channels dynamically
- **DecoratorFactory**: Applies cross-cutting concerns (retry, logging, rate limiting)
- **Channels**: Implement specific notification delivery mechanisms

## 🎨 Design Patterns

This project demonstrates 12 design patterns:

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Facade** | `NotificationManager` | Simplified interface to complex subsystem |
| **Factory Method** | `ChannelFactory`, `DecoratorFactory` | Create objects without specifying exact class |
| **Abstract Factory** | `ChannelFactory` | Create families of related objects |
| **Strategy** | Channel implementations | Interchangeable algorithms |
| **Template Method** | `NotificationChannel.send()` | Define algorithm skeleton |
| **Decorator** | Retry, Logging, RateLimit | Add behavior dynamically |
| **Observer** | `EventProcessor` | React to events |
| **Mediator** | `EventProcessor` | Coordinate components |
| **Registry** | Channel/Decorator registration | Manage available implementations |
| **Builder** | Event/Notification construction | Build complex objects step-by-step |
| **DTO** | `Notification`, `NotificationResult` | Transfer data between layers |
| **Singleton** | `Settings` (conceptually) | Single configuration instance |

## 🔧 Extending the System

### Adding a New Channel

```python
# 1. Create channel class
from notification_system.channels.base import NotificationChannel

class SmsChannel(NotificationChannel):
    def validate_notification(self, notification):
        # Validate phone numbers
        pass
    
    def prepare_message(self, notification):
        # Format SMS message
        pass
    
    def send_message(self, message, connection):
        # Send via SMS API
        pass
    
    def create_connection(self):
        # Create SMS API connection
        pass
    
    def close_connection(self, connection):
        # Close connection
        pass

# 2. Register channel
factory = ChannelFactory()
factory.register('SmsChannel', SmsChannel)

# 3. Add to configuration
# config/channels.yaml
# channels:
#   sms:
#     type: SmsChannel
#     config:
#       api_key: ${SMS_API_KEY}
```

### Adding a Custom Decorator

```python
from notification_system.channels.base import ChannelProtocol

class MetricsDecorator:
    """Track notification metrics."""
    
    def __init__(self, wrapped: ChannelProtocol):
        self.wrapped = wrapped
        self.metrics = {'sent': 0, 'failed': 0}
    
    def send(self, notification):
        result = self.wrapped.send(notification)
        if result.success:
            self.metrics['sent'] += 1
        else:
            self.metrics['failed'] += 1
        return result
    
    def __getattr__(self, name):
        return getattr(self.wrapped, name)

# Register decorator
factory = DecoratorFactory()
factory.register('metrics', MetricsDecorator)
```

### Creating Custom Event Classes

```python
from notification_system.core.event import Event, EventPriority

class ProductLaunchEvent(Event):
    REQUIRED_PAYLOAD_FIELDS = {'product_name', 'launch_date', 'price'}
    
    def __init__(self, product_name, launch_date, price, **kwargs):
        payload = {
            'product_name': product_name,
            'launch_date': launch_date,
            'price': price,
            **kwargs
        }
        super().__init__(
            event_type='product.launch',
            payload=payload,
            priority=EventPriority.HIGH
        )
    
    def validate_payload(self):
        if self.payload['price'] <= 0:
            raise ValueError("Price must be positive")
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/notification_system --cov-report=html

# Run specific test file
pytest tests/unit/test_channels.py -v

# Run integration tests only
pytest tests/integration/ -v
```

### Test Structure

```
tests/
├── unit/
│   ├── test_channels.py      # Channel implementations
│   ├── test_decorators.py    # Decorator logic
│   └── test_factory.py       # Factory patterns
├── integration/
│   └── test_notification_system.py  # End-to-end tests
└── fixtures/
    └── sample_events.py      # Test data
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src/notification_system --cov-report=html

# Open in browser
open htmlcov/index.html
```

Current coverage: **95%+**

## 📚 API Reference

### NotificationManager

```python
class NotificationManager:
    """High-level facade for notification system."""
    
    @classmethod
    def from_config(
        cls,
        channels_config_path: str = 'config/channels.yaml',
        events_config_path: str = 'config/events.yaml'
    ) -> 'NotificationManager':
        """Create manager from configuration files."""
    
    def send_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        priority: str = 'normal',
        **data
    ) -> List[NotificationResult]:
        """Send notifications for an event."""
    
    def send_notification(
        self,
        channel: str,
        recipients: List[str],
        body: str,
        subject: Optional[str] = None,
        **kwargs
    ) -> NotificationResult:
        """Send direct notification."""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics."""
    
    def list_available_channels(self) -> List[str]:
        """List available channels."""
    
    def list_configured_events(self) -> List[str]:
        """List configured event types."""
```

### Event Classes

```python
class Event:
    """Base event class."""
    
    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize event."""

class UserSignupEvent(Event):
    """User registration event."""
    
    def __init__(
        self,
        username: str,
        email: str,
        signup_date: str = None,
        **kwargs
    ):
        """Initialize user signup event."""

class OrderPlacedEvent(Event):
    """Order placement event."""
    
    def __init__(
        self,
        order_id: str,
        customer_name: str,
        customer_email: str,
        total_amount: float,
        item_count: int,
        **kwargs
    ):
        """Initialize order placed event."""
```

### Notification Classes

```python
@dataclass
class Notification:
    """Notification data transfer object."""
    
    event_id: str
    channel: str
    recipients: List[str]
    body: str
    subject: Optional[str] = None
    # ... other fields

@dataclass
class NotificationResult:
    """Result of notification send operation."""
    
    success: bool
    channel: str
    message: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests**: Maintain 90%+ coverage
5. **Run tests**: `pytest tests/ -v`
6. **Format code**: `black src/ tests/`
7. **Commit changes**: `git commit -m 'Add amazing feature'`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small
- Add tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by enterprise notification systems
- Built with Python and best practices
- Design patterns from Gang of Four
- Architecture principles from Clean Code and SOLID

## 📞 Contact

- **Author**: duthaho
- **GitHub**: [@duthaho](https://github.com/duthaho)

## 🗺️ Roadmap

### Current Version: 1.0.0

- [x] Multiple channels (Email, Webhook, Console)
- [x] Decorator pattern (Retry, Logging, RateLimit)
- [x] Event-driven architecture
- [x] Configuration management
- [x] Comprehensive testing

### Future Enhancements

- [ ] SMS channel (Twilio integration)
- [ ] Slack channel
- [ ] Push notification support
- [ ] Template engine (Jinja2)
- [ ] Async/await support
- [ ] Message queue integration (RabbitMQ/Kafka)
- [ ] Web dashboard UI
- [ ] Metrics and monitoring (Prometheus)
- [ ] Database persistence
- [ ] Multi-language support

---

**Built with ❤️ and Design Patterns**

⭐ Star this repo if you find it helpful!
