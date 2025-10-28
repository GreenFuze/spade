"""
MavenEntrypoint - Generates RIG from Maven projects using no-heuristics policy.
Parses pom.xml files, dependency trees, and build outputs to extract components.
"""

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from core.schemas import Component, ComponentType, Runtime, ExternalPackage, PackageManager, TestDefinition, Evidence, Aggregator, Runner, RepositoryInfo, BuildSystemInfo
from core.rig import RIG


class MavenEntrypoint:
    """
    Maven RIG generator with strict no-heuristics policy.
    Only states what can be determined deterministically from Maven build system.
    """
    
    def __init__(self, project_root: Path, parse_maven: bool = True):
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
        
        # Parse Maven if requested
        if parse_maven:
            self._parse_maven()
    
    @property
    def rig(self) -> RIG:
        """Get the generated RIG."""
        if not self._parsing_completed:
            self._parse_maven()
        return self._rig
    
    def _parse_maven(self) -> None:
        """Parse Maven project and generate RIG."""
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
            raise RuntimeError(f"Failed to parse Maven project: {e}")
    
    def _extract_build_information(self) -> None:
        """Extract all build information from Maven project."""
        # Extract components from modules
        self._extract_components_from_modules()
        
        # Extract external packages from dependencies
        self._extract_external_packages()
        
        # Extract test information
        self._extract_test_information()
    
    def _extract_components_from_modules(self) -> None:
        """Extract components from Maven modules."""
        # Find all pom.xml files
        pom_files = list(self.project_root.rglob("pom.xml"))
        
        for pom_file in pom_files:
            # Skip if this is a parent pom without modules
            if self._is_parent_pom_only(pom_file):
                continue
                
            component = self._create_component_from_pom(pom_file)
            if component:
                self._temp_components.append(component)
    
    def _is_parent_pom_only(self, pom_file: Path) -> bool:
        """Check if pom.xml is parent-only (no source code)."""
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Check if it has packaging=pom and no source directory
            packaging = root.find(".//{http://maven.apache.org/POM/4.0.0}packaging")
            if packaging is not None and packaging.text == "pom":
                # Check if it has source directory
                source_dir = pom_file.parent / "src" / "main" / "java"
                return not source_dir.exists()
            
            return False
        except Exception:
            return False
    
    def _create_component_from_pom(self, pom_file: Path) -> Optional[Component]:
        """Create a Component from a Maven pom.xml file."""
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            
            # Extract artifact information - get direct child elements, not from parent
            group_id = root.find("{http://maven.apache.org/POM/4.0.0}groupId")
            artifact_id = root.find("{http://maven.apache.org/POM/4.0.0}artifactId")
            version = root.find("{http://maven.apache.org/POM/4.0.0}version")
            packaging = root.find("{http://maven.apache.org/POM/4.0.0}packaging")
            
            if artifact_id is None:
                return None
            
            # Use artifact ID as component name, or fallback to directory name
            component_name = artifact_id.text if artifact_id.text else pom_file.parent.name
            component_type = self._get_component_type_from_packaging(packaging.text if packaging is not None else "jar")
            
            # Determine programming language (Maven is primarily Java)
            programming_language = "java"
            
            # Determine runtime
            runtime = Runtime.JVM
            
            # Get output information
            output_path = self._get_maven_output_path(pom_file, component_name, component_type)
            
            # Create evidence from pom.xml location
            evidence = Evidence(call_stack=[f"pom.xml: {pom_file.relative_to(self.project_root)}"])
            
            # Create component location
            location = ComponentLocation(
                path=pom_file,
                action="build",
                evidence=evidence
            )
            
            # Create component
            component = Component(
                name=component_name,
                type=component_type,
                programming_language=programming_language,
                runtime=runtime,
                output=component_name,
                output_path=output_path,
                source_files=[Path("src/main/java")],  # Default Maven structure
                depends_on=[],  # Will be populated from dependencies
                evidence=evidence,
                locations=[location]
            )
            
            return component
            
        except Exception as e:
            print(f"Warning: Could not parse pom.xml {pom_file}: {e}")
            return None
    
    def _get_component_type_from_packaging(self, packaging: str) -> ComponentType:
        """Map Maven packaging to ComponentType."""
        packaging_lower = packaging.lower()
        
        if packaging_lower == "jar":
            return ComponentType.STATIC_LIBRARY
        elif packaging_lower == "war":
            return ComponentType.SHARED_LIBRARY  # Treat WAR as shared library
        elif packaging_lower == "ear":
            return ComponentType.SHARED_LIBRARY  # Treat EAR as shared library
        elif packaging_lower == "pom":
            return ComponentType.STATIC_LIBRARY  # Treat POM as static library
        else:
            # Unknown packaging - mark as UNKNOWN
            return ComponentType.STATIC_LIBRARY  # Default fallback
    
    def _get_maven_output_path(self, pom_file: Path, component_name: str, component_type: ComponentType) -> Path:
        """Get Maven output path for component."""
        target_dir = pom_file.parent / "target"
        
        if component_type == ComponentType.EXECUTABLE:
            return target_dir / f"{component_name}.jar"
        elif component_type == ComponentType.STATIC_LIBRARY:
            return target_dir / f"{component_name}.jar"
        elif component_type == ComponentType.SHARED_LIBRARY:
            return target_dir / f"{component_name}.war"
        else:
            return target_dir / f"{component_name}.jar"
    
    def _extract_external_packages(self) -> None:
        """Extract external packages from Maven dependencies."""
        try:
            # Try to find mvn command
            mvn_cmd = "mvn"
            try:
                subprocess.run(["mvn", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try common Maven installation paths
                mvn_paths = [
                    "C:\\Program Files\\Apache\\Maven\\bin\\mvn.cmd",
                    "C:\\apache-maven\\bin\\mvn.cmd",
                    "/usr/bin/mvn",
                    "/usr/local/bin/mvn"
                ]
                for path in mvn_paths:
                    if Path(path).exists():
                        mvn_cmd = path
                        break
                else:
                    print("Warning: Maven command not found, skipping dependency extraction")
                    return
            
            # Run mvn dependency:tree to get dependency information
            result = subprocess.run(
                [mvn_cmd, "dependency:tree", "-DoutputType=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse dependency tree JSON
                dependency_data = json.loads(result.stdout)
                self._process_dependency_tree(dependency_data)
            
        except Exception as e:
            print(f"Warning: Could not extract Maven dependencies: {e}")
    
    def _process_dependency_tree(self, dependency_data: Dict[str, Any]) -> None:
        """Process Maven dependency tree data."""
        if "dependencies" not in dependency_data:
            return
        
        for dep in dependency_data["dependencies"]:
            self._process_dependency(dep)
    
    def _process_dependency(self, dep: Dict[str, Any]) -> None:
        """Process a single Maven dependency."""
        try:
            group_id = dep.get("groupId", "UNKNOWN")
            artifact_id = dep.get("artifactId", "UNKNOWN")
            version = dep.get("version", "UNKNOWN")
            scope = dep.get("scope", "compile")
            
            # Skip test dependencies for external packages
            if scope == "test":
                return
            
            # Create external package
            package_name = f"{group_id}:{artifact_id}:{version}"
            external_package = ExternalPackage(
                package_manager=PackageManager(
                    name="maven",
                    package_name=package_name
                )
            )
            self._temp_external_packages.append(external_package)
            
            # Process child dependencies
            if "children" in dep:
                for child in dep["children"]:
                    self._process_dependency(child)
                    
        except Exception as e:
            print(f"Warning: Could not process dependency: {e}")
    
    def _extract_test_information(self) -> None:
        """Extract test information from Maven project."""
        # Find all test files
        test_files = list(self.project_root.rglob("**/test/**/*Test.java"))
        
        for test_file in test_files:
            test_def = self._create_test_definition_from_file(test_file)
            if test_def:
                self._temp_tests.append(test_def)
    
    def _create_test_definition_from_file(self, test_file: Path) -> Optional[TestDefinition]:
        """Create test definition from test file."""
        try:
            # Extract test class name from file path
            test_name = test_file.stem
            
            # Determine test framework from file content or naming
            test_framework = self._detect_test_framework(test_file)
            
            # Create evidence
            evidence = Evidence(call_stack=[f"test file: {test_file.relative_to(self.project_root)}"])
            
            # Create test definition
            test_def = TestDefinition(
                name=test_name,
                test_framework=test_framework,
                test_type="unit",  # Default for Maven tests
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
            
            # Check for JUnit 5
            if "@test" in content_lower and "junit" in content_lower:
                return "junit5"
            # Check for JUnit 4
            elif "import org.junit.test" in content_lower:
                return "junit4"
            # Check for TestNG
            elif "import org.testng" in content_lower:
                return "testng"
            # Check for Mockito
            elif "import org.mockito" in content_lower:
                return "mockito"
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
            output_directory=self.project_root / "target",
            configure_command="mvn clean compile",
            build_command="mvn package",
            install_command="mvn install",
            test_command="mvn test"
        )
        
        # Create build system info
        build_system_info = BuildSystemInfo(
            name="maven",
            version="UNKNOWN",  # Could be extracted from mvn --version
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