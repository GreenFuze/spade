"""
V6 Phase 3: Test Structure Store

This module defines the phase-specific memory store for test structure discovery.
The store maintains information about test frameworks, test components, and test organization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .base_agent_v6 import BasePhaseStore


@dataclass
class TestComponent:
    """Test component information."""
    name: str
    path: str
    framework: str
    type: str  # unit, integration, e2e, etc.
    files: List[str] = field(default_factory=list)
    test_targets: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestFramework:
    """Test framework information."""
    name: str
    version: Optional[str] = None
    configuration_files: List[str] = field(default_factory=list)
    test_runner: Optional[str] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)


class TestStructureStore(BasePhaseStore):
    """Phase 3 store for test structure information."""
    
    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from previous phases (constructor-based handoff)
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
            self.build_systems = getattr(phase1_store, 'build_systems', [])
            self.test_dirs_to_explore = getattr(phase1_store, 'directory_structure', {}).get('test_dirs', [])
        else:
            # Default values if no previous stores
            self.repository_name = 'unknown'
            self.build_systems = []
            self.test_dirs_to_explore = []
            
        if previous_stores and len(previous_stores) > 1:
            phase2_store = previous_stores[1]
            self.source_components = getattr(phase2_store, 'components', [])
        else:
            self.source_components = []
        
        # Phase 3 specific fields
        self.test_components: List[TestComponent] = []
        self.test_frameworks: List[TestFramework] = []
        self.test_directories: List[str] = []
        self.test_configuration: Dict[str, Any] = {}
        self.test_organization: Dict[str, List[str]] = {}
        self.evidence: List[Dict[str, Any]] = []
    
    def add_test_component(self, name: str, path: str, framework: str, test_type: str) -> str:
        """Add a test component."""
        # Check if test component already exists
        existing = next((tc for tc in self.test_components if tc.name == name), None)
        if existing:
            return f"Test component '{name}' already exists"
        
        test_component = TestComponent(
            name=name,
            path=path,
            framework=framework,
            type=test_type
        )
        self.test_components.append(test_component)
        return f"Added test component: {name} ({test_type}) at {path}"
    
    def add_test_component_file(self, component_name: str, file_path: str) -> str:
        """Add a file to a test component."""
        component = next((tc for tc in self.test_components if tc.name == component_name), None)
        if not component:
            return f"Test component '{component_name}' not found"
        
        if file_path not in component.files:
            component.files.append(file_path)
            return f"Added file '{file_path}' to test component '{component_name}'"
        return f"File '{file_path}' already exists in test component '{component_name}'"
    
    def add_test_target(self, component_name: str, target: str) -> str:
        """Add a test target to a test component."""
        component = next((tc for tc in self.test_components if tc.name == component_name), None)
        if not component:
            return f"Test component '{component_name}' not found"
        
        if target not in component.test_targets:
            component.test_targets.append(target)
            return f"Added test target '{target}' to component '{component_name}'"
        return f"Test target '{target}' already exists in component '{component_name}'"
    
    def add_test_component_evidence(self, component_name: str, evidence: Dict[str, Any]) -> str:
        """Add evidence to a test component."""
        component = next((tc for tc in self.test_components if tc.name == component_name), None)
        if not component:
            return f"Test component '{component_name}' not found"
        
        component.evidence.append(evidence)
        return f"Added evidence to test component '{component_name}': {evidence.get('description', 'Unknown evidence')}"
    
    def add_test_framework(self, name: str, version: str = None) -> str:
        """Add a test framework."""
        # Check if framework already exists
        existing = next((tf for tf in self.test_frameworks if tf.name == name), None)
        if existing:
            return f"Test framework '{name}' already exists"
        
        framework = TestFramework(name=name, version=version)
        self.test_frameworks.append(framework)
        return f"Added test framework: {name}" + (f" (version {version})" if version else "")
    
    def add_framework_config_file(self, framework_name: str, config_file: str) -> str:
        """Add a configuration file to a test framework."""
        framework = next((tf for tf in self.test_frameworks if tf.name == framework_name), None)
        if not framework:
            return f"Test framework '{framework_name}' not found"
        
        if config_file not in framework.configuration_files:
            framework.configuration_files.append(config_file)
            return f"Added config file '{config_file}' to framework '{framework_name}'"
        return f"Config file '{config_file}' already exists in framework '{framework_name}'"
    
    def set_framework_runner(self, framework_name: str, runner: str) -> str:
        """Set the test runner for a framework."""
        framework = next((tf for tf in self.test_frameworks if tf.name == framework_name), None)
        if not framework:
            return f"Test framework '{framework_name}' not found"
        
        framework.test_runner = runner
        return f"Set test runner for '{framework_name}': {runner}"
    
    def add_framework_evidence(self, framework_name: str, evidence: Dict[str, Any]) -> str:
        """Add evidence to a test framework."""
        framework = next((tf for tf in self.test_frameworks if tf.name == framework_name), None)
        if not framework:
            return f"Test framework '{framework_name}' not found"
        
        framework.evidence.append(evidence)
        return f"Added evidence to framework '{framework_name}': {evidence.get('description', 'Unknown evidence')}"
    
    def add_test_directory(self, dir_path: str) -> str:
        """Add a test directory."""
        if dir_path not in self.test_directories:
            self.test_directories.append(dir_path)
            return f"Added test directory: {dir_path}"
        return f"Test directory '{dir_path}' already exists"
    
    def add_test_configuration(self, key: str, value: str) -> str:
        """Add test configuration information."""
        self.test_configuration[key] = value
        return f"Added test configuration: {key} = {value}"
    
    def add_test_organization(self, category: str, files: List[str]) -> str:
        """Add test organization information."""
        if category not in self.test_organization:
            self.test_organization[category] = []
        
        for file_path in files:
            if file_path not in self.test_organization[category]:
                self.test_organization[category].append(file_path)
        
        return f"Added {len(files)} files to test organization category '{category}'"
    
    def add_evidence(self, evidence: Dict[str, Any]) -> str:
        """Add evidence for the test structure."""
        self.evidence.append(evidence)
        return f"Added evidence: {evidence.get('description', 'Unknown evidence')}"
    
    def validate(self) -> List[str]:
        """Validate the test structure store."""
        errors = []
        
        if not self.test_frameworks:
            errors.append("At least one test framework is required")
        
        if not self.test_organization:
            errors.append("Test organization information is required")
        
        # Validate test components
        for component in self.test_components:
            if not component.files:
                errors.append(f"Test component '{component.name}' has no files")
            if not component.framework:
                errors.append(f"Test component '{component.name}' has no framework specified")
        
        # Validate test frameworks
        for framework in self.test_frameworks:
            if not framework.configuration_files:
                errors.append(f"Test framework '{framework.name}' has no configuration files")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the test structure."""
        return {
            "repository_name": self.repository_name,
            "test_components_count": len(self.test_components),
            "test_components": [
                {
                    "name": tc.name,
                    "path": tc.path,
                    "framework": tc.framework,
                    "type": tc.type,
                    "files_count": len(tc.files),
                    "test_targets_count": len(tc.test_targets)
                }
                for tc in self.test_components
            ],
            "test_frameworks_count": len(self.test_frameworks),
            "test_frameworks": [
                {
                    "name": tf.name,
                    "version": tf.version,
                    "config_files_count": len(tf.configuration_files),
                    "test_runner": tf.test_runner
                }
                for tf in self.test_frameworks
            ],
            "test_directories": self.test_directories,
            "test_configuration": self.test_configuration,
            "test_organization": self.test_organization,
            "evidence_count": len(self.evidence)
        }
