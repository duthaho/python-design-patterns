"""
Unit tests for factory implementations.
"""

import os
import tempfile
import unittest
from pathlib import Path

import yaml
from notification_system.channels.console import ConsoleChannel
from notification_system.config.settings import ConfigurationError, Settings
from notification_system.decorators.logging import LoggingDecorator
from notification_system.decorators.retry import RetryDecorator
from notification_system.factories import ChannelFactory, DecoratorFactory


class TestSettings(unittest.TestCase):
    """Test Settings configuration loader."""

    def setUp(self):
        """Create a temporary config file."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"

    def tearDown(self):
        """Clean up temp files."""
        if self.config_file.exists():
            self.config_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_load_valid_config(self):
        """Should load valid YAML configuration."""
        config = {
            "channels": {
                "console": {
                    "type": "ConsoleChannel",
                    "config": {"format": "pretty"},
                    "decorators": [],
                }
            }
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        settings = Settings(config_path=str(self.config_file))

        self.assertIn("channels", settings.config)
        self.assertEqual(settings.get("channels.console.type"), "ConsoleChannel")

    def test_env_var_substitution_with_default(self):
        """Should substitute environment variables with defaults."""
        config = {
            "channels": {
                "test": {
                    "type": "ConsoleChannel",
                    "config": {"host": "${TEST_HOST:localhost}"},
                    "decorators": [],
                }
            }
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        # Don't set TEST_HOST env var, should use default
        settings = Settings(config_path=str(self.config_file))

        self.assertEqual(settings.get("channels.test.config.host"), "localhost")

    def test_env_var_substitution_from_environment(self):
        """Should use environment variable if set."""
        config = {
            "channels": {
                "test": {
                    "type": "ConsoleChannel",
                    "config": {"host": "${TEST_HOST_VALUE:default}"},
                    "decorators": [],
                }
            }
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        # Set environment variable
        os.environ["TEST_HOST_VALUE"] = "prod.example.com"

        try:
            settings = Settings(config_path=str(self.config_file))
            self.assertEqual(
                settings.get("channels.test.config.host"), "prod.example.com"
            )
        finally:
            del os.environ["TEST_HOST_VALUE"]

    def test_missing_required_env_var(self):
        """Should raise error if required env var is missing."""
        config = {
            "channels": {
                "test": {
                    "type": "ConsoleChannel",
                    "config": {"api_key": "${REQUIRED_API_KEY}"},  # No default
                    "decorators": [],
                }
            }
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        with self.assertRaises(ConfigurationError) as ctx:
            Settings(config_path=str(self.config_file))

        self.assertIn("REQUIRED_API_KEY", str(ctx.exception))

    def test_invalid_yaml(self):
        """Should raise error for invalid YAML."""
        with open(self.config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with self.assertRaises(ConfigurationError):
            Settings(config_path=str(self.config_file))

    def test_missing_channels_key(self):
        """Should raise error if 'channels' key is missing."""
        config = {"other": "data"}

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        with self.assertRaises(ConfigurationError) as ctx:
            Settings(config_path=str(self.config_file))

        self.assertIn("channels", str(ctx.exception))

    def test_get_channel_config(self):
        """Should get specific channel configuration."""
        config = {
            "channels": {
                "email": {
                    "type": "EmailChannel",
                    "config": {"smtp_host": "smtp.test.com"},
                    "decorators": [],
                }
            }
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        settings = Settings(config_path=str(self.config_file))
        channel_config = settings.get_channel_config("email")

        self.assertEqual(channel_config["type"], "EmailChannel")
        self.assertEqual(channel_config["config"]["smtp_host"], "smtp.test.com")

    def test_from_dict(self):
        """Should create Settings from dictionary."""
        config_dict = {
            "channels": {
                "console": {"type": "ConsoleChannel", "config": {}, "decorators": []}
            }
        }

        settings = Settings.from_dict(config_dict)

        self.assertEqual(settings.config, config_dict)
        self.assertEqual(settings.get("channels.console.type"), "ConsoleChannel")


class TestDecoratorFactory(unittest.TestCase):
    """Test DecoratorFactory."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = DecoratorFactory()
        self.base_channel = ConsoleChannel(config={"format": "json"})

    def test_list_builtin_decorators(self):
        """Should list built-in decorators."""
        decorators = self.factory.list_decorators()

        self.assertIn("retry", decorators)
        self.assertIn("logging", decorators)
        self.assertIn("rate_limit", decorators)

    def test_create_retry_decorator(self):
        """Should create retry decorator."""
        decorator = self.factory.create(
            "retry", self.base_channel, {"max_retries": 5, "initial_delay": 2.0}
        )

        self.assertIsInstance(decorator, RetryDecorator)
        self.assertEqual(decorator.max_retries, 5)
        self.assertEqual(decorator.initial_delay, 2.0)

    def test_create_unknown_decorator(self):
        """Should raise error for unknown decorator type."""
        with self.assertRaises(ValueError) as ctx:
            self.factory.create("unknown", self.base_channel, {})

        self.assertIn("Unknown decorator type", str(ctx.exception))

    def test_apply_multiple_decorators(self):
        """Should apply decorators in correct order."""
        configs = [
            {"type": "retry", "max_retries": 3},
            {"type": "logging", "log_level": "INFO"},
        ]

        decorated = self.factory.apply_decorators(self.base_channel, configs)

        # Should be: Logging(Retry(Console))
        self.assertIsInstance(decorated, LoggingDecorator)
        self.assertIsInstance(decorated.wrapped, RetryDecorator)

    def test_register_custom_decorator(self):
        """Should register custom decorator."""

        class CustomDecorator:
            def __init__(self, wrapped, custom_param="default"):
                self.wrapped = wrapped
                self.custom_param = custom_param

        self.factory.register("custom", CustomDecorator)

        self.assertIn("custom", self.factory.list_decorators())

        decorator = self.factory.create(
            "custom", self.base_channel, {"custom_param": "test"}
        )

        self.assertIsInstance(decorator, CustomDecorator)
        self.assertEqual(decorator.custom_param, "test")


