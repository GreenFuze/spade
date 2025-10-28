#!/usr/bin/env python3
"""
Test the complete V3 pipeline on MetaFFI repository.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v3.llm0_rig_generator_v3 import DiscoveryAgent, ClassificationAgent, RelationshipsAgent, AssemblyAgent


async def test_metaffi_complete_v3():
    """Test the complete V3 pipeline on MetaFFI repository."""
    
    print("=" * 80)
    print("TESTING COMPLETE V3 PIPELINE - MetaFFI")
    print("=" * 80)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"Testing complete V3 pipeline at: {test_path}")
    
    try:
        # Phase 1: Discovery
        print("\n" + "=" * 60)
        print("PHASE 1: DISCOVERY")
        print("=" * 60)
        
        discovery_agent = DiscoveryAgent(
            repository_path=test_path,
            max_requests=200,
            max_retries=3
        )
        
        print("Starting discovery phase...")
        discovery_results = await discovery_agent.discover_repository()
        
        print(f"Discovery completed:")
        print(f"  - Build systems: {len(discovery_results.get('repository_info', {}).get('build_systems', []))}")
        print(f"  - Source directories: {len(discovery_results.get('repository_info', {}).get('source_directories', []))}")
        print(f"  - Test directories: {len(discovery_results.get('repository_info', {}).get('test_directories', []))}")
        print(f"  - Test frameworks: {len(discovery_results.get('evidence_catalog', {}).get('test_frameworks', []))}")
        
        # Phase 2: Classification
        print("\n" + "=" * 60)
        print("PHASE 2: CLASSIFICATION")
        print("=" * 60)
        
        classification_agent = ClassificationAgent(
            repository_path=test_path,
            max_requests=200,
            max_retries=3
        )
        
        print("Starting classification phase...")
        classification_results = await classification_agent.classify_components(discovery_results)
        
        print(f"Classification completed:")
        print(f"  - Components: {len(classification_results.get('components', []))}")
        print(f"  - Relationships: {len(classification_results.get('relationships', []))}")
        
        # Phase 3: Relationships
        print("\n" + "=" * 60)
        print("PHASE 3: RELATIONSHIPS")
        print("=" * 60)
        
        relationships_agent = RelationshipsAgent(
            repository_path=test_path,
            max_requests=200
        )
        
        print("Starting relationships phase...")
        relationships_results = await relationships_agent.map_relationships(discovery_results, classification_results)
        
        print(f"Relationships completed:")
        print(f"  - Relationships: {len(relationships_results.get('relationships', []))}")
        print(f"  - Dependencies: {len(relationships_results.get('dependencies', []))}")
        print(f"  - Aggregations: {len(relationships_results.get('aggregations', []))}")
        
        # Phase 4: Assembly
        print("\n" + "=" * 60)
        print("PHASE 4: ASSEMBLY")
        print("=" * 60)
        
        assembly_agent = AssemblyAgent(
            repository_path=test_path,
            max_requests=200
        )
        
        print("Starting assembly phase...")
        rig = await assembly_agent.assemble_rig(discovery_results, classification_results, relationships_results)
        
        print(f"Assembly completed:")
        print(f"  - RIG Components: {len(rig._components)}")
        print(f"  - RIG Aggregators: {len(rig._aggregators)}")
        print(f"  - RIG Runners: {len(rig._runners)}")
        print(f"  - RIG Utilities: {len(rig.utilities)}")
        print(f"  - RIG Tests: {len(rig._tests)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("V3 PIPELINE COMPLETE - SUMMARY")
        print("=" * 80)
        
        print(f"[OK] Phase 1 (Discovery): SUCCESS")
        print(f"   - Build system detected: {discovery_results.get('repository_info', {}).get('build_systems', [{}])[0].get('type', 'UNKNOWN')}")
        print(f"   - Source directories found: {len(discovery_results.get('repository_info', {}).get('source_directories', []))}")
        
        print(f"[OK] Phase 2 (Classification): SUCCESS")
        print(f"   - Components classified: {len(classification_results.get('components', []))}")
        print(f"   - Relationships mapped: {len(classification_results.get('relationships', []))}")
        
        print(f"[OK] Phase 3 (Relationships): SUCCESS")
        print(f"   - Relationships found: {len(relationships_results.get('relationships', []))}")
        print(f"   - Dependencies mapped: {len(relationships_results.get('dependencies', []))}")
        
        print(f"[OK] Phase 4 (Assembly): SUCCESS")
        print(f"   - Final RIG created with {len(rig._components)} components")
        print(f"   - Repository: {rig._repository_info.name}")
        print(f"   - Build System: {rig._build_system_info.name}")
        
        # Performance metrics
        total_requests = (
            discovery_agent.request_count + 
            classification_agent.request_count + 
            relationships_agent.request_count + 
            assembly_agent.request_count
        )
        
        print(f"\nPERFORMANCE METRICS:")
        print(f"  - Total requests: {total_requests}")
        print(f"  - Discovery requests: {discovery_agent.request_count}")
        print(f"  - Classification requests: {classification_agent.request_count}")
        print(f"  - Relationships requests: {relationships_agent.request_count}")
        print(f"  - Assembly requests: {assembly_agent.request_count}")
        
        print(f"\n[SUCCESS] Complete V3 pipeline completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] V3 pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metaffi_complete_v3())
    sys.exit(0 if success else 1)
