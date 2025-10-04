#!/usr/bin/env python3
"""
Create HTML graph for MetaFFI repository using V4+ Enhanced Phase 8
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4_enhanced import LLMRIGGeneratorV4Enhanced


async def create_metaffi_rig_html_v4_enhanced():
    """Create RIG HTML graph for MetaFFI repository using V4+ Enhanced Phase 8."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("create_metaffi_rig_html_v4_enhanced")
    
    # Use the MetaFFI repository
    repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not repo_path.exists():
        logger.error(f"Repository not found: {repo_path}")
        return False
    
    try:
        logger.info(f"Creating RIG HTML graph for MetaFFI using V4+ Enhanced Phase 8...")
        logger.info(f"Repository path: {repo_path}")
        
        # Create V4+ Enhanced generator (model settings are hardcoded in V4 agents)
        generator = LLMRIGGeneratorV4Enhanced(repo_path)
        
        # Run the complete 8-phase pipeline with V4+ enhancement
        logger.info("Running 8-phase V4+ Enhanced pipeline...")
        logger.info("Phases 1-7: V4 JSON-based (unchanged)")
        logger.info("Phase 8: Enhanced RIG manipulation with direct object manipulation")
        
        rig = await generator.generate_rig()
        
        logger.info("✅ V4+ Enhanced RIG generation completed!")
        logger.info(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        logger.info(f"Components: {len(rig.components) if rig.components else 0}")
        logger.info(f"Tests: {len(rig.tests) if rig.tests else 0}")
        logger.info(f"Evidence: {len(rig.evidence) if rig.evidence else 0}")
        
        # Get RIG summary
        summary = generator.get_rig_summary()
        logger.info(f"RIG Summary: {summary}")
        
        # Generate HTML graph
        logger.info("Generating HTML graph visualization...")
        rig.show_graph(validate_before_show=True)
        
        # Get the generated filename
        project_name = rig.repository.name if rig.repository else "MetaFFI"
        html_filename = f"rig_{project_name}_v4_enhanced_graph.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the V4+ Enhanced RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create V4+ Enhanced RIG HTML graph: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Creating V4+ Enhanced RIG HTML graph for MetaFFI...")
    print("This uses the V4+ Phase 8 Enhancement with direct RIG manipulation")
    
    success = await create_metaffi_rig_html_v4_enhanced()
    
    if success:
        print("\n[OK] V4+ Enhanced RIG HTML graph created successfully!")
        print("Open the HTML file in your browser to view the interactive graph.")
        print("This graph shows the RIG created using the V4+ Phase 8 Enhancement architecture.")
    else:
        print("\n[ERROR] V4+ Enhanced RIG HTML graph creation failed.")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
