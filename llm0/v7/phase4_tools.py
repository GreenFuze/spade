# Phase 4 Tools: Exploration Scope Definition
# Deterministic tools for exploration scope definition

"""
Phase 4 Tools: Exploration Scope Definition

This module provides deterministic tools for Phase 4:
- define_exploration_scope: Defines exploration scope and strategy for subsequent phases

All tools are pure functions with no LLM calls.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import os


class Phase4Tools:
    """Phase 4 Tools for Exploration Scope Definition"""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("Phase4Tools")
    
    def define_exploration_scope(self, 
                               languages_detected: Dict[str, Any],
                               build_systems_detected: Dict[str, Any],
                               architecture_classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Define exploration scope and strategy for subsequent phases
        
        Args:
            languages_detected: Output from Phase 1 (languages detected)
            build_systems_detected: Output from Phase 2 (build systems detected)
            architecture_classification: Output from Phase 3 (architecture classification)
            
        Returns:
            Dictionary with exploration scope and strategy
        """
        
        self.logger.info(f"Defining exploration scope for {self.repository_path}")
        
        # Analyze directory structure
        directory_analysis = self._analyze_directory_structure()
        
        # Identify source directories
        source_directories = self._identify_source_directories(directory_analysis, languages_detected)
        
        # Identify test directories
        test_directories = self._identify_test_directories(directory_analysis)
        
        # Identify build directories
        build_directories = self._identify_build_directories(directory_analysis, build_systems_detected)
        
        # Identify config directories
        config_directories = self._identify_config_directories(directory_analysis, build_systems_detected)
        
        # Define priority exploration
        priority_exploration = self._define_priority_exploration(
            source_directories, test_directories, architecture_classification
        )
        
        # Define skip directories
        skip_directories = self._define_skip_directories(
            build_directories, config_directories, directory_analysis
        )
        
        # Identify entry points
        entry_points = self._identify_entry_points(
            source_directories, build_systems_detected, languages_detected
        )
        
        # Define exploration strategy
        exploration_strategy = self._define_exploration_strategy(
            architecture_classification, source_directories, test_directories
        )
        
        return {
            "exploration_scope": {
                "source_directories": source_directories,
                "test_directories": test_directories,
                "build_directories": build_directories,
                "config_directories": config_directories,
                "priority_exploration": priority_exploration,
                "skip_directories": skip_directories
            },
            "entry_points": entry_points,
            "exploration_strategy": exploration_strategy,
            "confidence_verification": {
                "scope_defined": True,
                "entry_points_identified": len(entry_points.get("main_files", [])) > 0,
                "ready_for_phase_5": True
            }
        }
    
    def _analyze_directory_structure(self) -> Dict[str, Any]:
        """Analyze the directory structure of the repository"""
        
        directories = []
        files = []
        
        def scan_directory(path: Path, depth: int = 0, max_depth: int = 3):
            if depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        directories.append({
                            "path": str(item.relative_to(self.repository_path)),
                            "name": item.name,
                            "depth": depth
                        })
                        scan_directory(item, depth + 1, max_depth)
                    else:
                        files.append({
                            "path": str(item.relative_to(self.repository_path)),
                            "name": item.name,
                            "extension": item.suffix
                        })
            except PermissionError:
                pass
        
        scan_directory(self.repository_path)
        
        return {
            "directories": directories,
            "files": files,
            "total_directories": len(directories),
            "total_files": len(files)
        }
    
    def _identify_source_directories(self, directory_analysis: Dict[str, Any], 
                                   languages_detected: Dict[str, Any]) -> List[str]:
        """Identify source directories based on structure and languages"""
        
        source_dirs = []
        directories = directory_analysis.get("directories", [])
        
        # Common source directory patterns
        source_patterns = [
            "src", "source", "sources", "lib", "library", "libraries",
            "core", "main", "app", "application", "bin", "include",
            "headers", "public", "private", "internal"
        ]
        
        # Language-specific patterns
        language_patterns = {
            "C++": ["cpp", "cxx", "cc", "c++"],
            "Java": ["java", "javac", "src/main/java"],
            "Python": ["python", "py", "src"],
            "JavaScript": ["js", "javascript", "src", "lib"],
            "Go": ["go", "golang", "cmd", "pkg"],
            "Rust": ["rust", "src", "examples"],
            "C#": ["csharp", "cs", "src"]
        }
        
        # Get detected languages
        languages = languages_detected.get("languages_detected", {})
        detected_languages = [lang for lang, data in languages.items() 
                            if data.get("detected", False)]
        
        for directory in directories:
            dir_name = directory["name"].lower()
            dir_path = directory["path"].lower()
            
            # Check common source patterns
            if any(pattern in dir_name for pattern in source_patterns):
                source_dirs.append(directory["path"])
                continue
            
            # Check language-specific patterns
            for lang in detected_languages:
                if lang in language_patterns:
                    for pattern in language_patterns[lang]:
                        if pattern in dir_name or pattern in dir_path:
                            source_dirs.append(directory["path"])
                            break
        
        # Remove duplicates and sort
        return sorted(list(set(source_dirs)))
    
    def _identify_test_directories(self, directory_analysis: Dict[str, Any]) -> List[str]:
        """Identify test directories"""
        
        test_dirs = []
        directories = directory_analysis.get("directories", [])
        
        # Common test directory patterns
        test_patterns = [
            "test", "tests", "testing", "spec", "specs", "specification",
            "unit", "integration", "e2e", "end-to-end", "acceptance",
            "fixtures", "mocks", "stubs", "testdata", "test_data"
        ]
        
        for directory in directories:
            dir_name = directory["name"].lower()
            
            if any(pattern in dir_name for pattern in test_patterns):
                test_dirs.append(directory["path"])
        
        return sorted(list(set(test_dirs)))
    
    def _identify_build_directories(self, directory_analysis: Dict[str, Any], 
                                  build_systems_detected: Dict[str, Any]) -> List[str]:
        """Identify build directories"""
        
        build_dirs = []
        directories = directory_analysis.get("directories", [])
        
        # Common build directory patterns
        build_patterns = [
            "build", "builds", "dist", "distrib", "out", "output", "outputs",
            "target", "targets", "obj", "objects", "bin", "bins",
            "cmake-build-*", "bazel-*", "node_modules"
        ]
        
        for directory in directories:
            dir_name = directory["name"].lower()
            
            if any(pattern.replace("*", "") in dir_name for pattern in build_patterns):
                build_dirs.append(directory["path"])
        
        return sorted(list(set(build_dirs)))
    
    def _identify_config_directories(self, directory_analysis: Dict[str, Any], 
                                   build_systems_detected: Dict[str, Any]) -> List[str]:
        """Identify configuration directories"""
        
        config_dirs = []
        directories = directory_analysis.get("directories", [])
        
        # Common config directory patterns
        config_patterns = [
            "config", "configs", "configuration", "conf", "settings",
            "scripts", "tools", "utils", "utilities", "misc",
            "docs", "documentation", "doc", "examples", "samples"
        ]
        
        for directory in directories:
            dir_name = directory["name"].lower()
            
            if any(pattern in dir_name for pattern in config_patterns):
                config_dirs.append(directory["path"])
        
        return sorted(list(set(config_dirs)))
    
    def _define_priority_exploration(self, source_directories: List[str], 
                                   test_directories: List[str],
                                   architecture_classification: Dict[str, Any]) -> List[str]:
        """Define priority exploration order"""
        
        priority = []
        
        # Add source directories first
        priority.extend(source_directories)
        
        # Add test directories second
        priority.extend(test_directories)
        
        # Add other directories based on architecture type
        arch_type = architecture_classification.get("architecture_classification", {}).get("type", "application")
        
        if arch_type == "framework":
            # For frameworks, prioritize API and plugin directories
            priority.extend(["api", "plugin", "extension", "binding"])
        elif arch_type == "library":
            # For libraries, prioritize include and src directories
            priority.extend(["include", "headers", "public"])
        elif arch_type == "tool":
            # For tools, prioritize command-line and utility directories
            priority.extend(["cli", "cmd", "tool", "util"])
        
        return priority
    
    def _define_skip_directories(self, build_directories: List[str], 
                               config_directories: List[str],
                               directory_analysis: Dict[str, Any]) -> List[str]:
        """Define directories to skip during exploration"""
        
        skip_dirs = []
        
        # Always skip build directories
        skip_dirs.extend(build_directories)
        
        # Skip common non-source directories
        common_skip_patterns = [
            ".git", ".svn", ".hg", ".bzr",  # Version control
            "node_modules", "vendor", "deps",  # Dependencies
            "tmp", "temp", "cache", "logs",  # Temporary files
            "coverage", "reports", "profiles"  # Generated reports
        ]
        
        directories = directory_analysis.get("directories", [])
        for directory in directories:
            dir_name = directory["name"].lower()
            
            if any(pattern in dir_name for pattern in common_skip_patterns):
                skip_dirs.append(directory["path"])
        
        return sorted(list(set(skip_dirs)))
    
    def _identify_entry_points(self, source_directories: List[str], 
                             build_systems_detected: Dict[str, Any],
                             languages_detected: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify entry points for the repository"""
        
        entry_points = {
            "main_files": [],
            "config_files": [],
            "build_files": []
        }
        
        # Get detected languages
        languages = languages_detected.get("languages_detected", {})
        detected_languages = [lang for lang, data in languages.items() 
                            if data.get("detected", False)]
        
        # Language-specific main file patterns
        main_file_patterns = {
            "C++": ["main.cpp", "main.c", "main.cxx", "main.cc"],
            "Java": ["Main.java", "App.java", "Application.java"],
            "Python": ["main.py", "__main__.py", "app.py", "run.py"],
            "JavaScript": ["index.js", "main.js", "app.js", "server.js"],
            "Go": ["main.go"],
            "Rust": ["main.rs", "lib.rs"],
            "C#": ["Program.cs", "Main.cs", "App.cs"]
        }
        
        # Find main files in source directories
        for source_dir in source_directories:
            source_path = self.repository_path / source_dir
            if source_path.exists():
                for lang in detected_languages:
                    if lang in main_file_patterns:
                        for pattern in main_file_patterns[lang]:
                            main_file = source_path / pattern
                            if main_file.exists():
                                entry_points["main_files"].append(str(main_file.relative_to(self.repository_path)))
        
        # Find config files
        config_files = build_systems_detected.get("exploration_scope", {}).get("build_config_files", [])
        entry_points["config_files"] = config_files
        
        # Find build files
        build_files = []
        build_file_patterns = [
            "CMakeLists.txt", "Makefile", "makefile", "pom.xml", "build.gradle",
            "package.json", "Cargo.toml", "meson.build", "SConstruct"
        ]
        
        for pattern in build_file_patterns:
            build_file = self.repository_path / pattern
            if build_file.exists():
                build_files.append(pattern)
        
        entry_points["build_files"] = build_files
        
        return entry_points
    
    def _define_exploration_strategy(self, architecture_classification: Dict[str, Any],
                                   source_directories: List[str],
                                   test_directories: List[str]) -> Dict[str, str]:
        """Define exploration strategy for subsequent phases"""
        
        arch_type = architecture_classification.get("architecture_classification", {}).get("type", "application")
        complexity = architecture_classification.get("architecture_classification", {}).get("complexity", "simple")
        
        strategy = {
            "phase_5_focus": "source_structure",
            "phase_6_focus": "test_structure",
            "phase_7_focus": "build_analysis",
            "phase_8_focus": "artifact_discovery"
        }
        
        # Adjust strategy based on architecture type
        if arch_type == "framework":
            strategy["phase_5_focus"] = "framework_structure"
            strategy["phase_6_focus"] = "plugin_structure"
        elif arch_type == "library":
            strategy["phase_5_focus"] = "library_structure"
            strategy["phase_6_focus"] = "api_structure"
        elif arch_type == "tool":
            strategy["phase_5_focus"] = "tool_structure"
            strategy["phase_6_focus"] = "cli_structure"
        
        # Adjust strategy based on complexity
        if complexity == "complex":
            strategy["phase_7_focus"] = "complex_build_analysis"
            strategy["phase_8_focus"] = "complex_artifact_discovery"
        
        return strategy
