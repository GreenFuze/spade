import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sanitize import sanitize_llm_output
from models import LLMResponse, LLMInferred, NodeUpdate, Evidence, Nav, DirMeta, RunConfig
from conftest import write_dirmeta


def test_sanitizer_trims_and_normalization(repo_tmp):
    """Test sanitizer trims and normalization."""
    # Arrange
    # Create current dirmeta with Python dominant
    current_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 10, "dirs": 0},
        "siblings": ["api", "web"],
        "excluded_children": [],
        "ext_histogram": {"py": 10, "ts": 1},  # Python dominant
        "markers": ["pyproject.toml"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 11,
            "name_hash": "src123"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Create LLM response with issues
    long_summary = "This is sentence one. " * 10  # 10 sentences
    long_summary += "This is a very long sentence that exceeds the character limit. " * 20  # 1200+ chars
    
    resp = LLMResponse(
        inferred=LLMInferred(
            high_level_components=[],
            nodes={
                "src": NodeUpdate(
                    summary=long_summary,
                    languages=["js", "Python", "C Plus Plus", "js"],  # Non-canonical, duplicates
                    tags=["backend", "api", "backend", "server", "api"],  # Duplicates
                    evidence=[
                        Evidence(type="marker", value="pyproject.toml"),
                        Evidence(type="lang_ext", value="py"),
                        Evidence(type="marker", value="pyproject.toml"),  # Duplicate
                        Evidence(type="name", value="src"),
                        Evidence(type="name", value="src")  # Duplicate
                    ],
                    confidence=0.9
                )
            }
        ),
        nav=Nav(
            descend_into=["api", "web"],
            descend_one_level_only=False,  # Should be forced to True
            reasons=["contains code"]
        ),
        open_questions_ranked=[]
    )
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    # Convert dict to DirMeta object
    from models import DirMeta
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    sanitized, was_trimmed, trim_notes = sanitize_llm_output(repo_tmp, cfg, current_dirmeta_obj, resp)
    
    # Assert
    # Check nav flag was forced to True
    assert sanitized.nav.descend_one_level_only == True
    
    # Check summary was trimmed
    node = sanitized.inferred.nodes["src"]
    assert len(node.summary) <= cfg.policies.max_summary_chars
    assert node.summary.count('.') <= cfg.policies.max_summary_sentences
    
    # Check languages were normalized, deduped, and reranked
    # Python should come first due to local evidence
    assert node.languages[0] == "python"
    assert "javascript" in node.languages
    assert "c++" in node.languages
    assert len(node.languages) <= cfg.policies.max_languages_per_node
    
    # Check tags were deduped and capped
    assert len(node.tags) <= cfg.policies.max_tags_per_node
    assert len(set(node.tags)) == len(node.tags)  # No duplicates
    
    # Check evidence was deduped and capped
    assert len(node.evidence) <= cfg.policies.max_evidence_per_node
    evidence_keys = [(e.type, e.value) for e in node.evidence]
    assert len(evidence_keys) == len(set(evidence_keys))  # No duplicates
    
    # Check policy evidence was added
    policy_evidence = [e for e in node.evidence if e.type == "policy"]
    assert len(policy_evidence) > 0
    
    # Check confidence was clamped
    assert node.confidence <= 0.7
    
    # Check trim tracking
    assert was_trimmed == True
    assert "summary" in trim_notes or "langs" in trim_notes or "tags" in trim_notes or "evidence" in trim_notes


def test_sanitizer_no_trimming_needed(repo_tmp):
    """Test sanitizer when no trimming is needed."""
    # Arrange
    current_dirmeta = {
        "path": "src",
        "depth": 1,
        "counts": {"files": 5, "dirs": 0},
        "siblings": ["api"],
        "excluded_children": [],
        "ext_histogram": {"py": 5},
        "markers": ["pyproject.toml"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 6,
            "name_hash": "src456"
        }
    }
    write_dirmeta(repo_tmp, "src", current_dirmeta)
    
    # Create LLM response within limits
    resp = LLMResponse(
        inferred=LLMInferred(
            high_level_components=[],
            nodes={
                "src": NodeUpdate(
                    summary="This is a short summary.",
                    languages=["python"],
                    tags=["backend"],
                    evidence=[Evidence(type="marker", value="pyproject.toml")],
                    confidence=0.8
                )
            }
        ),
        nav=Nav(
            descend_into=["api"],
            descend_one_level_only=True,
            reasons=["contains code"]
        ),
        open_questions_ranked=[]
    )
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    # Convert dict to DirMeta object
    from models import DirMeta
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    sanitized, was_trimmed, trim_notes = sanitize_llm_output(repo_tmp, cfg, current_dirmeta_obj, resp)
    
    # Assert
    # No trimming should be needed
    assert was_trimmed == False
    assert trim_notes == ""
    
    # Original confidence should be preserved
    node = sanitized.inferred.nodes["src"]
    assert node.confidence == 0.8
    
    # No policy evidence should be added
    policy_evidence = [e for e in node.evidence if e.type == "policy"]
    assert len(policy_evidence) == 0


def test_sanitizer_component_evidence(repo_tmp):
    """Test sanitizer with high-level components."""
    # Arrange
    current_dirmeta = {
        "path": ".",
        "depth": 0,
        "counts": {"files": 1, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["README.md"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "root123"
        }
    }
    write_dirmeta(repo_tmp, ".", current_dirmeta)
    
    # Create LLM response with component evidence issues
    resp = LLMResponse(
        inferred=LLMInferred(
            high_level_components=[
                {
                    "name": "API Server",
                    "role": "Backend API",
                    "dirs": ["src/api"],
                    "evidence": [
                        Evidence(type="marker", value="pyproject.toml"),
                        Evidence(type="marker", value="pyproject.toml"),  # Duplicate
                        Evidence(type="name", value="api"),
                        Evidence(type="name", value="api")  # Duplicate
                    ],
                    "confidence": 0.9
                }
            ],
            nodes={}
        ),
        nav=Nav(
            descend_into=[],
            descend_one_level_only=True,
            reasons=[]
        ),
        open_questions_ranked=[]
    )
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    # Convert dict to DirMeta object
    from models import DirMeta
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    sanitized, was_trimmed, trim_notes = sanitize_llm_output(repo_tmp, cfg, current_dirmeta_obj, resp)
    
    # Assert
    component = sanitized.inferred.high_level_components[0]
    
    # Evidence should be deduped and capped
    assert len(component.evidence) <= cfg.policies.max_evidence_per_node
    evidence_keys = [(e.type, e.value) for e in component.evidence]
    assert len(evidence_keys) == len(set(evidence_keys))  # No duplicates
    
    # Policy evidence should be added if trimming occurred
    policy_evidence = [e for e in component.evidence if e.type == "policy"]
    if was_trimmed:
        assert len(policy_evidence) > 0
        assert component.confidence <= 0.7


def test_sanitizer_path_filtering(repo_tmp):
    """Test sanitizer path filtering."""
    # Arrange
    current_dirmeta = {
        "path": "src/api",
        "depth": 2,
        "counts": {"files": 1, "dirs": 0},
        "siblings": [],
        "excluded_children": [],
        "ext_histogram": {"py": 1},
        "markers": ["__init__.py"],
        "staleness_fingerprint": {
            "latest_modified_time": "2025-01-01T00:00:00Z",
            "total_entries": 1,
            "name_hash": "api123"
        }
    }
    write_dirmeta(repo_tmp, "src/api", current_dirmeta)
    
    # Create LLM response with disallowed paths
    resp = LLMResponse(
        inferred=LLMInferred(
            high_level_components=[],
            nodes={
                ".": NodeUpdate(  # Allowed - root
                    summary="Root directory",
                    languages=["python"],
                    tags=["root"],
                    evidence=[Evidence(type="name", value="root")],
                    confidence=0.8
                ),
                "src": NodeUpdate(  # Allowed - parent
                    summary="Source directory",
                    languages=["python"],
                    tags=["src"],
                    evidence=[Evidence(type="name", value="src")],
                    confidence=0.8
                ),
                "src/api": NodeUpdate(  # Allowed - current
                    summary="API directory",
                    languages=["python"],
                    tags=["api"],
                    evidence=[Evidence(type="name", value="api")],
                    confidence=0.8
                ),
                "src/api/sub": NodeUpdate(  # Disallowed - child
                    summary="Sub directory",
                    languages=["python"],
                    tags=["sub"],
                    evidence=[Evidence(type="name", value="sub")],
                    confidence=0.8
                ),
                "other": NodeUpdate(  # Disallowed - unrelated
                    summary="Other directory",
                    languages=["python"],
                    tags=["other"],
                    evidence=[Evidence(type="name", value="other")],
                    confidence=0.8
                )
            }
        ),
        nav=Nav(
            descend_into=[],
            descend_one_level_only=True,
            reasons=[]
        ),
        open_questions_ranked=[]
    )
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    # Convert dict to DirMeta object
    from models import DirMeta
    current_dirmeta_obj = DirMeta(**current_dirmeta)
    sanitized, was_trimmed, trim_notes = sanitize_llm_output(repo_tmp, cfg, current_dirmeta_obj, resp)
    
    # Assert
    # Only allowed paths should remain
    allowed_paths = {".", "src", "src/api"}
    actual_paths = set(sanitized.inferred.nodes.keys())
    assert actual_paths == allowed_paths
    
    # Disallowed paths should be filtered out
    assert "src/api/sub" not in sanitized.inferred.nodes
    assert "other" not in sanitized.inferred.nodes
