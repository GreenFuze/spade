"""
V6 LLM RIG Generator - Phase-Specific Memory Stores Architecture

This package provides the V6 implementation of the LLM-based RIG generation system
using phase-specific memory stores instead of passing large JSON between phases.
"""

from .llm0_rig_generator_v6_smart import LLMRIGGeneratorV6Smart
from .base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from .phase1_repository_overview_agent_v6_optimized import RepositoryOverviewAgentV6Optimized
from .phase2_source_structure_agent_v6_optimized import SourceStructureDiscoveryAgentV6Optimized
from .phase3_test_structure_agent_v6_optimized import TestStructureDiscoveryAgentV6Optimized
from .phase4_build_system_agent_v6_optimized import BuildSystemAnalysisAgentV6Optimized
from .phase5_artifact_discovery_agent_v6_optimized import ArtifactDiscoveryAgentV6Optimized
from .phase6_component_classification_agent_v6_optimized import ComponentClassificationAgentV6Optimized
from .phase7_relationship_mapping_agent_v6_optimized import RelationshipMappingAgentV6Optimized
from .phase8_rig_assembly_agent_v6_optimized import RIGAssemblyAgentV6Optimized

__all__ = [
    'LLMRIGGeneratorV6Smart',
    'BaseLLMAgentV6',
    'BasePhaseStore',
    'RepositoryOverviewAgentV6Optimized',
    'SourceStructureDiscoveryAgentV6Optimized',
    'TestStructureDiscoveryAgentV6Optimized',
    'BuildSystemAnalysisAgentV6Optimized',
    'ArtifactDiscoveryAgentV6Optimized',
    'ComponentClassificationAgentV6Optimized',
    'RelationshipMappingAgentV6Optimized',
    'RIGAssemblyAgentV6Optimized',
]
