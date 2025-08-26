"""
SPADE Worklist Management
Handles DFS traversal state with resume capability
"""

from __future__ import annotations
from pathlib import Path
import json

from models import Worklist
from models import save_json_data

WORKLIST_PATH = ".spade/worklist.json"


class WorklistStore:
    """
    Manages worklist state for DFS traversal with resume capability.
    
    Args:
        repo_root: Root directory of the repository
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.path = repo_root / WORKLIST_PATH
        if not self.path.exists():
            self._init_fresh()
    
    def _init_fresh(self):
        """Initialize a fresh worklist starting from root."""
        # Ensure .spade directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        save_json_data(self.path, {"queue": ["."], "visited": []})
    
    def load(self) -> Worklist:
        """
        Load worklist from file.
        
        Returns:
            Worklist object with current state
            
        Raises:
            SystemExit: If file is corrupted and cannot be reset
        """
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return Worklist(**data)
        except Exception:
            # If corrupted, reset
            self._init_fresh()
            return Worklist(queue=["."], visited=[])
    
    def save(self, obj: Worklist) -> None:
        """
        Save worklist to file.
        
        Args:
            obj: Worklist object to save
        """
        save_json_data(self.path, obj.model_dump())
    
    def push_many_left(self, rels: list[str]) -> None:
        """
        Push multiple relative paths to the left of the queue (DFS order).
        
        Args:
            rels: List of relative paths to add
        """
        wl = self.load()
        # DFS: add new items at the left in reverse order to preserve natural order
        for r in reversed(rels):
            wl.queue.insert(0, r)
        self.save(wl)
    
    def pop_left(self) -> str | None:
        """
        Pop and return the leftmost item from the queue.
        
        Returns:
            Relative path string, or None if queue is empty
        """
        wl = self.load()
        if not wl.queue:
            return None
        item = wl.queue.pop(0)
        self.save(wl)
        return item
    
    def mark_visited(self, realpath: str) -> None:
        """
        Mark a realpath as visited.
        
        Args:
            realpath: Absolute path that has been processed
        """
        wl = self.load()
        if realpath not in wl.visited:
            wl.visited.append(realpath)
        self.save(wl)
    
    def is_visited(self, realpath: str) -> bool:
        """
        Check if a realpath has been visited.
        
        Args:
            realpath: Absolute path to check
            
        Returns:
            True if path has been visited, False otherwise
        """
        wl = self.load()
        return realpath in wl.visited

    def reset(self) -> None:
        """Reset queue to ['.'] and visited to [], write atomically."""
        save_json_data(self.path, {"queue": ["."], "visited": []})

    def reset_if_exists(self) -> None:
        """Reset worklist if it exists, otherwise do nothing."""
        if self.path.exists():
            self.reset()
