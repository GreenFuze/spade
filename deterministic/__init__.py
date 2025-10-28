"""
Deterministic RIG generation package.

This package provides deterministic (non-LLM) approaches for generating
Repository Intelligence Graphs (RIGs) from various build systems.
"""

from .cmake.cmake_plugin import CMakePlugin
# from .maven.maven_entrypoint import MavenEntrypoint
# from .npm.npm_entrypoint import NpmEntrypoint
# from .cargo.cargo_entrypoint import CargoEntrypoint
# from .go.go_entrypoint import GoEntrypoint
# from .meson.meson_entrypoint import MesonEntrypoint

__all__ = [
    'CMakePlugin',
    # 'MavenEntrypoint',
    # 'NpmEntrypoint',
    # 'CargoEntrypoint',
    # 'GoEntrypoint',
    # 'MesonEntrypoint'
]
