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
        
        # Reset context to prevent context explosion
        self._reset_context()
        
        prompt = f"""
You are a Source Structure Discovery Agent for the Repository Intelligence Graph (RIG) system.

MISSION: Comprehensive source directory and component discovery.

REPOSITORY: {self.repository_path}
REPOSITORY OVERVIEW: {json.dumps(repository_overview, indent=2)}

TASK: Analyze source directories and identify potential components.

MANDATORY SOURCE DIRECTORIES TO EXPLORE (from Phase 1):
You MUST explore ALL source directories identified in Phase 1. Do not skip any.

ANALYSIS STEPS:
1. Map all source directories and their contents
2. Identify potential components from source structure
3. Determine programming languages from file extensions and content
4. Find modules, packages, and logical groupings
5. Identify potential dependencies from import/include statements

CRITICAL RULES:
- MANDATORY: Explore ALL source directories from Phase 1 - do not skip any
- MANDATORY: Read build configuration files in each directory to understand build structure                                                                     
- MANDATORY: Use glob patterns to efficiently filter files by type
- Analyze file extensions and content for language detection
- Identify potential components from source structure
- Map import/include statements for dependency hints
- Use evidence-based approach - only report what you can verify
- VALIDATION: After exploring each directory, confirm you've read its build configuration files                                                                 
- If you cannot determine something with evidence, mark it as "unknown" or "not_determined"                                                                     
- NEVER guess, speculate, or make assumptions about unknown information
- If a component type cannot be determined, use "unknown" instead of guessing
- If a programming language cannot be identified, use "unknown" instead of guessing

SECURITY RULES (CRITICAL):
- NEVER access files or directories outside the repository root
- ONLY use relative paths from the repository root
- NEVER use absolute paths or paths that go outside the repository
- If you need to access a file, use relative paths like "src/main.cpp" not absolute paths
- Stay within the repository boundaries at all times
- If you're unsure about a path, use 'list_dir' to check what's available first
- Use 'validate_path' tool to check if a path is safe before accessing it
- Use 'get_repository_root' to understand the repository boundaries

    TOOL CALL OPTIMIZATION RULES (CRITICAL - MAX 50 REQUESTS):
    - Use SHORT, SIMPLE tool calls to avoid JSON parsing errors
    - Use relative paths instead of absolute paths when possible
    - Break complex operations into multiple simple steps
    - Use basic commands like 'ls' instead of complex operations
    - Keep tool call arguments under 200 characters total
    - Use simple directory names, avoid very long paths
    - For large repositories: explore ONE directory at a time
    - MANDATORY: Use 'list_dir' with glob patterns like "*.cpp", "*.py", "*.java", "*.go"
    - MANDATORY: Use 'read_file' to read build configuration files in each directory
    - Avoid complex command combinations in single tool calls
    - If a path is too long, use 'cd' first, then 'ls' in the target directory
    - CRITICAL: You have a MAXIMUM of 50 requests total - use them efficiently
    - CRITICAL: Prioritize the most important directories first
    - CRITICAL: Use batch operations when possible (e.g., list multiple file types in one call)

CONTEXT MANAGEMENT RULES:
- Focus on ONE directory at a time - do not accumulate context from multiple directories
- After exploring a directory, move to the next one and forget the previous context
- Use 'cd' to change to target directory, then explore only that directory
- Do not try to explore multiple directories simultaneously
- Keep your exploration focused and sequential

    SYSTEMATIC EXPLORATION STRATEGY (OPTIMIZED FOR 50 REQUEST LIMIT):
    - STEP 1: Start with the first source directory from Phase 1
    - STEP 2: Use 'list_dir' to see the directory contents
    - STEP 3: Use 'list_dir' with glob patterns to filter files by type
    - STEP 4: Use 'read_file' to read build configuration files in each directory
    - STEP 5: Move to the next source directory from Phase 1
    - STEP 6: Repeat steps 2-5 for ALL source directories
    - VALIDATION: Ensure you've explored ALL directories listed in Phase 1
    - CRITICAL: If you approach 40 requests, prioritize the most important directories
    - CRITICAL: Use batch operations to maximize efficiency
    - CRITICAL: Focus on directories with build configuration files first

PATH DISCOVERY STRATEGY:
- NEVER assume directory structure - always discover first
- Start with the root directory and list its contents
- Only explore directories that actually exist
- Use 'list_dir' to see what's available before trying to access subdirectories
- If a path doesn't exist, check the parent directory to see what's actually there
- Do not make assumptions about common directory names like 'src', 'lib', 'include'

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
        "dependencies": ["boost", "opencv"],
        "build_evidence": "Build configuration lines 5-10: add_executable(main_app main.cpp)",
        "exploration_complete": true
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
    ],
    "exploration_summary": {{
      "total_directories_explored": 7,
      "directories_with_build_config": 5,
      "directories_without_build_config": 2,
      "all_phase1_directories_covered": true
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

Use the available tools directly to explore source directories:
- Use `list_dir` to explore directories
- Use `read_text` to read files
- Use `validate_path_safety` to check path safety
- Use `get_repository_root` to understand boundaries
"""
        
        try:
            result = await self._execute_with_retry(prompt)
            self.logger.info("SUCCESS: Phase 2 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase 2 failed: {e}")
            raise
