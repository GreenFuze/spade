#!/usr/bin/env python3
"""
Phase 2: Source Structure Discovery Agent (V5)

This agent discovers and analyzes source code structure, using direct RIG manipulation
tools to add source components to the RIG.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class SourceStructureDiscoveryAgentV5(BaseLLMAgentV5):
    """V5 Source Structure Discovery Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "SourceStructureDiscovery", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 2: Source Structure Discovery."""
        self.logger.info("Phase 2: Source Structure Discovery...")
        
        prompt = f"""
You are a Source Structure Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Discover and analyze source code structure, adding source components to the RIG.

REPOSITORY: {self.repository_path}

TASK: Discover source code components and add them to the RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Explore source directories identified in Phase 1
2. Discover source files and their purposes
3. Identify programming languages and file types
4. Classify components by type (executable, library, utility, etc.)
5. Add source components to the RIG with evidence

CRITICAL RULES:
- Focus on source code structure and components
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If a component type cannot be determined, use "unknown" instead of guessing
- If a programming language cannot be identified, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to add source components:

1. Use 'add_component' to add source components:
   - name: component name
   - type: "executable|library|utility|test|unknown"
   - programming_language: "C++|Java|Python|JavaScript|Go|etc|unknown"
   - runtime: "native|managed|interpreted|unknown"
   - source_files: list of source file paths
   - output_path: expected output path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

2. Use 'list_dir' to explore source directories
3. Use 'read_text' to examine source files and build configurations
4. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'list_dir' to explore source directories
2. Look for main source files, headers, configuration files
3. Identify programming languages from file extensions and content
4. Determine component types from build configurations
5. Use 'add_component' to add each discovered component
6. Use 'read_text' to get evidence from source files and build configs

EVIDENCE REQUIREMENTS:
- Every component must have evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

COMPONENT TYPES:
- executable: main applications, CLI tools
- library: shared libraries, static libraries
- utility: helper scripts, build tools
- test: test files and test executables
- unknown: when type cannot be determined

Use the available tools to explore source structure and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 2 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "source_structure_discovery",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 2 failed: {e}")
            return {
                "status": "error",
                "phase": "source_structure_discovery",
                "error": str(e)
            }
