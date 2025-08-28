"""
SPADE Logger - Centralized logging configuration
"""

import logging
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def init_logger(repo_root: Path) -> None:
    """
    Initialize the SPADE logger with file and console handlers.

    Args:
        repo_root: Root directory of the repository (optional for basic initialization)

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is not None:
        raise RuntimeError("Logger is trying to be initialized multiple times")

    # Create logger
    logger = logging.getLogger("spade")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create console handler (info level for console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if repo_root is provided
    spade_dir = repo_root / ".spade"
    spade_dir.mkdir(exist_ok=True)
    log_path = spade_dir / "spade.log"

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger


def get_logger() -> logging.Logger:
    """
    Get the SPADE logger instance.
    If not initialized, creates a basic logger with console handler only.
    """
    global _logger

    if _logger is None:
        raise RuntimeError("Logger was never initialized")

    return _logger
