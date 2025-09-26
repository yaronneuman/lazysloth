"""
Integration tests for the FastParrot CLI.
"""

import pytest
import os
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from fastparrot.cli import main, install, uninstall, collect, monitor, status, add


@pytest.mark.integration
class TestCLI:
    """Test the CLI commands with realistic scenarios."""

    def test_main_command_help(self):
        """Test that main command shows help."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'FastParrot: Learn and share terminal shortcuts and aliases' in result.output

    def test_main_command_version(self):
        """Test that version flag works."""
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])

        assert result.exit_code == 0
        # Version should be displayed

    @patch('fastparrot.cli.Installer')
    def test_install_command_auto_detect(self, mock_installer_class):
        """Test install command with auto-detected shell."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = 'zsh'
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install)

        assert result.exit_code == 0
        assert 'Detected shell: zsh' in result.output
        assert '✅ FastParrot installed for zsh' in result.output
        mock_installer.install.assert_called_once_with('zsh', force=False)

    @patch('fastparrot.cli.Installer')
    def test_install_command_specified_shell(self, mock_installer_class):
        """Test install command with specified shell."""
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install, ['--shell', 'bash'])

        assert result.exit_code == 0
        assert '✅ FastParrot installed for bash' in result.output
        mock_installer.install.assert_called_once_with('bash', force=False)

    @patch('fastparrot.cli.Installer')
    def test_install_command_force_flag(self, mock_installer_class):
        """Test install command with force flag."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = 'bash'
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install, ['--force'])

        assert result.exit_code == 0
        mock_installer.install.assert_called_once_with('bash', force=True)

    @patch('fastparrot.cli.Installer')
    def test_install_command_failure(self, mock_installer_class):
        """Test install command when installation fails."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = 'bash'
        mock_installer.install.side_effect = Exception("Installation failed")
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install)

        assert result.exit_code == 1
        assert '❌ Installation failed: Installation failed' in result.output

    @patch('fastparrot.cli.Installer')
    def test_uninstall_command(self, mock_installer_class):
        """Test uninstall command."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = 'zsh'
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(uninstall)

        assert result.exit_code == 0
        assert 'Detected shell: zsh' in result.output
        assert '✅ FastParrot uninstalled from zsh' in result.output
        mock_installer.uninstall.assert_called_once_with('zsh')

    @patch('fastparrot.cli.Installer')
    def test_uninstall_command_failure(self, mock_installer_class):
        """Test uninstall command when uninstallation fails."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = 'bash'
        mock_installer.uninstall.side_effect = Exception("Uninstall failed")
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(uninstall)

        assert result.exit_code == 1
        assert '❌ Uninstallation failed: Uninstall failed' in result.output

    @patch('fastparrot.cli.AliasCollector')
    def test_collect_command_success(self, mock_collector_class):
        """Test collect command successful execution."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = {
            'gs': {'command': 'git status'},
            'll': {'command': 'ls -la'},
            'dps': {'command': 'docker ps'}
        }
        mock_collector_class.return_value = mock_collector

        runner = CliRunner()
        result = runner.invoke(collect)

        assert result.exit_code == 0
        assert 'Found 3 aliases:' in result.output
        assert 'gs: git status' in result.output
        assert 'll: ls -la' in result.output
        assert 'dps: docker ps' in result.output

    @patch('fastparrot.cli.AliasCollector')
    def test_collect_command_failure(self, mock_collector_class):
        """Test collect command when collection fails."""
        mock_collector = MagicMock()
        mock_collector.collect_all.side_effect = Exception("Collection failed")
        mock_collector_class.return_value = mock_collector

        runner = CliRunner()
        result = runner.invoke(collect)

        assert result.exit_code == 1
        assert '❌ Collection failed: Collection failed' in result.output

    @patch('fastparrot.cli.Config')
    def test_monitor_command_enable(self, mock_config_class):
        """Test monitor command enabling monitoring."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ['--enabled=true'])

        assert result.exit_code == 0
        assert 'Command monitoring enabled' in result.output
        mock_config.set.assert_called_with('monitoring.enabled', True)

    @patch('fastparrot.cli.Config')
    def test_monitor_command_disable(self, mock_config_class):
        """Test monitor command disabling monitoring."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ['--enabled=false'])

        assert result.exit_code == 0
        assert 'Command monitoring disabled' in result.output
        mock_config.set.assert_called_with('monitoring.enabled', False)

    @patch('fastparrot.cli.Config')
    def test_monitor_command_thresholds(self, mock_config_class):
        """Test monitor command setting thresholds."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, [
            '--notice-threshold', '2',
            '--block-threshold', '5'
        ])

        assert result.exit_code == 0
        assert 'Notice threshold set to 2' in result.output
        assert 'Block threshold set to 5' in result.output

    @patch('fastparrot.cli.Config')
    def test_monitor_command_enable_blocking(self, mock_config_class):
        """Test monitor command enabling blocking with warning."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ['--action=block'])

        assert result.exit_code == 0
        assert 'Monitoring action set to: block' in result.output
        assert 'Warning: Commands will be blocked' in result.output

    @patch('fastparrot.cli.Config')
    def test_monitor_command_disable_blocking(self, mock_config_class):
        """Test monitor command disabling blocking."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ['--action=notice'])

        assert result.exit_code == 0
        assert 'Monitoring action set to: notice' in result.output

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.core.fastparrotrc.FastParrotRC')
    def test_add_command_success(self, mock_fastparrotrc_class, mock_config_class):
        """Test add command successful execution."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}  # No existing aliases
        mock_config_class.return_value = mock_config

        # Mock FastParrotRC
        mock_fastparrotrc = MagicMock()
        mock_fastparrotrc_class.return_value = mock_fastparrotrc

        runner = CliRunner()
        result = runner.invoke(add, ['gs', 'git status'])

        assert result.exit_code == 0
        assert '✅ Added alias: gs -> git status' in result.output
        assert 'Alias added to ~/.fastparrotrc' in result.output
        mock_config.save_aliases_data.assert_called_once()
        mock_fastparrotrc.add_alias.assert_called_once_with('gs', 'git status')

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.core.fastparrotrc.FastParrotRC')
    def test_add_command_with_complex_command(self, mock_fastparrotrc_class, mock_config_class):
        """Test add command with complex multi-word command."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}
        mock_config_class.return_value = mock_config

        # Mock FastParrotRC
        mock_fastparrotrc = MagicMock()
        mock_fastparrotrc_class.return_value = mock_fastparrotrc

        runner = CliRunner()
        result = runner.invoke(add, ['ll', 'ls -la --color=auto --human-readable'])

        assert result.exit_code == 0
        assert '✅ Added alias: ll -> ls -la --color=auto --human-readable' in result.output

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.core.fastparrotrc.FastParrotRC')
    def test_add_command_overwrite_existing(self, mock_fastparrotrc_class, mock_config_class):
        """Test add command when alias already exists."""
        # Mock config with existing alias
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            'gs': {'command': 'git status', 'shell': 'bash'}
        }
        mock_config_class.return_value = mock_config

        # Mock FastParrotRC
        mock_fastparrotrc = MagicMock()
        mock_fastparrotrc_class.return_value = mock_fastparrotrc

        runner = CliRunner()
        # Test overwriting with same command
        result = runner.invoke(add, ['gs', 'git status'])

        assert result.exit_code == 0
        assert '✅ Alias \'gs\' already exists with the same command' in result.output

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.core.fastparrotrc.FastParrotRC')
    def test_add_command_overwrite_different(self, mock_fastparrotrc_class, mock_config_class):
        """Test add command when alias exists with different command."""
        # Mock config with existing alias
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            'gs': {'command': 'git status', 'shell': 'bash'}
        }
        mock_config_class.return_value = mock_config

        # Mock FastParrotRC
        mock_fastparrotrc = MagicMock()
        mock_fastparrotrc_class.return_value = mock_fastparrotrc

        runner = CliRunner()
        # Test overwriting with different command - answer 'no'
        result = runner.invoke(add, ['gs', 'git show'], input='n\n')

        assert result.exit_code == 0
        assert 'already exists with command: git status' in result.output
        assert 'Operation cancelled' in result.output

    def test_add_command_empty_args(self):
        """Test add command with empty arguments."""
        runner = CliRunner()
        result = runner.invoke(add, ['', 'git status'])

        assert result.exit_code == 1
        assert '❌ Both alias name and command are required' in result.output

        result = runner.invoke(add, ['gs', ''])
        assert result.exit_code == 1
        assert '❌ Both alias name and command are required' in result.output

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.cli.AliasCollector')
    @patch('fastparrot.monitors.command_monitor.CommandMonitor')
    def test_status_command_full(self, mock_monitor_class, mock_collector_class, mock_config_class):
        """Test status command showing full status."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'version': '1.0.0',
            'monitoring.enabled': True,
            'monitoring.notice_threshold': 2,
            'monitoring.blocking_threshold': 5,
            'monitoring.blocking_enabled': True
        }.get(key, default)
        mock_config.config_dir = Path('/home/user/.config/fastparrot')
        mock_config_class.return_value = mock_config

        # Mock collector
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = {
            'gs': {'command': 'git status'},
            'll': {'command': 'ls -la'}
        }
        mock_collector_class.return_value = mock_collector

        # Mock command monitor
        mock_monitor = MagicMock()
        mock_monitor.get_command_stats.return_value = {
            'gs': {'count': 3},
            'll': {'count': 1}
        }
        mock_monitor_class.return_value = mock_monitor

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert 'FastParrot Status:' in result.output
        assert 'Version: 1.0.0' in result.output
        assert 'Monitoring enabled: True' in result.output
        assert 'Action: block' in result.output
        assert 'Notice threshold: 2' in result.output
        assert 'Block threshold: 5' in result.output
        assert 'Known aliases: 2' in result.output
        assert 'Tracked aliases: 2' in result.output

    @patch('fastparrot.cli.Config')
    @patch('fastparrot.cli.AliasCollector')
    @patch('fastparrot.monitors.command_monitor.CommandMonitor')
    def test_status_command_disabled_monitoring(self, mock_monitor_class, mock_collector_class, mock_config_class):
        """Test status command when monitoring is disabled."""
        # Mock config with monitoring disabled
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'version': '1.0.0',
            'monitoring.enabled': False,
            'monitoring.notice_threshold': 1,
            'monitoring.blocking_threshold': 3,
            'monitoring.blocking_enabled': False
        }.get(key, default)
        mock_config.config_dir = Path('/home/user/.config/fastparrot')
        mock_config_class.return_value = mock_config

        # Mock collector
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = {}
        mock_collector_class.return_value = mock_collector

        # Mock command monitor
        mock_monitor = MagicMock()
        mock_monitor.get_command_stats.return_value = {}
        mock_monitor_class.return_value = mock_monitor

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert 'Monitoring enabled: False' in result.output
        assert 'Action: none' in result.output
        assert 'Known aliases: 0' in result.output


@pytest.mark.integration
class TestCLIWithRealFiles:
    """Test CLI commands with real file operations (using temporary directories)."""

    def test_install_uninstall_integration(self):
        """Test full install and uninstall cycle with real files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('shutil.which', return_value='/usr/bin/python3'):
                    runner = CliRunner()

                    # Install FastParrot
                    result = runner.invoke(install, ['--shell', 'bash'])
                    assert result.exit_code == 0

                    # Verify bashrc was created and contains integration
                    bashrc = home_dir / '.bashrc'
                    assert bashrc.exists()
                    content = bashrc.read_text()
                    assert '# FastParrot integration' in content
                    assert 'fastparrot_preexec()' in content

                    # Uninstall FastParrot
                    result = runner.invoke(uninstall, ['--shell', 'bash'])
                    assert result.exit_code == 0

                    # Verify integration was removed
                    content = bashrc.read_text()
                    assert '# FastParrot integration' not in content
                    assert 'fastparrot_preexec()' not in content

    def test_collect_with_real_files(self):
        """Test collect command with real shell configuration files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)

            # Create realistic shell config files
            bashrc = home_dir / '.bashrc'
            bashrc.write_text("""
# Bash configuration
alias ll='ls -la'
alias gs='git status'
alias ..='cd ..'
""")

            zshrc = home_dir / '.zshrc'
            zshrc.write_text("""
# Zsh configuration
alias dps='docker ps'
alias gp='git push'
""")

            # Create fish config
            fish_config_dir = home_dir / '.config' / 'fish'
            fish_config_dir.mkdir(parents=True)
            fish_config = fish_config_dir / 'config.fish'
            fish_config.write_text("""
# Fish configuration
alias gc 'git commit'
""")

            with patch.object(Path, 'home', return_value=home_dir):
                runner = CliRunner()
                result = runner.invoke(collect)

                assert result.exit_code == 0
                # Should find aliases from all shell configs
                assert 'Found' in result.output
                assert 'aliases:' in result.output