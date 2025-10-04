#!/usr/bin/env python3
"""
Test V4 Phase 7 ONLY: Relationship Mapping for jni_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase7_relationship_mapping_agent_v4 import RelationshipMappingAgentV4

async def test_phase7_only_jni_hello_world():
    """Test Phase 7 ONLY: Relationship Mapping for jni_hello_world."""
    print("INFO:test_phase7_only_jni_hello_world:Running Phase 7 ONLY: Relationship Mapping...")
    
    # Use jni_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "jni_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase7_only_jni_hello_world:Using repository: {test_repo_path}")
    
    # Create mock Phase 1-6 results for jni_hello_world
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
    
    phase5_results = {
        "artifact_discovery": {
            "build_artifacts": [
                {
                    "name": "jni_hello_world",
                    "type": "executable",
                    "output_file": "build/Debug/jni_hello_world.exe",
                    "size": "86KB",
                    "dependencies": ["JNI"]
                },
                {
                    "name": "test_jni_wrapper",
                    "type": "executable",
                    "output_file": "build/Debug/test_jni_wrapper.exe",
                    "size": "526KB",
                    "dependencies": ["JNI"]
                }
            ],
            "library_artifacts": [],
            "package_artifacts": [
                {
                    "name": "java_hello_lib",
                    "type": "jar",
                    "output_file": "build/java_hello_lib-1.0.0.jar",
                    "version": "1.0.0"
                }
            ]
        }
    }
    
    phase6_results = {
        "component_classification": {
            "classified_components": [
                {
                    "name": "jni_hello_world",
                    "type": "executable",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "src/cpp/main.cpp",
                        "src/cpp/jni_wrapper.cpp",
                        "src/cpp/jni_wrapper.h"
                    ],
                    "output_path": "build/Debug/jni_hello_world.exe",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L27-L30",
                            "content": "add_executable(jni_hello_world\n    src/cpp/main.cpp\n    src/cpp/jni_wrapper.cpp\n)",
                            "reason": "CMake defines executable target for JNI Hello World"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L33-L39",
                            "content": "add_jar(java_hello_lib\n    SOURCES \n        src/java/HelloWorld.java\n        src/java/HelloWorldJNI.java\n    VERSION ${PROJECT_VERSION}\n    ENTRY_POINT HelloWorld\n)",
                            "reason": "CMake defines Java JAR library (dependency context for JNI example)"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L42-L44",
                            "content": "target_link_libraries(jni_hello_world\n    ${JNI_LIBRARIES}\n)",
                            "reason": "JNI libraries are linked to the executable"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L46-L49",
                            "content": "target_include_directories(jni_hello_world PRIVATE\n    ${JNI_INCLUDE_DIRS}\n)",
                            "reason": "JNI headers are included for compilation"
                        }
                    ],
                    "dependencies": ["JNI"],
                    "test_relationship": "test_jni_wrapper"
                },
                {
                    "name": "java_hello_lib",
                    "type": "library",
                    "programming_language": "Java",
                    "runtime": "JVM",
                    "source_files": [
                        "src/java/HelloWorld.java",
                        "src/java/HelloWorldJNI.java"
                    ],
                    "output_path": "build/java_hello_lib-1.0.0.jar",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L33-L39",
                            "content": "add_jar(java_hello_lib\n    SOURCES \n        src/java/HelloWorld.java\n        src/java/HelloWorldJNI.java\n    VERSION ${PROJECT_VERSION}\n    ENTRY_POINT HelloWorld\n)",
                            "reason": "CMake defines Java JAR library for Hello World"
                        }
                    ],
                    "dependencies": [],
                    "test_relationship": None
                },
                {
                    "name": "test_jni_wrapper",
                    "type": "executable",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "tests/cpp/test_jni_wrapper.cpp",
                        "src/cpp/jni_wrapper.cpp"
                    ],
                    "output_path": "build/Debug/test_jni_wrapper.exe",
                    "evidence": [
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L57-L60",
                            "content": "add_executable(test_jni_wrapper\n    tests/cpp/test_jni_wrapper.cpp\n    src/cpp/jni_wrapper.cpp\n)",
                            "reason": "CTest test executable defined for JNI wrapper"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L63-L65",
                            "content": "target_link_libraries(test_jni_wrapper\n    ${JNI_LIBRARIES}\n)",
                            "reason": "JNI libraries linked for test executable"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L67-L70",
                            "content": "target_include_directories(test_jni_wrapper PRIVATE\n    ${JNI_INCLUDE_DIRS}\n    src/cpp\n)",
                            "reason": "JNI headers and project headers included for test"
                        },
                        {
                            "file": "CMakeLists.txt",
                            "lines": "L73-L74",
                            "content": "add_test(NAME test_jni_wrapper_cpp COMMAND test_jni_wrapper)",
                            "reason": "CTest test registration for the JNI wrapper test"
                        }
                    ],
                    "dependencies": ["JNI"],
                    "test_relationship": "NA"
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
        
        print(f"INFO:test_phase7_only_jni_hello_world:Phase 7 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        relationships = result.get("relationship_mapping", {}).get("relationships", [])
        dependencies = result.get("relationship_mapping", {}).get("dependencies", [])
        
        print(f"INFO:test_phase7_only_jni_hello_world:Relationships mapped: {len(relationships)}")
        print(f"INFO:test_phase7_only_jni_hello_world:Dependencies mapped: {len(dependencies)}")
        
        print("[OK] Phase 7 ONLY test with jni_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase7_only_jni_hello_world:Phase 7 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase7_only_jni_hello_world())
    if not success:
        sys.exit(1)
