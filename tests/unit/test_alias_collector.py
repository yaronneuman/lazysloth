"""
Unit tests for the AliasCollector class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from lazysloth.collectors.alias_collector import AliasCollector


@pytest.mark.unit
class TestAliasCollector:
    """Test the AliasCollector class functionality."""

    def test_init(self, isolated_config):
        """Test AliasCollector initialization."""
        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config
            collector = AliasCollector()
            assert collector.config == isolated_config

    def test_parse_bash_zsh_aliases(self, mock_home_dir, sample_shell_configs):
        """Test parsing aliases from bash/zsh configuration files."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            collector.home = mock_home_dir

            # Create a bash config file
            bashrc = mock_home_dir / '.bashrc'
            bashrc.write_text(sample_shell_configs['bashrc'])

            aliases = collector._parse_bash_zsh_aliases(bashrc, 'bash')

            assert 'll' in aliases
            assert aliases['ll']['command'] == 'ls -la'
            assert aliases['ll']['shell'] == 'bash'
            assert aliases['ll']['type'] == 'alias'

            assert 'gs' in aliases
            assert aliases['gs']['command'] == 'git status'

    def test_parse_zsh_aliases(self, mock_home_dir, sample_shell_configs):
        """Test parsing aliases from zsh configuration file."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            collector.home = mock_home_dir

            # Create a zsh config file
            zshrc = mock_home_dir / '.zshrc'
            zshrc.write_text(sample_shell_configs['zshrc'])

            aliases = collector._parse_bash_zsh_aliases(zshrc, 'zsh')

            assert 'gs' in aliases
            assert aliases['gs']['command'] == 'git status'
            assert aliases['gs']['shell'] == 'zsh'

            assert 'dps' in aliases
            assert aliases['dps']['command'] == 'docker ps'



    def test_collect_from_bash(self, mock_home_dir, sample_shell_configs):
        """Test collecting aliases from bash configuration."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            collector.home = mock_home_dir

            # Create bash config
            bashrc = mock_home_dir / '.bashrc'
            bashrc.write_text(sample_shell_configs['bashrc'])

            aliases = collector.collect_from_shell('bash')

            assert 'll' in aliases
            assert 'gs' in aliases
            assert aliases['ll']['command'] == 'ls -la'


    def test_find_alias_for_command_exact_match(self, isolated_config, sample_aliases):
        """Test finding alias for exact command match."""
        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config
            isolated_config.get_aliases_data = MagicMock(return_value=sample_aliases)

            collector = AliasCollector()

            # Test exact match
            result = collector.find_alias_for_command('git status')
            assert result is not None
            alias_name, alias_data = result
            assert alias_name == 'gs'  # Should prefer first match
            assert alias_data['command'] == 'git status'

    def test_find_alias_for_command_with_arguments(self, isolated_config, sample_aliases):
        """Test finding alias for command with additional arguments."""
        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config
            isolated_config.get_aliases_data = MagicMock(return_value=sample_aliases)

            collector = AliasCollector()

            # Test command with arguments
            result = collector.find_alias_for_command('git status --short')
            assert result is not None
            alias_name, alias_data = result
            assert alias_name in ['gs', 'gst']  # Could match either
            assert alias_data['command'] == 'git status'

    def test_find_alias_for_command_no_match(self, isolated_config, sample_aliases):
        """Test finding alias for command with no matches."""
        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config
            isolated_config.get_aliases_data = MagicMock(return_value=sample_aliases)

            collector = AliasCollector()

            # Test no match
            result = collector.find_alias_for_command('some unknown command')
            assert result is None

    def test_find_alias_for_command_prefers_specific(self, isolated_config):
        """Test that more specific aliases are preferred over general ones."""
        aliases_with_specificity = {
            'g': {
                'command': 'git',
                'shell': 'zsh',
                'source_file': '/home/user/.zshrc',
                'type': 'alias'
            },
            'gs': {
                'command': 'git status',
                'shell': 'zsh',
                'source_file': '/home/user/.zshrc',
                'type': 'alias'
            }
        }

        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config
            isolated_config.get_aliases_data = MagicMock(return_value=aliases_with_specificity)

            collector = AliasCollector()

            # Should prefer more specific alias
            result = collector.find_alias_for_command('git status')
            assert result is not None
            alias_name, alias_data = result
            assert alias_name == 'gs'  # More specific than 'g'

    def test_collect_all_saves_data(self, isolated_config, mock_home_dir, sample_shell_configs):
        """Test that collect_all saves data to config."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
                mock_config.return_value = isolated_config
                isolated_config.save_aliases_data = MagicMock()

                collector = AliasCollector()
                collector.home = mock_home_dir

                # Create some config files
                bashrc = mock_home_dir / '.bashrc'
                bashrc.write_text(sample_shell_configs['bashrc'])

                # Run collect_all
                result = collector.collect_all()

                # Verify save was called
                isolated_config.save_aliases_data.assert_called_once()

                # Verify result contains collected aliases
                assert isinstance(result, dict)

    def test_get_config_files(self, mock_home_dir):
        """Test getting configuration files for different shells."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            collector.home = mock_home_dir

            # Test bash config files
            bash_files = collector._get_config_files('bash')
            expected_bash = [
                mock_home_dir / '.bashrc',
                mock_home_dir / '.bash_profile',
                mock_home_dir / '.bash_aliases',
                mock_home_dir / '.profile'
            ]
            assert bash_files == expected_bash

            # Test zsh config files
            zsh_files = collector._get_config_files('zsh')
            expected_zsh = [
                mock_home_dir / '.zshrc',
                mock_home_dir / '.zsh_profile',
                mock_home_dir / '.zshenv',
                mock_home_dir / '.profile'
            ]
            assert zsh_files == expected_zsh

            # Test unknown shell
            unknown_files = collector._get_config_files('unknown')
            assert unknown_files == []

    def test_parse_aliases_ignores_unreadable_files(self, mock_home_dir):
        """Test that parsing gracefully handles unreadable files."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            collector.home = mock_home_dir

            # Create a file that will cause UnicodeDecodeError
            bad_file = mock_home_dir / '.bashrc'
            bad_file.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8

            # Should not raise exception
            aliases = collector._parse_bash_zsh_aliases(bad_file, 'bash')
            assert aliases == {}

    def test_recursive_alias_resolution_basic(self, mock_home_dir):
        """Test basic recursive alias resolution."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()

            # Setup aliases: g -> git, gcm -> git commit -m
            aliases = {
                'g': {'command': 'git', 'shell': 'bash'},
                'gcm': {'command': 'git commit -m', 'shell': 'bash'}
            }

            with patch.object(collector.config, 'get_aliases_data', return_value=aliases):
                # Test: g commit -m "message" should suggest gcm
                result = collector.find_alias_for_command('g commit -m "message"')
                assert result is not None
                alias_name, alias_data = result
                assert alias_name == 'gcm'
                assert alias_data['command'] == 'git commit -m'

    def test_recursive_alias_resolution_multiple_levels(self, mock_home_dir):
        """Test multiple levels of recursive alias resolution."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()

            # Setup aliases: a -> b, b -> git, gc -> git commit
            aliases = {
                'a': {'command': 'b', 'shell': 'bash'},
                'b': {'command': 'git', 'shell': 'bash'},
                'gc': {'command': 'git commit', 'shell': 'bash'}
            }

            with patch.object(collector.config, 'get_aliases_data', return_value=aliases):
                # Test: a commit should suggest gc
                result = collector.find_alias_for_command('a commit')
                assert result is not None
                alias_name, alias_data = result
                assert alias_name == 'gc'
                assert alias_data['command'] == 'git commit'

    def test_recursive_alias_resolution_prefers_most_specific(self, mock_home_dir):
        """Test that recursive resolution prefers the most specific alias."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()

            # Setup aliases with different levels of specificity
            aliases = {
                'g': {'command': 'git', 'shell': 'bash'},
                'gc': {'command': 'git commit', 'shell': 'bash'},
                'gcm': {'command': 'git commit -m', 'shell': 'bash'}
            }

            with patch.object(collector.config, 'get_aliases_data', return_value=aliases):
                # Test: g commit -m "message" should suggest gcm (most specific)
                result = collector.find_alias_for_command('g commit -m "message"')
                assert result is not None
                alias_name, alias_data = result
                assert alias_name == 'gcm'

                # Test: g commit should suggest gc
                result = collector.find_alias_for_command('g commit')
                assert result is not None
                alias_name, alias_data = result
                assert alias_name == 'gc'

    def test_recursive_alias_expansion_circular_protection(self, mock_home_dir):
        """Test that circular alias references are handled safely."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()

            # Setup circular aliases: a -> b, b -> a
            aliases = {
                'a': {'command': 'b', 'shell': 'bash'},
                'b': {'command': 'a', 'shell': 'bash'}
            }

            # This should not cause infinite recursion
            expanded = collector._expand_aliases_in_command('a', aliases)
            # Should return something (not crash), exact result may vary based on max_depth
            assert isinstance(expanded, str)

    def test_expand_aliases_in_command_no_aliases(self, mock_home_dir):
        """Test command expansion when no aliases are present."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()
            aliases = {}

            command = 'git status'
            expanded = collector._expand_aliases_in_command(command, aliases)
            assert expanded == 'git status'

    def test_expand_aliases_in_command_with_arguments(self, mock_home_dir):
        """Test command expansion preserves arguments correctly."""
        with patch.object(Path, 'home', return_value=mock_home_dir):
            collector = AliasCollector()

            aliases = {
                'g': {'command': 'git', 'shell': 'bash'},
                'l': {'command': 'ls -la', 'shell': 'bash'}
            }

            # Test with multiple arguments
            expanded = collector._expand_aliases_in_command('g status --porcelain', aliases)
            assert expanded == 'git status --porcelain'

            # Test alias that already has arguments
            expanded = collector._expand_aliases_in_command('l --color=auto', aliases)
            assert expanded == 'ls -la --color=auto'

    def test_parse_bash_zsh_aliases_ignores_comments(self, isolated_config):
        """Test that commented aliases are not parsed."""
        test_content = """
# This is a commented alias
# alias commented_alias='echo commented'

# Regular aliases that should be found
alias valid_alias='echo valid'
alias another_valid="git status"

# Mixed scenarios
alias normal_alias='echo normal'  # This should work
# alias disabled_alias='echo disabled'  # This should be ignored

    # Indented comment
    # alias indented_commented='echo indented comment'

    alias indented_valid='echo indented valid'  # Should work

# Inline comment scenarios (these should be ignored)
echo "test" # alias inline_comment='echo inline'
some_command && alias after_command='echo after'  # This has text before alias

# Edge cases
alias edge1='echo test'
#alias edge2='echo test2'
 # alias edge3='echo test3'
"""

        with patch('lazysloth.collectors.alias_collector.Config') as mock_config:
            mock_config.return_value = isolated_config

            collector = AliasCollector()

            with tempfile.NamedTemporaryFile(mode='w', suffix='.zshrc', delete=False) as f:
                f.write(test_content)
                f.flush()

                try:
                    aliases = collector._parse_bash_zsh_aliases(Path(f.name), 'zsh')

                    # Should find these valid aliases
                    expected_aliases = {
                        'valid_alias': 'echo valid',
                        'another_valid': 'git status',
                        'normal_alias': 'echo normal',
                        'indented_valid': 'echo indented valid',
                        'edge1': 'echo test'
                    }

                    # Should NOT find these (they're commented or have text before alias)
                    forbidden_aliases = [
                        'commented_alias', 'disabled_alias', 'indented_commented',
                        'inline_comment', 'after_command', 'edge2', 'edge3'
                    ]

                    # Check expected aliases were found
                    for name, expected_cmd in expected_aliases.items():
                        assert name in aliases, f"Missing expected alias: {name}"
                        assert aliases[name]['command'] == expected_cmd, f"Wrong command for {name}"

                    # Check forbidden aliases were NOT found
                    for name in forbidden_aliases:
                        assert name not in aliases, f"Found forbidden (commented) alias: {name}"

                    # Should have exactly the expected number
                    assert len(aliases) == len(expected_aliases)

                finally:
                    os.unlink(f.name)