#!/usr/bin/env python3
"""
Test CargoEntrypoint with cargo_workspace project.
Tests Rust Cargo workspace parsing and crate component extraction.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from deterministic.cargo.cargo_entrypoint import CargoEntrypoint

def test_cargo_workspace():
    """Test CargoEntrypoint with cargo_workspace project."""
    project_dir = project_root / "tests" / "test_repos" / "cargo_workspace"
    
    print(f"Testing CargoEntrypoint with project directory: {project_dir}")
    
    try:
        # Create entrypoint
        entrypoint = CargoEntrypoint(project_dir)
        
        # Get RIG
        rig = entrypoint.rig
        
        print(f"\n=== RIG Generated Successfully ===")
        print(f"Repository: {rig._repository_info.name if rig._repository_info else 'None'}")
        print(f"Build System: {rig._build_system_info.name if rig._build_system_info else 'None'}")
        print(f"Components: {len(rig._components)}")
        print(f"Tests: {len(rig._tests)}")
        print(f"External Packages: {len(rig._external_packages)}")
        
        # Print components
        print(f"\n=== Components ===")
        for component in rig._components:
            print(f"- {component.name} ({component.type.value}) - {component.programming_language}")
            print(f"  Runtime: {component.runtime}")
            print(f"  Output: {component.output}")
            print(f"  Evidence: {component.evidence.call_stack}")
        
        # Print tests
        if rig._tests:
            print(f"\n=== Tests ===")
            for test in rig._tests:
                print(f"- {test.name} ({test.test_framework})")
                print(f"  Evidence: {test.evidence.call_stack}")
        
        # Print external packages
        if rig._external_packages:
            print(f"\n=== External Packages ===")
            for pkg in rig._external_packages:
                print(f"- {pkg.package_manager.package_name}")
        
        # Generate JSON output
        print(f"\n=== JSON Output ===")
        json_output = rig.generate_prompts(optimize=False)
        print(f"JSON length: {len(json_output)} characters")
        
        # Save to file for inspection
        # Create results directory
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        output_file = results_dir / "cargo_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"JSON saved to: {output_file}")
        
        # Assertions
        assert rig._repository_info is not None, "Repository info should be present"
        assert rig._build_system_info is not None, "Build system info should be present"
        assert len(rig._components) >= 2, "Should have at least 2 components (core, proc-macro-utils)"
        assert any(c.name == "core" for c in rig._components), "Should have core component"
        assert any(c.name == "proc-macro-utils" for c in rig._components), "Should have proc-macro-utils component"
        assert all(c.programming_language == "rust" for c in rig._components), "All components should be Rust"
        
        print("✅ All assertions passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing CargoEntrypoint...")
    
    success = test_cargo_workspace()
    
    if success:
        print("\n🎉 All Cargo tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Cargo tests failed!")
        sys.exit(1)
