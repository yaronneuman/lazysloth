import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class Installer:
    """Handles installation of LazySloth shell integration."""

    def __init__(self):
        self.package_dir = Path(__file__).parent.parent
        self.shells_dir = self.package_dir / "shells"

    def _clean_lazysloth_data(self):
        """Clean LazySloth learned data files while preserving configuration."""
        from .config import Config

        config = Config()

        # Files to remove (learned data)
        files_to_remove = [
            config.aliases_file,  # ~/.config/lazysloth/aliases.yaml
            config.stats_file,  # ~/.config/lazysloth/stats.yaml
            config.config_dir / ".file_mtimes",  # file change tracking
            config.config_dir / ".last_file_check",  # last check timestamp
        ]

        for file_path in files_to_remove:
            try:
                if file_path.exists():
                    file_path.unlink()
            except OSError:
                # Silently continue if we can't remove a file
                pass

    def detect_shell(self) -> str:
        """Detect the user's current shell."""
        shell_path = os.environ.get("SHELL", "/bin/bash")
        shell_name = Path(shell_path).name

        # Map shell names to our supported shells
        shell_mapping = {"bash": "bash", "zsh": "zsh"}

        return shell_mapping.get(shell_name, "bash")

    def get_shell_config_files(self, shell: str) -> List[Path]:
        """Get list of configuration files for a shell."""
        home = Path.home()

        shell_configs = {
            "bash": [home / ".bash_profile", home / ".bash_profile", home / ".profile"],
            "zsh": [home / ".zshrc", home / ".zsh_profile", home / ".profile"],
        }

        return shell_configs.get(shell, [])

    def find_existing_config(self, shell: str) -> Optional[Path]:
        """Find existing shell configuration file."""
        config_files = self.get_shell_config_files(shell)

        for config_file in config_files:
            if config_file.exists():
                return config_file

        # Return the primary config file even if it doesn't exist
        return config_files[0] if config_files else None

    def install(self, shell: str, force: bool = False):
        """Install LazySloth for the specified shell."""
        config_file = self.find_existing_config(shell)

        if not config_file:
            raise ValueError(f"No configuration file found for shell: {shell}")

        # Create config file if it doesn't exist
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.touch()

        # Check if already installed
        lazysloth_marker = "# LazySloth integration"
        already_installed = False

        if config_file.exists():
            with open(config_file, "r") as f:
                content = f.read()
                already_installed = lazysloth_marker in content

            if already_installed and not force:
                raise ValueError(
                    "LazySloth is already installed. Use --force to reinstall."
                )

        # Always clean up existing installations first (especially when using --force)
        if already_installed:
            self.uninstall(shell)
        elif force:
            # Even if not detected as installed, clean data when forcing reinstall
            self._clean_lazysloth_data()

        # Generate integration code
        integration_code = self._generate_integration_code(shell)

        # Add integration to config file
        with open(config_file, "a") as f:
            f.write(f"\n\n{lazysloth_marker}\n")
            f.write(integration_code)
            f.write("\n# End LazySloth integration\n")

        # Ensure .slothrc exists and is sourced
        from .slothrc import SlothRC

        slothrc = SlothRC()
        slothrc.ensure_exists()

    def _generate_integration_code(self, shell: str) -> str:
        """Generate shell-specific integration code."""
        python_path = shutil.which("python3") or shutil.which("python")

        # Get .slothrc source line
        from .slothrc import SlothRC

        slothrc = SlothRC()
        slothrc_source = slothrc.get_source_line(shell)

        if shell == "bash":
            return f"""
# Source LazySloth user aliases
{slothrc_source}

# Download and source bash-preexec if not already installed
if [[ ! -f ~/.bash-preexec.sh ]]; then
    curl -s https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh -o ~/.bash-preexec.sh
fi
[[ -f ~/.bash-preexec.sh ]] && source ~/.bash-preexec.sh

# LazySloth command monitoring and blocking function
lazysloth_preexec() {{
    local cmd_line="$1"

    # Skip empty commands
    [[ -z "$cmd_line" || "$cmd_line" =~ ^[[:space:]]*$ ]] && return

    # Skip LazySloth itself
    [[ "$cmd_line" =~ ^[[:space:]]*lazysloth ]] && return

    # Skip pyenv internals
    case "$cmd_line" in
        _pyenv_virtualenv_hook*|pyenv\\ init*|pyenv\\ virtualenv-init*)
            return
            ;;
    esac

    # Call Python checker
    {python_path} -m lazysloth.monitors.hook "$cmd_line"
    local exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        # Kill the command immediately
        kill -INT $$
    fi
}}

# Register the function with bash-preexec
preexec_functions+=(lazysloth_preexec)
"""

        elif shell == "zsh":
            return f"""
# Source LazySloth user aliases
{slothrc_source}

# LazySloth ZLE widget for command interception

# LazySloth command interceptor widget
lazysloth_widget() {{
    # Get the command from the buffer
    local cmd_line="$BUFFER"

    # Skip empty commands
    if [[ -z "$cmd_line" || "$cmd_line" =~ '^[[:space:]]*$' ]]; then
        zle .accept-line
        return
    fi

    # Skip LazySloth's own commands to avoid infinite loops
    if [[ "$cmd_line" =~ '^[[:space:]]*lazysloth' ]]; then
        zle .accept-line
        return
    fi

    # Call Python script to check command
    {python_path} -m lazysloth.monitors.hook "$cmd_line"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        # Command allowed - execute normally
        zle .accept-line
    else
        # Command blocked - clear buffer and reset prompt
        BUFFER=""
        zle reset-prompt
    fi
}}

# Create the ZLE widget
zle -N lazysloth_widget

# Bind to Enter key (^M) and ^J
bindkey "^M" lazysloth_widget
bindkey "^J" lazysloth_widget
"""

        else:
            raise ValueError(
                f"Unsupported shell: {shell}. Only 'bash' and 'zsh' are supported."
            )

    def uninstall(self, shell: str):
        """Remove LazySloth integration from shell configuration."""
        config_file = self.find_existing_config(shell)

        if not config_file or not config_file.exists():
            return

        with open(config_file, "r") as f:
            content = f.read()

        # Remove all LazySloth integrations (handle multiple sections)
        import re

        # Pattern to match LazySloth integration blocks
        pattern = r"# LazySloth integration.*?# End LazySloth integration\s*"

        # Remove all LazySloth blocks (with newlines)
        cleaned_content = re.sub(pattern, "", content, flags=re.DOTALL)

        # Clean up excessive newlines (more than 2 consecutive newlines)
        cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content)

        with open(config_file, "w") as f:
            f.write(cleaned_content)

        # Clean up LazySloth learned data
        self._clean_lazysloth_data()
