"""
V6 Phase 4: Build System Store

This module defines the phase-specific memory store for build system analysis.
The store maintains information about build configurations, targets, and build dependencies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .base_agent_v6 import BasePhaseStore


@dataclass
class BuildTarget:
    """Build target information."""
    name: str
    type: str  # executable, library, test, etc.
    source_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    build_flags: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BuildConfiguration:
    """Build configuration information."""
    name: str
    type: str  # debug, release, test, etc.
    compiler_flags: List[str] = field(default_factory=list)
    linker_flags: List[str] = field(default_factory=list)
    defines: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


class BuildSystemStore(BasePhaseStore):
    """Phase 4 store for build system information."""
    
    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from previous phases
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
            self.build_systems = getattr(phase1_store, 'build_systems', [])
        else:
            self.repository_name = 'unknown'
            self.build_systems = []
        
        if previous_stores and len(previous_stores) > 1:
            phase2_store = previous_stores[1]
            self.source_components = getattr(phase2_store, 'components', [])
        else:
            self.source_components = []
        if previous_stores and len(previous_stores) > 2:
            phase3_store = previous_stores[2]
            self.test_components = getattr(phase3_store, 'test_components', [])
        else:
            self.test_components = []
        
        # Phase 4 specific fields
        self.build_targets: List[BuildTarget] = []
        self.build_configurations: List[BuildConfiguration] = []
        self.build_dependencies: Dict[str, List[str]] = {}
        self.build_scripts: List[str] = []
        self.build_artifacts: List[str] = []
        self.build_environment: Dict[str, Any] = {}
        self.evidence: List[Dict[str, Any]] = []
    
    def add_build_target(self, name: str, target_type: str, output_path: str = None) -> str:
        """Add a build target."""
        # Check if build target already exists
        existing = next((bt for bt in self.build_targets if bt.name == name), None)
        if existing:
            return f"Build target '{name}' already exists"
        
        build_target = BuildTarget(
            name=name,
            type=target_type,
            output_path=output_path
        )
        self.build_targets.append(build_target)
        return f"Added build target: {name} ({target_type})"
    
    def add_target_source_file(self, target_name: str, source_file: str) -> str:
        """Add a source file to a build target."""
        target = next((bt for bt in self.build_targets if bt.name == target_name), None)
        if not target:
            return f"Build target '{target_name}' not found"
        
        if source_file not in target.source_files:
            target.source_files.append(source_file)
            return f"Added source file '{source_file}' to target '{target_name}'"
        return f"Source file '{source_file}' already exists in target '{target_name}'"
    
    def add_target_dependency(self, target_name: str, dependency: str) -> str:
        """Add a dependency to a build target."""
        target = next((bt for bt in self.build_targets if bt.name == target_name), None)
        if not target:
            return f"Build target '{target_name}' not found"
        
        if dependency not in target.dependencies:
            target.dependencies.append(dependency)
            return f"Added dependency '{dependency}' to target '{target_name}'"
        return f"Dependency '{dependency}' already exists in target '{target_name}'"
    
    def add_target_build_flag(self, target_name: str, flag: str) -> str:
        """Add a build flag to a build target."""
        target = next((bt for bt in self.build_targets if bt.name == target_name), None)
        if not target:
            return f"Build target '{target_name}' not found"
        
        if flag not in target.build_flags:
            target.build_flags.append(flag)
            return f"Added build flag '{flag}' to target '{target_name}'"
        return f"Build flag '{flag}' already exists in target '{target_name}'"
    
    def add_target_evidence(self, target_name: str, evidence: Dict[str, Any]) -> str:
        """Add evidence to a build target."""
        target = next((bt for bt in self.build_targets if bt.name == target_name), None)
        if not target:
            return f"Build target '{target_name}' not found"
        
        target.evidence.append(evidence)
        return f"Added evidence to build target '{target_name}': {evidence.get('description', 'Unknown evidence')}"
    
    def add_build_configuration(self, name: str, config_type: str) -> str:
        """Add a build configuration."""
        # Check if configuration already exists
        existing = next((bc for bc in self.build_configurations if bc.name == name), None)
        if existing:
            return f"Build configuration '{name}' already exists"
        
        config = BuildConfiguration(name=name, type=config_type)
        self.build_configurations.append(config)
        return f"Added build configuration: {name} ({config_type})"
    
    def add_config_compiler_flag(self, config_name: str, flag: str) -> str:
        """Add a compiler flag to a build configuration."""
        config = next((bc for bc in self.build_configurations if bc.name == config_name), None)
        if not config:
            return f"Build configuration '{config_name}' not found"
        
        if flag not in config.compiler_flags:
            config.compiler_flags.append(flag)
            return f"Added compiler flag '{flag}' to configuration '{config_name}'"
        return f"Compiler flag '{flag}' already exists in configuration '{config_name}'"
    
    def add_config_linker_flag(self, config_name: str, flag: str) -> str:
        """Add a linker flag to a build configuration."""
        config = next((bc for bc in self.build_configurations if bc.name == config_name), None)
        if not config:
            return f"Build configuration '{config_name}' not found"
        
        if flag not in config.linker_flags:
            config.linker_flags.append(flag)
            return f"Added linker flag '{flag}' to configuration '{config_name}'"
        return f"Linker flag '{flag}' already exists in configuration '{config_name}'"
    
    def add_config_define(self, config_name: str, define: str) -> str:
        """Add a preprocessor define to a build configuration."""
        config = next((bc for bc in self.build_configurations if bc.name == config_name), None)
        if not config:
            return f"Build configuration '{config_name}' not found"
        
        if define not in config.defines:
            config.defines.append(define)
            return f"Added define '{define}' to configuration '{config_name}'"
        return f"Define '{define}' already exists in configuration '{config_name}'"
    
    def add_config_evidence(self, config_name: str, evidence: Dict[str, Any]) -> str:
        """Add evidence to a build configuration."""
        config = next((bc for bc in self.build_configurations if bc.name == config_name), None)
        if not config:
            return f"Build configuration '{config_name}' not found"
        
        config.evidence.append(evidence)
        return f"Added evidence to build configuration '{config_name}': {evidence.get('description', 'Unknown evidence')}"
    
    def add_build_dependency(self, target: str, dependency: str) -> str:
        """Add a build dependency."""
        if target not in self.build_dependencies:
            self.build_dependencies[target] = []
        
        if dependency not in self.build_dependencies[target]:
            self.build_dependencies[target].append(dependency)
            return f"Added build dependency '{dependency}' to target '{target}'"
        return f"Build dependency '{dependency}' already exists for target '{target}'"
    
    def add_build_script(self, script_path: str) -> str:
        """Add a build script."""
        if script_path not in self.build_scripts:
            self.build_scripts.append(script_path)
            return f"Added build script: {script_path}"
        return f"Build script '{script_path}' already exists"
    
    def add_build_artifact(self, artifact_path: str) -> str:
        """Add a build artifact."""
        if artifact_path not in self.build_artifacts:
            self.build_artifacts.append(artifact_path)
            return f"Added build artifact: {artifact_path}"
        return f"Build artifact '{artifact_path}' already exists"
    
    def add_build_environment(self, key: str, value: str) -> str:
        """Add build environment information."""
        self.build_environment[key] = value
        return f"Added build environment: {key} = {value}"
    
    def add_evidence(self, evidence: Dict[str, Any]) -> str:
        """Add evidence for the build system."""
        self.evidence.append(evidence)
        return f"Added evidence: {evidence.get('description', 'Unknown evidence')}"
    
    def validate(self) -> List[str]:
        """Validate the build system store."""
        errors = []
        
        if not self.build_targets:
            errors.append("At least one build target is required")
        
        if not self.build_configurations:
            errors.append("At least one build configuration is required")
        
        # Validate build targets
        for target in self.build_targets:
            if not target.source_files:
                errors.append(f"Build target '{target.name}' has no source files")
            if not target.type:
                errors.append(f"Build target '{target.name}' has no type specified")
        
        # Validate build configurations
        for config in self.build_configurations:
            if not config.type:
                errors.append(f"Build configuration '{config.name}' has no type specified")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the build system."""
        return {
            "repository_name": self.repository_name,
            "build_systems": self.build_systems,
            "build_targets_count": len(self.build_targets),
            "build_targets": [
                {
                    "name": bt.name,
                    "type": bt.type,
                    "source_files_count": len(bt.source_files),
                    "dependencies_count": len(bt.dependencies),
                    "output_path": bt.output_path
                }
                for bt in self.build_targets
            ],
            "build_configurations_count": len(self.build_configurations),
            "build_configurations": [
                {
                    "name": bc.name,
                    "type": bc.type,
                    "compiler_flags_count": len(bc.compiler_flags),
                    "linker_flags_count": len(bc.linker_flags),
                    "defines_count": len(bc.defines)
                }
                for bc in self.build_configurations
            ],
            "build_dependencies": self.build_dependencies,
            "build_scripts": self.build_scripts,
            "build_artifacts": self.build_artifacts,
            "build_environment": self.build_environment,
            "evidence_count": len(self.evidence)
        }
