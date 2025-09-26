#!/usr/bin/env python3
"""
Command hook module - called by shell integration to monitor commands.
This is invoked before each command execution.
"""

import sys
import os
from .command_monitor import CommandMonitor

def main():
    """Main entry point for the command hook."""
    if len(sys.argv) < 2:
        return

    # Get the command from arguments
    command = ' '.join(sys.argv[1:]).strip()

    # Skip empty commands or FastParrot commands
    if not command or command.startswith('fastparrot') or 'fastparrot' in command:
        sys.exit(0)  # Allow command to proceed

    try:
        monitor = CommandMonitor()
        message = monitor.record_command(command)
        if message:
            # Print message to stdout for visibility
            print(f"{message}", flush=True)

            # If this is a blocking message, exit with error to prevent command execution
            if "Command blocked!" in message:
                sys.exit(1)
    except Exception as e:
        print("FastParrot failed:", e)
        # Silently fail - never block user commands due to FastParrot errors
        pass

    # If no message or non-blocking message, exit with success (allow command)
    sys.exit(0)


if __name__ == '__main__':
    main()