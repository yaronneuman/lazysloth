import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.config import Config


class AliasCollector:
    """Collects aliases from bash and zsh shell configuration files."""

    def __init__(self):
        self.config = Config()
        self.home = Path.home()

    def collect_all(self) -> Dict[str, Dict]:
        """Collect aliases from all supported shell configurations (bash and zsh)."""
        all_aliases = {}

        # Collect from different shell configs
        for shell in ["bash", "zsh"]:
            aliases = self.collect_from_shell(shell)
            all_aliases.update(aliases)

        # Save to config
        self.config.save_aliases_data(all_aliases)

        return all_aliases

    def collect_from_shell(self, shell: str) -> Dict[str, Dict]:
        """Collect aliases from a specific shell configuration (bash or zsh)."""
        if shell in ["bash", "zsh"]:
            return self._collect_bash_zsh_aliases(shell)
        else:
            raise ValueError(
                f"Unsupported shell: {shell}. Only 'bash' and 'zsh' are supported."
            )

    def _collect_bash_zsh_aliases(self, shell: str) -> Dict[str, Dict]:
        """Collect aliases from bash/zsh configuration files."""
        aliases = {}
        config_files = self._get_config_files(shell)

        for config_file in config_files:
            if config_file.exists():
                aliases.update(self._parse_bash_zsh_aliases(config_file, shell))

        return aliases

    def _get_config_files(self, shell: str) -> List[Path]:
        """Get configuration files for a shell."""
        config_files = {
            "bash": [
                self.home / ".bash_profile",
                self.home / ".bash_profile",
                self.home / ".bash_aliases",
                self.home / ".profile",
            ],
            "zsh": [
                self.home / ".zshrc",
                self.home / ".zsh_profile",
                self.home / ".zshenv",
                self.home / ".profile",
            ],
        }

        return config_files.get(shell, [])

    def _parse_bash_zsh_aliases(self, config_file: Path, shell: str) -> Dict[str, Dict]:
        """Parse aliases from bash/zsh configuration file."""
        aliases = {}

        try:
            with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Process line by line to properly handle comments
            lines = content.split("\n")
            alias_pattern = r"alias\s+([^=\s]+)=(['\"]?)([^'\"\n]+)\2"

            for line in lines:
                # Skip commented lines (lines that start with # after optional whitespace)
                stripped_line = line.lstrip()
                if stripped_line.startswith("#"):
                    continue

                # Skip lines that have text before 'alias' (not pure alias definitions)
                if not stripped_line.startswith("alias "):
                    continue

                # Now try to match the alias pattern
                match = re.search(alias_pattern, line)
                if match:
                    alias_name = match.group(1)
                    alias_command = match.group(3)

                    aliases[alias_name] = {
                        "command": alias_command,
                        "shell": shell,
                        "source_file": str(config_file),
                        "type": "alias",
                    }

        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {config_file}: {e}")

        return aliases

    def find_alias_for_command(self, command: str) -> Optional[Tuple[str, Dict]]:
        """Find the best alias for the given command with recursive resolution."""
        aliases = self.config.get_aliases_data()

        # First, expand any aliases in the command recursively
        expanded_command = self._expand_aliases_in_command(command, aliases)
        # Then find the most specific alias for the expanded command
        alias = self._find_most_specific_alias(
            expanded_command, self._expand_aliases(aliases)
        )
        return alias

    def _expand_aliases(
        self, aliases: Dict[str, Dict], max_depth: int = 10
    ) -> Dict[str, Dict]:
        """Recursively expand aliases commands to full form."""
        expanded_aliases_map = {}
        for alias_name, alias_data in aliases.items():
            current_command = alias_data.get("command", "")
            if not current_command:
                expanded_aliases_map[alias_name] = alias_data
                continue

            history = {alias_name}
            depth = 0
            while depth < max_depth:
                parts = current_command.split()
                if not parts:
                    break

                first_part = parts[0]
                if first_part in aliases and first_part not in history:
                    history.add(first_part)
                    aliased_command = aliases[first_part].get("command", "")
                    if aliased_command:
                        current_command = (
                            f"{aliased_command} {' '.join(parts[1:])}".strip()
                        )
                    else:
                        break  # Alias points to nothing
                else:
                    break  # No more aliases to expand or circular reference detected
                depth += 1

            expanded_aliases_map[alias_name] = {
                **alias_data,
                "command": current_command,
            }
        return expanded_aliases_map

    def _expand_aliases_in_command(
        self,
        command: str,
        aliases: Dict[str, Dict],
        max_depth: int = 10,
        expanded_aliases: set = None,
    ) -> str:
        """Recursively expand aliases in a command to get the full form, tracking already expanded aliases."""
        if max_depth <= 0:
            return command  # Prevent infinite recursion

        if expanded_aliases is None:
            expanded_aliases = set()

        parts = command.split()
        if not parts:
            return command

        first_part = parts[0]
        rest_parts = parts[1:] if len(parts) > 1 else []

        # Check if the first part is an alias and hasn't been expanded yet
        if first_part in aliases and first_part not in expanded_aliases:
            alias_command = aliases[first_part].get("command", "")
            if alias_command:
                # Add this alias to the set of expanded aliases
                expanded_aliases.add(first_part)

                # Replace the first part with the alias command
                if rest_parts:
                    expanded = f"{alias_command} {' '.join(rest_parts)}"
                else:
                    expanded = alias_command

                # Recursively expand in case the alias command contains more aliases
                return self._expand_aliases_in_command(
                    expanded, aliases, max_depth - 1, expanded_aliases
                )

        return command

    def _find_most_specific_alias(
        self, command: str, aliases: Dict[str, Dict]
    ) -> Optional[Tuple[str, Dict]]:
        """Find the most specific alias that matches the given command."""
        matches = []
        # Find all matching aliases
        for alias_name, alias_data in aliases.items():
            alias_command = alias_data.get("command", "")

            # Check if command starts with alias command (for commands with arguments)
            if alias_command == command or command.startswith(alias_command + " "):
                matches.append((alias_name, alias_data, len(alias_command)))

        if not matches:
            return None
        # Sort by length of alias command (descending) to prefer more specific aliases
        # For example: "git commit -m" (length 13) over "git" (length 3)
        matches.sort(key=lambda x: x[2], reverse=True)

        # Return the most specific match
        return matches[0][0], matches[0][1]
