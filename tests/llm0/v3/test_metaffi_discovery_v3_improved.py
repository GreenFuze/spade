#!/usr/bin/env python3
"""
Test the improved V3 Discovery agent with retry mechanism and unlimited usage limits.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v3.llm0_rig_generator_v3 import DiscoveryAgent


async def test_metaffi_discovery_v3_improved():
    """Test the improved V3 Discovery agent on MetaFFI repository."""
    
    print("=" * 80)
    print("TESTING IMPROVED V3 DISCOVERY AGENT")
    print("=" * 80)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"Testing MetaFFI discovery with improved V3 agent at: {test_path}")
    print(f"Repository exists: {test_path.exists()}")
    
    # Create discovery agent with retry mechanism
    discovery_agent = DiscoveryAgent(
        repository_path=test_path,
        max_requests=200,  # Higher limit
        max_retries=3       # Allow 3 retries for path issues
    )
    
    print("Discovery agent created with:")
    print(f"  - Max requests: {discovery_agent.max_requests}")
    print(f"  - Max retries: {discovery_agent.max_retries}")
    print(f"  - Usage limit: {discovery_agent.agent._usage_limit}")
    
    print("\nStarting discovery with retry mechanism...")
    
    try:
        result = await discovery_agent.discover_repository()
        
        print("\n" + "=" * 80)
        print("DISCOVERY RESULTS:")
        print("=" * 80)
        
        # Print key results
        repo_info = result.get("repository_info", {})
        build_systems = repo_info.get("build_systems", [])
        
        print(f"Build Systems Found: {len(build_systems)}")
        for bs in build_systems:
            print(f"  - Type: {bs.get('type', 'UNKNOWN')}")
            print(f"    Version: {bs.get('version', 'UNKNOWN')}")
            print(f"    API Available: {bs.get('api_available', False)}")
            print(f"    Evidence: {bs.get('evidence', 'N/A')}")
        
        source_dirs = repo_info.get("source_directories", [])
        test_dirs = repo_info.get("test_directories", [])
        
        print(f"\nSource Directories: {len(source_dirs)}")
        for sd in source_dirs[:5]:  # Show first 5
            print(f"  - {sd}")
        if len(source_dirs) > 5:
            print(f"  ... and {len(source_dirs) - 5} more")
        
        print(f"\nTest Directories: {len(test_dirs)}")
        for td in test_dirs[:5]:  # Show first 5
            print(f"  - {td}")
        if len(test_dirs) > 5:
            print(f"  ... and {len(test_dirs) - 5} more")
        
        # Print evidence catalog
        evidence_catalog = result.get("evidence_catalog", {})
        cmake_api = evidence_catalog.get("cmake_file_api", {})
        test_frameworks = evidence_catalog.get("test_frameworks", [])
        
        print(f"\nCMake File API:")
        print(f"  - Available: {cmake_api.get('available', False)}")
        print(f"  - Index File: {cmake_api.get('index_file', 'UNKNOWN')}")
        
        print(f"\nTest Frameworks: {len(test_frameworks)}")
        for tf in test_frameworks:
            print(f"  - Type: {tf.get('type', 'UNKNOWN')}")
            print(f"    Evidence: {tf.get('evidence', 'N/A')}")
        
        # Print retry statistics
        print(f"\nRETRY STATISTICS:")
        print(f"  - Retry count: {discovery_agent.retry_count}/{discovery_agent.max_retries}")
        print(f"  - Failed paths: {len(discovery_agent.failed_paths)}")
        if discovery_agent.failed_paths:
            print("  - Failed paths:")
            for path in discovery_agent.failed_paths:
                print(f"    - {path}")
        
        print(f"\nREQUEST STATISTICS:")
        print(f"  - Total requests: {discovery_agent.request_count}")
        print(f"  - Found files: {discovery_agent.found_files}")
        print(f"  - Missing files: {discovery_agent.missing_files}")
        
        print("\n[SUCCESS] Improved V3 Discovery completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Discovery failed: {e}")
        print(f"Retry count: {discovery_agent.retry_count}/{discovery_agent.max_retries}")
        print(f"Failed paths: {discovery_agent.failed_paths}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metaffi_discovery_v3_improved())
    sys.exit(0 if success else 1)
