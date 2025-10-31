"""
CMakeSourceFileParser - Extracts source files from CMakeLists.txt for custom targets.

Uses parse_cmake package to parse CMakeLists.txt and extract source file arguments
from function calls like add_jar(), add_custom_jar(), add_go_shared_library(), etc.
"""

from pathlib import Path
from typing import List, Optional

try:
    import parse_cmake.parsing as cmp
except ImportError:
    cmp = None


class CMakeSourceFileParser:
    """
    Parses CMakeLists.txt to extract source files for custom targets.

    Supports various function signatures:
    - add_jar(NAME SOURCES file1 file2 ...) - CMake built-in
    - add_custom_jar(target jar_name version file1 file2 ...) - our custom
    - add_go_shared_library(target output_name file1 file2 ...) - our custom
    """

    def __init__(self):
        """Initialize parser."""
        if cmp is None:
            raise ImportError("parse_cmake package is required. Install with: pip install parse_cmake")

    def extract_sources_for_target(
        self,
        target_name: str,
        cmake_lists_path: Path,
        repo_root: Path
    ) -> List[Path]:
        """
        Extract source files for a target from CMakeLists.txt.

        Args:
            target_name: Name of the CMake target to find
            cmake_lists_path: Path to CMakeLists.txt
            repo_root: Repository root for resolving relative paths

        Returns:
            List of source file paths relative to repo root

        Raises:
            FileNotFoundError: If CMakeLists.txt doesn't exist
            ValueError: If parsing fails or target not found
        """
        # Read CMakeLists.txt (fail-fast if missing)
        try:
            with open(cmake_lists_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Cannot extract sources for target '{target_name}': "
                f"CMakeLists.txt not found at {cmake_lists_path}"
            ) from e

        # Parse CMakeLists.txt (fail-fast on parsing errors)
        try:
            ast = cmp.parse(content)
        except Exception as e:
            raise ValueError(
                f"Failed to parse CMakeLists.txt at {cmake_lists_path}: {e}"
            ) from e

        # Find function call for this target
        found_targets = []
        for item in ast:
            if not hasattr(item, 'name') or not hasattr(item, 'body'):
                continue

            function_name = item.name
            if function_name not in ['add_jar', 'add_custom_jar', 'add_go_shared_library', 'add_custom_target']:
                continue

            # Track all targets we find for better error messages
            if len(item.body) > 0:
                found_targets.append(item.body[0].contents)

            # Check if this function call is for our target
            if not self._is_our_target(item, target_name):
                continue

            # Extract source files based on function signature
            source_args = self._extract_source_arguments(item)

            # Convert to Path objects relative to repo root
            source_files = []
            for source_str in source_args:
                # Handle CMake variables (basic support)
                source_str = self._resolve_simple_variables(source_str, repo_root)

                # Convert to Path relative to repo root
                source_path = Path(source_str)
                if not source_path.is_absolute():
                    # Relative to CMakeLists.txt directory
                    cmake_dir = cmake_lists_path.parent
                    source_path = (cmake_dir / source_path).relative_to(repo_root)

                source_files.append(source_path)

            return source_files

        # Target not found - fail-fast with details
        found_list = ', '.join(found_targets) if found_targets else 'none'
        raise ValueError(
            f"Target '{target_name}' not found in {cmake_lists_path}. "
            f"Found targets: {found_list}"
        )

    def _is_our_target(self, command, target_name: str) -> bool:
        """
        Check if this function call is for the target we're looking for.

        Args:
            command: Parsed command from AST
            target_name: Target name to match

        Returns:
            True if this command is for our target
        """
        if len(command.body) == 0:
            return False

        # Target name is always first argument
        first_arg = command.body[0].contents
        return first_arg == target_name

    def _extract_source_arguments(self, command) -> List[str]:
        """
        Extract source file arguments from a function call.

        Different functions have different signatures:
        - add_jar(name SOURCES file1 file2 VERSION ...) - after SOURCES keyword
        - add_custom_jar(target jar_name version file1 file2) - args 3+
        - add_go_shared_library(target output_name file1 file2) - args 2+

        Args:
            command: Parsed command from AST

        Returns:
            List of source file argument strings
        """
        function_name = command.name
        args = [arg.contents for arg in command.body]

        if function_name == 'add_jar':
            # add_jar(name SOURCES file1 file2 VERSION ver ENTRY_POINT ...)
            # Extract files after SOURCES keyword until next keyword
            return self._extract_after_keyword(args, 'SOURCES')

        elif function_name == 'add_custom_jar':
            # add_custom_jar(target jar_name version file1 file2 ...)
            # Source files start at index 3
            return args[3:] if len(args) > 3 else []

        elif function_name == 'add_go_shared_library':
            # add_go_shared_library(target output_name file1 file2 ...)
            # Source files start at index 2
            return args[2:] if len(args) > 2 else []

        else:
            # Unknown function, return empty
            return []

    def _extract_after_keyword(self, args: List[str], keyword: str) -> List[str]:
        """
        Extract arguments after a keyword until the next keyword.

        For add_jar: extract files after SOURCES until VERSION/ENTRY_POINT/etc.

        Args:
            args: List of all arguments
            keyword: Keyword to find (e.g., "SOURCES")

        Returns:
            List of arguments after keyword until next keyword
        """
        # Known keywords in add_jar
        keywords = ['SOURCES', 'INCLUDE_JARS', 'VERSION', 'OUTPUT_NAME',
                    'OUTPUT_DIR', 'ENTRY_POINT', 'MANIFEST']

        try:
            start_idx = args.index(keyword) + 1
        except ValueError:
            return []

        # Find next keyword
        result = []
        for i in range(start_idx, len(args)):
            if args[i] in keywords:
                break
            result.append(args[i])

        return result

    def _resolve_simple_variables(self, source_str: str, repo_root: Path) -> str:
        """
        Resolve simple CMake variables in source strings.

        Only handles basic cases:
        - ${CMAKE_CURRENT_SOURCE_DIR}/file.java
        - ${CMAKE_SOURCE_DIR}/file.go

        More complex variable resolution would require full CMake evaluation.

        Args:
            source_str: Source file path potentially with variables
            repo_root: Repository root for variable resolution

        Returns:
            Resolved path string
        """
        # Simple variable substitution
        if '${CMAKE_CURRENT_SOURCE_DIR}' in source_str:
            source_str = source_str.replace('${CMAKE_CURRENT_SOURCE_DIR}/', '')
        if '${CMAKE_SOURCE_DIR}' in source_str:
            source_str = source_str.replace('${CMAKE_SOURCE_DIR}/', '')

        return source_str