class TestChannelFactory(unittest.TestCase):
    """Test ChannelFactory."""

    def setUp(self):
        """Set up test fixtures."""
        # Create settings from dict (no file needed)
        config_dict = {
            "channels": {
                "console": {
                    "type": "ConsoleChannel",
                    "enabled": True,
                    "config": {"format": "pretty"},
                    "decorators": [{"type": "logging", "log_level": "INFO"}],
                },
                "disabled": {
                    "type": "ConsoleChannel",
                    "enabled": False,
                    "config": {},
                    "decorators": [],
                },
            }
        }

        settings = Settings.from_dict(config_dict)
        self.factory = ChannelFactory(settings=settings)

    def test_list_builtin_channels(self):
        """Should list built-in channel types."""
        types = self.factory.list_channel_types()

        self.assertIn("ConsoleChannel", types)
        self.assertIn("EmailChannel", types)
        self.assertIn("WebhookChannel", types)

    def test_list_enabled_channels(self):
        """Should list only enabled channels from config."""
        channels = self.factory.list_channels()

        self.assertIn("console", channels)
        self.assertNotIn("disabled", channels)

    def test_create_channel_from_config(self):
        """Should create channel with decorators from config."""
        channel = self.factory.create("console")

        # Should be decorated with logging
        self.assertIsInstance(channel, LoggingDecorator)
        self.assertIsInstance(channel.wrapped, ConsoleChannel)

    def test_create_disabled_channel(self):
        """Should raise error when creating disabled channel."""
        with self.assertRaises(ConfigurationError) as ctx:
            self.factory.create("disabled")

        self.assertIn("disabled", str(ctx.exception))

    def test_create_unknown_channel(self):
        """Should raise error for unknown channel name."""
        with self.assertRaises(ConfigurationError) as ctx:
            self.factory.create("nonexistent")

        self.assertIn("not found", str(ctx.exception))

    def test_create_with_override_config(self):
        """Should merge override config with base config."""
        channel = self.factory.create("console", format="json")

        # Override should be applied
        self.assertEqual(channel.wrapped.config["format"], "json")

    def test_create_from_config_programmatic(self):
        """Should create channel programmatically without Settings."""
        channel = self.factory.create_from_config(
            "ConsoleChannel", {"format": "json"}, [{"type": "retry", "max_retries": 2}]
        )

        # Should be decorated
        self.assertIsInstance(channel, RetryDecorator)
        self.assertIsInstance(channel.wrapped, ConsoleChannel)

    def test_register_custom_channel(self):
        """Should register custom channel class."""

        class CustomChannel(ConsoleChannel):
            pass

        self.factory.register("CustomChannel", CustomChannel)

        self.assertIn("CustomChannel", self.factory.list_channel_types())


if __name__ == "__main__":
    unittest.main(verbosity=2)
