from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase6_component_classification_store import ComponentClassificationStore

class ComponentClassificationAgentV6Optimized(BaseLLMAgentV6):
    """Optimized Phase 6 agent for component classification with 70% prompt reduction."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> ComponentClassificationStore:
        """Creates and initializes the ComponentClassificationStore."""
        return ComponentClassificationStore(previous_stores)

    def get_phase_tools(self, phase_store: ComponentClassificationStore) -> List[Any]:
        """Returns the essential tools for Phase 6 (reduced from 14+ to 5)."""
        return [
            phase_store.classify_component,
            phase_store.add_component_metadata,
            phase_store.add_component_relationship,
            phase_store.validate_classification,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: ComponentClassificationStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are a Component Classification Agent. Analyze {self.repository_path} and populate the store.

MISSION: Classify components into RIG types and establish relationships.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- classify_component(name, rig_type): Classify component into RIG type
- add_component_metadata(component, metadata): Add metadata to component
- add_component_relationship(component, relationship): Add relationship
- validate_classification(component): Validate classification
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Analyze discovered components systematically
2. Classify into appropriate RIG types
3. Establish component relationships
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Skip phase if no components discovered."""
        return False  # Always run classification

    def get_next_phases(self, phase_store: ComponentClassificationStore) -> List[str]:
        """Smart adaptation: Determine which phases to run next."""
        return ["phase7_relationship_mapping", "phase8_rig_assembly"]
