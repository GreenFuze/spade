from pathlib import Path
from typing import List, Set

from cmake_file_api.kinds.cache.v2 import CacheV2
from cmake_file_api.kinds.codemodel.target.v2 import TargetType

from core.schemas import ComponentType, ExternalPackage, Evidence
from deterministic.cmake.cmake_target import CMakeTargetWrapper


# You'll need to extract: type, programming_language, source_files,
# relative_path, locations, external_packages, evidence

class CMakeTargetRigComponent:

    def __init__(self, target: 'CMakeTargetWrapper', cmake_cache: CacheV2):
        
        assert isinstance(target, CMakeTargetWrapper)
        
        self._target = target
        self._cmake_cache = cmake_cache
        
    def get_component_type(self) -> ComponentType:
        
        if self._target.cmake_target.target.type == TargetType.EXECUTABLE:
            return ComponentType.EXECUTABLE
        elif self._target.cmake_target.target.type == TargetType.STATIC:
            return ComponentType.STATIC_LIBRARY
        elif self._target.cmake_target.target.type == TargetType.SHARED:
            return ComponentType.SHARED_LIBRARY
        else:
            raise ValueError(f"Don't know how to map this to ComponentType: {self._target.cmake_target.target.type}")

    def get_programming_language(self) -> str:
        if len(self._target.cmake_target.target.compileGroups) == 0:
            raise ValueError("No compile groups found for target - cannot extract programming language")
        
        return self._target.cmake_target.target.compileGroups[0].language.lower()
    
    def get_source_files(self) -> List[Path]:
        res = []
        for src in self._target.cmake_target.target.sources:
            res.append(src.path)
        return res
    
    def get_relative_path(self) -> Path:
        """Get the primary location where the artifact is built (relative to repo root).

        Returns the full path like: spade_build/Debug/utils.lib
        Formula: (BINARY_DIR / artifact.path).relative_to(repo_root)
        """

        # Get binary directory from cache
        binary_dir_abs = None
        for cache_entry in self._cmake_cache.entries:
            if cache_entry.name == f"{self._target.cmake_target.project.name}_BINARY_DIR":
                binary_dir_abs = Path(cache_entry.value)
                break

        if binary_dir_abs is None:
            raise ValueError(f"Could not find BINARY_DIR for project {self._target.cmake_target.project.name}")

        # Find artifact with matching nameOnDisk
        for art in self._target.cmake_target.target.artifacts:
            if art.name == self._target.cmake_target.target.nameOnDisk:
                # art is a Path object relative to BINARY_DIR (e.g., "Debug/utils.lib" or "utils.lib")
                full_abs_path = binary_dir_abs / art
                return full_abs_path.relative_to(self._target.repo_root)

        raise ValueError(f"No artifact found with nameOnDisk {self._target.cmake_target.target.nameOnDisk}")
    
    def get_locations(self) -> List[Path]|None:
        """Get additional locations where the artifact might exist.

        This returns locations OTHER than the primary build location (returned by get_relative_path).
        Examples include:
        - Install directories (CMAKE_INSTALL_PREFIX)
        - Post-build copy destinations
        - Custom output directories

        Currently returns empty list as we don't have information about additional locations.
        """
        return []
    
    def get_external_packages(self) -> List[ExternalPackage]|None:
        return []
    
    def get_evidence(self) -> List[Evidence]:
        file_path: Path = self._target.cmake_target.target.backtrace.file
        evidence_line = self._target.cmake_target.target.backtrace.line
        
        return [Evidence(line=[f'{file_path}:{evidence_line}'], call_stack=None)]
    