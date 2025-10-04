#!/usr/bin/env python3
"""
Test V4 Phase 4 ONLY: Build System Analysis for jni_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase4_build_system_agent_v4 import BuildSystemAnalysisAgentV4

async def test_phase4_only_jni_hello_world():
    """Test Phase 4 ONLY: Build System Analysis for jni_hello_world."""
    print("INFO:test_phase4_only_jni_hello_world:Running Phase 4 ONLY: Build System Analysis...")
    
    # Use jni_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "jni_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase4_only_jni_hello_world:Using repository: {test_repo_path}")
    
    # Create mock Phase 1, Phase 2, and Phase 3 results for jni_hello_world
    phase1_results = {
        "repository_overview": {
            "name": "jni_hello_world",
            "type": "application",
            "primary_language": "multi-language (C++/Java)",
            "build_systems": ["cmake"],
            "directory_structure": {
                "source_dirs": ["src"],
                "test_dirs": ["tests"],
                "build_dirs": ["build"],
                "config_dirs": []
            },
            "entry_points": ["CMakeLists.txt"],
            "exploration_scope": {
                "priority_dirs": ["src", "tests"],
                "skip_dirs": [".git", "build", "node_modules"],
                "deep_exploration": ["src", "tests"]
            }
        }
    }
    
    phase2_results = {
        "source_structure": {
            "source_directories": [
                {
                    "path": "src",
                    "language": "multi-language (C++/Java)",
                    "components": [
                        {"name": "cpp", "type": "module", "language": "C++"},
                        {"name": "java", "type": "module", "language": "Java"}
                    ],
                    "files": [],
                    "dependencies": ["JNI", "Java"],
                    "build_evidence": "Root CMakeLists.txt: add_executable(jni_hello_world src/cpp/main.cpp src/cpp/jni_wrapper.cpp); add_jar(java_hello_lib ...); find_package(JNI REQUIRED); find_package(Java REQUIRED)",
                    "exploration_complete": True
                }
            ],
            "language_analysis": {
                "primary_language": "multi-language (C++/Java)",
                "secondary_languages": ["C++", "Java"],
                "language_distribution": {
                    "C++": 0.6,
                    "Java": 0.4
                }
            },
            "component_hints": [
                {
                    "name": "cpp",
                    "type": "module",
                    "source_files": ["src/cpp/jni_wrapper.cpp","src/cpp/main.cpp","src/cpp/jni_wrapper.h"],
                    "language": "C++"
                },
                {
                    "name": "java",
                    "type": "module",
                    "source_files": ["src/java/HelloWorld.java","src/java/HelloWorldJNI.java"],
                    "language": "Java"
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
                    "version": "3.16+",
                    "config_files": ["CMakeLists.txt"],
                    "test_directories": ["tests/cpp"]
                }
            ],
            "test_organization": {
                "test_directories": [
                    {
                        "path": "tests/cpp",
                        "framework": "CTest",
                        "test_files": ["test_jni_wrapper.cpp"],
                        "targets": ["test_jni_wrapper"]
                    }
                ]
            },
            "test_configuration": {
                "test_command": "ctest --output-on-failure",
                "test_timeout": "300",
                "parallel_tests": True
            }
        }
    }
    
    try:
        # Create Phase 4 agent
        agent = BuildSystemAnalysisAgentV4(test_repo_path)
        
        # Run Phase 4 with Phase 1, Phase 2, and Phase 3 results
        start_time = time.time()
        result = await agent.execute_phase(phase1_results, phase2_results, phase3_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase4_only_jni_hello_world:Phase 4 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        build_targets = result.get("build_system", {}).get("build_targets", [])
        dependencies = result.get("build_system", {}).get("dependencies", [])
        
        print(f"INFO:test_phase4_only_jni_hello_world:Build targets found: {len(build_targets)}")
        print(f"INFO:test_phase4_only_jni_hello_world:Dependencies found: {len(dependencies)}")
        
        print("[OK] Phase 4 ONLY test with jni_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase4_only_jni_hello_world:Phase 4 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase4_only_jni_hello_world())
    if not success:
        sys.exit(1)
