"""
CMakeEntrypoint class for parsing CMake configuration and extracting build system information.
Uses the cmake-file-api package to analyze CMake projects and create a canonical representation.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any, Union, Set, cast

from cmake_file_api import CMakeProject, ObjectKind
from cmake_file_api.kinds.cache.v2 import CacheV2
from cmake_file_api.kinds.cmakeFiles.v1 import CMakeFilesV1
from cmake_file_api.kinds.codemodel.target.v2 import CodemodelTargetV2
from cmake_file_api.kinds.codemodel.v2 import CodemodelV2, CMakeDirectory, CMakeConfiguration, CMakeTarget
from cmake_file_api.kinds.common import VersionMajorMinor
from cmake_file_api.kinds.configureLog.v1 import ConfigureLogV1
from cmake_file_api.kinds.toolchains.v1 import ToolchainsV1

from core.schemas import Component, ComponentType, ExternalPackage, PackageManager, TestDefinition, Evidence, Aggregator, Runner, RepositoryInfo, BuildSystemInfo, NodeType
from core.rig import RIG

from .cmake_target import CMakeTargetWrapper
from .cmake_parser import CMakeParser
from .ctest_wrapper import CTestWrapper

spade_build_dir_name = "spade_build"

class CMakePlugin:
    """
    Parses CMake configuration and extracts build system information.

    This class uses the cmake-file-api package to analyze CMake projects and create
    a canonical representation of the build system structure, including components,
    tests, dependencies, and external packages.
    """

    def __init__(self, repo_root: Path) -> None:
        """
        Initialize CMakeEntrypoint with CMake configuration directory.

        Args:
            cmake_config_dir: Path to CMake configuration directory
            parse_cmake: Whether to parse CMake configuration (default: True)
        """
        self.repo_root = repo_root
        self.cmake_config_dir = repo_root / spade_build_dir_name

        # Create RIG instance to hold all extracted data
        self._rig = RIG()
        
        # Create CMakeProject instance
        self._proj: CMakeProject = CMakeProject(build_path=self.cmake_config_dir, source_path=self.repo_root, api_version=1)
        
        # Ask CMake for all supported object kinds
        self._proj.cmake_file_api.instrument_all()
        
        # Run CMake configure to produce all information required to read from the file API
        self._proj.configure(quiet=False, args=["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])
        
        # load all cmake entities
        self._entities = self._proj.cmake_file_api.inspect_all()
        self._cmake_cache:CacheV2 = cast(CacheV2, self._entities[ObjectKind.CACHE][2])
        self._cmake_files:CMakeFilesV1 = cast(CMakeFilesV1, self._entities[ObjectKind.CMAKEFILES][1])
        self._cmake_code_model:CodemodelV2 = cast(CodemodelV2, self._entities[ObjectKind.CODEMODEL][2])
        self._cmake_configure_log:ConfigureLogV1 = cast(ConfigureLogV1, self._entities[ObjectKind.CONFIGURELOG][1])
        self._cmake_toolchains:ToolchainsV1 = cast(ToolchainsV1, self._entities[ObjectKind.TOOLCHAINS][1])
        
        self._generate_rig()

    def _generate_rig(self) -> None:
        """Parse CMake configuration using the file API."""
        
        # extract RepositoryInfo
        self._rig.set_repository_info(self._extract_repository_info())
        self._rig.set_build_system_info(self._extract_build_system_info())

        # Extract RIG nodes (components, aggregators, runners, tests)
        # Nodes are added directly to self._rig during extraction
        self._extract_rig_nodes()


    def _extract_rig_nodes(self) -> None:
        """Extract components, aggregators, runners, and tests from CMakeProject data."""

        # Initialize findings cache (keys are CMake target IDs)
        findings: Dict[NodeType, Dict[str, Union[Component, Aggregator, Runner, TestDefinition]]] = {
            NodeType.COMPONENT: {},      # Dict[str, Component]
            NodeType.AGGREGATOR: {},     # Dict[str, Aggregator]
            NodeType.RUNNER: {},         # Dict[str, Runner]
            NodeType.TEST_DEFINITION: {}            # Dict[str, TestDefinition]
        }

        # Iterate over configurations (usually just one: Debug or Release)
        config = self._cmake_code_model.configurations[0]

        # Iterate over targets in configuration
        for target in config.targets:
            target_wrapper = CMakeTargetWrapper(target, self._cmake_toolchains, self._cmake_cache, self.repo_root)
            target_id = target.target.id
            node_type = target_wrapper.get_rig_node_type()

            # Skip non-RIG targets (e.g., UTILITY)
            if node_type is None:
                continue

            # Check if already created (by recursive dependency resolution)
            if target_id in findings.get(node_type, {}):
                continue

            # Create node (will recursively create dependencies with cycle detection)
            if node_type == NodeType.COMPONENT:
                component = target_wrapper.get_as_rig_component(findings)
                self._rig.add_component(component)

            elif node_type == NodeType.AGGREGATOR:
                aggregator = target_wrapper.get_as_rig_aggregator(findings)
                self._rig.add_aggregator(aggregator)

            elif node_type == NodeType.RUNNER:
                runner = target_wrapper.get_as_rig_runner(findings)
                self._rig.add_runner(runner)

        # Process CTest tests after all CMake targets
        # Create CTestWrapper and extract test definitions
        ctest_wrapper = CTestWrapper(
            repo_root=self.repo_root,
            build_dir_name=spade_build_dir_name,
            configuration=config.name,
            findings=findings
        )

        for ctest_info in ctest_wrapper.get_all_tests():
            test_def = ctest_wrapper.create_test_definition(ctest_info)
            self._rig.add_test(test_def)

    def _extract_repository_info(self) -> RepositoryInfo:
        """Constructs RepositoryInfo from CMakeProject data."""

        # Get project name from first configuration's first project
        project_name = self._cmake_code_model.configurations[0].projects[0].name

        # Get build directory (where binaries are built)
        build_dir = self._cmake_code_model.paths.build
        try:
            build_dir_relative = build_dir.relative_to(self.repo_root)
        except ValueError:
            # If build is outside repo, keep absolute path
            build_dir_relative = build_dir

        # Extract install directory from CMAKE_INSTALL_PREFIX cache variable
        install_dir = None
        output_dir = None
        for entry in self._cmake_cache.entries:
            if entry.name == "CMAKE_INSTALL_PREFIX":
                install_path = Path(entry.value)
                install_dir = install_path.relative_to(self.repo_root) if install_path.is_relative_to(self.repo_root) else install_path
            elif entry.name == f"{project_name}_BINARY_DIR":
                output_dir = Path(entry.value).relative_to(self.repo_root)

        # Create RepositoryInfo
        # Commands are left as None since CMake File API doesn't store them
        ri = RepositoryInfo(
            name=project_name,
            root_path=self.repo_root,
            build_directory=build_dir_relative,
            output_directory=output_dir,  # Same as build_directory (where binaries go)
            install_directory=install_dir,
            configure_command=None,  # Not available in CMake File API
            build_command=None,  # Not available in CMake File API
            install_command=None,  # Not available in CMake File API
            test_command=None  # Not available in CMake File API
        )

        return ri
    
    def _extract_build_system_info(self) -> BuildSystemInfo:
        """Constructs BuildSystemInfo from CMakeProject data."""

        # extract CMake version by running and reading cmake --version
        try:
            result = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True)
            first_line = result.stdout.splitlines()[0]
            cmake_version = first_line.split("version")[-1].strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            cmake_version = "unknown"

        # Create BuildSystemInfo
        bsi = BuildSystemInfo(
            name="CMake",
            version=cmake_version,
            build_type=self._cmake_code_model.configurations[0].name
        )

        return bsi
    

    @property
    def rig(self) -> RIG:
        """Get the Repository Intelligence Graph."""
        return self._rig

    
