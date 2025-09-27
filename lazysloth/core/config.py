import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """Manages LazySloth configuration."""

    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'lazysloth'
        self.config_file = self.config_dir / 'config.yaml'
        self.aliases_file = self.config_dir / 'aliases.yaml'
        self.stats_file = self.config_dir / 'stats.yaml'

        self._ensure_config_dir()
        self._config = self._load_config()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        home = Path.home()
        return {
            'version': '1.0.0',
            'monitoring': {
                'enabled': True,
                'notice_threshold': 1,     # Show notice after N uses
                'blocking_threshold': 5,   # Block command after N uses
                'blocking_enabled': True,  # Whether to block commands
                'ignored_commands': []
            },
            'monitored_files': {
                'bash': [
                    str(home / '.bashrc'),
                    str(home / '.bash_aliases'),
                    str(home / '.slothrc')
                ],
                'zsh': [
                    str(home / '.zshrc'),
                    str(home / '.zsh_aliases'),
                    str(home / '.slothrc')
                ],
            }
        }

    def save(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save()

    def get_aliases_data(self) -> Dict[str, Any]:
        """Load aliases data."""
        if self.aliases_file.exists():
            with open(self.aliases_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_aliases_data(self, data: Dict[str, Any]):
        """Save aliases data."""
        with open(self.aliases_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_stats_data(self) -> Dict[str, Any]:
        """Load statistics data."""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_stats_data(self, data: Dict[str, Any]):
        """Save statistics data."""
        with open(self.stats_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)