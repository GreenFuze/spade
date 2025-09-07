"""
Repository Intelligence Graph (RIG) - Canonical representation of build system data.

This module provides the RIG class that holds all extracted build system information
in a canonical, non-build-system-specific format. The data is structured to be
SQL-friendly for future SQLite storage.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from schemas import Component, Aggregator, Runner, Test, ComponentType, Runtime, Evidence, ComponentLocation, ExternalPackage, PackageManager, BuildNode, RepositoryInfo, BuildSystemInfo, ValidationSeverity, ValidationError, RIGValidationError


class RIG:
    """
    Repository Intelligence Graph - Canonical representation of build system data.

    This class holds all extracted information from build systems in a flat,
    SQL-friendly structure. It's designed to be build-system agnostic and
    suitable for future SQLite storage and graph visualization.
    """

    def __init__(self, custom_build_artifact_patterns: Optional[List[str]] = None) -> None:
        """
        Initialize an empty RIG.

        Args:
            custom_build_artifact_patterns: Project-specific patterns to skip as build artifacts
        """
        # Repository-level information
        self.repository: Optional[RepositoryInfo] = None

        # Build system information
        self.build_system: Optional[BuildSystemInfo] = None

        # Build entities (flat lists for SQL compatibility)
        self.components: List[Component] = []
        self.aggregators: List[Aggregator] = []
        self.runners: List[Runner] = []
        self.tests: List[Test] = []

        # Custom build artifact patterns for project-specific filtering
        self.custom_build_artifact_patterns: Optional[List[str]] = custom_build_artifact_patterns

        # Supporting data (also flat for SQL)
        self.evidence: List[Evidence] = []
        self.component_locations: List[ComponentLocation] = []
        self.external_packages: List[ExternalPackage] = []
        self.package_managers: List[PackageManager] = []

        # Lookup dictionaries for efficient access (not stored in SQL)
        self._components_by_name: Dict[str, Component] = {}
        self._aggregators_by_name: Dict[str, Aggregator] = {}
        self._runners_by_name: Dict[str, Runner] = {}
        self._tests_by_name: Dict[str, Test] = {}

    def add_component(self, component: Component) -> None:
        """Add a component to the RIG."""
        self.components.append(component)
        self._components_by_name[component.name] = component

        # Add evidence and locations to flat lists
        self.evidence.append(component.evidence)
        self.component_locations.extend(component.locations)
        self.external_packages.extend(component.external_packages)

        # Add package managers
        for pkg in component.external_packages:
            self.package_managers.append(pkg.package_manager)

    def add_aggregator(self, aggregator: Aggregator) -> None:
        """Add an aggregator to the RIG."""
        self.aggregators.append(aggregator)
        self._aggregators_by_name[aggregator.name] = aggregator
        self.evidence.append(aggregator.evidence)

    def add_runner(self, runner: Runner) -> None:
        """Add a runner to the RIG."""
        self.runners.append(runner)
        self._runners_by_name[runner.name] = runner
        self.evidence.append(runner.evidence)

    def add_test(self, test: Test) -> None:
        """Add a test to the RIG."""
        self.tests.append(test)
        self._tests_by_name[test.name] = test
        self.evidence.append(test.evidence)

    def set_repository_info(self, repo_info: RepositoryInfo) -> None:
        """Set repository-level information."""
        self.repository = repo_info

    def set_build_system_info(self, build_system_info: BuildSystemInfo) -> None:
        """Set build system information."""
        self.build_system = build_system_info

    # Lookup methods for efficient access
    def get_component_by_name(self, name: str) -> Optional[Component]:
        """Get a component by name."""
        return self._components_by_name.get(name)

    def get_aggregator_by_name(self, name: str) -> Optional[Aggregator]:
        """Get an aggregator by name."""
        return self._aggregators_by_name.get(name)

    def get_runner_by_name(self, name: str) -> Optional[Runner]:
        """Get a runner by name."""
        return self._runners_by_name.get(name)

    def get_test_by_name(self, name: str) -> Optional[Test]:
        """Get a test by name."""
        return self._tests_by_name.get(name)

    def get_all_build_nodes(self) -> List[Any]:
        """Get all build nodes (components, aggregators, runners) as a flat list."""
        return self.components + self.aggregators + self.runners

    def get_build_node_by_name(self, name: str) -> Optional[Any]:
        """Get any build node (component, aggregator, or runner) by name."""
        return self.get_component_by_name(name) or self.get_aggregator_by_name(name) or self.get_runner_by_name(name)

    # Statistics and analysis methods
    def get_component_count_by_type(self) -> Dict[ComponentType, int]:
        """Get count of components by type."""
        counts: Dict[ComponentType, int] = {}
        for component in self.components:
            counts[component.type] = counts.get(component.type, 0) + 1
        return counts

    def get_component_count_by_language(self) -> Dict[str, int]:
        """Get count of components by programming language."""
        counts: Dict[str, int] = {}
        for component in self.components:
            counts[component.programming_language] = counts.get(component.programming_language, 0) + 1
        return counts

    def get_component_count_by_runtime(self) -> Dict[Optional[Runtime], int]:
        """Get count of components by runtime environment."""
        counts: Dict[Optional[Runtime], int] = {}
        for component in self.components:
            counts[component.runtime] = counts.get(component.runtime, 0) + 1
        return counts

    def get_test_count_by_framework(self) -> Dict[str, int]:
        """Get count of tests by framework."""
        counts: Dict[str, int] = {}
        for test in self.tests:
            counts[test.test_framework] = counts.get(test.test_framework, 0) + 1
        return counts

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get a dependency graph as a dictionary mapping node names to their dependencies."""
        graph: Dict[str, List[str]] = {}

        # Add all build nodes
        for node in self.get_all_build_nodes():
            graph[node.name] = [dep.name for dep in node.depends_on]

        return graph

    def get_reverse_dependency_graph(self) -> Dict[str, List[str]]:
        """Get a reverse dependency graph mapping node names to what depends on them."""
        reverse_graph: Dict[str, List[str]] = {}

        # Initialize all nodes
        for node in self.get_all_build_nodes():
            reverse_graph[node.name] = []

        # Build reverse dependencies
        for node in self.get_all_build_nodes():
            for dep in node.depends_on:
                reverse_graph[dep.name].append(node.name)

        return reverse_graph

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the RIG contents."""
        return {
            "repository": {
                "name": self.repository.name if self.repository else None,
                "root_path": str(self.repository.root_path) if self.repository else None,
                "build_directory": str(self.repository.build_directory) if self.repository else None,
                "output_directory": str(self.repository.output_directory) if self.repository else None,
            },
            "build_system": {"name": self.build_system.name if self.build_system else None, "version": self.build_system.version if self.build_system else None, "build_type": self.build_system.build_type if self.build_system else None},
            "counts": {
                "components": len(self.components),
                "aggregators": len(self.aggregators),
                "runners": len(self.runners),
                "tests": len(self.tests),
                "evidence": len(self.evidence),
                "component_locations": len(self.component_locations),
                "external_packages": len(self.external_packages),
                "package_managers": len(self.package_managers),
            },
            "component_types": self.get_component_count_by_type(),
            "programming_languages": self.get_component_count_by_language(),
            "runtimes": self.get_component_count_by_runtime(),
            "test_frameworks": self.get_test_count_by_framework(),
        }

    def __str__(self) -> str:
        """String representation of the RIG."""
        summary = self.get_summary()
        return f"RIG({summary['counts']['components']} components, {summary['counts']['tests']} tests, {summary['counts']['aggregators']} aggregators, {summary['counts']['runners']} runners)"

    def __repr__(self) -> str:
        """Detailed representation of the RIG."""
        return self.__str__()

    def validate(self) -> List[ValidationError]:
        """
        Validate the RIG for correctness and consistency.

        Returns:
            List of validation errors found. Empty list means no issues.
        """
        errors: List[ValidationError] = []

        # Run all validation checks
        errors.extend(self._validate_missing_source_files())
        errors.extend(self._validate_broken_dependencies())
        errors.extend(self._validate_missing_output_files())
        errors.extend(self._validate_orphaned_nodes())
        errors.extend(self._validate_circular_dependencies())
        errors.extend(self._validate_inconsistent_language())
        errors.extend(self._validate_duplicate_node_names())
        errors.extend(self._validate_test_relationships())
        errors.extend(self._validate_component_locations())
        errors.extend(self._validate_evidence_consistency())

        return errors

    def _is_cmake_build_artifact(self, source_file: Path, custom_patterns: Optional[List[str]] = None) -> bool:
        """
        Check if a source file is a CMake build artifact that should be skipped.

        Args:
            source_file: The source file path to check
            custom_patterns: Additional patterns to check (project-specific)

        Returns:
            True if the file should be skipped as a build artifact
        """
        source_str = str(source_file)

        # Standard CMake build artifact patterns
        standard_patterns = [
            "CMakeFiles/",
            "CMakeFiles\\",  # Windows path separator
            ".rule",
            ".dll.rule",  # Windows
            ".so.rule",  # Linux
            ".dylib.rule",  # macOS
            ".exe.rule",  # Windows
            ".lib.rule",  # Windows
            ".a.rule",  # Linux/macOS static library
            ".jar.rule",
        ]

        # Combine standard and custom patterns
        all_patterns = standard_patterns
        if custom_patterns:
            all_patterns.extend(custom_patterns)

        return any(skip_pattern in source_str for skip_pattern in all_patterns)

    def _validate_missing_source_files(self) -> List[ValidationError]:
        """Validate that all referenced source files exist."""
        errors: List[ValidationError] = []

        if not self.repository:
            return errors

        repo_root = self.repository.root_path

        for component in self.components:
            for source_file in component.source_files:
                # Skip CMake build artifacts and generated files
                if self._is_cmake_build_artifact(source_file, self.custom_build_artifact_patterns):
                    continue

                # Handle both relative and absolute paths
                if source_file.is_absolute():
                    full_path = source_file
                else:
                    full_path = repo_root / source_file

                if not full_path.exists():
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR,
                            category="missing_source_file",
                            message=f"Source file does not exist: {source_file}",
                            node_name=component.name,
                            file_path=source_file,
                            suggestion="Check if the file path is correct or if the file was moved/deleted",
                        )
                    )

        return errors

    def _validate_broken_dependencies(self) -> List[ValidationError]:
        """Validate that all dependencies reference existing nodes."""
        errors: List[ValidationError] = []

        # Create lookup for all node names
        all_node_names: set[str] = set()
        for node in self.get_all_build_nodes():
            all_node_names.add(node.name)

        for node in self.get_all_build_nodes():
            for dep in node.depends_on:
                if dep.name not in all_node_names:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR, category="broken_dependency", message=f"Dependency '{dep.name}' does not exist", node_name=node.name, suggestion="Check if the dependency name is correct or if the target was removed"
                        )
                    )

        return errors

    def _validate_missing_output_files(self) -> List[ValidationError]:
        """Validate that components produce expected output files."""
        errors: List[ValidationError] = []

        if not self.repository:
            return errors

        output_root = self.repository.output_directory

        for component in self.components:
            for location in component.locations:
                if location.action == "build":
                    full_path = output_root / location.path
                    if not full_path.exists():
                        errors.append(
                            ValidationError(
                                severity=ValidationSeverity.WARNING,
                                category="missing_output_file",
                                message=f"Expected output file does not exist: {location.path}",
                                node_name=component.name,
                                file_path=location.path,
                                suggestion="The component may not have been built yet or the output path is incorrect",
                            )
                        )

        return errors

    def _validate_orphaned_nodes(self) -> List[ValidationError]:
        """Validate that all nodes are connected to the graph."""
        errors: List[ValidationError] = []

        # Find all nodes that have no connections
        all_nodes = self.get_all_build_nodes()
        connected_nodes: set[str] = set()

        # Mark all nodes that are referenced as dependencies
        for node in all_nodes:
            for dep in node.depends_on:
                connected_nodes.add(dep.name)

        # Mark all nodes that have dependencies (they're connected)
        for node in all_nodes:
            if node.depends_on:
                connected_nodes.add(node.name)

        # Check for orphaned nodes
        for node in all_nodes:
            if node.name not in connected_nodes:
                # Check if it's a root node (no dependencies and nothing depends on it)
                has_dependents = any(node.name in [dep.name for dep in other.depends_on] for other in all_nodes)
                if not has_dependents:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.WARNING,
                            category="orphaned_node",
                            message=f"Node '{node.name}' has no connections to other nodes",
                            node_name=node.name,
                            suggestion="Check if this node should have dependencies or if other nodes should depend on it",
                        )
                    )

        return errors

    def _validate_circular_dependencies(self) -> List[ValidationError]:
        """Validate that there are no circular dependencies."""
        errors: List[ValidationError] = []

        def has_cycle(node_name: str, visited: set[str], rec_stack: set[str], graph: Dict[str, List[str]]) -> bool:
            visited.add(node_name)
            rec_stack.add(node_name)

            for neighbor in graph.get(node_name, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack, graph):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_name)
            return False

        # Build dependency graph
        dep_graph: Dict[str, List[str]] = {}
        for node in self.get_all_build_nodes():
            dep_graph[node.name] = [dep.name for dep in node.depends_on]

        # Check for cycles
        visited: set[str] = set()
        for node_name in dep_graph:
            if node_name not in visited:
                if has_cycle(node_name, visited, set(), dep_graph):
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR,
                            category="circular_dependency",
                            message=f"Circular dependency detected involving node '{node_name}'",
                            node_name=node_name,
                            suggestion="Review the dependency chain to break the circular reference",
                        )
                    )
                    break  # Only report one cycle to avoid spam

        return errors

    def _validate_inconsistent_language(self) -> List[ValidationError]:
        """Validate that component language matches source file extensions."""
        errors: List[ValidationError] = []

        # Language to extension mapping
        language_extensions = {"c": [".c"], "cxx": [".cpp", ".cxx", ".cc", ".c++"], "java": [".java"], "go": [".go"], "python": [".py"], "csharp": [".cs"], "javascript": [".js"], "typescript": [".ts"]}

        for component in self.components:
            expected_extensions = language_extensions.get(component.programming_language, [])
            if not expected_extensions:
                continue  # Unknown language, skip validation

            for source_file in component.source_files:
                # Skip CMake build artifacts
                if self._is_cmake_build_artifact(source_file, self.custom_build_artifact_patterns):
                    continue

                file_ext = source_file.suffix.lower()
                if file_ext not in expected_extensions:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.WARNING,
                            category="inconsistent_language",
                            message=f"Source file '{source_file}' has extension '{file_ext}' but component language is '{component.programming_language}'",
                            node_name=component.name,
                            file_path=source_file,
                            suggestion=f"Check if the file extension matches the programming language or update the language detection",
                        )
                    )

        return errors

    def _validate_duplicate_node_names(self) -> List[ValidationError]:
        """Validate that all node names are unique."""
        errors: List[ValidationError] = []

        all_nodes = self.get_all_build_nodes()
        name_counts: Dict[str, int] = {}

        for node in all_nodes:
            name_counts[node.name] = name_counts.get(node.name, 0) + 1

        for name, count in name_counts.items():
            if count > 1:
                errors.append(
                    ValidationError(severity=ValidationSeverity.ERROR, category="duplicate_node_name", message=f"Node name '{name}' is used by {count} different nodes", node_name=name, suggestion="Ensure all node names are unique across the entire RIG")
                )

        return errors

    def _validate_test_relationships(self) -> List[ValidationError]:
        """Validate test relationships and structure."""
        errors: List[ValidationError] = []

        # Check that tests have proper relationships
        for test in self.tests:
            if not test.components_being_tested and not test.test_executable:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.WARNING,
                        category="isolated_test",
                        message=f"Test '{test.name}' has no components being tested and no test executable",
                        node_name=test.name,
                        suggestion="Check if the test should be linked to components or if it's a standalone test",
                    )
                )

        return errors

    def _validate_component_locations(self) -> List[ValidationError]:
        """Validate component location information."""
        errors: List[ValidationError] = []

        for component in self.components:
            if not component.locations:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.WARNING,
                        category="missing_location_info",
                        message=f"Component '{component.name}' has no location information",
                        node_name=component.name,
                        suggestion="Components should have at least one location indicating where they are built",
                    )
                )

        return errors

    def _validate_evidence_consistency(self) -> List[ValidationError]:
        """Validate that evidence information is consistent."""
        errors: List[ValidationError] = []

        # Check that all nodes have evidence
        for node in self.get_all_build_nodes():
            if not hasattr(node, "evidence") or not node.evidence:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.WARNING, category="missing_evidence", message=f"Node '{node.name}' has no evidence information", node_name=node.name, suggestion="All nodes should have evidence indicating where they are defined"
                    )
                )

        return errors

    def show_graph(self, validate_before_show: bool = True) -> None:
        """
        Display the RIG as an interactive graph using Cytoscape.js.
        Creates a self-contained HTML file with all JavaScript libraries embedded.

        Args:
            validate_before_show: If True, validate the RIG before showing the graph.
                                If validation fails, raises RIGValidationError.
        """
        if validate_before_show:
            errors = self.validate()
            # Only raise error if there are actual errors (not just warnings)
            error_errors = [e for e in errors if e.severity == ValidationSeverity.ERROR]
            if error_errors:
                raise RIGValidationError(error_errors)

        # Generate the HTML file
        html_content = self._generate_graph_html()

        # Determine filename
        project_name = self.repository.name if self.repository else "unknown"
        filename = f"rig_{project_name}_graph.html"

        # Create self-contained HTML with embedded libraries
        self._create_embedded_html(html_content, filename)

        # Get absolute path for user reference
        import os

        file_url = f"file://{os.path.abspath(filename)}"

        print(f"Self-contained graph visualization generated: {filename}")
        print(f"File location: {file_url}")
        print(f"")
        print(f"To view the graph: Open {filename} directly in your browser")
        print(f"This file has no external dependencies and works offline.")

    def _create_embedded_html(self, html_content: str, filename: str) -> None:
        """Create a self-contained HTML file with embedded JavaScript libraries."""
        import urllib.request
        import urllib.error

        # Download the libraries
        libraries = {
            "cytoscape": "https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js",
            "dagre": "https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js",
            "cytoscape-dagre": "https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js",
        }

        downloaded_libs: Dict[str, str] = {}
        for name, url in libraries.items():
            try:
                print(f"Downloading {name}...")
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode("utf-8")
                downloaded_libs[name] = content
                print(f"✓ Downloaded {name} ({len(content)} characters)")
            except urllib.error.URLError as e:
                print(f"✗ Failed to download {name}: {e}")
                # Continue with CDN fallback

        # Replace script tags with embedded content
        for name, content in downloaded_libs.items():
            if content:
                # Find the script tag for this library
                script_pattern = f'<script src="https://cdn.jsdelivr.net/npm/{name}@'
                start_idx = html_content.find(script_pattern)
                if start_idx != -1:
                    # Find the end of the script tag
                    end_idx = html_content.find("></script>", start_idx)
                    if end_idx != -1:
                        end_idx += len("></script>")
                        # Replace with embedded script
                        embedded_script = f"<script>\n{content}\n</script>"
                        html_content = html_content[:start_idx] + embedded_script + html_content[end_idx:]
                        print(f"✓ Embedded {name} library")

        # Write the final HTML file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _get_available_languages(self) -> List[str]:
        """Get all unique programming languages from components."""
        languages: set[str] = set()
        for component in self.components:
            if component.programming_language:
                languages.add(component.programming_language)
        return sorted(list(languages))

    def _get_available_runtimes(self) -> List[str]:
        """Get all unique runtime environments from components."""
        runtimes: set[str] = set()
        for component in self.components:
            if component.runtime:
                runtimes.add(str(component.runtime))
        return sorted(list(runtimes))

    def _generate_language_filter_options(self) -> str:
        """Generate HTML options for language filter based on actual RIG data."""
        options = ['<option value="all">All</option>']
        for lang in self._get_available_languages():
            # Capitalize first letter for display
            display_name = lang.capitalize()
            options.append(f'<option value="{lang}">{display_name}</option>')
        return "\n                ".join(options)

    def _generate_runtime_filter_options(self) -> str:
        """Generate HTML options for runtime filter based on actual RIG data."""
        options = ['<option value="all">All</option>']
        for runtime in self._get_available_runtimes():
            # Clean up runtime display name
            display_name = runtime.replace("Runtime.", "").replace("_", "-")
            options.append(f'<option value="{runtime}">{display_name}</option>')
        return "\n                ".join(options)

    def generate_prompts(self, limit: int = 50, filename: Optional[str] = None) -> str:
        """
        Generate a comprehensive prompt for AI agents with repository build information.

        This method creates a structured prompt that provides AI agents (like Cursor) with
        essential information about the repository's build system, components, dependencies,
        and potential issues. The data is formatted for easy consumption and understanding.

        Args:
            limit: Maximum number of components to include in the prompt (default: 50)
            filename: Optional filename to write the prompt to a file

        Returns:
            Formatted string containing repository build information for AI agents
        """
        # Extract basic repository information
        repo_name = self.repository.name if self.repository else "Unknown"
        repo_root = str(self.repository.root_path) if self.repository else "Unknown"
        build_system = self.build_system.name if self.build_system else "Unknown"
        configure_cmd = self.repository.configure_command if self.repository else ""
        test_cmd = self.repository.test_command if self.repository else ""

        # Determine build roots (for now, just use repo root)
        build_roots = ["./"]

        # Generate header section
        header = f"""Repo={repo_name}  Root={repo_root}
