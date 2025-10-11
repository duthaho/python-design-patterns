"""
Final demonstration of the complete notification system.
Shows all patterns working together.
"""

import logging

from notification_system import NotificationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    print("=" * 80)
    print("🎉 Notification System - Complete Demo")
    print("=" * 80)

    # Initialize manager from config
    print("\n📂 Initializing from configuration...")
    manager = NotificationManager.from_config()

    print(f"✅ {manager}")
    print(f"📋 Available channels: {manager.list_available_channels()}")
    print(f"📋 Configured events: {manager.list_configured_events()}")

    # Example 1: Send event-based notification (simple API)
    print("\n" + "=" * 80)
    print("Example 1: Event-based notification (simple string event)")
    print("=" * 80)

    results = manager.send_event(
        "user.signup",
        username="Alice",
        email="alice@example.com",
        signup_date="2025-01-15",
    )

    print(f"\n📊 Results: {len(results)} notifications sent")
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"  {status} {result.channel}: {result.message}")

    # Example 2: Send with concrete event class
    print("\n" + "=" * 80)
    print("Example 2: Using concrete event classes")
    print("=" * 80)

    # Note: For this to work, you'd need to modify send_event to accept Event objects
    # For now, we'll just show direct notification

    # Example 3: Direct notification (bypass event mapping)
    print("\n" + "=" * 80)
    print("Example 3: Direct notification (bypass event system)")
    print("=" * 80)

    result = manager.send_notification(
        channel="console",
        recipients=["bob@example.com"],
        subject="Direct Notification",
        body="This is a direct notification that bypasses the event system!",
    )

    print(f"\n📧 Direct send result:")
    print(f"  {'✅' if result.success else '❌'} Channel: {result.channel}")
    print(f"  Message: {result.message}")

    # Example 4: Multiple events in sequence
    print("\n" + "=" * 80)
    print("Example 4: Processing multiple events")
    print("=" * 80)

    events_to_send = [
        ("user.signup", {"username": "Charlie", "email": "charlie@example.com"}),
        (
            "order.placed",
            {
                "order_id": "ORD-001",
                "customer_name": "Charlie",
                "customer_email": "charlie@example.com",
                "total_amount": 99.99,
                "item_count": 3,
            },
        ),
        (
            "order.shipped",
            {
                "order_id": "ORD-001",
                "customer_email": "charlie@example.com",
                "tracking_number": "TRACK-12345",
                "carrier": "FedEx",
            },
        ),
    ]

    for event_type, data in events_to_send:
        print(f"\n📨 Sending event: {event_type}")
        results = manager.send_event(event_type, **data)
        print(f"  ✅ Sent to {len(results)} channels")

    # Example 5: Statistics
    print("\n" + "=" * 80)
    print("Example 5: System Statistics")
    print("=" * 80)

    stats = manager.get_statistics()
    print(f"\n📊 Notification Statistics:")
    print(f"  Total sent: {stats['total_sent']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")

    # Example 6: Error handling demonstration
    print("\n" + "=" * 80)
    print("Example 6: Error handling (invalid event)")
    print("=" * 80)

    try:
        # This should use default channels since event type is not configured
        results = manager.send_event("unknown.event", some_data="test")
        print(
            f"  ℹ️  Unknown event handled gracefully with {len(results)} default notifications"
        )
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print("\n" + "=" * 80)
    print("✅ Demo completed successfully!")
    print("=" * 80)

    # Show final stats
    final_stats = manager.get_statistics()
    print(f"\n🎯 Final Statistics:")
    print(f"  Total: {final_stats['total_sent']}")
    print(
        f"  Success: {final_stats['successful']} ({final_stats['success_rate']:.1f}%)"
    )
    print(f"  Failed: {final_stats['failed']}")


if __name__ == "__main__":
    main()
