"""
Phase 3: Artifact Discovery Tools

This module provides deterministic tools for analyzing build configurations
to discover and classify artifacts without assuming anything has been built.

Key Design Principles:
- Completely deterministic - NO LLM calls inside tools
- LLM controls extraction strategy parameters
- Smart filtering to prevent token overflow
- Evidence-based artifact discovery
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json


class Phase3ArtifactTools:
    """
    Deterministic tools for artifact discovery from build configurations.
    
    The LLM controls the extraction strategy, but the tool execution is
    completely deterministic with no AI/LLM calls.
    """
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("Phase3ArtifactTools")
    
    def analyze_build_configurations(self, 
                                   search_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze build configuration files using LLM-defined search patterns and regexes.
        
        Args:
            search_configs: List of search configurations, each containing:
                - patterns: List of file patterns to search (e.g., ["*.cmake", "CMakeLists.txt"])
                - content_regexes: List of regex patterns to match within files (e.g., ["add_executable\\(.*\\)"])
            
        Returns:
            Dict containing structured data with matched files and lines
        """
        try:
            self.logger.info(f"Analyzing build configurations with {len(search_configs)} search configs")
            
            results = []
            
            for config in search_configs:
                patterns = config.get("patterns", [])
                content_regexes = config.get("content_regexes", [])
                
                self.logger.info(f"Processing config: patterns={patterns}, regexes={content_regexes}")
                
                # Find all matching files for this config
                found_files = self._find_config_files(patterns)
                self.logger.info(f"Found {len(found_files)} files matching patterns: {patterns}")
                
                # Process each file
                config_results = {
                    "search_config": config,
                    "matched_files": []
                }
                
                for file_path in found_files:
                    try:
                        matches = self._extract_matching_lines(file_path, content_regexes)
                        if matches:
                            config_results["matched_files"].append({
                                "file_path": str(file_path.relative_to(self.repository_path)),
                                "matches": matches
                            })
                    except Exception as e:
                        self.logger.error(f"Error processing {file_path}: {e}")
                        continue
                
                results.append(config_results)
            
            return {
                "search_results": results,
                "metadata": {
                    "total_configs_processed": len(search_configs),
                    "total_files_analyzed": sum(len(r["matched_files"]) for r in results),
                    "repository_path": str(self.repository_path)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in analyze_build_configurations: {e}")
            return {
                "search_results": [],
                "metadata": {
                    "error": str(e),
                    "total_configs_processed": 0,
                    "total_files_analyzed": 0
                }
            }
    
    def query_build_system(self, 
                          build_system: str, 
                          query_commands: List[str]) -> Dict[str, Any]:
        """
        Execute build system queries to gather additional information.
        
        Args:
            build_system: The build system to query (e.g., "cmake", "maven", "gradle")
            query_commands: List of commands to execute (e.g., ["--help", "--version"])
        
        Returns:
            Dict containing command outputs and metadata
        """
        try:
            self.logger.info(f"Querying build system: {build_system} with commands: {query_commands}")
            
            results = {}
            for command in query_commands:
                try:
                    # Construct full command
                    full_command = [build_system] + command.split()
                    
                    # Execute command
                    result = subprocess.run(
                        full_command,
                        cwd=self.repository_path,
                        capture_output=True,
                        text=True,
                        timeout=30  # 30 second timeout
                    )
                    
                    results[command] = {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.returncode == 0
                    }
                    
                except subprocess.TimeoutExpired:
                    results[command] = {
                        "return_code": -1,
                        "stdout": "",
                        "stderr": "Command timed out after 30 seconds",
                        "success": False
                    }
                except FileNotFoundError:
                    results[command] = {
                        "return_code": -1,
                        "stdout": "",
                        "stderr": f"Build system '{build_system}' not found",
                        "success": False
                    }
                except Exception as e:
                    results[command] = {
                        "return_code": -1,
                        "stdout": "",
                        "stderr": str(e),
                        "success": False
                    }
            
            return {
                "build_system": build_system,
                "query_results": results,
                "metadata": {
                    "total_commands": len(query_commands),
                    "successful_commands": sum(1 for r in results.values() if r["success"]),
                    "repository_path": str(self.repository_path)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in query_build_system: {e}")
        return {
                "build_system": build_system,
                "query_results": {},
                "metadata": {
                    "error": str(e),
                    "total_commands": 0,
                    "successful_commands": 0
                }
            }
    
    def _find_config_files(self, patterns: List[str]) -> List[Path]:
        """Find all files matching the given patterns."""
        found_files = []
        
        for pattern in patterns:
            if "*" in pattern:
                # Glob pattern
                for file_path in self.repository_path.rglob(pattern):
                    if file_path.is_file():
                        found_files.append(file_path)
            else:
                # Exact filename
                file_path = self.repository_path / pattern
                if file_path.exists() and file_path.is_file():
                    found_files.append(file_path)
        
        # Remove duplicates and sort
        found_files = sorted(list(set(found_files)))
        return found_files
    
    def _extract_matching_lines(self, 
                              file_path: Path, 
                              content_regexes: List[str]) -> List[Dict[str, Any]]:
        """Extract lines matching the given regex patterns from a file."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines or not content_regexes:
                return []
            
            matches = []
            
            for i, line in enumerate(lines):
                line_content = line.strip()
                if not line_content:  # Skip empty lines
                    continue
                
                # Check each regex pattern
                for regex_pattern in content_regexes:
                    try:
                        if re.search(regex_pattern, line_content, re.IGNORECASE):
                            matches.append({
                                "line_number": i + 1,
                                "content": line_content,
                                "matched_regex": regex_pattern
                            })
                            break  # Only match once per line
                    except re.error as e:
                        self.logger.warning(f"Invalid regex pattern '{regex_pattern}': {e}")
                        continue
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error extracting matching lines from {file_path}: {e}")
            return []