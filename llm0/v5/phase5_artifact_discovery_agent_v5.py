#!/usr/bin/env python3
"""
Phase 5: Artifact Discovery Agent (V5)

This agent discovers build output files and artifacts, using direct RIG manipulation
tools to add artifact information to the RIG.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class ArtifactDiscoveryAgentV5(BaseLLMAgentV5):
    """V5 Artifact Discovery Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "ArtifactDiscovery", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 5: Artifact Discovery."""
        self.logger.info("Phase 5: Artifact Discovery...")
        
        prompt = f"""
You are an Artifact Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Discover build output files and artifacts, adding artifact information to the RIG.

REPOSITORY: {self.repository_path}

TASK: Discover build artifacts and add them to the RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Explore build output directories (build/, dist/, target/, etc.)
2. Identify executable files, libraries, and other build outputs
3. Analyze artifact types and purposes
4. Determine artifact dependencies and relationships
5. Add artifact information to the RIG with evidence

CRITICAL RULES:
- Focus on build artifacts and output files
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If artifact types cannot be determined, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to add artifact information:

1. Use 'add_component' to add artifact components:
   - name: artifact name
   - type: "executable|shared_library|static_library|package_library|unknown"
   - programming_language: "C++|Java|Python|JavaScript|Go|etc|unknown"
   - runtime: "native|managed|interpreted|unknown"
   - source_files: list of source file paths
   - output_path: actual output path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

2. Use 'list_dir' to explore build directories
3. Use 'read_text' to examine build output files
4. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'list_dir' to explore build directories
2. Look for executable files, libraries, and other outputs
3. Identify artifact types and purposes
4. Determine artifact dependencies
5. Use 'add_component' to add each discovered artifact
6. Use 'read_text' to get evidence from build outputs

EVIDENCE REQUIREMENTS:
- Every artifact must have evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

ARTIFACT TYPES:
- executable: main applications, CLI tools
- shared_library: shared libraries (.so, .dll, .dylib)
- static_library: static libraries (.a, .lib)
- package_library: packaged libraries (.jar, .whl, .tgz)
- unknown: when type cannot be determined

Use the available tools to explore build artifacts and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 5 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "artifact_discovery",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 5 failed: {e}")
            return {
                "status": "error",
                "phase": "artifact_discovery",
                "error": str(e)
            }
