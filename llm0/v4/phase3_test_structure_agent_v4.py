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
1. Identify testing frameworks (CTest, JUnit, pytest, Jest, Mocha, etc.)
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
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"
- NEVER guess, speculate, or make assumptions about unknown information
- If a test framework cannot be identified, use "unknown" instead of guessing
- If test targets cannot be determined, use "unknown" instead of guessing

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
      }},
      {{
        "name": "JUnit",
        "version": "5.x",
        "config_files": ["pom.xml", "build.gradle"],
        "test_directories": ["src/test/java"]
      }},
      {{
        "name": "pytest",
        "version": "7.x",
        "config_files": ["pytest.ini", "pyproject.toml"],
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
      "test_command": "ctest|mvn test|npm test|pytest",
      "test_timeout": "300",
      "parallel_tests": true
    }}
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

Use the available tools directly to explore test directories:
- Use `list_dir` to explore test directories
- Use `read_text` to read test configuration files
- Use `validate_path_safety` to check path safety
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 3 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 3 failed: {e}")
            raise
