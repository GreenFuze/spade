#!/usr/bin/env python3
"""
Test V4 Phase 7 ONLY: Relationship Mapping for MetaFFI
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase7_relationship_mapping_agent_v4 import RelationshipMappingAgentV4

async def test_phase7_only_metaffi():
    """Test Phase 7 ONLY: Relationship Mapping for MetaFFI."""
    print("INFO:test_phase7_only_metaffi:Running Phase 7 ONLY: Relationship Mapping...")
    
    # Use MetaFFI repository
    test_repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_repo_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase7_only_metaffi:Using repository: {test_repo_path}")
    
    # Load Phase 1-6 results from previous tests
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
    
    phase5_results = {
        "artifact_discovery": {
            "build_artifacts": [
                {
                    "name": "metaffi",
                    "type": "executable",
                    "output_file": "build/metaffi",
                    "size": "unknown",
                    "dependencies": ["Boost::filesystem", "Boost::program_options", "plugin-sdk"]
                }
            ],
            "library_artifacts": [
                {
                    "name": "xllr",
                    "type": "library",
                    "output_file": "build/xllr",
                    "size": "unknown",
                    "dependencies": ["plugin-sdk", "Boost::filesystem", "Boost::thread"]
                }
            ],
            "package_artifacts": []
        }
    }
    
    phase6_results = {
        "component_classification": {
            "classified_components": [
                {
                    "name": "xllr",
                    "type": "library",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "metaffi-core/XLLR/xllr_api.cpp",
                        "metaffi-core/XLLR/runtime_plugin.cpp"
                    ],
                    "output_path": "build/xllr",
                    "evidence": [
                        {
                            "file": "metaffi-core/XLLR/CMakeLists.txt",
                            "lines": "7-11",
                            "content": "c_cpp_shared_lib(xllr\n  \"${xllr_src};${sdk_src}\"\n  \"${sdk_include_dir};${Boost_INCLUDE_DIRS}\"\n  \"Boost::filesystem;Boost::thread\"\n  \".\")",
                            "reason": "XLLR is built as a shared library via c_cpp_shared_lib"
                        },
                        {
                            "file": "metaffi-core/XLLR/CMakeLists.txt",
                            "lines": "13-13",
                            "content": "set(xllr xllr PARENT_SCOPE)",
                            "reason": "library name propagated to parent scope"
                        },
                        {
                            "file": "",
                            "lines": "",
                            "content": "Build artifact evidence: library output path is build/xllr for the xllr library",
                            "reason": "artifact evidence confirms library output path"
                        }
                    ],
                    "dependencies": [
                        "plugin-sdk",
                        "Boost::filesystem",
                        "Boost::thread"
                    ],
                    "test_relationship": "XLLR is a runtime library used by metaffi-core and tests; included in the metaffi-core build graph (metaffi-core target depends on xllr)."
                },
                {
                    "name": "metaffi",
                    "type": "executable",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "metaffi-core/CLI/main.cpp",
                        "metaffi-core/CLI/cli_executor.cpp"
                    ],
                    "output_path": "build/metaffi",
                    "evidence": [
                        {
                            "file": "metaffi-core/CLI/CMakeLists.txt",
                            "lines": "6-10",
                            "content": "c_cpp_exe(metaffi\n\t\t\"${cli_src};${sdk_src}\"\n\t\t\"${cli_include_dir};${sdk_include_dir};${Boost_INCLUDE_DIRS}\"\n\t\t\"Boost::filesystem;Boost::program_options\"\n\t\t\".\")",
                            "reason": "Executable target metaffi defined"
                        },
                        {
                            "file": "metaffi-core/CLI/CMakeLists.txt",
                            "lines": "12-12",
                            "content": "set(metaffi metaffi PARENT_SCOPE)",
                            "reason": "executable target propagated to parent scope"
                        }
                    ],
                    "dependencies": [
                        "Boost::filesystem",
                        "Boost::program_options",
                        "plugin-sdk"
                    ],
                    "test_relationship": "Metaffi is the CLI component of metaffi-core; part of the core build and tested via the metaffi-core suite."
                },
                {
                    "name": "metaffi-core",
                    "type": "utility",
                    "programming_language": "C/C++",
                    "runtime": "native",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "metaffi-core/CMakeLists.txt",
                            "lines": "3-9",
                            "content": "add_subdirectory(XLLR)\nadd_subdirectory(CLI)\n# run SDK tests",
                            "reason": "metaffi-core wires in XLLR and CLI subdirectories (core components)"
                        },
                        {
                            "file": "metaffi-core/CMakeLists.txt",
                            "lines": "15-17",
                            "content": "add_custom_target(metaffi-core\n\tDEPENDS xllr metaffi cdts_test xllr_capi_test\n)",
                            "reason": "metaffi-core acts as an aggregator target for core components"
                        }
                    ],
                    "dependencies": [
                        "xllr",
                        "metaffi",
                        "cdts_test",
                        "xllr_capi_test"
                    ],
                    "test_relationship": "Core aggregation target for MetaFFI; used by top-level MetaFFI build"
                },
                {
                    "name": "lang-plugin-python311",
                    "type": "utility",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "lang-plugin-python311/CMakeLists.txt",
                            "lines": "15-17",
                            "content": "add_custom_target(python311\n\tDEPENDS xllr.python311 python_runtime_test metaffi.idl.python311 python311_idl_plugin_test metaffi.compiler.python311\n)",
                            "reason": "Python 311 plugin aggregator target"
                        },
                        {
                            "file": "lang-plugin-python311/CMakeLists.txt",
                            "lines": "21-21",
                            "content": "set(python311 ${python311} PARENT_SCOPE)",
                            "reason": "exposed to parent scope"
                        }
                    ],
                    "dependencies": [
                        "xllr.python311",
                        "python_runtime_test",
                        "metaffi.idl.python311",
                        "python311_idl_plugin_test",
                        "metaffi.compiler.python311"
                    ],
                    "test_relationship": "Python 3.11 plugin components are exercised by Python-based tests (see test structure for Python tests)."
                },
                {
                    "name": "lang-plugin-go",
                    "type": "utility",
                    "programming_language": "Go",
                    "runtime": "native",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "lang-plugin-go/CMakeLists.txt",
                            "lines": "1-4",
                            "content": "# add SDK\nadd_subdirectory(\"${CMAKE_CURRENT_LIST_DIR}/plugin-sdk\")\n\n# runtime\nadd_subdirectory(\"${CMAKE_CURRENT_LIST_DIR}/runtime\")\n",
                            "reason": "Go plugin scaffolding and submodules"
                        },
                        {
                            "file": "lang-plugin-go/CMakeLists.txt",
                            "lines": "12-20",
                            "content": "add_custom_target(go ALL\n\tDEPENDS xllr.go metaffi.compiler.go metaffi.idl.go go_api_test\n)\nset_target_properties(go PROPERTIES EXCLUDE_FROM_ALL TRUE)",
                            "reason": "Go runtime aggregator target"
                        }
                    ],
                    "dependencies": [
                        "xllr.go",
                        "metaffi.compiler.go",
                        "metaffi.idl.go",
                        "go_api_test"
                    ],
                    "test_relationship": "Go runtime tests are invoked via the Go testing framework as per test structure."
                },
                {
                    "name": "lang-plugin-openjdk",
                    "type": "utility",
                    "programming_language": "C/C++",
                    "runtime": "native",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "lang-plugin-openjdk/CMakeLists.txt",
                            "lines": "1-6",
                            "content": "# add SDK\nadd_subdirectory(\"${CMAKE_CURRENT_LIST_DIR}/plugin-sdk\")\n\n# idl plugin\nadd_subdirectory(\"${CMAKE_CURRENT_LIST_DIR}/idl\")\n",
                            "reason": "OpenJDK plugin submodules wired in"
                        },
                        {
                            "file": "lang-plugin-openjdk/CMakeLists.txt",
                            "lines": "8-12",
                            "content": "add_custom_target(openjdk\n\tDEPENDS xllr.openjdk xllr.openjdk.jni.bridge xllr.openjdk.bridge metaffi.api openjdk_api_test cdts_java_test metaffi.idl.openjdk metaffi.compiler.openjdk\n)",
                            "reason": "OpenJDK plugin aggregator target"
                        }
                    ],
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
                    "test_relationship": "OpenJDK tests are orchestrated via JUnit/Java tests under the openjdk target (see test structure)."
                },
                {
                    "name": "lang-plugin-c",
                    "type": "utility",
                    "programming_language": "C/C++",
                    "runtime": "native",
                    "source_files": [],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "lang-plugin-c/CMakeLists.txt",
                            "lines": "18-19",
                            "content": "add_custom_target(c ALL\n\tDEPENDS metaffi.idl.c idl.c.test\n)",
                            "reason": "C plugin aggregator target"
                        }
                    ],
                    "dependencies": [
                        "metaffi.idl.c",
                        "idl.c.test"
                    ],
                    "test_relationship": "C plugin tests are integrated via CTest (see test structure for C tests)."
                },
                {
                    "name": "metaffi-installer",
                    "type": "utility",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [
                        "build_installer.py",
                        "build_plugin_installer.py",
                        "installers_output",
                        "metaffi_installer_template.py",
                        "metaffi_plugin_installer_template.py",
                        "post_install_tests_template.py",
                        "uninstall_template.py",
                        "version.py",
                        "__pycache__"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "metaffi-installer",
                            "lines": "",
                            "content": "Python-based installer tooling (no CMakeLists.txt).",
                            "reason": "Metaffi installer is Python-based tooling"
                        }
                    ],
                    "dependencies": [
                        "Python3"
                    ],
                    "test_relationship": "Installer tooling is not covered by a dedicated CTest/Go/Java test harness in this repo excerpt."
                },
                {
                    "name": "containers",
                    "type": "utility",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [
                        "LICENSE.md",
                        "metaffi-u2204.dockerfile",
                        "metaffi-win-core2022.dockerfile",
                        "requirements.txt"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "SOURCE STRUCTURE JSON",
                            "lines": "",
                            "content": "containers directory contains Dockerfiles and Python requirements indicating environment setup",
                            "reason": "Container/environment tooling"
                        }
                    ],
                    "dependencies": [
                        "Python3"
                    ],
                    "test_relationship": "Container-related tooling is environment setup support; no unit tests shown."
                },
                {
                    "name": "c_compiler_runtime",
                    "type": "test",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "lang-plugin-c/compiler/test/test_runtime.cpp"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "CTest-based test: path lang-plugin-c/compiler/test; target c_compiler_runtime; test file test_runtime.cpp",
                            "reason": "C test target mapping"
                        }
                    ],
                    "dependencies": [
                        "metaffi-core"
                    ],
                    "test_relationship": "CTest-based unit test for C compiler runtime"
                },
                {
                    "name": "c_runtime_tests",
                    "type": "test",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": [
                        "lang-plugin-c/runtime/test/test_runtime.cpp"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "CTest-based test: path lang-plugin-c/runtime/test; target c_runtime_tests; test file test_runtime.cpp",
                            "reason": "C test target mapping"
                        }
                    ],
                    "dependencies": [
                        "metaffi-core"
                    ],
                    "test_relationship": "CTest-based unit test for C runtime"
                },
                {
                    "name": "go_runtime_test",
                    "type": "test",
                    "programming_language": "Go",
                    "runtime": "native",
                    "source_files": [
                        "lang-plugin-go/go-runtime/test/TestRuntime.go"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "Go testing; test target go_runtime; file TestRuntime.go",
                            "reason": "Go unit test target for runtime"
                        }
                    ],
                    "dependencies": [
                        "lang-plugin-go/go-runtime"
                    ],
                    "test_relationship": "Go runtime tests"
                },
                {
                    "name": "openjdk_idl_tests",
                    "type": "test",
                    "programming_language": "Java",
                    "runtime": "native",
                    "source_files": [
                        "lang-plugin-openjdk/idl/test/BytecodeExtractorTest.java",
                        "lang-plugin-openjdk/idl/test/JarExtractorTest.java"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "JUnit tests; path lang-plugin-openjdk/idl/test; test files BytecodeExtractorTest.java, JarExtractorTest.java",
                            "reason": "JUnit-based OpenJDK IDL tests"
                        }
                    ],
                    "dependencies": [
                        "metaffi.api",
                        "openjdk_api_test"
                    ],
                    "test_relationship": "JUnit tests for OpenJDK IDL"
                },
                {
                    "name": "python_api_tests",
                    "type": "test",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [
                        "lang-plugin-python311/api/tests/run_api_tests.py"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "Python API tests; path lang-plugin-python311/api/tests; test file run_api_tests.py",
                            "reason": "Python custom-runner tests for API"
                        }
                    ],
                    "dependencies": [
                        "lang-plugin-python311/api/tests/run_api_tests.py"
                    ],
                    "test_relationship": "Python API tests"
                },
                {
                    "name": "python_idl_tests",
                    "type": "test",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [
                        "lang-plugin-python311/idl/test_fixed_extractor.py",
                        "lang-plugin-python311/idl/test_py_extractor.py",
                        "lang-plugin-python311/idl/test_py_idl_generator.py"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "Python IDL tests; path lang-plugin-python311/idl; test files listed; target python_idl_tests",
                            "reason": "Python IDL test suite"
                        }
                    ],
                    "dependencies": [],
                    "test_relationship": "Python IDL tests"
                },
                {
                    "name": "python_runtime_tests",
                    "type": "test",
                    "programming_language": "Python",
                    "runtime": "interpreted",
                    "source_files": [
                        "lang-plugin-python311/runtime/test/runtime_test_target.py"
                    ],
                    "output_path": "",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "Python runtime tests; path lang-plugin-python311/runtime/test; test file runtime_test_target.py; target python_runtime_tests",
                            "reason": "Python runtime test suite"
                        }
                    ],
                    "dependencies": [],
                    "test_relationship": "Python runtime tests"
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
        
        print(f"INFO:test_phase7_only_metaffi:Phase 7 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        relationships = result.get("relationship_mapping", {}).get("relationships", [])
        dependencies = result.get("relationship_mapping", {}).get("dependencies", [])
        
        print(f"INFO:test_phase7_only_metaffi:Relationships mapped: {len(relationships)}")
        print(f"INFO:test_phase7_only_metaffi:Dependencies mapped: {len(dependencies)}")
        
        print("[OK] Phase 7 ONLY test with MetaFFI passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase7_only_metaffi:Phase 7 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase7_only_metaffi())
    if not success:
        sys.exit(1)
