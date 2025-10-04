#!/usr/bin/env python3
"""
Phase 7: Relationship Mapping Agent (V5)

This agent maps dependencies and relationships between entities, using direct RIG manipulation
tools to add relationship information to the RIG.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class RelationshipMappingAgentV5(BaseLLMAgentV5):
    """V5 Relationship Mapping Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "RelationshipMapping", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 7: Relationship Mapping."""
        self.logger.info("Phase 7: Relationship Mapping...")
        
        prompt = f"""
You are a Relationship Mapping Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Map dependencies and relationships between entities, adding relationship information to the RIG.

REPOSITORY: {self.repository_path}

TASK: Map relationships between components and add them to the RIG using direct manipulation tools.

ANALYSIS STEPS:
1. Analyze component dependencies from build configurations
2. Identify runtime dependencies and relationships
3. Map test relationships to components
4. Determine build order and dependency chains
5. Add relationship information to the RIG with evidence

CRITICAL RULES:
- Focus on component relationships and dependencies
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If relationships cannot be determined, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to add relationship information:

1. Use 'get_rig_summary' to see current components and their relationships
2. Analyze build configurations for dependency information
3. Identify runtime dependencies from source code
4. Map test relationships to components
5. Update component dependencies as needed

EXPLORATION STRATEGY:
1. Start with 'get_rig_summary' to see current components
2. Analyze build configurations for dependencies
3. Examine source code for runtime dependencies
4. Identify test relationships
5. Map all discovered relationships

EVIDENCE REQUIREMENTS:
- Every relationship must be backed by evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

RELATIONSHIP TYPES:
- depends_on: component depends on another component
- links_with: component links with another component
- tests: test component tests another component
- builds_from: component builds from source files
- unknown: when relationship type cannot be determined

Use the available tools to map relationships and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 7 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "relationship_mapping",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 7 failed: {e}")
            return {
                "status": "error",
                "phase": "relationship_mapping",
                "error": str(e)
            }
