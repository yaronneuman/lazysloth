"""
Test configuration and shared fixtures for FastParrot tests.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
import pytest
import yaml

from fastparrot.core.config import Config


@pytest.fixture
def isolated_config_dir(tmp_path):
    """Create an isolated configuration directory for testing."""
    config_dir = tmp_path / "fastparrot_test_config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_home_dir(tmp_path):
    """Create a mock home directory with shell config files."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Create shell config directories
    (home_dir / ".config" / "fish").mkdir(parents=True)
    (home_dir / ".config" / "fish" / "functions").mkdir(parents=True)

    return home_dir


@pytest.fixture
def isolated_config(isolated_config_dir, mock_home_dir):
    """Create a Config instance that uses isolated directories."""
    with patch.object(Path, 'home', return_value=mock_home_dir):
        with patch.object(Config, '__init__', lambda self: None):
            config = Config()
            config.config_dir = isolated_config_dir
            config.config_file = isolated_config_dir / 'config.yaml'
            config.aliases_file = isolated_config_dir / 'aliases.yaml'
            config.stats_file = isolated_config_dir / 'stats.yaml'
            config._config = config._default_config()
            return config


@pytest.fixture
def sample_aliases():
    """Provide sample aliases for testing."""
    return {
        'gs': {
            'command': 'git status',
            'shell': 'zsh',
            'source_file': '/home/user/.zshrc',
            'type': 'alias'
        },
        'll': {
            'command': 'ls -la',
            'shell': 'bash',
            'source_file': '/home/user/.bashrc',
            'type': 'alias'
        },
        'dps': {
            'command': 'docker ps',
            'shell': 'zsh',
            'source_file': '/home/user/.zshrc',
            'type': 'alias'
        },
        'gst': {
            'command': 'git status',
            'shell': 'fish',
            'source_file': '/home/user/.config/fish/config.fish',
            'type': 'alias'
        }
    }


@pytest.fixture
def sample_shell_configs():
    """Provide sample shell configuration file contents."""
    return {
        'bashrc': '''
# Basic bash configuration
export PATH=$HOME/bin:$PATH

# Aliases
alias ll='ls -la'
alias gs='git status'
alias gd='git diff'
alias ..='cd ..'

# Functions
function mkcd() {
    mkdir -p "$1" && cd "$1"
}
''',
        'zshrc': '''
# Zsh configuration
export ZSH="$HOME/.oh-my-zsh"

# Aliases
alias gs="git status"
alias gp="git push"
alias gc="git commit"
alias dps="docker ps"
alias ll="ls -la"

# Custom aliases
alias tmux='tmux -2'
alias vim='nvim'
''',
        'fish_config': '''
# Fish configuration
set -gx PATH $HOME/bin $PATH

# Aliases
alias ll 'ls -la'
alias gs 'git status'
alias gc 'git commit'

# Abbreviations (Fish-specific)
abbr gp 'git push'
abbr gd 'git diff'
''',
        'fish_function_ll': '''
function ll --description 'List files in long format'
    ls -la $argv
end
''',
        'fish_function_gs': '''
function gs --description 'Git status shortcut'
    git status $argv
end
'''
    }


@pytest.fixture
def populated_shell_configs(mock_home_dir, sample_shell_configs):
    """Create shell config files with sample content."""
    # Create bash config
    bashrc = mock_home_dir / '.bashrc'
    bashrc.write_text(sample_shell_configs['bashrc'])

    # Create zsh config
    zshrc = mock_home_dir / '.zshrc'
    zshrc.write_text(sample_shell_configs['zshrc'])

    # Create fish config
    fish_config = mock_home_dir / '.config' / 'fish' / 'config.fish'
    fish_config.write_text(sample_shell_configs['fish_config'])

    # Create fish functions
    functions_dir = mock_home_dir / '.config' / 'fish' / 'functions'
    (functions_dir / 'll.fish').write_text(sample_shell_configs['fish_function_ll'])
    (functions_dir / 'gs.fish').write_text(sample_shell_configs['fish_function_gs'])

    return {
        'bashrc': bashrc,
        'zshrc': zshrc,
        'fish_config': fish_config,
        'fish_functions': functions_dir
    }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls to avoid actual shell commands."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        yield mock_run


@pytest.fixture
def mock_shutil_which():
    """Mock shutil.which to return predictable python path."""
    with patch('shutil.which') as mock_which:
        mock_which.return_value = '/usr/bin/python3'
        yield mock_which


@pytest.fixture
def command_stats_sample():
    """Provide sample command statistics data."""
    return {
        'gs': {
            'count': 5,
            'first_seen': '2024-01-01T10:00:00',
            'last_seen': '2024-01-01T15:00:00',
            'alias_command': 'git status'
        },
        'll': {
            'count': 2,
            'first_seen': '2024-01-01T11:00:00',
            'last_seen': '2024-01-01T14:00:00',
            'alias_command': 'ls -la'
        }
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime to ensure consistent test results."""
    from datetime import datetime
    mock_dt = datetime(2024, 1, 1, 12, 0, 0)
    with patch('fastparrot.monitors.command_monitor.datetime') as mock:
        mock.now.return_value = mock_dt
        yield mock


class TestEnvironment:
    """Helper class to set up and manage test environments."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.home_dir = tmp_path / "home"
        self.config_dir = tmp_path / "config"
        self.setup_directories()

    def setup_directories(self):
        """Set up the basic directory structure."""
        self.home_dir.mkdir()
        self.config_dir.mkdir()
        (self.home_dir / ".config" / "fish").mkdir(parents=True)
        (self.home_dir / ".config" / "fish" / "functions").mkdir(parents=True)

    def create_shell_config(self, shell: str, content: str):
        """Create a shell configuration file with the given content."""
        if shell == 'bash':
            config_file = self.home_dir / '.bashrc'
        elif shell == 'zsh':
            config_file = self.home_dir / '.zshrc'
        elif shell == 'fish':
            config_file = self.home_dir / '.config' / 'fish' / 'config.fish'
        else:
            raise ValueError(f"Unknown shell: {shell}")

        config_file.write_text(content)
        return config_file

    def create_fish_function(self, name: str, content: str):
        """Create a fish function file."""
        func_file = self.home_dir / '.config' / 'fish' / 'functions' / f'{name}.fish'
        func_file.write_text(content)
        return func_file


@pytest.fixture
def test_environment(tmp_path):
    """Provide a TestEnvironment instance."""
    return TestEnvironment(tmp_path)