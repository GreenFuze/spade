#!/usr/bin/env python3
"""
Direct Test V7 Phase 2: Build System Detection on cmake_hello_world repository

This test validates Phase 2 of the V7 Enhanced Architecture by importing files directly.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import files directly to avoid __init__.py issues
sys.path.insert(0, str(project_root / "llm0" / "v7"))

from phase1_repository_overview_agent_v7 import RepositoryOverviewAgentV7
from phase2_build_system_detection_agent_v7 import BuildSystemDetectionAgentV7


async def test_phase2_build_system_detection():
    """Test Phase 2: Build System Detection on cmake_hello_world"""
    
    print("=" * 80)
    print("V7 Phase 2: Build System Detection Test (Direct)")
    print("Repository: cmake_hello_world")
    print("=" * 80)
    
    # Setup
    repository_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not repository_path.exists():
        print(f"❌ Repository not found: {repository_path}")
        return
    
    print(f"📁 Repository: {repository_path}")
    
    # Phase 1: Get language detection results
    print("\n🔄 Running Phase 1: Language Detection...")
    start_time = time.time()
    
    phase1_agent = RepositoryOverviewAgentV7(repository_path)
    phase1_output = await phase1_agent.execute_phase()
    
    phase1_time = time.time() - start_time
    print(f"✅ Phase 1 completed in {phase1_time:.2f} seconds")
    
    # Display Phase 1 results
    print("\n📊 Phase 1 Results:")
    languages_detected = phase1_output.get("languages_detected", {})
    for lang, data in languages_detected.items():
        if data.get("detected", False):
            confidence = data.get("confidence", 0)
            print(f"  - {lang}: {confidence:.1%} confidence")
    
    # Phase 2: Build System Detection
    print("\n🔄 Running Phase 2: Build System Detection...")
    start_time = time.time()
    
    phase2_agent = BuildSystemDetectionAgentV7(repository_path)
    phase2_output = await phase2_agent.execute_phase(phase1_output)
    
    phase2_time = time.time() - start_time
    print(f"✅ Phase 2 completed in {phase2_time:.2f} seconds")
    
    # Display Phase 2 results
    print("\n📊 Phase 2 Results:")
    build_systems = phase2_output.get("build_systems_detected", {})
    for system, data in build_systems.items():
        if data.get("detected", False):
            confidence = data.get("confidence", 0)
            evidence = data.get("evidence", [])
            print(f"  - {system}: {confidence:.1%} confidence")
            print(f"    Evidence: {', '.join(evidence)}")
    
    # Analysis
    print("\n🔍 Analysis:")
    
    # Check if CMake was detected
    cmake_detected = build_systems.get("cmake", {}).get("detected", False)
    if cmake_detected:
        print("✅ CMake build system correctly detected")
    else:
        print("❌ CMake build system NOT detected")
    
    # Check primary build system
    primary_system = phase2_output.get("build_analysis", {}).get("primary_build_system")
    if primary_system == "cmake":
        print("✅ Primary build system correctly identified as CMake")
    else:
        print(f"❌ Primary build system incorrectly identified as: {primary_system}")
    
    # Check language-build mapping
    language_mapping = phase2_output.get("build_analysis", {}).get("language_build_mapping", {})
    if "C++" in language_mapping and language_mapping["C++"] == "cmake":
        print("✅ C++ to CMake mapping correctly established")
    else:
        print("❌ C++ to CMake mapping NOT established")
    
    # Token usage analysis
    print("\n📈 Token Usage Analysis:")
    
    # Count tool calls from agent history
    phase2_history = phase2_agent.agent.history
    tool_calls = 0
    total_tokens = 0
    
    for msg in phase2_history:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            # Count tool calls in the content
            if "detect_build_systems" in msg.content:
                tool_calls += 1
        
        # Try to extract token usage
        if hasattr(msg, 'usage'):
            if hasattr(msg.usage, 'total_tokens'):
                total_tokens += msg.usage.total_tokens
    
    print(f"  - Tool calls: {tool_calls}")
    print(f"  - Total tokens: {total_tokens}")
    print(f"  - Execution time: {phase2_time:.2f} seconds")
    
    # Success criteria
    success = (
        cmake_detected and 
        primary_system == "cmake" and 
        "C++" in language_mapping and 
        language_mapping["C++"] == "cmake"
    )
    
    if success:
        print("\n🎉 Phase 2 Test PASSED!")
        print("✅ All success criteria met")
    else:
        print("\n❌ Phase 2 Test FAILED!")
        print("❌ Some success criteria not met")
    
    # Save results
    results = {
        "test": "V7 Phase 2: Build System Detection (Direct)",
        "repository": "cmake_hello_world",
        "success": success,
        "phase1_time": phase1_time,
        "phase2_time": phase2_time,
        "total_time": phase1_time + phase2_time,
        "tool_calls": tool_calls,
        "total_tokens": total_tokens,
        "phase1_output": phase1_output,
        "phase2_output": phase2_output
    }
    
    results_file = project_root / "tests" / "llm0" / "v7" / "phase2_direct_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return success


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    success = asyncio.run(test_phase2_build_system_detection())
    
    if success:
        print("\n🎯 Ready to test on larger repositories!")
    else:
        print("\n🔧 Need to fix issues before testing on larger repositories")
