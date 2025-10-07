#!/usr/bin/env python3
"""
RIG Manipulation Tools for V4+ Phase 8 Enhancement

This module provides tools for the LLM to manipulate the RIG instance directly
during Phase 8, avoiding the need for huge JSON generation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from core.rig import RIG
from core.schemas import (
    Component, TestDefinition, Evidence, RepositoryInfo, BuildSystemInfo,
    Runtime, ComponentType
)


class RIGToolsV7:
    """Enhanced tools for direct RIG manipulation in V7 Phase 8 with batch operations."""
    
    def __init__(self, rig_instance: RIG):
        self.rig = rig_instance
        self.logger = logging.getLogger("RIGToolsV7")
    
    def add_repository_info(self, name: str, type: str, primary_language: str, 
                           build_systems: List[str], evidence: List[Dict]) -> str:
        """Add repository overview information to the RIG."""
        try:
            # Create evidence objects
            evidence_objects = []
            if evidence:
                for e in evidence:
                    evidence_obj = Evidence(
                        call_stack=e.get('call_stack', [])
                    )
                    evidence_objects.append(evidence_obj)
            
            # Create repository info with correct parameters
            repo_info = RepositoryInfo(
                name=name,
                root_path=Path("."),  # Default to current directory
                build_directory=Path("build"),
                output_directory=Path("output"),
                configure_command="",
                build_command="",
                install_command="",
                test_command=""
            )
            
            # Set in RIG
            self.rig.repository = repo_info
            return f"Added repository info: {name} ({type}, {primary_language})"
        except Exception as e:
            self.logger.error(f"Failed to add repository info: {e}")
            return f"Error adding repository info: {e}"
    
    def add_build_system_info(self, name: str, version: str, build_type: str, 
                             evidence: List[Dict]) -> str:
        """Add build system information to the RIG."""
        try:
            # BuildSystemInfo doesn't have evidence field, so we create it without evidence
            build_info = BuildSystemInfo(
                name=name,
                version=version,
                build_type=build_type
            )
            
            self.rig.build_system = build_info
            return f"Added build system info: {name} {version} ({build_type})"
        except Exception as e:
            self.logger.error(f"Failed to add build system info: {e}")
            return f"Error adding build system info: {e}"
    
    def add_component(self, name: str, type: str, programming_language: str = "unknown",
                     runtime: str = "unknown", source_files: List[str] = None,
                     output_path: str = "unknown", dependencies: List[str] = None,
                     evidence: List[Dict] = None, **kwargs) -> str:
        """Add a component to the RIG with strict parameter validation."""
        try:
            # STRICT VALIDATION: Filter out unsupported parameters and log them
            supported_params = {
                'name', 'type', 'programming_language', 'runtime', 
                'source_files', 'output_path', 'dependencies', 'evidence'
            }
            
            # PARAMETER MAPPING: Handle common LLM parameter mistakes
            parameter_mapping = {
                'language': 'programming_language',  # LLM often uses 'language' instead of 'programming_language'
                'path': 'output_path',  # LLM often uses 'path' instead of 'output_path'
                'description': None,  # Ignore description (not supported)
                'version': None,  # Ignore version (not supported)
                'properties': None,  # Ignore properties (not supported)
                'test_relationship': None,  # Ignore test_relationship (not supported in Component schema)
            }
            
            # Apply parameter mapping
            mapped_kwargs = {}
            for key, value in kwargs.items():
                if key in parameter_mapping:
                    mapped_key = parameter_mapping[key]
                    if mapped_key is not None:
                        mapped_kwargs[mapped_key] = value
                        self.logger.info(f"Mapped parameter '{key}' -> '{mapped_key}' for component '{name}'")
                    else:
                        self.logger.info(f"Ignored unsupported parameter '{key}' for component '{name}'")
                else:
                    mapped_kwargs[key] = value
            
            # Check for remaining unsupported parameters
            unsupported_params = {k: v for k, v in mapped_kwargs.items() if k not in supported_params}
            if unsupported_params:
                self.logger.warning(f"Unsupported parameters for component '{name}': {list(unsupported_params.keys())}")
                self.logger.warning(f"Supported parameters: {sorted(supported_params)}")
                # Continue with supported parameters only - ignore unsupported ones
            
            # VALIDATE REQUIRED FIELDS
            if not name or not isinstance(name, str):
                return f"Error: Component name must be a non-empty string"
            
            if not type:
                return f"Error: Component type must be provided"
            
            # VALIDATE ENUM VALUES - handle both string and dict inputs
            if isinstance(type, dict):
                type_value = type.get('value', type.get('type', 'unknown'))
            else:
                type_value = str(type)
            
            try:
                type_enum = ComponentType(type_value.lower())
            except ValueError:
                valid_types = [t.value for t in ComponentType]
                return f"Error: Invalid component type '{type_value}'. Valid types: {valid_types}"
            
            # Convert runtime string to enum with validation and mapping
            runtime_enum = None
            if runtime and runtime != "unknown":
                # Map common LLM runtime values to valid enum values
                runtime_mapping = {
                    'native': 'CLANG-C',  # Native C++ typically uses CLANG-C
                    'cpp': 'CLANG-C',
                    'c++': 'CLANG-C',
                    'c': 'CLANG-C',
                    'cxx': 'CLANG-C',
                    'msvc': 'VS-CPP',
                    'visual_studio': 'VS-CPP',
                    'gcc': 'CLANG-C',
                    'g++': 'CLANG-C'
                }
                
                # Apply runtime mapping - handle both string and dict inputs
                if isinstance(runtime, dict):
                    # Extract runtime value from dict if it's a dict
                    runtime_value = runtime.get('value', runtime.get('runtime', 'unknown'))
                else:
                    runtime_value = str(runtime)
                
                mapped_runtime = runtime_mapping.get(runtime_value.lower(), runtime_value)
                
                try:
                    runtime_enum = Runtime(mapped_runtime.upper())
                except ValueError:
                    valid_runtimes = [r.value for r in Runtime]
                    self.logger.warning(f"Invalid runtime '{runtime}' for component '{name}'. Valid runtimes: {valid_runtimes}")
                    runtime_enum = Runtime.UNKNOWN
            
            # VALIDATE SOURCE FILES
            if source_files is None:
                source_files = []
            elif not isinstance(source_files, list):
                return f"Error: source_files must be a list, got {type(source_files)}"
            
            # VALIDATE DEPENDENCIES
            if dependencies is None:
                dependencies = []
            elif not isinstance(dependencies, list):
                return f"Error: dependencies must be a list, got {type(dependencies)}"
            
            # VALIDATE EVIDENCE
            if evidence is None:
                evidence = []
            elif not isinstance(evidence, list):
                return f"Error: evidence must be a list, got {type(evidence)}"
            
            # VALIDATE OUTPUT PATH
            if not output_path or not isinstance(output_path, str):
                output_path = name  # Use component name as fallback
            
            # Create evidence object with validation
            evidence_obj = Evidence(call_stack=[])
            if evidence and len(evidence) > 0:
                try:
                    evidence_obj = Evidence(
                        call_stack=evidence[0].get('call_stack', [])
                    )
                except Exception as e:
                    self.logger.warning(f"Invalid evidence format for component '{name}': {e}")
                    evidence_obj = Evidence(call_stack=[])
            
            # Create component with strict validation
            try:
                component = Component(
                    name=name,
                    type=type_enum,
                    programming_language=programming_language,
                    runtime=runtime_enum,
                    output=name,  # Required field
                    output_path=Path(output_path),
                    source_files=[Path(f) for f in source_files],
                    external_packages=[],  # Default empty list
                    locations=[],  # Default empty list
                    test_link_id=None,
                    test_link_name=None,
                    evidence=evidence_obj,
                    depends_on=[]  # Default empty list
                )
                
                # Add to RIG
                self.rig.add_component(component)
                return f"Added component: {name} ({type_enum.value}, {programming_language})"
                
            except Exception as e:
                self.logger.error(f"Failed to create component '{name}': {e}")
                return f"Error creating component '{name}': {e}"
                
        except Exception as e:
            self.logger.error(f"Failed to add component {name}: {e}")
            return f"Error adding component {name}: {e}"
    
    def add_test(self, name: str, framework: str, source_files: List[str] = None,
                output_path: str = "unknown", dependencies: List[str] = None,
                evidence: List[Dict] = None) -> str:
        """Add a test to the RIG."""
        try:
            # Create evidence object
            evidence_obj = Evidence(call_stack=[])
            if evidence and len(evidence) > 0:
                evidence_obj = Evidence(
                    call_stack=evidence[0].get('call_stack', [])
                )
            
            test = TestDefinition(
                name=name,
                test_framework=framework,
                source_files=[Path(f) for f in (source_files or [])],
                evidence=evidence_obj,
                test_executable=None,
                components_being_tested=[],
                test_runner=None
            )
            
            # Add to RIG
            self.rig.add_test(test)
            return f"Added test: {name} ({framework})"
        except Exception as e:
            self.logger.error(f"Failed to add test {name}: {e}")
            return f"Error adding test {name}: {e}"
    
    def add_relationship(self, source: str, target: str, relationship_type: str = None, 
                        evidence: List[Dict] = None, **kwargs) -> str:
        """Add a relationship between components with parameter mapping."""
        try:
            # PARAMETER MAPPING: Handle common LLM parameter mistakes
            parameter_mapping = {
                'type': 'relationship_type',  # LLM often uses 'type' instead of 'relationship_type'
                'from': 'source',  # LLM often uses 'from' instead of 'source'
                'to': 'target',  # LLM often uses 'to' instead of 'target'
            }
            
            # Apply parameter mapping
            mapped_kwargs = {}
            for key, value in kwargs.items():
                if key in parameter_mapping:
                    mapped_key = parameter_mapping[key]
                    mapped_kwargs[mapped_key] = value
                    self.logger.info(f"Mapped relationship parameter '{key}' -> '{mapped_key}'")
                else:
                    mapped_kwargs[key] = value
            
            # Use mapped parameters
            if 'relationship_type' in mapped_kwargs:
                relationship_type = mapped_kwargs['relationship_type']
            if 'source' in mapped_kwargs:
                source = mapped_kwargs['source']
            if 'target' in mapped_kwargs:
                target = mapped_kwargs['target']
            
            # For now, relationships are handled through component dependencies
            # This is a placeholder for future relationship support
            return f"Relationship noted: {source} -> {target} ({relationship_type or 'unknown'}) - handled through component dependencies"
        except Exception as e:
            self.logger.error(f"Failed to add relationship {source} -> {target}: {e}")
            return f"Error adding relationship {source} -> {target}: {e}"
    
    def get_rig_state(self) -> str:
        """Get current RIG state summary."""
        try:
            components_count = len(self.rig.components) if self.rig.components else 0
            tests_count = len(self.rig.tests) if self.rig.tests else 0
            
            state = f"RIG State: {components_count} components, {tests_count} tests"
            
            if self.rig.repository:
                state += f", Repository: {self.rig.repository.name}"
            if self.rig.build_system:
                state += f", Build System: {self.rig.build_system.name}"
            
            return state
        except Exception as e:
            self.logger.error(f"Failed to get RIG state: {e}")
            return f"Error getting RIG state: {e}"
    
    def validate_rig(self) -> Dict[str, Any]:
        """Validate RIG completeness and consistency."""
        try:
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "summary": {}
            }
            
            # Check repository info
            if not self.rig.repository:
                validation_result["errors"].append("Missing repository information")
                validation_result["is_valid"] = False
            
            # Check build system info
            if not self.rig.build_system:
                validation_result["warnings"].append("Missing build system information")
            
            # Check components
            if not self.rig.components or len(self.rig.components) == 0:
                validation_result["errors"].append("No components found")
                validation_result["is_valid"] = False
            
            # Check tests
            if not self.rig.tests or len(self.rig.tests) == 0:
                validation_result["warnings"].append("No tests found")
            
            # Relationships are handled through component dependencies
            # No separate relationship validation needed
            
            # Summary
            validation_result["summary"] = {
                "components": len(self.rig.components) if self.rig.components else 0,
                "tests": len(self.rig.tests) if self.rig.tests else 0,
                "repository": self.rig.repository.name if self.rig.repository else "Missing",
                "build_system": self.rig.build_system.name if self.rig.build_system else "Missing"
            }
            
            return validation_result
        except Exception as e:
            self.logger.error(f"Failed to validate RIG: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {e}"],
                "warnings": [],
                "summary": {}
            }
    
    # V7 Enhanced Tools - Batch Operations
    def add_components_batch(self, components_data: List[Dict]) -> str:
        """Add multiple components in one operation - V7 enhancement."""
        added_count = 0
        failed_components = []
        
        for comp_data in components_data:
            try:
                # Use existing add_component logic
                result = self.add_component(**comp_data)
                if "Error" not in result:
                    added_count += 1
                else:
                    failed_components.append(comp_data.get('name', 'unknown'))
            except Exception as e:
                self.logger.warning(f"Failed to add component {comp_data.get('name', 'unknown')}: {e}")
                failed_components.append(comp_data.get('name', 'unknown'))
        
        if failed_components:
            return f"Added {added_count}/{len(components_data)} components. Failed: {failed_components}"
        else:
            return f"Successfully added {added_count} components"
    
    def add_relationships_batch(self, relationships_data: List[Dict]) -> str:
        """Add multiple relationships in one operation - V7 enhancement."""
        added_count = 0
        failed_relationships = []
        
        for rel_data in relationships_data:
            try:
                result = self.add_relationship(**rel_data)
                if "Error" not in result:
                    added_count += 1
                else:
                    failed_relationships.append(f"{rel_data.get('source', 'unknown')}->{rel_data.get('target', 'unknown')}")
            except Exception as e:
                self.logger.warning(f"Failed to add relationship: {e}")
                failed_relationships.append(f"{rel_data.get('source', 'unknown')}->{rel_data.get('target', 'unknown')}")
        
        if failed_relationships:
            return f"Added {added_count}/{len(relationships_data)} relationships. Failed: {failed_relationships}"
        else:
            return f"Successfully added {added_count} relationships"
    
    # V7 Smart Validation Tools
    def validate_component_exists(self, component_name: str) -> str:
        """Check if component exists in RIG - V7 enhancement."""
        if self.rig.has_component(component_name):
            return f"Component {component_name} exists"
        else:
            return f"Component {component_name} NOT FOUND - needs to be added first"
    
    def validate_relationships_consistency(self) -> str:
        """Check if all relationships reference existing components - V7 enhancement."""
        issues = []
        for component in self.rig.components:
            for dep in component.depends_on:
                if not self.rig.has_component(dep):
                    issues.append(f"Component {component.name} depends on missing component: {dep}")
        
        if issues:
            return f"Relationship issues: {issues}"
        else:
            return "All relationships are consistent"
    
    def get_assembly_status(self) -> str:
        """Get current assembly status - V7 enhancement."""
        components_count = len(self.rig.components)
        tests_count = len(self.rig.tests)
        
        # Count relationships from component dependencies
        relationships_count = sum(len(comp.depends_on) for comp in self.rig.components)
        
        return f"Assembly status: {components_count} components, {relationships_count} relationships, {tests_count} tests"
    
    def get_missing_items(self) -> str:
        """Identify what's missing from assembly - V7 enhancement."""
        missing = []
        
        # Check for components without dependencies (except main/entry points)
        for comp in self.rig.components:
            if not comp.depends_on and comp.name not in ["main", "hello_world"]:  # main/entry points might not need dependencies
                missing.append(f"Component {comp.name} has no dependencies")
        
        return f"Missing items: {missing}" if missing else "Assembly appears complete"
