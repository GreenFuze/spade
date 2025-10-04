#!/usr/bin/env python3
"""
Create HTML graph for a simple repository (cmake_hello_world)
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4


async def create_rig_html_simple():
    """Create RIG HTML graph for cmake_hello_world repository."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("create_rig_html_simple")
    
    # Use the simple cmake_hello_world repository
    repo_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not repo_path.exists():
        logger.error(f"Repository not found: {repo_path}")
        return False
    
    try:
        logger.info(f"Creating RIG HTML graph for cmake_hello_world...")
        logger.info(f"Repository path: {repo_path}")
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(repo_path)
        
        # Run the complete 8-phase pipeline
        logger.info("Running 8-phase V4 pipeline...")
        rig = await generator.generate_rig()
        
        logger.info("✅ RIG generation completed!")
        logger.info(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        logger.info(f"Components: {len(rig.components) if rig.components else 0}")
        logger.info(f"Tests: {len(rig.tests) if rig.tests else 0}")
        logger.info(f"Evidence: {len(rig.evidence) if rig.evidence else 0}")
        
        # Generate HTML graph
        logger.info("Generating HTML graph visualization...")
        rig.show_graph(validate_before_show=True)
        
        # Get the generated filename
        project_name = rig.repository.name if rig.repository else "cmake_hello_world"
        html_filename = f"rig_{project_name}_graph.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create RIG HTML graph: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Creating RIG HTML graph for cmake_hello_world...")
    
    success = await create_rig_html_simple()
    
    if success:
        print("\n[OK] RIG HTML graph created successfully!")
        print("Open the HTML file in your browser to view the interactive graph.")
    else:
        print("\n[ERROR] RIG HTML graph creation failed.")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
