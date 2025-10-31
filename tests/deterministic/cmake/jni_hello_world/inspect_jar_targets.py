"""
Script to build jni_hello_world and inspect both JAR targets in cmake-file-api.
This helps us understand how add_jar() vs add_custom_target() appear in the metadata.
"""
from pathlib import Path
from deterministic import CMakePlugin
from tests.test_utils import test_repos_root

def main() -> None:
    repo_root = test_repos_root / "jni_hello_world"

    # Build using CMakePlugin
    print("Building jni_hello_world with CMakePlugin...")
    cmakeplugin = CMakePlugin(repo_root)

    # Access the cmake-file-api targets
    print("\n" + "="*80)
    print("INSPECTING JAR TARGETS FROM cmake-file-api")
    print("="*80)

    # Find both JAR targets from the first configuration
    config = cmakeplugin._cmake_code_model.configurations[0]
    java_hello_lib_target = None
    math_lib_target = None

    for cmake_target in config.targets:
        target_data = cmake_target.target
        if target_data.name == "java_hello_lib":
            java_hello_lib_target = target_data
        elif target_data.name == "math_lib":
            math_lib_target = target_data

    # Inspect java_hello_lib (from add_jar)
    if java_hello_lib_target:
        print("\n" + "-"*80)
        print("TARGET: java_hello_lib (from add_jar)")
        print("-"*80)
        print(f"  TargetType: {java_hello_lib_target.type}")
        print(f"  nameOnDisk: {java_hello_lib_target.nameOnDisk}")
        print(f"  artifacts: {len(java_hello_lib_target.artifacts)}")
        for artifact in java_hello_lib_target.artifacts:
            print(f"    - {artifact}")
        print(f"  sources: {len(java_hello_lib_target.sources)}")
        for source in java_hello_lib_target.sources:
            source_path = Path(source.path) if hasattr(source, 'path') else source
            print(f"    - {source_path}")
        print(f"  compileGroups: {len(java_hello_lib_target.compileGroups)}")
        print(f"  dependencies: {[dep.id for dep in java_hello_lib_target.dependencies]}")
        print(f"  folder: {java_hello_lib_target.folder}")
        if hasattr(java_hello_lib_target, 'backtraceGraph') and java_hello_lib_target.backtraceGraph:
            if java_hello_lib_target.backtraceGraph.files:
                print(f"  backtrace file: {java_hello_lib_target.backtraceGraph.files[0]}")
            if java_hello_lib_target.backtraceGraph.nodes:
                print(f"  backtrace line: {java_hello_lib_target.backtraceGraph.nodes[0].line}")
    else:
        print("\nWARNING: java_hello_lib target not found!")

    # Inspect math_lib (from add_custom_target)
    if math_lib_target:
        print("\n" + "-"*80)
        print("TARGET: math_lib (from add_custom_target)")
        print("-"*80)
        print(f"  TargetType: {math_lib_target.type}")
        print(f"  nameOnDisk: {math_lib_target.nameOnDisk}")
        print(f"  artifacts: {len(math_lib_target.artifacts)}")
        for artifact in math_lib_target.artifacts:
            print(f"    - {artifact}")
        print(f"  sources: {len(math_lib_target.sources)}")
        for source in math_lib_target.sources:
            source_path = Path(source.path) if hasattr(source, 'path') else source
            print(f"    - {source_path}")
        print(f"  compileGroups: {len(math_lib_target.compileGroups)}")
        print(f"  dependencies: {[dep.id for dep in math_lib_target.dependencies]}")
        print(f"  folder: {math_lib_target.folder}")
        if hasattr(math_lib_target, 'backtraceGraph') and math_lib_target.backtraceGraph:
            if math_lib_target.backtraceGraph.files:
                print(f"  backtrace file: {math_lib_target.backtraceGraph.files[0]}")
            if math_lib_target.backtraceGraph.nodes:
                print(f"  backtrace line: {math_lib_target.backtraceGraph.nodes[0].line}")
    else:
        print("\nWARNING: math_lib target not found!")

    print("\n" + "="*80)
    print("INSPECTION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
