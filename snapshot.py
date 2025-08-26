"""
SPADE Snapshot Scanner
Walks the repository and produces deterministic directory metadata
"""

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from models import (
    RunConfig, DirMeta, DirCounts, DirSamples, StalenessFingerprint,
    save_json, load_json
)
from ignore import load_specs, should_skip, explain_skip
from markers import active_rules, detect_markers_for_dir
from scoring import score_children_for_dir
from logger import get_logger


def iso8601_z_of(epoch: float) -> str:
    """Convert epoch timestamp to ISO-8601 UTC with trailing Z."""
    dt = datetime.utcfromtimestamp(epoch).replace(tzinfo=timezone.utc)
    return dt.isoformat().replace('+00:00', 'Z')


def sha1_of(name_list: List[str]) -> str:
    """Compute SHA-1 hash of sorted name list joined with '||'."""
    sorted_names = sorted(name_list)
    joined = "||".join(sorted_names)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def get_file_extension(filename: str) -> str:
    """
    Extract file extension following the specified rules:
    - Skip files with NO extension entirely
    - For multi-dot files use the suffix after the final dot (e.g., file.backup.txt → "txt")
    - Hidden dotfiles (e.g., ".env") are kept as ".env" (with the leading dot)
    """
    if filename.startswith('.') and '.' not in filename[1:]:
        # Hidden dotfile with no other dots (e.g., ".env")
        return filename
    elif filename.startswith('.') and '.' in filename[1:]:
        # Hidden file with extension (e.g., ".gitignore")
        return filename.split('.')[-1].lower()
    elif '.' in filename:
        # Multi-dot file, take suffix after last dot
        return filename.split('.')[-1].lower()
    else:
        # No extension
        return ""


def build_snapshot(repo_root: Path, cfg: RunConfig) -> None:
    """
    Walk the repository and build snapshot metadata for all reachable directories.
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
        
    Raises:
        SystemExit: If snapshot directory cannot be created
    """
    logger = get_logger()
    logger.info(f"Starting snapshot build for {repo_root}")
    
    # Ensure snapshot directory exists
    snapshot_dir = repo_root / ".spade" / "snapshot"
    try:
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created snapshot directory: {snapshot_dir}")
    except Exception as e:
        error_msg = f"Failed to create snapshot directory {snapshot_dir}: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # Load ignore/allow specs
    try:
        ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_root)
        logger.debug("Loaded ignore/allow specifications")
    except Exception as e:
        error_msg = f"Failed to load ignore/allow specs: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # DFS traversal starting at repo_root
    _build_snapshot_recursive(
        repo_root, repo_root, snapshot_dir, cfg, ignore_spec, allow_spec, 
        ignore_lines, allow_lines, depth=0, logger=logger
    )
    
    logger.info("Snapshot build completed successfully")


