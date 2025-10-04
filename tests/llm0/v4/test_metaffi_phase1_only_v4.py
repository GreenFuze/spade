#!/usr/bin/env python3
"""
Test Phase 1 ONLY with MetaFFI to get accurate measurements
"""

import sys
import asyncio
import logging
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase1_repository_overview_agent_v4 import RepositoryOverviewAgentV4


async def test_phase1_only_metaffi():
    """Test Phase 1 ONLY with MetaFFI to get accurate measurements."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_phase1_only_metaffi")
    
    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    
    if not metaffi_path.exists():
        logger.error(f"MetaFFI repository not found: {metaffi_path}")
        return False
    
    try:
        # Phase 1: Repository Overview (MEASURE THIS ONLY)
        logger.info("Running Phase 1 ONLY: Repository Overview...")
        start_time = time.time()
        
        phase1_agent = RepositoryOverviewAgentV4(metaffi_path)
        repository_overview = await phase1_agent.execute_phase()
        
        execution_time = time.time() - start_time
        
        logger.info(f"Phase 1 completed in {execution_time:.1f} seconds")
        logger.info(f"Repository: {repository_overview.get('repository_overview', {}).get('name', 'Unknown')}")
        
        # Save Phase 1 output for Phase 2 input
        with open("phase1_output.json", "w") as f:
            json.dump(repository_overview, f, indent=2)
        
        # Print precise measurements
        print(f"\n=== PHASE 1 PRECISE MEASUREMENTS ===")
        print(f"Execution Time: {execution_time:.1f} seconds")
        print(f"Repository: {repository_overview.get('repository_overview', {}).get('name', 'Unknown')}")
        print(f"Build Systems: {repository_overview.get('repository_overview', {}).get('build_systems', [])}")
        print(f"Source Dirs: {repository_overview.get('repository_overview', {}).get('directory_structure', {}).get('source_dirs', [])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Phase 1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase1_only_metaffi())
    if success:
        print("[OK] Phase 1 ONLY test with MetaFFI passed")
    else:
        print("[ERROR] Phase 1 ONLY test with MetaFFI failed")
        sys.exit(1)
