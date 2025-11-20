#!/usr/bin/env python3
"""
Generate prompt files for agent evaluation.

This script generates two text files:
- prompt_without_rig.txt: Prompt for agents WITHOUT RIG context
- prompt_with_rig.txt: Prompt for agents WITH RIG context

These files contain the exact prompts that are passed to agents by ask_agents.py.
"""

import json
import os
from glob import glob
from pathlib import Path


def find_ground_truth_file(directory: str) -> str:
    """
    Find exactly one *_ground_truth.json file in the directory.

    Args:
        directory: Path to search for ground truth file

    Returns:
        Path to the ground truth file

    Raises:
        FileNotFoundError: If no ground truth file found
        ValueError: If multiple ground truth files found
    """
    pattern = os.path.join(directory, "*_ground_truth.json")
    matches = glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(f"No ground truth file found in: {directory}")

    if len(matches) > 1:
        raise ValueError(f"Multiple ground truth files found in {directory}: {matches}")

    return matches[0]


def build_prompt_without_rig(questions: list) -> str:
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


def build_prompt_with_rig(questions: list, ground_truth: dict) -> str:
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


def main():
    """Generate prompt files."""
    # Get current directory
    current_dir = Path(__file__).parent

    # Load evaluation questions
    questions_file = current_dir / "evaluation_questions.json"
    if not questions_file.exists():
        raise FileNotFoundError(f"evaluation_questions.json not found in {current_dir}")

    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)

    questions = questions_data.get("questions", [])
    if not questions:
        raise ValueError("No questions found in evaluation_questions.json")

    print(f"Loaded {len(questions)} questions from {questions_file}")

    # Find and load ground truth
    ground_truth_file = find_ground_truth_file(str(current_dir))
    print(f"Found ground truth file: {ground_truth_file}")

    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    # Generate prompts
    prompt_without_rig = build_prompt_without_rig(questions)
    prompt_with_rig = build_prompt_with_rig(questions, ground_truth)

    # Save prompts to files
    without_rig_file = current_dir / "prompt_without_rig.txt"
    with_rig_file = current_dir / "prompt_with_rig.txt"

    with open(without_rig_file, 'w', encoding='utf-8') as f:
        f.write(prompt_without_rig)
    print(f"[OK] Saved prompt WITHOUT RIG to: {without_rig_file}")
    print(f"     Length: {len(prompt_without_rig)} characters")

    with open(with_rig_file, 'w', encoding='utf-8') as f:
        f.write(prompt_with_rig)
    print(f"[OK] Saved prompt WITH RIG to: {with_rig_file}")
    print(f"     Length: {len(prompt_with_rig)} characters")

    print("\n[OK] Prompt files generated successfully!")


if __name__ == "__main__":
    main()
