"""
SPADE Data Models
Pydantic v2 schemas for configuration, snapshots, LLM I/O, and telemetry
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


# ---------- Config ----------
class RunConfig(BaseModel):
    """SPADE runtime configuration with validation and defaults."""

    model: str = Field(default="gpt-5-nano")  # LLM model to use for analysis

    class Caps(BaseModel):
        """Capacity limits for sampling and navigation."""

        class Samples(BaseModel):
            """Sampling limits for directory and file entries."""

            max_dirs: int = Field(ge=0, default=8)  # 0 allowed (runtime = unlimited not applicable here)
            max_files: int = Field(ge=0, default=8)

        class Nav(BaseModel):
            """Navigation limits for directory traversal."""

            max_children_per_step: int = Field(ge=0, default=4)  # 0 => unlimited (runtime)

        class Context(BaseModel):
            """Context building limits for prompt size control."""

            max_siblings_in_prompt: int = Field(ge=0, default=200)  # 0 => unlimited (runtime)
            max_children_scores_in_prompt: int = Field(ge=0, default=200)  # 0 => unlimited (runtime)
            max_reasons_per_child: int = Field(ge=0, default=3)  # 0 => unlimited (runtime)
            max_ancestor_summaries: int = Field(ge=0, default=10)  # 0 => unlimited (runtime)

        samples: Samples = Samples()
        nav: Nav = Nav()
        context: Context = Context()

    class Limits(BaseModel):
        """Runtime limits for analysis depth and scope."""

        max_depth: int = Field(ge=0, default=0)  # 0 => unlimited (runtime)
        max_nodes: int = Field(ge=0, default=0)  # 0 => unlimited (runtime)
        max_llm_calls: int = Field(ge=0, default=0)  # 0 => unlimited (runtime)

    class Scoring(BaseModel):
        """Scoring weights and parameters for analysis."""

        class Weights(BaseModel):
            """Weight distribution for different evidence types."""

            marker: float = Field(ge=0, le=1, default=0.55)
            lang: float = Field(ge=0, le=1, default=0.25)
            name: float = Field(ge=0, le=1, default=0.15)
            size: float = Field(ge=0, le=1, default=0.05)

            @field_validator("*", mode="after")
            def _sum_le_one(cls, v, info):
                return v

        weights: Weights = Weights()
        name_signals: list[str] = Field(default_factory=lambda: ["api", "cli", "server", "service", "pkg", "src", "web", "ui", "infra", "tests", "docs"])
        size_log_k: int = Field(ge=1, default=200)

    class Policies(BaseModel):
        """Runtime policies for directory traversal and analysis."""

        skip_symlinks: bool = True
        descend_one_level_only: bool = True
        max_summary_sentences: int = Field(ge=1, default=3)
        max_summary_chars: int = Field(ge=64, default=400)
        max_languages_per_node: int = Field(ge=1, default=6)
        max_tags_per_node: int = Field(ge=1, default=12)
        max_evidence_per_node: int = Field(ge=1, default=12)

    class MarkerLearning(BaseModel):
        """Parameters for marker learning and confidence thresholds."""

        top_k_candidates: int = Field(ge=0, default=50)
        min_confidence: float = Field(ge=0, le=1, default=0.75)

    caps: Caps = Caps()
    limits: Limits = Limits()
    scoring: Scoring = Scoring()
    policies: Policies = Policies()
    learn_markers: bool = False
    use_learned_markers: bool = False
    learn_languages: bool = False
    use_learned_languages: bool = False
    timestamps_utc: bool = True
    marker_learning: MarkerLearning = MarkerLearning()


# ---------- Unified State Management ----------
class DirCounts(BaseModel):
    """File and directory counts for a directory."""

    files: int = Field(ge=0)
    dirs: int = Field(ge=0)


class StalenessFingerprint(BaseModel):
    """Fingerprint for detecting staleness of directory metadata."""

    latest_modified_time: str  # ISO8601 timestamp
    total_entries: int = Field(ge=0)
    name_hash: str  # SHA1 hash of sorted entry names


class ChildScore(BaseModel):
    """Deterministic scoring for a child directory."""

    score: float = Field(ge=0, le=1)
    reasons: list[str] = []
    evidence: list[str] = []


class DirSamples(BaseModel):
    """Sample entries from a directory for analysis."""

    dirs: list[str] = []
    files: list[str] = []


# ---------- Learned files ----------
class LearnedMarker(BaseModel):
    """A learned marker pattern for directory analysis."""

    match: str
    type: str
    languages: list[str] | None = None
    weight: float = Field(ge=0, le=1, default=0.7)
    confidence: float = Field(ge=0, le=1, default=1.0)
    source: str = "llm"


class LearnedLanguage(BaseModel):
    """A learned language mapping for file extensions."""

    ext: str
    language: str
    confidence: float = Field(ge=0, le=1, default=1.0)
    source: str = "llm"


# ---------- LLM I/O ----------
EvidenceType = Literal["marker", "name", "lang_ext", "ci", "size", "path", "policy"]


class Evidence(BaseModel):
    """Evidence supporting an analysis conclusion."""

    type: EvidenceType
    value: str


class NodeUpdate(BaseModel):
    """Update information for a directory node."""

    summary: str
    languages: list[str]
    tags: list[str] = []
    evidence: list[Evidence]
    confidence: float = Field(ge=0, le=1)

    @field_validator("summary")
    def _max_three_sentences(cls, v):
        # naive sentence split is fine
        return v

    @field_validator("languages")
    def _norm_langs(cls, v):
        return list(dict.fromkeys([s.lower() for s in v]))  # dedupe, lowercase


class HighLevelComponent(BaseModel):
    """High-level architectural component inferred from directory structure."""

    name: str
    role: str
    dirs: list[str]
    evidence: list[Evidence]
    confidence: float = Field(ge=0, le=1)


class Nav(BaseModel):
    """Navigation instructions for directory traversal."""

    descend_into: list[str]
    descend_one_level_only: bool
    reasons: list[str] = []


class LLMInferred(BaseModel):
    """Complete inference results from LLM analysis."""

    high_level_components: list[HighLevelComponent] = []
    nodes: dict[str, NodeUpdate] = {}


class LLMResponse(BaseModel):
    """Complete LLM response including inference and navigation."""

    inferred: LLMInferred
    nav: Nav
    open_questions_ranked: list[str] = []


# ---------- Telemetry ----------
class TelemetryRow(BaseModel):
    """Telemetry data for a single analysis step."""

    step: int
    path: str
    depth: int
    prompt_chars: int
    response_chars: int
    duration_ms: int
    json_valid: bool
    nav_requested: list[str] = []
    nav_kept: list[str] = []
    nav_rejected: list[str] = []
    fallback_used: bool = False
    sanitizer_trimmed: bool = False
    sanitizer_notes: str = ""


# ---------- YAML Helpers ----------
def load_yaml(path: Path, model: type[BaseModel]) -> BaseModel:
    """Load and validate YAML data into a Pydantic model."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return model.model_validate(data)


