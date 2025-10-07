#!/usr/bin/env python3
"""
Phase 6: Component Classification Agent V4

Classify all discovered entities into RIG types.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v7 import BaseLLMAgentV7


class ComponentClassificationAgentV7(BaseLLMAgentV7):
    """Phase 6: Component Classification Agent - Classify all discovered entities into RIG types."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "ComponentClassification")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any], test_structure: Dict[str, Any], build_analysis: Dict[str, Any], artifact_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute component classification analysis."""
        self.logger.info("Phase 6: Component Classification...")
        
        prompt = f"""
You are a Component Classification Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Classify all discovered entities into RIG types.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}
TEST STRUCTURE: {json.dumps(test_structure, indent=2)}
BUILD ANALYSIS: {json.dumps(build_analysis, indent=2)}
ARTIFACT ANALYSIS: {json.dumps(artifact_analysis, indent=2)}

TASK: Classify all discovered entities into RIG component types.

ANALYSIS STEPS:
1. Classify all discovered entities into RIG component types
2. Determine component types (executable, library, test, utility, etc.)
3. Analyze runtime requirements and dependencies
4. Integrate evidence from all previous phases
5. Validate component classifications against RIG schema

CRITICAL RULES:
- Use all previous phase results for comprehensive classification
- Provide detailed evidence for each component
- Validate component types against RIG schema
- Map dependencies and relationships
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"
- NEVER guess, speculate, or make assumptions about unknown information
- If a component type cannot be determined, use "unknown" instead of guessing
- If a programming language cannot be identified, use "unknown" instead of guessing
- If runtime requirements cannot be determined, use "unknown" instead of guessing

OUTPUT FORMAT:
```json
{{
  "classified_components": [
    {{
      "name": "main_app",
      "type": "executable",
      "programming_language": "C++",
      "runtime": "native",
      "source_files": ["src/main/main.cpp"],
      "output_path": "build/main_app.exe",
      "evidence": [
        {{
          "file": "CMakeLists.txt",
          "lines": "L5-L5",
          "content": "add_executable(main_app src/main/main.cpp)",
          "reason": "CMake defines executable target"
        }}
      ],
      "dependencies": ["utils_lib"],
      "test_relationship": "test_main_app"
    }}
  ]
}}
```

CRITICAL JSON FORMATTING RULES:
- Output MUST be valid JSON - no comments allowed
- Do NOT use // or /* */ comments in JSON
- Do NOT add explanatory text outside the JSON structure
- If you need to explain something, put it in a "reason" or "description" field
- Ensure all strings are properly quoted
- Ensure all brackets and braces are properly balanced

Use the available tools directly to analyze components:
- Use `read_text` to analyze source files
- Use `list_dir` to explore component directories
- Use `validate_path_safety` to check path safety
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 6 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 6 failed: {e}")
            raise
