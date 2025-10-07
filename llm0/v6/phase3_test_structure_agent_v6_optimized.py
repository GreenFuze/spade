from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase3_test_structure_store import TestStructureStore

class TestStructureDiscoveryAgentV6Optimized(BaseLLMAgentV6):
    """Optimized V6 Phase 3 Agent with reduced prompt size and smart adaptation."""
    
    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> TestStructureStore:
        """Creates and initializes the TestStructureStore with constructor-based handoff."""
        return TestStructureStore(previous_stores)

    def get_phase_tools(self, phase_store: TestStructureStore) -> List[Any]:
        """Returns the essential tools for Phase 3 (reduced from 14+ to 5)."""
        return [
            phase_store.add_test_component,
            phase_store.add_test_component_file,
            phase_store.add_test_framework,
            phase_store.add_test_directory,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: TestStructureStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        # Get Phase 1 results
        phase1_store = previous_stores[0] if previous_stores else None
        test_dirs = []
        if phase1_store:
            test_dirs = phase1_store.directory_structure.test_dirs

        return f"""
You are a Test Structure Discovery Agent. Analyze {self.repository_path} and populate the store.

MISSION: Discover test frameworks, test components, and test organization.

TEST DIRECTORIES: {test_dirs}

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- add_test_component(name, path, framework, type): Add test component
- add_test_component_file(component_name, file_path): Add file to test component
- add_test_framework(name, version): Add test framework
- add_test_directory(path): Add test directory
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Explore test directories systematically
2. Identify test frameworks and components
3. Analyze test organization and patterns
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase_store: TestStructureStore) -> bool:
        """Smart adaptation: Skip phase if no test directories."""
        return len(phase_store.test_dirs_to_explore) == 0
