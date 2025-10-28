#!/usr/bin/env python3
"""
Basic test for LLM0 V4 implementation
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4
from core.rig import RIG


async def test_v4_rig_generation_cmake_hello_world():
    """Test V4 RIG generation with cmake_hello_world repository."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_v4")
    
    # Test repository path
    test_repo_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not test_repo_path.exists():
        logger.error(f"Test repository not found: {test_repo_path}")
        return False
    
    try:
        # Create V4 generator
        generator = LLMRIGGeneratorV4(test_repo_path)
        
        # Generate RIG
        logger.info("Starting V4 RIG generation...")
        rig = await generator.generate_rig()
        
        # Validate RIG
        if not isinstance(rig, RIG):
            logger.error("Generated object is not a RIG instance")
            return False
        
        logger.info(f"SUCCESS: Generated RIG with repository: {rig._repository_info.name}")
        logger.info(f"Build system: {rig._build_system_info.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"V4 RIG generation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v4_rig_generation_cmake_hello_world())
    if success:
        print("[OK] V4 RIG generation test passed")
    else:
        print("[ERROR] V4 RIG generation test failed")
        sys.exit(1)