def _build_snapshot_recursive(
    current_dir: Path,
    repo_root: Path,
    snapshot_dir: Path,
    cfg: RunConfig,
    ignore_spec,
    allow_spec,
    ignore_lines: list[str],
    allow_lines: list[str],
    depth: int,
    logger
) -> None:
    """
    Recursively build snapshot metadata for a directory and its children.
    
    Args:
        current_dir: Current directory being processed
        repo_root: Root directory of the repository
        snapshot_dir: Base snapshot directory
        cfg: Runtime configuration
        ignore_spec: Ignore patterns
        allow_spec: Allow patterns
        depth: Current depth (0 for root)
        logger: Logger instance
    """
    # Check depth limit
    if depth > cfg.limits.max_depth:
        logger.debug(f"Skipping {current_dir} - exceeded max depth {cfg.limits.max_depth}")
        return
    
    # Compute relative path
    if current_dir == repo_root:
        rel = "."
    else:
        rel = current_dir.relative_to(repo_root).as_posix()
    
    logger.debug(f"Processing directory: {rel} (depth: {depth})")
    
    # Create output directory
    out_dir = snapshot_dir / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if directory should be skipped
    if should_skip(current_dir, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
        reason = explain_skip(current_dir, repo_root, ignore_spec, allow_spec, ignore_lines, allow_lines, cfg.policies.skip_symlinks)
        logger.info(f"[snapshot] skipped by policy: {rel} ({reason})")
        
        # Build DirMeta for skipped directory
        skipped_meta = DirMeta(
            path=rel,
            depth=depth,
            counts=DirCounts(files=0, dirs=0),
            ext_histogram={},
            markers=[],
            samples=DirSamples(),
            siblings=[],
            excluded_children=[],
            is_symlink=current_dir.is_symlink(),
            ignored_reason=reason or "skipped by policy",
            staleness_fingerprint=StalenessFingerprint(
                latest_modified_time=iso8601_z_of(current_dir.stat().st_mtime),
                total_entries=0,
                name_hash=sha1_of([])
            ),
            deterministic_scoring={}
        )
        
        # Save skipped directory metadata
        save_json(out_dir / "dirmeta.json", skipped_meta)
        return
    
    # Try to list directory entries
    try:
        entries = list(current_dir.iterdir())
    except OSError as e:
        logger.error(f"[snapshot] permission denied: {rel}")
        logger.error(f"Error details: {e}")
        
        # Build DirMeta for unreadable directory
        error_meta = DirMeta(
            path=rel,
            depth=depth,
            counts=DirCounts(files=0, dirs=0),
            ext_histogram={},
            markers=[],
            samples=DirSamples(),
            siblings=[],
            excluded_children=[],
            is_symlink=current_dir.is_symlink(),
            ignored_reason="permission denied",
            staleness_fingerprint=StalenessFingerprint(
                latest_modified_time=iso8601_z_of(current_dir.stat().st_mtime),
                total_entries=0,
                name_hash=sha1_of([])
            ),
            deterministic_scoring={}
        )
        
        # Save error directory metadata
        save_json(out_dir / "dirmeta.json", error_meta)
        return
    
    # Split entries into files and directories
    files = []
    dirs = []
    
    for entry in entries:
        if entry.is_file():
            files.append(entry)
        elif entry.is_dir():
            dirs.append(entry)
    
    # Build counts
    counts = DirCounts(files=len(files), dirs=len(dirs))
    
    # Build extension histogram
    ext_histogram = {}
    for file_path in files:
        filename = file_path.name
        ext = get_file_extension(filename)
        if ext:  # Skip files with no extension
            ext_histogram[ext] = ext_histogram.get(ext, 0) + 1
    
    # Build siblings (child directory names)
    siblings = sorted([d.name for d in dirs])
    
    # Build excluded children
    excluded_children = []
    for child_dir in dirs:
        if should_skip(child_dir, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
            excluded_children.append(child_dir.name)
    
    # Build samples
    sample_dirs = siblings[:cfg.caps.samples.max_dirs]
    sample_files = sorted([f.name for f in files])[:cfg.caps.samples.max_files]
    samples = DirSamples(dirs=sample_dirs, files=sample_files)
    
    # Build staleness fingerprint
    latest_mtime = current_dir.stat().st_mtime
    total_entries = len(files) + len(dirs)
    
    # Build name list for hash (relative to root paths)
    name_list = []
    for entry in entries:
        if rel == ".":
            name_list.append(entry.name)
        else:
            name_list.append(f"{rel}/{entry.name}")
    
    name_hash = sha1_of(name_list)
    
    # Update latest_mtime from immediate entries
    for entry in entries:
        try:
            entry_mtime = entry.stat().st_mtime
            if entry_mtime > latest_mtime:
                latest_mtime = entry_mtime
        except OSError:
            # Skip entries we can't stat
            continue
    
    staleness_fingerprint = StalenessFingerprint(
        latest_modified_time=iso8601_z_of(latest_mtime),
        total_entries=total_entries,
        name_hash=name_hash
    )
    
    # Build DirMeta
    dirmeta = DirMeta(
        path=rel,
        depth=depth,
        counts=counts,
        ext_histogram=ext_histogram,
        markers=[],  # Empty in this task
        samples=samples,
        siblings=siblings,
        excluded_children=excluded_children,
        is_symlink=current_dir.is_symlink(),
        ignored_reason=None,
        staleness_fingerprint=staleness_fingerprint,
        deterministic_scoring={}  # Empty in this task
    )
    
    # Save metadata
    save_json(out_dir / "dirmeta.json", dirmeta)
    logger.debug(f"Saved dirmeta for {rel}: {counts.files} files, {counts.dirs} dirs")
    
    # Recursively process child directories (not excluded)
    for child_dir in dirs:
        if child_dir.name not in excluded_children:
            _build_snapshot_recursive(
                child_dir, repo_root, snapshot_dir, cfg, ignore_spec, allow_spec,
                ignore_lines, allow_lines, depth + 1, logger
            )


def enrich_markers_and_samples(repo_root: Path, cfg: RunConfig) -> None:
    """
    Post-processing pass to inject markers and adjust samples.
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
    """
    logger = get_logger()
    logger.info("Starting marker detection and sample enrichment")
    
    # Load active marker rules
    rules = active_rules(cfg, repo_root)
    logger.debug(f"Loaded {len(rules)} marker rules")
    
    # Walk all existing dirmeta.json files
    snapshot_dir = repo_root / ".spade" / "snapshot"
    if not snapshot_dir.exists():
        logger.warning("Snapshot directory does not exist, skipping marker enrichment")
        return
    
    # Find all dirmeta.json files
    dirmeta_files = list(snapshot_dir.rglob("dirmeta.json"))
    logger.debug(f"Found {len(dirmeta_files)} dirmeta files to process")
    
    for dirmeta_path in dirmeta_files:
        try:
            # Load dirmeta
            dirmeta = load_json(dirmeta_path, DirMeta)
            
            # Skip if directory was ignored (has ignored_reason)
            if dirmeta.ignored_reason:
                continue
            
            # Determine filesystem path
            if dirmeta.path == ".":
                dir_fs_path = repo_root
            else:
                dir_fs_path = repo_root / dirmeta.path
            
            # Detect markers
            markers = detect_markers_for_dir(dir_fs_path, rules)
            
            # Update dirmeta.markers
            dirmeta.markers = markers
            
            # Rebuild samples with priority on markers
            dirmeta.samples = _rebuild_samples_with_marker_priority(
                dir_fs_path, markers, cfg
            )
            
            # Save updated dirmeta
            save_json(dirmeta_path, dirmeta)
            
            logger.info(f"[markers] updated: {dirmeta.path} (found {len(markers)})")
            
        except Exception as e:
            logger.error(f"Failed to process {dirmeta_path}: {e}")
            continue
    
    logger.info("Marker detection and sample enrichment completed")


def _rebuild_samples_with_marker_priority(
    dir_path: Path, markers: List[str], cfg: RunConfig
) -> DirSamples:
    """
    Rebuild samples with priority on markers, then alphabetical fill.
    
    Args:
        dir_path: Directory path
        markers: List of detected marker names
        cfg: Runtime configuration
        
    Returns:
        Updated DirSamples with marker priority
    """
    try:
        entries = list(dir_path.iterdir())
    except OSError:
        return DirSamples()
    
    # Split entries into files and directories
    files = []
    dirs = []
    
    for entry in entries:
        if entry.is_file():
            files.append(entry)
        elif entry.is_dir():
            dirs.append(entry)
    
    # Build samples with marker priority
    sample_dirs = _build_priority_samples([d.name for d in dirs], markers, cfg.caps.samples.max_dirs)
    sample_files = _build_priority_samples([f.name for f in files], markers, cfg.caps.samples.max_files)
    
    return DirSamples(dirs=sample_dirs, files=sample_files)


def _build_priority_samples(names: List[str], markers: List[str], max_count: int) -> List[str]:
    """
    Build sample list with marker priority, then alphabetical fill.
    
    Args:
        names: List of all names (files or directories)
        markers: List of marker names
        max_count: Maximum number of samples to include
        
    Returns:
        List of sample names with marker priority
    """
    if max_count == 0:
        return []
    
    # Extract marker names that are exact matches in the names list
    marker_matches = []
    for marker in markers:
        # For path patterns containing '/', extract the basename
        if '/' in marker:
            basename = marker.split('/')[-1]
            if basename in names:
                marker_matches.append(basename)
        else:
            # Direct name match
            if marker in names:
                marker_matches.append(marker)
    
    # Remove duplicates and sort
    marker_matches = sorted(list(set(marker_matches)))
    
    # Get remaining names (excluding marker matches)
    remaining_names = sorted([name for name in names if name not in marker_matches])
    
    # Build result: markers first, then remaining names
    result = marker_matches + remaining_names
    
    # Apply cap
    return result[:max_count]


def compute_deterministic_scoring(repo_root: Path, cfg: RunConfig) -> None:
    """
    Compute deterministic scoring for all directories in the snapshot.
    
    Args:
        repo_root: Root directory of the repository
        cfg: Runtime configuration
    """
    logger = get_logger()
    logger.info("Starting deterministic scoring computation")
    
    # Walk all existing dirmeta.json files
    snapshot_dir = repo_root / ".spade" / "snapshot"
    if not snapshot_dir.exists():
        logger.warning("Snapshot directory does not exist, skipping scoring computation")
        return
    
    # Find all dirmeta.json files
    dirmeta_files = list(snapshot_dir.rglob("dirmeta.json"))
    logger.debug(f"Found {len(dirmeta_files)} dirmeta files to process for scoring")
    
    updated_count = 0
    
    for dirmeta_path in dirmeta_files:
        try:
            # Load parent metadata
            parent_meta = load_json(dirmeta_path, DirMeta)
            
            # Compute scores for children
            scores = score_children_for_dir(repo_root, cfg, parent_meta)
            
            # Check if scores differ from existing ones
            if parent_meta.deterministic_scoring != scores:
                parent_meta.deterministic_scoring = scores
                save_json(dirmeta_path, parent_meta)
                logger.info(f"[score] updated: {parent_meta.path} (children={len(scores)})")
                updated_count += 1
                
        except Exception as e:
            logger.error(f"Failed to process scoring for {dirmeta_path}: {e}")
            continue
    
    logger.info(f"Deterministic scoring completed. Updated {updated_count} directories.")
