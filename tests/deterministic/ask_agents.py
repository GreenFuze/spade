#!/usr/bin/env python3
"""
Ask CLI agents (Claude, Cursor, Codex) evaluation questions about a repository.

This script:
1. Loads evaluation questions and ground truth
2. Runs agents WITH and WITHOUT RIG context
3. Saves answers for comparison

Usage:
    python ask_agents.py <relative_path>
    python ask_agents.py all

Examples:
    python ask_agents.py cmake/cmake_hello_world  # Process single repo
    python ask_agents.py all                       # Process all repos from config.py

The relative path maps to:
    - Questions: tests/deterministic/{relative_path}/evaluation_questions.json
    - Ground truth: tests/deterministic/{relative_path}/*_ground_truth.json
    - Repository: tests/test_repos/{relative_path}/
"""

import argparse
import json
import os
import sys
from glob import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple

from agent_executors import ClaudeAgentExecutor, CursorAgentExecutor, CodexAgentExecutor

# Import REPOS from config.py
sys.path.insert(0, str(Path(__file__).parent / "summary_analysis"))
from config import REPOS


def get_relative_path_from_config(repo_config: Dict[str, Any]) -> str:
    """
    Convert config.REPOS path to relative path string for ask_agents.py.

    Args:
        repo_config: Repository configuration dictionary from REPOS

    Returns:
        Relative path string (e.g., "cmake/cmake_hello_world")
    """
    repo_path = Path(repo_config["path"])
    script_dir = Path(__file__).parent  # tests/deterministic
    relative_path = repo_path.relative_to(script_dir)
    return str(relative_path)


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


