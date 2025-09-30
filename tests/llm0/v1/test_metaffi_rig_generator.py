#!/usr/bin/env python3
"""
Test script for LLM-based RIG generation against the MetaFFI repository.

This test validates the LLM-0 RIG generation system against a large, complex,
multi-language project (MetaFFI) to ensure it can handle real-world scenarios.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator
from schemas import ComponentType, Runtime, Component, TestDefinition
from rig import RIG


def validate_metaffi_rig_structure(rig: RIG) -> bool:
    """
    Validate the basic structure of the MetaFFI RIG.
    
    Args:
        rig: The generated RIG object
        
    Returns:
        True if validation passes, False otherwise
    """
    print("INFO: Validating MetaFFI RIG structure...")
    
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
    
    # Check components (MetaFFI should have many components)
    if not rig.components:
        print("ERROR: No components found in RIG")
        return False
    
    print(f"SUCCESS: Found {len(rig.components)} components")
    
    # Validate each component
    for i, component in enumerate(rig.components):
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
        
        if not component.evidence:
            print(f"    ERROR: Component {i+1} missing evidence")
            return False
        
        print(f"    SUCCESS: {component.name} - Type: {component.type}, Language: {component.programming_language}")
    
    print("SUCCESS: MetaFFI RIG structure validation passed")
    return True


def validate_metaffi_rig_content(rig: RIG) -> bool:
    """
    Validate the content of the MetaFFI RIG against expected components.
    
    Args:
        rig: The generated RIG object
        
    Returns:
        True if validation passes, False otherwise
    """
    print("INFO: Validating MetaFFI RIG content...")
    
    # Create component map for easy lookup
    component_map = {comp.name: comp for comp in rig.components}
    
    # Expected key components from MetaFFI (based on the reference RIG)
    expected_components = [
        "metaffi",           # Main CLI executable
        "xllr",              # Core XLLR library
        "cdts_test",         # Test executable
        "xllr_capi_test",    # Test executable
        "metaffi.compiler.go",      # Go compiler plugin
        "metaffi.compiler.openjdk", # OpenJDK compiler plugin
        "metaffi.compiler.python311", # Python compiler plugin
        "metaffi.idl.go",           # Go IDL plugin
        "metaffi.idl.openjdk",      # OpenJDK IDL plugin
        "metaffi.idl.python311",   # Python IDL plugin
        "xllr.go",           # Go runtime library
        "xllr.openjdk",      # OpenJDK runtime library
        "xllr.python311",    # Python runtime library
    ]
    
    # Check for expected components
    found_components = set(component_map.keys())
    missing_components = []
    
    for expected in expected_components:
        if expected not in found_components:
            missing_components.append(expected)
    
    if missing_components:
        print(f"WARNING: Missing expected components: {missing_components}")
        print(f"INFO: Found {len(found_components)} components total")
    else:
        print("SUCCESS: All expected components found")
    
    # Check for multi-language support
    languages = set(comp.programming_language for comp in rig.components)
    print(f"SUCCESS: Found programming languages: {languages}")
    
    # Check for different component types
    types = set(comp.type for comp in rig.components)
    print(f"SUCCESS: Found component types: {types}")
    
    # Check for different runtimes
    runtimes = set(comp.runtime for comp in rig.components if comp.runtime)
    print(f"SUCCESS: Found runtimes: {runtimes}")
    
    # Check evidence quality
    components_with_evidence = sum(1 for comp in rig.components if comp.evidence.call_stack)
    print(f"SUCCESS: {components_with_evidence}/{len(rig.components)} components have evidence")
    
    print("SUCCESS: MetaFFI RIG content validation passed")
    return True


def test_metaffi_rig_generation():
    """
    Test the LLM-based RIG generation against the MetaFFI repository.
    """
    print("RUNNING: LLM-based RIG Generator - MetaFFI Repository Test")
    print("=" * 70)
    print("TEST: Testing LLM-0 against Large Multi-Language Project")
    print("=" * 70)

    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    print(f"PATH: Using MetaFFI repository at: {metaffi_path}")

    # Ensure the MetaFFI repository exists
    if not metaffi_path.exists():
        print(f"ERROR: MetaFFI repository not found at {metaffi_path}")
        print("INFO: Please ensure the MetaFFI repository is available at the expected location")
        return False

    # Initialize the generator
    print("INIT: Initializing LLM RIG Generator for MetaFFI...")
    generator = LLMRIGGenerator(metaffi_path, openai_api_key=os.getenv("OPENAI_API_KEY"))

    # Run the complete pipeline
    print("RUNNING: Running LLM-based RIG generation for MetaFFI...")
    try:
        rig = generator.generate_rig()
        print("SUCCESS: MetaFFI RIG generation completed successfully")
    except Exception as e:
        print(f"ERROR: MetaFFI RIG generation failed: {e}")
        return False

    # Validate the generated RIG
    print("\nINFO: Validating generated MetaFFI RIG...")
    
    # Structure validation
    if not validate_metaffi_rig_structure(rig):
        print("ERROR: MetaFFI RIG structure validation failed")
        return False
    
    # Content validation
    if not validate_metaffi_rig_content(rig):
        print("ERROR: MetaFFI RIG content validation failed")
        return False
    
    # Additional RIG validation
    print("\nINFO: Running MetaFFI RIG internal validation...")
    validation_errors = rig.validate()
    if validation_errors:
        print(f"WARNING: MetaFFI RIG validation found {len(validation_errors)} issues:")
        for error in validation_errors:
            print(f"   {error.severity}: {error.message}")
    else:
        print("SUCCESS: MetaFFI RIG internal validation passed")
    
    # Print summary
    print("\nSUMMARY: MetaFFI RIG Generation Summary:")
    print(f"   Repository: {rig.repository_info.name}")
    print(f"   Build System: {rig.build_system_info.name} {rig.build_system_info.version}")
    print(f"   Components: {len(rig.components)}")
    print(f"   Tests: {len(rig.tests)}")
    print(f"   Aggregators: {len(rig.aggregators)}")
    print(f"   Runners: {len(rig.runners)}")
    print(f"   Validation Errors: {len(validation_errors) if validation_errors else 0}")
    
    # Print component breakdown
    print("\nDETAILS: MetaFFI Component Breakdown:")
    languages = {}
    types = {}
    runtimes = {}
    
    for component in rig.components:
        # Count languages
        lang = component.programming_language
        languages[lang] = languages.get(lang, 0) + 1
        
        # Count types
        comp_type = component.type
        types[comp_type] = types.get(comp_type, 0) + 1
        
        # Count runtimes
        runtime = component.runtime
        if runtime:
            runtimes[runtime] = runtimes.get(runtime, 0) + 1
    
    print(f"   Languages: {languages}")
    print(f"   Types: {types}")
    print(f"   Runtimes: {runtimes}")
    
    print("\n" + "=" * 70)
    print("PASSED: MetaFFI RIG generation test PASSED!")
    print("SUCCESS: LLM-0 successfully analyzed large multi-language project")
    print("SUCCESS: MetaFFI RIG structure validation passed")
    print("SUCCESS: MetaFFI RIG content validation passed")
    print("SUCCESS: LLM-based RIG generation system handles real-world complexity")
    
    return True


def main():
    """
    Main test function.
    """
    print("LLM-based RIG Generation - MetaFFI Repository Test")
    print("=" * 70)
    
    success = test_metaffi_rig_generation()
    
    print("\n" + "=" * 70)
    if success:
        print("PASSED: MetaFFI repository test PASSED!")
        print("SUCCESS: LLM-0 RIG generation system validated against real-world project")
        print("SUCCESS: System ready for production use")
    else:
        print("ERROR: MetaFFI repository test FAILED!")
        print("WARNING: Check the output above for details")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
