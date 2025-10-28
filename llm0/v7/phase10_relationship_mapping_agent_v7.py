#!/usr/bin/env python3
"""
Phase 7: Relationship Mapping Agent V4

Map dependencies and relationships between entities.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v7 import BaseLLMAgentV7


class RelationshipMappingAgentV7(BaseLLMAgentV7):
    """Phase 7: Relationship Mapping Agent - Map dependencies and relationships between entities."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "RelationshipMapping")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any], test_structure: Dict[str, Any], build_analysis: Dict[str, Any], artifact_analysis: Dict[str, Any], classified_components: Dict[str, Any]) -> Dict[str, Any]:
        """Execute relationship mapping analysis."""
        self.logger.info("Phase 7: Relationship Mapping...")
        
        prompt = f"""
You are a Relationship Mapping Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Map dependencies and relationships between entities.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}
TEST STRUCTURE: {json.dumps(test_structure, indent=2)}
BUILD ANALYSIS: {json.dumps(build_analysis, indent=2)}
ARTIFACT ANALYSIS: {json.dumps(artifact_analysis, indent=2)}
CLASSIFIED COMPONENTS: {json.dumps(classified_components, indent=2)}

TASK: Map dependencies and relationships between all entities.

ANALYSIS STEPS:
1. Map dependencies between components
2. Identify test relationships (what tests what)
3. Map build dependencies and build order
4. Identify external package dependencies
5. Map runtime dependencies and requirements

CRITICAL RULES:
- Use all previous phase results for comprehensive relationship mapping
- Map all types of dependencies (build, runtime, test)
- Identify external package dependencies
- Map test relationships accurately
- Use evidence-based approach - only report what you can verify
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"
- NEVER guess, speculate, or make assumptions about unknown information
- If a dependency type cannot be determined, use "unknown" instead of guessing
- If external package versions cannot be identified, use "unknown" instead of guessing
- If test relationships cannot be determined, use "unknown" instead of guessing

OUTPUT FORMAT:
```json
{{
  "relationships": {{
    "component_dependencies": [
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
    "test_relationships": [
      {{
        "test": "test_main_app",
        "target": "main_app",
        "type": "unit_test",
        "evidence": [
          {{
            "file": "tests/test_main.cpp",
            "lines": "L1-L1",
            "content": "#include \"../src/main/main.cpp\"",
            "reason": "Test includes main component"
          }}
        ]
      }}
    ],
    "external_dependencies": [
      {{
        "component": "main_app",
        "package": "boost",
        "type": "external_library",
        "version": "1.70+",
        "evidence": [
          {{
            "file": "CMakeLists.txt",
            "lines": "L3-L3",
            "content": "find_package(Boost REQUIRED)",
            "reason": "CMake finds Boost package"
          }}
        ]
      }}
    ]
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

Use the available tools directly to analyze relationships:
- Use `read_text` to analyze source files for dependencies
- Use `list_dir` to explore component directories
- Use `validate_path_safety` to check path safety
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 7 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 7 failed: {e}")
            raise
