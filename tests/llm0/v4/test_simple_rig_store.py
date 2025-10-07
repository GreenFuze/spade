#!/usr/bin/env python3
"""
Test RIG Store functionality with cmake_hello_world repository
Generate RIG, save to store, load back, and compare
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.llm0_rig_generator_v4_enhanced import LLMRIGGeneratorV4Enhanced
from core.rig_store import RIGStore


async def test_simple_rig_store():
    """Test RIG store functionality with cmake_hello_world repository."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("test_simple_rig_store")
    
    # Use the cmake_hello_world repository
    repo_path = Path("tests/test_repos/cmake_hello_world")
    
    if not repo_path.exists():
        logger.error(f"Repository not found: {repo_path}")
        return False
    
    try:
        logger.info(f"Testing RIG Store with cmake_hello_world repository...")
        logger.info(f"Repository path: {repo_path}")
        
        # Step 1: Generate RIG using V4+ Enhanced
        logger.info("=== STEP 1: Generating RIG using V4+ Enhanced ===")
        generator = LLMRIGGeneratorV4Enhanced(repo_path)
        original_rig = await generator.generate_rig()
        
        logger.info("✅ Original RIG generated successfully!")
        logger.info(f"Repository: {original_rig.repository.name if original_rig.repository else 'Unknown'}")
        logger.info(f"Components: {len(original_rig.components) if original_rig.components else 0}")
        logger.info(f"Tests: {len(original_rig.tests) if original_rig.tests else 0}")
        logger.info(f"Evidence: {len(original_rig.evidence) if original_rig.evidence else 0}")
        
        # Step 2: Save RIG to store
        logger.info("=== STEP 2: Saving RIG to store ===")
        db_path = Path("cmake_hello_world_rig_store.db")
        store = RIGStore(db_path)
        
        rig_id = store.save_rig(original_rig, "cmake_hello_world V4+ Enhanced RIG")
        logger.info(f"✅ RIG saved to store with ID: {rig_id}")
        
        # Step 3: Load RIG from store
        logger.info("=== STEP 3: Loading RIG from store ===")
        loaded_rig = store.load_rig(rig_id)
        logger.info("✅ RIG loaded from store successfully!")
        
        # Step 4: Compare RIGs
        logger.info("=== STEP 4: Comparing original and loaded RIGs ===")
        
        # Compare basic properties
        original_repo_name = original_rig.repository.name if original_rig.repository else None
        loaded_repo_name = loaded_rig.repository.name if loaded_rig.repository else None
        
        logger.info(f"Repository names - Original: {original_repo_name}, Loaded: {loaded_repo_name}")
        assert original_repo_name == loaded_repo_name, "Repository names don't match"
        
        original_components_count = len(original_rig.components) if original_rig.components else 0
        loaded_components_count = len(loaded_rig.components) if loaded_rig.components else 0
        
        logger.info(f"Components count - Original: {original_components_count}, Loaded: {loaded_components_count}")
        assert original_components_count == loaded_components_count, "Components count doesn't match"
        
        original_tests_count = len(original_rig.tests) if original_rig.tests else 0
        loaded_tests_count = len(loaded_rig.tests) if loaded_rig.tests else 0
        
        logger.info(f"Tests count - Original: {original_tests_count}, Loaded: {loaded_tests_count}")
        assert original_tests_count == loaded_tests_count, "Tests count doesn't match"
        
        original_evidence_count = len(original_rig.evidence) if original_rig.evidence else 0
        loaded_evidence_count = len(loaded_rig.evidence) if loaded_rig.evidence else 0
        
        logger.info(f"Evidence count - Original: {original_evidence_count}, Loaded: {loaded_evidence_count}")
        assert original_evidence_count == loaded_evidence_count, "Evidence count doesn't match"
        
        # Compare component details
        if original_rig.components and loaded_rig.components:
            original_component_names = [c.name for c in original_rig.components]
            loaded_component_names = [c.name for c in loaded_rig.components]
            
            logger.info(f"Component names - Original: {original_component_names}")
            logger.info(f"Component names - Loaded: {loaded_component_names}")
            
            # Sort for comparison
            original_component_names.sort()
            loaded_component_names.sort()
            assert original_component_names == loaded_component_names, "Component names don't match"
        
        # Compare test details
        if original_rig.tests and loaded_rig.tests:
            original_test_names = [t.name for t in original_rig.tests]
            loaded_test_names = [t.name for t in loaded_rig.tests]
            
            logger.info(f"Test names - Original: {original_test_names}")
            logger.info(f"Test names - Loaded: {loaded_test_names}")
            
            # Sort for comparison
            original_test_names.sort()
            loaded_test_names.sort()
            assert original_test_names == loaded_test_names, "Test names don't match"
        
        logger.info("✅ All comparisons passed! RIG store functionality is working correctly.")
        
        # Step 5: Generate HTML graph from loaded RIG
        logger.info("=== STEP 5: Generating HTML graph from loaded RIG ===")
        loaded_rig.show_graph(validate_before_show=True)
        
        project_name = loaded_rig.repository.name if loaded_rig.repository else "cmake_hello_world"
        html_filename = f"rig_{project_name}_v4_enhanced_from_store.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to test RIG store: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("Testing RIG Store functionality with cmake_hello_world...")
    print("This will generate a RIG, save it to SQLite, load it back, and compare")
    
    success = await test_simple_rig_store()
    
    if success:
        print("\n[OK] RIG Store test completed successfully!")
        print("The RIG was generated, saved to SQLite, loaded back, and verified.")
        print("HTML graph was generated from the loaded RIG.")
    else:
        print("\n[ERROR] RIG Store test failed.")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
