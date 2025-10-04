#!/usr/bin/env python3
"""
Test V4 Phase 5 ONLY: Artifact Discovery for jni_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase5_artifact_discovery_agent_v4 import ArtifactDiscoveryAgentV4

async def test_phase5_only_jni_hello_world():
    """Test Phase 5 ONLY: Artifact Discovery for jni_hello_world."""
    print("INFO:test_phase5_only_jni_hello_world:Running Phase 5 ONLY: Artifact Discovery...")
    
    # Use jni_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "jni_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase5_only_jni_hello_world:Using repository: {test_repo_path}")
    
    # Create mock Phase 1, Phase 2, Phase 3, and Phase 4 results for jni_hello_world
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
    
    phase4_results = {
        "build_analysis": {
            "build_targets": [
                {
                    "name": "jni_hello_world",
                    "type": "executable",
                    "source_files": [
                        "src/cpp/main.cpp",
                        "src/cpp/jni_wrapper.cpp"
                    ],
                    "dependencies": [
                        "JNI"
                    ],
                    "output_path": "build/jni_hello_world",
                    "build_options": [
                        "-std=c++17"
                    ]
                },
                {
                    "name": "java_hello_lib",
                    "type": "jar",
                    "source_files": [
                        "src/java/HelloWorld.java",
                        "src/java/HelloWorldJNI.java"
                    ],
                    "output_path": "build/java_hello_lib-1.0.0.jar",
                    "build_options": []
                },
                {
                    "name": "test_jni_wrapper",
                    "type": "executable",
                    "source_files": [
                        "tests/cpp/test_jni_wrapper.cpp",
                        "src/cpp/jni_wrapper.cpp"
                    ],
                    "dependencies": [
                        "JNI"
                    ],
                    "output_path": "build/test_jni_wrapper",
                    "build_options": [
                        "-std=c++17"
                    ]
                }
            ],
            "build_dependencies": [
                {
                    "source": "jni_hello_world",
                    "target": "JNI",
                    "type": "link_dependency"
                },
                {
                    "source": "test_jni_wrapper",
                    "target": "JNI",
                    "type": "link_dependency"
                }
            ],
            "build_configuration": {
                "build_type": "Debug|Release",
                "compiler": "system default C++ compiler",
                "flags": [
                    "-std=c++17"
                ],
                "notes": [
                    "CMakeLists.txt defines C++ standard as C++17 (CMAKE_CXX_STANDARD 17).",
                    "Java compilation is configured to source/target 21 via CMAKE_JAVA_COMPILE_FLAGS (21).",
                    "No explicit per-target optimization or extra compiler flags are set in CMakeLists.txt."
                ]
            }
        }
    }
    
    try:
        # Create Phase 5 agent
        agent = ArtifactDiscoveryAgentV4(test_repo_path)
        
        # Run Phase 5 with Phase 1, Phase 2, Phase 3, and Phase 4 results
        start_time = time.time()
        result = await agent.execute_phase(phase1_results, phase2_results, phase3_results, phase4_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase5_only_jni_hello_world:Phase 5 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        artifacts = result.get("artifact_discovery", {}).get("artifacts", [])
        build_outputs = result.get("artifact_discovery", {}).get("build_outputs", [])
        
        print(f"INFO:test_phase5_only_jni_hello_world:Artifacts found: {len(artifacts)}")
        print(f"INFO:test_phase5_only_jni_hello_world:Build outputs found: {len(build_outputs)}")
        
        print("[OK] Phase 5 ONLY test with jni_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase5_only_jni_hello_world:Phase 5 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase5_only_jni_hello_world())
    if not success:
        sys.exit(1)
