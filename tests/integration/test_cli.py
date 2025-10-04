"""
Integration tests for the LazySloth CLI.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lazysloth.cli import alias, install, main, monitor, status, uninstall


@pytest.mark.integration
class TestCLI:
    """Test the CLI commands with realistic scenarios."""

    def test_main_command_help(self):
        """Test that main command shows help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert (
            "LazySloth: Learn and share terminal shortcuts and aliases" in result.output
        )

    def test_main_command_version(self):
        """Test that version flag works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # Version should be displayed

    @patch("lazysloth.cli.Installer")
    def test_install_command_auto_detect(self, mock_installer_class):
        """Test install command with auto-detected shell."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = "zsh"
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install)

        assert result.exit_code == 0
        assert "Detected shell: zsh" in result.output
        assert "✅ LazySloth installed for zsh" in result.output
        mock_installer.install.assert_called_once_with("zsh", force=False)

    @patch("lazysloth.cli.Installer")
    def test_install_command_specified_shell(self, mock_installer_class):
        """Test install command with specified shell."""
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install, ["--shell", "bash"])

        assert result.exit_code == 0
        assert "✅ LazySloth installed for bash" in result.output
        mock_installer.install.assert_called_once_with("bash", force=False)

    @patch("lazysloth.cli.Installer")
    def test_install_command_force_flag(self, mock_installer_class):
        """Test install command with force flag."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = "bash"
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install, ["--force"])

        assert result.exit_code == 0
        mock_installer.install.assert_called_once_with("bash", force=True)

    @patch("lazysloth.cli.Installer")
    def test_install_command_failure(self, mock_installer_class):
        """Test install command when installation fails."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = "bash"
        mock_installer.install.side_effect = Exception("Installation failed")
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(install)

        assert result.exit_code == 1
        assert "❌ Installation failed: Installation failed" in result.output

    @patch("lazysloth.cli.Installer")
    def test_uninstall_command(self, mock_installer_class):
        """Test uninstall command."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = "zsh"
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(uninstall)

        assert result.exit_code == 0
        assert "Detected shell: zsh" in result.output
        assert "✅ LazySloth uninstalled from zsh" in result.output
        mock_installer.uninstall.assert_called_once_with("zsh")

    @patch("lazysloth.cli.Installer")
    def test_uninstall_command_failure(self, mock_installer_class):
        """Test uninstall command when uninstallation fails."""
        mock_installer = MagicMock()
        mock_installer.detect_shell.return_value = "bash"
        mock_installer.uninstall.side_effect = Exception("Uninstall failed")
        mock_installer_class.return_value = mock_installer

        runner = CliRunner()
        result = runner.invoke(uninstall)

        assert result.exit_code == 1
        assert "❌ Uninstallation failed: Uninstall failed" in result.output

    @patch("lazysloth.cli.Config")
    def test_monitor_config_command_enable(self, mock_config_class):
        """Test monitor config command enabling monitoring."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ["config", "--enabled=true"])

        assert result.exit_code == 0
        assert "Command monitoring enabled" in result.output
        mock_config.set.assert_called_with("monitoring.enabled", True)

    @patch("lazysloth.cli.Config")
    def test_monitor_config_command_disable(self, mock_config_class):
        """Test monitor config command disabling monitoring."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ["config", "--enabled=false"])

        assert result.exit_code == 0
        assert "Command monitoring disabled" in result.output
        mock_config.set.assert_called_with("monitoring.enabled", False)

    @patch("lazysloth.cli.Config")
    def test_monitor_config_command_thresholds(self, mock_config_class):
        """Test monitor config command setting thresholds."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            monitor, ["config", "--notice-threshold", "2", "--block-threshold", "5"]
        )

        assert result.exit_code == 0
        assert "Notice threshold set to 2" in result.output
        assert "Block threshold set to 5" in result.output

    @patch("lazysloth.cli.Config")
    def test_monitor_config_command_enable_blocking(self, mock_config_class):
        """Test monitor config command enabling blocking with warning."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ["config", "--action=block"])

        assert result.exit_code == 0
        assert "Monitoring action set to: block" in result.output
        assert "Warning: Commands will be blocked" in result.output

    @patch("lazysloth.cli.Config")
    def test_monitor_config_command_disable_blocking(self, mock_config_class):
        """Test monitor config command disabling blocking."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(monitor, ["config", "--action=notice"])

        assert result.exit_code == 0
        assert "Monitoring action set to: notice" in result.output

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_add_success(self, mock_slothrc_class, mock_config_class):
        """Test alias add command successful execution."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}  # No existing aliases
        mock_config_class.return_value = mock_config

        # Mock SlothRC
        mock_slothrc = MagicMock()
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        result = runner.invoke(alias, ["add", "gs", "git status"])

        assert result.exit_code == 0
        assert "✅ Added alias: gs -> git status" in result.output
        assert "Alias added to ~/.slothrc" in result.output
        mock_config.save_aliases_data.assert_called_once()
        mock_slothrc.add_alias.assert_called_once_with("gs", "git status")

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_add_with_complex_command(
        self, mock_slothrc_class, mock_config_class
    ):
        """Test alias add command with complex multi-word command."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}
        mock_config_class.return_value = mock_config

        # Mock SlothRC
        mock_slothrc = MagicMock()
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        result = runner.invoke(
            alias, ["add", "ll", "ls -la --color=auto --human-readable"]
        )

        assert result.exit_code == 0
        assert (
            "✅ Added alias: ll -> ls -la --color=auto --human-readable"
            in result.output
        )

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_add_overwrite_existing(self, mock_slothrc_class, mock_config_class):
        """Test alias add command when alias already exists."""
        # Mock config with existing alias
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {"command": "git status", "shell": "bash"}
        }
        mock_config_class.return_value = mock_config

        # Mock SlothRC
        mock_slothrc = MagicMock()
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        # Test overwriting with same command
        result = runner.invoke(alias, ["add", "gs", "git status"])

        assert result.exit_code == 0
        assert "✅ Alias 'gs' already exists with the same command" in result.output

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_add_overwrite_different(self, mock_slothrc_class, mock_config_class):
        """Test alias add command when alias exists with different command."""
        # Mock config with existing alias
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {"command": "git status", "shell": "bash"}
        }
        mock_config_class.return_value = mock_config

        # Mock SlothRC
        mock_slothrc = MagicMock()
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        # Test overwriting with different command - answer 'no'
        result = runner.invoke(alias, ["add", "gs", "git show"], input="n\n")

        assert result.exit_code == 0
        assert "already exists with command: git status" in result.output
        assert "Operation cancelled" in result.output

    def test_alias_add_empty_args(self):
        """Test alias add command with empty arguments."""
        runner = CliRunner()
        result = runner.invoke(alias, ["add", "", "git status"])

        assert result.exit_code == 1
        assert "❌ Both alias name and command are required" in result.output

        result = runner.invoke(alias, ["add", "gs", ""])
        assert result.exit_code == 1
        assert "❌ Both alias name and command are required" in result.output

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.AutoLearner")
    @patch("lazysloth.monitors.command_monitor.CommandMonitor")
    def test_status_command_full(
        self, mock_monitor_class, mock_learner_class, mock_config_class
    ):
        """Test status command showing full status."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "version": "1.0.0",
            "monitoring.enabled": True,
            "monitoring.notice_threshold": 2,
            "monitoring.blocking_threshold": 5,
            "monitoring.blocking_enabled": True,
        }.get(key, default)
        mock_config.config_dir = Path("/home/user/.config/lazysloth")
        mock_config_class.return_value = mock_config

        # Mock learner
        mock_learner = MagicMock()
        mock_learner.get_monitored_files.return_value = {
            "bash": ["/home/user/.bash_profile"],
            "zsh": ["/home/user/.zshrc"],
        }
        mock_config.get_aliases_data.return_value = {
            "gs": {"command": "git status"},
            "ll": {"command": "ls -la"},
        }
        mock_learner_class.return_value = mock_learner

        # Mock command monitor
        mock_monitor = MagicMock()
        mock_monitor.get_command_stats.return_value = {
            "gs": {"count": 3},
            "ll": {"count": 1},
        }
        mock_monitor_class.return_value = mock_monitor

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "LazySloth Status:" in result.output
        assert "Version: 1.0.0" in result.output
        assert "Monitoring enabled: True" in result.output
        assert "Action: block" in result.output
        assert "Notice threshold: 2" in result.output
        assert "Block threshold: 5" in result.output
        assert "Known aliases: 2" in result.output
        assert "Monitored files: 2" in result.output
        assert "Tracked aliases: 2" in result.output

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.AutoLearner")
    @patch("lazysloth.monitors.command_monitor.CommandMonitor")
    def test_status_command_disabled_monitoring(
        self, mock_monitor_class, mock_learner_class, mock_config_class
    ):
        """Test status command when monitoring is disabled."""
        # Mock config with monitoring disabled
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "version": "1.0.0",
            "monitoring.enabled": False,
            "monitoring.notice_threshold": 1,
            "monitoring.blocking_threshold": 3,
            "monitoring.blocking_enabled": False,
        }.get(key, default)
        mock_config.config_dir = Path("/home/user/.config/lazysloth")
        mock_config_class.return_value = mock_config

        # Mock learner
        mock_learner = MagicMock()
        mock_learner.get_monitored_files.return_value = {}
        mock_config.get_aliases_data.return_value = {}
        mock_learner_class.return_value = mock_learner

        # Mock command monitor
        mock_monitor = MagicMock()
        mock_monitor.get_command_stats.return_value = {}
        mock_monitor_class.return_value = mock_monitor

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "Monitoring enabled: False" in result.output
        assert "Action: none" in result.output
        assert "Known aliases: 0" in result.output
        assert "Monitored files: 0" in result.output

    @patch("lazysloth.cli.Config")
    def test_alias_list_with_aliases(self, mock_config_class):
        """Test alias list command with existing aliases."""
        # Mock config with multiple aliases from different sources
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {
                "command": "git status",
                "shell": "bash",
                "source_file": ".bash_profile",
            },
            "ll": {"command": "ls -la", "shell": "zsh", "source_file": ".zshrc"},
            "gc": {
                "command": "git commit",
                "shell": "user_defined",
                "source_file": ".slothrc",
            },
            "gp": {
                "command": "git push",
                "shell": "bash",
                "source_file": ".bash_aliases",
            },
        }
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["list"])

        assert result.exit_code == 0
        assert ".bash_profile:" in result.output
        assert ".zshrc:" in result.output
        assert ".slothrc:" in result.output
        assert ".bash_aliases:" in result.output
        assert "gs → git status (bash)" in result.output
        assert "ll → ls -la (zsh)" in result.output
        assert "gc → git commit (user_defined)" in result.output
        assert "gp → git push (bash)" in result.output

    @patch("lazysloth.cli.Config")
    def test_alias_list_empty(self, mock_config_class):
        """Test alias list command when no aliases exist."""
        # Mock config with no aliases
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["list"])

        assert result.exit_code == 0
        assert "No aliases found." in result.output

    @patch("lazysloth.cli.Config")
    def test_alias_list_failure(self, mock_config_class):
        """Test alias list command when config fails to load."""
        # Mock config that raises an exception
        mock_config = MagicMock()
        mock_config.get_aliases_data.side_effect = Exception("Config error")
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["list"])

        assert result.exit_code == 1
        assert "❌ Failed to list aliases: Config error" in result.output

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_rm_success(self, mock_slothrc_class, mock_config_class):
        """Test alias rm command successful removal."""
        # Mock config with alias from .slothrc
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {
                "command": "git status",
                "shell": "user_defined",
                "source_file": ".slothrc",
            }
        }
        mock_config_class.return_value = mock_config

        # Mock SlothRC successful removal
        mock_slothrc = MagicMock()
        mock_slothrc.remove_alias.return_value = True
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        result = runner.invoke(alias, ["rm", "gs"])

        assert result.exit_code == 0
        assert "✅ Removed alias: gs" in result.output
        assert "Alias removed from ~/.slothrc" in result.output
        mock_slothrc.remove_alias.assert_called_once_with("gs")
        mock_config.save_aliases_data.assert_called_once()

    @patch("lazysloth.cli.Config")
    def test_alias_rm_not_found(self, mock_config_class):
        """Test alias rm command when alias doesn't exist."""
        # Mock config with no aliases
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {}
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["rm", "nonexistent"])

        assert result.exit_code == 1
        assert "❌ Alias 'nonexistent' not found" in result.output

    @patch("lazysloth.cli.Config")
    def test_alias_rm_readonly_source(self, mock_config_class):
        """Test alias rm command when alias is from read-only source."""
        # Mock config with alias from .bash_profile (read-only)
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {
                "command": "git status",
                "shell": "bash",
                "source_file": ".bash_profile",
            }
        }
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["rm", "gs"])

        assert result.exit_code == 1
        assert "❌ Cannot remove alias 'gs' - it's from .bash_profile" in result.output
        assert (
            "Only aliases added via 'sloth alias add' can be removed" in result.output
        )

    @patch("lazysloth.cli.Config")
    @patch("lazysloth.cli.SlothRC")
    def test_alias_rm_slothrc_not_found(self, mock_slothrc_class, mock_config_class):
        """Test alias rm command when alias exists in config but not in .slothrc file."""
        # Mock config with alias from .slothrc
        mock_config = MagicMock()
        mock_config.get_aliases_data.return_value = {
            "gs": {
                "command": "git status",
                "shell": "user_defined",
                "source_file": ".slothrc",
            }
        }
        mock_config_class.return_value = mock_config

        # Mock SlothRC failed removal (alias not found in file)
        mock_slothrc = MagicMock()
        mock_slothrc.remove_alias.return_value = False
        mock_slothrc_class.return_value = mock_slothrc

        runner = CliRunner()
        result = runner.invoke(alias, ["rm", "gs"])

        assert result.exit_code == 0  # Still returns 0 even if not found in file
        assert "❌ Alias 'gs' not found in ~/.slothrc" in result.output

    @patch("lazysloth.cli.Config")
    def test_alias_rm_failure(self, mock_config_class):
        """Test alias rm command when config fails to load."""
        # Mock config that raises an exception
        mock_config = MagicMock()
        mock_config.get_aliases_data.side_effect = Exception("Config error")
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(alias, ["rm", "gs"])

        assert result.exit_code == 1
        assert "❌ Failed to remove alias: Config error" in result.output

    def test_alias_rm_missing_argument(self):
        """Test alias rm command without alias name argument."""
        runner = CliRunner()
        result = runner.invoke(alias, ["rm"])

        assert result.exit_code == 2  # Click returns 2 for missing arguments
        assert "Missing argument" in result.output


@pytest.mark.integration
class TestCLIWithRealFiles:
    """Test CLI commands with real file operations (using temporary directories)."""

    def test_install_uninstall_integration(self):
        """Test full install and uninstall cycle with real files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)

            with patch.object(Path, "home", return_value=home_dir):
                with patch("shutil.which", return_value="/usr/bin/python3"):
                    runner = CliRunner()

                    # Install LazySloth
                    result = runner.invoke(install, ["--shell", "bash"])
                    assert result.exit_code == 0

                    # Verify bash_profile was created and contains integration
                    bash_profile = home_dir / ".bash_profile"
                    assert bash_profile.exists()
                    content = bash_profile.read_text()
                    assert "# LazySloth integration" in content
                    assert "lazysloth_preexec()" in content

                    # Uninstall LazySloth
                    result = runner.invoke(uninstall, ["--shell", "bash"])
                    assert result.exit_code == 0

                    # Verify integration was removed
                    content = bash_profile.read_text()
                    assert "# LazySloth integration" not in content
                    assert "lazysloth_preexec()" not in content
