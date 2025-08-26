"""
SPADE Logger - Centralized logging configuration
"""

import logging
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def init_logger(repo_root: Path) -> logging.Logger:
    """
    Initialize the SPADE logger with file and console handlers.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    spade_dir = repo_root / ".spade"
    spade_dir.mkdir(exist_ok=True)
    log_path = spade_dir / "spade.log"
    
    # Create logger
    logger = logging.getLogger("spade")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler (info level for console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the SPADE logger instance.
    If not initialized, creates a basic logger without file handler.
    """
    global _logger
    
    if _logger is None:
        # Create a basic logger if not initialized
        logger = logging.getLogger("spade")
        if not logger.handlers:
            # Add console handler only
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        _logger = logger
    
    return _logger


# Legacy function for backward compatibility
def setup_logging(repo_root: Path) -> logging.Logger:
    """Legacy function - use init_logger instead."""
    return init_logger(repo_root)
