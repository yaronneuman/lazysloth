import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..core.config import Config

class AliasCollector:
    """Collects aliases from shell configuration files."""

    def __init__(self):
        self.config = Config()
        self.home = Path.home()

    def collect_all(self) -> Dict[str, Dict]:
        """Collect aliases from all supported shell configurations."""
        all_aliases = {}

        # Collect from different shell configs
        for shell in ['bash', 'zsh', 'fish']:
            aliases = self.collect_from_shell(shell)
            all_aliases.update(aliases)

        # Save to config
        self.config.save_aliases_data(all_aliases)

        return all_aliases

    def collect_from_shell(self, shell: str) -> Dict[str, Dict]:
        """Collect aliases from a specific shell configuration."""
        if shell == 'fish':
            return self._collect_fish_aliases()
        else:
            return self._collect_bash_zsh_aliases(shell)

    def _collect_bash_zsh_aliases(self, shell: str) -> Dict[str, Dict]:
        """Collect aliases from bash/zsh configuration files."""
        aliases = {}
        config_files = self._get_config_files(shell)

        for config_file in config_files:
            if config_file.exists():
                aliases.update(self._parse_bash_zsh_aliases(config_file, shell))

        return aliases

    def _collect_fish_aliases(self) -> Dict[str, Dict]:
        """Collect aliases from Fish shell configuration."""
        aliases = {}
        fish_config = self.home / '.config' / 'fish' / 'config.fish'
        fish_functions = self.home / '.config' / 'fish' / 'functions'

        # Parse config.fish for aliases
        if fish_config.exists():
            aliases.update(self._parse_fish_config(fish_config))

        # Parse function files
        if fish_functions.exists() and fish_functions.is_dir():
            for func_file in fish_functions.glob('*.fish'):
                aliases.update(self._parse_fish_function(func_file))

        return aliases

    def _get_config_files(self, shell: str) -> List[Path]:
        """Get configuration files for a shell."""
        config_files = {
            'bash': [
                self.home / '.bashrc',
                self.home / '.bash_profile',
                self.home / '.bash_aliases',
                self.home / '.profile'
            ],
            'zsh': [
                self.home / '.zshrc',
                self.home / '.zsh_profile',
                self.home / '.zshenv',
                self.home / '.profile'
            ]
        }

        return config_files.get(shell, [])

    def _parse_bash_zsh_aliases(self, config_file: Path, shell: str) -> Dict[str, Dict]:
        """Parse aliases from bash/zsh configuration file."""
        aliases = {}

        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Pattern to match alias definitions
            # Matches: alias name='command' or alias name="command"
            alias_pattern = r"alias\s+([^=\s]+)=(['\"]?)([^'\"\n]+)\2"

            for match in re.finditer(alias_pattern, content, re.MULTILINE):
                alias_name = match.group(1)
                alias_command = match.group(3)

                aliases[alias_name] = {
                    'command': alias_command,
                    'shell': shell,
                    'source_file': str(config_file),
                    'type': 'alias'
                }

        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {config_file}: {e}")

        return aliases

    def _parse_fish_config(self, config_file: Path) -> Dict[str, Dict]:
        """Parse aliases from Fish config.fish."""
        aliases = {}

        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Pattern for Fish aliases: alias name 'command'
            alias_pattern = r"alias\s+([^\s]+)\s+(['\"]?)([^'\"\n]+)\2"

            for match in re.finditer(alias_pattern, content, re.MULTILINE):
                alias_name = match.group(1)
                alias_command = match.group(3)

                aliases[alias_name] = {
                    'command': alias_command,
                    'shell': 'fish',
                    'source_file': str(config_file),
                    'type': 'alias'
                }

        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {config_file}: {e}")

        return aliases

    def _parse_fish_function(self, func_file: Path) -> Dict[str, Dict]:
        """Parse Fish function file."""
        aliases = {}
        func_name = func_file.stem

        try:
            with open(func_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Simple heuristic: if function is short and contains a single command,
            # treat it as an alias-like function
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            non_empty_lines = [line for line in lines if not line.startswith('#') and line != 'end']

            if 2 <= len(non_empty_lines) <= 4:  # function declaration + 1-2 commands + end
                # Extract the main command (usually the second non-empty line)
                if len(non_empty_lines) >= 2:
                    main_command = non_empty_lines[1]

                    aliases[func_name] = {
                        'command': main_command,
                        'shell': 'fish',
                        'source_file': str(func_file),
                        'type': 'function'
                    }

        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {func_file}: {e}")

        return aliases

    def find_alias_for_command(self, command: str) -> Optional[Tuple[str, Dict]]:
        """Find the best alias for the given command with recursive resolution."""
        aliases = self.config.get_aliases_data()

        # First, expand any aliases in the command recursively
        expanded_command = self._expand_aliases_in_command(command, aliases)

        # Then find the most specific alias for the expanded command
        return self._find_most_specific_alias(expanded_command, aliases)

    def _expand_aliases_in_command(self, command: str, aliases: Dict[str, Dict], max_depth: int = 10) -> str:
        """Recursively expand aliases in a command to get the full form."""
        if max_depth <= 0:
            return command  # Prevent infinite recursion

        parts = command.split()
        if not parts:
            return command

        first_part = parts[0]
        rest_parts = parts[1:] if len(parts) > 1 else []

        # Check if the first part is an alias
        if first_part in aliases:
            alias_command = aliases[first_part].get('command', '')
            if alias_command:
                # Replace the first part with the alias command
                if rest_parts:
                    expanded = f"{alias_command} {' '.join(rest_parts)}"
                else:
                    expanded = alias_command

                # Recursively expand in case the alias command contains more aliases
                return self._expand_aliases_in_command(expanded, aliases, max_depth - 1)

        return command

    def _find_most_specific_alias(self, command: str, aliases: Dict[str, Dict]) -> Optional[Tuple[str, Dict]]:
        """Find the most specific alias that matches the given command."""
        matches = []

        # Find all matching aliases
        for alias_name, alias_data in aliases.items():
            alias_command = alias_data.get('command', '')

            # Exact match
            if alias_command == command:
                matches.append((alias_name, alias_data, len(alias_command)))

            # Check if command starts with alias command (for commands with arguments)
            elif command.startswith(alias_command + ' '):
                matches.append((alias_name, alias_data, len(alias_command)))

        if not matches:
            return None

        # Sort by length of alias command (descending) to prefer more specific aliases
        # For example: "git commit -m" (length 13) over "git" (length 3)
        matches.sort(key=lambda x: x[2], reverse=True)

        # Return the most specific match
        return matches[0][0], matches[0][1]

