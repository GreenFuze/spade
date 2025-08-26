"""
SPADE Learning Coordinator
Post-snapshot learning passes for markers and languages with re-scoring
"""

import json
import collections
from pathlib import Path
from typing import Counter

from logger import get_logger
from models import RunConfig, DirMeta, load_json, save_json, save_json_data
from ignore import load_specs, should_skip
from llm import LLMClient
from languages import active_map
from markers import active_rules

logger = get_logger()


def build_name_histogram(repo_root: Path, cfg: RunConfig) -> Counter[str]:
    """
    For each snapshotted directory (depth ≤ max_depth, not ignored), list immediate entries (files+dirs)
    and count by name. Skip entries that match ignore rules. Return Counter of names.
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        
    Returns:
        Counter of entry names with their frequencies
    """
    ignore_spec, allow_spec, _, _ = load_specs(repo_root)
    base = repo_root / ".spade/snapshot"
    hist = collections.Counter()
    
    for dm_path in base.rglob("dirmeta.json"):
        try:
            dm = load_json(dm_path, DirMeta)
        except Exception:
            continue
        
        if dm.ignored_reason:
            continue
        
        dir_fs = repo_root / ("" if dm.path == "." else dm.path)
        try:
            for p in dir_fs.iterdir():
                # filter by ignore specs
                if should_skip(p, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
                    continue
                # Skip .spade directory entries
                if p.name == ".spade":
                    continue
                hist[p.name] += 1
        except OSError:
            # unreadable; already recorded earlier
            continue
    
    return hist


def build_unknown_ext_histogram(repo_root: Path, cfg: RunConfig) -> Counter[str]:
    """
    Aggregate ext_histogram keys across all dirmeta and return those NOT in active ext→lang map (seed∪learned if enabled).
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        
    Returns:
        Counter of unknown extensions with their frequencies
    """
    base = repo_root / ".spade/snapshot"
    ext2lang = active_map(cfg, repo_root)
    hist = collections.Counter()
    
    for dm_path in base.rglob("dirmeta.json"):
        try:
            dm = load_json(dm_path, DirMeta)
        except Exception:
            continue
        
        for ext, n in (dm.ext_histogram or {}).items():
            key = ext.lower().lstrip(".")
            if not key or key in ext2lang:
                continue
            if isinstance(n, int) and n > 0:
                hist[key] += n
    
    return hist


def learn_markers_once(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
    """
    If cfg.learn_markers is True and .spade/markers.learned.json does not exist:
      - Build name histogram
      - Remove entries that are already known markers (seed ∪ learned if use_learned_markers True)
      - Take top-K = cfg.marker_learning.top_k_candidates
      - Call LLM to classify; filter by confidence ≥ cfg.marker_learning.min_confidence
      - Save .spade/markers.learned.json
      
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        llm: LLM client for learning
    """
    if not cfg.learn_markers:
        return
    
    out_path = repo_root / ".spade/markers.learned.json"
    if out_path.exists():
        logger.info("[learn] markers.learned.json exists; skipping learning.")
        return
    
    # build candidates
    hist = build_name_histogram(repo_root, cfg)
    
    # remove already-known markers by NAME (compare to rule.match values)
    known = {r.get("match", "") for r in active_rules(cfg, repo_root)}
    candidates = [n for (n, _) in hist.most_common() if n not in known]
    
    # cap
    K = cfg.marker_learning.top_k_candidates
    if K and K > 0:
        candidates = candidates[:K]
    
    if not candidates:
        logger.info("[learn] no marker candidates.")
        save_json_data(out_path, [])
        return
    
    # call LLM
    res = llm.learn_markers(repo_root.name, cfg.marker_learning.min_confidence, candidates)
    if not isinstance(res, list):
        logger.warning("[learn] marker LLM returned no list; skipping.")
        return
    
    # filter + normalize
    accepted = []
    for item in res:
        try:
            match = str(item.get("match", "")).strip()
            typ = str(item.get("type", "")).strip().lower()
            langs = [str(x).strip().lower() for x in (item.get("languages") or [])]
            weight = float(item.get("weight", 0.7))
            conf = float(item.get("confidence", 0.0))
            
            if not match or conf < cfg.marker_learning.min_confidence:
                continue
            
            accepted.append({
                "match": match,
                "type": typ or "other",
                "languages": langs or None,
                "weight": max(0.0, min(1.0, weight)),
                "confidence": max(0.0, min(1.0, conf)),
                "source": "llm"
            })
        except Exception:
            continue
    
    save_json_data(out_path, accepted)
    logger.info(f"[learn] markers learned: {len(accepted)} saved to {out_path}")


def learn_languages_once(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
    """
    If cfg.learn_languages is True and .spade/languages.learned.json does not exist:
      - Build histogram of unknown extensions across all dirmeta.ext_histogram
      - Take top-K (reuse marker_learning.top_k_candidates)
      - Call LLM to classify; save .spade/languages.learned.json
      
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        llm: LLM client for learning
    """
    if not cfg.learn_languages:
        return
    
    out_path = repo_root / ".spade/languages.learned.json"
    if out_path.exists():
        logger.info("[learn] languages.learned.json exists; skipping learning.")
        return
    
    hist = build_unknown_ext_histogram(repo_root, cfg)
    candidates = [ext for (ext, _) in hist.most_common()]
    
    K = cfg.marker_learning.top_k_candidates
    if K and K > 0:
        candidates = candidates[:K]
    
    if not candidates:
        logger.info("[learn] no unknown extensions.")
        save_json_data(out_path, [])
        return
    
    res = llm.learn_languages(repo_root.name, candidates)
    if not isinstance(res, list):
        logger.warning("[learn] language LLM returned no list; skipping.")
        return
    
    accepted = []
    for item in res:
        try:
            ext = str(item.get("ext", "")).lstrip(".").lower()
            lang = str(item.get("language", "")).strip().lower()
            conf = float(item.get("confidence", 0.0))
            
            if not ext or not lang:
                continue
            
            accepted.append({
                "ext": ext,
                "language": lang,
                "confidence": max(0.0, min(1.0, conf)),
                "source": "llm"
            })
        except Exception:
            continue
    
    save_json_data(out_path, accepted)
    logger.info(f"[learn] languages learned: {len(accepted)} saved to {out_path}")


def post_snapshot_learning_and_rescore(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
    """
    Orchestrate learning passes and re-apply effects if use_* flags are set:
      - learn_markers_once()
      - learn_languages_once()
      - if cfg.use_learned_markers: re-run enrich_markers_and_samples()
      - if cfg.use_learned_markers or cfg.use_learned_languages: re-run compute_deterministic_scoring()
      
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        llm: LLM client for learning
    """
    learn_markers_once(repo_root, cfg, llm)
    learn_languages_once(repo_root, cfg, llm)

    from snapshot import enrich_markers_and_samples, compute_deterministic_scoring

    # Re-apply enrichment/scoring as configured
    if cfg.use_learned_markers:
        logger.info("[learn] re-applying markers enrichment with learned data")
        enrich_markers_and_samples(repo_root, cfg)
    
    if cfg.use_learned_markers or cfg.use_learned_languages:
        logger.info("[learn] re-computing deterministic scoring with learned data")
        compute_deterministic_scoring(repo_root, cfg)
