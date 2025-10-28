from pathlib import Path
from typing import List

from core.schemas import Evidence
# Note: CMakeTargetWrapper not imported to avoid circular import - using string literal type hint


class CMakeTargetRigAggregator:

    def __init__(self, target: 'CMakeTargetWrapper'):
        # Import here to check type at runtime (avoid circular import at module level)
        from deterministic.cmake.cmake_target import CMakeTargetWrapper
        assert isinstance(target, CMakeTargetWrapper)

        self._target = target

    def get_name(self) -> str:
        """Get aggregator name from CMake target name (not nameOnDisk)."""
        return self._target._cmake_target.name

    def get_evidence(self) -> List[Evidence]:
        """Extract evidence from target backtrace (same as Component)."""
        file_path: Path = self._target._cmake_target.target.backtrace.file
        evidence_line = self._target._cmake_target.target.backtrace.line

        return [Evidence(line=[f'{file_path}:{evidence_line}'], call_stack=None)]