# FastParrot Testing Framework

## Overview

FastParrot includes a comprehensive testing framework designed to test all functionality without interfering with the user's environment or actual statistics. The framework provides complete isolation while testing realistic scenarios.

## Key Features

### 🔒 **Complete Environment Isolation**
- Uses temporary directories for all file operations
- Mocks `Path.home()` to point to test directories
- No interference with user's shell configurations
- No impact on actual FastParrot usage statistics
- Automatic cleanup after tests

### 🧪 **Comprehensive Test Coverage**
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and CLI functionality
- **Realistic Scenarios**: Test with actual shell configurations and aliases

### 🛠 **Test Infrastructure**
- Custom fixtures for isolated environments
- Sample shell configurations for realistic testing
- Mock utilities for subprocess and file system operations
- Configurable test runners and CI integration

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_runner.py           # Custom test runner script
├── README.md               # Detailed testing documentation
├── unit/                   # Unit tests for individual components
│   ├── test_config.py      # Configuration management tests
│   ├── test_alias_collector.py  # Alias collection tests
│   ├── test_command_monitor.py  # Command monitoring tests
│   └── test_installer.py   # Shell integration tests
├── integration/            # Integration and CLI tests
│   ├── test_cli.py         # CLI command tests
│   └── test_hook.py        # Hook functionality tests
├── fixtures/               # Test data and sample configurations
│   └── sample_configs.py   # Realistic shell config samples
└── TESTING.md              # This file
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
make install-dev

# Run all tests
make test

# Run specific test types
make test-unit        # Unit tests only
make test-integration # Integration tests only
```

### Using Test Runner

```bash
# Install dependencies
python tests/test_runner.py install-deps

# Run all tests with coverage
python tests/test_runner.py test --coverage

# Run specific types
python tests/test_runner.py test --type unit -v
python tests/test_runner.py test --type integration -v
```

### Using Pytest Directly

```bash
# Install dependencies
pip install -e .[test]

# Run all tests
pytest tests/

# Run with markers
pytest tests/ -m "unit" -v      # Unit tests only
pytest tests/ -m "integration"  # Integration tests only
pytest tests/ -m "not slow"     # Skip slow tests
```

## Environment Isolation Examples

### Configuration Isolation
```python
def test_config_isolation(isolated_config, tmp_path):
    # Config operates in temporary directory
    config = isolated_config
    config.set('monitoring.enabled', False)

    # Changes are saved to test directory only
    assert config.config_dir == tmp_path / "lazysloth_test_config"
    # User's real config is unaffected
```

### Shell Environment Isolation
```python
def test_shell_isolation(mock_home_dir, sample_shell_configs):
    # Shell configs created in temporary directory
    bash_profile = mock_home_dir / '.bash_profile'
    bash_profile.write_text(sample_shell_configs['bash_profile'])

    # Collector operates on test files only
    collector = AliasCollector()
    aliases = collector._parse_bash_zsh_aliases(bash_profile, 'bash')
    # User's real .bash_profile is never touched
```

### Statistics Isolation
```python
def test_statistics_isolation(isolated_config):
    # Statistics stored in test directory only
    stats = {'gs': {'count': 5, 'alias_command': 'git status'}}
    isolated_config.save_stats_data(stats)

    # User's real FastParrot statistics unaffected
