#!/usr/bin/env python3
"""
Phase 8: RIG Assembly Agent V4

Assemble final RIG with validation.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class RIGAssemblyAgentV4(BaseLLMAgentV4):
    """Phase 8: RIG Assembly Agent - Assemble final RIG with validation."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "RIGAssembly")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any], test_structure: Dict[str, Any], build_analysis: Dict[str, Any], artifact_analysis: Dict[str, Any], classified_components: Dict[str, Any], relationships: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RIG assembly analysis."""
        self.logger.info("Phase 8: RIG Assembly...")
        
        prompt = f"""
You are a RIG Assembly Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Assemble final RIG with validation.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}
TEST STRUCTURE: {json.dumps(test_structure, indent=2)}
BUILD ANALYSIS: {json.dumps(build_analysis, indent=2)}
ARTIFACT ANALYSIS: {json.dumps(artifact_analysis, indent=2)}
CLASSIFIED COMPONENTS: {json.dumps(classified_components, indent=2)}
RELATIONSHIPS: {json.dumps(relationships, indent=2)}

TASK: Assemble the final RIG from all previous phase results.

ANALYSIS STEPS:
1. Integrate all previous phase results into a comprehensive RIG
2. Validate RIG structure and completeness
3. Ensure all components have proper evidence
4. Validate all relationships and dependencies
5. Generate final RIG with comprehensive validation

CRITICAL RULES:
- Integrate all previous phase results comprehensively
- Validate RIG structure and completeness
- Ensure all components have proper evidence
- Validate all relationships and dependencies
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"
- NEVER guess, speculate, or make assumptions about unknown information
- If validation metrics cannot be determined, use "unknown" instead of guessing
- If confidence levels cannot be calculated, use "unknown" instead of guessing

OUTPUT FORMAT:
```json
{{
  "rig_assembly": {{
    "repository_info": {{
      "name": "repository_name",
      "root_path": "{self.repository_path}",
      "build_directory": "build",
      "output_directory": "output",
      "configure_command": "cmake .",
      "build_command": "cmake --build .",
      "install_command": "cmake --install .",
      "test_command": "ctest"
    }},
    "build_system_info": {{
      "name": "CMake",
      "version": "3.10+",
      "build_type": "Debug"
    }},
    "components": [
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
    ],
    "relationships": [
      {{
        "source": "main_app",
        "target": "utils_lib",
        "type": "link_dependency",
        "evidence": [
          {{
            "file": "CMakeLists.txt",
            "lines": "L5-L5",
            "content": "target_link_libraries(main_app utils_lib)",
            "reason": "CMake links main_app to utils_lib"
          }}
        ]
      }}
    ],
    "validation": {{
      "completeness": 0.95,
      "evidence_quality": 0.90,
      "relationship_accuracy": 0.85,
      "overall_confidence": 0.90
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

Use the available tools directly to validate the final RIG assembly:
- Use `read_text` to access previous phase results
- Use `validate_path_safety` to check path safety
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 8 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 8 failed: {e}")
            raise
