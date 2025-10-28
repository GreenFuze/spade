"""
Cargo deterministic entrypoint package for RIG generation.

This package provides components for parsing Cargo projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- cargo_entrypoint: Main orchestrator class for Cargo projects
"""

from .cargo_entrypoint import CargoEntrypoint

__all__ = [
    'CargoEntrypoint'
]