```

## Test Categories and Markers

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in complete isolation
- Fast execution (< 1 second per test)
- Mock all external dependencies
- Focus on single responsibility

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- Test CLI commands end-to-end
- Use realistic but isolated environments
- Slower but more comprehensive

### Slow Tests (`@pytest.mark.slow`)
- Tests that take longer to execute
- Can be skipped for quick feedback
- Include complex scenarios

## Sample Test Data

The framework includes realistic sample configurations:

### Shell Configurations
- **Bash**: Common aliases like `ll`, `gs`, `dps`
- **Zsh**: Oh-My-Zsh style with git and kubectl aliases
- **Fish**: Fish-specific syntax with functions

### Aliases Database
- Git shortcuts: `gs` → `git status`, `gc` → `git commit`
- System shortcuts: `ll` → `ls -la`, `..` → `cd ..`
- Docker shortcuts: `dps` → `docker ps`, `dc` → `docker-compose`

### Usage Statistics
- Realistic command usage patterns
- Multiple threshold scenarios
- Learning progression simulation

## Key Test Fixtures

### Environment Fixtures
- `isolated_config_dir`: Temporary config directory
- `mock_home_dir`: Isolated home directory with shell structure
- `populated_shell_configs`: Pre-configured shell files

### Data Fixtures
- `sample_aliases`: Realistic alias definitions
- `command_stats_sample`: Sample usage statistics
- `sample_shell_configs`: Complete shell configuration files

### Mock Fixtures
- `mock_subprocess`: Mocked subprocess calls
- `mock_shutil_which`: Predictable Python path discovery
- `mock_datetime`: Consistent timestamps for testing

## Safety Guarantees

### What Tests Never Touch
✅ User's actual home directory files
✅ Real shell configuration files (.bash_profile, .zshrc, etc.)
✅ Actual FastParrot configuration and statistics
✅ System-wide installations or modifications

### What Tests Create/Modify
📁 Temporary directories (automatically cleaned up)
📄 Test-specific configuration files
🧪 Isolated mock environments

## Continuous Integration

Tests run automatically on:
- Pull requests to main/develop branches
- Direct pushes to main/develop branches
- Multiple Python versions (3.8-3.11)
- Multiple platforms (Ubuntu, macOS)

### CI Pipeline
1. **Linting**: Code style and formatting checks
2. **Unit Tests**: Fast component-level tests
3. **Integration Tests**: CLI and interaction tests
4. **Coverage**: Minimum coverage requirements
5. **Security**: Dependency and code security scanning

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import patch
from lazysloth.component import Component

@pytest.mark.unit
class TestComponent:
    def test_feature(self, isolated_config):
        # Test isolated component functionality
        component = Component(config=isolated_config)
        result = component.method()
        assert result == expected
```

### Integration Test Template
```python
import pytest
from click.testing import CliRunner
from lazysloth.cli import command

@pytest.mark.integration
class TestCLICommand:
    def test_command(self, test_environment):
        # Set up realistic environment
        test_environment.create_shell_config('bash', 'alias ll="ls -la"')

        # Test CLI command
        runner = CliRunner()
        result = runner.invoke(command, ['--option'])
        assert result.exit_code == 0
```

## Best Practices

### Test Design
1. **Isolation First**: Always use fixtures for environment isolation
2. **Realistic Data**: Use realistic shell configs and aliases
3. **Error Coverage**: Test both success and failure scenarios
4. **Fast Units**: Keep unit tests under 1 second each
5. **Clear Names**: Use descriptive test method names

### Debugging
1. **Verbose Output**: Use `-v` flag for detailed test output
2. **Specific Tests**: Run individual test methods for debugging
3. **Coverage Reports**: Use coverage to identify untested code
4. **Temporary Files**: Inspect temp directories for debugging

## Performance

### Test Execution Times
- **Unit Tests**: ~0.1-0.5 seconds each
- **Integration Tests**: ~0.5-2 seconds each
- **Full Suite**: ~30-60 seconds total

### Optimization
- Parallel test execution where possible
- Efficient fixture reuse
- Minimal file I/O operations
- Strategic use of mocks vs real operations

## Coverage Goals

- **Minimum**: 85% overall coverage
- **Core Components**: 95%+ coverage
- **CLI Commands**: 90%+ coverage
- **Error Handling**: 100% coverage

## Conclusion

The FastParrot testing framework provides:

✅ **Safety**: Complete isolation from user environment
✅ **Realism**: Tests with actual shell configurations and workflows
✅ **Comprehensiveness**: Unit and integration test coverage
✅ **Maintainability**: Clean, documented, and extensible test code
✅ **CI/CD Ready**: Automated testing across platforms and Python versions

This ensures FastParrot is thoroughly tested without any risk to user data or configurations.