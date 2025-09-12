"""
Pydantic schemas for SPADE build system analysis.
Defines the canonical structure for representing build system information.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Types of build components."""

    EXECUTABLE = "executable"
    SHARED_LIBRARY = "shared_library"
    STATIC_LIBRARY = "static_library"
    VM = "vm"
    INTERPRETED = "interpreted"


class Runtime(str, Enum):
    """Runtime environments."""

    JVM = "JVM"
    VS_C = "VS-C"
    VS_CPP = "VS-CPP"
    CLANG_C = "CLANG-C"
    GO = "Go"
    DOTNET = ".NET"
    PYTHON = "Python"
    UNKNOWN = "UNKNOWN"


class PackageManager(BaseModel):
    """Package manager information."""

    id: Optional[int] = Field(None, description="Database ID")
    name: str = Field(..., description="Package manager name (e.g., vcpkg, conan)")
    package_name: str = Field(..., description="Package name")


class ExternalPackage(BaseModel):
    """External package dependency."""

    id: Optional[int] = Field(None, description="Database ID")
    package_manager: PackageManager = Field(..., description="Package manager information")


class Evidence(BaseModel):
    """Evidence with location and text information."""

    id: Optional[int] = Field(None, description="Database ID")
    call_stack: List[str] = Field(..., description="List of GitHub-style line references in call stack order (leaf first)")


class ComponentLocation(BaseModel):
    """Component location with action information."""

    id: Optional[int] = Field(None, description="Database ID")
    path: Path = Field(..., description="Path to the component at this location")
    action: str = Field(..., description="Action that created this location (build, copy, move)")
    source_location: Optional["ComponentLocation"] = Field(None, description="Source location for copy/move operations")
    evidence: Evidence = Field(..., description="Evidence for this location action")


class BuildNode(BaseModel):
    """Base class for all build system nodes."""

    id: Optional[int] = Field(None, description="Database ID")
    name: str = Field(..., description="Node name")
    depends_on: List[Union["Component", "Aggregator", "Runner", "Utility"]] = Field(default_factory=list, description="Dependencies")
    evidence: Evidence = Field(..., description="Location evidence in CMake files")


class Component(BuildNode):
    """Build component (executable, library, etc.)."""

    type: ComponentType = Field(..., description="Component type")
    runtime: Optional[Runtime] = Field(None, description="Runtime environment")
    output: str = Field(..., description="Output component name")
    output_path: Path = Field(..., description="Output path relative to output root")
    programming_language: str = Field(..., description="Programming language (lowercase)")
    source_files: List[Path] = Field(..., description="Source files relative to repo root")
    external_packages: List[ExternalPackage] = Field(default_factory=list, description="External package dependencies")
    locations: List[ComponentLocation] = Field(default_factory=list, description="All locations where this component exists")
    test_link_id: Optional[int] = Field(None, description="ID of corresponding test node (if this component is a test)")
    test_link_name: Optional[str] = Field(None, description="Name of corresponding test node (if this component is a test)")


class Aggregator(BuildNode):
    """Build aggregator (orchestrates other targets)."""

    pass


class Runner(BuildNode):
    """Build runner (executes commands)."""

    pass


class Utility(BuildNode):
    """Build utility (UTILITY targets with no artifacts or dependencies)."""

    pass


class Test(BaseModel):
    """Test definition."""

    id: Optional[int] = Field(None, description="Database ID")
    name: str = Field(..., description="Test name")
    test_executable: Optional[Component] = Field(None, description="Component that produces the test executable")
    components_being_tested: List[Component] = Field(default_factory=list, description="Components being tested")
    test_runner: Optional[Runner] = Field(None, description="Custom test runner if used")
    source_files: List[Path] = Field(..., description="Source files used to build the test")
    test_framework: str = Field(..., description="Test framework name")
    evidence: Evidence = Field(..., description="Location evidence in CMake files")


@dataclass
class RepositoryInfo:
    """Repository-level information."""

    name: str
    root_path: Path
    build_directory: Path
    output_directory: Path
    configure_command: str
    build_command: str
    install_command: str
    test_command: str


@dataclass
class BuildSystemInfo:
    """Build system specific information."""

    name: str  # e.g., "CMake/Ninja", "Bazel", "Make", etc.
    version: Optional[str] = None
    build_type: Optional[str] = None  # e.g., "Debug", "Release", etc.


class ValidationSeverity(str, Enum):
    """Severity levels for validation errors."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Detailed validation error information."""

    severity: ValidationSeverity
    category: str
    message: str
    node_name: Optional[str] = None
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class RIGValidationError(Exception):
    """Exception raised when RIG validation fails with errors."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
        warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])
        super().__init__(f"RIG validation failed: {error_count} errors, {warning_count} warnings")
