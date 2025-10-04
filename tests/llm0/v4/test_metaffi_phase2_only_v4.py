#!/usr/bin/env python3
"""
Test Phase 2 ONLY with MetaFFI using Phase 1 output as input
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

from llm0.v4.phase2_source_structure_agent_v4 import SourceStructureDiscoveryAgentV4


async def test_phase2_only_metaffi():
    """Test Phase 2 ONLY with MetaFFI using Phase 1 output as input."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_phase2_only_metaffi")
    
    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    
    if not metaffi_path.exists():
        logger.error(f"MetaFFI repository not found: {metaffi_path}")
        return False
    
    # Load Phase 1 output
    try:
        with open("phase1_output.json", "r") as f:
            repository_overview = json.load(f)
        logger.info("Loaded Phase 1 output as input for Phase 2")
    except FileNotFoundError:
        logger.error("Phase 1 output not found. Run Phase 1 first.")
        return False
    
    try:
        # Phase 2: Source Structure Discovery (MEASURE THIS ONLY)
        logger.info("Running Phase 2 ONLY: Source Structure Discovery...")
        start_time = time.time()
        
        phase2_agent = SourceStructureDiscoveryAgentV4(metaffi_path)
        source_structure = await phase2_agent.execute_phase(repository_overview)
        
        execution_time = time.time() - start_time
        
        logger.info(f"Phase 2 completed in {execution_time:.1f} seconds")
        logger.info(f"Source directories found: {len(source_structure.get('source_structure', {}).get('source_directories', []))}")
        
        # Print precise measurements
        print(f"\n=== PHASE 2 PRECISE MEASUREMENTS ===")
        print(f"Execution Time: {execution_time:.1f} seconds")
        print(f"Source Directories: {len(source_structure.get('source_structure', {}).get('source_directories', []))}")
        
        # Count components and files
        components = 0
        files = 0
        for source_dir in source_structure.get('source_structure', {}).get('source_directories', []):
            components += len(source_dir.get('components', []))
            files += len(source_dir.get('files', []))
        
        print(f"Components: {components}")
        print(f"Files: {files}")
        
        return True
        
    except Exception as e:
        logger.error(f"Phase 2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase2_only_metaffi())
    if success:
        print("[OK] Phase 2 ONLY test with MetaFFI passed")
    else:
        print("[ERROR] Phase 2 ONLY test with MetaFFI failed")
        sys.exit(1)