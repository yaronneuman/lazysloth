"""
Integration tests specifically for bash integration functionality.
"""

import pytest
import tempfile
import subprocess
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from lazysloth.cli import install, uninstall
from lazysloth.core.installer import Installer
from lazysloth.monitors.hook import main as hook_main


@pytest.mark.integration
class TestBashIntegration:
    """Test bash integration with realistic scenarios."""

    def test_bash_integration_code_generation(self):
        """Test that bash integration code is generated correctly."""
        installer = Installer()

        with patch('shutil.which', return_value='/usr/bin/python3'):
            code = installer._generate_integration_code('bash')

            # Verify essential components
            assert '# Source LazySloth user aliases' in code
            assert 'lazysloth_preexec()' in code
            assert 'bash-preexec' in code
            assert 'preexec_functions+=(lazysloth_preexec)' in code
            assert 'python3 -m lazysloth.monitors.hook' in code
            assert 'kill -INT $$' in code

    def test_bash_installation_with_real_files(self):
        """Test bash installation creates proper integration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)
            bash_profile = home_dir / '.bash_profile'

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('shutil.which', return_value='/usr/bin/python3'):
                    installer = Installer()
                    installer.install('bash', force=False)

                    # Verify file was created and contains integration
                    assert bash_profile.exists()
                    content = bash_profile.read_text()

                    # Check for required components
                    assert '# LazySloth integration' in content
                    assert 'lazysloth_preexec()' in content
                    assert 'bash-preexec' in content
                    assert 'preexec_functions+=(lazysloth_preexec)' in content
                    assert '# End LazySloth integration' in content

                    # Verify the integration is properly structured
                    lines = content.splitlines()
                    start_idx = None
                    end_idx = None

                    for i, line in enumerate(lines):
                        if '# LazySloth integration' in line:
                            start_idx = i
                        elif '# End LazySloth integration' in line:
                            end_idx = i
                            break

                    assert start_idx is not None, "Start marker not found"
                    assert end_idx is not None, "End marker not found"
                    assert end_idx > start_idx, "End marker should come after start"

    def test_bash_hook_command_detection(self):
        """Test that bash hook properly detects and processes commands."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Set up isolated config environment
            home_dir = Path(tmp_dir)
            config_dir = home_dir / ".config" / "lazysloth"

            with patch.object(Path, 'home', return_value=home_dir):
                # Create test config directory
                config_dir.mkdir(parents=True, exist_ok=True)

                # Test hook with a simple command
                import sys
                original_argv = sys.argv

                try:
                    # Test hook doesn't crash on normal command
                    sys.argv = ['hook_main', 'ls', '-la']
                    result = None

                    try:
                        hook_main()
                        result = "success"
                    except SystemExit as e:
                        result = f"exit_{e.code}"
                    except Exception as e:
                        result = f"error_{e}"

                    # Hook should exit with 0 (allow command) for normal commands
                    assert result in ["success", "exit_0"], f"Unexpected result: {result}"

                    # Test hook ignores lazysloth commands
                    sys.argv = ['hook_main', 'lazysloth', 'status']
                    result = None

                    try:
                        hook_main()
                        result = "success"
                    except SystemExit as e:
                        result = f"exit_{e.code}"
                    except Exception as e:
                        result = f"error_{e}"

                    # Should exit with 0 for lazysloth commands (allow them)
                    assert result in ["success", "exit_0"], f"LazySloth commands should be allowed: {result}"

                finally:
                    sys.argv = original_argv

    def test_bash_integration_with_existing_bash_profile(self):
        """Test installation when .bash_profile already exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)
            bash_profile = home_dir / '.bash_profile'

            # Create existing bash_profile with content
            existing_content = """
