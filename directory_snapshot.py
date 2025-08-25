"""
SPADE Directory Snapshot
Directory scanning and filtering functionality
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from logger import get_logger


class DirectorySnapshot:
    """Encapsulates directory scanning outputs (no file contents)."""
    
    # TODO: in the future, remove this. This is for safety for now.
    SKIP_DIRS = {".git", ".spade", ".idea", ".vscode", "__pycache__", "node_modules", "dist", "build", "target", "bin", "obj"}
    
    def __init__(self, root: Path, max_depth: int = 3, max_entries: int = 40, logger: logging.Logger = None):
        self.root = root
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.logger = logger or get_logger()
    
    def scan(self) -> List[Dict]:
        """Scans directory tree and returns structured entries."""
        max_depth_str = "unlimited" if self.max_depth == 0 else str(self.max_depth)
        max_entries_str = "unlimited" if self.max_entries == 0 else str(self.max_entries)
        self.logger.debug(f"Starting directory scan of {self.root} (max_depth={max_depth_str}, max_entries={max_entries_str})")
        entries = []
        skipped_dirs = []
        
        # Determine scan depth: 0 = unlimited, otherwise use specified depth
        scan_depth = None if self.max_depth == 0 else self.max_depth
        
        if scan_depth is None:
            # Unlimited depth scan
            self.logger.debug("Performing unlimited depth scan")
            for root, dirnames, _ in os.walk(self.root):
                try:
                    current_depth = len(Path(root).relative_to(self.root).parts)
                    for dirname in sorted(dirnames):
                        dir_path = Path(root) / dirname
                        if self._should_skip_dir(dir_path):
                            skipped_dirs.append(str(dir_path.relative_to(self.root)))
                            self.logger.debug(f"Skipping directory: {dir_path}")
                            continue
                        
                        entry = self._create_entry(dir_path, current_depth + 1)
                        entries.append(entry)
                        self.logger.debug(f"Added directory entry: {entry['path']} (depth={current_depth + 1}, entries={entry['entry_count']})")
                except ValueError:
                    # Skip if path is not relative to root
                    continue
        else:
            # Limited depth scan
            for depth in range(scan_depth + 1):
                self.logger.debug(f"Scanning directories at depth {depth}")
                for dir_path in self._get_dirs_at_depth(depth):
                    if self._should_skip_dir(dir_path):
                        skipped_dirs.append(str(dir_path.relative_to(self.root)))
                        self.logger.debug(f"Skipping directory: {dir_path}")
                        continue
                    
                    entry = self._create_entry(dir_path, depth)
                    entries.append(entry)
                    self.logger.debug(f"Added directory entry: {entry['path']} (depth={depth}, entries={entry['entry_count']})")
        
        self.logger.debug(f"Directory scan complete: {len(entries)} directories found, {len(skipped_dirs)} skipped")
        return entries
    
    def _get_dirs_at_depth(self, depth: int) -> List[Path]:
        """Gets all directories at specified depth, sorted for determinism."""
        if depth == 0:
            return [self.root]
        
        dirs = []
        try:
            for root, dirnames, _ in os.walk(self.root):
                try:
                    current_depth = len(Path(root).relative_to(self.root).parts)
                    if current_depth == depth - 1:
                        for dirname in sorted(dirnames):
                            dir_path = Path(root) / dirname
                            if not self._should_skip_dir(dir_path):
                                dirs.append(dir_path)
                except ValueError:
                    # Skip if path is not relative to root (shouldn't happen in normal usage)
                    continue
        except Exception as e:
            # Fail fast on unexpected errors
            self.logger.error(f"Failed to scan directories at depth {depth}: {e}")
            raise RuntimeError(f"Failed to scan directories at depth {depth}: {e}")
        
        return sorted(dirs)
    
    def _should_skip_dir(self, dir_path: Path) -> bool:
        """Determines if directory should be skipped."""
        return dir_path.name in self.SKIP_DIRS
    
    def _create_entry(self, dir_path: Path, depth: int) -> Dict:
        """Creates a directory entry with statistics."""
        try:
            items = list(dir_path.iterdir())
            entry_count = len(items)
            
            subdirs = [item for item in items if item.is_dir() and not self._should_skip_dir(item)]
            subdir_count = len(subdirs)
            
            # Sample entries (files and dirs, sorted)
            # 0 = unlimited, otherwise use specified limit
            sample_limit = None if self.max_entries == 0 else self.max_entries
            sample_entries = sorted([item.name for item in items])
            if sample_limit is not None:
                sample_entries = sample_entries[:sample_limit]
            
            return {
                "path": str(dir_path.relative_to(self.root)) if dir_path != self.root else ".",
                "depth": depth,
                "entry_count": entry_count,
                "subdir_count": subdir_count,
                "sample_entries": sample_entries
            }
        except PermissionError:
            # Handle permission errors gracefully
            self.logger.warning(f"Permission denied accessing directory: {dir_path}")
            return {
                "path": str(dir_path.relative_to(self.root)) if dir_path != self.root else ".",
                "depth": depth,
                "entry_count": 0,
                "subdir_count": 0,
                "sample_entries": []
            }
