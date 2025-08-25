#!/usr/bin/env python3
"""
SPADE - Software Program Architecture Discovery Engine
Phase 0: Directory-based scaffold inference
"""

import signal
import sys
import os
import shutil
from pathlib import Path
from phase0 import Phase0Agent


def signal_handler(signum, frame):
    """Handle CTRL+C for hard shutdown."""
    print("\nCTRL+C received. Hard shutdown.")
    sys.exit(1)


# Register signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)


def print_usage():
    """Print usage information and exit."""
    print("Usage: python main.py <repo_path> [options]")
    print("Options:")
    print("  --model MODEL_ID     LLM model to use (default: gpt-5-nano)")
    print("  --max_depth N        Maximum directory scan depth (default: 3, 0 = unlimited)")
    print("  --max_entries N      Maximum entries per directory (default: 40, 0 = unlimited)")
    print("  --fresh              Delete .spade directory before running")
    print("  --help               Show this help message and exit")
    sys.exit(0)


def parse_arguments() -> tuple[Path, str | None, int | None, int | None, bool]:
    """Parse command line arguments and return parsed values."""
    if len(sys.argv) < 2:
        print_usage()
    
    # Check for --help before parsing repo_path
    if sys.argv[1] == "--help":
        print_usage()
    
    repo_path = Path(sys.argv[1])
    model_id = None
    max_depth = None
    max_entries = None
    fresh_run = False
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--help":
            print_usage()
        elif arg == "--model":
            if i + 1 >= len(sys.argv):
                print("Error: --model requires a value")
                sys.exit(2)
            model_id = sys.argv[i + 1]
            i += 2
        elif arg == "--max_depth":
            if i + 1 >= len(sys.argv):
                print("Error: --max_depth requires a value")
                sys.exit(2)
            try:
                max_depth = int(sys.argv[i + 1])
                if max_depth < 0:
                    print("Error: --max_depth must be >= 0 (0 = unlimited)")
                    sys.exit(2)
            except ValueError:
                print("Error: --max_depth requires an integer value")
                sys.exit(2)
            i += 2
        elif arg == "--max_entries":
            if i + 1 >= len(sys.argv):
                print("Error: --max_entries requires a value")
                sys.exit(2)
            try:
                max_entries = int(sys.argv[i + 1])
                if max_entries < 0:
                    print("Error: --max_entries must be >= 0 (0 = unlimited)")
                    sys.exit(2)
            except ValueError:
                print("Error: --max_entries requires an integer value")
                sys.exit(2)
            i += 2
        elif arg == "--fresh":
            fresh_run = True
            i += 1
        else:
            print(f"Error: Unknown option: {arg}")
            sys.exit(2)
    
    return repo_path, model_id, max_depth, max_entries, fresh_run


def main():
    """Main entry point for SPADE Phase 0."""
    repo_path, model_id, max_depth, max_entries, fresh_run = parse_arguments()
    
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"Error: Invalid repository path: {repo_path}")
        sys.exit(2)
    
    # Handle --fresh flag
    if fresh_run:
        spade_dir = repo_path / ".spade"
        if spade_dir.exists():
            print(f"Deleting existing .spade directory: {spade_dir}... ", end='')
            shutil.rmtree(spade_dir)
            print('Done')
    
    try:
        # Convert None values to defaults for the agent
        agent_model_id = model_id if model_id is not None else "gpt-5-nano"
        agent_max_depth = max_depth if max_depth is not None else 3
        agent_max_entries = max_entries if max_entries is not None else 40
        
        # Initialize agent AFTER potential --fresh deletion to avoid logger file handle conflicts
        agent = Phase0Agent(repo_path, agent_model_id, agent_max_depth, agent_max_entries)
        agent.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
