import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from snapshot import compute_deterministic_scoring
from models import RunConfig, load_json
from conftest import write_dirmeta


def test_scoring_reasons_and_ordering(repo_tmp):
    """Test deterministic scoring reasons and ordering."""
    # Arrange
    # Create parent dirmeta
    parent_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 2, "dirs": 2},
        "siblings": ["api", "web"],
        "excluded_children": [],
        "ext_histogram": {"py": 1, "md": 1},
        "markers": ["README.md"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 4,
            "name_hash": "parent123"
        }
    }
    write_dirmeta(repo_tmp, "src", parent_dirmeta)
    
    # Create child dirmeta for "api" with strong signals
    api_dirmeta = {
        "path": "src/api",
        "depth": 2,
        "counts": {"files": 7, "dirs": 2},
        "siblings": ["v1", "v2"],
        "excluded_children": [],
        "ext_histogram": {"py": 7},  # Strong Python signal
        "markers": ["pyproject.toml", "requirements.txt"],  # Strong markers
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 9,
            "name_hash": "api456"
        }
    }
    write_dirmeta(repo_tmp, "src/api", api_dirmeta)
    
    # Create child dirmeta for "web" with weaker signals
    web_dirmeta = {
        "path": "src/web",
        "depth": 2,
        "counts": {"files": 2, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"ts": 2},  # Weaker TypeScript signal
        "markers": ["package.json"],  # Single marker
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 2,
            "name_hash": "web789"
        }
    }
    write_dirmeta(repo_tmp, "src/web", web_dirmeta)
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    compute_deterministic_scoring(repo_tmp, cfg)
    
    # Reload parent dirmeta
    parent_dirmeta_path = repo_tmp / ".spade" / "snapshot" / "src" / "dirmeta.json"
    from models import DirMeta
    parent_dirmeta = load_json(parent_dirmeta_path, DirMeta)
    
    # Assert
    deterministic_scoring = parent_dirmeta.deterministic_scoring or {}
    
    # Check that both children have scores
    assert "api" in deterministic_scoring
    assert "web" in deterministic_scoring
    
    # Check that "api" has higher score than "web" (given weights)
    api_score = deterministic_scoring["api"].score
    web_score = deterministic_scoring["web"].score
    assert api_score > web_score
    
    # Check reasons for "api"
    api_reasons = deterministic_scoring["api"].reasons
    assert len(api_reasons) > 0
    
    # Check for expected reason prefixes
    marker_reasons = [r for r in api_reasons if r.startswith("marker:")]
    lang_reasons = [r for r in api_reasons if r.startswith("lang:python(")]
    size_reasons = [r for r in api_reasons if r.startswith("size:")]
    
    assert len(marker_reasons) > 0  # Should have marker reasons
    assert len(lang_reasons) > 0    # Should have language reasons
    assert len(size_reasons) > 0    # Should have size reasons
    
    # Check reasons for "web"
    web_reasons = deterministic_scoring["web"].reasons
    assert len(web_reasons) > 0
    
    # Web should have fewer reasons due to weaker signals
    assert len(web_reasons) <= len(api_reasons)


def test_name_signals_scoring(repo_tmp):
    """Test scoring based on name signals."""
    # Arrange
    # Create parent dirmeta with name-signal children
    parent_dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 3},
        "siblings": ["api", "tests", "docs"],
        "excluded_children": [],
        "ext_histogram": {"md": 1},
        "markers": ["README.md"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 4,
            "name_hash": "root123"
        }
    }
    write_dirmeta(repo_tmp, ".", parent_dirmeta)
    
    # Create children with name signals
    api_dirmeta = {
        "path": "api",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "api456"
        }
    }
    write_dirmeta(repo_tmp, "api", api_dirmeta)
    
    tests_dirmeta = {
        "path": "tests",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "tests789"
        }
    }
    write_dirmeta(repo_tmp, "tests", tests_dirmeta)
    
    docs_dirmeta = {
        "path": "docs",
        "depth": 1,
        "counts": {"files": 1, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"md": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "docs012"
        }
    }
    write_dirmeta(repo_tmp, "docs", docs_dirmeta)
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    compute_deterministic_scoring(repo_tmp, cfg)
    
    # Reload parent dirmeta
    parent_dirmeta_path = repo_tmp / ".spade" / "snapshot" / "." / "dirmeta.json"
    from models import DirMeta
    parent_dirmeta = load_json(parent_dirmeta_path, DirMeta)
    
    # Assert
    deterministic_scoring = parent_dirmeta.deterministic_scoring or {}
    
    # Check that all children have scores
    assert "api" in deterministic_scoring
    assert "tests" in deterministic_scoring
    assert "docs" in deterministic_scoring
    
    # Check for name signal reasons
    api_reasons = deterministic_scoring["api"].reasons
    tests_reasons = deterministic_scoring["tests"].reasons
    docs_reasons = deterministic_scoring["docs"].reasons
    
    # Should have name signal reasons
    api_name_reasons = [r for r in api_reasons if r.startswith("name:")]
    tests_name_reasons = [r for r in tests_reasons if r.startswith("name:")]
    docs_name_reasons = [r for r in docs_reasons if r.startswith("name:")]
    
    assert len(api_name_reasons) > 0
    assert len(tests_name_reasons) > 0
    assert len(docs_name_reasons) > 0


def test_size_scoring(repo_tmp):
    """Test scoring based on file/directory size."""
    # Arrange
    # Create parent dirmeta
    parent_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 1, "dirs": 2},
        "siblings": ["large", "small"],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 3,
            "name_hash": "parent123"
        }
    }
    write_dirmeta(repo_tmp, "src", parent_dirmeta)
    
    # Create large child
    large_dirmeta = {
        "path": "src/large",
        "depth": 2,
        "counts": {"files": 50, "dirs": 10},  # Large directory
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 50},
        "markers": ["pyproject.toml"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 60,
            "name_hash": "large456"
        }
    }
    write_dirmeta(repo_tmp, "src/large", large_dirmeta)
    
    # Create small child
    small_dirmeta = {
        "path": "src/small",
        "depth": 2,
        "counts": {"files": 2, "dirs": 0},  # Small directory
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 2},
        "markers": [],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 2,
            "name_hash": "small789"
        }
    }
    write_dirmeta(repo_tmp, "src/small", small_dirmeta)
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    compute_deterministic_scoring(repo_tmp, cfg)
    
    # Reload parent dirmeta
    parent_dirmeta_path = repo_tmp / ".spade" / "snapshot" / "src" / "dirmeta.json"
    from models import DirMeta
    parent_dirmeta = load_json(parent_dirmeta_path, DirMeta)
    
    # Assert
    deterministic_scoring = parent_dirmeta.deterministic_scoring or {}
    
    # Check that both children have scores
    assert "large" in deterministic_scoring
    assert "small" in deterministic_scoring
    
    # Large should have higher score due to size
    large_score = deterministic_scoring["large"].score
    small_score = deterministic_scoring["small"].score
    assert large_score > small_score
    
    # Check size reasons
    large_reasons = deterministic_scoring["large"].reasons
    small_reasons = deterministic_scoring["small"].reasons
    
    large_size_reasons = [r for r in large_reasons if r.startswith("size:")]
    small_size_reasons = [r for r in small_reasons if r.startswith("size:")]
    
    assert len(large_size_reasons) > 0
    assert len(small_size_reasons) > 0
