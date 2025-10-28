"""
Standalone test for V7 Phase 3: Artifact Discovery on cmake_hello_world repository.

This test runs Phase 1, Phase 2, and Phase 3 in sequence to test the complete
artifact discovery pipeline.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v7.phase1_repository_overview_agent_v7 import RepositoryOverviewAgentV7
from llm0.v7.phase2_build_system_detection_agent_v7 import BuildSystemDetectionAgentV7
from llm0.v7.phase3_artifact_discovery_agent_v7 import ArtifactDiscoveryAgentV7


async def test_phase3_cmake_hello_world():
    """Test Phase 3 artifact discovery on cmake_hello_world repository."""
    
    # Setup logging with file output
    log_filename = f"test_v7_phase3_cmake_hello_world_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("TestPhase3CMakeHelloWorld")
    logger.info(f"Test log saved to: {log_filename}")
    
    # Repository path
    repository_path = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not repository_path.exists():
        logger.error(f"Repository not found: {repository_path}")
        return False
    
    logger.info(f"Testing Phase 3 on repository: {repository_path}")
    
    try:
        # Phase 1: Repository Overview
        logger.info("=== PHASE 1: Repository Overview ===")
        phase1_agent = RepositoryOverviewAgentV7(repository_path)
        phase1_result = await phase1_agent.execute_phase()
        
        logger.info(f"Phase 1 completed. Result: {json.dumps(phase1_result, indent=2)}")
        
        # Phase 2: Build System Detection
        logger.info("=== PHASE 2: Build System Detection ===")
        phase2_agent = BuildSystemDetectionAgentV7(repository_path)
        phase2_result = await phase2_agent.execute_phase(phase1_result)
        
        logger.info(f"Phase 2 completed. Result: {json.dumps(phase2_result, indent=2)}")
        
        # Phase 3: Artifact Discovery
        logger.info("=== PHASE 3: Artifact Discovery ===")
        phase3_agent = ArtifactDiscoveryAgentV7(repository_path)
        phase3_result = await phase3_agent.execute_phase(phase1_result, phase2_result)
        
        logger.info(f"Phase 3 completed. Result: {json.dumps(phase3_result, indent=2)}")
        
        # Validate Phase 3 results
        logger.info("=== VALIDATING PHASE 3 RESULTS ===")
        
        # Get token usage for each phase
        phase1_tokens = phase1_agent.get_total_token_usage()
        phase2_tokens = phase2_agent.get_total_token_usage()
        phase3_tokens = phase3_agent.get_total_token_usage()
        
        total_tokens = phase1_tokens.total_tokens + phase2_tokens.total_tokens + phase3_tokens.total_tokens
        
        logger.info("=== TOKEN USAGE SUMMARY ===")
        logger.info(f"Phase 1 - Input: {phase1_tokens.input_tokens}, Output: {phase1_tokens.output_tokens}, Total: {phase1_tokens.total_tokens}")
        logger.info(f"Phase 2 - Input: {phase2_tokens.input_tokens}, Output: {phase2_tokens.output_tokens}, Total: {phase2_tokens.total_tokens}")
        logger.info(f"Phase 3 - Input: {phase3_tokens.input_tokens}, Output: {phase3_tokens.output_tokens}, Total: {phase3_tokens.total_tokens}")
        logger.info(f"TOTAL - Input: {phase1_tokens.input_tokens + phase2_tokens.input_tokens + phase3_tokens.input_tokens}, Output: {phase1_tokens.output_tokens + phase2_tokens.output_tokens + phase3_tokens.output_tokens}, Total: {total_tokens}")
        
        success = True
        
        # Check if artifact_discovery exists
        if "artifact_discovery" not in phase3_result:
            logger.error("❌ Missing 'artifact_discovery' in Phase 3 result")
            success = False
        else:
            artifact_discovery = phase3_result["artifact_discovery"]
            
            # Check build_system_artifacts
            if "build_system_artifacts" not in artifact_discovery:
                logger.error("❌ Missing 'build_system_artifacts' in artifact_discovery")
                success = False
            else:
                build_system_artifacts = artifact_discovery["build_system_artifacts"]
                
                # Check if CMake artifacts were found
                if "cmake" not in build_system_artifacts:
                    logger.error("❌ Missing 'cmake' in build_system_artifacts")
                    success = False
                else:
                    cmake_artifacts = build_system_artifacts["cmake"]
                    
                    # Check for executables
                    if "executables" not in cmake_artifacts:
                        logger.error("❌ Missing 'executables' in cmake artifacts")
                        success = False
                    else:
                        executables = cmake_artifacts["executables"]
                        if len(executables) == 0:
                            logger.error("❌ No executables found in cmake artifacts")
                            success = False
                        else:
                            logger.info(f"✅ Found {len(executables)} executables")
                            for exe in executables:
                                logger.info(f"  - {exe.get('name', 'unnamed')}")
                    
                    # Check for libraries (may be empty for simple project)
                    if "libraries" in cmake_artifacts:
                        libraries = cmake_artifacts["libraries"]
                        logger.info(f"✅ Found {len(libraries)} libraries")
                        for lib in libraries:
                            logger.info(f"  - {lib.get('name', 'unnamed')}")
            
            # Check artifact_summary
            if "artifact_summary" not in artifact_discovery:
                logger.error("❌ Missing 'artifact_summary' in artifact_discovery")
                success = False
            else:
                artifact_summary = artifact_discovery["artifact_summary"]
                total_artifacts = artifact_summary.get("total_artifacts", 0)
                if total_artifacts == 0:
                    logger.error("❌ No artifacts found in summary")
                    success = False
                else:
                    logger.info(f"✅ Total artifacts: {total_artifacts}")
            
            # Check confidence_scores
            if "confidence_scores" not in artifact_discovery:
                logger.error("❌ Missing 'confidence_scores' in artifact_discovery")
                success = False
            else:
                confidence_scores = artifact_discovery["confidence_scores"]
                overall_confidence = confidence_scores.get("overall_confidence", 0)
                if overall_confidence < 0.8:
                    logger.warning(f"⚠️ Low overall confidence: {overall_confidence}")
                else:
                    logger.info(f"✅ Overall confidence: {overall_confidence}")
            
            # Check evidence_summary
            if "evidence_summary" not in artifact_discovery:
                logger.error("❌ Missing 'evidence_summary' in artifact_discovery")
                success = False
            else:
                evidence_summary = artifact_discovery["evidence_summary"]
                files_analyzed = evidence_summary.get("files_analyzed", [])
                if len(files_analyzed) == 0:
                    logger.error("❌ No files analyzed")
                    success = False
                else:
                    logger.info(f"✅ Files analyzed: {files_analyzed}")
        
        # Final result
        if success:
            logger.info("🎉 Phase 3 test PASSED - All validations successful")
            return True
        else:
            logger.error("❌ Phase 3 test FAILED - Some validations failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Phase 3 test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_phase3_cmake_hello_world()
    if success:
        print("\n✅ Phase 3 test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Phase 3 test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
