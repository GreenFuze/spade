"""
Maven deterministic entrypoint package for RIG generation.

This package provides components for parsing Maven projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- maven_entrypoint: Main orchestrator class for Maven projects
"""

from .maven_entrypoint import MavenEntrypoint

__all__ = [
    'MavenEntrypoint'
]
