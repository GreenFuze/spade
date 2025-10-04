#!/usr/bin/env python3
"""
Test V4 Phase 3 ONLY: Test Structure Discovery for MetaFFI
"""

import sys
import asyncio
import time
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase3_test_structure_agent_v4 import TestStructureDiscoveryAgentV4

async def test_phase3_only_metaffi():
    """Test Phase 3 ONLY: Test Structure Discovery for MetaFFI."""
    print("INFO:test_phase3_only_metaffi:Running Phase 3 ONLY: Test Structure Discovery...")
    
    # Use MetaFFI repository
    test_repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_repo_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase3_only_metaffi:Using repository: {test_repo_path}")
    
    # Load Phase 1 and Phase 2 results from previous tests
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
    
    try:
        # Create Phase 3 agent
        agent = TestStructureDiscoveryAgentV4(test_repo_path)
        
        # Run Phase 3 with Phase 1 and Phase 2 results
        start_time = time.time()
        result = await agent.execute_phase(phase1_results, phase2_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase3_only_metaffi:Phase 3 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        test_frameworks = result.get("test_structure", {}).get("test_frameworks", [])
        test_directories = result.get("test_structure", {}).get("test_organization", {}).get("test_directories", [])
        
        print(f"INFO:test_phase3_only_metaffi:Test frameworks found: {len(test_frameworks)}")
        print(f"INFO:test_phase3_only_metaffi:Test directories found: {len(test_directories)}")
        
        print("[OK] Phase 3 ONLY test with MetaFFI passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase3_only_metaffi:Phase 3 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase3_only_metaffi())
    if not success:
        sys.exit(1)
