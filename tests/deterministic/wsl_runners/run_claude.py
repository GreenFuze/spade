#!/usr/bin/env python3
"""
WSL runner script for Claude agent using claude-agent-sdk.

This script runs in WSL where claude-agent-sdk is installed.
It reads a prompt file and executes Claude, allowing it to create answers.json.
"""

import sys
import anyio
import asyncio
import json
import time
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from validation import validate_answers_file, extract_question_ids_from_prompt
from file_watcher import FileStabilityWatcher


async def run_claude_with_monitoring(prompt: str, cwd: str, timeout: int = 300) -> str:
    """
    Run Claude agent with the given prompt, monitoring for completion signal.

    Args:
        prompt: The prompt to send to Claude
        cwd: Working directory for Claude
        timeout: Maximum seconds to wait (default 300 = 5 minutes)

    Returns:
        Combined text response from Claude

    Raises:
        TimeoutError: If agent doesn't complete within timeout
    """
    options = ClaudeAgentOptions(
        cwd=cwd,
        permission_mode="acceptEdits",  # Allow file operations without asking
        system_prompt="You are a helpful technical assistant analyzing a code repository."
    )

    result = []
    ready_detected = False

    async def _run_agent():
        nonlocal ready_detected
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text = block.text
                        result.append(text)

                        # Check for READY! signal
                        if "READY!" in text:
                            ready_detected = True
                            return

    # Run with timeout
    try:
        await asyncio.wait_for(_run_agent(), timeout=timeout)
    except asyncio.TimeoutError:
        if not ready_detected:
            raise TimeoutError(f"Claude did not complete within {timeout} seconds")

    return "".join(result)


def output_answers_json(working_dir: str) -> bool:
    """
    Read and output answers.json to stdout if it exists.

    Args:
        working_dir: Directory where answers.json should be located

    Returns:
        True if answers.json was found and output, False otherwise
    """
    answers_path = Path(working_dir) / "answers.json"

    if not answers_path.exists():
        return False

    try:
        with open(answers_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)

        # Output the answers.json content as JSON to stdout
        print("\n--- answers.json ---")
        print(json.dumps(answers_data, indent=2))
        print("--- End answers.json ---\n")
        return True

    except Exception as e:
        print(f"[WARNING] Found answers.json but failed to read it: {e}", file=sys.stderr)
        return False


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


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: run_claude.py <prompt_file> <working_directory>", file=sys.stderr)
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

    # Track agent execution timing
    start_time = time.time()
    completion_time = None

    # Setup file watcher for answers.json
    answers_path = f"{working_dir}/answers.json"
    file_watcher = FileStabilityWatcher(answers_path, stability_duration=5.0, check_interval=0.5)

    # Run Claude with monitoring
    try:
        print("[LOG] Starting Claude agent execution...")
        response = anyio.run(run_claude_with_monitoring, prompt, working_dir)
        print("[LOG] Claude execution completed successfully")
        print(f"[LOG] Response length: {len(response)} characters")

        # Check if READY! was in response
        if "READY!" in response:
            print("[LOG] ✓ READY! signal detected in response")
        else:
            print("[LOG] ⚠ READY! signal NOT detected in response")

        # Validate answers file
        print(f"[LOG] Validating answers.json at: {working_dir}/answers.json")
        is_valid, error_msg = validate_answers_file(working_dir, expected_ids)

        if is_valid:
            print("[LOG] ✓ Validation passed: answers.json is complete")
            if error_msg:  # Warnings
                print(f"[LOG]   {error_msg}")

            # Wait for file to be stable (5 seconds of no changes)
            print("[LOG] Waiting for answers.json to stabilize (5 seconds of no changes)...")
            remaining_timeout = max(10, 300 - (time.time() - start_time))
            stable, elapsed = file_watcher.wait_for_stable_file(timeout=remaining_timeout)

            if stable:
                completion_time = time.time() - start_time
                print(f"[LOG] answers.json is stable after {completion_time:.2f} seconds")
                write_timing_metadata(working_dir, completion_time)
            else:
                # File never stabilized but it's valid, use current time
                completion_time = time.time() - start_time
                print(f"[LOG] File didn't stabilize but is valid, using elapsed time: {completion_time:.2f} seconds")
                write_timing_metadata(working_dir, completion_time)

            # Output answers.json content
            output_answers_json(working_dir)

            print("\n--- Agent Response ---")
            print(response)
            print("--- End Response ---\n")
        else:
            print(f"[LOG] ✗ Validation failed: {error_msg}", file=sys.stderr)
            # Still calculate and save timing
            completion_time = time.time() - start_time
            write_timing_metadata(working_dir, completion_time)

            # Still try to output answers.json if it exists (even if incomplete)
            if output_answers_json(working_dir):
                print("[LOG] Note: answers.json was output despite validation failure", file=sys.stderr)
            sys.exit(1)

    except TimeoutError as e:
        print(f"[ERROR] Timeout: {str(e)}", file=sys.stderr)
        completion_time = time.time() - start_time
        write_timing_metadata(working_dir, completion_time)

        # Check if answers file is complete anyway
        print("[LOG] Checking if answers.json is complete despite timeout...", file=sys.stderr)
        is_valid, error_msg = validate_answers_file(working_dir, expected_ids)
        if is_valid:
            print("[LOG] ✓ Despite timeout, answers.json is complete!", file=sys.stderr)
            # Output answers.json content
            output_answers_json(working_dir)
            sys.exit(0)  # Success
        else:
            print(f"[ERROR] Validation failed: {error_msg}", file=sys.stderr)
            # Still try to output answers.json if it exists (even if incomplete)
            if output_answers_json(working_dir):
                print("[LOG] Note: answers.json was output despite being incomplete", file=sys.stderr)
                # Exit with success since we have answers, even if incomplete
                sys.exit(0)
            else:
                print("[ERROR] answers.json not found", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Exception running Claude: {type(e).__name__}: {str(e)}", file=sys.stderr)
        import traceback
        print("[ERROR] Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

        completion_time = time.time() - start_time
        write_timing_metadata(working_dir, completion_time)

        # Check if answers file exists despite the exception
        print("[LOG] Checking if answers.json exists despite exception...", file=sys.stderr)
        is_valid, error_msg = validate_answers_file(working_dir, expected_ids)
        if is_valid:
            print("[LOG] ✓ Despite exception, answers.json is complete!", file=sys.stderr)
            # Output answers.json content
            output_answers_json(working_dir)
            sys.exit(0)  # Success
        else:
            # Still try to output answers.json if it exists (even if incomplete)
            if output_answers_json(working_dir):
                print("[LOG] Note: answers.json was output despite being incomplete", file=sys.stderr)
                # Exit with success since we have answers, even if incomplete
                sys.exit(0)
            else:
                print("[ERROR] answers.json not found", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
