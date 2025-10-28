# Phase 2 Tools: Build System Detection
# Deterministic tools for build system detection

"""
Phase 2 Tools: Build System Detection

This module provides deterministic tools for Phase 2:
- detect_build_systems: Identifies all build systems present in the repository

All tools are pure functions with no LLM calls.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import glob
import os


class Phase2Tools:
    """Phase 2 Tools for Build System Detection"""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("Phase2Tools")
    
    def detect_build_systems(self, 
                           file_patterns: List[str] = None,
                           directory_patterns: List[str] = None) -> Dict[str, Any]:
        """
        PURELY DETERMINISTIC signal collection tool for build systems
        
        Args:
            file_patterns: Glob patterns for files to scan (from LLM)
                          e.g., ["CMakeLists.txt", "*.cmake", "pom.xml"]
            directory_patterns: Glob patterns for directories to scan (from LLM)
                              e.g., ["build/", "target/", "node_modules/"]
        
        Returns:
            All found signals with confidence levels
        """
        
        self.logger.info(f"Scanning build system signals in {self.repository_path}")
        
        # Default patterns if none provided
        if file_patterns is None:
            file_patterns = []
        if directory_patterns is None:
            directory_patterns = []
        
        # Scan for file patterns
        found_files = []
        for pattern in file_patterns:
            matches = list(self.repository_path.rglob(pattern))
            found_files.extend([str(m.relative_to(self.repository_path)) for m in matches])
        
        # Scan for directory patterns
        found_dirs = []
        for pattern in directory_patterns:
            matches = list(self.repository_path.rglob(pattern))
            found_dirs.extend([str(m.relative_to(self.repository_path)) for m in matches if m.is_dir()])
        
        # Map found files/dirs to build systems
        build_system_signals = self._map_signals_to_build_systems(found_files, found_dirs)
        
        return {
            "build_system_signals": build_system_signals,
            "scan_metadata": {
                "file_patterns_scanned": file_patterns,
                "directory_patterns_scanned": directory_patterns,
                "total_files_found": len(found_files),
                "total_dirs_found": len(found_dirs),
                "found_files": found_files,
                "found_dirs": found_dirs
            }
        }
    
    def _map_signals_to_build_systems(self, found_files: List[str], found_dirs: List[str]) -> Dict[str, Any]:
        """Map found files and directories to build systems"""
        
        # Build system mapping patterns
        build_system_mappings = {
            "cmake": {
                "file_patterns": ["CMakeLists.txt", "*.cmake"],
                "dir_patterns": ["build", "cmake-build-*"],
                "primary_files": ["CMakeLists.txt"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "maven": {
                "file_patterns": ["pom.xml"],
                "dir_patterns": ["target"],
                "primary_files": ["pom.xml"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "gradle": {
                "file_patterns": ["build.gradle", "build.gradle.kts", "gradlew"],
                "dir_patterns": ["build"],
                "primary_files": ["build.gradle", "build.gradle.kts"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "npm": {
                "file_patterns": ["package.json", "package-lock.json"],
                "dir_patterns": ["node_modules", "dist"],
                "primary_files": ["package.json"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "cargo": {
                "file_patterns": ["Cargo.toml", "Cargo.lock"],
                "dir_patterns": ["target"],
                "primary_files": ["Cargo.toml"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "make": {
                "file_patterns": ["Makefile", "makefile", "*.mk"],
                "dir_patterns": ["build", "obj"],
                "primary_files": ["Makefile", "makefile"],
                "confidence_weights": {"primary_file": 0.7, "secondary_file": 0.3, "dir": 0.2}
            },
            "bazel": {
                "file_patterns": ["BUILD", "BUILD.bazel", "WORKSPACE"],
                "dir_patterns": ["bazel-*"],
                "primary_files": ["BUILD", "WORKSPACE"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            },
            "meson": {
                "file_patterns": ["meson.build", "meson_options.txt"],
                "dir_patterns": ["builddir", "build"],
                "primary_files": ["meson.build"],
                "confidence_weights": {"primary_file": 0.8, "secondary_file": 0.4, "dir": 0.2}
            }
        }
        
        build_system_signals = {}
        
        for system_name, mapping in build_system_mappings.items():
            evidence_files = []
            evidence_dirs = []
            confidence = 0.0
            
            # Check files
            for file_path in found_files:
                file_name = Path(file_path).name
                if file_name in mapping["primary_files"]:
                    evidence_files.append(file_path)
                    confidence += mapping["confidence_weights"]["primary_file"]
                elif any(file_name.endswith(pattern.replace("*", "")) for pattern in mapping["file_patterns"] if "*" in pattern):
                    evidence_files.append(file_path)
                    confidence += mapping["confidence_weights"]["secondary_file"]
                elif file_name in mapping["file_patterns"]:
                    evidence_files.append(file_path)
                    confidence += mapping["confidence_weights"]["secondary_file"]
            
            # Check directories
            for dir_path in found_dirs:
                dir_name = Path(dir_path).name
                if dir_name in mapping["dir_patterns"]:
                    evidence_dirs.append(dir_path)
                    confidence += mapping["confidence_weights"]["dir"]
                elif any(dir_name.startswith(pattern.replace("*", "")) for pattern in mapping["dir_patterns"] if "*" in pattern):
                    evidence_dirs.append(dir_path)
                    confidence += mapping["confidence_weights"]["dir"]
            
            # Cap confidence at 1.0
            confidence = min(1.0, confidence)
            
            # Determine evidence strength
            if confidence >= 0.8:
                evidence_strength = "strong"
            elif confidence >= 0.5:
                evidence_strength = "medium"
            elif confidence > 0.0:
                evidence_strength = "weak"
            else:
                evidence_strength = "none"
            
            build_system_signals[system_name] = {
                "evidence_files": evidence_files,
                "evidence_dirs": evidence_dirs,
                "file_count": len(evidence_files),
                "dir_count": len(evidence_dirs),
                "confidence_level": round(confidence, 3),
                "evidence_strength": evidence_strength
            }
        
        return build_system_signals
