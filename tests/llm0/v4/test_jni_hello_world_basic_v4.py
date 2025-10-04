#!/usr/bin/env python3
"""
Test V4 implementation with jni_hello_world repository
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


async def build_jni_project(project_path: Path) -> bool:
    """Build the JNI CMake project."""
    try:
        # Clean existing build directory
        build_dir = project_path / "build"
        if build_dir.exists():
            import shutil
            shutil.rmtree(build_dir)
            print("Cleaned existing build directory")
        
        # Create fresh build directory
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
        
        print("JNI project built successfully!")
        return True
        
    except Exception as e:
        print(f"Build failed: {e}")
        return False


async def test_v4_rig_generation_jni():
    """Test V4 RIG generation with JNI project."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_v4_jni")
    
    # Test repository path
    test_repo_path = project_root / "tests" / "test_repos" / "jni_hello_world"
    
    if not test_repo_path.exists():
        logger.error(f"Test repository not found: {test_repo_path}")
        return False
    
    try:
        # Build the project first
        logger.info("Building JNI CMake project...")
        if not await build_jni_project(test_repo_path):
            logger.error("Failed to build JNI project")
            return False
        
        # Create V4 generator
        generator = LLMRIGGeneratorV4(test_repo_path)
        
        # Generate RIG
        logger.info("Starting V4 RIG generation for JNI project...")
        rig = await generator.generate_rig()
        
        # Validate RIG
        if not isinstance(rig, RIG):
            logger.error("Generated object is not a RIG instance")
            return False
        
        logger.info(f"SUCCESS: Generated RIG with repository: {rig.repository.name}")
        logger.info(f"Build system: {rig.build_system.name}")
        
        # Print some details about discovered components
        if hasattr(rig, 'components') and rig.components:
            logger.info(f"Discovered {len(rig.components)} components:")
            for component in rig.components[:5]:  # Show first 5 components
                logger.info(f"  - {component.name} ({component.type})")
            if len(rig.components) > 5:
                logger.info(f"  ... and {len(rig.components) - 5} more components")
        
        return True
        
    except Exception as e:
        logger.error(f"V4 RIG generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v4_rig_generation_jni())
    if success:
        print("[OK] V4 RIG generation test with JNI project passed")
    else:
        print("[ERROR] V4 RIG generation test with JNI project failed")
        sys.exit(1)
