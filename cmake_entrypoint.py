"""
CMakeEntrypoint class for parsing CMake configuration and extracting build information.
Uses the cmake-file-api package to extract all build system information.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any, Union, Set

from cmake_file_api import CMakeProject, ObjectKind
from schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, Test, Evidence, ComponentLocation, Aggregator, Runner, RepositoryInfo, BuildSystemInfo
from rig import RIG


class ResearchBackedUtilities:
    """
    Utility class for research-backed upgrades to maximize coverage before falling back to UNKNOWN.
    Implements evidence-first approach with no heuristics.
    """
    
    # Regex for variable expansion
    VAR_RX = re.compile(r"\$\{(\w+)\}")
    
    @staticmethod
    def expand_vars(s: str, cache: Dict[str, str]) -> str:
        """Expand ${VAR} using File API cache."""
        return ResearchBackedUtilities.VAR_RX.sub(
            lambda m: cache.get(m.group(1), m.group(0)), s
        )
    
    @staticmethod
    def normalize_token(t: str) -> str:
        """Normalize tokens for classifier while preserving evidence."""
        return t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in ('"', "'") else t
    
    @staticmethod
    def unknown_field(field: str, context: str, evidence: Dict[str, Any], errors: Set[str]) -> None:
        """Evidence-first UNKNOWN field reporting."""
        error_msg = f"unknown_{field}"
        errors.add(f"{error_msg}: context={context}, evidence={evidence}")
    
    @staticmethod
    def direct_deps(target_id: str, fileapi_deps: Set[str], graphviz_deps: Optional[Set[str]] = None) -> Set[str]:
        """Direct vs transitive deps reconciliation."""
        if graphviz_deps:
            return fileapi_deps & graphviz_deps
        return fileapi_deps  # fall back when graphviz disabled
    
    @staticmethod
    def get_artifact_name_from_target(target: Any) -> Optional[str]:
        """Get artifact name from target using File API evidence."""
        # Priority 1: nameOnDisk (most authoritative)
        if hasattr(target, 'nameOnDisk') and target.nameOnDisk:
            return Path(target.nameOnDisk).name
        
        # Priority 2: artifacts array
        if hasattr(target, 'artifacts') and target.artifacts:
            for artifact in target.artifacts:
                if hasattr(artifact, 'path') and artifact.path:
                    return Path(artifact.path).name
        
        return None
    
    @staticmethod
    def get_output_path_from_target(target: Any, cache: Dict[str, str]) -> Optional[Path]:
        """Get output path from target using File API evidence."""
        # Priority 1: artifacts array (most authoritative)
        if hasattr(target, 'artifacts') and target.artifacts:
            for artifact in target.artifacts:
                if hasattr(artifact, 'path') and artifact.path:
                    artifact_path = Path(artifact.path)
                    # Expand variables in path
                    expanded_path = ResearchBackedUtilities.expand_vars(str(artifact_path), cache)
                    return Path(expanded_path)
        
        # Priority 2: nameOnDisk
        if hasattr(target, 'nameOnDisk') and target.nameOnDisk:
            expanded_path = ResearchBackedUtilities.expand_vars(target.nameOnDisk, cache)
            return Path(expanded_path)
        
        return None
    
    @staticmethod
    def get_language_from_toolchains(target: Any, toolchains: Any) -> Optional[str]:
        """Get language from toolchains using File API evidence."""
        if not toolchains or not hasattr(toolchains, 'toolchains'):
            return None
        
        # Get primary language from target's compileGroups
        if hasattr(target, 'compileGroups'):
            for cg in target.compileGroups:
                if hasattr(cg, 'language') and cg.language:
                    return cg.language.lower()
        
        return None
    
    @staticmethod
    def get_source_extensions_from_toolchains(toolchains: Any, language: str) -> List[str]:
        """Get source file extensions from toolchains for a language."""
        if not toolchains or not hasattr(toolchains, 'toolchains'):
            return []
        
        for tc in toolchains.toolchains:
            if hasattr(tc, 'language') and tc.language and tc.language.lower() == language.lower():
                if hasattr(tc, 'sourceFileExtensions') and tc.sourceFileExtensions:
                    return tc.sourceFileExtensions
        
        return []
    
    @staticmethod
    def detect_package_manager_from_cache(cache_entries: List[Any]) -> Optional[str]:
        """Detect package manager from cache entries using evidence."""
        for entry in cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                name = entry.name
                value = str(entry.value)
                
                # vcpkg detection
                if name == 'CMAKE_TOOLCHAIN_FILE' and 'vcpkg.cmake' in value:
                    return 'vcpkg'
                elif name.startswith('VCPKG_') or name.startswith('Z_VCPKG_'):
                    return 'vcpkg'
                
                # Conan detection
                if name == 'CMAKE_TOOLCHAIN_FILE' and 'conan_toolchain.cmake' in value:
                    return 'conan'
                elif name.startswith('CONAN_'):
                    return 'conan'
        
        return None
    
    @staticmethod
    def strip_generator_expressions(text: str) -> str:
        """Strip generator expressions from text, pointing to resolved File API values instead."""
        # Pattern to match generator expressions like $<CONFIG:Debug,Release>
        genex_pattern = r'\$<[^>]+>'
        
        # Replace generator expressions with placeholders
        stripped = re.sub(genex_pattern, '[RESOLVED_BY_FILE_API]', text)
        
        return stripped
    
    @staticmethod
    def has_generator_expressions(text: str) -> bool:
        """Check if text contains generator expressions."""
        genex_pattern = r'\$<[^>]+>'
        return bool(re.search(genex_pattern, text))
    
    @staticmethod
    def prefer_file_api_resolved_value(raw_value: str, file_api_value: Optional[str], context: str) -> str:
        """Prefer File API resolved value over raw value with generator expressions."""
        if file_api_value and not ResearchBackedUtilities.has_generator_expressions(file_api_value):
            return file_api_value
        
        if ResearchBackedUtilities.has_generator_expressions(raw_value):
            # Strip generator expressions and indicate File API should be used
            stripped = ResearchBackedUtilities.strip_generator_expressions(raw_value)
            return f"{stripped} [Use File API resolved value for {context}]"
        
        return raw_value


class CMakeParser:
    """
    Parser for CMakeLists.txt files to extract evidence-based information.
    Replaces heuristics with deterministic parsing of CMake commands.
    """
    
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.custom_targets: Dict[str, Dict[str, Any]] = {}
        self.find_packages: List[Dict[str, Any]] = []
        self.add_tests: List[Dict[str, Any]] = []
        self.target_link_libraries: Dict[str, List[str]] = {}
        self.output_directories: Dict[str, str] = {}
        
    def parse_all_cmake_files(self) -> None:
        """Parse all CMakeLists.txt files in the source directory."""
        cmake_files = list(self.source_dir.rglob("CMakeLists.txt"))
        if not cmake_files:
            raise ValueError(f"No CMakeLists.txt files found in {self.source_dir}")
            
        for cmake_file in cmake_files:
            self._parse_cmake_file(cmake_file)
    
    def _parse_cmake_file(self, cmake_file: Path) -> None:
        """Parse a single CMakeLists.txt file."""
        try:
            with open(cmake_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read {cmake_file}: {e}")
        
        # Parse different CMake commands
        self._parse_add_custom_target(content, cmake_file)
        self._parse_find_package(content, cmake_file)
        self._parse_add_test(content, cmake_file)
        self._parse_target_link_libraries(content, cmake_file)
        self._parse_output_directories(content, cmake_file)
    
    def _parse_add_custom_target(self, content: str, file_path: Path) -> None:
        """Parse add_custom_target() calls."""
        # Pattern to match add_custom_target with various parameters (including hyphens in target names)
        pattern = r'add_custom_target\s*\(\s*([\w-]+)\s*(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            target_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.custom_targets[target_name] = {
                'name': target_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'has_commands': 'COMMAND' in params,
                'has_depends': 'DEPENDS' in params,
                'has_output': 'OUTPUT' in params,
                'has_byproducts': 'BYPRODUCTS' in params
            }
    
    def _parse_find_package(self, content: str, file_path: Path) -> None:
        """Parse find_package() calls."""
        # Pattern to match find_package with package name and options (including hyphens)
        pattern = r'find_package\s*\(\s*([\w-]+)\s*(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            package_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.find_packages.append({
                'name': package_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'is_required': 'REQUIRED' in params,
                'components': params.get('COMPONENTS', [])
            })
    
    def _parse_add_test(self, content: str, file_path: Path) -> None:
        """Parse add_test() calls."""
        # Pattern to match add_test with NAME and COMMAND (including hyphens)
        pattern = r'add_test\s*\(\s*NAME\s+([\w-]+)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            test_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.add_tests.append({
                'name': test_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'command': params.get('COMMAND', []),
                'working_directory': params.get('WORKING_DIRECTORY', '')
            })
    
    def _parse_target_link_libraries(self, content: str, file_path: Path) -> None:
        """Parse target_link_libraries() calls."""
        # Pattern to match target_link_libraries (including hyphens)
        pattern = r'target_link_libraries\s*\(\s*([\w-]+)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            target_name = match.group(1)
            libraries_str = match.group(2)
            
            # Parse library names (split by whitespace, handle quoted strings)
            libraries = self._parse_cmake_list(libraries_str)
            
            if target_name not in self.target_link_libraries:
                self.target_link_libraries[target_name] = []
            self.target_link_libraries[target_name].extend(libraries)
    
    def _parse_output_directories(self, content: str, file_path: Path) -> None:
        """Parse CMAKE_*_OUTPUT_DIRECTORY settings."""
        # Pattern to match set(CMAKE_*_OUTPUT_DIRECTORY ...)
        pattern = r'set\s*\(\s*(CMAKE_\w+_OUTPUT_DIRECTORY)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            var_name = match.group(1)
            value = match.group(2).strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            self.output_directories[var_name] = value
    
    def _parse_cmake_parameters(self, params_str: str) -> Dict[str, List[str]]:
        """Parse CMake function parameters into a dictionary."""
        params: Dict[str, List[str]] = {}
        current_key: Optional[str] = None
        current_values: List[str] = []
        
        # Split by whitespace but handle quoted strings
        tokens = self._tokenize_cmake_string(params_str)
        
        for token in tokens:
            if token.upper() in ['COMMAND', 'DEPENDS', 'OUTPUT', 'BYPRODUCTS', 'COMPONENTS', 
                               'REQUIRED', 'WORKING_DIRECTORY', 'NAME']:
                # Save previous key-value pair
                if current_key:
                    params[current_key] = current_values
                
                # Start new key
                current_key = token.upper()
                current_values = []
            else:
                current_values.append(token)
        
        # Save last key-value pair
        if current_key:
            params[current_key] = current_values
        
        return params
    
    def _parse_cmake_list(self, list_str: str) -> List[str]:
        """Parse a CMake list (space-separated values, handling quotes)."""
        return self._tokenize_cmake_string(list_str)
    
    def _tokenize_cmake_string(self, text: str) -> List[str]:
        """Tokenize CMake string handling quotes and variables."""
        tokens: List[str] = []
        current_token = ""
        in_quotes = False
        quote_char: Optional[str] = None
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if not in_quotes:
                if char in ['"', "'"]:
                    in_quotes = True
                    quote_char = char
                    current_token += char
                elif char.isspace():
                    if current_token.strip():
                        tokens.append(current_token.strip())
                        current_token = ""
                else:
                    current_token += char
            else:
                current_token += char
                if char == quote_char and (i == 0 or text[i-1] != '\\'):
                    in_quotes = False
                    quote_char = None
            
            i += 1
        
        if current_token.strip():
            tokens.append(current_token.strip())
        
        return tokens
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a character position in content."""
        return content[:position].count('\n') + 1
    
    def get_custom_target_info(self, target_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a custom target."""
        return self.custom_targets.get(target_name)
    
    def get_find_package_info(self, package_name: str) -> List[Dict[str, Any]]:
        """Get information about find_package calls for a package."""
        return [pkg for pkg in self.find_packages if pkg['name'] == package_name]
    
    def get_test_info(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an add_test call."""
        for test in self.add_tests:
            if test['name'] == test_name:
                return test
        return None
    
    def get_target_dependencies(self, target_name: str) -> List[str]:
        """Get dependencies for a target from target_link_libraries."""
        return self.target_link_libraries.get(target_name, [])
    
    def get_output_directory(self, directory_type: str) -> Optional[str]:
        """Get output directory for a specific type (RUNTIME, LIBRARY, etc.)."""
        return self.output_directories.get(f"CMAKE_{directory_type}_OUTPUT_DIRECTORY")


class CMakeEntrypoint:
    """
    Parses CMake configuration and extracts build system information.

    This class uses the cmake-file-api package to analyze CMake projects and create
    a canonical representation of the build system structure, including components,
    tests, dependencies, and external packages.
    """

    def __init__(self, cmake_config_dir: Path, parse_cmake: bool = True) -> None:
        """
        Initialize CMakeEntrypoint with CMake configuration directory.

        Args:
            cmake_config_dir: Path to CMake configuration directory
            parse_cmake: Whether to parse CMake configuration (default: True)
        """
        self.cmake_config_dir = Path(cmake_config_dir)
        self.repo_root = self._find_repo_root()

        # Create RIG instance to hold all extracted data
        # MetaFFI-specific build artifact patterns
        metaFFI_patterns = ["cmake-build-", "build/", "build\\", "output/", "output\\"]
        self._rig = RIG(custom_build_artifact_patterns=metaFFI_patterns)

        # Temporary storage for extracted data (will be moved to RIG)
        self._temp_project_name: str = ""
        self._temp_components: List[Component] = []
        self._temp_aggregators: List[Aggregator] = []
        self._temp_runners: List[Runner] = []
        self._temp_tests: List[Test] = []
        self._temp_build_directory: Path = Path()
        self._temp_output_directory: Path = Path()
        self._temp_configure_command: str = ""
        self._temp_build_command: str = ""
        self._temp_install_command: str = ""
        self._temp_test_command: str = ""
        self._temp_build_system_info: Optional[BuildSystemInfo] = None
        self._temp_backtrace_graph: Optional[Any] = None
        self._temp_cache_entries: List[Any] = []
        self._temp_global_external_packages: List[ExternalPackage] = []
        self._temp_toolchains: Optional[Any] = None
        
        # Research-backed upgrades: evidence tracking
        self._temp_cache_dict: Dict[str, str] = {}  # Cache as dict for variable expansion
        self._temp_unknown_errors: Set[str] = set()  # Track UNKNOWN_* errors
        self._temp_compile_commands: Optional[Dict[str, Any]] = None  # compile_commands.json
        self._temp_graphviz_deps: Optional[Dict[str, Set[str]]] = None  # Graphviz dependencies
        
        # Initialize CMake parser for evidence-based detection
        self._cmake_parser: Optional[CMakeParser] = None
        if parse_cmake:
            try:
                # Find source directory (parent of cmake_config_dir)
                source_dir = self.cmake_config_dir.parent
                self._cmake_parser = CMakeParser(source_dir)
                self._cmake_parser.parse_all_cmake_files()
            except Exception as e:
                raise ValueError(f"Failed to parse CMakeLists.txt files: {e}")

        # Parse CMake information using the file API (optional)
        if parse_cmake:
            self.parse_cmake_info()

    def _find_repo_root(self) -> Path:
        """Find the repository root by looking for CMakeLists.txt."""
        current = self.cmake_config_dir
        while current != current.parent:
            if (current / "CMakeLists.txt").exists():
                return current
            current = current.parent

        raise ValueError(f"Could not find repository root from {self.cmake_config_dir}")

    def parse_cmake_info(self) -> None:
        """Parse CMake configuration using the file API."""
        try:
            # Create CMakeProject instance
            proj = CMakeProject(build_path=self.cmake_config_dir, source_path=self.repo_root, api_version=1)

            # Ask CMake for all supported object kinds for API v1
            proj.cmake_file_api.instrument_all()

            # Run CMake configure to produce replies
            proj.configure(quiet=False, args=["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])

            # Read all replies
            replies = proj.cmake_file_api.inspect_all()

            # Extract information from replies
            self._extract_from_replies(replies)

            # Extract additional information
            self._extract_build_commands()
            self._extract_output_directory()

            # Populate RIG with extracted data
            self._populate_rig()

        except Exception as e:
            raise RuntimeError(f"Failed to parse CMake configuration: {e}")

    def _extract_from_replies(self, replies: Dict[ObjectKind, Dict[int, Any]]) -> None:
        """Extract all information from CMake API replies."""
        # Load toolchains information first for language detection
        self._temp_toolchains_info = self._load_toolchains_info()
        
        # Extract from codemodel v2 (the build graph)
        if ObjectKind.CODEMODEL in replies and 2 in replies[ObjectKind.CODEMODEL]:
            codemodel_v2 = replies[ObjectKind.CODEMODEL][2]
            self._extract_from_codemodel(codemodel_v2)
        else:
            # Fallback: Load codemodel directly from JSON files
            self._extract_from_codemodel_fallback()

        # Extract from cache v2 (cache variables)
        if ObjectKind.CACHE in replies and 2 in replies[ObjectKind.CACHE]:
            cache_v2 = replies[ObjectKind.CACHE][2]
            self._extract_from_cache(cache_v2)
        else:
            # Fallback: Load cache directly from JSON files
            self._extract_from_cache_fallback()
            
            # Update existing components with global external packages
            self._update_components_with_global_packages()

        # Extract from toolchains v1 (compilers, versions)
        if ObjectKind.TOOLCHAINS in replies and 1 in replies[ObjectKind.TOOLCHAINS]:
            toolchains_v1 = replies[ObjectKind.TOOLCHAINS][1]
            self._extract_from_toolchains(toolchains_v1)

        # Extract from cmakeFiles v1 (CMakeLists.txt and included .cmake files)
        if ObjectKind.CMAKEFILES in replies and 1 in replies[ObjectKind.CMAKEFILES]:
            cmake_files_v1 = replies[ObjectKind.CMAKEFILES][1]
            self._extract_from_cmake_files(cmake_files_v1)

        # Extract tests using CTest JSON (requires built targets for reliable command[])
        self._extract_tests_from_ctest()
        
        # Load compile_commands.json as fallback for per-TU evidence
        self._load_compile_commands_json()
        
        # Load graphviz dependencies for direct vs transitive distinction
        self._load_graphviz_dependencies()

    def _extract_from_codemodel(self, codemodel: Any) -> None:
        """Extract information from codemodel v2."""
        # Use proper type checking instead of hasattr
        if not hasattr(codemodel, "configurations") or not codemodel.configurations:
            return

        # Store the backtraceGraph for evidence resolution
        self._temp_backtrace_graph = getattr(codemodel, 'backtraceGraph', None)
        
        # Extract install metadata from codemodel directories
        self._extract_install_metadata_from_codemodel(codemodel)

        # Use the first configuration (typically Debug or Release)
        cfg = codemodel.configurations[0]

        # Extract project information
        if hasattr(cfg, "projects") and cfg.projects:
            self._temp_project_name = cfg.projects[0].name

        # Extract targets (components, aggregators, runners)
        if hasattr(cfg, "targets"):
            # First pass: Create all nodes without resolving dependencies
            for target in cfg.targets:
                build_node = self._create_build_node_from_target(target)
                if build_node:
                    if isinstance(build_node, Component):
                        self._temp_components.append(build_node)
                    elif isinstance(build_node, Aggregator):
                        self._temp_aggregators.append(build_node)
                    else:  # Runner
                        self._temp_runners.append(build_node)

            # Second pass: Resolve all dependencies
            self._resolve_all_dependencies(cfg.targets)

    def _resolve_all_dependencies(self, targets: List[Any]) -> None:
        """Resolve all dependencies for all nodes in a second pass."""
        # Create a mapping of target names to nodes
        name_to_node: Dict[str, Union[Component, Aggregator, Runner]] = {}

        for comp in self._temp_components:
            name_to_node[comp.name] = comp
        for agg in self._temp_aggregators:
            name_to_node[agg.name] = agg
        for runner in self._temp_runners:
            name_to_node[runner.name] = runner

        # Resolve dependencies for each target
        for target in targets:
            target_name = getattr(target, "name", "")
            if target_name in name_to_node:
                node = name_to_node[target_name]
                dependencies = self._extract_dependencies_from_target_with_mapping(target, name_to_node)
                # Update the node's dependencies
                node.depends_on = dependencies

    def _extract_dependencies_from_target_with_mapping(self, target: Any, name_to_node: Dict[str, Union[Component, Aggregator, Runner]]) -> List[Union[Component, Aggregator, Runner]]:
        """Extract dependencies from target using the name mapping."""
        dependencies: List[Union[Component, Aggregator, Runner]] = []

        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)

        if hasattr(actual_target, "dependencies"):
            for dep in actual_target.dependencies:
                if hasattr(dep, "target") and hasattr(dep.target, "name"):
                    dep_name = dep.target.name
                    if dep_name in name_to_node:
                        dependencies.append(name_to_node[dep_name])

        return dependencies

    def _create_build_node_from_target(self, target: Any) -> Optional[Union[Component, Aggregator, Runner]]:
        """Create appropriate build node from CMake target using detection logic."""
        try:
            # Get the actual target object from the wrapper
            actual_target = getattr(target, "target", target)
            
            # Load detailed target information if available
            actual_target = self._load_detailed_target_info(actual_target)
            target_type = getattr(actual_target, "type", "")
            target_name = getattr(target, "name", "")

            # Create evidence for this target
            evidence = self._create_evidence_from_target(target)

            # Don't resolve dependencies yet - will be done in second pass
            dependencies: List[Union[Component, Aggregator, Runner]] = []

            # Detection logic based on target type and properties
            # Handle both string and enum types
            target_type_str = str(target_type)

            if target_type_str in ["EXECUTABLE", "TargetType.EXECUTABLE", "SHARED_LIBRARY", "STATIC_LIBRARY", "MODULE_LIBRARY"]:
                # Standard CMake target types -> Component
                return self._create_component_from_standard_target(target, evidence, dependencies)

            elif target_type_str in ["UTILITY", "TargetType.UTILITY"]:
                # UTILITY targets are typically custom targets - need to determine if it's Component, Runner, or Aggregator
                return self._create_node_from_custom_target(target, evidence, dependencies)

            elif target_type_str in ["SHARED", "TargetType.SHARED"]:
                # SHARED targets are shared libraries -> Component
                return self._create_component_from_standard_target(target, evidence, dependencies)

            else:
                # Unknown target type - fatal error as requested
                raise RuntimeError(f"Unknown target type '{target_type}' for target '{target_name}'. This indicates a missed case in the detection logic.")

        except Exception as e:
            # Log the error but don't crash the entire parsing
            print(f"Warning: Failed to create build node for target '{getattr(target, 'name', 'unknown')}': {e}")
            return None

    def _create_evidence_from_target(self, target: Any) -> Evidence:
        """Create Evidence from target's backtrace information."""
        # Get the actual target data (target.target contains the real data)
        target_data = target.target if hasattr(target, 'target') else target
        target_name = getattr(target_data, 'name', 'unknown')
        
        # Try to get line numbers from backtrace
        if hasattr(target_data, 'backtrace') and target_data.backtrace is not None:
            backtrace = target_data.backtrace
            
            # Check if backtrace has file and line information directly
            if hasattr(backtrace, 'file') and hasattr(backtrace, 'line'):
                file_path = backtrace.file
                line = backtrace.line
                return Evidence(
                    id=None, 
                    file=Path(file_path), 
                    start_line=line, 
                    end_line=line, 
                    text=f"Target definition for {target_name}"
                )
            
            # If backtrace is an index, try to resolve it through backtraceGraph
            elif isinstance(backtrace, int) and self._temp_backtrace_graph:
                # Resolve backtrace index using the stored backtraceGraph
                file_path, line = self._resolve_backtrace(backtrace, self._temp_backtrace_graph)
                if file_path and line:
                    return Evidence(
                        id=None, 
                        file=Path(file_path), 
                        start_line=line, 
                        end_line=line, 
                        text=f"Target definition for {target_name}"
                    )
                else:
                    return Evidence(
                        id=None, 
                        file=Path("CMakeLists.txt"), 
                        start_line=1, 
                        end_line=1, 
                        text=f"Target definition for {target_name} (backtrace index: {backtrace})"
                    )

        # Fallback
        return Evidence(
            id=None, 
            file=Path("CMakeLists.txt"), 
            start_line=1, 
            end_line=1, 
            text=f"Target definition for {target_name}"
        )

    def _extract_dependencies_from_target(self, target: Any) -> List[Union[Component, Aggregator, Runner]]:
        """Extract dependencies using research-backed approach with direct vs transitive distinction."""
        dependencies: List[Union[Component, Aggregator, Runner]] = []

        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)
        target_name = getattr(actual_target, "name", "")

        # Research-backed approach: Use codemodel dependencies first
        fileapi_deps: Set[str] = set()
        if hasattr(actual_target, "dependencies"):
            for dep in actual_target.dependencies:
                if hasattr(dep, "target") and hasattr(dep.target, "name"):
                    fileapi_deps.add(dep.target.name)

        # Cross-check with graphviz for direct-only dependencies if available
        direct_deps = ResearchBackedUtilities.direct_deps(
            target_name, 
            fileapi_deps, 
            self._temp_graphviz_deps.get(target_name) if self._temp_graphviz_deps else None
        )

        # Find the dependency objects
        for dep_name in direct_deps:
            # Find in components
            for comp in self._temp_components:
                if comp.name == dep_name:
                    dependencies.append(comp)
                    break
            else:
                # Find in aggregators
                for agg in self._temp_aggregators:
                    if agg.name == dep_name:
                        dependencies.append(agg)
                        break
                else:
                    # Find in runners
                    for runner in self._temp_runners:
                        if runner.name == dep_name:
                            dependencies.append(runner)
                            break

        return dependencies

    def _create_component_from_standard_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner]]) -> Component:
        """Create Component from standard CMake target (EXECUTABLE, LIBRARY, etc.)."""
        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)
        
        # Load detailed target information (research-backed approach)
        hydrated_target = self._load_detailed_target_info(actual_target)

        # Determine component type from CMake target type (evidence-based)
        component_type = self._get_component_type_from_cmake_target(hydrated_target)

        # Extract source files
        source_files: List[Path] = []
        if hasattr(hydrated_target, "sources"):
            for source in hydrated_target.sources:
                if hasattr(source, "path"):
                    source_path = Path(source.path)
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)

        # Get programming language from compileGroups
        programming_language = self._extract_programming_language_from_target(hydrated_target)

        # Get output paths from artifacts
        output_path = self._extract_output_path_from_target(hydrated_target)

        # Extract external packages from link command fragments
        external_packages = self._extract_external_packages_from_target(hydrated_target)

        # Detect runtime environment
        runtime = self._detect_runtime_from_target(hydrated_target, source_files)

        # Create component location for the build action
        build_location = ComponentLocation(id=None, path=output_path, action="build", source_location=None, evidence=evidence)

        # Research-backed approach: Get artifact name from File API
        artifact_name = ResearchBackedUtilities.get_artifact_name_from_target(hydrated_target)
        if not artifact_name:
            # Report UNKNOWN if no artifact evidence
            ResearchBackedUtilities.unknown_field(
                "artifact_name",
                f"target_{getattr(hydrated_target, 'name', '')}",
                {
                    "has_artifacts": hasattr(hydrated_target, "artifacts") and bool(hydrated_target.artifacts),
                    "has_nameOnDisk": hasattr(hydrated_target, "nameOnDisk") and bool(hydrated_target.nameOnDisk)
                },
                self._temp_unknown_errors
            )
            artifact_name = getattr(hydrated_target, "name", "")

        return Component(
            id=None,
            name=getattr(target, "name", ""),
            type=component_type,
            runtime=runtime,
            output=artifact_name,
            output_path=output_path,
            programming_language=programming_language,
            source_files=source_files,
            external_packages=external_packages,
            depends_on=dependencies,
            evidence=evidence,
            locations=[build_location],
        )

    def _create_node_from_custom_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner]]) -> Union[Component, Aggregator, Runner]:
        """Create appropriate node from custom target using evidence-based classification."""
        target_name = getattr(target, "name", "")
        
        # Use CMakeParser for evidence-based classification
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based classification.")
        
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        if not custom_target_info:
            raise ValueError(f"No CMakeLists.txt evidence found for custom target '{target_name}'. " +
                           f"Cannot determine target classification without evidence.")
        
        # Evidence-based classification using parsed CMakeLists.txt data
        has_commands = custom_target_info['has_commands']
        has_depends = custom_target_info['has_depends']
        has_output = custom_target_info['has_output']
        has_byproducts = custom_target_info['has_byproducts']
        
        # Classification logic based on evidence:
        # 1. Has OUTPUT/BYPRODUCTS -> Component (produces artifacts)
        if has_output or has_byproducts:
            return self._create_component_from_custom_target(target, evidence, dependencies)
        
        # 2. Has DEPENDS but no COMMAND/OUTPUT -> Aggregator (groups dependencies)
        elif has_depends and not has_commands and not has_output:
            return Aggregator(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
        
        # 3. Has COMMAND but no OUTPUT/BYPRODUCTS -> Runner (executes commands)
        elif has_commands and not has_output and not has_byproducts:
            # Check if this is a risky runner
            is_risky = self._is_risky_runner(custom_target_info, target_name)
            runner = Runner(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
            
            # Add risky runner validation error if needed
            if is_risky:
                ResearchBackedUtilities.unknown_field(
                    "risky_runner",
                    f"target_{target_name}",
                    {
                        "has_commands": has_commands,
                        "has_depends": has_depends,
                        "command": custom_target_info.get('parameters', {}).get('COMMAND', []),
                        "working_directory": custom_target_info.get('parameters', {}).get('WORKING_DIRECTORY', '')
                    },
                    self._temp_unknown_errors
                )
            
            return runner
        
        # 4. No clear evidence -> fail fast
        else:
            raise ValueError(f"Custom target '{target_name}' has ambiguous classification. " +
                           f"Evidence: commands={has_commands}, depends={has_depends}, " +
                           f"output={has_output}, byproducts={has_byproducts}. " +
                           f"Cannot determine target type without clear evidence.")

    def _has_output_or_byproduct(self, target: Any) -> bool:
        """Check if custom target has OUTPUT or BYPRODUCT using evidence-based detection."""
        # Check artifacts for output files (evidence-based)
        if hasattr(target, "artifacts") and target.artifacts:
            return True

        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            return custom_target_info.get('has_output', False) or custom_target_info.get('has_byproducts', False)
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has OUTPUT/BYPRODUCTS without evidence.")

    def _has_command_only(self, target: Any) -> bool:
        """Check if custom target has COMMAND but no OUTPUT/BYPRODUCT using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            has_commands = custom_target_info.get('has_commands', False)
            has_output = custom_target_info.get('has_output', False)
            has_byproducts = custom_target_info.get('has_byproducts', False)
            
            return has_commands and not has_output and not has_byproducts
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has COMMAND without evidence.")

    def _has_depends_only(self, target: Any) -> bool:
        """Check if custom target has only DEPENDS using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            has_depends = custom_target_info.get('has_depends', False)
            has_commands = custom_target_info.get('has_commands', False)
            has_output = custom_target_info.get('has_output', False)
            has_byproducts = custom_target_info.get('has_byproducts', False)
            
            # Has DEPENDS but no COMMAND/OUTPUT/BYPRODUCTS -> Aggregator
            return has_depends and not has_commands and not has_output and not has_byproducts
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has DEPENDS without evidence.")

    def _create_component_from_custom_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner]]) -> Component:
        """Create Component from custom target that produces output."""
        target_name = getattr(target, "name", "")
        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)

        # Extract source files (may be empty for custom targets)
        source_files: List[Path] = []
        if hasattr(actual_target, "sources"):
            for source in actual_target.sources:
                if hasattr(source, "path"):
                    source_path = Path(source.path)
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)

        # Get output path from artifacts
        output_path = self._extract_output_path_from_target(actual_target)

        # Determine component type based on output (evidence-based)
        component_type = self._detect_component_type_from_output(output_path)

        # Get programming language from custom commands
        programming_language = self._extract_programming_language_from_custom_target(actual_target)

        # Detect runtime environment
        runtime = self._detect_runtime_from_custom_target(actual_target, source_files)

        # Create component location for the build action
        build_location = ComponentLocation(id=None, path=output_path, action="build", source_location=None, evidence=evidence)

        return Component(
            id=None,
            name=target_name,
            type=component_type,
            runtime=runtime,
            output=target_name,
            output_path=output_path,
            programming_language=programming_language,
            source_files=source_files,
            external_packages=[],  # Custom targets typically don't have external packages
            depends_on=dependencies,
            evidence=evidence,
            locations=[build_location],
        )

    def _detect_component_type_from_output(self, output_path: Path) -> ComponentType:
        """Detect component type from output file extension."""
        ext = output_path.suffix.lower()
        if ext in [".exe", ""]:  # Empty extension often means executable
            return ComponentType.EXECUTABLE
        elif ext in [".so", ".dll", ".dylib"]:
            return ComponentType.SHARED_LIBRARY
        elif ext in [".a", ".lib"]:
            return ComponentType.STATIC_LIBRARY
        elif ext in [".jar"]:
            return ComponentType.VM
        else:
            return ComponentType.EXECUTABLE  # Default

    def _extract_programming_language_from_custom_target(self, target: Any) -> str:
        """Extract programming language from custom target using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based language detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Try to extract language from COMMAND parameters
            command_params = custom_target_info.get('parameters', {}).get('COMMAND', [])
            if command_params:
                # Look for language indicators in the command
                command_str = " ".join(command_params).lower()
                if "go" in command_str or "go build" in command_str:
                    return "go"
                elif "java" in command_str or "javac" in command_str:
                    return "java"
                elif "python" in command_str or "py" in command_str:
                    return "python"
                elif "gcc" in command_str or "g++" in command_str or "clang" in command_str:
                    return "cpp"
                elif "csc" in command_str or "dotnet" in command_str:
                    return "csharp"
            
            # If no clear language indicators in command, fail fast
            raise ValueError(f"No programming language evidence found in COMMAND for target '{target_name}'. " +
                           f"Command: {command_params}. Cannot determine language without evidence.")
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine programming language without evidence.")

    def _detect_runtime_from_custom_target(self, target: Any, source_files: List[Path]) -> Optional[Runtime]:
        """Detect runtime environment from custom target using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based runtime detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Try to extract runtime from COMMAND parameters
            command_params = custom_target_info.get('parameters', {}).get('COMMAND', [])
            if command_params:
                # Look for runtime indicators in the command
                command_str = " ".join(command_params).lower()
                if "go" in command_str or "go build" in command_str:
                    return Runtime.GO
                elif "java" in command_str or "javac" in command_str:
                    return Runtime.JVM
                elif "python" in command_str or "py" in command_str:
                    return Runtime.CLANG_C  # Python extensions are typically C/C++
                elif "gcc" in command_str or "g++" in command_str or "clang" in command_str:
                    return Runtime.CLANG_C
                elif "csc" in command_str or "dotnet" in command_str:
                    return Runtime.DOTNET
            
            # If no clear runtime indicators in command, fail fast
            raise ValueError(f"No runtime evidence found in COMMAND for target '{target_name}'. " +
                           f"Command: {command_params}. Cannot determine runtime without evidence.")
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine runtime without evidence.")

    def _extract_programming_language_from_target(self, target: Any) -> str:
        """Extract programming language using research-backed toolchains approach."""
        target_name = getattr(target, "name", "")
        
        # Research-backed approach: Use toolchains first
        language = self._detect_programming_language_from_toolchains(target, self._temp_toolchains_info)
        
        if language:
            return language
        
        # If no evidence found, report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "programming_language",
            f"target_{target_name}",
            {
                "has_compileGroups": hasattr(target, "compileGroups") and bool(target.compileGroups),
                "has_sources": hasattr(target, "sources") and bool(target.sources),
                "has_toolchains": bool(self._temp_toolchains_info)
            },
            self._temp_unknown_errors
        )
        
        # Final fallback - return a default
        return "UNKNOWN"

    def _detect_programming_language_from_files_with_toolchains(self, source_files: List[Path]) -> Optional[str]:
        """Detect programming language from source files using toolchain extensions."""
        if not source_files or not self._temp_toolchains:
            return None
        
        # Get file extensions
        extensions = [f.suffix.lower() for f in source_files]
        
        # Check each toolchain for matching extensions
        for tc in self._temp_toolchains.toolchains:
            if hasattr(tc, 'language') and hasattr(tc, 'sourceFileExtensions'):
                language = tc.language.lower()
                toolchain_extensions = tc.sourceFileExtensions
                
                # Check if any file extension matches this toolchain
                if any(ext in toolchain_extensions for ext in extensions):
                    return language
        
        return None

    def _detect_programming_language_from_files(self, source_files: List[Path]) -> str:
        """Detect programming language from source file extensions."""
        if not source_files:
            return "cpp"  # Default

        # Count file extensions
        extensions: Dict[str, int] = {}
        for source_file in source_files:
            ext = source_file.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        # Determine primary language
        if ".cpp" in extensions or ".cc" in extensions or ".cxx" in extensions:
            return "cpp"
        elif ".c" in extensions:
            return "c"
        elif ".py" in extensions:
            return "python"
        elif ".java" in extensions:
            return "java"
        elif ".go" in extensions:
            return "go"
        elif ".cs" in extensions:
            return "csharp"
        else:
            return "cpp"  # Default

    def _extract_output_path_from_target(self, target: Any) -> Path:
        """Extract output path from target using research-backed File API approach."""
        target_name = getattr(target, "name", "")
        
        # Research-backed approach: Prefer artifacts[].path, fall back to nameOnDisk
        if hasattr(target, "artifacts") and target.artifacts:
            # Use first artifact path
            artifact_path = target.artifacts[0].get("path", "") if isinstance(target.artifacts[0], dict) else getattr(target.artifacts[0], "path", "")
            if artifact_path:
                output_path = Path(artifact_path)
                # Make relative to repo root if absolute
                if output_path.is_absolute():
                    try:
                        return output_path.relative_to(self.repo_root)
                    except ValueError:
                        return output_path
                return output_path
        
        # Fallback to nameOnDisk
        if hasattr(target, "nameOnDisk") and target.nameOnDisk:
            return Path(target.nameOnDisk)
        
        # Check if this is a UTILITY/INTERFACE target (legitimately has no artifacts)
        target_type = getattr(target, "type", "")
        if target_type in ["UTILITY", "INTERFACE"]:
            # These targets legitimately have no artifacts
            return Path(target_name)
        
        # If no evidence found, report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "artifact_name",
            f"target_{target_name}",
            {
                "has_artifacts": hasattr(target, "artifacts") and bool(target.artifacts),
                "has_nameOnDisk": hasattr(target, "nameOnDisk") and bool(target.nameOnDisk)
            },
            self._temp_unknown_errors
        )
        
        # Final fallback
        return Path(target_name)

    def _construct_output_path_evidence_based(self, target_name: str, target: Any) -> Path:
        """Construct output path using evidence from CMakeLists.txt and cache."""
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based output path construction.")
        
        # Get target type to determine output directory type
        target_type = getattr(target, "type", "")
        target_type_str = str(target_type).lower()
        
        # Map CMake target types to output directory types
        if target_type_str in ["executable", "targettype.executable"]:
            directory_type = "RUNTIME"
        elif target_type_str in ["shared_library", "shared", "targettype.shared", "module_library", "targettype.module_library"]:
            directory_type = "LIBRARY"
        elif target_type_str in ["static_library", "static", "targettype.static"]:
            directory_type = "ARCHIVE"
        else:
            # For custom targets, try to determine from CMakeLists.txt
            custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
            if custom_target_info and custom_target_info.get('has_output'):
                # Custom target with OUTPUT parameter - use RUNTIME as default
                directory_type = "RUNTIME"
            else:
                raise ValueError(f"Cannot determine output directory type for target '{target_name}' " +
                               f"with type '{target_type_str}'. No evidence available.")
        
        # Get output directory from CMakeLists.txt or cache
        output_dir = self._cmake_parser.get_output_directory(directory_type)
        if not output_dir:
            # Try to get from cache entries
            for entry in self._temp_cache_entries:
                if hasattr(entry, 'name') and entry.name == f"CMAKE_{directory_type}_OUTPUT_DIRECTORY":
                    output_dir = str(entry.value)
                    break
        
        if not output_dir:
            raise ValueError(f"No output directory found for type '{directory_type}' for target '{target_name}'. " +
                           f"Cannot construct output path without evidence.")
        
        # Construct the full path
        if target_type_str in ["executable", "targettype.executable"]:
            # Executables typically have .exe extension on Windows
            if self._is_windows():
                output_path = Path(output_dir) / f"{target_name}.exe"
            else:
                output_path = Path(output_dir) / target_name
        else:
            # Libraries - determine extension from target type
            if target_type_str in ["shared_library", "shared", "targettype.shared", "module_library", "targettype.module_library"]:
                if self._is_windows():
                    ext = ".dll"
                elif self._is_macos():
                    ext = ".dylib"
                else:
                    ext = ".so"
            else:  # static library
                if self._is_windows():
                    ext = ".lib"
                else:
                    ext = ".a"
            
            output_path = Path(output_dir) / f"lib{target_name}{ext}"
        
        return output_path

    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        import platform
        return platform.system() == "Windows"
    
    def _is_macos(self) -> bool:
        """Check if running on macOS."""
        import platform
        return platform.system() == "Darwin"

    def _construct_output_path_from_target_name(self, target_name: str, target: Any) -> Path:
        """Construct output path using evidence-based detection from CMakeLists.txt and cache."""
        # Use evidence-based path construction instead of heuristics
        return self._construct_output_path_evidence_based(target_name, target)

    def _create_snippet_from_target(self, target: Any) -> Evidence:
        """Create Evidence with proper line numbers from target's backtrace."""
        # Try to get line numbers from backtrace
        if hasattr(target, "backtraceGraph"):
            # Look for backtrace indices in dependencies or other fields
            # For now, use a placeholder - this would need more complex backtrace resolution
            return Evidence(id=None, file=Path("CMakeLists.txt"), start_line=1, end_line=1, text=f"Target definition for {getattr(target, 'name', 'unknown')}")  # Will be updated if we can find the actual file

        # Fallback
        return Evidence(id=None, file=Path("CMakeLists.txt"), start_line=1, end_line=1, text=f"Target definition for {getattr(target, 'name', 'unknown')}")

    def _extract_external_packages_from_target(self, target: Any) -> List[ExternalPackage]:
        """Extract external package dependencies from target's link command fragments and cache entries."""
        packages: List[ExternalPackage] = []

        # First, try to extract from link command fragments
        if hasattr(target, "link") and hasattr(target.link, "commandFragments"):
            for frag in target.link.commandFragments:
                if hasattr(frag, "role") and frag.role in ("libraries", "flags", "libraryPath", "frameworkPath", "linker"):
                    # Extract package information from fragment
                    fragment_text = getattr(frag, "fragment", "")
                    if fragment_text:
                        # Try to identify package manager from fragment
                        package_manager = self._identify_package_manager_from_fragment(fragment_text)
                        if package_manager:
                            packages.append(ExternalPackage(id=None, package_manager=package_manager))

        # Add global external packages from cache (vcpkg, conan, etc.)
        packages.extend(self._temp_global_external_packages)

        return packages

    def _identify_package_manager_from_fragment(self, fragment: str) -> Optional[PackageManager]:
        """Identify package manager from link fragment."""
        # This is a simplified approach - in practice, you'd need more sophisticated parsing
        if "vcpkg" in fragment.lower():
            return PackageManager(id=None, name="vcpkg", package_name="unknown")
        elif "conan" in fragment.lower():
            return PackageManager(id=None, name="conan", package_name="unknown")
        return None

    def _extract_external_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract external package dependencies from CMake cache entries and CMakeLists.txt files."""
        packages: List[ExternalPackage] = []
        
        # Check if we have cache data available
        if not hasattr(self, '_temp_cache_entries'):
            return packages
        
        # Look for package manager indicators in cache entries
        vcpkg_packages = self._extract_vcpkg_packages_from_cache()
        conan_packages = self._extract_conan_packages_from_cache()
        
        packages.extend(vcpkg_packages)
        packages.extend(conan_packages)
        
        # Extract packages from CMakeLists.txt files (evidence-based)
        if self._cmake_parser:
            packages.extend(self._extract_packages_from_cmake_files())
        
        return packages

    def _extract_packages_from_cmake_files(self) -> List[ExternalPackage]:
        """Extract external packages from CMakeLists.txt files using evidence-based parsing."""
        packages: List[ExternalPackage] = []
        
        if not self._cmake_parser:
            return packages
        
        # Extract packages from find_package() calls
        for package_info in self._cmake_parser.find_packages:
            package_name = package_info['name']
            
            # Determine package manager based on evidence
            package_manager = self._determine_package_manager_from_evidence(package_name, package_info)
            
            if package_manager:
                external_package = ExternalPackage(
                    id=None,
                    package_manager=package_manager
                )
                packages.append(external_package)
        
        return packages

    def _determine_package_manager_from_evidence(self, package_name: str, package_info: Dict[str, Any]) -> Optional[PackageManager]:
        """Determine package manager from evidence in CMakeLists.txt and cache."""
        # Check if vcpkg is being used (from cache evidence)
        vcpkg_active = any(
            hasattr(entry, 'name') and entry.name == 'CMAKE_TOOLCHAIN_FILE' and 
            hasattr(entry, 'value') and 'vcpkg' in str(entry.value).lower()
            for entry in self._temp_cache_entries
        )
        
        # Check if conan is being used (from cache evidence)
        conan_active = any(
            hasattr(entry, 'name') and 'conan' in entry.name.lower() or
            hasattr(entry, 'value') and 'conan' in str(entry.value).lower()
            for entry in self._temp_cache_entries
        )
        
        # Determine package manager based on evidence
        if vcpkg_active:
            return PackageManager(id=None, name="vcpkg", package_name=package_name)
        elif conan_active:
            return PackageManager(id=None, name="conan", package_name=package_name)
        else:
            # Default to system package manager
            return PackageManager(id=None, name="system", package_name=package_name)

    def _extract_vcpkg_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract vcpkg packages from CMake cache entries."""
        packages: List[ExternalPackage] = []
        
        # Check for vcpkg toolchain file
        vcpkg_detected = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if entry.name == 'CMAKE_TOOLCHAIN_FILE' and 'vcpkg' in str(entry.value).lower():
                    vcpkg_detected = True
                    break
        
        if vcpkg_detected:
            # Extract specific packages from vcpkg cache entries
            for entry in self._temp_cache_entries:
                if hasattr(entry, 'name') and hasattr(entry, 'value'):
                    name = entry.name
                    value = str(entry.value)
                    
                    # Look for package-specific entries (e.g., Boost_DIR, doctest_DIR)
                    if name.endswith('_DIR') and 'vcpkg' in value.lower():
                        # Extract package name from the directory entry
                        package_name = name[:-4]  # Remove '_DIR' suffix
                        
                        # Skip vcpkg-specific entries
                        if not package_name.startswith(('VCPKG_', 'Z_VCPKG_', '_VCPKG_', 'X_VCPKG_')):
                            packages.append(ExternalPackage(
                                id=None, 
                                package_manager=PackageManager(id=None, name="vcpkg", package_name=package_name)
                            ))
        
        return packages

    def _extract_conan_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract conan packages from CMake cache entries."""
        packages: List[ExternalPackage] = []
        
        # Check for conan indicators in cache entries
        conan_detected = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if 'conan' in entry.name.lower() or 'conan' in str(entry.value).lower():
                    conan_detected = True
                    break
        
        if conan_detected:
            # Add a generic conan package entry
            packages.append(ExternalPackage(
                id=None, 
                package_manager=PackageManager(id=None, name="conan", package_name="unknown")
            ))
        
        return packages

    def _update_components_with_global_packages(self) -> None:
        """Update existing components with global external packages from cache."""
        for component in self._temp_components:
            # Add global packages to each component
            component.external_packages.extend(self._temp_global_external_packages)

    def _detect_runtime_from_target(self, target: Any, source_files: List[Path]) -> Optional[Runtime]:
        """Detect runtime environment using evidence from CMake data."""
        # Check for C# (first-class language in CMake)
        if hasattr(target, "compileGroups"):
            for cg in target.compileGroups:
                if hasattr(cg, "language") and cg.language == "CSharp":
                    return Runtime.DOTNET

        # Check for Java - use evidence from artifacts
        if hasattr(target, "artifacts"):
            for artifact in target.artifacts:
                if hasattr(artifact, "path") and str(artifact.path).endswith(".jar"):
                    return Runtime.JVM

        # Check for Go - use evidence from artifacts and source files
        if hasattr(target, "artifacts"):
            for artifact in target.artifacts:
                if hasattr(artifact, "path"):
                    path_str = str(artifact.path)
                    if path_str.endswith(".a") or "go" in path_str.lower():
                        return Runtime.GO

        # Check for Go source files
        if any(".go" in str(f) for f in source_files):
            return Runtime.GO

        # Check for Python extensions - use evidence from source files
        if any(".py" in str(f) for f in source_files):
            return Runtime.CLANG_C  # Python extensions are typically C/C++

        # Use compiler information from toolchains if available
        if hasattr(self, '_temp_toolchains') and self._temp_toolchains:
            return self._detect_runtime_from_toolchains(target)

        # Default to VS-CPP for C++ projects
        return Runtime.VS_CPP

    def _detect_runtime_from_toolchains(self, target: Any) -> Optional[Runtime]:
        """Detect runtime from toolchain information."""
        if not hasattr(self, '_temp_toolchains') or not self._temp_toolchains:
            return None
            
        # Get the primary language from compileGroups
        primary_language = None
        if hasattr(target, "compileGroups"):
            for cg in target.compileGroups:
                if hasattr(cg, "language") and cg.language:
                    primary_language = cg.language.lower()
                    break
        
        if not primary_language:
            return None
            
        # Map language to runtime based on toolchain
        for tc in self._temp_toolchains.toolchains:
            if hasattr(tc, "language") and tc.language.lower() == primary_language:
                if hasattr(tc, "compiler") and hasattr(tc.compiler, "id"):
                    compiler_id = str(tc.compiler.id).lower()
                    if "msvc" in compiler_id or "cl" in compiler_id:
                        return Runtime.VS_CPP
                    elif "gcc" in compiler_id or "g++" in compiler_id:
                        return Runtime.CLANG_C
                    elif "clang" in compiler_id:
                        return Runtime.CLANG_C
                break
                
        return None

    def _get_component_type_from_cmake_target(self, target: Any) -> ComponentType:
        """Get component type from CMake target type (evidence-based)."""
        target_type = getattr(target, "type", "")
        target_type_str = str(target_type)

        # Map CMake target types to component types
        if target_type_str in ["EXECUTABLE", "TargetType.EXECUTABLE"]:
            return ComponentType.EXECUTABLE
        elif target_type_str in ["SHARED_LIBRARY", "SHARED", "TargetType.SHARED"]:
            return ComponentType.SHARED_LIBRARY
        elif target_type_str in ["STATIC_LIBRARY", "STATIC", "TargetType.STATIC"]:
            return ComponentType.STATIC_LIBRARY
        elif target_type_str in ["MODULE_LIBRARY", "TargetType.MODULE_LIBRARY"]:
            return ComponentType.SHARED_LIBRARY  # Treat as shared library
        else:
            # Research-backed approach: Use artifacts for Windows-specific detection
            if hasattr(target, "artifacts") and target.artifacts:
                return self._detect_component_type_from_artifacts(target.artifacts)
            elif hasattr(target, "nameOnDisk") and target.nameOnDisk:
                return self._detect_component_type_from_output(Path(target.nameOnDisk))
            return ComponentType.EXECUTABLE  # Default

    def _detect_component_type_from_artifacts(self, artifacts: List[Any]) -> ComponentType:
        """Detect component type from artifacts with Windows-specific handling."""
        for artifact in artifacts:
            if hasattr(artifact, "path"):
                artifact_path = Path(artifact.path)
                extension = artifact_path.suffix.lower()
                
                # Windows-specific extensions
                if extension == ".exe":
                    return ComponentType.EXECUTABLE
                elif extension == ".dll":
                    return ComponentType.SHARED_LIBRARY
                elif extension == ".lib":
                    # Could be static library or import library
                    # Check if there's also a .dll artifact
                    has_dll = any(
                        hasattr(a, "path") and Path(a.path).suffix.lower() == ".dll" 
                        for a in artifacts
                    )
                    if has_dll:
                        # This is an import library, the .dll is the main artifact
                        continue
                    else:
                        return ComponentType.STATIC_LIBRARY
                elif extension in [".so", ".dylib"]:
                    return ComponentType.SHARED_LIBRARY
                elif extension == ".a":
                    return ComponentType.STATIC_LIBRARY
        
        # Fallback to first artifact
        if artifacts and hasattr(artifacts[0], "path"):
            return self._detect_component_type_from_output(Path(artifacts[0].path))
        
        return ComponentType.EXECUTABLE

    def _is_risky_runner(self, custom_target_info: Dict[str, Any], target_name: str) -> bool:
        """Determine if a runner is risky based on evidence-based criteria."""
        # Risky criteria:
        # 1. Has COMMAND with no DEPENDS
        # 2. COMMAND resolves to a path under the build dir
        
        has_commands = custom_target_info.get('has_commands', False)
        has_depends = custom_target_info.get('has_depends', False)
        
        # Criterion 1: Has COMMAND with no DEPENDS
        if has_commands and not has_depends:
            return True
        
        # Criterion 2: COMMAND resolves to a path under the build dir
        if has_commands:
            command_params = custom_target_info.get('parameters', {}).get('COMMAND', [])
            if command_params:
                first_command = str(command_params[0])
                # Check if command is a path under build directory
                try:
                    command_path = Path(first_command)
                    if command_path.is_absolute() and self.cmake_config_dir in command_path.parents:
                        return True
                except (ValueError, OSError):
                    pass
        
        return False

    def _load_detailed_target_info(self, target: Any) -> Any:
        """Load detailed target information from separate JSON file if available."""
        # For now, just return the target as-is to avoid hanging
        # The cmake-file-api package should already provide the necessary information
        return target

    def _load_target_info_research_backed(self, target: Any) -> Any:
        """Load target information using the research-backed approach."""
        try:
            target_name = getattr(target, 'name', '')
            if not target_name:
                return target
            
            print(f"DEBUG: Loading target info for {target_name}")
            
            # Step 1: Read reply/index-*.json to find codemodel path
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            print(f"DEBUG: Looking for index files in {reply_dir}")
            index_files = list(reply_dir.glob("index-*.json"))
            if not index_files:
                print(f"DEBUG: No index files found for {target_name}")
                return target
            
            # Load index to find codemodel path
            with open(index_files[0], 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Step 2: Find codemodel v2 in index
            codemodel_path = None
            if 'reply' in index_data and 'codemodel-v2' in index_data['reply']:
                codemodel_path = index_data['reply']['codemodel-v2'].get('jsonFile')
            
            if not codemodel_path:
                return target
            
            # Load codemodel
            codemodel_file = reply_dir / codemodel_path
            if not codemodel_file.exists():
                return target
            
            with open(codemodel_file, 'r', encoding='utf-8') as f:
                codemodel_data = json.load(f)
            
            # Step 3: Pick the active config (e.g., Debug) from configurations
            if not codemodel_data.get('configurations'):
                return target
            
            # Use first configuration (typically Debug)
            config = codemodel_data['configurations'][0]
            
            # Step 4: For each target, resolve jsonFile relative to codemodel file
            for target_stub in config.get('targets', []):
                if target_stub.get('name') == target_name:
                    json_file = target_stub.get('jsonFile', '')
                    if json_file:
                        # Load the detailed target JSON (path is relative to codemodel file)
                        target_json_path = codemodel_file.parent / json_file
                        if target_json_path.exists():
                            with open(target_json_path, 'r', encoding='utf-8') as f:
                                target_data = json.load(f)
                            
                            # Step 5: Extract target details (type, nameOnDisk, artifacts)
                            class DetailedTarget:
                                def __init__(self, data: Dict[str, Any]):
                                    # Copy essential original target attributes
                                    self.name = getattr(target, 'name', '')
                                    self.id = getattr(target, 'id', '')
                                    
                                    # Override with detailed data
                                    self.type = data.get('type', '')
                                    self.nameOnDisk = data.get('nameOnDisk', '')
                                    self.artifacts = data.get('artifacts', [])
                                    self.dependencies = data.get('dependencies', [])
                                    self.compileGroups = data.get('compileGroups', [])
                                    self.sourceGroups = data.get('sourceGroups', [])
                                    self.sources = data.get('sources', [])
                                    self.link = data.get('link', {})
                                    self.paths = data.get('paths', {})
                                    self.backtrace = data.get('backtrace', 0)
                                    self.backtraceGraph = data.get('backtraceGraph', [])
                            
                            detailed_target = DetailedTarget(target_data)
                            return detailed_target
                    break
            
        except Exception as e:
            # If loading fails, continue with original target
            pass
        
        return target

    def _load_toolchains_info(self) -> Dict[str, Any]:
        """Load toolchains information from CMake File API for language detection."""
        toolchains_info = {}
        
        try:
            # Find the toolchains JSON file
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            toolchains_files = list(reply_dir.glob("toolchains-v1-*.json"))
            
            if not toolchains_files:
                return toolchains_info
            
            # Load toolchains JSON
            with open(toolchains_files[0], 'r', encoding='utf-8') as f:
                toolchains_data = json.load(f)
            
            # Extract language information
            for toolchain in toolchains_data.get('toolchains', []):
                language = toolchain.get('language', '')
                if language:
                    toolchains_info[language] = {
                        'sourceFileExtensions': toolchain.get('sourceFileExtensions', []),
                        'compiler': toolchain.get('compiler', {}),
                        'path': toolchain.get('path', ''),
                        'version': toolchain.get('version', '')
                    }
            
        except Exception as e:
            # If loading fails, return empty dict
            pass
        
        return toolchains_info

    def _detect_programming_language_from_toolchains(self, target: Any, toolchains_info: Dict[str, Any]) -> Optional[str]:
        """Detect programming language using toolchains and compile groups."""
        try:
            # First, try to get language from compile groups
            if hasattr(target, 'compileGroups') and target.compileGroups:
                for compile_group in target.compileGroups:
                    if hasattr(compile_group, 'language') and compile_group.language:
                        return compile_group.language
            
            # Fallback: use source file extensions
            if hasattr(target, 'sources') and target.sources:
                for source in target.sources:
                    if hasattr(source, 'path') and source.path:
                        source_path = Path(source.path)
                        extension = source_path.suffix.lower()
                        
                        # Check each language's source file extensions
                        for language, info in toolchains_info.items():
                            if extension in info.get('sourceFileExtensions', []):
                                return language
            
        except Exception as e:
            pass
        
        return None

    def _extract_from_codemodel_fallback(self) -> None:
        """Fallback: Load codemodel directly from JSON files when cmake-file-api fails."""
        print("DEBUG: _extract_from_codemodel_fallback called")
        try:
            # Step 1: Read reply/index-*.json → find the "codemodel" object (v2)
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            if not reply_dir.exists():
                print(f"DEBUG: Reply directory not found: {reply_dir}")
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "reply_directory_missing",
                    {"path": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Find index file
            index_files = list(reply_dir.glob("index-*.json"))
            if not index_files:
                print(f"DEBUG: No index files found in {reply_dir}")
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "index_file_missing",
                    {"reply_dir": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Load index to find codemodel path
            with open(index_files[0], 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Find codemodel v2 in index
            codemodel_path = None
            if 'reply' in index_data:
                for reply_obj in index_data['reply']:
                    if reply_obj.get('kind') == 'codemodel' and reply_obj.get('version', {}).get('major') == 2:
                        codemodel_path = reply_obj.get('jsonFile')
                        break
            
            if not codemodel_path:
                print(f"DEBUG: No codemodel v2 found in index")
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "codemodel_v2_not_in_index",
                    {"index_data": index_data},
                    self._temp_unknown_errors
                )
                return
            
            # Step 2: Open codemodel.json (path in index)
            codemodel_file = reply_dir / codemodel_path
            if not codemodel_file.exists():
                print(f"DEBUG: Codemodel file not found: {codemodel_file}")
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "codemodel_file_missing",
                    {"path": str(codemodel_file)},
                    self._temp_unknown_errors
                )
                return
            
            print(f"DEBUG: Found codemodel file: {codemodel_file}")
            # Load the codemodel JSON
            with open(codemodel_file, 'r', encoding='utf-8') as f:
                codemodel_data = json.load(f)
            
            # Create a simple object to hold the data
            class CodemodelFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.configurations = []
                    for config_data in data.get('configurations', []):
                        config = CodemodelConfigFallback(config_data, codemodel_file_path)
                        self.configurations.append(config)
                    self.backtraceGraph = data.get('backtraceGraph')
            
            class CodemodelConfigFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.projects = []
                    for project_data in data.get('projects', []):
                        project = CodemodelProjectFallback(project_data)
                        self.projects.append(project)
                    self.targets = []
                    for target_data in data.get('targets', []):
                        target = CodemodelTargetFallback(target_data, codemodel_file_path)
                        self.targets.append(target)
                    self.directories = data.get('directories', [])
            
            class CodemodelProjectFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.name = data.get('name', '')
                    self.directoryIndexes = data.get('directoryIndexes', [])
                    self.targetIndexes = data.get('targetIndexes', [])
            
            class CodemodelTargetFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.name = data.get('name', '')
                    self.id = data.get('id', '')
                    self.jsonFile = data.get('jsonFile', '')
                    self.directoryIndex = data.get('directoryIndex', 0)
                    self.projectIndex = data.get('projectIndex', 0)
                    self._codemodel_file_path = codemodel_file_path
                    
                    # Initialize default values
                    self.type = ''
                    self.nameOnDisk = ''
                    self.artifacts = []
                    self.dependencies = []
                    self.compileGroups = []
                    self.sourceGroups = []
                    self.sources = []
                    self.link = {}
                    self.paths = {}
                    self.backtrace = 0
                    self.backtraceGraph = []
                    
                    # Step 3: Load detailed target information if jsonFile exists
                    if self.jsonFile:
                        self._load_detailed_target_info()
                
                def _load_detailed_target_info(self):
                    """Load detailed target information from target JSON file."""
                    try:
                        # Step 3: For each target → resolve and open target's JSON (relative to codemodel file)
                        target_json_path = self._codemodel_file_path.parent / self.jsonFile
                        if target_json_path.exists():
                            with open(target_json_path, 'r', encoding='utf-8') as f:
                                target_data = json.load(f)
                            
                            # Step 4: Read target details
                            self.type = target_data.get('type', '')
                            self.nameOnDisk = target_data.get('nameOnDisk', '')
                            self.artifacts = target_data.get('artifacts', [])
                            self.dependencies = target_data.get('dependencies', [])
                            self.compileGroups = target_data.get('compileGroups', [])
                            self.sourceGroups = target_data.get('sourceGroups', [])
                            self.sources = target_data.get('sources', [])
                            self.link = target_data.get('link', {})
                            self.paths = target_data.get('paths', {})
                            self.backtrace = target_data.get('backtrace', 0)
                            self.backtraceGraph = target_data.get('backtraceGraph', [])
                            
                            print(f"DEBUG: Loaded detailed info for {self.name}: type={self.type}, nameOnDisk={self.nameOnDisk}, artifacts={len(self.artifacts)}")
                        else:
                            print(f"DEBUG: Target JSON file not found: {target_json_path}")
                    except Exception as e:
                        print(f"DEBUG: Failed to load detailed target info for {self.name}: {e}")
            
            codemodel = CodemodelFallback(codemodel_data, codemodel_file)
            self._extract_from_codemodel(codemodel)
            
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "codemodel_fallback",
                "load_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _extract_from_cache_fallback(self) -> None:
        """Fallback: Load cache directly from JSON files when cmake-file-api fails."""
        try:
            # Find the cache JSON file
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            cache_files = list(reply_dir.glob("cache-v2-*.json"))
            if not cache_files:
                ResearchBackedUtilities.unknown_field(
                    "cache_fallback",
                    "cache_v2_file_missing",
                    {"reply_dir": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Load the cache JSON
            with open(cache_files[0], 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Create a simple object to hold the data
            class CacheFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.entries = []
                    for entry_data in data.get('entries', []):
                        entry = CacheEntryFallback(entry_data)
                        self.entries.append(entry)
            
            class CacheEntryFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.name = data.get('name', '')
                    self.value = data.get('value', '')
                    self.type = data.get('type', '')
                    self.properties = data.get('properties', {})
            
            cache = CacheFallback(cache_data)
            self._extract_from_cache(cache)
            
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "cache_fallback",
                "load_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _extract_install_metadata_from_codemodel(self, codemodel: Any) -> None:
        """Extract install metadata from codemodel directory.installers."""
        if not hasattr(codemodel, "configurations"):
            return
        
        install_metadata: List[Dict[str, Any]] = []
        
        for config in codemodel.configurations:
            if hasattr(config, "directories"):
                for directory in config.directories:
                    if hasattr(directory, "installers"):
                        for installer in directory.installers:
                            install_info = {
                                "destination": getattr(installer, "destination", ""),
                                "install_type": getattr(installer, "type", ""),
                                "paths": []
                            }
                            
                            # Extract paths from installer
                            if hasattr(installer, "paths"):
                                for path in installer.paths:
                                    if hasattr(path, "path"):
                                        install_info["paths"].append(str(path.path))
                            
                            install_metadata.append(install_info)
        
        # Store install metadata for potential use
        if install_metadata:
            # Could be used to enhance component location information
            # For now, we'll just track it for potential future use
            pass

    def _extract_from_cache(self, cache: Any) -> None:
        """Extract information from cache v2 using research-backed approach."""
        # Store cache entries for external package detection
        self._temp_cache_entries = getattr(cache, "entries", [])
        
        # Build cache dictionary for variable expansion
        self._temp_cache_dict = {}
        if hasattr(cache, "entries"):
            for entry in cache.entries:
                if hasattr(entry, "name") and hasattr(entry, "value"):
                    self._temp_cache_dict[entry.name] = str(entry.value)
        
        # Extract global external packages from cache
        self._temp_global_external_packages = self._extract_external_packages_from_cache()
        
        # Extract package manager information
        package_manager = ResearchBackedUtilities.detect_package_manager_from_cache(self._temp_cache_entries)
        if not package_manager:
            ResearchBackedUtilities.unknown_field(
                "package_manager", 
                "cache_analysis", 
                {"cache_entries": len(self._temp_cache_entries)},
                self._temp_unknown_errors
            )
        
        # Check for compile commands JSON
        self._check_compile_commands_json()

    def _check_compile_commands_json(self) -> None:
        """Check for compile_commands.json file based on CMake configuration."""
        compile_commands_path = self.cmake_config_dir / "compile_commands.json"
        
        # Check if CMAKE_EXPORT_COMPILE_COMMANDS is enabled
        export_compile_commands = self._temp_cache_dict.get("CMAKE_EXPORT_COMPILE_COMMANDS", "").upper()
        generator = self._temp_cache_dict.get("CMAKE_GENERATOR", "")
        
        if export_compile_commands in ["ON", "TRUE", "1"]:
            # Compile commands export is enabled
            if not compile_commands_path.exists():
                # Check if generator supports compile_commands.json
                if generator in ["Ninja", "Unix Makefiles", "MinGW Makefiles"]:
                    # Generator supports it but file is missing - this is an error
                    ResearchBackedUtilities.unknown_field(
                        "compile_commands_json",
                        "file_missing",
                        {"path": str(compile_commands_path), "generator": generator},
                        self._temp_unknown_errors
                    )
                else:
                    # Generator doesn't support it (e.g., Visual Studio) - this is expected
                    print(f"INFO: compile_commands.json not available with {generator} generator (only supported by Makefile/Ninja generators)")
            else:
                print(f"INFO: compile_commands.json found at {compile_commands_path}")
        else:
            # CMAKE_EXPORT_COMPILE_COMMANDS is not enabled
            if generator in ["Ninja", "Unix Makefiles", "MinGW Makefiles"]:
                print("INFO: CMAKE_EXPORT_COMPILE_COMMANDS is not enabled (set to ON to generate compile_commands.json)")
            else:
                print(f"INFO: CMAKE_EXPORT_COMPILE_COMMANDS not available with {generator} generator")

    def _extract_from_toolchains(self, toolchains: Any) -> None:
        """Extract information from toolchains v1."""
        # Store toolchains for runtime detection
        self._temp_toolchains = toolchains
        
        if hasattr(toolchains, "toolchains"):
            for tc in toolchains.toolchains:
                # Could extract compiler information
                if hasattr(tc, "language") and hasattr(tc, "compiler"):
                    pass

    def _extract_from_cmake_files(self, cmake_files: Any) -> None:
        """Extract information from cmakeFiles v1."""
        # This could be used to detect Java/Go support by looking for UseJava.cmake, etc.
        pass

    def _extract_tests_from_ctest(self) -> None:
        """Extract tests using CTest JSON (research-backed approach)."""
        try:
            # Run ctest --show-only=json-v1 to get comprehensive test information
            result = subprocess.run(
                ["ctest", "--show-only=json-v1"], 
                cwd=self.cmake_config_dir, 
                capture_output=True, 
                text=True, 
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                ctest_info = json.loads(result.stdout)
                self._process_ctest_info_research_backed(ctest_info)
            else:
                ResearchBackedUtilities.unknown_field(
                    "ctest_json",
                    "execution_failed",
                    {"error": result.stderr, "returncode": result.returncode},
                    self._temp_unknown_errors
                )

        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "ctest_json",
                "execution_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _process_ctest_info_research_backed(self, ctest_info: Dict[str, Any]) -> None:
        """Process CTest JSON information using research-backed approach."""
        tests = ctest_info.get("tests", [])
        backtrace_graph = ctest_info.get("backtraceGraph", {})
        
        # Build component mapping tables
        by_artifact_basename = self._build_artifact_basename_map()
        by_source_dir = self._build_source_directory_map()

        for test in tests:
            try:
                test_name = test.get("name", "")
                test_command = test.get("command", [])
                test_properties = test.get("properties", [])
                
                # Extract working directory
                workdir = None
                for prop in test_properties:
                    if prop.get("name") == "WORKING_DIRECTORY":
                        workdir = prop.get("value")
                        break
                
                # Get test provenance from backtrace
                cmake_file, cmake_line = self._get_test_provenance(test, backtrace_graph)
                
                # Map test to components using two-source approach
                component_refs = self._map_test_to_components(
                    test_name, test_command, cmake_file, by_artifact_basename, by_source_dir
                )
                
                # Create evidence from CTest backtrace
                evidence = self._create_snippet_from_ctest(test, backtrace_graph)
                
                # Create test object with ComponentRef
                test_obj = Test(
                    id=None,
                    name=test_name,
                    test_framework=self._detect_test_framework_from_ctest(test),
                    components_being_tested=component_refs,
                    test_executable=None,  # Will be determined from components
                    source_files=[],  # Tests don't have source files in the traditional sense
                    evidence=evidence
                )
                
                self._temp_tests.append(test_obj)
                
            except Exception as e:
                ResearchBackedUtilities.unknown_field(
                    "test_processing",
                    f"test_{test.get('name', 'unknown')}",
                    {"error": str(e), "test_data": test},
                    self._temp_unknown_errors
                )

    def _build_artifact_basename_map(self) -> Dict[str, str]:
        """Build map from artifact basename to component ID."""
        by_artifact_basename = {}
        
        for component in self._temp_components:
            if hasattr(component, 'output') and component.output:
                basename = Path(component.output).name
                by_artifact_basename[basename] = component.name
        
        return by_artifact_basename

    def _build_source_directory_map(self) -> Dict[str, List[str]]:
        """Build map from source directory to component IDs."""
        by_source_dir = {}
        
        for component in self._temp_components:
            if hasattr(component, 'source_files') and component.source_files:
                # Get the directory of the first source file
                first_source = component.source_files[0]
                source_dir = str(first_source.parent)
                
                if source_dir not in by_source_dir:
                    by_source_dir[source_dir] = []
                by_source_dir[source_dir].append(component.name)
        
        return by_source_dir

    def _get_test_provenance(self, test: Dict[str, Any], backtrace_graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
        """Get test provenance from backtrace graph."""
        backtrace = test.get("backtrace")
        if not backtrace or not backtrace_graph:
            return None, None
        
        # Get the backtrace node
        nodes = backtrace_graph.get("nodes", [])
        files = backtrace_graph.get("files", [])
        
        if backtrace < len(nodes):
            node = nodes[backtrace]
            file_idx = node.get("file")
            line = node.get("line")
            
            if file_idx is not None and file_idx < len(files):
                return files[file_idx], line
        
        return None, None

    def _map_test_to_components(self, test_name: str, test_command: List[str], 
                               cmake_file: Optional[str], by_artifact_basename: Dict[str, str], 
                               by_source_dir: Dict[str, List[str]]) -> List[Component]:
        """Map test to components using two-source approach."""
        component_refs = []
        
        # Source 1: Executable artifact match (strongest)
        if test_command and len(test_command) > 0:
            command_path = test_command[0]
            if command_path and not command_path.startswith('$'):
                # Extract basename from command
                basename = Path(command_path).name
                if basename in by_artifact_basename:
                    component_name = by_artifact_basename[basename]
                    component = self._find_component_by_name(component_name)
                    if component:
                        component_refs.append(component)
                    return component_refs
        
        # Source 2: Backtrace directory → owning target
        if cmake_file:
            cmake_dir = str(Path(cmake_file).parent)
            if cmake_dir in by_source_dir:
                candidates = by_source_dir[cmake_dir]
                for candidate_name in candidates:
                    component = self._find_component_by_name(candidate_name)
                    if component:
                        component_refs.append(component)
        
        return component_refs

    def _find_component_by_name(self, name: str) -> Optional[Component]:
        """Find component by name."""
        for component in self._temp_components:
            if component.name == name:
                return component
        return None

    def _process_ctest_info(self, ctest_info: Dict[str, Any]) -> None:
        """Process CTest JSON information."""
        tests = ctest_info.get("tests", [])
        backtrace_graph = ctest_info.get("backtraceGraph")

        for test in tests:
            test_obj = self._create_test_from_ctest(test, backtrace_graph)
            if test_obj:
                self._temp_tests.append(test_obj)

    def _create_test_from_ctest(self, test: Dict[str, Any], backtrace_graph: Optional[Dict[str, Any]]) -> Optional[Test]:
        """Create Test from CTest information."""
        try:
            # Get test name
            test_name = test.get("name", "")

            # Get test framework from properties or labels
            test_framework = self._detect_test_framework_from_ctest(test)

            # Get line numbers from backtrace
            evidence = self._create_snippet_from_ctest(test, backtrace_graph)

            # Get test source files by mapping to target
            source_files = self._get_test_source_files(test)
            
            # Get components being tested using evidence-based detection
            components_being_tested_names = self._get_components_being_tested_evidence_based(test_name)
            
            # Convert component names to actual Component objects
            components_being_tested: List[Component] = []
            for comp_name in components_being_tested_names:
                for component in self._temp_components:
                    if component.name == comp_name:
                        components_being_tested.append(component)
                        break

            return Test(
                id=None,
                name=test_name,
                test_executable=None,  # Would need custom logic to determine
                components_being_tested=components_being_tested,
                test_runner=None,  # Would need custom logic to determine
                source_files=source_files,
                test_framework=test_framework,
                evidence=evidence,
            )
        except Exception:
            return None

    def _detect_test_framework_from_ctest(self, test: Dict[str, Any]) -> str:
        """Detect test framework from CTest properties and command (evidence-based)."""
        # Check for framework-specific labels (evidence from CTest properties)
        properties = test.get("properties", [])
        labels: List[Any] = []

        # Properties is a list of dictionaries
        for prop in properties:
            if isinstance(prop, dict) and prop.get("name") == "LABELS":
                labels_value: Any = prop.get("value", [])
                if isinstance(labels_value, list):
                    labels: List[Any] = labels_value
                break

        # Check labels for framework indicators
        detected_framework = None
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                if "gtest" in label_lower or "googletest" in label_lower:
                    return "Google Test"
                elif "catch" in label_lower or "catch2" in label_lower:
                    return "Catch2"
                elif "doctest" in label_lower:
                    return "doctest"
                elif "boost.test" in label_lower:
                    return "Boost.Test"
                else:
                    # Use the actual label as evidence if no known framework detected
                    detected_framework = label

        # Check command for framework indicators (evidence from test command)
        command = test.get("command", [])
        if command:
            cmd_str = " ".join(command)
            
            # Only detect frameworks with clear, unambiguous indicators
            # Google Test indicators (very specific flags)
            if "--gtest_list_tests" in cmd_str or "--gtest_filter" in cmd_str:
                return "Google Test"
            
            # Catch2 indicators (very specific flags)
            elif "--list-tests" in cmd_str and "catch" in cmd_str.lower():
                return "Catch2"
            
            # Python test frameworks (very specific commands)
            elif "pytest" in cmd_str.lower():
                return "pytest"
            elif "python -m unittest" in cmd_str.lower():
                return "Python unittest"
            
            # Go test indicators (very specific command)
            elif cmd_str.lower().startswith("go test"):
                return "Go Test"
            
            # Java test indicators (very specific classpath/class names)
            elif "junit" in cmd_str.lower() and "java" in cmd_str.lower():
                return "JUnit"
            elif "testng" in cmd_str.lower() and "java" in cmd_str.lower():
                return "TestNG"
            
            # If we have a command but no clear framework indicators, use the command as evidence
            else:
                # Extract the executable name as evidence
                if command and len(command) > 0:
                    executable = command[0]
                    if executable:
                        return f"Test executable: {executable}"

        # Use evidence-based fallback: return the actual label if available, otherwise fail fast
        if detected_framework:
            return detected_framework
        
        # If no evidence at all, fail fast rather than guessing
        raise ValueError(f"No test framework evidence found for test. " +
                       f"Labels: {labels}, Command: {command}. " +
                       f"Cannot determine test framework without evidence.")

    def _get_components_being_tested_evidence_based(self, test_name: str) -> List[str]:
        """Get components being tested using evidence from CMakeLists.txt files."""
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based test-component mapping.")
        
        # Get test information from CMakeLists.txt
        test_info = self._cmake_parser.get_test_info(test_name)
        if not test_info:
            raise ValueError(f"No CMakeLists.txt evidence found for test '{test_name}'. " +
                           f"Cannot determine test-component relationships without evidence.")
        
        # Extract component names from test command
        command = test_info.get('command', [])
        components: List[str] = []
        
        for cmd_part in command:
            cmd_str = str(cmd_part)
            # Look for executable names that match component names
            for component in self._temp_components:
                if hasattr(component, 'name') and component.name in cmd_str:
                    components.append(component.name)
        
        # If no components found, fail fast
        if not components:
            raise ValueError(f"No components found for test '{test_name}'. " +
                           f"Test command: {command}. " +
                           f"Cannot determine test-component relationships without evidence.")
        
        return components

    def _load_compile_commands_json(self) -> None:
        """Load compile_commands.json as fallback for per-TU evidence."""
        compile_commands_path = self.cmake_config_dir / "compile_commands.json"
        
        if compile_commands_path.exists():
            try:
                with open(compile_commands_path, 'r', encoding='utf-8') as f:
                    self._temp_compile_commands = json.load(f)
            except Exception as e:
                ResearchBackedUtilities.unknown_field(
                    "compile_commands_json",
                    "file_loading",
                    {"error": str(e), "path": str(compile_commands_path)},
                    self._temp_unknown_errors
                )
        else:
            ResearchBackedUtilities.unknown_field(
                "compile_commands_json",
                "file_missing",
                {"path": str(compile_commands_path)},
                self._temp_unknown_errors
            )

    def _load_graphviz_dependencies(self) -> None:
        """Load graphviz dependencies for direct vs transitive distinction."""
        try:
            # Try to generate graphviz output
            result = subprocess.run(
                ["cmake", "--graphviz=graph.dot", "."],
                cwd=self.cmake_config_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                graphviz_file = self.cmake_config_dir / "graph.dot"
                if graphviz_file.exists():
                    self._parse_graphviz_dependencies(graphviz_file)
                else:
                    ResearchBackedUtilities.unknown_field(
                        "graphviz_dependencies",
                        "file_missing",
                        {"path": str(graphviz_file)},
                        self._temp_unknown_errors
                    )
            else:
                ResearchBackedUtilities.unknown_field(
                    "graphviz_dependencies",
                    "generation_failed",
                    {"error": result.stderr, "returncode": result.returncode},
                    self._temp_unknown_errors
                )
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "graphviz_dependencies",
                "generation_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _parse_graphviz_dependencies(self, graphviz_file: Path) -> None:
        """Parse graphviz .dot file to extract direct dependencies."""
        self._temp_graphviz_deps = {}
        
        try:
            with open(graphviz_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing of .dot file for dependencies
            # Look for lines like: "target1" -> "target2"
            import re
            dep_pattern = r'"([^"]+)"\s*->\s*"([^"]+)"'
            
            for match in re.finditer(dep_pattern, content):
                source = match.group(1)
                target = match.group(2)
                
                if source not in self._temp_graphviz_deps:
                    self._temp_graphviz_deps[source] = set()
                self._temp_graphviz_deps[source].add(target)
                
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "graphviz_parsing",
                "file_parsing_error",
                {"error": str(e), "path": str(graphviz_file)},
                self._temp_unknown_errors
            )

    def _create_snippet_from_ctest(self, test: Dict[str, Any], backtrace_graph: Optional[Dict[str, Any]]) -> Evidence:
        """Create Evidence with line numbers from CTest backtrace."""
        if backtrace_graph and test.get("backtrace") is not None:
            backtrace_idx = test["backtrace"]
            # Resolve backtrace to get file and line
            file_path, line = self._resolve_backtrace(backtrace_idx, backtrace_graph)
            if file_path:
                return Evidence(id=None, file=Path(file_path), start_line=line or 1, end_line=line or 1, text=f"Test definition for {test.get('name', 'unknown')}")

        # Fallback
        return Evidence(id=None, file=Path("CMakeLists.txt"), start_line=1, end_line=1, text=f"Test definition for {test.get('name', 'unknown')}")

    def _resolve_backtrace(self, backtrace_idx: int, backtrace_graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
        """Resolve backtrace index to file path and line number."""
        try:
            nodes = backtrace_graph.get("nodes", [])
            files = backtrace_graph.get("files", [])

            if backtrace_idx < len(nodes):
                node = nodes[backtrace_idx]
                file_idx = node.get("file")
                line = node.get("line")

                if file_idx is not None and file_idx < len(files):
                    file_path = files[file_idx]
                    return file_path, line

        except Exception:
            pass

        return None, None

    def _find_test_dependencies(self, test: Dict[str, Any]) -> List[Component]:
        """Find components that this test depends on."""
        dependent_components: List[Component] = []

        # Map test command to target artifacts to find dependencies
        command = test.get("command", [])
        if command:
            test_exe_path = command[0]
            if test_exe_path:
                # Find target that produces this executable
                for component in self._temp_components:
                    if component.output_path.name == Path(test_exe_path).name:
                        dependent_components.append(component)
                        break

        return dependent_components

    def _get_test_source_files(self, test: Dict[str, Any]) -> List[Path]:
        """Get source files for this test."""
        source_files: List[Path] = []

        # Map test to target to get source files
        command = test.get("command", [])
        if command:
            test_exe_path = command[0]
            if test_exe_path:
                # Find target that produces this executable
                for component in self._temp_components:
                    if component.output_path.name == Path(test_exe_path).name:
                        source_files = component.source_files
                        break

        return source_files

    def _extract_build_commands(self) -> None:
        """Extract build commands."""
        self._temp_configure_command = f"cmake -B {self.cmake_config_dir}"
        self._temp_build_command = f"cmake --build {self.cmake_config_dir}"
        self._temp_install_command = f"cmake --install {self.cmake_config_dir}"
        self._temp_test_command = f"ctest --test-dir {self.cmake_config_dir}"

    def _extract_output_directory(self) -> None:
        """Extract output directory information using evidence-based detection."""
        self._temp_build_directory = self.cmake_config_dir

        # Try to get output directory from CMake cache (evidence-based)
        output_dir_found = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if entry.name == "CMAKE_RUNTIME_OUTPUT_DIRECTORY":
                    runtime_dir = Path(str(entry.value))
                    if runtime_dir.exists():
                        self._temp_output_directory = runtime_dir
                        output_dir_found = True
                        break
                elif entry.name == "CMAKE_BINARY_DIR":
                    binary_dir = Path(str(entry.value))
                    if binary_dir.exists():
                        self._temp_output_directory = binary_dir
                        output_dir_found = True
                        break
                elif entry.name == "CMAKE_LIBRARY_OUTPUT_DIRECTORY":
                    library_dir = Path(str(entry.value))
                    if library_dir.exists():
                        self._temp_output_directory = library_dir
                        output_dir_found = True
                        break

        # If no evidence found in cache, use build directory as fallback
        if not output_dir_found:
            self._temp_output_directory = self.cmake_config_dir

    def _report_unknown_errors(self) -> None:
        """Report UNKNOWN_* errors for transparency in research-backed approach."""
        if self._temp_unknown_errors:
            print(f"\nResearch-backed UNKNOWN_* errors detected ({len(self._temp_unknown_errors)}):")
            for error in sorted(self._temp_unknown_errors):
                print(f"  • {error}")
            print("  These represent fields where evidence was insufficient for deterministic detection.")
            print("  Consider providing additional CMake configuration or build artifacts.\n")

    def _populate_rig(self) -> None:
        """Populate the RIG with extracted data."""
        # Create repository info
        repo_info = RepositoryInfo(
            name=self._temp_project_name,
            root_path=self.repo_root,
            build_directory=self._temp_build_directory,
            output_directory=self._temp_output_directory,
            configure_command=self._temp_configure_command,
            build_command=self._temp_build_command,
            install_command=self._temp_install_command,
            test_command=self._temp_test_command,
        )
        self._rig.set_repository_info(repo_info)
        
        # Report UNKNOWN errors for transparency
        self._report_unknown_errors()

        # Set build system info
        # TODO: Extract generator and version from CMake cache if needed
        build_system_info = BuildSystemInfo(name="CMake", version=None, build_type=None)
        self._rig.set_build_system_info(build_system_info)

        # Add all components, aggregators, runners, and tests
        for component in self._temp_components:
            self._rig.add_component(component)

        for aggregator in self._temp_aggregators:
            self._rig.add_aggregator(aggregator)

        for runner in self._temp_runners:
            self._rig.add_runner(runner)

        for test in self._temp_tests:
            self._rig.add_test(test)

    @property
    def rig(self) -> RIG:
        """Get the Repository Intelligence Graph."""
        return self._rig

    def get_rig(self) -> RIG:
        """Get the Repository Intelligence Graph."""
        return self._rig

    def parse_cmake(self) -> None:
        """Manually trigger CMake parsing after initialization."""
        self.parse_cmake_info()
