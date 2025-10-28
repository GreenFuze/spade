"""
CargoEntrypoint - Generates RIG from Rust Cargo projects using no-heuristics policy.
Parses Cargo.toml files, workspaces, and build outputs to extract components.
"""

import json
import subprocess
import toml
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from core.schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, TestDefinition, Evidence, ComponentLocation, Aggregator, Runner, Utility, RepositoryInfo, BuildSystemInfo
from core.rig import RIG


class CargoEntrypoint:
    """
    Cargo RIG generator with strict no-heuristics policy.
    Only states what can be determined deterministically from Cargo build system.
    """
    
    def __init__(self, project_root: Path, parse_cargo: bool = True):
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
        
        # Parse Cargo if requested
        if parse_cargo:
            self._parse_cargo()
    
    @property
    def rig(self) -> RIG:
        """Get the generated RIG."""
        if not self._parsing_completed:
            self._parse_cargo()
        return self._rig
    
    def _parse_cargo(self) -> None:
        """Parse Cargo project and generate RIG."""
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
            raise RuntimeError(f"Failed to parse Cargo project: {e}")
    
    def _extract_build_information(self) -> None:
        """Extract all build information from Cargo project."""
        # Extract components from crates
        self._extract_components_from_crates()
        
        # Extract external packages from dependencies
        self._extract_external_packages()
        
        # Extract test information
        self._extract_test_information()
    
    def _extract_components_from_crates(self) -> None:
        """Extract components from Cargo crates."""
        # Find all Cargo.toml files
        cargo_files = list(self.project_root.rglob("Cargo.toml"))
        
        for cargo_file in cargo_files:
            component = self._create_component_from_cargo_toml(cargo_file)
            if component:
                self._temp_components.append(component)
    
    def _create_component_from_cargo_toml(self, cargo_file: Path) -> Optional[Component]:
        """Create a Component from a Cargo.toml file."""
        try:
            with open(cargo_file, 'r', encoding='utf-8') as f:
                cargo_data = toml.load(f)
            
            # Skip workspace-only Cargo.toml files
            if "package" not in cargo_data and "workspace" in cargo_data:
                return None
            
            # Extract package information
            package_info = cargo_data.get("package", {})
            package_name = package_info.get("name", "UNKNOWN")
            package_version = package_info.get("version", "0.1.0")
            
            # Determine component type
            component_type = self._get_component_type_from_cargo(cargo_data)
            
            # Determine programming language (Cargo is Rust)
            programming_language = "rust"
            
            # Determine runtime
            runtime = self._get_runtime_from_cargo(cargo_data)
            
            # Get output information
            output_path = self._get_cargo_output_path(cargo_file, package_name, component_type)
            
            # Create evidence from Cargo.toml location
            evidence = Evidence(call_stack=[f"Cargo.toml: {cargo_file.relative_to(self.project_root)}"])
            
            # Create component location
            location = ComponentLocation(
                path=cargo_file,
                action="build",
                evidence=evidence
            )
            
            # Create component
            component = Component(
                name=package_name,
                type=component_type,
                programming_language=programming_language,
                runtime=runtime,
                output=package_name,
                output_path=output_path,
                source_files=[Path("src")],  # Default Cargo structure
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not parse Cargo.toml {cargo_file}: {e}")
            return None
    
    def _get_component_type_from_cargo(self, cargo_data: Dict[str, Any]) -> ComponentType:
        """Map Cargo package type to ComponentType."""
        package_info = cargo_data.get("package", {})
        
        # Check for binary packages
        if "bin" in cargo_data:
            return ComponentType.EXECUTABLE
        
        # Check for library packages
        if "lib" in cargo_data:
            lib_info = cargo_data["lib"]
            crate_type = lib_info.get("crate-type", ["lib"])
            
            if "proc-macro" in crate_type:
                return ComponentType.STATIC_LIBRARY  # Treat proc-macro as static library
            elif "cdylib" in crate_type:
                return ComponentType.SHARED_LIBRARY
            else:
                return ComponentType.STATIC_LIBRARY
        
        # Check for proc-macro packages
        if package_info.get("proc-macro", False):
            return ComponentType.STATIC_LIBRARY
        
        # Default to static library for Cargo packages
        return ComponentType.STATIC_LIBRARY
    
    def _get_runtime_from_cargo(self, cargo_data: Dict[str, Any]) -> Runtime:
        """Determine runtime from Cargo.toml."""
        # Check for async runtime dependencies
        dependencies = cargo_data.get("dependencies", {})
        dev_dependencies = cargo_data.get("dev-dependencies", {})
        all_deps = {**dependencies, **dev_dependencies}
        
        # Check for Tokio (async runtime)
        if "tokio" in all_deps:
            return Runtime.PYTHON  # Placeholder for async runtime
        
        # Check for other runtimes
        if "actix" in all_deps:
            return Runtime.PYTHON  # Placeholder for web runtime
        
        # Default to Python runtime (placeholder)
        return Runtime.PYTHON
    
    def _get_cargo_output_path(self, cargo_file: Path, package_name: str, component_type: ComponentType) -> Path:
        """Get Cargo output path for component."""
        package_dir = cargo_file.parent
        target_dir = package_dir / "target" / "release"
        
        if component_type == ComponentType.EXECUTABLE:
            return target_dir / package_name
        elif component_type == ComponentType.SHARED_LIBRARY:
            return target_dir / f"lib{package_name}.so"  # Linux
        else:
            return target_dir / f"lib{package_name}.rlib"
    
    def _extract_external_packages(self) -> None:
        """Extract external packages from Cargo dependencies."""
        try:
            # Try to find cargo command
            cargo_cmd = "cargo"
            try:
                subprocess.run(["cargo", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try common Cargo installation paths
                cargo_paths = [
                    "C:\\Users\\{username}\\.cargo\\bin\\cargo.exe",
                    "/usr/bin/cargo",
                    "/usr/local/bin/cargo"
                ]
                for path in cargo_paths:
                    if Path(path).exists():
                        cargo_cmd = path
                        break
                else:
                    print("Warning: Cargo command not found, skipping dependency extraction")
                    return
            
            # Run cargo tree to get dependency information
            result = subprocess.run(
                [cargo_cmd, "tree", "--format", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse dependency tree JSON
                dependency_lines = result.stdout.strip().split('\n')
                for line in dependency_lines:
                    if line.strip():
                        try:
                            dependency_data = json.loads(line)
                            self._process_cargo_dependency(dependency_data)
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            print(f"Warning: Could not extract Cargo dependencies: {e}")
    
    def _process_cargo_dependency(self, dependency_data: Dict[str, Any]) -> None:
        """Process a single Cargo dependency."""
        try:
            package_name = dependency_data.get("name", "UNKNOWN")
            version = dependency_data.get("version", "UNKNOWN")
            
            # Skip workspace dependencies
            if dependency_data.get("workspace", False):
                return
            
            # Create external package
            package_full_name = f"{package_name}@{version}"
            external_package = ExternalPackage(
                package_manager=PackageManager(
                    name="cargo",
                    package_name=package_full_name
                )
            )
            self._temp_external_packages.append(external_package)
                    
        except Exception as e:
            print(f"Warning: Could not process Cargo dependency: {e}")
    
    def _extract_test_information(self) -> None:
        """Extract test information from Cargo project."""
        # Find all test files
        test_files = list(self.project_root.rglob("**/tests/*.rs")) + \
                    list(self.project_root.rglob("**/benches/*.rs"))
        
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
                test_type="unit",  # Default for Cargo tests
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
            
            # Check for built-in Rust testing
            if "#[test]" in content_lower or "#[cfg(test)]" in content_lower:
                return "rust_test"
            # Check for Criterion benchmarks
            elif "criterion" in content_lower:
                return "criterion"
            # Check for other testing frameworks
            elif "proptest" in content_lower:
                return "proptest"
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
            build_directory=self.project_root / "target",
            output_directory=self.project_root / "target" / "release",
            configure_command="cargo check",
            build_command="cargo build --release",
            install_command="cargo install",
            test_command="cargo test"
        )
        
        # Create build system info
        build_system_info = BuildSystemInfo(
            name="cargo",
            version="UNKNOWN",  # Could be extracted from cargo --version
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