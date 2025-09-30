#!/usr/bin/env python3
"""
Test a completely different approach - pre-analyze the repository structure
and give the LLM much more focused information to avoid the "reading all files" problem.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator

def test_simple_approach():
    """Test a completely different approach to avoid the 'reading all files' problem."""
    print("=" * 60)
    print("SIMPLE APPROACH TEST")
    print("=" * 60)
    
    # Use the simple cmake_hello_world project
    test_project = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    
    if not test_project.exists():
        print(f"ERROR: Test project not found at {test_project}")
        return False
    
    print(f"PATH: Using test project at: {test_project}")
    
    try:
        # Create generator with very low request limit to force efficiency
        generator = LLMRIGGenerator(test_project)
        generator.max_requests_per_phase = 5  # Very low limit to force efficiency
        
        print("INIT: Initializing LLM RIG Generator...")
        
        # Test just Phase 1 (Discovery) with minimal requests
        print("RUNNING: Testing Phase 1: Repository Discovery...")
        discovery_result = generator.discover_repository()
        
        if discovery_result.success:
            print("SUCCESS: Phase 1 completed successfully!")
            print(f"TOKENS: Phase 1 Token Usage: {discovery_result.token_usage['total_tokens']} tokens")
            print(f"REQUESTS: Used {generator.current_phase_requests} requests")
            
            # Now let's try a completely different approach for Phase 2
            # Instead of letting the LLM explore, let's pre-analyze the structure
            print("\nRUNNING: Testing Pre-Analysis Approach...")
            
            # Pre-analyze the repository structure
            cmake_file = test_project / "CMakeLists.txt"
            if cmake_file.exists():
                with open(cmake_file, 'r') as f:
                    cmake_content = f.read()
                
                print("PRE-ANALYSIS: Found CMakeLists.txt")
                print(f"PRE-ANALYSIS: Content length: {len(cmake_content)} characters")
                
                # Extract key information from CMakeLists.txt
                lines = cmake_content.split('\n')
                executables = []
                libraries = []
                tests = []
                
                for i, line in enumerate(lines):
                    if 'add_executable(' in line:
                        # Extract executable name
                        parts = line.split('(')
                        if len(parts) > 1:
                            name = parts[1].split()[0]
                            executables.append(name)
                    elif 'add_library(' in line:
                        # Extract library name
                        parts = line.split('(')
                        if len(parts) > 1:
                            name = parts[1].split()[0]
                            libraries.append(name)
                    elif 'add_test(' in line:
                        # Extract test name
                        parts = line.split('(')
                        if len(parts) > 1:
                            name = parts[1].split()[0]
                            tests.append(name)
                
                print(f"PRE-ANALYSIS: Found executables: {executables}")
                print(f"PRE-ANALYSIS: Found libraries: {libraries}")
                print(f"PRE-ANALYSIS: Found tests: {tests}")
                
                # Now we can give the LLM much more focused information
                # instead of letting it explore the entire repository
                print("SUCCESS: Pre-analysis approach could work!")
                return True
            else:
                print("ERROR: CMakeLists.txt not found")
                return False
        else:
            print(f"ERROR: Phase 1 failed: {discovery_result.errors}")
            return False
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_simple_approach()
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Simple approach test PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ERROR: Simple approach test FAILED!")
        print("=" * 60)
        sys.exit(1)
