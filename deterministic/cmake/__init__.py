"""
CMake deterministic entrypoint package for RIG generation.

This package provides modular components for parsing CMake projects and generating
Repository Intelligence Graphs (RIGs) without LLM involvement.

Modules:
- cmake_entrypoint: Main orchestrator class
- build_output_finder: Generator-aware build output detection
- utilities: Research-backed utility functions
- parser: CMakeLists.txt parsing
- file_api: CMake File API interaction
- evidence: Evidence extraction and backtrace handling
- component_builder: Component creation logic
- test_detection: Test framework and mapping logic
"""
#
# from .cmake_plugin import CMakePlugin
# from .build_output_finder import BuildOutputFinder
# from .utilities import ResearchBackedUtilities
# from .cmake_parser import CMakeParser
#
# __all__ = [
#     'CMakePlugin',
#     'BuildOutputFinder',
#     'ResearchBackedUtilities',
#     'CMakeParser'
# ]