def save_yaml(path: Path, obj: BaseModel) -> None:
    """Save a Pydantic model to YAML with atomic write."""
    # Create temporary file in same directory
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        # Write to temporary file
        with open(temp_path, "w", encoding="utf-8") as f:
            yaml.dump(obj.model_dump(), f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Atomic rename
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def save_yaml_data(path: Path, data) -> None:
    """Save plain data (dict, list, etc.) to YAML with atomic write."""
    # Create temporary file in same directory
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        # Write to temporary file
        with open(temp_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Atomic rename
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


# ---------- JSON Helpers (for backward compatibility) ----------
def load_json(path: Path, model: type[BaseModel]) -> BaseModel:
    """Load and validate JSON data into a Pydantic model."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return model.model_validate(data)


def save_json(path: Path, obj: BaseModel) -> None:
    """Save a Pydantic model to JSON with atomic write."""
    # Create temporary file in same directory
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        # Write to temporary file
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(obj.model_dump(), f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def save_json_data(path: Path, data) -> None:
    """Save plain data (dict, list, etc.) to JSON with atomic write."""
    # Create temporary file in same directory
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        # Write to temporary file
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


# ---------- SpadeState Schemas ----------
class SpadeStateEntryFile(BaseModel):
    """File entry in SpadeState database."""

    path: str
    parent: str | None = None
    visited: bool = False
    visited_at: str | None = None
    depth: int = Field(ge=0)
    confidence: int = Field(default=0, ge=0, le=100)

    # File-specific fields
    extension: str | None = None
    file_size: int = Field(ge=0)
    last_modified: str  # ISO8601 timestamp

    # Analysis fields (for future LLM integration)
    analysis: dict | None = None
    summary: str | None = None
    tags: list[str] | None = None


class SpadeStateEntryDir(BaseModel):
    """Directory entry in SpadeState database."""

    path: str
    parent: str | None = None
    children: list[str] = Field(default_factory=list)
    visited: bool = False
    visited_at: str | None = None
    depth: int = Field(ge=0)
    confidence: int = Field(default=0, ge=0, le=100)

    # Directory-specific fields
    counts: DirCounts
    ext_histogram: dict[str, int] | None = None
    siblings: list[str] | None = None
    excluded_children: list[str] | None = None
    is_symlink: bool = False
    ignored_reason: str | None = None
    markers: list[str] | None = None
    samples: DirSamples | None = None
    staleness_fingerprint: StalenessFingerprint | None = None

    # Analysis fields (for future LLM integration)
    analysis: dict | None = None
    summary: str | None = None
    tags: list[str] | None = None
    deterministic_scoring: dict[str, ChildScore] | None = None


class SpadeStateMetadata(BaseModel):
    """Metadata for SpadeState database."""

    repo_root: str
    created_at: str  # ISO8601 timestamp
    last_updated: str  # ISO8601 timestamp
    version: str = "1.0"
