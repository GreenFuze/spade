#!/usr/bin/env python3
"""
Test V4 implementation with project build
"""

import sys
import asyncio
import logging
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4 import LLMRIGGeneratorV4
from core.rig import RIG


async def build_cmake_project(project_path: Path) -> bool:
    """Build the CMake project."""
    try:
        # Create build directory
        build_dir = project_path / "build"
        build_dir.mkdir(exist_ok=True)
        
        # Configure with CMake
        configure_cmd = ["cmake", "-S", ".", "-B", "build"]
        result = subprocess.run(configure_cmd, cwd=project_path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"CMake configure failed: {result.stderr}")
            return False
        
        # Build the project
        build_cmd = ["cmake", "--build", "build"]
        result = subprocess.run(build_cmd, cwd=project_path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"CMake build failed: {result.stderr}")
            return False
        
        print("Project built successfully!")
        return True
        
    except Exception as e:
        print(f"Build failed: {e}")
        return False


async def test_v4_rig_generation_with_build():
    """Test V4 RIG generation with built project."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_v4_with_build")
    
    # Test repository path
    test_repo_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not test_repo_path.exists():
        logger.error(f"Test repository not found: {test_repo_path}")
        return False
    
    try:
        # Build the project first
        logger.info("Building CMake project...")
        if not await build_cmake_project(test_repo_path):
            logger.error("Failed to build project")
            return False
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(test_repo_path)
        
        # Generate RIG
        logger.info("Starting V4 RIG generation...")
        rig = await generator.generate_rig()
        
        # Validate RIG
        if not isinstance(rig, RIG):
            logger.error("Generated object is not a RIG instance")
            return False
        
        logger.info(f"SUCCESS: Generated RIG with repository: {rig._repository_info.name}")
        logger.info(f"Build system: {rig._build_system_info.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"V4 RIG generation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v4_rig_generation_with_build())
    if success:
        print("[OK] V4 RIG generation test with build passed")
    else:
        print("[ERROR] V4 RIG generation test with build failed")
        sys.exit(1)
