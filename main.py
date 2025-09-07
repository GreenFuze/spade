#!/usr/bin/env python3
"""
SPADE CLI - Main entry point
Command-line interface for SPADE workspace management and analysis
"""

import signal
import sys
from pathlib import Path
from typing import Any


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__)))


def signal_handler(signum: int, frame: Any) -> None:
    """Handle CTRL+C for hard shutdown."""
    print("\nCTRL+C received. Hard shutdown.")
    sys.exit(1)


# Register signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)


def main() -> None:
    """Main entry point for SPADE CLI."""
    pass


if __name__ == "__main__":
    main()
