#!/usr/bin/env python3
"""
Test the V3 Classification Agent with MetaFFI discovery results.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v3.llm0_rig_generator_v3 import ClassificationAgent


async def test_metaffi_classification_v3():
    """Test the V3 Classification Agent on MetaFFI repository."""
    
    print("=" * 80)
    print("TESTING V3 CLASSIFICATION AGENT")
    print("=" * 80)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"Testing MetaFFI classification with V3 agent at: {test_path}")
    
    # Create classification agent
    classification_agent = ClassificationAgent(
        repository_path=test_path,
        max_requests=200
    )
    
    print("Classification agent created with:")
    print(f"  - Max requests: {classification_agent.max_requests}")
    print(f"  - Usage limit: {classification_agent.agent._usage_limit}")
    
    # Discovery results from previous phase (simulated)
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
    
    print("\nStarting classification with discovery results...")
    print(f"Discovery found {len(discovery_results['repository_info']['source_directories'])} source directories")
    
    try:
        result = await classification_agent.classify_components(discovery_results)
        
        print("\n" + "=" * 80)
        print("CLASSIFICATION RESULTS:")
        print("=" * 80)
        
        # Print key results
        components = result.get("components", [])
        aggregators = result.get("aggregators", [])
        runners = result.get("runners", [])
        utilities = result.get("utilities", [])
        tests = result.get("tests", [])
        
        print(f"Components Found: {len(components)}")
        for comp in components[:5]:  # Show first 5
            print(f"  - {comp.get('name', 'UNKNOWN')} ({comp.get('type', 'UNKNOWN')})")
            print(f"    Runtime: {comp.get('runtime', 'UNKNOWN')}")
            print(f"    Location: {comp.get('location', 'UNKNOWN')}")
        if len(components) > 5:
            print(f"  ... and {len(components) - 5} more")
        
        print(f"\nAggregators Found: {len(aggregators)}")
        for agg in aggregators[:3]:  # Show first 3
            print(f"  - {agg.get('name', 'UNKNOWN')}")
            print(f"    Sub-aggregators: {len(agg.get('sub_aggregators', []))}")
        if len(aggregators) > 3:
            print(f"  ... and {len(aggregators) - 3} more")
        
        print(f"\nRunners Found: {len(runners)}")
        for run in runners[:3]:  # Show first 3
            print(f"  - {run.get('name', 'UNKNOWN')}")
            print(f"    Commands: {len(run.get('commands', []))}")
        if len(runners) > 3:
            print(f"  ... and {len(runners) - 3} more")
        
        print(f"\nUtilities Found: {len(utilities)}")
        for util in utilities[:3]:  # Show first 3
            print(f"  - {util.get('name', 'UNKNOWN')}")
        if len(utilities) > 3:
            print(f"  ... and {len(utilities) - 3} more")
        
        print(f"\nTests Found: {len(tests)}")
        for test in tests[:3]:  # Show first 3
            print(f"  - {test.get('name', 'UNKNOWN')}")
            print(f"    Type: {test.get('type', 'UNKNOWN')}")
        if len(tests) > 3:
            print(f"  ... and {len(tests) - 3} more")
        
        # Print evidence summary
        evidence_summary = result.get("evidence_summary", {})
        print(f"\nEVIDENCE SUMMARY:")
        print(f"  - Files analyzed: {evidence_summary.get('files_analyzed', 0)}")
        print(f"  - Lines analyzed: {evidence_summary.get('lines_analyzed', 0)}")
        print(f"  - Evidence points: {evidence_summary.get('evidence_points', 0)}")
        
        print("\n[SUCCESS] V3 Classification completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Classification failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metaffi_classification_v3())
    sys.exit(0 if success else 1)