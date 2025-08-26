"""
SPADE Deterministic Scoring
Computes advisory scores for directory children based on metadata signals
"""

import math
import json
from pathlib import Path
from typing import Dict, List, Tuple

from models import RunConfig, DirMeta, ChildScore
from logger import get_logger
from languages import active_map, aggregate_languages
from markers import active_rules
from models import load_json, save_json

logger = get_logger()


def _marker_weight_index(rules: List[Dict]) -> Dict[str, float]:
    """
    Build a lookup from rule.match → rule.weight (for quick sum).
    If multiple rules yield the same match, keep the max weight.
    
    Args:
        rules: List of marker rules
        
    Returns:
        Dictionary mapping marker names to their maximum weights
    """
    weight_idx: Dict[str, float] = {}
    
    for rule in rules:
        match = rule.get("match", "")
        weight = rule.get("weight", 0.0)
        
        if match and weight > 0:
            # Keep the maximum weight if multiple rules have the same match
            weight_idx[match] = max(weight_idx.get(match, 0.0), weight)
    
    return weight_idx


def _marker_strength(markers: List[str], weight_idx: Dict[str, float]) -> Tuple[float, List[str]]:
    """
    Sum weights for any marker name present in weight_idx.
    
    Args:
        markers: List of marker names from dirmeta.markers
        weight_idx: Dictionary mapping marker names to weights
        
    Returns:
        Tuple of (total_strength, reasons_markers)
    """
    total_strength = 0.0
    contributing_markers = []
    
    for marker in markers:
        if marker in weight_idx:
            weight = weight_idx[marker]
            total_strength += weight
            contributing_markers.append(f"marker:{marker}")
    
    # Cap to top 3 for brevity
    reasons_markers = contributing_markers[:3]
    
    return total_strength, reasons_markers


def _language_signal(child_meta: DirMeta, ext2lang: Dict[str, str]) -> Tuple[float, List[str]]:
    """
    Compute language signal from child's ext_histogram.
    
    Args:
        child_meta: Directory metadata for the child
        ext2lang: Extension to language mapping
        
    Returns:
        Tuple of (signal_value, reasons_langs)
    """
    langs = aggregate_languages(child_meta.ext_histogram, ext2lang)
    total = sum(count for _, count in langs)
    
    # Signal is 1.0 if any programming mass exists, 0.0 otherwise
    signal = 0.0 if total == 0 else 1.0
    
    # Build reasons (up to 3 entries)
    reasons_langs = []
    for lang, count in langs[:3]:
        reasons_langs.append(f"lang:{lang}({count})")
    
    return signal, reasons_langs


def _size_signal(child_meta: DirMeta, k: int) -> Tuple[float, str]:
    """
    Compute size signal based on total entries.
    
    Args:
        child_meta: Directory metadata for the child
        k: Size log parameter from config
        
    Returns:
        Tuple of (signal_value, reason_string)
    """
    entries = child_meta.counts.files + child_meta.counts.dirs
    denom = math.log1p(k)
    
    if denom <= 0:
        sig = 0.0
    else:
        sig = min(1.0, math.log1p(entries) / denom)
    
    reason = f"size:dirs={child_meta.counts.dirs},files={child_meta.counts.files}"
    
    return sig, reason


def score_children_for_dir(repo_root: Path, cfg: RunConfig, parent_meta: DirMeta) -> Dict[str, ChildScore]:
    """
    Compute advisory scores for direct child directories of a parent directory.
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        parent_meta: Parent directory metadata
        
    Returns:
        Dictionary mapping child names to their scores
    """
    # Do not score children of ignored nodes
    if parent_meta.ignored_reason is not None:
        return {}
    
    # Do not score children beyond depth (no traversal allowed)
    if cfg.limits.max_depth != 0 and parent_meta.depth >= cfg.limits.max_depth:
        return {}
    
    # Build mappings and indices
    ext2lang = active_map(cfg, repo_root)
    rule_idx = _marker_weight_index(active_rules(cfg, repo_root))
    
    out: Dict[str, ChildScore] = {}
    
    # Process each child in alphabetical order to stabilize results
    for child_name in sorted(parent_meta.siblings):
        # Skip excluded children
        if child_name in parent_meta.excluded_children:
            continue
        
        # Determine child's relative path
        if parent_meta.path == ".":
            child_rel = child_name
        else:
            child_rel = f"{parent_meta.path}/{child_name}"
        
        # Check if child metadata exists
        child_meta_path = repo_root / ".spade" / "snapshot" / child_rel / "dirmeta.json"
        if not child_meta_path.exists():
            # Child is beyond snapshot (e.g., parent at max_depth-1 and we didn't scan deeper)
            continue
        
        try:
            # Load child metadata
            child_meta = load_json(child_meta_path, DirMeta)
            
            # Compute scoring features
            marker_val, reason_markers = _marker_strength(child_meta.markers, rule_idx)
            lang_val, reason_langs = _language_signal(child_meta, ext2lang)
            name_val = 1.0 if child_name in cfg.scoring.name_signals else 0.0
            size_val, reason_size = _size_signal(child_meta, cfg.scoring.size_log_k)
            
            # Compute weighted score
            score = (
                cfg.scoring.weights.marker * marker_val +
                cfg.scoring.weights.lang * lang_val +
                cfg.scoring.weights.name * name_val +
                cfg.scoring.weights.size * size_val
            )
            
            # Build reasons list
            reasons = []
            if marker_val > 0:
                reasons.extend(reason_markers)
            if lang_val > 0:
                reasons.extend(reason_langs)
            if name_val > 0:
                reasons.append(f"name:{child_name}")
            if size_val > 0:
                reasons.append(reason_size)
            
            # Cap reasons for brevity
            reasons = reasons[:6]
            
            out[child_name] = ChildScore(
                score=round(float(score), 3),
                reasons=reasons
            )
            
        except Exception as e:
            logger.warning(f"[score] failed to score child {child_name} in {parent_meta.path}: {e}")
            continue
    
    return out
