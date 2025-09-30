#!/usr/bin/env python3
"""
Test the V3 Relationships Agent with MetaFFI classification results.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v3.llm0_rig_generator_v3 import RelationshipsAgent


async def test_metaffi_relationships_v3():
    """Test the V3 Relationships Agent on MetaFFI repository."""
    
    print("=" * 80)
    print("TESTING V3 RELATIONSHIPS AGENT")
    print("=" * 80)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"Testing MetaFFI relationships with V3 agent at: {test_path}")
    
    # Create relationships agent
    relationships_agent = RelationshipsAgent(
        repository_path=test_path,
        max_requests=200
    )
    
    print("Relationships agent created with:")
    print(f"  - Max requests: {relationships_agent.max_requests}")
    print(f"  - Usage limit: {relationships_agent.agent._usage_limit}")
    
    # Discovery results from Phase 1 (simulated)
    discovery_results = {
        "repository_info": {
            "path": "C:\\src\\github.com\\MetaFFI",
            "build_systems": [
                {
                    "type": "CMake",
                    "version": "3.10",
                    "config_files": [
                        "CMakeLists.txt",
                        "cmake/CPP.cmake",
                        "cmake/Environment.cmake",
                        "cmake/GlobalSettings.cmake",
                        "cmake/Go.cmake",
                        "cmake/InstallUtils.cmake",
                        "cmake/JVM.cmake",
                        "cmake/MetaFFIGitRepository.cmake",
                        "cmake/PackageManagement.cmake",
                        "cmake/Python3.cmake",
                        "cmake/Utils.cmake"
                    ],
                    "api_available": True,
                    "evidence": "Root CMakeLists.txt declares cmake_minimum_required(VERSION 3.10) and includes modules under the cmake directory; add_subdirectory references indicate a multi-target CMake build"
                }
            ],
            "source_directories": [
                "C:\\src\\github.com\\MetaFFI\\metaffi-core",
                "C:\\src\\github.com\\MetaFFI\\lang-plugin-python311",
                "C:\\src\\github.com\\MetaFFI\\lang-plugin-openjdk",
                "C:\\src\\github.com\\MetaFFI\\lang-plugin-go"
            ],
            "test_directories": []
        },
        "evidence_catalog": {
            "cmake_file_api": {
                "available": False,
                "index_file": "UNKNOWN"
            },
            "test_frameworks": [
                {
                    "type": "CTest",
                    "config_files": ["CMakeLists.txt"],
                    "evidence": "Root CMakeLists.txt calls enable_testing(), indicating a CTest-based testing framework"
                }
            ]
        }
    }
    
    # Classification results from Phase 2 (simulated)
    classification_results = {
        "phase": "CLASSIFICATION",
        "repository": {
            "path": "C:\\src\\github.com\\MetaFFI"
        },
        "build_systems": [
            {
                "type": "CMake",
                "version": "3.10",
                "config_files": [
                    "CMakeLists.txt",
                    "cmake/CPP.cmake",
                    "cmake/Environment.cmake",
                    "cmake/GlobalSettings.cmake",
                    "cmake/Go.cmake",
                    "cmake/InstallUtils.cmake",
                    "cmake/JVM.cmake",
                    "cmake/MetaFFIGitRepository.cmake",
                    "cmake/PackageManagement.cmake",
                    "cmake/Python3.cmake",
                    "cmake/Utils.cmake"
                ],
                "api_available": True
            }
        ],
        "components": [
            {
                "name": "MetaFFI",
                "type": "build_aggregator",
                "description": "Top-level aggregator target that depends on the primary components: metaffi-core, Python 311 plugin, OpenJDK plugin, and Go plugin."
            },
            {
                "name": "metaffi-core",
                "type": "library / core",
                "description": "Core MetaFFI library/framework. Submodules include XLLR, CLI, runtime, and plugin SDK; exposes a top-level custom target (metaffi-core) and is wired into the root via add_subdirectory."
            },
            {
                "name": "metaffi-core/XLLR",
                "type": "shared_library",
                "description": "XLLR component within the core, tied into the core build through metaffi-core/XLLR/CMakeLists.txt."
            },
            {
                "name": "metaffi-core/CLI",
                "type": "executable",
                "description": "CLI-related component within the core, built via metaffi-core/CLI/CMakeLists.txt."
            },
            {
                "name": "lang-plugin-python311",
                "type": "language_plugin",
                "description": "Python 3.11 language plugin. Submodules include plugin-sdk, runtime, api, idl, compiler; top-level target named 'python311'."
            },
            {
                "name": "lang-plugin-openjdk",
                "type": "language_plugin",
                "description": "OpenJDK language plugin. Submodules include plugin-sdk, idl, compiler, runtime, bridge, api; top-level target named 'openjdk'."
            },
            {
                "name": "lang-plugin-go",
                "type": "language_plugin",
                "description": "Go language plugin. Submodules include plugin-sdk, runtime, go-runtime, idl, compiler, api; top-level target named 'go'."
            }
        ],
        "relationships": [
            {
                "parent": "CMakeRoot",
                "children": [
                    "metaffi-core",
                    "lang-plugin-python311",
                    "lang-plugin-openjdk",
                    "lang-plugin-go"
                ]
            },
            {
                "parent": "metaffi-core",
                "children": [
                    "XLLR",
                    "CLI",
                    "runtime",
                    "plugin-sdk"
                ]
            },
            {
                "parent": "lang-plugin-python311",
                "children": [
                    "plugin-sdk",
                    "runtime",
                    "api",
                    "idl",
                    "compiler"
                ]
            },
            {
                "parent": "lang-plugin-openjdk",
                "children": [
                    "plugin-sdk",
                    "idl",
                    "compiler",
                    "runtime",
                    "bridge",
                    "api"
                ]
            },
            {
                "parent": "lang-plugin-go",
                "children": [
                    "plugin-sdk",
                    "runtime",
                    "go-runtime",
                    "idl",
                    "compiler",
                    "api"
                ]
            }
        ],
        "notes": [
            "Root CMake enables testing via CTest (enable_testing()).",
            "The root defines a MetaFFI aggregator target that depends on the main components.",
            "Each language plugin exposes its own top-level target and aggregates its submodules."
        ]
    }
    
    print("\nStarting relationships mapping with discovery and classification results...")
    print(f"Discovery found {len(discovery_results['repository_info']['source_directories'])} source directories")
    print(f"Classification found {len(classification_results['components'])} components")
    
    try:
        result = await relationships_agent.map_relationships(discovery_results, classification_results)
        
        print("\n" + "=" * 80)
        print("RELATIONSHIPS RESULTS:")
        print("=" * 80)
        
        # Print key results
        relationships = result.get("relationships", [])
        dependencies = result.get("dependencies", [])
        aggregations = result.get("aggregations", [])
        
        print(f"Relationships Found: {len(relationships)}")
        for rel in relationships[:5]:  # Show first 5
            print(f"  - {rel.get('source', 'UNKNOWN')} -> {rel.get('target', 'UNKNOWN')}")
            print(f"    Type: {rel.get('type', 'UNKNOWN')}")
        if len(relationships) > 5:
            print(f"  ... and {len(relationships) - 5} more")
        
        print(f"\nDependencies Found: {len(dependencies)}")
        for dep in dependencies[:5]:  # Show first 5
            print(f"  - {dep.get('source', 'UNKNOWN')} depends on {dep.get('target', 'UNKNOWN')}")
            print(f"    Type: {dep.get('type', 'UNKNOWN')}")
        if len(dependencies) > 5:
            print(f"  ... and {len(dependencies) - 5} more")
        
        print(f"\nAggregations Found: {len(aggregations)}")
        for agg in aggregations[:3]:  # Show first 3
            print(f"  - {agg.get('aggregator', 'UNKNOWN')} aggregates:")
            for child in agg.get('children', [])[:3]:
                print(f"    - {child}")
            if len(agg.get('children', [])) > 3:
                print(f"    ... and {len(agg.get('children', [])) - 3} more")
        if len(aggregations) > 3:
            print(f"  ... and {len(aggregations) - 3} more")
        
        # Print evidence summary
        evidence_summary = result.get("evidence_summary", {})
        print(f"\nEVIDENCE SUMMARY:")
        print(f"  - Files analyzed: {evidence_summary.get('files_analyzed', 0)}")
        print(f"  - Lines analyzed: {evidence_summary.get('lines_analyzed', 0)}")
        print(f"  - Evidence points: {evidence_summary.get('evidence_points', 0)}")
        
        print("\n[SUCCESS] V3 Relationships completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Relationships failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metaffi_relationships_v3())
    sys.exit(0 if success else 1)
