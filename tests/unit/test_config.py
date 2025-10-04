"""
Unit tests for the Config class.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from lazysloth.core.config import Config


@pytest.mark.unit
class TestConfig:
    """Test the Config class functionality."""

    def test_init_creates_config_dir(self, tmp_path):
        """Test that Config initialization creates the config directory."""
        config_dir = tmp_path / "test_config"

        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Config, "__init__", lambda self: None):
                config = Config()
                config.config_dir = config_dir
                config.config_file = config_dir / "config.yaml"
                config.aliases_file = config_dir / "aliases.yaml"
                config.stats_file = config_dir / "stats.yaml"
                config._ensure_config_dir()

        assert config_dir.exists()

    def test_default_config(self, isolated_config):
        """Test that default configuration is properly set."""
        config = isolated_config

        assert config.get("version") == "1.0.0"
        assert config.get("monitoring.enabled") is True
        assert config.get("monitoring.notice_threshold") == 1
        assert config.get("monitoring.blocking_threshold") == 5
        assert config.get("monitoring.blocking_enabled") is True
        assert config.get("monitoring.ignored_commands") == []

    def test_get_with_dot_notation(self, isolated_config):
        """Test getting configuration values with dot notation."""
        config = isolated_config

        # Test existing keys
        assert config.get("monitoring.enabled") is True
        assert config.get("monitoring.notice_threshold") == 1

        # Test non-existing keys with default
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("monitoring.nonexistent", "default") == "default"

    def test_set_with_dot_notation(self, isolated_config):
        """Test setting configuration values with dot notation."""
        config = isolated_config

        # Set existing key
        config.set("monitoring.enabled", False)
        assert config.get("monitoring.enabled") is False

        # Set new nested key
        config.set("new.nested.key", "value")
        assert config.get("new.nested.key") == "value"

    def test_save_and_load_config(self, isolated_config):
        """Test saving and loading configuration."""
        config = isolated_config

        # Modify config
        config.set("monitoring.enabled", False)
        config.set("test.key", "test_value")

        # Save config
        config.save()

        # Verify file was created
        assert config.config_file.exists()

        # Read and verify content
        with open(config.config_file, "r") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["monitoring"]["enabled"] is False
        assert saved_config["test"]["key"] == "test_value"

    def test_aliases_data_operations(self, isolated_config, sample_aliases):
        """Test saving and loading aliases data."""
        config = isolated_config

        # Save aliases data
        config.save_aliases_data(sample_aliases)

        # Verify file was created
        assert config.aliases_file.exists()

        # Load and verify data
        loaded_aliases = config.get_aliases_data()
        assert loaded_aliases == sample_aliases

    def test_stats_data_operations(self, isolated_config, command_stats_sample):
        """Test saving and loading statistics data."""
        config = isolated_config

        # Save stats data
        config.save_stats_data(command_stats_sample)

        # Verify file was created
        assert config.stats_file.exists()

        # Load and verify data
        loaded_stats = config.get_stats_data()
        assert loaded_stats == command_stats_sample

    def test_get_empty_data_files(self, isolated_config):
        """Test getting data from non-existent files returns empty dict."""
        config = isolated_config

        # Files don't exist yet
        assert config.get_aliases_data() == {}
        assert config.get_stats_data() == {}

    def test_load_config_from_existing_file(self, tmp_path):
        """Test loading configuration from an existing file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"

        # Create existing config file
        existing_config = {
            "version": "2.0.0",
            "monitoring": {"enabled": False, "notice_threshold": 5},
            "custom_key": "custom_value",
        }

        with open(config_file, "w") as f:
            yaml.dump(existing_config, f)

        # Initialize Config with existing file
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Config, "__init__", lambda self: None):
                config = Config()
                config.config_dir = config_dir
                config.config_file = config_file
                config.aliases_file = config_dir / "aliases.yaml"
                config.stats_file = config_dir / "stats.yaml"
                config._config = config._load_config()

        # Verify loaded values
        assert config.get("version") == "2.0.0"
        assert config.get("monitoring.enabled") is False
        assert config.get("monitoring.notice_threshold") == 5
        assert config.get("custom_key") == "custom_value"

    def test_load_config_with_empty_file(self, tmp_path):
        """Test loading configuration from an empty file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"

        # Create empty config file
        config_file.write_text("")

        # Initialize Config with empty file - the actual _load_config should handle empty files
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Config, "__init__", lambda self: None):
                config = Config()
                config.config_dir = config_dir
                config.config_file = config_file
                config.aliases_file = config_dir / "aliases.yaml"
                config.stats_file = config_dir / "stats.yaml"

                # Test that _load_config handles empty files correctly
                loaded_config = config._load_config()
                assert (
                    loaded_config == {}
                )  # Empty file should return empty dict due to `or {}`

                # Now test with default config fallback
                config._config = config._default_config()

        # Should have default config
        assert config.get("version") == "1.0.0"
        assert config.get("monitoring.enabled") is True
