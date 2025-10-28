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


class RIGToolsV4:
    """Tools for direct RIG manipulation in V4+ Phase 8."""
    
    def __init__(self, rig_instance: RIG):
        self.rig = rig_instance
        self.logger = logging.getLogger("RIGToolsV4")
    
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
            self.rig._repository_info = repo_info
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
            
            self.rig._build_system_info = build_info
            return f"Added build system info: {name} {version} ({build_type})"
        except Exception as e:
            self.logger.error(f"Failed to add build system info: {e}")
            return f"Error adding build system info: {e}"
    
    def add_component(self, name: str, type: str, programming_language: str = "unknown",
                     runtime: str = "unknown", source_files: List[str] = None,
                     output_path: str = "unknown", dependencies: List[str] = None,
                     evidence: List[Dict] = None) -> str:
        """Add a component to the RIG."""
        try:
            # Convert runtime string to enum
            runtime_enum = getattr(Runtime, runtime.upper(), Runtime.UNKNOWN)
            
            # Convert type to ComponentType enum
            type_enum = getattr(ComponentType, type.upper(), ComponentType.EXECUTABLE)
            
            # Create evidence object
            evidence_obj = Evidence(call_stack=[])
            if evidence and len(evidence) > 0:
                evidence_obj = Evidence(
                    call_stack=evidence[0].get('call_stack', [])
                )
            
            # Create component with required fields
            component = Component(
                name=name,
                type=type_enum,
                programming_language=programming_language,
                runtime=runtime_enum,
                output=name,  # Required field
                output_path=Path(output_path),
                source_files=[Path(f) for f in (source_files or [])],
                external_packages=[],  # Default empty list
                locations=[],  # Default empty list
                evidence=evidence_obj,
                depends_on=[]  # Default empty list
            )
            
            # Add to RIG
            self.rig.add_component(component)
            return f"Added component: {name} ({type}, {programming_language})"
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
    
    def add_relationship(self, source: str, target: str, relationship_type: str, 
                        evidence: List[Dict] = None) -> str:
        """Add a relationship between components (placeholder - relationships handled in components)."""
        try:
            # For now, relationships are handled through component dependencies
            # This is a placeholder for future relationship support
            return f"Relationship noted: {source} -> {target} ({relationship_type}) - handled through component dependencies"
        except Exception as e:
            self.logger.error(f"Failed to add relationship {source} -> {target}: {e}")
            return f"Error adding relationship {source} -> {target}: {e}"
    
    def get_rig_state(self) -> str:
        """Get current RIG state summary."""
        try:
            components_count = len(self.rig._components) if self.rig._components else 0
            tests_count = len(self.rig._tests) if self.rig._tests else 0
            
            state = f"RIG State: {components_count} components, {tests_count} tests"
            
            if self.rig._repository_info:
                state += f", Repository: {self.rig._repository_info.name}"
            if self.rig._build_system_info:
                state += f", Build System: {self.rig._build_system_info.name}"
            
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
            if not self.rig._repository_info:
                validation_result["errors"].append("Missing repository information")
                validation_result["is_valid"] = False
            
            # Check build system info
            if not self.rig._build_system_info:
                validation_result["warnings"].append("Missing build system information")
            
            # Check components
            if not self.rig._components or len(self.rig._components) == 0:
                validation_result["errors"].append("No components found")
                validation_result["is_valid"] = False
            
            # Check tests
            if not self.rig._tests or len(self.rig._tests) == 0:
                validation_result["warnings"].append("No tests found")
            
            # Relationships are handled through component dependencies
            # No separate relationship validation needed
            
            # Summary
            validation_result["summary"] = {
                "components": len(self.rig._components) if self.rig._components else 0,
                "tests": len(self.rig._tests) if self.rig._tests else 0,
                "repository": self.rig._repository_info.name if self.rig._repository_info else "Missing",
                "build_system": self.rig._build_system_info.name if self.rig._build_system_info else "Missing"
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
