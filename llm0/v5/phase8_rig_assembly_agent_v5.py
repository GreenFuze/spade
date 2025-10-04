#!/usr/bin/env python3
"""
Phase 8: RIG Assembly Agent (V5)

This agent assembles the final RIG with validation, using direct RIG manipulation
tools to complete the RIG assembly.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class RIGAssemblyAgentV5(BaseLLMAgentV5):
    """V5 RIG Assembly Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "RIGAssembly", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 8: RIG Assembly."""
        self.logger.info("Phase 8: RIG Assembly...")
        
        prompt = f"""
You are a RIG Assembly Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Assemble the final RIG with validation, completing the RIG assembly process.

REPOSITORY: {self.repository_path}

TASK: Complete the RIG assembly and validate the final RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Review all components, tests, and relationships in the RIG
2. Validate RIG completeness and consistency
3. Ensure all components have proper evidence
4. Verify relationship mappings are correct
5. Complete the final RIG assembly

CRITICAL RULES:
- Focus on RIG assembly and validation
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If validation cannot be completed, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to complete RIG assembly:

1. Use 'get_rig_summary' to review the current RIG state
2. Validate all components have proper evidence
3. Verify relationship mappings are correct
4. Ensure RIG completeness and consistency
5. Complete the final RIG assembly

EXPLORATION STRATEGY:
1. Start with 'get_rig_summary' to see current RIG state
2. Review all components and their properties
3. Validate evidence for all components
4. Verify relationship mappings
5. Complete the final RIG assembly

EVIDENCE REQUIREMENTS:
- Every component must have evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

VALIDATION CRITERIA:
- All components have proper evidence
- All relationships are correctly mapped
- All tests are properly linked to components
- RIG is complete and consistent
- No missing or invalid data

Use the available tools to complete RIG assembly and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 8 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "rig_assembly",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 8 failed: {e}")
            return {
                "status": "error",
                "phase": "rig_assembly",
                "error": str(e)
            }
