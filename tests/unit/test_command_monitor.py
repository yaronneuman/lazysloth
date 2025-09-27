"""
Unit tests for the CommandMonitor class.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from lazysloth.monitors.command_monitor import CommandMonitor, MonitorAction, MonitorResult


@pytest.mark.unit
class TestCommandMonitor:
    """Test the CommandMonitor class functionality."""

    def test_init(self, isolated_config):
        """Test CommandMonitor initialization."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                mock_collector.return_value = MagicMock()

                monitor = CommandMonitor()
                assert monitor.config == isolated_config

    def test_record_command_disabled_monitoring(self, isolated_config):
        """Test that monitoring can be disabled."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': False
                }.get(key, default))

                monitor = CommandMonitor()
                result = monitor.record_command('git status')

                assert result is None

    def test_record_command_ignored_command(self, isolated_config):
        """Test that ignored commands are not monitored."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': ['git']
                }.get(key, default))

                monitor = CommandMonitor()
                result = monitor.record_command('git status')

                assert result is None

    def test_record_command_no_alias(self, isolated_config):
        """Test recording command that has no alias."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': []
                }.get(key, default))

                mock_collector_instance = MagicMock()
                mock_collector_instance.find_alias_for_command.return_value = None
                mock_collector.return_value = mock_collector_instance

                monitor = CommandMonitor()
                result = monitor.record_command('unknown_command')

                assert result is None

    def test_record_command_first_time(self, isolated_config, mock_datetime):
        """Test recording a command for the first time."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': [],
                    'monitoring.notice_threshold': 1,
                    'monitoring.blocking_threshold': 3,
                    'monitoring.blocking_enabled': False
                }.get(key, default))

                isolated_config.get_stats_data = MagicMock(return_value={})
                isolated_config.save_stats_data = MagicMock()

                mock_collector_instance = MagicMock()
                mock_collector_instance.find_alias_for_command.return_value = (
                    'gs', {'command': 'git status'}
                )
                mock_collector.return_value = mock_collector_instance

                monitor = CommandMonitor()
                result = monitor.record_command('git status')

                # Should suggest alias immediately (threshold = 1)
                assert result is not None
                assert result.is_notice()
                assert "'gs'" in result.message
                assert "git status" in result.message

    def test_record_command_blocking_threshold(self, isolated_config, mock_datetime):
        """Test command blocking when threshold is reached."""
        existing_stats = {
            'gs': {
                'count': 2,  # Will become 3 after this command
                'first_seen': '2024-01-01T10:00:00',
                'last_seen': '2024-01-01T11:00:00',
                'alias_command': 'git status'
            }
        }

        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': [],
                    'monitoring.notice_threshold': 1,
                    'monitoring.blocking_threshold': 3,
                    'monitoring.blocking_enabled': True
                }.get(key, default))

                isolated_config.get_stats_data = MagicMock(return_value=existing_stats)
                isolated_config.save_stats_data = MagicMock()

                mock_collector_instance = MagicMock()
                mock_collector_instance.find_alias_for_command.return_value = (
                    'gs', {'command': 'git status'}
                )
                mock_collector.return_value = mock_collector_instance

                monitor = CommandMonitor()
                result = monitor.record_command('git status')

                # Should block command
                assert result is not None
                assert result.is_blocking()
                assert "'gs'" in result.message

    def test_record_command_notice_threshold(self, isolated_config, mock_datetime):
        """Test command notice when between notice and blocking threshold."""
        existing_stats = {
            'gs': {
                'count': 1,  # Will become 2 after this command
                'first_seen': '2024-01-01T10:00:00',
                'last_seen': '2024-01-01T11:00:00',
                'alias_command': 'git status'
            }
        }

        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': [],
                    'monitoring.notice_threshold': 1,
                    'monitoring.blocking_threshold': 5,
                    'monitoring.blocking_enabled': False
                }.get(key, default))

                isolated_config.get_stats_data = MagicMock(return_value=existing_stats)
                isolated_config.save_stats_data = MagicMock()

                mock_collector_instance = MagicMock()
                mock_collector_instance.find_alias_for_command.return_value = (
                    'gs', {'command': 'git status'}
                )
                mock_collector.return_value = mock_collector_instance

                monitor = CommandMonitor()
                result = monitor.record_command('git status')

                # Should show notice
                assert result is not None
                assert result.is_notice()
                assert "'gs'" in result.message

    def test_generate_alias_suggestion_exact_match(self, isolated_config):
        """Test alias suggestion generation for exact match."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector'):
                mock_config.return_value = isolated_config

                monitor = CommandMonitor()
                alias_data = {'command': 'git status'}

                suggestion = monitor._generate_alias_suggestion('git status', 'gs', alias_data)
                assert suggestion == "'gs'"

    def test_generate_alias_suggestion_with_args(self, isolated_config):
        """Test alias suggestion generation for command with arguments."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector'):
                mock_config.return_value = isolated_config

                monitor = CommandMonitor()
                alias_data = {'command': 'git status'}

                suggestion = monitor._generate_alias_suggestion('git status --short', 'gs', alias_data)
                assert suggestion == "'gs --short'"

    def test_get_command_stats(self, isolated_config, command_stats_sample):
        """Test getting command statistics."""
        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector'):
                mock_config.return_value = isolated_config
                isolated_config.get_stats_data = MagicMock(return_value=command_stats_sample)

                monitor = CommandMonitor()
                stats = monitor.get_command_stats()

                assert stats == command_stats_sample

    def test_record_command_updates_stats(self, isolated_config, mock_datetime):
        """Test that recording a command properly updates statistics."""
        existing_stats = {
            'gs': {
                'count': 1,
                'first_seen': '2024-01-01T10:00:00',
                'last_seen': '2024-01-01T11:00:00',
                'alias_command': 'git status'
            }
        }

        with patch('lazysloth.monitors.command_monitor.Config') as mock_config:
            with patch('lazysloth.monitors.command_monitor.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitoring.enabled': True,
                    'monitoring.ignored_commands': [],
                    'monitoring.notice_threshold': 1,
                    'monitoring.blocking_threshold': 5,
                    'monitoring.blocking_enabled': False
                }.get(key, default))

                isolated_config.get_stats_data = MagicMock(return_value=existing_stats)
                isolated_config.save_stats_data = MagicMock()

                mock_collector_instance = MagicMock()
                mock_collector_instance.find_alias_for_command.return_value = (
                    'gs', {'command': 'git status'}
                )
                mock_collector.return_value = mock_collector_instance

                monitor = CommandMonitor()
                monitor.record_command('git status')

                # Verify save_stats_data was called
                isolated_config.save_stats_data.assert_called_once()

                # Get the stats that were saved
                saved_stats = isolated_config.save_stats_data.call_args[0][0]

                # Verify the stats were updated correctly
                assert saved_stats['gs']['count'] == 2  # Incremented from 1
                assert saved_stats['gs']['last_seen'] == '2024-01-01T12:00:00'  # Updated time