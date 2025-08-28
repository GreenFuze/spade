"""
SPADE Lock Manager
Cross-platform, race-safe exclusive locking for Phase-0 runs
"""

import json
import os
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from logger import get_logger

# Use get_logger() directly instead of storing local copy

LOCK_FILENAME = "phase0.lock"


def acquire_lock(repo_root: Path, break_lock: bool = False) -> contextmanager:
    """
    Acquire an exclusive lock for Phase-0 analysis.

    Args:
        repo_root: Root directory of the repository
        break_lock: If True, delete existing lock and proceed

    Yields:
        None

    Raises:
        SystemExit: If lock exists and break_lock is False
    """
    lock_path = repo_root / ".spade" / LOCK_FILENAME

    # Ensure .spade directory exists
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if lock exists
    if lock_path.exists():
        if not break_lock:
            try:
                # Try to read lock info for helpful error message
                lock_info = json.loads(lock_path.read_text(encoding="utf-8"))
                pid = lock_info.get("pid", "unknown")
                host = lock_info.get("host", "unknown")
                started_at = lock_info.get("started_at_utc", "unknown")
                get_logger().error(f"[lock] phase0 lock found at {lock_path}")
                get_logger().error(
                    f"[lock] another run may be active (pid={pid}, host={host}, started={started_at})"
                )
                get_logger().error("[lock] Use --break-lock to override.")
                raise SystemExit(1)
            except Exception:
                # If we can't read the lock file, still show the basic error
                get_logger().error(
                    f"[lock] phase0 lock found at {lock_path} — another run may be active."
                )
                get_logger().error("[lock] Use --break-lock to override.")
                raise SystemExit(1)
        else:
            # Break the lock
            try:
                lock_path.unlink()
                get_logger().info(f"[lock] removed existing lock at {lock_path}")
            except Exception as e:
                get_logger().warning(f"[lock] failed to remove existing lock: {e}")

    # Create lock info
    lock_info = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "command": "phase0",
        "repo_root": str(repo_root.resolve()),
    }

    @contextmanager
    def lock_context():
        try:
            # Create lock file with O_EXCL (exclusive create)
            with open(lock_path, "x", encoding="utf-8") as f:
                json.dump(lock_info, f, ensure_ascii=False, indent=2)

            get_logger().debug(f"[lock] acquired lock at {lock_path}")
            yield

        except FileExistsError:
            # Race condition - another process created the lock
            get_logger().error(
                f"[lock] lock already exists at {lock_path} (race condition)"
            )
            raise SystemExit(1)
        except Exception as e:
            get_logger().error(f"[lock] failed to acquire lock: {e}")
            raise SystemExit(1)
        finally:
            # Always try to remove the lock file
            try:
                if lock_path.exists():
                    lock_path.unlink()
                    get_logger().debug(f"[lock] released lock at {lock_path}")
            except Exception as e:
                get_logger().warning(
                    f"[lock] failed to remove lock file {lock_path}: {e}"
                )

    return lock_context()
