"""
SPADE CLI - Main entry point
Command-line interface for SPADE workspace management and analysis
"""

import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from workspace import Workspace
from logger import get_logger


def signal_handler(signum, frame):
    """Handle CTRL+C for hard shutdown."""
    print("\nCTRL+C received. Hard shutdown.")
    sys.exit(1)


# Register signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)


def print_usage():
    """Print usage information and exit."""
    print("Usage: python -m cli.main <repo_path> [options]")
    print("Commands:")
    print("  --init-workspace    Initialize .spade workspace directory and exit")
    print("  --clean             Clean .spade workspace directory and exit")
    print("  phase0 [options]    Run Phase-0 analysis")
    print("  phase0 inspect <relpath>  Preview Phase-0 context for a path")
    print("")
    print("Phase-0 options:")
    print("  --refresh           Rebuild snapshot and reset worklist (start from root)")
    print("  --break-lock        Override existing phase0 lock")
    print("  --help              Show this help message and exit")
    sys.exit(0)


def parse_arguments() -> tuple[Path, str, list[str]]:
    """Parse command line arguments and return parsed values."""
    if len(sys.argv) < 2:
        print_usage()
    
    # Check for --help before parsing repo_path
    if sys.argv[1] == "--help":
        print_usage()
    
    repo_path = Path(sys.argv[1])
    command = ""
    args = []
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--help":
            print_usage()
        elif arg == "--init-workspace":
            command = "init-workspace"
            i += 1
        elif arg == "--clean":
            command = "clean"
            i += 1
        elif arg == "phase0":
            command = "phase0"
            i += 1
            # Check for inspect subcommand
            if i < len(sys.argv) and sys.argv[i] == "inspect":
                command = "phase0-inspect"
                i += 1
                # Collect remaining arguments for inspect
                while i < len(sys.argv):
                    args.append(sys.argv[i])
                    i += 1
                break
            else:
                # Collect remaining arguments for phase0
                while i < len(sys.argv):
                    args.append(sys.argv[i])
                    i += 1
                break
        else:
            print(f"Error: Unknown command: {arg}")
            sys.exit(2)
    
    return repo_path, command, args


def handle_phase0(repo_path: Path, args: list[str]):
    """Handle phase0 command with refresh functionality."""
    logger = get_logger()
    
    # Parse phase0 arguments
    refresh = False
    break_lock = False
    for arg in args:
        if arg == "--refresh":
            refresh = True
        elif arg == "--break-lock":
            break_lock = True
        elif arg == "--help":
            print_usage()
        else:
            print(f"Error: Unknown phase0 option: {arg}")
            sys.exit(2)
    
    try:
        # Import phase0-related modules
        from snapshot import build_snapshot, enrich_markers_and_samples, compute_deterministic_scoring
        from worklist import WorklistStore
        from phase0 import run_phase0
        from schemas import RunConfig
        import json
        
        # Load configuration
        cfg_path = repo_path / ".spade/run.json"
        if not cfg_path.exists():
            logger.error("[cli] .spade/run.json missing. Run --init-workspace first.")
            sys.exit(2)
        
        cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
        
        # Initialize logger for the repository
        from logger import init_logger
        init_logger(repo_path)
        
        # Acquire lock for Phase-0 run
        from lock import acquire_lock
        with acquire_lock(repo_path, break_lock=break_lock):
            if refresh:
                logger.info("[cli] refresh requested - rebuilding snapshot and resetting worklist")
                
                # Build snapshot (existing)
                build_snapshot(repo_path, cfg)
                
                # Enrich markers (existing)
                enrich_markers_and_samples(repo_path, cfg)
                
                # Compute scoring (existing)
                compute_deterministic_scoring(repo_path, cfg)
                
                # Reset worklist
                wl = WorklistStore(repo_path)
                wl.reset()
                logger.info("[cli] worklist reset for new traversal (queue=['.'], visited cleared)")
            
            # TODO: Add learning step here when transport is available
            # For now, we'll use a dummy transport for testing
            from dev.dummy_transport import valid_dummy_transport
            
            # Run phase0
            run_phase0(repo_path, valid_dummy_transport)
        
    except Exception as e:
        logger.error(f"[cli] phase0 failed: {e}")
        sys.exit(1)


def handle_phase0_inspect(repo_path: Path, args: list[str]):
    """Handle phase0 inspect command to preview context for a path."""
    logger = get_logger()
    
    # Parse inspect arguments
    if len(args) == 0:
        relpath = "."
    elif len(args) == 1:
        relpath = args[0]
    else:
        print(f"Error: Too many arguments for inspect command: {args}")
        sys.exit(2)
    
    try:
        # Import required modules
        from context import build_phase0_context, pretty_json, render_context_preview
        from schemas import RunConfig
        import json
        
        # Ensure run.json exists
        cfg_path = repo_path / ".spade/run.json"
        if not cfg_path.exists():
            logger.error("[inspect] .spade/run.json missing. Run --init-workspace first.")
            sys.exit(2)
        
        cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
        
        # Initialize logger for the repository
        from logger import init_logger
        init_logger(repo_path)
        
        # Ensure snapshot for path exists
        if relpath == ".":
            dm_path = repo_path / ".spade/snapshot/dirmeta.json"
        else:
            dm_path = repo_path / ".spade/snapshot" / relpath / "dirmeta.json"
        
        if not dm_path.exists():
            logger.error(f"[inspect] missing dirmeta for {relpath}. Run: phase0 --refresh {repo_path}")
            sys.exit(2)
        
        # Build context with caps
        ctx = build_phase0_context(repo_path, relpath, cfg)
        
        # Write artifacts
        if relpath == ".":
            out_dir = repo_path / ".spade/inspect"
        else:
            out_dir = repo_path / ".spade/inspect" / relpath
        
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Write context.json
        context_path = out_dir / "context.json"
        context_path.write_text(pretty_json(ctx), encoding="utf-8")
        
        # Build preview.md
        preview_md = [
            "# Phase-0 Inspect Preview",
            f"- repo: {repo_path.name}",
            f"- path: `{relpath}`",
            ""
        ]
        preview_md.append("```")
        preview_md.append(render_context_preview(ctx))
        preview_md.append("```")
        
        preview_path = out_dir / "preview.md"
        preview_path.write_text("\n".join(preview_md) + "\n", encoding="utf-8")
        
        # Echo a short summary to STDOUT
        print(render_context_preview(ctx, width=120))
        logger.info(f"[inspect] wrote {out_dir}/context.json and preview.md")
        
    except Exception as e:
        logger.error(f"[cli] phase0 inspect failed: {e}")
        sys.exit(1)


def main():
    """Main entry point for SPADE CLI."""
    repo_path, command, args = parse_arguments()
    
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"Error: Invalid repository path: {repo_path}")
        sys.exit(2)
    
    try:
        # Handle workspace management commands
        if command == "init-workspace":
            Workspace.init(repo_path)
            sys.exit(0)
        
        if command == "clean":
            Workspace.clean(repo_path)
            sys.exit(0)
        
        if command == "phase0":
            handle_phase0(repo_path, args)
            sys.exit(0)
        
        if command == "phase0-inspect":
            handle_phase0_inspect(repo_path, args)
            sys.exit(0)
        
        # No command specified
        print("Error: No command specified")
        print_usage()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
