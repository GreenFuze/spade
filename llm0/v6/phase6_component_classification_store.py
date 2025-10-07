from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm0.v6.base_agent_v6 import BasePhaseStore

@dataclass
class ClassifiedComponent:
    """Represents a classified component."""
    name: str
    rig_type: str  # EXECUTABLE, LIBRARY, TEST, PACKAGE_LIBRARY, etc.
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)

class ComponentClassificationStore(BasePhaseStore):
    """Phase 6 store for component classification information."""

    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from previous phases
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
        else:
            self.repository_name = 'unknown'

        # Phase 6 specific fields
        self.classified_components: List[ClassifiedComponent] = []
        self.rig_types: List[str] = []
        self.evidence: List[str] = []

    def classify_component(self, name: str, rig_type: str) -> str:
        """Classify a component into a RIG type."""
        component = ClassifiedComponent(name=name, rig_type=rig_type, path="")
        self.classified_components.append(component)
        if rig_type not in self.rig_types:
            self.rig_types.append(rig_type)
        return f"Component {name} classified as {rig_type}"

    def add_component_metadata(self, component_name: str, metadata: Dict[str, Any]) -> str:
        """Add metadata to a component."""
        for component in self.classified_components:
            if component.name == component_name:
                component.metadata.update(metadata)
                return f"Metadata added to component {component_name}"
        return f"Component {component_name} not found"

    def add_component_relationship(self, component_name: str, relationship: str) -> str:
        """Add a relationship to a component."""
        for component in self.classified_components:
            if component.name == component_name:
                component.relationships.append(relationship)
                return f"Relationship {relationship} added to component {component_name}"
        return f"Component {component_name} not found"

    def validate_classification(self, component_name: str) -> str:
        """Validate a component classification."""
        for component in self.classified_components:
            if component.name == component_name:
                # Basic validation logic
                if not component.rig_type:
                    return f"Component {component_name} has no RIG type"
                return f"Component {component_name} classification validated"
        return f"Component {component_name} not found"

    def add_evidence(self, evidence_item: str) -> str:
        """Add evidence."""
        self.evidence.append(evidence_item)
        return f"Evidence added: {evidence_item}"

    def validate(self) -> List[str]:
        """Validate the store."""
        errors = []
        if not self.classified_components:
            errors.append("At least one component must be classified")
        return errors

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the classification store."""
        return {
            "repository_name": self.repository_name,
            "classified_components_count": len(self.classified_components),
            "classified_components": [
                {
                    "name": c.name,
                    "rig_type": c.rig_type,
                    "path": c.path,
                    "metadata_count": len(c.metadata),
                    "relationships_count": len(c.relationships)
                }
                for c in self.classified_components
            ],
            "rig_types": self.rig_types,
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
