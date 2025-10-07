"""
LLM0 V7 Enhanced Architecture - Eight-Phase RIG Generation System

This module implements the V7 Enhanced architecture with eight specialized phases:
1. Repository Overview Agent
2. Source Structure Discovery Agent  
3. Test Structure Discovery Agent
4. Build System Analysis Agent
5. Artifact Discovery Agent
6. Component Classification Agent
7. Relationship Mapping Agent
8. RIG Assembly Agent (Enhanced with batch operations)
"""

from .llm0_rig_generator_v7_enhanced import LLMRIGGeneratorV7Enhanced

__all__ = ['LLMRIGGeneratorV7Enhanced']
