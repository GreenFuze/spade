#!/usr/bin/env python3
"""
SPADE CLI - Main entry point
Command-line interface for SPADE workspace management and analysis
"""

import signal
import sys
from pathlib import Path
from typing import Optional

import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger, init_logger
from workspace import Workspace


def signal_handler(signum, frame):
    """Handle CTRL+C for hard shutdown."""
    print("\nCTRL+C received. Hard shutdown.")
    sys.exit(1)


# Register signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)


@click.group()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.pass_context
def cli(ctx, repo_path: Path):
    """SPADE - Software Program Architecture Discovery Engine"""
    ctx.ensure_object(dict)
    ctx.obj["repo_path"] = repo_path
    ctx.obj["break_lock"] = False


@cli.command()
@click.pass_context
def init_workspace(ctx):
    """Create .spade workspace directory and exit"""
    repo_path = ctx.obj["repo_path"]
    try:
        workspace = Workspace(repo_path)
        workspace.create()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def clean(ctx):
    """Clean .spade workspace directory and exit"""
    repo_path = ctx.obj["repo_path"]
    try:
        workspace = Workspace(repo_path)
        workspace.clean()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def refresh(ctx):
    """Rebuild snapshot and reset worklist (start from root)"""
    repo_path = ctx.obj["repo_path"]

    # Initialize logger for refresh command
    init_logger(repo_path)

    try:
        workspace = Workspace(repo_path)
        workspace.refresh()
    except Exception as e:
        get_logger().error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--break-lock", is_flag=True, help="Override existing phase0 lock (force run if previous crashed)")
@click.pass_context
def phase0(ctx, break_lock: bool):
    """Run Phase-0 analysis"""
    repo_path = ctx.obj["repo_path"]

    # Initialize logger for phase0 command
    init_logger(repo_path)

    try:
        workspace = Workspace(repo_path)

        # Import phase0-related modules
        from phase0_agent import Phase0Agent
        from lock import acquire_lock

        with acquire_lock(workspace.repo_root, break_lock=break_lock):
            # Run phase0
            agent = Phase0Agent(workspace)
            agent.run()

    except Exception as e:
        get_logger().error(f"[cli] phase0 failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("phase", type=str)
@click.argument("relpath", type=str, default=".")
@click.pass_context
def inspect(ctx, phase: str, relpath: str):
    """Preview context for a phase and path"""
    repo_path = ctx.obj["repo_path"]

    # Initialize logger for inspect command
    init_logger(repo_path)

    # Currently only phase0 is supported
    if phase != "phase0":
        click.echo(f"Error: Unsupported phase '{phase}'. Only 'phase0' is currently supported.", err=True)
        sys.exit(2)

    try:
        workspace = Workspace(repo_path)

        # Check if state exists and entry exists
        state = workspace.get_spade_state()

        try:
            entry = state.get_entry(relpath)
        except Exception:
            get_logger().error(f"[inspect] missing entry for {relpath}. Run: phase0 --refresh {workspace.repo_root}")
            sys.exit(2)

        # Context building is temporarily disabled (LLM interactions disabled)
        ctx = {"message": "Context building temporarily disabled"}

        # Write artifacts
        if relpath == ".":
            out_dir = workspace.repo_root / ".spade/inspect"
        else:
            out_dir = workspace.repo_root / ".spade/inspect" / relpath

        out_dir.mkdir(parents=True, exist_ok=True)

        # Write context.json
        context_path = out_dir / "context.json"
        context_path.write_text(str(ctx), encoding="utf-8")

        # Build preview.md
        preview_md = ["# Phase-0 Inspect Preview", f"- repo: {workspace.repo_root.name}", f"- path: `{relpath}`", "", "Context building is temporarily disabled (LLM interactions disabled)"]

        preview_path = out_dir / "preview.md"
        preview_path.write_text("\n".join(preview_md) + "\n", encoding="utf-8")

        # Echo a short summary to STDOUT
        click.echo("Context building temporarily disabled (LLM interactions disabled)")
        get_logger().info(f"[inspect] wrote {out_dir}/context.json and preview.md")

    except Exception as e:
        get_logger().error(f"[cli] inspect failed: {e}")
        sys.exit(1)


def main():
    """Main entry point for SPADE CLI."""
    cli()


if __name__ == "__main__":
    main()
