"""
CustomTargetRigComponent - Extracts RIG component metadata from custom UTILITY targets.

This module parallels CMakeTargetRigComponent but handles UTILITY targets that
produce custom artifacts (JARs, Go shared libraries, etc.).
"""

from pathlib import Path
from typing import List

from cmake_file_api.kinds.cache.v2 import CacheV2

from core.schemas import ComponentType, ExternalPackage, Evidence
from deterministic.cmake.backtrace_walker import BacktraceWalker
from deterministic.cmake.cmake_target import CMakeTargetWrapper
from deterministic.cmake.custom_target_detector import CustomTargetDetector


class CustomTargetRigComponent:
    """
    Extracts RIG component information from custom UTILITY targets.

    Custom targets lack standard cmake-file-api metadata (no artifacts array,
    no compileGroups), so we use CustomTargetDetector to infer properties
    from the .rule files.
    """

    def __init__(self, target: CMakeTargetWrapper, cmake_cache: CacheV2):
        """
        Initialize component extractor for a custom target.

        Args:
            target: CMakeTargetWrapper for the UTILITY target
            cmake_cache: CMake cache for extracting paths
        """
        assert isinstance(target, CMakeTargetWrapper)

        self._target = target
        self._cmake_cache = cmake_cache

        # Initialize detector
        self._detector = CustomTargetDetector(
            self._target.cmake_target.target,
            self._target.repo_root
        )

        # Get artifact info (should always succeed since we only call this for detected artifacts)
        self._artifact_info = self._detector.get_artifact_info()
        if self._artifact_info is None:
            raise ValueError(f"CustomTargetRigComponent created for non-artifact target: {self._target.cmake_target.target.name}")

    def get_component_type(self) -> ComponentType:
        """
        Get the component type based on artifact classification.

        Returns:
            ComponentType (PACKAGE_LIBRARY for JARs, SHARED_LIBRARY for DLLs/SOs)
        """
        return self._artifact_info.type

    def get_programming_language(self) -> str:
        """
        Get the programming language based on artifact classification.

        Returns:
            Language string ("java", "go", "unknown", etc.)
        """
        return self._artifact_info.language

    def get_source_files(self) -> List[Path]:
        """
        Get source files used to build the artifact.

        Parses CMakeLists.txt to extract source file arguments from the function call
        that created this target (add_jar, add_custom_jar, add_go_shared_library, etc.).

        Returns:
            List of source file paths relative to repo root
        """
        from deterministic.cmake.cmake_source_file_parser import CMakeSourceFileParser

        parser = CMakeSourceFileParser()

        # Use the repo's main CMakeLists.txt (backtrace might point to external modules)
        cmake_lists_path = self._target.repo_root / "CMakeLists.txt"

        target_name = self._target.cmake_target.target.name

        source_files = parser.extract_sources_for_target(
            target_name,
            cmake_lists_path,
            self._target.repo_root
        )

        return source_files


    def get_relative_path(self) -> Path:
        """
        Get the path where the artifact is built (relative to repo root).

        Custom artifacts are placed at the build directory root, NOT in configuration
        subdirectories like Debug/Release:
        - JARs: spade_build/java_hello_lib-1.0.0.jar
        - DLLs: spade_build/libhello.dll

        Returns:
            Path relative to repo root (e.g., "spade_build/libhello.dll")
        """
        # Get binary directory from cache
        binary_dir_abs = None
        for cache_entry in self._cmake_cache.entries:
            if cache_entry.name == f"{self._target.cmake_target.project.name}_BINARY_DIR":
                binary_dir_abs = Path(cache_entry.value)
                break

        if binary_dir_abs is None:
            raise ValueError(f"Could not find BINARY_DIR for project {self._target.cmake_target.project.name}")

        # Custom artifacts go to build root (not Debug/Release subdirectory)
        full_abs_path = binary_dir_abs / self._artifact_info.name
        return full_abs_path.relative_to(self._target.repo_root)

    def get_locations(self) -> List[Path]:
        """
        Get additional locations where the artifact might exist.

        Currently returns empty list as we don't track install destinations or
        post-build copy operations for custom targets.

        Returns:
            Empty list
        """
        return []

    def get_external_packages(self) -> List[ExternalPackage]:
        """
        Get external packages used by this custom target.

        Detects packages by matching link libraries (if any) to find_package() results.
        Custom UTILITY targets typically don't link libraries, so this usually returns empty.

        Returns:
            List of ExternalPackage objects
        """
        from deterministic.cmake.external_package_detector import ExternalPackageDetector

        # Build paths
        cmake_cache_path = self._target.repo_root / "spade_build" / "CMakeCache.txt"

        # Use the repo's main CMakeLists.txt (backtrace might point to external modules)
        cmake_lists_path = self._target.repo_root / "CMakeLists.txt"

        # Detect packages (fail-fast - let exceptions propagate)
        detector = ExternalPackageDetector()
        return detector.detect_packages_for_target(
            self._target.cmake_target.target,
            cmake_cache_path,
            cmake_lists_path
        )

    def get_evidence(self) -> List[Evidence]:
        """
        Get evidence (source location in CMakeLists.txt) for this target.

        Uses backtrace walker to find the user's actual function call rather than
        internal implementation details.

        Returns:
            List containing single Evidence with CMakeLists.txt location
        """
        evidence = BacktraceWalker.get_user_call_site(
            self._target.cmake_target.target.backtrace,
            self._target.repo_root
        )
        return [evidence]
