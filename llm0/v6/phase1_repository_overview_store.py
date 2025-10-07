"""
V6 Phase 1: Repository Overview Store

This module defines the phase-specific memory store for repository overview analysis.
The store maintains information about repository structure, build systems, and exploration scope.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .base_agent_v6 import BasePhaseStore


@dataclass
class DirectoryStructure:
    """Directory structure information."""
    source_dirs: List[str] = field(default_factory=list)
    test_dirs: List[str] = field(default_factory=list)
    build_dirs: List[str] = field(default_factory=list)
    config_dirs: List[str] = field(default_factory=list)


@dataclass
class ExplorationScope:
    """Exploration scope information."""
    priority_dirs: List[str] = field(default_factory=list)
    skip_dirs: List[str] = field(default_factory=list)
    deep_exploration: List[str] = field(default_factory=list)


class RepositoryOverviewStore(BasePhaseStore):
    """Phase 1 store for repository overview information."""
    
    def __init__(self):
        super().__init__()
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.primary_language: Optional[str] = None
        self.build_systems: List[str] = []
        self.directory_structure = DirectoryStructure()
        self.entry_points: List[str] = []
        self.exploration_scope = ExplorationScope()
        self.evidence: List[Dict[str, Any]] = []
    
    def set_name(self, name: str) -> str:
        """Set repository name."""
        self.name = name
        return f"Repository name set to: {name}"
    
    def set_type(self, repo_type: str) -> str:
        """Set repository type."""
        valid_types = ["application", "library", "framework", "tool"]
        if repo_type not in valid_types:
            return f"Invalid type '{repo_type}'. Must be one of: {valid_types}"
        self.type = repo_type
        return f"Repository type set to: {repo_type}"
    
    def set_primary_language(self, language: str) -> str:
        """Set primary programming language."""
        self.primary_language = language
        return f"Primary language set to: {language}"
    
    def add_build_system(self, build_system: str) -> str:
        """Add a build system."""
        if build_system not in self.build_systems:
            self.build_systems.append(build_system)
            return f"Added build system: {build_system}"
        return f"Build system '{build_system}' already exists"
    
    def add_source_dir(self, dir_path: str) -> str:
        """Add a source directory."""
        if dir_path not in self.directory_structure.source_dirs:
            self.directory_structure.source_dirs.append(dir_path)
            return f"Added source directory: {dir_path}"
        return f"Source directory '{dir_path}' already exists"
    
    def add_test_dir(self, dir_path: str) -> str:
        """Add a test directory."""
        if dir_path not in self.directory_structure.test_dirs:
            self.directory_structure.test_dirs.append(dir_path)
            return f"Added test directory: {dir_path}"
        return f"Test directory '{dir_path}' already exists"
    
    def add_build_dir(self, dir_path: str) -> str:
        """Add a build directory."""
        if dir_path not in self.directory_structure.build_dirs:
            self.directory_structure.build_dirs.append(dir_path)
            return f"Added build directory: {dir_path}"
        return f"Build directory '{dir_path}' already exists"
    
    def add_config_dir(self, dir_path: str) -> str:
        """Add a config directory."""
        if dir_path not in self.directory_structure.config_dirs:
            self.directory_structure.config_dirs.append(dir_path)
            return f"Added config directory: {dir_path}"
        return f"Config directory '{dir_path}' already exists"
    
    def add_entry_point(self, entry_point: str) -> str:
        """Add an entry point file."""
        if entry_point not in self.entry_points:
            self.entry_points.append(entry_point)
            return f"Added entry point: {entry_point}"
        return f"Entry point '{entry_point}' already exists"
    
    def add_priority_dir(self, dir_path: str) -> str:
        """Add a priority directory for exploration."""
        if dir_path not in self.exploration_scope.priority_dirs:
            self.exploration_scope.priority_dirs.append(dir_path)
            return f"Added priority directory: {dir_path}"
        return f"Priority directory '{dir_path}' already exists"
    
    def add_skip_dir(self, dir_path: str) -> str:
        """Add a directory to skip during exploration."""
        if dir_path not in self.exploration_scope.skip_dirs:
            self.exploration_scope.skip_dirs.append(dir_path)
            return f"Added skip directory: {dir_path}"
        return f"Skip directory '{dir_path}' already exists"
    
    def add_deep_exploration_dir(self, dir_path: str) -> str:
        """Add a directory for deep exploration."""
        if dir_path not in self.exploration_scope.deep_exploration:
            self.exploration_scope.deep_exploration.append(dir_path)
            return f"Added deep exploration directory: {dir_path}"
        return f"Deep exploration directory '{dir_path}' already exists"
    
    def add_evidence(self, evidence: Dict[str, Any]) -> str:
        """Add evidence for the repository overview."""
        self.evidence.append(evidence)
        return f"Added evidence: {evidence.get('description', 'Unknown evidence')}"
    
    def validate(self) -> List[str]:
        """Validate the repository overview store."""
        errors = []
        
        if not self.name:
            errors.append("Repository name is required")
        
        if not self.type:
            errors.append("Repository type is required")
        
        if not self.primary_language:
            errors.append("Primary language is required")
        
        if not self.build_systems:
            errors.append("At least one build system is required")
        
        if not self.directory_structure.source_dirs:
            errors.append("At least one source directory is required")
        
        if not self.entry_points:
            errors.append("At least one entry point is required")
        
        if not self.exploration_scope.priority_dirs:
            errors.append("At least one priority directory is required")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the repository overview."""
        return {
            "name": self.name,
            "type": self.type,
            "primary_language": self.primary_language,
            "build_systems": self.build_systems,
            "directory_structure": {
                "source_dirs": self.directory_structure.source_dirs,
                "test_dirs": self.directory_structure.test_dirs,
                "build_dirs": self.directory_structure.build_dirs,
                "config_dirs": self.directory_structure.config_dirs
            },
            "entry_points": self.entry_points,
            "exploration_scope": {
                "priority_dirs": self.exploration_scope.priority_dirs,
                "skip_dirs": self.exploration_scope.skip_dirs,
                "deep_exploration": self.exploration_scope.deep_exploration
            },
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
