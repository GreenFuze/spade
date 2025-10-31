"""
ExternalPackageDetector - Detects external packages used by CMake targets.

Uses hybrid approach:
1. Parse find_package() calls from CMakeLists.txt
2. Map packages to library paths via CMakeCache.txt
3. Extract target link libraries from cmake-file-api
4. Match libraries to packages

Fail-fast: Raises exceptions on errors rather than returning partial data.
"""

from pathlib import Path
from typing import List, Dict, Set

try:
    import parse_cmake.parsing as cmp
except ImportError:
    cmp = None

from core.schemas import ExternalPackage, PackageManager


class ExternalPackageDetector:
    """
    Detects which external packages a CMake target uses.

    Matches target link libraries to find_package() results via CMakeCache.txt.
    """

    # Known system libraries to ignore
    SYSTEM_LIBRARIES = {
        'kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib',
        'shell32.lib', 'ole32.lib', 'oleaut32.lib', 'uuid.lib',
        'comdlg32.lib', 'advapi32.lib', 'wsock32.lib', 'ws2_32.lib'
    }

    def __init__(self):
        """Initialize detector."""
        if cmp is None:
            raise ImportError("parse_cmake package is required for external package detection")

    def detect_packages_for_target(
        self,
        target,
        cmake_cache_path: Path,
        cmake_lists_path: Path
    ) -> List[ExternalPackage]:
        """
        Detect external packages used by a target.

        Args:
            target: CMake target from cmake-file-api
            cmake_cache_path: Path to CMakeCache.txt
            cmake_lists_path: Path to CMakeLists.txt

        Returns:
            List of ExternalPackage objects

        Raises:
            FileNotFoundError: If required files don't exist
            ValueError: If parsing fails
            RuntimeError: If detection logic fails
        """
        # Step 1: Parse find_package() calls
        package_names = self._parse_find_package_calls(cmake_lists_path)

        # Step 2: Build package → libraries map
        package_lib_map = self._build_package_library_map(package_names, cmake_cache_path)

        # Step 3: Extract target link libraries
        target_libraries = self._extract_target_link_libraries(target)

        # Step 4: Match libraries to packages
        detected_packages = self._match_libraries_to_packages(target_libraries, package_lib_map)

        # Step 5: Create ExternalPackage objects
        return [
            ExternalPackage(
                name=pkg_name,
                package_manager=PackageManager(
                    name="CMake",
                    package_name=pkg_name
                )
            )
            for pkg_name in detected_packages
        ]

    def _parse_find_package_calls(self, cmake_lists_path: Path) -> List[str]:
        """
        Parse find_package() calls from CMakeLists.txt.

        Args:
            cmake_lists_path: Path to CMakeLists.txt (can be relative or absolute)

        Returns:
            List of package names

        Raises:
            FileNotFoundError: If CMakeLists.txt doesn't exist
            ValueError: If parsing fails
        """
        # Ensure absolute path
        cmake_lists_path = Path(cmake_lists_path).resolve()

        if not cmake_lists_path.exists():
            raise FileNotFoundError(
                f"Cannot detect external packages: CMakeLists.txt not found at {cmake_lists_path}"
            )

        try:
            with open(cmake_lists_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read {cmake_lists_path}: {e}")

        try:
            ast = cmp.parse(content)
        except Exception as e:
            raise ValueError(f"Failed to parse {cmake_lists_path}: {e}")

        # Extract package names from find_package() calls
        packages = []
        for item in ast:
            if hasattr(item, 'name') and item.name == 'find_package':
                if len(item.body) > 0:
                    # First argument is package name
                    package_name = item.body[0].contents
                    packages.append(package_name)

        return packages

    def _build_package_library_map(
        self,
        packages: List[str],
        cmake_cache_path: Path
    ) -> Dict[str, List[str]]:
        """
        Build map of package names to library file paths from CMakeCache.txt.

        Args:
            packages: List of package names from find_package()
            cmake_cache_path: Path to CMakeCache.txt

        Returns:
            Dictionary mapping package name to list of library paths

        Raises:
            FileNotFoundError: If CMakeCache.txt doesn't exist
        """
        if not cmake_cache_path.exists():
            raise FileNotFoundError(
                f"Cannot detect external packages: CMakeCache.txt not found at {cmake_cache_path}"
            )

        # Read cache file
        try:
            with open(cmake_cache_path, 'r', encoding='utf-8') as f:
                cache_lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Failed to read {cmake_cache_path}: {e}")

        # Build map for each package
        package_map = {}
        for package in packages:
            libs = self._find_package_libraries_in_cache(package, cache_lines)
            package_map[package] = libs

        return package_map

    def _find_package_libraries_in_cache(
        self,
        package: str,
        cache_lines: List[str]
    ) -> List[str]:
        """
        Find library paths for a package in CMakeCache.txt lines.

        Searches for patterns like:
        - {PACKAGE}_LIBRARIES
        - {PACKAGE}_LIBRARY
        - Special case for JNI: JAVA_JVM_LIBRARY, JAVA_AWT_LIBRARY

        Args:
            package: Package name (e.g., "JNI", "Java")
            cache_lines: Lines from CMakeCache.txt

        Returns:
            List of library file paths
        """
        # Standard patterns
        patterns = [
            f"{package}_LIBRARIES",
            f"{package}_LIBRARY"
        ]

        # Special cases for known packages
        if package == "JNI":
            patterns.extend(["JAVA_JVM_LIBRARY", "JAVA_AWT_LIBRARY"])

        libraries = []
        for line in cache_lines:
            # Skip comments and empty lines
            if line.startswith('#') or line.startswith('//') or not line.strip():
                continue

            # Check each pattern
            for pattern in patterns:
                if line.startswith(f"{pattern}:"):
                    # Parse: VARIABLE:TYPE=value
                    if '=' in line:
                        value = line.split('=', 1)[1].strip()
                        # Handle NOTFOUND values
                        if value and value != "NOTFOUND" and not value.endswith("-NOTFOUND"):
                            # Handle semicolon-separated lists
                            libs = value.split(';')
                            libraries.extend([lib for lib in libs if lib])

        return libraries

    def _extract_target_link_libraries(self, target) -> List[str]:
        """
        Extract link libraries from cmake-file-api target.

        Args:
            target: CMake target from cmake-file-api

        Returns:
            List of library paths/names
        """
        # Check if target has link section
        # UTILITY targets and targets that don't link libraries won't have this
        if not hasattr(target, 'link') or target.link is None:
            return []

        libraries = []
        for fragment in target.link.commandFragments:
            if fragment.role == 'libraries':
                # Fragment may contain multiple space-separated libraries
                fragment_str = fragment.fragment.strip('"')
                libs = fragment_str.split()
                libraries.extend(libs)

        return libraries

    def _match_libraries_to_packages(
        self,
        target_libs: List[str],
        package_lib_map: Dict[str, List[str]]
    ) -> Set[str]:
        """
        Match target libraries to packages.

        Args:
            target_libs: Libraries linked by the target
            package_lib_map: Map of package name → library paths

        Returns:
            Set of package names detected
        """
        if not target_libs:
            # Valid case: target doesn't link any libraries
            return set()

        detected = set()

        for target_lib in target_libs:
            # Skip system libraries
            lib_name = Path(target_lib).name.lower()
            if lib_name in self.SYSTEM_LIBRARIES:
                continue

            # Check which package(s) this library belongs to
            for pkg_name, pkg_libs in package_lib_map.items():
                if any(self._normalize_path(target_lib) == self._normalize_path(pkg_lib)
                       for pkg_lib in pkg_libs):
                    detected.add(pkg_name)

        return detected

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for comparison.

        Handles:
        - Case-insensitive comparison (Windows)
        - Forward/backward slashes
        - Absolute path resolution

        Args:
            path: Path string

        Returns:
            Normalized lowercase string
        """
        try:
            # Convert to absolute path and lowercase for comparison
            return str(Path(path).resolve()).lower()
        except Exception:
            # If path is invalid, just lowercase it
            return path.lower()
