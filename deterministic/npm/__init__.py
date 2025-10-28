"""
npm deterministic entrypoint package for RIG generation.

This package provides components for parsing npm projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- npm_entrypoint: Main orchestrator class for npm projects
"""

from .npm_entrypoint import NpmEntrypoint

__all__ = [
    'NpmEntrypoint'
]
