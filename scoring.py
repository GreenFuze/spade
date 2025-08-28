"""
SPADE Deterministic Scoring
Computes advisory scores for directory children based on metadata signals

NOTE: This file is temporarily commented out as LLM interactions are disabled.
"""

# import math
# import json
# from pathlib import Path
# from typing import Dict, List, Tuple

# from schemas import RunConfig, DirMeta, ChildScore
# from logger import get_logger
# from languages import active_map, aggregate_languages
# from markers import active_rules
# from schemas import load_json, save_json

# logger = get_logger()


# def _marker_weight_index(rules: List[Dict]) -> Dict[str, float]:
#     """
#     Build a lookup from rule.match → rule.weight (for quick sum).
#     If multiple rules yield the same match, keep the max weight.
#
#     Args:
#         rules: List of marker rules
#
#     Returns:
#         Dictionary mapping marker names to their maximum weights
#     """
#     weight_idx: Dict[str, float] = {}
#
#     for rule in rules:
#         match = rule.get("match", "")
#         weight = rule.get("weight", 0.0)
#
#         if match and weight > 0:
#             # Keep the maximum weight if multiple rules have the same match
#             weight_idx[match] = max(weight_idx.get(match, 0.0), weight)
#
#     return weight_idx


# def _marker_strength(markers: List[str], weight_idx: Dict[str, float]) -> Tuple[float, List[str]]:
#     """
#     Sum weights for any marker name present in weight_idx.
#
#     Args:
#         markers: List of marker names from dirmeta.markers
#         weight_idx: Dictionary mapping marker names to weights
#
#     Returns:
#         Tuple of (total_strength, reasons_markers)
#     """
#     total_strength = 0.0
#     contributing_markers = []
#
#     for marker in markers:
#         if marker in weight_idx:
#             weight = weight_idx[marker]
#             total_strength += weight
#             contributing_markers.append(f"marker:{marker}")
#
#     # Cap to top 3 for brevity
#     reasons_markers = contributing_markers[:3]
#
#     return total_strength, reasons_markers


# def _language_signal(child_meta: DirMeta, ext2lang: Dict[str, str]) -> Tuple[float, List[str]]:
#     """
#     Compute language signal from child's ext_histogram.
#
#     Args:
#         child_meta: Directory metadata for the child
#         ext2lang: Extension to language mapping
#
#     Returns:
#         Tuple of (signal_value, reasons_langs)
#     """
#     langs = aggregate_languages(child_meta.ext_histogram, ext2lang)
#     total = sum(count for _, count in langs)
#
#     # Signal is 1.0 if any programming mass exists, 0.0 otherwise
#     signal = 0.0 if total == 0 else 1.0
#
#     # Build reasons (up to 3 entries)
#     reasons_langs = []
#     for lang, count in langs[:3]:
#         reasons_langs.append(f"lang:{lang}({count})")
#
#     return signal, reasons_langs


# def _size_signal(child_meta: DirMeta, k: int) -> Tuple[float, str]:
#     """
#     Compute size signal based on total entries.
#
#     Args:
#         child_meta: Directory metadata for the child
#         k: Number of top entries to consider
#
#     Returns:
#         Tuple of (signal_value, reason)
#     """
#     total_entries = child_meta.counts.files + child_meta.counts.dirs
#
#     if total_entries == 0:
#         return 0.0, "empty"
#
#     # Signal is 1.0 if total entries >= k, 0.0 otherwise
#     signal = 1.0 if total_entries >= k else 0.0
#     reason = f"size:{total_entries}>=?{k}"
#
#     return signal, reason


# def score_children_for_dir(repo_root: Path, cfg: RunConfig, parent_meta: DirMeta) -> Dict[str, ChildScore]:
#     """
#     Compute deterministic scores for all children of a directory.
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#         parent_meta: Directory metadata for the parent
#
#     Returns:
#         Dictionary mapping child names to their scores
#     """
#     if not parent_meta.siblings:
#         return {}
#
#     # Load child metadata
#     ext2lang = active_map(cfg, repo_root)
#     rules = active_rules(cfg, repo_root)
#     weight_idx = _marker_weight_index(rules)
#
#     scores: Dict[str, ChildScore] = {}
#
#     for child_name in parent_meta.siblings:
#         # Load child metadata
#         child_rel = parent_meta.path + "/" + child_name if parent_meta.path != "." else child_name
#         child_meta_path = repo_root / ".spade" / "snapshot" / child_rel / "dirmeta.json"
#
#         try:
#             child_meta = load_json(child_meta_path, DirMeta)
#         except Exception:
#             # Skip if child metadata cannot be loaded
#             continue
#
#         # Compute signals
#         marker_strength, reasons_markers = _marker_strength(child_meta.markers or [], weight_idx)
#         lang_signal, reasons_langs = _language_signal(child_meta, ext2lang)
#         size_signal, reason_size = _size_signal(child_meta, cfg.scoring.size_threshold)
#
#         # Combine signals
#         total_score = marker_strength + lang_signal + size_signal
#
#         # Build reasons list
#         reasons = reasons_markers + reasons_langs + [reason_size]
#
#         scores[child_name] = ChildScore(
#             score=total_score,
#             reasons=reasons
#         )
#
#     return scores
