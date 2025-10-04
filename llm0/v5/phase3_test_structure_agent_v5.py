#!/usr/bin/env python3
"""
Phase 3: Test Structure Discovery Agent (V5)

This agent discovers and analyzes test structure, using direct RIG manipulation
tools to add test components to the RIG.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class TestStructureDiscoveryAgentV5(BaseLLMAgentV5):
    """V5 Test Structure Discovery Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "TestStructureDiscovery", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 3: Test Structure Discovery."""
        self.logger.info("Phase 3: Test Structure Discovery...")
        
        prompt = f"""
You are a Test Structure Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Discover and analyze test structure, adding test components to the RIG.

REPOSITORY: {self.repository_path}

TASK: Discover test components and add them to the RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Explore test directories and test files
2. Identify test frameworks (JUnit, pytest, CTest, etc.)
3. Discover test targets and test executables
4. Classify tests by type (unit, integration, system, etc.)
5. Add test components to the RIG with evidence

CRITICAL RULES:
- Focus on test structure and test components
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If a test framework cannot be identified, use "unknown" instead of guessing
- If test targets cannot be determined, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to add test components:

1. Use 'add_test' to add test components:
   - name: test name
   - framework: "JUnit|pytest|CTest|GoogleTest|etc|unknown"
   - source_files: list of test source file paths
   - output_path: expected test executable path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

2. Use 'list_dir' to explore test directories
3. Use 'read_text' to examine test files and test configurations
4. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'list_dir' to explore test directories
2. Look for test files, test configurations, test frameworks
3. Identify test frameworks from file content and configurations
4. Determine test types and test targets
5. Use 'add_test' to add each discovered test
6. Use 'read_text' to get evidence from test files

EVIDENCE REQUIREMENTS:
- Every test must have evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

TEST FRAMEWORKS TO LOOK FOR:
- JUnit (Java)
- pytest (Python)
- CTest (C++)
- GoogleTest (C++)
- Jest (JavaScript)
- Mocha (JavaScript)
- RSpec (Ruby)
- etc.

Use the available tools to explore test structure and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 3 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "test_structure_discovery",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 3 failed: {e}")
            return {
                "status": "error",
                "phase": "test_structure_discovery",
                "error": str(e)
            }
