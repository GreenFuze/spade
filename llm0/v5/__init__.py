"""
V5 LLM-based RIG Generation with Direct RIG Manipulation

This package implements the V5 architecture where all agents work with a single
RIG instance that grows incrementally through all phases, eliminating JSON
conversion issues and providing type safety.
"""

from .base_agent_v5 import BaseLLMAgentV5, RIGTools
from .llm0_rig_generator_v5 import LLMRIGGeneratorV5
from .phase1_repository_overview_agent_v5 import RepositoryOverviewAgentV5
from .phase2_source_structure_agent_v5 import SourceStructureDiscoveryAgentV5
from .phase3_test_structure_agent_v5 import TestStructureDiscoveryAgentV5

__all__ = [
    'BaseLLMAgentV5',
    'RIGTools', 
    'LLMRIGGeneratorV5',
    'RepositoryOverviewAgentV5',
    'SourceStructureDiscoveryAgentV5',
    'TestStructureDiscoveryAgentV5'
]
