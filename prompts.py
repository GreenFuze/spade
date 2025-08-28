"""
SPADE Prompts Loader
Loads system and user prompt files from the prompts directory
"""

from pathlib import Path
from logger import get_logger

# Use get_logger() directly instead of storing local copy

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_system(name: str) -> str:
    """Load a system prompt by base name (e.g., 'phase0_scaffold')."""
    p = PROMPTS_DIR / f"{name}_system.md"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        get_logger().error(f"[prompts] failed to load system prompt {p}: {e}")
        raise


def load_user(name: str) -> str:
    """Load a user prompt template by base name (e.g., 'phase0_scaffold')."""
    p = PROMPTS_DIR / f"{name}_user.md"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        get_logger().error(f"[prompts] failed to load user prompt {p}: {e}")
        raise
