#!/usr/bin/env python3
"""
WSL runner script for Claude agent using claude-agent-sdk.

This script runs in WSL where claude-agent-sdk is installed.
It reads a prompt file and executes Claude, allowing it to create answers.json.
"""

import sys
import anyio
import asyncio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from validation import validate_answers_file, extract_question_ids_from_prompt


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
        else:
            print(f"[LOG] ✗ Validation failed: {error_msg}", file=sys.stderr)
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
            print("[LOG] ✓ Despite timeout, answers.json is complete!", file=sys.stderr)
            sys.exit(0)  # Success
        else:
            print(f"[ERROR] Validation also failed: {error_msg}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Exception running Claude: {type(e).__name__}: {str(e)}", file=sys.stderr)
        import traceback
        print("[ERROR] Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
