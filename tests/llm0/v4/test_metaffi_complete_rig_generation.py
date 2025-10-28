#!/usr/bin/env python3
"""
Test complete RIG generation for MetaFFI and create HTML graph
"""

import sys
import asyncio
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4


async def test_metaffi_complete_rig_generation():
    """Test complete RIG generation for MetaFFI and create HTML graph."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("test_metaffi_complete_rig")
    
    # MetaFFI repository path
    repo_path = Path("C:/src/github.com/MetaFFI")
    
    if not repo_path.exists():
        logger.error(f"MetaFFI repository not found: {repo_path}")
        return False
    
    try:
        logger.info("="*80)
        logger.info("TESTING: Complete RIG Generation for MetaFFI")
        logger.info("="*80)
        logger.info(f"Repository: {repo_path}")
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(repo_path)
        
        # Run the complete 8-phase pipeline
        logger.info("Running complete 8-phase V4 pipeline for MetaFFI...")
        rig = await generator.generate_rig()
        
        logger.info("✅ COMPLETE RIG GENERATION SUCCESSFUL!")
        logger.info(f"Repository: {rig._repository_info.name if rig._repository_info else 'Unknown'}")
        logger.info(f"Components: {len(rig._components) if rig._components else 0}")
        logger.info(f"Tests: {len(rig._tests) if rig._tests else 0}")
        logger.info(f"Evidence: {len(rig._evidence) if rig._evidence else 0}")
        logger.info(f"Aggregators: {len(rig._aggregators) if rig._aggregators else 0}")
        logger.info(f"Runners: {len(rig._runners) if rig._runners else 0}")
        logger.info(f"Utilities: {len(rig.utilities) if rig.utilities else 0}")
        
        # Save the complete RIG to JSON for future use
        rig_data = {
            "repository": {
                "name": rig._repository_info.name if rig._repository_info else "Unknown",
                "root_path": str(rig._repository_info.root_path) if rig._repository_info else "Unknown",
                "build_directory": rig._repository_info.build_directory if rig._repository_info else "Unknown",
                "output_directory": rig._repository_info.output_directory if rig._repository_info else "Unknown",
                "configure_command": rig._repository_info.configure_command if rig._repository_info else "Unknown",
                "build_command": rig._repository_info.build_command if rig._repository_info else "Unknown",
                "install_command": rig._repository_info.install_command if rig._repository_info else "Unknown",
                "test_command": rig._repository_info.test_command if rig._repository_info else "Unknown"
            } if rig._repository_info else {},
            "build_system": {
                "name": rig._build_system_info.name if rig._build_system_info else "Unknown",
                "version": rig._build_system_info.version if rig._build_system_info else "Unknown",
                "build_type": rig._build_system_info.build_type if rig._build_system_info else "Unknown"
            } if rig._build_system_info else {},
            "components_count": len(rig._components) if rig._components else 0,
            "tests_count": len(rig._tests) if rig._tests else 0,
            "evidence_count": len(rig._evidence) if rig._evidence else 0,
            "aggregators_count": len(rig._aggregators) if rig._aggregators else 0,
            "runners_count": len(rig._runners) if rig._runners else 0,
            "utilities_count": len(rig.utilities) if rig.utilities else 0
        }
        
        # Save RIG summary to JSON
        rig_summary_file = project_root / "metaffi_complete_rig_summary.json"
        with open(rig_summary_file, 'w') as f:
            json.dump(rig_data, f, indent=2)
        
        logger.info(f"✅ RIG summary saved to: {rig_summary_file}")
        
        # Generate HTML graph from complete RIG
        logger.info("Generating HTML graph from complete RIG...")
        rig.show_graph(validate_before_show=True)
        
        # Get the generated filename
        project_name = rig._repository_info.name if rig._repository_info else "MetaFFI"
        html_filename = f"rig_{project_name}_graph.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the complete RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete RIG generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Testing complete RIG generation for MetaFFI...")
    
    success = await test_metaffi_complete_rig_generation()
    
    if success:
        print("\n[OK] Complete RIG generation and HTML graph creation successful!")
        print("The RIG graph shows the complete repository structure discovered by all 8 phases.")
    else:
        print("\n[ERROR] Complete RIG generation failed.")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
