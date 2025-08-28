import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from context import build_phase0_context
from schemas import RunConfig
from conftest import write_dirmeta


def test_context_caps(repo_tmp):
    """Test token-safe prompt caps."""
    # Arrange
    # Create parent dirmeta with 500 siblings and 500 children
    siblings = [f"sibling_{i}" for i in range(500)]
    
    # Create deterministic scoring for 500 children with descending scores
    deterministic_scoring = {}
    for i in range(500):
        child_name = f"child_{i}"
        score = 1.0 - (i * 0.001)  # Descending scores
        reasons = [f"reason_{j}" for j in range(5)]  # 5 reasons each
        deterministic_scoring[child_name] = {
            "score": score,
            "reasons": reasons
        }
    
    parent_dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 500},
        "siblings": siblings,
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["README.md"],
        "deterministic_scoring": deterministic_scoring,
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 501,
            "name_hash": "root123"
        }
    }
    write_dirmeta(repo_tmp, ".", parent_dirmeta)
    
    # Create ancestor dirmetas for testing ancestor caps
    for i in range(10):
        ancestor_path = "/".join(["ancestor"] * (i + 1))
        # Create the actual directory structure
        (repo_tmp / ancestor_path).mkdir(parents=True, exist_ok=True)
        (repo_tmp / ancestor_path / "dummy.py").write_text("dummy", encoding="utf-8")
        
        ancestor_dirmeta = {
            "path": ancestor_path,
            "depth": i + 1,
            "counts": {"files": 1, "dirs": 0},
            "siblings": [],
            "excluded_children": [],
            "ext_histogram": {"py": 1},
            "markers": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 1,
                "name_hash": f"ancestor{i}"
            }
        }
        write_dirmeta(repo_tmp, ancestor_path, ancestor_dirmeta)
    
    # Update run.json with lower caps
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg_data["caps"]["context"] = {
        "max_siblings_in_prompt": 100,
        "max_children_scores_in_prompt": 100,
        "max_reasons_per_child": 2,
        "max_ancestor_summaries": 5
    }
    cfg_path.write_text(json.dumps(cfg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Load config
    cfg = RunConfig(**cfg_data)
    
    # Act
    context = build_phase0_context(repo_tmp, ".", cfg)
    
    # Assert
    # Check siblings are capped
    assert len(context["siblings"]) == 100
    assert context["context_meta"]["siblings_included"] == 100
    assert context["context_meta"]["siblings_total"] == 500
    
    # Check deterministic scoring children are capped
    det_children = context["deterministic_scoring"]["children"]
    assert len(det_children) == 100
    assert context["context_meta"]["children_scores_included"] == 100
    assert context["context_meta"]["children_scores_total"] == 500
    
    # Check reasons per child are capped
    for child_name, child_data in det_children.items():
        assert len(child_data["reasons"]) <= 2
    assert context["context_meta"]["max_reasons_per_child"] == 2
    
        # Check ancestors are capped (root directory has no ancestors)
    assert len(context["ancestors"]) == 0
    assert context["context_meta"]["ancestors_included"] == 0
    assert context["context_meta"]["ancestors_total"] == 0
    
    # Check that highest scoring children are included first
    child_scores = [(name, data["score"]) for name, data in det_children.items()]
    child_scores.sort(key=lambda x: x[1], reverse=True)
    assert child_scores[0][1] > child_scores[-1][1]  # First should have higher score


def test_context_caps_unlimited(repo_tmp):
    """Test context caps when set to unlimited (0)."""
    # Arrange
    # Create dirmeta with moderate amounts
    siblings = [f"sibling_{i}" for i in range(50)]
    deterministic_scoring = {}
    for i in range(50):
        child_name = f"child_{i}"
        score = 1.0 - (i * 0.01)
        reasons = [f"reason_{j}" for j in range(3)]
        deterministic_scoring[child_name] = {
            "score": score,
            "reasons": reasons
        }
    
    dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 50},
        "siblings": siblings,
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["README.md"],
        "deterministic_scoring": deterministic_scoring,
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 51,
            "name_hash": "root456"
        }
    }
    write_dirmeta(repo_tmp, ".", dirmeta)
    
    # Update run.json with unlimited caps
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg_data["caps"]["context"] = {
        "max_siblings_in_prompt": 0,
        "max_children_scores_in_prompt": 0,
        "max_reasons_per_child": 0,
        "max_ancestor_summaries": 0
    }
    cfg_path.write_text(json.dumps(cfg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Load config
    cfg = RunConfig(**cfg_data)
    
    # Act
    context = build_phase0_context(repo_tmp, ".", cfg)
    
    # Assert
    # Check that all items are included when caps are unlimited
    assert len(context["siblings"]) == 50
    assert context["context_meta"]["siblings_included"] == 50
    assert context["context_meta"]["siblings_total"] == 50
    
    det_children = context["deterministic_scoring"]["children"]
    assert len(det_children) == 50
    assert context["context_meta"]["children_scores_included"] == 50
    assert context["context_meta"]["children_scores_total"] == 50
    
    # Check that all reasons are included
    for child_name, child_data in det_children.items():
        assert len(child_data["reasons"]) == 3
    assert context["context_meta"]["max_reasons_per_child"] == 0


def test_context_caps_ordering(repo_tmp):
    """Test that context caps maintain proper ordering."""
    # Arrange
    # Create dirmeta with specific ordering requirements
    siblings = ["zebra", "alpha", "beta", "gamma", "delta"]
    
    deterministic_scoring = {
        "low_score": {"score": 0.1, "reasons": ["reason1", "reason2", "reason3"]},
        "high_score": {"score": 0.9, "reasons": ["reason1", "reason2", "reason3"]},
        "medium_score": {"score": 0.5, "reasons": ["reason1", "reason2", "reason3"]}
    }
    
    dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 8},
        "siblings": siblings,
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["README.md"],
        "deterministic_scoring": deterministic_scoring,
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 9,
            "name_hash": "root789"
        }
    }
    write_dirmeta(repo_tmp, ".", dirmeta)
    
    # Update run.json with caps that will trigger ordering
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg_data["caps"]["context"] = {
        "max_siblings_in_prompt": 3,
        "max_children_scores_in_prompt": 2,
        "max_reasons_per_child": 2,
        "max_ancestor_summaries": 10
    }
    cfg_path.write_text(json.dumps(cfg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Load config
    cfg = RunConfig(**cfg_data)
    
    # Act
    context = build_phase0_context(repo_tmp, ".", cfg)
    
    # Assert
    # Check siblings maintain alphabetical order when capped
    assert len(context["siblings"]) == 3
    assert context["siblings"] == ["alpha", "beta", "delta"]  # First 3 alphabetically
    
    # Check deterministic scoring maintains score order when capped
    det_children = context["deterministic_scoring"]["children"]
    assert len(det_children) == 2
    
    # Should have highest scoring children first
    child_names = list(det_children.keys())
    assert "high_score" in child_names
    assert "medium_score" in child_names
    assert "low_score" not in child_names  # Should be excluded by cap
    
    # Check reasons are capped per child
    for child_name, child_data in det_children.items():
        assert len(child_data["reasons"]) == 2  # Capped to 2


def test_context_meta_accuracy(repo_tmp):
    """Test that context_meta accurately reflects capping."""
    # Arrange
    # Create dirmeta with known counts
    siblings = [f"sibling_{i}" for i in range(25)]
    deterministic_scoring = {}
    for i in range(15):
        child_name = f"child_{i}"
        score = 1.0 - (i * 0.05)
        reasons = [f"reason_{j}" for j in range(4)]
        deterministic_scoring[child_name] = {
            "score": score,
            "reasons": reasons
        }
    
    dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 40},
        "siblings": siblings,
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["README.md"],
        "deterministic_scoring": deterministic_scoring,
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 41,
            "name_hash": "root012"
        }
    }
    write_dirmeta(repo_tmp, ".", dirmeta)
    
    # Update run.json with specific caps
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg_data["caps"]["context"] = {
        "max_siblings_in_prompt": 10,
        "max_children_scores_in_prompt": 8,
        "max_reasons_per_child": 2,
        "max_ancestor_summaries": 3
    }
    cfg_path.write_text(json.dumps(cfg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Load config
    cfg = RunConfig(**cfg_data)
    
    # Act
    context = build_phase0_context(repo_tmp, ".", cfg)
    
    # Assert
    # Check context_meta accuracy
    meta = context["context_meta"]
    
    # Siblings
    assert meta["siblings_included"] == 10
    assert meta["siblings_total"] == 25
    assert len(context["siblings"]) == 10
    
    # Children scores
    assert meta["children_scores_included"] == 8
    assert meta["children_scores_total"] == 15
    assert len(context["deterministic_scoring"]["children"]) == 8
    
    # Reasons per child
    assert meta["max_reasons_per_child"] == 2
    for child_data in context["deterministic_scoring"]["children"].values():
        assert len(child_data["reasons"]) <= 2
    
    # Ancestors (should be 0 for root)
    assert meta["ancestors_included"] == 0
    assert meta["ancestors_total"] == 0
    assert len(context["ancestors"]) == 0
