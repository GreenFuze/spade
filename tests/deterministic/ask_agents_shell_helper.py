#!/usr/bin/env python3
"""
Shell helper for ask_agents.sh interactive execution.

Provides utility functions for prompt generation, timing injection, and repo listing.
"""

import json
import os
import sys
from glob import glob
from pathlib import Path
from typing import Dict, List, Any

# Import REPOS from config.py
sys.path.insert(0, str(Path(__file__).parent / "summary_analysis"))
from config import REPOS


def find_ground_truth_file(deterministic_path: str) -> str:
    """
    Find exactly one *_ground_truth.json file in the directory.

    Args:
        deterministic_path: Path to search for ground truth file

    Returns:
        Path to the ground truth file

    Raises:
        FileNotFoundError: If no ground truth file found
        ValueError: If multiple ground truth files found
    """
    pattern = os.path.join(deterministic_path, "*_ground_truth.json")
    matches = glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(f"No ground truth file found in: {deterministic_path}")

    if len(matches) > 1:
        raise ValueError(f"Multiple ground truth files found in {deterministic_path}: {matches}")

    return matches[0]


def load_evaluation_questions(deterministic_path: str) -> Dict[str, Any]:
    """
    Load evaluation_questions.json file.

    Args:
        deterministic_path: Path containing evaluation_questions.json

    Returns:
        Parsed JSON dictionary

    Raises:
        FileNotFoundError: If evaluation_questions.json not found
        json.JSONDecodeError: If JSON is invalid
    """
    questions_file = os.path.join(deterministic_path, "evaluation_questions.json")

    if not os.path.exists(questions_file):
        raise FileNotFoundError(f"evaluation_questions.json not found at: {questions_file}")

    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)

    return questions_data


def load_ground_truth(ground_truth_path: str) -> Dict[str, Any]:
    """
    Load ground truth JSON file.

    Args:
        ground_truth_path: Path to ground truth JSON file

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth_data = json.load(f)

    return ground_truth_data


def build_prompt_without_rig(questions: List[Dict[str, Any]]) -> str:
    """
    Build prompt for agents WITHOUT RIG context.

    Args:
        questions: List of question dictionaries

    Returns:
        Formatted prompt string
    """
    prompt = """You are an expert at analyzing code repositories and build systems.

Please answer the following questions about this repository. Analyze the repository structure, build files, and source code to provide accurate answers.

When answering questions, you should understand these common build system terms:

- **Components**: Build components (executables, libraries, runnable artifacts like JARs or Python files). Each component generates an artifact from source files, or is the source files themselves if interpreted.
- **Aggregators**: Build steps that don't generate artifacts but invoke or depend on other build steps (e.g., "build-all" targets).
- **Runners**: Execution or test runners that don't generate artifacts.
- **Tests**: Test suites that use a component for testing or a runner that executes the test.

IMPORTANT: Write your answers to a file named "answers.json" in the root of this repository.

The answers.json file must be a JSON array with this exact format:
[
  {
    "id": 1,
    "answer": "your answer here"
  },
  {
    "id": 2,
    "answer": ["list", "of", "items"]
  }
]

For answers that are lists, use JSON arrays. For yes/no questions, answer with "yes" or "no".

Questions:

"""

    # Add each question
    for q in questions:
        prompt += f"{q['id']}. {q['question']}\n"

    prompt += "\n\nRemember: Write your answers to answers.json in the repository root!"
    prompt += "\n\nWhen you have finished writing all answers, output EXACTLY this line with nothing else:\nREADY!"

    return prompt


def build_prompt_with_rig(questions: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> str:
    """
    Build prompt for agents WITH RIG context.

    Args:
        questions: List of question dictionaries
        ground_truth: Ground truth JSON data (RIG)

    Returns:
        Formatted prompt string
    """
    # Convert ground truth to pretty JSON string
    rig_json = json.dumps(ground_truth, indent=2)

    prompt = f"""You are an expert at analyzing code repositories and build systems.

You have been provided with structured metadata about this repository in the following JSON:

In the following JSON, you'll find these entity types:

- **Components**: Build components (executables, libraries, runnable artifacts like JARs or Python files). Each component must generate an artifact from source files, or be the source files themselves if interpreted.
- **Aggregators**: Build steps that don't generate artifacts but invoke or depend on other build steps.
- **Runners**: Execution or test runners that don't generate artifacts.
- **Test Definitions**: Tests that contain a component used for testing or a runner that executes the test.

