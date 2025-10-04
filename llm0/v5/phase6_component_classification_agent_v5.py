#!/usr/bin/env python3
"""
Phase 6: Component Classification Agent (V5)

This agent classifies all discovered entities into RIG types, using direct RIG manipulation
tools to refine component classifications.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .base_agent_v5 import BaseLLMAgentV5


class ComponentClassificationAgentV5(BaseLLMAgentV5):
    """V5 Component Classification Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance, max_retries: int = 3):
        super().__init__(repository_path, rig_instance, "ComponentClassification", max_retries)
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute Phase 6: Component Classification."""
        self.logger.info("Phase 6: Component Classification...")
        
        prompt = f"""
You are a Component Classification Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Classify all discovered entities into RIG types, refining component classifications.

REPOSITORY: {self.repository_path}

TASK: Classify discovered components and refine their types using direct manipulation tools.

ANALYSIS STEPS:
1. Review all discovered components from previous phases
2. Classify components by type (executable, library, utility, test, etc.)
3. Refine component classifications based on evidence
4. Update component types and properties
5. Ensure consistent classification across all components

CRITICAL RULES:
- Focus on component classification and type refinement
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information
- If component types cannot be determined, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V5 ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to refine component classifications:

1. Use 'add_component' to update component classifications:
   - name: component name
   - type: "executable|shared_library|static_library|package_library|vm|interpreted|unknown"
   - programming_language: "C++|Java|Python|JavaScript|Go|etc|unknown"
   - runtime: "native|managed|interpreted|unknown"
   - source_files: list of source file paths
   - output_path: expected output path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

2. Use 'list_dir' to explore component directories
3. Use 'read_text' to examine component files
4. Use 'get_rig_summary' to check current RIG state

EXPLORATION STRATEGY:
1. Start with 'get_rig_summary' to see current components
2. Review each component's classification
3. Refine component types based on evidence
4. Update component properties as needed
5. Ensure consistent classification across all components

EVIDENCE REQUIREMENTS:
- Every classification must be backed by evidence
- Evidence must include: file path, line numbers, content, reason
- Use 'read_text' to get file content for evidence
- If you can't determine something, mark as "unknown"

COMPONENT TYPES:
- executable: main applications, CLI tools
- shared_library: shared libraries (.so, .dll, .dylib)
- static_library: static libraries (.a, .lib)
- package_library: packaged libraries (.jar, .whl, .tgz)
- vm: virtual machine executables
- interpreted: interpreted scripts
- unknown: when type cannot be determined

Use the available tools to classify components and build the RIG directly.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            
            # Log RIG state after phase completion
            self.logger.info(f"Phase 6 completed. RIG state: {self.rig_tools.get_rig_summary()}")
            
            return {
                "status": "success",
                "phase": "component_classification",
                "rig_summary": self.rig_tools.get_rig_summary(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 6 failed: {e}")
            return {
                "status": "error",
                "phase": "component_classification",
                "error": str(e)
            }
