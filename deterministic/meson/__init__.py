"""
Meson deterministic entrypoint package for RIG generation.

This package provides components for parsing Meson projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- meson_entrypoint: Main orchestrator class for Meson projects
"""

from .meson_entrypoint import MesonEntrypoint

__all__ = [
    'MesonEntrypoint'
]
