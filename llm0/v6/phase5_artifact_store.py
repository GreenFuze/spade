from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm0.v6.base_agent_v6 import BasePhaseStore

@dataclass
class Artifact:
    """Represents a build artifact."""
    name: str
    type: str  # e.g., executable, library, package
    path: str
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)

class ArtifactStore(BasePhaseStore):
    """Phase 5 store for artifact discovery information."""

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

        # Phase 5 specific fields
        self.artifacts: List[Artifact] = []
        self.artifact_types: List[str] = []
        self.build_output_dirs: List[str] = []
        self.evidence: List[str] = []

    def add_artifact(self, name: str, type: str, path: str) -> str:
        """Add a build artifact."""
        artifact = Artifact(name=name, type=type, path=path)
        self.artifacts.append(artifact)
        return f"Artifact added: {name} ({type}) at {path}"

    def add_artifact_file(self, artifact_name: str, file_path: str) -> str:
        """Add a file to an artifact."""
        for artifact in self.artifacts:
            if artifact.name == artifact_name:
                artifact.files.append(file_path)
                return f"File {file_path} added to artifact {artifact_name}"
        return f"Artifact {artifact_name} not found"

    def add_artifact_dependency(self, artifact_name: str, dependency: str) -> str:
        """Add a dependency to an artifact."""
        for artifact in self.artifacts:
            if artifact.name == artifact_name:
                artifact.dependencies.append(dependency)
                return f"Dependency {dependency} added to artifact {artifact_name}"
        return f"Artifact {artifact_name} not found"

    def classify_artifact(self, artifact_name: str, classification: str) -> str:
        """Classify an artifact type."""
        for artifact in self.artifacts:
            if artifact.name == artifact_name:
                artifact.type = classification
                return f"Artifact {artifact_name} classified as {classification}"
        return f"Artifact {artifact_name} not found"

    def add_artifact_type(self, type: str) -> str:
        """Add an artifact type."""
        if type not in self.artifact_types:
            self.artifact_types.append(type)
        return f"Artifact type added: {type}"

    def add_build_output_dir(self, path: str) -> str:
        """Add a build output directory."""
        if path not in self.build_output_dirs:
            self.build_output_dirs.append(path)
        return f"Build output directory added: {path}"

    def add_evidence(self, evidence_item: str) -> str:
        """Add evidence."""
        self.evidence.append(evidence_item)
        return f"Evidence added: {evidence_item}"

    def validate(self) -> List[str]:
        """Validate the store."""
        errors = []
        if not self.artifacts:
            errors.append("At least one artifact must be identified")
        return errors

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the artifact store."""
        return {
            "repository_name": self.repository_name,
            "artifacts_count": len(self.artifacts),
            "artifacts": [
                {
                    "name": a.name,
                    "type": a.type,
                    "path": a.path,
                    "files_count": len(a.files),
                    "dependencies_count": len(a.dependencies)
                }
                for a in self.artifacts
            ],
            "artifact_types": self.artifact_types,
            "build_output_dirs": self.build_output_dirs,
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
