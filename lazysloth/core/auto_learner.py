"""
Automatic alias learning system that monitors bash and zsh shell configuration files.
"""

from pathlib import Path
from typing import List, Dict, Set
from .config import Config
from ..collectors.alias_collector import AliasCollector


class AutoLearner:
    """Handles automatic learning of aliases from monitored files."""

    def __init__(self):
        self.config = Config()
        self.collector = AliasCollector()

    def learn_from_monitored_files(self, shell: str = None) -> Dict[str, int]:
        """
        Learn aliases from all monitored files for specified shell or all shells.

        Args:
            shell: Specific shell to learn from. If None, learns from all shells.

        Returns:
            Dict with counts: {'learned': N, 'updated': N, 'removed': N}
        """
        if shell:
            shells_to_process = [shell]
        else:
            monitored_files = self.config.get('monitored_files', {})
            shells_to_process = list(monitored_files.keys())

        total_learned = 0
        total_updated = 0
        total_removed = 0

        for shell_name in shells_to_process:
            counts = self._learn_from_shell(shell_name)
            total_learned += counts['learned']
            total_updated += counts['updated']
            total_removed += counts['removed']

        return {
            'learned': total_learned,
            'updated': total_updated,
            'removed': total_removed
        }

    def _learn_from_shell(self, shell: str) -> Dict[str, int]:
        """Learn aliases from monitored files for a specific shell."""
        monitored_files = self.config.get(f'monitored_files.{shell}', [])

        if not monitored_files:
            return {'learned': 0, 'updated': 0, 'removed': 0}

        # Get existing aliases to track changes
        existing_aliases = self.config.get_aliases_data()
        existing_from_shell = {
            name: data for name, data in existing_aliases.items()
            if data.get('shell') == shell
        }

        # Collect aliases from all monitored files for this shell
        new_aliases = {}
        for file_path in monitored_files:
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                try:
                    if shell in ['bash', 'zsh']:
                        file_aliases = self.collector._parse_bash_zsh_aliases(file_path, shell)
                    else:
                        continue

                    new_aliases.update(file_aliases)
                except Exception as e:
                    print(f"Warning: Could not parse {file_path}: {e}")

        # Calculate changes
        learned_count = 0
        updated_count = 0

        # Update existing aliases with new data
        for alias_name, alias_data in new_aliases.items():
            if alias_name not in existing_aliases:
                # New alias learned
                existing_aliases[alias_name] = alias_data
                learned_count += 1
            elif existing_aliases[alias_name].get('command') != alias_data.get('command'):
                # Existing alias updated
                existing_aliases[alias_name] = alias_data
                updated_count += 1
            else:
                # Alias exists and unchanged, update metadata
                existing_aliases[alias_name].update(alias_data)

        # Find removed aliases (existed in shell but not found in files now)
        new_alias_names = set(new_aliases.keys())
        old_alias_names = set(existing_from_shell.keys())
        removed_aliases = old_alias_names - new_alias_names
        removed_count = 0

        # Remove aliases that are no longer in the monitored files
        for alias_name in removed_aliases:
            # Only remove if it was from a monitored file (not manually added)
            alias_data = existing_aliases.get(alias_name, {})
            source_file = alias_data.get('source_file', '')

            # Check if source file is in monitored files
            monitored_file_names = [str(Path(f).name) for f in monitored_files]
            if (Path(source_file).name in monitored_file_names or
                source_file in monitored_files):
                del existing_aliases[alias_name]
                removed_count += 1

        # Save updated aliases
        self.config.save_aliases_data(existing_aliases)

        return {
            'learned': learned_count,
            'updated': updated_count,
            'removed': removed_count
        }

    def get_monitored_files(self, shell: str = None) -> Dict[str, List[str]]:
        """
        Get list of monitored files for shell(s).

        Args:
            shell: Specific shell. If None, returns all shells.

        Returns:
            Dict mapping shell names to list of monitored file paths.
        """
        monitored_files = self.config.get('monitored_files', {})

        if shell:
            return {shell: monitored_files.get(shell, [])}

        return monitored_files

    def add_monitored_file(self, shell: str, file_path: str) -> bool:
        """
        Add a file to the monitored files list for a shell.

        Args:
            shell: Shell name (bash, zsh)
            file_path: Path to file to monitor

        Returns:
            True if added successfully, False if already existed
        """
        monitored_files = self.config.get('monitored_files', {})

        if shell not in monitored_files:
            monitored_files[shell] = []

        # Convert to absolute path
        abs_path = str(Path(file_path).expanduser().resolve())

        if abs_path not in monitored_files[shell]:
            monitored_files[shell].append(abs_path)
            self.config.set('monitored_files', monitored_files)
            self.config.save()
            return True

        return False

    def remove_monitored_file(self, shell: str, file_path: str) -> bool:
        """
        Remove a file from the monitored files list for a shell.

        Args:
            shell: Shell name (bash, zsh)
            file_path: Path to file to stop monitoring

        Returns:
            True if removed successfully, False if not found
        """
        monitored_files = self.config.get('monitored_files', {})

        if shell not in monitored_files:
            return False

        # Convert to absolute path for comparison
        abs_path = str(Path(file_path).expanduser().resolve())

        # Try both absolute and original path
        removed = False
        if abs_path in monitored_files[shell]:
            monitored_files[shell].remove(abs_path)
            removed = True
        elif file_path in monitored_files[shell]:
            monitored_files[shell].remove(file_path)
            removed = True

        if removed:
            self.config.set('monitored_files', monitored_files)
            self.config.save()

        return removed

    def check_file_changes(self, shell: str = None) -> bool:
        """
        Check if any monitored files have changed and relearn if needed.

        Args:
            shell: Specific shell to check. If None, checks all shells.

        Returns:
            True if any files changed and relearning occurred.
        """
        # This is a simple implementation. In a real system, you'd want to:
        # 1. Store file modification times in config
        # 2. Compare with current modification times
        # 3. Only relearn if files actually changed

        # For now, we'll just always relearn
        results = self.learn_from_monitored_files(shell)
        return (results['learned'] > 0 or
                results['updated'] > 0 or
                results['removed'] > 0)