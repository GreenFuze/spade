#!/usr/bin/env python3
"""
Test V4 Phase 7 ONLY: Relationship Mapping for cmake_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase7_relationship_mapping_agent_v4 import RelationshipMappingAgentV4

async def test_phase7_only_cmake_hello_world():
    """Test Phase 7 ONLY: Relationship Mapping for cmake_hello_world."""
    print("INFO:test_phase7_only_cmake_hello_world:Running Phase 7 ONLY: Relationship Mapping...")
    
    # Use cmake_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "cmake_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase7_only_cmake_hello_world:Using repository: {test_repo_path}")
    
    # Create mock Phase 1-6 results for cmake_hello_world
    phase1_results = {
        "repository_overview": {
            "name": "cmake_hello_world",
            "type": "application",
            "primary_language": "C++",
            "build_systems": ["cmake"],
            "directory_structure": {
                "source_dirs": ["src"],
                "test_dirs": [],
                "build_dirs": ["build"],
                "config_dirs": []
            },
            "entry_points": ["CMakeLists.txt"],
            "exploration_scope": {
                "priority_dirs": ["src"],
                "skip_dirs": [".git", "build", "node_modules"],
                "deep_exploration": ["src"]
            }
        }
    }
    
    phase2_results = {
        "source_structure": {
            "source_directories": [
                {
                    "path": "src",
                    "language": "C++",
                    "components": ["hello_world_executable", "utils_library"],
                    "files": ["src/main.cpp", "src/utils.cpp", "src/utils.h"],
                    "dependencies": ["std::iostream (standard C++)", "none external inferred from code beyond standard library"],
                    "build_evidence": "Top-level CMakeLists.txt defines executable 'hello_world' from src/main.cpp and library 'utils' from src/utils.cpp; link: hello_world -> utils",
                    "exploration_complete": True
                }
            ],
            "language_analysis": {
                "primary_language": "C++",
                "secondary_languages": [],
                "language_distribution": {
                    "C++": 1.0
                }
            },
            "component_hints": [
                {
                    "name": "hello_world_executable",
                    "type": "executable",
                    "source_files": ["src/main.cpp"],
                    "language": "C++"
                },
                {
                    "name": "utils_library",
                    "type": "library",
                    "source_files": ["src/utils.cpp", "src/utils.h"],
                    "language": "C++"
                }
            ],
            "exploration_summary": {
                "total_directories_explored": 1,
                "directories_with_build_config": 1,
                "directories_without_build_config": 0,
                "all_phase1_directories_covered": True
            }
        }
    }
    
    phase3_results = {
        "test_structure": {
            "test_frameworks": [
                {
                    "name": "CTest",
                    "version": "3.10+",
                    "config_files": ["CMakeLists.txt"],
                    "test_directories": []
                }
            ],
            "test_organization": {
                "test_directories": [
                    {
                        "path": ".",
                        "framework": "CTest",
                        "test_files": ["src/main.cpp"],
                        "targets": ["hello_world"]
                    }
                ]
            },
            "test_configuration": {
                "test_command": "ctest",
                "test_timeout": "300",
                "parallel_tests": True
            }
        }
    }
    
    phase4_results = {
        "build_analysis": {
            "build_targets": [
                {
                    "name": "hello_world",
                    "type": "executable",
                    "source_files": ["src/main.cpp"],
                    "dependencies": ["utils"],
                    "output_path": "build/hello_world",
                    "build_options": []
                },
                {
                    "name": "utils",
                    "type": "library",
                    "source_files": ["src/utils.cpp", "src/utils.h"],
                    "dependencies": [],
                    "output_path": "build/libutils.a",
                    "build_options": []
                },
                {
                    "name": "test_hello_world",
                    "type": "test",
                    "source_files": [],
                    "dependencies": ["hello_world"],
                    "output_path": "",
                    "build_options": []
                }
            ],
            "build_dependencies": [
                {
                    "source": "hello_world",
                    "target": "utils",
                    "type": "link_dependency"
                }
            ],
            "build_configuration": {
                "build_type": "unspecified",
                "compiler": "unspecified",
                "flags": []
            }
        }
    }
    
    phase5_results = {
        "artifact_discovery": {
            "build_artifacts": [
                {
                    "name": "hello_world",
                    "type": "executable",
                    "output_file": "build/hello_world",
                    "size": "unknown",
                    "dependencies": ["utils"]
                }
            ],
            "library_artifacts": [
                {
                    "name": "utils",
                    "type": "static_library",
                    "output_file": "build/libutils.a",
                    "size": "unknown"
                }
            ],
            "package_artifacts": []
        }
    }
    
    phase6_results = {
        "component_classification": {
            "classified_components": [
                {
                    "name": "hello_world_executable",
                    "type": "executable",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": ["src/main.cpp"],
                    "output_path": "build/hello_world",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L5-L5",
                            "content": "add_executable(hello_world src/main.cpp)",
                            "reason": "CMake defines executable target hello_world from main.cpp."
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L11-L11",
                            "content": "target_link_libraries(hello_world utils)",
                            "reason": "Executable links to library utils, establishing dependency."
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L15-L15",
                            "content": "add_test(NAME test_hello_world COMMAND hello_world)",
                            "reason": "CTest test configuration for the executable."
                        }
                    ],
                    "dependencies": ["utils"],
                    "test_relationship": "test_hello_world"
                },
                {
                    "name": "utils_library",
                    "type": "library",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": ["src/utils.cpp", "src/utils.h"],
                    "output_path": "build/libutils.a",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L8-L8",
                            "content": "add_library(utils src/utils.cpp)",
                            "reason": "CMake defines a static library named utils from utils.cpp."
                        }
                    ],
                    "dependencies": [],
                    "test_relationship": None
                },
                {
                    "name": "test_hello_world",
                    "type": "test",
                    "programming_language": "CTest",
                    "runtime": "native",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L15-L15",
                            "content": "add_test(NAME test_hello_world COMMAND hello_world)",
                            "reason": "CTest configuration defines test that executes the hello_world executable."
                        }
                    ],
                    "dependencies": ["hello_world"],
                    "test_relationship": None
                }
            ]
        }
    }
    
    try:
        # Create Phase 7 agent
        agent = RelationshipMappingAgentV4(test_repo_path)
        
        # Run Phase 7 with Phase 1-6 results
        start_time = time.time()
        result = await agent.execute_phase(phase1_results, phase2_results, phase3_results, phase4_results, phase5_results, phase6_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase7_only_cmake_hello_world:Phase 7 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        relationships = result.get("relationship_mapping", {}).get("relationships", [])
        dependencies = result.get("relationship_mapping", {}).get("dependencies", [])
        
        print(f"INFO:test_phase7_only_cmake_hello_world:Relationships mapped: {len(relationships)}")
        print(f"INFO:test_phase7_only_cmake_hello_world:Dependencies mapped: {len(dependencies)}")
        
        print("[OK] Phase 7 ONLY test with cmake_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase7_only_cmake_hello_world:Phase 7 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase7_only_cmake_hello_world())
    if not success:
        sys.exit(1)
