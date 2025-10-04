#!/usr/bin/env python3
"""
Phase 1: Repository Overview Agent (V5)

This agent performs high-level repository structure analysis and build system
identification, using direct RIG manipulation tools instead of JSON generation.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class RepositoryOverviewAgentV5(BaseLLMAgentV5):
    """V5 Repository Overview Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "RepositoryOverview", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 1: Repository Overview Analysis."""
        self.logger.info("Phase 1: Repository Overview Analysis...")
        
        prompt = f"""
You are a Repository Overview Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Perform high-level repository structure analysis and build system identification.

REPOSITORY: {self.repository_path}

TASK: Analyze the repository structure and identify build systems using direct RIG manipulation tools.

ANALYSIS STEPS:
1. Scan the repository root directory to identify build system indicator files
2. Categorize directories by purpose (source, test, build, documentation)
3. Identify main entry points and configuration files
4. Determine exploration scope for subsequent phases
5. Detect primary programming languages and build systems

CRITICAL RULES:
- Focus on high-level structure, not detailed analysis
- Identify build systems from configuration files
- Determine exploration scope for subsequent phases
- Avoid deep directory traversal in this phase
- Use evidence-based approach - only report what you can verify
- Do NOT assume subdirectory structure (e.g., don't assume 'src/main' exists)
- Only report directories that you can actually see and verify
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"
- NEVER guess, speculate, or make assumptions about unknown information
- If a build system cannot be identified, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- NEVER use absolute paths or paths that go outside the repository
- If you need to access a file, use relative paths like "CMakeLists.txt" not absolute paths
- Stay within the repository boundaries at all times
- If you're unsure about a path, use 'list_dir' to check what's available first

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Instead of generating JSON, use the available RIG manipulation tools:

1. Use 'set_repository_overview' to set basic repository information:
   - name: repository name
   - type: "application|library|framework|tool"
   - primary_language: "C++|Java|Python|JavaScript|Go|etc"
   - build_systems: ["cmake", "maven", "npm", etc.]
   - evidence: list of evidence objects with file, lines, content, reason

2. Use 'set_build_system_info' to set build system details:
   - name: build system name (e.g., "CMake", "Maven", "npm")
   - version: version string or "unknown"
   - build_type: "Debug|Release|unknown"
   - evidence: list of evidence objects

3. Use 'list_dir' to explore the repository structure
4. Use 'read_text' to examine configuration files
5. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'list_dir' to see the root directory contents
2. Look for build system indicator files (CMakeLists.txt, package.json, pom.xml, etc.)
3. Identify source directories, test directories, build directories
4. Use 'set_repository_overview' to record your findings
5. Use 'set_build_system_info' to record build system details

EVIDENCE REQUIREMENTS:
- Every conclusion must be backed by evidence
- Evidence must include: file path, line numbers (if applicable), content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

Use the available tools to explore the repository and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 1 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "repository_overview",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 1 failed: {e}")
            return {
                "status": "error",
                "phase": "repository_overview",
                "error": str(e)
            }
