"""
Unit tests for the FileWatcher class.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lazysloth.core.file_watcher import FileWatcher


@pytest.mark.unit
class TestFileWatcher:
    """Test the FileWatcher class functionality."""

    def test_init(self):
        """Test FileWatcher initialization."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                watcher = FileWatcher()

                assert watcher.config is not None
                assert watcher.learner is not None
                mock_config.assert_called_once()
                mock_learner.assert_called_once()

    def test_get_changed_files_new_file(self, isolated_config):
        """Test detecting new files as changed."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(b"test content")
                    test_file = f.name

                try:
                    watcher = FileWatcher()

                    # Mock no previous mtimes (first run)
                    with patch.object(watcher, "_load_file_mtimes", return_value={}):
                        with patch.object(watcher, "_save_file_mtimes") as mock_save:
                            changed = watcher._get_changed_files([test_file])

                            assert test_file in changed
                            mock_save.assert_called_once()

                finally:
                    Path(test_file).unlink()

    def test_get_changed_files_modified_file(self, isolated_config):
        """Test detecting modified files."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(b"original content")
                    test_file = f.name

                try:
                    watcher = FileWatcher()

                    # Get initial mtime
                    initial_mtime = Path(test_file).stat().st_mtime

                    # Mock previous mtime (older)
                    old_mtime = initial_mtime - 100
                    with patch.object(
                        watcher,
                        "_load_file_mtimes",
                        return_value={test_file: old_mtime},
                    ):
                        with patch.object(watcher, "_save_file_mtimes") as mock_save:
                            changed = watcher._get_changed_files([test_file])

                            assert test_file in changed
                            mock_save.assert_called_once()

                finally:
                    Path(test_file).unlink()

    def test_get_changed_files_unchanged_file(self, isolated_config):
        """Test that unchanged files are not detected."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(b"content")
                    test_file = f.name

                try:
                    watcher = FileWatcher()

                    # Get current mtime
                    current_mtime = Path(test_file).stat().st_mtime

                    # Mock same mtime (unchanged)
                    with patch.object(
                        watcher,
                        "_load_file_mtimes",
                        return_value={test_file: current_mtime},
                    ):
                        with patch.object(watcher, "_save_file_mtimes") as mock_save:
                            changed = watcher._get_changed_files([test_file])

                            assert test_file not in changed
                            mock_save.assert_called_once()

                finally:
                    Path(test_file).unlink()

    def test_check_and_relearn_if_needed_no_files(self, isolated_config):
        """Test behavior when no monitored files configured."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(return_value={})

                watcher = FileWatcher()
                result = watcher.check_and_relearn_if_needed()

                assert result is False

    def test_check_and_relearn_if_needed_with_changes(self, isolated_config):
        """Test relearning when files have changed."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(
                    return_value={
                        "bash": ["/fake/bash_profile"],
                        "zsh": ["/fake/zshrc"],
                    }
                )

                mock_learner_instance = MagicMock()
                mock_learner_instance.learn_from_monitored_files.return_value = {
                    "learned": 2,
                    "updated": 1,
                    "removed": 0,
                }
                mock_learner.return_value = mock_learner_instance

                watcher = FileWatcher()

                # Mock file changes detected
                with patch.object(
                    watcher, "_get_changed_files", return_value={"/fake/bash_profile"}
                ):
                    with patch.object(watcher, "_update_last_check") as mock_update:
                        result = watcher.check_and_relearn_if_needed()

                        assert result is True
                        mock_learner_instance.learn_from_monitored_files.assert_called_once_with(
                            "bash"
                        )
                        mock_update.assert_called_once()

    def test_check_and_relearn_if_needed_no_changes(self, isolated_config):
        """Test no relearning when files haven't changed."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config
                isolated_config.get = MagicMock(
                    return_value={"bash": ["/fake/bash_profile"]}
                )

                mock_learner_instance = MagicMock()
                mock_learner.return_value = mock_learner_instance

                watcher = FileWatcher()

                # Mock no file changes
                with patch.object(watcher, "_get_changed_files", return_value=set()):
                    result = watcher.check_and_relearn_if_needed()

                    assert result is False
                    mock_learner_instance.learn_from_monitored_files.assert_not_called()

    def test_force_relearn_all(self, isolated_config):
        """Test force relearning all aliases."""
        with patch("lazysloth.core.file_watcher.Config") as mock_config:
            with patch("lazysloth.core.file_watcher.AutoLearner") as mock_learner:
                mock_config.return_value = isolated_config

                mock_learner_instance = MagicMock()
                mock_learner_instance.learn_from_monitored_files.return_value = {
                    "learned": 5,
                    "updated": 2,
                    "removed": 1,
                }
                mock_learner.return_value = mock_learner_instance

                watcher = FileWatcher()

                with patch.object(watcher, "_update_last_check") as mock_update:
                    result = watcher.force_relearn_all()

                    assert result["learned"] == 5
                    assert result["updated"] == 2
                    assert result["removed"] == 1

                    mock_learner_instance.learn_from_monitored_files.assert_called_once_with()
                    mock_update.assert_called_once()
