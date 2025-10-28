from pathlib import Path

from cmake_file_api.kinds.cache.v2 import CacheV2
from cmake_file_api.kinds.codemodel.target.v2 import TargetType
from cmake_file_api.kinds.codemodel.v2 import CMakeTarget
from cmake_file_api.kinds.toolchains.v1 import ToolchainsV1

import core.schemas
from typing import Tuple, Optional, Set, Dict, List, Union
from core.schemas import Component, Aggregator, Runner, TestDefinition, NodeType


# enum rig

class CMakeTargetWrapper:
    def __init__(self, target: CMakeTarget, cmake_toolchains: ToolchainsV1, cmake_cache: CacheV2, repo_root: Path):
        
        assert isinstance(target, CMakeTarget)
        
        self._cmake_target = target
        self._cmake_toolchains = cmake_toolchains
        self._cmake_cache = cmake_cache
        self._repo_root = repo_root

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def cmake_target(self)->CMakeTarget:
        return self._cmake_target

    @property
    def name(self) -> str:
        return self._cmake_target.target.nameOnDisk

    @property
    def toolchains(self) -> ToolchainsV1:
        return self._cmake_toolchains

    @property
    def dependencies(self) -> List['CMakeTargetWrapper']:
        """Return list of dependency target wrappers."""
        
        if self._cmake_target.target.dependencies is None:
            return []
        
        res = []
        for dep in self._cmake_target.target.dependencies:
            found = False
            for dep_target in self._cmake_target.project.targets:
                if dep.id == dep_target.target.id:
                    res.append(CMakeTargetWrapper(dep_target, self._cmake_toolchains, self._cmake_cache, self.repo_root))
                    found = True
                    break
            
            if not found:
                raise ValueError(f"Failed to find Dependency target {dep.id} in the project targets")
        
        return res

    def get_rig_node_type(self) -> core.schemas.NodeType|None:
        """ detect target node type

        if target has an output, its a component
        if a target has *only* dependencies, its an aggregator
        if a target executes a command and has no output, its a runner
        if a target executes test (as a test platform), its a test

        If none relevant to RIG, returns None
        """

        tt: TargetType = self._cmake_target.target.type
        if tt == TargetType.UTILITY:
            return None
        else:
            return core.schemas.NodeType.COMPONENT

    def _resolve_dependencies(
        self,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]],
        visited: Set[str],
        target_id: str
    ) -> Tuple[List[Union[Component, Aggregator, Runner, TestDefinition]], Set[str]]:
        """Common dependency resolution logic with cycle detection.

        Args:
            findings: Cache of already-created nodes
            visited: Set of CMake target IDs currently being visited
            target_id: CMake target ID of this node

        Returns:
            Tuple of (depends_on list, depends_on_ids set)

        Raises:
            ValueError: If circular dependency detected
        """
        # Check for cycle
        if target_id in visited:
            cycle_path = " -> ".join(visited) + f" -> {self._cmake_target.name}"
            raise ValueError(f"Circular dependency detected: {cycle_path}")

        # Add ourselves to visited (immutable - create new set)
        new_visited = visited | {target_id}

        # Resolve dependencies recursively
        depends_on = []
        depends_on_ids = set()

        for dep_wrapper in self.dependencies:
            dep_type = dep_wrapper.get_rig_node_type()

            if dep_type is None:
                continue  # Skip non-RIG targets (e.g., UTILITY)

            # Call appropriate method based on type
            if dep_type == NodeType.COMPONENT:
                dep_node = dep_wrapper.get_as_rig_component(findings, new_visited)
            elif dep_type == NodeType.AGGREGATOR:
                dep_node = dep_wrapper.get_as_rig_aggregator(findings, new_visited)
            elif dep_type == NodeType.RUNNER:
                dep_node = dep_wrapper.get_as_rig_runner(findings, new_visited)
            elif dep_type == NodeType.TEST_DEFINITION:
                dep_node = dep_wrapper.get_as_rig_test_def(findings, new_visited)
            else:
                raise ValueError(f"Unknown dependency type: {dep_type}")

            depends_on.append(dep_node)
            depends_on_ids.add(dep_node.id)

        return depends_on, depends_on_ids

    def _cache_node(
        self,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]],
        node_type: NodeType,
        target_id: str,
        node: Union[Component, Aggregator, Runner, TestDefinition]
    ) -> None:
        """Cache a created node."""
        if node_type not in findings:
            findings[node_type] = {}
        findings[node_type][target_id] = node
        
    
    
    def get_as_rig_component(
        self,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]],
        visited: Optional[Set[str]] = None
    ) -> Component:
        """Convert to RIG component node with recursive dependency resolution.

        Args:
            findings: Cache of already-created nodes by type and CMake target ID
            visited: Set of CMake target IDs currently being visited (for cycle detection)

        Returns:
            Component object

        Raises:
            ValueError: If circular dependency detected
        """
        if visited is None:
            visited = set()

        target_id = self._cmake_target.target.id

        # Check cache
        if target_id in findings.get(NodeType.COMPONENT, {}):
            return findings[NodeType.COMPONENT][target_id]

        # Resolve dependencies (handles cycle detection)
        depends_on, depends_on_ids = self._resolve_dependencies(findings, visited, target_id)

        # Lazy import to avoid circular dependency
        from deterministic.cmake.cmake_target_rig_component import CMakeTargetRigComponent

        cmake_rig_component = CMakeTargetRigComponent(self, self._cmake_cache)
        component_type = cmake_rig_component.get_component_type()
        component_programming_language = cmake_rig_component.get_programming_language()
        component_source_files = cmake_rig_component.get_source_files()
        component_relative_path = cmake_rig_component.get_relative_path()
        component_locations = cmake_rig_component.get_locations()
        component_external_packages = cmake_rig_component.get_external_packages()
        component_evidence = cmake_rig_component.get_evidence()

        component = Component(name=self.name, type=component_type, programming_language=component_programming_language,
            source_files=component_source_files, relative_path=component_relative_path,
            depends_on=depends_on, evidence=component_evidence, locations=component_locations,
            external_packages=component_external_packages)
    
        # Cache and return
        self._cache_node(findings, NodeType.COMPONENT, target_id, component)
        return component

    def get_as_rig_aggregator(
        self,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]],
        visited: Optional[Set[str]] = None
    ) -> Aggregator:
        """Convert to RIG aggregator node with recursive dependency resolution.

        Args:
            findings: Cache of already-created nodes by type and CMake target ID
            visited: Set of CMake target IDs currently being visited (for cycle detection)

        Returns:
            Aggregator object

        Raises:
            ValueError: If circular dependency detected
        """
        if visited is None:
            visited = set()

        target_id = self._cmake_target.target.id

        # Check cache
        if target_id in findings.get(NodeType.AGGREGATOR, {}):
            return findings[NodeType.AGGREGATOR][target_id]

        # Resolve dependencies (handles cycle detection)
        depends_on, depends_on_ids = self._resolve_dependencies(findings, visited, target_id)

        # Lazy import to avoid circular dependency
        from deterministic.cmake.cmake_target_rig_aggregator import CMakeTargetRigAggregator

        # Extract aggregator properties using helper
        cmake_rig_aggregator = CMakeTargetRigAggregator(self)
        aggregator_name = cmake_rig_aggregator.get_name()
        aggregator_evidence = cmake_rig_aggregator.get_evidence()

        # Create Aggregator object
        aggregator = Aggregator(
            name=aggregator_name,
            depends_on=depends_on,
            evidence=aggregator_evidence
        )

        # Cache and return
        self._cache_node(findings, NodeType.AGGREGATOR, target_id, aggregator)
        return aggregator

    def get_as_rig_runner(
        self,
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]],
        visited: Optional[Set[str]] = None
    ) -> Runner:
        """Convert to RIG runner node with recursive dependency resolution.

        Args:
            findings: Cache of already-created nodes by type and CMake target ID
            visited: Set of CMake target IDs currently being visited (for cycle detection)

        Returns:
            Runner object

        Raises:
            ValueError: If circular dependency detected
        """
        if visited is None:
            visited = set()

        target_id = self._cmake_target.target.id

        # Check cache
        if target_id in findings.get(NodeType.RUNNER, {}):
            return findings[NodeType.RUNNER][target_id]

        # Resolve dependencies (handles cycle detection)
        depends_on, depends_on_ids = self._resolve_dependencies(findings, visited, target_id)

        # Lazy import to avoid circular dependency
        from deterministic.cmake.cmake_target_rig_runner import CMakeTargetRigRunner

        # Extract runner properties using helper
        cmake_rig_runner = CMakeTargetRigRunner(self)
        runner_name = cmake_rig_runner.get_name()
        runner_evidence = cmake_rig_runner.get_evidence()
        runner_arguments = cmake_rig_runner.get_arguments()
        runner_args_nodes = cmake_rig_runner.get_args_nodes()

        # Create Runner object
        runner = Runner(
            name=runner_name,
            depends_on=depends_on,
            evidence=runner_evidence,
            arguments=runner_arguments,
            args_nodes=runner_args_nodes,
            args_nodes_ids={node.id for node in runner_args_nodes}
        )

        # Cache and return
        self._cache_node(findings, NodeType.RUNNER, target_id, runner)
        return runner
