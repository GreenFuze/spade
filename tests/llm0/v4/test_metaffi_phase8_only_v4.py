#!/usr/bin/env python3
"""
Test Phase 8 (RIG Assembly) in isolation for MetaFFI repository.
This test validates the RIG Assembly Agent's ability to assemble the final RIG
from all previous phase results.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase8_rig_assembly_agent_v4 import RIGAssemblyAgentV4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_phase8_only_metaffi():
    """Test Phase 8 (RIG Assembly) in isolation for MetaFFI."""
    
    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    
    if not metaffi_path.exists():
        logger.error(f"MetaFFI repository not found at {metaffi_path}")
        return False
    
    logger.info(f"Testing Phase 8 (RIG Assembly) with MetaFFI repository: {metaffi_path}")
    
    # Create Phase 8 agent
    agent = RIGAssemblyAgentV4(metaffi_path)
    
    # Mock previous phase results (simplified for testing)
    phase1_results = {
        "repository_overview": {
            "name": "MetaFFI",
            "type": "library",
            "primary_language": "C/C++",
            "build_systems": ["cmake"],
            "directory_structure": {
                "source_dirs": ["metaffi-core", "lang-plugin-c", "lang-plugin-go", "lang-plugin-openjdk", "lang-plugin-python311", "metaffi-installer", "containers"],
                "test_dirs": [],
                "build_dirs": ["cmake-build-debug", "cmake-build-relwithdebinfo"],
                "config_dirs": ["cmake"]
            },
            "entry_points": ["CMakeLists.txt", "MetaFFI.code-workspace"],
            "exploration_scope": {
                "priority_dirs": ["metaffi-core", "metaffi-installer", "lang-plugin-c", "lang-plugin-go", "lang-plugin-openjdk", "lang-plugin-python311", "containers"],
                "skip_dirs": ["cmake", "cmake-build-debug", "cmake-build-relwithdebinfo"],
                "deep_exploration": ["metaffi-core", "metaffi-installer", "lang-plugin-c", "lang-plugin-go", "lang-plugin-openjdk", "lang-plugin-python311"]
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
                }
            ],
            "language_analysis": {
                "primary_language": "C/C++",
                "secondary_languages": ["Python", "Go"],
                "language_distribution": {"C/C++": 0.57, "Python": 0.29, "Go": 0.14}
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
                    "test_directories": ["lang-plugin-c/compiler/test", "lang-plugin-c/runtime/test", "lang-plugin-openjdk/idl/test"]
                },
                {
                    "name": "JUnit",
                    "version": "unknown",
                    "config_files": ["pom.xml", "build.gradle"],
                    "test_directories": ["lang-plugin-openjdk/idl/test/java_extractor"]
                },
                {
                    "name": "Python (custom runner)",
                    "version": "unknown",
                    "config_files": ["run_api_tests.py"],
                    "test_directories": ["lang-plugin-python311/api/tests", "lang-plugin-python311/idl", "lang-plugin-python311/runtime/test"]
                },
                {
                    "name": "Go testing",
                    "version": "unknown",
                    "config_files": ["go.mod", "go.sum"],
                    "test_directories": ["lang-plugin-go/go-runtime/test", "lang-plugin-go/runtime/test", "lang-plugin-go/api/tests"]
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
                    "source_files": ["metaffi-core/XLLR/xllr_api.cpp", "metaffi-core/XLLR/runtime_plugin.cpp"],
                    "dependencies": ["plugin-sdk", "Boost::filesystem", "Boost::thread"],
                    "output_path": "build/xllr",
                    "build_options": []
                },
                {
                    "name": "metaffi",
                    "type": "executable",
                    "source_files": ["metaffi-core/CLI/main.cpp", "metaffi-core/CLI/cli_executor.cpp"],
                    "dependencies": ["Boost::filesystem", "Boost::program_options", "plugin-sdk"],
                    "output_path": "build/metaffi",
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
                    "source": "metaffi-core",
                    "target": "xllr",
                    "type": "link_dependency"
                },
                {
                    "source": "metaffi-core",
                    "target": "metaffi",
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
                    "source_files": ["metaffi-core/XLLR/xllr_api.cpp", "metaffi-core/XLLR/runtime_plugin.cpp"],
                    "output_path": "build/xllr",
                    "evidence": [
                        {
                            "file": "metaffi-core/XLLR/CMakeLists.txt",
                            "lines": "7-11",
                            "content": "c_cpp_shared_lib(xllr ...)",
                            "reason": "XLLR is built as a shared library via c_cpp_shared_lib"
                        }
                    ],
                    "dependencies": ["plugin-sdk", "Boost::filesystem", "Boost::thread"],
                    "test_relationship": "XLLR is a runtime library used by metaffi-core and tests"
                },
                {
                    "name": "metaffi",
                    "type": "executable",
                    "programming_language": "C++",
                    "runtime": "native",
                    "source_files": ["metaffi-core/CLI/main.cpp", "metaffi-core/CLI/cli_executor.cpp"],
                    "output_path": "build/metaffi",
                    "evidence": [
                        {
                            "file": "metaffi-core/CLI/CMakeLists.txt",
                            "lines": "6-10",
                            "content": "c_cpp_exe(metaffi ...)",
                            "reason": "Executable target metaffi defined"
                        }
                    ],
                    "dependencies": ["Boost::filesystem", "Boost::program_options", "plugin-sdk"],
                    "test_relationship": "Metaffi is the CLI component of metaffi-core"
                }
            ]
        }
    }
    
    phase7_results = {
        "relationships": {
            "component_dependencies": [
                {
                    "source": "metaffi-core",
                    "target": "xllr",
                    "type": "link_dependency",
                    "evidence": [
                        {
                            "file": "metaffi-core/CMakeLists.txt",
                            "lines": "5-9",
                            "content": "add_subdirectory(\"${CMAKE_CURRENT_LIST_DIR}/XLLR\")",
                            "reason": "XLLR is included as a subdirectory of metaffi-core"
                        }
                    ]
                },
                {
                    "source": "metaffi-core",
                    "target": "metaffi",
                    "type": "link_dependency",
                    "evidence": [
                        {
                            "file": "metaffi-core/CLI/CMakeLists.txt",
                            "lines": "6-10",
                            "content": "c_cpp_exe(metaffi ...)",
                            "reason": "metaffi executable target defined in CLI CMakeLists"
                        }
                    ]
                }
            ],
            "test_relationships": [
                {
                    "test": "c_compiler_runtime",
                    "target": "lang-plugin-c",
                    "type": "unit_test",
                    "evidence": [
                        {
                            "file": "TEST STRUCTURE JSON",
                            "lines": "",
                            "content": "CTest-based test: path lang-plugin-c/compiler/test; target c_compiler_runtime; test file test_runtime.cpp",
                            "reason": "CTest-based unit test for C compiler runtime"
                        }
                    ]
                }
            ],
            "external_dependencies": [
                {
                    "component": "xllr",
                    "package": "Boost",
                    "type": "external_library",
                    "version": "unknown",
                    "evidence": [
                        {
                            "file": "metaffi-core/XLLR/CMakeLists.txt",
                            "lines": "1-2",
                            "content": "find_or_install_package(Boost COMPONENTS filesystem thread)",
                            "reason": "Boost is used by XLLR"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        # Execute Phase 8
        logger.info("Executing Phase 8 (RIG Assembly)...")
        result = await agent.execute_phase(
            phase1_results, phase2_results, phase3_results, phase4_results,
            phase5_results, phase6_results, phase7_results
        )
        
        logger.info(f"Phase 8 completed in {result.get('execution_time', 'unknown')} seconds")
        
        # Validate result structure
        if "rig_assembly" not in result:
            logger.error("Phase 8 result missing 'rig_assembly' key")
            return False
        
        rig_assembly = result["rig_assembly"]
        
        # Check for required fields
        required_fields = ["components", "relationships", "validation_metrics"]
        for field in required_fields:
            if field not in rig_assembly:
                logger.error(f"Phase 8 result missing required field: {field}")
                return False
        
        # Log results
        components = rig_assembly.get("components", [])
        relationships = rig_assembly.get("relationships", [])
        validation_metrics = rig_assembly.get("validation_metrics", {})
        
        logger.info(f"Components assembled: {len(components)}")
        logger.info(f"Relationships assembled: {len(relationships)}")
        logger.info(f"Validation metrics: {validation_metrics}")
        
        # Check if RIG is valid
        if validation_metrics.get("is_valid", False):
            logger.info("✅ RIG assembly successful - RIG is valid")
        else:
            logger.warning("⚠️ RIG assembly completed but RIG may not be valid")
            logger.warning(f"Validation issues: {validation_metrics.get('issues', [])}")
        
        logger.info("[OK] Phase 8 ONLY test with MetaFFI passed")
        return True
        
    except Exception as e:
        logger.error(f"Phase 8 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase8_only_metaffi())
    sys.exit(0 if success else 1)
