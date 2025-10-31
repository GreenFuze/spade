"""
CustomTargetDetector - Detects UTILITY targets that produce custom artifacts.

This module provides generic detection for custom artifacts (JARs, shared libraries, etc.)
built via add_custom_command/add_custom_target, which appear as UTILITY targets in cmake-file-api.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cmake_file_api.kinds.codemodel.target.v2 import CodemodelTargetV2
from core.schemas import ComponentType


@dataclass
class ArtifactInfo:
    """Information about a detected custom artifact."""
    name: str  # Full artifact filename (e.g., "java_hello_lib-1.0.0.jar", "libhello.dll")
    type: ComponentType  # Component type (PACKAGE_LIBRARY, SHARED_LIBRARY, etc.)
    language: str  # Programming language ("java", "go", "unknown")
    extension: str  # File extension (".jar", ".dll", ".so", etc.)


class CustomTargetDetector:
    """
    Detects if a UTILITY target produces a custom artifact.

    Custom artifacts are identified by the presence of {artifact_name}.rule files
    in the target's sources. The rule filename reveals the artifact name and type.
    """

    def __init__(self, cmake_target: CodemodelTargetV2, repo_root: Path):
        """
        Initialize detector for a CMake target.

        Args:
            cmake_target: The CMake target to inspect (from cmake-file-api)
            repo_root: Repository root path for path resolution
        """
        self.cmake_target = cmake_target
        self.repo_root = repo_root

    def is_custom_artifact(self) -> bool:
        """
        Check if this UTILITY target produces a custom artifact.

        Returns:
            True if an artifact rule file is found, False otherwise
        """
        return self._find_artifact_rule() is not None

    def get_artifact_info(self) -> Optional[ArtifactInfo]:
        """
        Extract artifact information from the target.

        Returns:
            ArtifactInfo object if artifact detected, None otherwise
        """
        rule_file = self._find_artifact_rule()
        if not rule_file:
            return None

        # Extract artifact name by removing .rule suffix
        artifact_name = rule_file.name.replace('.rule', '')

        # Classify based on extension
        return self._classify_artifact(artifact_name)

    def _find_artifact_rule(self) -> Optional[Path]:
        """
        Find the artifact rule file in target sources.

        Artifact rule files follow the pattern: {artifact_name}.{ext}.rule
        Examples:
        - java_hello_lib-1.0.0.jar.rule
        - libhello.dll.rule
        - libfoo.so.rule

        Returns:
            Path to the rule file if found, None otherwise
        """
        for source in self.cmake_target.sources:
            source_path = Path(source.path) if hasattr(source, 'path') else Path(source)
            name = source_path.name

            # Check for known artifact patterns
            if name.endswith('.jar.rule'):
                return source_path
            elif name.endswith(('.dll.rule', '.so.rule', '.dylib.rule')):
                return source_path
            # Future: Add more patterns (.whl.rule for Python, .gem.rule for Ruby, etc.)

        return None

    def _classify_artifact(self, artifact_name: str) -> ArtifactInfo:
        """
        Classify artifact by extension to determine type and language.

        Args:
            artifact_name: Full artifact filename (e.g., "libhello.dll")

        Returns:
            ArtifactInfo with classified type and language
        """
        # Determine extension
        if artifact_name.endswith('.jar'):
            return ArtifactInfo(
                name=artifact_name,
                type=ComponentType.PACKAGE_LIBRARY,
                language="java",
                extension=".jar"
            )
        elif artifact_name.endswith('.dll'):
            return ArtifactInfo(
                name=artifact_name,
                type=ComponentType.SHARED_LIBRARY,
                language=self._detect_language_from_sources(),
                extension=".dll"
            )
        elif artifact_name.endswith('.so'):
            return ArtifactInfo(
                name=artifact_name,
                type=ComponentType.SHARED_LIBRARY,
                language=self._detect_language_from_sources(),
                extension=".so"
            )
        elif artifact_name.endswith('.dylib'):
            return ArtifactInfo(
                name=artifact_name,
                type=ComponentType.SHARED_LIBRARY,
                language=self._detect_language_from_sources(),
                extension=".dylib"
            )
        else:
            # Unknown artifact type
            return ArtifactInfo(
                name=artifact_name,
                type=ComponentType.SHARED_LIBRARY,  # Default guess
                language="unknown",
                extension=Path(artifact_name).suffix
            )

    def _detect_language_from_sources(self) -> str:
        """
        Attempt to detect programming language from source file patterns.

        For shared libraries, cmake-file-api doesn't track the actual source files
        used to build the library. We can try heuristics:
        - Look for .go files in sources → "go"
        - Look for .c/.cpp files → "c"/"cxx"
        - Check target name for hints (e.g., "go_lib" → "go")

        Returns:
            Language string ("go", "c", "cxx", "unknown")
        """
        target_name = self.cmake_target.name.lower()

        # Check target name for language hints
        if 'go' in target_name or '_go_' in target_name:
            return "go"
        elif 'rust' in target_name or '_rust_' in target_name:
            return "rust"
        elif 'java' in target_name or '_java_' in target_name:
            return "java"

        # Check sources for file extensions (though UTILITY targets usually have no compile sources)
        for source in self.cmake_target.sources:
            source_path = Path(source.path) if hasattr(source, 'path') else Path(source)

            if source_path.suffix == '.go':
                return "go"
            elif source_path.suffix in ['.c', '.h']:
                return "c"
            elif source_path.suffix in ['.cpp', '.cxx', '.hpp', '.hxx']:
                return "cxx"
            elif source_path.suffix == '.rs':
                return "rust"

        # Default to unknown
        return "unknown"
