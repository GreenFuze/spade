"""
Complete test script for LLM-based RIG generation system.
Tests the complete four-phase pipeline using generate_rig() method.
"""

import json
import os
import sys
from pathlib import Path
import logging

# Add local agentkit-gf to path
agentkit_path = Path(__file__).parent.parent / "agentkit-gf"
if agentkit_path.exists():
    sys.path.insert(0, str(agentkit_path))

from llm0_rig_generator import LLMRIGGenerator
from rig import RIG
from schemas import Component, ComponentType, Runtime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_rig_structure(rig: RIG) -> bool:
    """
    Validate that the generated RIG has the expected structure and content.
    
    Args:
        rig: The generated RIG object
        
    Returns:
        True if validation passes, False otherwise
    """
    print("Validating RIG structure...")
    
    # Check basic RIG structure
    if not isinstance(rig, RIG):
        print("ERROR: RIG is not a valid RIG object")
        return False
    
    # Check repository info
    if rig.repository_info is None:
        print("ERROR: Repository info is missing")
        return False
    
    print(f"SUCCESS: Repository info: {rig.repository_info.name}")
    
    # Check build system info
    if rig.build_system_info is None:
        print("ERROR: Build system info is missing")
        return False
    
    print(f"SUCCESS: Build system info: {rig.build_system_info.name} {rig.build_system_info.version}")
    
    # Check components
    if not rig._components:
        print("ERROR: No components found in RIG")
        return False
    
    print(f"SUCCESS: Found {len(rig._components)} components")
    
    # Validate each component
    for i, component in enumerate(rig._components):
        print(f"  Component {i+1}: {component.name}")
        
        # Check required fields
        if not component.name:
            print(f"    ERROR: Component {i+1} missing name")
            return False
        
        if not component.type:
            print(f"    ERROR: Component {i+1} missing type")
            return False
        
        if not component.programming_language:
            print(f"    ERROR: Component {i+1} missing programming language")
            return False
        
        if not component._evidence:
            print(f"    ERROR: Component {i+1} missing evidence")
            return False
        
        print(f"    SUCCESS: Type: {component.type}")
        print(f"    SUCCESS: Language: {component.programming_language}")
        print(f"    SUCCESS: Runtime: {component.runtime}")
        print(f"    SUCCESS: Evidence: {len(component._evidence.call_stack)} call stack entries")
        print(f"    SUCCESS: Source files: {len(component.source_files)}")
    
    print("SUCCESS: RIG structure validation passed")
    return True

def validate_rig_content(rig: RIG) -> bool:
    """
    Validate that the RIG contains the expected content for our test repository.
    
    Args:
        rig: The generated RIG object
        
    Returns:
        True if validation passes, False otherwise
    """
    print("INFO: Validating RIG content...")
    
    # Expected components for cmake_hello_world
    expected_components = ["hello_world", "utils", "test_hello_world"]
    found_components = [comp.name for comp in rig._components]
    
    for expected in expected_components:
        if expected not in found_components:
            print(f"ERROR: Expected component '{expected}' not found")
            return False
        print(f"SUCCESS: Found expected component: {expected}")
    
    # Check specific component types
    component_map = {comp.name: comp for comp in rig._components}
    
    # Check hello_world is an executable
    if component_map["hello_world"].type != ComponentType.EXECUTABLE:
        print(f"ERROR: hello_world should be an executable, got {component_map['hello_world'].type}")
        return False
    print("SUCCESS: hello_world is correctly identified as executable")
    
    # Check utils is a library
    if component_map["utils"].type not in [ComponentType.STATIC_LIBRARY, ComponentType.SHARED_LIBRARY]:
        print(f"ERROR: utils should be a library, got {component_map['utils'].type}")
        return False
    print("SUCCESS: utils is correctly identified as library")
    
    # Check test_hello_world is an executable (tests are executables)
    if component_map["test_hello_world"].type != ComponentType.EXECUTABLE:
        print(f"ERROR: test_hello_world should be an executable, got {component_map['test_hello_world'].type}")
        return False
    print("SUCCESS: test_hello_world is correctly identified as executable")
    
    # Check programming languages
    for comp_name, comp in component_map.items():
        if comp_name in ["hello_world", "utils"] and comp.programming_language != "C++":
            print(f"ERROR: {comp_name} should be C++, got {comp.programming_language}")
            return False
        print(f"SUCCESS: {comp_name} has correct programming language: {comp.programming_language}")
    
    # Check evidence quality
    for comp_name, comp in component_map.items():
        if not comp._evidence.call_stack:
            print(f"ERROR: {comp_name} has no evidence")
            return False
        print(f"SUCCESS: {comp_name} has evidence: {comp._evidence.call_stack[0]}")
    
    print("SUCCESS: RIG content validation passed")
    return True

