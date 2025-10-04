#!/usr/bin/env python3
"""
Phase 4: Build System Analysis Agent (V5)

This agent analyzes build system configuration and targets, using direct RIG manipulation
tools to add build system information to the RIG.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class BuildSystemAnalysisAgentV5(BaseLLMAgentV5):
    """V5 Build System Analysis Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "BuildSystemAnalysis", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 4: Build System Analysis."""
        self.logger.info("Phase 4: Build System Analysis...")
        
        prompt = f"""
You are a Build System Analysis Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Analyze build system configuration and targets, adding build system information to the RIG.

REPOSITORY: {self.repository_path}

TASK: Analyze build system configuration and add build system details to the RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Examine build configuration files (CMakeLists.txt, Makefile, package.json, etc.)
2. Identify build targets and their dependencies
3. Analyze build system settings and options
4. Determine build output locations and artifacts
5. Add build system information to the RIG with evidence

CRITICAL RULES:
- Focus on build system configuration and targets
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If build targets cannot be determined, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to add build system information:

1. Use 'set_build_system_info' to set build system details:
   - name: build system name (e.g., "CMake", "Make", "npm")
   - version: version string or "unknown"
   - build_type: "Debug|Release|unknown"
   - evidence: list of evidence objects

2. Use 'list_dir' to explore build directories
3. Use 'read_text' to examine build configuration files
4. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'list_dir' to explore build directories
2. Look for build configuration files
3. Identify build targets and dependencies
4. Determine build system settings
5. Use 'set_build_system_info' to record findings
6. Use 'read_text' to get evidence from build files

EVIDENCE REQUIREMENTS:
- Every conclusion must be backed by evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

BUILD SYSTEMS TO LOOK FOR:
- CMake (CMakeLists.txt)
- Make (Makefile)
- npm (package.json)
- Maven (pom.xml)
- Gradle (build.gradle)
- etc.

Use the available tools to explore build system and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 4 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "build_system_analysis",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 4 failed: {e}")
            return {
                "status": "error",
                "phase": "build_system_analysis",
                "error": str(e)
            }
