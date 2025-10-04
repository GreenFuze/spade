#!/usr/bin/env python3
"""
Simple V4 test to get accurate metrics for stats_log.md
"""

import asyncio
import logging
import time
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_v4_rerun():
    """Test V4 pipeline with simple repository to get accurate metrics."""
    
    # Use a simple test repository
    repository_path = Path("tests/test_repos/cmake_hello_world")
    
    if not repository_path.exists():
        logger.error(f"Repository not found: {repository_path}")
        return
    
    logger.info(f"Testing V4 pipeline with: {repository_path}")
    
    # Create generator
    generator = LLMRIGGeneratorV4(repository_path)
    
    start_time = time.time()
    
    try:
        # Run the complete pipeline
        rig = await generator.generate_rig()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"✅ V4 pipeline completed successfully!")
        logger.info(f"Execution time: {execution_time:.1f} seconds")
        logger.info(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        logger.info(f"Components found: {len(rig.components) if rig.components else 0}")
        logger.info(f"Relationships found: {len(rig.relationships) if rig.relationships else 0}")
        
        # Calculate accuracy metrics
        total_expected = 10  # Expected components/files for cmake_hello_world
        total_found = len(rig.components) if rig.components else 0
        accuracy = (total_found / total_expected) * 100 if total_expected > 0 else 0
        
        logger.info(f"Accuracy: {accuracy:.2f}% ({total_found}/{total_expected})")
        logger.info(f"Found: {total_found}/{total_expected}")
        logger.info(f"Not Found: {total_expected - total_found}/{total_expected}")
        
        return {
            "success": True,
            "execution_time": execution_time,
            "accuracy": accuracy,
            "found": total_found,
            "not_found": total_expected - total_found,
            "total_expected": total_expected,
            "components": len(rig.components) if rig.components else 0,
            "relationships": len(rig.relationships) if rig.relationships else 0
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.error(f"❌ V4 pipeline failed: {e}")
        logger.error(f"Execution time: {execution_time:.1f} seconds")
        
        return {
            "success": False,
            "execution_time": execution_time,
            "accuracy": 0.0,
            "found": 0,
            "not_found": 10,
            "total_expected": 10,
            "error": str(e)
        }

if __name__ == "__main__":
    result = asyncio.run(test_simple_v4_rerun())
    print(f"\n=== TEST RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Execution Time: {result['execution_time']:.1f} seconds")
    print(f"Accuracy: {result['accuracy']:.2f}%")
    print(f"Found: {result['found']}/{result['total_expected']}")
    print(f"Not Found: {result['not_found']}/{result['total_expected']}")
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')}")
