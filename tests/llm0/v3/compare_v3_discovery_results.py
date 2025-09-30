#!/usr/bin/env python3
"""
Compare V3 Discovery results with MetaFFI ground truth.
"""

import json
from pathlib import Path

def load_ground_truth():
    """Load the MetaFFI ground truth JSON."""
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    gt_path = project_root / "metaffi_architecture_manual.json"
    with open(gt_path, 'r') as f:
        return json.load(f)

def analyze_v3_results():
    """Analyze the V3 discovery results."""
    # This is the actual output from our V3 discovery test
    v3_results = {
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
    return v3_results

def compare_results():
    """Compare V3 results with ground truth."""
    print("=" * 80)
    print("V3 DISCOVERY RESULTS vs GROUND TRUTH COMPARISON")
    print("=" * 80)
    
    gt = load_ground_truth()
    v3 = analyze_v3_results()
    
    # Compare build system
    print("\n1. BUILD SYSTEM COMPARISON:")
    print("-" * 40)
    
    gt_build = gt["repository"]["build_system"]
    v3_build = v3["repository_info"]["build_systems"][0]
    
    print(f"Ground Truth: {gt_build['type']} {gt_build['version']}")
    print(f"V3 Result:    {v3_build['type']} {v3_build['version']}")
    print(f"Match: {'[OK] YES' if gt_build['type'] == v3_build['type'] else '[ERROR] NO'}")
    
    # Compare test framework
    print(f"\nGround Truth Test Framework: {gt_build['test_framework']}")
    print(f"V3 Test Framework: {v3['evidence_catalog']['test_frameworks'][0]['type']}")
    print(f"Match: {'[OK] YES' if gt_build['test_framework'] == v3['evidence_catalog']['test_frameworks'][0]['type'] else '[ERROR] NO'}")
    
    # Compare source directories
    print("\n2. SOURCE DIRECTORIES COMPARISON:")
    print("-" * 40)
    
    # Extract expected directories from ground truth
    expected_dirs = set()
    for component_name, component_data in gt["components"].items():
        if "location" in component_data:
            location = component_data["location"]
            if "/" in location:
                # Extract the directory part
                dir_path = location.split("/")[0]
                expected_dirs.add(f"C:\\src\\github.com\\MetaFFI\\{dir_path}")
    
    # Add the main aggregator sub-aggregators
    main_agg = gt["aggregators"]["main_aggregator"]
    for sub_agg in main_agg["sub_aggregators"]:
        expected_dirs.add(f"C:\\src\\github.com\\MetaFFI\\{sub_agg}")
    
    v3_dirs = set(v3["repository_info"]["source_directories"])
    
    print(f"Expected directories: {len(expected_dirs)}")
    for dir_path in sorted(expected_dirs):
        print(f"  - {dir_path}")
    
    print(f"\nV3 discovered directories: {len(v3_dirs)}")
    for dir_path in sorted(v3_dirs):
        print(f"  - {dir_path}")
    
    # Calculate precision and recall
    true_positives = expected_dirs.intersection(v3_dirs)
    false_positives = v3_dirs - expected_dirs
    false_negatives = expected_dirs - v3_dirs
    
    precision = len(true_positives) / len(v3_dirs) if v3_dirs else 0
    recall = len(true_positives) / len(expected_dirs) if expected_dirs else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nPrecision: {precision:.2%} ({len(true_positives)}/{len(v3_dirs)})")
    print(f"Recall: {recall:.2%} ({len(true_positives)}/{len(expected_dirs)})")
    print(f"F1 Score: {f1_score:.2%}")
    
    if false_positives:
        print(f"\nFalse Positives ({len(false_positives)}):")
        for fp in sorted(false_positives):
            print(f"  - {fp}")
    
    if false_negatives:
        print(f"\nFalse Negatives ({len(false_negatives)}):")
        for fn in sorted(false_negatives):
            print(f"  - {fn}")
    
    # Overall assessment
    print("\n3. OVERALL ASSESSMENT:")
    print("-" * 40)
    
    build_system_correct = gt_build['type'] == v3_build['type']
    test_framework_correct = gt_build['test_framework'] == v3['evidence_catalog']['test_frameworks'][0]['type']
    directory_accuracy = f1_score
    
    print(f"Build System Detection: {'[OK] CORRECT' if build_system_correct else '[ERROR] INCORRECT'}")
    print(f"Test Framework Detection: {'[OK] CORRECT' if test_framework_correct else '[ERROR] INCORRECT'}")
    print(f"Directory Discovery: {directory_accuracy:.1%} accuracy")
    
    overall_score = (build_system_correct + test_framework_correct + directory_accuracy) / 3
    print(f"\nOverall V3 Discovery Score: {overall_score:.1%}")
    
    if overall_score >= 0.8:
        print("[SUCCESS] EXCELLENT: V3 Discovery is highly accurate!")
    elif overall_score >= 0.6:
        print("[OK] GOOD: V3 Discovery is reasonably accurate")
    else:
        print("[WARNING] NEEDS IMPROVEMENT: V3 Discovery needs refinement")

if __name__ == "__main__":
    compare_results()
