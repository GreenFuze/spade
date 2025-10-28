"""
Phase 3: Artifact Discovery Agent

This agent identifies and classifies all artifacts that will be built by the
detected build systems, without assuming anything has been built yet.

The agent uses smart filtering tools to extract relevant content from build
configuration files and then uses LLM reasoning to determine artifacts.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools

from .base_agent_v7 import BaseLLMAgentV7
from .phase3_artifact_tools import Phase3ArtifactTools


class ArtifactDiscoveryAgentV7(BaseLLMAgentV7):
    """
    Phase 3 Agent: Artifact Discovery
    
    Goal: Identify and classify all artifacts that will be built by the detected build systems
    """
    
    def __init__(self, repository_path: Path):
        super().__init__(repository_path, "ArtifactDiscoveryAgentV7", max_retries=1)
        self.phase3_tools = Phase3ArtifactTools(repository_path)
        
        # Initialize the LLM agent with tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.phase3_tools, FileTools(root_dir=repository_path)],
            builtin_enums=[],
            temperature=0,
            max_tool_retries=1,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the artifact discovery agent."""
        return """
You are an Artifact Discovery Agent (Phase 3) for the Repository Intelligence Graph (RIG) system.

MISSION: Identify and classify all artifacts that will be built by the detected build systems.

CRITICAL PRINCIPLES:
- Do NOT assume anything has been built yet
- Use your knowledge of build systems to determine what artifacts will be created
- Extract relevant content from build configuration files using smart filtering
- All conclusions must be backed by evidence from build configurations

TOOL USAGE:
1. Use `analyze_build_configurations()` with search configurations containing file patterns and content regexes
2. Use `query_build_system()` to execute build system queries if needed
3. Use `read_text()` to read specific files if needed

SEARCH CONFIGURATION STRATEGY:
The `analyze_build_configurations` tool takes a list of search configurations. Each configuration should contain:
- "patterns": List of file patterns to search (e.g., ["*.cmake", "CMakeLists.txt", "pom.xml", "build.gradle"])
- "content_regexes": List of regex patterns to match within files

Example patterns for different build systems:
- CMake: patterns=["CMakeLists.txt", "*.cmake"], regexes=["add_executable\\(.*\\)", "add_library\\(.*\\)"]
- Maven: patterns=["pom.xml"], regexes=["<artifactId>.*</artifactId>", "<packaging>.*</packaging>"]
- Gradle: patterns=["build.gradle", "*.gradle"], regexes=["application\\s*\\{", "jar\\s*\\{"]
- npm: patterns=["package.json"], regexes=["\"main\"\\s*:", "\"bin\"\\s*:"]
- Cargo: patterns=["Cargo.toml"], regexes=["\\[\\[bin\\]\\]", "\\[lib\\]"]

ARTIFACT CLASSIFICATION:
- Executables: Binary programs, scripts, applications
- Libraries: Static, dynamic, shared libraries
- JVM Artifacts: JARs, class files, modules
- Language-Specific: Go binaries, Rust crates, Python packages
- Build Artifacts: Generated files, intermediate outputs

OUTPUT FORMAT:
{
  "artifact_discovery": {
    "build_system_artifacts": {
      "cmake": {
        "executables": [
          {
            "name": "executable_name",
            "source_files": ["src/main.cpp"],
            "evidence": "add_executable(executable_name src/main.cpp)",
            "confidence": 0.95
          }
        ],
        "libraries": [
          {
            "name": "library_name",
            "type": "static|dynamic|shared",
            "source_files": ["src/lib.cpp"],
            "evidence": "add_library(library_name STATIC src/lib.cpp)",
            "confidence": 0.95
          }
        ]
      }
    },
    "artifact_summary": {
      "total_artifacts": 5,
      "executables": 2,
      "libraries": 3,
      "build_systems_analyzed": ["cmake"]
    },
    "confidence_scores": {
      "overall_confidence": 0.95,
      "build_system_confidence": {
        "cmake": 0.95
      }
    },
    "evidence_summary": {
      "files_analyzed": ["CMakeLists.txt"],
      "patterns_found": ["add_executable", "add_library"],
      "extraction_strategy_used": "cmake_patterns"
    }
  }
}

CRITICAL: USE THE TOOL RESULTS IN YOUR OUTPUT:
- Base your artifact discovery on the extracted build configuration content
- Use the evidence from the tools to support your conclusions
- If confidence is low, request more specific content extraction
- Always provide evidence for each discovered artifact
"""
    
    async def execute_phase(self, phase1_output: Dict[str, Any], phase2_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Phase 3: Artifact Discovery
        
        Args:
            phase1_output: Output from Phase 1 (repository overview)
            phase2_output: Output from Phase 2 (build system detection)
            
        Returns:
            Dict containing artifact discovery results
        """
        try:
            self.logger.info("Starting Phase 3: Artifact Discovery")
        
            # Create the prompt with phase inputs
            prompt = f"""
You are an Artifact Discovery Agent (Phase 3). Your single goal is to identify and classify all artifacts that will be built by the detected build systems.

PHASE 1 OUTPUT (Repository Overview): {json.dumps(phase1_output, indent=2)}
PHASE 2 OUTPUT (Build System Detection): {json.dumps(phase2_output, indent=2)}

YOUR TASK:
1. Based on the detected build systems, determine which configuration files to analyze
2. Use the `analyze_build_configurations` tool with the correct parameter format
3. Analyze the matched lines to identify artifacts from the build configuration files
4. Classify each artifact by type (executable, library, etc.)
5. Provide evidence for each discovered artifact

CRITICAL: The `analyze_build_configurations` tool takes a single parameter called `search_configs` which is a list of search configurations.

Each search configuration must contain:
- "patterns": List of file patterns to search (e.g., ["CMakeLists.txt", "*.cmake"])
- "content_regexes": List of regex patterns to match within files (e.g., ["add_executable\\(.*\\)", "add_library\\(.*\\)"])

CORRECT USAGE EXAMPLE:
```python
analyze_build_configurations([
    {
        "patterns": ["CMakeLists.txt", "*.cmake"],
        "content_regexes": ["add_executable\\(.*\\)", "add_library\\(.*\\)", "target_sources\\(.*\\)"]
    }
])
```

IMPORTANT: If the build system supports macros or functions, include patterns to search for them as well, as they can internally create modules or artifacts.

Start by calling the tool with the correct parameter format.
"""
            
            # Execute the agent
            result = await self._execute_with_retry(prompt)
            
            # Parse the JSON response
            artifact_discovery = result
            
            self.logger.info("Phase 3 completed successfully")
            return artifact_discovery
            
        except Exception as e:
            self.logger.error(f"Error in Phase 3 execution: {e}")
            return {
                "artifact_discovery": {
                    "error": str(e),
                    "build_system_artifacts": {},
                    "artifact_summary": {
                        "total_artifacts": 0,
                        "executables": 0,
                        "libraries": 0,
                        "build_systems_analyzed": []
                    },
                    "confidence_scores": {
                        "overall_confidence": 0.0
                    },
                    "evidence_summary": {
                        "files_analyzed": [],
                        "patterns_found": [],
                        "extraction_strategy_used": "error"
                    }
                }
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from the LLM, handling comments and extra text."""
        try:
            # Remove comments and extra text
            lines = response.split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') and not in_json:
                    in_json = True
                    json_lines.append(line)
                elif in_json:
                    if line.endswith('}') and line.count('}') >= line.count('{'):
                        json_lines.append(line)
                        break
                    else:
                        # Remove // comments
                        if '//' in line:
                            line = line[:line.index('//')]
                        json_lines.append(line)
            
            json_str = '\n'.join(json_lines)
            
            # Try to fix common JSON issues
            # Fix missing commas between array elements
            json_str = re.sub(r'}\s*{', '}, {', json_str)
            # Fix missing commas between object properties
            json_str = re.sub(r'"\s*\n\s*"', '",\n    "', json_str)
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.error(f"Response was: {response}")
            
            # Try to extract the artifact discovery part manually
            try:
                # Look for the artifact_discovery section
                if '"artifact_discovery"' in response:
                    start = response.find('"artifact_discovery"')
                    # Find the matching closing brace
                    brace_count = 0
                    end = start
                    for i, char in enumerate(response[start:], start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    artifact_section = response[start:end]
                    # Try to parse just this section
                    artifact_data = json.loads('{' + artifact_section + '}')
                    return artifact_data
            except:
                pass
            
            return {
                "artifact_discovery": {
                    "error": f"JSON parsing failed: {e}",
                    "build_system_artifacts": {},
                    "artifact_summary": {
                        "total_artifacts": 0,
                        "executables": 0,
                        "libraries": 0,
                        "build_systems_analyzed": []
                    },
                    "confidence_scores": {
                        "overall_confidence": 0.0
                    },
                    "evidence_summary": {
                        "files_analyzed": [],
                        "patterns_found": [],
                        "extraction_strategy_used": "parse_error"
                    }
                }
            }