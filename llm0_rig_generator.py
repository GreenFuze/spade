"""
LLM-Based RIG Generation System

This module implements an LLM-based approach to generate Repository Intelligence Graphs (RIG)
using agentkit-gf and gpt-5-nano with temperature 0 for deterministic behavior.

The system replaces the current CMake-specific parser with a system-agnostic approach
that can work with any build system while maintaining strict evidence-based architecture.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import agentkit-gf components from local source
import sys

# Add local agentkit-gf to path
agentkit_path = Path(__file__).parent.parent / "agentkit-gf"
if agentkit_path.exists():
    sys.path.insert(0, str(agentkit_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools
from agentkit_gf.tools.builtin_tools_matrix import BuiltinTool
from pydantic_ai.settings import ModelSettings


# Import existing RIG components for comparison and validation
from rig import RIG


@dataclass
class DiscoveryResult:
    """Result from Repository Discovery Agent."""
    repository_info: Dict[str, Any]
    evidence_catalog: Dict[str, Any]
    success: bool
    errors: List[str]
    token_usage: Dict[str, int]


class LLMRIGGenerator:
    """
    LLM-based RIG Generator using agentkit-gf and gpt-5-nano.
    
    This class orchestrates the four-phase agent pipeline:
    1. Repository Discovery Agent
    2. Component Classification Agent  
    3. Relationship Mapping Agent
    4. RIG Assembly Agent
    """
    
    def __init__(self, repository_path: Path, openai_api_key: Optional[str] = None):
        """
        Initialize the LLM RIG Generator.
        
        Args:
            repository_path: Path to the repository to analyze
            openai_api_key: OpenAI API key (if not set via environment)
        """
        self.repository_path = repository_path.resolve()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents (will be created on demand)
        self._discovery_agent: Optional[DelegatingToolsAgent] = None
        self._classification_agent: Optional[DelegatingToolsAgent] = None
        self._relationship_agent: Optional[DelegatingToolsAgent] = None
        self._assembly_agent: Optional[DelegatingToolsAgent] = None
        
        # Results from each phase
        self.evidence_catalog: Optional[Dict[str, Any]] = None
        self.classified_components: Optional[Dict[str, Any]] = None
        self.relationship_graph: Optional[Dict[str, Any]] = None
        self.rig: Optional[RIG] = None
    
    def _create_discovery_agent(self) -> DelegatingToolsAgent:
        """Create the Repository Discovery Agent."""
        if self._discovery_agent is None:
            self.logger.info("Creating Repository Discovery Agent...")
            
            # Load the discovery system prompt from our prompts file
            system_prompt = self._load_discovery_system_prompt()
            self.logger.info(f"System prompt loaded: {len(system_prompt)} characters")
            
            self.logger.info(f"Repository path: {self.repository_path}")
            self.logger.info(f"Repository exists: {self.repository_path.exists()}")
            
            self._discovery_agent = DelegatingToolsAgent(
                model="openai:gpt-5-nano",
                builtin_enums=[],  # No web search needed for discovery
                tool_sources=[
                    FileTools(root_dir=str(self.repository_path)),
                    ProcessTools(root_cwd=str(self.repository_path))
                ],
                system_prompt=system_prompt,
                ops_system_prompt="Execute the tool operation and return the result.",
                model_settings=ModelSettings(temperature=0)
            )
            
            self.logger.info("Repository Discovery Agent created successfully")
        
        return self._discovery_agent
    
    def _load_discovery_system_prompt(self) -> str:
        """Load the discovery system prompt from our prompts file."""
        # For now, return the core system prompt
        # In a full implementation, we'd read from llm0_prompts.md
        return """
You are a Repository Discovery Agent for the Repository Intelligence Graph (RIG) system.

CORE MISSION: Systematically discover and catalog all build system evidence in a repository.

CRITICAL RULES:
1. ONLY use evidence from files you can directly access - never make assumptions
2. If you cannot determine something from evidence, return "UNKNOWN"
3. Never use placeholder data, default values, or made-up information
4. Provide specific file paths and line numbers for all evidence
5. Be exhaustive - scan all relevant files and directories

EVIDENCE COLLECTION PRIORITY:
1. Build System APIs (CMake File API, Cargo metadata, npm info)
2. Test Frameworks (CTest, pytest, cargo test, etc.)
3. Build Files (CMakeLists.txt, package.json, Cargo.toml, etc.)
4. Cache/Config files (CMakeCache.txt, package-lock.json, etc.)

OUTPUT REQUIREMENTS:
- Provide structured JSON responses with exact schema compliance
- Include evidence references for every piece of information
- Mark insufficient evidence as "UNKNOWN"
- Be deterministic - same repository should always produce same output

