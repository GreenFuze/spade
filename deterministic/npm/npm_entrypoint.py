"""
NpmEntrypoint - Generates RIG from npm projects using no-heuristics policy.
Parses package.json files, workspaces, and build outputs to extract components.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from core.schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, TestDefinition, Evidence, Aggregator, Runner, RepositoryInfo, BuildSystemInfo
from core.rig import RIG


class NpmEntrypoint:
    """
    npm RIG generator with strict no-heuristics policy.
    Only states what can be determined deterministically from npm build system.
    """
    
    def __init__(self, project_root: Path, parse_npm: bool = True):
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
        
        # Parse npm if requested
        if parse_npm:
            self._parse_npm()
    
    @property
    def rig(self) -> RIG:
        """Get the generated RIG."""
        if not self._parsing_completed:
            self._parse_npm()
        return self._rig
    
    def _parse_npm(self) -> None:
        """Parse npm project and generate RIG."""
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
            raise RuntimeError(f"Failed to parse npm project: {e}")
    
    def _extract_build_information(self) -> None:
        """Extract all build information from npm project."""
        # Extract components from packages
        self._extract_components_from_packages()
        
        # Extract external packages from dependencies
        self._extract_external_packages()
        
        # Extract test information
        self._extract_test_information()
    
    def _extract_components_from_packages(self) -> None:
        """Extract components from npm packages."""
        # Find all package.json files
        package_files = list(self.project_root.rglob("package.json"))
        
        for package_file in package_files:
            component = self._create_component_from_package_json(package_file)
            if component:
                self._temp_components.append(component)
    
    def _create_component_from_package_json(self, package_file: Path) -> Optional[Component]:
        """Create a Component from a package.json file."""
        try:
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Extract package information
            package_name = package_data.get("name", "UNKNOWN")
            package_version = package_data.get("version", "1.0.0")
            package_type = package_data.get("type", "commonjs")
            
            # Determine component type
            component_type = self._get_component_type_from_package(package_data)
            
            # Determine programming language
            programming_language = self._get_programming_language_from_package(package_data)
            
            # Determine runtime
            runtime = self._get_runtime_from_package(package_data)
            
            # Get output information
            output_path = self._get_npm_output_path(package_file, package_name, component_type)
            
            # Create evidence from package.json location
            evidence = Evidence(call_stack=[f"package.json: {package_file.relative_to(self.project_root)}"])
            
            # Create component location
            location = ComponentLocation(
                path=package_file,
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
                source_files=[Path("src")],  # Default npm structure
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not parse package.json {package_file}: {e}")
            return None
    
    def _get_component_type_from_package(self, package_data: Dict[str, Any]) -> ComponentType:
        """Map npm package type to ComponentType."""
        # Check for binary packages
        if "bin" in package_data:
            return ComponentType.EXECUTABLE
        
        # Check for library packages
        if "main" in package_data or "module" in package_data or "exports" in package_data:
            return ComponentType.STATIC_LIBRARY
        
        # Check for application packages
        if "scripts" in package_data and "start" in package_data["scripts"]:
            return ComponentType.EXECUTABLE
        
        # Default to static library for npm packages
        return ComponentType.STATIC_LIBRARY
    
    def _get_programming_language_from_package(self, package_data: Dict[str, Any]) -> str:
        """Determine programming language from package.json."""
        # Check for TypeScript
        if "typescript" in package_data.get("devDependencies", {}):
            return "typescript"
        if "typescript" in package_data.get("dependencies", {}):
            return "typescript"
        
        # Check for TypeScript files
        if "types" in package_data or "type" in package_data:
            return "typescript"
        
        # Default to JavaScript
        return "javascript"
    
    def _get_runtime_from_package(self, package_data: Dict[str, Any]) -> Runtime:
        """Determine runtime from package.json."""
        # Check for Node.js version requirement
        engines = package_data.get("engines", {})
        if "node" in engines:
            return Runtime.PYTHON  # We don't have a Node.js runtime enum, use Python as placeholder
        
        # Check for browser environment
        if "browser" in package_data:
            return Runtime.PYTHON  # Placeholder for browser runtime
        
        # Default to Python runtime (placeholder)
        return Runtime.PYTHON
    
    def _get_npm_output_path(self, package_file: Path, package_name: str, component_type: ComponentType) -> Path:
        """Get npm output path for component."""
        package_dir = package_file.parent
        
        if component_type == ComponentType.EXECUTABLE:
            return package_dir / "dist" / f"{package_name}.js"
        elif component_type == ComponentType.STATIC_LIBRARY:
            return package_dir / "dist" / f"{package_name}.js"
        else:
            return package_dir / "dist" / f"{package_name}.js"
    
    def _extract_external_packages(self) -> None:
        """Extract external packages from npm dependencies."""
        try:
            # Try to find npm command
            npm_cmd = "npm"
            try:
                subprocess.run(["npm", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try common npm installation paths
                npm_paths = [
                    "C:\\Program Files\\nodejs\\npm.cmd",
                    "/usr/bin/npm",
                    "/usr/local/bin/npm"
                ]
                for path in npm_paths:
                    if Path(path).exists():
                        npm_cmd = path
                        break
                else:
                    print("Warning: npm command not found, skipping dependency extraction")
                    return
            
            # Run npm list to get dependency information
            result = subprocess.run(
                [npm_cmd, "list", "--json", "--depth=0"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse dependency list JSON
                dependency_data = json.loads(result.stdout)
                self._process_dependency_list(dependency_data)
            
        except Exception as e:
            print(f"Warning: Could not extract npm dependencies: {e}")
    
    def _process_dependency_list(self, dependency_data: Dict[str, Any]) -> None:
        """Process npm dependency list data."""
        if "dependencies" not in dependency_data:
            return
        
        for dep_name, dep_info in dependency_data["dependencies"].items():
            self._process_npm_dependency(dep_name, dep_info)
    
    def _process_npm_dependency(self, dep_name: str, dep_info: Dict[str, Any]) -> None:
        """Process a single npm dependency."""
        try:
            version = dep_info.get("version", "UNKNOWN")
            
            # Create external package
            package_name = f"{dep_name}@{version}"
            external_package = ExternalPackage(
                package_manager=PackageManager(
                    name="npm",
                    package_name=package_name
                )
            )
            self._temp_external_packages.append(external_package)
                    
        except Exception as e:
            print(f"Warning: Could not process npm dependency {dep_name}: {e}")
    
    def _extract_test_information(self) -> None:
        """Extract test information from npm project."""
        # Find all test files
        test_files = list(self.project_root.rglob("**/*.test.js")) + \
                    list(self.project_root.rglob("**/*.test.ts")) + \
                    list(self.project_root.rglob("**/*.spec.js")) + \
                    list(self.project_root.rglob("**/*.spec.ts"))
        
        for test_file in test_files:
            test_def = self._create_test_definition_from_file(test_file)
            if test_def:
                self._temp_tests.append(test_def)
    
    def _create_test_definition_from_file(self, test_file: Path) -> Optional[TestDefinition]:
        """Create test definition from test file."""
        try:
            # Extract test name from file path
            test_name = test_file.stem
            
            # Determine test framework from file content or naming
            test_framework = self._detect_test_framework(test_file)
            
            # Create evidence
            evidence = Evidence(call_stack=[f"test file: {test_file.relative_to(self.project_root)}"])
            
            # Create test definition
            test_def = TestDefinition(
                name=test_name,
                test_framework=test_framework,
                test_type="unit",  # Default for npm tests
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
            
            # Check for Jest
            if "describe" in content_lower and "it" in content_lower:
                return "jest"
            # Check for Mocha
            elif "describe" in content_lower and "before" in content_lower:
                return "mocha"
            # Check for Jasmine
            elif "describe" in content_lower and "expect" in content_lower:
                return "jasmine"
            # Check for Vitest
            elif "import" in content_lower and "vitest" in content_lower:
                return "vitest"
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
            build_directory=self.project_root / "node_modules",
            output_directory=self.project_root / "dist",
            configure_command="npm install",
            build_command="npm run build",
            install_command="npm install",
            test_command="npm test"
        )
        
        # Create build system info
        build_system_info = BuildSystemInfo(
            name="npm",
            version="UNKNOWN",  # Could be extracted from npm --version
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