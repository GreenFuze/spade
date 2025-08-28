"""
SPADE State Management
Unified SQLite-based state management for files and directories
"""

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from logger import get_logger
from schemas import SpadeStateEntryFile, SpadeStateEntryDir, SpadeStateMetadata, DirCounts, DirSamples, StalenessFingerprint, ChildScore
from ignore import load_specs, should_skip, explain_skip
from markers import active_rules, detect_markers_for_dir
import hashlib


class SpadeState:
    """Unified state management using SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    path TEXT PRIMARY KEY,
                    parent TEXT,
                    children TEXT,
                    visited BOOLEAN DEFAULT FALSE,
                    visited_at TEXT,
                    depth INTEGER,
                    is_file BOOLEAN,
                    confidence INTEGER DEFAULT 0,
                    
                    -- File-specific fields (NULL for directories)
                    extension TEXT,
                    file_size INTEGER,
                    last_modified TEXT,
                    
                    -- Directory-specific fields (NULL for files)
                    files_count INTEGER,
                    dirs_count INTEGER,
                    ext_histogram TEXT,
                    siblings TEXT,
                    excluded_children TEXT,
                    is_symlink BOOLEAN,
                    ignored_reason TEXT,
                    markers TEXT,
                    samples TEXT,
                    staleness_fingerprint TEXT,
                    
                    -- Analysis fields (for both files and dirs)
                    analysis TEXT,
                    summary TEXT,
                    tags TEXT,
                    deterministic_scoring TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_id INTEGER,
                    path TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """
            )

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_visited ON nodes(visited)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_is_file ON nodes(is_file)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_depth ON nodes(depth)")

    def _iso8601_z_of(self, epoch: float) -> str:
        """Convert epoch timestamp to ISO8601 format with Z timezone."""
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _sha1_of(self, name_list: List[str]) -> str:
        """Compute SHA1 hash of a list of names."""
        sorted_names = sorted(name_list)
        content = "\n".join(sorted_names)
        content_bytes = content.encode("utf-8")
        sha1_hash = hashlib.sha1(content_bytes)
        return sha1_hash.hexdigest()

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename, handling multi-dot extensions."""
        if filename.startswith("."):
            if "." in filename[1:]:
                last_dot = filename.rindex(".")
                return filename[last_dot:]
            else:
                return ""

        if "." in filename:
            last_dot = filename.rindex(".")
            return filename[last_dot:]
        else:
            return ""

    def build_filesystem_tree(self, repo_root: Path, config) -> None:
        """Parse filesystem and populate all non-LLM data upfront."""
        get_logger().info(f"Building filesystem tree for {repo_root}")

        # Load ignore/allow specs
        ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_root)

        # Build tree recursively starting from root
        self._build_tree_recursive(repo_root, ".", None, 0, ignore_spec, allow_spec, ignore_lines, allow_lines, config)  # no parent for root  # depth 0

        # Post-processing passes
        self._enrich_markers_and_samples(repo_root, config)
        self._compute_deterministic_scoring(repo_root, config)

        # Update metadata
        self._update_metadata(repo_root)

        get_logger().info("Filesystem tree built successfully")

    def _build_tree_recursive(self, current_path: Path, rel_path: str, parent_path: Optional[str], depth: int, ignore_spec, allow_spec, ignore_lines: List[str], allow_lines: List[str], config) -> None:
        """Recursively build tree structure."""
        # Check depth limit
        if config.limits.max_depth != 0 and depth > config.limits.max_depth:
            get_logger().debug(f"Skipping {rel_path} - exceeded max depth {config.limits.max_depth}")
            return

        get_logger().debug(f"Building tree node: {rel_path} (depth: {depth})")

        # Check if should be skipped
        if should_skip(current_path, current_path.parent, ignore_spec, allow_spec, config.policies.skip_symlinks):
            reason = explain_skip(current_path, current_path.parent, ignore_spec, allow_spec, ignore_lines, allow_lines, config.policies.skip_symlinks)
            get_logger().info(f"[tree] skipped by policy: {rel_path} ({reason})")

            # Create skipped directory entry
            skipped_entry = SpadeStateEntryDir(
                path=rel_path,
                parent=parent_path,
                children=[],
                visited=False,
                depth=depth,
                confidence=0,
                counts=DirCounts(files=0, dirs=0),
                ext_histogram=None,
                siblings=[],
                excluded_children=[],
                is_symlink=current_path.is_symlink(),
                ignored_reason=reason or "skipped by policy",
                markers=None,
                samples=None,
                staleness_fingerprint=StalenessFingerprint(latest_modified_time=self._iso8601_z_of(time.time()), total_entries=0, name_hash=self._sha1_of([])),
                analysis=None,
                summary=None,
                tags=None,
                deterministic_scoring=None,
            )
            self._save_entry(skipped_entry)
            return

        # Determine if it's a file or directory
        if current_path.is_file():
            self._build_file_entry(current_path, rel_path, parent_path, depth)
        elif current_path.is_dir():
            self._build_directory_entry(current_path, rel_path, parent_path, depth, ignore_spec, allow_spec, ignore_lines, allow_lines, config)
        else:
            get_logger().warning(f"Skipping {rel_path} - not a file or directory")

    def _build_file_entry(self, file_path: Path, rel_path: str, parent_path: Optional[str], depth: int) -> None:
        """Build entry for a file."""
        try:
            stat = file_path.stat()
            extension = self._get_file_extension(file_path.name)

            file_entry = SpadeStateEntryFile(path=rel_path, parent=parent_path, visited=False, depth=depth, confidence=0, extension=extension, file_size=stat.st_size, last_modified=self._iso8601_z_of(stat.st_mtime), analysis=None, summary=None, tags=None)

            self._save_entry(file_entry)
            get_logger().debug(f"Added file: {rel_path}")

        except OSError as e:
            get_logger().error(f"Failed to process file {rel_path}: {e}")

    def _build_directory_entry(self, dir_path: Path, rel_path: str, parent_path: Optional[str], depth: int, ignore_spec, allow_spec, ignore_lines: List[str], allow_lines: List[str], config) -> None:
        """Build entry for a directory."""
        try:
            entries = list(dir_path.iterdir())
        except OSError as e:
            # Handle inaccessible directory
            error_type = "permission denied"
            if hasattr(e, "errno"):
                if e.errno == 13:
                    error_type = "permission denied"
                elif e.errno == 2:
                    error_type = "broken symlink"
                elif e.errno == 5:
                    error_type = "access denied"
                else:
                    error_type = f"OS error {e.errno}"

            get_logger().error(f"[tree] cannot access directory: {rel_path} ({error_type})")

            # Create error directory entry
            error_entry = SpadeStateEntryDir(
                path=rel_path,
                parent=parent_path,
                children=[],
                visited=False,
                depth=depth,
                confidence=0,
                counts=DirCounts(files=0, dirs=0),
                ext_histogram=None,
                siblings=[],
                excluded_children=[],
                is_symlink=dir_path.is_symlink(),
                ignored_reason=error_type,
                markers=None,
                samples=None,
                staleness_fingerprint=StalenessFingerprint(latest_modified_time=self._iso8601_z_of(time.time()), total_entries=0, name_hash=self._sha1_of([])),
                analysis=None,
                summary=None,
                tags=None,
                deterministic_scoring=None,
            )
            self._save_entry(error_entry)
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
            ext = self._get_file_extension(filename)
            if ext:
                ext_histogram[ext] = ext_histogram.get(ext, 0) + 1

        # Build siblings (child directory names)
        siblings = sorted([d.name for d in dirs])

        # Build excluded children
        excluded_children = []
        for child_dir in dirs:
            if should_skip(child_dir, dir_path, ignore_spec, allow_spec, config.policies.skip_symlinks):
                excluded_children.append(child_dir.name)

        # Build samples
        sample_dirs = siblings[: config.caps.samples.max_dirs]
        sample_files = sorted([f.name for f in files])[: config.caps.samples.max_files]
        samples = DirSamples(dirs=sample_dirs, files=sample_files)

        # Build staleness fingerprint
        latest_mtime = dir_path.stat().st_mtime
        total_entries = len(files) + len(dirs)

        # Build name list for hash
        name_list = []
        for entry in entries:
            if rel_path == ".":
                name_list.append(entry.name)
            else:
                name_list.append(f"{rel_path}/{entry.name}")

        name_hash = self._sha1_of(name_list)

        # Update latest_mtime from immediate entries
        for entry in entries:
            try:
                entry_mtime = entry.stat().st_mtime
                if entry_mtime > latest_mtime:
                    latest_mtime = entry_mtime
            except OSError:
                continue

        # Create directory entry
        dir_entry = SpadeStateEntryDir(
            path=rel_path,
            parent=parent_path,
            children=[],  # Will be populated below
            visited=False,
            depth=depth,
            confidence=0,
            counts=counts,
            ext_histogram=ext_histogram,
            siblings=siblings,
            excluded_children=excluded_children,
            is_symlink=dir_path.is_symlink(),
            ignored_reason=None,
            markers=None,  # Will be populated in post-processing
            samples=samples,
            staleness_fingerprint=StalenessFingerprint(latest_modified_time=self._iso8601_z_of(latest_mtime), total_entries=total_entries, name_hash=name_hash),
            analysis=None,
            summary=None,
            tags=None,
            deterministic_scoring=None,  # Will be populated in post-processing
        )

        # Save directory entry
        self._save_entry(dir_entry)

        # Recursively process child directories (not excluded)
        child_paths = []
        for child_dir in dirs:
            if child_dir.name not in excluded_children:
                child_rel_path = f"{rel_path}/{child_dir.name}" if rel_path != "." else child_dir.name
                child_paths.append(child_rel_path)

                self._build_tree_recursive(child_dir, child_rel_path, rel_path, depth + 1, ignore_spec, allow_spec, ignore_lines, allow_lines, config)

        # Update children list
        dir_entry.children = child_paths
        self._save_entry(dir_entry)

    def _enrich_markers_and_samples(self, repo_root: Path, config) -> None:
        """Post-processing pass to inject markers and adjust samples."""
        get_logger().info("Starting marker detection and sample enrichment")

        # Load active marker rules
        rules = active_rules(config, repo_root)
        get_logger().debug(f"Loaded {len(rules)} marker rules")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT path FROM nodes WHERE is_file = FALSE")
            for (path,) in cursor.fetchall():
                try:
                    # Skip if directory was ignored
                    cursor2 = conn.execute("SELECT ignored_reason FROM nodes WHERE path = ?", (path,))
                    ignored_reason = cursor2.fetchone()[0]
                    if ignored_reason:
                        continue

                    # Determine filesystem path
                    if path == ".":
                        dir_fs_path = repo_root
                    else:
                        dir_fs_path = repo_root / path

                    # Detect markers
                    markers = detect_markers_for_dir(dir_fs_path, rules)

                    # Update markers in database
                    conn.execute("UPDATE nodes SET markers = ? WHERE path = ?", (json.dumps(markers) if markers else None, path))

                    get_logger().debug(f"[markers] updated: {path} (found {len(markers)})")

                except Exception as e:
                    get_logger().error(f"Failed to process {path} for markers: {e}")
                    continue

        get_logger().info("Marker detection and sample enrichment completed")

    def _compute_deterministic_scoring(self, repo_root: Path, config) -> None:
        """Post-processing pass to compute deterministic scoring for all directories."""
        get_logger().info("Starting deterministic scoring computation")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT path FROM nodes WHERE is_file = FALSE")
            for (path,) in cursor.fetchall():
                try:
                    # Skip if directory was ignored
                    cursor2 = conn.execute("SELECT ignored_reason FROM nodes WHERE path = ?", (path,))
                    ignored_reason = cursor2.fetchone()[0]
                    if ignored_reason:
                        continue

                    # Get directory entry
                    dir_entry = self.get_entry(path)
                    if not isinstance(dir_entry, SpadeStateEntryDir):
                        continue

                    # Compute deterministic scoring for this directory (disabled for now)
                    # from scoring import score_children_for_dir

                    # try:
                    #     scoring = score_children_for_dir(repo_root, config, dir_entry)
                    # except Exception as scoring_error:
                    #     get_logger().warning(f"Scoring failed for {path}: {scoring_error}")
                    #     scoring = None
                    scoring = None

                    # Update scoring in database
                    if scoring:
                        scoring_dict = {k: v.model_dump() for k, v in scoring.items()}
                        conn.execute("UPDATE nodes SET deterministic_scoring = ? WHERE path = ?", (json.dumps(scoring_dict), path))
                        get_logger().debug(f"[scoring] updated: {path} ({len(scoring)} children scored)")
                    else:
                        get_logger().debug(f"[scoring] skipped: {path} (scoring disabled)")

                except Exception as e:
                    get_logger().error(f"Failed to process {path} for scoring: {e}")
                    continue

        get_logger().info("Deterministic scoring computation completed")

    def _update_metadata(self, repo_root: Path) -> None:
        """Update metadata in database."""
        metadata = SpadeStateMetadata(repo_root=str(repo_root), created_at=self._iso8601_z_of(time.time()), last_updated=self._iso8601_z_of(time.time()), version="1.0")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM metadata")
            conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ("repo_root", metadata.repo_root))
            conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ("created_at", metadata.created_at))
            conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ("last_updated", metadata.last_updated))
            conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ("version", metadata.version))

    def _save_entry(self, entry: Union[SpadeStateEntryFile, SpadeStateEntryDir]) -> None:
        """Save entry to database."""
        with sqlite3.connect(self.db_path) as conn:
            if isinstance(entry, SpadeStateEntryFile):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO nodes (
                        path, parent, visited, visited_at, depth, is_file, confidence,
                        extension, file_size, last_modified,
                        analysis, summary, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.path,
                        entry.parent,
                        entry.visited,
                        entry.visited_at,
                        entry.depth,
                        True,
                        entry.confidence,
                        entry.extension,
                        entry.file_size,
                        entry.last_modified,
                        json.dumps(entry.analysis) if entry.analysis else None,
                        entry.summary,
                        json.dumps(entry.tags) if entry.tags else None,
                    ),
                )
            else:  # SpadeStateEntryDir
                conn.execute(
                    """
                    INSERT OR REPLACE INTO nodes (
                        path, parent, children, visited, visited_at, depth, is_file, confidence,
                        files_count, dirs_count, ext_histogram, siblings, excluded_children,
                        is_symlink, ignored_reason, markers, samples, staleness_fingerprint,
                        analysis, summary, tags, deterministic_scoring
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.path,
                        entry.parent,
                        json.dumps(entry.children),
                        entry.visited,
                        entry.visited_at,
                        entry.depth,
                        False,
                        entry.confidence,
                        entry.counts.files,
                        entry.counts.dirs,
                        json.dumps(entry.ext_histogram) if entry.ext_histogram else None,
                        json.dumps(entry.siblings) if entry.siblings else None,
                        json.dumps(entry.excluded_children) if entry.excluded_children else None,
                        entry.is_symlink,
                        entry.ignored_reason,
                        json.dumps(entry.markers) if entry.markers else None,
                        json.dumps(entry.samples.model_dump()) if entry.samples else None,
                        json.dumps(entry.staleness_fingerprint.model_dump()) if entry.staleness_fingerprint else None,
                        json.dumps(entry.analysis) if entry.analysis else None,
                        entry.summary,
                        json.dumps(entry.tags) if entry.tags else None,
                        json.dumps({k: v.model_dump() for k, v in entry.deterministic_scoring.items()}) if entry.deterministic_scoring else None,
                    ),
                )

    def get_entry(self, path: str) -> Union[SpadeStateEntryFile, SpadeStateEntryDir]:
        """Get entry by path, returns appropriate type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM nodes WHERE path = ?", (path,))
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Entry not found: {path}")

            # Convert row to dict
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))

            if data["is_file"]:
                return SpadeStateEntryFile(
                    path=data["path"],
                    parent=data["parent"],
                    visited=data["visited"],
                    visited_at=data["visited_at"],
                    depth=data["depth"],
                    confidence=data["confidence"],
                    extension=data["extension"],
                    file_size=data["file_size"],
                    last_modified=data["last_modified"],
                    analysis=json.loads(data["analysis"]) if data["analysis"] else None,
                    summary=data["summary"],
                    tags=json.loads(data["tags"]) if data["tags"] else None,
                )
            else:
                return SpadeStateEntryDir(
                    path=data["path"],
                    parent=data["parent"],
                    children=json.loads(data["children"]) if data["children"] else [],
                    visited=data["visited"],
                    visited_at=data["visited_at"],
                    depth=data["depth"],
                    confidence=data["confidence"],
                    counts=DirCounts(files=data["files_count"], dirs=data["dirs_count"]),
                    ext_histogram=json.loads(data["ext_histogram"]) if data["ext_histogram"] else None,
                    siblings=json.loads(data["siblings"]) if data["siblings"] else None,
                    excluded_children=json.loads(data["excluded_children"]) if data["excluded_children"] else None,
                    is_symlink=data["is_symlink"],
                    ignored_reason=data["ignored_reason"],
                    markers=json.loads(data["markers"]) if data["markers"] else None,
                    samples=DirSamples(**json.loads(data["samples"])) if data["samples"] else None,
                    staleness_fingerprint=StalenessFingerprint(**json.loads(data["staleness_fingerprint"])) if data["staleness_fingerprint"] else None,
                    analysis=json.loads(data["analysis"]) if data["analysis"] else None,
                    summary=data["summary"],
                    tags=json.loads(data["tags"]) if data["tags"] else None,
                    deterministic_scoring={k: ChildScore(**v) for k, v in json.loads(data["deterministic_scoring"]).items()} if data["deterministic_scoring"] else None,
                )

    def get_root_dir(self) -> SpadeStateEntryDir:
        """Get root directory entry."""
        return self.get_entry(".")

    def get_unvisited_dirs(self) -> List[str]:
        """Get unvisited directories only."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT path FROM nodes WHERE is_file = FALSE AND visited = FALSE")
            return [row[0] for row in cursor.fetchall()]

    def mark_visited(self, path: str) -> None:
        """Mark entry as visited."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE nodes SET visited = TRUE, visited_at = ? WHERE path = ?", (self._iso8601_z_of(time.time()), path))

    def add_telemetry(self, step_id: int, path: str, data: dict) -> None:
        """Add telemetry entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO telemetry (step_id, path, timestamp, data) VALUES (?, ?, ?, ?)", (step_id, path, self._iso8601_z_of(time.time()), json.dumps(data)))

    def get_statistics(self) -> dict:
        """Compute statistics on-demand with SQL queries."""
        with sqlite3.connect(self.db_path) as conn:
            # Total counts
            cursor = conn.execute("SELECT COUNT(*) FROM nodes WHERE is_file = TRUE")
            total_files = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM nodes WHERE is_file = FALSE")
            total_dirs = cursor.fetchone()[0]

            # Visited counts
            cursor = conn.execute("SELECT COUNT(*) FROM nodes WHERE is_file = TRUE AND visited = TRUE")
            visited_files = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM nodes WHERE is_file = FALSE AND visited = TRUE")
            visited_dirs = cursor.fetchone()[0]

            # Max depth
            cursor = conn.execute("SELECT MAX(depth) FROM nodes")
            max_depth = cursor.fetchone()[0] or 0

            return {"total_files": total_files, "total_dirs": total_dirs, "visited_files": visited_files, "visited_dirs": visited_dirs, "max_depth": max_depth, "timestamp": self._iso8601_z_of(time.time())}

    def get_parent(self, path: str) -> Optional[SpadeStateEntryDir]:
        """Get parent directory entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT parent FROM nodes WHERE path = ?", (path,))
            result = cursor.fetchone()
            if result and result[0]:
                return self.get_entry(result[0])
            return None

    def get_sub_directories(self, path: str, include_visited: bool = True) -> List[SpadeStateEntryDir]:
        """Get child directories of a directory."""
        with sqlite3.connect(self.db_path) as conn:
            if include_visited:
                cursor = conn.execute("SELECT path FROM nodes WHERE parent = ? AND is_file = FALSE", (path,))
            else:
                cursor = conn.execute("SELECT path FROM nodes WHERE parent = ? AND is_file = FALSE AND visited = FALSE", (path,))

            return [self.get_entry(row[0]) for row in cursor.fetchall()]

    def get_files(self, path: str, include_visited: bool = True) -> List[SpadeStateEntryFile]:
        """Get files in a directory."""
        with sqlite3.connect(self.db_path) as conn:
            if include_visited:
                cursor = conn.execute("SELECT path FROM nodes WHERE parent = ? AND is_file = TRUE", (path,))
            else:
                cursor = conn.execute("SELECT path FROM nodes WHERE parent = ? AND is_file = TRUE AND visited = FALSE", (path,))

            return [self.get_entry(row[0]) for row in cursor.fetchall()]

    def get_file_content(self, path: str) -> bytes:
        """Read file content from filesystem."""
        # Get the repo root from metadata
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM metadata WHERE key = 'repo_root'")
            result = cursor.fetchone()
            if not result:
                raise ValueError("Repository root not found in metadata")
            repo_root = Path(result[0])

        # Construct full file path
        if path == ".":
            file_path = repo_root
        else:
            file_path = repo_root / path

        # Read file content
        try:
            return file_path.read_bytes()
        except OSError as e:
            raise OSError(f"Failed to read file {path}: {e}")

    def save_entry(self, entry: Union[SpadeStateEntryFile, SpadeStateEntryDir]) -> None:
        """Save entry to database."""
        self._save_entry(entry)
