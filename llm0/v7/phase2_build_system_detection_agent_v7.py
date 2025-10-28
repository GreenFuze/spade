# Phase 2: Build System Detection Agent V7
# Single Goal: Identify all build systems present in the repository

"""
Phase 2: Build System Detection Agent V7

This agent focuses on a single, well-defined goal:
- Identify all build systems present in the repository with evidence and confidence scores

Input: Repository path, Phase 1 output (languages detected)
Output: Build systems detected with evidence

The agent uses deterministic tools and maintains context isolation.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from agentkit_gf.tools.fs import FileTools
from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent

from .base_agent_v7 import BaseLLMAgentV7
from .phase2_tools import Phase2Tools


class BuildSystemDetectionAgentV7(BaseLLMAgentV7):
    """Phase 2: Build System Detection Agent V7"""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "BuildSystemDetectionAgentV7")
        
        # Initialize Phase 2 specific tools
        self.phase2_tools = Phase2Tools(repository_path)
        
        # Create agent with Phase 2 tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.phase2_tools, FileTools(root_dir=repository_path)],
            builtin_enums=[],
            temperature=0,
            max_tool_retries=1,
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def execute_phase(self, phase1_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Phase 2: Build System Detection
        
        Args:
            phase1_output: Output from Phase 1 (languages detected)
            
        Returns:
            Build systems detected with evidence and confidence scores
        """
        
        prompt = f"""
You are a Build System Detection Agent (Phase 2). Your single goal is to identify all build systems present in the repository.

PHASE 1 OUTPUT (Languages Detected):
{phase1_output}

YOUR TASK:
1. Based on the detected languages, decide which file and directory patterns to scan
2. Use the `detect_build_systems` tool with your chosen patterns
3. Interpret the tool results to determine build systems with confidence scores
4. If confidence is low, call the tool again with different patterns
5. Provide structured output with evidence for each detected build system

CRITICAL RULES:
- You control the exploration by setting file_patterns and directory_patterns
- Based on detected languages, choose relevant build system patterns to scan
- The tool will return all found signals - you interpret them
- You can call the tool multiple times with different patterns if needed
- Focus only on build system detection - this is your single goal

EXAMPLES OF PATTERN SELECTION:
- If C++ detected: file_patterns=["CMakeLists.txt", "*.cmake", "Makefile"], directory_patterns=["build/"]
- If Java detected: file_patterns=["pom.xml", "build.gradle"], directory_patterns=["target/", "build/"]
- If JavaScript detected: file_patterns=["package.json"], directory_patterns=["node_modules/", "dist/"]
- If multiple languages: scan broadly with common patterns

OUTPUT FORMAT:
{{
  "build_systems_detected": {{
    "cmake": {{
      "detected": true,
      "confidence": 0.95,
      "evidence": ["CMakeLists.txt", "build/"],
      "reasoning": "CMakeLists.txt found in root directory"
    }},
    "maven": {{
      "detected": false,
      "confidence": 0.0,
      "evidence": [],
      "reasoning": "No pom.xml found"
    }}
  }},
  "build_analysis": {{
    "primary_build_system": "cmake",
    "secondary_build_systems": [],
    "multi_build_system": false,
    "language_build_mapping": {{"C++": "cmake"}}
  }},
  "confidence_verification": {{
    "all_build_systems_analyzed": true,
    "all_confidence_scores_above_95": true,
    "evidence_sufficient": true,
    "ready_for_phase_3": true
  }}
}}

Remember: You control the exploration strategy. Choose patterns based on detected languages, then interpret the results.
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            return result
        except Exception as e:
            self.logger.error(f"Phase 2 execution failed: {e}")
            raise
