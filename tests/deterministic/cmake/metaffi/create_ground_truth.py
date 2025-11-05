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
from typing import List


# ==================== CMake Variable Expansion Helpers ====================


def collect_c_cpp_files(base_dirs: List[Path], repo_root: Path, exclude_tests: bool = True) -> List[Path]:
    """
    Simulate CMake's collect_c_cpp_files() macro.

    Scans directories for .c, .cpp files.
    Optionally filters out test files (*_test.cpp, *_test.c).

    This matches the behavior of the CMake macro defined in cmake/CPP.cmake:30-59
    which uses file(GLOB ...) to collect source files.

    Args:
        base_dirs: List of directories to scan (non-recursive)
        repo_root: Repository root path to compute relative paths
        exclude_tests: If True, filter out *_test.c and *_test.cpp files

    Returns:
        List of source files (.c, .cpp) as relative paths from repo root, sorted for deterministic order
    """
    source_files = []
    extensions = [".c", ".cpp"]

    for base_dir in base_dirs:
        if not base_dir.exists():
            continue

        for ext in extensions:
            # Use glob for non-recursive scan (matches CMake file(GLOB ...) behavior)
            for file in base_dir.glob(f"*{ext}"):
                # Exclude test files (matching CMake macro logic)
                if exclude_tests and file.stem.endswith("_test"):
                    continue
                # Convert to relative path from repo root
                relative_file = file.relative_to(repo_root)
                source_files.append(relative_file)

    return sorted(source_files)  # Sort for deterministic order


# CMake variable to directory mappings
# These map to collect_c_cpp_files() calls throughout the CMakeLists.txt files
REPO_PATH = test_repos_root / "cmake" / "metaffi"

CMAKE_VARS = {
    # ${sdk_src} - defined in each plugin-sdk/CMakeLists.txt
    # collect_c_cpp_files("${CMAKE_CURRENT_LIST_DIR};.../compiler;.../runtime;.../utils" sdk)
    "sdk_src": {
        "metaffi-core": [
            REPO_PATH / "metaffi-core/plugin-sdk",
            REPO_PATH / "metaffi-core/plugin-sdk/compiler",
            REPO_PATH / "metaffi-core/plugin-sdk/runtime",
            REPO_PATH / "metaffi-core/plugin-sdk/utils",
        ],
        "lang-plugin-c": [
            REPO_PATH / "lang-plugin-c/plugin-sdk",
            REPO_PATH / "lang-plugin-c/plugin-sdk/compiler",
            REPO_PATH / "lang-plugin-c/plugin-sdk/runtime",
            REPO_PATH / "lang-plugin-c/plugin-sdk/utils",
        ],
        "lang-plugin-go": [
            REPO_PATH / "lang-plugin-go/plugin-sdk",
            REPO_PATH / "lang-plugin-go/plugin-sdk/compiler",
            REPO_PATH / "lang-plugin-go/plugin-sdk/runtime",
            REPO_PATH / "lang-plugin-go/plugin-sdk/utils",
        ],
        "lang-plugin-openjdk": [
            REPO_PATH / "lang-plugin-openjdk/plugin-sdk",
            REPO_PATH / "lang-plugin-openjdk/plugin-sdk/compiler",
            REPO_PATH / "lang-plugin-openjdk/plugin-sdk/runtime",
            REPO_PATH / "lang-plugin-openjdk/plugin-sdk/utils",
        ],
        "lang-plugin-python311": [
            REPO_PATH / "lang-plugin-python311/plugin-sdk",
            REPO_PATH / "lang-plugin-python311/plugin-sdk/compiler",
            REPO_PATH / "lang-plugin-python311/plugin-sdk/runtime",
            REPO_PATH / "lang-plugin-python311/plugin-sdk/utils",
        ],
    },
    # ${xllr_src} - metaffi-core/XLLR/CMakeLists.txt:4
    "xllr_src": [REPO_PATH / "metaffi-core/XLLR"],
    # ${cli_src} - metaffi-core/CLI/CMakeLists.txt:4
    "cli_src": [REPO_PATH / "metaffi-core/CLI"],
    # ${xllr.python311_src} - lang-plugin-python311/runtime/CMakeLists.txt:4
    "xllr.python311_src": [REPO_PATH / "lang-plugin-python311/runtime"],
    # ${xllr.openjdk_src} - lang-plugin-openjdk/runtime/CMakeLists.txt:4
    "xllr.openjdk_src": [REPO_PATH / "lang-plugin-openjdk/runtime"],
    # ${xllr.go_src} - lang-plugin-go/runtime/CMakeLists.txt:4
    "xllr.go_src": [REPO_PATH / "lang-plugin-go/runtime"],
    # ${xllr.c_src} - lang-plugin-c/runtime/CMakeLists.txt:4
    "xllr.c_src": [REPO_PATH / "lang-plugin-c/runtime"],
    # ${idl.c_src} - lang-plugin-c/idl/CMakeLists.txt:4
    "idl.c_src": [REPO_PATH / "lang-plugin-c/idl"],
    # ${metaffi_idl_python311_src} - lang-plugin-python311/idl/CMakeLists.txt:4
    "metaffi_idl_python311_src": [REPO_PATH / "lang-plugin-python311/idl"],
    # ${xllr.openjdk.jni.bridge_src} - lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt:4
    "xllr.openjdk.jni.bridge_src": [REPO_PATH / "lang-plugin-openjdk/xllr-openjdk-bridge"],
}

