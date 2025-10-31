"""
Validation utilities for agent answer files.

This module provides functions to validate that agents have completed
their work and produced valid, complete answer files.
"""

import json
import os
from typing import Tuple, List, Set


def validate_answers_file(repo_path: str, expected_question_ids: List[int]) -> Tuple[bool, str]:
    """
    Validate that answers.json exists and contains all expected question IDs.

    Args:
        repo_path: Path to the repository where answers.json should be
        expected_question_ids: List of question IDs that should have answers

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if file is complete and valid, False otherwise
        - error_message: Empty string if valid, otherwise describes the problem
    """
    answers_file = os.path.join(repo_path, "answers.json")

    # Check if file exists
    if not os.path.exists(answers_file):
        return False, f"answers.json not found at: {answers_file}"

    # Try to read and parse JSON
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            content = f.read()

        answers = json.loads(content)

    except json.JSONDecodeError as e:
        return False, f"answers.json contains invalid JSON: {str(e)}"

    except Exception as e:
        return False, f"Failed to read answers.json: {str(e)}"

    # Validate structure (should be a list)
    if not isinstance(answers, list):
        return False, f"answers.json must be a JSON array, got {type(answers).__name__}"

    # Extract question IDs from answers
    answered_ids = set()
    for i, answer_obj in enumerate(answers):
        if not isinstance(answer_obj, dict):
            return False, f"Answer at index {i} is not a JSON object"

        if "id" not in answer_obj:
            return False, f"Answer at index {i} is missing 'id' field"

        answered_ids.add(answer_obj["id"])

    # Check for missing questions
    expected_ids = set(expected_question_ids)
    missing_ids = expected_ids - answered_ids
    extra_ids = answered_ids - expected_ids

    if missing_ids:
        missing_list = sorted(list(missing_ids))
        return False, f"Missing answers for question IDs: {missing_list}"

    if extra_ids:
        extra_list = sorted(list(extra_ids))
        # This is a warning, not an error
        return True, f"Warning: Unexpected question IDs in answers: {extra_list}"

    # All good!
    return True, ""


def extract_question_ids_from_prompt(prompt: str) -> List[int]:
    """
    Extract question IDs from the prompt text.

    Looks for lines matching pattern: "N. Question text?"

    Args:
        prompt: The prompt text containing questions

    Returns:
        List of question IDs found
    """
    import re

    question_ids = []
    # Match lines like "1. What is..." or "15. How many..."
    pattern = r'^(\d+)\.\s+'

    for line in prompt.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            question_ids.append(int(match.group(1)))

    return question_ids