# User's existing bash_profile
export PATH="$PATH:$HOME/bin"
alias ll='ls -la'
"""
            bash_profile.write_text(existing_content)

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('shutil.which', return_value='/usr/bin/python3'):
                    installer = Installer()
                    installer.install('bash', force=False)

                    # Verify existing content is preserved
                    content = bash_profile.read_text()
                    assert "export PATH" in content
                    assert "alias ll='ls -la'" in content

                    # Verify integration was added
                    assert '# LazySloth integration' in content
                    assert 'lazysloth_preexec()' in content

    def test_bash_uninstallation_cleanup(self):
        """Test that uninstallation properly removes integration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)
            bash_profile = home_dir / '.bash_profile'

            # Create bash_profile with existing content and integration
            content_with_integration = """
# User's existing bash_profile
export PATH="$PATH:$HOME/bin"
alias ll='ls -la'

# LazySloth integration
# Source LazySloth user aliases
source ~/.slothrc

# LazySloth command monitoring and blocking function
lazysloth_preexec() {
    local cmd_line="$1"
    /usr/bin/python3 -m lazysloth.monitors.hook "$cmd_line"
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        kill -INT $$
    fi
}
preexec_functions+=(lazysloth_preexec)
# End LazySloth integration
"""
            bash_profile.write_text(content_with_integration)

            with patch.object(Path, 'home', return_value=home_dir):
                installer = Installer()
                installer.uninstall('bash')

                # Verify integration was removed
                content = bash_profile.read_text()
                assert '# LazySloth integration' not in content
                assert 'lazysloth_preexec()' not in content
                assert 'preexec_functions+=(lazysloth_preexec)' not in content

                # Verify existing content is preserved
                assert "export PATH" in content
                assert "alias ll='ls -la'" in content

    def test_bash_force_reinstall(self):
        """Test force reinstallation removes old integration and adds new."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)
            bash_profile = home_dir / '.bash_profile'

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('shutil.which', return_value='/usr/bin/python3'):
                    installer = Installer()

                    # First installation
                    installer.install('bash', force=False)
                    first_content = bash_profile.read_text()

                    # Modify the integration manually (simulate old version)
                    modified_content = first_content.replace(
                        'lazysloth_preexec()',
                        'old_lazysloth_preexec()'
                    )
                    bash_profile.write_text(modified_content)

                    # Force reinstall
                    installer.install('bash', force=True)
                    final_content = bash_profile.read_text()

                    # Should have new integration, not old
                    assert 'lazysloth_preexec()' in final_content
                    assert 'old_lazysloth_preexec()' not in final_content

                    # Should only have one integration block
                    integration_count = final_content.count('# LazySloth integration')
                    assert integration_count == 1, f"Expected 1 integration block, found {integration_count}"

    @pytest.mark.slow
    def test_bash_integration_end_to_end(self):
        """End-to-end test: install, create alias, test hook simulation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            home_dir = Path(tmp_dir)
            config_dir = home_dir / ".config" / "lazysloth"

            with patch.object(Path, 'home', return_value=home_dir):
                with patch('shutil.which', return_value='/usr/bin/python3'):
                    # Install LazySloth
                    runner = CliRunner()
                    result = runner.invoke(install, ['--shell', 'bash'])
                    assert result.exit_code == 0

                    # Verify installation
                    bash_profile = home_dir / '.bash_profile'
                    assert bash_profile.exists()
                    content = bash_profile.read_text()
                    assert 'lazysloth_preexec()' in content

                    # Test that we can uninstall cleanly
                    result = runner.invoke(uninstall, ['--shell', 'bash'])
                    assert result.exit_code == 0

                    # Verify uninstallation
                    content = bash_profile.read_text()
                    assert 'lazysloth_preexec()' not in content

    def test_bash_python_path_detection(self):
        """Test that bash integration handles different Python paths."""
        installer = Installer()

        # Test with python3
        with patch('shutil.which', side_effect=lambda cmd: '/usr/bin/python3' if cmd == 'python3' else None):
            code = installer._generate_integration_code('bash')
            assert '/usr/bin/python3 -m lazysloth.monitors.hook' in code

        # Test with python (fallback)
        with patch('shutil.which', side_effect=lambda cmd: '/usr/bin/python' if cmd == 'python' else None):
            code = installer._generate_integration_code('bash')
            assert '/usr/bin/python -m lazysloth.monitors.hook' in code

    def test_bash_integration_error_handling(self):
        """Test that bash integration includes proper error handling."""
        installer = Installer()

        with patch('shutil.which', return_value='/usr/bin/python3'):
            code = installer._generate_integration_code('bash')

            # Should include pyenv filtering
            assert 'pyenv' in code

            # Should include curl for bash-preexec download
            assert 'curl' in code

    def test_bash_preexec_integration_format(self):
        """Test that bash-preexec integration is properly formatted."""
        installer = Installer()

        with patch('shutil.which', return_value='/usr/bin/python3'):
            code = installer._generate_integration_code('bash')

            # Verify bash-preexec download and sourcing
            assert 'curl -s https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh' in code
            assert '[[ -f ~/.bash-preexec.sh ]] && source ~/.bash-preexec.sh' in code

            # Verify function definition format
            lines = code.splitlines()
            func_lines = [line for line in lines if 'lazysloth_preexec()' in line or line.strip().startswith('{')]

            # Should have function definition
            assert any('lazysloth_preexec()' in line for line in func_lines), "Function definition not found"

    def test_bash_blocking_mechanism(self):
        """Test that bash integration includes blocking mechanism."""
        installer = Installer()

        with patch('shutil.which', return_value='/usr/bin/python3'):
            code = installer._generate_integration_code('bash')

            # Should capture exit code
            assert 'local exit_code=$?' in code

            # Should check for blocking condition
            assert '[[ $exit_code -ne 0 ]]' in code

            # Should use kill to interrupt execution when blocked
            assert 'kill -INT $$' in code

            # Should use preexec parameter for command input
            assert 'local cmd_line="$1"' in code

            # Should include pyenv filtering
            assert 'pyenv' in code

            # Should skip LazySloth commands
            assert 'lazysloth' in code

            # Should register with preexec_functions
            assert 'preexec_functions+=(lazysloth_preexec)' in code

            # Should not include || true anymore
            assert '|| true' not in code