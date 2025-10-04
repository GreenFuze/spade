#!/usr/bin/env python3
"""
Debug path issues in V4
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add agentkit-gf to path
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools


async def test_paths():
    """Test path handling."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_paths")
    
    # Test repository path
    test_repo_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Test repo path: {test_repo_path}")
    logger.info(f"Test repo exists: {test_repo_path.exists()}")
    logger.info(f"Test repo absolute: {test_repo_path.absolute()}")
    
    try:
        # Create tools
        file_tools = FileTools(root_dir=str(test_repo_path.absolute()))
        process_tools = ProcessTools(root_cwd=str(test_repo_path.absolute()))
        
        logger.info("Tools created successfully")
        
        # Test file listing
        result = file_tools.list_dir(".")
        logger.info(f"List dir result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Path test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_paths())
    if success:
        print("[OK] Path test passed")
    else:
        print("[ERROR] Path test failed")
        sys.exit(1)
