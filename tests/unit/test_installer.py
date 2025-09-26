"""
Unit tests for the Installer class.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from fastparrot.core.installer import Installer


@pytest.mark.unit
class TestInstaller:
    """Test the Installer class functionality."""

    def test_init(self):
        """Test Installer initialization."""
        installer = Installer()
        assert installer.package_dir.exists()

    def test_detect_shell_from_env(self):
        """Test shell detection from environment variable."""
        installer = Installer()

        # Test bash
        with patch.dict(os.environ, {'SHELL': '/bin/bash'}):
            assert installer.detect_shell() == 'bash'

        # Test zsh
        with patch.dict(os.environ, {'SHELL': '/usr/bin/zsh'}):
            assert installer.detect_shell() == 'zsh'

        # Test fish
        with patch.dict(os.environ, {'SHELL': '/usr/local/bin/fish'}):
            assert installer.detect_shell() == 'fish'

        # Test unknown shell defaults to bash
        with patch.dict(os.environ, {'SHELL': '/bin/unknownshell'}):
            assert installer.detect_shell() == 'bash'

    def test_detect_shell_no_env(self):
        """Test shell detection when SHELL env var is not set."""
        installer = Installer()

        with patch.dict(os.environ, {}, clear=True):
            # Should default to bash when SHELL is not set
            assert installer.detect_shell() == 'bash'

    def test_get_shell_config_files(self, mock_home_dir):
        """Test getting configuration files for different shells."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Test bash config files
            bash_files = installer.get_shell_config_files('bash')
            expected_bash = [
                mock_home_dir / '.bashrc',
                mock_home_dir / '.bash_profile',
                mock_home_dir / '.profile'
            ]
            assert bash_files == expected_bash

            # Test zsh config files
            zsh_files = installer.get_shell_config_files('zsh')
            expected_zsh = [
                mock_home_dir / '.zshrc',
                mock_home_dir / '.zsh_profile',
                mock_home_dir / '.profile'
            ]
            assert zsh_files == expected_zsh

            # Test fish config files
            fish_files = installer.get_shell_config_files('fish')
            expected_fish = [
                mock_home_dir / '.config' / 'fish' / 'config.fish'
            ]
            assert fish_files == expected_fish

            # Test unknown shell
            unknown_files = installer.get_shell_config_files('unknown')
            assert unknown_files == []

    def test_find_existing_config(self, mock_home_dir):
        """Test finding existing shell configuration file."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create .bashrc
            bashrc = mock_home_dir / '.bashrc'
            bashrc.touch()

            # Should find existing .bashrc
            config_file = installer.find_existing_config('bash')
            assert config_file == bashrc

            # Test when no config exists, should return first option
            config_file = installer.find_existing_config('zsh')
            assert config_file == mock_home_dir / '.zshrc'

    def test_generate_integration_code_bash(self, mock_shutil_which):
        """Test generating bash integration code."""
        installer = Installer()

        code = installer._generate_integration_code('bash')

        assert 'fastparrot_preexec()' in code
        assert 'trap \'fastparrot_preexec\' DEBUG' in code
        assert '/usr/bin/python3 -m fastparrot.monitors.hook' in code

    def test_generate_integration_code_zsh(self, mock_shutil_which):
        """Test generating zsh integration code."""
        installer = Installer()

        code = installer._generate_integration_code('zsh')

        assert 'fastparrot_widget()' in code
        assert 'zle -N fastparrot_widget' in code
        assert 'bindkey "^M" fastparrot_widget' in code
        assert '/usr/bin/python3 -m fastparrot.monitors.hook' in code

    def test_generate_integration_code_fish(self, mock_shutil_which):
        """Test generating fish integration code."""
        installer = Installer()

        code = installer._generate_integration_code('fish')

        assert 'function fastparrot_preexec --on-event fish_preexec' in code
        assert '/usr/bin/python3 -m fastparrot.monitors.hook' in code

    def test_generate_integration_code_unsupported_shell(self):
        """Test generating integration code for unsupported shell."""
        installer = Installer()

        with pytest.raises(ValueError, match="Unsupported shell: unknown"):
            installer._generate_integration_code('unknown')

    def test_install_new_config_file(self, mock_home_dir, mock_shutil_which):
        """Test installing FastParrot to a new configuration file."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Install to bash (no existing config)
            installer.install('bash')

            # Verify config file was created
            bashrc = mock_home_dir / '.bashrc'
            assert bashrc.exists()

            # Verify integration was added
            content = bashrc.read_text()
            assert '# FastParrot integration' in content
            assert 'fastparrot_preexec()' in content
            assert '# End FastParrot integration' in content

    def test_install_existing_config_file(self, mock_home_dir, mock_shutil_which):
        """Test installing FastParrot to an existing configuration file."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create existing bashrc
            bashrc = mock_home_dir / '.bashrc'
            original_content = "# Existing config\nexport PATH=$HOME/bin:$PATH\n"
            bashrc.write_text(original_content)

            # Install FastParrot
            installer.install('bash')

            # Verify original content is preserved and integration is added
            content = bashrc.read_text()
            assert original_content in content
            assert '# FastParrot integration' in content
            assert 'fastparrot_preexec()' in content

    def test_install_already_installed_no_force(self, mock_home_dir, mock_shutil_which):
        """Test installing when already installed without force flag."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with existing integration
            bashrc = mock_home_dir / '.bashrc'
            bashrc.write_text("# FastParrot integration\necho 'already installed'\n")

            # Should raise error when trying to install again
            with pytest.raises(ValueError, match="FastParrot is already installed"):
                installer.install('bash')

    def test_install_already_installed_with_force(self, mock_home_dir, mock_shutil_which):
        """Test installing when already installed with force flag."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with existing integration
            bashrc = mock_home_dir / '.bashrc'
            old_integration = """# FastParrot integration
