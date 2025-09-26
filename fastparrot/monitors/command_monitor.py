import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from ..core.config import Config
from ..collectors.alias_collector import AliasCollector

class CommandMonitor:
    """Monitors command usage and provides alias suggestions."""

    def __init__(self):
        self.config = Config()
        self.collector = AliasCollector()

    def record_command(self, command: str) -> Optional[str]:
        """
        Record a command execution by alias and return suggestion/blocking message.
        Returns suggestion text, blocking message, or None.
        """
        if not self.config.get('monitoring.enabled', True):
            return None

        # Skip ignored commands
        ignored_commands = self.config.get('monitoring.ignored_commands', [])
        command_base = command.split()[0] if command.split() else command

        if command_base in ignored_commands:
            return None

        # Only track commands that have aliases
        existing_alias = self.collector.find_alias_for_command(command)
        if not existing_alias:
            return None

        alias_name, alias_data = existing_alias

        # Load current stats (now organized by alias)
        stats = self.config.get_stats_data()

        # Initialize alias entry if it doesn't exist
        if alias_name not in stats:
            stats[alias_name] = {
                'count': 0,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'alias_command': alias_data.get('command', '')
            }

        # Update stats
        stats[alias_name]['count'] += 1
        stats[alias_name]['last_seen'] = datetime.now().isoformat()

        # Save updated stats
        self.config.save_stats_data(stats)

        # Check for notice or blocking
        return self._check_for_action(command, stats[alias_name], existing_alias)

    def _generate_alias_suggestion(self, command: str, alias_name: str, alias_data: Dict) -> str:
        """Generate a proper alias suggestion that handles commands with arguments."""
        alias_command = alias_data.get('command', '')

        # If the command is exactly the alias command, just suggest the alias
        if command == alias_command:
            return f"'{alias_name}'"

        # If command starts with alias command + space, replace the base command with alias
        if command.startswith(alias_command + ' '):
            args = command[len(alias_command):]  # Get everything after the base command
            return f"'{alias_name}{args}'"

        # Fallback - just suggest the alias (shouldn't happen with current logic)
        return f"'{alias_name}'"

    def _check_for_action(self, command: str, command_stats: Dict, existing_alias) -> Optional[str]:
        """Check if we should show notice, block command, or do nothing."""
        notice_threshold = self.config.get('monitoring.notice_threshold', 1)
        blocking_threshold = self.config.get('monitoring.blocking_threshold', 3)
        blocking_enabled = self.config.get('monitoring.blocking_enabled', False)

        count = command_stats['count']
        if not existing_alias:
            return None
        alias_name, alias_data = existing_alias

        # Check for blocking first (if enabled and threshold reached)
        if (blocking_enabled and
            existing_alias and
            count >= blocking_threshold):
            suggested_command = self._generate_alias_suggestion(command, alias_name, alias_data)
            return (f"\nCommand blocked!"
                    f"\n🚫🦥 Time to be lazy."
                    f"\nUse {suggested_command} instead of '{command}'"
                    )
        # Check for notice (show every time when at threshold, before blocking)
        if (existing_alias and notice_threshold <= count < blocking_threshold):
            suggested_command = self._generate_alias_suggestion(command, alias_name, alias_data)
            return f"\n🦥💡 You can use {suggested_command} instead of '{command}'"

        return None

    def get_command_stats(self) -> Dict[str, Dict]:
        """Get command usage statistics."""
        return self.config.get_stats_data()