BuildSystem={build_system}              # e.g., cmake | bazel | gradle | custom_script
Scope={build_roots}                     # e.g., ["./"] or ["./", "subproj/ui"]
DetectionMode=configure_only            # e.g., no_exec | configure_only | build
Commands={{                                # optional hints; empty if not applicable
  "configure": "{configure_cmd}",
  "test_discovery": "{test_cmd}"
}}"""

        # Generate JSON data section
        json_data = self._generate_prompts_json_data(limit)

        # Combine header and JSON data
        full_prompt = f"{header}\n\n{json_data}"

        # Write to file if filename is provided
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(full_prompt)

        return full_prompt

    def _generate_prompts_json_data(self, limit: int) -> str:
        """Generate the JSON data section for the prompts."""
        import json

        # Basic repository info
        repo_info = {"name": self.repository.name if self.repository else "Unknown", "root": str(self.repository.root_path) if self.repository else "Unknown"}

        # Build system info
        build_info = {
            "system": self.build_system.name if self.build_system else "Unknown",
            "generator": None,  # Removed as per our refactoring
            "type": self.build_system.build_type if self.build_system else None,
            "configure_cmd": self.repository.configure_command if self.repository else "",
            "test_cmd": self.repository.test_command if self.repository else "",
            "limits": {"max_list": limit},
        }

        # Components (topologically sorted, limited)
        components = self._generate_prompts_components(limit)

        # Aggregators
        aggregators = self._generate_prompts_aggregators()

        # Runners
        runners = self._generate_prompts_runners()

        # Tests
        tests = self._generate_prompts_tests()

        # Gaps (validation issues)
        gaps = self._generate_prompts_gaps()

        # Combine all data
        data = {"repo": repo_info, "build": build_info, "components": components, "aggregators": aggregators, "runners": runners, "tests": tests, "gaps": gaps}

        return json.dumps(data, indent=2)

    def _generate_prompts_components(self, limit: int) -> List[Dict[str, Any]]:
        """Generate component data for prompts."""
        components: List[Dict[str, Any]] = []

        # Sort components topologically (dependencies first)
        sorted_components = self._topological_sort_components()

        for i, component in enumerate(sorted_components[:limit]):
            comp_data: Dict[str, Any] = {
                "id": component.id or i,
                "name": component.name,
                "type": component.type.value,
                "language": component.programming_language,
                "runtime": str(component.runtime) if component.runtime else "native",
                "output": component.output,
                "output_path": str(component.output_path),
                "depends_on": [dep.name for dep in component.depends_on],
                "externals": [{"mgr": ext.package_manager.name, "pkg": ext.package_manager.package_name} for ext in component.external_packages],
                "evidence": [{"file": str(ev.file), "start": ev.start_line, "end": ev.end_line} for ev in [component.evidence]],  # Main evidence
            }
            components.append(comp_data)

        return components

    def _generate_prompts_aggregators(self) -> List[Dict[str, Any]]:
        """Generate aggregator data for prompts."""
        aggregators: List[Dict[str, Any]] = []

        for i, agg in enumerate(self.aggregators):
            agg_data: Dict[str, Any] = {"id": agg.id or i, "name": agg.name, "depends_on": [dep.name for dep in agg.depends_on], "evidence": [{"file": str(agg.evidence.file), "start": agg.evidence.start_line, "end": agg.evidence.end_line}]}
            aggregators.append(agg_data)

        return aggregators

    def _generate_prompts_runners(self) -> List[Dict[str, Any]]:
        """Generate runner data for prompts."""
        runners: List[Dict[str, Any]] = []

        for i, runner in enumerate(self.runners):
            # Extract command hint from evidence text
            command_hint = runner.evidence.text[:100] if runner.evidence.text else "No command info"

            runner_data: Dict[str, Any] = {"id": runner.id or i, "name": runner.name, "hint": command_hint, "evidence": [{"file": str(runner.evidence.file), "start": runner.evidence.start_line, "end": runner.evidence.end_line}]}
            runners.append(runner_data)

        return runners

    def _generate_prompts_tests(self) -> List[Dict[str, Any]]:
        """Generate test data for prompts."""
        tests: List[Dict[str, Any]] = []

        for i, test in enumerate(self.tests):
            test_data: Dict[str, Any] = {
                "id": test.id or i,
                "name": test.name,
                "framework": test.test_framework,
                "exe_component": test.test_executable.name if test.test_executable else None,
                "components": [comp.name for comp in test.components_being_tested],
                "evidence": [{"file": str(test.evidence.file), "start": test.evidence.start_line, "end": test.evidence.end_line}],
            }
            tests.append(test_data)

        return tests

    def _generate_prompts_gaps(self) -> Dict[str, Any]:
        """Generate gaps/validation issues for prompts."""
        # Run validation to get current issues
        validation_errors = self.validate()

        missing_sources: List[str] = []
        missing_outputs: List[str] = []
        orphaned_aggregators: List[str] = []
        orphaned_tests: List[str] = []
        risky_runners: List[str] = []

        for error in validation_errors:
            if error.category == "missing_source_files" and error.node_name:
                missing_sources.append(error.node_name)
            elif error.category == "missing_output_files" and error.node_name:
                missing_outputs.append(error.node_name)
            elif error.category == "orphaned_nodes":
                if error.node_name in [agg.name for agg in self.aggregators]:
                    orphaned_aggregators.append(error.node_name)
                elif error.node_name in [test.name for test in self.tests]:
                    orphaned_tests.append(error.node_name)
            elif error.category == "risky_runners" and error.node_name:
                risky_runners.append(error.node_name)

        return {"missing_sources": list(set(missing_sources)), "missing_outputs": list(set(missing_outputs)), "orphans": {"aggregators": list(set(orphaned_aggregators)), "tests": list(set(orphaned_tests))}, "risky_runners": list(set(risky_runners))}

    def _topological_sort_components(self) -> List[Component]:
        """Sort components topologically (dependencies first)."""
        # Simple topological sort using Kahn's algorithm
        in_degree: Dict[str, int] = {comp.name: 0 for comp in self.components}
        graph: Dict[str, List[str]] = {comp.name: [] for comp in self.components}

        # Build graph and calculate in-degrees
        for component in self.components:
            for dep in component.depends_on:
                if isinstance(dep, Component):
                    graph[dep.name].append(component.name)
                    in_degree[component.name] += 1

        # Find components with no dependencies
        queue: List[str] = [comp.name for comp in self.components if in_degree[comp.name] == 0]
        result: List[Component] = []

        # Process queue
        while queue:
            current = queue.pop(0)
            result.append(next(comp for comp in self.components if comp.name == current))

            # Update in-degrees of dependent components
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def _generate_graph_html(self) -> str:
        """Generate the complete HTML content for the graph visualization."""

        # Generate graph data
        nodes_data, edges_data = self._generate_graph_data()

        # Convert to JSON for JavaScript
        import json

        nodes_json = json.dumps(nodes_data)
        edges_json = json.dumps(edges_data)

        # Generate the HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RIG Graph - {self.repository.name if self.repository else "Unknown Project"}</title>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        
        #header {{
            background-color: #2c3e50;
            color: white;
            padding: 10px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        #header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        
        #header p {{
            margin: 5px 0 0 0;
            opacity: 0.8;
        }}
        
        #controls {{
            background-color: white;
            padding: 15px 20px;
            border-bottom: 1px solid #ddd;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .control-group label {{
            font-weight: bold;
            color: #555;
        }}
        
        select, input, button {{
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        button {{
            background-color: #3498db;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        button:hover {{
            background-color: #2980b9;
        }}
        
        #search-box {{
            min-width: 200px;
        }}
        
        #cy {{
            width: 100%;
            height: calc(100vh - 140px);
            background-color: #fafafa;
        }}
        
        .node-tooltip {{
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            word-wrap: break-word;
        }}
        
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            border-radius: 3px;
            margin: 1px;
        }}
        
        .badge-language {{
            background-color: #e74c3c;
            color: white;
        }}
        
        .badge-runtime {{
            background-color: #9b59b6;
            color: white;
        }}
        
        .badge-type {{
            background-color: #f39c12;
            color: white;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Repository Intelligence Graph</h1>
        <p>Project: {self.repository.name if self.repository else "Unknown"} | 
           Components: {len(self.components)} | 
           Tests: {len(self.tests)} | 
           Aggregators: {len(self.aggregators)} | 
           Runners: {len(self.runners)}</p>
    </div>
    
    <div id="controls">
        <div class="control-group">
            <label>Show Sources:</label>
            <input type="checkbox" id="show-sources" onchange="toggleSources()">
        </div>
        
        <div class="control-group">
            <label>Node Type:</label>
            <select id="node-type-filter" onchange="filterNodes()">
                <option value="all">All</option>
                <option value="component">Components</option>
                <option value="test">Tests</option>
                <option value="aggregator">Aggregators</option>
                <option value="runner">Runners</option>
                <option value="source">Source Files</option>
            </select>
        </div>
        
        <div class="control-group">
            <label>Language:</label>
            <select id="language-filter" onchange="filterNodes()">
                {self._generate_language_filter_options()}
            </select>
        </div>
        
        <div class="control-group">
            <label>Runtime:</label>
            <select id="runtime-filter" onchange="filterNodes()">
                {self._generate_runtime_filter_options()}
            </select>
        </div>
        
        <div class="control-group">
            <label>Search:</label>
            <input type="text" id="search-box" placeholder="Search nodes..." onkeyup="searchNodes()">
        </div>
        
        <div class="control-group">
            <button onclick="resetView()">Reset View</button>
            <button onclick="fitToScreen()">Fit to Screen</button>
            <button onclick="exportGraph()">Export Graph</button>
        </div>
    </div>
    
    <div id="cy"></div>
    <div id="tooltip" class="node-tooltip" style="display: none;"></div>
    
    <script>
        // Graph data
        const nodesData = {nodes_json};
        const edgesData = {edges_json};
        
        let cy;
        let showSources = false;
        
        // Initialize Cytoscape
        function initCytoscape() {{
            cy = cytoscape({{
                container: document.getElementById('cy'),
                
                elements: {{
                    nodes: nodesData,
                    edges: edgesData
                }},
                
                layout: {{
                    name: 'dagre',
                    rankDir: 'TB',
                    spacingFactor: 1.5,
                    nodeSep: 50,
                    rankSep: 100
                }},
                
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'color': '#333',
                            'text-outline-width': 2,
                            'text-outline-color': '#fff',
                            'width': 'data(width)',
                            'height': 'data(height)',
                            'background-color': 'data(color)',
                            'border-width': 2,
                            'border-color': 'data(borderColor)',
                            'shape': 'data(shape)'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="component"]',
                        style: {{
                            'background-color': '#3498db',
                            'border-color': '#2980b9',
                            'shape': 'round-rectangle'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="test"]',
                        style: {{
                            'background-color': '#e74c3c',
                            'border-color': '#c0392b',
                            'shape': 'diamond'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="aggregator"]',
                        style: {{
                            'background-color': '#2ecc71',
                            'border-color': '#27ae60',
                            'shape': 'hexagon'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="runner"]',
                        style: {{
                            'background-color': '#f39c12',
                            'border-color': '#e67e22',
                            'shape': 'triangle'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="source"]',
                        style: {{
                            'background-color': '#95a5a6',
                            'border-color': '#7f8c8d',
                            'shape': 'ellipse',
                            'width': 30,
                            'height': 30
                        }}
                    }},
                    
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': 'data(color)',
                            'target-arrow-color': 'data(color)',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="aggregation"]',
                        style: {{
                            'line-color': '#2c3e50',
                            'target-arrow-color': '#2c3e50',
                            'line-style': 'solid'
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="test"]',
                        style: {{
                            'line-color': '#e74c3c',
                            'target-arrow-color': '#e74c3c',
                            'line-style': 'dashed'
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="build"]',
                        style: {{
                            'line-color': '#f39c12',
                            'target-arrow-color': '#f39c12',
                            'line-style': 'solid'
                        }}
                    }}
                ]
            }});
            
            // Add event listeners
            cy.on('mouseover', 'node', showTooltip);
            cy.on('mouseout', 'node', hideTooltip);
            cy.on('tap', 'node', selectNode);
            
            // Apply initial filters (hide sources by default)
            filterNodes();
        }}
        
        // Show tooltip on hover
        function showTooltip(event) {{
            const node = event.target;
            const data = node.data();
            const tooltip = document.getElementById('tooltip');
            
            let content = `<strong>${{data.label}}</strong><br>`;
            content += `Type: ${{data.type}}<br>`;
            
            if (data.language) {{
                content += `Language: ${{data.language}}<br>`;
            }}
            if (data.runtime) {{
                content += `Runtime: ${{data.runtime}}<br>`;
            }}
            if (data.componentType) {{
                content += `Component Type: ${{data.componentType}}<br>`;
            }}
            if (data.filePath) {{
                content += `Path: ${{data.filePath}}<br>`;
            }}
            if (data.sourceFiles && data.sourceFiles.length > 0) {{
                content += `<br><strong>Source Files:</strong><br>`;
                data.sourceFiles.forEach(file => {{
                    content += `• ${{file}}<br>`;
                }});
            }}
            if (data.testFramework) {{
                content += `Test Framework: ${{data.testFramework}}<br>`;
            }}
            
            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
        }}
        
        // Hide tooltip
        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}
        
        // Select node
        function selectNode(event) {{
            const node = event.target;
            cy.elements().unselect();
            node.select();
        }}
        
        // Toggle source files visibility
        function toggleSources() {{
            showSources = document.getElementById('show-sources').checked;
            filterNodes();
        }}
        
        // Filter nodes based on controls
        function filterNodes() {{
            const nodeTypeFilter = document.getElementById('node-type-filter').value;
            const languageFilter = document.getElementById('language-filter').value;
            const runtimeFilter = document.getElementById('runtime-filter').value;
            const searchTerm = document.getElementById('search-box').value.toLowerCase();
            
            cy.elements().forEach(ele => {{
                const data = ele.data();
                let visible = true;
                
                // Source files filter
                if (data.type === 'source' && !showSources) {{
                    visible = false;
                }}
                
                // Node type filter
                if (nodeTypeFilter !== 'all' && data.type !== nodeTypeFilter) {{
                    visible = false;
                }}
                
                // Language filter
                if (languageFilter !== 'all' && data.language !== languageFilter) {{
                    visible = false;
                }}
                
                // Runtime filter
                if (runtimeFilter !== 'all' && data.runtime !== runtimeFilter) {{
                    visible = false;
                }}
                
                // Search filter
                if (searchTerm && !data.label.toLowerCase().includes(searchTerm) && 
                    !data.filePath?.toLowerCase().includes(searchTerm)) {{
                    visible = false;
                }}
                
                ele.style('display', visible ? 'element' : 'none');
            }});
            
            cy.layout({{ name: 'dagre', rankDir: 'TB' }}).run();
        }}
        
        // Search nodes
        function searchNodes() {{
            filterNodes();
        }}
        
        // Reset view
        function resetView() {{
            document.getElementById('show-sources').checked = false;
            document.getElementById('node-type-filter').value = 'all';
            document.getElementById('language-filter').value = 'all';
            document.getElementById('runtime-filter').value = 'all';
            document.getElementById('search-box').value = '';
            showSources = false;
            filterNodes();
        }}
        
        // Fit to screen
        function fitToScreen() {{
            cy.fit();
        }}
        
        // Export graph to PNG
        function exportGraph() {{
            try {{
                // Get the current graph as PNG
                const pngData = cy.png({{
                    output: 'blob',
                    bg: 'white',
                    full: true,
                    scale: 2  // Higher resolution
                }});
                
                // Create download link
                const url = URL.createObjectURL(pngData);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'rig_graph.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                console.log('Graph exported successfully');
            }} catch (error) {{
                console.error('Export failed:', error);
                alert('Export failed. Please try again.');
            }}
        }}
        
        // Update tooltip position
        document.addEventListener('mousemove', function(e) {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip.style.display === 'block') {{
                tooltip.style.left = e.pageX + 10 + 'px';
                tooltip.style.top = e.pageY - 10 + 'px';
            }}
        }});
        
        // Initialize when page loads
        window.addEventListener('load', initCytoscape);
    </script>
</body>
</html>"""

        return html_template

    def _generate_graph_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate nodes and edges data for the graph visualization."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Add root node if we have a repository
        if self.repository:
            nodes.append({"data": {"id": "root", "label": self.repository.name, "type": "root", "color": "#34495e", "borderColor": "#2c3e50", "shape": "round-rectangle", "width": 120, "height": 40}})

        # Add all build nodes
        for node in self.get_all_build_nodes():
            node_data = self._create_node_data(node)
            nodes.append(node_data)

        # Add test nodes
        for test in self.tests:
            node_data = self._create_test_node_data(test)
            nodes.append(node_data)

        # Add source file nodes (will be filtered by UI)
        for component in self.components:
            for source_file in component.source_files:
                source_id = f"source_{source_file}"
                if not any(n["data"]["id"] == source_id for n in nodes):
                    nodes.append({"data": {"id": source_id, "label": source_file.name, "type": "source", "color": "#95a5a6", "borderColor": "#7f8c8d", "shape": "ellipse", "width": 30, "height": 30, "filePath": str(source_file)}})

        # Add edges
        edges.extend(self._create_aggregation_edges())
        edges.extend(self._create_test_edges())
        edges.extend(self._create_build_edges())

        return nodes, edges

    def _create_node_data(self, node: BuildNode) -> Dict[str, Any]:
        """Create node data for a build node."""
        node_type = type(node).__name__.lower()

        # Determine color based on type
        color_map = {"component": "#3498db", "aggregator": "#2ecc71", "runner": "#f39c12"}
        color = color_map.get(node_type, "#95a5a6")

        # Use plain text label (no HTML)
        label = node.name

        node_data: Dict[str, Any] = {"data": {"id": node.name, "label": label, "type": node_type, "color": color, "borderColor": color, "shape": "round-rectangle", "width": 100, "height": 50}}

        # Add component-specific data
        if isinstance(node, Component):
            node_data["data"]["language"] = node.programming_language
            node_data["data"]["runtime"] = str(node.runtime)
            node_data["data"]["componentType"] = str(node.type)
            node_data["data"]["filePath"] = str(node.output_path)
            node_data["data"]["sourceFiles"] = [str(f) for f in node.source_files]

        return node_data

    def _create_test_node_data(self, test: Test) -> Dict[str, Any]:
        """Create node data for a test."""
        # Use plain text label (no HTML)
        label = test.name

        return {
            "data": {
                "id": test.name,
                "label": label,
                "type": "test",
                "color": "#e74c3c",
                "borderColor": "#c0392b",
                "shape": "diamond",
                "width": 100,
                "height": 50,
                "testFramework": test.test_framework,
                "filePath": str(test.evidence.file) if test.evidence else None,
            }
        }

    def _create_aggregation_edges(self) -> List[Dict[str, Any]]:
        """Create aggregation edges."""
        edges: List[Dict[str, Any]] = []

        # Root to aggregators
        if self.repository:
            for aggregator in self.aggregators:
                edges.append({"data": {"id": f"root_to_{aggregator.name}", "source": "root", "target": aggregator.name, "type": "aggregation", "color": "#2c3e50", "label": "aggregates"}})

        # Aggregators to their dependencies
        for aggregator in self.aggregators:
            for dep in aggregator.depends_on:
                edges.append({"data": {"id": f"{aggregator.name}_to_{dep.name}", "source": aggregator.name, "target": dep.name, "type": "aggregation", "color": "#2c3e50", "label": "aggregates"}})

        return edges

    def _create_test_edges(self) -> List[Dict[str, Any]]:
        """Create test edges."""
        edges: List[Dict[str, Any]] = []

        for test in self.tests:
            for component in test.components_being_tested:
                edges.append({"data": {"id": f"{test.name}_tests_{component.name}", "source": test.name, "target": component.name, "type": "test", "color": "#e74c3c", "label": "tests"}})

        return edges

    def _create_build_edges(self) -> List[Dict[str, Any]]:
        """Create build edges."""
        edges: List[Dict[str, Any]] = []

        # Components to source files
        for component in self.components:
            for source_file in component.source_files:
                source_id = f"source_{source_file}"
                edges.append({"data": {"id": f"{component.name}_builds_{source_id}", "source": component.name, "target": source_id, "type": "build", "color": "#f39c12", "label": "builds"}})

        # Components to test executables
        for test in self.tests:
            if test.test_executable:
                edges.append({"data": {"id": f"{test.test_executable.name}_builds_{test.name}", "source": test.test_executable.name, "target": test.name, "type": "build", "color": "#f39c12", "label": "builds"}})

        return edges
