"""
SPADE Workspace Management
Handles .spade directory creation and configuration files
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from schemas import RunConfig, load_yaml, save_yaml
from spade_state import SpadeState


class Workspace:
    """Manages SPADE workspace directory and configuration files."""

    def __init__(self, repo_root: Path):
        """Initialize workspace with repository root path."""
        self.repo_root = repo_root
        self.spade_dir = repo_root / ".spade"
        self._spade_state: Optional[SpadeState] = None

    def create(self) -> None:
        """Create .spade workspace directory with default configuration files."""
        self.spade_dir.mkdir(exist_ok=True)

        # Create configuration files if they don't exist
        self._create_run_phase0_yaml()
        self._create_spadeignore()
        self._create_spadeallow()

        # Print success message with path list
        print(f"✓ Created SPADE workspace: {self.spade_dir}")
        print(f"✓ Created configuration files:")
        print(f"  - {self.spade_dir / 'run_phase0.yaml'}")
        print(f"  - {self.spade_dir / '.spadeignore'}")
        print(f"  - {self.spade_dir / '.spadeallow'}")

    def clean(self) -> None:
        """Delete .spade directory recursively."""
        if self.spade_dir.exists():
            shutil.rmtree(self.spade_dir)
            print(f"✓ Cleaned SPADE workspace: {self.spade_dir}")
        else:
            print(f"✓ No SPADE workspace found: {self.spade_dir}")

    def refresh(self) -> None:
        """Refresh workspace by rebuilding the unified state."""
        from logger import get_logger

        get_logger().info("[workspace] refresh requested - rebuilding unified state")

        # Get configuration
        config = self.get_config()

        # Rebuild unified state
        state = self.get_spade_state()
        state.build_filesystem_tree(self.repo_root, config)
        get_logger().info("[workspace] unified state rebuilt successfully")

    def path(self, filename: str) -> Path:
        """Get path to a file in the .spade directory."""
        return self.spade_dir / filename

    def _create_run_phase0_yaml(self) -> None:
        """Create default run_phase0.yaml configuration file."""
        run_yaml_path = self.spade_dir / "run_phase0.yaml"
        if run_yaml_path.exists():
            return

        # Read default content from template file
        default_content = self._get_default_run_phase0_yaml_content()

        with open(run_yaml_path, "w", encoding="utf-8") as f:
            f.write(default_content)

    def _get_default_run_phase0_yaml_content(self) -> str:
        """Get default run_phase0.yaml content from template file."""
        # Read from default_run_phase0.yaml in the same directory as this file
        default_file = Path(__file__).parent / "default_run_phase0.yaml"

        if not default_file.exists():
            raise FileNotFoundError(f"Default run_phase0.yaml template not found: {default_file}")

        return default_file.read_text(encoding="utf-8")

    def _create_spadeignore(self) -> None:
        """Create default .spadeignore file."""
        spadeignore_path = self.spade_dir / ".spadeignore"
        if spadeignore_path.exists():
            return

        # Read default content from file
        default_content = self._get_default_spadeignore_content()

        with open(spadeignore_path, "w", encoding="utf-8") as f:
            f.write(default_content)

    def _get_default_spadeignore_content(self) -> str:
        """Get default .spadeignore content from file."""
        # Read from default.spadeignore in the same directory as this file
        default_file = Path(__file__).parent / "default.spadeignore"

        if not default_file.exists():
            raise FileNotFoundError(f"Default spadeignore file not found: {default_file}")

        return default_file.read_text(encoding="utf-8")

    def _create_spadeallow(self) -> None:
        """Create empty .spadeallow file."""
        spadeallow_path = self.spade_dir / ".spadeallow"
        if spadeallow_path.exists():
            return

        spadeallow_path.touch()

    def get_config(self) -> RunConfig:
        """Get configuration from run_phase0.yaml."""
        config_path = self.path("run_phase0.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        return load_yaml(config_path, RunConfig)

    def load_config(self) -> RunConfig:
        """Load configuration from run_phase0.yaml."""
        config_path = self.path("run_phase0.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        return load_yaml(config_path, RunConfig)

    def open_scaffold_file(self, filename: str, mode: str = "r"):
        """Open a file in the scaffold directory."""
        scaffold_dir = self.spade_dir / "scaffold"
        scaffold_dir.mkdir(parents=True, exist_ok=True)
        return open(scaffold_dir / filename, mode, encoding="utf-8")

    def append_telemetry(self, telemetry_data: dict) -> None:
        """Append telemetry data to telemetry.jsonl."""
        telemetry_path = self.spade_dir / "telemetry.jsonl"
        import json

        with telemetry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(telemetry_data, ensure_ascii=False) + "\n")

    def write_summary(self, summary_data: dict) -> None:
        """Write summary data to summary.json."""
        summary_path = self.spade_dir / "summary.json"
        import json

        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

    def ensure_analysis_root(self) -> None:
        """Ensure analysis root directory exists."""
        analysis_dir = self.spade_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

    def ensure_checkpoint_dir(self) -> None:
        """Ensure checkpoint directory exists."""
        checkpoint_dir = self.spade_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def write_checkpoint(self, checkpoint_data: dict) -> None:
        """Write checkpoint data to phase0_last_step.json."""
        self.ensure_checkpoint_dir()
        checkpoint_path = self.spade_dir / "checkpoints" / "phase0_last_step.json"
        import json

        with checkpoint_path.open("w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

    def get_analysis_dir(self, rel: str) -> Path:
        """Get analysis directory path for a relative path."""
        return self.spade_dir / "analysis" / (rel if rel != "." else ".")

    def get_state_path(self) -> Path:
        """Get spade.db path."""
        return self.spade_dir / "spade.db"

    def get_spade_state(self) -> SpadeState:
        """Get the SpadeState instance for this workspace."""
        if self._spade_state is None:
            self._spade_state = SpadeState(self.get_state_path())
        return self._spade_state

    def get_real_path(self, rel: str) -> str:
        """Get real (absolute) path for a relative path."""
        return (self.repo_root / ("" if rel == "." else rel)).resolve().as_posix()
