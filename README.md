# LazySloth 🦥

A CLI-first application that helps developers and terminal users improve their productivity by sharing shortcuts, aliases, and scripts with each other.

## Features

- **Multi-shell support**: Works with Bash and Zsh shells
- **Alias collection**: Automatically discovers existing aliases from your shell configuration
- **Smart suggestions**: Learn when to use aliases through intelligent command monitoring
- **Muscle memory training**: Get reminded about available shortcuts to build better habits

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

### Collect Existing Aliases

Discover aliases already defined in your shell configurations:

```bash
sloth collect
```

### Monitor Command Usage

Enable command monitoring (enabled by default):

```bash
sloth monitor --enable
```

Disable monitoring:

```bash
sloth monitor --disable
```

### Check Status

View FastParrot status and configuration:

```bash
sloth status
```

## How It Works

1. **Installation**: LazySloth integrates with your shell by adding a command hook that runs before each command execution.

2. **Alias Collection**: It scans your shell configuration files (`.bashrc`, `.zshrc`, etc.) to discover existing aliases.

3. **Command Monitoring**: Every command you run is monitored. When you use a command that has an available alias, LazySloth suggests using the alias instead.

4. **Learning**: After seeing the same command multiple times (default: 3 times), LazySloth will suggest creating an alias or remind you about an existing one.

## Configuration

LazySloth stores its configuration in `~/.config/lazysloth/`:

- `config.yaml` - Main configuration
- `aliases.yaml` - Discovered aliases
- `stats.yaml` - Command usage statistics

### Configuration Options

```yaml
monitoring:
  enabled: true
  suggestion_threshold: 3  # Show suggestion after N uses

aliases:
  auto_learn: true
  share_enabled: false

ui:
  colors: true
  notifications: true
```

## Examples

After installation and running a few commands:

```bash
$ git status
💡 You can use 'gs' instead of 'git status'

$ docker ps
💡 Consider creating an alias: alias dps='docker ps'

$ ls -la
💡 You can use 'll' instead of 'ls -la'
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
```

## Architecture

LazySloth is designed with a modular architecture:

- **Core**: Configuration management and installation logic
- **Collectors**: Extract aliases from various shell configurations
- **Monitors**: Track command usage and provide suggestions
- **Utils**: Shared utilities and helpers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0+). See the [LICENSE](LICENSE) file for details.

## Author

Created by Yaron Neuman