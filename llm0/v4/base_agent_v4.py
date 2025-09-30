#!/usr/bin/env python3
"""
Base LLM Agent V4 - Common functionality for all V4 agents.

This module provides the base class for all V4 agents with common functionality
and ensures no direct pydantic_ai usage - only agentkit-gf.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

# Add agentkit-gf to path BEFORE any imports
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools


class BaseLLMAgentV4(ABC):
    """Base class for all V4 LLM agents with common functionality."""
    
    def __init__(self, repository_path: Path, agent_name: str):
        self.repository_path = repository_path.absolute()
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"V4_{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent - NO direct pydantic_ai usage, only agentkit-gf
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,  # Let agentkit-gf handle this
            usage_limit=None,  # Unlimited usage
            real_time_log_user=True,
            real_time_log_agent=True
        )
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
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
            raise ValueError(f"Invalid JSON response from {self.agent_name}: {e}")
    
    @abstractmethod
    async def execute_phase(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the specific phase logic. Must be implemented by subclasses."""
        pass
