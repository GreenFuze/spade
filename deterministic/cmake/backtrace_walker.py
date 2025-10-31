"""Backtrace walker utility for extracting user's actual function call location from CMake backtraces.

This module provides functionality to walk CMake's backtrace parent chain to find
the user's actual function call in their CMakeLists.txt, rather than pointing to
internal implementation files (like UseJava.cmake).
"""

from pathlib import Path
from typing import Optional

from cmake_file_api.kinds.codemodel.target.v2 import BacktraceNode

from core.schemas import Evidence


class BacktraceWalker:
    """Utility for walking CMake backtrace chains to find user call sites."""

    # Maximum depth to prevent infinite loops in case of cycles
    MAX_DEPTH = 50

    @staticmethod
    def get_user_call_site(backtrace: BacktraceNode, repo_root: Path) -> Evidence:
        """Walk backtrace to find the user's actual function call.

        Walks up the backtrace parent chain to find the first node that:
        - Is in a user file (relative to repo_root, not external modules)
        - Has a valid line number and command

        This ensures evidence points to where the user called the function
        (e.g., CMakeLists.txt:36 for add_jar call) rather than where the
        internal implementation is (e.g., UseJava.cmake:974 for add_custom_target).

        Args:
            backtrace: The CMake backtrace node to start walking from
            repo_root: The repository root path to determine user vs external files

        Returns:
            Evidence object with line pointing to user's call site

        Raises:
            ValueError: If no valid user call site found within MAX_DEPTH iterations
            ValueError: If repo_root is not a valid directory
        """
        if not repo_root.is_dir():
            raise ValueError(f"repo_root must be a valid directory: {repo_root}")

        # Normalize repo_root for consistent path comparisons
        repo_root = repo_root.resolve()

        current: Optional[BacktraceNode] = backtrace
        depth = 0
        user_node: Optional[BacktraceNode] = None

        # Walk the backtrace parent chain
        while current is not None:
            # Prevent infinite loops
            if depth >= BacktraceWalker.MAX_DEPTH:
                raise ValueError(
                    f"Exceeded maximum backtrace depth ({BacktraceWalker.MAX_DEPTH}). "
                    f"Possible cycle in backtrace or overly deep call stack."
                )

            depth += 1

            # Check if this node has valid line number and command
            if current.line is not None and current.command is not None:
                try:
                    file_path = Path(current.file)

                    # Handle both absolute and relative paths
                    if file_path.is_absolute():
                        resolved_path = file_path.resolve()
                    else:
                        # If relative, resolve it relative to repo_root
                        resolved_path = (repo_root / file_path).resolve()

                    # Try to make it relative to repo_root to check if it's within
                    rel_path = resolved_path.relative_to(repo_root)

                    # This is a user file! Save it as candidate
                    # We want the FIRST user node (closest to leaf in the call stack)
                    if user_node is None:
                        user_node = current

                except (ValueError, OSError):
                    # File is outside repo (like UseJava.cmake in CMake modules) - skip it
                    # OSError can happen if path doesn't exist
                    pass

            # Move to parent
            current = current.parent

        # Use the user node we found
        if user_node is not None:
            file_path = Path(user_node.file)

            # Try to make path relative to repo_root for cleaner evidence
            try:
                # Handle both absolute and relative paths
                if file_path.is_absolute():
                    resolved_path = file_path.resolve()
                else:
                    resolved_path = (repo_root / file_path).resolve()

                relative_file_path = resolved_path.relative_to(repo_root)
                evidence_location = f'{relative_file_path}:{user_node.line}'
            except (ValueError, OSError):
                # If we can't make it relative, use the original path
                evidence_location = f'{file_path}:{user_node.line}'

            return Evidence(line=[evidence_location], call_stack=None)

        # If we didn't find any user node, this is a critical failure
        # Fall back to the original backtrace but raise an error
        raise ValueError(
            f"Could not find user call site in backtrace. "
            f"Backtrace started at {backtrace.file}:{backtrace.line} "
            f"but no nodes were within repo_root: {repo_root}"
        )
