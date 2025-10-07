#!/usr/bin/env python3
"""
Enhanced Phase 8: RIG Assembly Agent (V7)

This agent assembles the final RIG with validation using enhanced V7 tools
with batch operations and smart validation, with strict 1 retry limit.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools
from core.rig import RIG
from .rig_tools_v7 import RIGToolsV7


class RIGAssemblyAgentV7Enhanced:
    """Enhanced V7 Phase 8 RIG Assembly Agent with batch operations and 1 retry limit."""
    
    def __init__(self, repository_path: Path, rig_instance: RIG, max_retries: int = 1):
        self.repository_path = repository_path
        self.rig = rig_instance
        self.max_retries = max_retries  # V7: Strict 1 retry limit
        self.logger = logging.getLogger("RIGAssemblyAgentV7Enhanced")
        
        # Initialize enhanced RIG manipulation tools
        self.rig_tools = RIGToolsV7(rig_instance)
        
        # Initialize file and process tools
        self.file_tools = FileTools(root_dir=str(repository_path))
        self.process_tools = ProcessTools(root_cwd=str(repository_path))
        
        # V7: Track retry context for smart error handling
        self._retry_context = []
    
    async def execute_phase(self, phase_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Phase 8 with enhanced V7 tools and strict retry limit."""
        self.logger.info("Starting V7 Enhanced Phase 8: RIG Assembly")
        
        # Create agent with enhanced tools
        agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[
                self.file_tools,
                self.process_tools,
                self.rig_tools
            ],
            builtin_enums=[],
            model_settings={'temperature': 0, 'max_tool_calls': 200, 'request_limit': 500},
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0
        )
        
        # Build enhanced prompt with V7 tools
        prompt = self._build_enhanced_prompt(phase_results)
        
        # Execute with strict 1 retry limit
        for attempt in range(self.max_retries + 1):
            self.logger.info(f"V7 Phase 8 attempt {attempt + 1}/{self.max_retries + 1}")
            
            try:
                # Add retry context if this is a retry
                if self._retry_context:
                    prompt += "\nPREVIOUS ERRORS:\n" + "\n".join([
                        f"Attempt {ctx['attempt']}: {ctx.get('error', 'Validation failed')}\nSUGGESTION: {ctx.get('suggestion', 'Please fix the errors and try again')}"
                        for ctx in self._retry_context
                    ])
                    prompt += "\nCRITICAL: Review the previous errors and fix your tool calls or reasoning.\n"
                
                # Execute the agent
                await agent.run(prompt)
                
                # Validate the RIG
                validation_result = self.rig_tools.validate_rig()
                if "validation passed" in validation_result.lower():
                    self.logger.info("V7 Phase 8 completed successfully")
                    self._clear_retry_context()
                    return {
                        "status": "success",
                        "message": "RIG assembly completed successfully",
                        "rig": self.rig,
                        "validation": validation_result
                    }
                else:
                    error_message = f"Validation failed: {validation_result}"
                    self.logger.warning(f"V7 Phase 8 validation failed: {error_message}")
                    self._retry_context.append({
                        'attempt': attempt + 1,
                        'error': error_message,
                        'suggestion': 'Use batch operations and smart validation tools to fix issues'
                    })
                    
                    if attempt < self.max_retries:
                        prompt += f"\nVALIDATION FAILED: {error_message}\nCRITICAL: Use batch operations and smart validation tools to fix the issues.\n"
                    else:
                        raise Exception(f"V7 Phase 8 failed after {self.max_retries + 1} attempts: {error_message}")
                        
            except Exception as e:
                error_message = f"Tool execution failed: {str(e)}"
                self.logger.error(f"V7 Phase 8 tool error: {error_message}")
                self._retry_context.append({
                    'attempt': attempt + 1,
                    'error': error_message,
                    'suggestion': 'Check tool usage and use batch operations for efficiency'
                })
                
                if attempt < self.max_retries:
                    prompt += f"\nTOOL ERROR: {error_message}\nCRITICAL: Use batch operations and smart validation tools to fix the issues.\n"
                else:
                    raise Exception(f"V7 Phase 8 failed after {self.max_retries + 1} attempts: {error_message}")
        
        # This should never be reached due to the exception above
        raise Exception("V7 Phase 8 failed unexpectedly")
    
    def _build_enhanced_prompt(self, phase_results: List[Dict[str, Any]]) -> str:
        """Build enhanced V7 prompt with batch operations and smart validation."""
        return f"""
You are a V7 Enhanced RIG Assembly Agent. Assemble the final RIG using enhanced tools.

MISSION: Assemble the complete RIG from all previous phase results using V7 enhanced tools.

PHASE RESULTS SUMMARY:
{self._summarize_phase_results(phase_results)}

ENHANCED V7 TOOLS (USE THESE FOR EFFICIENCY):
- add_components_batch(components_data): Add multiple components at once
- add_relationships_batch(relationships_data): Add multiple relationships at once
- add_tests_batch(tests_data): Add multiple tests at once
- validate_component_exists(name): Check if component exists
- validate_relationships_consistency(): Check relationship consistency
- get_assembly_status(): Get current assembly progress
- get_missing_items(): Identify missing items
- get_rig_state(): Get current RIG state
- validate_rig(): Final validation

V7 ENHANCED APPROACH:
1. Use batch operations to add multiple items efficiently
2. Use smart validation tools to check consistency
3. Monitor assembly progress with status tools
4. Fix any issues using validation tools
5. Final validation to ensure completeness

CRITICAL RULES:
- Use batch operations whenever possible (60-70% fewer tool calls)
- Use smart validation tools to catch issues early
- Monitor progress with status tools
- Fix issues immediately using validation tools
- Only 1 retry allowed - be efficient and accurate

ASSEMBLY STRATEGY:
1. Start with batch component addition
2. Add relationships in batches
3. Add tests in batches
4. Validate consistency at each step
5. Monitor progress throughout
6. Final validation

Use the enhanced V7 tools for maximum efficiency and accuracy.
"""
    
    def _summarize_phase_results(self, phase_results: List[Dict[str, Any]]) -> str:
        """Summarize phase results for the prompt."""
        import json
        summary = []
        for i, result in enumerate(phase_results, 1):
            if isinstance(result, dict):
                # Try to extract key information from each phase
                if i == 1:  # Repository Overview
                    repo_info = result.get('repository_overview', {})
                    summary.append(f"Phase {i} (Repository Overview): {json.dumps(repo_info, indent=2)}")
                elif i == 2:  # Source Structure
                    source_info = result.get('source_structure', {})
                    summary.append(f"Phase {i} (Source Structure): {json.dumps(source_info, indent=2)}")
                elif i == 3:  # Test Structure
                    test_info = result.get('test_structure', {})
                    summary.append(f"Phase {i} (Test Structure): {json.dumps(test_info, indent=2)}")
                elif i == 4:  # Build Analysis
                    build_info = result.get('build_analysis', {})
                    summary.append(f"Phase {i} (Build Analysis): {json.dumps(build_info, indent=2)}")
                elif i == 5:  # Artifact Analysis
                    artifact_info = result.get('artifact_analysis', {})
                    summary.append(f"Phase {i} (Artifact Analysis): {json.dumps(artifact_info, indent=2)}")
                elif i == 6:  # Component Classification
                    components_info = result.get('classified_components', {})
                    summary.append(f"Phase {i} (Component Classification): {json.dumps(components_info, indent=2)}")
                elif i == 7:  # Relationship Mapping
                    relationships_info = result.get('relationships', {})
                    summary.append(f"Phase {i} (Relationship Mapping): {json.dumps(relationships_info, indent=2)}")
                else:
                    summary.append(f"Phase {i}: {json.dumps(result, indent=2)}")
            else:
                summary.append(f"Phase {i}: {str(result)[:200]}...")
        return "\n".join(summary)
    
    def _clear_retry_context(self):
        """Clear retry context after successful operation."""
        self._retry_context = []
