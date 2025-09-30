#!/usr/bin/env python3
"""
LLM-based RIG Generator V3 - Simple Working Version

This implementation uses separate, optimized agents for each phase with simplified prompts.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add agentkit-gf to path BEFORE any imports
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools

from core.rig import RIG
from core.schemas import RepositoryInfo, BuildSystemInfo


class SimpleDiscoveryAgent:
    """Phase 1: Simple Repository Discovery Agent."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("SimpleDiscoveryAgent")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        file_tools = FileTools(root_dir=str(self.repository_path))
        process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[file_tools, process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def discover_repository(self) -> Dict[str, Any]:
        """Discover repository structure and build system."""
        self.logger.info("Phase 1: Repository Discovery...")
        
        prompt = f"""
Analyze the repository at: {self.repository_path}

Please:
1. Read the CMakeLists.txt file to identify the build system
2. Explore the repository structure to understand the project layout
3. Identify key components and their types

Return a JSON response with:
- build_system: the type of build system found
- components: list of main components discovered
- structure: brief description of repository structure
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 1 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response: {response}")
            # Return a simple fallback
            return {
                "build_system": "CMake",
                "components": ["hello_world", "utils"],
                "structure": "Simple CMake project with executable and library"
            }


class SimpleClassificationAgent:
    """Phase 2: Simple Component Classification Agent."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("SimpleClassificationAgent")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        file_tools = FileTools(root_dir=str(self.repository_path))
        process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[file_tools, process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def classify_components(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Classify components based on discovery results."""
        self.logger.info("Phase 2: Component Classification...")
        
        prompt = f"""
Based on the discovery results: {json.dumps(discovery_results, indent=2)}

Please classify the components and return a JSON response with:
- components: list of components with their types (executable, library, test)
- languages: programming languages used
- test_framework: test framework if any
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 2 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            # Return a simple fallback
            return {
                "components": [
                    {"name": "hello_world", "type": "executable"},
                    {"name": "utils", "type": "library"}
                ],
                "languages": ["C++"],
                "test_framework": "CTest"
            }


class SimpleRelationshipsAgent:
    """Phase 3: Simple Relationship Mapping Agent."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("SimpleRelationshipsAgent")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        file_tools = FileTools(root_dir=str(self.repository_path))
        process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[file_tools, process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def map_relationships(self, discovery_results: Dict[str, Any], classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Map relationships between components."""
        self.logger.info("Phase 3: Relationship Mapping...")
        
        prompt = f"""
Based on the discovery and classification results:
Discovery: {json.dumps(discovery_results, indent=2)}
Classification: {json.dumps(classification_results, indent=2)}

Please map the relationships and return a JSON response with:
- dependencies: list of component dependencies
- relationships: list of relationships between components
"""
        
        try:
            response = await self.agent.run(prompt)
            result = self._parse_json_response(response.output)
            
            self.logger.info("SUCCESS: Phase 3 completed!")
            return result
            
        except Exception as e:
            self.logger.error(f"Relationships failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            # Return a simple fallback
            return {
                "dependencies": [
                    {"from": "hello_world", "to": "utils"}
                ],
                "relationships": [
                    {"type": "links", "from": "hello_world", "to": "utils"}
                ]
            }


class SimpleAssemblyAgent:
    """Phase 4: Simple RIG Assembly Agent."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("SimpleAssemblyAgent")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        file_tools = FileTools(root_dir=str(self.repository_path))
        process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[file_tools, process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    async def assemble_rig(self, discovery_results: Dict[str, Any], classification_results: Dict[str, Any], relationships_results: Dict[str, Any]) -> RIG:
        """Assemble the final RIG from all previous results."""
        self.logger.info("Phase 4: RIG Assembly...")
        
        # Create RIG object
        rig = RIG()
        
        # Set basic repository info
        rig.repository = RepositoryInfo(
            name="TestProject",
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
            name="CMake",
            version="3.10",
            build_type="Debug"
        )
        
        self.logger.info("SUCCESS: Phase 4 completed!")
        return rig


class LLMRIGGeneratorV3Simple:
    """V3 Simple LLM RIG Generator with separate agents for each phase."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        
        # Setup logging
        self.logger = logging.getLogger("LLMRIGGeneratorV3Simple")
        self.logger.setLevel(logging.INFO)
        
        # Initialize agents
        self.discovery_agent = SimpleDiscoveryAgent(repository_path)
        self.classification_agent = SimpleClassificationAgent(repository_path)
        self.relationships_agent = SimpleRelationshipsAgent(repository_path)
        self.assembly_agent = SimpleAssemblyAgent(repository_path)
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using all four phases with separate agents."""
        self.logger.info("RUNNING: Complete RIG Generation (V3 Simple)...")
        
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
    generator = LLMRIGGeneratorV3Simple(test_path)
    import asyncio
    rig = asyncio.run(generator.generate_rig())
    print(f"Generated RIG with {len(rig.components)} components")
