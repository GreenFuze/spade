from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm0.v6.base_agent_v6 import BasePhaseStore

@dataclass
class Relationship:
    """Represents a relationship between components."""
    source: str
    target: str
    type: str  # e.g., depends_on, tests, uses
    evidence: List[Dict[str, Any]] = field(default_factory=list)

class RelationshipStore(BasePhaseStore):
    """Phase 7 store for relationship mapping information."""

    def __init__(self, previous_stores=None):
        super().__init__()
        # Extract information from previous phases
        if previous_stores and len(previous_stores) > 0:
            phase1_store = previous_stores[0]
            self.repository_name = getattr(phase1_store, 'name', 'unknown')
        else:
            self.repository_name = 'unknown'

        # Phase 7 specific fields
        self.relationships: List[Relationship] = []
        self.dependencies: List[Dict[str, str]] = []
        self.test_relationships: List[Dict[str, str]] = []
        self.external_dependencies: List[Dict[str, str]] = []
        self.evidence: List[str] = []

    def add_relationship(self, source: str, target: str, type: str) -> str:
        """Add a relationship between components."""
        relationship = Relationship(source=source, target=target, type=type)
        self.relationships.append(relationship)
        return f"Relationship added: {source} -> {target} ({type})"

    def add_dependency(self, component: str, dependency: str) -> str:
        """Add a dependency."""
        dep = {"component": component, "dependency": dependency}
        self.dependencies.append(dep)
        return f"Dependency added: {component} depends on {dependency}"

    def add_test_relationship(self, test: str, target: str) -> str:
        """Add a test relationship."""
        test_rel = {"test": test, "target": target}
        self.test_relationships.append(test_rel)
        return f"Test relationship added: {test} tests {target}"

    def add_external_dependency(self, component: str, external: str) -> str:
        """Add an external dependency."""
        ext_dep = {"component": component, "external": external}
        self.external_dependencies.append(ext_dep)
        return f"External dependency added: {component} uses {external}"

    def add_evidence(self, evidence_item: str) -> str:
        """Add evidence."""
        self.evidence.append(evidence_item)
        return f"Evidence added: {evidence_item}"

    def validate(self) -> List[str]:
        """Validate the store."""
        errors = []
        if not self.relationships and not self.dependencies:
            errors.append("At least one relationship or dependency must be identified")
        return errors

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the relationship store."""
        return {
            "repository_name": self.repository_name,
            "relationships_count": len(self.relationships),
            "relationships": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.type,
                    "evidence_count": len(r.evidence)
                }
                for r in self.relationships
            ],
            "dependencies_count": len(self.dependencies),
            "test_relationships_count": len(self.test_relationships),
            "external_dependencies_count": len(self.external_dependencies),
            "evidence_count": len(self.evidence)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the store to a dictionary (alias for get_summary)."""
        return self.get_summary()
