#!/usr/bin/env python3
"""
V7 Phase 3 Test - MetaFFI Repository (Standalone)
Tests Phase 3: Artifact Discovery on MetaFFI repository
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v7.phase1_repository_overview_agent_v7 import RepositoryOverviewAgentV7
from llm0.v7.phase2_build_system_detection_agent_v7 import BuildSystemDetectionAgentV7
from llm0.v7.phase3_artifact_discovery_agent_v7 import ArtifactDiscoveryAgentV7

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestPhase3MetaFFI")

async def main():
    """Run Phase 3 test on MetaFFI repository."""
    
    # Set up log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"test_v7_phase3_metaffi_{timestamp}.log"
    
    # Add file handler to logger
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Test log saved to: {log_file}")
    
    # MetaFFI repository path
    repository_path = Path("C:/src/github.com/MetaFFI")
    
    if not repository_path.exists():
        logger.error(f"MetaFFI repository not found at: {repository_path}")
        logger.error("Please ensure MetaFFI repository is available at the specified path")
        return
    
    logger.info(f"Testing Phase 3 on repository: {repository_path}")
    
    try:
        # === PHASE 1: Repository Overview ===
        logger.info("=== PHASE 1: Repository Overview ===")
        phase1_agent = RepositoryOverviewAgentV7(repository_path)
        phase1_result = await phase1_agent.execute_phase()
        logger.info(f"Phase 1 completed. Result: {phase1_result}")
        
        # === PHASE 2: Build System Detection ===
        logger.info("=== PHASE 2: Build System Detection ===")
        phase2_agent = BuildSystemDetectionAgentV7(repository_path)
        phase2_result = await phase2_agent.execute_phase(phase1_result)
        logger.info(f"Phase 2 completed. Result: {phase2_result}")
        
        # === PHASE 3: Artifact Discovery ===
        logger.info("=== PHASE 3: Artifact Discovery ===")
        phase3_agent = ArtifactDiscoveryAgentV7(repository_path)
        phase3_result = await phase3_agent.execute_phase(phase1_result, phase2_result)
        logger.info(f"Phase 3 completed. Result: {phase3_result}")
        
        # === VALIDATING PHASE 3 RESULTS ===
        logger.info("=== VALIDATING PHASE 3 RESULTS ===")
        
        # Check if artifact discovery was successful
        if "error" in phase3_result.get("artifact_discovery", {}):
            logger.error(f"Phase 3 failed with error: {phase3_result['artifact_discovery']['error']}")
            logger.error("Phase 3 test FAILED - Error in artifact discovery")
            return
        
        artifact_discovery = phase3_result.get("artifact_discovery", {})
        build_system_artifacts = artifact_discovery.get("build_system_artifacts", {})
        artifact_summary = artifact_discovery.get("artifact_summary", {})
        confidence_scores = artifact_discovery.get("confidence_scores", {})
        evidence_summary = artifact_discovery.get("evidence_summary", {})
        
        # Validate build system artifacts
        if "cmake" not in build_system_artifacts:
            logger.error("Missing 'cmake' in build_system_artifacts")
        else:
            cmake_artifacts = build_system_artifacts["cmake"]
            executables = cmake_artifacts.get("executables", [])
            libraries = cmake_artifacts.get("libraries", [])
            
            logger.info(f"Found {len(executables)} executables")
            for exe in executables:
                logger.info(f"  - {exe.get('name', 'unknown')}")
            
            logger.info(f"Found {len(libraries)} libraries")
            for lib in libraries:
                logger.info(f"  - {lib.get('name', 'unknown')}")
        
        # Validate artifact summary
        total_artifacts = artifact_summary.get("total_artifacts", 0)
        if total_artifacts == 0:
            logger.error("No artifacts found in summary")
        else:
            logger.info(f"Total artifacts: {total_artifacts}")
            logger.info(f"  - Executables: {artifact_summary.get('executables', 0)}")
            logger.info(f"  - Libraries: {artifact_summary.get('libraries', 0)}")
            logger.info(f"  - JVM Artifacts: {artifact_summary.get('jvm_artifacts', 0)}")
        
        # Validate confidence scores
        overall_confidence = confidence_scores.get("overall_confidence", 0.0)
        if overall_confidence < 0.8:
            logger.warning(f"Low overall confidence: {overall_confidence}")
        else:
            logger.info(f"Overall confidence: {overall_confidence}")
        
        # Validate evidence summary
        files_analyzed = evidence_summary.get("files_analyzed", [])
        if not files_analyzed:
            logger.error("No files analyzed")
        else:
            logger.info(f"Files analyzed: {files_analyzed}")
        
        # Check for MetaFFI-specific patterns
        patterns_found = evidence_summary.get("patterns_found", [])
        if "metaffi" in str(patterns_found).lower():
            logger.info("MetaFFI-specific patterns detected")
        else:
            logger.info("No MetaFFI patterns explicitly mentioned")
        
        # === TOKEN USAGE SUMMARY ===
        logger.info("=== TOKEN USAGE SUMMARY ===")
        
        # Get token usage from each phase
        phase1_tokens = phase1_agent.get_total_token_usage()
        phase2_tokens = phase2_agent.get_total_token_usage()
        phase3_tokens = phase3_agent.get_total_token_usage()
        
        logger.info(f"Phase 1 tokens: {phase1_tokens.input_tokens} input, {phase1_tokens.output_tokens} output, {phase1_tokens.total_tokens} total")
        logger.info(f"Phase 2 tokens: {phase2_tokens.input_tokens} input, {phase2_tokens.output_tokens} output, {phase2_tokens.total_tokens} total")
        logger.info(f"Phase 3 tokens: {phase3_tokens.input_tokens} input, {phase3_tokens.output_tokens} output, {phase3_tokens.total_tokens} total")
        
        total_tokens = phase1_tokens.total_tokens + phase2_tokens.total_tokens + phase3_tokens.total_tokens
        logger.info(f"TOTAL tokens: {total_tokens}")
        
        logger.info("Phase 3 test completed successfully!")
        
    except Exception as e:
        logger.error(f"Phase 3 test FAILED with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
