import json
import os
import shutil
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import RunConfig


@pytest.fixture
def repo_tmp(tmp_path):
    """Create a temporary repository with .spade/ directory and minimal run.json."""
    repo = tmp_path / "repo"
    repo.mkdir()
    spade = repo / ".spade"
    spade.mkdir()
    
    # minimal run.json with sane caps/policies
    run = {
        "limits": {"max_depth": 6, "max_nodes": 0, "max_llm_calls": 0},
        "caps": {
            "samples": {"max_dirs": 10, "max_files": 10},
            "nav": {"max_children_per_step": 4},
            "context": {
                "max_siblings_in_prompt": 200,
                "max_children_scores_in_prompt": 200,
                "max_reasons_per_child": 3,
                "max_ancestor_summaries": 10
            }
        },
        "policies": {
            "skip_symlinks": True,
            "descend_one_level_only": True,
            "max_summary_sentences": 3,
            "max_summary_chars": 400,
            "max_languages_per_node": 6,
            "max_tags_per_node": 12,
            "max_evidence_per_node": 12
        },
        "scoring": {
            "weights": {
                "marker": 0.55,
                "lang": 0.25,
                "name": 0.15,
                "size": 0.05
            },
            "name_signals": ["api", "cli", "server", "service", "pkg", "src", "web", "ui", "infra", "tests", "docs"],
            "size_log_k": 200
        },
        "use_learned_markers": False,
        "use_learned_languages": False,
        "learn_markers": False,
        "learn_languages": False,
        "marker_learning": {"top_k_candidates": 50, "min_confidence": 0.6},
        "timestamps_utc": True
    }
    
    (spade / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    return repo


def write_ignore(repo, ignore_lines=None, allow_lines=None):
    """Write .spadeignore and/or .spadeallow files."""
    spade = repo / ".spade"
    if ignore_lines is not None:
        (spade / ".spadeignore").write_text(
            "\n".join(ignore_lines) + "\n", 
            encoding="utf-8"
        )
    if allow_lines is not None:
        (spade / ".spadeallow").write_text(
            "\n".join(allow_lines) + "\n", 
            encoding="utf-8"
        )


def write_dirmeta(repo, rel, obj):
    """Write a dirmeta.json file under .spade/snapshot/<rel>/dirmeta.json."""
    target = repo / ".spade" / "snapshot" / (rel if rel != "." else ".")
    target.mkdir(parents=True, exist_ok=True)
    (target / "dirmeta.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )


def create_test_files(repo, files_and_dirs):
    """Create test files and directories in the repository."""
    for item in files_and_dirs:
        path = repo / item
        if item.endswith('/'):
            # Directory
            path.mkdir(parents=True, exist_ok=True)
        else:
            # File
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"test content for {item}", encoding="utf-8")


def create_symlink_if_supported(repo, target_path, link_path):
    """Create a symlink if the platform supports it."""
    try:
        target = repo / target_path
        link = repo / link_path
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        return True
    except (OSError, NotImplementedError):
        # Symlinks not supported on this platform
        return False
