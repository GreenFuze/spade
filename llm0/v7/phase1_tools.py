#!/usr/bin/env python3
"""
Phase 1 Tools for V7 Enhanced Architecture

Implements the explore_repository_signals tool for Phase 1:
- Language Detection with confidence scores
- Build System Detection with evidence
- Architecture Classification
- Exploration Scope Definition
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


class Phase1Tools:
    """Tools for Phase 1: Repository Overview and Language Detection."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("Phase1Tools")
        
    def explore_repository_signals(self, 
                                 exploration_paths: List[str] = None,
                                 file_patterns: List[str] = None,
                                 language_focus: List[str] = None,
                                 content_depth: str = "medium",
                                 confidence_threshold: float = 0.95) -> Dict[str, Any]:
        """
        Explore repository signals for language detection, build system detection, and architecture classification.
        
        Args:
            exploration_paths: List of directories to explore (default: ["."])
            file_patterns: List of file patterns to focus on (default: ["*"])
            language_focus: List of languages to focus on (default: ["C++", "Java", "Python", "JavaScript", "Go"])
            content_depth: How much content to analyze ("shallow", "medium", "deep")
            confidence_threshold: Minimum confidence required (0.0-1.0)
            
        Returns:
            Dict with languages_detected, build_systems_detected, architecture_classification, exploration_scope
        """
        try:
            # Default parameters
            if exploration_paths is None:
                exploration_paths = ["."]
            if file_patterns is None:
                file_patterns = ["*"]
            if language_focus is None:
                language_focus = ["C++", "Java", "Python", "JavaScript", "Go", "C", "C#", "Rust", "TypeScript"]
            
            self.logger.info(f"Exploring repository signals in: {exploration_paths}")
            
            # Initialize results
            results = {
                "languages_detected": {},
                "build_systems_detected": {},
                "architecture_classification": {},
                "exploration_scope": {},
                "confidence_verification": {}
            }
            
            # Language detection
            languages_detected = self._detect_languages(exploration_paths, language_focus, content_depth)
            results["languages_detected"] = languages_detected
            
            # Build system detection
            build_systems_detected = self._detect_build_systems(exploration_paths, content_depth)
            results["build_systems_detected"] = build_systems_detected
            
            # Architecture classification
            architecture_classification = self._classify_architecture(languages_detected, build_systems_detected)
            results["architecture_classification"] = architecture_classification
            
            # Exploration scope definition
            exploration_scope = self._define_exploration_scope(architecture_classification, exploration_paths)
            results["exploration_scope"] = exploration_scope
            
            # Confidence verification
            confidence_verification = self._verify_confidence(results, confidence_threshold)
            results["confidence_verification"] = confidence_verification
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in explore_repository_signals: {e}")
            return {
                "error": str(e),
                "languages_detected": {},
                "build_systems_detected": {},
                "architecture_classification": {},
                "exploration_scope": {},
                "confidence_verification": {"ready_for_phase_2": False}
            }
    
    def _detect_languages(self, exploration_paths: List[str], language_focus: List[str], content_depth: str) -> Dict[str, Any]:
        """Detect programming languages with confidence scores."""
        language_results = {}
        
        # Language detection patterns
        language_patterns = {
            "C++": [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".h"],
            "Java": [".java"],
            "Python": [".py", ".pyc", ".pyo"],
            "JavaScript": [".js", ".jsx", ".ts", ".tsx"],
            "Go": [".go"],
            "C": [".c", ".h"],
            "C#": [".cs"],
            "Rust": [".rs"],
            "TypeScript": [".ts", ".tsx"]
        }
        
        # Content patterns for deeper analysis
        content_patterns = {
            "C++": ["#include", "namespace", "class", "std::", "int main()"],
            "Java": ["package", "import", "public class", "public static void main"],
            "Python": ["import", "def", "class", "if __name__ == \"__main__\""],
            "JavaScript": ["import", "export", "function", "const", "let"],
            "Go": ["package", "import", "func main()", "var", "type"]
        }
        
        for lang in language_focus:
            if lang not in language_patterns:
                continue
                
            # Count files by extension
            file_count = 0
            file_evidence = []
            content_evidence = []
            
            for path in exploration_paths:
                search_path = self.repository_path / path
                if not search_path.exists():
                    continue
                    
                for ext in language_patterns[lang]:
                    for file_path in search_path.rglob(f"*{ext}"):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            file_count += 1
                            file_evidence.append(str(file_path.relative_to(self.repository_path)))
                            
                            # Content analysis if depth allows
                            if content_depth in ["medium", "deep"] and lang in content_patterns:
                                try:
                                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                                    for pattern in content_patterns[lang]:
                                        if pattern in content:
                                            content_evidence.append(f"{pattern} found in {file_path.name}")
                                            break
                                except:
                                    pass
            
            # Calculate confidence
            file_confidence = min(file_count / 10, 1.0)  # Max confidence at 10+ files
            content_confidence = min(len(content_evidence) / 5, 1.0)  # Max confidence at 5+ patterns
            total_confidence = min(file_confidence + content_confidence, 1.0)
            
            language_results[lang] = {
                "detected": total_confidence > 0.1,
                "confidence": total_confidence,
                "evidence": file_evidence[:5],  # Limit evidence
                "file_count": file_count,
                "content_patterns": content_evidence[:3]  # Limit patterns
            }
        
        return language_results
    
    def _detect_build_systems(self, exploration_paths: List[str], content_depth: str) -> Dict[str, Any]:
        """Detect build systems with confidence scores."""
        build_system_results = {}
        
        # Build system patterns
        build_patterns = {
            "cmake": ["CMakeLists.txt", "cmake_install.cmake"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "gradlew"],
            "npm": ["package.json", "package-lock.json"],
            "cargo": ["Cargo.toml", "Cargo.lock"],
            "make": ["Makefile", "makefile"],
            "ant": ["build.xml"]
        }
        
        for build_system, files in build_patterns.items():
            file_count = 0
            file_evidence = []
            content_evidence = []
            
            for path in exploration_paths:
                search_path = self.repository_path / path
                if not search_path.exists():
                    continue
                    
                for file_name in files:
                    for file_path in search_path.rglob(file_name):
                        if file_path.is_file():
                            file_count += 1
                            file_evidence.append(str(file_path.relative_to(self.repository_path)))
                            
                            # Content analysis for build files
                            if content_depth in ["medium", "deep"]:
                                try:
                                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                                    if build_system == "cmake" and ("add_executable" in content or "add_library" in content):
                                        content_evidence.append("CMake targets found")
                                    elif build_system == "maven" and ("<groupId>" in content or "<artifactId>" in content):
                                        content_evidence.append("Maven project structure found")
                                    elif build_system == "npm" and ("dependencies" in content or "scripts" in content):
                                        content_evidence.append("npm package structure found")
                                except:
                                    pass
            
            # Calculate confidence
            confidence = min(file_count / 3, 1.0)  # Max confidence at 3+ files
            
            build_system_results[build_system] = {
                "detected": confidence > 0.3,
                "confidence": confidence,
                "evidence": file_evidence,
                "file_count": file_count,
                "content_patterns": content_evidence
            }
        
        return build_system_results
    
    def _classify_architecture(self, languages_detected: Dict, build_systems_detected: Dict) -> Dict[str, Any]:
        """Classify repository architecture."""
        # Find all detected languages with their confidence scores
        detected_languages = []
        language_confidence_scores = {}
        total_confidence = 0
        
        for lang, data in languages_detected.items():
            if data.get("detected", False):
                confidence = data.get("confidence", 0)
                detected_languages.append(lang)
                language_confidence_scores[lang] = confidence
                total_confidence += confidence
        
        # Calculate language percentages
        language_percentages = {}
        if total_confidence > 0:
            for lang, confidence in language_confidence_scores.items():
                language_percentages[lang] = (confidence / total_confidence) * 100
        
        # Find primary language (highest confidence)
        primary_language = None
        max_confidence = 0
        for lang, data in languages_detected.items():
            if data.get("detected", False) and data.get("confidence", 0) > max_confidence:
                max_confidence = data.get("confidence", 0)
                primary_language = lang
        
        # Find primary build system
        primary_build_system = None
        max_build_confidence = 0
        for build_sys, data in build_systems_detected.items():
            if data.get("detected", False) and data.get("confidence", 0) > max_build_confidence:
                max_build_confidence = data.get("confidence", 0)
                primary_build_system = build_sys
        
        # Count detected build systems
        detected_build_systems = [build_sys for build_sys, data in build_systems_detected.items() if data.get("detected", False)]
        
        return {
            "primary_language": primary_language,
            "primary_build_system": primary_build_system,
            "detected_languages": detected_languages,
            "detected_build_systems": detected_build_systems,
            "language_confidence_scores": language_confidence_scores,
            "language_percentages": language_percentages,
            "multi_language": len(detected_languages) > 1,
            "multi_build_system": len(detected_build_systems) > 1,
            "language_build_mapping": {primary_language: primary_build_system} if primary_language and primary_build_system else {}
        }
    
    def _define_exploration_scope(self, architecture: Dict, exploration_paths: List[str]) -> Dict[str, Any]:
        """Define exploration scope for subsequent phases."""
        primary_language = architecture.get("primary_language", "unknown")
        primary_build_system = architecture.get("primary_build_system", "unknown")
        
        # Define directory priorities based on language and build system
        priority_dirs = []
        skip_dirs = ["build", "dist", "target", "node_modules", ".git", ".svn"]
        deep_exploration = []
        
        # Language-specific directory patterns
        if primary_language == "C++":
            priority_dirs.extend(["src", "include", "lib"])
            deep_exploration.extend(["src", "include"])
        elif primary_language == "Java":
            priority_dirs.extend(["src/main/java", "src/test/java"])
            deep_exploration.extend(["src/main/java"])
        elif primary_language == "Python":
            priority_dirs.extend(["src", "lib", "scripts"])
            deep_exploration.extend(["src"])
        elif primary_language == "JavaScript":
            priority_dirs.extend(["src", "lib", "public"])
            deep_exploration.extend(["src"])
        else:
            priority_dirs.extend(["src", "lib", "core"])
            deep_exploration.extend(["src"])
        
        # Filter existing directories
        existing_priority_dirs = []
        for dir_name in priority_dirs:
            for path in exploration_paths:
                check_path = self.repository_path / path / dir_name
                if check_path.exists() and check_path.is_dir():
                    existing_priority_dirs.append(dir_name)
                    break
        
        return {
            "priority_dirs": existing_priority_dirs,
            "skip_dirs": skip_dirs,
            "deep_exploration": deep_exploration,
            "language_focus": primary_language,
            "build_system_focus": primary_build_system
        }
    
    def _verify_confidence(self, results: Dict, confidence_threshold: float) -> Dict[str, bool]:
        """Verify confidence levels meet requirements."""
        languages = results.get("languages_detected", {})
        build_systems = results.get("build_systems_detected", {})
        architecture = results.get("architecture_classification", {})
        
        # Check language confidence
        language_confidence_ok = True
        for lang, data in languages.items():
            if data.get("detected", False) and data.get("confidence", 0) < confidence_threshold:
                language_confidence_ok = False
                break
        
        # Check build system confidence
        build_confidence_ok = True
        for build_sys, data in build_systems.items():
            if data.get("detected", False) and data.get("confidence", 0) < confidence_threshold:
                build_confidence_ok = False
                break
        
        return {
            "all_languages_analyzed": len(languages) > 0,
            "all_build_systems_analyzed": len(build_systems) > 0,
            "language_confidence_ok": language_confidence_ok,
            "build_confidence_ok": build_confidence_ok,
            "architecture_determined": architecture.get("primary_language") is not None,
            "ready_for_phase_2": language_confidence_ok and build_confidence_ok and architecture.get("primary_language") is not None
        }

