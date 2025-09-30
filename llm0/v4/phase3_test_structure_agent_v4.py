#!/usr/bin/env python3
"""
Phase 3: Test Structure Discovery Agent V4

Test framework and test directory discovery.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class TestStructureDiscoveryAgentV4(BaseLLMAgentV4):
    """Phase 3: Test Structure Discovery Agent - Test framework and test directory discovery."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "TestStructureDiscovery")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test structure discovery analysis."""
        self.logger.info("Phase 3: Test Structure Discovery...")
        
        prompt = f"""
You are a Test Structure Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Test framework and test directory discovery.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}

TASK: Analyze test frameworks and test directory structure.

ANALYSIS STEPS:
1. Identify testing frameworks (CTest, JUnit, pytest, etc.)
2. Map test directory structure and organization
3. Analyze test configuration files and settings
4. Identify what components are tested
5. Discover test execution patterns and commands

CRITICAL RULES:
- Focus on test directories identified in Phase 1
- Analyze test configuration files for framework detection
- Map test files to their target components
- Identify test execution patterns and commands
- Use evidence-based approach - only report what you can verify

OUTPUT FORMAT:
```json
{{
  "test_structure": {{
    "test_frameworks": [
      {{
        "name": "CTest",
        "version": "3.10+",
        "config_files": ["CMakeLists.txt"],
        "test_directories": ["tests", "test"]
      }}
    ],
    "test_organization": {{
      "test_directories": [
        {{
          "path": "tests/unit",
          "framework": "CTest",
          "test_files": ["test_main.cpp", "test_utils.cpp"],
          "targets": ["main_app", "utils_lib"]
        }}
      ]
    }},
    "test_configuration": {{
      "test_command": "ctest",
      "test_timeout": "300",
      "parallel_tests": true
    }}
  }}
}}
```

Use the delegate_ops tool to explore test directories and configurations.
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 3 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 3 failed: {e}")
            raise
