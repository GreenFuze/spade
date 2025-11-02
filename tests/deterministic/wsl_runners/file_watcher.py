#!/usr/bin/env python3
"""
File watching utility for monitoring answers.json completion with stability checks.

This module provides a utility to watch for file creation/modification and detect
when a file has stopped being modified (stabilized) before considering it complete.
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple


class FileStabilityWatcher:
    """
    Watches a file for modifications and detects when it has stabilized.

    A file is considered "stable" when it hasn't been modified for a specified
    duration (e.g., 5 seconds). This ensures the writing process is complete.
    """

    def __init__(self, file_path: str, stability_duration: float = 5.0, check_interval: float = 0.5):
        """
        Initialize the file watcher.

        Args:
            file_path: Path to the file to watch
            stability_duration: Seconds of no modification to consider file stable (default 5.0)
            check_interval: Seconds between file checks (default 0.5)
        """
        self.file_path = Path(file_path)
        self.stability_duration = stability_duration
        self.check_interval = check_interval

    def wait_for_stable_file(self, timeout: float) -> Tuple[bool, Optional[float]]:
        """
        Wait for the file to exist and become stable.

        Returns when either:
        1. File exists and has been stable for stability_duration seconds
        2. Timeout is reached

        Args:
            timeout: Maximum seconds to wait for stable file

        Returns:
            Tuple of (success, elapsed_time):
            - success: True if file is stable, False if timeout
            - elapsed_time: Seconds elapsed until file stabilized (or None if timeout)
        """
        start_time = time.time()
        last_mtime = None
        last_change_time = None

        while True:
            current_time = time.time()
            elapsed = current_time - start_time

            # Check timeout
            if elapsed >= timeout:
                return False, None

            # Check if file exists
            if self.file_path.exists():
                # Get current modification time
                current_mtime = os.path.getmtime(self.file_path)

                # File modification detected (or first time seeing file)
                if last_mtime is None or current_mtime != last_mtime:
                    last_mtime = current_mtime
                    last_change_time = current_time

                # Check if file has been stable for stability_duration
                elif last_change_time is not None:
                    stable_duration = current_time - last_change_time
                    if stable_duration >= self.stability_duration:
                        # File is stable!
                        return True, elapsed

            # Sleep before next check
            time.sleep(self.check_interval)

    def get_file_stability_time(self) -> Optional[float]:
        """
        Get the time (in seconds) since the file was last modified.

        Returns:
            Seconds since last modification, or None if file doesn't exist
        """
        if not self.file_path.exists():
            return None

        mtime = os.path.getmtime(self.file_path)
        return time.time() - mtime
