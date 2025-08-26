"""
SPADE Ignore Logic
Centralized skip logic using .spade/.spadeignore and .spade/.spadeallow patterns
"""

from pathlib import Path
from typing import Optional, Union
import pathspec


def load_specs(repo_root: Path) -> tuple[pathspec.PathSpec, pathspec.PathSpec, list[str], list[str]]:
    """
    Load ignore and allow patterns from .spade/.spadeignore and .spade/.spadeallow files.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        Tuple of (ignore_spec, allow_spec, ignore_lines, allow_lines)
        
    Raises:
        FileNotFoundError: If .spade directory doesn't exist
        ValueError: If patterns are invalid
    """
    ig_path = repo_root / ".spade" / ".spadeignore"
    al_path = repo_root / ".spade" / ".spadeallow"
    
    # Read ignore patterns
    if ig_path.exists():
        try:
            ig_patterns = ig_path.read_text(encoding='utf-8').splitlines()
        except Exception as e:
            raise ValueError(f"Failed to read .spadeignore: {e}")
    else:
        ig_patterns = []
    
    # Read allow patterns
    if al_path.exists():
        try:
            al_patterns = al_path.read_text(encoding='utf-8').splitlines()
        except Exception as e:
            raise ValueError(f"Failed to read .spadeallow: {e}")
    else:
        al_patterns = []
    
    # Create PathSpec objects
    try:
        ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", ig_patterns)
        allow_spec = pathspec.PathSpec.from_lines("gitwildmatch", al_patterns)
    except Exception as e:
        raise ValueError(f"Invalid patterns in ignore/allow files: {e}")
    
    return ignore_spec, allow_spec, ig_patterns, al_patterns


def _find_matching_pattern(rel: str, spec: pathspec.PathSpec, raw_lines: list[str]) -> Optional[str]:
    """
    Find the first pattern that matches the given relative path.
    
    Args:
        rel: Relative path to check
        spec: PathSpec object (for validation)
        raw_lines: Raw pattern lines from the ignore/allow file
        
    Returns:
        The first matching pattern string, or None if no match
    """
    for line in raw_lines:
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Create a one-off PathSpec from this single pattern
        try:
            single_spec = pathspec.PathSpec.from_lines("gitwildmatch", [line])
            if single_spec.match_file(rel):
                return line
        except Exception:
            # Skip invalid patterns
            continue
    
    return None


def should_skip(
    path: Union[Path, str], 
    repo_root: Path, 
    ignore_spec: pathspec.PathSpec, 
    allow_spec: pathspec.PathSpec, 
    skip_symlinks: bool
) -> bool:
    """
    Determine if a path should be skipped based on ignore/allow patterns and symlink policy.
    
    Args:
        path: Path to check (Path object or string)
        repo_root: Root directory of the repository
        ignore_spec: PathSpec for ignore patterns
        allow_spec: PathSpec for allow patterns
        skip_symlinks: Whether to skip symlinks
        
    Returns:
        True if path should be skipped, False otherwise
        
    Raises:
        ValueError: If path is not under repo_root
    """
    # Convert string to Path if needed
    if isinstance(path, str):
        path = repo_root / path
    
    # Check symlinks first
    if skip_symlinks and path.is_symlink():
        return True
    
    # Get relative path
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        raise ValueError(f"Path {path} is not under repository root {repo_root}")
    
    # Root directory should never be skipped
    if rel == ".":
        return False
    
    # Check ignore/allow patterns
    return ignore_spec.match_file(rel) and not allow_spec.match_file(rel)


def explain_skip(
    path: Union[Path, str], 
    repo_root: Path, 
    ignore_spec: pathspec.PathSpec, 
    allow_spec: pathspec.PathSpec, 
    ignore_lines: list[str],
    allow_lines: list[str],
    skip_symlinks: bool
) -> Optional[str]:
    """
    Explain why a path is being skipped, or return None if not skipped.
    
    Args:
        path: Path to check (Path object or string)
        repo_root: Root directory of the repository
        ignore_spec: PathSpec for ignore patterns
        allow_spec: PathSpec for allow patterns
        ignore_lines: Raw ignore pattern lines
        allow_lines: Raw allow pattern lines
        skip_symlinks: Whether to skip symlinks
        
    Returns:
        Explanation string if path should be skipped, None otherwise
        
    Raises:
        ValueError: If path is not under repo_root
    """
    # Convert string to Path if needed
    if isinstance(path, str):
        path = repo_root / path
    
    # Check symlinks first
    if skip_symlinks and path.is_symlink():
        return "symlink target"
    
    # Get relative path
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        raise ValueError(f"Path {path} is not under repository root {repo_root}")
    
    # Root directory should never be skipped
    if rel == ".":
        return None
    
    # Check ignore/allow patterns
    if ignore_spec.match_file(rel) and not allow_spec.match_file(rel):
        # Find the specific pattern that matched
        pattern = _find_matching_pattern(rel, ignore_spec, ignore_lines) or "<unknown>"
        return f"matched .spadeignore: '{pattern}'"
    
    return None
