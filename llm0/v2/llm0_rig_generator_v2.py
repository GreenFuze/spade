#!/usr/bin/env python3
"""
LLM-based RIG Generator V2 - Directory Listing + Context Tracking Approach

This version uses a single agent with directory listing and context tracking
to avoid the "reading all files" problem.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Add the local agentkit-gf source to path
agentkit_gf_path = Path(__file__).parent.parent / "agentkit-gf"
sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools
from pydantic_ai.settings import ModelSettings

from schemas import (
    Component, ComponentType, Runtime, Evidence, ComponentLocation,
    ExternalPackage, PackageManager, RepositoryInfo, BuildSystemInfo,
    TestDefinition, Aggregator, Runner, Utility
)
from rig import RIG


@dataclass
class DiscoveryResult:
    """Result from repository discovery phase."""
    success: bool
    data: Dict[str, Any]
    token_usage: Dict[str, int]
    errors: List[str]


class LLMRIGGeneratorV2:
    """
    LLM-based RIG Generator V2 using directory listing + context tracking approach.
    
    This version uses a single agent with directory listing to avoid the
    "reading all files" problem while maintaining evidence-based approach.
    """
    
    def __init__(self, repository_path: Path):
        """
        Initialize the LLM RIG Generator.
        
        Args:
            repository_path: Path to the repository to analyze
        """
        self.repository_path = Path(repository_path).resolve()
        self.logger = logging.getLogger(__name__)
        
        # Request limit management
        self.max_requests_per_phase = 100
        self.current_phase_requests = 0
        
        # Context tracking for missing files
        self.missing_files: List[str] = []
        self.requested_files: List[str] = []
        self.found_files: List[str] = []
        
        # Single agent for all phases
        self.agent = None
        self._create_unified_agent()
    
    def _create_unified_agent(self):
        """Create a single agent for all phases with context tracking."""
        try:
            # Create tools with repository root
            file_tools = FileTools(root_dir=str(self.repository_path))
            process_tools = ProcessTools(root_cwd=str(self.repository_path))
            
            # Create the unified agent
            self.agent = DelegatingToolsAgent(
                model="openai:gpt-5-nano",
                tool_sources=[file_tools, process_tools],
                builtin_enums=[],
                model_settings=ModelSettings(temperature=0),
                real_time_log_user=True,
                real_time_log_agent=True
            )
            
            self.logger.info("Unified LLM RIG Generator V2 created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create unified agent: {e}")
            raise
    
    def _get_directory_structure(self, path: Path = None, prefix: str = "") -> str:
        """
        Generate a tree-like directory structure string.
        
        Args:
            path: Directory path to scan (defaults to repository root)
            prefix: Prefix for tree structure
            
        Returns:
            Tree-like directory structure string
        """
        if path is None:
            path = self.repository_path
        
        structure = []
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "+-- " if is_last else "+-- "
                next_prefix = "    " if is_last else "|   "
                
                structure.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and not item.name.startswith('.') and item.name not in ['node_modules', 'build', 'dist', 'target']:
                    sub_structure = self._get_directory_structure(item, prefix + next_prefix)
                    structure.append(sub_structure)
                    
        except PermissionError:
            structure.append(f"{prefix}+-- [Permission Denied]")
        
        return "\n".join(structure)
    
    def _check_request_limit(self):
        """Check if we've exceeded the request limit."""
        if self.current_phase_requests >= self.max_requests_per_phase:
            raise Exception(f"Request limit exceeded: {self.current_phase_requests}/{self.max_requests_per_phase}")
    
    def _increment_request_counter(self):
        """Increment the request counter."""
        self.current_phase_requests += 1
        self.logger.info(f"Request count: {self.current_phase_requests}/{self.max_requests_per_phase}")
    
    def _reset_request_counter(self):
        """Reset the request counter for a new phase."""
        self.current_phase_requests = 0
        self.logger.info(f"Starting new phase with request limit: {self.max_requests_per_phase}")
    
    def _handle_missing_file(self, file_path: str) -> str:
        """
        Handle a request for a missing file.
        
        Args:
            file_path: Path to the missing file
            
        Returns:
            Response message about the missing file
        """
        if file_path not in self.missing_files:
            self.missing_files.append(file_path)
        
        return f"File not found: {file_path}"
    
    def _create_unified_prompt(self, phase: str, context: Dict[str, Any] = None) -> str:
        """
        Create a unified prompt for all phases with directory listing and context.
        
        Args:
            phase: Current phase (discovery, classification, relationships, assembly)
            context: Context from previous phases
            
        Returns:
            Unified prompt with directory listing and context
        """
        # Get directory structure
        directory_structure = self._get_directory_structure()
        
        # Build context information
        context_info = ""
        if context:
            context_info = f"""
PREVIOUS PHASE CONTEXT:
{json.dumps(context, indent=2)}
"""
        
        # Build missing files information
        missing_files_info = ""
        if self.missing_files:
            missing_files_info = f"""
FILES PREVIOUSLY REQUESTED BUT NOT FOUND:
{', '.join(self.missing_files)}
"""
        
        return f"""
Analyze the repository at: {self.repository_path}

PHASE: {phase.upper()}

DIRECTORY STRUCTURE:
{directory_structure}

{context_info}
{missing_files_info}

EVIDENCE-BASED APPROACH - DIRECTORY LISTING FIRST:

1. FIRST: Use the directory structure above to understand the repository layout
2. SECOND: Identify the build system type from the directory structure
3. THIRD: Request only the files you need to read based on the build system
4. FOURTH: If a file doesn't exist, you'll get a "File not found" response - adapt your strategy

CRITICAL RULES:
- NEVER assume a file exists - always check the directory structure first
- If you request a file that doesn't exist, you'll get a "File not found" response
- Focus on build system configuration files and key source files only
- Don't explore every subdirectory unless necessary
- Use the directory structure to guide your file requests

CONTEXT TRACKING:
- Files requested: {len(self.requested_files)}
- Files found: {len(self.found_files)}
- Files missing: {len(self.missing_files)}

Use delegate_ops to:
- Read specific files you need based on the directory structure
- Focus on build system configuration files first
- Request source files only if necessary for your analysis

Return a JSON response with the appropriate structure for the {phase} phase.
"""
    
    def discover_repository(self) -> DiscoveryResult:
        """
        Phase 1: Repository Discovery with directory listing.
        
        Returns:
            DiscoveryResult with repository information
        """
        self.logger.info("INFO: Starting Phase 1: Repository Discovery (V2)")
        self._reset_request_counter()
        
        try:
            # Create discovery prompt with directory listing
            discovery_prompt = self._create_unified_prompt("discovery")
            self.logger.info(f"Discovery prompt created: {len(discovery_prompt)} characters")
            
            # Execute discovery
            self.logger.info("Executing discovery with unified agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = self.agent.run_sync(discovery_prompt)
            
            self.logger.info(f"Agent execution completed")
            self.logger.info(f"Result type: {type(result)}")
            
            # Parse the result
            result_data = self._parse_agent_json_response(result.output, "Discovery")
            
            # Extract token usage
            usage = result.usage()
            token_usage = {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.input_tokens + usage.output_tokens
            }
            
            self.logger.info(f"Discovery completed successfully")
            self.logger.info(f"Token usage: {token_usage}")
            
            return DiscoveryResult(
                success=True,
                data=result_data,
                token_usage=token_usage,
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"Discovery failed with exception: {e}")
            return DiscoveryResult(
                success=False,
                data={},
                token_usage={'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                errors=[f"Discovery failed with exception: {e}"]
            )
    
    def _parse_agent_json_response(self, result_output: str, phase_name: str) -> Dict[str, Any]:
        """
        Parse JSON response from agent, handling markdown code blocks and other formatting.
        
        Args:
            result_output: Raw output from agent
            phase_name: Name of the phase for logging purposes
            
        Returns:
            Parsed JSON data as dictionary
        """
        self.logger.info(f"Attempting to parse {phase_name} result as JSON...")
        
        # Clean the output - extract JSON from markdown code blocks
        output_text = result_output.strip()
        
        # Look for JSON code blocks
        json_start = output_text.find("```json")
        if json_start != -1:
            # Find the start of the JSON content
            json_start += 7  # Skip "```json"
            json_end = output_text.find("```", json_start)
            if json_end != -1:
                json_content = output_text[json_start:json_end].strip()
            else:
                json_content = output_text[json_start:].strip()
        else:
            # Look for regular JSON
            json_start = output_text.find("{")
            if json_start != -1:
                json_content = output_text[json_start:].strip()
            else:
                json_content = output_text
        
        # Remove any trailing text after JSON
        if json_content.endswith("```"):
            json_content = json_content[:-3].strip()
        
        # Remove comments from JSON (// style comments)
        lines = json_content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments
            if '//' in line:
                line = line[:line.index('//')]
            cleaned_lines.append(line)
        json_content = '\n'.join(cleaned_lines)
        
        try:
            result_data = json.loads(json_content)
            self.logger.info(f"{phase_name} JSON parsing successful")
            return result_data
        except json.JSONDecodeError as e:
            self.logger.error(f"{phase_name} JSON parsing failed: {e}")
            self.logger.error(f"JSON content: {json_content[:500]}...")
            raise
    
    def classify_components(self, discovery_result: DiscoveryResult) -> Dict[str, Any]:
        """
        Phase 2: Component Classification with directory listing and context.
        
        Args:
            discovery_result: Results from the discovery phase
            
        Returns:
            Classification results with components
        """
        self.logger.info("INFO: Starting Phase 2: Component Classification (V2)")
        self._reset_request_counter()
        
        try:
            # Create classification prompt with directory listing and discovery context
            classification_prompt = self._create_unified_prompt("classification", discovery_result.data)
            self.logger.info(f"Classification prompt created: {len(classification_prompt)} characters")
            
            # Execute classification
            self.logger.info("Executing component classification with unified agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = self.agent.run_sync(classification_prompt)
            
            self.logger.info(f"Agent execution completed")
            
            # Parse the result
            result_data = self._parse_agent_json_response(result.output, "Classification")
            
            # Extract token usage
            usage = result.usage()
            token_usage = {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.input_tokens + usage.output_tokens
            }
            
            self.logger.info(f"Classification completed successfully")
            self.logger.info(f"Token usage: {token_usage}")
            
            return {
                "success": True,
                "data": result_data,
                "token_usage": token_usage,
                "errors": []
            }
            
        except Exception as e:
            self.logger.error(f"Classification failed with exception: {e}")
            return {
                "success": False,
                "data": {},
                "token_usage": {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                "errors": [f"Classification failed with exception: {e}"]
            }
    
    def map_relationships(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 3: Relationship Mapping with directory listing and context.
        
        Args:
            discovery_result: Results from the discovery phase
            classification_result: Results from the classification phase
            
        Returns:
            Relationship mapping results
        """
        self.logger.info("INFO: Starting Phase 3: Relationship Mapping (V2)")
        self._reset_request_counter()
        
        try:
            # Create relationship prompt with directory listing and previous context
            context = {
                "discovery": discovery_result.data,
                "classification": classification_result["data"]
            }
            relationship_prompt = self._create_unified_prompt("relationships", context)
            self.logger.info(f"Relationship prompt created: {len(relationship_prompt)} characters")
            
            # Execute relationship mapping
            self.logger.info("Executing relationship mapping with unified agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = self.agent.run_sync(relationship_prompt)
            
            self.logger.info(f"Agent execution completed")
            
            # Parse the result
            result_data = self._parse_agent_json_response(result.output, "Relationships")
            
            # Extract token usage
            usage = result.usage()
            token_usage = {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.input_tokens + usage.output_tokens
            }
            
            self.logger.info(f"Relationship mapping completed successfully")
            self.logger.info(f"Token usage: {token_usage}")
            
            return {
                "success": True,
                "data": result_data,
                "token_usage": token_usage,
                "errors": []
            }
            
        except Exception as e:
            self.logger.error(f"Relationship mapping failed with exception: {e}")
            return {
                "success": False,
                "data": {},
                "token_usage": {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                "errors": [f"Relationship mapping failed with exception: {e}"]
            }
    
    def assemble_rig(self, discovery_result: DiscoveryResult, classification_result: Dict[str, Any], relationship_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: RIG Assembly with directory listing and context.
        
        Args:
            discovery_result: Results from the discovery phase
            classification_result: Results from the classification phase
            relationship_result: Results from the relationship mapping phase
            
        Returns:
            RIG assembly results
        """
        self.logger.info("INFO: Starting Phase 4: RIG Assembly (V2)")
        self._reset_request_counter()
        
        try:
            # Create assembly prompt with directory listing and all previous context
            context = {
                "discovery": discovery_result.data,
                "classification": classification_result["data"],
                "relationships": relationship_result["data"]
            }
            assembly_prompt = self._create_unified_prompt("assembly", context)
            self.logger.info(f"Assembly prompt created: {len(assembly_prompt)} characters")
            
            # Execute RIG assembly
            self.logger.info("Executing RIG assembly with unified agent...")
            self._check_request_limit()
            self._increment_request_counter()
            result = self.agent.run_sync(assembly_prompt)
            
            self.logger.info(f"Agent execution completed")
            
            # Parse the result
            result_data = self._parse_agent_json_response(result.output, "Assembly")
            
            # Extract token usage
            usage = result.usage()
            token_usage = {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.input_tokens + usage.output_tokens
            }
            
            self.logger.info(f"RIG assembly completed successfully")
            self.logger.info(f"Token usage: {token_usage}")
            
            return {
                "success": True,
                "data": result_data,
                "token_usage": token_usage,
                "errors": []
            }
            
        except Exception as e:
            self.logger.error(f"RIG assembly failed with exception: {e}")
            return {
                "success": False,
                "data": {},
                "token_usage": {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                "errors": [f"RIG assembly failed with exception: {e}"]
            }
    
    def generate_rig(self) -> RIG:
        """
        Generate a complete RIG using the unified V2 approach.
        
        Returns:
            Complete RIG object
        """
        self.logger.info("Starting LLM-based RIG generation (V2)...")
        
        # Phase 1: Repository Discovery
        print("INFO: Phase 1: Repository Discovery...")
        discovery_result = self.discover_repository()
        
        if not discovery_result.success:
            raise Exception(f"Repository discovery failed: {discovery_result.errors}")
        
        print(f"SUCCESS: Phase 1 completed!")
        print(f"TOKENS: Phase 1 Token Usage: {discovery_result.token_usage['total_tokens']} tokens")
        print(f"REQUESTS: Used {self.current_phase_requests} requests")
        
        # Phase 2: Component Classification
        print("\nINFO: Phase 2: Component Classification...")
        classification_result = self.classify_components(discovery_result)
        
        if not classification_result["success"]:
            raise Exception(f"Component classification failed: {classification_result['errors']}")
        
        print(f"SUCCESS: Phase 2 completed!")
        print(f"TOKENS: Phase 2 Token Usage: {classification_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {self.current_phase_requests} requests")
        
        # Phase 3: Relationship Mapping
        print("\nINFO: Phase 3: Relationship Mapping...")
        relationship_result = self.map_relationships(discovery_result, classification_result)
        
        if not relationship_result["success"]:
            raise Exception(f"Relationship mapping failed: {relationship_result['errors']}")
        
        print(f"SUCCESS: Phase 3 completed!")
        print(f"TOKENS: Phase 3 Token Usage: {relationship_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {self.current_phase_requests} requests")
        
        # Phase 4: RIG Assembly
        print("\nINFO: Phase 4: RIG Assembly...")
        assembly_result = self.assemble_rig(discovery_result, classification_result, relationship_result)
        
        if not assembly_result["success"]:
            raise Exception(f"RIG assembly failed: {assembly_result['errors']}")
        
        print(f"SUCCESS: Phase 4 completed!")
        print(f"TOKENS: Phase 4 Token Usage: {assembly_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {self.current_phase_requests} requests")
        
        # Calculate totals
        total_tokens = (
            discovery_result.token_usage['total_tokens'] +
            classification_result['token_usage']['total_tokens'] +
            relationship_result['token_usage']['total_tokens'] +
            assembly_result['token_usage']['total_tokens']
        )
        
        print(f"\nTOTAL: Total Token Usage: {total_tokens} tokens")
        print(f"TOTAL: Total Requests: {self.current_phase_requests} requests")
        
        # For now, return a basic RIG with assembly data
        # TODO: Convert assembly data to proper RIG object
        rig = RIG()
        
        # Set basic repository info
        rig.repository = RepositoryInfo(
            name="Unknown",
            root_path=self.repository_path,
            build_directory=self.repository_path / "build",
            output_directory=self.repository_path / "output",
            configure_command="cmake .",
            build_command="cmake --build .",
            install_command="cmake --install .",
            test_command="ctest"
        )
        
        # Set basic build system info
        rig.build_system = BuildSystemInfo(
            name="Unknown",
            version="Unknown",
            build_type="Unknown"
        )
        
        return rig


def main():
    """Test the LLM RIG Generator V2."""
    import sys
    from pathlib import Path
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with cmake_hello_world
    test_project = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    
    if not test_project.exists():
        print(f"ERROR: Test project not found at {test_project}")
        sys.exit(1)
    
    print(f"Testing LLM RIG Generator V2 with: {test_project}")
    
    try:
        generator = LLMRIGGeneratorV2(test_project)
        rig = generator.generate_rig()
        print(f"SUCCESS: Generated RIG with {len(rig.components)} components")
    except Exception as e:
        print(f"ERROR: Failed to generate RIG: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
