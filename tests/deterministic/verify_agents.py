#!/usr/bin/env python3
"""
Verify that CLI agents (claude, cursor, codex) are installed and accessible.

This script tests basic connectivity to each agent before running full evaluations.
"""

import subprocess
import sys


def check_wsl():
    """Check if WSL is available."""
    try:
        result = subprocess.run(
            ["wsl.exe", "-e", "bash", "-c", "echo test"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("[OK] WSL is available")
            return True
        else:
            print("[FAIL] WSL failed:", result.stderr)
            return False
    except Exception as e:
        print(f"[FAIL] WSL check failed: {str(e)}")
        return False


def check_agent(agent_name: str, command: str):
    """
    Check if an agent CLI is installed and accessible.

    Args:
        agent_name: Name of the agent (for display)
        command: Command to test (e.g., "claude --version")
    """
    try:
        result = subprocess.run(
            ["wsl.exe", "-e", "bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"[OK] {agent_name} is available")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[FAIL] {agent_name} failed:")
            print(f"  stdout: {result.stdout.strip()}")
            print(f"  stderr: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print(f"[FAIL] {agent_name} timed out (command may be hanging)")
        return False
    except Exception as e:
        print(f"[FAIL] {agent_name} check failed: {str(e)}")
        return False


def main():
    """Run all verification checks."""
    print("=== Verifying Agent CLI Tools ===\n")

    results = {}

    # Check WSL
    print("1. Checking WSL...")
    results["wsl"] = check_wsl()
    print()

    if not results["wsl"]:
        print("ERROR: WSL is required but not available!")
        return 1

    # Check Claude
    print("2. Checking Claude CLI...")
    results["claude"] = check_agent("Claude", "claude --version")
    print()

    # Check Cursor
    print("3. Checking Cursor CLI...")
    results["cursor"] = check_agent("Cursor", "cursor --version")
    print()

    # Check Codex
    print("4. Checking Codex CLI...")
    results["codex"] = check_agent("Codex", "codex --version")
    print()

    # Summary
    print("=== Summary ===")
    available = sum(1 for k, v in results.items() if v and k != "wsl")
    total = len(results) - 1  # Exclude WSL from count

    print(f"Available agents: {available}/{total}")

    if available == 0:
        print("\nWARNING: No agents are available!")
        print("You may need to install the CLI tools in WSL.")
        return 1
    elif available < total:
        print("\nWARNING: Some agents are not available.")
        print("Evaluations will fail for unavailable agents.")
        return 0
    else:
        print("\nAll agents are available! Ready to run evaluations.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
