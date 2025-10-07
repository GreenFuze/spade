"""
Smart V6 Complete Pipeline Test

Tests the complete Smart V6 pipeline with adaptive phase selection and optimized prompts.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v6.llm0_rig_generator_v6_smart import LLMRIGGeneratorV6Smart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_smart_v6_complete():
    """Test complete Smart V6 pipeline with adaptive phase selection."""
    
    # Test repositories
    test_repos = [
        "tests/test_repos/cmake_hello_world",
        "tests/test_repos/jni_hello_world", 
        "C:/src/github.com/MetaFFI"
    ]
    
    model_settings = {
        "temperature": 0,
        "max_tool_calls": 200,
        "request_limit": 500
    }
    
    for repo_path in test_repos:
        repo_path = Path(repo_path)
        if not repo_path.exists():
            logger.warning(f"Repository not found: {repo_path}")
            continue
            
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing Smart V6 with: {repo_path}")
        logger.info(f"{'='*60}")
        
        try:
            # Create Smart V6 generator
            generator = LLMRIGGeneratorV6Smart(repo_path, model_settings)
            
            # Generate RIG with smart adaptation
            logger.info("Starting Smart V6 RIG generation...")
            phase_results = await generator.generate_rig()
            
            # Log results
            logger.info(f"Smart V6 completed successfully!")
            logger.info(f"Executed phases: {generator.executed_phases}")
            logger.info(f"Total phases: {len(phase_results)}")
            
            # Log phase summaries
            for i, result in enumerate(phase_results):
                logger.info(f"Phase {i+1} result: {result.to_dict()}")
            
            # Test smart adaptation
            if repo_path.name == "cmake_hello_world":
                expected_phases = ["phase1_repository_overview"]
                if generator.executed_phases == expected_phases:
                    logger.info("✅ Smart adaptation working: Skipped unnecessary phases for simple repo")
                else:
                    logger.warning(f"⚠️ Smart adaptation issue: Expected {expected_phases}, got {generator.executed_phases}")
            
            logger.info(f"✅ Smart V6 test passed for {repo_path}")
            
        except Exception as e:
            logger.error(f"❌ Smart V6 test failed for {repo_path}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(test_smart_v6_complete())
