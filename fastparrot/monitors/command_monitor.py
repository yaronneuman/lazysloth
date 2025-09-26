import os
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
from ..core.config import Config
from ..collectors.alias_collector import AliasCollector


class MonitorAction(Enum):
    """Enum representing the action to take based on command monitoring."""
    NO_ACTION = "no_action"
    NOTICE = "notice"
    BLOCK = "block"


@dataclass
class MonitorResult:
    """Result of command monitoring containing action and message."""
    action: MonitorAction
    message: str

    def is_blocking(self) -> bool:
        """Check if this result represents a blocking action."""
        return self.action == MonitorAction.BLOCK

    def is_notice(self) -> bool:
        """Check if this result represents a notice action."""
        return self.action == MonitorAction.NOTICE

class CommandMonitor:
    """Monitors command usage and provides alias suggestions."""

    def __init__(self):
        self.config = Config()
        self.collector = AliasCollector()

    def record_command(self, command: str) -> Optional[MonitorResult]:
        """
        Record a command execution by alias and return monitor result.
        Returns MonitorResult with action and message, or None if no action needed.
        """
        if not self.config.get('monitoring.enabled', True):
            return None

        # Skip ignored commands
        ignored_commands = self.config.get('monitoring.ignored_commands', [])
        command_base = command.split()[0] if command.split() else command

        if command_base in ignored_commands:
            return None

        # Check if user is already using an optimal alias
        if self._is_using_optimal_alias(command):
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

    def _is_using_optimal_alias(self, command: str) -> bool:
        """Check if the user is already using the most optimal alias for this command."""
        try:
            # Get the first part of the command (the command itself)
            command_parts = command.split()
            if not command_parts:
                return False

            first_part = command_parts[0]

            # Get all aliases
            aliases = self.collector.config.get_aliases_data()

            # Check if the first part is an alias
            if first_part not in aliases:
                return False  # Not using an alias at all

            # Expand the command to see what it would become without aliases
            expanded_command = self.collector._expand_aliases_in_command(command, aliases)

            # Find what the optimal alias would be for the expanded command
            optimal_alias = self.collector.find_alias_for_command(expanded_command)

            if not optimal_alias:
                return True  # No better alias exists

            # Safely unpack the result
            if isinstance(optimal_alias, tuple) and len(optimal_alias) == 2:
                optimal_alias_name, optimal_alias_data = optimal_alias
            else:
                return True  # Couldn't get valid optimal alias

            # If the user is already using the optimal alias, return True
            if first_part == optimal_alias_name:
                return True

            # Check if this alias is equivalent to the optimal one
            # (in case there are multiple aliases for the same command)
            current_alias_command = aliases[first_part].get('command', '')
            optimal_alias_command = optimal_alias_data.get('command', '')

            if current_alias_command == optimal_alias_command:
                return True

            return False

        except (AttributeError, TypeError, KeyError):
            # If anything goes wrong, assume they're not using optimal alias
            return False

    def _generate_alias_suggestion(self, original_command: str, alias_name: str, alias_data: Dict) -> str:
        """Generate a proper alias suggestion that handles recursive commands with arguments."""
        alias_command = alias_data.get('command', '')

        # Try to expand the original command to see what it would become
        try:
            aliases = self.collector.config.get_aliases_data()
            expanded_command = self.collector._expand_aliases_in_command(original_command, aliases)

            # Ensure we got a string back (not a mock object)
            if not isinstance(expanded_command, str):
                expanded_command = original_command
        except (AttributeError, TypeError):
            # Fallback to original command if expansion fails (e.g., in tests with mocks)
            expanded_command = original_command

        # If the expanded command is exactly the alias command, just suggest the alias
        if expanded_command == alias_command:
            return f"'{alias_name}'"

        # If expanded command starts with alias command + space, replace with alias + remaining args
        if expanded_command.startswith(alias_command + ' '):
            args = expanded_command[len(alias_command):]  # Get everything after the base command
            return f"'{alias_name}{args}'"

        # Fallback - just suggest the alias (shouldn't happen with current logic)
        return f"'{alias_name}'"

    def _check_for_action(self, command: str, command_stats: Dict, existing_alias) -> Optional[MonitorResult]:
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
            message = (f"\n🚫🦥 Time to be lazy."
                      f"\nUse {suggested_command} instead of '{command}'"
                      )
            return MonitorResult(MonitorAction.BLOCK, message)

        # Check for notice (show every time when at threshold, before blocking)
        if existing_alias and notice_threshold <= count:
            suggested_command = self._generate_alias_suggestion(command, alias_name, alias_data)
            message = f"\n🦥💡 You can use {suggested_command} instead of '{command}'"
            return MonitorResult(MonitorAction.NOTICE, message)

        return None

    def get_command_stats(self) -> Dict[str, Dict]:
        """Get command usage statistics."""
        return self.config.get_stats_data()

