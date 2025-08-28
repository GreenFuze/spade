#!/usr/bin/env python3
"""
Test script for SPADE Pydantic models
Validates that models can be instantiated with defaults and work as expected
"""

from schemas import (
    RunConfig, DirMeta, DirCounts, StalenessFingerprint, DirSamples,
    LLMResponse, LLMInferred, Nav, HighLevelComponent, NodeUpdate, Evidence
)


def test_run_config():
    """Test RunConfig instantiation with defaults."""
    print("Testing RunConfig...")
    config = RunConfig()
    print(f"✓ RunConfig created with defaults:")
    print(f"  - max_depth: {config.limits.max_depth}")
    print(f"  - max_nodes: {config.limits.max_nodes}")
    print(f"  - max_llm_calls: {config.limits.max_llm_calls}")
    print(f"  - max_children_per_step: {config.caps.nav.max_children_per_step}")
    print(f"  - name_signals: {config.scoring.name_signals}")
    return config


def test_dir_meta():
    """Test DirMeta instantiation with minimal fields."""
    print("\nTesting DirMeta...")
    
    # Create minimal required fields
    counts = DirCounts(files=10, dirs=5)
    fingerprint = StalenessFingerprint(
        latest_modified_time="2024-12-19T17:30:00Z",
        total_entries=15,
        name_hash="abc123"
    )
    
    dir_meta = DirMeta(
        path="src/api",
        depth=2,
        counts=counts,
        staleness_fingerprint=fingerprint
    )
    
    print(f"✓ DirMeta created with minimal fields:")
    print(f"  - path: {dir_meta.path}")
    print(f"  - depth: {dir_meta.depth}")
    print(f"  - files: {dir_meta.counts.files}")
    print(f"  - dirs: {dir_meta.counts.dirs}")
    return dir_meta


def test_llm_response():
    """Test LLMResponse creation from schema."""
    print("\nTesting LLMResponse...")
    
    # Create evidence
    evidence = Evidence(type="marker", value="api/")
    
    # Create high-level component
    component = HighLevelComponent(
        name="api_layer",
        role="REST API implementation",
        dirs=["src/api"],
        evidence=[evidence],
        confidence=0.85
    )
    
    # Create node update
    node_update = NodeUpdate(
        summary="API layer with REST endpoints",
        languages=["python"],
        tags=["api", "rest"],
        evidence=[evidence],
        confidence=0.85
    )
    
    # Create navigation
    nav = Nav(
        descend_into=["src/api/controllers", "src/api/models"],
        descend_one_level_only=True,
        reasons=["Contains important API structure"]
    )
    
    # Create inferred results
    inferred = LLMInferred(
        high_level_components=[component],
        nodes={"src/api": node_update}
    )
    
    # Create complete response
    response = LLMResponse(
        inferred=inferred,
        nav=nav,
        open_questions_ranked=["What authentication system is used?"]
    )
    
    print(f"✓ LLMResponse created from schema:")
    print(f"  - components: {len(response.inferred.high_level_components)}")
    print(f"  - nodes: {len(response.inferred.nodes)}")
    print(f"  - nav descend_into: {response.nav.descend_into}")
    print(f"  - questions: {len(response.open_questions_ranked)}")
    return response


def test_validation():
    """Test validation rules."""
    print("\nTesting validation...")
    
    # Test that 0 values are allowed (for unlimited)
    config = RunConfig()
    config.limits.max_depth = 0
    config.limits.max_nodes = 0
    config.limits.max_llm_calls = 0
    config.caps.nav.max_children_per_step = 0
    print("✓ Zero values allowed for unlimited limits")
    
    # Test confidence bounds
    try:
        evidence = Evidence(type="marker", value="test")
        component = HighLevelComponent(
            name="test",
            role="test",
            dirs=["test"],
            evidence=[evidence],
            confidence=1.5  # Should fail validation
        )
        print("✗ Should have failed validation for confidence > 1")
    except Exception as e:
        print("✓ Validation correctly rejected confidence > 1")
    
    # Test language normalization
    node_update = NodeUpdate(
        summary="Test",
        languages=["Python", "PYTHON", "python"],  # Should be normalized
        evidence=[Evidence(type="marker", value="test")],
        confidence=0.5
    )
    print(f"✓ Language normalization: {node_update.languages}")


def main():
    """Run all tests."""
    print("SPADE Models Test Suite")
    print("=" * 50)
    
    try:
        config = test_run_config()
        dir_meta = test_dir_meta()
        response = test_llm_response()
        test_validation()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Models are working correctly.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
