# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LazySloth is a CLI-first application that learns from shell configurations and helps optimize command-line productivity by tracking command usage and suggesting better alternatives. It monitors shell commands and suggests aliases when available, supporting Bash and Zsh shells.

## Development Commands

### Setup
```bash
# Install in development mode
make install-dev

# Basic installation
make install
```

### Testing
```bash
# Run all tests with coverage
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-fast          # Skip slow tests
make quick-test         # Unit tests without coverage

# Using custom test runner
python tests/test_runner.py test --coverage
python tests/test_runner.py test --type unit -v
```

### Code Quality
```bash
# Run linting
make lint

# Format code
make format

# Check formatting only
make format-check

# Run all checks
make check              # lint + test
```

### Development Workflow
```bash
# Complete CI pipeline
make ci                 # install-dev + lint + test

# Build package
make build

# Clean artifacts
make clean
```

## Architecture

LazySloth follows a modular architecture with clear separation of concerns:

### Core Modules (`lazysloth/core/`)
- **config.py**: Configuration management with YAML storage in `~/.config/lazysloth/`
- **installer.py**: Shell integration logic for Bash/Zsh hook installation
- **auto_learner.py**: Automatic alias discovery and learning system
- **file_watcher.py**: Monitors shell config files for changes using watchdog
- **slothrc.py**: Manages user-defined aliases in `.slothrc` file

### Collectors (`lazysloth/collectors/`)
- **alias_collector.py**: Extracts aliases from various shell configuration files

### Monitors (`lazysloth/monitors/`)
- **command_monitor.py**: Core command monitoring and suggestion logic
- **hook.py**: Shell hook implementation for command interception

### CLI (`lazysloth/cli.py`)
- Click-based command-line interface with subcommands:
  - `sloth install` - Shell integration
  - `sloth monitor` - Configure monitoring behavior
  - `sloth alias` - Manage aliases
  - `sloth status` - View statistics

## Shell Integration

LazySloth integrates differently with each shell:
- **Bash**: Uses `trap 'DEBUG'` hook to monitor commands before execution
- **Zsh**: Creates custom ZLE widget that intercepts commands on Enter/Return

Shell integration files are stored in `lazysloth/shells/` and installed to user's shell config.

## Configuration

Configuration is stored in `~/.config/lazysloth/`:
- `config.yaml` - Main configuration with monitoring settings
- `aliases.yaml` - Discovered aliases from shell configs
- `stats.yaml` - Command usage statistics

## Testing Framework

The project uses a comprehensive testing framework with complete environment isolation:

### Test Structure
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration and CLI tests
- `tests/fixtures/` - Test data and sample configurations

### Key Features
- Complete environment isolation using temporary directories
- Mocks `Path.home()` to avoid touching user's real configurations
- Realistic sample shell configurations for testing
- Coverage requirements: minimum 50% (configured in pyproject.toml)

### Test Markers
- `@pytest.mark.unit` - Fast isolated component tests
- `@pytest.mark.integration` - End-to-end CLI tests
- `@pytest.mark.slow` - Longer-running tests

## Dependencies

Key dependencies from pyproject.toml:
- **click>=8.0.0** - CLI framework
- **colorama>=0.4.4** - Terminal colors
- **watchdog>=2.1.0** - File system monitoring
- **psutil>=5.8.0** - Process utilities
- **pyyaml>=6.0** - YAML configuration

Test dependencies:
- **pytest>=7.0.0** with coverage and mock plugins

## Development Notes

- Entry point: `sloth` command (configured in pyproject.toml scripts)
- Python 3.8+ required
- Uses setuptools build system
- AGPL-3.0+ license
- Shell script templates in `lazysloth/shells/` directory are included in package data