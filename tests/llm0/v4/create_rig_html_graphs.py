#!/usr/bin/env python3
"""
Create HTML graphs for all test repositories
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4


async def create_rig_html_for_repository(repo_name: str, repo_path: Path):
    """Create RIG HTML graph for a specific repository."""
    
    logger = logging.getLogger(f"create_rig_html_{repo_name}")
    
    if not repo_path.exists():
        logger.error(f"Repository not found: {repo_path}")
        return False
    
    try:
        logger.info(f"Creating RIG HTML graph for {repo_name}...")
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(repo_path)
        
        # Run the complete 8-phase pipeline
        logger.info(f"Running 8-phase V4 pipeline for {repo_name}...")
        rig = await generator.generate_rig()
        
        logger.info(f"✅ RIG generation completed for {repo_name}!")
        logger.info(f"Components: {len(rig.components) if rig.components else 0}")
        logger.info(f"Relationships: {len(rig.relationships) if rig.relationships else 0}")
        
        # Generate HTML graph
        logger.info(f"Generating HTML graph for {repo_name}...")
        rig.show_graph(validate_before_show=True)
        
        # Get the generated filename
        project_name = rig.repository.name if rig.repository else repo_name
        html_filename = f"rig_{project_name}_graph.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create RIG HTML graph for {repo_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def create_all_rig_html_graphs():
    """Create RIG HTML graphs for all test repositories."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("create_all_rig_html_graphs")
    
    # Define test repositories
    test_repos = {
        "cmake_hello_world": project_root / "tests" / "test_repos" / "cmake_hello_world",
        "jni_hello_world": project_root / "tests" / "test_repos" / "jni_hello_world",
        "MetaFFI": Path("C:/src/github.com/MetaFFI")
    }
    
    results = {}
    
    for repo_name, repo_path in test_repos.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {repo_name}")
        logger.info("="*60)
        
        success = await create_rig_html_for_repository(repo_name, repo_path)
        results[repo_name] = success
        
        if success:
            logger.info(f"✅ {repo_name} completed successfully")
        else:
            logger.error(f"❌ {repo_name} failed")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    for repo_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{repo_name}: {status}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    logger.info(f"\nOverall: {successful}/{total} repositories processed successfully")
    
    if successful > 0:
        logger.info("\nHTML graph files created:")
        for repo_name, success in results.items():
            if success:
                logger.info(f"  - rig_{repo_name}_graph.html")
        
        logger.info("\nTo view the graphs:")
        logger.info("  1. Open the HTML files directly in your browser")
        logger.info("  2. The graphs are interactive and show component relationships")
        logger.info("  3. Each graph is self-contained with no external dependencies")
    
    return successful == total


async def main():
    """Main function."""
    print("Creating RIG HTML graphs for all test repositories...")
    
    success = await create_all_rig_html_graphs()
    
    if success:
        print("\n[OK] All RIG HTML graphs created successfully!")
    else:
        print("\n[WARNING] Some RIG HTML graphs failed to create.")
        print("Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
