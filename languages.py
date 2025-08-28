"""
SPADE Language Mapping Helpers
Provides deterministic extension→language mapping and aggregation utilities
"""

from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, List, Tuple

from schemas import RunConfig
from logger import get_logger

# Use get_logger() directly instead of storing local copy

# Minimal but useful seed mapping (extensions → canonical language)
SEED_EXT2LANG: Dict[str, str] = {
    "py": "python", "rs": "rust", "go": "go", "ts": "typescript", "js": "javascript",
    "cpp": "c++", "cxx": "c++", "cc": "c++", "hpp": "c++", "hxx": "c++", "hh": "c++",
    "c": "c", "h": "c", "kt": "kotlin", "java": "java", "rb": "ruby", "php": "php",
    "swift": "swift", "m": "objective-c", "mm": "objective-c++", "jl": "julia",
    "sh": "shell", "ps1": "powershell", "bat": "batch", "pl": "perl", "r": "r",
    "scala": "scala", "hs": "haskell", "lua": "lua", "dart": "dart", "sql": "sql",
    "proto": "protobuf", "qml": "qml", "tf": "hcl", "tsx": "typescript", "jsx": "javascript"
}


def load_learned(repo_root: Path) -> Dict[str, str]:
    """
    Load .spade/languages.learned.json if exists. Format: list of {ext, language}.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        Dictionary mapping extensions to languages, or empty dict if file doesn't exist
    """
    p = repo_root / ".spade" / "languages.learned.json"
    if not p.exists():
        return {}
    
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out: Dict[str, str] = {}
        for item in data:
            ext = str(item.get("ext", "")).lstrip(".").lower()
            lang = str(item.get("language", "")).strip().lower()
            if ext and lang:
                out[ext] = lang
        get_logger().info(f"[languages] loaded {len(out)} learned mappings")
        return out
    except Exception as e:
        get_logger().warning(f"[languages] failed to load learned mapping: {e}")
        return {}


def active_map(cfg: RunConfig, repo_root: Path) -> Dict[str, str]:
    """
    Return the active ext→language map (seed ∪ learned if enabled).
    
    Args:
        cfg: Runtime configuration
        repo_root: Root directory of the repository
        
    Returns:
        Dictionary mapping extensions to languages
    """
    mapping = dict(SEED_EXT2LANG)
    if cfg.use_learned_languages:
        learned = load_learned(repo_root)
        mapping.update(learned)  # learned overrides seed
    return mapping


def aggregate_languages(ext_histogram: Dict[str, int], ext2lang: Dict[str, str]) -> List[Tuple[str, int]]:
    """
    Convert an ext_histogram to a list of (language, weight) sorted by weight desc.
    
    Rules:
    - Keys starting with '.' (e.g., '.env') are ignored unless present in ext2lang (rare; typically ignored).
    - Unknown extensions are ignored.
    
    Args:
        ext_histogram: Dictionary mapping extensions to counts
        ext2lang: Dictionary mapping extensions to languages
        
    Returns:
        List of (language, weight) tuples sorted by weight descending, then name ascending
    """
    totals: Dict[str, int] = {}
    
    for ext, count in ext_histogram.items():
        if not isinstance(count, int) or count <= 0:
            continue
        
        # dotfile keys (".env") are ignored unless present in ext2lang (rare; typically ignored)
        key = ext.lower()
        if key.startswith("."):
            # For dotfiles, only include if the full key (with dot) is explicitly mapped
            if key not in ext2lang:
                continue
            lang = ext2lang[key]
        else:
            # For regular extensions, strip any leading dots
            key = key.lstrip(".")
            if not key:  # "."
                continue
            lang = ext2lang.get(key)
            if not lang:
                continue
        
        totals[lang] = totals.get(lang, 0) + count
    
    # sort by count desc, then name asc for stability
    return sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
