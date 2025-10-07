"""
V6 Phase 2: Source Structure Store

This module defines the phase-specific memory store for source structure discovery.
The store maintains information about source components, languages, and file organization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .base_agent_v6 import BasePhaseStore


@dataclass
class SourceComponent:
    """Source component information."""
    name: str
    path: str
    language: str
    type: str  # main, library, utility, etc.
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LanguageAnalysis:
    """Language analysis information."""
    primary_language: str
    secondary_languages: List[str] = field(default_factory=list)
    language_distribution: Dict[str, int] = field(default_factory=dict)
    file_patterns: Dict[str, List[str]] = field(default_factory=dict)


class SourceStructureStore(BasePhaseStore):
    """Phase 2 store for source structure information."""
    
    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from Phase 1 (constructor-based handoff)
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.source_dirs_to_explore = getattr(phase1_store, 'directory_structure', {}).get('source_dirs', [])
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
            self.build_systems = getattr(phase1_store, 'build_systems', [])
            self.primary_language = getattr(phase1_store, 'primary_language', 'unknown')
        else:
            # Default values if no previous stores
            self.source_dirs_to_explore = []
            self.repository_name = 'unknown'
            self.build_systems = []
            self.primary_language = 'unknown'
        
        # Phase 2 specific fields
        self.components: List[SourceComponent] = []
        self.language_analysis = LanguageAnalysis(primary_language=self.primary_language)
        self.file_organization: Dict[str, List[str]] = {}
        self.build_dependencies: Dict[str, List[str]] = {}
        self.evidence: List[Dict[str, Any]] = []
    
    def add_component(self, name: str, path: str, language: str, component_type: str) -> str:
        """Add a source component."""
        # Check if component already exists
        existing = next((c for c in self.components if c.name == name), None)
        if existing:
            return f"Component '{name}' already exists"
        
        component = SourceComponent(
            name=name,
            path=path,
            language=language,
            type=component_type
        )
        self.components.append(component)
        return f"Added component: {name} ({component_type}) at {path}"
    
    def add_component_file(self, component_name: str, file_path: str) -> str:
        """Add a file to a component."""
        component = next((c for c in self.components if c.name == component_name), None)
        if not component:
            return f"Component '{component_name}' not found"
        
        if file_path not in component.files:
            component.files.append(file_path)
            return f"Added file '{file_path}' to component '{component_name}'"
        return f"File '{file_path}' already exists in component '{component_name}'"
    
    def add_component_dependency(self, component_name: str, dependency: str) -> str:
        """Add a dependency to a component."""
        component = next((c for c in self.components if c.name == component_name), None)
        if not component:
            return f"Component '{component_name}' not found"
        
        if dependency not in component.dependencies:
            component.dependencies.append(dependency)
            return f"Added dependency '{dependency}' to component '{component_name}'"
        return f"Dependency '{dependency}' already exists in component '{component_name}'"
    
    def add_component_evidence(self, component_name: str, evidence: Dict[str, Any]) -> str:
        """Add evidence to a component."""
        component = next((c for c in self.components if c.name == component_name), None)
        if not component:
            return f"Component '{component_name}' not found"
        
        component.evidence.append(evidence)
        return f"Added evidence to component '{component_name}': {evidence.get('description', 'Unknown evidence')}"
    
    def add_secondary_language(self, language: str) -> str:
        """Add a secondary programming language."""
        if language not in self.language_analysis.secondary_languages:
            self.language_analysis.secondary_languages.append(language)
            return f"Added secondary language: {language}"
        return f"Secondary language '{language}' already exists"
    
    def update_language_distribution(self, language: str, count: int) -> str:
        """Update language distribution count."""
        self.language_analysis.language_distribution[language] = count
        return f"Updated language distribution: {language} = {count} files"
    
    def add_file_pattern(self, language: str, pattern: str) -> str:
        """Add a file pattern for a language."""
        if language not in self.language_analysis.file_patterns:
            self.language_analysis.file_patterns[language] = []
        
        if pattern not in self.language_analysis.file_patterns[language]:
            self.language_analysis.file_patterns[language].append(pattern)
            return f"Added file pattern for {language}: {pattern}"
        return f"File pattern '{pattern}' already exists for {language}"
    
    def add_file_organization(self, category: str, files: List[str]) -> str:
        """Add file organization information."""
        if category not in self.file_organization:
            self.file_organization[category] = []
        
        for file_path in files:
            if file_path not in self.file_organization[category]:
                self.file_organization[category].append(file_path)
        
        return f"Added {len(files)} files to organization category '{category}'"
    
    def add_build_dependency(self, component: str, dependency: str) -> str:
        """Add a build dependency."""
        if component not in self.build_dependencies:
            self.build_dependencies[component] = []
        
        if dependency not in self.build_dependencies[component]:
            self.build_dependencies[component].append(dependency)
            return f"Added build dependency '{dependency}' to component '{component}'"
        return f"Build dependency '{dependency}' already exists for component '{component}'"
    
    def add_evidence(self, evidence: Dict[str, Any]) -> str:
        """Add evidence for the source structure."""
        self.evidence.append(evidence)
        return f"Added evidence: {evidence.get('description', 'Unknown evidence')}"
    
    def validate(self) -> List[str]:
        """Validate the source structure store."""
        errors = []
        
        if not self.components:
            errors.append("At least one source component is required")
        
        if not self.language_analysis.primary_language:
            errors.append("Primary language is required")
        
        if not self.file_organization:
            errors.append("File organization information is required")
        
        # Validate components
        for component in self.components:
            if not component.files:
                errors.append(f"Component '{component.name}' has no files")
            if not component.language:
                errors.append(f"Component '{component.name}' has no language specified")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the source structure."""
        return {
            "repository_name": self.repository_name,
            "components_count": len(self.components),
            "components": [
                {
                    "name": c.name,
                    "path": c.path,
                    "language": c.language,
                    "type": c.type,
                    "files_count": len(c.files),
                    "dependencies_count": len(c.dependencies)
                }
                for c in self.components
            ],
            "language_analysis": {
                "primary_language": self.language_analysis.primary_language,
                "secondary_languages": self.language_analysis.secondary_languages,
                "language_distribution": self.language_analysis.language_distribution,
                "file_patterns": self.language_analysis.file_patterns
            },
            "file_organization": self.file_organization,
            "build_dependencies": self.build_dependencies,
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
