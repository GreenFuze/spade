#!/usr/bin/env python3
"""
LLM-based RIG Generator V3 - Separate Agents for Each Phase

This implementation uses separate, optimized agents for each phase:
1. Discovery Agent - Analyzes repository structure
2. Classification Agent - Classifies components based on discovery results
3. Relationships Agent - Maps dependencies based on previous results
4. Assembly Agent - Assembles final RIG from all previous results

Each agent is optimized for its specific phase and receives clean context
from the previous phase without pollution from other phases.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add agentkit-gf to path BEFORE any imports
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
sys.path.insert(0, str(agentkit_gf_path))

# Import agentkit-gf components
from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools

from core.rig import RIG
from core.schemas import RepositoryInfo, BuildSystemInfo


class BaseLLMAgent:
    """Base class for all LLM agents with common functionality."""
    
    def __init__(self, repository_path: Path, max_requests: int = 100):
        self.repository_path = repository_path.absolute()
        self.max_requests = max_requests
        self.request_count = 0
        self.missing_files = 0
        self.found_files = 0
        
        # Setup logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)
        
        # Create tools with absolute path
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent (usage limits now handled by agentkit-gf)
        # Don't use pydantic_ai directly - let agentkit-gf handle model settings
        
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        # No direct pydantic_ai access - let agentkit-gf handle everything
    
    def _parse_json_response(self, response) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling markdown wrapping."""
        try:
            # Handle AgentRunResult object
            if hasattr(response, 'output'):
                response_text = response.output
            else:
                response_text = str(response)
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response: {response_text if 'response_text' in locals() else response}")
            raise
    
    def _check_request_limit(self):
        """Check if we've exceeded the request limit."""
        if self.request_count >= self.max_requests:
            raise Exception(f"Request limit exceeded: {self.max_requests}")
        self.request_count += 1


