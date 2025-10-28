# Phase 4: Exploration Scope Definition Agent V7
# Single Goal: Define exploration scope and strategy for subsequent phases

"""
Phase 4: Exploration Scope Definition Agent V7

This agent focuses on a single, well-defined goal:
- Define exploration scope and strategy for subsequent phases

Input: Repository path, Phase 1-3 outputs (languages, build systems, architecture)
Output: Exploration scope with priority directories and skip lists

The agent uses deterministic tools and maintains context isolation.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from agentkit_gf.tools.fs import FileTools
from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent

from .base_agent_v7 import BaseLLMAgentV7
from .phase4_tools import Phase4Tools


class ExplorationScopeAgentV7(BaseLLMAgentV7):
    """Phase 4: Exploration Scope Definition Agent V7"""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "ExplorationScopeAgentV7")
        
        # Initialize Phase 4 specific tools
        self.phase4_tools = Phase4Tools(repository_path)
        
        # Create agent with Phase 4 tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.phase4_tools, FileTools(root_dir=repository_path)],
            builtin_enums=[],
            temperature=0,
            max_tool_retries=1,
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def execute_phase(self, phase1_output: Dict[str, Any], 
                          phase2_output: Dict[str, Any], 
                          phase3_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Phase 4: Exploration Scope Definition
        
        Args:
            phase1_output: Output from Phase 1 (languages detected)
            phase2_output: Output from Phase 2 (build systems detected)
            phase3_output: Output from Phase 3 (architecture classification)
            
        Returns:
            Exploration scope with priority directories and skip lists
        """
        
        prompt = f"""
You are an Exploration Scope Definition Agent (Phase 4). Your single goal is to define exploration scope and strategy for subsequent phases.

PHASE 1 OUTPUT (Languages Detected):
{phase1_output}

PHASE 2 OUTPUT (Build Systems Detected):
{phase2_output}

PHASE 3 OUTPUT (Architecture Classification):
{phase3_output}

YOUR TASK:
1. Use the `define_exploration_scope` tool to analyze the repository structure
2. The tool will identify source, test, build, and config directories
3. Interpret the tool results to define exploration scope and strategy
4. Provide structured output with priority directories and skip lists

CRITICAL RULES:
- Use the `define_exploration_scope` tool to analyze the repository
- All conclusions must be backed by evidence from the tool
- Focus only on exploration scope definition - this is your single goal
- Consider the architecture type and build systems when defining scope

OUTPUT FORMAT:
{{
  "exploration_scope": {{
    "source_directories": ["src", "lib", "core"],
    "test_directories": ["tests", "test", "spec"],
    "build_directories": ["build", "dist", "target"],
    "config_directories": ["config", "scripts", "tools"],
    "priority_exploration": ["src", "tests"],
    "skip_directories": ["build", ".git", "node_modules"]
  }},
  "entry_points": {{
    "main_files": ["src/main.cpp", "src/main.py"],
    "config_files": ["CMakeLists.txt", "package.json"],
    "build_files": ["CMakeLists.txt", "Makefile"]
  }},
  "exploration_strategy": {{
    "phase_5_focus": "source_structure",
    "phase_6_focus": "test_structure",
    "phase_7_focus": "build_analysis",
    "phase_8_focus": "artifact_discovery"
  }},
  "confidence_verification": {{
    "scope_defined": true,
    "entry_points_identified": true,
    "ready_for_phase_5": true
  }}
}}

Remember: Your single goal is exploration scope definition. Use the tool and provide evidence-based results.
"""
        
        try:
            result = await self.agent.run(prompt)
            return self._parse_json_response(result)
        except Exception as e:
            self.logger.error(f"Phase 4 execution failed: {e}")
            raise
