#!/usr/bin/env python3
"""
WSL runner script for Cursor agent using cursor-agent CLI.

This script runs in WSL where cursor-agent CLI is installed.
It reads a prompt file and executes cursor-agent by writing the prompt to stdin,
then polling for answers.json completion.

IMPORTANT: cursor-agent requires the working directory to be trusted.
This script expects to be run in a fixed workspace directory
(tests/deterministic/wsl_runners/_cursor_workspace) that has been trusted once manually.

Usage:
    The prompt is written directly to cursor-agent's stdin.
"""

import os
import select
import subprocess
import sys
import time
import json
from pathlib import Path
from validation import validate_answers_file, extract_question_ids_from_prompt
from file_watcher import FileStabilityWatcher


def ensure_venv_and_cursor_agent():
    """
    Ensure shared venv exists and cursor-agent is installed.

    Returns:
        Tuple of (venv_path, cursor_agent_path)

    Raises:
        RuntimeError: If venv creation or cursor-agent installation fails
    """
    venv_path = os.path.expanduser("~/.cursor_agent_venv")
    cursor_agent_path = os.path.expanduser("~/.local/bin/cursor-agent")

    # Check if venv exists
    if not os.path.exists(venv_path):
        print(f"[LOG] Creating persistent venv at {venv_path}...")
        try:
            subprocess.run(['python3', '-m', 'venv', venv_path], check=True, capture_output=True)
            print(f"[LOG] Venv created successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create venv: {e.stderr.decode()}")
    else:
        print(f"[LOG] Using existing venv at {venv_path}")

    # Check if cursor-agent is available at the expected absolute path
    if not os.path.exists(cursor_agent_path):
        print(f"[LOG] cursor-agent not found at {cursor_agent_path}, installing...")
        install_cmd = "curl https://cursor.com/install -fsSL | bash"
        try:
            subprocess.run(['bash', '-c', install_cmd], check=True, capture_output=True, text=True)
            print("[LOG] cursor-agent installed successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install cursor-agent: {e.stderr}")
    else:
        print(f"[LOG] cursor-agent found at: {cursor_agent_path}")

    return venv_path, cursor_agent_path


def write_timing_metadata(working_dir: str, completion_time: float) -> None:
    """
    Write timing metadata to answers_metadata.json.

    Args:
        working_dir: Directory where metadata file should be written
        completion_time: Agent completion time in seconds
    """
    metadata_path = Path(working_dir) / "answers_metadata.json"
    metadata = {
        "agent_completion_time_seconds": round(completion_time, 2)
    }

    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"[LOG] Wrote timing metadata: {completion_time:.2f} seconds")
    except Exception as e:
        print(f"[WARNING] Failed to write timing metadata: {e}", file=sys.stderr)


