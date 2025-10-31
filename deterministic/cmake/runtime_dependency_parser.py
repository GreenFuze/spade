"""
RuntimeDependencyParser - Extracts runtime dependencies from target properties.

Since cmake-file-api does not expose target properties like VS_DEBUGGER_ENVIRONMENT,
this module parses CMakeLists.txt to find set_target_properties() calls and extract
runtime dependencies specified via CLASSPATH, PATH, LD_LIBRARY_PATH, etc.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Union

from core.schemas import Component, Aggregator, Runner, TestDefinition, NodeType


class RuntimeDependencyParser:
    """
    Parses runtime dependencies from CMakeLists.txt target properties.

    Focuses on environment variable properties that specify runtime artifacts:
    - VS_DEBUGGER_ENVIRONMENT: Windows Visual Studio debugger environment
    - Looks for CLASSPATH, PATH, LD_LIBRARY_PATH, DYLD_LIBRARY_PATH
    """

    def parse_dependencies(
        self,
        target_name: str,
        cmake_lists_path: Path,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]]
    ) -> List[Union[Component, Aggregator, Runner]]:
        """
        Parse runtime dependencies for a target from CMakeLists.txt.

        Args:
            target_name: Name of the CMake target
            cmake_lists_path: Path to CMakeLists.txt
            findings: Cache of already-created RIG nodes

        Returns:
            List of RIG nodes that are runtime dependencies
        """
        # Read CMakeLists.txt
        try:
            with open(cmake_lists_path, 'r', encoding='utf-8') as f:
                cmake_content = f.read()
        except FileNotFoundError:
            return []

        # Find set_target_properties() for this target
        property_value = self._extract_target_property(
            cmake_content,
            target_name,
            "VS_DEBUGGER_ENVIRONMENT"
        )

        if not property_value:
            return []

        # Parse environment variables to find artifact references
        artifacts = self._parse_environment_string(property_value)

        # Match artifacts to components
        dependencies = []
        for artifact_name in artifacts:
            component = self._match_artifact_to_component(artifact_name, findings)
            if component:
                dependencies.append(component)

        return dependencies

    def _extract_target_property(
        self,
        cmake_content: str,
        target_name: str,
        property_name: str
    ) -> Optional[str]:
        """
        Extract a property value from set_target_properties() call.

        Looks for patterns like:
        set_target_properties(target_name PROPERTIES
            PROPERTY_NAME "value"
        )

        Args:
            cmake_content: Full CMakeLists.txt content
            target_name: Target name to search for
            property_name: Property name to extract

        Returns:
            Property value string, or None if not found
        """
        # Pattern to match set_target_properties(target_name PROPERTIES ...)
        # This handles multi-line calls and various spacing
        pattern = rf'set_target_properties\s*\(\s*{re.escape(target_name)}\s+PROPERTIES\s+(.*?)\)'

        # Search with DOTALL to handle multi-line
        match = re.search(pattern, cmake_content, re.DOTALL | re.IGNORECASE)
        if not match:
            return None

        properties_block = match.group(1)

        # Find the specific property
        # Pattern: PROPERTY_NAME "value" or PROPERTY_NAME value
        prop_pattern = rf'{re.escape(property_name)}\s+["\']?(.*?)["\']?\s*(?:\n|$|\)|,)'
        prop_match = re.search(prop_pattern, properties_block, re.IGNORECASE)

        if not prop_match:
            return None

        value = prop_match.group(1).strip()

        # Remove quotes if present
        value = value.strip('"\'')

        return value

    def _parse_environment_string(self, env_string: str) -> List[str]:
        """
        Parse environment variable string to extract artifact names.

        Looks for:
        - CLASSPATH=path1;path2;path3 (Windows)
        - CLASSPATH=path1:path2:path3 (Unix)
        - PATH=path1;path2
        - LD_LIBRARY_PATH=path1:path2
        - DYLD_LIBRARY_PATH=path1:path2 (macOS)

        Args:
            env_string: Environment string like "CLASSPATH=foo.jar;bar.jar"

        Returns:
            List of artifact filenames found in paths
        """
        artifacts = []

        # Split by newlines or spaces to handle multiple environment variables
        env_vars = re.split(r'[\n\s]+', env_string)

        for env_var in env_vars:
            if not env_var.strip():
                continue

            # Check if this is an environment variable assignment
            if '=' not in env_var:
                continue

            var_name, var_value = env_var.split('=', 1)
            var_name = var_name.strip().upper()

            # Only process known runtime dependency environment variables
            if var_name not in ['CLASSPATH', 'PATH', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH']:
                continue

            # Split by path separators (both ; for Windows and : for Unix)
            paths = re.split(r'[;:]', var_value)

            for path_str in paths:
                path_str = path_str.strip()
                if not path_str:
                    continue

                # Extract just the filename from the path
                # Handle both CMake variables and literal paths
                # E.g., ${CMAKE_CURRENT_BINARY_DIR}/foo.jar -> foo.jar
                path_obj = Path(path_str)
                artifact_name = path_obj.name

                # Only include files with known extensions
                if artifact_name.endswith(('.jar', '.dll', '.so', '.dylib', '.exe')):
                    artifacts.append(artifact_name)

        return artifacts

    def _match_artifact_to_component(
        self,
        artifact_name: str,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]]
    ) -> Optional[Union[Component, Aggregator, Runner]]:
        """
        Match an artifact filename to an existing RIG component.

        Args:
            artifact_name: Filename like "java_hello_lib-1.0.0.jar"
            findings: Cache of already-created RIG nodes

        Returns:
            Component if found, None otherwise
        """
        # Search in components (most common case)
        if NodeType.COMPONENT in findings:
            for component in findings[NodeType.COMPONENT].values():
                if isinstance(component, Component) and component.name == artifact_name:
                    return component

        # Could also search aggregators and runners if needed
        # For now, only components are relevant for runtime dependencies

        return None
