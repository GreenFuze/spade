#!/usr/bin/env python3
"""
Phase 1: Repository Overview Agent V4

High-level repository structure analysis and build system identification.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class RepositoryOverviewAgentV4(BaseLLMAgentV4):
    """Phase 1: Repository Overview Agent - High-level structure and build system identification."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "RepositoryOverview")
    
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

OUTPUT FORMAT:
```json
{{
  "repository_overview": {{
    "name": "repository_name",
    "type": "application|library|framework|tool",
    "primary_language": "C++|Java|Python|JavaScript|Go|etc",
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
      "deep_exploration": ["src/main", "tests/unit"]
    }}
  }}
}}
```

Use the delegate_ops tool to explore the repository structure.
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 1 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 1 failed: {e}")
            raise
