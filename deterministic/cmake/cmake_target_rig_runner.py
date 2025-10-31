from pathlib import Path
from typing import List, Union

from core.schemas import Evidence, Component, Aggregator, Runner, TestDefinition
from deterministic.cmake.backtrace_walker import BacktraceWalker
# Note: CMakeTargetWrapper not imported to avoid circular import - using string literal type hint


class CMakeTargetRigRunner:

    def __init__(self, target: 'CMakeTargetWrapper'):
        # Import here to check type at runtime (avoid circular import at module level)
        from deterministic.cmake.cmake_target import CMakeTargetWrapper
        assert isinstance(target, CMakeTargetWrapper)

        self._target = target

    def get_name(self) -> str:
        """Get runner name from CMake target name (same as Aggregator)."""
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

    def get_arguments(self) -> List[str]:
        """Get command-line arguments for runner.

        Returns empty list for CMake targets (no explicit arguments in CMake target definition).
        """
        return []

    def get_args_nodes(self) -> List[Union[Component, Aggregator, Runner, TestDefinition]]:
        """Get RIG nodes referenced by arguments.

        Returns empty list for CMake targets (no explicit argument nodes in CMake target definition).
        """
        return []
