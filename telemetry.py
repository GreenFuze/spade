"""
SPADE Telemetry - Capture and persist run telemetry
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from logger import get_logger


class Telemetry:
    """Capture run telemetry and persist as JSONL."""

    def __init__(self, run_id: str, repo_root: str, model_id: str):
        self.run_id = run_id
        self.repo_root = repo_root
        self.model_id = model_id
        self.started_at = None
        self.finished_at = None
        self.wall_ms = None

        # Scan stats
        self.dir_count = 0
        self.max_depth = 0
        self.max_entries = 0
        self.skipped_dirs = []

        # LLM stats
        self.llm_attempts = 0
        self.llm_prompt_chars = 0
        self.llm_response_chars = 0
        self.llm_latency_ms = 0.0
        self.llm_parse_retries = 0

        # Scaffold stats
        self.scaffold_big_blocks_count = 0
        self.scaffold_conf_min = 0
        self.scaffold_conf_max = 0
        self.scaffold_conf_avg = 0.0
        self.scaffold_questions_count = 0

        # Run result
        self.success = False
        self.error_message = None

    def start(self) -> None:
        """Records monotonic start and UTC timestamp."""
        self.started_at = datetime.now(timezone.utc).isoformat()

    def end(self, success: bool, error_message: Optional[str] = None) -> None:
        """Records completion with success status and optional error."""
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.success = success
        self.error_message = error_message

        if self.started_at:
            start_time = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
            self.wall_ms = (end_time - start_time).total_seconds() * 1000

    def record_scan_stats(
        self, dir_count: int, max_depth: int, max_entries: int, skipped_dirs: List[str]
    ) -> None:
        """Records directory scanning statistics."""
        self.dir_count = dir_count
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.skipped_dirs = skipped_dirs

    def record_llm_stats(
        self,
        attempts: int,
        prompt_chars: int,
        response_chars: int,
        latency_ms: float,
        parse_retries: int,
    ) -> None:
        """Records LLM interaction statistics."""
        self.llm_attempts = attempts
        self.llm_prompt_chars = prompt_chars
        self.llm_response_chars = response_chars
        self.llm_latency_ms = latency_ms
        self.llm_parse_retries = parse_retries

    def record_scaffold_stats(
        self,
        big_blocks_count: int,
        conf_min: int,
        conf_max: int,
        conf_avg: float,
        questions_count: int,
    ) -> None:
        """Records scaffold inference statistics."""
        self.scaffold_big_blocks_count = big_blocks_count
        self.scaffold_conf_min = conf_min
        self.scaffold_conf_max = conf_max
        self.scaffold_conf_avg = conf_avg
        self.scaffold_questions_count = questions_count

    def to_dict(self) -> Dict:
        """Converts telemetry to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "repo_root": self.repo_root,
            "model_id": self.model_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "wall_ms": self.wall_ms,
            "dir_count": self.dir_count,
            "max_depth": self.max_depth,
            "max_entries": self.max_entries,
            "skipped_dirs": self.skipped_dirs,
            "llm_attempts": self.llm_attempts,
            "llm_prompt_chars": self.llm_prompt_chars,
            "llm_response_chars": self.llm_response_chars,
            "llm_latency_ms": self.llm_latency_ms,
            "llm_parse_retries": self.llm_parse_retries,
            "scaffold_big_blocks_count": self.scaffold_big_blocks_count,
            "scaffold_conf_min": self.scaffold_conf_min,
            "scaffold_conf_max": self.scaffold_conf_max,
            "scaffold_conf_avg": self.scaffold_conf_avg,
            "scaffold_questions_count": self.scaffold_questions_count,
            "success": self.success,
            "error_message": self.error_message,
        }

    def append_jsonl(self, path: str | Path) -> None:
        """Appends one line to JSONL file (UTF-8)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict()) + "\n")
