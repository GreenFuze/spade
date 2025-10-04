#!/usr/bin/env python3
"""
Test V4 Phase 5 ONLY: Artifact Discovery for MetaFFI
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase5_artifact_discovery_agent_v4 import ArtifactDiscoveryAgentV4

async def test_phase5_only_metaffi():
    """Test Phase 5 ONLY: Artifact Discovery for MetaFFI."""
    print("INFO:test_phase5_only_metaffi:Running Phase 5 ONLY: Artifact Discovery...")
    
    # Use MetaFFI repository
    test_repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_repo_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase5_only_metaffi:Using repository: {test_repo_path}")
    
    # Load Phase 1, Phase 2, Phase 3, and Phase 4 results from previous tests
    phase1_results = {
        "repository_overview": {
            "name": "MetaFFI",
            "type": "library",
            "primary_language": "C/C++",
            "build_systems": ["cmake"],
            "directory_structure": {
                "source_dirs": [
                    "containers",
                    "lang-plugin-c",
                    "lang-plugin-go",
                    "lang-plugin-openjdk",
                    "lang-plugin-python311",
                    "metaffi-core",
                    "metaffi-installer"
                ],
                "test_dirs": [],
                "build_dirs": [
                    "cmake-build-debug",
                    "cmake-build-debug-wsl-2404",
                    "cmake-build-relwithdebinfo",
                    "cmake-build-relwithdebinfo-wsl-2404"
                ],
                "config_dirs": ["cmake"]
            },
            "entry_points": ["CMakeLists.txt", "MetaFFI.code-workspace"],
            "exploration_scope": {
                "priority_dirs": [
                    "metaffi-core",
                    "metaffi-installer",
                    "lang-plugin-c",
                    "lang-plugin-go",
                    "lang-plugin-openjdk",
                    "lang-plugin-python311",
                    "containers"
                ],
                "skip_dirs": [
                    "cmake",
                    "cmake-build-debug",
                    "cmake-build-debug-wsl-2404",
                    "cmake-build-relwithdebinfo",
                    "cmake-build-relwithdebinfo-wsl-2404"
                ],
                "deep_exploration": [
                    "metaffi-core",
                    "metaffi-installer",
                    "lang-plugin-c",
                    "lang-plugin-go",
                    "lang-plugin-openjdk",
                    "lang-plugin-python311"
                ]
            }
        }
    }
    
    phase2_results = {
        "source_structure": {
            "source_directories": [
                {
                    "path": "metaffi-core",
                    "language": "C/C++",
                    "components": ["XLLR", "CLI", "plugin-sdk"],
                    "files": ["CMakeLists.txt", "LICENSE.txt"],
                    "dependencies": ["Boost (via XLLR CMake)"],
                    "build_evidence": "CMakeLists.txt: add_subdirectory(plugin-sdk), add_subdirectory(XLLR), add_subdirectory(CLI); metaffi-core target; includes run_sdk_tests.cmake",
                    "exploration_complete": True
                },
                {
                    "path": "containers",
                    "language": "Python",
                    "components": ["LICENSE.md", "metaffi-u2204.dockerfile", "metaffi-win-core2022.dockerfile", "requirements.txt"],
                    "files": ["LICENSE.md", "metaffi-u2204.dockerfile", "metaffi-win-core2022.dockerfile", "requirements.txt"],
                    "dependencies": ["Python 3.x"],
                    "build_evidence": "No CMakeLists.txt; container/dockerfiles and Python requirements indicate environment setup",
                    "exploration_complete": True
                },
                {
                    "path": "lang-plugin-c",
                    "language": "C/C++",
                    "components": ["plugin-sdk", "idl", "api", "runtime", "compiler"],
                    "files": ["CMakeLists.txt", "LICENSE", "idl/CMakeLists.txt"],
                    "dependencies": ["Boost", "Boost::filesystem", "Boost::thread", "doctest"],
                    "build_evidence": "CMakeLists.txt: add_subdirectory for plugin-sdk and idl; custom target 'c'; idl CMakeLists.txt loads doctest; Boost imports",
                    "exploration_complete": True
                },
                {
                    "path": "lang-plugin-go",
                    "language": "Go",
                    "components": ["plugin-sdk", "runtime", "go-runtime", "idl", "compiler", "api"],
                    "files": ["CMakeLists.txt", "LICENSE"],
                    "dependencies": ["Go tooling via CMake; xllr.go; go test targets"],
                    "build_evidence": "CMakeLists.txt defines go target and subdirectories; 'go' target aggregates tests",
                    "exploration_complete": True
                },
                {
                    "path": "lang-plugin-openjdk",
                    "language": "C/C++",
                    "components": ["plugin-sdk", "idl", "compiler", "runtime", "xllr-openjdk-bridge", "api"],
                    "files": ["CMakeLists.txt", "LICENSE"],
                    "dependencies": ["Boost (likely)", "JNI bridge (xllr-openjdk-bridge)"],
                    "build_evidence": "CMakeLists.txt lists subdirectories including xllr-openjdk-bridge",
                    "exploration_complete": True
                },
                {
                    "path": "lang-plugin-python311",
                    "language": "Python",
                    "components": ["plugin-sdk", "runtime", "idl", "compiler", "api"],
                    "files": ["CMakeLists.txt", "LICENSE", "build_plugin_installer_helper.py"],
                    "dependencies": ["Python3"],
                    "build_evidence": "CMakeLists.txt defines python311 target; subdirectories for plugin",
                    "exploration_complete": True
                },
                {
                    "path": "metaffi-installer",
                    "language": "Python",
                    "components": ["build_installer.py", "build_plugin_installer.py", "installers_output", "metaffi_installer_template.py", "metaffi_plugin_installer_template.py", "post_install_tests_template.py", "uninstall_template.py", "version.py"],
                    "files": ["build_installer.py", "build_plugin_installer.py", "metaffi_installer_template.py", "metaffi_plugin_installer_template.py", "post_install_tests_template.py", "uninstall_template.py", "version.py", "__pycache__"],
                    "dependencies": ["Python3"],
                    "build_evidence": "No CMakeLists.txt; Python-based installer tooling",
                    "exploration_complete": True
                }
            ],
            "language_analysis": {
                "primary_language": "C/C++",
                "secondary_languages": ["Python", "Go"],
                "language_distribution": {
                    "C/C++": 0.57,
                    "Python": 0.29,
                    "Go": 0.14
                }
            },
            "component_hints": [
                {
                    "name": "metaffi-core XLLR",
                    "type": "runtime library",
                    "source_files": ["metaffi-core/XLLR/xllr_api.cpp", "metaffi-core/XLLR/runtime_plugin.cpp"],
                    "language": "C++"
                },
                {
                    "name": "metaffi-core CLI",
                    "type": "executable",
                    "source_files": ["metaffi-core/CLI/main.cpp", "metaffi-core/CLI/cli_executor.cpp"],
                    "language": "C++"
                }
            ],
            "exploration_summary": {
                "total_directories_explored": 7,
                "directories_with_build_config": 5,
                "directories_without_build_config": 2,
                "all_phase1_directories_covered": True
            }
        }
    }
    
    phase3_results = {
        "test_structure": {
            "test_frameworks": [
                {
                    "name": "CTest",
                    "version": "unknown",
                    "config_files": ["CMakeLists.txt"],
                    "test_directories": [
                        "lang-plugin-c/compiler/test",
                        "lang-plugin-c/runtime/test",
                        "lang-plugin-openjdk/idl/test"
                    ]
                },
                {
                    "name": "JUnit",
                    "version": "unknown",
                    "config_files": ["pom.xml", "build.gradle"],
                    "test_directories": [
                        "lang-plugin-openjdk/idl/test/java_extractor"
                    ]
                },
                {
                    "name": "Python (custom runner)",
                    "version": "unknown",
                    "config_files": ["run_api_tests.py"],
                    "test_directories": [
                        "lang-plugin-python311/api/tests",
                        "lang-plugin-python311/idl",
                        "lang-plugin-python311/runtime/test"
                    ],
                    "notes": "Python tests appear to be orchestrated by a custom runner (run_api_tests.py) rather than a single pytest/unittest config."
                },
                {
                    "name": "Go testing",
                    "version": "unknown",
                    "config_files": ["go.mod", "go.sum"],
                    "test_directories": [
                        "lang-plugin-go/go-runtime/test",
                        "lang-plugin-go/runtime/test",
                        "lang-plugin-go/api/tests"
                    ]
                }
            ],
            "test_organization": {
                "test_directories": [
                    {
                        "path": "lang-plugin-c/compiler/test",
                        "framework": "CTest",
                        "test_files": ["test_runtime.cpp"],
                        "targets": ["c_compiler_runtime"]
                    },
                    {
                        "path": "lang-plugin-c/runtime/test",
                        "framework": "CTest",
                        "test_files": ["test_runtime.cpp"],
                        "targets": ["c_runtime_tests"]
                    },
                    {
                        "path": "lang-plugin-go/go-runtime/test",
                        "framework": "Go testing",
                        "test_files": ["TestRuntime.go"],
                        "targets": ["go_runtime"]
                    },
                    {
                        "path": "lang-plugin-openjdk/idl/test",
                        "framework": "JUnit",
                        "test_files": ["BytecodeExtractorTest.java", "JarExtractorTest.java"],
                        "targets": ["openjdk_idl_tests"]
                    },
                    {
                        "path": "lang-plugin-python311/api/tests",
                        "framework": "Python (custom runner)",
                        "test_files": ["run_api_tests.py"],
                        "targets": ["python_api_tests"]
                    },
                    {
                        "path": "lang-plugin-python311/idl",
                        "framework": "Python (custom runner)",
                        "test_files": ["test_fixed_extractor.py", "test_py_extractor.py", "test_py_idl_generator.py"],
                        "targets": ["python_idl_tests"]
                    },
                    {
                        "path": "lang-plugin-python311/runtime/test",
                        "framework": "Python (custom runner)",
                        "test_files": ["runtime_test_target.py"],
                        "targets": ["python_runtime_tests"]
                    }
                ]
            },
            "test_configuration": {
                "test_command": "ctest --output-on-failure; go test ./...; python3 lang-plugin-python311/api/tests/run_api_tests.py; mvn test || gradle test (for Java tests as applicable)",
                "test_timeout": "300",
                "parallel_tests": True
            }
        }
    }
    
    phase4_results = {
        "build_analysis": {
            "build_targets": [
                {
                    "name": "xllr",
                    "type": "library",
                    "source_files": [
                        "metaffi-core/XLLR/xllr_api.cpp",
                        "metaffi-core/XLLR/runtime_plugin.cpp"
                    ],
                    "dependencies": [
                        "plugin-sdk",
                        "Boost::filesystem",
                        "Boost::thread"
                    ],
                    "output_path": "build/xllr",
                    "build_options": []
                },
                {
                    "name": "metaffi",
                    "type": "executable",
                    "source_files": [
                        "metaffi-core/CLI/main.cpp",
                        "metaffi-core/CLI/cli_executor.cpp"
                    ],
                    "dependencies": [
                        "Boost::filesystem",
                        "Boost::program_options",
                        "plugin-sdk"
                    ],
                    "output_path": "build/metaffi",
                    "build_options": []
                },
                {
                    "name": "metaffi-core",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "xllr",
                        "metaffi",
                        "cdts_test",
                        "xllr_capi_test"
                    ],
                    "output_path": "",
                    "build_options": []
                },
                {
                    "name": "python311",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "xllr.python311",
                        "python_runtime_test",
                        "metaffi.idl.python311",
                        "python311_idl_plugin_test",
                        "metaffi.compiler.python311"
                    ],
                    "output_path": "",
                    "build_options": []
                },
                {
                    "name": "openjdk",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "xllr.openjdk",
                        "xllr.openjdk.jni.bridge",
                        "xllr.openjdk.bridge",
                        "metaffi.api",
                        "openjdk_api_test",
                        "cdts_java_test",
                        "metaffi.idl.openjdk",
                        "metaffi.compiler.openjdk"
                    ],
                    "output_path": "",
                    "build_options": []
                },
                {
                    "name": "go",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "go_runtime"
                    ],
                    "output_path": "",
                    "build_options": []
                },
                {
                    "name": "c",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "metaffi.idl.c",
                        "idl.c.test"
                    ],
                    "output_path": "",
                    "build_options": []
                },
                {
                    "name": "MetaFFI",
                    "type": "custom_target",
                    "source_files": [],
                    "dependencies": [
                        "metaffi-core",
                        "python311",
                        "openjdk",
                        "go"
                    ],
                    "output_path": "",
                    "build_options": []
                }
            ],
            "build_dependencies": [
                {
                    "source": "MetaFFI",
                    "target": "metaffi-core",
                    "type": "aggregate_dependency"
                },
                {
                    "source": "MetaFFI",
                    "target": "python311",
                    "type": "aggregate_dependency"
                },
                {
                    "source": "MetaFFI",
                    "target": "openjdk",
                    "type": "aggregate_dependency"
                },
                {
                    "source": "MetaFFI",
                    "target": "go",
                    "type": "aggregate_dependency"
                },
                {
                    "source": "metaffi-core",
                    "target": "xllr",
                    "type": "link_dependency"
                },
                {
                    "source": "metaffi-core",
                    "target": "metaffi",
                    "type": "link_dependency"
                },
                {
                    "source": "lang-plugin-python311",
                    "target": "xllr.python311",
                    "type": "link_dependency"
                },
                {
                    "source": "lang-plugin-openjdk",
                    "target": "xllr.openjdk",
                    "type": "link_dependency"
                },
                {
                    "source": "lang-plugin-go",
                    "target": "go_runtime",
                    "type": "link_dependency"
                },
                {
                    "source": "lang-plugin-c",
                    "target": "idl.c.test",
                    "type": "link_dependency"
                }
            ],
            "build_configuration": {
                "build_type": "Debug|Release",
                "compiler": "gcc|clang|msvc",
                "flags": []
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
        
        print(f"INFO:test_phase5_only_metaffi:Phase 5 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        artifacts = result.get("artifact_discovery", {}).get("artifacts", [])
        build_outputs = result.get("artifact_discovery", {}).get("build_outputs", [])
        
        print(f"INFO:test_phase5_only_metaffi:Artifacts found: {len(artifacts)}")
        print(f"INFO:test_phase5_only_metaffi:Build outputs found: {len(build_outputs)}")
        
        print("[OK] Phase 5 ONLY test with MetaFFI passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase5_only_metaffi:Phase 5 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase5_only_metaffi())
    if not success:
        sys.exit(1)
