#!/usr/bin/env python3
"""
Phase 5: Artifact Discovery Agent V4

Build output files and artifacts discovery.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_agent_v4 import BaseLLMAgentV4


class ArtifactDiscoveryAgentV4(BaseLLMAgentV4):
    """Phase 5: Artifact Discovery Agent - Build output files and artifacts discovery."""
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "ArtifactDiscovery")
    
    async def execute_phase(self, repository_overview: Dict[str, Any], source_structure: Dict[str, Any], test_structure: Dict[str, Any], build_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute artifact discovery analysis."""
        self.logger.info("Phase 5: Artifact Discovery...")
        
        prompt = f"""
You are an Artifact Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Build output files and artifacts discovery.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}
SOURCE STRUCTURE: {json.dumps(source_structure, indent=2)}
TEST STRUCTURE: {json.dumps(test_structure, indent=2)}
BUILD ANALYSIS: {json.dumps(build_analysis, indent=2)}

TASK: Discover build output files and artifacts.

ANALYSIS STEPS:
1. Identify build output files and artifacts
2. Map build targets to their output files
3. Classify artifacts by type (executables, libraries, packages)
4. Discover installation targets and procedures
5. Identify distribution and packaging artifacts

CRITICAL RULES:
- Focus on build output directories
- Map build targets to their actual output files
- Classify artifacts by type and purpose
- Identify installation and distribution artifacts
- Use evidence-based approach - only report what you can verify

OUTPUT FORMAT:
```json
{{
  "artifact_analysis": {{
    "build_artifacts": [
      {{
        "name": "main_app",
        "type": "executable",
        "output_file": "build/main_app.exe",
        "size": "1024KB",
        "dependencies": ["msvcrt.dll"]
      }}
    ],
    "library_artifacts": [
      {{
        "name": "utils_lib",
        "type": "static_library",
        "output_file": "build/utils_lib.lib",
        "size": "256KB"
      }}
    ],
    "package_artifacts": [
      {{
        "name": "java_hello_lib",
        "type": "jar",
        "output_file": "build/java_hello_lib-1.0.0.jar",
        "version": "1.0.0"
      }}
    ]
  }}
}}
```

Use the delegate_ops tool to discover build artifacts.
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 5 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 5 failed: {e}")
            raise
