# Phase 5 Tools: Source Structure Discovery
# Deterministic tools for source structure discovery

"""
Phase 5 Tools: Source Structure Discovery

This module provides deterministic tools for Phase 5:
- discover_source_structure: Discovers source code structure and identifies potential components

All tools are pure functions with no LLM calls.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import glob
import os


class Phase5Tools:
    """Phase 5 Tools for Source Structure Discovery"""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("Phase5Tools")
    
    def discover_source_structure(self, 
                                exploration_scope: Dict[str, Any],
                                languages_detected: Dict[str, Any],
                                build_systems_detected: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discover source code structure and identify potential components
        
        Args:
            exploration_scope: Output from Phase 4 (exploration scope)
            languages_detected: Output from Phase 1 (languages detected)
            build_systems_detected: Output from Phase 2 (build systems detected)
            
        Returns:
            Dictionary with source structure and component hints
        """
        
        self.logger.info(f"Discovering source structure for {self.repository_path}")
        
        # Get source directories from exploration scope
        source_directories = exploration_scope.get("exploration_scope", {}).get("source_directories", [])
        
        # Analyze each source directory
        source_structure = []
        component_hints = []
        
        for source_dir in source_directories:
            source_path = self.repository_path / source_dir
            if source_path.exists():
                dir_analysis = self._analyze_source_directory(source_path, source_dir, languages_detected)
                source_structure.append(dir_analysis)
                
                # Extract component hints from this directory
                hints = self._extract_component_hints(dir_analysis, build_systems_detected)
                component_hints.extend(hints)
        
        return {
            "source_structure": {
                "source_directories": source_structure,
                "component_hints": component_hints,
                "total_directories": len(source_structure),
                "total_components": len(component_hints)
            },
            "confidence_verification": {
                "all_source_dirs_explored": len(source_structure) == len(source_directories),
                "components_identified": len(component_hints) > 0,
                "ready_for_phase_6": True
            }
        }
    
    def _analyze_source_directory(self, source_path: Path, source_dir: str, 
                                languages_detected: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single source directory"""
        
        # Get detected languages
        languages = languages_detected.get("languages_detected", {})
        detected_languages = [lang for lang, data in languages.items() 
                            if data.get("detected", False)]
        
        # Find source files by language
        source_files = []
        language_files = {}
        
        for lang in detected_languages:
            lang_files = self._find_language_files(source_path, lang)
            language_files[lang] = lang_files
            source_files.extend(lang_files)
        
        # Determine primary language for this directory
        primary_language = self._determine_primary_language(language_files)
        
        # Find potential components
        components = self._find_potential_components(source_path, source_files, primary_language)
        
        # Find dependencies
        dependencies = self._find_dependencies(source_path, source_files, primary_language)
        
        return {
            "path": source_dir,
            "language": primary_language,
            "components": components,
            "files": source_files,
            "dependencies": dependencies,
            "language_files": language_files,
            "total_files": len(source_files),
            "exploration_complete": True
        }
    
    def _find_language_files(self, source_path: Path, language: str) -> List[str]:
        """Find source files for a specific language"""
        
        # Language-specific file extensions
        language_extensions = {
            "C++": ["*.cpp", "*.cxx", "*.cc", "*.c++", "*.h", "*.hpp", "*.hxx", "*.hh"],
            "Java": ["*.java"],
            "Python": ["*.py", "*.pyi"],
            "JavaScript": ["*.js", "*.jsx", "*.ts", "*.tsx"],
            "Go": ["*.go"],
            "Rust": ["*.rs"],
            "C#": ["*.cs"],
            "C": ["*.c", "*.h"],
            "TypeScript": ["*.ts", "*.tsx"],
            "Kotlin": ["*.kt", "*.kts"],
            "Scala": ["*.scala"],
            "PHP": ["*.php"],
            "Ruby": ["*.rb"],
            "Swift": ["*.swift"],
            "Objective-C": ["*.m", "*.mm", "*.h"]
        }
        
        extensions = language_extensions.get(language, [])
        files = []
        
        for extension in extensions:
            pattern = str(source_path / "**" / extension)
            matches = glob.glob(pattern, recursive=True)
            files.extend([str(Path(m).relative_to(self.repository_path)) for m in matches])
        
        return sorted(files)
    
    def _determine_primary_language(self, language_files: Dict[str, List[str]]) -> str:
        """Determine the primary language for a directory"""
        
        if not language_files:
            return "unknown"
        
        # Find language with most files
        primary_language = max(language_files.keys(), key=lambda k: len(language_files[k]))
        
        return primary_language
    
    def _find_potential_components(self, source_path: Path, source_files: List[str], 
                                 primary_language: str) -> List[str]:
        """Find potential components in the source directory"""
        
        components = []
        
        # Language-specific component patterns
        component_patterns = {
            "C++": ["main", "app", "application", "lib", "library", "core", "utils", "common"],
            "Java": ["Main", "App", "Application", "Service", "Controller", "Model", "Util"],
            "Python": ["main", "app", "application", "core", "utils", "common", "lib"],
            "JavaScript": ["index", "app", "main", "server", "client", "utils", "lib"],
            "Go": ["main", "app", "server", "client", "utils", "common"],
            "Rust": ["main", "lib", "bin", "utils", "common"],
            "C#": ["Program", "App", "Application", "Service", "Controller", "Model"]
        }
        
        patterns = component_patterns.get(primary_language, [])
        
        for file_path in source_files:
            file_name = Path(file_path).stem.lower()
            
            # Check if file matches component patterns
            for pattern in patterns:
                if pattern.lower() in file_name:
                    component_name = self._extract_component_name(file_path, pattern)
                    if component_name and component_name not in components:
                        components.append(component_name)
        
        return sorted(components)
    
    def _extract_component_name(self, file_path: str, pattern: str) -> Optional[str]:
        """Extract component name from file path"""
        
        file_name = Path(file_path).stem
        
        # Simple extraction logic - can be enhanced
        if pattern.lower() in file_name.lower():
            return file_name
        
        return None
    
    def _find_dependencies(self, source_path: Path, source_files: List[str], 
                         primary_language: str) -> List[str]:
        """Find dependencies in source files"""
        
        dependencies = []
        
        # Language-specific dependency patterns
        dependency_patterns = {
            "C++": ["#include", "import"],
            "Java": ["import", "package"],
            "Python": ["import", "from"],
            "JavaScript": ["import", "require", "from"],
            "Go": ["import"],
            "Rust": ["use", "mod"],
            "C#": ["using", "namespace"]
        }
        
        patterns = dependency_patterns.get(primary_language, [])
        
        for file_path in source_files:
            full_path = self.repository_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for pattern in patterns:
                            # Simple dependency extraction - can be enhanced
                            lines = content.split('\n')
                            for line in lines:
                                if pattern in line:
                                    # Extract dependency name (simplified)
                                    dep = self._extract_dependency_name(line, pattern)
                                    if dep and dep not in dependencies:
                                        dependencies.append(dep)
                except Exception as e:
                    self.logger.warning(f"Could not read file {file_path}: {e}")
        
        return sorted(dependencies)
    
    def _extract_dependency_name(self, line: str, pattern: str) -> Optional[str]:
        """Extract dependency name from import/include line"""
        
        # Simple extraction - can be enhanced with proper parsing
        try:
            if pattern in line:
                # Extract the part after the pattern
                parts = line.split(pattern)
                if len(parts) > 1:
                    dep_part = parts[1].strip()
                    # Extract the first word/identifier
                    dep_name = dep_part.split()[0] if dep_part.split() else None
                    return dep_name
        except Exception:
            pass
        
        return None
    
    def _extract_component_hints(self, dir_analysis: Dict[str, Any], 
                               build_systems_detected: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract component hints from directory analysis"""
        
        hints = []
        components = dir_analysis.get("components", [])
        source_files = dir_analysis.get("files", [])
        primary_language = dir_analysis.get("language", "unknown")
        
        for component in components:
            # Find source files for this component
            component_files = [f for f in source_files if component.lower() in f.lower()]
            
            # Determine component type
            component_type = self._determine_component_type(component, component_files, primary_language)
            
            hint = {
                "name": component,
                "type": component_type,
                "source_files": component_files,
                "language": primary_language,
                "directory": dir_analysis.get("path", ""),
                "evidence": f"Found in {dir_analysis.get('path', '')} directory"
            }
            
            hints.append(hint)
        
        return hints
    
    def _determine_component_type(self, component: str, source_files: List[str], 
                                language: str) -> str:
        """Determine component type based on name and files"""
        
        component_lower = component.lower()
        
        # Type determination logic
        if any(keyword in component_lower for keyword in ["main", "app", "application", "server"]):
            return "executable"
        elif any(keyword in component_lower for keyword in ["lib", "library", "core", "common"]):
            return "library"
        elif any(keyword in component_lower for keyword in ["test", "spec", "unit"]):
            return "test"
        elif any(keyword in component_lower for keyword in ["util", "helper", "tool"]):
            return "utility"
        else:
            # Default based on file analysis
            if any("main" in f.lower() for f in source_files):
                return "executable"
            else:
                return "library"
