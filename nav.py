"""
SPADE Navigation Guardrails
Validates LLM navigation requests and provides deterministic fallbacks

NOTE: This file is temporarily commented out as LLM interactions are disabled.
"""

# from __future__ import annotations
# from pathlib import Path
# from typing import List, Tuple

# from schemas import RunConfig, DirMeta, Nav
# from ignore import should_skip
# from logger import get_logger

# Use get_logger() directly instead of storing local copy

# Reason codes used for uniform logging/telemetry
# REASON_NOT_IN_SIBLINGS = "not in siblings"
# REASON_EXCLUDED = "excluded by scanner"
# REASON_BAD_NAME = "invalid name"
# REASON_DEPTH = "over max_depth"
# REASON_IGNORED = "skipped by ignore rules"


# def _is_single_segment(name: str) -> bool:
#     """
#     Check if name is a valid single-segment directory name.
#
#     Args:
#         name: Directory name to validate
#
#     Returns:
#         True if name is valid single segment, False otherwise
#     """
#     # Disallow path separators, empty, dot/current, dotdot/parent, spaces
#     if not name or name in (".", ".."):
#         return False
#     return ("/" not in name) and ("\\" not in name) and (" " not in name)


# def _depth_allows(current_depth: int, cfg: RunConfig) -> bool:
#     """
#     Check if current depth allows descending to children.
#
#     Args:
#         current_depth: Current directory depth
#         cfg: Runtime configuration
#
#     Returns:
#         True if depth allows descending, False otherwise
#     """
#     # Allow one more level unless limited
#     if cfg.limits.max_depth == 0:
#         return True
#     return (current_depth + 1) <= cfg.limits.max_depth


# def filter_nav(
#     repo_root: Path,
#     current_meta: DirMeta,
#     cfg: RunConfig,
#     nav: Nav,
#     specs: tuple
# ) -> Tuple[List[str], List[Tuple[str, str]]]:
#     """
#     Validate requested children and return (kept, rejected_with_reasons).
#
#     Args:
#         repo_root: Root directory of the repository
#         current_meta: Pydantic-validated dirmeta for the current directory
#         cfg: Runtime configuration
#         nav: Pydantic-validated LLM navigation output
#         specs: Tuple of (ignore_spec, allow_spec) from spade.ignore.load_specs
#
#     Returns:
#         Tuple of (kept_children, rejected_with_reasons)
#     """
#     # Handle both old format (ignore_spec, allow_spec) and new format (ignore_spec, allow_spec, ignore_lines, allow_lines)
#     if len(specs) == 2:
#         ignore_spec, allow_spec = specs
#     elif len(specs) == 4:
#         ignore_spec, allow_spec, _, _ = specs
#     else:
#         raise ValueError(f"Expected specs tuple of length 2 or 4, got {len(specs)}")
#
#     requested = nav.descend_into or []
#
#     # Deduplicate preserving order
#     seen = set()
#     req = []
#     for c in requested:
#         if c not in seen:
#             seen.add(c)
#             req.append(c)

#     kept: List[str] = []
#     rejected: List[Tuple[str, str]] = []

#     # Depth check (global for this parent)
#     parent_depth_ok = _depth_allows(current_meta.depth, cfg)

#     for child in req:
#         # Basic validation
#         if not _is_single_segment(child):
#             rejected.append((child, REASON_BAD_NAME))
#             continue

#         # Depth check
#         if not parent_depth_ok:
#             rejected.append((child, REASON_DEPTH))
#             continue

#         # Siblings check
#         if current_meta.siblings and child not in current_meta.siblings:
#             rejected.append((child, REASON_NOT_IN_SIBLINGS))
#             continue

#         # Excluded check
#         if current_meta.excluded_children and child in current_meta.excluded_children:
#             rejected.append((child, REASON_EXCLUDED))
#             continue

#         # Ignore rules check
#         child_path = repo_root / current_meta.path / child
#         if should_skip(child_path, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
#             rejected.append((child, REASON_IGNORED))
#             continue

#         kept.append(child)

#     return kept, rejected


# def fallback_children(current_meta: DirMeta, cfg: RunConfig) -> List[str]:
#     """
#     Return deterministic fallback children when LLM navigation fails.
#
#     Args:
#         current_meta: Pydantic-validated dirmeta for the current directory
#         cfg: Runtime configuration
#
#     Returns:
#         List of child names to descend into
#     """
#     # Use siblings if available, otherwise empty
#     if not current_meta.siblings:
#         return []
#
#     # Apply depth limit
#     if not _depth_allows(current_meta.depth, cfg):
#         return []
#
#     # Return all siblings (filtering will be done by caller)
#     return current_meta.siblings
