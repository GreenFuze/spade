#!/usr/bin/env python3
"""
Test acceptance criteria for deterministic scoring
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from snapshot import build_snapshot, enrich_markers_and_samples, compute_deterministic_scoring
from workspace import Workspace
from schemas import load_json, DirMeta

def test_acceptance_criteria():
    """Test the exact acceptance criteria from the task."""
    print("Testing scoring acceptance criteria...")
    
    repo_root = Path("fakeapp")
    cfg = Workspace.load_config(repo_root)
    
    # Run the full pipeline
    print("Running full pipeline: snapshot + markers + scoring...")
    build_snapshot(repo_root, cfg)
    enrich_markers_and_samples(repo_root, cfg)
    compute_deterministic_scoring(repo_root, cfg)
    
    # Check that dirmeta files contain deterministic_scoring
    snapshot_dir = repo_root / ".spade" / "snapshot"
    dirmeta_files = list(snapshot_dir.rglob("dirmeta.json"))
    
    valid_count = 0
    for dirmeta_path in dirmeta_files:
        try:
            meta = load_json(dirmeta_path, DirMeta)
            
            # Check that deterministic_scoring exists and has proper structure
            if hasattr(meta, 'deterministic_scoring') and meta.deterministic_scoring is not None:
                if isinstance(meta.deterministic_scoring, dict):
                    valid_count += 1
                    
                    # Check structure of a sample child score
                    for child_name, child_score in list(meta.deterministic_scoring.items())[:1]:
                        print(f"✓ Valid scoring in {meta.path}:")
                        print(f"  {child_name}: score={child_score.score:.3f}")
                        print(f"  reasons: {child_score.reasons}")
                        break
                        
        except Exception as e:
            print(f"✗ Error checking {dirmeta_path}: {e}")
            continue
    
    if valid_count > 0:
        print(f"\n✓ Acceptance criteria met: {valid_count} directories have valid scoring")
        
        # Show sample of the actual JSON structure
        sample_path = repo_root / ".spade" / "snapshot" / "dirmeta.json"
        if sample_path.exists():
            with open(sample_path, 'r') as f:
                data = json.load(f)
                if 'deterministic_scoring' in data and data['deterministic_scoring']:
                    print("\nSample JSON structure:")
                    sample_child = list(data['deterministic_scoring'].keys())[0]
                    print(f"  \"deterministic_scoring\": {{")
                    print(f"    \"{sample_child}\": {{")
                    print(f"      \"score\": {data['deterministic_scoring'][sample_child]['score']},")
                    print(f"      \"reasons\": {data['deterministic_scoring'][sample_child]['reasons']}")
                    print(f"    }}")
                    print(f"  }}")
        
        return True
    else:
        print("✗ No directories have valid scoring structure")
        return False

if __name__ == "__main__":
    test_acceptance_criteria()
