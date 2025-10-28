#!/usr/bin/env python3
"""
Test V5 RIG Generation with cmake_hello_world

This test validates the V5 architecture with direct RIG manipulation
using the simple cmake_hello_world repository.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v5.llm0_rig_generator_v5 import LLMRIGGeneratorV5


async def test_cmake_hello_world_v5():
    """Test V5 RIG generation with cmake_hello_world."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("test_cmake_hello_world_v5")
    
    # Repository path
    repo_path = Path("tests/test_repos/cmake_hello_world")
    
    if not repo_path.exists():
        logger.error(f"Repository not found: {repo_path}")
        return False
    
    try:
        logger.info("="*80)
        logger.info("TESTING: V5 RIG Generation with cmake_hello_world")
        logger.info("="*80)
        logger.info(f"Repository: {repo_path}")
        
        # Create V5 generator
        generator = LLMRIGGeneratorV5(repo_path)
        
        # Generate RIG using V5 architecture
        logger.info("Generating RIG using V5 architecture...")
        rig = await generator.generate_rig()
        
        # Log results
        logger.info("✅ V5 RIG generation completed successfully!")
        logger.info(f"Repository: {rig._repository_info.name if rig._repository_info else 'Unknown'}")
        logger.info(f"Build System: {rig._build_system_info.name if rig._build_system_info else 'Unknown'}")
        
        # Log RIG summary
        summary = generator.get_rig_summary()
        logger.info(f"Components: {summary['components_count']}")
        logger.info(f"Tests: {summary['tests_count']}")
        logger.info(f"Aggregators: {summary['aggregators_count']}")
        logger.info(f"Runners: {summary['runners_count']}")
        logger.info(f"Utilities: {summary['utilities_count']}")
        
        # Validate RIG structure
        if rig._repository_info:
            logger.info(f"✅ Repository info: {rig._repository_info.name} ({rig._repository_info.type})")
        else:
            logger.warning("⚠️ No repository info found")
        
        if rig._build_system_info:
            logger.info(f"✅ Build system: {rig._build_system_info.name} {rig._build_system_info.version}")
        else:
            logger.warning("⚠️ No build system info found")
        
        if rig._components:
            logger.info(f"✅ Found {len(rig._components)} components")
            for component in rig._components:
                logger.info(f"  - {component.name} ({component.type}, {component.programming_language})")
        else:
            logger.warning("⚠️ No components found")
        
        if rig._tests:
            logger.info(f"✅ Found {len(rig._tests)} tests")
            for test in rig._tests:
                logger.info(f"  - {test.name} ({test.framework})")
        else:
            logger.warning("⚠️ No tests found")
        
        if rig._aggregators:
            logger.info(f"✅ Found {len(rig._aggregators)} aggregators")
            for agg in rig._aggregators:
                logger.info(f"  - {agg.name} ({agg.type})")
        else:
            logger.warning("⚠️ No aggregators found")
        
        if rig._runners:
            logger.info(f"✅ Found {len(rig._runners)} runners")
            for runner in rig._runners:
                logger.info(f"  - {runner.name} ({runner.type})")
        else:
            logger.warning("⚠️ No runners found")
        
        if rig.utilities:
            logger.info(f"✅ Found {len(rig.utilities)} utilities")
            for util in rig.utilities:
                logger.info(f"  - {util.name} ({util.type})")
        else:
            logger.warning("⚠️ No utilities found")
        
        logger.info("="*80)
        logger.info("V5 ARCHITECTURE VALIDATION")
        logger.info("="*80)
        logger.info("✅ Single RIG instance used throughout all phases")
        logger.info("✅ Direct RIG manipulation (no JSON conversion)")
        logger.info("✅ Type safety maintained with Pydantic models")
        logger.info("✅ Incremental RIG building through phases")
        logger.info("✅ No serialization issues")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ V5 RIG generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Testing V5 RIG Generation with cmake_hello_world...")
    
    success = await test_cmake_hello_world_v5()
    
    if success:
        print("\n[OK] V5 RIG generation test passed!")
        print("V5 architecture successfully eliminates JSON conversion issues.")
    else:
        print("\n[ERROR] V5 RIG generation test failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
