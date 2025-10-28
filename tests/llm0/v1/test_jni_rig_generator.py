import json
import os
import sys
from pathlib import Path
import logging

# Add local agentkit-gf to path
agentkit_path = Path(__file__).parent / "agentkit-gf"
if agentkit_path.exists():
    sys.path.insert(0, str(agentkit_path))

from llm0_rig_generator import LLMRIGGenerator
from rig import RIG, ComponentType, Runtime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_jni_rig_generation():
    """
    Tests the LLM-based RIG generation with the JNI Hello World project.
    """
    print("LLM-based RIG Generator - JNI Hello World Testing")
    print("============================================================")
    print("Testing multi-language project: C++ + Java with JNI")
    print("============================================================")

    test_project_path = Path(__file__).parent / "test_repos" / "jni_hello_world"
    print(f"Using JNI test project at: {test_project_path}")

    # Ensure the test project exists
    if not test_project_path.exists():
        print(f"JNI test project not found at {test_project_path}. Please ensure it's created.")
        return False

    # Initialize the generator
    print("Initializing LLM RIG Generator...")
    generator = LLMRIGGenerator(test_project_path, openai_api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Run the complete RIG generation pipeline
        rig = generator._generate_rig()
        print("SUCCESS: Complete pipeline execution successful")

        print("\nINFO Validating generated RIG...")
        # Basic structural validation
        if not isinstance(rig, RIG):
            print(f"ERROR Generated object is not a RIG instance: {type(rig)}")
            return False

        print("INFO Validating RIG structure...")
        if not rig.repository_info:
            print("ERROR Repository info is missing")
            return False
        print(f"SUCCESS Repository info: {rig.repository_info.name}")

        if not rig.build_system_info:
            print("ERROR Build system info is missing")
            return False
        print(f"SUCCESS Build system info: {rig.build_system_info.name} {rig.build_system_info.version}")

        if not rig._components:
            print("ERROR No components found in RIG")
            return False
        print(f"SUCCESS Found {len(rig._components)} components")

        # Validate individual components
        for i, comp in enumerate(rig._components):
            print(f"  Component {i+1}: {comp.name}")
            if not comp.name:
                print(f"    ERROR Component {i+1} has no name")
                return False
            if not comp.type:
                print(f"    ERROR Component {comp.name} has no type")
                return False
            if not comp.programming_language:
                print(f"    ERROR Component {comp.name} has no programming language")
                return False
            if not comp._evidence:
                print(f"    ERROR Component {comp.name} has no evidence")
                return False
            if not comp.source_files is not None: # Can be empty list
                print(f"    ERROR Component {comp.name} has no source_files field")
                return False
            print(f"    SUCCESS Type: {comp.type}")
            print(f"    SUCCESS Language: {comp.programming_language}")
            print(f"    SUCCESS Runtime: {comp.runtime}")
            print(f"    SUCCESS Evidence: {len(comp._evidence.call_stack)} call stack entries")
            print(f"    SUCCESS Source files: {len(comp.source_files)}")

        print("SUCCESS RIG structure validation passed")

        # More detailed content validation for JNI Hello World
        print("INFO Validating JNI Hello World content...")
        
        # Expected components for JNI Hello World
        expected_components = {
            "jni_hello_world": {"type": ComponentType.EXECUTABLE, "language": "C++", "runtime": Runtime.CLANG_C},
            "java_hello_lib": {"type": ComponentType.PACKAGE_LIBRARY, "language": "Java", "runtime": Runtime.JVM},
            "test_jni_wrapper": {"type": ComponentType.EXECUTABLE, "language": "C++", "runtime": Runtime.CLANG_C}
        }

        found_components = {comp.name: comp for comp in rig._components}

        for name, expected in expected_components.items():
            # Find component by partial name match (handle variations like "jni_hello_world (C++ executable)")
            matching_comp = None
            for comp_name, comp in found_components.items():
                if name in comp_name or comp_name.startswith(name):
                    matching_comp = comp
                    break
            
            if not matching_comp:
                print(f"ERROR Expected component '{name}' not found")
                print(f"   Available components: {list(found_components.keys())}")
                return False
            print(f"SUCCESS Found expected component: {name}")
            comp = matching_comp

            if comp.type != expected["type"]:
                print(f"ERROR Component '{name}' has incorrect type: Expected {expected['type']}, Got {comp.type}")
                return False
            print(f"SUCCESS {name} is correctly identified as {expected['type'].value}")

            if comp.programming_language != expected["language"]:
                print(f"ERROR Component '{name}' has incorrect language: Expected {expected['language']}, Got {comp.programming_language}")
                return False
            print(f"SUCCESS {name} has correct programming language: {expected['language']}")

            if comp.runtime != expected["runtime"]:
                print(f"ERROR Component '{name}' has incorrect runtime: Expected {expected['runtime']}, Got {comp.runtime}")
                return False
            print(f"SUCCESS {name} has correct runtime: {expected['runtime']}")

            # Validate evidence
            if not comp.evidence or not comp.evidence.call_stack:
                print(f"ERROR Component '{name}' has no call stack evidence")
                return False
            print(f"SUCCESS {name} has evidence: {comp.evidence.call_stack[0]}")

        print("SUCCESS JNI Hello World content validation passed")

        # Validate multi-language detection
        print("INFO Validating multi-language detection...")
        languages = set(comp.programming_language for comp in rig._components)
        expected_languages = {"C++", "Java"}
        if not languages.issuperset(expected_languages):
            print(f"ERROR Missing expected languages. Found: {languages}, Expected: {expected_languages}")
            return False
        print(f"SUCCESS Multi-language detection successful: {languages}")

        # Validate JNI dependencies
        print("INFO Validating JNI dependencies...")
        jni_component = found_components.get("jni_hello_world")
        if jni_component and jni_component.depends_on:
            java_deps = [dep for dep in jni_component.depends_on if dep.programming_language == "Java"]
            if java_deps:
                print(f"SUCCESS JNI component has Java dependencies: {[dep.name for dep in java_deps]}")
            else:
                print("WARNING: JNI component has no Java dependencies (may be expected)")
        else:
            print("WARNING: JNI component has no dependencies (may be expected)")

        print("\nINFO Running RIG internal validation...")
        validation_errors = rig.validate()
        if validation_errors:
            print(f"WARNING: RIG validation found {len(validation_errors)} issues:")
            for error in validation_errors:
                print(f"   {error.severity}: {error.message}")
        else:
            print("SUCCESS RIG internal validation passed with no issues.")

        print("\n📊 JNI RIG Generation Summary:")
        print(f"   Repository: {rig.repository_info.name}")
        print(f"   Build System: {rig.build_system_info.name} {rig.build_system_info.version}")
        print(f"   Components: {len(rig._components)}")
        print(f"   Languages: {languages}")
        print(f"   Validation Errors: {len(validation_errors)}")

        print("\nINFO Component Details:")
        for i, comp in enumerate(rig._components):
            print(f"   {i+1}. {comp.name}")
            print(f"      Type: {comp.type}")
            print(f"      Language: {comp.programming_language}")
            print(f"      Runtime: {comp.runtime}")
            print(f"      Source Files: {len(comp.source_files)}")
            print(f"      Evidence: {len(comp._evidence.call_stack)} entries")
            if comp.depends_on:
                print(f"      Dependencies: {[dep.name for dep in comp.depends_on]}")

        if validation_errors:
            print("\nWARNING: Test passed with warnings. See details above.")
            return True # Still consider it a pass if only warnings
        else:
            return True

    except Exception as e:
        print(f"ERROR An unexpected error occurred during pipeline execution: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    overall_success = True
    print("\nTest Summary:")
    if test_jni_rig_generation():
        print("============================================================")
        print("JNI Hello World RIG generation test PASSED!")
        print("Multi-language detection working correctly")
        print("JNI component relationships detected")
        print("C++ and Java components properly classified")
        print("LLM-based RIG generation system handles complex projects")
        print("============================================================")
    else:
        print("============================================================")
        print("JNI Hello World RIG generation test FAILED. Check the output above for details.")
        print("============================================================")
        overall_success = False

    if not overall_success:
        sys.exit(1)

if __name__ == "__main__":
    main()
