"""
Example usage of the Factory Pattern.
"""

import logging

from notification_system.core.notification import Notification
from notification_system.factories import ChannelFactory

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    print("=" * 70)
    print("🏭 Notification System - Factory Pattern Demo")
    print("=" * 70)

    # Create factory from config file
    print("\n📂 Loading configuration...")
    factory = ChannelFactory.from_config("config/channels.yaml")

    # Show available channels
    print(f"\n✅ Available channels: {factory.list_channels()}")
    print(f"✅ Registered types: {factory.list_channel_types()}")

    # Create console channel
    print("\n🔧 Creating console channel with decorators...")
    console_channel = factory.create("console")
    print(f"   Type: {type(console_channel).__name__}")
    print(
        f"   Wrapped: {type(console_channel.wrapped).__name__ if hasattr(console_channel, 'wrapped') else 'N/A'}"
    )

    # Create notification
    notification = Notification(
        event_id="demo-001",
        channel="console",
        recipients=["user@example.com", "admin@example.com"],
        subject="Factory Pattern Demo",
        body="This notification was created using the Factory Pattern!\n\n"
        "Features demonstrated:\n"
        "- Configuration-driven channel creation\n"
        "- Automatic decorator application\n"
        "- Environment variable substitution",
    )

    # Send notification
    print("\n📤 Sending notification...")
    result = console_channel.send(notification)

    print(f"\n✅ Result:")
    print(f"   Success: {result.success}")
    print(f"   Channel: {result.channel}")
    print(f"   Sent at: {result.sent_at}")

    # Demonstrate programmatic creation
    print("\n🔧 Creating channel programmatically (without config file)...")
    custom_channel = factory.create_from_config(
        "ConsoleChannel",
        {"format": "json", "colored": False},
        [
            {"type": "retry", "max_retries": 2},
            {"type": "logging", "log_level": "DEBUG"},
        ],
    )

    notification2 = Notification(
        event_id="demo-002",
        channel="console",
        recipients=["test@example.com"],
        subject="Programmatic Creation",
        body="This was created without YAML config!",
    )

    print("\n📤 Sending through programmatically created channel...")
    result2 = custom_channel.send(notification2)
    print(f"✅ Success: {result2.success}")

    print("\n" + "=" * 70)
    print("✅ Factory Pattern demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
