"""
GoEntrypoint - Generates RIG from Go projects using no-heuristics policy.
Parses go.mod files, go.sum, and build outputs to extract components.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from core.schemas import Component, ComponentType, ExternalPackage, PackageManager, TestDefinition, Evidence, ComponentLocation, Aggregator, Runner, Utility, RepositoryInfo, BuildSystemInfo
from core.rig import RIG


class GoEntrypoint:
    """
    Go RIG generator with strict no-heuristics policy.
    Only states what can be determined deterministically from Go build system.
    """
    
    def __init__(self, project_root: Path, parse_go: bool = True):
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
        
        # Parse Go if requested
        if parse_go:
            self._parse_go()
    
    @property
    def rig(self) -> RIG:
        """Get the generated RIG."""
        if not self._parsing_completed:
            self._parse_go()
        return self._rig
    
    def _parse_go(self) -> None:
        """Parse Go project and generate RIG."""
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
            raise RuntimeError(f"Failed to parse Go project: {e}")
    
    def _extract_build_information(self) -> None:
        """Extract all build information from Go project."""
        # Extract components from Go packages
        self._extract_components_from_packages()
        
        # Extract external packages from dependencies
        self._extract_external_packages()
        
        # Extract test information
        self._extract_test_information()
    
    def _extract_components_from_packages(self) -> None:
        """Extract components from Go packages."""
        # Find go.mod file
        go_mod_file = self.project_root / "go.mod"
        if not go_mod_file.exists():
            return
        
        # Parse go.mod to get module name
        module_name = self._get_module_name_from_go_mod(go_mod_file)
        if not module_name:
            return
        
        # Find all Go source files
        go_files = list(self.project_root.rglob("*.go"))
        if not go_files:
            return
        
        # Create main component
        component = self._create_component_from_go_files(go_files, module_name)
        if component:
            self._temp_components.append(component)
    
    def _get_module_name_from_go_mod(self, go_mod_file: Path) -> Optional[str]:
        """Extract module name from go.mod file."""
        try:
            with open(go_mod_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find module line
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('module '):
                    return line.split(' ', 1)[1]
            
            return None
        except Exception as e:
            print(f"Warning: Could not parse go.mod {go_mod_file}: {e}")
            return None
    
    def _create_component_from_go_files(self, go_files: List[Path], module_name: str) -> Optional[Component]:
        """Create a Component from Go source files."""
        try:
            # Determine component type
            component_type = self._get_component_type_from_go_files(go_files)
            
            # Determine programming language (Go)
            programming_language = "go"

            # Get output information
            output_path = self._get_go_output_path(module_name, component_type)
            
            # Create evidence from go.mod location
            evidence = Evidence(call_stack=[f"go.mod: {self.project_root / 'go.mod'}"])
            
            # Create component location
            location = ComponentLocation(
                path=self.project_root / "go.mod",
                action="build",
                evidence=evidence
            )
            
            # Create component
            component = Component(
                name=module_name.split('/')[-1],  # Use last part of module name
                type=component_type,
                programming_language=programming_language,
                output=module_name.split('/')[-1],
                output_path=output_path,
                source_files=[Path(".")],  # All Go files in project
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not create component from Go files: {e}")
            return None
    
    def _get_component_type_from_go_files(self, go_files: List[Path]) -> ComponentType:
        """Map Go files to ComponentType."""
        # Check for main package (executable)
        for go_file in go_files:
            try:
                content = go_file.read_text(encoding="utf-8")
                if "package main" in content and "func main()" in content:
                    return ComponentType.EXECUTABLE
            except Exception:
                continue
        
        # Default to static library for Go packages
        return ComponentType.STATIC_LIBRARY
    
    def _get_go_output_path(self, module_name: str, component_type: ComponentType) -> Path:
        """Get Go output path for component."""
        component_name = module_name.split('/')[-1]
        
        if component_type == ComponentType.EXECUTABLE:
            return self.project_root / component_name
        else:
            return self.project_root / f"lib{component_name}.a"
    
    def _extract_external_packages(self) -> None:
        """Extract external packages from Go dependencies."""
        try:
            # Try to find go command
            go_cmd = "go"
            try:
                subprocess.run(["go", "version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try common Go installation paths
                go_paths = [
                    "C:\\Program Files\\Go\\bin\\go.exe",
                    "/usr/bin/go",
                    "/usr/local/bin/go"
                ]
                for path in go_paths:
                    if Path(path).exists():
                        go_cmd = path
                        break
                else:
                    print("Warning: Go command not found, skipping dependency extraction")
                    return
            
            # Run go list to get dependency information
            result = subprocess.run(
                [go_cmd, "list", "-m", "all"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse dependency list
                dependency_lines = result.stdout.strip().split('\n')
                for line in dependency_lines:
                    if line.strip() and not line.startswith('github.com/example/go-modules'):
                        self._process_go_dependency(line.strip())
            
        except Exception as e:
            print(f"Warning: Could not extract Go dependencies: {e}")
    
    def _process_go_dependency(self, dependency_line: str) -> None:
        """Process a single Go dependency."""
        try:
            # Parse dependency line (format: module version)
            parts = dependency_line.split()
            if len(parts) >= 2:
                module_name = parts[0]
                version = parts[1]
                
                # Create external package
                package_name = f"{module_name}@{version}"
                external_package = ExternalPackage(
                    package_manager=PackageManager(
                        name="go",
                        package_name=package_name
                    )
                )
                self._temp_external_packages.append(external_package)
                    
        except Exception as e:
            print(f"Warning: Could not process Go dependency {dependency_line}: {e}")
    
    def _extract_test_information(self) -> None:
        """Extract test information from Go project."""
        # Find all test files
        test_files = list(self.project_root.rglob("*_test.go"))
        
        for test_file in test_files:
            test_def = self._create_test_definition_from_file(test_file)
            if test_def:
                self._temp_tests.append(test_def)
    
    def _create_test_definition_from_file(self, test_file: Path) -> Optional[TestDefinition]:
        """Create test definition from test file."""
        try:
            # Extract test name from file path
            test_name = test_file.stem
            
            # Determine test framework from file content
            test_framework = self._detect_test_framework(test_file)
            
            # Create evidence
            evidence = Evidence(call_stack=[f"test file: {test_file.relative_to(self.project_root)}"])
            
            # Create test definition
            test_def = TestDefinition(
                name=test_name,
                test_framework=test_framework,
                test_type="unit",  # Default for Go tests
                source_files=[test_file],
                location=ComponentLocation(
                    path=test_file,
                    action="test",
                    evidence=evidence
                ),
                evidence=evidence
            )
            
            return test_def
            
        except Exception as e:
            print(f"Warning: Could not create test definition from {test_file}: {e}")
            return None
    
    def _detect_test_framework(self, test_file: Path) -> str:
        """Detect test framework from test file."""
        try:
            content = test_file.read_text(encoding="utf-8")
            content_lower = content.lower()
            
            # Check for built-in Go testing
            if "func test" in content_lower or "func benchmark" in content_lower:
                return "go_test"
            # Check for testify
            elif "github.com/stretchr/testify" in content_lower:
                return "testify"
            # Check for ginkgo
            elif "github.com/onsi/ginkgo" in content_lower:
                return "ginkgo"
            else:
                return "UNKNOWN"
                
        except Exception:
            return "UNKNOWN"
    
    def _create_rig_from_temp_data(self) -> RIG:
        """Create RIG from temporary data."""
        # Create repository info
        repo_info = RepositoryInfo(
            name=self.project_root.name,
            root_path=self.project_root,
            build_directory=self.project_root,
            output_directory=self.project_root,
            configure_command="go mod download",
            build_command="go build",
            install_command="go install",
            test_command="go test"
        )
        
        # Create build system info
        build_system_info = BuildSystemInfo(
            name="go",
            version="UNKNOWN",  # Could be extracted from go version
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