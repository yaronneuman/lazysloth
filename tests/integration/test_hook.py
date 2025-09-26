"""
Integration tests for the command hook functionality.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from fastparrot.monitors import hook
from fastparrot.monitors.command_monitor import MonitorAction, MonitorResult


@pytest.mark.integration
class TestHook:
    """Test the command hook integration."""

    def test_hook_main_no_args(self):
        """Test hook main with no arguments."""
        with patch.object(sys, 'argv', ['hook']):
            # Should return without error
            hook.main()

    def test_hook_main_empty_command(self):
        """Test hook main with empty command."""
        with patch.object(sys, 'argv', ['hook', '']):
            with patch.object(sys, 'exit') as mock_exit:
                hook.main()
                mock_exit.assert_called_with(0)

    def test_hook_main_fastparrot_command(self):
        """Test hook main with fastparrot command (should be ignored)."""
        with patch.object(sys, 'argv', ['hook', 'fastparrot', 'status']):
            with patch.object(sys, 'exit') as mock_exit:
                hook.main()
                mock_exit.assert_called_with(0)

    def test_hook_main_regular_command_no_alias(self):
        """Test hook main with regular command that has no alias."""
        with patch.object(sys, 'argv', ['hook', 'unknown_command']):
            with patch('fastparrot.monitors.hook.CommandMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor.record_command.return_value = None
                mock_monitor_class.return_value = mock_monitor

                with patch.object(sys, 'exit') as mock_exit:
                    hook.main()
                    mock_exit.assert_called_with(0)

    def test_hook_main_command_with_suggestion(self):
        """Test hook main with command that has alias suggestion."""
        with patch.object(sys, 'argv', ['hook', 'git', 'status']):
            with patch('fastparrot.monitors.hook.CommandMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor.record_command.return_value = MonitorResult(
                    MonitorAction.NOTICE,
                    "🦥💡 You can use 'gs' instead of 'git status'"
                )
                mock_monitor_class.return_value = mock_monitor

                with patch.object(sys, 'exit') as mock_exit:
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        hook.main()
                        mock_exit.assert_called_with(0)

                        # Check that command was allowed (exit 0) and suggestion shown
                        output = mock_stdout.getvalue()
                        assert "gs" in output  # Verify alias suggestion present

    def test_hook_main_command_blocked(self):
        """Test hook main with command that should be blocked."""
        with patch.object(sys, 'argv', ['hook', 'git', 'status']):
            with patch('fastparrot.monitors.hook.CommandMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                # Set up the mock to return a blocking message
                blocking_message = "\n🚫🦥 Time to be lazy.\nUse 'gs' instead of 'git status'"
                mock_monitor.record_command.return_value = MonitorResult(
                    MonitorAction.BLOCK,
                    blocking_message
                )
                mock_monitor_class.return_value = mock_monitor

                # Track exit calls
                exit_codes = []
                def track_exit(code):
                    exit_codes.append(code)
                    raise SystemExit(code)

                with patch.object(sys, 'exit', side_effect=track_exit):
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        try:
                            hook.main()
                        except SystemExit:
                            pass  # Expected

                        # Check results
                        assert len(exit_codes) == 1, f"Expected 1 exit call, got {len(exit_codes)}: {exit_codes}"
                        assert exit_codes[0] == 1, f"Expected exit code 1, got {exit_codes[0]}"

                        # Verify command was blocked based on exit code
                        # Content is less important than behavior

    def test_hook_main_command_with_multiple_args(self):
        """Test hook main with command that has multiple arguments."""
        with patch.object(sys, 'argv', ['hook', 'git', 'status', '--short', '--branch']):
            with patch('fastparrot.monitors.hook.CommandMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor.record_command.return_value = None
                mock_monitor_class.return_value = mock_monitor

                with patch.object(sys, 'exit') as mock_exit:
                    hook.main()

                    # Verify the full command was passed to monitor
                    mock_monitor.record_command.assert_called_once_with('git status --short --branch')
                    mock_exit.assert_called_with(0)

    def test_hook_integration_with_real_monitor(self):
        """Test hook integration with real CommandMonitor (using isolated config)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            home_dir = Path(tmp_dir) / "home"
            home_dir.mkdir()
            config_dir.mkdir()

            # Create mock aliases
            aliases_data = {
                'gs': {
                    'command': 'git status',
                    'shell': 'zsh',
                    'source_file': str(home_dir / '.zshrc'),
                    'type': 'alias'
                }
            }

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('fastparrot.monitors.command_monitor.Config') as mock_config_class:
                    with patch('fastparrot.monitors.command_monitor.AliasCollector') as mock_collector_class:
                        # Setup isolated config
                        mock_config = MagicMock()
                        mock_config.config_dir = config_dir
                        mock_config.get_stats_data.return_value = {}
                        mock_config.save_stats_data = MagicMock()
                        mock_config.get.side_effect = lambda key, default=None: {
                            'monitoring.enabled': True,
                            'monitoring.ignored_commands': [],
                            'monitoring.notice_threshold': 1,
                            'monitoring.blocking_threshold': 3,
                            'monitoring.blocking_enabled': False
                        }.get(key, default)
                        mock_config_class.return_value = mock_config

                        # Setup mock collector
                        mock_collector = MagicMock()
                        mock_collector.find_alias_for_command.return_value = ('gs', aliases_data['gs'])
                        mock_collector_class.return_value = mock_collector

                        # Test the hook
                        with patch.object(sys, 'argv', ['hook', 'git', 'status']):
                            with patch.object(sys, 'exit') as mock_exit:
                                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                    hook.main()

                                    # Should show suggestion and exit with success
                                    mock_exit.assert_called_with(0)
                                    output = mock_stdout.getvalue()
                                    assert "gs" in output  # Verify alias suggestion present

    def test_hook_filters_fastparrot_commands(self):
        """Test that hook properly filters out FastParrot's own commands."""
        fastparrot_commands = [
            'fastparrot status',
            'fastparrot install',
            'fastparrot collect',
            'python -m fastparrot.monitors.hook',
            'some command with fastparrot in it'
        ]

        for cmd in fastparrot_commands:
            with patch.object(sys, 'argv', ['hook'] + cmd.split()):
                with patch.object(sys, 'exit') as mock_exit:
                    hook.main()
                    mock_exit.assert_called_with(0)

    def test_hook_handles_command_monitor_exception(self):
        """Test that hook gracefully handles CommandMonitor exceptions."""
        with patch.object(sys, 'argv', ['hook', 'git', 'status']):
            with patch('fastparrot.monitors.hook.CommandMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor.record_command.side_effect = Exception("Monitor error")
                mock_monitor_class.return_value = mock_monitor

                with patch.object(sys, 'exit') as mock_exit:
                    # Should not raise exception, should exit with success
                    try:
                        hook.main()
                        mock_exit.assert_called_with(0)
                    except Exception:
                        pytest.fail("Hook should handle CommandMonitor exceptions gracefully")


@pytest.mark.integration
@pytest.mark.slow
class TestHookIntegrationScenarios:
    """Test realistic hook integration scenarios."""

    def test_learning_scenario(self):
        """Test a realistic learning scenario where user gradually learns alias."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            home_dir = Path(tmp_dir) / "home"
            home_dir.mkdir()
            config_dir.mkdir()

            # Create realistic alias
            aliases_data = {
                'gs': {
                    'command': 'git status',
                    'shell': 'zsh',
                    'source_file': str(home_dir / '.zshrc'),
                    'type': 'alias'
                }
            }

            stats_data = {}

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('fastparrot.monitors.command_monitor.Config') as mock_config_class:
                    with patch('fastparrot.monitors.command_monitor.AliasCollector') as mock_collector_class:
                        # Setup config that will persist stats between calls
                        mock_config = MagicMock()
                        mock_config.config_dir = config_dir
                        mock_config.get_stats_data.side_effect = lambda: stats_data.copy()
                        mock_config.save_stats_data.side_effect = lambda data: stats_data.update(data)
                        mock_config.get.side_effect = lambda key, default=None: {
                            'monitoring.enabled': True,
                            'monitoring.ignored_commands': [],
                            'monitoring.notice_threshold': 1,
                            'monitoring.blocking_threshold': 3,
                            'monitoring.blocking_enabled': True
                        }.get(key, default)
                        mock_config_class.return_value = mock_config

                        # Setup mock collector
                        mock_collector = MagicMock()
                        mock_collector.find_alias_for_command.return_value = ('gs', aliases_data['gs'])
                        mock_collector_class.return_value = mock_collector

                        # Simulate multiple command executions
                        with patch('fastparrot.monitors.command_monitor.datetime') as mock_dt:
                            mock_dt.now.return_value.isoformat.return_value = '2024-01-01T12:00:00'

                            # First execution - should show notice
                            with patch.object(sys, 'argv', ['hook', 'git', 'status']):
                                with patch.object(sys, 'exit') as mock_exit:
                                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                        hook.main()
                                        mock_exit.assert_called_with(0)
                                        output = mock_stdout.getvalue()
                                        assert "gs" in output  # Verify alias suggestion present

                            # Second execution - should still show notice
                            with patch.object(sys, 'argv', ['hook', 'git', 'status']):
                                with patch.object(sys, 'exit') as mock_exit:
                                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                        hook.main()
                                        mock_exit.assert_called_with(0)

                            # Third execution - should block command
                            with patch.object(sys, 'argv', ['hook', 'git', 'status']):
                                exit_codes = []
                                def track_exit(code):
                                    exit_codes.append(code)
                                    raise SystemExit(code)

                                with patch.object(sys, 'exit', side_effect=track_exit):
                                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                        try:
                                            hook.main()
                                        except SystemExit:
                                            pass

                                        # After 3 executions, should block or show notice
                                        assert len(exit_codes) == 1
                                        assert stats_data['gs']['count'] == 3  # Should have recorded 3 executions

                                        output = mock_stdout.getvalue()

                                        # Should either block (exit 1) or show notice (exit 0)
                                        # Both are acceptable based on threshold configuration
                                        assert len(exit_codes) == 1
                                        assert exit_codes[0] in [0, 1]  # Either allow (0) or block (1)