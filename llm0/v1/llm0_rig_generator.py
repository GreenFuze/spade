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
from pydantic_ai.settings import ModelSettings

# Import RIG data models
from rig import RIG
from schemas import (
    Component, Evidence, RepositoryInfo, BuildSystemInfo,
    ComponentType, Runtime
)


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
        
        # Request tracking
        self.max_requests_per_phase = 100
        self.current_phase_requests = 0
    
    def _check_request_limit(self) -> None:
        """Check if we've exceeded the request limit for the current phase."""
        if self.current_phase_requests >= self.max_requests_per_phase:
            raise Exception(f"Request limit exceeded: {self.current_phase_requests}/{self.max_requests_per_phase} requests used in this phase")
    
    def _increment_request_counter(self) -> None:
        """Increment the request counter for the current phase."""
        self.current_phase_requests += 1
        self.logger.info(f"Request count: {self.current_phase_requests}/{self.max_requests_per_phase}")
    
    def _reset_request_counter(self) -> None:
        """Reset the request counter for a new phase."""
        self.current_phase_requests = 0
        self.logger.info(f"Starting new phase with request limit: {self.max_requests_per_phase}")
    
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
                model_settings=ModelSettings(temperature=0),
                real_time_log_user=True,
                real_time_log_agent=True
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
    
    def _load_relationship_system_prompt(self) -> str:
        """Load the relationship mapping system prompt."""
        return """
You are a Relationship Mapping Agent for the Repository Intelligence Graph (RIG) system.

CORE MISSION: Analyze classified components and establish their relationships, dependencies, and interactions.

CRITICAL RULES:
1. ONLY use evidence from files you can directly access - never make assumptions
2. ALWAYS provide line-level evidence (file#Lstart-Lend) for each relationship
3. If you cannot determine a relationship from evidence, return "UNKNOWN"
4. Never use placeholder data, default values, or made-up information
5. Focus on actual build system relationships, not just source code imports

RELATIONSHIP MAPPING PRIORITY:
1. Build Dependencies (target_link_libraries, add_dependencies)
2. Test Relationships (add_test, test commands)
3. Source Dependencies (include statements, imports)
4. External Dependencies (find_package, external libraries)
5. Runtime Dependencies (shared libraries, plugins)

EVIDENCE REQUIREMENTS:
- File path and line numbers for each relationship
- Actual line content that establishes the relationship
- Clear reasoning for why this evidence supports the relationship type
- Relationship direction (source -> target)
- Relationship strength (direct, transitive, optional)

Use the available tools to systematically analyze build files and source code for relationship evidence.
"""
    
    def _load_assembly_system_prompt(self) -> str:
        """Load the RIG assembly system prompt."""
        return """
You are a RIG Assembly Agent for the Repository Intelligence Graph (RIG) system.

CORE MISSION: Assemble all discovered data into a complete, validated RIG structure.

CRITICAL RULES:
1. ONLY use data from the previous phases - never make assumptions
2. ALWAYS validate data against the RIG schema requirements
3. If data cannot be determined from previous phases, mark as "UNKNOWN"
4. Never use placeholder data, default values, or made-up information
5. Ensure all evidence is properly structured and validated

RIG ASSEMBLY PRIORITY:
1. Repository Information (from Phase 1)
2. Build System Information (from Phase 1)
3. Component Assembly (from Phase 2)
4. Relationship Assembly (from Phase 3)
5. Evidence Validation and Structuring
6. Final RIG Validation

ASSEMBLY REQUIREMENTS:
- Convert all discovered data into proper Pydantic models
- Validate all evidence structures
- Ensure proper component type mapping
- Create complete relationship mappings
- Validate against RIG schema

Use the available tools to access any additional files needed for validation.
"""
    
    def discover_repository(self) -> DiscoveryResult:
        """
        Phase 1: Repository Discovery
        
        Systematically discover and catalog all build system evidence.
        """
        self.logger.info(f"INFO: Starting repository discovery for: {self.repository_path}")
        
        try:
            agent = self._create_discovery_agent()
            
            # Create the discovery task prompt
            discovery_prompt = self._create_discovery_task_prompt()
            self.logger.info(f"Discovery prompt created: {len(discovery_prompt)} characters")
            self.logger.info(f"Discovery prompt:\n{discovery_prompt}")
            
            # Execute the discovery
            self.logger.info("Executing discovery with agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = agent.run_sync(discovery_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("DETAILS: Full conversation history:")
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
                discovery_data = self._parse_agent_json_response(result.output, "Discovery")
                
                # Validate the result
                validation_passed, validation_errors = self._validate_phase_result("Discovery", discovery_data)
                if not validation_passed:
                    return DiscoveryResult(
                        repository_info={},
                        evidence_catalog={},
                        success=False,
                        errors=validation_errors,
                        token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                    )
                
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

CRITICAL: FOLLOW THE BUILD SYSTEM'S NATURAL GRAPH:
1. ALWAYS start with list_dir to see what files exist
2. Identify build system configuration files from the directory listing
3. Read build system files to understand the project structure
4. Follow build system references to discover build targets and dependencies
5. NEVER access files in build/, dist/, target/, node_modules/, Testing/, or other build artifact directories

BUILD SYSTEM GRAPH FOLLOWING RULES:
- Let the build system guide your exploration
- Only read files that are referenced by the build system
- Follow build system dependency chains naturally
- Do NOT explore directories unless the build system references them
- Focus on build targets and their dependencies, not arbitrary file scanning

ABSOLUTE REQUIREMENT: You MUST first list the directory contents, then ONLY read files that are explicitly shown in that listing. If you try to read a file that is not in the directory listing, the system will fail.

CRITICAL WARNING: The LLM has been trying to read package.json even when it's not in the directory listing. This is a VIOLATION of the evidence-based approach. You MUST NOT read any file unless it is explicitly shown in the directory listing. If package.json is not in the listing, DO NOT try to read it.

CRITICAL FILE EXISTENCE CHECK:
- Before reading ANY file, you MUST first list the directory it's in using list_dir
- If a file is not in the directory listing, DO NOT try to read it
- Even if a file is referenced in CMakeLists.txt, you MUST verify it exists before reading
- NEVER assume a file exists based on build system references alone

Use delegate_ops to:
- FIRST: List files in the current directory using list_dir with path "."
- THEN: Based on the directory listing, ONLY read files that are explicitly shown:
  - ONLY if you see CMakeLists.txt in the listing, read it using read_text with path "CMakeLists.txt"
  - ONLY if you see package.json in the listing, read it using read_text with path "package.json"
  - ONLY if you see Cargo.toml in the listing, read it using read_text with path "Cargo.toml"
- NEVER try to read any other files
- NEVER assume a file exists - if it's not in the directory listing, DO NOT read it
- NEVER try to read package.json if it's not explicitly shown in the directory listing

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
            model_settings=ModelSettings(temperature=0),
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        self.logger.info("Component Classification Agent created successfully")
        return agent
    
    def _create_relationship_agent(self) -> DelegatingToolsAgent:
        """Create the Relationship Mapping Agent."""
        self.logger.info("Creating Relationship Mapping Agent...")
        
        # Load system prompt
        system_prompt = self._load_relationship_system_prompt()
        self.logger.info(f"System prompt loaded: {len(system_prompt)} characters")
        
        # Create agent with FileTools and ProcessTools
        agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            builtin_enums=[],  # No web search needed for relationship mapping
            tool_sources=[
                FileTools(root_dir=str(self.repository_path)),
                ProcessTools(root_cwd=str(self.repository_path))
            ],
            system_prompt=system_prompt,
            ops_system_prompt="Execute the tool operation and return the result.",
            model_settings=ModelSettings(temperature=0),
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        self.logger.info("Relationship Mapping Agent created successfully")
        return agent
    
    def _create_assembly_agent(self) -> DelegatingToolsAgent:
        """Create the RIG Assembly Agent."""
        self.logger.info("Creating RIG Assembly Agent...")
        
        # Load system prompt
        system_prompt = self._load_assembly_system_prompt()
        self.logger.info(f"System prompt loaded: {len(system_prompt)} characters")
        
        # Create agent with FileTools and ProcessTools
        agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            builtin_enums=[],  # No web search needed for assembly
            tool_sources=[
                FileTools(root_dir=str(self.repository_path)),
                ProcessTools(root_cwd=str(self.repository_path))
            ],
            system_prompt=system_prompt,
            ops_system_prompt="Execute the tool operation and return the result.",
            model_settings=ModelSettings(temperature=0),
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        self.logger.info("RIG Assembly Agent created successfully")
        return agent
    
    def _create_ultra_restrictive_classification_prompt(self, discovery_result: DiscoveryResult) -> str:
        """
        Create an ultra-restrictive classification prompt that forces the LLM to be extremely focused.
        
        Args:
            discovery_result: Results from the discovery phase
            
        Returns:
            Ultra-restrictive classification prompt
        """
        discovery_data = discovery_result.data
        
        return f"""
Analyze the repository at: {self.repository_path}

ULTRA-RESTRICTIVE COMPONENT CLASSIFICATION - MAXIMUM EFFICIENCY

Based on the discovery results from Phase 1, perform MINIMAL component classification:

Discovery Results:
{json.dumps(discovery_data, indent=2)}

ULTRA-RESTRICTIVE RULES - VIOLATION WILL CAUSE FAILURE:
1. ONLY read the main CMakeLists.txt file - NO other files
2. ONLY analyze the build targets defined in CMakeLists.txt
3. NEVER explore subdirectories unless absolutely necessary
4. NEVER read source files unless they are explicitly referenced in CMakeLists.txt
5. MAXIMUM 5 file reads total - if you exceed this, you will fail

ABSOLUTE REQUIREMENT: You MUST first list the directory contents, then ONLY read files that are explicitly shown in that listing.

CRITICAL FILE EXISTENCE CHECK:
- Before reading ANY file, you MUST first list the directory it's in using list_dir
- If a file is not in the directory listing, DO NOT try to read it
- Even if a file is referenced in CMakeLists.txt, you MUST verify it exists before reading
- NEVER assume a file exists based on build system references alone

COMPONENT TYPE DEFINITIONS:
- executable: Entity that can be executed directly by the operating system, VM, or interpreter as a standalone program
- dynamic library: Entity that is loaded dynamically during runtime and can be shared across multiple processes
- static library: Entity that is linked and embedded into executables during compile time, becoming part of the final binary
- package library: Entity that is a packaged library (JAR, wheel, npm package, etc.) that is loaded by a runtime environment

ULTRA-RESTRICTIVE STRATEGY:
- Start with the main CMakeLists.txt to understand the overall structure
- Identify ONLY the main components from the build system
- Focus on the most important components first
- Do NOT explore every subdirectory unless absolutely necessary
- Use the discovery results to guide your focus

Use delegate_ops to:
- List the main directory to understand structure
- Read the main build system file (CMakeLists.txt) to understand component definitions
- Focus on the most important components only
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

    def _create_classification_task_prompt(self, discovery_result: DiscoveryResult) -> str:
        """Create the component classification task prompt."""
        return f"""
Analyze the repository at: {self.repository_path}

PHASE 2: COMPONENT CLASSIFICATION WITH LINE-LEVEL EVIDENCE

Based on the discovery results from Phase 1, perform detailed component classification:

Discovery Results:
{json.dumps(discovery_result.repository_info, indent=2)}

EVIDENCE-BASED APPROACH - BUILD SYSTEM GRAPH FOLLOWING:

CRITICAL: Follow the build system's natural dependency graph:
1. FIRST: Use list_dir with path "." to see what files exist in the repository root
2. SECOND: Identify the main build system configuration file from the directory listing
3. THIRD: Read the main build system file to understand the build structure and targets
4. FOURTH: Follow build system references to find only the files that are actually referenced
5. FIFTH: Analyze only the build targets and components that the build system defines

BUILD SYSTEM GRAPH FOLLOWING RULES:
- Follow the build system's natural dependency chain
- Only read files that are referenced by the build system
- Do NOT explore directories unless the build system references them
- Focus on build targets and their dependencies
- Let the build system guide your exploration, not arbitrary file scanning

ABSOLUTE RULE: NEVER try to read a file unless you have FIRST seen it in a directory listing. If you need to read a file, you MUST first list the directory it's in to confirm it exists.

CRITICAL FILE EXISTENCE CHECK:
- Before reading ANY file, you MUST first list the directory it's in using list_dir
- If a file is not in the directory listing, DO NOT try to read it
- Even if a file is referenced in CMakeLists.txt, you MUST verify it exists before reading
- NEVER assume a file exists based on build system references alone

COMPONENT TYPE DEFINITIONS:
- executable: Entity that can be executed directly by the operating system, VM, or interpreter as a standalone program
- dynamic library: Entity that is loaded dynamically during runtime and can be shared across multiple processes
- static library: Entity that is linked and embedded into executables during compile time, becoming part of the final binary
- package library: Entity that is a packaged library (JAR, wheel, npm package, etc.) that is loaded by a runtime environment

STRICT RULES:
- NEVER assume a component exists without evidence
- ALWAYS provide line-level evidence (file#Lstart-Lend)
- If evidence cannot be determined, mark as "UNKNOWN"
- Focus on actual build targets, not just source files
- NEVER access files in build/, dist/, target/, node_modules/, Testing/, or other build artifact directories
- ONLY analyze source files and configuration files in the repository root and src/ directories
- CRITICAL: ALWAYS use list_dir to see what files exist BEFORE trying to read them
- NEVER try to read a file that you haven't seen in a directory listing
- NEVER try to read Makefile, Makefile.in, configure, or other build system files unless they are explicitly listed in directory listings                                                     
- ONLY read files that are explicitly shown in directory listings
- ALWAYS use the EXACT file paths shown in directory listings - do not guess or assume file locations
- If a file is listed as "src/java/HelloWorld.java" in CMakeLists.txt, you MUST first list the "src/java/" directory to confirm the file exists before trying to read it

EFFICIENCY STRATEGY:
- Start with the main CMakeLists.txt to understand the overall structure
- Identify the main components from the build system
- Focus on the most important components first
- Do NOT explore every subdirectory unless absolutely necessary
- Use the discovery results to guide your focus

Use delegate_ops to:
- List the main directory to understand structure
- Read the main build system file (CMakeLists.txt) to understand component definitions
- Focus on the most important components only
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
    
    def _create_relationship_task_prompt(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any]) -> str:
        """Create the relationship mapping task prompt."""
        return f"""
Analyze the repository at: {self.repository_path}

PHASE 3: RELATIONSHIP MAPPING WITH EVIDENCE

Based on the discovery and classification results from Phases 1 and 2, establish component relationships:

Discovery Results:
{json.dumps(discovery_result.repository_info, indent=2)}

Classification Results:
{json.dumps(classification_result.get("components", []), indent=2)}

EVIDENCE-BASED APPROACH - RELATIONSHIP ANALYSIS:

1. FIRST: Analyze build system files to understand component dependencies
2. SECOND: Examine source files for include/import relationships
3. THIRD: Map test relationships to their target components
4. FOURTH: Identify external dependencies and package relationships

STRICT RULES:
- NEVER assume a relationship exists without evidence
- ALWAYS provide line-level evidence (file#Lstart-Lend) for each relationship
- If evidence cannot be determined, mark as "UNKNOWN"
- Focus on actual build system relationships, not just source code patterns

Use delegate_ops to:
- Read build system files (CMakeLists.txt, package.json, Cargo.toml, etc.)
- Analyze source files for include/import statements
- Examine test configurations and relationships
- Extract specific line numbers for relationship evidence

Return a JSON response with this structure:
{{
  "relationships": [
    {{
      "source": "string (source component name)",
      "target": "string (target component name)",
      "type": "depends_on|tests|includes|links_to|external_dependency",
      "strength": "direct|transitive|optional",
      "evidence": [
        {{
          "file": "path/to/file",
          "lines": "Lstart-Lend",
          "content": "actual line content",
          "reason": "why this is evidence for this relationship"
        }}
      ]
    }}
  ],
  "relationship_graph": {{
    "nodes": [
      {{
        "id": "component_name",
        "type": "executable|library|test|utility|aggregator|runner",
        "label": "component_name"
      }}
    ],
    "edges": [
      {{
        "source": "source_component",
        "target": "target_component",
        "type": "depends_on|tests|includes|links_to|external_dependency",
        "strength": "direct|transitive|optional"
      }}
    ]
  }}
}}
"""
    
    def _create_assembly_task_prompt(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any], relationship_result: Dict[str, Any]) -> str:
        """Create the RIG assembly task prompt."""
        return f"""
Analyze the repository at: {self.repository_path}

PHASE 4: RIG ASSEMBLY WITH VALIDATION

Based on the results from Phases 1-3, assemble the complete RIG structure:

Discovery Results (Phase 1):
{json.dumps(discovery_result.repository_info, indent=2)}

Classification Results (Phase 2):
{json.dumps(classification_result.get("components", []), indent=2)}

Relationship Results (Phase 3):
{json.dumps(relationship_result.get("relationships", []), indent=2)}

EVIDENCE-BASED APPROACH - RIG ASSEMBLY:

1. FIRST: Create RepositoryInfo from discovery results
2. SECOND: Create BuildSystemInfo from discovery results  
3. THIRD: Convert classified components to proper RIG component types
4. FOURTH: Assemble relationships and evidence
5. FIFTH: Validate all data against RIG schema requirements

STRICT RULES:
- ONLY use data from the previous phases - never make assumptions
- Convert all data to proper Pydantic model structures
- Ensure all evidence is properly structured with line numbers
- If data cannot be determined, mark as "UNKNOWN"
- Validate against RIG schema requirements

Use delegate_ops to:
- Access any additional files needed for validation
- Verify component types and relationships
- Ensure proper evidence structuring

Return a JSON response with this structure:
{{
  "repository_info": {{
    "path": "string",
    "name": "string|UNKNOWN",
    "description": "string|UNKNOWN",
    "version": "string|UNKNOWN",
    "license": "string|UNKNOWN",
    "url": "string|UNKNOWN"
  }},
  "build_system_info": {{
    "type": "string",
    "version": "string|UNKNOWN",
    "config_files": ["path1", "path2"],
    "api_available": true|false
  }},
  "components": [
    {{
      "name": "string",
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
  ],
  "relationships": [
    {{
      "source": "string",
      "target": "string", 
      "type": "depends_on|tests|includes|links_to|external_dependency",
      "strength": "direct|transitive|optional",
      "evidence": [
        {{
          "file": "path/to/file",
          "lines": "Lstart-Lend",
          "content": "actual line content",
          "reason": "why this is evidence for this relationship"
        }}
      ]
    }}
  ],
  "validation_status": {{
    "valid": true|false,
    "errors": ["error1", "error2"],
    "warnings": ["warning1", "warning2"]
  }}
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
        self.logger.info("INFO: Starting Phase 2: Component Classification")
        
        try:
            # Create Component Classification Agent
            agent = self._create_classification_agent()
            
            # Create the classification task prompt
            classification_prompt = self._create_classification_task_prompt(discovery_result)
            self.logger.info(f"Classification prompt created: {len(classification_prompt)} characters")
            self.logger.info(f"Classification prompt:\n{classification_prompt}")
            
            # Execute the classification
            self.logger.info("Executing component classification with agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = agent.run_sync(classification_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("DETAILS: Full conversation history:")
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
                classification_data = self._parse_agent_json_response(result.output, "Classification")
                
                # Validate the result
                validation_passed, validation_errors = self._validate_phase_result("Classification", classification_data)
                
                # If validation failed with runtime detection issues, try refinement
                if not validation_passed and any("runtime" in error.lower() for error in validation_errors):
                    self.logger.info("RETRY: Runtime detection validation failed, attempting refinement...")
                    
                    # Create refined prompt with validation feedback
                    refined_prompt = self._create_refined_classification_prompt(classification_prompt, validation_errors)
                    
                    # Re-run classification with refined prompt
                    self.logger.info("RETRY: Re-running classification with validation feedback...")
                    self._check_request_limit()
                    self._increment_request_counter()
                    result = agent.run_sync(refined_prompt)
                    
                    # Parse the refined result
                    try:
                        classification_data = self._parse_agent_json_response(result.output, "Classification")
                        
                        # Validate the refined result
                        validation_passed, validation_errors = self._validate_phase_result("Classification", classification_data)
                        
                        if not validation_passed:
                            self.logger.warning(f"WARNING: Refined classification still has validation issues: {validation_errors}")
                        else:
                            self.logger.info("SUCCESS: Refined classification validation passed")
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Refined classification JSON parsing failed: {e}")
                        return {
                            "components": [],
                            "success": False,
                            "errors": [f"Refined classification JSON parsing failed: {e}"],
                            "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                        }
                
                if not validation_passed:
                    return {
                        "components": [],
                        "success": False,
                        "errors": validation_errors,
                        "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                    }
                
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

    def map_relationships(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 3: Relationship Mapping Agent
        
        Analyzes classified components and establishes their relationships,
        dependencies, and interactions with detailed evidence.
        
        Args:
            discovery_result: Results from Phase 1 (Repository Discovery)
            classification_result: Results from Phase 2 (Component Classification)
            
        Returns:
            Dict containing relationship mappings with detailed evidence
        """
        self.logger.info("INFO: Starting Phase 3: Relationship Mapping")
        
        try:
            # Create Relationship Mapping Agent
            agent = self._create_relationship_agent()
            
            # Create the relationship mapping task prompt
            relationship_prompt = self._create_relationship_task_prompt(discovery_result, classification_result)
            self.logger.info(f"Relationship prompt created: {len(relationship_prompt)} characters")
            self.logger.info(f"Relationship prompt:\n{relationship_prompt}")
            
            # Execute the relationship mapping
            self.logger.info("Executing relationship mapping with agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = agent.run_sync(relationship_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("DETAILS: Full conversation history:")
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
                    "relationships": [],
                    "relationship_graph": {"nodes": [], "edges": []},
                    "success": False,
                    "errors": ["Relationship mapping failed: No output from agent"],
                    "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                }
            
            # Parse the result
            try:
                relationship_data = self._parse_agent_json_response(result.output, "Relationship")
                
                # Validate the result
                validation_passed, validation_errors = self._validate_phase_result("Relationship", relationship_data)
                if not validation_passed:
                    return {
                        "relationships": [],
                        "relationship_graph": {"nodes": [], "edges": []},
                        "success": False,
                        "errors": validation_errors,
                        "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                    }
                
                # Extract token usage
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return {
                    "relationships": relationship_data.get("relationships", []),
                    "relationship_graph": relationship_data.get("relationship_graph", {"nodes": [], "edges": []}),
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
                    "relationships": [],
                    "relationship_graph": {"nodes": [], "edges": []},
                    "success": False,
                    "errors": [f"Failed to parse relationship mapping result as JSON: {e}"],
                    "token_usage": token_usage
                }
                
        except Exception as e:
            self.logger.error(f"Relationship mapping failed with exception: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "relationships": [],
                "relationship_graph": {"nodes": [], "edges": []},
                "success": False,
                "errors": [f"Relationship mapping failed with exception: {e}"],
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }

    def assemble_rig(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any], relationship_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: RIG Assembly Agent
        
        Assembles all data from previous phases into a complete, validated RIG structure.
        
        Args:
            discovery_result: Results from Phase 1 (Repository Discovery)
            classification_result: Results from Phase 2 (Component Classification)
            relationship_result: Results from Phase 3 (Relationship Mapping)
            
        Returns:
            Dict containing the complete assembled RIG data
        """
        self.logger.info("INFO: Starting Phase 4: RIG Assembly")
        
        try:
            # Create RIG Assembly Agent
            agent = self._create_assembly_agent()
            
            # Create the RIG assembly task prompt
            assembly_prompt = self._create_assembly_task_prompt(discovery_result, classification_result, relationship_result)
            self.logger.info(f"Assembly prompt created: {len(assembly_prompt)} characters")
            self.logger.info(f"Assembly prompt:\n{assembly_prompt}")
            
            # Execute the RIG assembly
            self.logger.info("Executing RIG assembly with agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = agent.run_sync(assembly_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            self.logger.info(f"Result output: {result.output}")
            self.logger.info(f"Result usage: {result.usage()}")
            self.logger.info(f"New messages count: {len(result.new_messages())}")
            
            # Log the full conversation for debugging
            self.logger.info("DETAILS: Full conversation history:")
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
                    "repository_info": {},
                    "build_system_info": {},
                    "components": [],
                    "relationships": [],
                    "validation_status": {"valid": False, "errors": ["RIG assembly failed: No output from agent"], "warnings": []},
                    "success": False,
                    "errors": ["RIG assembly failed: No output from agent"],
                    "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                }
            
            # Parse the result
            try:
                assembly_data = self._parse_agent_json_response(result.output, "Assembly")
                
                # Validate the result
                validation_passed, validation_errors = self._validate_phase_result("Assembly", assembly_data)
                if not validation_passed:
                    return {
                        "repository_info": {},
                        "build_system_info": {},
                        "components": [],
                        "relationships": [],
                        "validation_status": {"valid": False, "errors": validation_errors, "warnings": []},
                        "success": False,
                        "errors": validation_errors,
                        "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                    }
                
                # Extract token usage
                usage = result.usage()
                token_usage = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                }
                
                return {
                    "repository_info": assembly_data.get("repository_info", {}),
                    "build_system_info": assembly_data.get("build_system_info", {}),
                    "components": assembly_data.get("components", []),
                    "relationships": assembly_data.get("relationships", []),
                    "validation_status": assembly_data.get("validation_status", {"valid": True, "errors": [], "warnings": []}),
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
                    "repository_info": {},
                    "build_system_info": {},
                    "components": [],
                    "relationships": [],
                    "validation_status": {"valid": False, "errors": [f"Failed to parse RIG assembly result as JSON: {e}"], "warnings": []},
                    "success": False,
                    "errors": [f"Failed to parse RIG assembly result as JSON: {e}"],
                    "token_usage": token_usage
                }
                
        except Exception as e:
            self.logger.error(f"RIG assembly failed with exception: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "repository_info": {},
                "build_system_info": {},
                "components": [],
                "relationships": [],
                "validation_status": {"valid": False, "errors": [f"RIG assembly failed with exception: {e}"], "warnings": []},
                "success": False,
                "errors": [f"RIG assembly failed with exception: {e}"],
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }

    def generate_rig(self) -> RIG:
        """
        Generate the complete RIG using the four-phase agent pipeline.
        
        Returns:
            Complete RIG with all entities and relationships
        """
        print("RUNNING: Starting LLM-based RIG generation...")
        
        # Phase 1: Repository Discovery
        print("INFO: Phase 1: Repository Discovery...")
        self._reset_request_counter()
        discovery_result = self.discover_repository()
        if not discovery_result.success:
            raise RuntimeError(f"Repository discovery failed: {discovery_result.errors}")
        
        print("SUCCESS: Phase 1: Repository Discovery completed")
        print(f"TOKENS: Phase 1 Token Usage: {discovery_result.token_usage['total_tokens']} tokens")
        
        # Phase 2: Component Classification
        print("INFO: Phase 2: Component Classification...")
        self._reset_request_counter()
        classification_result = self.classify_components(discovery_result)
        if not classification_result["success"]:
            raise RuntimeError(f"Component classification failed: {classification_result['errors']}")
        
        print("SUCCESS: Phase 2: Component Classification completed")
        print(f"TOKENS: Phase 2 Token Usage: {classification_result['token_usage']['total_tokens']} tokens")
        
        # Phase 3: Relationship Mapping
        print("INFO: Phase 3: Relationship Mapping...")
        self._reset_request_counter()
        relationship_result = self.map_relationships(discovery_result, classification_result)
        if not relationship_result["success"]:
            raise RuntimeError(f"Relationship mapping failed: {relationship_result['errors']}")
        
        print("SUCCESS: Phase 3: Relationship Mapping completed")
        print(f"TOKENS: Phase 3 Token Usage: {relationship_result['token_usage']['total_tokens']} tokens")
        
        # Phase 4: RIG Assembly
        print("INFO: Phase 4: RIG Assembly...")
        self._reset_request_counter()
        assembly_result = self.assemble_rig(discovery_result, classification_result, relationship_result)
        if not assembly_result["success"]:
            raise RuntimeError(f"RIG assembly failed: {assembly_result['errors']}")
        
        print("SUCCESS: Phase 4: RIG Assembly completed")
        print(f"TOKENS: Phase 4 Token Usage: {assembly_result['token_usage']['total_tokens']} tokens")
        
        # Calculate total token usage
        total_tokens = (
            discovery_result.token_usage['total_tokens'] +
            classification_result['token_usage']['total_tokens'] +
            relationship_result['token_usage']['total_tokens'] +
            assembly_result['token_usage']['total_tokens']
        )
        print(f"TOTAL: Total Token Usage: {total_tokens} tokens")
        
        # Convert assembly_result to actual RIG object
        self.rig = self._convert_assembly_to_rig(assembly_result)
        
        print("PASSED: LLM-based RIG generation completed successfully!")
        return self.rig
    
    def _convert_assembly_to_rig(self, assembly_result: Dict[str, Any]) -> RIG:
        """
        Convert the assembly result to a proper RIG object.
        
        Args:
            assembly_result: The result from Phase 4 RIG Assembly
            
        Returns:
            Complete RIG object with all entities and relationships
        """
        self.logger.info("Converting assembly result to RIG object...")
        
        # Create new RIG instance
        rig = RIG()
        
        # Convert repository info
        repo_info_data = assembly_result.get("repository_info", {})
        if repo_info_data:
            rig.repository_info = RepositoryInfo(
                name=repo_info_data.get("name", "UNKNOWN"),
                root_path=Path(repo_info_data.get("path", "")),
                build_directory=Path("build"),  # Default build directory
                output_directory=Path("output"),  # Default output directory
                configure_command="cmake .",  # Default configure command
                build_command="cmake --build .",  # Default build command
                install_command="cmake --install .",  # Default install command
                test_command="ctest"  # Default test command
            )
        
        # Convert build system info
        build_info_data = assembly_result.get("build_system_info", {})
        if build_info_data:
            rig.build_system_info = BuildSystemInfo(
                name=build_info_data.get("type", "UNKNOWN"),
                version=build_info_data.get("version", "UNKNOWN"),
                build_type="Debug"  # Default build type
            )
        
        # Convert components
        components_data = assembly_result.get("components", [])
        for comp_data in components_data:
            # Convert evidence
            evidence_list = []
            for ev_data in comp_data.get("evidence", []):
                # Create call stack from file and lines
                call_stack = [f"{ev_data.get('file', '')}#{ev_data.get('lines', '')}"]
                evidence = Evidence(
                    id=None,
                    call_stack=call_stack
                )
                evidence_list.append(evidence)
            
            # Determine component type
            comp_type_str = comp_data.get("type", "UNKNOWN")
            if comp_type_str == "executable":
                comp_type = ComponentType.EXECUTABLE
            elif comp_type_str == "library":
                # Check if it's a JAR or other package library
                if comp_data.get("programming_language", "").lower() == "java":
                    comp_type = ComponentType.PACKAGE_LIBRARY
                else:
                    comp_type = ComponentType.STATIC_LIBRARY  # Default to static
            elif comp_type_str == "test":
                comp_type = ComponentType.EXECUTABLE  # Tests are executables
            else:
                comp_type = ComponentType.EXECUTABLE  # Default fallback
            
            # Determine runtime
            runtime_str = comp_data.get("runtime", "UNKNOWN")
            if "C++" in runtime_str or "native" in runtime_str:
                runtime = Runtime.CLANG_C
            elif "JVM" in runtime_str or "Java Virtual Machine" in runtime_str:
                runtime = Runtime.JVM
            elif "Python" in runtime_str:
                runtime = Runtime.PYTHON
            elif "Go" in runtime_str:
                runtime = Runtime.GO
            else:
                runtime = None  # UNKNOWN
            
            # Create component
            component = Component(
                id=None,
                name=comp_data.get("name", ""),
                depends_on=[],  # Will be populated from relationships later
                evidence=evidence_list[0] if evidence_list else Evidence(id=None, call_stack=[]),
                type=comp_type,
                runtime=runtime,
                output=comp_data.get("name", ""),  # Use name as output
                output_path=Path(comp_data.get("output_path", "UNKNOWN")),
                programming_language=comp_data.get("programming_language", "UNKNOWN"),
                source_files=[Path(f) for f in comp_data.get("source_files", [])],
                external_packages=[],
                locations=[],
                test_link_id=None,
                test_link_name=comp_data.get("test_relationship", "UNKNOWN") if comp_data.get("test_relationship") != "UNKNOWN" else None
            )
            rig.components.append(component)
        
        # Convert relationships and populate component dependencies
        relationships_data = assembly_result.get("relationships", [])
        self.logger.info(f"Found {len(relationships_data)} relationships to process")
        
        # Create a map of component names to Component objects for dependency resolution
        component_map = {comp.name: comp for comp in rig.components}
        
        # Process relationships to populate dependencies
        for relationship in relationships_data:
            source_name = relationship.get("source", "")
            target_name = relationship.get("target", "")
            rel_type = relationship.get("type", "")
            
            if source_name in component_map and target_name in component_map:
                source_comp = component_map[source_name]
                target_comp = component_map[target_name]
                
                # Add dependency based on relationship type
                if rel_type == "depends_on" and target_comp not in source_comp.depends_on:
                    source_comp.depends_on.append(target_comp)
                    self.logger.info(f"Added dependency: {source_name} depends on {target_name}")
                elif rel_type == "tests" and target_comp not in source_comp.depends_on:
                    source_comp.depends_on.append(target_comp)
                    self.logger.info(f"Added test dependency: {source_name} tests {target_name}")
        
        self.logger.info(f"Processed {len(relationships_data)} relationships")
        
        # Log validation status
        validation_status = assembly_result.get("validation_status", {})
        if validation_status.get("valid", False):
            self.logger.info("SUCCESS: RIG validation passed")
        else:
            errors = validation_status.get("errors", [])
            warnings = validation_status.get("warnings", [])
            if errors:
                self.logger.warning(f"WARNING: RIG validation errors: {errors}")
            if warnings:
                self.logger.warning(f"WARNING: RIG validation warnings: {warnings}")
        
        self.logger.info(f"RIG conversion completed: {len(rig.components)} components created")
        return rig
    
    def _parse_agent_json_response(self, result_output: str, phase_name: str) -> Dict[str, Any]:
        """
        Parse JSON response from agent, handling markdown code blocks and other formatting.
        
        Args:
            result_output: Raw output from agent
            phase_name: Name of the phase for logging purposes
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            json.JSONDecodeError: If JSON parsing fails
        """
        self.logger.info(f"Attempting to parse {phase_name} result as JSON...")
        
        # Clean the output - extract JSON from markdown code blocks
        output_text = result_output.strip()
        
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
        
        # Remove JavaScript-style comments that might be in the JSON
        import re
        # Remove single-line comments (// comment)
        output_text = re.sub(r'//.*?(?=\n|$)', '', output_text)
        # Remove multi-line comments (/* comment */)
        output_text = re.sub(r'/\*.*?\*/', '', output_text, flags=re.DOTALL)
        
        # Clean up any trailing commas before closing brackets/braces
        output_text = re.sub(r',(\s*[}\]])', r'\1', output_text)
        
        # Parse the JSON
        parsed_data = json.loads(output_text)
        self.logger.info(f"{phase_name} JSON parsing successful")
        return parsed_data
    
    def _validate_phase_result(self, phase_name: str, result_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that the LLM output is "real" and contains expected data.

        Args:
            phase_name: Name of the phase for logging
            result_data: Parsed JSON data from the phase

        Returns:
            Tuple of (validation_passed, validation_errors)
        """
        self.logger.info(f"Validating {phase_name} result...")
        validation_errors = []

        if phase_name == "Discovery":
            # Validate discovery result structure
            required_fields = ["repository_info", "evidence_catalog"]
            for field in required_fields:
                if field not in result_data:
                    error_msg = f"Discovery validation failed: Missing required field '{field}'"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)

            # Validate repository_info structure
            repo_info = result_data.get("repository_info", {})
            if not isinstance(repo_info, dict):
                error_msg = "Discovery validation failed: repository_info is not a dictionary"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)

            # Validate evidence_catalog structure
            evidence_catalog = result_data.get("evidence_catalog", {})
            if not isinstance(evidence_catalog, dict):
                error_msg = "Discovery validation failed: evidence_catalog is not a dictionary"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)

        elif phase_name == "Classification":
            # Validate classification result structure
            if "components" not in result_data:
                error_msg = "Classification validation failed: Missing 'components' field"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)
                return False, validation_errors

            components = result_data.get("components", [])
            if not isinstance(components, list):
                error_msg = "Classification validation failed: components is not a list"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)
                return False, validation_errors

            # Validate each component has required fields
            for i, component in enumerate(components):
                required_fields = ["name", "type", "evidence"]
                for field in required_fields:
                    if field not in component:
                        error_msg = f"Classification validation failed: Component {i} missing '{field}' field"
                        self.logger.error(error_msg)
                        validation_errors.append(error_msg)

                # Validate evidence is a list
                evidence = component.get("evidence", [])
                if not isinstance(evidence, list):
                    error_msg = f"Classification validation failed: Component {i} evidence is not a list"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)

            # Validate runtime detection logic
            for component in components:
                name = component.get("name", "unknown")
                programming_language = component.get("programming_language", "")
                runtime = component.get("runtime", "")
                component_type = component.get("type", "")
                
                # Check if runtime is UNKNOWN when it should be inferred
                # Skip validation for test components that don't have their own source code
                if programming_language and programming_language != "UNKNOWN" and runtime == "UNKNOWN":
                    error_msg = f"Component '{name}' has programming language '{programming_language}' but runtime is UNKNOWN - runtime should be inferred from programming language"
                    self.logger.warning(error_msg)
                    validation_errors.append(error_msg)
                elif component_type == "test" and programming_language == "UNKNOWN" and runtime == "UNKNOWN":
                    # Test components that run other executables don't need their own runtime
                    # This is acceptable for CTest-style tests that just execute other components
                    self.logger.info(f"Test component '{name}' has UNKNOWN programming language and runtime - this is acceptable for test runners")
                    pass

        elif phase_name == "Relationship":
            # Validate relationship result structure
            required_fields = ["relationships", "relationship_graph"]
            for field in required_fields:
                if field not in result_data:
                    error_msg = f"Relationship validation failed: Missing required field '{field}'"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)

            relationships = result_data.get("relationships", [])
            if not isinstance(relationships, list):
                error_msg = "Relationship validation failed: relationships is not a list"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)

            # Validate each relationship has required fields
            for i, relationship in enumerate(relationships):
                required_fields = ["source", "target", "type", "evidence"]
                for field in required_fields:
                    if field not in relationship:
                        error_msg = f"Relationship validation failed: Relationship {i} missing '{field}' field"
                        self.logger.error(error_msg)
                        validation_errors.append(error_msg)

        elif phase_name == "Assembly":
            # Validate assembly result structure
            required_fields = ["repository_info", "build_system_info", "components", "relationships", "validation_status"]
            for field in required_fields:
                if field not in result_data:
                    error_msg = f"Assembly validation failed: Missing required field '{field}'"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)

            # Validate validation_status
            validation_status = result_data.get("validation_status", {})
            if not isinstance(validation_status, dict):
                error_msg = "Assembly validation failed: validation_status is not a dictionary"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)

            if "valid" not in validation_status:
                error_msg = "Assembly validation failed: validation_status missing 'valid' field"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)

        if validation_errors:
            self.logger.warning(f"WARNING: {phase_name} validation found {len(validation_errors)} issues")
            return False, validation_errors
        else:
            self.logger.info(f"SUCCESS: {phase_name} validation passed")
            return True, []

    def _create_refined_classification_prompt(self, original_prompt: str, validation_errors: List[str]) -> str:
        """
        Create a refined classification prompt with validation feedback.

        Args:
            original_prompt: The original classification prompt
            validation_errors: List of validation errors from the previous attempt

        Returns:
            Refined prompt with validation feedback
        """
        validation_feedback = "\n".join([f"- {error}" for error in validation_errors])
        
        refined_prompt = f"""
{original_prompt}

VALIDATION FEEDBACK FROM PREVIOUS ATTEMPT:
The following logical inconsistencies were detected in the previous classification:

{validation_feedback}

CRITICAL RUNTIME INFERENCE GUIDANCE:
Based on the validation feedback, you MUST infer the runtime environment from the programming language:

- For C++ components: Use "native runtime" or "C++ runtime" 
- For Java components: Use "JVM" or "Java Virtual Machine"
- For Python components: Use "Python runtime"
- For Go components: Use "Go runtime"
- For .NET components: Use ".NET runtime"

NEVER leave runtime as "UNKNOWN" when you have identified a programming language. The runtime is the environment that executes the compiled or interpreted code.

Please reconsider your analysis based on this feedback. Pay special attention to the relationship between programming languages and their corresponding runtime environments. Use the evidence you have to make logical connections between language types and runtime requirements.
"""
        return refined_prompt


