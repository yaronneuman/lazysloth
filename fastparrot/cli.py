#!/usr/bin/env python3
from email.policy import default
from os import close
from pickle import FALSE

import click
import sys
from pathlib import Path
from .core.config import Config
from .core.installer import Installer
from .collectors.alias_collector import AliasCollector
from .monitors.command_monitor import CommandMonitor

@click.group()
@click.version_option()
def main():
    """FastParrot: Learn and share terminal shortcuts and aliases."""
    pass

@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Target shell')
@click.option('--force', is_flag=True, help='Force reinstallation')
def install(shell, force):
    """Install FastParrot shell integration."""
    installer = Installer()

    if not shell:
        shell = installer.detect_shell()
        click.echo(f"Detected shell: {shell}")

    try:
        installer.install(shell, force=force)
        click.echo(f"✅ FastParrot installed for {shell}")
        click.echo("Restart your shell or run 'source ~/.bashrc' (or equivalent) to activate.")
    except Exception as e:
        click.echo(f"❌ Installation failed: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Target shell')
def uninstall(shell):
    """Uninstall FastParrot shell integration."""
    installer = Installer()

    if not shell:
        shell = installer.detect_shell()
        click.echo(f"Detected shell: {shell}")

    try:
        installer.uninstall(shell)
        click.echo(f"✅ FastParrot uninstalled from {shell}")
        click.echo("Restart your shell or run 'source ~/.bashrc' (or equivalent) to deactivate.")
    except Exception as e:
        click.echo(f"❌ Uninstallation failed: {e}", err=True)
        sys.exit(1)

@main.command()
def collect():
    """Collect existing aliases from shell configuration files."""
    collector = AliasCollector()

    try:
        aliases = collector.collect_all()
        click.echo(f"Found {len(aliases)} aliases:")

        for alias_name, alias_data in aliases.items():
            click.echo(f"  {alias_name}: {alias_data['command']}")

    except Exception as e:
        click.echo(f"❌ Collection failed: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--enabled', type=bool, help='Enable or disable monitoring (true/false)')
@click.option('--action', type=click.Choice(['none', 'notice', 'block']), help='Set monitoring action: none (no action), notice (show suggestions), block (prevent command execution)')
@click.option('--notice-threshold', type=int, help='Threshold for showing notices')
@click.option('--block-threshold', type=int, help='Threshold for blocking commands')
def monitor(enabled, action, notice_threshold, block_threshold):
    """Configure command monitoring settings."""
    config = Config()
    # If no options provided, show current settings and help
    if enabled is None and action is None and notice_threshold is None and block_threshold is None:
        current_enabled = config.get('monitoring.enabled', True)
        current_blocking = config.get('monitoring.blocking_enabled', False)
        current_notice = config.get('monitoring.notice_threshold', 1)
        current_block = config.get('monitoring.blocking_threshold', 5)

        if not current_enabled:
            current_action = "none"
        elif current_blocking:
            current_action = "block"
        else:
            current_action = "notice"

        click.echo("Current monitoring settings:")
        click.echo(f"  Enabled: {current_enabled}")
        click.echo(f"  Action: {current_action}")
        click.echo(f"  Notice threshold: {current_notice}")
        click.echo(f"  Block threshold: {current_block}")
        click.echo()
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if enabled is not None:
        config.set('monitoring.enabled', enabled)
        status = "enabled" if enabled else "disabled"
        click.echo(f"Command monitoring {status}")

    if action is not None:
        if action == 'none':
            config.set('monitoring.blocking_enabled', False)
            click.echo("Monitoring action set to: none (no action taken)")
        elif action == 'notice':
            config.set('monitoring.blocking_enabled', False)
            click.echo("Monitoring action set to: notice (show suggestions)")
        elif action == 'block':
            config.set('monitoring.blocking_enabled', True)
            click.echo("Monitoring action set to: block (prevent command execution)")
            click.echo("⚠️  Warning: Commands will be blocked when threshold is reached!")
            click.echo("   Make sure you know your aliases or switch to notice action if needed.")

    if notice_threshold is not None:
        config.set('monitoring.notice_threshold', notice_threshold)
        click.echo(f"Notice threshold set to {notice_threshold}")

    if block_threshold is not None:
        config.set('monitoring.blocking_threshold', block_threshold)
        click.echo(f"Block threshold set to {block_threshold}")


@main.command()
def status():
    """Show FastParrot status and configuration."""
    config = Config()
    collector = AliasCollector()

    click.echo("FastParrot Status:")
    click.echo(f"  Version: {config.get('version', '1.0.0')}")
    click.echo(f"  Config dir: {config.config_dir}")

    # Show monitoring settings
    enabled = config.get('monitoring.enabled', True)
    blocking_enabled = config.get('monitoring.blocking_enabled', False)

    if not enabled:
        action = "none"
    elif blocking_enabled:
        action = "block"
    else:
        action = "notice"

    click.echo(f"  Monitoring enabled: {enabled}")
    click.echo(f"  Action: {action}")

    # Show monitoring settings
    notice_threshold = config.get('monitoring.notice_threshold', 1)
    blocking_threshold = config.get('monitoring.blocking_threshold', 5)

    click.echo(f"  Notice threshold: {notice_threshold}")
    click.echo(f"  Block threshold: {blocking_threshold}")
    click.echo(f"  Tracking: only commands with aliases")

    aliases = collector.collect_all()
    click.echo(f"  Known aliases: {len(aliases)}")

    # Show alias stats summary
    from .monitors.command_monitor import CommandMonitor
    monitor = CommandMonitor()
    stats = monitor.get_command_stats()
    if stats:
        click.echo(f"  Tracked aliases: {len(stats)}")

if __name__ == '__main__':
    main()