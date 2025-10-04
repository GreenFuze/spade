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
if str(agentkit_gf_path) not in sys.path:
    sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools


class BaseLLMAgentV4(ABC):
    """Base class for all V4 LLM agents with common functionality."""
    
    def __init__(self, repository_path: Path, agent_name: str, max_retries: int = 3):
        self.repository_path = repository_path.absolute()
        self.agent_name = agent_name
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"V4_{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create tools
        self.file_tools = FileTools(root_dir=str(self.repository_path))
        self.process_tools = ProcessTools(root_cwd=str(self.repository_path))
        
        # Create agent with direct tools (no delegate_ops)
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=None,
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0
        )
        
        # Note: pydantic_ai has a hardcoded default limit of 50 requests
        # We need to work within this limitation
        
        # Context management for large repositories
        self._current_context = None
        self._context_history = []
    
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
            
            # Find the first complete JSON object
            # Look for the first { and find the matching }
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
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response: {response}")
            raise ValueError(f"Invalid JSON response from {self.agent_name}: {e}")
    
    def _reset_context(self):
        """Reset agent context to prevent context explosion."""
        # Clear any accumulated context
        self._current_context = None
        self.logger.info("Context reset - starting fresh exploration")
    
    def _set_context_scope(self, scope: str):
        """Set the current exploration scope to prevent context mixing."""
        self._current_context = scope
        self.logger.info(f"Context scope set to: {scope}")
    
    def _is_context_clean(self) -> bool:
        """Check if context is clean (no accumulated state)."""
        return self._current_context is None
    
    async def _execute_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Execute agent with retry mechanism for path discovery errors."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1}")
                response = await self.agent.run(prompt)
                result = self._parse_json_response(response.output)
                return result
                
            except FileNotFoundError as e:
                last_error = e
                self.logger.warning(f"Path not found (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries:
                    # Update context with the non-existent path and retry
                    error_context = f"\n\nIMPORTANT: The path '{e.args[0].split(': ')[-1]}' does not exist. Please check the directory structure first using 'list_dir' before trying to access files or directories."
                    prompt += error_context
                    self.logger.info(f"Updated context with error information, retrying...")
                else:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded for path discovery")
                    raise
                    
            except PermissionError as e:
                # Path traversal security violation - add recovery mechanism
                last_error = e
                self.logger.warning(f"Path traversal attempt (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries:
                    # Update context with security violation and retry
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