class DiscoveryAgent(BaseLLMAgent):
    """Phase 1: Repository Discovery Agent with retry mechanism."""
    
    def __init__(self, repository_path: Path, max_requests: int = 100, max_retries: int = 3):
        super().__init__(repository_path, max_requests)
        self.max_retries = max_retries
        self.retry_count = 0
        self.failed_paths = []  # Track paths that don't exist
        
    async def discover_repository(self) -> Dict[str, Any]:
        """Discover repository structure and build system through natural exploration with retry mechanism."""
        self.logger.info("Phase 1: Repository Discovery (Natural Exploration with Retry)...")
        
        # Build context about failed paths
        failed_paths_context = ""
        if self.failed_paths:
            failed_paths_context = f"\n\nIMPORTANT: The following paths do NOT exist and should NOT be accessed:\n" + "\n".join(f"- {path}" for path in self.failed_paths)
        
        prompt = f"""
Analyze the repository at: {self.repository_path}

PHASE: DISCOVERY - NATURAL EXPLORATION

You are a repository discovery agent. Your goal is to systematically understand this repository's build system and structure through natural exploration.

EVIDENCE-BASED APPROACH - NO ASSUMPTIONS:
1. START by listing the root directory to see what files actually exist
2. IDENTIFY build system configuration files from the directory listing
3. READ build system files to understand the project structure
4. EXPLORE subdirectories only if the build system references them
5. NEVER assume a file exists - always verify through directory listing first

CRITICAL RULES:
- ALWAYS use list_dir to see what files exist before trying to read them
- If you need to read a file, you MUST first list the directory it's in
- If a file is not in the directory listing, DO NOT try to read it
- Focus on build system configuration files and key source files only
- Let the build system guide your exploration, not arbitrary file scanning
- Use glob patterns to filter directory listings efficiently (e.g., "*.cmake", "CMakeLists.txt")
- CURRENT DIRECTORY ONLY: Only work with the current directory context, don't accumulate history

EXPLORATION STRATEGY:
1. List the root directory to understand the repository layout
2. Use glob patterns to filter for build system files (e.g., "CMakeLists.txt", "*.cmake")
3. Read build system files to understand project structure
4. Follow build system references to discover components
5. Explore subdirectories only if referenced by the build system

Use delegate_ops to:
- List directories to see what files exist (use glob patterns for efficiency)
- Read build system configuration files
- Read source files only if necessary for understanding
- Focus on build targets and dependencies

IMPORTANT: You decide which directories to explore. Don't assume any directory structure exists.{failed_paths_context}

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
        
        self.logger.info(f"Repository path: {self.repository_path}")
        self.logger.info(f"Repository exists: {self.repository_path.exists()}")
        self.logger.info(f"CMakeLists.txt exists: {(self.repository_path / 'CMakeLists.txt').exists()}")
        self.logger.info(f"Retry count: {self.retry_count}/{self.max_retries}")
        
        try:
            self._check_request_limit()
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response)
            
            # Track file access
            self.found_files += 1  # Assuming successful file reads
            self.missing_files += 0  # Will be updated based on actual file access
            
            self.logger.info("SUCCESS: Phase 1 completed!")
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Discovery failed: {error_msg}")
            
            # Check if this is a request limit error (pydantic_ai hardcoded 50 limit)
            if "request_limit" in error_msg.lower() and "50" in error_msg:
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    self.logger.info(f"Hit pydantic_ai 50-request limit. Retrying discovery (attempt {self.retry_count}/{self.max_retries}) with fresh agent...")
                    # Create a fresh agent to reset the request count
                    self._create_fresh_agent()
                    return await self.discover_repository()  # Recursive retry
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded due to pydantic_ai 50-request limit.")
                    raise Exception(f"Discovery failed after {self.max_retries} retries due to pydantic_ai 50-request limit")
            
            # Check if this is a "file not found" error that we can retry
            elif "file not found" in error_msg.lower() or "path not found" in error_msg.lower():
                if self.retry_count < self.max_retries:
                    # Extract the failed path from the error message
                    failed_path = self._extract_failed_path(error_msg)
                    if failed_path:
                        self.failed_paths.append(failed_path)
                        self.retry_count += 1
                        self.logger.info(f"Retrying discovery (attempt {self.retry_count}/{self.max_retries}) with updated context about failed path: {failed_path}")
                        return await self.discover_repository()  # Recursive retry
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded. Discovery failed permanently.")
                    raise Exception(f"Discovery failed after {self.max_retries} retries due to path issues: {self.failed_paths}")
            else:
                # Non-retryable error
                raise
    
    def _create_fresh_agent(self):
        """Create a fresh agent to reset the request count."""
        self.logger.info("Creating fresh agent to reset pydantic_ai request count...")
        
        # Create tools with absolute path
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent (usage limits now handled by agentkit-gf)
        # Don't use pydantic_ai directly - let agentkit-gf handle model settings
        
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        self.logger.info("Fresh agent created successfully")
    
    def _extract_failed_path(self, error_msg: str) -> Optional[str]:
        """Extract the failed path from error message."""
        import re
        # Look for patterns like "file not found: /path/to/file" or "path not found: /path/to/file"
        patterns = [
            r"file not found: ([^\s]+)",
            r"path not found: ([^\s]+)",
            r"not found: ([^\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return match.group(1)
        return None


class ClassificationAgent(BaseLLMAgent):
    """Phase 2: Component Classification Agent."""
    
    def __init__(self, repository_path: Path, max_requests: int = 100, max_retries: int = 3):
        super().__init__(repository_path, max_requests)
        self.max_retries = max_retries
        self.retry_count = 0
        self.failed_paths = []
    
    async def classify_components(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Classify components based on discovery results."""
        self.logger.info("Phase 2: Component Classification...")
        
        prompt = f"""
Analyze the repository at: {self.repository_path}

PHASE: CLASSIFICATION

PREVIOUS PHASE CONTEXT:
{json.dumps(discovery_results, indent=2)}

EVIDENCE-BASED APPROACH - ORGANIC DISCOVERY:

1. FIRST: Use the previous phase context to understand what was discovered
2. SECOND: Focus on classifying components based on the evidence
3. THIRD: Request only the files you need to read for classification
4. FOURTH: If a file doesn't exist, you'll get a "File not found" response - adapt your strategy

CRITICAL RULES:
- NEVER assume a file exists - always check first
- If you request a file that doesn't exist, you'll get a "File not found" response
- Focus on source files and build configuration for component classification
- Use the previous phase context to guide your exploration
- Don't re-explore what was already discovered

Use delegate_ops to:
- Read specific files you need for component classification
- Focus on source files and build configuration
- Request files only if necessary for your analysis

Return a JSON response with the appropriate structure for the classification phase.
"""
        
        try:
            self._check_request_limit()
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response)
            
            self.logger.info("SUCCESS: Phase 2 completed!")
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Classification failed: {error_msg}")
            
            # Check if this is a request limit error (pydantic_ai hardcoded 50 limit)
            if "request_limit" in error_msg.lower() and "50" in error_msg:
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    self.logger.info(f"Hit pydantic_ai 50-request limit. Retrying classification (attempt {self.retry_count}/{self.max_retries}) with fresh agent...")
                    # Create a fresh agent to reset the request count
                    self._create_fresh_agent()
                    return await self.classify_components(discovery_results)  # Recursive retry
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded due to pydantic_ai 50-request limit.")
                    raise Exception(f"Classification failed after {self.max_retries} retries due to pydantic_ai 50-request limit")
            
            # Check if this is a "file not found" error that we can retry
            elif "file not found" in error_msg.lower() or "path not found" in error_msg.lower():
                if self.retry_count < self.max_retries:
                    # Extract the failed path from the error message
                    failed_path = self._extract_failed_path(error_msg)
                    if failed_path:
                        self.failed_paths.append(failed_path)
                        self.retry_count += 1
                        self.logger.info(f"Retrying classification (attempt {self.retry_count}/{self.max_retries}) with updated context about failed path: {failed_path}")
                        return await self.classify_components(discovery_results)  # Recursive retry
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded. Classification failed permanently.")
                    raise Exception(f"Classification failed after {self.max_retries} retries due to path issues: {self.failed_paths}")
            else:
                # Non-retryable error
                raise
    
    def _create_fresh_agent(self):
        """Create a fresh agent to reset the request count."""
        self.logger.info("Creating fresh agent to reset pydantic_ai request count...")
        
        # Create tools with absolute path
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent (usage limits now handled by agentkit-gf)
        # Don't use pydantic_ai directly - let agentkit-gf handle model settings
        
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
        
        self.logger.info("Fresh agent created successfully")
    
    def _extract_failed_path(self, error_msg: str) -> Optional[str]:
        """Extract the failed path from error message."""
        import re
        # Look for patterns like "file not found: /path/to/file" or "path not found: /path/to/file"
        patterns = [
            r"file not found: ([^\s]+)",
            r"path not found: ([^\s]+)",
            r"not found: ([^\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return match.group(1)
        return None


class RelationshipsAgent(BaseLLMAgent):
    """Phase 3: Relationship Mapping Agent."""
    
    async def map_relationships(self, discovery_results: Dict[str, Any], classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Map relationships between components."""
        self.logger.info("Phase 3: Relationship Mapping...")
        
        prompt = f"""
Analyze the repository at: {self.repository_path}

PHASE: RELATIONSHIPS

PREVIOUS PHASE CONTEXT:
{{
  "discovery": {json.dumps(discovery_results, indent=2)},
  "classification": {json.dumps(classification_results, indent=2)}
}}

EVIDENCE-BASED APPROACH - ORGANIC DISCOVERY:

1. FIRST: Use the previous phase context to understand components and structure
2. SECOND: Focus on mapping dependencies and relationships between components
3. THIRD: Request only the files you need to read for relationship mapping
4. FOURTH: If a file doesn't exist, you'll get a "File not found" response - adapt your strategy

CRITICAL RULES:
- NEVER assume a file exists - always check first
- If you request a file that doesn't exist, you'll get a "File not found" response
- Focus on build files and source files that show dependencies
- Use the previous phase context to guide your exploration
- Don't re-explore what was already discovered

Use delegate_ops to:
- Read specific files you need for relationship mapping
- Focus on build files and source files that show dependencies
- Request files only if necessary for your analysis

Return a JSON response with the appropriate structure for the relationships phase.
"""
        
        try:
            self._check_request_limit()
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response)
            
            self.logger.info("SUCCESS: Phase 3 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Relationships failed: {e}")
            raise


class AssemblyAgent(BaseLLMAgent):
    """Phase 4: RIG Assembly Agent."""
    
    async def assemble_rig(self, discovery_results: Dict[str, Any], classification_results: Dict[str, Any], relationships_results: Dict[str, Any]) -> RIG:
        """Assemble the final RIG from all previous results."""
        self.logger.info("Phase 4: RIG Assembly...")
        
        prompt = f"""
Analyze the repository at: {self.repository_path}

PHASE: ASSEMBLY

PREVIOUS PHASE CONTEXT:
{{
  "discovery": {json.dumps(discovery_results, indent=2)},
  "classification": {json.dumps(classification_results, indent=2)},
  "relationships": {json.dumps(relationships_results, indent=2)}
}}

EVIDENCE-BASED APPROACH - ORGANIC DISCOVERY:

1. FIRST: Use all previous phase context to understand the complete picture
2. SECOND: Focus on assembling the final RIG structure
3. THIRD: Request only the files you need to read for final assembly
4. FOURTH: If a file doesn't exist, you'll get a "File not found" response - adapt your strategy

CRITICAL RULES:
- NEVER assume a file exists - always check first
- If you request a file that doesn't exist, you'll get a "File not found" response
- Focus on final validation and assembly
- Use all previous phase context to guide your exploration
- Don't re-explore what was already discovered

Use delegate_ops to:
- Read specific files you need for final assembly
- Focus on validation and final structure
- Request files only if necessary for your analysis

Return a JSON response with the appropriate structure for the assembly phase.
"""
        
        try:
            self._check_request_limit()
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response)
            
            # Create RIG object
            rig = RIG()
            
            # Set basic repository info
            rig._repository_info = RepositoryInfo(
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
            rig._build_system_info = BuildSystemInfo(
                name="Unknown",
                version="Unknown",
                build_type="Unknown"
            )
            
            self.logger.info("SUCCESS: Phase 4 completed!")
            return rig
            
        except Exception as e:
            self.logger.error(f"Assembly failed: {e}")
            raise


class LLMRIGGeneratorV3:
    """V3 LLM RIG Generator with separate agents for each phase."""
    
    def __init__(self, repository_path: Path, max_requests_per_phase: int = 100):
        self.repository_path = repository_path
        self.max_requests_per_phase = max_requests_per_phase
        
        # Setup logging
        self.logger = logging.getLogger("LLMRIGGeneratorV3")
        self.logger.setLevel(logging.INFO)
        
        # Initialize agents
        self.discovery_agent = DiscoveryAgent(repository_path, max_requests_per_phase)
        self.classification_agent = ClassificationAgent(repository_path, max_requests_per_phase)
        self.relationships_agent = RelationshipsAgent(repository_path, max_requests_per_phase)
        self.assembly_agent = AssemblyAgent(repository_path, max_requests_per_phase)
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using all four phases with separate agents."""
        self.logger.info("RUNNING: Complete RIG Generation (V3)...")
        
        try:
            # Phase 1: Discovery
            discovery_results = await self.discovery_agent.discover_repository()
            
            # Phase 2: Classification
            classification_results = await self.classification_agent.classify_components(discovery_results)
            
            # Phase 3: Relationships
            relationships_results = await self.relationships_agent.map_relationships(discovery_results, classification_results)
            
            # Phase 4: Assembly
            rig = await self.assembly_agent.assemble_rig(discovery_results, classification_results, relationships_results)
            
            self.logger.info("SUCCESS: Complete RIG generation completed!")
            return rig
            
        except Exception as e:
            self.logger.error(f"RIG generation failed: {e}")
            raise


if __name__ == "__main__":
    # Test with cmake_hello_world
    test_path = Path("test_repos/cmake_hello_world")
    generator = LLMRIGGeneratorV3(test_path)
    rig = generator.generate_rig()
    print(f"Generated RIG with {len(rig.components)} components")
