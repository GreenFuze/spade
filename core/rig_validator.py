"""
RIG Validator - Validates Repository Intelligence Graph for correctness and consistency.

This module provides the RIGValidator class that performs comprehensive validation
of RIG data structures, checking for missing files, broken dependencies, circular
dependencies, and other consistency issues.
"""

from pathlib import Path
from typing import List, Dict

from core.schemas import (
    Component,
    ValidationError, ValidationSeverity, ComponentType, ValidationErrorCategory, RIGNode, Runner
)


class RIGValidator:
    """
    Validates Repository Intelligence Graph for correctness and consistency.
    
    This class performs comprehensive validation of RIG data structures,
    checking for missing files, broken dependencies, circular dependencies,
    and other consistency issues.
    """
    
    def __init__(self, rig):
        """
        Initialize the validator with a RIG instance.
        
        Args:
            rig: The RIG instance to validate
        """
        self.rig = rig
    
    def validate(self) -> List[ValidationError]:
        """
        Validate the RIG for correctness and consistency.

        Returns:
            List of validation errors found. Empty list means no issues.
        """
        errors: List[ValidationError] = []
        
        # make sure all nodes are hydrated
        self.rig.hydrate_all_nodes()

        # Run all validation checks
        errors.extend(self._validate_missing_source_files())
        errors.extend(self._validate_broken_dependencies())
        errors.extend(self._validate_circular_dependencies())
        errors.extend(self._validate_duplicate_node_ids())
        errors.extend(self._validate_test_relationships())
        errors.extend(self._validate_evidence_consistency())

        return errors

    def _validate_missing_source_files(self) -> List[ValidationError]:
        """Validate that all referenced source files exist."""
        errors: List[ValidationError] = []

        if not self.rig._repository_info:
            return errors

        for component in self.rig._components:
            for source_file in component.source_files:
               
                # Handle both relative and absolute paths
                if source_file.is_absolute():
                    full_path = source_file
                else:
                    full_path = self.rig._repository_info.root_path / source_file

                if not full_path.exists():
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationErrorCategory.MISSING_SOURCE_FILE,
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
        for node in self.rig.get_all_rig_nodes():
            all_node_names.add(node.name)

        for node in self.rig.get_all_rig_nodes():
            for dep in node.depends_on:
                if dep.name not in all_node_names:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR, 
                            category=ValidationErrorCategory.BROKEN_DEPENDENCY,
                            message=f"Dependency '{dep.name}' does not exist", 
                            node_name=node.name, 
                            suggestion="Check if the dependency name is correct or if the target was removed"
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
        for node in self.rig.get_all_rig_nodes():
            dep_graph[node.name] = [dep.name for dep in node.depends_on]

        # Check for cycles
        visited: set[str] = set()
        for node_name in dep_graph:
            if node_name in visited:
                continue
                
            if has_cycle(node_name, visited, set(), dep_graph):
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationErrorCategory.CIRCULAR_DEPENDENCY,
                        message=f"Circular dependency detected involving node '{node_name}'",
                        node_name=node_name,
                        suggestion="Review the dependency chain to break the circular reference",
                    )
                )
                break  # Only report one cycle to reduce noise

        return errors

    def _validate_duplicate_node_ids(self) -> List[ValidationError]:
        """Validate that all node names are unique."""
        errors: List[ValidationError] = []

        all_nodes = self.rig.get_all_rig_nodes()
        name_counts: Dict[str, int] = {}

        for node in all_nodes:
            name_counts[node.id] = name_counts.get(node.id, 0) + 1

        for name, count in name_counts.items():
            if count > 1:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR, 
                        category=ValidationErrorCategory.DUPLICATE_NODE_ID,
                        message=f"Node name '{name}' is used by {count} different nodes", 
                        node_name=name, 
                        suggestion="Ensure all node names are unique across the entire RIG"
                    )
                )

        return errors

    def _validate_test_relationships(self) -> List[ValidationError]:
        """Validate test relationships and structure."""
        errors: List[ValidationError] = []

        # Check that tests have proper relationships
        for test in self.rig._tests:
            if test.test_executable_component is None:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationErrorCategory.MISSING_TEST_EXECUTABLE,
                        message=f"Test '{test.name}' has no test executable component defined",
                        node_name=test.name,
                        suggestion="Each test should have an associated test executable component",
                    )
                )
                continue
            
            if isinstance(test.test_executable_component, Component):
                if test.test_executable_component.id not in self.rig._components_by_id:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationErrorCategory.TEST_EXECUTABLE_COMPONENT_NOT_FOUND,
                            message=f"Test '{test.name}' references a test executable component that does not exist in the RIG",
                            node_name=test.name,
                            suggestion="Ensure the test executable component is correctly added to the RIG",
                        )
                    )

            if isinstance(test.test_executable_component, Runner):
                if test.test_executable_component.id not in self.rig._runners_by_id:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationErrorCategory.TEST_EXECUTABLE_COMPONENT_NOT_FOUND,
                            message=f"Test '{test.name}' references a test executable component that does not exist in the RIG",
                            node_name=test.name,
                            suggestion="Ensure the test executable component is correctly added to the RIG",
                        )
                    )
            
            
        return errors

    def _validate_evidence_consistency(self) -> List[ValidationError]:
        """Validate that evidence information is consistent."""
        errors: List[ValidationError] = []

        # Check that all nodes have evidence
        for node in self.rig.get_all_rig_nodes():
            if node.evidence is None or len(node.evidence) == 0:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationErrorCategory.MISSING_EVIDENCE,
                        message=f"Node '{node.name}' has no evidence information", 
                        node_name=node.name, 
                        suggestion="All nodes should have evidence indicating where they are defined"
                    )
                )

        return errors
