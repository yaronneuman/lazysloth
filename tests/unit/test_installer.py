"""
Unit tests for the Installer class.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from lazysloth.core.installer import Installer


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

        assert 'lazysloth_preexec()' in code
        assert 'trap \'lazysloth_preexec\' DEBUG' in code
        assert '/usr/bin/python3 -m lazysloth.monitors.hook' in code

    def test_generate_integration_code_zsh(self, mock_shutil_which):
        """Test generating zsh integration code."""
        installer = Installer()

        code = installer._generate_integration_code('zsh')

        assert 'lazysloth_widget()' in code
        assert 'zle -N lazysloth_widget' in code
        assert 'bindkey "^M" lazysloth_widget' in code
        assert '/usr/bin/python3 -m lazysloth.monitors.hook' in code

    def test_generate_integration_code_fish(self, mock_shutil_which):
        """Test generating fish integration code."""
        installer = Installer()

        code = installer._generate_integration_code('fish')

        assert 'function lazysloth_preexec --on-event fish_preexec' in code
        assert '/usr/bin/python3 -m lazysloth.monitors.hook' in code

    def test_generate_integration_code_unsupported_shell(self):
        """Test generating integration code for unsupported shell."""
        installer = Installer()

        with pytest.raises(ValueError, match="Unsupported shell: unknown"):
            installer._generate_integration_code('unknown')

    def test_install_new_config_file(self, mock_home_dir, mock_shutil_which):
        """Test installing LazySloth to a new configuration file."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Install to bash (no existing config)
            installer.install('bash')

            # Verify config file was created
            bashrc = mock_home_dir / '.bashrc'
            assert bashrc.exists()

            # Verify integration was added
            content = bashrc.read_text()
            assert '# LazySloth integration' in content
            assert 'lazysloth_preexec()' in content
            assert '# End LazySloth integration' in content

    def test_install_existing_config_file(self, mock_home_dir, mock_shutil_which):
        """Test installing LazySloth to an existing configuration file."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create existing bashrc
            bashrc = mock_home_dir / '.bashrc'
            original_content = "# Existing config\nexport PATH=$HOME/bin:$PATH\n"
            bashrc.write_text(original_content)

            # Install LazySloth
            installer.install('bash')

            # Verify original content is preserved and integration is added
            content = bashrc.read_text()
            assert original_content in content
            assert '# LazySloth integration' in content
            assert 'lazysloth_preexec()' in content

    def test_install_already_installed_no_force(self, mock_home_dir, mock_shutil_which):
        """Test installing when already installed without force flag."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with existing integration
            bashrc = mock_home_dir / '.bashrc'
            bashrc.write_text("# LazySloth integration\necho 'already installed'\n")

            # Should raise error when trying to install again
            with pytest.raises(ValueError, match="LazySloth is already installed"):
                installer.install('bash')

    def test_install_already_installed_with_force(self, mock_home_dir, mock_shutil_which):
        """Test installing when already installed with force flag."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with existing integration
            bashrc = mock_home_dir / '.bashrc'
            old_integration = """# LazySloth integration
old integration code
# End LazySloth integration"""
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
        """Test uninstalling LazySloth removes integration code."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with LazySloth integration
            bashrc = mock_home_dir / '.bashrc'
            content_with_integration = """# Original content
export PATH=$HOME/bin:$PATH

# LazySloth integration
lazysloth_preexec() {
    echo "LazySloth hook"
}
# End LazySloth integration

# More original content
alias ll='ls -la'
"""
            bashrc.write_text(content_with_integration)

            # Uninstall LazySloth
            installer.uninstall('bash')

            # Verify integration was removed but original content remains
            content = bashrc.read_text()
            assert '# LazySloth integration' not in content
            assert 'lazysloth_preexec' not in content
            assert '# End LazySloth integration' not in content
            assert 'export PATH=$HOME/bin:$PATH' in content
            assert "alias ll='ls -la'" in content

    def test_uninstall_no_config_file(self, mock_home_dir):
        """Test uninstalling when no config file exists."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Should not raise error when config file doesn't exist
            installer.uninstall('bash')  # Should complete without error

    def test_uninstall_multiple_integrations(self, mock_home_dir):
        """Test uninstalling removes multiple LazySloth integration blocks."""
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create bashrc with multiple integration blocks
            bashrc = mock_home_dir / '.bashrc'
            content_with_multiple = """# Original content

# LazySloth integration
old integration 1
# End LazySloth integration

# Some other content

# LazySloth integration
old integration 2
# End LazySloth integration

# More content
"""
            bashrc.write_text(content_with_multiple)

            # Uninstall LazySloth
            installer.uninstall('bash')

            # Verify all integration blocks were removed
            content = bashrc.read_text()
            assert '# LazySloth integration' not in content
            assert 'old integration 1' not in content
            assert 'old integration 2' not in content
            assert '# End LazySloth integration' not in content

    def test_clean_lazysloth_data(self, mock_home_dir):
        """Test that _clean_lazysloth_data removes the correct files."""
        from lazysloth.core.installer import Installer

        # Create installer and config
        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            # Create config dir and files that should be removed
            config_dir = mock_home_dir / '.config' / 'lazysloth'
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create files that should be removed
            aliases_file = config_dir / 'aliases.yaml'
            stats_file = config_dir / 'stats.yaml'
            file_mtimes = config_dir / '.file_mtimes'
            last_check = config_dir / '.last_file_check'

            # Create file that should be preserved
            config_file = config_dir / 'config.yaml'

            # Write test content to all files
            for f in [aliases_file, stats_file, file_mtimes, last_check, config_file]:
                f.write_text('test content')
                assert f.exists()

            # Call cleanup method
            installer._clean_lazysloth_data()

            # Verify files to be removed are gone
            assert not aliases_file.exists()
            assert not stats_file.exists()
            assert not file_mtimes.exists()
            assert not last_check.exists()

            # Verify config file is preserved
            assert config_file.exists()
            assert config_file.read_text() == 'test content'

    def test_uninstall_calls_cleanup(self, mock_home_dir):
        """Test that uninstall method calls cleanup."""
        from lazysloth.core.installer import Installer

        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            with patch.object(installer, '_clean_lazysloth_data') as mock_cleanup:
                # Create a bashrc file to uninstall from
                bashrc = mock_home_dir / '.bashrc'
                bashrc.write_text('# LazySloth integration\ntest\n# End LazySloth integration\n')

                installer.uninstall('bash')

                # Verify cleanup was called
                mock_cleanup.assert_called_once()

    def test_install_force_calls_cleanup(self, mock_home_dir):
        """Test that install with force calls cleanup."""
        from lazysloth.core.installer import Installer

        installer = Installer()

        with patch.object(Path, 'home', return_value=mock_home_dir):
            with patch.object(installer, '_clean_lazysloth_data') as mock_cleanup:
                with patch('lazysloth.core.slothrc.SlothRC'):
                    # Create a bashrc file
                    bashrc = mock_home_dir / '.bashrc'
                    bashrc.write_text('# Some existing content\n')

                    # Install with force=True should call cleanup
                    installer.install('bash', force=True)

                    # Verify cleanup was called
                    mock_cleanup.assert_called_once()