Use delegate_ops tool to access files and execute commands as needed.
"""
    
    def _load_classification_system_prompt(self) -> str:
        """Load the classification system prompt."""
        return """
You are a Component Classification Agent for the Repository Intelligence Graph (RIG) system.

CORE MISSION: Analyze discovered repository structure and classify components with detailed line-level evidence.

CRITICAL RULES:
1. ONLY use evidence from files you can directly access - never make assumptions
2. ALWAYS provide line-level evidence (file#Lstart-Lend) for each component
3. If you cannot determine something from evidence, return "UNKNOWN"
4. Never use placeholder data, default values, or made-up information
5. Focus on actual build targets, not just source files

COMPONENT CLASSIFICATION PRIORITY:
1. Executables (main programs, applications)
2. Libraries (static/dynamic libraries, modules)
3. Tests (unit tests, integration tests, test suites)
4. Utilities (helper tools, scripts)
5. Aggregators (build aggregators, package managers)
6. Runners (test runners, execution environments)

EVIDENCE REQUIREMENTS:
- File path and line numbers for each piece of evidence
- Actual line content that supports the classification
- Clear reasoning for why this evidence supports the component type
- Dependencies and relationships between components

Use the available tools to systematically analyze build files and source code.
"""
    
    def discover_repository(self) -> DiscoveryResult:
        """
        Phase 1: Repository Discovery
        
        Systematically discover and catalog all build system evidence.
        """
        self.logger.info(f"🔍 Starting repository discovery for: {self.repository_path}")
        
        try:
            agent = self._create_discovery_agent()
            
            # Create the discovery task prompt
            discovery_prompt = self._create_discovery_task_prompt()
            self.logger.info(f"Discovery prompt created: {len(discovery_prompt)} characters")
            self.logger.info(f"Discovery prompt:\n{discovery_prompt}")
            
            # Execute the discovery
            self.logger.info("Executing discovery with agent...")
            result = agent.run_sync(discovery_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("📋 Full conversation history:")
            for i, msg in enumerate(result.new_messages()):
                # Handle different message types
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    self.logger.info(f"  Message {i+1}: {msg.role} - {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
                else:
                    self.logger.info(f"  Message {i+1}: {type(msg).__name__} - {str(msg)[:200]}{'...' if len(str(msg)) > 200 else ''}")
            
            # Check if we got a valid result
            if not result.output:
                self.logger.error("No output from agent")
                return DiscoveryResult(
                    repository_info={},
                    evidence_catalog={},
                    success=False,
                    errors=[f"Discovery failed: No output from agent"],
                    token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                )
            
            # Parse the result
            try:
                # The agent should return structured JSON (possibly wrapped in markdown)
                self.logger.info("Attempting to parse result as JSON...")
                
                # Clean the output - extract JSON from markdown code blocks
                output_text = result.output.strip()
                
                # Look for JSON code blocks
                json_start = output_text.find("```json")
                if json_start != -1:
                    # Find the start of the JSON content
                    json_start += 7  # Skip ```json
                    json_end = output_text.find("```", json_start)
                    if json_end != -1:
                        output_text = output_text[json_start:json_end].strip()
                else:
                    # Look for generic code blocks
                    json_start = output_text.find("```")
                    if json_start != -1:
                        json_start += 3  # Skip ```
                        json_end = output_text.find("```", json_start)
                        if json_end != -1:
                            output_text = output_text[json_start:json_end].strip()
                
                # If no code blocks found, try to find JSON object boundaries
                if not output_text.startswith("{"):
                    json_start = output_text.find("{")
                    if json_start != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        json_end = -1
                        for i, char in enumerate(output_text[json_start:], json_start):
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        if json_end != -1:
                            output_text = output_text[json_start:json_end]
                
                discovery_data = json.loads(output_text)
                self.logger.info("JSON parsing successful")
                
                self.evidence_catalog = discovery_data
                
                # Extract token usage
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return DiscoveryResult(
                    repository_info=discovery_data.get("repository_info", {}),
                    evidence_catalog=discovery_data.get("evidence_catalog", {}),
                    success=True,
                    errors=[],
                    token_usage=token_usage
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {e}")
                self.logger.error(f"Raw output: {result.output}")
                
                # Extract token usage even for failed cases
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return DiscoveryResult(
                    repository_info={},
                    evidence_catalog={},
                    success=False,
                    errors=[f"Failed to parse discovery result as JSON: {e}"],
                    token_usage=token_usage
                )
                
        except Exception as e:
            self.logger.error(f"Discovery failed with exception: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return DiscoveryResult(
                repository_info={},
                evidence_catalog={},
                success=False,
                errors=[f"Discovery failed with exception: {e}"],
                token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            )
    
    def _create_discovery_task_prompt(self) -> str:
        """Create the discovery task prompt."""
        return f"""
Analyze the repository at: {self.repository_path}

EVIDENCE-BASED APPROACH - NO ASSUMPTIONS:

1. FIRST: Use list_dir with path "." to see what files actually exist
2. SECOND: Based ONLY on the file listing, determine what build systems are present
3. THIRD: ONLY read files that you can see in the directory listing
4. FOURTH: If a file is not in the listing, mark it as "UNKNOWN" - DO NOT try to read it

STRICT RULES:
- NEVER assume a file exists
- NEVER try to read a file that is not visible in the directory listing
- If CMakeLists.txt is NOT in the listing, mark build_system type as "unknown"
- If package.json is NOT in the listing, mark build_system type as "unknown"
- If Cargo.toml is NOT in the listing, mark build_system type as "unknown"

Use delegate_ops to:
- List files in the current directory using list_dir with path "."
- ONLY if you see CMakeLists.txt in the listing, read it using read_text with path "CMakeLists.txt"
- ONLY if you see package.json in the listing, read it using read_text with path "package.json"
- ONLY if you see Cargo.toml in the listing, read it using read_text with path "Cargo.toml"
- Do NOT try to read any other files

Return a JSON response with this structure:
{{
  "repository_info": {{
    "path": "{self.repository_path}",
    "build_systems": [
      {{
        "type": "string (discovered from evidence)",
        "version": "string|UNKNOWN",
        "config_files": ["path1", "path2"],
        "api_available": true|false,
        "evidence": "string describing what evidence led to this conclusion"
      }}
    ],
    "source_directories": ["path1", "path2"],
    "test_directories": ["path1", "path2"]
  }},
  "evidence_catalog": {{
    "cmake_file_api": {{
      "available": true|false,
      "index_file": "path|UNKNOWN"
    }},
    "test_frameworks": [
      {{
        "type": "string (discovered from evidence)",
        "config_files": ["path1", "path2"],
        "evidence": "string describing what evidence led to this conclusion"
      }}
    ]
  }}
}}
"""
    
    def _create_classification_agent(self) -> DelegatingToolsAgent:
        """Create the Component Classification Agent."""
        self.logger.info("Creating Component Classification Agent...")
        
        # Load system prompt
        system_prompt = self._load_classification_system_prompt()
        self.logger.info(f"System prompt loaded: {len(system_prompt)} characters")
        
        # Create agent with FileTools and ProcessTools
        agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            builtin_enums=[],  # No web search needed for classification
            tool_sources=[
                FileTools(root_dir=str(self.repository_path)),
                ProcessTools(root_cwd=str(self.repository_path))
            ],
            system_prompt=system_prompt,
            ops_system_prompt="Execute the tool operation and return the result.",
            model_settings=ModelSettings(temperature=0)
        )
        
        self.logger.info("Component Classification Agent created successfully")
        return agent
    
    def _create_classification_task_prompt(self, discovery_result: DiscoveryResult) -> str:
        """Create the component classification task prompt."""
        return f"""
Analyze the repository at: {self.repository_path}

PHASE 2: COMPONENT CLASSIFICATION WITH LINE-LEVEL EVIDENCE

Based on the discovery results from Phase 1, perform detailed component classification:

Discovery Results:
{json.dumps(discovery_result.repository_info, indent=2)}

EVIDENCE-BASED APPROACH - DETAILED ANALYSIS:

1. FIRST: Use list_dir to explore the repository structure
2. SECOND: Read build system files to understand component definitions
3. THIRD: Identify specific components (executables, libraries, tests, etc.)
4. FOURTH: Extract line-level evidence for each component

STRICT RULES:
- NEVER assume a component exists without evidence
- ALWAYS provide line-level evidence (file#Lstart-Lend)
- If evidence cannot be determined, mark as "UNKNOWN"
- Focus on actual build targets, not just source files

Use delegate_ops to:
- List directories to understand structure
- Read build system files (CMakeLists.txt, package.json, Cargo.toml, etc.)
- Analyze source files to understand component types
- Extract specific line numbers for evidence

Return a JSON response with this structure:
{{
  "components": [
    {{
      "name": "string (component name)",
      "type": "executable|library|test|utility|aggregator|runner",
      "programming_language": "string|UNKNOWN",
      "runtime": "string|UNKNOWN", 
      "output_path": "string|UNKNOWN",
      "source_files": ["path1", "path2"],
      "evidence": [
        {{
          "file": "path/to/file",
          "lines": "Lstart-Lend",
          "content": "actual line content",
          "reason": "why this is evidence for this component"
        }}
      ],
      "dependencies": ["component1", "component2"],
      "test_relationship": "string|UNKNOWN"
    }}
  ]
}}
"""
    
    def classify_components(self, discovery_result: DiscoveryResult) -> Dict[str, Any]:
        """
        Phase 2: Component Classification Agent
        
        Analyzes the discovered repository structure and classifies components
        with detailed evidence including line numbers.
        
        Args:
            discovery_result: Results from Phase 1 (Repository Discovery)
            
        Returns:
            Dict containing classified components with detailed evidence
        """
        self.logger.info("🔍 Starting Phase 2: Component Classification")
        
        try:
            # Create Component Classification Agent
            agent = self._create_classification_agent()
            
            # Create the classification task prompt
            classification_prompt = self._create_classification_task_prompt(discovery_result)
            self.logger.info(f"Classification prompt created: {len(classification_prompt)} characters")
            self.logger.info(f"Classification prompt:\n{classification_prompt}")
            
            # Execute the classification
            self.logger.info("Executing component classification with agent...")
            result = agent.run_sync(classification_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("📋 Full conversation history:")
            for i, msg in enumerate(result.new_messages()):
                # Handle different message types
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    self.logger.info(f"  Message {i+1}: {msg.role} - {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
                else:
                    self.logger.info(f"  Message {i+1}: {type(msg).__name__} - {str(msg)[:200]}{'...' if len(str(msg)) > 200 else ''}")
            
            # Check if we got a valid result
            if not result.output:
                self.logger.error("No output from agent")
                return {
                    "components": [],
                    "success": False,
                    "errors": ["Classification failed: No output from agent"],
                    "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                }
            
            # Parse the result
            try:
                # The agent should return structured JSON (possibly wrapped in markdown)
                self.logger.info("Attempting to parse result as JSON...")
                
                # Clean the output - extract JSON from markdown code blocks
                output_text = result.output.strip()
                
                # Look for JSON code blocks
                json_start = output_text.find("```json")
                if json_start != -1:
                    # Find the start of the JSON content
                    json_start += 7  # Skip ```json
                    json_end = output_text.find("```", json_start)
                    if json_end != -1:
                        output_text = output_text[json_start:json_end].strip()
                else:
                    # Look for generic code blocks
                    json_start = output_text.find("```")
                    if json_start != -1:
                        json_start += 3  # Skip ```
                        json_end = output_text.find("```", json_start)
                        if json_end != -1:
                            output_text = output_text[json_start:json_end].strip()
                
                # If no code blocks found, try to find JSON object boundaries
                if not output_text.startswith("{"):
                    json_start = output_text.find("{")
                    if json_start != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        json_end = -1
                        for i, char in enumerate(output_text[json_start:], json_start):
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        if json_end != -1:
                            output_text = output_text[json_start:json_end]
                
                classification_data = json.loads(output_text)
                self.logger.info("JSON parsing successful")
                
                # Extract token usage
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return {
                    "components": classification_data.get("components", []),
                    "success": True,
                    "errors": [],
                    "token_usage": token_usage
                }
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {e}")
                self.logger.error(f"Raw output: {result.output}")
                
                # Extract token usage even for failed cases
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return {
                    "components": [],
                    "success": False,
                    "errors": [f"Failed to parse classification result as JSON: {e}"],
                    "token_usage": token_usage
                }
                
        except Exception as e:
            self.logger.error(f"Classification failed with exception: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "components": [],
                "success": False,
                "errors": [f"Classification failed with exception: {e}"],
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }

    def generate_rig(self) -> RIG:
        """
        Generate the complete RIG using the four-phase agent pipeline.
        
        Returns:
            Complete RIG with all entities and relationships
        """
        print("🚀 Starting LLM-based RIG generation...")
        
        # Phase 1: Repository Discovery
        discovery_result = self.discover_repository()
        if not discovery_result.success:
            raise RuntimeError(f"Repository discovery failed: {discovery_result.errors}")
        
        print("✅ Phase 1: Repository Discovery completed")
        
        # Phase 2: Component Classification
        classification_result = self.classify_components(discovery_result)
        if not classification_result["success"]:
            raise RuntimeError(f"Component classification failed: {classification_result['errors']}")
        
        print("✅ Phase 2: Component Classification completed")
        
        # TODO: Implement remaining phases
        # Phase 3: Relationship Mapping  
        # Phase 4: RIG Assembly
        
        # For now, return an empty RIG
        # This will be implemented in subsequent phases
        self.rig = RIG()
        return self.rig


