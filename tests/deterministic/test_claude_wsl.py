#!/usr/bin/env python3
"""
Simple WSL connectivity test for Claude agent.

This script verifies we can communicate with claude-agent-sdk in WSL.
"""

import os
import subprocess
import sys
import tempfile
import shutil


def convert_to_wsl_path(win_path: str) -> str:
    """Convert Windows path to WSL path."""
    win_path = os.path.normpath(win_path)
    wsl_path = win_path.replace('\\', '/')

    if len(wsl_path) >= 2 and wsl_path[1] == ':':
        drive_letter = wsl_path[0].lower()
        wsl_path = f"/mnt/{drive_letter}{wsl_path[2:]}"

    return wsl_path


def main():
    """Run WSL connectivity test."""
    print("=== Claude WSL Connectivity Test ===\n")

    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="claude_wsl_test_")
    print(f"1. Created test directory: {test_dir}")

    try:
        # Write test prompt
        prompt = """Please create a file named "test_output.txt" in the current directory.
Write the text "Communication successful!" to this file.

This is a connectivity test to verify the agent can write files."""

        prompt_file = os.path.join(test_dir, "test_prompt.txt")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"2. Created prompt file: {prompt_file}")

        # Get runner script path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        runner_script = os.path.join(script_dir, "wsl_runners", "run_claude.py")

        if not os.path.exists(runner_script):
            print(f"ERROR: Runner script not found: {runner_script}")
            return 1

        print(f"3. Found runner script: {runner_script}")

        # Convert paths to WSL format
        wsl_prompt = convert_to_wsl_path(prompt_file)
        wsl_test_dir = convert_to_wsl_path(test_dir)
        wsl_runner = convert_to_wsl_path(runner_script)

        print(f"4. Converted to WSL paths:")
        print(f"   Prompt: {wsl_prompt}")
        print(f"   Work dir: {wsl_test_dir}")
        print(f"   Runner: {wsl_runner}")

        # Build WSL command
        command = f'python3 "{wsl_runner}" "{wsl_prompt}" "{wsl_test_dir}"'
        wsl_command = ["wsl.exe", "-e", "bash", "-c", command]

        print(f"\n5. Executing Claude agent in WSL...")
        print(f"   Command: {command}")
        print()

        # Execute
        result = subprocess.run(
            wsl_command,
            capture_output=True,
            text=True,
            timeout=120
        )

        print("6. Claude execution output:")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        if result.stderr:
            print(f"   stderr: {result.stderr}")
        print(f"   return code: {result.returncode}")

        # Check if output file was created
        output_file = os.path.join(test_dir, "test_output.txt")

        print(f"\n7. Checking for output file: {output_file}")

        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"   [SUCCESS] File exists!")
            print(f"   Content: {content}")

            if "Communication successful" in content:
                print("\n=== TEST PASSED ===")
                print("Claude agent communication via WSL is working!")
                return 0
            else:
                print("\n=== TEST FAILED ===")
                print("File created but content is unexpected")
                return 1
        else:
            print(f"   [FAILED] File not created")
            print("\n=== TEST FAILED ===")
            print("Claude agent did not create the output file")
            return 1

    except subprocess.TimeoutExpired:
        print("\n=== TEST FAILED ===")
        print("Claude agent execution timed out")
        return 1

    except Exception as e:
        print(f"\n=== TEST FAILED ===")
        print(f"Error: {str(e)}")
        return 1

    finally:
        # Cleanup
        print(f"\n8. Cleaning up test directory...")
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
