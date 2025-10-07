"""
V6 Base Agent - Phase-Specific Memory Stores Architecture

This module provides the base classes for V6 agents that use phase-specific memory stores
instead of passing large JSON between phases. Each phase maintains its own dedicated object
with tools to manipulate it, completely eliminating context explosion.
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, TypeVar
from abc import ABC, abstractmethod

# Add agentkit-gf to path BEFORE any imports
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
if str(agentkit_gf_path) not in sys.path:
    sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools

logger = logging.getLogger(__name__)

# Generic type for phase stores
T = TypeVar('T', bound='BasePhaseStore')


class BasePhaseStore(ABC):
    """Base class for all phase-specific memory stores."""
    
    def __init__(self):
        self._validation_errors: List[str] = []
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate the store and return any errors."""
        pass
    
    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the store's current state."""
        pass
    
    def is_valid(self) -> bool:
        """Check if the store is valid."""
        self._validation_errors = self.validate()
        return len(self._validation_errors) == 0
    
    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self._validation_errors.copy()


class BaseLLMAgentV6(ABC):
    """Base class for all V6 LLM agents with phase-specific memory stores."""
    
    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        self.repository_path = repository_path
        self.model_settings = model_settings
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize tools
        self.file_tools = FileTools(root_dir=str(repository_path))
        self.process_tools = ProcessTools(root_cwd=str(repository_path))
        
        # Initialize agent with tools
        self.agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools],
            builtin_enums=[],
            model_settings=model_settings,
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0
        )
        
        # Retry configuration - increased for better reliability
        self.max_retries = 10  # Increased from 5 to 10 for better reliability
        self._retry_context = []
    
    @abstractmethod
    def create_phase_store(self) -> BasePhaseStore:
        """Create a new phase store instance."""
        pass
    
    @abstractmethod
    def get_phase_tools(self, phase_store: BasePhaseStore) -> List[Any]:
        """Get the tools available for this phase."""
        pass
    
    @abstractmethod
    def build_prompt(self, phase_store: BasePhaseStore, previous_stores: List[BasePhaseStore]) -> str:
        """Build the prompt for this phase."""
        pass
    
    async def execute_phase(self, previous_stores: List[BasePhaseStore] = None) -> BasePhaseStore:
        """Execute this phase and return the populated phase store."""
        if previous_stores is None:
            previous_stores = []
        
        # Create new phase store
        phase_store = self.create_phase_store()
        
        # Get phase-specific tools
        phase_tools = self.get_phase_tools(phase_store)
        
        # Create agent with phase-specific tools
        agent = DelegatingToolsAgent(
            model="openai:gpt-5-nano",
            tool_sources=[self.file_tools, self.process_tools] + phase_tools,
            builtin_enums=[],
            model_settings=self.model_settings,
            usage_limit=None,
            real_time_log_user=True,
            real_time_log_agent=True,
            temperature=0
        )
        
        # Build prompt
        prompt = self.build_prompt(phase_store, previous_stores)
        
        # Execute with retry mechanism
        result = await self._execute_with_retry(agent, prompt, phase_store)
        
        return result
    
    async def _execute_with_retry(self, agent: DelegatingToolsAgent, prompt: str, phase_store: BasePhaseStore) -> BasePhaseStore:
        """Execute the phase with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
                
                # Add retry context if this is a retry
                if attempt > 0:
                    retry_prompt = self._build_retry_prompt(prompt, attempt)
                else:
                    retry_prompt = prompt
                
                # Execute the agent
                await agent.run(retry_prompt)
                
                # Validate the result
                if phase_store.is_valid():
                    self.logger.info("✅ Phase completed successfully!")
                    # Clear retry context on success
                    self._retry_context = []
                    return phase_store
                else:
                    errors = phase_store.get_validation_errors()
                    self.logger.warning(f"Validation failed: {errors}")
                    if attempt < self.max_retries - 1:
                        self._retry_context.append({
                            'attempt': attempt + 1,
                            'errors': errors,
                            'suggestion': self._get_validation_suggestion(errors)
                        })
                        continue
                    else:
                        raise Exception(f"Validation failed after {self.max_retries} attempts: {errors}")
                        
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    self._retry_context.append({
                        'attempt': attempt + 1,
                        'error': str(e),
                        'suggestion': self._get_error_suggestion(str(e))
                    })
                    continue
                else:
                    raise e
        
        raise Exception(f"Phase failed after {self.max_retries} attempts")
    
    def _build_retry_prompt(self, original_prompt: str, attempt: int) -> str:
        """Build a retry prompt with error context."""
        retry_context = "\n\n".join([
            f"PREVIOUS ERROR (Attempt {ctx['attempt']}): {ctx.get('error', 'Validation failed')}\n"
            f"SUGGESTION: {ctx.get('suggestion', 'Please fix the errors and try again')}"
            for ctx in self._retry_context
        ])
        
        return f"{original_prompt}\n\n{retry_context}"
    
    def _get_validation_suggestion(self, errors: List[str]) -> str:
        """Get a suggestion for validation errors."""
        if not errors:
            return "No specific suggestions available."
        
        suggestions = []
        for error in errors:
            if "required" in error.lower():
                suggestions.append("Make sure to provide all required information")
            elif "invalid" in error.lower():
                suggestions.append("Check the format and validity of the data")
            elif "missing" in error.lower():
                suggestions.append("Ensure all necessary data is provided")
            else:
                suggestions.append("Review the error and correct the issue")
        
        return "; ".join(suggestions)
    
    def _get_error_suggestion(self, error: str) -> str:
        """Generate smart error response with contextual information."""
        return self._generate_smart_error_response(error)
    
    def _generate_smart_error_response(self, error: str) -> str:
        """Generate intelligent error response with contextual help."""
        error_lower = error.lower()
        
        # File not found errors
        if "file not found" in error_lower or "path not found" in error_lower:
            return self._handle_file_not_found_error(error)
        
        # Directory not found errors  
        elif "directory" in error_lower and "not found" in error_lower:
            return self._handle_directory_not_found_error(error)
        
        # Permission errors
        elif "permission denied" in error_lower or "access denied" in error_lower:
            return self._handle_permission_error(error)
        
        # Tool errors
        elif "tool" in error_lower:
            return "Check tool usage and parameters. Use 'list_dir' to explore available files first."
        
        # JSON errors
        elif "json" in error_lower:
            return "Ensure proper JSON formatting. Check for syntax errors in your response."
        
        # Generic error with helpful suggestion
        else:
            return f"Error occurred: {error}. Try using 'list_dir' to explore available files and directories first."
    
    def _handle_file_not_found_error(self, error: str) -> str:
        """Handle file not found errors with smart suggestions."""
        try:
            # Extract the requested file path from error
            import re
            path_match = re.search(r'file not found: (.+)', error)
            if path_match:
                requested_path = path_match.group(1)
                parent_dir = str(Path(requested_path).parent)
                
                # Check if parent directory exists and list available files
                if Path(parent_dir).exists():
                    try:
                        available_files = list(Path(parent_dir).iterdir())
                        file_extensions = {}
                        for file_path in available_files:
                            if file_path.is_file():
                                ext = file_path.suffix
                                if ext not in file_extensions:
                                    file_extensions[ext] = []
                                file_extensions[ext].append(file_path.name)
                        
                        # Get the extension of the requested file
                        requested_ext = Path(requested_path).suffix
                        if requested_ext and requested_ext in file_extensions:
                            return f"File '{Path(requested_path).name}' not found in {parent_dir}. Available {requested_ext} files: {file_extensions[requested_ext][:5]}. Use 'list_dir' to see all files."
                        else:
                            return f"File '{Path(requested_path).name}' not found in {parent_dir}. Available files: {[f.name for f in available_files if f.is_file()][:5]}. Use 'list_dir' to explore."
                    except Exception:
                        return f"File not found: {requested_path}. Use 'list_dir' to see available files in the directory."
                else:
                    return f"Parent directory {parent_dir} does not exist. Use 'list_dir' to explore the repository structure."
        except Exception:
            pass
        
        return f"File not found: {error}. Use 'list_dir' to explore available files and directories."
    
    def _handle_directory_not_found_error(self, error: str) -> str:
        """Handle directory not found errors with smart suggestions."""
        try:
            import re
            path_match = re.search(r'directory.*not found.*?([^\s]+)', error)
            if path_match:
                requested_path = path_match.group(1)
                parent_dir = str(Path(requested_path).parent)
                
                if Path(parent_dir).exists():
                    try:
                        available_dirs = [d.name for d in Path(parent_dir).iterdir() if d.is_dir()]
                        return f"Directory '{Path(requested_path).name}' not found in {parent_dir}. Available directories: {available_dirs[:5]}. Use 'list_dir' to see all directories."
                    except Exception:
                        return f"Directory not found: {requested_path}. Use 'list_dir' to see available directories."
                else:
                    return f"Parent directory {parent_dir} does not exist. Use 'list_dir' to explore the repository structure."
        except Exception:
            pass
        
        return f"Directory not found: {error}. Use 'list_dir' to explore available directories."
    
    def _handle_permission_error(self, error: str) -> str:
        """Handle permission errors with smart suggestions."""
        return f"Permission denied: {error}. This file/directory may be protected or outside the repository. Stay within the repository boundaries and use relative paths only."
