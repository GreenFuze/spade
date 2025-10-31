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
    ExternalPackage,
    PackageManager,
)

from tests.test_utils import test_repos_root

def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "jni_hello_world"

    # Set repository and build system info via public setters
    rig.set_repository_info(
        RepositoryInfo(
            name="JNIHelloWorld",
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

    # Create external package for JNI
    jni_package_manager = PackageManager(
        name="CMake",
        package_name="JNI"
    )

    jni_external_package = ExternalPackage(
        name="JNI",
        package_manager=jni_package_manager
    )

    # Component 1: JAR library (no dependencies)
    java_hello_lib = Component(
        name="java_hello_lib-1.0.0.jar",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("spade_build/java_hello_lib-1.0.0.jar"),
        source_files=[
            Path("src/java/HelloWorld.java"),
            Path("src/java/HelloWorldJNI.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:36"])],
        locations=[],
    )

    # Component 2: math_lib JAR (built with custom commands)
    math_lib = Component(
        name="math_lib-1.0.0.jar",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("spade_build/math_lib-1.0.0.jar"),
        source_files=[
            Path("src/java/MathUtils.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:82"])],
        locations=[],
    )

    # Component 3: Go shared library (built with go build -buildmode=c-shared)
    hello_go_lib = Component(
        name="libhello.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("spade_build/libhello.dll"),
        source_files=[
            Path("src/go/hello.go")
        ],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:107"])],
        locations=[],
    )

    # Component 4: C++ executable that uses JAR (runtime dependency)
    jni_hello_world = Component(
        name="jni_hello_world.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("spade_build/Debug/jni_hello_world.exe"),
        source_files=[
            Path("src/cpp/main.cpp"),
            Path("src/cpp/jni_wrapper.cpp")
        ],
        external_packages=[jni_external_package],
        evidence=[Evidence(line=["CMakeLists.txt:30"])],
        locations=[],
        depends_on=[java_hello_lib, math_lib, hello_go_lib]
    )

    # Component 5: Test executable
    test_jni_wrapper = Component(
        name="test_jni_wrapper.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("spade_build/Debug/test_jni_wrapper.exe"),
        source_files=[
            Path("tests/cpp/test_jni_wrapper.cpp"),
            Path("src/cpp/jni_wrapper.cpp")
        ],
        external_packages=[jni_external_package],
        evidence=[Evidence(line=["CMakeLists.txt:60"])],
        locations=[],
    )


    rig.add_component(java_hello_lib)
    rig.add_component(math_lib)
    rig.add_component(hello_go_lib)
    rig.add_component(jni_hello_world)
    rig.add_component(test_jni_wrapper)

    # Add the test: add_test(NAME test_jni_wrapper_cpp COMMAND test_jni_wrapper)
    ctest_test = TestDefinition(
        name="test_jni_wrapper_cpp",
        test_executable_component=test_jni_wrapper,
        test_executable_component_id=None,
        test_components=[jni_hello_world],
        test_framework="CTest",
        source_files=[Path("src/main.cpp")],
        evidence=[Evidence(line=["CMakeLists.txt:75"])],
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
    sqlite_path = Path(__file__).parent / "jni_hello_world_ground_truth.sqlite3"
    rig.save(sqlite_path)

    # Write JSON prompt (unoptimized for readability in ground-truth)
    json_path = Path(__file__).parent / "jni_hello_world_ground_truth.json"
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
