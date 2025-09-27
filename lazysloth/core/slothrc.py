"""
SlothRC management - handles ~/.slothrc file for user-defined aliases.
"""

import os
from pathlib import Path
from typing import Dict, List


class SlothRC:
    """Manages the ~/.slothrc file for user-defined aliases."""

    def __init__(self):
        self.rc_file = Path.home() / '.slothrc'

    def add_alias(self, alias_name: str, command: str):
        """Add an alias to .slothrc file."""
        # Read existing content
        existing_aliases = self._read_aliases()

        # Update or add the alias
        existing_aliases[alias_name] = command

        # Write back to file
        self._write_aliases(existing_aliases)

    def remove_alias(self, alias_name: str) -> bool:
        """Remove an alias from .slothrc file. Returns True if removed, False if not found."""
        existing_aliases = self._read_aliases()

        if alias_name in existing_aliases:
            del existing_aliases[alias_name]
            self._write_aliases(existing_aliases)
            return True

        return False

    def get_aliases(self) -> Dict[str, str]:
        """Get all aliases from .slothrc file."""
        return self._read_aliases()

    def _read_aliases(self) -> Dict[str, str]:
        """Read aliases from .slothrc file."""
        aliases = {}

        if not self.rc_file.exists():
            return aliases

        try:
            with open(self.rc_file, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse alias lines: alias name="command"
                    if line.startswith('alias '):
                        alias_part = line[6:]  # Remove 'alias '

                        # Find the = sign
                        if '=' in alias_part:
                            alias_name, alias_command = alias_part.split('=', 1)
                            alias_name = alias_name.strip()
                            alias_command = alias_command.strip()

                            # Remove quotes if present
                            if alias_command.startswith('"') and alias_command.endswith('"'):
                                alias_command = alias_command[1:-1]
                            elif alias_command.startswith("'") and alias_command.endswith("'"):
                                alias_command = alias_command[1:-1]

                            aliases[alias_name] = alias_command

        except (IOError, UnicodeDecodeError):
            # If we can't read the file, return empty dict
            pass

        return aliases

    def _write_aliases(self, aliases: Dict[str, str]):
        """Write aliases to .slothrc file."""
        # Create the file with header comment
        content = [
            "# LazySloth user-defined aliases",
            "# This file is automatically managed by LazySloth",
            "# You can edit it manually, but changes may be overwritten",
            ""
        ]

        # Add aliases in sorted order for consistency
        for alias_name in sorted(aliases.keys()):
            command = aliases[alias_name]
            # Escape double quotes in the command
            escaped_command = command.replace('"', '\\"')
            content.append(f'alias {alias_name}="{escaped_command}"')

        content.append("")  # Trailing newline

        try:
            with open(self.rc_file, 'w') as f:
                f.write('\n'.join(content))
        except IOError as e:
            raise RuntimeError(f"Failed to write to {self.rc_file}: {e}")

    def ensure_exists(self):
        """Ensure .slothrc file exists (create if it doesn't)."""
        if not self.rc_file.exists():
            self._write_aliases({})

    def get_source_line(self, shell: str) -> str:
        """Get the source line to add to shell config for the given shell."""
        rc_path = str(self.rc_file)

        if shell == 'fish':
            return f"source {rc_path}"
        else:  # bash, zsh
            return f"[ -f {rc_path} ] && source {rc_path}"