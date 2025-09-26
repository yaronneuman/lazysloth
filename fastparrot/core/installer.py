import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class Installer:
    """Handles installation of FastParrot shell integration."""

    def __init__(self):
        self.package_dir = Path(__file__).parent.parent
        self.shells_dir = self.package_dir / 'shells'

    def detect_shell(self) -> str:
        """Detect the user's current shell."""
        shell_path = os.environ.get('SHELL', '/bin/bash')
        shell_name = Path(shell_path).name

        # Map shell names to our supported shells
        shell_mapping = {
            'bash': 'bash',
            'zsh': 'zsh',
            'fish': 'fish'
        }

        return shell_mapping.get(shell_name, 'bash')

    def get_shell_config_files(self, shell: str) -> List[Path]:
        """Get list of configuration files for a shell."""
        home = Path.home()

        shell_configs = {
            'bash': [
                home / '.bashrc',
                home / '.bash_profile',
                home / '.profile'
            ],
            'zsh': [
                home / '.zshrc',
                home / '.zsh_profile',
                home / '.profile'
            ],
            'fish': [
                home / '.config' / 'fish' / 'config.fish'
            ]
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
        """Install FastParrot for the specified shell."""
        config_file = self.find_existing_config(shell)

        if not config_file:
            raise ValueError(f"No configuration file found for shell: {shell}")

        # Create config file if it doesn't exist
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.touch()

        # Check if already installed
        fastparrot_marker = "# FastParrot integration"
        already_installed = False

        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()
                already_installed = fastparrot_marker in content

            if already_installed and not force:
                raise ValueError("FastParrot is already installed. Use --force to reinstall.")

        # Always clean up existing installations first (especially when using --force)
        if already_installed:
            self.uninstall(shell)

        # Generate integration code
        integration_code = self._generate_integration_code(shell)

        # Add integration to config file
        with open(config_file, 'a') as f:
            f.write(f"\n\n{fastparrot_marker}\n")
            f.write(integration_code)
            f.write("\n# End FastParrot integration\n")

        # Ensure .fastparrotrc exists and is sourced
        from .fastparrotrc import FastParrotRC
        fastparrotrc = FastParrotRC()
        fastparrotrc.ensure_exists()

    def _generate_integration_code(self, shell: str) -> str:
        """Generate shell-specific integration code."""
        python_path = shutil.which('python3') or shutil.which('python')

        # Get .fastparrotrc source line
        from .fastparrotrc import FastParrotRC
        fastparrotrc = FastParrotRC()
        fastparrotrc_source = fastparrotrc.get_source_line(shell)

        if shell == 'bash':
            return f'''
# Source FastParrot user aliases
{fastparrotrc_source}

# FastParrot command monitoring hook
fastparrot_preexec() {{
    if [ -n "${{BASH_COMMAND}}" ]; then
        {python_path} -m fastparrot.monitors.hook "${{BASH_COMMAND}}" 2>/dev/null || true
    fi
}}
trap 'fastparrot_preexec' DEBUG
'''

        elif shell == 'zsh':
            return f'''
# Source FastParrot user aliases
{fastparrotrc_source}

# FastParrot ZLE widget for command interception

# FastParrot command interceptor widget
fastparrot_widget() {{
    # Get the command from the buffer
    local cmd_line="$BUFFER"

    # Skip empty commands
    if [[ -z "$cmd_line" || "$cmd_line" =~ '^[[:space:]]*$' ]]; then
        zle .accept-line
        return
    fi

    # Skip FastParrot's own commands to avoid infinite loops
    if [[ "$cmd_line" =~ '^[[:space:]]*fastparrot' ]]; then
        zle .accept-line
        return
    fi

    # Call Python script to check command
    {python_path} -m fastparrot.monitors.hook "$cmd_line"
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
zle -N fastparrot_widget

# Bind to Enter key (^M) and ^J
bindkey "^M" fastparrot_widget
bindkey "^J" fastparrot_widget
'''

        elif shell == 'fish':
            return f'''
# Source FastParrot user aliases
{fastparrotrc_source}

# FastParrot command monitoring hook
function fastparrot_preexec --on-event fish_preexec
    {python_path} -m fastparrot.monitors.hook "$argv" 2>/dev/null || true
end
'''

        else:
            raise ValueError(f"Unsupported shell: {shell}")

    def uninstall(self, shell: str):
        """Remove FastParrot integration from shell configuration."""
        config_file = self.find_existing_config(shell)

        if not config_file or not config_file.exists():
            return

        with open(config_file, 'r') as f:
            content = f.read()

        # Remove all FastParrot integrations (handle multiple sections)
        import re

        # Pattern to match FastParrot integration blocks
        pattern = r'# FastParrot integration.*?# End FastParrot integration\s*'

        # Remove all FastParrot blocks (with newlines)
        cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Clean up excessive newlines (more than 2 consecutive newlines)
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)

        with open(config_file, 'w') as f:
            f.write(cleaned_content)