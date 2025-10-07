from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm0.v6.base_agent_v6 import BasePhaseStore

@dataclass
class RIGComponent:
    """Represents a component in the final RIG."""
    name: str
    type: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RIGRelationship:
    """Represents a relationship in the final RIG."""
    source: str
    target: str
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class RIGAssemblyStore(BasePhaseStore):
    """Phase 8 store for RIG assembly information."""

    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from previous phases
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
        else:
            self.repository_name = 'unknown'

        # Phase 8 specific fields
        self.rig_components: List[RIGComponent] = []
        self.rig_relationships: List[RIGRelationship] = []
        self.rig_metadata: Dict[str, Any] = {}
        self.evidence: List[str] = []

    def assemble_rig(self) -> str:
        """Assemble the complete RIG."""
        return "RIG assembly initiated"

    def add_rig_component(self, component: Dict[str, Any]) -> str:
        """Add a component to the RIG."""
        rig_comp = RIGComponent(
            name=component.get('name', ''),
            type=component.get('type', ''),
            path=component.get('path', ''),
            metadata=component.get('metadata', {})
        )
        self.rig_components.append(rig_comp)
        return f"RIG component added: {rig_comp.name}"

    def add_rig_relationship(self, relationship: Dict[str, Any]) -> str:
        """Add a relationship to the RIG."""
        rig_rel = RIGRelationship(
            source=relationship.get('source', ''),
            target=relationship.get('target', ''),
            type=relationship.get('type', ''),
            metadata=relationship.get('metadata', {})
        )
        self.rig_relationships.append(rig_rel)
        return f"RIG relationship added: {rig_rel.source} -> {rig_rel.target}"

    def validate_rig(self) -> str:
        """Validate the assembled RIG."""
        if not self.rig_components:
            return "RIG validation failed: No components found"
        if not self.rig_relationships:
            return "RIG validation warning: No relationships found"
        return "RIG validation passed"

    def add_rig_metadata(self, key: str, value: Any) -> str:
        """Add metadata to the RIG."""
        self.rig_metadata[key] = value
        return f"RIG metadata added: {key} = {value}"

    def add_evidence(self, evidence_item: str) -> str:
        """Add evidence."""
        self.evidence.append(evidence_item)
        return f"Evidence added: {evidence_item}"

    def validate(self) -> List[str]:
        """Validate the store."""
        errors = []
        if not self.rig_components:
            errors.append("At least one RIG component must be assembled")
        return errors

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the RIG assembly store."""
        return {
            "repository_name": self.repository_name,
            "rig_components_count": len(self.rig_components),
            "rig_components": [
                {
                    "name": c.name,
                    "type": c.type,
                    "path": c.path,
                    "metadata_count": len(c.metadata)
                }
                for c in self.rig_components
            ],
            "rig_relationships_count": len(self.rig_relationships),
            "rig_relationships": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.type,
                    "metadata_count": len(r.metadata)
                }
                for r in self.rig_relationships
            ],
            "rig_metadata": self.rig_metadata,
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
