"""
Enhanced script to build jni_hello_world and inspect custom targets (UTILITY) from cmake-file-api.
This compares Java JARs (from add_jar and add_custom_target) vs Go shared library.
"""
import json
from pathlib import Path
from deterministic import CMakePlugin
from tests.test_utils import test_repos_root

def inspect_target_json(build_dir: Path, target_name: str) -> dict:
    """
    Read the target JSON file from cmake-file-api for detailed metadata.
    """
    # Find the codemodel JSON index
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"

    # Find the index file
    index_files = list(reply_dir.glob("index-*.json"))
    if not index_files:
        return {}

    with open(index_files[0], 'r') as f:
        index_data = json.load(f)

    # Find the codemodel reference
    codemodel_ref = None
    for reply_obj in index_data.get('reply', {}).values():
        if isinstance(reply_obj, dict) and reply_obj.get('kind') == 'codemodel':
            codemodel_ref = reply_obj.get('jsonFile')
            break

    if not codemodel_ref:
        return {}

    # Read the codemodel
    codemodel_path = reply_dir / codemodel_ref
    with open(codemodel_path, 'r') as f:
        codemodel_data = json.load(f)

    # Find the target in the first configuration
    config = codemodel_data['configurations'][0]
    for target_ref in config.get('targets', []):
        target_json_file = target_ref.get('jsonFile')
        if not target_json_file:
            continue

        target_path = reply_dir / target_json_file
        with open(target_path, 'r') as f:
            target_data = json.load(f)

        if target_data.get('name') == target_name:
            return target_data

    return {}


def print_target_comparison(target_name: str, target_obj, target_json: dict) -> None:
    """
    Print comparison of basic metadata vs full JSON metadata.
    """
    print(f"\n{'='*80}")
    print(f"TARGET: {target_name}")
    print('='*80)

    # Basic metadata
    print("\n--- BASIC METADATA (from cmake-file-api Python object) ---")
    print(f"  TargetType: {target_obj.type}")
    print(f"  nameOnDisk: {target_obj.nameOnDisk}")
    print(f"  artifacts: {len(target_obj.artifacts)}")
    for artifact in target_obj.artifacts:
        print(f"    - {artifact}")

    print(f"  sources: {len(target_obj.sources)}")
    for source in target_obj.sources:
        source_path = Path(source.path) if hasattr(source, 'path') else source
        print(f"    - {source_path.name}")

    print(f"  compileGroups: {len(target_obj.compileGroups)}")
    print(f"  dependencies: {[dep.id for dep in target_obj.dependencies]}")
    print(f"  folder: {target_obj.folder}")

    # Full JSON metadata
    print("\n--- FULL JSON METADATA (from target-*.json file) ---")
    if target_json:
        print(f"  id: {target_json.get('id')}")
        print(f"  name: {target_json.get('name')}")
        print(f"  type: {target_json.get('type')}")
        print(f"  nameOnDisk: {target_json.get('nameOnDisk', 'N/A')}")

        # Backtrace info
        backtrace = target_json.get('backtrace')
        if backtrace is not None:
            print(f"  backtrace: node index {backtrace}")

            # Try to resolve backtrace
            backtrace_graph = target_json.get('backtraceGraph')
            if backtrace_graph:
                nodes = backtrace_graph.get('nodes', [])
                files = backtrace_graph.get('files', [])
                if backtrace < len(nodes):
                    node = nodes[backtrace]
                    file_idx = node.get('file')
                    line = node.get('line')
                    if file_idx is not None and file_idx < len(files):
                        print(f"    -> {files[file_idx]}:{line}")

        # Sources
        sources = target_json.get('sources', [])
        print(f"  sources in JSON: {len(sources)}")
        for src in sources[:5]:  # Show first 5
            print(f"    - {src.get('path', 'N/A')}")
        if len(sources) > 5:
            print(f"    ... and {len(sources) - 5} more")

        # Dependencies
        depends = target_json.get('dependencies', [])
        print(f"  dependencies in JSON: {len(depends)}")
        for dep in depends:
            print(f"    - {dep.get('id')}")

        # Install (if any)
        install = target_json.get('install')
        if install:
            print(f"  install: {install}")

        # Link (if any)
        link = target_json.get('link')
        if link:
            print(f"  link:")
            print(f"    language: {link.get('language')}")
            print(f"    commandFragments: {len(link.get('commandFragments', []))}")
    else:
        print("  (No JSON file found)")

    print()


def main() -> None:
    repo_root = test_repos_root / "jni_hello_world"

    # Build using CMakePlugin
    print("Building jni_hello_world with CMakePlugin...")
    print("(This will configure, build all targets including Go/Java)")
    print()

    cmakeplugin = CMakePlugin(repo_root)
    build_dir = repo_root / "spade_build"

    print("\n" + "="*80)
    print("INSPECTING CUSTOM TARGETS (UTILITY) FROM cmake-file-api")
    print("="*80)

    # Find all three custom targets from the first configuration
    config = cmakeplugin._cmake_code_model.configurations[0]

    targets_to_inspect = {
        "java_hello_lib": None,
        "math_lib": None,
        "hello_go_lib": None
    }

    for cmake_target in config.targets:
        target_data = cmake_target.target
        if target_data.name in targets_to_inspect:
            targets_to_inspect[target_data.name] = target_data

    # Inspect each target
    for target_name, target_obj in targets_to_inspect.items():
        if target_obj:
            # Read the full JSON
            target_json = inspect_target_json(build_dir, target_name)
            print_target_comparison(target_name, target_obj, target_json)
        else:
            print(f"\nWARNING: {target_name} target not found!")

    print("\n" + "="*80)
    print("INSPECTION COMPLETE")
    print("="*80)
    print("\nKEY OBSERVATIONS:")
    print("1. All three targets are TargetType.UTILITY")
    print("2. Look for .jar.rule and .dll.rule patterns in sources")
    print("3. Compare backtrace information (where in CMakeLists.txt)")
    print("4. Check JSON for any additional metadata not in Python object")
    print()


if __name__ == "__main__":
    main()
