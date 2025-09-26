#!/usr/bin/env python3
from email.policy import default
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
@click.option('--enable/--disable', default=True, help='Enable or disable monitoring')
@click.option('--notice-threshold', type=int, help='Threshold for showing notices')
@click.option('--blocking-threshold', type=int, help='Threshold for blocking commands')
@click.option('--enable-blocking/--disable-blocking', default=True, help='Enable/disable command blocking')
def monitor(enable, notice_threshold, blocking_threshold, enable_blocking):
    """Configure command monitoring settings."""
    config = Config()

    if enable is not None:
        config.set('monitoring.enabled', enable)
        status = "enabled" if enable else "disabled"
        click.echo(f"Command monitoring {status}")

    if notice_threshold is not None:
        config.set('monitoring.notice_threshold', notice_threshold)
        click.echo(f"Notice threshold set to {notice_threshold}")

    if blocking_threshold is not None:
        config.set('monitoring.blocking_threshold', blocking_threshold)
        click.echo(f"Blocking threshold set to {blocking_threshold}")

    if enable_blocking is not None:
        config.set('monitoring.blocking_enabled', enable_blocking)
        status = "enabled" if enable_blocking else "disabled"
        click.echo(f"Command blocking {status}")

        if enable_blocking:
            click.echo("⚠️  Warning: Commands will be blocked when threshold is reached!")
            click.echo("   Make sure you know your aliases or disable blocking if needed.")


@main.command()
def status():
    """Show FastParrot status and configuration."""
    config = Config()
    collector = AliasCollector()

    click.echo("FastParrot Status:")
    click.echo(f"  Version: {config.get('version', '1.0.0')}")
    click.echo(f"  Config dir: {config.config_dir}")
    click.echo(f"  Monitoring: {'enabled' if config.get('monitoring.enabled', True) else 'disabled'}")

    # Show monitoring settings
    notice_threshold = config.get('monitoring.notice_threshold', 1)
    blocking_threshold = config.get('monitoring.blocking_threshold', 3)
    blocking_enabled = config.get('monitoring.blocking_enabled', False)

    click.echo(f"  Notice threshold: {notice_threshold}")
    click.echo(f"  Blocking threshold: {blocking_threshold}")
    click.echo(f"  Blocking: {'enabled' if blocking_enabled else 'disabled'}")
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