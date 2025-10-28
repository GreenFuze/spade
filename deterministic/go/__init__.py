"""
Go deterministic entrypoint package for RIG generation.

This package provides components for parsing Go projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- go_entrypoint: Main orchestrator class for Go projects
"""

from .go_entrypoint import GoEntrypoint

__all__ = [
    'GoEntrypoint'
]
