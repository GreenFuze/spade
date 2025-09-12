"""
CMakeEntrypoint class for parsing CMake configuration and extracting build information.
Uses the cmake-file-api package to extract all build system information.
"""
import sys
import json
import re
import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any, Union, Set

from cmake_file_api import CMakeProject, ObjectKind
from schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, Test, Evidence, ComponentLocation, Aggregator, Runner, Utility, RepositoryInfo, BuildSystemInfo
from rig import RIG


class BuildOutputFinder:
    """
    Generator-aware build output finder that reads CMake's generated build files
    where variables have already been expanded, avoiding the need to parse CMake source.
    Handles all non-C/C++ languages (Go, Java, Python, C#, Rust, etc.).
    """
    
    def __init__(self, build_dir: Path):
        self.build_dir = Path(build_dir)
        self.cache = self._read_cache()
        
        # Language-specific build command patterns
        self.language_patterns = {
            "go": {
                "ninja": r'go\.exe.*?build.*?-o\s+([^\s"]+)',
                "msvc": r"go(?:\.exe)?\s+build\s+[^<]*?-buildmode=c-shared[^<]*?-o\s+([^\s<]+)",
                "makefile": r"go(?:\.exe)?\s+build\s+[^#\n]*?-buildmode=c-shared[^#\n]*?-o\s+([^\s#]+)",
                "extensions": [".dll", ".so", ".dylib"]
            },
            "java": {
                "ninja": r'javac.*?-d\s+([^\s"]+)|jar.*?-cf\s+([^\s"]+)|java.*?-jar\s+([^\s"]+)',
                "msvc": r"javac[^<]*?-d\s+([^\s<]+)|jar[^<]*?-cf\s+([^\s<]+)|java[^<]*?-jar\s+([^\s<]+)",
                "makefile": r"javac[^#\n]*?-d\s+([^\s#]+)|jar[^#\n]*?-cf\s+([^\s#]+)|java[^#\n]*?-jar\s+([^\s#]+)",
                "extensions": [".jar", ".class"]
            },
            "python": {
                "ninja": r'python.*?-m\s+py_compile.*?-o\s+([^\s"]+)|python.*?-c.*?-o\s+([^\s"]+)',
                "msvc": r"python[^<]*?-m\s+py_compile[^<]*?-o\s+([^\s<]+)|python[^<]*?-c[^<]*?-o\s+([^\s<]+)",
                "makefile": r"python[^#\n]*?-m\s+py_compile[^#\n]*?-o\s+([^\s#]+)|python[^#\n]*?-c[^#\n]*?-o\s+([^\s#]+)",
                "extensions": [".pyc", ".pyo", ".py"]
            },
            "csharp": {
                "ninja": r'csc.*?-out:([^\s"]+)|dotnet.*?build.*?-o\s+([^\s"]+)',
                "msvc": r"csc[^<]*?-out:([^\s<]+)|dotnet[^<]*?build[^<]*?-o\s+([^\s<]+)",
                "makefile": r"csc[^#\n]*?-out:([^\s#]+)|dotnet[^#\n]*?build[^#\n]*?-o\s+([^\s#]+)",
                "extensions": [".exe", ".dll"]
            },
            "rust": {
                "ninja": r'cargo.*?build.*?--target-dir\s+([^\s"]+)|rustc.*?-o\s+([^\s"]+)',
                "msvc": r"cargo[^<]*?build[^<]*?--target-dir\s+([^\s<]+)|rustc[^<]*?-o\s+([^\s<]+)",
                "makefile": r"cargo[^#\n]*?build[^#\n]*?--target-dir\s+([^\s#]+)|rustc[^#\n]*?-o\s+([^\s#]+)",
                "extensions": [".exe", ".so", ".dll", ".dylib", ".rlib"]
            }
        }

    def _read_cache(self) -> dict:
        """Read CMakeCache.txt to get generator and other variables."""
        cache_file = self.build_dir / "CMakeCache.txt"
        cache = {}
        if cache_file.exists():
            for line in cache_file.read_text(errors="ignore").splitlines():
                if line.startswith(("#", "//")) or "=" not in line:
                    continue
                # NAME:TYPE=VALUE
                k, v = line.split("=", 1)
                name = k.split(":", 1)[0].strip()
                cache[name] = v.strip()
        return cache

    @property
    def generator(self) -> str:
        """Get the CMake generator name."""
        return self.cache.get("CMAKE_GENERATOR", "").lower()

    def find_output(self, target_hint: Optional[str] = None, language: str = "go") -> Optional[Path]:
        """Find output path for any language from generated build files."""
        if language not in self.language_patterns:
            return None
            
        g = self.generator
        if "ninja" in g:
            p = self._from_ninja(target_hint, language)
            if p: return p
        if "visual studio" in g or "msbuild" in g:
            p = self._from_msvc(target_hint, language)
            if p: return p
        if "unix makefiles" in g or "mingw makefiles" in g or "nmake makefiles" in g:
            p = self._from_makefiles(target_hint, language)
            if p: return p
        # last-ditch fallback: scan everything for language-specific build commands
        return self._scan_any_build_files(target_hint, language)

    def _from_ninja(self, target_hint: Optional[str], language: str) -> Optional[Path]:
        """Extract output from Ninja build.ninja file for specified language."""
        ninja = self.build_dir / "build.ninja"
        if not ninja.exists():
            return None
        text = ninja.read_text(errors="ignore")
        pattern_str = self.language_patterns[language]["ninja"]
        pattern = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
        hits = pattern.findall(text)
        # Flatten hits if pattern has multiple groups
        hits = [hit for sublist in hits for hit in (sublist if isinstance(sublist, tuple) else [sublist]) if hit]
        hits = self._filter_hits_by_target(hits, text, target_hint)
        return self._first_existing_or_best(hits, language)

    def _from_msvc(self, target_hint: Optional[str], language: str) -> Optional[Path]:
        """Extract output from Visual Studio .vcxproj files for specified language."""
        projs = list(self.build_dir.glob("**/*.vcxproj"))
        if not projs:
            projs = list(self.build_dir.glob("*.vcxproj"))
        cmd_re = re.compile(self.language_patterns[language]["msvc"], re.IGNORECASE)
        out_re = re.compile(r"<Outputs>([^<]+)</Outputs>", re.IGNORECASE)
        best: List[str] = []
        for p in projs:
            t = p.read_text(errors="ignore")
            # Prefer matching projects whose ItemGroup mentions the target hint
            if target_hint and target_hint.lower() not in t.lower():
                continue
            hits = cmd_re.findall(t)
            # Flatten hits if pattern has multiple groups
            best += [hit for sublist in hits for hit in (sublist if isinstance(sublist, tuple) else [sublist]) if hit]
            # Secondary: explicit Outputs XML
            outs = out_re.findall(t)
            for o in outs:
                # Often semicolon-separated
                for token in re.split(r"[;,\s]+", o.strip()):
                    if any(token.lower().endswith(ext) for ext in self.language_patterns[language]["extensions"]):
                        best.append(token)
        return self._first_existing_or_best(best, language)

    def _from_makefiles(self, target_hint: Optional[str], language: str) -> Optional[Path]:
        """Extract output from Makefile for specified language."""
        mk = self.build_dir / "Makefile"
        if not mk.exists(): 
            return None
        t = mk.read_text(errors="ignore")
        # Recipes may be split with backslashes; drop them to ease regex:
        t = t.replace("\\\n", " ")
        pattern = re.compile(self.language_patterns[language]["makefile"], re.IGNORECASE)
        hits = pattern.findall(t)
        # Flatten hits if pattern has multiple groups
        hits = [hit for sublist in hits for hit in (sublist if isinstance(sublist, tuple) else [sublist]) if hit]
        return self._first_existing_or_best(hits, language)

    def _scan_any_build_files(self, target_hint: Optional[str], language: str) -> Optional[Path]:
        """Search common generator files for language-specific build commands."""
        candidates = list(self.build_dir.glob("**/*"))
        paths: List[str] = []
        extensions = "|".join(self.language_patterns[language]["extensions"])
        rx = re.compile(r"-o\s+([^\s\\<>\"]*\.(?:{})|\S+\.(?:{}))".format(extensions, extensions), re.IGNORECASE)
        for p in candidates:
            if not p.is_file(): 
                continue
            if p.suffix.lower() not in (".ninja", ".vcxproj", ".mak", ".make", ".txt", ".rule"):
                continue
            try:
                data = p.read_text(errors="ignore")
            except Exception:
                continue
            for m in rx.finditer(data):
                paths.append(m.group(1))
        return self._first_existing_or_best(paths, language)

    def _filter_hits_by_target(self, hits: List[str], text: str, target_hint: Optional[str]) -> List[str]:
        """Filter hits by target hint if provided."""
        if not target_hint:
            return hits
        # keep hits that occur in a section mentioning the target
        keep: List[str] = []
        for h in hits:
            idx = text.find(h)
            window = text[max(0, idx-300): idx+300] if idx >= 0 else ""
            if target_hint.lower() in window.lower():
                keep.append(h)
        return keep or hits

    def _first_existing_or_best(self, tokens: List[str], language: str) -> Optional[Path]:
        """Return the first existing file or best candidate for the specified language."""
        # Resolve env vars just in case and normalize to absolute
        cleaned: List[Path] = []
        for tok in tokens:
            p = Path(os.path.expandvars(tok.strip('"')))
            cleaned.append(p)
        # Prefer an existing file (if already built)
        for p in cleaned:
            if p.exists():
                return p
        # else return the first plausible path with language-specific extensions
        extensions = self.language_patterns[language]["extensions"]
        for p in cleaned:
            if p.suffix.lower() in extensions:
                return p
        return cleaned[0] if cleaned else None


class ResearchBackedUtilities:
    """
    Utility class for research-backed upgrades to maximize coverage before falling back to UNKNOWN.
    Implements evidence-first approach with no heuristics.
    """
    
    # Regex for variable expansion
    VAR_RX = re.compile(r"\$\{(\w+)\}")
    
    # CMake target types that produce artifacts (per CMake File API spec)
    ARTIFACT_KINDS = {"EXECUTABLE", "STATIC_LIBRARY", "SHARED_LIBRARY", "MODULE_LIBRARY", "OBJECT_LIBRARY"}
    
    # Data-driven runtime detection tables (evidence-only)
    ARTIFACT_EXT_TO_RUNTIME = {".jar": Runtime.JVM}
    LANG_TO_RUNTIME = {"csharp": Runtime.DOTNET}
    COMPILER_ID_TO_RUNTIME = {
        "MSVC": Runtime.VS_CPP,
        "Clang": Runtime.CLANG_C,
        "AppleClang": Runtime.CLANG_C,
        "GNU": Runtime.CLANG_C,
        "Intel": Runtime.CLANG_C,
        "IntelLLVM": Runtime.CLANG_C,
        "ARMClang": Runtime.CLANG_C,
        "NVHPC": Runtime.CLANG_C,
    }
    
    # Allowed compile definition keys for runtime detection (evidence-only)
    ALLOWED_DEFINE_KEYS = {"RIG_RUNTIME"}  # empty by default, can be extended via project JSON
    
    @staticmethod
    def expand_vars(s: str, cache: Dict[str, str]) -> str:
        """Expand ${VAR} using File API cache."""
        return ResearchBackedUtilities.VAR_RX.sub(
            lambda m: cache.get(m.group(1), m.group(0)), s
        )
    
    @staticmethod
    def normalize_token(t: str) -> str:
        """Normalize tokens for classifier while preserving evidence."""
        return t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in ('"', "'") else t
    
    @staticmethod
    def unknown_field(field: str, context: str, evidence: Dict[str, Any], errors: Set[str]) -> None:
        """Evidence-first UNKNOWN field reporting."""
        error_msg = f"unknown_{field}"
        errors.add(f"{error_msg}: context={context}, evidence={evidence}")
    
    @staticmethod
    def direct_deps(target_id: str, fileapi_deps: Set[str], graphviz_deps: Optional[Set[str]] = None) -> Set[str]:
        """Direct vs transitive deps reconciliation."""
        if graphviz_deps:
            return fileapi_deps & graphviz_deps
        return fileapi_deps  # fall back when graphviz disabled
    
    @staticmethod
    def get_artifact_name_from_target(target: Any) -> Optional[str]:
        """Get artifact name from target using File API evidence."""
        # Priority 1: nameOnDisk (most authoritative)
        if hasattr(target, 'nameOnDisk') and target.nameOnDisk:
            return Path(target.nameOnDisk).name
        
        # Priority 2: artifacts array
        if hasattr(target, 'artifacts') and target.artifacts:
            for artifact in target.artifacts:
                if hasattr(artifact, 'path') and artifact.path:
                    return Path(artifact.path).name
        
        return None
    
    @staticmethod
    def get_output_path_from_target(target: Any, cache: Dict[str, str]) -> Optional[Path]:
        """Get output path from target using File API evidence."""
        # Priority 1: artifacts array (most authoritative)
        if hasattr(target, 'artifacts') and target.artifacts:
            for artifact in target.artifacts:
                if hasattr(artifact, 'path') and artifact.path:
                    artifact_path = Path(artifact.path)
                    # Expand variables in path
                    expanded_path = ResearchBackedUtilities.expand_vars(str(artifact_path), cache)
                    return Path(expanded_path)
                elif isinstance(artifact, dict) and 'path' in artifact:
                    artifact_path = Path(artifact['path'])
                    # Expand variables in path
                    expanded_path = ResearchBackedUtilities.expand_vars(str(artifact_path), cache)
                    return Path(expanded_path)
        
        # Priority 2: nameOnDisk
        if hasattr(target, 'nameOnDisk') and target.nameOnDisk:
            expanded_path = ResearchBackedUtilities.expand_vars(target.nameOnDisk, cache)
            return Path(expanded_path)
        elif isinstance(target, dict) and 'nameOnDisk' in target:
            expanded_path = ResearchBackedUtilities.expand_vars(target['nameOnDisk'], cache)
            return Path(expanded_path)
        
        return None
    
    @staticmethod
    def get_language_from_toolchains(target: Any, toolchains: Any) -> Optional[str]:
        """Get language from toolchains using File API evidence."""
        if not toolchains or not hasattr(toolchains, 'toolchains'):
            return None
        
        # Get primary language from target's compileGroups
        if hasattr(target, 'compileGroups'):
            for cg in target.compileGroups:
                if hasattr(cg, 'language') and cg.language:
                    return cg.language.lower()
        
        return None
    
    @staticmethod
    def get_source_extensions_from_toolchains(toolchains: Any, language: str) -> List[str]:
        """Get source file extensions from toolchains for a language."""
        if not toolchains or not hasattr(toolchains, 'toolchains'):
            return []
        
        for tc in toolchains.toolchains:
            if hasattr(tc, 'language') and tc.language and tc.language.lower() == language.lower():
                if hasattr(tc, 'sourceFileExtensions') and tc.sourceFileExtensions:
                    return tc.sourceFileExtensions
        
        return []
    
    @staticmethod
    def detect_package_manager_from_cache(cache_entries: List[Any]) -> Optional[str]:
        """Detect package manager from cache entries using evidence."""
        for entry in cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                name = entry.name
                value = str(entry.value)
                
                # vcpkg detection
                if name == 'CMAKE_TOOLCHAIN_FILE' and 'vcpkg.cmake' in value:
                    return 'vcpkg'
                elif name.startswith('VCPKG_') or name.startswith('Z_VCPKG_'):
                    return 'vcpkg'
                
                # Conan detection
                if name == 'CMAKE_TOOLCHAIN_FILE' and 'conan_toolchain.cmake' in value:
                    return 'conan'
                elif name.startswith('CONAN_'):
                    return 'conan'
        
        return None
    
    @staticmethod
    def strip_generator_expressions(text: str) -> str:
        """Strip generator expressions from text, pointing to resolved File API values instead."""
        # Pattern to match generator expressions like $<CONFIG:Debug,Release>
        genex_pattern = r'\$<[^>]+>'
        
        # Replace generator expressions with placeholders
        stripped = re.sub(genex_pattern, '[RESOLVED_BY_FILE_API]', text)
        
        return stripped
    
    @staticmethod
    def has_generator_expressions(text: str) -> bool:
        """Check if text contains generator expressions."""
        genex_pattern = r'\$<[^>]+>'
        return bool(re.search(genex_pattern, text))
    
    @staticmethod
    def prefer_file_api_resolved_value(raw_value: str, file_api_value: Optional[str], context: str) -> str:
        """Prefer File API resolved value over raw value with generator expressions."""
        if file_api_value and not ResearchBackedUtilities.has_generator_expressions(file_api_value):
            return file_api_value
        
        if ResearchBackedUtilities.has_generator_expressions(raw_value):
            # Strip generator expressions and indicate File API should be used
            stripped = ResearchBackedUtilities.strip_generator_expressions(raw_value)
            return f"{stripped} [Use File API resolved value for {context}]"
        
        return raw_value
    
    @staticmethod
    def should_expect_artifacts(target_type: str) -> bool:
        """
        Determine if a target type should have artifacts based on CMake File API spec.
        
        Args:
            target_type: CMake target type (e.g., "EXECUTABLE", "UTILITY", etc.)
            
        Returns:
            True if target type should have artifacts, False otherwise
        """
        return target_type in ResearchBackedUtilities.ARTIFACT_KINDS
    
    @staticmethod
    def is_build_artifact(p: Path, build_dir: Path, known_artifacts: List[Path]) -> bool:
        """
        Generic, evidence-based build artifact detection.
        No project-specific hints, no name parsing, no guesses.
        """
        p = p.resolve()
        
        # Treat anything under the configured CMake build directory as generated
        if build_dir in p.parents or p == build_dir:
            return True
            
        # Treat anything under the parent directories of known artifacts as generated
        known_dirs = {a.resolve().parent for a in known_artifacts}
        if any(d == p or d in p.parents for d in known_dirs):
            return True
            
        # Include standard CMake internals (pure convention, not project hints)
        parts = {q.name for q in p.parents}
        if "CMakeFiles" in parts or ".cmake" in parts or "Testing" in parts:
            return True
            
        # Standard CMake files
        if p.name in {"CTestTestfile.cmake", "install_manifest.txt", "CMakeCache.txt"}:
            return True
            
        return False
    
    @staticmethod
    def detect_runtime_evidence_based(target: Any, toolchains_obj: Any = None) -> Optional[Runtime]:
        """
        Generic, evidence-based runtime detection.
        No name parsing, no project-specific hints, no guesses.
        """
        # 1. Artifact type → runtime (exact)
        for art in getattr(target, "artifacts", []) or []:
            if hasattr(art, "path") and art.path:
                rt = ResearchBackedUtilities.ARTIFACT_EXT_TO_RUNTIME.get(Path(art.path).suffix.lower())
                if rt:
                    return rt
        
        # 2. Compile groups language / Toolchains compiler.id (exact)
        for cg in getattr(target, "compileGroups", []) or []:
            lang = cg.get("language") or getattr(cg, "language", None)
            if lang:
                rt = ResearchBackedUtilities.LANG_TO_RUNTIME.get(lang.lower())
                if rt:
                    return rt
                    
                # Exact compiler.id mapping
                if toolchains_obj:
                    for tc in getattr(toolchains_obj, "toolchains", []) or []:
                        if str(getattr(tc, "language", "")).lower() == lang.lower():
                            cid = str(getattr(getattr(tc, "compiler", None), "id", "")).strip()
                            if cid in ResearchBackedUtilities.COMPILER_ID_TO_RUNTIME:
                                return ResearchBackedUtilities.COMPILER_ID_TO_RUNTIME[cid]
                            break
        
        # 3. Transitive linkage to a target that already has a runtime
        deps_runtimes = {getattr(d, "runtime", None)
                        for d in getattr(target, "depends_on", []) or [] 
                        if getattr(d, "runtime", None)}
        if len(deps_runtimes) == 1:
            return next(iter(deps_runtimes))
        
        # 4. Else → UNKNOWN (no evidence)
        return None
    
    @staticmethod
    def runtime_from_defines(compile_groups: List[Any]) -> Optional[Runtime]:
        """
        Generic compile definition parsing for runtime detection.
        Only accepts explicit, pre-declared contracts.
        """
        kv = {}
        for g in compile_groups or []:
            for d in g.get("defines", []):
                if "=" in d:
                    k, v = d.split("=", 1)
                    kv[k.strip()] = v.strip()
            for frag in g.get("compileCommandFragments", []):
                frag_text = frag.get("fragment") or ""
                # exact -DKEY=VALUE extraction
                for tok in frag_text.split():
                    if tok.startswith("-D") and "=" in tok:
                        k, v = tok[2:].split("=", 1)
                        kv[k.strip()] = v.strip()
        
        for k in ResearchBackedUtilities.ALLOWED_DEFINE_KEYS:
            if k in kv:
                # Try to map to Runtime enum
                try:
                    return Runtime(kv[k])
                except (ValueError, TypeError):
                    # Unknown runtime value, leave as None
                    pass
        return None
    
    @staticmethod
    def classify_target_evidence_based(target: Any) -> str:
        """
        Generic, evidence-based target classification.
        No name parsing, no project-specific hints, no guesses.
        Uses File-API target type + properties only.
        """
        ttype = getattr(target, "type", "").upper()
        
        # Standard CMake target types
        if ttype in {"EXECUTABLE", "STATIC_LIBRARY", "SHARED_LIBRARY", "MODULE_LIBRARY", "OBJECT_LIBRARY"}:
            return "COMPONENT"
        if ttype == "INTERFACE_LIBRARY":
            return "INTERFACE"
        if ttype == "IMPORTED_LIBRARY" or getattr(target, "isImported", False):
            return "EXTERNAL"
        
        # Custom/Utility targets - classify by properties
        if ttype in {"UTILITY", "CUSTOM"}:
            # Has BYPRODUCTS/OUTPUTS → Component
            byp = getattr(target, "byproducts", None) or getattr(target, "outputs", None)
            if byp:
                return "COMPONENT"
            
            # Has COMMAND and no byproducts → Runner
            cmd = getattr(target, "command", None) or getattr(target, "commands", None)
            if cmd:
                return "RUNNER"
            
            # Has DEPENDS and no command → Aggregator
            deps = getattr(target, "depends_on", None)
            if deps:
                return "AGGREGATOR"
            
            # Empty custom target → Aggregator (default)
            return "AGGREGATOR"
        
        # Fallback: if it has artifacts → Component, else Unknown
        arts = getattr(target, "artifacts", None)
        return "COMPONENT" if arts else "UNKNOWN"
    
    @staticmethod
    def validate_target_artifacts(target: Any, unknown_errors: Set[str]) -> None:
        """
        Validate target artifacts only for artifact-producing target types.
        
        Args:
            target: CMake target object
            unknown_errors: Set to collect unknown errors
        """
        target_type = getattr(target, "type", None)
        target_name = getattr(target, "name", "<unnamed>")
        
        # Only expect artifacts for artifact-producing target types
        if not ResearchBackedUtilities.should_expect_artifacts(str(target_type)):
            return  # UTILITY/INTERFACE/ALIAS/IMPORTED can legitimately lack artifacts
        
        # Check for artifacts only for artifact-producing types
        has_artifacts = bool(getattr(target, "artifacts", None))
        has_name_on_disk = bool(getattr(target, "nameOnDisk", None))
        
        if not (has_artifacts or has_name_on_disk):
            ResearchBackedUtilities.unknown_field(
                "artifact_name",
                context=f"target_{target_name}",
                evidence={"has_artifacts": has_artifacts, "has_nameOnDisk": has_name_on_disk},
                errors=unknown_errors
            )


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
        """Parse all CMakeLists.txt files in the source directory."""
        cmake_files = list(self.source_dir.rglob("CMakeLists.txt"))
        if not cmake_files:
            raise ValueError(f"No CMakeLists.txt files found in {self.source_dir}")
            
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
        # Pattern to match add_custom_target with various parameters (including hyphens in target names)
        pattern = r'add_custom_target\s*\(\s*([\w-]+)\s*(.*?)\)'
        
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


