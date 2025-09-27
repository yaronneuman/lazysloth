# FastParrot Test Suite

This directory contains the comprehensive test suite for FastParrot, designed to test functionality without interfering with the user's environment or actual statistics.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_runner.py           # Custom test runner script
├── README.md               # This file
├── unit/                   # Unit tests
│   ├── test_config.py      # Config class tests
│   ├── test_alias_collector.py  # AliasCollector tests
│   ├── test_command_monitor.py  # CommandMonitor tests
│   └── test_installer.py   # Installer tests
├── integration/            # Integration tests
│   ├── test_cli.py         # CLI command tests
│   └── test_hook.py        # Hook functionality tests
└── fixtures/               # Test data and fixtures
    └── sample_configs.py   # Sample shell configurations
```

## Environment Isolation

The test framework is designed with complete environment isolation:

### Configuration Isolation
- Uses temporary directories for all configuration files
- Mocks `Path.home()` to point to test directories
- Creates isolated config directories that don't affect user data

### Shell Environment Isolation
- Mocks shell configuration files in temporary locations
- Provides realistic sample configurations for testing
- Tests shell integration without modifying user's actual shell configs

### Statistics Isolation
- All command statistics are stored in test-specific locations
- No interference with actual FastParrot usage statistics
- Complete isolation of monitoring and learning data

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **Config Tests**: Configuration management, file operations, data persistence
- **AliasCollector Tests**: Alias discovery from shell configs, parsing logic
- **CommandMonitor Tests**: Command monitoring, suggestion logic, statistics tracking
- **Installer Tests**: Shell integration installation/uninstallation

### Integration Tests (`tests/integration/`)

Test component interactions and CLI functionality:

- **CLI Tests**: All command-line interface operations
- **Hook Tests**: Command hook functionality and shell integration

## Running Tests

### Using Make (Recommended)

```bash
# Install development dependencies
make install-dev

# Run all tests with coverage
make test

# Run specific test types
make test-unit
make test-integration

# Run linting
make lint

# Run all checks
make check
```

### Using the Test Runner

```bash
# Install test dependencies
python tests/test_runner.py install-deps

# Run all tests
python tests/test_runner.py test

# Run specific test types
python tests/test_runner.py test --type unit
python tests/test_runner.py test --type integration

# Run with coverage
python tests/test_runner.py test --coverage

# Run with specific markers
python tests/test_runner.py test -m "unit"
python tests/test_runner.py test -m "integration"
```

### Using Pytest Directly

```bash
# Install dependencies first
pip install -e .[test]

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=lazysloth --cov-report=term-missing

# Run specific test files
pytest tests/unit/test_config.py -v

# Run tests with specific markers
pytest tests/ -m "unit" -v
pytest tests/ -m "integration" -v
pytest tests/ -m "slow" -v
```

## Test Markers

The test suite uses pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, more comprehensive)
- `@pytest.mark.slow` - Tests that take longer to run

## Fixtures and Test Utilities

### Key Fixtures (in `conftest.py`)

- `isolated_config_dir` - Temporary configuration directory
- `mock_home_dir` - Mock home directory with shell structure
- `isolated_config` - Config instance using test directories
- `sample_aliases` - Pre-defined alias data for testing
- `populated_shell_configs` - Shell configs with realistic content
- `mock_subprocess` - Mocked subprocess calls
- `command_stats_sample` - Sample command usage statistics

### Test Environment Helper

The `TestEnvironment` class provides utilities for setting up realistic test scenarios:

```python
def test_example(test_environment):
    # Create shell configs
    test_environment.create_shell_config('bash', 'alias ll="ls -la"')
    test_environment.create_fish_function('gs', 'git status $argv')

    # Test functionality with isolated environment
```

## Writing New Tests

### Adding Unit Tests

1. Create test file in `tests/unit/`
2. Use `@pytest.mark.unit` decorator
3. Use isolation fixtures to avoid side effects
4. Test single component functionality

```python
import pytest
from lazysloth.core.config import Config

@pytest.mark.unit
class TestNewFeature:
    def test_feature(self, isolated_config):
        # Test implementation
        pass
```

### Adding Integration Tests

1. Create test file in `tests/integration/`
2. Use `@pytest.mark.integration` decorator
3. Test component interactions
4. Use realistic scenarios

```python
import pytest
from click.testing import CliRunner

@pytest.mark.integration
class TestNewCLIFeature:
    def test_cli_command(self, test_environment):
        # Test implementation
        pass
```

## Test Data and Fixtures

Sample configurations in `tests/fixtures/sample_configs.py` include:

- Realistic bash/zsh/fish configuration files
- Common aliases and functions
- Shell configurations with FastParrot already installed
- Sample statistics and aliases data

## Coverage Goals

The test suite aims for:
- Minimum 85% code coverage
- 100% coverage of core functionality
- Comprehensive testing of error conditions
- Testing of all CLI commands and options

## Continuous Integration

Tests run automatically on:
- All pull requests
- Pushes to main/develop branches
- Multiple Python versions (3.8-3.11)
- Multiple operating systems (Ubuntu, macOS)

## Best Practices

1. **Isolation**: Always use fixtures to isolate test environments
2. **Realistic Data**: Use realistic sample configurations and data
3. **Error Testing**: Test both success and failure scenarios
4. **Performance**: Keep unit tests fast, mark slow tests appropriately
5. **Maintenance**: Keep tests simple and maintainable

## Debugging Tests

To debug failing tests:

```bash
# Run specific test with verbose output
pytest tests/unit/test_config.py::TestConfig::test_specific_method -v -s

# Run with pdb debugger
pytest tests/unit/test_config.py --pdb

# Show local variables in traceback
pytest tests/unit/test_config.py --tb=long -v
```