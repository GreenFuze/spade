#!/usr/bin/env python3
"""
Test V4 implementation with MetaFFI repository
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


async def test_v4_rig_generation_metaffi():
    """Test V4 RIG generation with MetaFFI project."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_v4_metaffi")
    
    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    
    if not metaffi_path.exists():
        logger.error(f"MetaFFI repository not found: {metaffi_path}")
        return False
    
    try:
        # Create V4 generator
        generator = LLMRIGGeneratorV4(metaffi_path)
        
        # Generate RIG
        logger.info("Starting V4 RIG generation for MetaFFI project...")
        rig = await generator.generate_rig()
        
        # Validate RIG
        if not isinstance(rig, RIG):
            logger.error("Generated object is not a RIG instance")
            return False
        
        logger.info(f"SUCCESS: Generated RIG with repository: {rig._repository_info.name}")
        logger.info(f"Build system: {rig._build_system_info.name}")
        
        # Print some details about discovered components
        if hasattr(rig, 'components') and rig._components:
            logger.info(f"Discovered {len(rig._components)} components:")
            for component in rig._components[:10]:  # Show first 10 components
                logger.info(f"  - {component.name} ({component.type})")
            if len(rig._components) > 10:
                logger.info(f"  ... and {len(rig._components) - 10} more components")
        
        return True
        
    except Exception as e:
        logger.error(f"V4 RIG generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v4_rig_generation_metaffi())
    if success:
        print("[OK] V4 RIG generation test with MetaFFI project passed")
    else:
        print("[ERROR] V4 RIG generation test with MetaFFI project failed")
        sys.exit(1)
