from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase1_repository_overview_store import RepositoryOverviewStore
from llm0.v6.phase2_source_structure_store import SourceStructureStore

class SourceStructureDiscoveryAgentV6Optimized(BaseLLMAgentV6):
    """Optimized V6 Phase 2 Agent with reduced prompt size and smart adaptation."""
    
    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> SourceStructureStore:
        """Creates and initializes the SourceStructureStore with constructor-based handoff."""
        return SourceStructureStore(previous_stores)

    def get_phase_tools(self, phase_store: SourceStructureStore) -> List[Any]:
        """Returns the essential tools for Phase 2 (reduced from 14+ to 5)."""
        return [
            phase_store.add_component,
            phase_store.add_component_file,
            phase_store.add_component_dependency,
            phase_store.add_secondary_language,
            phase_store.add_file_organization,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: SourceStructureStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        # Get Phase 1 results
        phase1_store = previous_stores[0] if previous_stores else None
        source_dirs = []
        if phase1_store:
            source_dirs = phase1_store.directory_structure.source_dirs

        return f"""
You are a Source Structure Discovery Agent. Analyze {self.repository_path} and populate the store.

MISSION: Discover source components, languages, and file organization.

SOURCE DIRECTORIES: {source_dirs}

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- add_component(name, path, language, type): Add a source component
- add_component_file(component_name, file_path): Add file to component
- add_component_dependency(component_name, dependency): Add dependency
- add_secondary_language(language): Add secondary language
- add_file_organization(category, files): Add file organization
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Explore each source directory systematically
2. Identify components and their relationships
3. Analyze programming languages and file patterns
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Skip phase if no source directories."""
        if hasattr(phase1_store, 'directory_structure') and hasattr(phase1_store.directory_structure, 'source_dirs'):
            return len(phase1_store.directory_structure.source_dirs) == 0
        return True  # Skip if we can't determine source directories
