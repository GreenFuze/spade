#!/usr/bin/env python3
"""
Test the V3 Assembly Agent with MetaFFI relationships results.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v3.llm0_rig_generator_v3 import AssemblyAgent


async def test_metaffi_assembly_v3():
    """Test the V3 Assembly Agent on MetaFFI repository."""
    
    print("=" * 80)
    print("TESTING V3 ASSEMBLY AGENT")
    print("=" * 80)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"Testing MetaFFI assembly with V3 agent at: {test_path}")
    
    # Create assembly agent
    assembly_agent = AssemblyAgent(
        repository_path=test_path,
        max_requests=200
    )
    
    print("Assembly agent created with:")
    print(f"  - Max requests: {assembly_agent.max_requests}")
    print(f"  - Usage limit: {assembly_agent.agent._usage_limit}")
    
    # All previous results (simulated)
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
    
    relationships_results = {
        "phase": "RELATIONSHIPS",
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
    
    print("\nStarting RIG assembly with all previous results...")
    print(f"Discovery found {len(discovery_results['repository_info']['source_directories'])} source directories")
    print(f"Classification found {len(classification_results['components'])} components")
    print(f"Relationships found {len(relationships_results['relationships'])} relationships")
    
    try:
        result = await assembly_agent.assemble_rig(discovery_results, classification_results, relationships_results)
        
        print("\n" + "=" * 80)
        print("RIG ASSEMBLY RESULTS:")
        print("=" * 80)
        
        # Print key results - result is a RIG object
        print(f"RIG Components: {len(result._components)}")
        for comp in result._components[:5]:  # Show first 5
            print(f"  - {comp.name} ({comp.type})")
            print(f"    Runtime: {comp.runtime}")
            print(f"    Location: {comp.location}")
        if len(result._components) > 5:
            print(f"  ... and {len(result._components) - 5} more")
        
        print(f"\nRIG Aggregators: {len(result._aggregators)}")
        for agg in result._aggregators[:3]:  # Show first 3
            print(f"  - {agg.name}")
            print(f"    Sub-aggregators: {len(agg.sub_aggregators)}")
        if len(result._aggregators) > 3:
            print(f"  ... and {len(result._aggregators) - 3} more")
        
        print(f"\nRIG Runners: {len(result._runners)}")
        for run in result._runners[:3]:  # Show first 3
            print(f"  - {run.name}")
            print(f"    Commands: {len(run.commands)}")
        if len(result._runners) > 3:
            print(f"  ... and {len(result._runners) - 3} more")
        
        print(f"\nRIG Utilities: {len(result.utilities)}")
        for util in result.utilities[:3]:  # Show first 3
            print(f"  - {util.name}")
        if len(result.utilities) > 3:
            print(f"  ... and {len(result.utilities) - 3} more")
        
        print(f"\nRIG Tests: {len(result._tests)}")
        for test in result._tests[:3]:  # Show first 3
            print(f"  - {test.name}")
            print(f"    Type: {test.type}")
        if len(result._tests) > 3:
            print(f"  ... and {len(result._tests) - 3} more")
        
        # Print validation results
        print(f"\nVALIDATION RESULTS:")
        print(f"  - Repository: {result._repository_info}")
        print(f"  - Build System: {result._build_system_info}")
        print(f"  - Total Components: {len(result._components)}")
        print(f"  - Total Aggregators: {len(result._aggregators)}")
        print(f"  - Total Runners: {len(result._runners)}")
        print(f"  - Total Utilities: {len(result.utilities)}")
        print(f"  - Total Tests: {len(result._tests)}")
        
        print("\n[SUCCESS] V3 Assembly completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Assembly failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metaffi_assembly_v3())
    sys.exit(0 if success else 1)
