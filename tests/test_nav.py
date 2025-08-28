import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nav import filter_nav
from schemas import Nav, DirMeta
from conftest import write_dirmeta, write_ignore


def test_nav_guardrails(repo_tmp):
    """Test navigation guardrails and filtering."""
    # Arrange
    # Create current dirmeta with siblings and excluded children
    current_dirmeta = {
        "path": "src",
        "depth": 2,
        "counts": {"files": 5, "dirs": 3},
        "siblings": ["api", "web", ".github"],
        "excluded_children": [".github"],
        "ext_histogram": {"py": 3, "js": 2},
        "markers": ["pyproject.toml"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 8,
            "name_hash": "abc123"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    from schemas import RunConfig
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    cfg.limits.max_depth = 3  # Set max_depth to 3
    
    # Create ignore specs
    write_ignore(repo_tmp, ignore_lines=["*.tmp", "temp/"])
    
    # Create nav request with various issues
    nav = Nav(
        descend_into=["api", ".github", "../bad", "sub/dir", "nonexistent"],
        descend_one_level_only=True,
        reasons=["contains code"]
    )
    
    # Act
    # Convert dict to DirMeta object
    from schemas import DirMeta
    import pathspec
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    # Create empty PathSpec objects for testing
    empty_spec = pathspec.PathSpec.from_lines("gitwildmatch", [])
    kept, rejected_pairs = filter_nav(repo_tmp, current_dirmeta_obj, cfg, nav, (empty_spec, empty_spec))
    
    # Assert
    # Only "api" should be kept (it's in siblings and not excluded)
    assert kept == ["api"]
    
    # Check rejected reasons
    rejected_dict = dict(rejected_pairs)
    assert ".github" in rejected_dict
    assert "excluded by scanner" in rejected_dict[".github"]
    
    assert "../bad" in rejected_dict
    assert "invalid name" in rejected_dict["../bad"]
    
    assert "sub/dir" in rejected_dict
    assert "invalid name" in rejected_dict["sub/dir"]
    
    assert "nonexistent" in rejected_dict
    assert "not in siblings" in rejected_dict["nonexistent"]


def test_depth_limits(repo_tmp):
    """Test depth limit enforcement."""
    # Arrange
    # Create dirmeta at max_depth
    current_dirmeta = {
        "path": "src/api/v1",
        "depth": 3,  # At max_depth
        "counts": {"files": 2, "dirs": 0},
        "siblings": ["users", "products"],
        "excluded_children": [],
        "ext_histogram": {"py": 2},
        "markers": ["__init__.py"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 2,
            "name_hash": "def456"
        }
    }
    write_dirmeta(repo_tmp, "src/api/v1", current_dirmeta)
    
    # Load config with max_depth=3
    cfg_path = repo_tmp / ".spade" / "run.json"
    from schemas import RunConfig
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    cfg.limits.max_depth = 3
    
    # Create nav request
    nav = Nav(
        descend_into=["users", "products"],
        descend_one_level_only=True,
        reasons=["API endpoints"]
    )
    
    # Act
    # Convert dict to DirMeta object
    from schemas import DirMeta
    import pathspec
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    # Create empty PathSpec objects for testing
    empty_spec = pathspec.PathSpec.from_lines("gitwildmatch", [])
    kept, rejected_pairs = filter_nav(repo_tmp, current_dirmeta_obj, cfg, nav, (empty_spec, empty_spec))
    
    # Assert
    # Should reject all due to depth limit
    assert kept == []
    
    # Check rejected reasons
    rejected_dict = dict(rejected_pairs)
    assert "users" in rejected_dict
    assert "over max_depth" in rejected_dict["users"]
    
    assert "products" in rejected_dict
    assert "over max_depth" in rejected_dict["products"]


def test_safe_names(repo_tmp):
    """Test safe name validation."""
    # Arrange
    current_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": ["normal_dir"],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "ghi789"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    from schemas import RunConfig
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Create nav request with unsafe names
    nav = Nav(
        descend_into=["normal_dir", "dir with spaces", "dir/with/slashes", "..", ".", ""],
        descend_one_level_only=True,
        reasons=["testing"]
    )
    
    # Act
    # Convert dict to DirMeta object
    from schemas import DirMeta
    import pathspec
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    # Create empty PathSpec objects for testing
    empty_spec = pathspec.PathSpec.from_lines("gitwildmatch", [])
    kept, rejected_pairs = filter_nav(repo_tmp, current_dirmeta_obj, cfg, nav, (empty_spec, empty_spec))
    
    # Assert
    # Only "normal_dir" should be kept
    assert kept == ["normal_dir"]
    
    # Check rejected reasons
    rejected_dict = dict(rejected_pairs)
    # Invalid names should be rejected by name check first
    assert "dir with spaces" in rejected_dict
    assert "invalid name" in rejected_dict["dir with spaces"]
    
    assert "dir/with/slashes" in rejected_dict
    assert "invalid name" in rejected_dict["dir/with/slashes"]
    
    assert ".." in rejected_dict
    assert "invalid name" in rejected_dict[".."]
    
    assert "." in rejected_dict
    assert "invalid name" in rejected_dict["."]
    
    assert "" in rejected_dict
    assert "invalid name" in rejected_dict[""]


def test_ignore_patterns_in_nav(repo_tmp):
    """Test that ignore patterns are respected in navigation."""
    # Arrange
    current_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": ["api", "temp", "build"],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "jkl012"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Create ignore specs
    write_ignore(repo_tmp, ignore_lines=["temp", "build", "*.tmp"])
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    from schemas import RunConfig
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Create nav request
    nav = Nav(
        descend_into=["api", "temp", "build"],
        descend_one_level_only=True,
        reasons=["source code"]
    )
    
    # Act
    # Convert dict to DirMeta object
    from schemas import DirMeta
    import pathspec
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    # Load actual ignore specs for testing
    from ignore import load_specs
    ignore_spec, allow_spec, _, _ = load_specs(repo_tmp)
    kept, rejected_pairs = filter_nav(repo_tmp, current_dirmeta_obj, cfg, nav, (ignore_spec, allow_spec))
    
    # Assert
    # Only "api" should be kept (temp and build are ignored)
    assert kept == ["api"]
    
    # Check rejected reasons
    rejected_dict = dict(rejected_pairs)
    assert "temp" in rejected_dict
    assert "skipped by ignore rules" in rejected_dict["temp"]
    
    assert "build" in rejected_dict
    assert "skipped by ignore rules" in rejected_dict["build"]


def test_max_children_per_step(repo_tmp):
    """Test max_children_per_step limit."""
    # Arrange
    current_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": ["api", "web", "tests", "docs", "utils", "config"],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "mno345"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Load config with max_children_per_step=2
    cfg_path = repo_tmp / ".spade" / "run.json"
    from schemas import RunConfig
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    cfg.caps.nav.max_children_per_step = 2
    
    # Create nav request
    nav = Nav(
        descend_into=["api", "web", "tests", "docs", "utils", "config"],
        descend_one_level_only=True,
        reasons=["all directories"]
    )
    
    # Act
    # Convert dict to DirMeta object
    from schemas import DirMeta
    import pathspec
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    # Create empty PathSpec objects for testing
    empty_spec = pathspec.PathSpec.from_lines("gitwildmatch", [])
    kept, rejected_pairs = filter_nav(repo_tmp, current_dirmeta_obj, cfg, nav, (empty_spec, empty_spec))
    
    # Assert
    # Should only keep first 2 children due to limit
    assert len(kept) == 2
    assert kept == ["api", "web"]
    
    # Check that remaining are rejected due to limit
    rejected_dict = dict(rejected_pairs)
    assert "tests" in rejected_dict
    assert "exceeded max_children_per_step" in rejected_dict["tests"]
    
    assert "docs" in rejected_dict
    assert "exceeded max_children_per_step" in rejected_dict["docs"]
    
    assert "utils" in rejected_dict
    assert "exceeded max_children_per_step" in rejected_dict["utils"]
    
    assert "config" in rejected_dict
    assert "exceeded max_children_per_step" in rejected_dict["config"]
