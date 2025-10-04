#!/usr/bin/env python3
"""
Base V5 Agent with Direct RIG Manipulation

This module implements the base class for all V5 agents that work directly
with RIG objects through specialized tools, eliminating JSON conversion issues.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Add agentkit-gf to path BEFORE any imports
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
if str(agentkit_gf_path) not in sys.path:
    sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools

# Import RIG classes
from core.rig import RIG
from core.schemas import (
    Component, TestDefinition, Evidence, 
    RepositoryInfo, BuildSystemInfo, Runtime
)


class RIGTools:
    """Tools for direct RIG manipulation in V5 architecture."""
    
    def __init__(self, rig_instance: RIG):
        self.rig = rig_instance
        self.logger = logging.getLogger("RIGTools")
    
    def set_repository_overview(self, name: str, type: str, primary_language: str, 
                               build_systems: List[str], evidence: List[Dict]) -> str:
        """Set repository overview information."""
        try:
            # Create evidence with required call_stack field
            evidence_objects = []
            if evidence:
                for e in evidence:
                    evidence_obj = Evidence(
                        call_stack=e.get('call_stack', [])
                    )
                    evidence_objects.append(evidence_obj)
            
            # Create repository info
            repo_info = RepositoryInfo(
                name=name,
                type=type,
                primary_language=primary_language,
                build_systems=build_systems,
                evidence=evidence_objects
            )
            
            # Set in RIG
            self.rig.repository = repo_info
            return f"Set repository overview: {name} ({type}, {primary_language})"
        except Exception as e:
            self.logger.error(f"Failed to set repository overview: {e}")
            return f"Error setting repository overview: {e}"
    
    def set_build_system_info(self, name: str, version: str, build_type: str, 
                             evidence: List[Dict]) -> str:
        """Set build system information."""
        try:
            # Create evidence with required call_stack field
            evidence_objects = []
            if evidence:
                for e in evidence:
                    evidence_obj = Evidence(
                        call_stack=e.get('call_stack', [])
                    )
                    evidence_objects.append(evidence_obj)
            
            build_info = BuildSystemInfo(
                name=name,
                version=version,
                build_type=build_type,
                evidence=evidence_objects
            )
            
            self.rig.build_system = build_info
            return f"Set build system: {name} {version} ({build_type})"
        except Exception as e:
            self.logger.error(f"Failed to set build system info: {e}")
            return f"Error setting build system info: {e}"
    
    def add_component(self, name: str, type: str, programming_language: str = "unknown",
                     runtime: str = "unknown", source_files: List[str] = None,
                     output_path: str = "unknown", dependencies: List[str] = None,
                     evidence: List[Dict] = None) -> str:
        """Add a component to the RIG."""
        try:
            # Convert runtime string to enum
            runtime_enum = getattr(Runtime, runtime.upper(), Runtime.UNKNOWN)
            
            # Convert type to ComponentType enum
            from core.schemas import ComponentType
            type_enum = getattr(ComponentType, type.upper(), ComponentType.EXECUTABLE)
            
            # Create evidence object for BuildNode base class
            evidence_obj = Evidence(call_stack=[])
            if evidence and len(evidence) > 0:
                evidence_obj = Evidence(
                    call_stack=evidence[0].get('call_stack', [])
                )
            
            # Create component with required fields (including evidence from BuildNode)
            component = Component(
                name=name,
                type=type_enum,
                programming_language=programming_language,
                runtime=runtime_enum,
                output=name,  # Required field
                output_path=Path(output_path),
                source_files=[Path(f) for f in (source_files or [])],
                external_packages=[],  # Default empty list
                locations=[],  # Default empty list
                test_link_id=None,
                test_link_name=None,
                evidence=evidence_obj,  # Required by BuildNode base class
                depends_on=[]  # Default empty list
            )
            
            # Use RIG's add_component method
            self.rig.add_component(component)
            
            return f"Added component: {name} ({type}, {programming_language})"
        except Exception as e:
            self.logger.error(f"Failed to add component {name}: {e}")
            return f"Error adding component {name}: {e}"
    
    def add_test(self, name: str, framework: str, source_files: List[str] = None,
                output_path: str = "unknown", dependencies: List[str] = None,
                evidence: List[Dict] = None) -> str:
        """Add a test to the RIG."""
        try:
            # Create single evidence object with required call_stack field
            evidence_obj = Evidence(call_stack=[])
            if evidence and len(evidence) > 0:
                # Use the first evidence item's call_stack if available
                evidence_obj = Evidence(
                    call_stack=evidence[0].get('call_stack', [])
                )
            
            test = TestDefinition(
                name=name,
                test_framework=framework,  # Use correct field name
                source_files=[Path(f) for f in (source_files or [])],
                evidence=evidence_obj,  # Single Evidence object, not list
                test_executable=None,  # Will be set later if needed
                components_being_tested=[],  # Will be set later if needed
                test_runner=None  # Will be set later if needed
            )
            
            # Use RIG's add_test method
            self.rig.add_test(test)
            
            return f"Added test: {name} ({framework})"
        except Exception as e:
            self.logger.error(f"Failed to add test {name}: {e}")
            return f"Error adding test {name}: {e}"
    
    def get_rig_summary(self) -> str:
        """Get a summary of the current RIG state."""
        try:
            components_count = len(self.rig.components) if self.rig.components else 0
            tests_count = len(self.rig.tests) if self.rig.tests else 0
            aggregators_count = len(self.rig.aggregators) if self.rig.aggregators else 0
            runners_count = len(self.rig.runners) if self.rig.runners else 0
            utilities_count = len(self.rig.utilities) if self.rig.utilities else 0
            
            return f"RIG Summary: {components_count} components, {tests_count} tests, {aggregators_count} aggregators, {runners_count} runners, {utilities_count} utilities"
        except Exception as e:
            return f"Error getting RIG summary: {e}"


class BaseLLMAgentV5(ABC):
    """Base class for all V5 LLM agents with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path, rig_instance: RIG, agent_name: str, max_retries: int = 3):
        self.repository_path = repository_path.absolute()
        self.rig = rig_instance  # Shared RIG instance
        self.agent_name = agent_name
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"V5_{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        self.rig_tools = RIGTools(rig_instance)  # RIG manipulation tools
        
        # Create agent with all tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.rig_tools, self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle model settings
            usage_limit=None,  # Unlimited
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0  # Deterministic behavior
        )
        
        self.logger.info(f"Initialized V5 agent: {agent_name}")
        self.logger.info(f"RIG state: {self.rig_tools.get_rig_summary()}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        # Remove markdown code block if present
        if response.startswith("```json") and response.endswith("```"):
            response = response[7:-3].strip()
        
        # Try to find the first complete JSON object
        json_start = response.find('{')
        if json_start != -1:
            brace_count = 0
            json_end = 0
            for i, char in enumerate(response[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end > 0:
                response = response[json_start:json_end]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response: {response}")
            raise ValueError(f"Invalid JSON response from {self.agent_name}: {e}")
    
    async def _execute_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Execute agent with retry mechanism for path discovery errors."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1}")
                response = await self.agent.run(prompt)
                
                # For V5, we don't need to parse JSON - the LLM uses tools directly
                # But we might still need to parse some responses for validation
                if response.output.strip():
                    try:
                        result = self._parse_json_response(response.output)
                        return result
                    except:
                        # If not JSON, return the raw response
                        return {"status": "success", "message": response.output}
                else:
                    return {"status": "success", "message": "No output"}
                    
            except FileNotFoundError as e:
                last_error = e
                self.logger.warning(f"Path not found (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries:
                    error_context = f"\n\nIMPORTANT: The path '{e.args[0].split(': ')[-1]}' does not exist. Please check the directory structure first using 'list_dir' before trying to access files or directories."
                    prompt += error_context
                    self.logger.info(f"Updated context with error information, retrying...")
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded for path discovery")
                    raise
                    
            except PermissionError as e:
                last_error = e
                self.logger.warning(f"Path traversal attempt (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries:
                    error_context = f"\n\nSECURITY VIOLATION: You tried to access a path outside the repository root. You MUST stay within the repository directory '{self.repository_path}'. Only access files and directories that are inside this repository. Use relative paths from the repository root."
                    prompt += error_context
                    self.logger.info(f"Updated context with security violation information, retrying...")
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded for path traversal violations")
                    raise
                    
            except Exception as e:
                self.logger.error(f"Non-recoverable error: {e}")
                raise
        
        # This should never be reached, but just in case
        raise last_error
    
    @abstractmethod
    async def execute_phase(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the specific phase logic. Must be implemented by subclasses."""
        pass
