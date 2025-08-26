#!/usr/bin/env python3
"""
Integration test for SPADE Phase-0 traversal
Tests complete end-to-end workflow with real fakeapp data
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from phase0 import run_phase0
from dev.dummy_transport import echo_transport_valid_response


def test_phase0_with_real_fakeapp():
    """Test Phase-0 traversal with real fakeapp data."""
    print("Testing Phase-0 traversal with real fakeapp...")
    
    repo_root = Path("fakeapp")
    
    # Check if fakeapp exists and has proper structure
    if not repo_root.exists():
        print("✗ fakeapp directory not found")
        print("  Please ensure fakeapp exists with proper .spade structure")
        return False
    
    # Check for required .spade files
    required_files = [
        repo_root / ".spade" / "run.json",
        repo_root / ".spade" / "snapshot" / "dirmeta.json"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            print(f"✗ Required file missing: {file_path}")
            print("  Please run snapshot generation first")
            return False
    
    print("✓ Found fakeapp with proper .spade structure")
    
    try:
        # Run Phase-0 traversal
        run_phase0(repo_root, echo_transport_valid_response)
        print("✓ Phase-0 traversal completed successfully")
        
        # Check outputs
        analysis_root = repo_root / ".spade" / "analysis"
        if not analysis_root.exists():
            print("✗ Analysis directory not created")
            return False
        
        # Count analysis files
        analysis_files = list(analysis_root.rglob("llm_inferred.json"))
        print(f"✓ Created {len(analysis_files)} analysis files")
        
        # Check telemetry
        telemetry_path = repo_root / ".spade" / "telemetry.jsonl"
        if not telemetry_path.exists():
            print("✗ Telemetry file not created")
            return False
        
        telemetry_lines = telemetry_path.read_text().strip().split("\n")
        print(f"✓ Wrote {len(telemetry_lines)} telemetry lines")
        
        # Check scaffold
        scaffold_path = repo_root / ".spade" / "scaffold"
        if not scaffold_path.exists():
            print("✗ Scaffold directory not created")
            return False
        
        # Check worklist
        worklist_path = repo_root / ".spade" / "worklist.json"
        if not worklist_path.exists():
            print("✗ Worklist file not created")
            return False
        
        # Show some telemetry data
        if telemetry_lines:
            print("\nSample telemetry data:")
            for i, line in enumerate(telemetry_lines[:3]):  # Show first 3 lines
                import json
                data = json.loads(line)
                print(f"  Step {data['step']}: {data['path']} (d={data['depth']}, valid={data['json_valid']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Phase-0 traversal failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration test."""
    print("SPADE Phase-0 Integration Test")
    print("=" * 40)
    
    try:
        success = test_phase0_with_real_fakeapp()
        
        if success:
            print("\n" + "=" * 40)
            print("✓ Integration test passed! Phase-0 traversal works with real data.")
        else:
            print("\n" + "=" * 40)
            print("✗ Integration test failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