def test_complete_llm_rig_generation():
    """
    Test the complete LLM-based RIG generation pipeline.
    """
    print("RUNNING: LLM-based RIG Generator - Complete Pipeline Test")
    print("============================================================")
    print("TEST: Testing Complete Four-Phase Pipeline")
    print("============================================================")

    test_project_path = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    print(f"PATH: Using test project at: {test_project_path}")

    # Ensure the test project exists
    if not test_project_path.exists():
        print(f"ERROR: Test project not found at {test_project_path}. Please ensure it's created.")
        return False

    # Initialize the generator
    print("INIT: Initializing LLM RIG Generator...")
    generator = LLMRIGGenerator(test_project_path, openai_api_key=os.getenv("OPENAI_API_KEY"))

    # Run the complete pipeline
    print("RUNNING: Running complete LLM-based RIG generation pipeline...")
    try:
        rig = generator._generate_rig()
        print("SUCCESS: Complete pipeline execution successful")
    except Exception as e:
        print(f"ERROR: Pipeline execution failed: {e}")
        return False

    # Validate the generated RIG
    print("\nINFO: Validating generated RIG...")
    
    # Structure validation
    if not validate_rig_structure(rig):
        print("ERROR: RIG structure validation failed")
        return False
    
    # Content validation
    if not validate_rig_content(rig):
        print("ERROR: RIG content validation failed")
        return False
    
    # Additional RIG validation
    print("\nINFO: Running RIG internal validation...")
    validation_errors = rig.validate()
    if validation_errors:
        print(f"WARNING: RIG validation found {len(validation_errors)} issues:")
        for error in validation_errors:
            print(f"   {error.severity}: {error.message}")
    else:
        print("SUCCESS: RIG internal validation passed")
    
    # Print summary
    print("\nSUMMARY: RIG Generation Summary:")
    print(f"   Repository: {rig.repository_info.name}")
    print(f"   Build System: {rig.build_system_info.name} {rig.build_system_info.version}")
    print(f"   Components: {len(rig._components)}")
    print(f"   Validation Errors: {len(validation_errors)}")
    
    # Print component details
    print("\nDETAILS: Component Details:")
    for i, component in enumerate(rig._components, 1):
        print(f"   {i}. {component.name}")
        print(f"      Type: {component.type}")
        print(f"      Language: {component.programming_language}")
        print(f"      Runtime: {component.runtime}")
        print(f"      Source Files: {len(component.source_files)}")
        print(f"      Evidence: {len(component._evidence.call_stack)} entries")
    
    return True

def main():
    """
    Main test function.
    """
    print("LLM-based RIG Generation - Complete Pipeline Test")
    print("=" * 60)
    
    success = test_complete_llm_rig_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("PASSED: Complete pipeline test PASSED!")
        print("SUCCESS: All four phases working correctly")
        print("SUCCESS: RIG structure validation passed")
        print("SUCCESS: RIG content validation passed")
        print("SUCCESS: LLM-based RIG generation system is fully functional")
    else:
        print("ERROR: Complete pipeline test FAILED!")
        print("WARNING: Check the output above for details")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
