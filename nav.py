"""
SPADE Navigation Guardrails
Validates LLM navigation requests and provides deterministic fallbacks
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

from models import RunConfig, DirMeta, Nav
from ignore import should_skip
from logger import get_logger

logger = get_logger()

# Reason codes used for uniform logging/telemetry
REASON_NOT_IN_SIBLINGS = "not in siblings"
REASON_EXCLUDED = "excluded by scanner"
REASON_BAD_NAME = "invalid name"
REASON_DEPTH = "over max_depth"
REASON_IGNORED = "skipped by ignore rules"


def _is_single_segment(name: str) -> bool:
    """
    Check if name is a valid single-segment directory name.
    
    Args:
        name: Directory name to validate
        
    Returns:
        True if name is valid single segment, False otherwise
    """
    # Disallow path separators, empty, dot/current, dotdot/parent, spaces
    if not name or name in (".", ".."):
        return False
    return ("/" not in name) and ("\\" not in name) and (" " not in name)


def _depth_allows(current_depth: int, cfg: RunConfig) -> bool:
    """
    Check if current depth allows descending to children.
    
    Args:
        current_depth: Current directory depth
        cfg: Runtime configuration
        
    Returns:
        True if depth allows descending, False otherwise
    """
    # Allow one more level unless limited
    if cfg.limits.max_depth == 0:
        return True
    return (current_depth + 1) <= cfg.limits.max_depth


def filter_nav(
    repo_root: Path,
    current_meta: DirMeta,
    cfg: RunConfig,
    nav: Nav,
    specs: tuple
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Validate requested children and return (kept, rejected_with_reasons).
    
    Args:
        repo_root: Root directory of the repository
        current_meta: Pydantic-validated dirmeta for the current directory
        cfg: Runtime configuration
        nav: Pydantic-validated LLM navigation output
        specs: Tuple of (ignore_spec, allow_spec) from spade.ignore.load_specs
        
    Returns:
        Tuple of (kept_children, rejected_with_reasons)
    """
    # Handle both old format (ignore_spec, allow_spec) and new format (ignore_spec, allow_spec, ignore_lines, allow_lines)
    if len(specs) == 2:
        ignore_spec, allow_spec = specs
    elif len(specs) == 4:
        ignore_spec, allow_spec, _, _ = specs
    else:
        raise ValueError(f"Expected specs tuple of length 2 or 4, got {len(specs)}")
    
    requested = nav.descend_into or []
    
    # Deduplicate preserving order
    seen = set()
    req = []
    for c in requested:
        if c not in seen:
            seen.add(c)
            req.append(c)

    kept: List[str] = []
    rejected: List[Tuple[str, str]] = []

    # Depth check (global for this parent)
    parent_depth_ok = _depth_allows(current_meta.depth, cfg)

    for child in req:
        # name checks
        if not _is_single_segment(child):
            rejected.append((child, REASON_BAD_NAME))
            continue
        
        # siblings check
        if child not in current_meta.siblings:
            rejected.append((child, REASON_NOT_IN_SIBLINGS))
            continue
        
        # excluded by scanner
        if child in current_meta.excluded_children:
            rejected.append((child, REASON_EXCLUDED))
            continue
        
        # depth check
        if not parent_depth_ok:
            rejected.append((child, REASON_DEPTH))
            continue
        
        # ignore rules
        child_path = repo_root / ("" if current_meta.path == "." else current_meta.path) / child
        if should_skip(child_path, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
            rejected.append((child, REASON_IGNORED))
            continue
        
        kept.append(child)

    # Apply cap
    cap = cfg.caps.nav.max_children_per_step
    if cap != 0 and len(kept) > cap:
        # Move excess children to rejected list
        excess = kept[cap:]
        kept = kept[:cap]
        for child in excess:
            rejected.append((child, "exceeded max_children_per_step"))

    logger.info(f"[nav] requested={len(req)} kept={len(kept)} rejected={len(rejected)} at {current_meta.path}")
    return kept, rejected


def fallback_children(
    repo_root: Path,
    current_meta: DirMeta,
    cfg: RunConfig,
    specs: tuple
) -> List[str]:
    """
    Pick top children by deterministic_scoring, filtered by excluded/ignore/depth and capped.
    
    Args:
        repo_root: Root directory of the repository
        current_meta: Pydantic-validated dirmeta for the current directory
        cfg: Runtime configuration
        specs: Tuple of (ignore_spec, allow_spec) from spade.ignore.load_specs
        
    Returns:
        List of children to descend into, ordered by deterministic scoring
    """
    # Handle both old format (ignore_spec, allow_spec) and new format (ignore_spec, allow_spec, ignore_lines, allow_lines)
    if len(specs) == 2:
        ignore_spec, allow_spec = specs
    elif len(specs) == 4:
        ignore_spec, allow_spec, _, _ = specs
    else:
        raise ValueError(f"Expected specs tuple of length 2 or 4, got {len(specs)}")
    
    # No fallback if parent cannot descend due to depth
    if not _depth_allows(current_meta.depth, cfg):
        return []

    # Deterministic scoring may be dict[str, ChildScore] or {"children": {...}} depending on earlier write
    # Normalize to dict[str, ChildScore-like]
    scores = {}
    dm = current_meta.deterministic_scoring or {}
    if isinstance(dm, dict) and "children" in dm:
        scores = dm.get("children", {}) or {}
    else:
        scores = dm

    # Order by score desc, then name asc
    ordered = sorted(
        scores.items(),
        key=lambda kv: (-float(getattr(kv[1], "score", getattr(kv[1], "get", lambda _: 0)("score") if isinstance(kv[1], dict) else 0.0)), kv[0])
    )
    
    kept: List[str] = []
    for child, meta in ordered:
        if child in current_meta.excluded_children:
            continue
        if child not in current_meta.siblings:
            continue
        
        child_path = repo_root / ("" if current_meta.path == "." else current_meta.path) / child
        if should_skip(child_path, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
            continue
        
        kept.append(child)
        cap = cfg.caps.nav.max_children_per_step
        if cap != 0 and len(kept) >= cap:
            break
    
    logger.info(f"[nav] fallback kept={len(kept)} at {current_meta.path}")
    return kept
