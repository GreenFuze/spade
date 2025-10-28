#!/usr/bin/env python3
"""
Phase 1: Repository Overview Agent V7

High-level repository structure analysis and build system identification.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v7 import BaseLLMAgentV7
from .phase1_tools import Phase1Tools


class RepositoryOverviewAgentV7(BaseLLMAgentV7):
    """Phase 1: Repository Overview Agent - High-level structure and build system identification."""
    
    def __init__(self, repository_path: Path):
        # Initialize Phase 1 specific tools first
        self.phase1_tools = Phase1Tools(repository_path)
        
        # Call parent constructor with tools
        super().__init__(repository_path, "RepositoryOverview")
        
        # Recreate agent with Phase 1 tools included
        from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
        from agentkit_gf.tools.fs import FileTools
        from agentkit_gf.tools.os import ProcessTools
        
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools, self.phase1_tools],
            builtin_enums=[],
            temperature=0,
            max_tool_retries=1,
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        # Debug: Check if tools are properly exposed
        self.logger.info(f"Phase1Tools methods: {[method for method in dir(self.phase1_tools) if not method.startswith('_')]}")
        self.logger.info(f"explore_repository_signals available: {hasattr(self.phase1_tools, 'explore_repository_signals')}")
    
    async def execute_phase(self) -> Dict[str, Any]:
        """Execute repository overview analysis."""
        self.logger.info("Phase 1: Repository Overview Analysis...")
        
        prompt = f"""
You are a Repository Overview Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Perform high-level repository structure analysis and build system identification.

REPOSITORY: {self.repository_path}

TASK: Analyze the repository structure and identify build systems.

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

OUTPUT FORMAT:
```json
{{
  "repository_overview": {{
    "name": "repository_name",
    "type": "application|library|framework|tool",
    "primary_language": "C++|Java|Python|JavaScript|Go|etc",
    "detected_languages": ["C++", "Java", "Python"],
    "language_percentages": {{"C++": 60.0, "Java": 40.0}},
    "multi_language": true,
    "build_systems": ["cmake", "maven", "npm"],
    "directory_structure": {{
      "source_dirs": ["src", "lib", "core"],
      "test_dirs": ["tests", "test", "spec"],
      "build_dirs": ["build", "dist", "target"],
      "config_dirs": ["config", "scripts", "tools"]
    }},
    "entry_points": ["CMakeLists.txt", "package.json", "pom.xml"],
    "exploration_scope": {{
      "priority_dirs": ["src", "tests"],
      "skip_dirs": ["build", "node_modules", ".git"],
      "deep_exploration": ["src", "tests"]
    }},
    "notes": "Additional observations about the repository (e.g., JNI components, multi-language nature, special frameworks)"
  }}
}}
```

CRITICAL JSON FORMATTING RULES:
- Output MUST be valid JSON - no comments allowed
- Do NOT use // or /* */ comments in JSON
- Do NOT add explanatory text outside the JSON structure
- If you need to explain something, put it in a "reason" or "description" field
- Ensure all strings are properly quoted
- Ensure all brackets and braces are properly balanced

CRITICAL: You MUST use the explore_repository_signals tool for this analysis.

TOOL USAGE INSTRUCTIONS:
- MANDATORY: Start by calling explore_repository_signals() to analyze the repository
- This tool will detect languages, build systems, and define exploration scope
- You can customize parameters like exploration_paths, language_focus, content_depth, confidence_threshold
- Example: explore_repository_signals(exploration_paths=["."], language_focus=["C++", "Java"], content_depth="deep", confidence_threshold=0.95)
- DO NOT use basic file tools (list_dir, read_text) - use the specialized tool instead

CRITICAL: USE THE TOOL RESULTS IN YOUR OUTPUT:
- Use the "detected_languages" from the tool results
- Use the "language_percentages" from the tool results  
- Use the "multi_language" flag from the tool results
- If multi_language is true, mention this in the notes field
- If you detect JNI (Java Native Interface) components, mention this in the notes field
- Always base your output on the tool results, not assumptions
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 1 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 1 failed: {e}")
            raise
