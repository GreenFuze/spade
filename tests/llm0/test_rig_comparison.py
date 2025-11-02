"""
Unit tests for RIG comparison functionality.

Tests the normalization and comparison logic that allows RIGs generated
independently to be compared semantically, ignoring auto-generated ID differences.
"""

import pytest
from pathlib import Path
from core.rig import RIG
from core.schemas import (
    Component, ComponentType, Evidence, RepositoryInfo,
    BuildSystemInfo, TestDefinition
)


def test_identical_rigs_with_different_ids_are_equal():
    """Test that two semantically identical RIGs with different IDs compare as equal."""
    # Create first RIG
    rig1 = RIG()
    rig1.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))
    rig1.set_build_system_info(BuildSystemInfo(
        name="CMake",
        version="3.20",
        build_type="Debug"
    ))

    # Add components to rig1
    evidence1 = Evidence(line=["CMakeLists.txt:5"])
    comp1 = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[evidence1]
    )
    rig1.add_component(comp1)

    # Create second RIG with same content but independent ID generation
    rig2 = RIG()
    rig2.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))
    rig2.set_build_system_info(BuildSystemInfo(
        name="CMake",
        version="3.20",
        build_type="Debug"
    ))

    # Add same components to rig2 (will have different IDs due to separate counters)
    evidence2 = Evidence(line=["CMakeLists.txt:5"])
    comp2 = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[evidence2]
    )
    rig2.add_component(comp2)

    # Verify IDs are different (they're auto-generated independently)
    assert comp1.id != comp2.id
    assert evidence1.id != evidence2.id

    # But the RIGs should compare as equal
    diff = rig1.compare(rig2)
    assert diff is None, f"RIGs should be equal but got diff:\n{diff}"


def test_different_rigs_are_not_equal():
    """Test that two RIGs with different content are correctly identified as different."""
    # Create first RIG
    rig1 = RIG()
    rig1.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    evidence1 = Evidence(line=["CMakeLists.txt:5"])
    comp1 = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[evidence1]
    )
    rig1.add_component(comp1)

    # Create second RIG with different component
    rig2 = RIG()
    rig2.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    evidence2 = Evidence(line=["CMakeLists.txt:8"])
    comp2 = Component(
        name="utils.lib",  # Different name
        type=ComponentType.STATIC_LIBRARY,  # Different type
        programming_language="cxx",
        relative_path=Path("build/utils.lib"),
        source_files=[Path("src/utils.cpp")],  # Different source
        evidence=[evidence2]
    )
    rig2.add_component(comp2)

    # RIGs should be different
    diff = rig1.compare(rig2)
    assert diff is not None, "RIGs with different content should not be equal"
    assert "hello.exe" in diff or "utils.lib" in diff


def test_same_components_different_order_are_equal():
    """Test that RIGs with same components in different order compare as equal."""
    # Create first RIG with components in one order
    rig1 = RIG()
    rig1.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    evidence1a = Evidence(line=["CMakeLists.txt:5"])
    comp1a = Component(
        name="aaa.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/aaa.exe"),
        source_files=[Path("src/aaa.cpp")],
        evidence=[evidence1a]
    )
    evidence1b = Evidence(line=["CMakeLists.txt:10"])
    comp1b = Component(
        name="zzz.lib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="cxx",
        relative_path=Path("build/zzz.lib"),
        source_files=[Path("src/zzz.cpp")],
        evidence=[evidence1b]
    )
    rig1.add_component(comp1a)
    rig1.add_component(comp1b)

    # Create second RIG with components in reverse order
    rig2 = RIG()
    rig2.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    evidence2a = Evidence(line=["CMakeLists.txt:10"])
    comp2a = Component(
        name="zzz.lib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="cxx",
        relative_path=Path("build/zzz.lib"),
        source_files=[Path("src/zzz.cpp")],
        evidence=[evidence2a]
    )
    evidence2b = Evidence(line=["CMakeLists.txt:5"])
    comp2b = Component(
        name="aaa.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/aaa.exe"),
        source_files=[Path("src/aaa.cpp")],
        evidence=[evidence2b]
    )
    rig2.add_component(comp2a)
    rig2.add_component(comp2b)

    # RIGs should be equal despite different order
    diff = rig1.compare(rig2)
    assert diff is None, f"RIGs with same content in different order should be equal but got diff:\n{diff}"


def test_rigs_with_dependencies_compare_correctly():
    """Test that RIGs with dependencies are normalized and compared correctly."""
    # Create first RIG
    rig1 = RIG()
    rig1.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    # Add library
    evidence1a = Evidence(line=["CMakeLists.txt:5"])
    lib1 = Component(
        name="utils.lib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="cxx",
        relative_path=Path("build/utils.lib"),
        source_files=[Path("src/utils.cpp")],
        evidence=[evidence1a]
    )
    rig1.add_component(lib1)

    # Add executable that depends on library
    evidence1b = Evidence(line=["CMakeLists.txt:10"])
    exe1 = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[evidence1b],
        depends_on=[lib1]
    )
    rig1.add_component(exe1)

    # Create second RIG with same structure
    rig2 = RIG()
    rig2.set_repository_info(RepositoryInfo(
        name="TestRepo",
        root_path=Path("/test")
    ))

    # Add library
    evidence2a = Evidence(line=["CMakeLists.txt:5"])
    lib2 = Component(
        name="utils.lib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="cxx",
        relative_path=Path("build/utils.lib"),
        source_files=[Path("src/utils.cpp")],
        evidence=[evidence2a]
    )
    rig2.add_component(lib2)

    # Add executable that depends on library
    evidence2b = Evidence(line=["CMakeLists.txt:10"])
    exe2 = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[evidence2b],
        depends_on=[lib2]
    )
    rig2.add_component(exe2)

    # Verify IDs are different
    assert lib1.id != lib2.id
    assert exe1.id != exe2.id

    # But dependency structure should be the same after normalization
    diff = rig1.compare(rig2)
    assert diff is None, f"RIGs with same dependency structure should be equal but got diff:\n{diff}"


def test_compute_stable_key():
    """Test the stable key computation for different entity types."""
    # Test Component
    comp = Component(
        name="hello.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("build/hello.exe"),
        source_files=[Path("src/main.cpp")],
        evidence=[Evidence(line=["test:1"])]
    )
    key = RIG._compute_stable_key(comp)
    assert key == "hello.exe:executable:cxx"

    # Test Evidence
    evidence = Evidence(line=["CMakeLists.txt:5"])
    key = RIG._compute_stable_key(evidence)
    assert key == "evidence:CMakeLists.txt:5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
