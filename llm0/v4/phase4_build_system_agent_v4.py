#!/usr/bin/env python3
"""
Phase 4: Build System Analysis Agent V4

Build configuration and target analysis.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class BuildSystemAnalysisAgentV4(BaseLLMAgentV4):
    """Phase 4: Build System Analysis Agent - Build configuration and target analysis."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "BuildSystemAnalysis")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any], test_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Execute build system analysis."""
        self.logger.info("Phase 4: Build System Analysis...")
        
        prompt = f"""
You are a Build System Analysis Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Build configuration and target analysis.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}
TEST STRUCTURE: {json.dumps(test_structure, indent=2)}

TASK: Analyze build system configuration and targets.

ANALYSIS STEPS:
1. Analyze build system configuration files
2. Identify all build targets (executables, libraries, tests)
3. Map build dependencies between targets
4. Discover build options, flags, and configurations
5. Determine build outputs and artifacts

CRITICAL RULES:
- Analyze build system configuration files in detail
- Map all build targets and their dependencies
- Identify build options and configurations
- Determine build outputs and artifacts
- Use evidence-based approach - only report what you can verify

OUTPUT FORMAT:
```json
{{
  "build_analysis": {{
    "build_targets": [
      {{
        "name": "main_app",
        "type": "executable",
        "source_files": ["src/main/main.cpp"],
        "dependencies": ["utils_lib"],
        "output_path": "build/main_app",
        "build_options": ["-O2", "-Wall"]
      }}
    ],
    "build_dependencies": [
      {{
        "source": "main_app",
        "target": "utils_lib",
        "type": "link_dependency"
      }}
    ],
    "build_configuration": {{
      "build_type": "Debug|Release",
      "compiler": "gcc|clang|msvc",
      "flags": ["-std=c++17", "-Wall"]
    }}
  }}
}}
```

Use the delegate_ops tool to analyze build system files.
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 4 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 4 failed: {e}")
            raise
