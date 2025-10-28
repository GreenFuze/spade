"""
CMakeParser class for parsing CMakeLists.txt files to extract evidence-based information.
Replaces heuristics with deterministic parsing of CMake commands.
"""

import re
from itertools import chain
from pathlib import Path
from typing import Dict, List, Any, Optional


class CMakeParser:
    """
    Parser for CMakeLists.txt files to extract evidence-based information.
    Replaces heuristics with deterministic parsing of CMake commands.
    """
    
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.custom_targets: Dict[str, Dict[str, Any]] = {}
        self.find_packages: List[Dict[str, Any]] = []
        self.add_tests: List[Dict[str, Any]] = []
        self.target_link_libraries: Dict[str, List[str]] = {}
        self.output_directories: Dict[str, str] = {}
        
    def parse_all_cmake_files(self) -> None:
        """Parse all CMakeLists.txt and *.cmake files in the source directory."""
        cmake_files = list(chain(
            self.source_dir.rglob("CMakeLists.txt"),
            self.source_dir.rglob("*.cmake")
        ))
        if not cmake_files:
            raise ValueError(f"No CMakeLists.txt or *.cmake files found in {self.source_dir}")
            
        for cmake_file in cmake_files:
            self._parse_cmake_file(cmake_file)
    
    def _parse_cmake_file(self, cmake_file: Path) -> None:
        """Parse a single CMakeLists.txt file."""
        try:
            with open(cmake_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read {cmake_file}: {e}")
        
        # Parse different CMake commands
        self._parse_add_custom_target(content, cmake_file)
        self._parse_add_jar(content, cmake_file)
        self._parse_find_package(content, cmake_file)
        self._parse_add_test(content, cmake_file)
        self._parse_target_link_libraries(content, cmake_file)
        self._parse_output_directories(content, cmake_file)
    
    def _parse_add_custom_target(self, content: str, file_path: Path) -> None:
        """Parse add_custom_target() calls."""
        # Pattern to match add_custom_target with various parameters (including hyphens and dots in target names)
        pattern = r'add_custom_target\s*\(\s*([\w.-]+)\s*(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            target_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.custom_targets[target_name] = {
                'name': target_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'has_commands': 'COMMAND' in params,
                'has_depends': 'DEPENDS' in params,
                'has_output': 'OUTPUT' in params,
                'has_byproducts': 'BYPRODUCTS' in params
            }
    
    def _parse_add_jar(self, content: str, file_path: Path) -> None:
        """Parse add_jar() calls (Java JAR creation)."""
        # Pattern to match add_jar calls with variable names like ${TARGET_NAME}
        pattern = r'add_jar\s*\(\s*(\$\{[^}]+\})'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            target_name = match.group(1)
            
            # Store as custom target with Java language indicator
            self.custom_targets[target_name] = {
                'name': target_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': {},  # Simplified - just mark as JAR
                'has_commands': False,  # add_jar doesn't have COMMAND
                'has_depends': False,  # Simplified
                'has_output': True,  # JAR targets have output
                'has_byproducts': False,  # add_jar doesn't have BYPRODUCTS
                'is_jar': True  # Mark as JAR target
            }
    
    def _parse_find_package(self, content: str, file_path: Path) -> None:
        """Parse find_package() calls."""
        # Pattern to match find_package with package name and options (including hyphens)
        pattern = r'find_package\s*\(\s*([\w-]+)\s*(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            package_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.find_packages.append({
                'name': package_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'is_required': 'REQUIRED' in params,
                'components': params.get('COMPONENTS', [])
            })
    
    def _parse_add_test(self, content: str, file_path: Path) -> None:
        """Parse add_test() calls."""
        # Pattern to match add_test with NAME and COMMAND (including hyphens)
        pattern = r'add_test\s*\(\s*NAME\s+([\w-]+)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            test_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = self._parse_cmake_parameters(params_str)
            
            self.add_tests.append({
                'name': test_name,
                'file': file_path,
                'line': self._get_line_number(content, match.start()),
                'parameters': params,
                'command': params.get('COMMAND', []),
                'working_directory': params.get('WORKING_DIRECTORY', '')
            })
    
    def _parse_target_link_libraries(self, content: str, file_path: Path) -> None:
        """Parse target_link_libraries() calls."""
        # Pattern to match target_link_libraries (including hyphens)
        pattern = r'target_link_libraries\s*\(\s*([\w-]+)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            target_name = match.group(1)
            libraries_str = match.group(2)
            
            # Parse library names (split by whitespace, handle quoted strings)
            libraries = self._parse_cmake_list(libraries_str)
            
            if target_name not in self.target_link_libraries:
                self.target_link_libraries[target_name] = []
            self.target_link_libraries[target_name].extend(libraries)
    
    def _parse_output_directories(self, content: str, file_path: Path) -> None:
        """Parse CMAKE_*_OUTPUT_DIRECTORY settings."""
        # Pattern to match set(CMAKE_*_OUTPUT_DIRECTORY ...)
        pattern = r'set\s*\(\s*(CMAKE_\w+_OUTPUT_DIRECTORY)\s+(.*?)\)'
        
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            var_name = match.group(1)
            value = match.group(2).strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            self.output_directories[var_name] = value
    
    def _parse_cmake_parameters(self, params_str: str) -> Dict[str, List[str]]:
        """Parse CMake function parameters into a dictionary."""
        params: Dict[str, List[str]] = {}
        current_key: Optional[str] = None
        current_values: List[str] = []
        
        # Split by whitespace but handle quoted strings
        tokens = self._tokenize_cmake_string(params_str)
        
        for token in tokens:
            if token.upper() in ['COMMAND', 'DEPENDS', 'OUTPUT', 'BYPRODUCTS', 'COMPONENTS', 
                               'REQUIRED', 'WORKING_DIRECTORY', 'NAME']:
                # Save previous key-value pair
                if current_key:
                    params[current_key] = current_values
                
                # Start new key
                current_key = token.upper()
                current_values = []
            else:
                current_values.append(token)
        
        # Save last key-value pair
        if current_key:
            params[current_key] = current_values
        
        return params
    
    def _parse_cmake_list(self, list_str: str) -> List[str]:
        """Parse a CMake list (space-separated values, handling quotes)."""
        return self._tokenize_cmake_string(list_str)
    
    def _tokenize_cmake_string(self, text: str) -> List[str]:
        """Tokenize CMake string handling quotes and variables."""
        tokens: List[str] = []
        current_token = ""
        in_quotes = False
        quote_char: Optional[str] = None
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if not in_quotes:
                if char in ['"', "'"]:
                    in_quotes = True
                    quote_char = char
                    current_token += char
                elif char.isspace():
                    if current_token.strip():
                        tokens.append(current_token.strip())
                        current_token = ""
                else:
                    current_token += char
            else:
                current_token += char
                if char == quote_char and (i == 0 or text[i-1] != '\\'):
                    in_quotes = False
                    quote_char = None
            
            i += 1
        
        if current_token.strip():
            tokens.append(current_token.strip())
        
        return tokens
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a character position in content."""
        return content[:position].count('\n') + 1
    
    def get_custom_target_info(self, target_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a custom target."""
        return self.custom_targets.get(target_name)
    
    def get_find_package_info(self, package_name: str) -> List[Dict[str, Any]]:
        """Get information about find_package calls for a package."""
        return [pkg for pkg in self.find_packages if pkg['name'] == package_name]
    
    def get_test_info(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an add_test call."""
        for test in self.add_tests:
            if test['name'] == test_name:
                return test
        return None
    
    def get_target_dependencies(self, target_name: str) -> List[str]:
        """Get dependencies for a target from target_link_libraries."""
        return self.target_link_libraries.get(target_name, [])
    
    def get_output_directory(self, directory_type: str) -> Optional[str]:
        """Get output directory for a specific type (RUNTIME, LIBRARY, etc.)."""
        return self.output_directories.get(f"CMAKE_{directory_type}_OUTPUT_DIRECTORY")
