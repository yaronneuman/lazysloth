"""
File change monitoring for automatic alias relearning.
"""

import time
from pathlib import Path
from typing import Dict, Set

from .auto_learner import AutoLearner
from .config import Config


class FileWatcher:
    """Monitors configuration files for changes and triggers relearning."""

    def __init__(self):
        self.config = Config()
        self.learner = AutoLearner()
        self._last_check_file = self.config.config_dir / ".last_file_check"
        self._file_mtimes = {}

    def check_and_relearn_if_needed(self) -> bool:
        """
        Check if any monitored files have changed since last check.
        If so, relearn aliases and return True.

        Returns:
            True if files changed and relearning occurred, False otherwise.
        """
        try:
            # Get all monitored files
            monitored_files = self.config.get("monitored_files", {})
            all_files = []
            for shell, files in monitored_files.items():
                all_files.extend(files)

            if not all_files:
                return False

            # Check if any files have changed
            changed_files = self._get_changed_files(all_files)

            if changed_files:
                # Relearn aliases from all shells with changed files
                shells_to_relearn = set()
                for shell, files in monitored_files.items():
                    if any(f in changed_files for f in files):
                        shells_to_relearn.add(shell)

                # Relearn from affected shells
                total_changes = 0
                for shell in shells_to_relearn:
                    results = self.learner.learn_from_monitored_files(shell)
                    total_changes += (
                        results["learned"] + results["updated"] + results["removed"]
                    )

                # Update last check time
                self._update_last_check()
                return total_changes > 0

            return False

        except Exception as e:
            # Silently fail - don't break shell if monitoring fails
            return False

    def _get_changed_files(self, file_paths: list) -> Set[str]:
        """Get list of files that have changed since last check."""
        changed_files = set()
        current_mtimes = {}

        # Load previous modification times
        previous_mtimes = self._load_file_mtimes()

        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    mtime = path.stat().st_mtime
                    current_mtimes[file_path] = mtime

                    # Check if file is new or modified
                    if (
                        file_path not in previous_mtimes
                        or previous_mtimes[file_path] != mtime
                    ):
                        changed_files.add(file_path)

                except OSError:
                    # Skip files we can't read
                    continue

        # Save current modification times
        self._save_file_mtimes(current_mtimes)
        return changed_files

    def _load_file_mtimes(self) -> Dict[str, float]:
        """Load file modification times from last check."""
        mtime_file = self.config.config_dir / ".file_mtimes"
        if mtime_file.exists():
            try:
                import json

                with open(mtime_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_file_mtimes(self, mtimes: Dict[str, float]) -> None:
        """Save file modification times for next check."""
        mtime_file = self.config.config_dir / ".file_mtimes"
        try:
            import json

            with open(mtime_file, "w") as f:
                json.dump(mtimes, f)
        except OSError:
            # Silently fail if we can't save
            pass

    def _update_last_check(self) -> None:
        """Update the last check timestamp."""
        try:
            with open(self._last_check_file, "w") as f:
                f.write(str(time.time()))
        except OSError:
            # Silently fail if we can't save
            pass

    def force_relearn_all(self) -> Dict[str, int]:
        """Force relearning of all aliases from all monitored files."""
        results = self.learner.learn_from_monitored_files()
        self._update_last_check()
        return results