old integration code
# End FastParrot integration"""
            bashrc.write_text(old_integration)

            # Mock uninstall method
            installer.uninstall = MagicMock()

            # Should not raise error with force flag
            installer.install('bash', force=True)

            # Verify uninstall was called first
            installer.uninstall.assert_called_once_with('bash')

    def test_install_no_config_file_found(self):
        """Test installing when no configuration file path can be determined."""
        installer = Installer()

        # Mock find_existing_config to return None
        installer.find_existing_config = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="No configuration file found for shell"):
            installer.install('bash')

    def test_uninstall_removes_integration(self, mock_home_dir):
        """Test uninstalling FastParrot removes integration code."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with FastParrot integration
            bashrc = mock_home_dir / '.bashrc'
            content_with_integration = """# Original content
export PATH=$HOME/bin:$PATH

# FastParrot integration
fastparrot_preexec() {
    echo "FastParrot hook"
}
# End FastParrot integration

# More original content
alias ll='ls -la'
"""
            bashrc.write_text(content_with_integration)

            # Uninstall FastParrot
            installer.uninstall('bash')

            # Verify integration was removed but original content remains
            content = bashrc.read_text()
            assert '# FastParrot integration' not in content
            assert 'fastparrot_preexec' not in content
            assert '# End FastParrot integration' not in content
            assert 'export PATH=$HOME/bin:$PATH' in content
            assert "alias ll='ls -la'" in content

    def test_uninstall_no_config_file(self, mock_home_dir):
        """Test uninstalling when no config file exists."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Should not raise error when config file doesn't exist
            installer.uninstall('bash')  # Should complete without error

    def test_uninstall_multiple_integrations(self, mock_home_dir):
        """Test uninstalling removes multiple FastParrot integration blocks."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with multiple integration blocks
            bashrc = mock_home_dir / '.bashrc'
            content_with_multiple = """# Original content

# FastParrot integration
old integration 1
# End FastParrot integration

# Some other content

# FastParrot integration
old integration 2
# End FastParrot integration

# More content
"""
            bashrc.write_text(content_with_multiple)

            # Uninstall FastParrot
            installer.uninstall('bash')

            # Verify all integration blocks were removed
            content = bashrc.read_text()
            assert '# FastParrot integration' not in content
            assert 'old integration 1' not in content
            assert 'old integration 2' not in content
            assert '# End FastParrot integration' not in content