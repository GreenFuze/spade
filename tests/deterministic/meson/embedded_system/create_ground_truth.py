#!/usr/bin/env python3
"""
Ground truth generator for Meson embedded_system test repository.

This script creates the canonical RIG (Repository Information Graph) for the
embedded_system test repository, which demonstrates:
- Meson custom_target() for code generation
- Meson configure_file() for build-time configuration
- Meson subprojects with wrap files
- Mixed C/C++ codebase with static and shared libraries
- Unit tests as separate components
"""

from pathlib import Path

from core.rig import RIG
from core.schemas import (
    Component, TestDefinition, Evidence, ComponentType,
    RepositoryInfo, BuildSystemInfo, ExternalPackage,
    PackageManager, Aggregator, RIGValidationError
)
from tests.test_utils import test_repos_root


def main() -> None:
    rig = RIG()

    # Repository information
    repo_root = test_repos_root / "meson" / "embedded_system"
    rig.set_repository_info(
        RepositoryInfo(
            name="embedded_system",
            root_path=repo_root,
            build_directory=repo_root / "build",
            output_directory=repo_root / "build",
            install_directory=None,
            configure_command="meson setup build",
            build_command="meson compile -C build",
            install_command="meson install -C build",
            test_command="meson test -C build",
        )
    )

    # Build system information
    rig.set_build_system_info(
        BuildSystemInfo(
            name="meson",
            version="1.0.0",
            build_type="Release",
        )
    )

    # External packages
    # Note: json-c comes from Meson wrap (subproject)
    external_packages = []
    package_managers = {
        "json-c": PackageManager(name="meson", package_name="json-c"),
        "cmocka": PackageManager(name="system", package_name="cmocka"),
        "gtest": PackageManager(name="system", package_name="gtest"),
        "threads": PackageManager(name="system", package_name="threads"),
        "m": PackageManager(name="system", package_name="m"),
        "dl": PackageManager(name="system", package_name="dl"),
    }

    for name, pm in package_managers.items():
        external_packages.append(ExternalPackage(name=name, package_manager=pm))

    # Reference external packages by index
    json_c = external_packages[0]
    cmocka = external_packages[1]
    gtest = external_packages[2]
    pthread = external_packages[3]
    m_lib = external_packages[4]
    dl_lib = external_packages[5]

    # =========================================================================
    # Components
    # =========================================================================

    # Component 1: libcore.a (Static library, C)
    # Core system functionality
    libcore = Component(
        name="libcore.a",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="c",
        relative_path=Path("build/src/core/libcore.a"),
        source_files=[
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),  # Input template for configure_file()
        ],
        external_packages=[json_c, m_lib],
        evidence=[Evidence(line=["src/core/meson.build:10"])],  # static_library('core')
        locations=[],
    )
    rig.add_component(libcore)

    # Component 2: libdrivers.so (Shared library, C++)
    # Device drivers (UART, SPI)
    libdrivers = Component(
        name="libdrivers.so",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cpp",
        relative_path=Path("build/src/drivers/libdrivers.so"),
        source_files=[
            Path("src/drivers/uart.cpp"),
            Path("src/drivers/uart.hpp"),
            Path("src/drivers/spi.cpp"),
            Path("src/drivers/spi.hpp"),
            # Transitive source files from libcore
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),
        ],
        external_packages=[json_c, m_lib, dl_lib],
        depends_on=[libcore],
        evidence=[Evidence(line=["src/drivers/meson.build:10"])],  # shared_library('drivers')
        locations=[],
    )
    rig.add_component(libdrivers)

    # Component 3: libprotocol.a (Static library, C)
    # Protocol handler with generated code
    libprotocol = Component(
        name="libprotocol.a",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="c",
        relative_path=Path("build/src/protocol/libprotocol.a"),
        source_files=[
            Path("src/protocol/handler.c"),
            Path("src/protocol/handler.h"),
            Path("src/protocol/protocol.proto"),  # Input for code generation
            Path("tools/generate_protocol.py"),  # Generator script
            # Transitive source files from libcore
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),
        ],
        external_packages=[json_c, m_lib],
        depends_on=[libcore],
        evidence=[Evidence(line=["src/protocol/meson.build:18"])],  # static_library('protocol')
        locations=[],
    )
    rig.add_component(libprotocol)

    # Component 4: firmware.elf (Executable, C)
    # Main firmware application
    firmware = Component(
        name="firmware.elf",
        type=ComponentType.EXECUTABLE,
        programming_language="c",
        relative_path=Path("build/src/app/firmware.elf"),
        source_files=[
            Path("src/app/main.c"),
            # Transitive from libcore
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),
            # Transitive from libdrivers
            Path("src/drivers/uart.cpp"),
            Path("src/drivers/uart.hpp"),
            Path("src/drivers/spi.cpp"),
            Path("src/drivers/spi.hpp"),
            # Transitive from libprotocol
            Path("src/protocol/handler.c"),
            Path("src/protocol/handler.h"),
            Path("src/protocol/protocol.proto"),
            Path("tools/generate_protocol.py"),
        ],
        external_packages=[json_c, m_lib, dl_lib, pthread],
        depends_on=[libcore, libdrivers, libprotocol],
        evidence=[Evidence(line=["src/app/meson.build:7"])],  # executable('firmware.elf')
        locations=[],
    )
    rig.add_component(firmware)

    # Component 5: test_system (Executable, C)
    # Unit tests for core library
    test_system = Component(
        name="test_system",
        type=ComponentType.EXECUTABLE,
        programming_language="c",
        relative_path=Path("build/tests/test_system"),
        source_files=[
            Path("tests/test_system.c"),
            # Transitive from libcore
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),
        ],
        external_packages=[json_c, m_lib, cmocka],
        depends_on=[libcore],
        evidence=[Evidence(line=["tests/meson.build:6"])],  # executable('test_system')
        locations=[],
    )
    rig.add_component(test_system)

    # Component 6: test_drivers (Executable, C++)
    # Unit tests for drivers library
    test_drivers = Component(
        name="test_drivers",
        type=ComponentType.EXECUTABLE,
        programming_language="cpp",
        relative_path=Path("build/tests/test_drivers"),
        source_files=[
            Path("tests/test_drivers.cpp"),
            # Transitive from libdrivers
            Path("src/drivers/uart.cpp"),
            Path("src/drivers/uart.hpp"),
            Path("src/drivers/spi.cpp"),
            Path("src/drivers/spi.hpp"),
            # Transitive from libcore
            Path("src/core/system.c"),
            Path("src/core/system.h"),
            Path("src/core/memory.c"),
            Path("src/core/memory.h"),
            Path("config.h.in"),
        ],
        external_packages=[json_c, m_lib, dl_lib, gtest],
        depends_on=[libdrivers],
        evidence=[Evidence(line=["tests/meson.build:16"])],  # executable('test_drivers')
        locations=[],
    )
    rig.add_component(test_drivers)

    # =========================================================================
    # Aggregators
    # =========================================================================

    # Aggregator 1: build-all
    # Builds all components
    build_all = Aggregator(
        name="build-all",
        depends_on=[firmware, test_system, test_drivers],
        evidence=[Evidence(line=["meson.build:43"])]  # run_target('build-all')
    )
    rig.add_aggregator(build_all)

    # =========================================================================
    # Tests
    # =========================================================================

    # Test 1: Core system tests
    test_def_system = TestDefinition(
        name="Core System Tests",
        test_executable_component=test_system,
        test_framework="cmocka",
        source_files=[Path("tests/test_system.c")],
        evidence=[Evidence(line=["tests/meson.build:11"])]  # test('Core System Tests')
    )
    rig.add_test(test_def_system)

    # Test 2: Driver tests
    test_def_drivers = TestDefinition(
        name="Driver Tests",
        test_executable_component=test_drivers,
        test_framework="gtest",
        source_files=[Path("tests/test_drivers.cpp")],
        evidence=[Evidence(line=["tests/meson.build:21"])]  # test('Driver Tests')
    )
    rig.add_test(test_def_drivers)

    # =========================================================================
    # Validation and save
    # =========================================================================

    # Validate RIG
    validation_errors = rig.validate()
    if validation_errors:
        print("RIG Validation Errors:")
        for error in validation_errors:
            print(f"  - {error}")
        raise ValueError("RIG validation failed")

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "embedded_system_ground_truth.sqlite3"
    rig.save(sqlite_path)
    print(f"[OK] Saved RIG to: {sqlite_path}")

    # Save to JSON
    json_path = Path(__file__).parent / "embedded_system_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)
    print(f"[OK] Saved JSON to: {json_path}")

    # Reload and compare (determinism check)
    rig_loaded = RIG.load(sqlite_path)
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match original:\n{diff_text}")
    print("[OK] Determinism check passed")

    # =========================================================================
    # Complexity calculation
    # =========================================================================

    all_components = [libcore, libdrivers, libprotocol, firmware, test_system, test_drivers]
    all_aggregators = [build_all]

    component_count = len(all_components)
    programming_languages = set(c.programming_language for c in all_components)
    programming_language_count = len(programming_languages)

    external_packages = set()
    for c in all_components:
        external_packages.update(pkg.name for pkg in c.external_packages)
    external_package_count = len(external_packages)

    # Calculate max dependency depth
    def get_depth(component, memo=None):
        if memo is None:
            memo = {}
        if component.name in memo:
            return memo[component.name]
        if not component.depends_on:
            memo[component.name] = 0
            return 0
        max_dep_depth = max(get_depth(dep, memo) for dep in component.depends_on)
        memo[component.name] = max_dep_depth + 1
        return max_dep_depth + 1

    max_dependency_depth = max(get_depth(c) for c in all_components)

    aggregator_count = len(all_aggregators)

    has_cross_language_dependencies = len(programming_languages) > 1

    # Calculate raw score
    raw_score = (
        component_count * 2 +
        programming_language_count * 10 +
        external_package_count * 3 +
        max_dependency_depth * 8 +
        aggregator_count * 5 +
        (15 if has_cross_language_dependencies else 0)
    )

    # Normalize to 0-100 scale (229 is the maximum from metaffi)
    normalized_score = (raw_score / 229) * 100

    print("\n" + "=" * 70)
    print("COMPLEXITY ANALYSIS")
    print("=" * 70)
    print(f"Components:              {component_count:>3} × 2  = {component_count * 2:>3}")
    print(f"Programming Languages:   {programming_language_count:>3} × 10 = {programming_language_count * 10:>3}")
    print(f"  Languages: {', '.join(sorted(programming_languages))}")
    print(f"External Packages:       {external_package_count:>3} × 3  = {external_package_count * 3:>3}")
    print(f"  Packages: {', '.join(sorted(external_packages))}")
    print(f"Max Dependency Depth:    {max_dependency_depth:>3} × 8  = {max_dependency_depth * 8:>3}")
    print(f"Aggregators:             {aggregator_count:>3} × 5  = {aggregator_count * 5:>3}")
    print(f"Cross-language:         {'Yes' if has_cross_language_dependencies else 'No':>4} × 1  = {15 if has_cross_language_dependencies else 0:>3}")
    print("-" * 70)
    print(f"RAW SCORE:                      = {raw_score:>3}")
    print(f"NORMALIZED SCORE:               = {normalized_score:>6.2f}")
    print("=" * 70)

    # Verify target complexity
    if 35 <= normalized_score <= 40:
        print(f"[OK] Complexity score {normalized_score:.2f} is within target range (35-40)")
    else:
        print(f"[WARNING] Complexity score {normalized_score:.2f} is outside target range (35-40)")

    print("\n[OK] Ground truth generated successfully!")


if __name__ == "__main__":
    main()
