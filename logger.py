"""
SPADE Logger - Centralized logging configuration
"""

import logging
from pathlib import Path


def setup_logging(repo_root: Path) -> logging.Logger:
    """Setup logging configuration for SPADE."""
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
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """Get the SPADE logger instance."""
    return logging.getLogger("spade")
