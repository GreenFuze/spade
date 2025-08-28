"""
SPADE Marker Detection
Detects well-known "marker" names (build/CI/test/docs/framework hints) deterministically
"""

import fnmatch
import json
from pathlib import Path
from typing import List, Dict

from schemas import RunConfig


# Conservative core seed markers
SEED_MARKERS: List[Dict] = [
    {"match": "pyproject.toml", "type": "build", "languages": ["python"], "weight": 0.9},
    {"match": "go.mod", "type": "build", "languages": ["go"], "weight": 0.9},
    {"match": "Cargo.toml", "type": "build", "languages": ["rust"], "weight": 0.9},
    {"match": "package.json", "type": "build", "languages": ["javascript", "typescript"], "weight": 0.8},
    {"match": "CMakeLists.txt", "type": "build", "languages": ["c", "c++"], "weight": 0.85},
    {"match": "Makefile", "type": "build", "weight": 0.6},
    {"match": "Dockerfile", "type": "deploy", "weight": 0.7},
    {"match": "pom.xml", "type": "build", "languages": ["java"], "weight": 0.8},
    {"match": "build.gradle", "type": "build", "languages": ["java", "kotlin"], "weight": 0.8},
    {"match": ".github/workflows/", "type": "ci", "weight": 0.6},  # note: contains '/'
    {"match": "tox.ini", "type": "test", "languages": ["python"], "weight": 0.6},
    {"match": "pytest.ini", "type": "test", "languages": ["python"], "weight": 0.6},
    {"match": "mkdocs.yml", "type": "docs", "weight": 0.6},
    {"match": "tsconfig.json", "type": "build", "languages": ["typescript"], "weight": 0.7},
]


def load_learned_markers(repo_root: Path) -> List[Dict]:
    """
    Load learned markers from .spade/markers.learned.json.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        List of learned marker rules, or empty list if file doesn't exist
    """
    path = repo_root / ".spade" / "markers.learned.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            # If file is corrupted, return empty list
            return []
    else:
        return []


def active_rules(cfg: RunConfig, repo_root: Path) -> List[Dict]:
    """
    Get active marker rules combining seed markers and learned markers.
    
    Args:
        cfg: Runtime configuration
        repo_root: Root directory of the repository
        
    Returns:
        List of active marker rules
    """
    rules = SEED_MARKERS.copy()
    if cfg.use_learned_markers:
        rules += load_learned_markers(repo_root)
    return rules


def detect_markers_for_dir(dir_path: Path, rules: List[Dict]) -> List[str]:
    """
    Return a deduped list of matched marker names for dir_path.
    
    Matching semantics:
    - If rule.match contains '/', treat it as a relative path glob from dir_path (e.g., '.github/workflows/').
      Use dir_path.glob(rule.match.rstrip('/')) and consider a match if any exists.
    - Else match against immediate entry names in dir_path via fnmatch.fnmatch(name, rule.match).
    
    Only presence counts; do not descend arbitrarily (metadata-only).
    
    Args:
        dir_path: Directory path to check for markers
        rules: List of marker rules to apply
        
    Returns:
        Sorted list of matched marker names
    """
    matched: set[str] = set()
    
    try:
        names = {p.name for p in dir_path.iterdir()}  # immediate entries
    except OSError:
        return []  # unreadable; Task 4 already set ignored_reason
    
    for rule in rules:
        patt = rule.get("match", "")
        if not patt:
            continue
            
        if "/" in patt.strip("/"):
            # relative path pattern
            try:
                found = any(dir_path.glob(patt.rstrip("/")))
            except Exception:
                found = False
            if found:
                matched.add(patt)
        else:
            # single name pattern
            for n in names:
                if fnmatch.fnmatch(n, patt):
                    matched.add(n)
    
    return sorted(matched)