def run_cursor_with_polling(prompt: str, working_dir: str, expected_ids: list, cursor_agent_path: str, timeout: int = 300) -> str:
    """
    Run cursor-agent CLI with the given prompt, polling for completion.

    Args:
        prompt: The prompt to send to cursor-agent
        working_dir: Working directory for cursor-agent
        expected_ids: List of expected question IDs to validate
        cursor_agent_path: Absolute path to cursor-agent executable
        timeout: Maximum seconds to wait (default 300 = 5 minutes)

    Returns:
        Combined stdout/stderr from cursor-agent

    Raises:
        TimeoutError: If answers.json not complete within timeout
        RuntimeError: If cursor-agent fails to start
    """
    print(f"[LOG] Starting cursor-agent")
    print(f"[LOG] Using cursor-agent at: {cursor_agent_path}")
    print(f"[LOG] Working directory: {working_dir}")

    try:
        # Start cursor-agent with stdin pipe
        # cursor-agent reads prompt from stdin, just like: echo "prompt" | cursor-agent
        proc = subprocess.Popen(
            [cursor_agent_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            text=True
        )

        # Write prompt to stdin and close it (closing tells cursor-agent input is complete)
        proc.stdin.write(prompt)
        proc.stdin.close()

        print("[LOG] cursor-agent started, prompt sent to stdin")
    except Exception as e:
        raise RuntimeError(f"Failed to start cursor-agent: {e}")

    # Poll for answers.json completion with file stability checking
    start_time = time.time()
    poll_interval = 0.5  # Check every 0.5 seconds
    stability_duration = 5.0  # File must be stable for 5 seconds
    answers_path = os.path.join(working_dir, "answers.json")
    file_watcher = FileStabilityWatcher(answers_path, stability_duration=stability_duration, check_interval=poll_interval)

    print(f"[LOG] Polling for answers.json every {poll_interval} seconds (timeout: {timeout}s)...")
    print(f"[LOG] File must be stable for {stability_duration} seconds before considered complete")

    last_validation_status = None
    stable_file_detected_at = None

    while True:
        elapsed = time.time() - start_time

        # Check if timeout exceeded
        if elapsed > timeout:
            print(f"[LOG] Timeout reached ({timeout}s), terminating cursor-agent...")

            stdout = ""
            stderr = ""

            try:
                proc.terminate()
                proc.wait(timeout=5)
                stdout = proc.stdout.read() if proc.stdout else ""
                stderr = proc.stderr.read() if proc.stderr else ""
            except subprocess.TimeoutExpired:
                print("[LOG] Process didn't terminate gracefully, killing...")
                proc.kill()
                try:
                    proc.wait(timeout=2)
                    stdout = proc.stdout.read() if proc.stdout else ""
                    stderr = proc.stderr.read() if proc.stderr else ""
                except Exception as e:
                    print(f"[LOG] Warning: Failed to read output after kill: {e}")
            except Exception as e:
                print(f"[LOG] Warning: Error during termination: {e}")

            print(f"[LOG] Captured output from cursor-agent:")
            if stdout:
                print(f"[CURSOR-AGENT-STDOUT] {stdout}")
            if stderr:
                print(f"[CURSOR-AGENT-STDERR] {stderr}", file=sys.stderr)

            # Flush output before raising exception
            sys.stdout.flush()
            sys.stderr.flush()

            raise TimeoutError(f"cursor-agent did not complete within {timeout} seconds")

        # Check if answers.json is valid
        if os.path.exists(answers_path):
            is_valid, error_msg = validate_answers_file(working_dir, expected_ids)

            if is_valid and last_validation_status != "valid":
                print(f"[LOG] answers.json is valid, waiting for file stability...")
                last_validation_status = "valid"

            # Check file stability
            stability_time = file_watcher.get_file_stability_time()
            if is_valid and stability_time is not None and stability_time >= stability_duration:
                if stable_file_detected_at is None:
                    stable_file_detected_at = time.time()
                    completion_time = stable_file_detected_at - start_time
                    print(f"[LOG] SUCCESS: answers.json is stable after {completion_time:.2f} seconds!")
                    write_timing_metadata(working_dir, completion_time)

                print("[LOG] Terminating cursor-agent...")
                stdout = ""
                stderr = ""

                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    stdout = proc.stdout.read() if proc.stdout else ""
                    stderr = proc.stderr.read() if proc.stderr else ""
                except subprocess.TimeoutExpired:
                    print("[LOG] Process didn't terminate gracefully, killing...")
                    proc.kill()
                    try:
                        proc.wait(timeout=2)
                        stdout = proc.stdout.read() if proc.stdout else ""
                        stderr = proc.stderr.read() if proc.stderr else ""
                    except Exception as e:
                        print(f"[LOG] Warning: Failed to read output after kill: {e}")
                except Exception as e:
                    # Log termination errors but don't fail - answers are valid!
                    print(f"[LOG] Warning: Error during cursor-agent termination: {e}")

                print(f"[LOG] Captured output from cursor-agent:")
                if stdout:
                    print(f"[CURSOR-AGENT-STDOUT] {stdout}")
                if stderr:
                    print(f"[CURSOR-AGENT-STDERR] {stderr}", file=sys.stderr)

                return f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n\nREADY!"
            elif not is_valid and last_validation_status != "invalid":
                print(f"[LOG] answers.json exists but incomplete: {error_msg}")
                last_validation_status = "invalid"
        else:
            if last_validation_status is not None:
                last_validation_status = None

        # Check if process exited
        if proc.poll() is not None:
            exit_code = proc.returncode

            # Read remaining output
            stdout = ""
            stderr = ""
            try:
                stdout = proc.stdout.read() if proc.stdout else ""
                stderr = proc.stderr.read() if proc.stderr else ""
            except Exception as e:
                print(f"[LOG] Warning: Failed to read output from exited process: {e}")

            print(f"[LOG] cursor-agent exited with code {exit_code}")

            # If process exited successfully (code 0) and we're waiting for stability, continue waiting
            if exit_code == 0 and last_validation_status == "valid":
                print(f"[LOG] Process exited successfully, continuing to wait for file stability...")
                # Don't raise error, continue polling loop
            else:
                # Process died with error or answers incomplete
                completion_time = time.time() - start_time
                write_timing_metadata(working_dir, completion_time)

                print(f"[LOG] cursor-agent exited unexpectedly:")
                if stdout:
                    print(f"[CURSOR-AGENT-STDOUT] {stdout}")
                if stderr:
                    print(f"[CURSOR-AGENT-STDERR] {stderr}", file=sys.stderr)

                # Flush output before raising exception
                sys.stdout.flush()
                sys.stderr.flush()

                raise RuntimeError(
                    f"cursor-agent exited with code {exit_code} before answers were stable\n"
                    f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
                )

        # Sleep before next check
        time.sleep(poll_interval)


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: run_cursor.py <prompt_file> <working_directory>", file=sys.stderr)
        sys.exit(1)

    prompt_file = sys.argv[1]
    working_dir = sys.argv[2]

    # Read prompt from file
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt = f.read()

    # Extract expected question IDs from prompt
    expected_ids = extract_question_ids_from_prompt(prompt)
    print(f"[LOG] Working directory: {working_dir}")
    print(f"[LOG] Prompt file: {prompt_file}")
    print(f"[LOG] Prompt length: {len(prompt)} characters")
    print(f"[LOG] Expecting answers for {len(expected_ids)} questions: {expected_ids}")

    # Ensure cursor-agent is available
    print("[LOG] Checking cursor-agent...")
    venv_path, cursor_agent_path = ensure_venv_and_cursor_agent()

    # Run cursor-agent with polling
    try:
        response = run_cursor_with_polling(prompt, working_dir, expected_ids, cursor_agent_path)
        print("[LOG] Cursor execution completed successfully")

        # Check if READY! was in response (should be added by our code above)
        if "READY!" in response:
            print("[LOG] READY! signal detected in response")

        # Final validation
        print(f"[LOG] Final validation of answers.json...")
        is_valid, error_msg = validate_answers_file(working_dir, expected_ids)

        if is_valid:
            print("[LOG] Validation passed: answers.json is complete")
        else:
            print(f"[LOG] Validation failed: {error_msg}", file=sys.stderr)
            sys.exit(1)

        print("\n--- Agent Response ---")
        print(response)
        print("--- End Response ---\n")

    except TimeoutError as e:
        print(f"[ERROR] Timeout: {str(e)}", file=sys.stderr)
        # Check if answers file is complete anyway
        print("[LOG] Checking if answers.json is complete despite timeout...", file=sys.stderr)
        is_valid, error_msg = validate_answers_file(working_dir, expected_ids)
        if is_valid:
            print("[LOG] Despite timeout, answers.json is complete!", file=sys.stderr)
            sys.exit(0)  # Success
        else:
            print(f"[ERROR] Validation also failed: {error_msg}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Exception running cursor-agent: {type(e).__name__}: {str(e)}", file=sys.stderr)
        import traceback
        print("[ERROR] Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
