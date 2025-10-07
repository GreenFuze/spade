from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase7_relationship_store import RelationshipStore

class RelationshipMappingAgentV6Optimized(BaseLLMAgentV6):
    """Optimized Phase 7 agent for relationship mapping with 70% prompt reduction."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> RelationshipStore:
        """Creates and initializes the RelationshipStore."""
        return RelationshipStore(previous_stores)

    def get_phase_tools(self, phase_store: RelationshipStore) -> List[Any]:
        """Returns the essential tools for Phase 7 (reduced from 14+ to 5)."""
        return [
            phase_store.add_relationship,
            phase_store.add_dependency,
            phase_store.add_test_relationship,
            phase_store.add_external_dependency,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: RelationshipStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are a Relationship Mapping Agent. Analyze {self.repository_path} and populate the store.

MISSION: Map dependencies and relationships between components.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- add_relationship(source, target, type): Add component relationship
- add_dependency(component, dependency): Add component dependency
- add_test_relationship(test, target): Add test relationship
- add_external_dependency(component, external): Add external dependency
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Analyze component relationships systematically
2. Map dependencies and connections
3. Identify test relationships
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Skip phase if no components to map."""
        return False  # Always run relationship mapping

    def get_next_phases(self, phase_store: RelationshipStore) -> List[str]:
        """Smart adaptation: Determine which phases to run next."""
        return ["phase8_rig_assembly"]
