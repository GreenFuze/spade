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
    repo_root = test_repos_root / "cmake" / "jni_hello_world"

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

    # Create external packages for JUnit and Hamcrest
    junit_package_manager = PackageManager(
        name="Maven",
        package_name="junit:junit:4.13.2"
    )

    junit_external_package = ExternalPackage(
        name="junit-4.13.2.jar",
        package_manager=junit_package_manager
    )

    hamcrest_package_manager = PackageManager(
        name="Maven",
        package_name="org.hamcrest:hamcrest-core:1.3"
    )

    hamcrest_external_package = ExternalPackage(
        name="hamcrest-core-1.3.jar",
        package_manager=hamcrest_package_manager
    )

    # Component 1: Java JAR library (built via add_jar at line 36)
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

    # Component 2: Math JAR library (built via add_custom_jar at line 82)
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

    # Component 3: Go shared library (built via add_go_shared_library at line 107)
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

    # Component 4: Main C++ executable (built via add_executable at line 30)
    # Dependencies:
    #   - hello_go_lib: add_dependencies at line 127
    #   - java_hello_lib, math_lib: runtime classpath dependencies at line 123
    #   - JNI: external package via target_link_libraries at line 112
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

    # Component 5: C++ test executable (built via add_executable at line 138)
    # Links to JNI via target_link_libraries at line 143
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
        evidence=[Evidence(line=["CMakeLists.txt:138"])],
        locations=[],
    )

    # Component 6: Java JUnit test class (built via add_custom_command at line 161)
    # This compiles HelloWorldTest.java to .class file
    # Depends on java_hello_lib and uses junit and hamcrest
    hello_world_test_java = Component(
        name="HelloWorldTest.class",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("spade_build/test_classes/HelloWorldTest.class"),
        source_files=[
            Path("tests/java/HelloWorldTest.java")
        ],
        external_packages=[junit_external_package, hamcrest_external_package],
        evidence=[Evidence(line=["CMakeLists.txt:161"])],
        locations=[],
        depends_on=[java_hello_lib]
    )


    rig.add_component(java_hello_lib)
    rig.add_component(math_lib)
    rig.add_component(hello_go_lib)
    rig.add_component(jni_hello_world)
    rig.add_component(test_jni_wrapper)
    rig.add_component(hello_world_test_java)

    # Add the CTest test: add_test(NAME test_jni_wrapper_cpp COMMAND test_jni_wrapper) at line 153
    # This test runs test_jni_wrapper.exe which tests the JNI wrapper functionality
    ctest_test = TestDefinition(
        name="test_jni_wrapper_cpp",
        test_executable_component=test_jni_wrapper,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("tests/cpp/test_jni_wrapper.cpp"),
            Path("src/cpp/jni_wrapper.cpp")
        ],
        evidence=[Evidence(line=["CMakeLists.txt:153"])],
    )
    rig.add_test(ctest_test)

    # Add the JUnit test: add_test(NAME test_hello_world_java ...) at line 185
    # This test runs JUnit on HelloWorldTest.class
    # The test_executable_component is HelloWorldTest.class which is executed by java/JUnit
    junit_test = TestDefinition(
        name="test_hello_world_java",
        test_executable_component=hello_world_test_java,
        test_executable_component_id=None,
        test_components=[],
        test_framework="JUnit",
        source_files=[
            Path("tests/java/HelloWorldTest.java")
        ],
        evidence=[Evidence(line=["CMakeLists.txt:185"])],
    )
    rig.add_test(junit_test)

    # Add the Go test: add_test(NAME test_hello_go ...) at line 193
    # This test runs 'go test' on the Go source files
    # For Go tests, there's no single executable - it's the test framework running the test files
    # We'll use hello_go_lib as a proxy for what's being tested
    go_test = TestDefinition(
        name="test_hello_go",
        test_executable_component=hello_go_lib,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[
            Path("src/go/hello_test.go"),
            Path("src/go/hello.go")
        ],
        evidence=[Evidence(line=["CMakeLists.txt:193"])],
    )
    rig.add_test(go_test)

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