class CMakeEntrypoint:
    """
    Parses CMake configuration and extracts build system information.

    This class uses the cmake-file-api package to analyze CMake projects and create
    a canonical representation of the build system structure, including components,
    tests, dependencies, and external packages.
    """

    def __init__(self, cmake_config_dir: Path, parse_cmake: bool = True) -> None:
        """
        Initialize CMakeEntrypoint with CMake configuration directory.

        Args:
            cmake_config_dir: Path to CMake configuration directory
            parse_cmake: Whether to parse CMake configuration (default: True)
        """
        self.cmake_config_dir = Path(cmake_config_dir)
        self.repo_root = self._find_repo_root()

        # Create RIG instance to hold all extracted data
        self._rig = RIG()

        # Temporary storage for extracted data (will be moved to RIG)
        self._temp_project_name: str = ""
        self._temp_components: List[Component] = []
        self._temp_aggregators: List[Aggregator] = []
        self._temp_runners: List[Runner] = []
        self._temp_utilities: List[Utility] = []
        self._temp_tests: List[Test] = []
        self._temp_build_directory: Path = Path()
        self._temp_output_directory: Path = Path()
        self._temp_configure_command: str = ""
        self._temp_build_command: str = ""
        self._temp_install_command: str = ""
        self._temp_test_command: str = ""
        self._temp_build_system_info: Optional[BuildSystemInfo] = None
        self._temp_backtrace_graph: Optional[Any] = None
        self._temp_cache_entries: List[Any] = []
        self._temp_global_external_packages: List[ExternalPackage] = []
        self._temp_toolchains: Optional[Any] = None
        
        # Research-backed upgrades: evidence tracking
        self._temp_cache_dict: Dict[str, str] = {}  # Cache as dict for variable expansion
        self._temp_unknown_errors: Set[str] = set()  # Track UNKNOWN_* errors
        self._temp_compile_commands: Optional[Dict[str, Any]] = None
        self._parsing_completed: bool = False  # Track if parsing has been completed  # compile_commands.json
        self._temp_graphviz_deps: Optional[Dict[str, Set[str]]] = None  # Graphviz dependencies
        
        # Unified toolchains tracking
        self._toolchains_info: Dict[str, Any] = {}  # language -> details
        self._toolchains_obj: Any = None  # toolchains object from File API
        
        # Initialize CMake parser for evidence-based detection
        self._cmake_parser: Optional[CMakeParser] = None
        if parse_cmake:
            try:
                # Use the repository root as the source directory
                self._cmake_parser = CMakeParser(self.repo_root)
                self._cmake_parser.parse_all_cmake_files()
            except Exception as e:
                raise ValueError(f"Failed to parse CMakeLists.txt files: {e}")

        # Initialize build output finder for generator-aware detection of all non-C/C++ languages
        self._build_output_finder = BuildOutputFinder(self.cmake_config_dir)

        # Parse CMake information using the file API (optional)
        if parse_cmake:
            self.parse_cmake_info()

    def _find_repo_root(self) -> Path:
        """Find the repository root by looking for CMakeLists.txt."""
        current = self.cmake_config_dir
        while current != current.parent:
            if (current / "CMakeLists.txt").exists():
                return current
            current = current.parent

        raise ValueError(f"Could not find repository root from {self.cmake_config_dir}")

    def parse_cmake_info(self) -> None:
        """Parse CMake configuration using the file API."""
        # Prevent duplicate parsing
        if self._parsing_completed:
            return
            
        try:
            # Create CMakeProject instance
            proj = CMakeProject(build_path=self.cmake_config_dir, source_path=self.repo_root, api_version=1)

            # Ask CMake for all supported object kinds for API v1
            proj.cmake_file_api.instrument_all()

            # Run CMake configure to produce replies
            proj.configure(quiet=False, args=["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])

            # Read all replies
            replies = proj.cmake_file_api.inspect_all()

            # Extract information from replies
            self._extract_from_replies(replies)

            # Extract additional information
            self._extract_build_commands()
            self._extract_output_directory()

            # Populate RIG with extracted data
            self._populate_rig()

        except Exception as e:
            raise RuntimeError(f"Failed to parse CMake configuration: {e}")

    def _extract_from_replies(self, replies: Dict[ObjectKind, Dict[int, Any]]) -> None:
        """Extract all information from CMake API replies."""
        # Load toolchains information first for language detection
        self._toolchains_info = self._load_toolchains_info()
        
        # Extract from codemodel v2 (the build graph)
        if ObjectKind.CODEMODEL in replies and 2 in replies[ObjectKind.CODEMODEL]:
            codemodel_v2 = replies[ObjectKind.CODEMODEL][2]
            self._extract_from_codemodel(codemodel_v2)
        else:
            # Fallback: Load codemodel directly from JSON files
            self._extract_from_codemodel_fallback()

        # Extract from cache v2 (cache variables)
        if ObjectKind.CACHE in replies and 2 in replies[ObjectKind.CACHE]:
            cache_v2 = replies[ObjectKind.CACHE][2]
            self._extract_from_cache(cache_v2)
        else:
            # Fallback: Load cache directly from JSON files
            self._extract_from_cache_fallback()
            
            # Update existing components with global external packages
            self._update_components_with_global_packages()

        # Extract from toolchains v1 (compilers, versions)
        if ObjectKind.TOOLCHAINS in replies and 1 in replies[ObjectKind.TOOLCHAINS]:
            toolchains_v1 = replies[ObjectKind.TOOLCHAINS][1]
            self._extract_from_toolchains(toolchains_v1)

        # Extract from cmakeFiles v1 (CMakeLists.txt and included .cmake files)
        if ObjectKind.CMAKEFILES in replies and 1 in replies[ObjectKind.CMAKEFILES]:
            cmake_files_v1 = replies[ObjectKind.CMAKEFILES][1]
            self._extract_from_cmake_files(cmake_files_v1)

        # Extract tests using CTest JSON (requires built targets for reliable command[])
        self._extract_tests_from_ctest()
        
        # Load compile_commands.json as fallback for per-TU evidence
        self._load_compile_commands_json()
        
        # Load graphviz dependencies for direct vs transitive distinction
        self._load_graphviz_dependencies()
        
        # Mark parsing as completed
        self._parsing_completed = True

    def _extract_from_codemodel(self, codemodel: Any) -> None:
        """Extract information from codemodel v2."""
        # Use proper type checking instead of hasattr
        if not hasattr(codemodel, "configurations") or not codemodel.configurations:
            return

        # Store the backtraceGraph for evidence resolution
        self._temp_backtrace_graph = getattr(codemodel, 'backtraceGraph', None)
        
        # Extract install metadata from codemodel directories
        self._extract_install_metadata_from_codemodel(codemodel)

        # Use the first configuration (typically Debug or Release)
        cfg = codemodel.configurations[0]

        # Extract project information
        if hasattr(cfg, "projects") and cfg.projects:
            self._temp_project_name = cfg.projects[0].name

        # Extract targets (components, aggregators, runners)
        if hasattr(cfg, "targets"):
            # First pass: Create all nodes without resolving dependencies
            for target in cfg.targets:
                build_node: Optional[Union[Component, Aggregator, Runner, Utility]] = self._create_build_node_from_target(target)
                if build_node:
                    if isinstance(build_node, Component):
                        self._temp_components.append(build_node)
                    elif isinstance(build_node, Aggregator):
                        self._temp_aggregators.append(build_node)
                    elif isinstance(build_node, Runner):
                        self._temp_runners.append(build_node)
                    else:  # Must be Utility
                        self._temp_utilities.append(build_node)

            # Second pass: Resolve all dependencies
            self._resolve_all_dependencies(cfg.targets)
            
            # Third pass: Update runtime detection after dependencies are resolved
            self._update_runtime_after_dependencies()

    def _resolve_all_dependencies(self, targets: List[Any]) -> None:
        """Resolve all dependencies for all nodes in a second pass."""
        # Create a mapping of target names to nodes
        name_to_node: Dict[str, Union[Component, Aggregator, Runner, Utility]] = {}

        for comp in self._temp_components:
            name_to_node[comp.name] = comp
        for agg in self._temp_aggregators:
            name_to_node[agg.name] = agg
        for runner in self._temp_runners:
            name_to_node[runner.name] = runner
        for utility in self._temp_utilities:
            name_to_node[utility.name] = utility

        # Resolve dependencies for each target
        for target in targets:
            target_name = getattr(target, "name", "")
            if target_name in name_to_node:
                node = name_to_node[target_name]
                dependencies = self._extract_dependencies_from_target_with_mapping(target, name_to_node)
                # Update the node's dependencies
                node.depends_on = dependencies

    def _extract_dependencies_from_target_with_mapping(self, target: Any, name_to_node: Dict[str, Union[Component, Aggregator, Runner, Utility]]) -> List[Union[Component, Aggregator, Runner, Utility]]:
        """Extract dependencies from target using the name mapping."""
        dependencies: List[Union[Component, Aggregator, Runner, Utility]] = []

        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)

        if hasattr(actual_target, "dependencies"):
            for dep in actual_target.dependencies:
                if hasattr(dep, "target") and hasattr(dep.target, "name"):
                    dep_name = dep.target.name
                    if dep_name in name_to_node:
                        dependencies.append(name_to_node[dep_name])

        return dependencies

    def _update_runtime_after_dependencies(self) -> None:
        """Update runtime detection for all components after dependencies are resolved."""
        for component in self._temp_components:
            # Skip if runtime is already detected (e.g., from target name or compile definitions)
            if component.runtime is not None:
                continue
            
            # Try linkage-based runtime detection for test executables
            if component.name.endswith("_test") or "test" in component.name.lower():
                runtime = self._detect_runtime_via_linkage(component)
                if runtime is not None:
                    component.runtime = runtime
                    # Remove from unknown errors if it was there
                    self._temp_unknown_errors.discard(f"unknown_runtime: context=target_{component.name}")
        
        # Clean up any remaining runtime unknown errors for components that now have runtime
        errors_to_remove: List[str] = []
        for error in self._temp_unknown_errors:
            if error.startswith("unknown_runtime: context=target_"):
                # Extract target name from error
                target_name = error.split("context=target_")[1].split(",")[0]
                # Check if this component now has a runtime
                for component in self._temp_components:
                    if component.name == target_name and component.runtime is not None:
                        errors_to_remove.append(error)
                        break
        
        # Remove the errors
        for error in errors_to_remove:
            self._temp_unknown_errors.discard(error)

    def _classify_utility_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner, Utility]]) -> Union[Component, Aggregator, Runner, Utility]:
        """
        Classify UTILITY targets deterministically based on File API evidence.
        
        Args:
            target: CMake target object
            evidence: Evidence for this target
            dependencies: List of dependencies (will be populated later)
            
        Returns:
            Component if custom target with OUTPUT, Aggregator if has dependencies, Runner if has commands, Utility otherwise
        """
        target_name = getattr(target, "name", "")
        
        # Check if this is a custom target with OUTPUT/BYPRODUCTS (evidence-based)
        # First check File API data for OUTPUT/BYPRODUCTS
        has_output = bool(getattr(target, "outputs", None))
        has_byproducts = bool(getattr(target, "byproducts", None))
        has_commands = bool(getattr(target, "command", None) or getattr(target, "commands", None))
        
        # If File API shows OUTPUT/BYPRODUCTS -> Component (produces artifacts)
        if has_output or has_byproducts:
            return self._create_component_from_custom_target(target, evidence, dependencies)
        
        # If File API shows COMMAND but no OUTPUT -> Runner (executes commands)
        elif has_commands and not has_output and not has_byproducts:
            runner = Runner(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
            return runner
        
        # Fallback to CMake parser for additional evidence
        if self._cmake_parser:
            custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
            if custom_target_info:
                has_output_cmake = custom_target_info.get('has_output', False)
                has_byproducts_cmake = custom_target_info.get('has_byproducts', False)
                has_commands_cmake = custom_target_info.get('has_commands', False)
                has_depends_cmake = custom_target_info.get('has_depends', False)
                
                # Custom target with OUTPUT/BYPRODUCTS -> Component (produces artifacts)
                if has_output_cmake or has_byproducts_cmake:
                    return self._create_component_from_custom_target(target, evidence, dependencies)
                
                # Custom target with COMMAND but no OUTPUT -> Runner (executes commands)
                elif has_commands_cmake and not has_output_cmake and not has_byproducts_cmake:
                    # Check if this is a risky runner
                    is_risky = self._is_risky_runner(custom_target_info, target_name)
                    runner = Runner(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
                    
                    # Add risky runner validation error if needed
                    if is_risky:
                        ResearchBackedUtilities.unknown_field(
                            "risky_runner",
                            f"target_{target_name}",
                            {
                                "has_commands": has_commands_cmake,
                                "has_depends": has_depends_cmake,
                                "command": custom_target_info.get('parameters', {}).get('COMMAND', []),
                                "working_directory": custom_target_info.get('parameters', {}).get('WORKING_DIRECTORY', '')
                            },
                            self._temp_unknown_errors
                        )
                    
                    return runner
                
                # Custom target with DEPENDS but no COMMAND/OUTPUT -> Aggregator (groups dependencies)
                elif has_depends_cmake and not has_commands_cmake and not has_output_cmake:
                    return Aggregator(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
        
        # Check for evidence that this UTILITY target should be a component
        # Look for custom commands with OUTPUT and build commands (evidence-based)
        should_be_component = False
        
        # Check if this target has evidence of being a custom command with OUTPUT
        # This is evidence-based detection from CMake File API data
        if hasattr(target, "sources") and target.sources:
            # Look for generated rule files that indicate custom commands
            for source in target.sources:
                if hasattr(source, "path"):
                    source_path = str(source.path)
                    # Check for .rule files that indicate custom commands with OUTPUT
                    if source_path.endswith(".rule") and ("output" in source_path or "build" in source_path):
                        should_be_component = True
                        break
        
        # Check backtrace evidence for add_custom_target (evidence-based from JSON)
        if not should_be_component and hasattr(target, "backtraceGraph") and target.backtraceGraph:
            backtrace = target.backtraceGraph
            if isinstance(backtrace, dict) and "commands" in backtrace:
                commands = backtrace["commands"]
                # Look for evidence of add_custom_target (generic, not macro-specific)
                if "add_custom_target" in commands:
                    should_be_component = True
        
        if should_be_component:
            # This UTILITY target should be a component based on evidence
            return self._create_component_from_custom_target(target, evidence, dependencies)
        
        # Fallback to File API evidence for non-custom targets
        # Get dependencies from File API (evidence-based)
        target_deps = getattr(target, "dependencies", []) or []
        has_dependencies = len(target_deps) > 0
        
        if has_dependencies:
            # UTILITY with dependencies -> Aggregator (orchestrates other targets)
            return Aggregator(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
        else:
            # UTILITY without dependencies -> Utility (no artifacts, no deps)
            return Utility(id=None, name=target_name, depends_on=dependencies, evidence=evidence)

    def _create_build_node_from_target(self, target: Any) -> Optional[Union[Component, Aggregator, Runner, Utility]]:
        """Create appropriate build node from CMake target using evidence-first approach."""
        try:
            # Get the actual target object from the wrapper
            actual_target = getattr(target, "target", target)
            
            # Load detailed target information if available
            actual_target = self._load_detailed_target_info(actual_target)
            target_type = getattr(actual_target, "type", "")
            target_name = getattr(target, "name", "")

            # Create evidence for this target
            evidence = self._create_evidence_from_target(target)
            if evidence is None:
                # No evidence available - return None
                return None

            # Don't resolve dependencies yet - will be done in second pass
            dependencies: List[Union[Component, Aggregator, Runner, Utility]] = []

            # Evidence-first classification based on CMake File API spec
            target_type_str = str(target_type)

            # 1. Artifact-producing target types -> Component
            if target_type_str in ["EXECUTABLE", "TargetType.EXECUTABLE", "SHARED_LIBRARY", "STATIC_LIBRARY", "MODULE_LIBRARY", "OBJECT_LIBRARY"]:
                # Validate artifacts only for artifact-producing types
                ResearchBackedUtilities.validate_target_artifacts(actual_target, self._temp_unknown_errors)
                return self._create_component_from_standard_target(target, evidence, dependencies)

            # 2. UTILITY targets -> Classify based on dependencies (evidence-first)
            elif target_type_str in ["UTILITY", "TargetType.UTILITY"]:
                return self._classify_utility_target(actual_target, evidence, dependencies)

            # 3. Other target types -> Utility (no artifacts expected)
            elif target_type_str in ["SHARED", "TargetType.SHARED"]:
                # SHARED targets are shared libraries -> Component
                return self._create_component_from_standard_target(target, evidence, dependencies)

            else:
                # Unknown target type - fatal error as requested
                raise RuntimeError(f"Unknown target type '{target_type}' for target '{target_name}'. This indicates a missed case in the detection logic.")

        except Exception as e:
            # Log the error but don't crash the entire parsing
            print(f"Warning: Failed to create build node for target '{getattr(target, 'name', 'unknown')}': {e}")
            return None

    def _create_evidence_from_target(self, target: Any) -> Optional[Evidence]:
        """Create Evidence from target's backtrace information with full call stack."""
        tgt = target.target if hasattr(target, 'target') else target

        # Hydrate to ensure backtrace + backtraceGraph are present
        dt = self._load_detailed_target_info(tgt)
        if hasattr(dt, 'backtrace') and hasattr(dt, 'backtraceGraph') and dt.backtraceGraph:
            # Find the actual target definition in project files
            target_file, target_line = self._find_target_definition_in_backtrace(
                int(getattr(dt, 'backtrace', 0) or 0), 
                dt.backtraceGraph
            )
            
            if target_file and target_line:
                # Build the full call stack from the target definition
                frames = self._build_call_stack_from_backtrace(
                    leaf_idx=int(getattr(dt, 'backtrace', 0) or 0),
                    backtrace_graph=dt.backtraceGraph,
                    order="leaf-first",
                    repo_root=self.repo_root,
                    trim_non_project=True,  # Only include project files
                )
                if frames:
                    files_list = [f"{p}#L{ln}-L{ln}" for (p, ln, _cmd) in frames]
                    return Evidence(id=None, call_stack=files_list)

        # No evidence available - return None to indicate failure
        return None

    def _extract_dependencies_from_target(self, target: Any) -> List[Union[Component, Aggregator, Runner]]:
        """Extract dependencies using research-backed approach with direct vs transitive distinction."""
        dependencies: List[Union[Component, Aggregator, Runner]] = []

        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)
        target_name = getattr(actual_target, "name", "")

        # Research-backed approach: Use codemodel dependencies first
        fileapi_deps: Set[str] = set()
        if hasattr(actual_target, "dependencies"):
            for dep in actual_target.dependencies:
                if hasattr(dep, "target") and hasattr(dep.target, "name"):
                    fileapi_deps.add(dep.target.name)

        # Cross-check with graphviz for direct-only dependencies if available
        direct_deps = ResearchBackedUtilities.direct_deps(
            target_name, 
            fileapi_deps, 
            self._temp_graphviz_deps.get(target_name) if self._temp_graphviz_deps else None
        )

        # Find the dependency objects
        for dep_name in direct_deps:
            # Find in components
            for comp in self._temp_components:
                if comp.name == dep_name:
                    dependencies.append(comp)
                    break
            else:
                # Find in aggregators
                for agg in self._temp_aggregators:
                    if agg.name == dep_name:
                        dependencies.append(agg)
                        break
                else:
                    # Find in runners
                    for runner in self._temp_runners:
                        if runner.name == dep_name:
                            dependencies.append(runner)
                            break

        return dependencies

    def _create_component_from_standard_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner, Utility]]) -> Component:
        """Create Component from standard CMake target (EXECUTABLE, LIBRARY, etc.)."""
        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)
        
        # Load detailed target information (research-backed approach)
        hydrated_target = self._load_detailed_target_info(actual_target)

        # Determine component type from CMake target type (evidence-based)
        component_type = self._get_component_type_from_cmake_target(hydrated_target)

        # Extract source files
        source_files: List[Path] = []
        if hasattr(hydrated_target, "sources") and hydrated_target.sources:
            for source in hydrated_target.sources:
                if isinstance(source, dict) and "path" in source:
                    source_path = Path(str(source["path"]))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)
                elif hasattr(source, "path"):
                    source_path = Path(str(source.path))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)
        elif isinstance(hydrated_target, dict) and "sources" in hydrated_target:
            for source in hydrated_target["sources"]:
                if isinstance(source, dict) and "path" in source:
                    source_path = Path(str(source["path"]))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)

        # Get programming language from compileGroups
        programming_language = self._extract_programming_language_from_target(hydrated_target)

        # Get output paths from artifacts
        output_path = self._extract_output_path_from_target(hydrated_target)

        # Extract external packages from link command fragments
        external_packages = self._extract_external_packages_from_target(hydrated_target)

        # Detect runtime environment
        runtime = self._detect_runtime_from_target(hydrated_target, source_files)
        
        # Logical constraint: if programming language is UNKNOWN, runtime must also be UNKNOWN
        if programming_language == "UNKNOWN":
            runtime = None

        # Create component location for the build action
        build_location = ComponentLocation(id=None, path=output_path, action="build", source_location=None, evidence=evidence)

        # Research-backed approach: Get artifact name from File API
        artifact_name = ResearchBackedUtilities.get_artifact_name_from_target(hydrated_target)
        if not artifact_name:
            # Report UNKNOWN if no artifact evidence
            ResearchBackedUtilities.unknown_field(
                "artifact_name",
                f"target_{getattr(hydrated_target, 'name', '')}",
                {
                    "has_artifacts": hasattr(hydrated_target, "artifacts") and bool(hydrated_target.artifacts),
                    "has_nameOnDisk": hasattr(hydrated_target, "nameOnDisk") and bool(hydrated_target.nameOnDisk)
                },
                self._temp_unknown_errors
            )
            artifact_name = getattr(hydrated_target, "name", "")

        return Component(
            id=None,
            name=getattr(target, "name", ""),
            type=component_type,
            runtime=runtime,
            output=artifact_name,
            output_path=output_path,
            programming_language=programming_language,
            source_files=source_files,
            external_packages=external_packages,
            depends_on=dependencies,
            evidence=evidence,
            locations=[build_location],
            test_link_id=None,
            test_link_name=None,
        )

    def _create_node_from_custom_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner, Utility]]) -> Union[Component, Aggregator, Runner]:
        """Create appropriate node from custom target using evidence-based classification."""
        target_name = getattr(target, "name", "")
        
        # Use CMakeParser for evidence-based classification
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based classification.")
        
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        if not custom_target_info:
            # No evidence available - fail fast with UNKNOWN
            ResearchBackedUtilities.unknown_field(
                "custom_target_classification",
                f"target_{target_name}",
                {"has_cmake_evidence": False},
                self._temp_unknown_errors
            )
            raise ValueError(f"No CMakeLists.txt evidence found for custom target '{target_name}'. " +
                           f"Cannot perform evidence-based classification without CMakeLists.txt data.")
        
        # Evidence-based classification using parsed CMakeLists.txt data
        has_commands = custom_target_info['has_commands']
        has_depends = custom_target_info['has_depends']
        has_output = custom_target_info['has_output']
        has_byproducts = custom_target_info['has_byproducts']
        
        # Classification logic based on evidence:
        # 1. Has OUTPUT/BYPRODUCTS -> Component (produces artifacts)
        if has_output or has_byproducts:
            return self._create_component_from_custom_target(target, evidence, dependencies)
        
        # 2. Has DEPENDS but no COMMAND/OUTPUT -> Aggregator (groups dependencies)
        elif has_depends and not has_commands and not has_output:
            return Aggregator(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
        
        # 3. Has COMMAND but no OUTPUT/BYPRODUCTS -> Runner (executes commands)
        elif has_commands and not has_output and not has_byproducts:
            # Check if this is a risky runner
            is_risky = self._is_risky_runner(custom_target_info, target_name)
            runner = Runner(id=None, name=target_name, depends_on=dependencies, evidence=evidence)
            
            # Add risky runner validation error if needed
            if is_risky:
                ResearchBackedUtilities.unknown_field(
                    "risky_runner",
                    f"target_{target_name}",
                    {
                        "has_commands": has_commands,
                        "has_depends": has_depends,
                        "command": custom_target_info.get('parameters', {}).get('COMMAND', []),
                        "working_directory": custom_target_info.get('parameters', {}).get('WORKING_DIRECTORY', '')
                    },
                    self._temp_unknown_errors
                )
            
            return runner
        
        # 4. No clear evidence -> fail fast
        else:
            ResearchBackedUtilities.unknown_field(
                "custom_target_classification",
                f"target_{target_name}",
                {
                    "has_commands": has_commands,
                    "has_depends": has_depends,
                    "has_output": has_output,
                    "has_byproducts": has_byproducts
                },
                self._temp_unknown_errors
            )
            raise ValueError(f"Custom target '{target_name}' has ambiguous classification. " +
                           f"Evidence: commands={has_commands}, depends={has_depends}, " +
                           f"output={has_output}, byproducts={has_byproducts}. " +
                           f"Cannot determine target type without clear evidence.")
    

    def _has_output_or_byproduct(self, target: Any) -> bool:
        """Check if custom target has OUTPUT or BYPRODUCT using evidence-based detection."""
        # Check artifacts for output files (evidence-based)
        if hasattr(target, "artifacts") and target.artifacts:
            return True

        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            return custom_target_info.get('has_output', False) or custom_target_info.get('has_byproducts', False)
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has OUTPUT/BYPRODUCTS without evidence.")

    def _has_command_only(self, target: Any) -> bool:
        """Check if custom target has COMMAND but no OUTPUT/BYPRODUCT using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            has_commands = custom_target_info.get('has_commands', False)
            has_output = custom_target_info.get('has_output', False)
            has_byproducts = custom_target_info.get('has_byproducts', False)
            
            return has_commands and not has_output and not has_byproducts
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has COMMAND without evidence.")

    def _has_depends_only(self, target: Any) -> bool:
        """Check if custom target has only DEPENDS using evidence-based detection."""
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based detection.")
        
        target_name = getattr(target, "name", "")
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Use evidence from CMakeLists.txt
            has_depends = custom_target_info.get('has_depends', False)
            has_commands = custom_target_info.get('has_commands', False)
            has_output = custom_target_info.get('has_output', False)
            has_byproducts = custom_target_info.get('has_byproducts', False)
            
            # Has DEPENDS but no COMMAND/OUTPUT/BYPRODUCTS -> Aggregator
            return has_depends and not has_commands and not has_output and not has_byproducts
        
        # If no evidence found, fail fast
        raise ValueError(f"No CMakeLists.txt evidence found for target '{target_name}'. " +
                       f"Cannot determine if target has DEPENDS without evidence.")

    def _create_component_from_custom_target(self, target: Any, evidence: Evidence, dependencies: List[Union[Component, Aggregator, Runner, Utility]]) -> Component:
        """Create Component from custom target that produces output."""
        target_name = getattr(target, "name", "")
        # Get the actual target object from the wrapper
        actual_target = getattr(target, "target", target)

        # Extract source files (may be empty for custom targets)
        source_files: List[Path] = []
        if hasattr(actual_target, "sources") and actual_target.sources:
            for source in actual_target.sources:
                if hasattr(source, "path"):
                    source_path = Path(str(source.path))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)
        elif isinstance(actual_target, dict) and "sources" in actual_target:
            for source in actual_target["sources"]:
                if isinstance(source, dict) and "path" in source:
                    source_path = Path(str(source["path"]))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files.append(source_path)

        # Get output path from artifacts
        # For non-C/C++ components, use BuildOutputFinder to get the correct output path
        programming_language = self._extract_programming_language_from_custom_target(actual_target)
        if programming_language and programming_language not in ["c", "cpp", "cxx"]:
            # Use BuildOutputFinder for all non-C/C++ languages
            build_output_path = self._extract_build_output_path_from_target(actual_target, programming_language)
            if build_output_path:
                output_path = build_output_path
            else:
                # Fallback if BuildOutputFinder fails
                output_path = self._extract_output_path_from_target(actual_target)
        else:
            output_path = self._extract_output_path_from_target(actual_target)

        # Determine component type based on output (evidence-based)
        component_type = self._detect_component_type_from_output(output_path)
        if component_type is None:
            # Try to detect component type from build command evidence
            component_type = self._detect_component_type_from_build_command(actual_target)
            if component_type is None:
                # Unknown component type - report UNKNOWN
                ResearchBackedUtilities.unknown_field(
                    "component_type",
                    f"target_{target_name}",
                    {"output_path": str(output_path), "extension": output_path.suffix},
                    self._temp_unknown_errors
                )
                component_type = ComponentType.EXECUTABLE  # Fallback for schema compliance

        # Programming language was already detected above for output path extraction

        # Logical constraint: if programming language is UNKNOWN, runtime and component type must also be UNKNOWN
        if programming_language == "UNKNOWN":
            runtime = None
            component_type = ComponentType.EXECUTABLE  # Keep fallback for schema compliance, but mark as UNKNOWN in evidence
        else:
            # Detect runtime environment only if language is known
            runtime = self._detect_runtime_from_custom_target(actual_target, source_files)
            
            # Set runtime based on language if not detected from other evidence
            if runtime is None:
                if programming_language == "java":
                    runtime = Runtime.JVM
                elif programming_language == "go":
                    runtime = Runtime.GO
                elif programming_language == "python":
                    runtime = Runtime.PYTHON
                elif programming_language == "csharp":
                    runtime = Runtime.DOTNET

        # Create component location for the build action
        build_location = ComponentLocation(id=None, path=output_path, action="build", source_location=None, evidence=evidence)

        # Extract the actual output filename from the output path
        output_filename = output_path.name if output_path else target_name
        
        return Component(
            id=None,
            name=target_name,
            type=component_type,
            runtime=runtime,
            output=output_filename,
            output_path=output_path,
            programming_language=programming_language,
            source_files=source_files,
            external_packages=[],  # Custom targets typically don't have external packages
            depends_on=dependencies,
            evidence=evidence,
            locations=[build_location],
            test_link_id=None,
            test_link_name=None,
        )

    def _detect_component_type_from_output(self, output_path: Path) -> Optional[ComponentType]:
        """Detect component type from output file extension using evidence-based approach."""
        ext = output_path.suffix.lower()
        if ext in [".exe", ""]:  # Empty extension often means executable
            return ComponentType.EXECUTABLE
        elif ext in [".so", ".dll", ".dylib"]:
            return ComponentType.SHARED_LIBRARY
        elif ext in [".a", ".lib"]:
            return ComponentType.STATIC_LIBRARY
        elif ext in [".jar"]:
            return ComponentType.VM
        else:
            # Unknown extension - return None instead of defaulting
            return None

    def _detect_component_type_from_build_command(self, target: Any) -> Optional[ComponentType]:
        """Detect component type from build command evidence using generator-aware parsing."""
        target_name = getattr(target, "name", "")
        
        # For non-C/C++ components, use the BuildOutputFinder to detect type from build files
        programming_language = self._extract_programming_language_from_custom_target(target)
        if programming_language and programming_language not in ["c", "cpp", "cxx"]:
            # Check if we can find evidence of build commands in generated build files
            build_output_path = self._build_output_finder.find_output(target_hint=target_name, language=programming_language)
            if build_output_path and build_output_path.suffix.lower() in ['.dll', '.so', '.dylib']:
                return ComponentType.SHARED_LIBRARY
            elif build_output_path:
                return ComponentType.EXECUTABLE
            # If no output found, check rule files as fallback
            return self._detect_component_type_from_rule_files(target, programming_language)
        
        # For C/C++ components, use the original rule file approach
        return self._detect_component_type_from_rule_files(target, "c")
    
    def _detect_component_type_from_rule_files(self, target: Any, language: str) -> Optional[ComponentType]:
        """Detect component type from rule files as fallback for any language."""
        if hasattr(target, "sources") and target.sources:
            for source in target.sources:
                if hasattr(source, "path"):
                    source_path = str(source.path)
                    if source_path.endswith(".rule"):
                        try:
                            with open(source_path, 'r', encoding='utf-8') as f:
                                rule_content = f.read()
                                # Check if rule file is empty (only contains comments)
                                if rule_content.strip() in ["# generated from CMake", "# generated from CMake\n"]:
                                    return None
                                
                                rule_content_lower = rule_content.lower()
                                
                                # Language-specific type detection
                                if language == "go":
                                    if ("go build" in rule_content_lower or "go.exe build" in rule_content_lower):
                                        if "-buildmode=c-shared" in rule_content_lower:
                                            return ComponentType.SHARED_LIBRARY
                                        else:
                                            return ComponentType.EXECUTABLE
                                elif language == "java":
                                    # Check for JAR creation (library) vs javac (executable/class files)
                                    if "jar -cf" in rule_content_lower or "jar -c" in rule_content_lower:
                                        return ComponentType.SHARED_LIBRARY
                                    elif "javac" in rule_content_lower:
                                        return ComponentType.EXECUTABLE
                                elif language == "python":
                                    # Python components are typically executables or modules
                                    if "py_compile" in rule_content_lower:
                                        return ComponentType.EXECUTABLE
                                elif language == "csharp":
                                    # Check for DLL vs EXE compilation
                                    if "-target:library" in rule_content_lower or "-out:.dll" in rule_content_lower:
                                        return ComponentType.SHARED_LIBRARY
                                    elif "csc" in rule_content_lower or "dotnet build" in rule_content_lower:
                                        return ComponentType.EXECUTABLE
                                elif language == "rust":
                                    # Check for library vs binary compilation
                                    if "--crate-type lib" in rule_content_lower or ".rlib" in rule_content_lower:
                                        return ComponentType.SHARED_LIBRARY
                                    elif "cargo build" in rule_content_lower or "rustc" in rule_content_lower:
                                        return ComponentType.EXECUTABLE
                                        
                        except (IOError, UnicodeDecodeError):
                            continue
        return None
    


    def _extract_programming_language_from_custom_target(self, target: Any) -> str:
        """Extract programming language from custom target using evidence-based detection."""
        target_name = getattr(target, "name", "")
        
        # Check for evidence of build commands in generated rule files
        if hasattr(target, "sources") and target.sources:
            for source in target.sources:
                if hasattr(source, "path"):
                    source_path = str(source.path)
                    # Look for .rule files that contain build commands
                    if source_path.endswith(".rule"):
                        try:
                            with open(source_path, 'r', encoding='utf-8') as f:
                                rule_content = f.read().lower()
                                # Look for Go build commands
                                if "go build" in rule_content or "go.exe build" in rule_content:
                                    return "go"
                                # Look for Java build commands
                                elif "javac" in rule_content or "java" in rule_content:
                                    return "java"
                                # Look for Python build commands
                                elif "python" in rule_content or "pip" in rule_content:
                                    return "python"
                                # Look for C# build commands
                                elif "csc" in rule_content or "dotnet" in rule_content:
                                    return "csharp"
                                # Look for C/C++ build commands
                                elif "gcc" in rule_content or "g++" in rule_content or "clang" in rule_content:
                                    return "cpp"
                        except (IOError, UnicodeDecodeError):
                            # If we can't read the file, continue to next source
                            continue
        
        # Check backtrace evidence for build commands (evidence-based from JSON)
        if hasattr(target, "backtraceGraph") and target.backtraceGraph:
            backtrace = target.backtraceGraph
            if isinstance(backtrace, dict) and "commands" in backtrace:
                commands = backtrace["commands"]
                # Look for evidence of build commands in the backtrace
                # This is generic evidence, not macro-specific
                for command in commands:
                    if "go" in command.lower() and "build" in command.lower():
                        return "go"
                    elif "java" in command.lower() and "build" in command.lower():
                        return "java"
                    elif "python" in command.lower() and "build" in command.lower():
                        return "python"
                    elif "csharp" in command.lower() and "build" in command.lower():
                        return "csharp"
                    elif "cpp" in command.lower() and "build" in command.lower():
                        return "cpp"
        
        # No evidence from rule files or backtrace - try BuildOutputFinder as fallback
        # Check if BuildOutputFinder can detect the language from build files
        for language in ["java", "go", "python", "csharp", "rust"]:
            build_output = self._build_output_finder.find_output(target_hint=target_name, language=language)
            if build_output:
                return language
        
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based language detection.")
        
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            # Check if this is a JAR target (created with add_jar)
            if custom_target_info.get('is_jar', False):
                return "java"
            
            # Try to extract language from COMMAND parameters
            command_params = custom_target_info.get('parameters', {}).get('COMMAND', [])
            if command_params:
                # Look for language indicators in the command
                command_str = " ".join(command_params).lower()
                if "go" in command_str or "go build" in command_str:
                    return "go"
                elif "java" in command_str or "javac" in command_str or "jar" in command_str or "add_jar" in command_str:
                    return "java"
                elif "python" in command_str or "py" in command_str:
                    return "python"
                elif "gcc" in command_str or "g++" in command_str or "clang" in command_str:
                    return "cpp"
                elif "csc" in command_str or "dotnet" in command_str:
                    return "csharp"
            
            # If no clear language indicators in command, fail fast
            ResearchBackedUtilities.unknown_field(
                "programming_language",
                f"target_{target_name}",
                {"has_command_evidence": bool(command_params), "command": command_params},
                self._temp_unknown_errors
            )
            return "UNKNOWN"
        
        # No evidence available - fail fast with UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "programming_language",
            f"target_{target_name}",
            {"has_cmake_evidence": False},
            self._temp_unknown_errors
        )
        return "UNKNOWN"
    

    def _detect_runtime_from_custom_target(self, target: Any, source_files: List[Path]) -> Optional[Runtime]:
        """Detect runtime environment from custom target using evidence-based detection."""
        target_name = getattr(target, "name", "")
        
        # Check for evidence of build commands in generated rule files
        if hasattr(target, "sources") and target.sources:
            for source in target.sources:
                if hasattr(source, "path"):
                    source_path = str(source.path)
                    # Look for .rule files that contain build commands
                    if source_path.endswith(".rule"):
                        try:
                            with open(source_path, 'r', encoding='utf-8') as f:
                                rule_content = f.read().lower()
                                # Look for Go build commands
                                if "go build" in rule_content or "go.exe build" in rule_content:
                                    return Runtime.GO
                                # Look for Java build commands
                                elif "javac" in rule_content or "java" in rule_content or "jar" in rule_content:
                                    return Runtime.JVM
                                # Look for Python build commands
                                elif "python" in rule_content or "pip" in rule_content:
                                    return Runtime.PYTHON
                                # Look for C# build commands
                                elif "csc" in rule_content or "dotnet" in rule_content:
                                    return Runtime.DOTNET
                        except (IOError, UnicodeDecodeError):
                            # If we can't read the file, continue to next source
                            continue
        
        # Check for JAR files in target name or output path (evidence-based)
        if ".jar" in target_name.lower():
            return Runtime.JVM
        
        # Check backtrace evidence for build commands (evidence-based from JSON)
        if hasattr(target, "backtraceGraph") and target.backtraceGraph:
            backtrace = target.backtraceGraph
            if isinstance(backtrace, dict) and "commands" in backtrace:
                commands = backtrace["commands"]
                # Look for evidence of build commands in the backtrace
                # This is generic evidence, not macro-specific
                for command in commands:
                    if "go" in command.lower() and "build" in command.lower():
                        return Runtime.GO
                    elif "java" in command.lower() and "build" in command.lower():
                        return Runtime.JVM
                    elif "python" in command.lower() and "build" in command.lower():
                        return Runtime.PYTHON
                    elif "csharp" in command.lower() and "build" in command.lower():
                        return Runtime.DOTNET
        
        # Use CMakeParser for evidence-based detection
        if not self._cmake_parser:
            ResearchBackedUtilities.unknown_field(
                "runtime",
                f"target_{target_name}",
                {"has_cmake_parser": False},
                self._temp_unknown_errors
            )
            return None
        
        custom_target_info = self._cmake_parser.get_custom_target_info(target_name)
        
        if custom_target_info:
            runtime = None
            params = custom_target_info.get("parameters", {})
            cmd_tokens = params.get("COMMAND", [])
            
            # 1) Resolve genex and see if it points to a known component
            by_name = {comp.name: comp for comp in self._temp_components}
            for tok in cmd_tokens:
                resolved = self._expand_genexpr(str(tok), by_name)
                if resolved != tok:
                    # find component with this output_path
                    for comp in self._temp_components:
                        if hasattr(comp, 'output_path') and comp.output_path and str(comp.output_path) == resolved:
                            # Use evidence-based runtime detection
                            runtime = comp.runtime or ResearchBackedUtilities.detect_runtime_evidence_based(comp)
                            break
                if runtime: 
                    break
            
            # 2) Or infer from DEPENDS -> plugin targets (deterministic)
            if not runtime and custom_target_info.get('has_depends'):
                for dep in self._cmake_parser.get_target_dependencies(target_name):
                    # Find the dependency component and use evidence-based runtime detection
                    dep_comp = self._find_component_by_name(dep)
                    if dep_comp:
                        runtime = ResearchBackedUtilities.detect_runtime_evidence_based(dep_comp)
                        if runtime:
                            break
            
            if runtime:
                return runtime
            
            # If no clear runtime indicators found, report UNKNOWN
            ResearchBackedUtilities.unknown_field(
                "runtime",
                f"target_{target_name}",
                {"has_command_evidence": bool(cmd_tokens), "has_depends": custom_target_info.get('has_depends', False)},
                self._temp_unknown_errors
            )
            return None
        
        # No evidence found - report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "runtime",
            f"target_{target_name}",
            {"has_cmake_evidence": False},
            self._temp_unknown_errors
        )
        return None

    def _extract_programming_language_from_target(self, target: Any) -> str:
        """Extract programming language using research-backed toolchains approach."""
        target_name = getattr(target, "name", "")
        
        # Research-backed approach: Use toolchains first
        language = self._detect_programming_language_from_toolchains(target, self._toolchains_info)
        
        if language:
            return language
        
        # Try source files using toolchains as secondary evidence
        if hasattr(target, "sources") and target.sources:
            source_files_list: List[Path] = []
            for source in target.sources:
                if hasattr(source, "path"):
                    source_path = Path(str(source.path))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files_list.append(source_path)
        elif isinstance(target, dict) and "sources" in target:
            source_files_list2: List[Path] = []
            for source in target["sources"]:
                if isinstance(source, dict) and "path" in source:
                    source_path = Path(str(source["path"]))
                    if source_path.is_absolute():
                        source_path = source_path.relative_to(self.repo_root)
                    source_files_list2.append(source_path)
            
            if source_files_list2:
                language = self._detect_programming_language_from_files_with_toolchains(source_files_list2)
                if language:
                    return language
        
        # If no evidence found, report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "programming_language",
            f"target_{target_name}",
            {
                "has_compileGroups": hasattr(target, "compileGroups") and bool(target.compileGroups),
                "has_sources": hasattr(target, "sources") and bool(target.sources),
                "has_toolchains": bool(self._toolchains_info)
            },
            self._temp_unknown_errors
        )
        
        return "unknown"

    def _detect_programming_language_from_files_with_toolchains(self, source_files: List[Path]) -> Optional[str]:
        """Detect programming language from source files using toolchain extensions."""
        if not source_files or not self._toolchains_obj:
            return None
        
        # Get file extensions
        extensions = [f.suffix.lower() for f in source_files]
        
        # Check each toolchain for matching extensions
        for tc in self._toolchains_obj.toolchains:
            if hasattr(tc, 'language') and hasattr(tc, 'sourceFileExtensions'):
                language = tc.language.lower()
                toolchain_extensions = tc.sourceFileExtensions
                
                # Check if any file extension matches this toolchain
                if any(ext in toolchain_extensions for ext in extensions):
                    return language
        
        return None


    def _extract_output_path_from_target(self, target: Any) -> Path:
        """Extract output path from target using research-backed File API approach."""
        target_name = getattr(target, "name", "")
        
        # First, check if this is a Go component using the same logic as programming language detection
        # This ensures consistency between language detection and output path extraction
        programming_language = self._extract_programming_language_from_custom_target(target)
        if programming_language and programming_language not in ["c", "cpp", "cxx"]:
            build_output_path = self._extract_build_output_path_from_target(target, programming_language)
            if build_output_path:
                return build_output_path
        
        # Use the research-backed utility for output path extraction
        output_path = ResearchBackedUtilities.get_output_path_from_target(target, self._temp_cache_dict)
        
        if output_path:
            # Make relative to repo root if absolute
            if output_path.is_absolute():
                try:
                    return output_path.relative_to(self.repo_root)
                except ValueError:
                    return output_path
            else:
                # Path is relative to build directory, make it relative to repo root
                build_dir_relative = self.cmake_config_dir.relative_to(self.repo_root)
                return build_dir_relative / output_path
            return output_path
        
        # Check if this is an INTERFACE target (legitimately has no artifacts)
        target_type = getattr(target, "type", "")
        if target_type == "INTERFACE":
            return Path(target_name)
        
        # If no evidence found, report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "artifact_name",
            f"target_{target_name}",
            {
                "has_artifacts": hasattr(target, "artifacts") and bool(target.artifacts),
                "has_nameOnDisk": hasattr(target, "nameOnDisk") and bool(target.nameOnDisk)
            },
            self._temp_unknown_errors
        )
        
        # Final fallback
        return Path(target_name)

    def _extract_build_output_path_from_target(self, target: Any, language: str) -> Optional[Path]:
        """Extract output path for non-C/C++ components using generator-aware build file parsing."""
        target_name = getattr(target, "name", "")
        
        # Use the BuildOutputFinder to find the actual output path from generated build files
        # This will return None if the target is not a component of the specified language
        build_output_path = self._build_output_finder.find_output(target_hint=target_name, language=language)
        if build_output_path:
            # Convert absolute path to relative path from repo root
            try:
                relative_path = build_output_path.relative_to(self.repo_root)
                return relative_path
            except ValueError:
                # If path is not under repo root, return the filename as a Path
                return Path(build_output_path.name)
        
        # Special case for JVM targets: check if target name suggests JAR output
        if language == "java" and target_name:
            # Check if target name suggests it's a JAR file
            if "extractor" in target_name.lower() or "bridge" in target_name.lower():
                # Try to construct JAR path based on target name
                jar_name = f"{target_name}.jar"
                return Path(jar_name)
        
        # No evidence found for output path
        return None


    def _create_snippet_from_target(self, target: Any) -> Optional[Evidence]:
        """Create Evidence with proper line numbers from target's backtrace."""
        # This method should use the same logic as _create_evidence_from_target
        # For now, delegate to the proper evidence creation method
        return self._create_evidence_from_target(target)

    def _extract_external_packages_from_target(self, target: Any) -> List[ExternalPackage]:
        """Extract external package dependencies using evidence-based detection from CMake File API."""
        packages: List[ExternalPackage] = []
        seen_packages = set()  # To avoid duplicates

        # 1) From CMake cache (toolchain selection) → package manager
        pm = ResearchBackedUtilities.detect_package_manager_from_cache(self._temp_cache_entries)
        if pm:
            packages.append(ExternalPackage(id=None, package_manager=PackageManager(id=None, name=pm, package_name="unknown")))

        # 2) From CMake File API link command fragments (evidence-based)
        if hasattr(target, 'link') and target.link:
            link_data = target.link
            if isinstance(link_data, dict) and 'commandFragments' in link_data and link_data['commandFragments']:
                for fragment in link_data['commandFragments']:
                    if isinstance(fragment, dict) and 'fragment' in fragment and fragment['fragment']:
                        # Extract package names from link fragments
                        fragment_text = fragment['fragment']
                        package_name = self._extract_package_name_from_link_fragment(fragment_text)
                        if package_name and package_name not in seen_packages:
                            seen_packages.add(package_name)
                            packages.append(ExternalPackage(
                                id=None,
                                package_manager=PackageManager(id=None, name=pm or "system", package_name=package_name)
                            ))

        # 3) From CMake File API include directories (evidence-based)
        if hasattr(target, 'compileGroups') and target.compileGroups:
            for group in target.compileGroups:
                if isinstance(group, dict) and 'includes' in group and group['includes']:
                    for include in group['includes']:
                        if isinstance(include, dict) and 'path' in include and include['path']:
                            include_path = include['path']
                            package_name = self._extract_package_name_from_include_path(include_path)
                            if package_name and package_name not in seen_packages:
                                seen_packages.add(package_name)
                                packages.append(ExternalPackage(
                                    id=None,
                                    package_manager=PackageManager(id=None, name=pm or "system", package_name=package_name)
                                ))

        return packages

    def _extract_package_name_from_link_fragment(self, fragment_text: str) -> Optional[str]:
        """Extract package name from link command fragment."""
        fragment_lower = fragment_text.lower()
        
        # Skip compiler flags and system paths - these are not external libraries
        if (fragment_lower.startswith('/') or  # MSVC flags like /DWIN32, /machine:x64
            fragment_lower.startswith('-') or  # GCC flags like -l, -L, -I
            fragment_lower.startswith('"') or  # Quoted paths
            'libpath:' in fragment_lower or  # MSVC library paths
            fragment_lower in ['/subsystem:console', '/subsystem:windows']):  # MSVC subsystem flags
            return None
        
        # Everything else is evidence of an external library - return as-is
        return fragment_lower

    def _extract_package_name_from_include_path(self, include_path: str) -> Optional[str]:
        """Extract package name from include directory path."""
        path_lower = include_path.lower()
        
        # Check for vcpkg paths
        if 'vcpkg' in path_lower:
            # Extract package name from vcpkg path
            # Example: C:/src/vcpkg/installed/x64-windows/include/boost
            path_obj = Path(include_path)
            parts = path_obj.parts
            for i, part in enumerate(parts):
                if part.lower() == 'include' and i + 1 < len(parts):
                    package_name = parts[i + 1]
                    # Return the actual package name as evidence - no hardcoded recognition
                    return package_name.lower()
        
        # Check for Conan paths
        elif 'conan' in path_lower and 'data' in path_lower:
            # Extract package name from Conan path
            # Example: ~/.conan/data/package/version/user/channel/package_id/include/boost
            path_obj = Path(include_path)
            parts = path_obj.parts
            for i, part in enumerate(parts):
                if part.lower() == 'include' and i + 1 < len(parts):
                    package_name = parts[i + 1]
                    # Return the actual package name as evidence
                    return package_name.lower()
        
        # Check for system paths
        # Only extract from system include paths on non-Windows platforms
        if sys.platform != "win32" and (path_lower.startswith('/usr/include/') or path_lower.startswith('/usr/local/include/')):
            # Extract package name from system path
            # Example: /usr/include/boost, /usr/local/include/opencv2
            path_obj = Path(include_path)
            if len(path_obj.parts) >= 4:  # /usr/include/package or /usr/local/include/package
                package_name = path_obj.name  # Last part is the package name
                # Return the actual package name as evidence
                return package_name.lower()
        
        return None


    def _extract_external_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract external package dependencies from CMake cache entries and CMakeLists.txt files."""
        packages: List[ExternalPackage] = []
        
        # Check if we have cache data available
        if not hasattr(self, '_temp_cache_entries'):
            return packages
        
        # Look for package manager indicators in cache entries
        vcpkg_packages = self._extract_vcpkg_packages_from_cache()
        conan_packages = self._extract_conan_packages_from_cache()
        
        packages.extend(vcpkg_packages)
        packages.extend(conan_packages)
        
        # Extract packages from CMakeLists.txt files (evidence-based)
        if self._cmake_parser:
            packages.extend(self._extract_packages_from_cmake_files())
        
        return packages

    def _extract_packages_from_cmake_files(self) -> List[ExternalPackage]:
        """Extract external packages from CMakeLists.txt files using evidence-based parsing."""
        packages: List[ExternalPackage] = []
        
        if not self._cmake_parser:
            return packages
        
        # Extract packages from find_package() calls
        for package_info in self._cmake_parser.find_packages:
            package_name = package_info['name']
            
            # Determine package manager based on evidence
            package_manager = self._determine_package_manager_from_evidence(package_name, package_info)
            
            if package_manager:
                external_package = ExternalPackage(
                    id=None,
                    package_manager=package_manager
                )
                packages.append(external_package)
        
        return packages

    def _determine_package_manager_from_evidence(self, package_name: str, package_info: Dict[str, Any]) -> Optional[PackageManager]:
        """Determine package manager from evidence in CMakeLists.txt and cache."""
        # Check if vcpkg is being used (from cache evidence)
        vcpkg_active = any(
            hasattr(entry, 'name') and entry.name == 'CMAKE_TOOLCHAIN_FILE' and 
            hasattr(entry, 'value') and 'vcpkg' in str(entry.value).lower()
            for entry in self._temp_cache_entries
        )
        
        # Check if conan is being used (from cache evidence)
        conan_active = any(
            hasattr(entry, 'name') and 'conan' in entry.name.lower() or
            hasattr(entry, 'value') and 'conan' in str(entry.value).lower()
            for entry in self._temp_cache_entries
        )
        
        # Determine package manager based on evidence
        if vcpkg_active:
            return PackageManager(id=None, name="vcpkg", package_name=package_name)
        elif conan_active:
            return PackageManager(id=None, name="conan", package_name=package_name)
        else:
            # Default to system package manager
            return PackageManager(id=None, name="system", package_name=package_name)

    def _extract_vcpkg_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract vcpkg packages from CMake cache entries."""
        packages: List[ExternalPackage] = []
        
        # Check for vcpkg toolchain file
        vcpkg_detected = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if entry.name == 'CMAKE_TOOLCHAIN_FILE' and 'vcpkg' in str(entry.value).lower():
                    vcpkg_detected = True
                    break
        
        if vcpkg_detected:
            # Extract specific packages from vcpkg cache entries
            for entry in self._temp_cache_entries:
                if hasattr(entry, 'name') and hasattr(entry, 'value'):
                    name = entry.name
                    value = str(entry.value)
                    
                    # Look for package-specific entries (e.g., Boost_DIR, doctest_DIR)
                    if name.endswith('_DIR') and 'vcpkg' in value.lower():
                        # Extract package name from the directory entry
                        package_name = name[:-4]  # Remove '_DIR' suffix
                        
                        # Skip vcpkg-specific entries
                        if not package_name.startswith(('VCPKG_', 'Z_VCPKG_', '_VCPKG_', 'X_VCPKG_')):
                            packages.append(ExternalPackage(
                                id=None, 
                                package_manager=PackageManager(id=None, name="vcpkg", package_name=package_name)
                            ))
        
        return packages

    def _extract_conan_packages_from_cache(self) -> List[ExternalPackage]:
        """Extract conan packages from CMake cache entries."""
        packages: List[ExternalPackage] = []
        
        # Check for conan indicators in cache entries
        conan_detected = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if 'conan' in entry.name.lower() or 'conan' in str(entry.value).lower():
                    conan_detected = True
                    break
        
        if conan_detected:
            # Add a generic conan package entry
            packages.append(ExternalPackage(
                id=None, 
                package_manager=PackageManager(id=None, name="conan", package_name="unknown")
            ))
        
        return packages

    def _update_components_with_global_packages(self) -> None:
        """Update existing components with global external packages from cache."""
        for component in self._temp_components:
            # Add global packages to each component, avoiding duplicates
            seen = {(p.package_manager.name, p.package_manager.package_name)
                    for p in component.external_packages}
            for pkg in self._temp_global_external_packages:
                key = (pkg.package_manager.name, pkg.package_manager.package_name)
                if key not in seen:
                    component.external_packages.append(pkg)
                    seen.add(key)

    def _detect_runtime_from_target(self, target: Any, source_files: List[Path]) -> Optional[Runtime]:
        """Detect runtime environment using evidence from CMake data."""
        # Use generic, evidence-based runtime detection
        runtime = ResearchBackedUtilities.detect_runtime_evidence_based(target, self._toolchains_obj)
        if runtime:
            return runtime
        
        # Try compile definitions as fallback (evidence-based)
        if hasattr(target, "compileGroups"):
            runtime = ResearchBackedUtilities.runtime_from_defines(target.compileGroups)
            if runtime:
                return runtime
        
        # Try linkage-based detection for test executables
        target_name = getattr(target, "name", "")
        if target_name.endswith("_test") or "test" in target_name.lower():
            runtime = self._detect_runtime_via_linkage(target)
            if runtime is not None:
                return runtime

        # No evidence found - report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "runtime",
            f"target_{target_name}",
            {
                "has_compileGroups": hasattr(target, "compileGroups") and bool(target.compileGroups),
                "has_artifacts": hasattr(target, "artifacts") and bool(target.artifacts),
                "has_source_files": bool(source_files),
                "has_toolchains": self._has_toolchains()
            },
            self._temp_unknown_errors
        )
        
        return None

    def _detect_runtime_from_toolchains(self, target: Any) -> Optional[Runtime]:
        """Detect runtime from toolchain information."""
        if not self._has_toolchains():
            return None
            
        # Get the primary language from compileGroups
        primary_language = None
        if hasattr(target, "compileGroups"):
            for cg in target.compileGroups:
                # Handle both dict and object formats
                if isinstance(cg, dict):
                    language = cg.get('language')
                else:
                    language = getattr(cg, 'language', None)
                
                if language:
                    primary_language = language.lower()
                    break
        
        if not primary_language:
            return None
            
        # Map language to runtime based on toolchain
        if self._toolchains_obj and hasattr(self._toolchains_obj, 'toolchains'):
            for tc in self._toolchains_obj.toolchains:
                if hasattr(tc, "language") and tc.language.lower() == primary_language.lower():
                    if hasattr(tc, "compiler") and hasattr(tc.compiler, "id"):
                        compiler_id = str(tc.compiler.id).lower()
                        if "msvc" in compiler_id or "cl" in compiler_id:
                            return Runtime.VS_CPP
                        elif "gcc" in compiler_id or "g++" in compiler_id:
                            return Runtime.CLANG_C
                        elif "clang" in compiler_id:
                            return Runtime.CLANG_C
                    break
                
        return None

    def _detect_runtime_via_linkage(self, target: Any) -> Optional[Runtime]:
        """Detect runtime via linkage to plugin targets (deterministic)."""
        _ = getattr(target, "name", "")  # target_name not used
        
        # Get known plugin targets with their runtimes
        known_plugins = {}
        for comp in self._temp_components:
            if hasattr(comp, 'runtime') and comp.runtime is not None:
                # Check if this is a plugin target (has runtime token in name)
                runtime = ResearchBackedUtilities.detect_runtime_evidence_based(comp)
                if runtime:
                    known_plugins[comp.name] = runtime
        
        # Check transitive dependencies for plugin targets
        if hasattr(target, "depends_on"):
            plugin_runtimes = set()
            for dep in target.depends_on:
                if hasattr(dep, "name"):
                    dep_name = dep.name
                    if dep_name in known_plugins:
                        plugin_runtimes.add(known_plugins[dep_name])
            
            # If exactly one plugin runtime is linked, use it
            if len(plugin_runtimes) == 1:
                return plugin_runtimes.pop()
        
        # Check link command fragments for plugin artifacts
        if hasattr(target, "link") and hasattr(target.link, "commandFragments"):
            link_paths = set()
            for frag in target.link.commandFragments:
                if hasattr(frag, "path") and frag.path:
                    link_paths.add(str(frag.path))
                if hasattr(frag, "fragment") and frag.fragment:
                    frag_str = str(frag.fragment)
                    if frag_str.startswith("/") or (":" in frag_str and "\\" in frag_str):
                        link_paths.add(frag_str.strip())
            
            # Check if any link paths match plugin artifacts
            plugin_runtimes = set()
            for comp in self._temp_components:
                if hasattr(comp, 'output_path') and comp.output_path:
                    artifact_path = str(comp.output_path)
                    if artifact_path in link_paths:
                        runtime = ResearchBackedUtilities.detect_runtime_evidence_based(comp)
                        if runtime:
                            plugin_runtimes.add(runtime)
            
            if len(plugin_runtimes) == 1:
                return plugin_runtimes.pop()
        
        return None

    def _get_component_type_from_cmake_target(self, target: Any) -> ComponentType:
        """Get component type from CMake target type (evidence-based)."""
        target_type = getattr(target, "type", "")
        target_type_str = str(target_type)
        target_name = getattr(target, "name", "")

        # Map CMake target types to component types
        if target_type_str in ["EXECUTABLE", "TargetType.EXECUTABLE"]:
            return ComponentType.EXECUTABLE
        elif target_type_str in ["SHARED_LIBRARY", "SHARED", "TargetType.SHARED"]:
            return ComponentType.SHARED_LIBRARY
        elif target_type_str in ["STATIC_LIBRARY", "STATIC", "TargetType.STATIC"]:
            return ComponentType.STATIC_LIBRARY
        elif target_type_str in ["MODULE_LIBRARY", "TargetType.MODULE_LIBRARY"]:
            return ComponentType.SHARED_LIBRARY  # Treat as shared library
        else:
            # Research-backed approach: Use artifacts for Windows-specific detection
            if hasattr(target, "artifacts") and target.artifacts:
                component_type = self._detect_component_type_from_artifacts(target.artifacts)
                if component_type is not None:
                    return component_type
            elif hasattr(target, "nameOnDisk") and target.nameOnDisk:
                component_type = self._detect_component_type_from_output(Path(target.nameOnDisk))
                if component_type is not None:
                    return component_type
            
            # No evidence found - report UNKNOWN
            ResearchBackedUtilities.unknown_field(
                "component_type",
                f"target_{target_name}",
                {
                    "target_type": target_type_str,
                    "has_artifacts": hasattr(target, "artifacts") and bool(target.artifacts),
                    "has_nameOnDisk": hasattr(target, "nameOnDisk") and bool(target.nameOnDisk)
                },
                self._temp_unknown_errors
            )
            return ComponentType.EXECUTABLE  # Fallback for schema compliance

    def _detect_component_type_from_artifacts(self, artifacts: List[Any]) -> Optional[ComponentType]:
        """Detect component type from artifacts with Windows-specific handling."""
        for artifact in artifacts:
            if hasattr(artifact, "path"):
                artifact_path = Path(artifact.path)
                extension = artifact_path.suffix.lower()
                
                # Windows-specific extensions
                if extension == ".exe":
                    return ComponentType.EXECUTABLE
                elif extension == ".dll":
                    return ComponentType.SHARED_LIBRARY
                elif extension == ".lib":
                    # Could be static library or import library
                    # Check if there's also a .dll artifact
                    has_dll = any(
                        hasattr(a, "path") and Path(a.path).suffix.lower() == ".dll" 
                        for a in artifacts
                    )
                    if has_dll:
                        # This is an import library, the .dll is the main artifact
                        continue
                    else:
                        return ComponentType.STATIC_LIBRARY
                elif extension in [".so", ".dylib"]:
                    return ComponentType.SHARED_LIBRARY
                elif extension == ".a":
                    return ComponentType.STATIC_LIBRARY
        
        # Fallback to first artifact
        if artifacts and hasattr(artifacts[0], "path"):
            return self._detect_component_type_from_output(Path(artifacts[0].path))
        
        return None

    def _is_risky_runner(self, custom_target_info: Dict[str, Any], target_name: str) -> bool:
        """Determine if a runner is risky based on evidence-based criteria."""
        # Risky criteria:
        # 1. Has COMMAND with no DEPENDS
        # 2. COMMAND resolves to a path under the build dir
        
        has_commands = custom_target_info.get('has_commands', False)
        has_depends = custom_target_info.get('has_depends', False)
        
        # Criterion 1: Has COMMAND with no DEPENDS
        if has_commands and not has_depends:
            return True
        
        # Criterion 2: COMMAND resolves to a path under the build dir
        if has_commands:
            command_params = custom_target_info.get('parameters', {}).get('COMMAND', [])
            if command_params:
                first_command = str(command_params[0])
                # Check if command is a path under build directory
                try:
                    command_path = Path(first_command)
                    if command_path.is_absolute() and self.cmake_config_dir in command_path.parents:
                        return True
                except (ValueError, OSError):
                    pass
        
        return False

    def _extract_candidate_exe_from_command(self, cmd: List[str]) -> Optional[str]:
        """Return likely test executable basename by scanning the full CTest command (right-to-left).
        Ignores chain operators like &&, ;, | and filters out obvious launchers (python/go/java/ctest)."""
        chain_ops = {"&&", ";", "|"}
        for token in reversed(cmd):
            t = str(token).strip()
            if not t or t in chain_ops:
                continue
            try:
                name = Path(t).name or t
            except Exception:
                name = t
            base = name.lower()
            if base in {"python", "python3", "py", "go", "java", "ctest"}:
                continue
            return name
        return None

    def _has_toolchains(self) -> bool:
        """Check if toolchains information is available."""
        return bool(self._toolchains_obj) or bool(self._toolchains_info)




    def _build_artifact_index(self, codemodel_targets: List[Any]) -> Dict[str, Any]:
        """
        Build an artifact index by basename for deterministic test-to-component mapping.
        Cross-configuration: indexes all configurations for stem and basename matching.
        key: lowercase basename/stem (e.g., 'idl_plugin_test.exe', 'idl_plugin_test')
        val: target dict
        """
        idx = {}
        for t in codemodel_targets:
            if hasattr(t, "artifacts") and t.artifacts:
                for art in t.artifacts:
                    if hasattr(art, "path"):
                        p = Path(str(art.path))
                        base = p.name.lower()
                        stem = p.stem.lower()
                        idx[base] = t
                        # Also allow mapping by stem
                        idx[stem] = t
                        # Handle .exe extension
                        if not base.endswith('.exe'):
                            idx[stem + '.exe'] = t
            elif isinstance(t, dict) and "artifacts" in t:
                for art in t["artifacts"]:
                    if isinstance(art, dict) and "path" in art:
                        p = Path(art["path"])
                        base = p.name.lower()
                        stem = p.stem.lower()
                        idx[base] = t
                        idx[stem] = t
                        if not base.endswith('.exe'):
                            idx[stem + '.exe'] = t
        return idx

    def _build_component_artifact_index(self) -> Dict[str, Any]:
        """
        Build an artifact index from components for deterministic test-to-component mapping.
        Cross-configuration: indexes all components for stem and basename matching.
        key: lowercase basename/stem (e.g., 'idl_plugin_test.exe', 'idl_plugin_test')
        val: component object
        """
        idx = {}
        for comp in self._temp_components:
            if hasattr(comp, 'output') and comp.output:
                # Use the output name as the artifact name
                artifact_name = comp.output
                p = Path(artifact_name)
                base = p.name.lower()
                stem = p.stem.lower()
                idx[base] = comp
                # Also allow mapping by stem
                idx[stem] = comp
                # Handle .exe extension
                if not base.endswith('.exe'):
                    idx[stem + '.exe'] = comp
            elif hasattr(comp, 'output_path') and comp.output_path:
                # Use the output path as the artifact path
                p = comp.output_path
                base = p.name.lower()
                stem = p.stem.lower()
                idx[base] = comp
                idx[stem] = comp
                if not base.endswith('.exe'):
                    idx[stem + '.exe'] = comp
        return idx

    def _expand_genexpr(self, token: str, by_name: Dict[str, Any]) -> str:
        """Expand $<TARGET_FILE:...> generator expressions."""
        import re
        GEN_RE = re.compile(r"\$<TARGET_FILE:([A-Za-z0-9_.+-]+)>")
        m = GEN_RE.fullmatch(token)
        if not m:
            return token
        tgt = by_name.get(m.group(1))
        if not tgt:
            return token
        
        # Get artifacts from target
        artifacts = []
        if hasattr(tgt, "artifacts") and tgt.artifacts:
            artifacts = tgt.artifacts
        elif isinstance(tgt, dict) and "artifacts" in tgt:
            artifacts = tgt["artifacts"]
        
        if artifacts:
            if hasattr(artifacts[0], "path"):
                return str(artifacts[0].path)
            elif isinstance(artifacts[0], dict) and "path" in artifacts[0]:
                return artifacts[0]["path"]
        return token

    def _segment_command(self, cmd: List[str]) -> List[List[str]]:
        """Segment command by shell operators."""
        SHELL_SPLIT = {"&&", ";", "||"}
        segs, cur = [], []
        for tok in cmd:
            if tok in SHELL_SPLIT:
                if cur: 
                    segs.append(cur)
                    cur = []
            else:
                cur.append(tok)
        if cur: 
            segs.append(cur)
        return segs

    def _resolve_test_components(self, test: Dict[str, Any], art_by_base: Dict[str, Any], tgt_by_name: Dict[str, Any]) -> List[str]:
        """
        Returns a list of target names (components) this test exercises.
        Deterministic: artifacts or explicit labels only.
        """
        cmd = test.get("command", [])[:]  # list[str]
        # Expand $<TARGET_FILE:...>
        cmd = [self._expand_genexpr(tok, tgt_by_name) for tok in cmd]
        segs = self._segment_command(cmd)

        components: List[str] = []

        # 1) Direct artifact presence
        for seg in segs:
            lowered = [Path(x.strip('"')).name.lower() for x in seg]
            for base in lowered:
                if base in art_by_base:
                    target = art_by_base[base]
                    if hasattr(target, "name"):
                        components.append(target.name)
                    elif isinstance(target, dict) and "name" in target:
                        components.append(target["name"])
                    else:
                        # Handle component objects directly
                        components.append(str(target))

        if components:
            return components

        # 2/3/4) Labels contract (see Patch C)
        labels = {l.lower() for l in test.get("labels", [])}
        comp_labels = [l.split(":", 1)[1] for l in labels if l.startswith("component:")]
        if comp_labels:
            return comp_labels

        # 3) Environment path mapping (deterministic)
        env_components = self._map_via_env_paths(test, art_by_base, tgt_by_name)
        if env_components:
            return env_components

        # If no mapping found, this will be reported as UNKNOWN
        return []

    def _get_cmake_file_from_backtrace(self, backtrace_graph: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract CMake file path from backtrace graph."""
        if not backtrace_graph:
            return None
        
        # Try to get the file path from backtrace
        if "file" in backtrace_graph:
            return str(backtrace_graph["file"])
        elif "nodes" in backtrace_graph:
            # Look for file information in nodes
            for node in backtrace_graph["nodes"]:
                if isinstance(node, dict) and "file" in node:
                    return str(node["file"])
        return None

    def _map_via_env_paths(self, test: Dict[str, Any], art_by_base: Dict[str, Any], tgt_by_name: Dict[str, Any]) -> List[str]:
        """Map test to components via environment paths (deterministic)."""
        import os
        
        # Get environment from test properties
        properties = test.get("properties", [])
        env = ""
        for prop in properties:
            if isinstance(prop, dict) and prop.get("name") == "ENVIRONMENT":
                env = prop.get("value", "")
                break
        
        if not env:
            return []
        
        # Extract paths from environment
        dirs = set()
        for line in env.splitlines():
            if "=" not in line:
                continue
            _, v = line.split("=", 1)
            for e in v.split(os.pathsep):
                e = e.strip()
                if e:
                    dirs.add(Path(e))
        
        # Build plugin directories map
        plugin_dirs = {}
        for comp in self._temp_components:
            if hasattr(comp, 'output_path') and comp.output_path:
                # Check if this is a plugin target
                runtime = ResearchBackedUtilities.detect_runtime_evidence_based(comp)
                if runtime:  # This is a plugin target
                    plugin_dirs[comp.output_path.parent] = comp.name
        
        # Check for exact directory matches
        hits = set()
        for d in dirs:
            if d in plugin_dirs:
                hits.add(plugin_dirs[d])
        
        # Return exactly one component if found
        return [hits.pop()] if len(hits) == 1 else []

    def _load_detailed_target_info(self, target: Any) -> Any:
        """Load detailed target information from separate JSON file if available."""
        return self._load_target_info_research_backed(target)

    def _load_target_info_research_backed(self, target: Any) -> Any:
        """Load target information using the research-backed approach."""
        try:
            target_name = getattr(target, 'name', '')
            if not target_name:
                return target
            
            # Step 1: Read reply/index-*.json to find codemodel path
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            index_files = list(reply_dir.glob("index-*.json"))
            if not index_files:
                return target
            
            # Load the latest index file to find codemodel path
            latest_index = max(index_files, key=lambda p: p.stat().st_mtime)
            with open(latest_index, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Step 2: Find codemodel v2 in index
            codemodel_path = None
            if 'reply' in index_data and 'codemodel-v2' in index_data['reply']:
                codemodel_path = index_data['reply']['codemodel-v2'].get('jsonFile')
            
            if not codemodel_path:
                return target
            
            # Load codemodel
            codemodel_file = reply_dir / codemodel_path
            if not codemodel_file.exists():
                return target
            
            with open(codemodel_file, 'r', encoding='utf-8') as f:
                codemodel_data = json.load(f)
            
            # Step 3: Pick the active config (e.g., Debug) from configurations
            if not codemodel_data.get('configurations'):
                return target
            
            # Use first configuration (typically Debug)
            config = codemodel_data['configurations'][0]
            
            # Step 4: For each target, resolve jsonFile relative to codemodel file
            for target_stub in config.get('targets', []):
                if target_stub.get('name') == target_name:
                    json_file = target_stub.get('jsonFile', '')
                    if json_file:
                        # Load the detailed target JSON (path is relative to codemodel file)
                        target_json_path = codemodel_file.parent / json_file
                        if target_json_path.exists():
                            with open(target_json_path, 'r', encoding='utf-8') as f:
                                target_data = json.load(f)
                            
                            # Step 5: Extract target details (type, nameOnDisk, artifacts)
                            class DetailedTarget:
                                def __init__(self, data: Dict[str, Any]):
                                    # Copy essential original target attributes
                                    self.name = getattr(target, 'name', '')
                                    self.id = getattr(target, 'id', '')
                                    
                                    # Override with detailed data
                                    self.type = data.get('type', '')
                                    self.nameOnDisk = data.get('nameOnDisk', '')
                                    self.artifacts = data.get('artifacts', [])
                                    self.dependencies = data.get('dependencies', [])
                                    self.compileGroups = data.get('compileGroups', [])
                                    self.sourceGroups = data.get('sourceGroups', [])
                                    self.sources = data.get('sources', [])
                                    self.link = data.get('link', {})
                                    self.paths = data.get('paths', {})
                                    self.backtrace = data.get('backtrace', 0)
                                    self.backtraceGraph = data.get('backtraceGraph', [])
                                    
                                    # Add support for custom command outputs
                                    self.byproducts = data.get('byproducts', [])
                                    self.outputs = data.get('outputs', [])
                                    self.command = data.get('command', [])
                                    self.commands = data.get('commands', [])
                            
                            detailed_target = DetailedTarget(target_data)
                            return detailed_target
                    break
            
        except Exception as _:
            # If loading fails, continue with original target
            pass
        
        return target

    def _load_toolchains_info(self) -> Dict[str, Any]:
        """Load toolchains information from CMake File API for language detection."""
        toolchains_info = {}
        
        try:
            # Find the toolchains JSON file
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            toolchains_files = list(reply_dir.glob("toolchains-v1-*.json"))
            
            if not toolchains_files:
                return toolchains_info
            
            # Load toolchains JSON
            with open(toolchains_files[0], 'r', encoding='utf-8') as f:
                toolchains_data = json.load(f)
            
            # Extract language information
            for toolchain in toolchains_data.get('toolchains', []):
                language = toolchain.get('language', '')
                if language:
                    toolchains_info[language] = {
                        'sourceFileExtensions': toolchain.get('sourceFileExtensions', []),
                        'compiler': toolchain.get('compiler', {}),
                        'path': toolchain.get('path', ''),
                        'version': toolchain.get('version', '')
                    }
            
        except Exception as _:
            # If loading fails, return empty dict
            pass
        
        return toolchains_info

    def _detect_programming_language_from_toolchains(self, target: Any, toolchains_info: Dict[str, Any]) -> Optional[str]:
        """Detect programming language using toolchains and compile groups."""
        try:
            # First, try to get language from compile groups
            if hasattr(target, 'compileGroups') and target.compileGroups:
                for compile_group in target.compileGroups:
                    # Handle both dict and object formats
                    if isinstance(compile_group, dict):
                        language = compile_group.get('language')
                    else:
                        language = getattr(compile_group, 'language', None)
                    
                    if language:
                        # Convert to lowercase for consistency
                        return language.lower()
            
            # Fallback: use source file extensions
            if hasattr(target, 'sources') and target.sources:
                for source in target.sources:
                    if hasattr(source, 'path') and source.path:
                        source_path = Path(source.path)
                        extension = source_path.suffix.lower()
                        
                        # Check each language's source file extensions
                        for language, info in toolchains_info.items():
                            if extension in info.get('sourceFileExtensions', []):
                                return language.lower()
            
        except Exception as _:
            pass
        
        return None

    def _extract_from_codemodel_fallback(self) -> None:
        """Fallback: Load codemodel directly from JSON files when cmake-file-api fails."""
        try:
            # Step 1: Read reply/index-*.json → find the "codemodel" object (v2)
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            if not reply_dir.exists():
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "reply_directory_missing",
                    {"path": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Find index file
            index_files = list(reply_dir.glob("index-*.json"))
            if not index_files:
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "index_file_missing",
                    {"reply_dir": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Load index to find codemodel path
            with open(index_files[0], 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Find codemodel v2 in index
            codemodel_path = None
            if 'reply' in index_data:
                for reply_obj in index_data['reply']:
                    if reply_obj.get('kind') == 'codemodel' and reply_obj.get('version', {}).get('major') == 2:
                        codemodel_path = reply_obj.get('jsonFile')
                        break
            
            if not codemodel_path:
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "codemodel_v2_not_in_index",
                    {"index_data": index_data},
                    self._temp_unknown_errors
                )
                return
            
            # Step 2: Open codemodel.json (path in index)
            codemodel_file = reply_dir / codemodel_path
            if not codemodel_file.exists():
                ResearchBackedUtilities.unknown_field(
                    "codemodel_fallback",
                    "codemodel_file_missing",
                    {"path": str(codemodel_file)},
                    self._temp_unknown_errors
                )
                return
            
            # Load the codemodel JSON
            with open(codemodel_file, 'r', encoding='utf-8') as f:
                codemodel_data = json.load(f)
            
            # Create a simple object to hold the data
            class CodemodelFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.configurations = []
                    for config_data in data.get('configurations', []):
                        config = CodemodelConfigFallback(config_data, codemodel_file_path)
                        self.configurations.append(config)
                    self.backtraceGraph = data.get('backtraceGraph')
            
            class CodemodelConfigFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.projects = []
                    for project_data in data.get('projects', []):
                        project = CodemodelProjectFallback(project_data)
                        self.projects.append(project)
                    self.targets = []
                    for target_data in data.get('targets', []):
                        target = CodemodelTargetFallback(target_data, codemodel_file_path)
                        self.targets.append(target)
                    self.directories = data.get('directories', [])
            
            class CodemodelProjectFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.name = data.get('name', '')
                    self.directoryIndexes = data.get('directoryIndexes', [])
                    self.targetIndexes = data.get('targetIndexes', [])
            
            class CodemodelTargetFallback:
                def __init__(self, data: Dict[str, Any], codemodel_file_path: Path):
                    self.name = data.get('name', '')
                    self.id = data.get('id', '')
                    self.jsonFile = data.get('jsonFile', '')
                    self.directoryIndex = data.get('directoryIndex', 0)
                    self.projectIndex = data.get('projectIndex', 0)
                    self._codemodel_file_path = codemodel_file_path
                    
                    # Initialize default values
                    self.type = ''
                    self.nameOnDisk = ''
                    self.artifacts = []
                    self.dependencies = []
                    self.compileGroups = []
                    self.sourceGroups = []
                    self.sources = []
                    self.link = {}
                    self.paths = {}
                    self.backtrace = 0
                    self.backtraceGraph = []
                    
                    # Step 3: Load detailed target information if jsonFile exists
                    if self.jsonFile:
                        self._load_detailed_target_info()
                
                def _load_detailed_target_info(self):
                    """Load detailed target information from target JSON file."""
                    try:
                        # Step 3: For each target → resolve and open target's JSON (relative to codemodel file)
                        target_json_path = self._codemodel_file_path.parent / self.jsonFile
                        if target_json_path.exists():
                            with open(target_json_path, 'r', encoding='utf-8') as f:
                                target_data = json.load(f)
                            
                            # Step 4: Read target details
                            self.type = target_data.get('type', '')
                            self.nameOnDisk = target_data.get('nameOnDisk', '')
                            self.artifacts = target_data.get('artifacts', [])
                            self.dependencies = target_data.get('dependencies', [])
                            self.compileGroups = target_data.get('compileGroups', [])
                            self.sourceGroups = target_data.get('sourceGroups', [])
                            self.sources = target_data.get('sources', [])
                            self.link = target_data.get('link', {})
                            self.paths = target_data.get('paths', {})
                            self.backtrace = target_data.get('backtrace', 0)
                            self.backtraceGraph = target_data.get('backtraceGraph', [])
                    except Exception as _:
                        # If we can't load detailed info, continue with basic info
                        pass
            
            codemodel = CodemodelFallback(codemodel_data, codemodel_file)
            self._extract_from_codemodel(codemodel)
            
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "codemodel_fallback",
                "load_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _extract_from_cache_fallback(self) -> None:
        """Fallback: Load cache directly from JSON files when cmake-file-api fails."""
        try:
            # Find the cache JSON file
            reply_dir = self.cmake_config_dir / ".cmake" / "api" / "v1" / "reply"
            cache_files = list(reply_dir.glob("cache-v2-*.json"))
            if not cache_files:
                ResearchBackedUtilities.unknown_field(
                    "cache_fallback",
                    "cache_v2_file_missing",
                    {"reply_dir": str(reply_dir)},
                    self._temp_unknown_errors
                )
                return
            
            # Load the cache JSON
            with open(cache_files[0], 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Create a simple object to hold the data
            class CacheFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.entries = []
                    for entry_data in data.get('entries', []):
                        entry = CacheEntryFallback(entry_data)
                        self.entries.append(entry)
            
            class CacheEntryFallback:
                def __init__(self, data: Dict[str, Any]):
                    self.name = data.get('name', '')
                    self.value = data.get('value', '')
                    self.type = data.get('type', '')
                    self.properties = data.get('properties', {})
            
            cache = CacheFallback(cache_data)
            self._extract_from_cache(cache)
            
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "cache_fallback",
                "load_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _extract_install_metadata_from_codemodel(self, codemodel: Any) -> None:
        """Extract install metadata from codemodel directory.installers."""
        if not hasattr(codemodel, "configurations"):
            return
        
        install_metadata: List[Dict[str, Any]] = []
        
        for config in codemodel.configurations:
            if hasattr(config, "directories"):
                for directory in config.directories:
                    if hasattr(directory, "installers"):
                        for installer in directory.installers:
                            install_info = {
                                "destination": getattr(installer, "destination", ""),
                                "install_type": getattr(installer, "type", ""),
                                "paths": []
                            }
                            
                            # Extract paths from installer
                            if hasattr(installer, "paths"):
                                for path in installer.paths:
                                    if hasattr(path, "path"):
                                        install_info["paths"].append(str(path.path))
                            
                            install_metadata.append(install_info)
        
        # Store install metadata for potential use
        if install_metadata:
            # Could be used to enhance component location information
            # For now, we'll just track it for potential future use
            pass

    def _extract_from_cache(self, cache: Any) -> None:
        """Extract information from cache v2 using research-backed approach."""
        # Store cache entries for external package detection
        self._temp_cache_entries = getattr(cache, "entries", [])
        
        # Build cache dictionary for variable expansion
        self._temp_cache_dict = {}
        if hasattr(cache, "entries"):
            for entry in cache.entries:
                if hasattr(entry, "name") and hasattr(entry, "value"):
                    self._temp_cache_dict[entry.name] = str(entry.value)
        
        # Extract global external packages from cache
        self._temp_global_external_packages = self._extract_external_packages_from_cache()
        
        # Extract package manager information
        package_manager = ResearchBackedUtilities.detect_package_manager_from_cache(self._temp_cache_entries)
        if not package_manager:
            ResearchBackedUtilities.unknown_field(
                "package_manager", 
                "cache_analysis", 
                {"cache_entries": len(self._temp_cache_entries)},
                self._temp_unknown_errors
            )
        
        # Check for compile commands JSON
        self._check_compile_commands_json()

    def _check_compile_commands_json(self) -> None:
        """Check for compile_commands.json file based on CMake configuration."""
        compile_commands_path = self.cmake_config_dir / "compile_commands.json"
        
        # Check if CMAKE_EXPORT_COMPILE_COMMANDS is enabled
        export_compile_commands = self._temp_cache_dict.get("CMAKE_EXPORT_COMPILE_COMMANDS", "").upper()
        generator = self._temp_cache_dict.get("CMAKE_GENERATOR", "")
        
        if export_compile_commands in ["ON", "TRUE", "1"]:
            # Compile commands export is enabled
            if not compile_commands_path.exists():
                # Check if generator supports compile_commands.json
                if generator in ["Ninja", "Unix Makefiles", "MinGW Makefiles"]:
                    # Generator supports it but file is missing - this is an error
                    ResearchBackedUtilities.unknown_field(
                        "compile_commands_json",
                        "file_missing",
                        {"path": str(compile_commands_path), "generator": generator},
                        self._temp_unknown_errors
                    )
                else:
                    # Generator doesn't support it (e.g., Visual Studio) - this is expected
                    print(f"INFO: compile_commands.json not available with {generator} generator (only supported by Makefile/Ninja generators)")
            else:
                print(f"INFO: compile_commands.json found at {compile_commands_path}")
        else:
            # CMAKE_EXPORT_COMPILE_COMMANDS is not enabled
            if generator in ["Ninja", "Unix Makefiles", "MinGW Makefiles"]:
                print("INFO: CMAKE_EXPORT_COMPILE_COMMANDS is not enabled (set to ON to generate compile_commands.json)")
            else:
                print(f"INFO: CMAKE_EXPORT_COMPILE_COMMANDS not available with {generator} generator")

    def _extract_from_toolchains(self, toolchains: Any) -> None:
        """Extract information from toolchains v1."""
        # Store toolchains for runtime detection
        self._toolchains_obj = toolchains
        
        if hasattr(toolchains, "toolchains"):
            for tc in toolchains.toolchains:
                # Could extract compiler information
                if hasattr(tc, "language") and hasattr(tc, "compiler"):
                    pass

    def _extract_from_cmake_files(self, cmake_files: Any) -> None:
        """Extract information from cmakeFiles v1."""
        # This could be used to detect Java/Go support by looking for UseJava.cmake, etc.
        pass

    def _extract_tests_from_ctest(self) -> None:
        """Extract tests using CTest JSON (research-backed approach)."""
        try:
            # Run ctest --show-only=json-v1 to get comprehensive test information
            result = subprocess.run(
                ["ctest", "--show-only=json-v1"], 
                cwd=self.cmake_config_dir, 
                capture_output=True, 
                text=True, 
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                ctest_info = json.loads(result.stdout)
                self._process_ctest_info_research_backed(ctest_info)
            else:
                ResearchBackedUtilities.unknown_field(
                    "ctest_json",
                    "execution_failed",
                    {"error": result.stderr, "returncode": result.returncode},
                    self._temp_unknown_errors
                )

        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "ctest_json",
                "execution_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _process_ctest_info_research_backed(self, ctest_info: Dict[str, Any]) -> None:
        """Process CTest JSON information using research-backed approach."""
        tests = ctest_info.get("tests", [])
        backtrace_graph = ctest_info.get("backtraceGraph", {})
        
        # Build component mapping tables
        by_artifact_basename = self._build_artifact_basename_map()
        by_source_dir = self._build_source_directory_map()

        for test in tests:
            try:
                test_name = test.get("name", "")
                test_command = test.get("command", [])
                test_properties = test.get("properties", [])
                
                # Extract working directory
                _ = None  # workdir not used
                for prop in test_properties:
                    if prop.get("name") == "WORKING_DIRECTORY":
                        _ = prop.get("value")  # workdir not used
                        break
                
                # Get test provenance from backtrace
                cmake_file, _ = self._get_test_provenance(test, backtrace_graph)  # cmake_line not used
                
                # Map test to components using two-source approach
                component_refs = self._map_test_to_components(
                    test_name, test_command, cmake_file, by_artifact_basename, by_source_dir
                )
                
                # Create evidence from CTest backtrace
                evidence = self._create_snippet_from_ctest(test, backtrace_graph)
                if evidence is None:
                    # No evidence available - skip this test
                    continue
                
                # Create test object with ComponentRef
                test_obj = Test(
                    id=None,
                    name=test_name,
                    test_framework=self._detect_test_framework_from_ctest(test),
                    components_being_tested=component_refs,
                    test_executable=None,  # Will be determined from components
                    test_runner=None,  # Will be determined from components
                    source_files=[],  # Tests don't have source files in the traditional sense
                    evidence=evidence
                )
                
                self._temp_tests.append(test_obj)
                
            except Exception as e:
                ResearchBackedUtilities.unknown_field(
                    "test_processing",
                    f"test_{test.get('name', 'unknown')}",
                    {"error": str(e), "test_data": test},
                    self._temp_unknown_errors
                )

    def _build_artifact_basename_map(self) -> Dict[str, str]:
        """Build map from artifact basename to component ID."""
        by_artifact_basename = {}
        
        for component in self._temp_components:
            # Check output attribute
            if hasattr(component, 'output') and component.output:
                basename = Path(component.output).name
                by_artifact_basename[basename] = component.name
            
            # Check output_path attribute (Component has output_path, not artifacts)
            if hasattr(component, 'output_path') and component.output_path:
                basename = Path(component.output_path).name
                by_artifact_basename[basename] = component.name
        
        return by_artifact_basename

    def _build_source_directory_map(self) -> Dict[str, List[str]]:
        """Build map from source directory to component IDs."""
        by_source_dir = {}
        
        for component in self._temp_components:
            if hasattr(component, 'source_files') and component.source_files:
                # Get the directory of the first source file
                first_source = component.source_files[0]
                source_dir = str(first_source.parent)
                
                if source_dir not in by_source_dir:
                    by_source_dir[source_dir] = []
                by_source_dir[source_dir].append(component.name)
        
        return by_source_dir

    def _get_test_provenance(self, test: Dict[str, Any], backtrace_graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
        """Get test provenance from backtrace graph."""
        backtrace = test.get("backtrace")
        if not backtrace or not backtrace_graph:
            return None, None
        
        # Get the backtrace node
        nodes = backtrace_graph.get("nodes", [])
        files = backtrace_graph.get("files", [])
        
        if backtrace < len(nodes):
            node = nodes[backtrace]
            file_idx = node.get("file")
            line = node.get("line")
            
            if file_idx is not None and file_idx < len(files):
                return files[file_idx], line
        
        return None, None

    def _map_test_to_components(self, test_name: str, test_command: List[str], 
                               cmake_file: Optional[str], by_artifact_basename: Dict[str, str], 
                               by_source_dir: Dict[str, List[str]]) -> List[Component]:
        """Map test to components using evidence-based approaches only."""
        component_refs = []
        
        # Source 1: Executable artifact match (strongest)
        if test_command and len(test_command) > 0:
            command_path = test_command[0]
            if command_path and not command_path.startswith('$'):
                # Extract basename from command
                basename = Path(command_path).name
                if basename in by_artifact_basename:
                    component_name = by_artifact_basename[basename]
                    component = self._find_component_by_name(component_name)
                    if component:
                        component_refs.append(component)
                        return component_refs
        
        # Source 2: Backtrace directory → owning target
        if cmake_file:
            cmake_dir = str(Path(cmake_file).parent)
            if cmake_dir in by_source_dir:
                candidates = by_source_dir[cmake_dir]
                for candidate_name in candidates:
                    component = self._find_component_by_name(candidate_name)
                    if component:
                        component_refs.append(component)
                if component_refs:
                    return component_refs
        
        # No evidence found - report UNKNOWN
        ResearchBackedUtilities.unknown_field(
            "test_component_mapping",
            f"test_{test_name}",
            {
                "has_command": bool(test_command),
                "has_cmake_file": bool(cmake_file),
                "command": test_command,
                "cmake_file": cmake_file
            },
            self._temp_unknown_errors
        )
        
        return component_refs
    

    def _find_component_by_name(self, name: str) -> Optional[Component]:
        """Find component by name."""
        for component in self._temp_components:
            if component.name == name:
                return component
        return None

    def _process_ctest_info(self, ctest_info: Dict[str, Any]) -> None:
        """Process CTest JSON information."""
        tests = ctest_info.get("tests", [])
        backtrace_graph = ctest_info.get("backtraceGraph")

        for test in tests:
            test_obj = self._create_test_from_ctest(test, backtrace_graph)
            if test_obj:
                self._temp_tests.append(test_obj)

    def _create_test_from_ctest(self, test: Dict[str, Any], backtrace_graph: Optional[Dict[str, Any]]) -> Optional[Test]:
        """Create Test from CTest information."""
        try:
            # Get test name
            test_name = test.get("name", "")

            # Get test framework from properties or labels
            test_framework = self._detect_test_framework_from_ctest(test)

            # Get line numbers from backtrace
            evidence = self._create_snippet_from_ctest(test, backtrace_graph)
            if evidence is None:
                # No evidence available - skip this test
                return None

            # Get test source files by mapping to target
            source_files = self._get_test_source_files(test)
            
            # Use deterministic test-to-component mapping
            # Build artifact index from all components (cross-configuration)
            art_by_base = self._build_component_artifact_index()
            tgt_by_name = {comp.name: comp for comp in self._temp_components}
            
            # Resolve components using deterministic approach
            component_names = self._resolve_test_components(test, art_by_base, tgt_by_name)
            
            # Convert component names to actual Component objects
            components_being_tested: List[Component] = []
            for comp_name in component_names:
                for component in self._temp_components:
                    if component.name == comp_name:
                        components_being_tested.append(component)
                        break
            
            # If no components found, report UNKNOWN
            if not components_being_tested:
                ResearchBackedUtilities.unknown_field(
                    "test_component_mapping",
                    f"test_{test_name}",
                    {
                        "has_command": bool(test.get("command")),
                        "has_cmake_file": bool(backtrace_graph),
                        "command": test.get("command", []),
                        "cmake_file": self._get_cmake_file_from_backtrace(backtrace_graph) if backtrace_graph else None
                    },
                    self._temp_unknown_errors
                )

            return Test(
                id=None,
                name=test_name,
                test_executable=None,  # Would need custom logic to determine
                components_being_tested=components_being_tested,
                test_runner=None,  # Would need custom logic to determine
                source_files=source_files,
                test_framework=test_framework,
                evidence=evidence,
            )
        except Exception:
            return None

    def _detect_test_framework_from_ctest(self, test: Dict[str, Any]) -> str:
        """Detect test framework from CTest properties and command (evidence-based)."""
        # Check for framework-specific labels (evidence from CTest properties)
        properties = test.get("properties", [])
        labels: List[Any] = []

        # Properties is a list of dictionaries
        for prop in properties:
            if isinstance(prop, dict) and prop.get("name") == "LABELS":
                labels_value: Any = prop.get("value", [])
                if isinstance(labels_value, list):
                    labels = labels_value
                break

        # Check labels for framework indicators
        detected_framework = None
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                if "gtest" in label_lower or "googletest" in label_lower:
                    return "Google Test"
                elif "catch" in label_lower or "catch2" in label_lower:
                    return "Catch2"
                elif "doctest" in label_lower:
                    return "doctest"
                elif "boost.test" in label_lower:
                    return "Boost.Test"
                else:
                    # Use the actual label as evidence if no known framework detected
                    detected_framework = label

        # Check command for framework indicators (evidence from test command)
        command = test.get("command", [])
        if command:
            cmd_str = " ".join(command)
            
            # Only detect frameworks with clear, unambiguous indicators
            # Google Test indicators (very specific flags)
            if "--gtest_list_tests" in cmd_str or "--gtest_filter" in cmd_str:
                return "Google Test"
            
            # Catch2 indicators (very specific flags)
            elif "--list-tests" in cmd_str and "catch" in cmd_str.lower():
                return "Catch2"
            
            # Python test frameworks (very specific commands)
            elif "pytest" in cmd_str.lower():
                return "pytest"
            elif "python -m unittest" in cmd_str.lower():
                return "Python unittest"
            
            # Go test indicators (very specific command)
            elif cmd_str.lower().startswith("go test"):
                return "Go Test"
            
            # Java test indicators (very specific classpath/class names)
            elif "junit" in cmd_str.lower() and "java" in cmd_str.lower():
                return "JUnit"
            elif "testng" in cmd_str.lower() and "java" in cmd_str.lower():
                return "TestNG"
            
            # If we have a command but no clear framework indicators, use the command as evidence
            else:
                # Extract the executable name as evidence
                if command and len(command) > 0:
                    executable = command[0]
                    if executable:
                        return f"Test executable: {executable}"

        # Use evidence-based fallback: return the actual label if available, otherwise fail fast
        if detected_framework:
            return detected_framework
        
        # If no evidence at all, fail fast rather than guessing
        raise ValueError(f"No test framework evidence found for test. " +
                       f"Labels: {labels}, Command: {command}. " +
                       f"Cannot determine test framework without evidence.")

    def _get_components_being_tested_evidence_based(self, test_name: str) -> List[str]:
        """Get components being tested using evidence from CMakeLists.txt files."""
        if not self._cmake_parser:
            raise ValueError("CMakeParser not available. Cannot perform evidence-based test-component mapping.")
        
        # Get test information from CMakeLists.txt
        test_info = self._cmake_parser.get_test_info(test_name)
        if not test_info:
            raise ValueError(f"No CMakeLists.txt evidence found for test '{test_name}'. " +
                           f"Cannot determine test-component relationships without evidence.")
        
        # Extract component names from test command
        command = test_info.get('command', [])
        components: List[str] = []
        
        for cmd_part in command:
            cmd_str = str(cmd_part)
            # Look for executable names that match component names
            for component in self._temp_components:
                if hasattr(component, 'name') and component.name in cmd_str:
                    components.append(component.name)
        
        # If no components found, fail fast
        if not components:
            raise ValueError(f"No components found for test '{test_name}'. " +
                           f"Test command: {command}. " +
                           f"Cannot determine test-component relationships without evidence.")
        
        return components

    def _load_compile_commands_json(self) -> None:
        """Load compile_commands.json as fallback for per-TU evidence."""
        compile_commands_path = self.cmake_config_dir / "compile_commands.json"
        
        if compile_commands_path.exists():
            try:
                with open(compile_commands_path, 'r', encoding='utf-8') as f:
                    self._temp_compile_commands = json.load(f)
            except Exception as e:
                ResearchBackedUtilities.unknown_field(
                    "compile_commands_json",
                    "file_loading",
                    {"error": str(e), "path": str(compile_commands_path)},
                    self._temp_unknown_errors
                )
        else:
            # Only report missing file if CMAKE_EXPORT_COMPILE_COMMANDS is enabled and generator supports it
            export_compile_commands = self._temp_cache_dict.get("CMAKE_EXPORT_COMPILE_COMMANDS", "").upper()
            generator = self._temp_cache_dict.get("CMAKE_GENERATOR", "")
            
            if export_compile_commands in ["ON", "TRUE", "1"] and generator in ["Ninja", "Unix Makefiles", "MinGW Makefiles"]:
                ResearchBackedUtilities.unknown_field(
                    "compile_commands_json",
                    "file_missing",
                    {"path": str(compile_commands_path), "generator": generator, "export_enabled": True},
                    self._temp_unknown_errors
                )

    def _load_graphviz_dependencies(self) -> None:
        """Load graphviz dependencies for direct vs transitive distinction."""
        try:
            # Try to generate graphviz output
            result = subprocess.run(
                ["cmake", "--graphviz=graph.dot", "."],
                cwd=self.cmake_config_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                graphviz_file = self.cmake_config_dir / "graph.dot"
                if graphviz_file.exists():
                    self._parse_graphviz_dependencies(graphviz_file)
                else:
                    ResearchBackedUtilities.unknown_field(
                        "graphviz_dependencies",
                        "file_missing",
                        {"path": str(graphviz_file)},
                        self._temp_unknown_errors
                    )
            else:
                ResearchBackedUtilities.unknown_field(
                    "graphviz_dependencies",
                    "generation_failed",
                    {"error": result.stderr, "returncode": result.returncode},
                    self._temp_unknown_errors
                )
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "graphviz_dependencies",
                "generation_error",
                {"error": str(e)},
                self._temp_unknown_errors
            )

    def _parse_graphviz_dependencies(self, graphviz_file: Path) -> None:
        """Parse graphviz .dot file to extract direct dependencies."""
        self._temp_graphviz_deps = {}
        
        try:
            with open(graphviz_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing of .dot file for dependencies
            # Look for lines like: "target1" -> "target2"
            import re
            dep_pattern = r'"([^"]+)"\s*->\s*"([^"]+)"'
            
            for match in re.finditer(dep_pattern, content):
                source = match.group(1)
                target = match.group(2)
                
                if source not in self._temp_graphviz_deps:
                    self._temp_graphviz_deps[source] = set()
                self._temp_graphviz_deps[source].add(target)
                
        except Exception as e:
            ResearchBackedUtilities.unknown_field(
                "graphviz_parsing",
                "file_parsing_error",
                {"error": str(e), "path": str(graphviz_file)},
                self._temp_unknown_errors
            )

    def _create_snippet_from_ctest(self, test: Dict[str, Any], backtrace_graph: Optional[Dict[str, Any]]) -> Optional[Evidence]:
        """Create Evidence with line numbers from CTest backtrace."""
        if backtrace_graph and test.get("backtrace") is not None:
            backtrace_idx = test["backtrace"]
            # Resolve backtrace to get file and line
            file_path, line = self._resolve_backtrace(backtrace_idx, backtrace_graph)
            if file_path:
                return Evidence(id=None, call_stack=[f"{file_path}#L{line or 1}-L{line or 1}"])

        # No evidence available - return None to indicate failure
        return None

    def _build_call_stack_from_backtrace(
        self,
        leaf_idx: Optional[int],
        backtrace_graph: dict,
        order: str = "leaf-first",
        repo_root: Optional[Path] = None,
        trim_non_project: bool = False,
    ) -> List[Tuple[str, int, Optional[str]]]:
        """
        Build the full CMake call stack using the File API graph.

        Returns a list of frames as (file_path, line, command) where the first item
        is the leaf frame (target/test definition) when order='leaf-first'.
        """
        if not backtrace_graph or leaf_idx is None:
            return []

        nodes = backtrace_graph.get("nodes") or []
        files = backtrace_graph.get("files") or []
        commands = backtrace_graph.get("commands") or []

        def get_cmd(i: Optional[int]) -> Optional[str]:
            return commands[i] if isinstance(i, int) and 0 <= i < len(commands) else None

        frames: List[Tuple[str, int, Optional[str]]] = []
        seen = set()
        i = leaf_idx

        while isinstance(i, int) and 0 <= i < len(nodes) and i not in seen:
            seen.add(i)
            n = nodes[i] or {}
            fidx = n.get("file")
            line = int(n.get("line") or 1)
            cmd = get_cmd(n.get("command"))
            if isinstance(fidx, int) and 0 <= fidx < len(files):
                path = files[fidx]
                frames.append((path, line, cmd))
                i = n.get("parent")
            else:
                break  # corrupted node
        # frames are leaf-first by construction
        if order == "origin-first":
            frames.reverse()

        if trim_non_project and repo_root:
            # Keep frames that are inside the project (relative paths) or under repo_root
            norm_root = str(repo_root.as_posix()).lower()
            def in_project(p: str) -> bool:
                # File API uses forward slashes; relative => inside top-level source dir
                return not Path(p).is_absolute() or p.lower().startswith(norm_root)
            frames = [fr for fr in frames if in_project(fr[0])]

        return frames

    def _find_target_definition_in_backtrace(self, backtrace_idx: int, backtrace_graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
        """Find the actual target definition (add_executable, add_library, etc.) in project files."""
        frames = self._build_call_stack_from_backtrace(backtrace_idx, backtrace_graph)
        
        # Look for target definition commands in project files (not vcpkg or system files)
        target_commands = {"add_executable", "add_library", "add_custom_target", "add_custom_command"}
        
        for file_path, line, command in frames:
            # Skip vcpkg and system files
            if "vcpkg" in file_path.lower() or "cmake" in file_path.lower() and "scripts" in file_path:
                continue
                
            # Check if this is a target definition command
            if command and any(cmd in command.lower() for cmd in target_commands):
                return file_path, line
        
        # If no target definition found, return the first project file
        for file_path, line, command in frames:
            if "vcpkg" not in file_path.lower() and "cmake" not in file_path.lower():
                return file_path, line
                
        # Fallback to first frame
        if frames:
            return frames[0][0], frames[0][1]
        return None, None

    def _resolve_backtrace(self, backtrace_idx: int, backtrace_graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[int]]:
        """Resolve backtrace index to file path and line number."""
        try:
            nodes = backtrace_graph.get("nodes", [])
            files = backtrace_graph.get("files", [])

            if backtrace_idx < len(nodes):
                node = nodes[backtrace_idx]
                file_idx = node.get("file")
                line = node.get("line")

                if file_idx is not None and file_idx < len(files):
                    file_path = files[file_idx]
                    return file_path, line

        except Exception:
            pass

        return None, None

    def _find_test_dependencies(self, test: Dict[str, Any]) -> List[Component]:
        """Find components that this test depends on."""
        dependent_components: List[Component] = []

        # Map test command to target artifacts to find dependencies
        command = test.get("command", [])
        if command:
            test_exe_path = command[0]
            if test_exe_path:
                # Find target that produces this executable
                for component in self._temp_components:
                    if component.output_path.name == Path(test_exe_path).name:
                        dependent_components.append(component)
                        break

        return dependent_components

    def _get_test_source_files(self, test: Dict[str, Any]) -> List[Path]:
        """Get source files for this test."""
        source_files: List[Path] = []

        # Map test to target to get source files
        command = test.get("command", [])
        if command:
            test_exe_path = command[0]
            if test_exe_path:
                # Find target that produces this executable
                for component in self._temp_components:
                    if component.output_path.name == Path(test_exe_path).name:
                        source_files = component.source_files
                        break

        return source_files

    def _extract_build_commands(self) -> None:
        """Extract build commands."""
        self._temp_configure_command = f"cmake -B {self.cmake_config_dir}"
        self._temp_build_command = f"cmake --build {self.cmake_config_dir}"
        self._temp_install_command = f"cmake --install {self.cmake_config_dir}"
        self._temp_test_command = f"ctest --test-dir {self.cmake_config_dir}"

    def _extract_output_directory(self) -> None:
        """Extract output directory information using evidence-based detection."""
        self._temp_build_directory = self.cmake_config_dir

        # Try to get output directory from CMake cache (evidence-based)
        output_dir_found = False
        for entry in self._temp_cache_entries:
            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                if entry.name == "CMAKE_RUNTIME_OUTPUT_DIRECTORY":
                    runtime_dir = Path(str(entry.value))
                    if runtime_dir.exists():
                        self._temp_output_directory = runtime_dir
                        output_dir_found = True
                        break
                elif entry.name == "CMAKE_BINARY_DIR":
                    binary_dir = Path(str(entry.value))
                    if binary_dir.exists():
                        self._temp_output_directory = binary_dir
                        output_dir_found = True
                        break
                elif entry.name == "CMAKE_LIBRARY_OUTPUT_DIRECTORY":
                    library_dir = Path(str(entry.value))
                    if library_dir.exists():
                        self._temp_output_directory = library_dir
                        output_dir_found = True
                        break

        # If no evidence found in cache, use build directory as fallback
        if not output_dir_found:
            self._temp_output_directory = self.cmake_config_dir

    def _report_unknown_errors(self) -> None:
        """Report UNKNOWN_* errors for transparency in research-backed approach."""
        if self._temp_unknown_errors:
            print(f"\nResearch-backed UNKNOWN_* errors detected ({len(self._temp_unknown_errors)}):")
            for error in sorted(self._temp_unknown_errors):
                print(f"  • {error}")
            print("  These represent fields where evidence was insufficient for deterministic detection.")
            print("  Consider providing additional CMake configuration or build artifacts.\n")

    def _populate_rig(self) -> None:
        """Populate the RIG with extracted data."""
        # Create repository info
        repo_info = RepositoryInfo(
            name=self._temp_project_name,
            root_path=self.repo_root,
            build_directory=self._temp_build_directory,
            output_directory=self._temp_output_directory,
            configure_command=self._temp_configure_command,
            build_command=self._temp_build_command,
            install_command=self._temp_install_command,
            test_command=self._temp_test_command,
        )
        self._rig.set_repository_info(repo_info)
        
        # Report UNKNOWN errors for transparency
        self._report_unknown_errors()

        # Set build system info
        # TODO: Extract generator and version from CMake cache if needed
        build_system_info = BuildSystemInfo(name="CMake", version=None, build_type=None)
        self._rig.set_build_system_info(build_system_info)

        # Add all components, aggregators, runners, and tests
        for component in self._temp_components:
            # Check for duplicates before adding
            if not self._rig.get_component_by_name(component.name):
                self._rig.add_component(component)

        for aggregator in self._temp_aggregators:
            # Check for duplicates before adding
            if not self._rig.get_aggregator_by_name(aggregator.name):
                self._rig.add_aggregator(aggregator)

        for runner in self._temp_runners:
            # Check for duplicates before adding
            if not self._rig.get_runner_by_name(runner.name):
                self._rig.add_runner(runner)

        for utility in self._temp_utilities:
            # Check for duplicates before adding
            if not self._rig.get_utility_by_name(utility.name):
                self._rig.add_utility(utility)

        for test in self._temp_tests:
            # Check for duplicates before adding
            if not self._rig.get_test_by_name(test.name):
                self._rig.add_test(test)
        
        # Run deterministic analysis to resolve unknowns using cross-component relationships
        self._rig.analyze()

    @property
    def rig(self) -> RIG:
        """Get the Repository Intelligence Graph."""
        return self._rig

    def get_rig(self) -> RIG:
        """Get the Repository Intelligence Graph."""
        return self._rig

    def parse_cmake(self) -> None:
        """Manually trigger CMake parsing after initialization."""
        self.parse_cmake_info()
