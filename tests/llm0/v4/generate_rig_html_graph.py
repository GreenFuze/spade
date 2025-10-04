#!/usr/bin/env python3
"""
Generate HTML Graph from RIG created by Phase 8
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


async def generate_rig_and_html_graph(repository_path: Path, output_filename: str = None):
    """Generate RIG from Phase 8 and create HTML graph visualization."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("generate_rig_html_graph")
    
    if not repository_path.exists():
        logger.error(f"Repository not found: {repository_path}")
        return False
    
    try:
        logger.info(f"Generating RIG for repository: {repository_path}")
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(repository_path)
        
        # Run the complete 8-phase pipeline
        logger.info("Running complete 8-phase V4 pipeline...")
        rig = await generator.generate_rig()
        
        logger.info("✅ RIG generation completed successfully!")
        logger.info(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        logger.info(f"Components: {len(rig.components) if rig.components else 0}")
        logger.info(f"Relationships: {len(rig.relationships) if rig.relationships else 0}")
        
        # Generate HTML graph
        logger.info("Generating HTML graph visualization...")
        rig.show_graph(validate_before_show=True)
        
        # Get the generated filename
        project_name = rig.repository.name if rig.repository else "unknown"
        html_filename = f"rig_{project_name}_graph.html"
        
        if output_filename:
            # Rename to custom filename if provided
            import shutil
            shutil.move(html_filename, output_filename)
            html_filename = output_filename
        
        logger.info(f"✅ HTML graph generated: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate RIG and HTML graph: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to generate RIG HTML graph."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate HTML graph from RIG")
    parser.add_argument("repository_path", help="Path to repository to analyze")
    parser.add_argument("--output", "-o", help="Output HTML filename")
    
    args = parser.parse_args()
    
    repository_path = Path(args.repository_path)
    output_filename = args.output
    
    success = await generate_rig_and_html_graph(repository_path, output_filename)
    
    if success:
        print("\n[OK] RIG HTML graph generation completed successfully!")
    else:
        print("\n[ERROR] RIG HTML graph generation failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
