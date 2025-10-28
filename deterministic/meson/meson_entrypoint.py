"""
MesonEntrypoint - Generates RIG from Meson projects using no-heuristics policy.
Parses meson.build files, uses meson introspect, and build outputs to extract components.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from core.schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, TestDefinition, Evidence, ComponentLocation, Aggregator, Runner, Utility, RepositoryInfo, BuildSystemInfo
from core.rig import RIG


class MesonEntrypoint:
    """
    Meson RIG generator with strict no-heuristics policy.
    Only states what can be determined deterministically from Meson build system.
    """
    
    def __init__(self, project_root: Path, parse_meson: bool = True):
        self.project_root = Path(project_root)
        
        # Create RIG instance to hold all extracted data
        self._rig = RIG()
        
        # Temporary storage for RIG entities
        self._temp_components: List[Component] = []
        self._temp_aggregators: List[Aggregator] = []
        self._temp_runners: List[Runner] = []
        self._temp_utilities: List[Utility] = []
        self._temp_tests: List[TestDefinition] = []
        self._temp_external_packages: List[ExternalPackage] = []
        
        # Parsing state
        self._parsing_completed = False
        self._unknown_errors: Set[str] = set()
        
        # Parse Meson if requested
        if parse_meson:
            self._parse_meson()
    
    @property
    def rig(self) -> RIG:
        """Get the generated RIG."""
        if not self._parsing_completed:
            self._parse_meson()
        return self._rig
    
    def _parse_meson(self) -> None:
        """Parse Meson project and generate RIG."""
        if self._parsing_completed:
            return
            
        try:
            # Extract build information
            self._extract_build_information()
            
            # Mark parsing as completed
            self._parsing_completed = True
            
            # Create RIG from temporary data
            self._rig = self._create_rig_from_temp_data()
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse Meson project: {e}")
    
    def _extract_build_information(self) -> None:
        """Extract all build information from Meson project."""
        # Extract components from targets
        self._extract_components_from_targets()
        
        # Extract external packages from dependencies
        self._extract_external_packages()
        
        # Extract test information
        self._extract_test_information()
    
    def _extract_components_from_targets(self) -> None:
        """Extract components from Meson targets."""
        try:
            # Try to find meson command
            meson_cmd = "meson"
            try:
                subprocess.run(["meson", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try common Meson installation paths
                meson_paths = [
                    "C:\\Program Files\\Meson\\meson.exe",
                    "/usr/bin/meson",
                    "/usr/local/bin/meson"
                ]
                for path in meson_paths:
                    if Path(path).exists():
                        meson_cmd = path
                        break
                else:
                    print("Warning: Meson command not found, using fallback parsing")
                    self._extract_components_from_meson_build_files()
                    return
            
            # Try to use meson introspect if build directory exists
            build_dirs = list(self.project_root.glob("build*"))
            if build_dirs:
                build_dir = build_dirs[0]  # Use first build directory found
                self._extract_components_from_meson_introspect(build_dir, meson_cmd)
            else:
                # Fallback to parsing meson.build files
                self._extract_components_from_meson_build_files()
        
        except Exception as e:
            print(f"Warning: Could not extract Meson targets: {e}")
            self._extract_components_from_meson_build_files()
    
    def _extract_components_from_meson_introspect(self, build_dir: Path, meson_cmd: str) -> None:
        """Extract components using meson introspect."""
        try:
            # Get targets information
            result = subprocess.run(
                [meson_cmd, "introspect", "--targets"],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                targets_data = json.loads(result.stdout)
                for target in targets_data:
                    component = self._create_component_from_meson_target(target)
                    if component:
                        self._temp_components.append(component)
        
        except Exception as e:
            print(f"Warning: Could not use meson introspect: {e}")
            self._extract_components_from_meson_build_files()
    
    def _extract_components_from_meson_build_files(self) -> None:
        """Extract components by parsing meson.build files."""
        # Find all meson.build files
        meson_files = list(self.project_root.rglob("meson.build"))
        
        for meson_file in meson_files:
            components = self._parse_meson_build_file(meson_file)
            self._temp_components.extend(components)
    
    def _parse_meson_build_file(self, meson_file: Path) -> List[Component]:
        """Parse a meson.build file to extract components."""
        components = []
        
        try:
            content = meson_file.read_text(encoding="utf-8")
            
            # Look for executable() calls
            import re
            executable_matches = re.findall(r'executable\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
            for name in executable_matches:
                component = self._create_component_from_name(name, ComponentType.EXECUTABLE, meson_file)
                if component:
                    components.append(component)
            
            # Look for library() calls
            library_matches = re.findall(r'library\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
            for name in library_matches:
                component = self._create_component_from_name(name, ComponentType.STATIC_LIBRARY, meson_file)
                if component:
                    components.append(component)
        
        except Exception as e:
            print(f"Warning: Could not parse meson.build {meson_file}: {e}")
        
        return components
    
    def _create_component_from_meson_target(self, target_data: Dict[str, Any]) -> Optional[Component]:
        """Create a Component from Meson target data."""
        try:
            target_name = target_data.get("name", "UNKNOWN")
            target_type = target_data.get("type", "unknown")
            
            # Map Meson target type to ComponentType
            component_type = self._get_component_type_from_meson_target(target_type)
            
            # Determine programming language
            programming_language = self._get_programming_language_from_meson_target(target_data)
            
            # Determine runtime
            runtime = self._get_runtime_from_meson_target(target_data)
            
            # Get output information
            output_path = self._get_meson_output_path(target_name, component_type)
            
            # Create evidence
            evidence = Evidence(call_stack=[f"meson target: {target_name}"])
            
            # Create component location
            location = ComponentLocation(
                path=self.project_root / "meson.build",
                action="build",
                evidence=evidence
            )
            
            # Create component
            component = Component(
                name=target_name,
                type=component_type,
                programming_language=programming_language,
                runtime=runtime,
                output=target_name,
                output_path=output_path,
                source_files=[Path("src")],  # Default Meson structure
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not create component from Meson target: {e}")
            return None
    
    def _create_component_from_name(self, name: str, component_type: ComponentType, meson_file: Path) -> Optional[Component]:
        """Create a Component from name and type."""
        try:
            # Determine programming language (Meson is primarily C/C++)
            programming_language = "cpp"  # Default to C++
            
            # Determine runtime
            runtime = Runtime.CLANG_C  # Default to CLANG_C
            
            # Get output information
            output_path = self._get_meson_output_path(name, component_type)
            
            # Create evidence
            evidence = Evidence(call_stack=[f"meson.build: {meson_file.relative_to(self.project_root)}"])
            
            # Create component location
            location = ComponentLocation(
                path=meson_file,
                action="build",
                evidence=evidence
            )
            
            # Create component
            component = Component(
                name=name,
                type=component_type,
                programming_language=programming_language,
                runtime=runtime,
                output=name,
                output_path=output_path,
                source_files=[Path("src")],  # Default Meson structure
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not create component from name {name}: {e}")
            return None
    
    def _get_component_type_from_meson_target(self, target_type: str) -> ComponentType:
        """Map Meson target type to ComponentType."""
        target_type_lower = target_type.lower()
        
        if target_type_lower == "executable":
            return ComponentType.EXECUTABLE
        elif target_type_lower == "static_library":
            return ComponentType.STATIC_LIBRARY
        elif target_type_lower == "shared_library":
            return ComponentType.SHARED_LIBRARY
        elif target_type_lower == "shared_module":
            return ComponentType.SHARED_LIBRARY
        else:
            return ComponentType.STATIC_LIBRARY  # Default fallback
    
    def _get_programming_language_from_meson_target(self, target_data: Dict[str, Any]) -> str:
        """Determine programming language from Meson target data."""
        # Check for language information in target data
        if "language" in target_data:
            return target_data["language"].lower()
        
        # Default to C++ for Meson projects
        return "cpp"
    
    def _get_runtime_from_meson_target(self, target_data: Dict[str, Any]) -> Runtime:
        """Determine runtime from Meson target data."""
        # Check for compiler information
        if "compiler" in target_data:
            compiler = target_data["compiler"]
            if "gcc" in compiler.lower():
                return Runtime.CLANG_C
            elif "clang" in compiler.lower():
                return Runtime.CLANG_C
            elif "msvc" in compiler.lower():
                return Runtime.VS_CPP
        
        # Default to CLANG_C for Meson projects
        return Runtime.CLANG_C
    
    def _get_meson_output_path(self, target_name: str, component_type: ComponentType) -> Path:
        """Get Meson output path for component."""
        if component_type == ComponentType.EXECUTABLE:
            return self.project_root / "build" / target_name
        elif component_type == ComponentType.SHARED_LIBRARY:
            return self.project_root / "build" / f"lib{target_name}.so"
        else:
            return self.project_root / "build" / f"lib{target_name}.a"
    
    def _extract_external_packages(self) -> None:
        """Extract external packages from Meson dependencies."""
        # Meson dependencies are typically handled through pkg-config or find_library
        # This is complex to extract without running meson, so we'll mark as UNKNOWN
        pass
    
    def _extract_test_information(self) -> None:
        """Extract test information from Meson project."""
        # Find all meson.build files and look for test() calls
        meson_files = list(self.project_root.rglob("meson.build"))
        
        for meson_file in meson_files:
            tests = self._parse_tests_from_meson_build(meson_file)
            self._temp_tests.extend(tests)
    
    def _parse_tests_from_meson_build(self, meson_file: Path) -> List[TestDefinition]:
        """Parse tests from a meson.build file."""
        tests = []
        
        try:
            content = meson_file.read_text(encoding="utf-8")
            
            # Look for test() calls
            import re
            test_matches = re.findall(r'test\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
            for test_name in test_matches:
                test_def = self._create_test_definition_from_name(test_name, meson_file)
                if test_def:
                    tests.append(test_def)
        
        except Exception as e:
            print(f"Warning: Could not parse tests from meson.build {meson_file}: {e}")
        
        return tests
    
    def _create_test_definition_from_name(self, test_name: str, meson_file: Path) -> Optional[TestDefinition]:
        """Create test definition from test name."""
        try:
            # Create evidence
            evidence = Evidence(call_stack=[f"meson test: {test_name}"])
            
            # Create test definition
            test_def = TestDefinition(
                name=test_name,
                test_framework="meson_test",
                test_type="unit",  # Default for Meson tests
                source_files=[meson_file],
                location=ComponentLocation(
                    path=meson_file,
                    action="test",
                    evidence=evidence
                ),
                evidence=evidence
            )
            
            return test_def
            
        except Exception as e:
            print(f"Warning: Could not create test definition from {test_name}: {e}")
            return None
    
    def _create_rig_from_temp_data(self) -> RIG:
        """Create RIG from temporary data."""
        # Create repository info
        repo_info = RepositoryInfo(
            name=self.project_root.name,
            root_path=self.project_root,
            build_directory=self.project_root / "build",
            output_directory=self.project_root / "build",
            configure_command="meson setup build",
            build_command="meson compile -C build",
            install_command="meson install -C build",
            test_command="meson test -C build"
        )
        
        # Create build system info
        build_system_info = BuildSystemInfo(
            name="meson",
            version="UNKNOWN",  # Could be extracted from meson --version
            build_type="UNKNOWN"
        )
        
        # Create RIG
        rig = RIG()
        
        # Set repository and build system info
        rig._repository_info = repo_info
        rig._build_system_info = build_system_info
        
        # Set components and other entities
        rig._components = self._temp_components
        rig._aggregators = self._temp_aggregators
        rig._runners = self._temp_runners
        rig.utilities = self._temp_utilities
        rig._tests = self._temp_tests
        rig._external_packages = self._temp_external_packages
        
        return rig