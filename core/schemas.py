"""
Pydantic schemas for SPADE build system analysis.
Defines the canonical structure for representing build system information.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from itertools import count
from pydantic import BaseModel, Field, model_validator

# Built-in counters for ID generation
_component_counter = count(1)
_aggregator_counter = count(1)
_runner_counter = count(1)
_test_counter = count(1)
_package_counter = count(1)
_evidence_counter = count(1)

class NodeType(str, Enum):
    """Types of build system nodes."""
    
    COMPONENT = "component"
    AGGREGATOR = "aggregator"
    RUNNER = "runner"
    TEST_DEFINITION = "test_definition"


class ComponentType(str, Enum):
    """Types of build components."""

    EXECUTABLE = "executable"
    SHARED_LIBRARY = "shared_library"
    STATIC_LIBRARY = "static_library"
    PACKAGE_LIBRARY = "package_library"
    VM = "vm"
    INTERPRETED = "interpreted"

class PackageManager(BaseModel):
    """Package manager information."""

    id: str = Field(default_factory=lambda: f"pkg-{next(_package_counter)}", description="Auto-generated ID with prefix")
    name: str = Field(..., description="Package manager name (e.g., vcpkg, conan)")
    package_name: str = Field(..., description="Package name")


class ExternalPackage(BaseModel):
    """External package dependency."""

    id: str = Field(default_factory=lambda: f"pkg-{next(_package_counter)}", description="Auto-generated ID with prefix")
    name: str = Field(..., description="External package name")
    package_manager: PackageManager = Field(..., description="Package manager information")


class Evidence(BaseModel):
    """Evidence with location and text information.

    At least one of `line` or `call_stack` must be provided.
    """

    id: str = Field(default_factory=lambda: f"evidence-{next(_evidence_counter)}", description="Auto-generated ID with prefix")
    line: Optional[List[str]] = Field(None, description="GitHub-style line references")
    call_stack: Optional[List[str]] = Field(None, description="List of GitHub-style line references in build system call stack order (leaf first)")

    @model_validator(mode="after")
    def _require_line_or_call_stack(self) -> "Evidence":
        if not self.line and not self.call_stack:
            raise ValueError("Evidence must include at least one of 'line' or 'call_stack'")
        return self

# TODO: I think we can remove this and use locations as list of Paths
# class ComponentLocation(BaseModel):
#     """Component location with action information."""
#
#     id: str = Field(default_factory=lambda: str(uuid4()), description="Auto-generated UUID")
#     path: Path = Field(..., description="Path to the component at this location")
#     action: str = Field(..., description="Action that created this location (build, copy, move)")
#     source_location: Optional["ComponentLocation"] = Field(None, description="Source location for copy/move operations")
#     evidence: Evidence = Field(..., description="Evidence for this location action")


class RIGNode(BaseModel):
    """Base class for all build system nodes."""

    id: str = Field(default_factory=lambda: f"comp-{next(_component_counter)}", description="Auto-generated ID with prefix")
    name: str = Field(..., description="Node name")
    depends_on: Optional[List['RIGNode']] = Field(default_factory=list, description="Dependencies")
    depends_on_ids: Optional[Set[str]] = Field(default_factory=set, description="Dependencies IDs for quick lookup")
    evidence: List[Evidence] = Field(..., description="Location evidence in files")
    evidence_ids: Optional[Set[str]] = Field(default_factory=set, description="Set of evidence IDs for quick lookup")

class Artifact(RIGNode):
    """Artifact produced by a build node."""
    name: str = Field(..., description="artifact file name")
    relative_path: Path = Field(..., description="Output path relative to project root")
    locations: Optional[List[Path]] = Field(default_factory=list, description="Other locations of this artifact")

class Component(Artifact):
    """Code component (executable, static/dynamic library, etc.)."""

    type: ComponentType = Field(..., description="Component type")
    programming_language: str = Field(..., description="Programming language (lowercase)")
    source_files: List[Path] = Field(..., description="Source files relative to repo root")

    external_packages_ids: Optional[Set[str]] = Field(default_factory=set, description="IDs of external package dependencies")
    external_packages: Optional[List[ExternalPackage]] = Field(default_factory=list, description="External package dependencies")


class Aggregator(RIGNode):
    """Build aggregator (orchestrates other targets)."""
    id: str = Field(default_factory=lambda: f"agg-{next(_aggregator_counter)}", description="Auto-generated ID with prefix")


class Runner(RIGNode):
    """Build runner (executes commands)."""
    id: str = Field(default_factory=lambda: f"runner-{next(_runner_counter)}", description="Auto-generated ID with prefix")
    arguments: List[str] = Field(default_factory=list, description="Command-line arguments")
    args_nodes: List['RIGNode'] = Field(default_factory=list, description="RIG nodes referenced by arguments")
    args_nodes_ids: Set[str] = Field(default_factory=set, description="IDs of args_nodes for quick lookup")

# class Utility(RIGNode):
#     """Build utility (no artifacts or dependencies)."""
#     id: str = Field(default_factory=lambda: f"util-{next(_runner_counter)}", description="Auto-generated ID with prefix")


class TestDefinition(RIGNode):
    """Test """
    id: str = Field(default_factory=lambda: f"test-{next(_test_counter)}", description="Auto-generated ID with prefix")
    name: str = Field(..., description="Test name")
    test_executable_component: Optional[Component]|Optional[Runner] = Field(None, description="Component or Runner that produces the test executable")
    test_executable_component_id: Optional[str] = Field(None, description="ID of component or runner that produces the test executable")
    test_components: Optional[List[Component]] = Field(default_factory=list, description="Test components")
    test_components_ids: Optional[Set[str]] = Field(default_factory=set, description="IDs of test components")
    components_being_tested: Optional[List[Component]] = Field(default_factory=list, description="Components being tested")
    components_being_tested_ids: Optional[Set[str]] = Field(default_factory=set, description="IDs of components being tested")
    source_files: Optional[List[Path]] = Field(default_factory=list, description="Source files used to create the test")
    test_framework: str = Field(..., description="Test framework name")


@dataclass
class RepositoryInfo:
    """Repository-level information."""
    name: str
    root_path: Path
    build_directory: Optional[Path] = None
    output_directory: Optional[Path] = None
    install_directory: Optional[Path] = None
    configure_command: Optional[str] = None
    build_command: Optional[str] = None
    install_command: Optional[str] = None
    test_command: Optional[str] = None


@dataclass
class BuildSystemInfo:
    """Build system specific information."""
    name: str  # e.g., "CMake/Ninja", "Bazel", "Make", etc.
    version: Optional[str] = None
    build_type: Optional[str] = None  # e.g., "Debug", "Release", etc. # TODO: This should be changed to a list


class ValidationSeverity(str, Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationErrorCategory(str, Enum):
    """Categories for validation errors."""
    MISSING_SOURCE_FILE = "missing_source_file"
    BROKEN_DEPENDENCY = "broken_dependency"
    NO_DEPENDENCIES = "no_dependencies"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    DUPLICATE_NODE_ID = "duplicate_node_id"
    MISSING_TEST_EXECUTABLE = "missing_test_executable"
    TEST_EXECUTABLE_COMPONENT_NOT_FOUND = "test_executable_component_not_found"
    TEST_COMPONENT_OR_RUNNER_MISMATCH = "test_component_or_mismatch"
    MISSING_EVIDENCE = "missing_evidence"

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


class RIGPromptData(BaseModel):
    """Complete RIG data structure for JSON prompts."""
    repo: Dict[str, Any]
    build: Dict[str, Any]
    components: List[Dict[str, Any]]
    aggregators: List[Dict[str, Any]]
    runners: List[Dict[str, Any]]
    tests: List[Dict[str, Any]]
    external_packages: List[Dict[str, Any]]
    package_managers: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]


class RIGValidationError(Exception):
    """Exception raised when RIG validation fails with errors."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
        warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])
        super().__init__(f"RIG validation failed: {error_count} errors, {warning_count} warnings")