def save_answers(answers: Dict[str, Any], output_path: str) -> None:
    """
    Save agent answers to JSON file.

    Args:
        answers: Answer dictionary or error result
        output_path: Path to save answers
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(answers, f, indent=2)


def run_evaluation(
    agent_name: str,
    executor: Any,
    questions: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    repo_path: str,
    output_dir: str
) -> List[str]:
    """
    Run evaluation for one agent (both WITH and WITHOUT RIG).

    Args:
        agent_name: Name of the agent (e.g., 'claude')
        executor: Agent executor instance
        questions: List of evaluation questions
        ground_truth: Ground truth data (RIG)
        repo_path: Path to the repository
        output_dir: Directory to save answer files

    Returns:
        List of failed runs (e.g., ["codex with RIG"])
    """
    failed_runs = []
    print(f"\n=== Evaluating {agent_name.upper()} ===")
    print(f"[MAIN-LOG] Repository: {repo_path}")
    print(f"[MAIN-LOG] Output directory: {output_dir}")

    # WITHOUT RIG
    norig_output = os.path.join(output_dir, f"{agent_name}_NORIG_answers.json")

    if os.path.exists(norig_output):
        print(f"[MAIN-LOG] Answers file detected - skipping: {norig_output}")
    else:
        print(f"[MAIN-LOG] Running {agent_name} WITHOUT RIG...")
        prompt_norig = build_prompt_without_rig(questions)
        print(f"[MAIN-LOG] Prompt length: {len(prompt_norig)} characters")
        print(f"[MAIN-LOG] Number of questions: {len(questions)}")

        print(f"[MAIN-LOG] Executing {agent_name}...")
        answers_norig = executor.execute(prompt_norig, repo_path)

        print(f"[MAIN-LOG] Execution completed. Result type: {type(answers_norig)}")
        if isinstance(answers_norig, dict) and "error" in answers_norig:
            print(f"[MAIN-LOG] WARNING: Agent returned error: {answers_norig['error']}")
            failed_runs.append(f"{agent_name} without RIG")

        save_answers(answers_norig, norig_output)
        print(f"[MAIN-LOG] SUCCESS: Saved answers to: {norig_output}")

    # WITH RIG
    rig_output = os.path.join(output_dir, f"{agent_name}_RIG_answers.json")

    if os.path.exists(rig_output):
        print(f"[MAIN-LOG] Answers file detected - skipping: {rig_output}")
    else:
        print(f"[MAIN-LOG] Running {agent_name} WITH RIG...")
        prompt_rig = build_prompt_with_rig(questions, ground_truth)
        print(f"[MAIN-LOG] Prompt length: {len(prompt_rig)} characters")
        print(f"[MAIN-LOG] Number of questions: {len(questions)}")

        print(f"[MAIN-LOG] Executing {agent_name}...")
        answers_rig = executor.execute(prompt_rig, repo_path)

        print(f"[MAIN-LOG] Execution completed. Result type: {type(answers_rig)}")
        if isinstance(answers_rig, dict) and "error" in answers_rig:
            print(f"[MAIN-LOG] WARNING: Agent returned error: {answers_rig['error']}")
            failed_runs.append(f"{agent_name} with RIG")

        save_answers(answers_rig, rig_output)
        print(f"[MAIN-LOG] SUCCESS: Saved answers to: {rig_output}")

    return failed_runs


def process_repository(relative_path: str, script_dir: str, tests_root: str) -> Tuple[bool, List[str]]:
    """
    Process a single repository - load questions, ground truth, and run agents.

    Args:
        relative_path: Relative path to repository (e.g., "cmake/cmake_hello_world")
        script_dir: Path to tests/deterministic directory
        tests_root: Path to tests directory

    Returns:
        Tuple of (success: bool, failed_runs: List[str])
        - success: True if at least some runs completed, False if entire repo failed
        - failed_runs: List of failed agent runs (e.g., ["codex with RIG"])
    """
    all_failed_runs = []
    try:
        # Build paths
        deterministic_path = os.path.join(script_dir, relative_path)
        repo_path = os.path.join(tests_root, "test_repos", relative_path)

        print(f"[MAIN-LOG] Script directory: {script_dir}")
        print(f"[MAIN-LOG] Deterministic path: {deterministic_path}")
        print(f"[MAIN-LOG] Repository path: {repo_path}")

        # Validate repository exists
        if not os.path.exists(repo_path):
            print(f"[MAIN-LOG] WARNING: Repository not found: {repo_path}")
            print(f"[MAIN-LOG] Skipping...")
            return (False, [])

        # Find and load ground truth
        try:
            ground_truth_file = find_ground_truth_file(deterministic_path)
            print(f"[MAIN-LOG] Ground truth file: {ground_truth_file}")
            ground_truth = load_ground_truth(ground_truth_file)
        except FileNotFoundError as e:
            print(f"[MAIN-LOG] WARNING: {str(e)}")
            print(f"[MAIN-LOG] Skipping...")
            return (False, [])

        # Load evaluation questions
        try:
            questions_data = load_evaluation_questions(deterministic_path)
            questions = questions_data.get("questions", [])

            if not questions:
                print(f"[MAIN-LOG] WARNING: No questions found in evaluation_questions.json")
                print(f"[MAIN-LOG] Skipping...")
                return (False, [])

            print(f"[MAIN-LOG] Loaded {len(questions)} evaluation questions")
        except FileNotFoundError as e:
            print(f"[MAIN-LOG] WARNING: {str(e)}")
            print(f"[MAIN-LOG] Skipping...")
            return (False, [])

        # Create agent executors
        executors = {
            "claude": ClaudeAgentExecutor(),
            "cursor": CursorAgentExecutor(),
            "codex": CodexAgentExecutor()
        }

        # Run evaluation for each agent
        for agent_name, executor in executors.items():
            failed_runs = run_evaluation(
                agent_name=agent_name,
                executor=executor,
                questions=questions,
                ground_truth=ground_truth,
                repo_path=repo_path,
                output_dir=deterministic_path
            )
            all_failed_runs.extend(failed_runs)

        print(f"[MAIN-LOG] === Evaluation Complete for {relative_path} ===")
        return (True, all_failed_runs)

    except Exception as e:
        print(f"[MAIN-LOG] ERROR processing {relative_path}: {str(e)}", file=sys.stderr)
        return (False, [])


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Ask CLI agents evaluation questions about a repository"
    )
    parser.add_argument(
        "relative_path",
        help="Relative path (e.g., 'cmake/cmake_hello_world') or 'all' to process all repos from config.py"
    )
    args = parser.parse_args()

    # Get script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tests_root = os.path.dirname(script_dir)  # tests/

    # Check if processing all repositories
    if args.relative_path.lower() == "all":
        print("[MAIN-LOG] ========================================")
        print("[MAIN-LOG] Processing ALL repositories from config.py")
        print(f"[MAIN-LOG] Total repositories: {len(REPOS)}")
        print("[MAIN-LOG] ========================================\n")

        results = []
        for repo_config in REPOS:
            relative_path = get_relative_path_from_config(repo_config)
            print(f"\n{'='*60}")
            print(f"[MAIN-LOG] Processing repository: {repo_config['name']}")
            print(f"[MAIN-LOG] Relative path: {relative_path}")
            print(f"{'='*60}\n")

            success, failed_runs = process_repository(relative_path, script_dir, tests_root)
            results.append({
                "name": repo_config['name'],
                "path": relative_path,
                "success": success,
                "failed_runs": failed_runs
            })

        # Print summary
        print(f"\n\n{'='*60}")
        print("[MAIN-LOG] SUMMARY")
        print(f"{'='*60}")
        for result in results:
            if result['success']:
                if result['failed_runs']:
                    failed_list = "', '".join(result['failed_runs'])
                    status = f"[OK] PARTIAL: {result['name']} ({result['path']}). Failed runs: '{failed_list}'"
                else:
                    status = f"[OK] SUCCESS: {result['name']} ({result['path']})"
            else:
                status = f"[X] FAILED: {result['name']} ({result['path']})"
            print(status)

        failed_count = sum(1 for r in results if not r['success'])
        success_count = len(results) - failed_count
        print(f"\n[MAIN-LOG] Total: {len(results)} repositories")
        print(f"[MAIN-LOG] Success: {success_count}")
        print(f"[MAIN-LOG] Failed: {failed_count}")
        print(f"{'='*60}")

        return 0 if failed_count == 0 else 1

    else:
        # Process single repository (existing behavior)
        print("[MAIN-LOG] ========================================")
        print(f"[MAIN-LOG] Starting evaluation for: {args.relative_path}")
        print("[MAIN-LOG] ========================================\n")

        success, failed_runs = process_repository(args.relative_path, script_dir, tests_root)

        if success:
            if failed_runs:
                print(f"\n[MAIN-LOG] === Evaluation Complete with {len(failed_runs)} failed run(s) ===")
                print(f"[MAIN-LOG] Failed runs: {', '.join(failed_runs)}")
            else:
                print("\n[MAIN-LOG] === Evaluation Complete ===")
            return 0
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
