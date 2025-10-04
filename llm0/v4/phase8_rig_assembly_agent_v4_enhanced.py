#!/usr/bin/env python3
"""
Enhanced Phase 8: RIG Assembly Agent (V4+)

This agent assembles the final RIG with validation using direct RIG manipulation
tools, avoiding the context explosion issue of the original V4 Phase 8.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools
from core.rig import RIG
from .rig_tools_v4 import RIGToolsV4


class RIGAssemblyAgentV4Enhanced:
    """Enhanced V4+ Phase 8 RIG Assembly Agent with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance: RIG, max_retries: int = 3):
        self.repository_path = repository_path
        self.rig = rig_instance
        self.max_retries = max_retries
        self.logger = logging.getLogger("RIGAssemblyAgentV4Enhanced")
        
        # Initialize RIG manipulation tools
        self.rig_tools = RIGToolsV4(rig_instance)
        
        # Initialize file and process tools
        self.file_tools = FileTools(root_dir=str(repository_path))
        self.process_tools = ProcessTools(root_cwd=str(repository_path))
        
        # Create agent with RIG tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.rig_tools, self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0
        )
    
    async def execute_phase(self, phase1_7_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced Phase 8: RIG Assembly with validation loop."""
        self.logger.info("Phase 8: Enhanced RIG Assembly with direct manipulation...")
        
        try:
            # Step 1: Read Phase 1-7 results (small context)
            self.logger.info("Step 1: Reading Phase 1-7 results...")
            
            # Step 2: Use RIG tools to build RIG incrementally
            self.logger.info("Step 2: Building RIG incrementally...")
            
            prompt = f"""
You are an Enhanced RIG Assembly Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Assemble the final RIG using direct RIG manipulation tools, avoiding context explosion.

REPOSITORY: {self.repository_path}

PHASE 1-7 RESULTS:
{self._format_phase_results(phase1_7_results)}

TASK: Use the RIG manipulation tools to build the RIG step-by-step from the Phase 1-7 results.

CRITICAL RULES:
- Use RIG manipulation tools instead of generating huge JSON
- Build RIG incrementally, one component at a time
- Validate after each operation
- Fix mistakes if validation fails
- Focus on RIG assembly and validation
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown"
- NEVER guess, speculate, or make assumptions about unknown information

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- Stay within the repository boundaries at all times

V4+ ARCHITECTURE - DIRECT RIG MANIPULATION:
Use the available RIG manipulation tools to build the RIG:

1. Use 'add_repository_info' to add repository overview from Phase 1:
   - name: repository name
   - type: "application|library|framework|tool"
   - primary_language: "C++|Java|Python|JavaScript|Go|etc"
   - build_systems: ["cmake", "maven", "npm", etc.]
   - evidence: list of evidence objects

2. Use 'add_build_system_info' to add build system details from Phase 4:
   - name: build system name (e.g., "CMake", "Maven", "npm")
   - version: version string or "unknown"
   - build_type: "Debug|Release|unknown"
   - evidence: list of evidence objects

3. Use 'add_component' to add source components from Phase 2:
   - name: component name
   - type: "executable|shared_library|static_library|package_library|unknown"
   - programming_language: "C++|Java|Python|JavaScript|Go|etc|unknown"
   - runtime: "native|managed|interpreted|unknown"
   - source_files: list of source file paths
   - output_path: expected output path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

4. Use 'add_test' to add test components from Phase 3:
   - name: test name
   - framework: "JUnit|pytest|CTest|GoogleTest|etc|unknown"
   - source_files: list of test source file paths
   - output_path: expected test executable path or "unknown"
   - dependencies: list of dependency names
   - evidence: list of evidence objects

5. Use 'add_relationship' to add relationships from Phase 7:
   - source: source component name
   - target: target component name
   - relationship_type: "depends_on|links_with|tests|builds_from|unknown"
   - evidence: list of evidence objects

6. Use 'get_rig_state' to check current RIG state
7. Use 'validate_rig' to validate RIG completeness and consistency

VALIDATION LOOP STRATEGY:
1. Add repository information first
2. Add build system information
3. Add components one by one
4. Add tests one by one
5. Add relationships one by one
6. Validate after each major operation
7. Fix mistakes if validation fails
8. Repeat until RIG is complete and valid

EVIDENCE REQUIREMENTS:
- Every operation must be backed by evidence from Phase 1-7 results
- Evidence must include: file path, line numbers, content, reason
- If you can't determine something, mark as "unknown"

Use the available tools to build the RIG incrementally and validate each step.
"""
            
            # Execute the enhanced Phase 8
            result = await self._execute_with_validation_loop(prompt, phase1_7_results)
            
            # Log final RIG state
            self.logger.info(f"Phase 8 completed. Final RIG state: {self.rig_tools.get_rig_state()}")
            
            return {
                "status": "success",
                "phase": "rig_assembly_enhanced",
                "rig_summary": self.rig_tools.get_rig_state(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Phase 8 failed: {e}")
            return {
                "status": "error",
                "phase": "rig_assembly_enhanced",
                "error": str(e)
            }
    
    def _format_phase_results(self, phase_results: Dict[str, Any]) -> str:
        """Format Phase 1-7 results for the LLM context."""
        formatted = []
        
        for phase, result in phase_results.items():
            formatted.append(f"=== {phase.upper()} ===")
            formatted.append(f"Result: {result}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    async def _execute_with_validation_loop(self, prompt: str, phase_results: Dict[str, Any]) -> str:
        """Execute Phase 8 with validation loop."""
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # Execute the agent
                response = await self.agent.run(prompt)
                
                # Validate the RIG after execution
                validation = self.rig_tools.validate_rig()
                
                if validation["is_valid"]:
                    self.logger.info("RIG validation passed!")
                    return response
                else:
                    self.logger.warning(f"RIG validation failed: {validation['errors']}")
                    
                    if retries < self.max_retries:
                        # Give the LLM another chance to fix the issues
                        retry_prompt = f"""
VALIDATION FAILED: {validation['errors']}

Please fix the following issues in the RIG:
{validation['errors']}

Current RIG state: {self.rig_tools.get_rig_state()}

Use the RIG manipulation tools to fix these issues and try again.
"""
                        
                        self.logger.info(f"Retry {retries + 1}/{self.max_retries}: Fixing validation issues...")
                        response = await self.agent.run(retry_prompt)
                        retries += 1
                    else:
                        self.logger.error(f"Max retries ({self.max_retries}) exceeded for validation")
                        raise Exception(f"RIG validation failed after {self.max_retries} retries: {validation['errors']}")
                
            except Exception as e:
                self.logger.error(f"Execution failed (attempt {retries + 1}): {e}")
                retries += 1
                if retries > self.max_retries:
                    raise
        
        return "Phase 8 execution completed"
