"""Sample data fixtures for testing."""

from datetime import datetime, timedelta

from pipeline_framework.core.models import PipelineData


def create_sample_users(count: int = 5) -> list[PipelineData]:
    """Create sample user data."""
    users = []
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    cities = ["NYC", "SF", "LA", "Chicago", "Boston", "Seattle", "Austin", "Denver"]

    for i in range(count):
        data = PipelineData.create(
            payload={
                "name": names[i % len(names)],
                "age": 20 + (i * 5),
                "city": cities[i % len(cities)],
                "active": i % 2 == 0,
            }
        )
        users.append(data)

    return users


def create_sample_transactions(count: int = 10) -> list[PipelineData]:
    """Create sample transaction data."""
    transactions = []
    base_time = datetime.now()

    for i in range(count):
        data = PipelineData(
            id=f"txn-{i+1}",
            payload={
                "amount": 10.0 + (i * 5.5),
                "currency": "USD" if i % 2 == 0 else "EUR",
                "merchant": f"Store-{i % 3}",
                "category": ["food", "transport", "entertainment"][i % 3],
            },
            metadata={"source": "pos"},
            timestamp=base_time + timedelta(hours=i),
        )
        transactions.append(data)

    return transactions


def create_sample_events(count: int = 8) -> list[PipelineData]:
    """Create sample event data."""
    events = []
    event_types = ["login", "logout", "purchase", "view"]

    for i in range(count):
        data = PipelineData.create(
            payload={
                "event_type": event_types[i % len(event_types)],
                "user_id": f"user-{i % 3}",
                "session_id": f"session-{i // 2}",
                "properties": {
                    "browser": "chrome" if i % 2 == 0 else "firefox",
                    "device": "mobile" if i % 3 == 0 else "desktop",
                },
            }
        )
        events.append(data)

    return events