# Pre-compute file lists for reuse (this is done once at module load time)
CMAKE_VAR_FILES = {}
print("Expanding CMake variables...")
for var_name, dirs in CMAKE_VARS.items():
    if isinstance(dirs, dict):
        # sdk_src has per-plugin variants
        CMAKE_VAR_FILES[var_name] = {}
        for plugin, plugin_dirs in dirs.items():
            files = collect_c_cpp_files(plugin_dirs, REPO_PATH)
            CMAKE_VAR_FILES[var_name][plugin] = files
            print(f"  ${var_name}[{plugin}]: {len(files)} files")
    else:
        files = collect_c_cpp_files(dirs, REPO_PATH)
        CMAKE_VAR_FILES[var_name] = files
        print(f"  ${var_name}: {len(files)} files")


def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "cmake" / "metaffi"

    # Set repository and build system info
    rig.set_repository_info(
        RepositoryInfo(
            name="MetaFFI",
            root_path=repo_root,
            build_directory=repo_root / "cmake-build-debug",
            output_directory=repo_root / "output" / "windows" / "x64" / "Debug",
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

    # ==================== External Packages ====================

    # Boost components
    boost_filesystem_mgr = PackageManager(name="vcpkg", package_name="boost-filesystem")
    boost_filesystem = ExternalPackage(name="Boost.filesystem", package_manager=boost_filesystem_mgr)

    boost_thread_mgr = PackageManager(name="vcpkg", package_name="boost-thread")
    boost_thread = ExternalPackage(name="Boost.thread", package_manager=boost_thread_mgr)

    boost_program_options_mgr = PackageManager(name="vcpkg", package_name="boost-program-options")
    boost_program_options = ExternalPackage(name="Boost.program_options", package_manager=boost_program_options_mgr)

    # JNI
    jni_mgr = PackageManager(name="CMake", package_name="JNI")
    jni_package = ExternalPackage(name="JNI", package_manager=jni_mgr)

    # doctest
    doctest_mgr = PackageManager(name="vcpkg", package_name="doctest")
    doctest_package = ExternalPackage(name="doctest", package_manager=doctest_mgr)

    # External JAR files for openjdk_idl_extractor
    gson_mgr = PackageManager(name="Maven", package_name="com.google.code.gson:gson:2.10.1")
    gson_package = ExternalPackage(name="gson-2.10.1.jar", package_manager=gson_mgr)

    asm_mgr = PackageManager(name="Maven", package_name="org.ow2.asm:asm:9.6")
    asm_package = ExternalPackage(name="asm-9.6.jar", package_manager=asm_mgr)

    asm_tree_mgr = PackageManager(name="Maven", package_name="org.ow2.asm:asm-tree:9.6")
    asm_tree_package = ExternalPackage(name="asm-tree-9.6.jar", package_manager=asm_tree_mgr)

    javaparser_mgr = PackageManager(name="Maven", package_name="com.github.javaparser:javaparser-core:3.24.4")
    javaparser_package = ExternalPackage(name="javaparser-core-3.24.4.jar", package_manager=javaparser_mgr)

    # ==================== METAFFI-CORE AGGREGATOR ====================
    # Components defined in metaffi-core/

    # TODO: Collect actual source files from metaffi-core/plugin-sdk/
    # For now using placeholder to track SDK is used
    plugin_sdk = Component(
        name="plugin-sdk",
        type=ComponentType.STATIC_LIBRARY,  # SDK is source files, not a built artifact
        programming_language="cxx",
        relative_path=Path("metaffi-core/plugin-sdk"),
        source_files=[],  # SDK files are included in other components
        external_packages=[],
        evidence=[Evidence(line=["metaffi-core/plugin-sdk/CMakeLists.txt:3"])],
        locations=[],
    )

    # Component: xllr - C++ dynamic library
    xllr = Component(
        name="xllr.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/metaffi-core/XLLR/Debug/xllr.dll"),
        source_files=CMAKE_VAR_FILES["xllr_src"]  # ${xllr_src} expansion (5 files)
                     + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, boost_thread],
        evidence=[Evidence(line=["metaffi-core/XLLR/CMakeLists.txt:7"])],
        locations=[],
    )

    # Component: metaffi - C++ executable (CLI)
    metaffi_cli = Component(
        name="metaffi.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/metaffi-core/CLI/Debug/metaffi.exe"),
        source_files=CMAKE_VAR_FILES["cli_src"]  # ${cli_src} expansion (8 files)
                     + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, boost_program_options],
        evidence=[Evidence(line=["metaffi-core/CLI/CMakeLists.txt:6"])],
        locations=[],
    )

    # Component: cdts_test - C++ test executable
    cdts_test = Component(
        name="cdts_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/metaffi-core/plugin-sdk/Debug/cdts_test.exe"),
        source_files=[
            Path("metaffi-core/plugin-sdk/runtime/cdts_test.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package],
        evidence=[Evidence(line=["metaffi-core/plugin-sdk/run_sdk_tests.cmake:6"])],
        locations=[],
    )

    # Component: xllr_capi_test - C++ test executable
    xllr_capi_test = Component(
        name="xllr_capi_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/metaffi-core/plugin-sdk/Debug/xllr_capi_test.exe"),
        source_files=[
            Path("metaffi-core/plugin-sdk/runtime/xllr_capi_test.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package],
        evidence=[Evidence(line=["metaffi-core/plugin-sdk/run_sdk_tests.cmake:15"])],
        locations=[],
    )

    # Aggregator: metaffi-core
    metaffi_core_aggregator = Component(
        name="metaffi-core",
        type=ComponentType.INTERPRETED,
        programming_language="cxx",
        relative_path=Path("metaffi-core"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["metaffi-core/CMakeLists.txt:15"])],
        locations=[],
        depends_on=[xllr, metaffi_cli, cdts_test, xllr_capi_test]
    )

    # ==================== PYTHON311 AGGREGATOR ====================
    # Components defined in lang-plugin-python311/

    # Component: xllr.python311 - C++ dynamic library
    xllr_python311 = Component(
        name="xllr.python311.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-python311/runtime/Debug/python311/xllr.python311.dll"),
        source_files=CMAKE_VAR_FILES["xllr.python311_src"]  # ${xllr.python311_src} expansion (17 files)
                     + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem],
        evidence=[Evidence(line=["lang-plugin-python311/runtime/CMakeLists.txt:10"])],
        locations=[],
    )

    # Component: python_runtime_test - C++ test executable
    python_runtime_test = Component(
        name="python_runtime_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-python311/runtime/Debug/python_runtime_test.exe"),
        source_files=[
            Path("lang-plugin-python311/runtime/python_runtime_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.python311_src"]  # ${xllr.python311_src} expansion (17 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package],
        evidence=[Evidence(line=["lang-plugin-python311/runtime/CMakeLists.txt:19"])],
        locations=[],
        depends_on=[xllr_python311]
    )

    # Component: metaffi.idl.python311 - C++ dynamic library
    metaffi_idl_python311 = Component(
        name="metaffi.idl.python311.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-python311/idl/Debug/python311/metaffi.idl.python311.dll"),
        source_files=CMAKE_VAR_FILES["metaffi_idl_python311_src"]  # ${metaffi_idl_python311_src} expansion (1 file)
                     + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"]  # ${sdk_src} expansion (10 files)
                     + [Path("lang-plugin-python311/runtime/python3_api_wrapper.cpp")],  # ../runtime/python3_api_wrapper.cpp
        external_packages=[boost_filesystem],
        evidence=[Evidence(line=["lang-plugin-python311/idl/CMakeLists.txt:13"])],
        locations=[],
    )

    # Component: python311_idl_plugin_test - C++ test executable
    python311_idl_plugin_test = Component(
        name="python311_idl_plugin_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-python311/idl/Debug/python311_idl_plugin_test.exe"),
        source_files=[
            Path("lang-plugin-python311/idl/idl_plugin_test.cpp"),
            Path("lang-plugin-python311/idl/python_idl_plugin.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package],
        evidence=[Evidence(line=["lang-plugin-python311/idl/CMakeLists.txt:22"])],
        locations=[],
        depends_on=[metaffi_idl_python311]
    )

    # Component: metaffi.compiler.python311 - Go dynamic library
    metaffi_compiler_python311 = Component(
        name="metaffi.compiler.python311.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("cmake-build-debug/lang-plugin-python311/compiler/Debug/python311/metaffi.compiler.python311.dll"),
        source_files=[
            # Source files from lang-plugin-python311/compiler/
            # TODO: Enumerate all .go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/compiler/CMakeLists.txt:6"])],
        locations=[],
    )

    # Custom target: python3_api_unitest
    python3_api_unitest = Component(
        name="python3_api_unitest",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("lang-plugin-python311/api"),
        source_files=[Path("lang-plugin-python311/api/unittest/test_python311_api.py")],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/api/CMakeLists.txt:5"])],
        locations=[],
    )

    # Custom target: python3_api_cross_pl_tests
    python3_api_cross_pl_tests = Component(
        name="python3_api_cross_pl_tests",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("lang-plugin-python311/api"),
        source_files=[Path("lang-plugin-python311/api/tests/run_api_tests.py")],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/api/CMakeLists.txt:12"])],
        locations=[],
    )

    # Custom target: python311.publish
    python311_publish = Component(
        name="python311.publish",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("lang-plugin-python311/api"),
        source_files=[Path("lang-plugin-python311/api/publish_python_package.py")],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/api/CMakeLists.txt:19"])],
        locations=[],
        depends_on=[xllr_python311]
    )

    # Custom target: metaffi_compiler_python311_test (Go test)
    metaffi_compiler_python311_test = Component(
        name="metaffi_compiler_python311_test",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-python311/compiler"),
        source_files=[
            # Go test files in lang-plugin-python311/compiler/
            # TODO: Enumerate *_test.go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/compiler/CMakeLists.txt:19"])],
        locations=[],
    )

    # Aggregator: python311
    python311_aggregator = Component(
        name="python311",
        type=ComponentType.INTERPRETED,
        programming_language="cxx",
        relative_path=Path("lang-plugin-python311"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-python311/CMakeLists.txt:18"])],
        locations=[],
        depends_on=[xllr_python311, python_runtime_test, metaffi_idl_python311,
                    python311_idl_plugin_test, metaffi_compiler_python311]
    )

    # ==================== OPENJDK AGGREGATOR ====================
    # Components defined in lang-plugin-openjdk/

    # Component: xllr.openjdk - C++ dynamic library
    xllr_openjdk = Component(
        name="xllr.openjdk.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/runtime/Debug/openjdk/xllr.openjdk.dll"),
        source_files=CMAKE_VAR_FILES["xllr.openjdk_src"]  # ${xllr.openjdk_src} expansion (21 files)
                     + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, jni_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/runtime/CMakeLists.txt:10"])],
        locations=[],
    )

    # Component: cdts_java_test - C++ test executable
    cdts_java_test = Component(
        name="cdts_java_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/runtime/Debug/cdts_java_test.exe"),
        source_files=[
            Path("lang-plugin-openjdk/runtime/cdts_java_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.openjdk_src"]  # ${xllr.openjdk_src} expansion (21 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package, jni_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/runtime/CMakeLists.txt:19"])],
        locations=[],
        depends_on=[xllr_openjdk]
    )

    # Component: openjdk_api_test - C++ test executable
    openjdk_api_test = Component(
        name="openjdk_api_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/runtime/Debug/openjdk_api_test.exe"),
        source_files=[
            Path("lang-plugin-openjdk/runtime/cdts_java_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.openjdk_src"]  # ${xllr.openjdk_src} expansion (21 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package, jni_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/runtime/CMakeLists.txt:28"])],
        locations=[],
        depends_on=[xllr_openjdk]
    )

    # Component: xllr.openjdk.jni.bridge - C++ dynamic library
    xllr_openjdk_jni_bridge = Component(
        name="xllr.openjdk.jni.bridge.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/xllr-openjdk-bridge/Debug/openjdk/xllr.openjdk.jni.bridge.dll"),
        source_files=CMAKE_VAR_FILES["xllr.openjdk.jni.bridge_src"]  # ${xllr.openjdk.jni.bridge_src} expansion (1 file)
                     + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, jni_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt:9"])],
        locations=[],
        depends_on=[xllr_openjdk]
    )

    # Component: xllr.openjdk.bridge - JAR file
    xllr_openjdk_bridge = Component(
        name="xllr.openjdk.bridge.jar",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/xllr-openjdk-bridge/Debug/openjdk/xllr.openjdk.bridge.jar"),
        source_files=[
            # Java files from lang-plugin-openjdk/xllr-openjdk-bridge/*.java
            # TODO: Enumerate all .java files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt:19"])],
        locations=[],
        depends_on=[xllr_openjdk_jni_bridge]
    )

    # Component: metaffi.api - JAR file
    metaffi_api = Component(
        name="metaffi.api.jar",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/api/Debug/openjdk/metaffi.api.jar"),
        source_files=[
            # Java files from lang-plugin-openjdk/api/*.java
            # TODO: Enumerate all .java files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/api/CMakeLists.txt:9"])],
        locations=[],
        depends_on=[xllr_openjdk_bridge]
    )

    # Component: openjdk_idl_extractor - JAR file with external JAR dependencies
    openjdk_idl_extractor = Component(
        name="openjdk_idl_extractor.jar",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/idl/Debug/openjdk/openjdk_idl_extractor.jar"),
        source_files=[
            # Java files from lang-plugin-openjdk/idl/src/java_extractor/*.java
            # TODO: Enumerate all .java files
        ],
        external_packages=[gson_package, asm_package, asm_tree_package, javaparser_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:15"])],
        locations=[],
    )

    # Component: metaffi.idl.openjdk - C++ dynamic library
    metaffi_idl_openjdk = Component(
        name="metaffi.idl.openjdk.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/idl/Debug/openjdk/metaffi.idl.openjdk.dll"),
        source_files=[
            Path("lang-plugin-openjdk/idl/openjdk_idl_plugin.cpp"),
        ],
        external_packages=[jni_package],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:23"])],
        locations=[],
    )

    # Custom command: test_data_classes
    test_data_classes = Component(
        name="test_data_classes",
        type=ComponentType.INTERPRETED,
        programming_language="java",
        relative_path=Path("lang-plugin-openjdk/idl/test/testdata"),
        source_files=[
            # Test data classes - files may be generated during build
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:31"])],
        locations=[],
    )

    # Custom command: java_tests_classes
    java_tests_classes = Component(
        name="java_tests_classes",
        type=ComponentType.INTERPRETED,
        programming_language="java",
        relative_path=Path("lang-plugin-openjdk/idl/test/java_extractor"),
        source_files=[
            # Test classes - files may be generated during build
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:40"])],
        locations=[],
        depends_on=[test_data_classes]
    )

    # Custom command: java_tests_run
    java_tests_run = Component(
        name="java_tests_run",
        type=ComponentType.INTERPRETED,
        programming_language="java",
        relative_path=Path("lang-plugin-openjdk/idl"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:49"])],
        locations=[],
        depends_on=[java_tests_classes]
    )

    # Component: metaffi.compiler.openjdk - Go dynamic library
    metaffi_compiler_openjdk = Component(
        name="metaffi.compiler.openjdk.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("cmake-build-debug/lang-plugin-openjdk/compiler/Debug/openjdk/metaffi.compiler.openjdk.dll"),
        source_files=[
            # Go files from lang-plugin-openjdk/compiler/
            # TODO: Enumerate all .go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/compiler/CMakeLists.txt:4"])],
        locations=[],
    )

    # Custom target: openjdk_api_cross_pl_tests
    openjdk_api_cross_pl_tests = Component(
        name="openjdk_api_cross_pl_tests",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("lang-plugin-openjdk/api"),
        source_files=[
            # Test scripts may not be in test repo
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/api/CMakeLists.txt:23"])],
        locations=[],
    )

    # Custom target: openjdk_compiler_go_tests (Go test)
    openjdk_compiler_go_tests = Component(
        name="openjdk_compiler_go_tests",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-openjdk/compiler"),
        source_files=[
            # Go test files in lang-plugin-openjdk/compiler/
            # TODO: Enumerate *_test.go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/compiler/CMakeLists.txt:12"])],
        locations=[],
    )

    # Aggregator: openjdk
    openjdk_aggregator = Component(
        name="openjdk",
        type=ComponentType.INTERPRETED,
        programming_language="cxx",
        relative_path=Path("lang-plugin-openjdk"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-openjdk/CMakeLists.txt:20"])],
        locations=[],
        depends_on=[xllr_openjdk, xllr_openjdk_jni_bridge, xllr_openjdk_bridge, metaffi_api,
                    openjdk_api_test, cdts_java_test, metaffi_idl_openjdk, metaffi_compiler_openjdk]
    )

    # ==================== GO AGGREGATOR ====================
    # Components defined in lang-plugin-go/

    # Component: xllr.go - C++ dynamic library
    xllr_go = Component(
        name="xllr.go.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-go/runtime/Debug/go/xllr.go.dll"),
        source_files=CMAKE_VAR_FILES["xllr.go_src"]  # ${xllr.go_src} expansion (3 files)
                     + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-go"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem],
        evidence=[Evidence(line=["lang-plugin-go/runtime/CMakeLists.txt:11"])],
        locations=[],
    )

    # Custom target: build_go_guest
    build_go_guest = Component(
        name="build_go_guest",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-go/runtime/test"),
        source_files=[
            Path("lang-plugin-go/runtime/test/TestRuntime.go"),
            Path("lang-plugin-go/runtime/test/build_guest.py"),
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/runtime/CMakeLists.txt:20"])],
        locations=[],
    )

    # Component: go_api_test - C++ test executable
    go_api_test = Component(
        name="go_api_test.exe",
        type=ComponentType.EXECUTABLE,
        programming_language="cxx",
        relative_path=Path("cmake-build-debug/lang-plugin-go/runtime/Debug/go_api_test.exe"),
        source_files=[
            Path("lang-plugin-go/runtime/go_api_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.go_src"]  # ${xllr.go_src} expansion (3 files) - NOTE: CMake has bug using xllr.openjdk_src
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-go"],  # ${sdk_src} expansion (10 files)
        external_packages=[boost_filesystem, doctest_package],
        evidence=[Evidence(line=["lang-plugin-go/runtime/CMakeLists.txt:29"])],
        locations=[],
        depends_on=[xllr_go, build_go_guest]
    )

    # Component: metaffi.compiler.go - Go dynamic library
    metaffi_compiler_go = Component(
        name="metaffi.compiler.go.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("cmake-build-debug/lang-plugin-go/compiler/Debug/go/metaffi.compiler.go.dll"),
        source_files=[
            # Go files from lang-plugin-go/compiler/
            # TODO: Enumerate all .go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/compiler/CMakeLists.txt:7"])],
        locations=[],
    )

    # Component: metaffi.idl.go - Go dynamic library
    metaffi_idl_go = Component(
        name="metaffi.idl.go.dll",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("cmake-build-debug/lang-plugin-go/idl/Debug/go/metaffi.idl.go.dll"),
        source_files=[
            # Go files from lang-plugin-go/idl/
            # TODO: Enumerate all .go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/idl/CMakeLists.txt:3"])],
        locations=[],
    )

    # Custom target: metaffi_compiler_go_test (Go test)
    metaffi_compiler_go_test = Component(
        name="metaffi_compiler_go_test",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-go/compiler"),
        source_files=[
            # Go test files in lang-plugin-go/compiler/
            # TODO: Enumerate *_test.go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/compiler/CMakeLists.txt:21"])],
        locations=[],
    )

    # Custom target: metaffi_idl_go_test (Go test)
    metaffi_idl_go_test = Component(
        name="metaffi_idl_go_test",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-go/idl"),
        source_files=[
            # Go test files in lang-plugin-go/idl/
            # TODO: Enumerate *_test.go files
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/idl/CMakeLists.txt:16"])],
        locations=[],
    )

    # Custom target: go_runtime_test (Python script runner for Go tests)
    go_runtime_test = Component(
        name="go_runtime_test",
        type=ComponentType.INTERPRETED,
        programming_language="go",
        relative_path=Path("lang-plugin-go/go-runtime/test"),
        source_files=[
            Path("lang-plugin-go/go-runtime/test/run_test.py"),
        ],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/go-runtime/CMakeLists.txt:7"])],
        locations=[],
    )

    # Aggregator: go
    go_aggregator = Component(
        name="go",
        type=ComponentType.INTERPRETED,
        programming_language="cxx",
        relative_path=Path("lang-plugin-go"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["lang-plugin-go/CMakeLists.txt:20"])],
        locations=[],
        depends_on=[xllr_go, metaffi_compiler_go, metaffi_idl_go, go_api_test]
    )

    # ==================== TOP-LEVEL AGGREGATOR ====================

    # Aggregator: MetaFFI (top-level)
    metaffi_aggregator = Component(
        name="MetaFFI",
        type=ComponentType.INTERPRETED,
        programming_language="cxx",
        relative_path=Path("."),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["CMakeLists.txt:77"])],
        locations=[],
        depends_on=[metaffi_core_aggregator, python311_aggregator, openjdk_aggregator, go_aggregator]
    )

    # ==================== Add Components to RIG ====================

    # Plugin SDK
    rig.add_component(plugin_sdk)

    # metaffi-core components
    rig.add_component(xllr)
    rig.add_component(metaffi_cli)
    rig.add_component(cdts_test)
    rig.add_component(xllr_capi_test)
    rig.add_component(metaffi_core_aggregator)

    # python311 components
    rig.add_component(xllr_python311)
    rig.add_component(python_runtime_test)
    rig.add_component(metaffi_idl_python311)
    rig.add_component(python311_idl_plugin_test)
    rig.add_component(metaffi_compiler_python311)
    rig.add_component(python3_api_unitest)
    rig.add_component(python3_api_cross_pl_tests)
    rig.add_component(python311_publish)
    rig.add_component(metaffi_compiler_python311_test)
    rig.add_component(python311_aggregator)

    # openjdk components
    rig.add_component(xllr_openjdk)
    rig.add_component(cdts_java_test)
    rig.add_component(openjdk_api_test)
    rig.add_component(xllr_openjdk_jni_bridge)
    rig.add_component(xllr_openjdk_bridge)
    rig.add_component(metaffi_api)
    rig.add_component(openjdk_idl_extractor)
    rig.add_component(metaffi_idl_openjdk)
    rig.add_component(test_data_classes)
    rig.add_component(java_tests_classes)
    rig.add_component(java_tests_run)
    rig.add_component(metaffi_compiler_openjdk)
    rig.add_component(openjdk_api_cross_pl_tests)
    rig.add_component(openjdk_compiler_go_tests)
    rig.add_component(openjdk_aggregator)

    # go components
    rig.add_component(xllr_go)
    rig.add_component(build_go_guest)
    rig.add_component(go_api_test)
    rig.add_component(metaffi_compiler_go)
    rig.add_component(metaffi_idl_go)
    rig.add_component(metaffi_compiler_go_test)
    rig.add_component(metaffi_idl_go_test)
    rig.add_component(go_runtime_test)
    rig.add_component(go_aggregator)

    # Top-level aggregator
    rig.add_component(metaffi_aggregator)

    # ==================== Test Definitions ====================

    # ===== metaffi-core tests =====

    # CTest: cdts_test
    cdts_test_def = TestDefinition(
        name="cdts_test",
        test_executable_component=cdts_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("metaffi-core/plugin-sdk/runtime/cdts_test.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["metaffi-core/plugin-sdk/run_sdk_tests.cmake:11"])],
    )
    rig.add_test(cdts_test_def)

    # CTest: xllr_capi_test
    xllr_capi_test_def = TestDefinition(
        name="xllr_capi_test",
        test_executable_component=xllr_capi_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("metaffi-core/plugin-sdk/runtime/xllr_capi_test.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["metaffi-core"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["metaffi-core/plugin-sdk/run_sdk_tests.cmake:20"])],
    )
    rig.add_test(xllr_capi_test_def)

    # ===== python311 tests =====

    # CTest: python_runtime_test
    python_runtime_test_def = TestDefinition(
        name="python_runtime_test",
        test_executable_component=python_runtime_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("lang-plugin-python311/runtime/python_runtime_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.python311_src"]  # ${xllr.python311_src} expansion (17 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["lang-plugin-python311/runtime/CMakeLists.txt:35"])],
    )
    rig.add_test(python_runtime_test_def)

    # CTest: idl_plugin_test (python311_idl_plugin_test)
    idl_plugin_test_def = TestDefinition(
        name="idl_plugin_test",
        test_executable_component=python311_idl_plugin_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("lang-plugin-python311/idl/idl_plugin_test.cpp"),
            Path("lang-plugin-python311/idl/python_idl_plugin.cpp"),
        ] + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-python311"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["lang-plugin-python311/idl/CMakeLists.txt:32"])],
    )
    rig.add_test(idl_plugin_test_def)

    # CTest: python3_api_unitest
    python3_api_unitest_def = TestDefinition(
        name="python3_api_unitest",
        test_executable_component=python3_api_unitest,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Python",
        source_files=[Path("lang-plugin-python311/api/unittest/test_python311_api.py")],
        evidence=[Evidence(line=["lang-plugin-python311/api/CMakeLists.txt:5"])],
    )
    rig.add_test(python3_api_unitest_def)

    # CTest: python3_api_cross_pl_tests
    python3_api_cross_pl_tests_def = TestDefinition(
        name="python3_api_cross_pl_tests",
        test_executable_component=python3_api_cross_pl_tests,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Python",
        source_files=[Path("lang-plugin-python311/api/tests/run_api_tests.py")],
        evidence=[Evidence(line=["lang-plugin-python311/api/CMakeLists.txt:12"])],
    )
    rig.add_test(python3_api_cross_pl_tests_def)

    # CTest: metaffi_compiler_python311_test
    metaffi_compiler_python311_test_def = TestDefinition(
        name="metaffi_compiler_python311_test",
        test_executable_component=metaffi_compiler_python311_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[],  # Go test files
        evidence=[Evidence(line=["lang-plugin-python311/compiler/CMakeLists.txt:19"])],
    )
    rig.add_test(metaffi_compiler_python311_test_def)

    # ===== openjdk tests =====

    # CTest: cdts_java_test
    cdts_java_test_def = TestDefinition(
        name="cdts_java_test",
        test_executable_component=cdts_java_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("lang-plugin-openjdk/runtime/cdts_java_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.openjdk_src"]  # ${xllr.openjdk_src} expansion (21 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["lang-plugin-openjdk/runtime/CMakeLists.txt:25"])],
    )
    rig.add_test(cdts_java_test_def)

    # CTest: openjdk_api_test
    openjdk_api_test_def = TestDefinition(
        name="openjdk_api_test",
        test_executable_component=openjdk_api_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("lang-plugin-openjdk/runtime/cdts_java_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.openjdk_src"]  # ${xllr.openjdk_src} expansion (21 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-openjdk"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["lang-plugin-openjdk/runtime/CMakeLists.txt:34"])],
    )
    rig.add_test(openjdk_api_test_def)

    # CTest: openjdk_idl_plugin_java_tests
    openjdk_idl_plugin_java_tests_def = TestDefinition(
        name="openjdk_idl_plugin_java_tests",
        test_executable_component=java_tests_run,
        test_executable_component_id=None,
        test_components=[],
        test_framework="JUnit",
        source_files=[
            # Test files may be generated during build
        ],
        evidence=[Evidence(line=["lang-plugin-openjdk/idl/CMakeLists.txt:78"])],
    )
    rig.add_test(openjdk_idl_plugin_java_tests_def)

    # CTest: openjdk_api_cross_pl_tests
    openjdk_api_cross_pl_tests_def = TestDefinition(
        name="openjdk_api_cross_pl_tests",
        test_executable_component=openjdk_api_cross_pl_tests,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Python",
        source_files=[
            # Test scripts may not be in test repo
        ],
        evidence=[Evidence(line=["lang-plugin-openjdk/api/CMakeLists.txt:23"])],
    )
    rig.add_test(openjdk_api_cross_pl_tests_def)

    # CTest: openjdk_compiler_go_tests
    openjdk_compiler_go_tests_def = TestDefinition(
        name="openjdk_compiler_go_tests",
        test_executable_component=openjdk_compiler_go_tests,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[],  # Go test files
        evidence=[Evidence(line=["lang-plugin-openjdk/compiler/CMakeLists.txt:12"])],
    )
    rig.add_test(openjdk_compiler_go_tests_def)

    # ===== go tests =====

    # CTest: go_api_test
    go_api_test_def = TestDefinition(
        name="go_api_test",
        test_executable_component=go_api_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="CTest",
        source_files=[
            Path("lang-plugin-go/runtime/go_api_test.cpp"),
        ] + CMAKE_VAR_FILES["xllr.go_src"]  # ${xllr.go_src} expansion (3 files)
          + CMAKE_VAR_FILES["sdk_src"]["lang-plugin-go"],  # ${sdk_src} expansion (10 files)
        evidence=[Evidence(line=["lang-plugin-go/runtime/CMakeLists.txt:40"])],
    )
    rig.add_test(go_api_test_def)

    # CTest: metaffi_compiler_go_test
    metaffi_compiler_go_test_def = TestDefinition(
        name="metaffi_compiler_go_test",
        test_executable_component=metaffi_compiler_go_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[],  # Go test files
        evidence=[Evidence(line=["lang-plugin-go/compiler/CMakeLists.txt:21"])],
    )
    rig.add_test(metaffi_compiler_go_test_def)

    # CTest: metaffi_idl_go_test
    metaffi_idl_go_test_def = TestDefinition(
        name="metaffi_idl_go_test",
        test_executable_component=metaffi_idl_go_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[],  # Go test files in idl/IDLCompiler
        evidence=[Evidence(line=["lang-plugin-go/idl/CMakeLists.txt:16"])],
    )
    rig.add_test(metaffi_idl_go_test_def)

    # CTest: go_runtime_test
    go_runtime_test_def = TestDefinition(
        name="go_runtime_test",
        test_executable_component=go_runtime_test,
        test_executable_component_id=None,
        test_components=[],
        test_framework="Go",
        source_files=[Path("lang-plugin-go/go-runtime/test/run_test.py")],
        evidence=[Evidence(line=["lang-plugin-go/go-runtime/CMakeLists.txt:7"])],
    )
    rig.add_test(go_runtime_test_def)

    # ==================== Validation and Save ====================

    # Validate before saving/writing outputs (fail-fast on errors)
    validation_errors = rig.validate()
    if len(validation_errors) > 0:
        for error in validation_errors:
            print(f"""Validation Error ({error.category}):
    File: {error.file_path}
    Message: {error.message}
    Node Name: {error.node_name}
""")
        raise RIGValidationError(validation_errors)

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "metaffi_ground_truth.sqlite3"
    rig.save(sqlite_path)

    # Write JSON prompt (unoptimized for readability in ground-truth)
    json_path = Path(__file__).parent / "metaffi_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)

    # Load from SQLite into a new RIG instance and compare
    rig_loaded = RIG.load(sqlite_path)

    # Use the compare() method
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match ground truth:\n{diff_text}")


if __name__ == "__main__":
    main()
