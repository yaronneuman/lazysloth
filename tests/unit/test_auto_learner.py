"""
Unit tests for the AutoLearner class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from lazysloth.core.auto_learner import AutoLearner


@pytest.mark.unit
class TestAutoLearner:
    """Test the AutoLearner class functionality."""

    def test_init(self):
        """Test AutoLearner initialization."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                learner = AutoLearner()

                assert learner.config is not None
                assert learner.collector is not None
                mock_config.assert_called_once()
                mock_collector.assert_called_once()

    def test_get_monitored_files_all_shells(self, isolated_config):
        """Test getting monitored files for all shells."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={
                    'bash': ['/home/user/.bashrc'],
                    'zsh': ['/home/user/.zshrc', '/home/user/.zsh_aliases']
                })

                learner = AutoLearner()
                result = learner.get_monitored_files()

                assert 'bash' in result
                assert 'zsh' in result
                assert len(result['bash']) == 1
                assert len(result['zsh']) == 2

    def test_get_monitored_files_specific_shell(self, isolated_config):
        """Test getting monitored files for specific shell."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={
                    'bash': ['/home/user/.bashrc'],
                    'zsh': ['/home/user/.zshrc']
                })

                learner = AutoLearner()
                result = learner.get_monitored_files('zsh')

                assert 'bash' not in result
                assert 'zsh' in result
                assert len(result['zsh']) == 1
                assert result['zsh'][0] == '/home/user/.zshrc'

    def test_add_monitored_file_new_file(self, isolated_config):
        """Test adding a new monitored file."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={
                    'zsh': ['/home/user/.zshrc']
                })
                isolated_config.set = MagicMock()
                isolated_config.save = MagicMock()

                learner = AutoLearner()
                result = learner.add_monitored_file('zsh', '/home/user/.zsh_aliases')

                assert result is True
                isolated_config.set.assert_called_once()
                isolated_config.save.assert_called_once()

    def test_add_monitored_file_existing_file(self, isolated_config):
        """Test adding an already monitored file."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                # Use absolute path that will match the method's conversion
                from pathlib import Path
                abs_path = str(Path('/home/user/.zshrc').expanduser().resolve())

                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={
                    'zsh': [abs_path]
                })

                learner = AutoLearner()
                result = learner.add_monitored_file('zsh', '/home/user/.zshrc')

                assert result is False

    def test_remove_monitored_file_existing(self, isolated_config):
        """Test removing an existing monitored file."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                monitored_files = {
                    'zsh': ['/home/user/.zshrc', '/home/user/.zsh_aliases']
                }
                isolated_config.get = MagicMock(return_value=monitored_files)
                isolated_config.set = MagicMock()
                isolated_config.save = MagicMock()

                learner = AutoLearner()
                result = learner.remove_monitored_file('zsh', '/home/user/.zsh_aliases')

                assert result is True
                isolated_config.set.assert_called_once()
                isolated_config.save.assert_called_once()

    def test_remove_monitored_file_not_found(self, isolated_config):
        """Test removing a non-existent monitored file."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={
                    'zsh': ['/home/user/.zshrc']
                })

                learner = AutoLearner()
                result = learner.remove_monitored_file('zsh', '/home/user/.zsh_aliases')

                assert result is False

    def test_learn_from_shell_bash(self, isolated_config):
        """Test learning aliases from bash files."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                # Create test file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.bashrc', delete=False) as f:
                    f.write("alias test_alias='echo test'\n")
                    f.write("alias another='ls -la'\n")
                    f.flush()
                    test_file_path = f.name

                try:
                    mock_config.return_value = isolated_config
                    isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                        'monitored_files.bash': [test_file_path]
                    }.get(key, default))
                    isolated_config.get_aliases_data = MagicMock(return_value={})
                    isolated_config.save_aliases_data = MagicMock()

                    mock_collector_instance = MagicMock()
                    mock_collector_instance._parse_bash_zsh_aliases.return_value = {
                        'test_alias': {
                            'command': 'echo test',
                            'shell': 'bash',
                            'source_file': test_file_path,
                            'type': 'alias'
                        },
                        'another': {
                            'command': 'ls -la',
                            'shell': 'bash',
                            'source_file': test_file_path,
                            'type': 'alias'
                        }
                    }
                    mock_collector.return_value = mock_collector_instance

                    learner = AutoLearner()
                    result = learner._learn_from_shell('bash')

                    assert result['learned'] == 2
                    assert result['updated'] == 0
                    assert result['removed'] == 0

                    isolated_config.save_aliases_data.assert_called_once()

                finally:
                    os.unlink(test_file_path)

    def test_learn_from_monitored_files_all_shells(self, isolated_config):
        """Test learning from all monitored files."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(side_effect=lambda key, default=None: {
                    'monitored_files': {
                        'bash': ['/fake/bashrc'],
                        'zsh': ['/fake/zshrc']
                    }
                }.get(key, default))

                learner = AutoLearner()

                # Mock the _learn_from_shell method
                with patch.object(learner, '_learn_from_shell') as mock_learn:
                    mock_learn.side_effect = [
                        {'learned': 2, 'updated': 1, 'removed': 0},  # bash
                        {'learned': 1, 'updated': 0, 'removed': 1}   # zsh
                    ]

                    result = learner.learn_from_monitored_files()

                    assert result['learned'] == 3
                    assert result['updated'] == 1
                    assert result['removed'] == 1

                    # Should have been called for both shells
                    assert mock_learn.call_count == 2

    def test_learn_from_monitored_files_specific_shell(self, isolated_config):
        """Test learning from specific shell only."""
        with patch('lazysloth.core.auto_learner.Config') as mock_config:
            with patch('lazysloth.core.auto_learner.AliasCollector') as mock_collector:
                mock_config.return_value = isolated_config

                learner = AutoLearner()

                # Mock the _learn_from_shell method
                with patch.object(learner, '_learn_from_shell') as mock_learn:
                    mock_learn.return_value = {'learned': 2, 'updated': 0, 'removed': 0}

                    result = learner.learn_from_monitored_files('zsh')

                    assert result['learned'] == 2
                    assert result['updated'] == 0
                    assert result['removed'] == 0

                    # Should have been called only once for zsh
                    mock_learn.assert_called_once_with('zsh')