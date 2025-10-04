#!/usr/bin/env python3
"""
Test Phase 1 within the complete pipeline to isolate the issue
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4


async def test_phase1_in_complete_pipeline():
    """Test Phase 1 within the complete pipeline to isolate the issue."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("test_phase1_in_complete_pipeline")
    
    # MetaFFI repository path
    repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not repo_path.exists():
        logger.error(f"MetaFFI repository not found: {repo_path}")
        return False
    
    try:
        logger.info("="*80)
        logger.info("TESTING: Phase 1 within Complete Pipeline")
        logger.info("="*80)
        logger.info(f"Repository: {repo_path}")
        
        # Create V4 generator (this initializes all agents)
        generator = LLMRIGGeneratorV4(repo_path)
        
        # Test Phase 1 agent directly (same as complete pipeline)
        logger.info("Testing Phase 1 agent directly...")
        repository_overview = await generator.phase1_agent.execute_phase()
        
        logger.info("✅ Phase 1 completed successfully in complete pipeline context!")
        logger.info(f"Repository: {repository_overview.get('repository_overview', {}).get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 1 failed in complete pipeline context: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Testing Phase 1 within complete pipeline context...")
    
    success = await test_phase1_in_complete_pipeline()
    
    if success:
        print("\n[OK] Phase 1 works in complete pipeline context!")
        print("The issue is NOT in Phase 1 itself.")
    else:
        print("\n[ERROR] Phase 1 fails in complete pipeline context.")
        print("The issue IS in Phase 1 when run within the complete pipeline.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
