from pathlib import Path
from typing import List

from core.schemas import Evidence
from deterministic.cmake.backtrace_walker import BacktraceWalker
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
        """Get evidence pointing to user's actual function call in CMakeLists.txt.

        Uses backtrace walker to find the user's call site rather than
        internal implementation details.
        """
        evidence = BacktraceWalker.get_user_call_site(
            self._target._cmake_target.target.backtrace,
            self._target.repo_root
        )
        return [evidence]