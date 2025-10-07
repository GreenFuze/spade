from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase8_rig_assembly_store import RIGAssemblyStore

class RIGAssemblyAgentV6Optimized(BaseLLMAgentV6):
    """Optimized Phase 8 agent for RIG assembly with 70% prompt reduction."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> RIGAssemblyStore:
        """Creates and initializes the RIGAssemblyStore."""
        return RIGAssemblyStore(previous_stores)

    def get_phase_tools(self, phase_store: RIGAssemblyStore) -> List[Any]:
        """Returns the essential tools for Phase 8 (reduced from 14+ to 5)."""
        return [
            phase_store.assemble_rig,
            phase_store.add_rig_component,
            phase_store.add_rig_relationship,
            phase_store.validate_rig,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: RIGAssemblyStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are a RIG Assembly Agent. Analyze {self.repository_path} and populate the store.

MISSION: Assemble the final Repository Intelligence Graph from all previous phases.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- assemble_rig(): Assemble the complete RIG
- add_rig_component(component): Add component to RIG
- add_rig_relationship(relationship): Add relationship to RIG
- validate_rig(): Validate the assembled RIG
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Review all previous phase results
2. Assemble components into RIG structure
3. Add relationships and dependencies
4. Validate the complete RIG
5. Use tools to populate store

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Never skip the final assembly phase."""
        return False  # Always run RIG assembly

    def get_next_phases(self, phase_store: RIGAssemblyStore) -> List[str]:
        """Smart adaptation: No phases after RIG assembly."""
        return []
