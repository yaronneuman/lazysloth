#!/usr/bin/env python3

import click
import sys
from pathlib import Path
from .core.config import Config
from .core.installer import Installer
from .core.auto_learner import AutoLearner

@click.group()
@click.version_option()
def main():
    """LazySloth: Learn and share terminal shortcuts and aliases.

    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⠖⢶⣦⣄⡀⠀⢀⣴⣶⠟⠓⣶⣦⣄⡀⠀⠀⠀⠀⠀⣀⣤⣤⣀⡀⠀⠀⢠⣤⣤⣄⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⡿⣿⡄⠀⣿⠈⢻⣤⣾⠏⠀⠀⠀⠈⢷⡈⠻⣦⡀⠀⣠⣾⠟⠋⠀⠙⣿⣶⣴⠏⢠⣿⠋⠉⣷⡄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⠁⠈⣿⠀⣿⠃⢸⣿⡏⠀⠀⠀⠀⠀⢸⡻⣦⣹⣇⢠⣿⠃⠀⠀⠀⠀⠘⣇⠙⣧⡿⢁⣴⠞⠛⢿⡆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⠃⠀⠀⢹⣷⣿⣰⡿⢿⡇⠀⠀⠀⠀⠀⢸⢻⣜⣷⣿⣿⡇⠀⠀⠀⠀⠀⠀⣟⣷⣹⣁⡞⠁⠀⠀⠘⣿⡄⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣿⡟⠀⠀⠀⠈⠉⢹⡟⠁⢸⡇⠀⠀⠀⠀⠀⢸⡆⠙⠃⢀⣿⠀⠀⠀⠀⠀⠀⠀⣿⠛⣿⠛⠀⠀⠀⠀⠀⢹⡇⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠈⣇⠀⢸⡇⠀⠀⠀⠀⠀⠀⣇⠀⠀⠘⣿⡄⠀⠀⠀⠀⠀⠀⢹⡀⢸⡇⠀⠀⠀⠀⠀⠘⣿⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⣿⡀⢸⣷⠀⠀⠀⠀⠀⠀⢻⡆⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⠸⣧⢸⣿⠀⠀⠀⠀⠀⠀⢿⡆
⠀⠀⠀⠀⣠⣤⣶⣶⣿⠿⢶⣶⣤⣄⠀⠀⠘⡇⠀⢻⡄⠀⠀⠀⠀⠀⠀⢳⡀⠀⢻⣧⠀⠀⠀⠀⠀⠀⠀⢿⣾⣿⠀⠀⠀⠀⠀⠀⢸⡇
⠀⠀⣴⣿⢟⣯⣭⡎⠀⠀⢀⣤⡟⠻⣷⣄⠀⢹⡄⢸⣇⠀⠀⠀⠀⠀⠀⠈⣷⡀⠘⣿⡄⠀⠀⠀⠀⠀⠀⠀⢿⡏⠀⠀⠀⠀⠀⠀⢸⣧
⢀⣾⢏⠞⠉⠀⠀⠀⠀⠀⠻⢿⣿⣀⠼⢿⣶⣶⣷⡀⣿⡀⠀⠀⠀⠀⠀⠀⢸⣇⠀⢻⣷⠀⠀⠀⠀⠀⠀⠀⠈⢿⣆⠀⠀⠀⠀⠀⢸⣿
⣸⡷⠋⠀⠀⠀⠀⣠⣶⣿⠦⣤⠄⠀⠀⠀⣿⣿⣦⡀⣿⠇⠀⠀⠀⠀⠀⠀⠀⢻⡀⠈⣿⡆⠀⠀⠀⠀⠀⠀⠀⠈⢻⣆⠀⠀⠀⠀⢸⣿
⣿⢁⡴⣾⣿⡆⠀⠙⢛⣡⡾⠋⠀⠀⠀⢠⠇⠈⠛⣿⠏⠀⠀⠀⠀⠀⠀⠰⣄⠸⡗⠛⢻⣿⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣆⠀⠀⠀⣼⣿
⢿⡞⠀⠈⢉⡇⠉⠉⠉⠉⠀⠀⠀⠀⣠⠊⠀⢀⡾⠋⠀⠀⠀⠀⠀⢀⡀⠀⣿⠳⠇⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⣿⡇
⠸⣷⠀⢠⠎⠀⠀⠀⠀⠀⠀⣀⠴⠋⠀⠖⠚⠋⠀⠀⠀⠀⠀⢀⡄⢸⣷⡀⣿⠀⠀⠀⣸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⢰⣿⠇
⠀⢻⣷⣯⣀⣀⣀⣀⣠⠤⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠛⠿⣷⠇⠀⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⣾⡟⠀
⠀⠈⢻⣷⡉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠃⠀
⠀⠀⠀⢻⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⠃⠀⠀
⠀⠀⠀⠀⠙⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⠇⠀⠀⠀
⠀⠀⠀⠀⠀⠈⠻⣿⣷⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⡿⠃⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠛⢿⣿⣶⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣾⠟⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⢿⣿⣶⣦⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⣴⣶⣿⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⡻⠿⠿⣿⣿⣷⣶⣶⣶⣶⣶⣶⣶⣶⣶⣿⣿⠿⠿⢛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    pass

@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Target shell')
@click.option('--force', is_flag=True, help='Force reinstallation')
def install(shell, force):
    """Install LazySloth shell integration."""
    installer = Installer()

    if not shell:
        shell = installer.detect_shell()
        click.echo(f"Detected shell: {shell}")

    try:
        if force:
            click.echo("🧹 Cleaning previous LazySloth data (aliases, stats, file tracking)...")

        installer.install(shell, force=force)
        click.echo(f"✅ LazySloth installed for {shell}")

        # Automatically learn aliases from the detected shell
        learner = AutoLearner()
        click.echo(f"🎓 Learning aliases from {shell} configuration files...")
        results = learner.learn_from_monitored_files(shell)

        total_learned = results['learned'] + results['updated']
        if total_learned > 0:
            click.echo(f"   📚 Learned {total_learned} aliases")
        else:
            click.echo("   No aliases found to learn")

        click.echo("Restart your shell or run 'source ~/.bashrc' (or equivalent) to activate.")
    except Exception as e:
        click.echo(f"❌ Installation failed: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Target shell')
def uninstall(shell):
    """Uninstall LazySloth shell integration."""
    installer = Installer()

    if not shell:
        shell = installer.detect_shell()
        click.echo(f"Detected shell: {shell}")

    try:
        click.echo("🧹 Removing LazySloth integration and cleaning data (aliases, stats, file tracking)...")
        installer.uninstall(shell)
        click.echo(f"✅ LazySloth uninstalled from {shell}")
        click.echo("💡 Configuration settings preserved in ~/.config/lazysloth/config.yaml")
        click.echo("💡 User aliases preserved in ~/.slothrc (will not be used until reinstalled)")
        click.echo("Restart your shell or run 'source ~/.bashrc' (or equivalent) to deactivate.")
    except Exception as e:
        click.echo(f"❌ Uninstallation failed: {e}", err=True)
        sys.exit(1)

@main.command()
@click.argument('alias_name', required=True)
@click.argument('command', required=True)
def add(alias_name, command):
    """Add a new alias. Usage: sloth add <alias> "command"

    Example: sloth add gs "git status --porcelain"
    """
    if not alias_name or not command:
        click.echo("❌ Both alias name and command are required", err=True)
        sys.exit(1)

    try:
        config = Config()

        # Check if alias already exists in LazySloth's database
        aliases = config.get_aliases_data()
        if alias_name in aliases:
            existing_command = aliases[alias_name].get('command', '')
            if existing_command == command:
                click.echo(f"✅ Alias '{alias_name}' already exists with the same command")
                return
            else:
                click.echo(f"⚠️  Alias '{alias_name}' already exists with command: {existing_command}")
                if not click.confirm("Do you want to overwrite it?"):
                    click.echo("Operation cancelled")
                    return

        # Add the new alias to LazySloth's database
        aliases[alias_name] = {
            'command': command,
            'shell': 'user_defined',
            'source_file': '.slothrc',
            'type': 'alias'
        }
        config.save_aliases_data(aliases)

        # Add the alias to .slothrc file
        from .core.slothrc import SlothRC
        slothrc = SlothRC()
        slothrc.add_alias(alias_name, command)

        click.echo(f"✅ Added alias: {alias_name} -> {command}")
        click.echo(f"💡 Alias added to ~/.slothrc and will be available in new shell sessions")

    except Exception as e:
        click.echo(f"❌ Failed to add alias: {e}", err=True)
        sys.exit(1)


@main.group()
def monitor():
    """Configure command monitoring and manage monitored files."""
    pass

@monitor.command()
def status():
    """Show current monitoring settings."""
    config = Config()
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

@monitor.command()
@click.option('--enabled', type=bool, help='Enable or disable monitoring (true/false)')
@click.option('--action', type=click.Choice(['none', 'notice', 'block']), help='Set monitoring action: none (no action), notice (show suggestions), block (prevent command execution)')
@click.option('--notice-threshold', type=int, help='Threshold for showing notices')
@click.option('--block-threshold', type=int, help='Threshold for blocking commands')
def config(enabled, action, notice_threshold, block_threshold):
    """Configure command monitoring settings."""
    config_obj = Config()

    # If no options provided, show current settings and help
    if enabled is None and action is None and notice_threshold is None and block_threshold is None:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if enabled is not None:
        config_obj.set('monitoring.enabled', enabled)
        status = "enabled" if enabled else "disabled"
        click.echo(f"Command monitoring {status}")

    if action is not None:
        if action == 'none':
            config_obj.set('monitoring.blocking_enabled', False)
            click.echo("Monitoring action set to: none (no action taken)")
        elif action == 'notice':
            config_obj.set('monitoring.blocking_enabled', False)
            click.echo("Monitoring action set to: notice (show suggestions)")
        elif action == 'block':
            config_obj.set('monitoring.blocking_enabled', True)
            click.echo("Monitoring action set to: block (prevent command execution)")
            click.echo("⚠️  Warning: Commands will be blocked when threshold is reached!")
            click.echo("   Make sure you know your aliases or switch to notice action if needed.")

    if notice_threshold is not None:
        config_obj.set('monitoring.notice_threshold', notice_threshold)
        click.echo(f"Notice threshold set to {notice_threshold}")

    if block_threshold is not None:
        config_obj.set('monitoring.blocking_threshold', block_threshold)
        click.echo(f"Block threshold set to {block_threshold}")

@monitor.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), help='Show files for specific shell')
@click.option('--add', help='Add file to monitoring list (requires --shell)')
@click.option('--remove', help='Remove file from monitoring list (requires --shell)')
def files(shell, add, remove):
    """Manage monitored configuration files."""
    learner = AutoLearner()

    if add and shell:
        # Add file to monitored list
        if learner.add_monitored_file(shell, add):
            click.echo(f"✅ Added {add} to {shell} monitored files")
            # Automatically learn from the new file
            click.echo("🎓 Learning aliases from new file...")
            results = learner.learn_from_monitored_files(shell)
            if results['learned'] > 0:
                click.echo(f"   📚 Learned {results['learned']} new aliases")
        else:
            click.echo(f"⚠️  File {add} is already monitored for {shell}")

    elif remove and shell:
        # Remove file from monitored list
        if learner.remove_monitored_file(shell, remove):
            click.echo(f"✅ Removed {remove} from {shell} monitored files")
        else:
            click.echo(f"⚠️  File {remove} not found in {shell} monitored files")

    elif add or remove:
        click.echo("❌ --add and --remove require --shell option", err=True)
        sys.exit(1)

    else:
        # Show current monitored files
        monitored = learner.get_monitored_files(shell)

        if shell:
            files = monitored.get(shell, [])
            click.echo(f"Monitored files for {shell}:")
            if files:
                for file_path in files:
                    exists = "✅" if Path(file_path).exists() else "❌"
                    click.echo(f"  {exists} {file_path}")
            else:
                click.echo("  None configured")
        else:
            click.echo("Monitored files by shell:")
            for shell_name, files in monitored.items():
                click.echo(f"  {shell_name}:")
                if files:
                    for file_path in files:
                        exists = "✅" if Path(file_path).exists() else "❌"
                        click.echo(f"    {exists} {file_path}")
                else:
                    click.echo("    None configured")


@main.command()
def status():
    """Show LazySloth status and configuration."""
    config = Config()
    learner = AutoLearner()

    click.echo("LazySloth Status:")
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

    # Show alias info
    aliases = config.get_aliases_data()
    click.echo(f"  Known aliases: {len(aliases)}")

    # Show monitored files summary
    monitored = learner.get_monitored_files()
    total_monitored_files = sum(len(files) for files in monitored.values())
    click.echo(f"  Monitored files: {total_monitored_files}")

    # Show alias stats summary
    from .monitors.command_monitor import CommandMonitor
    monitor = CommandMonitor()
    stats = monitor.get_command_stats()
    if stats:
        click.echo(f"  Tracked aliases: {len(stats)}")

if __name__ == '__main__':
    main()