```json
{rig_json}
```

Please answer the following questions about this repository using the metadata above and by analyzing the repository files.

IMPORTANT: Write your answers to a file named "answers.json" in the root of this repository.

The answers.json file must be a JSON array with this exact format:
[
  {{
    "id": 1,
    "answer": "your answer here"
  }},
  {{
    "id": 2,
    "answer": ["list", "of", "items"]
  }}
]

For answers that are lists, use JSON arrays. For yes/no questions, answer with "yes" or "no".

Questions:

"""

    # Add each question
    for q in questions:
        prompt += f"{q['id']}. {q['question']}\n"

    prompt += "\n\nRemember: Write your answers to answers.json in the repository root!"
    prompt += "\n\nWhen you have finished writing all answers, output EXACTLY this line with nothing else:\nREADY!"

    return prompt


def generate_prompt(deterministic_path: str, mode: str) -> None:
    """
    Generate prompt and print to stdout.

    Args:
        deterministic_path: Path to deterministic test directory (e.g., tests/deterministic/maven)
        mode: "RIG" or "NORIG"

    Exits:
        0: Success
        1: Error (fail-fast)
    """
    try:
        # Load evaluation questions
        questions_data = load_evaluation_questions(deterministic_path)
        questions = questions_data["questions"]

        if not questions:
            raise ValueError("No questions found in evaluation_questions.json")

        # Build prompt based on mode
        if mode == "RIG":
            # Find and load ground truth
            ground_truth_file = find_ground_truth_file(deterministic_path)
            ground_truth = load_ground_truth(ground_truth_file)
            prompt = build_prompt_with_rig(questions, ground_truth)
        elif mode == "NORIG":
            prompt = build_prompt_without_rig(questions)
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'RIG' or 'NORIG'")

        # Print prompt to stdout
        print(prompt)
        sys.exit(0)

    except Exception as e:
        print(f"ERROR generating prompt: {e}", file=sys.stderr)
        sys.exit(1)


def add_timing_to_answers(answers_file: str, seconds: float) -> None:
    """
    Add timing information to answers JSON file.

    Args:
        answers_file: Path to answers.json file
        seconds: Completion time in seconds

    Exits:
        0: Success
        1: Error (fail-fast)
    """
    try:
        # Validate file exists
        if not os.path.exists(answers_file):
            raise FileNotFoundError(f"answers.json not found: {answers_file}")

        # Load existing answers
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = json.load(f)

        # Validate it's a list
        if not isinstance(answers, list):
            raise ValueError(f"answers.json must be a JSON array, got {type(answers).__name__}")

        # Create new structure with timing
        output = {
            "agent_completion_time_seconds": seconds,
            "answers": answers
        }

        # Write back to file
        with open(answers_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        sys.exit(0)

    except Exception as e:
        print(f"ERROR adding timing: {e}", file=sys.stderr)
        sys.exit(1)


def list_repos() -> None:
    """
    Print list of repository relative paths (one per line).

    Format: cmake/metaffi
            maven
            etc.

    Exits:
        0: Success
        1: Error (fail-fast)
    """
    try:
        script_dir = Path(__file__).parent

        for repo in REPOS:
            repo_path = Path(repo['path'])
            # Get relative path from tests/deterministic
            relative_path = repo_path.relative_to(script_dir)
            print(str(relative_path))

        sys.exit(0)

    except Exception as e:
        print(f"ERROR listing repos: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  ask_agents_shell_helper.py list_repos", file=sys.stderr)
        print("  ask_agents_shell_helper.py generate_prompt <deterministic_path> <RIG|NORIG>", file=sys.stderr)
        print("  ask_agents_shell_helper.py add_timing <answers_file> <seconds>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list_repos":
        list_repos()

    elif command == "generate_prompt":
        if len(sys.argv) != 4:
            print("ERROR: generate_prompt requires <deterministic_path> <RIG|NORIG>", file=sys.stderr)
            sys.exit(1)
        deterministic_path = sys.argv[2]
        mode = sys.argv[3]
        generate_prompt(deterministic_path, mode)

    elif command == "add_timing":
        if len(sys.argv) != 4:
            print("ERROR: add_timing requires <answers_file> <seconds>", file=sys.stderr)
            sys.exit(1)
        answers_file = sys.argv[2]
        seconds = float(sys.argv[3])
        add_timing_to_answers(answers_file, seconds)

    else:
        print(f"ERROR: Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
