#!/usr/bin/env python3
"""
Phase 2: Source Structure Discovery Agent V4

Comprehensive source directory and component discovery.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class SourceStructureDiscoveryAgentV4(BaseLLMAgentV4):
    """Phase 2: Source Structure Discovery Agent - Comprehensive source directory and component discovery."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "SourceStructureDiscovery")
    
    async def execute_phase(self, repository_overview: Dict[str, Any]) -> Dict[str, Any]:
        """Execute source structure discovery analysis."""
        self.logger.info("Phase 2: Source Structure Discovery...")
        
        prompt = f"""
You are a Source Structure Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Comprehensive source directory and component discovery.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}

TASK: Analyze source directories and identify potential components.

ANALYSIS STEPS:
1. Map all source directories and their contents
2. Identify potential components from source structure
3. Determine programming languages from file extensions and content
4. Find modules, packages, and logical groupings
5. Identify potential dependencies from import/include statements

CRITICAL RULES:
- Focus on source directories identified in Phase 1
- Analyze file extensions and content for language detection
- Identify potential components from source structure
- Map import/include statements for dependency hints
- Use evidence-based approach - only report what you can verify

OUTPUT FORMAT:
```json
{{
  "source_structure": {{
    "source_directories": [
      {{
        "path": "src/main",
        "language": "C++",
        "components": ["main_app", "utils_lib"],
        "files": ["main.cpp", "utils.cpp", "utils.h"],
        "dependencies": ["boost", "opencv"]
      }}
    ],
    "language_analysis": {{
      "primary_language": "C++",
      "secondary_languages": ["Python", "Java"],
      "language_distribution": {{
        "C++": 0.7,
        "Python": 0.2,
        "Java": 0.1
      }}
    }},
    "component_hints": [
      {{
        "name": "main_app",
        "type": "executable",
        "source_files": ["src/main/main.cpp"],
        "language": "C++"
      }}
    ]
  }}
}}
```

Use the delegate_ops tool to explore source directories.
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 2 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 2 failed: {e}")
            raise
