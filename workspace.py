"""
SPADE Workspace Management
Handles .spade directory creation and configuration files
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any

from models import RunConfig, save_json, load_json


class Workspace:
    """Manages SPADE workspace directory and configuration files."""
    
    @staticmethod
    def init(repo_root: Path) -> None:
        """Initialize .spade workspace directory with default configuration files."""
        spade_dir = repo_root / ".spade"
        spade_dir.mkdir(exist_ok=True)
        
        # Create configuration files if they don't exist
        Workspace._create_run_json(spade_dir)
        Workspace._create_spadeignore(spade_dir)
        Workspace._create_spadeallow(spade_dir)
        
        # Print success message with path list
        print(f"✓ Initialized SPADE workspace: {spade_dir}")
        print(f"✓ Created configuration files:")
        print(f"  - {spade_dir / 'run.json'}")
        print(f"  - {spade_dir / '.spadeignore'}")
        print(f"  - {spade_dir / '.spadeallow'}")
    
    @staticmethod
    def clean(repo_root: Path) -> None:
        """Delete .spade directory recursively."""
        spade_dir = repo_root / ".spade"
        if spade_dir.exists():
            shutil.rmtree(spade_dir)
            print(f"✓ Cleaned SPADE workspace: {spade_dir}")
        else:
            print(f"✓ No SPADE workspace found: {spade_dir}")
    
    @staticmethod
    def path(repo_root: Path, filename: str) -> Path:
        """Get path to a file in the .spade directory."""
        return repo_root / ".spade" / filename
    
    @staticmethod
    def _create_run_json(spade_dir: Path) -> None:
        """Create default run.json configuration file."""
        run_json_path = spade_dir / "run.json"
        if run_json_path.exists():
            return
        
        # Use Pydantic model for default configuration
        default_config = RunConfig()
        save_json(run_json_path, default_config)
    
    @staticmethod
    def _create_spadeignore(spade_dir: Path) -> None:
        """Create default .spadeignore file."""
        spadeignore_path = spade_dir / ".spadeignore"
        if spadeignore_path.exists():
            return
        
        default_ignore = """# dotdirs (keep .github visible)
.*
!.github/
# VCS
.git/
.hg/
.svn/
# builds/caches
__pycache__/
*.egg-info/
target/
build/
dist/
bin/
obj/
out/
node_modules/
vendor/
third_party/
# IDE
.idea/
.vscode/
"""
        
        with open(spadeignore_path, 'w', encoding='utf-8') as f:
            f.write(default_ignore)
    
    @staticmethod
    def _create_spadeallow(spade_dir: Path) -> None:
        """Create empty .spadeallow file."""
        spadeallow_path = spade_dir / ".spadeallow"
        if spadeallow_path.exists():
            return
        
        spadeallow_path.touch()
    
    @staticmethod
    def load_config(repo_root: Path) -> RunConfig:
        """Load configuration from run.json."""
        config_path = Workspace.path(repo_root, "run.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        return load_json(config_path, RunConfig)
