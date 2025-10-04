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
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"                                                                     
- NEVER guess, speculate, or make assumptions about unknown information
- If an artifact type cannot be determined, use "unknown" instead of guessing
- If artifact size cannot be determined, use "unknown" instead of guessing

HANDLING MISSING BUILD ARTIFACTS:
- ALWAYS use "list_dir" to check if build directories exist BEFORE trying to access them
- If build directories don't exist, report "no build artifacts found"
- If build artifacts don't exist, report "build artifacts not available"
- Do NOT try to access non-existent build paths repeatedly
- If no build artifacts are found, return empty arrays for build_artifacts, library_artifacts, package_artifacts

MANDATORY EXPLORATION STRATEGY:
1. FIRST: Use "list_dir" to check what build directories exist
2. ONLY THEN: Explore existing build directories
3. If no build directories exist, report "no build artifacts found"
4. If build directories exist but are empty, report "build artifacts not available"

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

CRITICAL JSON FORMATTING RULES:
- Output MUST be valid JSON - no comments allowed
- Do NOT use // or /* */ comments in JSON
- Do NOT add explanatory text outside the JSON structure
- If you need to explain something, put it in a "reason" or "description" field
- Ensure all strings are properly quoted
- Ensure all brackets and braces are properly balanced

Use the available tools directly to discover build artifacts:
- Use `list_dir` to explore build output directories
- Use `stat` to get file information
- Use `validate_path_safety` to check path safety
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 5 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 5 failed: {e}")
            raise
