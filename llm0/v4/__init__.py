"""
LLM0 V4 Architecture - Eight-Phase RIG Generation System

This module implements the V4 architecture with eight specialized phases:
1. Repository Overview Agent
2. Source Structure Discovery Agent  
3. Test Structure Discovery Agent
4. Build System Analysis Agent
5. Artifact Discovery Agent
6. Component Classification Agent
7. Relationship Mapping Agent
8. RIG Assembly Agent
"""

from .llm0_rig_generator_v4 import LLMRIGGeneratorV4

__all__ = ['LLMRIGGeneratorV4']
