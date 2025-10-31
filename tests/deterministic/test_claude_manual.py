#!/usr/bin/env python3
"""
Manual test for Claude agent executor with a simple prompt.
"""

import json
import sys
from agent_executors import ClaudeAgentExecutor


def main():
    """Test Claude with a simple prompt."""
    executor = ClaudeAgentExecutor()

    # Simple test prompt
    prompt = """Please analyze this repository and create a file named "answers.json" in the root directory.

The file should contain a JSON array with one answer:
[
  {
    "id": 1,
    "answer": "test successful"
  }
]

Make sure to write the file exactly as specified."""

    # Repository path (use raw string to avoid escape sequence issues)
    repo_path = r"C:\src\github.com\GreenFuze\spade\tests\test_repos\cmake\cmake_hello_world"

    print("Testing Claude agent executor...")
    print(f"Repository: {repo_path}")
    print(f"Prompt length: {len(prompt)} characters")
    print()

    try:
        result = executor.execute(prompt, repo_path)

        print("Execution completed!")
        print(f"Result type: {type(result)}")
        print(f"Result content:")
        print(json.dumps(result, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
