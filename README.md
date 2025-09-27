# LazySloth 🦥

A CLI-first application that learns from your shell configuration and helps you optimize your command-line productivity by tracking command usage and suggesting better alternatives.

## Features

- **Multi-shell support**: Works with Bash and Zsh shells
- **Automatic alias discovery**: Scans and learns from your existing shell configuration files
- **Command monitoring**: Tracks command usage and suggests aliases when available
- **Configurable actions**: Choose between notices (suggestions) or blocking (prevent execution) when aliases are available
- **Smart file watching**: Automatically relearns aliases when configuration files change
- **User alias management**: Add, list, and remove custom aliases through the CLI

## Installation

### From Source

```bash
git clone https://github.com/yaronneuman/lazysloth.git
cd lazysloth
pip install -e .
```

### Install Shell Integration

After installing LazySloth, you need to integrate it with your shell:

```bash
# Auto-detect shell and install
sloth install

# Or specify a shell explicitly
sloth install --shell bash
sloth install --shell zsh
```

Then restart your shell or source your configuration:

```bash
# For bash
source ~/.bashrc

# For zsh
source ~/.zshrc

```

## Usage

### Configure Command Monitoring

View current monitoring settings:

```bash
sloth monitor status
```

Configure monitoring behavior:

```bash
# Set action type: none (disabled), notice (suggestions), or block (prevent execution)
sloth monitor config --action notice

# Set thresholds for notifications and blocking
sloth monitor config --notice-threshold 2 --block-threshold 5

# Enable/disable monitoring entirely
sloth monitor config --enabled true
```

### Check Status

View LazySloth status and configuration:

```bash
sloth status
```

## How It Works

1. **Installation**: LazySloth integrates with your shell by adding hooks:
   - **Bash**: Uses a `trap 'DEBUG'` hook to monitor commands before execution
   - **Zsh**: Creates a custom ZLE widget that intercepts commands on Enter/Return

2. **Alias Discovery**: Automatically scans and learns from your shell configuration files:
   - `.bashrc`, `.bash_aliases`, `.zshrc`, `.zsh_aliases`
   - Custom `.slothrc` file for user-defined aliases

3. **Command Monitoring**: Tracks command usage and matches against known aliases:
   - Configurable thresholds for notices and blocking
   - Smart filtering to avoid self-monitoring LazySloth commands

4. **File Watching**: Monitors configuration files for changes and automatically relearns aliases when they're modified

## Configuration

LazySloth stores its configuration in `~/.config/lazysloth/`:

- `config.yaml` - Main configuration
- `aliases.yaml` - Discovered aliases
- `stats.yaml` - Command usage statistics

### Configuration Options

```yaml
monitoring:
  enabled: true
  notice_threshold: 1        # Show notice after N command uses
  blocking_threshold: 5      # Block command after N uses
  blocking_enabled: true     # Whether to block commands
  ignored_commands: []       # Commands to never monitor

monitored_files:
  bash:
    - ~/.bashrc
    - ~/.bash_aliases
    - ~/.slothrc
  zsh:
    - ~/.zshrc
    - ~/.zsh_aliases
    - ~/.slothrc
```

## Examples

After installation and running a few commands:

```bash
$ git status
💡 LazySloth: You can use 'gs' instead of 'git status'

$ ls -la
⚠️  LazySloth: Command blocked! Use 'll' instead of 'ls -la'
# (if blocking is enabled and threshold reached)
```

## Managing Aliases

You can add, list, and remove custom aliases:

```bash
# Add a new alias
$ sloth alias add gs "git status --porcelain"
✅ Added alias: gs -> git status --porcelain

# List all known aliases
$ sloth alias list
📁 .slothrc:
  gs → git status --porcelain (user_defined)

📁 /home/user/.bashrc:
  ll → ls -la (bash)
  ..  → cd .. (bash)

# Remove an alias (only works for .slothrc aliases)
$ sloth alias rm gs
✅ Removed alias: gs
💡 Alias removed from ~/.slothrc
```

## Manage Monitored Files

Add or remove files from the monitoring list:

```bash
# View monitored files
sloth monitor files

# Add a file to monitor (for a specific shell)
sloth monitor files --shell bash --add ~/.bash_custom

# Remove a file from monitoring
sloth monitor files --shell bash --remove ~/.bash_custom
```

## Architecture

LazySloth is designed with a modular architecture:

- **Core**: Configuration management, installation logic, auto-learning, and file watching
- **Collectors**: Extract aliases from various shell configuration files
- **Monitors**: Command monitoring hooks and suggestion logic
- **CLI**: Click-based command-line interface for all user interactions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0+). See the [LICENSE](LICENSE) file for details.

## Author

Created by Yaron Neuman