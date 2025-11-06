"""
Repository Intelligence Graph (RIG) - Canonical representation of build system data.

This module provides the RIG class that holds all extracted build system information
in a canonical, non-build-system-specific format. The data is structured to be
SQL-friendly for future SQLite storage.
"""

import json
import difflib
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Iterable, Union

from core.schemas import RepositoryInfo, BuildSystemInfo, Component, Aggregator, Runner, TestDefinition, ExternalPackage, PackageManager, Evidence, RIGNode, ComponentType, ValidationError, RIGPromptData
from core.rig_validator import RIGValidator
from core.rig_visualizer import RIGVisualizer


class RIG:
    """
    Repository Intelligence Graph - Canonical representation of build system data.

    This class holds all extracted information from build systems in a flat,
    SQL-friendly structure. It's designed to be build-system agnostic and
    suitable for future SQLite storage and graph visualization.
    """

    def __init__(self) -> None:
        """
        Initialize an empty RIG.
        """
        # Repository-level information
        self._repository_info: Optional[RepositoryInfo] = None

        # Build system information
        self._build_system_info: Optional[BuildSystemInfo] = None

        # Lookup dictionaries for efficient access (not stored in SQL)
        self._components_by_id: Dict[str, Component] = {}
        self._aggregators_by_id: Dict[str, Aggregator] = {}
        self._runners_by_id: Dict[str, Runner] = {}
        # self._utilities_by_name: Dict[str, Utility] = {} # TODO: I think its not needed
        self._tests_by_id: Dict[str, TestDefinition] = {}
        
        self._external_packages_by_id: Dict[str, ExternalPackage] = {}
        self._package_managers_by_id: Dict[str, PackageManager] = {}
        self._evidence_by_id: Dict[str, Evidence] = {}

    def _set_rig_nodes_ids(self, rignode: RIGNode, processed_ids: Optional[Set[str]] = None) -> None:
        """Set artifact IDs for a given RIG node.

        Args:
            rignode: The RIG node to process
            processed_ids: Set of node IDs that have already been processed (to prevent infinite recursion)
        """
        # Initialize processed_ids if not provided
        if processed_ids is None:
            processed_ids = set()

        # Skip if this node has already been processed
        if rignode.id in processed_ids:
            return

        # Mark this node as processed
        processed_ids.add(rignode.id)

        # evidence
        for evidence in rignode.evidence:
            self._evidence_by_id[evidence.id] = evidence

            if rignode.evidence_ids is None:
                rignode.evidence_ids = set()

            rignode.evidence_ids.add(evidence.id)

        # dependencies
        if rignode.depends_on is None:
            rignode.depends_on = []

        for dep in rignode.depends_on:
            if rignode.depends_on_ids is None:
                rignode.depends_on_ids = set()

            rignode.depends_on_ids.add(dep.id)
            if isinstance(dep, Component):
                self._components_by_id[dep.id] = dep
            elif isinstance(dep, Aggregator):
                self._aggregators_by_id[dep.id] = dep
            elif isinstance(dep, Runner):
                self._runners_by_id[dep.id] = dep
            elif isinstance(dep, TestDefinition):
                self._tests_by_id[dep.id] = dep
            else:
                raise ValueError(f"Unknown dependency type: {type(dep)}")

            # Recursively process the dependency to register its evidence
            self._set_rig_nodes_ids(dep, processed_ids)


    def add_component(self, component: Component) -> None:
        """Add a component to the RIG."""
        
        if component.id in self._components_by_id:
            # Component already exists, skip adding
            return
            
        # add component
        self._components_by_id[component.id] = component

        # external packages
        assert component.external_packages is not None
        
        for external_package in component.external_packages:
            if external_package.package_manager.id not in self._package_managers_by_id:
                self._package_managers_by_id[external_package.package_manager.id] = external_package.package_manager
            
            assert component.external_packages_ids is not None
            component.external_packages_ids.add(external_package.id)
            self._external_packages_by_id[external_package.id] = external_package
            
        self._set_rig_nodes_ids(component)
        
        
    def add_aggregator(self, aggregator: Aggregator) -> None:
        """Add an aggregator to the RIG."""
        self._aggregators_by_id[aggregator.id] = aggregator
        self._set_rig_nodes_ids(aggregator)

    def add_runner(self, runner: Runner) -> None:
        """Add a runner to the RIG."""
        self._runners_by_id[runner.id] = runner
        self._set_rig_nodes_ids(runner)

    # def add_utility(self, utility: Utility) -> None:
    #     """Add a utility to the RIG."""
    #     self.utilities.append(utility)
    #     self._utilities_by_name[utility.name] = utility
    #     self.evidence.extend(utility.evidence)

    def add_test(self, test: TestDefinition) -> None:
        """Add a test to the RIG."""
        self._tests_by_id[test.id] = test
        
        if test.test_executable_component is not None:
            test.test_executable_component_id = test.test_executable_component.id
            
            assert test.test_executable_component is not None
            
            if isinstance(test.test_executable_component, Component):
                self._components_by_id[test.test_executable_component.id] = test.test_executable_component
            else:
                raise RuntimeError(f'test.test_executable_component is expected to be Component, while it is {type(test.test_executable_component)}')
            
        if test.test_components is not None:
            for comp in test.test_components:
                assert test.test_components_ids is not None
                test.test_components_ids.add(comp.id)
                self._components_by_id[comp.id] = comp
                
        if test.components_being_tested is not None:
            for comp in test.components_being_tested:
                assert test.components_being_tested_ids is not None
                test.components_being_tested_ids.add(comp.id)
                self._components_by_id[comp.id] = comp
                
        self._set_rig_nodes_ids(test)
        

    def set_repository_info(self, repo_info: RepositoryInfo) -> None:
        """Set repository-level information."""
        self._repository_info = repo_info

    def set_build_system_info(self, build_system_info: BuildSystemInfo) -> None:
        """Set build system information."""
        self._build_system_info = build_system_info

    # Lookup methods for efficient access
    def get_component_by_name(self, name: str) -> Optional[Component]:
        """Get a component by name."""
        return self._components_by_id.get(name)

    def get_aggregator_by_name(self, name: str) -> Optional[Aggregator]:
        """Get an aggregator by name."""
        return self._aggregators_by_id.get(name)

    def get_runner_by_name(self, name: str) -> Optional[Runner]:
        """Get a runner by name."""
        return self._runners_by_id.get(name)

    # def get_utility_by_name(self, name: str) -> Optional[Utility]:
    #     """Get a utility by name."""
    #     return self._utilities_by_name.get(name)

    def get_test_by_name(self, name: str) -> Optional[TestDefinition]:
        """Get a test by name."""
        return self._tests_by_id.get(name)

    # properties to get all entities
    @property
    def _components(self) -> List[Component]:
        """Get all components as a list."""
        return list(self._components_by_id.values())
    
    @property
    def _aggregators(self) -> List[Aggregator]:
        """Get all aggregators as a list."""
        return list(self._aggregators_by_id.values())
    
    @property
    def _runners(self) -> List[Runner]:
        """Get all runners as a list."""
        return list(self._runners_by_id.values())
    
    @property
    def _tests(self) -> List[TestDefinition]:
        """Get all tests as a list."""
        return list(self._tests_by_id.values())
    
    def get_rig_node_by_name(self, name: str) -> Union[Component, Aggregator, Runner, None]:
        """Get any build node (component, aggregator, runner, or utility) by name."""
        return (self.get_component_by_name(name) or 
                self.get_aggregator_by_name(name) or 
                self.get_runner_by_name(name))

    def get_all_rig_nodes(self) -> List[RIGNode]:
        """Get all build nodes (components, aggregators, runners) as a list."""
        all_nodes = []
        all_nodes.extend(self._components)
        all_nodes.extend(self._aggregators)
        all_nodes.extend(self._runners)
        return all_nodes
    
    def _hydrate_components(self):
        """Hydrate all component nodes to ensure references are set from the IDs."""
        for component in self._components:
            # hydrate external packages
            for external_package_id in component.external_packages_ids:
                # if the external package object is not already in the component's external_packages list, add it
                if not any(ep.id == external_package_id for ep in component.external_packages):
                    external_package_obj = self._external_packages_by_id.get(external_package_id)
                    assert external_package_obj is not None
                    component.external_packages.append(external_package_obj)
                
                    
    def _hydrate_tests(self):
        """Hydrate all test nodes to ensure references are set from the IDs."""
        for test in self._tests:
            # hydrate test_executable_component
            if test.test_executable_component_id is not None and test.test_executable_component is None:
                component_obj = self.get_component_by_name(test.test_executable_component_id)
                assert component_obj is not None
                test.test_executable_component = component_obj
            
            # hydrate test_components
            for test_component_id in test.test_components_ids:
                # if the component object is not already in the test's test_components list, add it
                if not any(comp.id == test_component_id for comp in test.test_components):
                    component_obj = self.get_component_by_name(test_component_id)
                    assert component_obj is not None
                    test.test_components.append(component_obj)
            
            # hydrate components_being_tested
            for tested_component_id in test.components_being_tested_ids:
                # if the component object is not already in the test's components_being_tested list, add it
                if not any(comp.id == tested_component_id for comp in test.components_being_tested):
                    component_obj = self.get_component_by_name(tested_component_id)
                    assert component_obj is not None
                    test.components_being_tested.append(component_obj)
    
    
    def _hydrate_rig_nodes(self):
        for node in self.get_all_rig_nodes():
            # make sure every evidence_id has its evidence object loaded into the test's evidence list
            for evidence_id in node.evidence_ids:
                # if the evidence object is not already in the test's evidence list, add it
                if not any(ev.id == evidence_id for ev in node.evidence):
                    evidence_obj = self._evidence_by_id.get(evidence_id)
                    assert evidence_obj is not None
                    node.evidence.append(evidence_obj)
            
            # hydrate dependencies
            for depends_on_id in node.depends_on_ids:
                # if the dependency object is not already in the test's depends_on list, add it
                if not any(dep.id == depends_on_id for dep in node.depends_on):
                    dependency_obj = self.get_rig_node_by_name(depends_on_id)
                    assert dependency_obj is not None
                    node.depends_on.append(dependency_obj)
    
    def hydrate_all_nodes(self):
        """Hydrate all RIG nodes to ensure references are set from the IDs."""
        self._hydrate_rig_nodes()
        self._hydrate_components()
        self._hydrate_tests()
        
                

    # Statistics and analysis methods
    def get_component_count_by_type(self) -> Dict[ComponentType, int]:
        """Get count of components by type."""
        counts: Dict[ComponentType, int] = {}
        for component in self._components:
            counts[component.type] = counts.get(component.type, 0) + 1
        return counts

    def get_component_count_by_language(self) -> Dict[str, int]:
        """Get count of components by programming language."""
        counts: Dict[str, int] = {}
        for component in self._components:
            counts[component.programming_language] = counts.get(component.programming_language, 0) + 1
        return counts

    def validate(self) -> List[ValidationError]:
        """
        Validate the RIG for correctness and consistency.

        Returns:
            List of validation errors found. Empty list means no issues.
        """
        validator = RIGValidator(self)
        return validator.validate()

    def show_graph(self, validate_before_show: bool = True) -> None:
        """
        Display the RIG as an interactive graph using Cytoscape.js.
        Creates a self-contained HTML file with all JavaScript libraries embedded.

        Args:
            validate_before_show: If True, validate the RIG before showing the graph.
                                If validation fails, raises RIGValidationError.
        """
        visualizer = RIGVisualizer(self)
        visualizer.show_graph(validate_before_show)

    def generate_prompts_json_data(self, optimize: bool = True) -> str:
        """Generate the JSON data section for the prompts."""
        # Basic repository info
        repo_info = {"name": self._repository_info.name if self._repository_info else "Unknown", "root": str(self._repository_info.root_path) if self._repository_info else "Unknown"}

        # Build system info
        build_info = {
            "system": self._build_system_info.name if self._build_system_info else "Unknown",
            "generator": None,  # Removed as per our refactoring
            "type": self._build_system_info.build_type if self._build_system_info else None,
            "configure_cmd": self._repository_info.configure_command if self._repository_info else "",
            "test_cmd": self._repository_info.test_command if self._repository_info else "",
        }

        # Components (topologically sorted, no limit)
        components = self._generate_prompts_components()

        # Aggregators
        aggregators = self._generate_prompts_aggregators()

        # Runners
        runners = self._generate_prompts_runners()

        # Tests
        tests = self._generate_prompts_tests()

        # Supporting data
        external_packages = self._generate_prompts_external_packages()
        package_managers = self._generate_prompts_package_managers()
        evidence = self._generate_prompts_evidence()

        # Combine all data into Pydantic model
        rig_data = RIGPromptData(
            repo=repo_info,
            build=build_info,
            components=components,
            aggregators=aggregators,
            runners=runners,
            tests=tests,
            external_packages=external_packages,
            package_managers=package_managers,
            evidence=evidence
        )

        # Apply optimization if requested
        # TODO: re-enable optimization once optimization method is fixed
        if optimize:
            rig_data = self._optimize_json_for_llm(rig_data)

        # Use Pydantic's JSON serialization (handles sets → lists automatically)
        # exclude_none=True removes null fields for more efficient LLM processing
        return rig_data.model_dump_json(indent=2, exclude_none=True)

    def _generate_prompts_components(self) -> List[Dict[str, Any]]:
        """Generate component data for prompts."""
        components: List[Dict[str, Any]] = []

        for _, component in enumerate(self._components):
            # Use Pydantic serialization with exclusions for flat JSON
            comp_data = component.model_dump(
                exclude={
                    'depends_on',        # Keep depends_on_ids
                    'evidence',           # Keep evidence_ids
                    'external_packages'   # Keep external_packages_ids
                },
                exclude_none=True
            )

            # ID is already generated by Pydantic model, no fallback needed

            components.append(comp_data)

        return components

    def _generate_prompts_aggregators(self) -> List[Dict[str, Any]]:
        """Generate aggregator data for prompts."""
        aggregators: List[Dict[str, Any]] = []

        for _, agg in enumerate(self._aggregators):
            # Use Pydantic serialization with exclusions for flat JSON
            agg_data = agg.model_dump(
                exclude={
                    'depends_on',        # Keep depends_on_ids
                    'evidence'           # Keep evidence_ids
                },
                exclude_none=True
            )

            # ID is already generated by Pydantic model, no fallback needed

            aggregators.append(agg_data)

        return aggregators

    def _generate_prompts_runners(self) -> List[Dict[str, Any]]:
        """Generate runner data for prompts."""
        runners: List[Dict[str, Any]] = []

        for _, runner in enumerate(self._runners):
            # Use Pydantic serialization with exclusions for flat JSON
            runner_data = runner.model_dump(
                exclude={
                    'depends_on',        # Keep depends_on_ids
                    'evidence'           # Keep evidence_ids
                },
                exclude_none=True
            )

            # ID is already generated by Pydantic model, no fallback needed

            runners.append(runner_data)

        return runners

    def _generate_prompts_tests(self) -> List[Dict[str, Any]]:
        """Generate test data for prompts."""
        tests: List[Dict[str, Any]] = []

        for _, test in enumerate(self._tests):
            # Use Pydantic serialization with exclusions for flat JSON
            test_data = test.model_dump(
                exclude={
                    'depends_on',                    # Keep depends_on_ids
                    'evidence',                      # Keep evidence_ids
                    'test_executable_component',     # Keep test_executable_component_id
                    'test_components',               # Keep test_components_ids
                    'components_being_tested'        # Keep components_being_tested_ids
                },
                exclude_none=True
            )

            # ID is already generated by Pydantic model, no fallback needed

            tests.append(test_data)

        return tests

    def _generate_prompts_external_packages(self) -> List[Dict[str, Any]]:
        """Generate external package data for prompts."""
        external_packages: List[Dict[str, Any]] = []

        for _, package in enumerate(self._external_packages_by_id.values()):
            # Use Pydantic serialization with exclusions for flat JSON
            package_data = package.model_dump(
                exclude={
                    'package_manager'  # Keep package_manager_id
                },
                exclude_none=True
            )

            # ID is already generated by Pydantic model, no fallback needed

            external_packages.append(package_data)

        return external_packages

    def _generate_prompts_package_managers(self) -> List[Dict[str, Any]]:
        """Generate package manager data for prompts."""
        package_managers: List[Dict[str, Any]] = []

        for _, manager in enumerate(self._package_managers_by_id.values()):
            # Use Pydantic serialization - no exclusions needed for package managers
            manager_data = manager.model_dump(exclude_none=True)

            # ID is already generated by Pydantic model, no fallback needed

            package_managers.append(manager_data)

        return package_managers

    def _generate_prompts_evidence(self) -> List[Dict[str, Any]]:
        """Generate evidence data for prompts."""
        evidence: List[Dict[str, Any]] = []

        for _, ev in enumerate(self._evidence_by_id.values()):
            # Use Pydantic serialization - no exclusions needed for evidence
            evidence_data = ev.model_dump(exclude_none=True)
            
            # ID is already generated by Pydantic model, no fallback needed
            
            evidence.append(evidence_data)

        return evidence

    @staticmethod
    def _compute_stable_key(entity: Any) -> str:
        """
        Compute a stable, content-based key for an entity.

        This key is deterministic and based on the entity's content rather than
        auto-generated IDs, making it suitable for comparing RIGs generated independently.

        Args:
            entity: Entity to compute key for (Component, Aggregator, Runner, etc.)

        Returns:
            Stable string key
        """
        from core.schemas import Component, Aggregator, Runner, TestDefinition, Evidence, ExternalPackage, PackageManager

        if isinstance(entity, Component):
            # Format: name:type:language
            return f"{entity.name}:{entity.type.value}:{entity.programming_language}"
        elif isinstance(entity, Aggregator):
            # Format: name:aggregator
            return f"{entity.name}:aggregator"
        elif isinstance(entity, Runner):
            # Format: name:runner
            return f"{entity.name}:runner"
        elif isinstance(entity, TestDefinition):
            # Format: name:test:framework
            return f"{entity.name}:test:{entity.test_framework}"
        elif isinstance(entity, Evidence):
            # Format: evidence:first_reference
            # Use first line reference or first call_stack entry as stable identifier
            if entity.line and len(entity.line) > 0:
                ref = entity.line[0]
            elif entity.call_stack and len(entity.call_stack) > 0:
                ref = entity.call_stack[0]
            else:
                ref = "unknown"
            return f"evidence:{ref}"
        elif isinstance(entity, PackageManager):
            # Format: pm:name:package_name
            return f"pm:{entity.name}:{entity.package_name}"
        elif isinstance(entity, ExternalPackage):
            # Format: pkg:name:pm_name
            return f"pkg:{entity.name}:{entity.package_manager.name}"
        else:
            # Fallback for unknown types
            return f"unknown:{getattr(entity, 'name', str(entity))}"

    def _normalize_for_comparison(self) -> "RIG":
        """
        Create a normalized copy of this RIG with stable, content-based IDs.

        This replaces all auto-generated IDs (comp-1, agg-2, etc.) with stable keys
        based on entity content (name:type:language), making it suitable for comparing
        RIGs generated independently.

        Returns:
            New RIG with normalized IDs
        """
        from core.schemas import Component, Aggregator, Runner, TestDefinition

        # Build ID mapping dictionaries: old_id → stable_key
        evidence_map = {e.id: self._compute_stable_key(e) for e in self._evidence_by_id.values()}
        pm_map = {pm.id: self._compute_stable_key(pm) for pm in self._package_managers_by_id.values()}
        ep_map = {ep.id: self._compute_stable_key(ep) for ep in self._external_packages_by_id.values()}
        component_map = {c.id: self._compute_stable_key(c) for c in self._components}
        aggregator_map = {a.id: self._compute_stable_key(a) for a in self._aggregators}
        runner_map = {r.id: self._compute_stable_key(r) for r in self._runners}
        test_map = {t.id: self._compute_stable_key(t) for t in self._tests}

        # Helper to remap ID sets
        def remap_ids(id_set: Optional[Set[str]], mapping: Dict[str, str]) -> Set[str]:
            if not id_set:
                return set()
            return {mapping.get(old_id, old_id) for old_id in id_set}

        # Create normalized RIG
        normalized = RIG()

        # Copy repository and build system info (no IDs to normalize)
        normalized._repository_info = self._repository_info
        normalized._build_system_info = self._build_system_info

        # Normalize evidence (no dependencies to remap)
        for evidence in self._evidence_by_id.values():
            normalized_evidence = evidence.model_copy(deep=True)
            normalized_evidence.id = evidence_map[evidence.id]
            normalized._evidence_by_id[normalized_evidence.id] = normalized_evidence

        # Normalize package managers (no dependencies)
        for pm in self._package_managers_by_id.values():
            normalized_pm = pm.model_copy(deep=True)
            normalized_pm.id = pm_map[pm.id]
            normalized._package_managers_by_id[normalized_pm.id] = normalized_pm

        # Normalize external packages (update package_manager reference)
        for ep in self._external_packages_by_id.values():
            normalized_ep = ep.model_copy(deep=True)
            normalized_ep.id = ep_map[ep.id]
            # Update package_manager reference to use normalized PM
            old_pm_id = ep.package_manager.id
            normalized_ep.package_manager = normalized._package_managers_by_id[pm_map[old_pm_id]]
            normalized._external_packages_by_id[normalized_ep.id] = normalized_ep

        # Normalize components
        for component in self._components:
            normalized_comp = component.model_copy(deep=True)
            normalized_comp.id = component_map[component.id]
            normalized_comp.depends_on_ids = remap_ids(component.depends_on_ids, {**component_map, **aggregator_map, **runner_map})
            normalized_comp.evidence_ids = remap_ids(component.evidence_ids, evidence_map)
            normalized_comp.external_packages_ids = remap_ids(component.external_packages_ids, ep_map)
            normalized._components_by_id[normalized_comp.id] = normalized_comp

        # Normalize aggregators
        for aggregator in self._aggregators:
            normalized_agg = aggregator.model_copy(deep=True)
            normalized_agg.id = aggregator_map[aggregator.id]
            normalized_agg.depends_on_ids = remap_ids(aggregator.depends_on_ids, {**component_map, **aggregator_map, **runner_map})
            normalized_agg.evidence_ids = remap_ids(aggregator.evidence_ids, evidence_map)
            normalized._aggregators_by_id[normalized_agg.id] = normalized_agg

        # Normalize runners
        for runner in self._runners:
            normalized_runner = runner.model_copy(deep=True)
            normalized_runner.id = runner_map[runner.id]
            normalized_runner.depends_on_ids = remap_ids(runner.depends_on_ids, {**component_map, **aggregator_map, **runner_map})
            normalized_runner.evidence_ids = remap_ids(runner.evidence_ids, evidence_map)
            normalized_runner.args_nodes_ids = remap_ids(runner.args_nodes_ids, {**component_map, **aggregator_map, **runner_map, **test_map})
            normalized._runners_by_id[normalized_runner.id] = normalized_runner

        # Normalize tests
        for test in self._tests:
            normalized_test = test.model_copy(deep=True)
            normalized_test.id = test_map[test.id]
            normalized_test.depends_on_ids = remap_ids(test.depends_on_ids, {**component_map, **aggregator_map, **runner_map})
            normalized_test.evidence_ids = remap_ids(test.evidence_ids, evidence_map)
            normalized_test.test_components_ids = remap_ids(test.test_components_ids, component_map)
            normalized_test.components_being_tested_ids = remap_ids(test.components_being_tested_ids, component_map)
            # Update test_executable_component_id if present
            if test.test_executable_component_id:
                if test.test_executable_component_id in component_map:
                    normalized_test.test_executable_component_id = component_map[test.test_executable_component_id]
                elif test.test_executable_component_id in runner_map:
                    normalized_test.test_executable_component_id = runner_map[test.test_executable_component_id]
            normalized._tests_by_id[normalized_test.id] = normalized_test

        return normalized

    @staticmethod
    def _sort_json_for_comparison(data: Any) -> Any:
        """
        Recursively sort JSON data structures for consistent comparison.

        Sorts:
        - Dictionary keys alphabetically
        - Lists by content (using 'name' field if present, else JSON string)

        Args:
            data: JSON-compatible data structure (dict, list, or scalar)

        Returns:
            Sorted version of the input data
        """
        if isinstance(data, dict):
            # Sort dictionary keys and recursively sort values
            return {k: RIG._sort_json_for_comparison(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            # Sort list items by stable key
            sorted_items = []
            for item in data:
                sorted_items.append(RIG._sort_json_for_comparison(item))

            # Try to sort by 'name' field if items are dicts with 'name'
            try:
                if sorted_items and isinstance(sorted_items[0], dict) and 'name' in sorted_items[0]:
                    sorted_items.sort(key=lambda x: x.get('name', ''))
                else:
                    # Fall back to sorting by JSON string representation
                    sorted_items.sort(key=lambda x: json.dumps(x, sort_keys=True))
            except (TypeError, ValueError):
                # If sorting fails, keep original order
                pass

            return sorted_items
        else:
            # Scalar values (str, int, bool, None) - return as is
            return data

    def compare(self, other_rig: "RIG") -> Optional[str]:
        """
        Compare this RIG with another RIG by comparing their JSON representations.

        This method normalizes both RIGs to use stable, content-based IDs before comparison,
        making it suitable for comparing RIGs generated independently. It also sorts all
        lists to ensure ordering doesn't cause false differences.

        Args:
            other_rig: The RIG to compare against

        Returns:
            None if RIGs are identical, diff text string if they differ
        """
        # Normalize both RIGs to use stable IDs (e.g., "hello_world.exe:executable:cxx")
        # instead of auto-generated IDs (e.g., "comp-1", "comp-2")
        self_normalized = self._normalize_for_comparison()
        other_normalized = other_rig._normalize_for_comparison()

        # Generate JSON from normalized RIGs (without optimization for accurate comparison)
        self_json = self_normalized.generate_prompts_json_data(optimize=False)
        other_json = other_normalized.generate_prompts_json_data(optimize=False)

        # Parse JSON strings into dictionaries
        self_data = json.loads(self_json)
        other_data = json.loads(other_json)

        # Sort both data structures for consistent comparison
        self_data_sorted = self._sort_json_for_comparison(self_data)
        other_data_sorted = self._sort_json_for_comparison(other_data)

        # Compare the sorted dictionaries
        if self_data_sorted == other_data_sorted:
            return None

        # Generate unified diff if they differ (using sorted, normalized versions)
        diff = difflib.unified_diff(
            json.dumps(self_data_sorted, indent=2).splitlines(),
            json.dumps(other_data_sorted, indent=2).splitlines(),
            fromfile='self',
            tofile='other',
            lineterm=''
        )
        diff_text = "\n".join(diff)
        return diff_text
    
    def save(self, db_path: Union[str, Path], description: str = "RIG Export") -> None:
        """
        Save RIG to SQLite database.
        Replaces any existing RIG in the database.

        Args:
            db_path: Path to SQLite database file
            description: Description for this RIG export
        """
        from core.rig_store import save_rig
        save_rig(self, db_path, description)
    
    @staticmethod
    def load(db_path: Union[str, Path]) -> 'RIG':
        """
        Load RIG from SQLite database.

        Args:
            db_path: Path to SQLite database file

        Returns:
            Loaded RIG object

        Raises:
            ValueError: If database contains 0 or >1 RIGs
        """
        from core.rig_store import load_rig
        return load_rig(db_path)

    def analyze(self) -> None:
        """
        Deterministic, evidence-only closure over unknowns.
        Mutates self.* in place; never guesses; leaves fields unknown if evidence is
        absent or ambiguous. Returns None.
        """
        # ---------- indices (all deterministic) ----------
        comps: List[Any] = list(getattr(self, "components", []))
        tests: List[Any] = list(getattr(self, "tests", []))
        runners: List[Any] = list(getattr(self, "runners", []))
        utilities: List[Any] = list(getattr(self, "utilities", []))

        name_idx: Dict[str, object] = {getattr(c, "name", ""): c for c in comps if getattr(c, "name", None)}
        # Artifact index by basename/stem (lowercased), across all components with output_path
        artifact_idx: Dict[str, object] = {}
        plugin_dirs: Dict[Path, object] = {}

        for c in comps:
            outp = getattr(c, "output_path", None)
            if outp:
                p = Path(str(outp))
                base = p.name.lower()
                stem = p.stem.lower()
                # allow lookup by "foo", "foo.exe", "foo.dll", etc. (basenames/stems only)
                artifact_idx.setdefault(base, c)
                artifact_idx.setdefault(stem, c)
                if stem + ".exe" not in artifact_idx:
                    artifact_idx[stem + ".exe"] = c
                # for plugin components, remember their directories for ENV dir equality
                # Check if this is a plugin target by looking for plugin tokens in name
                cname = getattr(c, "name", "")
                if any(token in cname.lower() for token in ["openjdk", "python311", "go"]):
                    plugin_dirs.setdefault(p.parent, c)

        # Dependency graph by component name -> set(component names)
        dep_graph: Dict[str, Set[str]] = {}
        for c in comps:
            cname = getattr(c, "name", None)
            if not cname:
                continue
            deps: Set[str] = set()

            # Try common fields that may encode deps as component names or ids
            cand_lists: Iterable[Any] = [
                getattr(c, "dependencies", None),
                getattr(c, "depends_on", None),
                getattr(c, "links_to", None),
            ]
            for L in cand_lists:
                if not L:
                    continue
                for d in L:
                    # accept both name strings and objects with a 'name'
                    if isinstance(d, str):
                        if d in name_idx:
                            deps.add(d)
                    else:
                        dname = getattr(d, "name", None)
                        if dname:
                            deps.add(dname)

            dep_graph[cname] = deps

        # Helper: transitive closure of deps (by names)
        def transitive_deps(cname: str) -> Set[str]:
            seen: Set[str] = set()
            stack: list[str] = [cname]
            out: Set[str] = set()
            while stack:
                cur = stack.pop()
                for nxt in dep_graph.get(cur, set()):
                    if nxt not in seen:
                        seen.add(nxt)
                        out.add(nxt)
                        stack.append(nxt)
            return out

        # ---------- helpers for tests ----------
        def set_test_component(t: Any, comp_obj: object) -> None:
            # prefer setting by name if present
            _ = getattr(comp_obj, "name", None)  # cname not used
            if hasattr(t, "components_being_tested"):
                if not getattr(t, "components_being_tested", None):
                    setattr(t, "components_being_tested", [comp_obj])
                elif comp_obj not in getattr(t, "components_being_tested", []):
                    getattr(t, "components_being_tested", []).append(comp_obj)

        def test_already_mapped(t: Any) -> bool:
            return bool(getattr(t, "components_being_tested", None))

        # Extract possible tokens (without parsing free-form strings)
        def test_tokens(t: Any) -> List[str]:
            toks: List[str] = []
            # Look for test_executable or similar fields
            texe = getattr(t, "test_executable", None)
            if texe:
                toks.append(str(texe))
            return toks

        # ---------- pass 2: test → component via artifact basenames / genex expansions ----------
        for t in tests:
            if test_already_mapped(t):
                continue

            candidates: Set[object] = set()

            # a) explicit test_executable field (exact path)
            texe = getattr(t, "test_executable", None)
            if texe:
                base = Path(str(texe)).name.lower()
                if base in artifact_idx:
                    candidates.add(artifact_idx[base])

            # b) command tokens that look like filenames → basename match
            for tok in test_tokens(t):
                base = Path(str(tok)).name.lower()
                if base in artifact_idx:
                    candidates.add(artifact_idx[base])

            if len(candidates) == 1:
                set_test_component(t, next(iter(candidates)))
                continue
            # otherwise: leave unmapped here; other passes may help

        # Done with test mapping passes.

    
    def _optimize_json_for_llm(self, data: RIGPromptData) -> RIGPromptData:
        """Return the same RIGPromptData object, but make its JSON output LLM-friendly.

        - Deduplicate path-like and frequent long strings via lookup tables.
        - Apply short key aliases for high-frequency inner keys in the JSON view.
        - Do not mutate semantic content; only override serialization.
        - If optimized output is not smaller, leave serialization intact.
        """
        from collections import Counter
        import json
        import types

        # Build a plain dict from the model
        base_dict = data.model_dump(exclude_none=True, mode="json")

        # Collect strings and identify paths
        string_counter: Counter[str] = Counter()
        path_candidates: set[str] = set()

        path_suffixes = {
            'c', 'cc', 'cpp', 'cxx', 'h', 'hpp', 'hxx', 'py', 'java', 'go', 'cs',
            'js', 'ts', 'json', 'yaml', 'yml', 'toml', 'cmake', 'ini', 'cfg', 'dll', 'exe'
        }

        def is_path(value: str) -> bool:
            if len(value) < 4:
                return False
            if '/' in value or '\\' in value:
                return True
            if '.' not in value:
                return False
            ext = value.rsplit('.', 1)[-1].lower()
            return ext in path_suffixes

        def scan(node):
            if isinstance(node, str):
                string_counter[node] += 1
                if is_path(node):
                    path_candidates.add(node)
                return
            if isinstance(node, dict):
                for v in node.values():
                    scan(v)
                return
            if isinstance(node, list):
                for v in node:
                    scan(v)

        scan(base_dict)

        # Lookups (stable order)
        sorted_paths = sorted(path_candidates)
        path_to_idx = {p: i for i, p in enumerate(sorted_paths)}

        frequent_strings = [s for s, c in string_counter.items() if c >= 3 and len(s) > 12 and s not in path_to_idx]
        sorted_strings = sorted(frequent_strings)
        string_to_idx = {s: i for i, s in enumerate(sorted_strings)}

        # Compact key aliases
        key_alias = {
            'components': 'comp',
            'aggregators': 'agg',
            'runners': 'run',
            'tests': 'test',
            'external_packages': 'extpkg',
            'package_managers': 'pkgmgr',
            'source_files': 'sf',
            'depends_on_ids': 'deps',
            'external_packages_ids': 'extdeps',
            'evidence_ids': 'evid',
            'programming_language': 'lang',
            'relative_path': 'rel',
            'test_components_ids': 'tcomp',
            'components_being_tested_ids': 'cbt',
            'test_executable_component_id': 'texe',
            'call_stack': 'cs',
            'package_name': 'pkg',
            'package_manager': 'pm',
            'configure_cmd': 'cfg',
            'test_cmd': 'tcmd',
            'test_framework': 'tf',
        }
        reverse_key_alias = {alias: key for key, alias in key_alias.items()}

        def transform(node):
            if isinstance(node, str):
                if node in path_to_idx:
                    return f"$p{path_to_idx[node]}"
                if node in string_to_idx:
                    return f"$s{string_to_idx[node]}"
                return node
            if isinstance(node, list):
                return [transform(v) for v in node]
            if isinstance(node, dict):
                out = {}
                for k, v in node.items():
                    k2 = key_alias.get(k, k)
                    out[k2] = transform(v)
                return out
            return node

        optimized_payload = transform(base_dict)
        lookups = { 'paths': sorted_paths, 'strings': sorted_strings, 'keys': reverse_key_alias }
        optimized = { 'lookups': lookups, 'data': optimized_payload }

        optimized_compact = json.dumps(optimized, separators=(',', ':'), ensure_ascii=False)
        original_compact = data.model_dump_json(exclude_none=True, indent=None)

        if len(optimized_compact) >= len(original_compact):
            # No improvement; keep original serializer
            return data

        # Return a subclass instance that overrides JSON serialization only.
        from typing import Any as _Any
        class _OptimizedRIGPromptData(type(data)):
            def model_dump_json(self, *args: _Any, **kwargs: _Any) -> str:  # type: ignore[override]
                indent = kwargs.get('indent') if 'indent' in kwargs else (args[0] if args else None)
                if indent is None:
                    return optimized_compact
                import json as _json
                return _json.dumps(optimized, indent=indent, ensure_ascii=False)

        return _OptimizedRIGPromptData(**data.model_dump(exclude_none=False))


