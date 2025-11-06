from pathlib import Path

from core.rig import RIG
from core.schemas import (
    Component,
    TestDefinition,
    Evidence,
    ComponentType,
    RepositoryInfo,
    BuildSystemInfo,
    RIGValidationError,
)

from tests.test_utils import test_repos_root

def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "cmake" / "cmake_hello_world"

    # Set repository and build system info via public setters
    rig.set_repository_info(
        RepositoryInfo(
            name="CMakeHelloWorld",
            root_path=repo_root,
            build_directory=repo_root / "spade_build",
            output_directory=repo_root / "spade_build",
            install_directory=None,
            configure_command=None,
            build_command=None,
            install_command=None,
            test_command=None,
        )
    )

    rig.set_build_system_info(
        BuildSystemInfo(
            name="CMake",
            version=None,
            build_type="Debug",
        )
    )
    
    lib = Component(
        name="utils.lib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="cxx",
        relative_path=Path("spade_build/Debug/utils.lib"),
        source_files=[Path("src/utils.cpp")],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:8"])],
        locations=[],
    )

    # Manually create ground-truth components
    executable = Component(
        name="hello_world.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("spade_build/Debug/hello_world.exe"),
        source_files=[Path("src/main.cpp")],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:5"])],
        locations=[],
        depends_on=[lib]
    )

    
    rig.add_component(executable)
    rig.add_component(lib)

    # Add the test: add_test(NAME test_hello_world COMMAND hello_world)
    ctest_test = TestDefinition(
        name="test_hello_world",
        test_executable_component=executable,
        test_executable_component_id=None,
        test_components=[lib],
        test_framework="CTest",
        source_files=[Path("src/main.cpp")],
        evidence=[Evidence(line=["CMakeLists.txt:15"])],
    )
    rig.add_test(ctest_test)

    # Validate before saving/writing outputs (fail-fast on errors)
    validation_errors = rig.validate()
    if len(validation_errors) > 0:
        # print validation errors
        for error in validation_errors:
            print(f"""Validation Error ({error.category}):
    File: {error.file_path}
    Message: {error.message}
    Node Name: {error.node_name}
""")
        raise RIGValidationError(validation_errors)

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "cmake_hello_world_ground_truth.sqlite3"
    rig.save(sqlite_path)

    # Write JSON prompt (unoptimized for readability in ground-truth)
    json_path = Path(__file__).parent / "cmake_hello_world_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)
        
    # load from SQLite into a new RIG instance and compare
    # to make sure there's no serialization/deserialization issues
    rig_loaded = RIG.load(sqlite_path)

    # Use the new compare() method
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match ground truth:\n{diff_text}")


if __name__ == "__main__":
    main()