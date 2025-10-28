import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from pydantic import BaseModel, Field

from core.schemas import Evidence, Component, Aggregator, Runner, TestDefinition, NodeType


# Pydantic models for CTest JSON structure

class CTestBacktraceNode(BaseModel):
    """Represents a node in the backtrace graph."""
    file: Optional[int] = None
    line: Optional[int] = None
    command: Optional[int] = None
    parent: Optional[int] = None


class CTestBacktraceGraph(BaseModel):
    """Backtrace graph containing commands, files, and nodes."""
    commands: List[str]
    files: List[str]
    nodes: List[CTestBacktraceNode]


class CTestProperty(BaseModel):
    """Test property (name-value pair)."""
    name: str
    value: str


class CTestInfo(BaseModel):
    """Individual test information."""
    name: str
    config: str
    backtrace: int
    properties: List[CTestProperty] = Field(default_factory=list)


class CTestVersion(BaseModel):
    """CTest version information."""
    major: int
    minor: int


class CTestData(BaseModel):
    """Root CTest JSON structure."""
    kind: str
    backtraceGraph: CTestBacktraceGraph
    tests: List[CTestInfo]
    version: CTestVersion


class CTestWrapper:
    """Wrapper for CTest information extraction."""

    def __init__(
        self,
        repo_root: Path,
        build_dir_name: str,
        configuration: str,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]]
    ):
        """Initialize CTest wrapper.

        Args:
            repo_root: Repository root path
            build_dir_name: Build directory name (relative to repo root)
            configuration: Build configuration (Debug, Release, etc.)
            findings: Reference to findings dict for caching created test definitions
        """
        self._repo_root = repo_root
        self._build_dir_name = build_dir_name
        self._configuration = configuration
        self._findings = findings
        self._ctest_data: Optional[CTestData] = None

    def _run_ctest(self) -> dict:
        """Run ctest command and return parsed JSON.

        Returns:
            Parsed JSON as dictionary

        Raises:
            subprocess.CalledProcessError: If ctest command fails
            json.JSONDecodeError: If output is not valid JSON
        """
        cmd = [
            "ctest",
            "-N",
            "--show-only=json-v1",
            f"--test-dir",
            self._build_dir_name,
            "-C",
            self._configuration
        ]

        result = subprocess.run(
            cmd,
            cwd=self._repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        return json.loads(result.stdout)

    def get_all_tests(self) -> List[CTestInfo]:
        """Get all CTest tests.

        Returns:
            List of CTestInfo objects
        """
        if self._ctest_data is None:
            json_data = self._run_ctest()
            self._ctest_data = CTestData(**json_data)

        return self._ctest_data.tests

    def extract_evidence(self, test: CTestInfo) -> Evidence:
        """Extract evidence from test backtrace.

        Args:
            test: CTest test information

        Returns:
            Evidence object with file:line information
        """
        if self._ctest_data is None:
            json_data = self._run_ctest()
            self._ctest_data = CTestData(**json_data)

        backtrace_graph = self._ctest_data.backtraceGraph
        backtrace_node = backtrace_graph.nodes[test.backtrace]

        file_idx = backtrace_node.file
        line_num = backtrace_node.line

        if file_idx is None or line_num is None:
            # Fallback to parent node if current node doesn't have file/line
            if backtrace_node.parent is not None:
                parent_node = backtrace_graph.nodes[backtrace_node.parent]
                file_idx = parent_node.file
                line_num = parent_node.line

        if file_idx is None or line_num is None:
            raise ValueError(f"Could not extract file/line from backtrace for test {test.name}")

        file_path = Path(backtrace_graph.files[file_idx])

        return Evidence(line=[f'{file_path}:{line_num}'], call_stack=None)

    def parse_add_test_command(self, cmake_file: Path, line_num: int) -> Dict[str, Any]:
        """Parse add_test command from CMake file.

        Args:
            cmake_file: Path to CMakeLists.txt file
            line_num: Line number where add_test is called

        Returns:
            Dictionary with parsed information:
            - 'name': Test name (if NAME keyword used)
            - 'command': Command/executable to run
            - 'args': List of command arguments

        Raises:
            FileNotFoundError: If cmake_file doesn't exist
            ValueError: If add_test command cannot be parsed
        """
        with open(cmake_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find add_test starting at line_num (1-indexed)
        if line_num < 1 or line_num > len(lines):
            raise ValueError(f"Line number {line_num} out of range for {cmake_file}")

        # Collect the full add_test statement (may span multiple lines)
        statement = ""
        i = line_num - 1  # Convert to 0-indexed
        paren_count = 0
        started = False

        while i < len(lines):
            line = lines[i].strip()

            # Skip comments
            if line.startswith('#'):
                i += 1
                continue

            # Check if this line contains add_test
            if not started and 'add_test' in line.lower():
                started = True

            if started:
                statement += " " + line
                paren_count += line.count('(') - line.count(')')

                # Found complete statement
                if paren_count <= 0 and '(' in statement:
                    break

            i += 1

        if not statement:
            raise ValueError(f"Could not find add_test command at {cmake_file}:{line_num}")

        # Parse the statement
        # Extract content between parentheses
        match = re.search(r'add_test\s*\((.*)\)', statement, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse add_test statement: {statement}")

        args_str = match.group(1).strip()

        # Split by whitespace, respecting quotes
        # Simple tokenization (can be improved)
        tokens = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', args_str)

        # Parse tokens
        result: Dict[str, Any] = {
            'name': None,
            'command': None,
            'args': []
        }

        # Check if using NAME/COMMAND syntax
        if 'NAME' in [t.upper() for t in tokens]:
            # Modern syntax: add_test(NAME name COMMAND command args...)
            i = 0
            while i < len(tokens):
                token = tokens[i].upper()

                if token == 'NAME' and i + 1 < len(tokens):
                    result['name'] = tokens[i + 1]
                    i += 2
                elif token == 'COMMAND' and i + 1 < len(tokens):
                    result['command'] = tokens[i + 1]
                    # Rest are arguments
                    result['args'] = tokens[i + 2:]
                    break
                else:
                    i += 1
        else:
            # Old syntax: add_test(name command args...)
            if len(tokens) >= 2:
                result['name'] = tokens[0]
                result['command'] = tokens[1]
                result['args'] = tokens[2:] if len(tokens) > 2 else []

        # Clean up command (remove generator expressions, quotes, etc.)
        if result['command']:
            # Handle $<TARGET_FILE:target> -> target
            target_file_match = re.search(r'\$<TARGET_FILE:([^>]+)>', result['command'])
            if target_file_match:
                result['command'] = target_file_match.group(1)

            # Remove quotes
            result['command'] = result['command'].strip('"\'')

        return result

    def _collect_all_dependencies(self, component: Component, visited: Optional[Set[str]] = None) -> Tuple[List[Union[Component, Aggregator, Runner, TestDefinition]], Set[str]]:
        """Recursively collect all transitive dependencies from a Component.

        Args:
            component: Component to collect dependencies from
            visited: Set of IDs already visited (for cycle detection)

        Returns:
            Tuple of (dependencies list, dependency IDs set)
        """
        if visited is None:
            visited = set()

        # Check for cycle
        if component.id in visited:
            return [], set()

        # Add component to visited
        visited = visited | {component.id}

        # Collect dependencies recursively
        all_deps = []
        all_dep_ids = set()

        for dep in component.depends_on:
            # Add this dependency
            all_deps.append(dep)
            all_dep_ids.add(dep.id)

            # If dependency is a Component, recursively collect its dependencies
            if isinstance(dep, Component):
                transitive_deps, transitive_dep_ids = self._collect_all_dependencies(dep, visited)
                all_deps.extend(transitive_deps)
                all_dep_ids.update(transitive_dep_ids)

        return all_deps, all_dep_ids

    def _parse_args_nodes(self, args: List[str]) -> Tuple[List[Union[Component, Aggregator, Runner, TestDefinition]], Set[str], List[str]]:
        """Parse command arguments to find Components or other RIG nodes in findings.

        Args:
            args: List of command arguments

        Returns:
            Tuple of (args_nodes list, args_nodes_ids set, remaining_arguments list)
        """
        args_nodes = []
        args_nodes_ids = set()
        remaining_args = []

        for arg in args:
            # Check if argument matches any Component name in findings
            matched = False
            for component_key, component_val in self._findings[NodeType.COMPONENT].items():
                if arg == component_key.split('::')[0] or arg == component_val.name:
                    args_nodes.append(component_val)
                    args_nodes_ids.add(component_val.id)
                    matched = True
                    break

            if not matched:
                remaining_args.append(arg)

        return args_nodes, args_nodes_ids, remaining_args

    def _check_files_in_args(self, args: List[str]) -> List[Path]:
        """Check if any arguments are file paths that exist on disk.

        Args:
            args: List of command arguments (potentially file paths)

        Returns:
            List of existing file paths
        """
        file_paths = []

        for arg in args:
            # Try to resolve as absolute path first
            try:
                file_path = Path(arg)
                if file_path.is_absolute() and file_path.is_file():
                    file_paths.append(file_path)
                    continue
            except Exception:
                pass

            # Try to resolve relative to repo root
            try:
                file_path = self._repo_root / arg
                if file_path.is_file():
                    file_paths.append(file_path)
            except Exception:
                pass

        return file_paths

    def create_test_definition(self, ctest_info: CTestInfo) -> TestDefinition:
        """Create TestDefinition from CTest test information.

        Args:
            ctest_info: CTest test information

        Returns:
            TestDefinition object (also cached internally in findings)
        """
        # Extract evidence from CTest backtrace
        evidence = self.extract_evidence(ctest_info)

        # Parse evidence to get file and line
        # Evidence line format is "file:line"
        evidence_parts = evidence.line[0].rsplit(':', maxsplit=1)
        cmake_file = Path(evidence_parts[0])
        line_num = int(evidence_parts[1])
        evidence.line = [f'{cmake_file.relative_to(self._repo_root)}:{line_num}']

        # Parse add_test command to extract COMMAND
        add_test_info = self.parse_add_test_command(cmake_file, line_num)
        command_name = add_test_info['command']
        assert command_name is not None, f'command_name failed to extract from {add_test_info}'
        # Try to find Component with matching name
        test_executable_component: Optional[Union[Component, Runner]] = None

        # Search in Components
        for component_key, component_val in self._findings[NodeType.COMPONENT].items():
            if command_name == component_key.split('::')[0]:
                test_executable_component = component_val
                break

        # If not found in Components, create a Runner
        if not test_executable_component:
            # Parse arguments to find RIG nodes
            args_nodes, args_nodes_ids, remaining_args = self._parse_args_nodes(add_test_info['args'])

            test_executable_component = Runner(
                name=command_name,
                depends_on=[],
                evidence=[evidence],
                arguments=add_test_info['args'],
                args_nodes=args_nodes,
                args_nodes_ids=args_nodes_ids
            )

        # Extract test_components based on test_executable_component type
        test_components = []
        test_components_ids = set()

        if isinstance(test_executable_component, Component):
            # Recursively collect all dependencies
            test_components, test_components_ids = self._collect_all_dependencies(test_executable_component)
        elif isinstance(test_executable_component, Runner):
            # Extract from Runner's args_nodes
            test_components = test_executable_component.args_nodes
            test_components_ids = test_executable_component.args_nodes_ids

        # Extract source_files based on test_executable_component type
        source_files = []

        if isinstance(test_executable_component, Component):
            # Use Component's source files
            source_files = test_executable_component.source_files
        elif isinstance(test_executable_component, Runner):
            # Check if arguments are files on disk
            source_files = self._check_files_in_args(test_executable_component.arguments)

        # Create TestDefinition
        test_def = TestDefinition(
            name=ctest_info.name,
            test_framework="CTest",
            test_executable_component=test_executable_component,
            test_executable_component_id=test_executable_component.id if test_executable_component else None,
            test_components=test_components,
            test_components_ids=test_components_ids,
            components_being_tested=[],  # TODO: infer from test structure
            components_being_tested_ids=set(),
            source_files=source_files,
            depends_on=[],
            evidence=[evidence]
        )

        # Cache the test definition internally
        self._findings[NodeType.TEST_DEFINITION][test_def.id] = test_def

        return test_def
