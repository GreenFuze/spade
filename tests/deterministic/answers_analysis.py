#!/usr/bin/env python3
"""
Answer Analysis and Scoring Script

This script analyzes agent answers against expected answers and produces
detailed scoring reports.

Usage:
    python answers_analysis.py <relative_path>

Example:
    python answers_analysis.py cmake/cmake_hello_world

The relative path maps to:
    - Questions: tests/deterministic/{relative_path}/evaluation_questions.json
    - Answers: tests/deterministic/{relative_path}/*_answers.json
    - Output: tests/deterministic/{relative_path}/answers_analysis.json
"""

import argparse
import json
import os
import sys
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


class AnswerNormalizer:
    """
    Handles normalization of answers for flexible comparison.

    Normalization rules:
    1. Path separators: backslash to forward slash
    2. Case insensitive comparison
    3. Optional file extensions (.exe, .lib, .dll, .so, .a, .dylib)
    4. Language aliases (cxx <-> C++ <-> cpp <-> c++)
    5. Library type aliases (static_library <-> library)
    """

    # File extensions to strip for comparison
    EXTENSIONS = {'.exe', '.lib', '.dll', '.so', '.a', '.dylib', '.out'}

    # Language equivalence groups
    LANGUAGE_ALIASES = {
        'cxx': {'cxx', 'c++', 'cpp'},
        'c++': {'cxx', 'c++', 'cpp'},
        'cpp': {'cxx', 'c++', 'cpp'},
    }

    # Library type equivalence
    LIBRARY_TYPE_ALIASES = {
        'static_library': {'static_library', 'library'},
        'library': {'static_library', 'library'},
    }

    @staticmethod
    def normalize_path(value: str) -> str:
        """Normalize path separators to forward slashes and strip trailing slashes."""
        normalized = value.replace('\\', '/')
        # Strip trailing slash unless it's the root "/"
        if len(normalized) > 1 and normalized.endswith('/'):
            normalized = normalized.rstrip('/')
        return normalized

    @staticmethod
    def normalize_case(value: str) -> str:
        """Convert to lowercase for case-insensitive comparison."""
        return value.lower()

    @classmethod
    def strip_extension(cls, value: str) -> str:
        """Strip known file extensions from value."""
        for ext in cls.EXTENSIONS:
            if value.lower().endswith(ext):
                return value[:-len(ext)]
        return value

    @classmethod
    def normalize_value(cls, value: Any) -> Any:
        """
        Normalize a single value (string, number, bool, list).

        Args:
            value: Value to normalize

        Returns:
            Normalized value
        """
        if isinstance(value, str):
            # Apply all string normalizations
            normalized = cls.normalize_path(value)
            normalized = cls.normalize_case(normalized)
            return normalized
        elif isinstance(value, list):
            # Normalize each element in the list
            return [cls.normalize_value(item) for item in value]
        else:
            # Numbers and booleans return as-is
            return value

    @classmethod
    def are_equivalent(cls, val1: Any, val2: Any) -> bool:
        """
        Check if two values are equivalent considering all normalization rules.

        Args:
            val1: First value
            val2: Second value

        Returns:
            True if values are equivalent
        """
        # Handle None cases
        if val1 is None or val2 is None:
            return val1 == val2

        # Normalize both values
        norm1 = cls.normalize_value(val1)
        norm2 = cls.normalize_value(val2)

        # Try numeric comparison if one is numeric and one is string
        if (isinstance(norm1, (int, float)) and isinstance(norm2, str)) or \
           (isinstance(norm1, str) and isinstance(norm2, (int, float))):
            try:
                # Convert both to numbers for comparison
                num1 = float(norm1) if isinstance(norm1, str) else norm1
                num2 = float(norm2) if isinstance(norm2, str) else norm2
                if num1 == num2:
                    return True
            except (ValueError, TypeError):
                # Not a valid numeric string, continue with other checks
                pass

        # Direct comparison
        if norm1 == norm2:
            return True

        # String-specific equivalences
        if isinstance(norm1, str) and isinstance(norm2, str):
            # Try with extension stripping
            stripped1 = cls.strip_extension(norm1)
            stripped2 = cls.strip_extension(norm2)
            if stripped1 == stripped2:
                return True

            # Check language aliases
            if norm1 in cls.LANGUAGE_ALIASES:
                if norm2 in cls.LANGUAGE_ALIASES[norm1]:
                    return True

            # Check library type aliases
            if norm1 in cls.LIBRARY_TYPE_ALIASES:
                if norm2 in cls.LIBRARY_TYPE_ALIASES[norm1]:
                    return True

        return False

    @classmethod
    def compare_lists(cls, expected: List[Any], actual: List[Any], ordered: bool = False) -> bool:
        """
        Compare two lists considering normalization.

        Args:
            expected: Expected list
            actual: Actual list
            ordered: If True, order matters; if False, treat as sets

        Returns:
            True if lists match
        """
        if len(expected) != len(actual):
            return False

        if ordered:
            # Order matters - compare element by element
            for exp_item, act_item in zip(expected, actual):
                if not cls.are_equivalent(exp_item, act_item):
                    return False
            return True
        else:
            # Order doesn't matter - treat as sets
            # For each expected item, find a matching actual item
            matched_indices = set()
            for exp_item in expected:
                found_match = False
                for i, act_item in enumerate(actual):
                    if i not in matched_indices and cls.are_equivalent(exp_item, act_item):
                        matched_indices.add(i)
                        found_match = True
                        break
                if not found_match:
                    return False
            return True


class QuestionScorer:
    """
    Scores individual questions by comparing expected vs actual answers.
    """

    def __init__(self, normalizer: AnswerNormalizer):
        """
        Initialize question scorer.

        Args:
            normalizer: Answer normalizer instance
        """
        self.normalizer = normalizer

    def score_question(self, question: Dict[str, Any], actual_answer: Any) -> Tuple[int, str]:
        """
        Score a single question.

        Expected answer format:
        - Single scalar: expected_answer = 16
        - Multiple acceptable scalars: expected_answer = [15, 16]
        - Single list answer: expected_answer = ["main.h"]
        - Multiple acceptable lists: expected_answer = [["main.h"], ["utils.h", "main.h"]]

        Args:
            question: Question dictionary with expected_answer
            actual_answer: Actual answer provided by agent

        Returns:
            Tuple of (score, debug_message)
            Score is 1 for correct, 0 for incorrect
        """
        expected = question["expected_answer"]

        # Check if question explicitly mentions order
        question_text = question.get("question", "").lower()
        ordered = "order" in question_text and "build order" in question_text

        # Determine answer type and compare
        if not isinstance(expected, list):
            # Case 1: Single scalar answer
            # expected = 16
            is_correct = self.normalizer.are_equivalent(expected, actual_answer)

        elif len(expected) > 0 and all(isinstance(item, list) for item in expected):
            # Case 2: Multiple acceptable list answers
            # expected = [["main.h"], ["utils.h", "main.h"]]
            is_correct = False
            if isinstance(actual_answer, list):
                # Actual is a list - compare against acceptable lists
                for acceptable_list in expected:
                    if self.normalizer.compare_lists(acceptable_list, actual_answer, ordered=ordered):
                        is_correct = True
                        break
            else:
                # Actual is a scalar - check if all expected lists are single-element lists
                # If so, treat scalar as equivalent to single-element list
                if all(len(acceptable_list) == 1 for acceptable_list in expected):
                    # Extract single elements from each list
                    single_elements = [acceptable_list[0] for acceptable_list in expected]
                    # Check if scalar matches any of those elements
                    is_correct = any(self.normalizer.are_equivalent(element, actual_answer) for element in single_elements)

        else:
            # Case 3: Multiple acceptable scalar answers OR single list answer
            # expected = [15, 16] OR expected = ["main.h"]

            if isinstance(actual_answer, list):
                # Agent gave a list - treat expected as a single list answer
                is_correct = self.normalizer.compare_lists(expected, actual_answer, ordered=ordered)
            else:
                # Agent gave a scalar - check if it matches any element in expected
                is_correct = any(self.normalizer.are_equivalent(exp, actual_answer) for exp in expected)

        score = 1 if is_correct else 0

        # Debug message
        if is_correct:
            debug_msg = "Correct"
        else:
            debug_msg = f"Incorrect (expected: {expected}, got: {actual_answer})"

        return score, debug_msg


class AnalysisRunner:
    """
    Main orchestrator for answer analysis and scoring.
    """

    def __init__(self, deterministic_path: str):
        """
        Initialize analysis runner.

        Args:
            deterministic_path: Path to deterministic test directory
        """
        self.deterministic_path = deterministic_path
        self.normalizer = AnswerNormalizer()
        self.scorer = QuestionScorer(self.normalizer)
        self.questions = []
        self.questions_by_id = {}

    def load_evaluation_questions(self) -> None:
        """
        Load evaluation_questions.json file.

        Raises:
            FileNotFoundError: If evaluation_questions.json not found
            json.JSONDecodeError: If JSON is invalid
        """
        questions_file = os.path.join(self.deterministic_path, "evaluation_questions.json")

        if not os.path.exists(questions_file):
            raise FileNotFoundError(f"evaluation_questions.json not found at: {questions_file}")

        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        self.questions = questions_data.get("questions", [])

        if not self.questions:
            raise ValueError("No questions found in evaluation_questions.json")

        # Build ID lookup
        self.questions_by_id = {q["id"]: q for q in self.questions}

        print(f"[LOG] Loaded {len(self.questions)} evaluation questions")

    def find_answer_files(self) -> List[str]:
        """
        Find all *_answers.json files in the directory.

        Returns:
            List of answer file paths

        Raises:
            FileNotFoundError: If no answer files found
        """
        pattern = os.path.join(self.deterministic_path, "*_answers.json")
        answer_files = glob(pattern)

        # Exclude answers_analysis.json itself
        answer_files = [f for f in answer_files if not f.endswith("answers_analysis.json")]

        if not answer_files:
            raise FileNotFoundError(f"No *_answers.json files found in: {self.deterministic_path}")

        print(f"[LOG] Found {len(answer_files)} answer files")
        return answer_files

    def extract_agent_name(self, answer_file: str) -> str:
        """
        Extract agent name from answer file path.

        Args:
            answer_file: Path to answer file

        Returns:
            Agent name (e.g., "claude_RIG", "cursor_NORIG")
        """
        basename = os.path.basename(answer_file)
        # Remove "_answers.json" suffix
        agent_name = basename.replace("_answers.json", "")
        return agent_name

    def score_answer_file(self, answer_file: str) -> Dict[str, Any]:
        """
        Score all answers in a single answer file.

        Args:
            answer_file: Path to answer file

        Returns:
            Dictionary with scoring results
        """
        agent_name = self.extract_agent_name(answer_file)
        print(f"[LOG] Scoring {agent_name}...")

        # Load answers
        with open(answer_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract timing data if present
        completion_time = None
        if isinstance(data, dict) and "agent_completion_time_seconds" in data:
            completion_time = data["agent_completion_time_seconds"]
            answers = data.get("answers", [])
        else:
            answers = data

        # Score each answer
        question_scores = []
        total_score = 0
        difficulty_scores = {"easy": {"score": 0, "max": 0}, "medium": {"score": 0, "max": 0}, "hard": {"score": 0, "max": 0}}

        for answer_entry in answers:
            answer_id = answer_entry.get("id")
            actual_answer = answer_entry.get("answer")

            if answer_id not in self.questions_by_id:
                print(f"[WARNING] Answer ID {answer_id} not found in questions, skipping")
                continue

            question = self.questions_by_id[answer_id]
            expected_answer = question["expected_answer"]
            difficulty = question["difficulty"]

            # Score the question
            score, debug_msg = self.scorer.score_question(question, actual_answer)

            # Accumulate scores
            total_score += score
            difficulty_scores[difficulty]["score"] += score
            difficulty_scores[difficulty]["max"] += 1

            # Record question score
            question_record = {
                "id": answer_id,
                "score": score,
                "expected": expected_answer,
                "actual": actual_answer
            }

            # For incorrect answers or questions with multiple acceptable answers, include full details
            # This helps reviewers understand what was expected and decide if more answers should be accepted
            if score == 0 or isinstance(expected_answer, list):
                question_record["question"] = question["question"]

            question_scores.append(question_record)

        # Calculate max score
        max_score = len(self.questions)

        print(f"[LOG] {agent_name}: {total_score}/{max_score} points")
        if completion_time is not None:
            print(f"[LOG] {agent_name}: completed in {completion_time}s")

        result = {
            "total_score": total_score,
            "max_score": max_score,
            "by_difficulty": difficulty_scores,
            "questions": question_scores
        }

        # Add timing data if available
        if completion_time is not None:
            result["completion_time_seconds"] = completion_time

        return result

    def restructure_results_to_question_centric(
        self, agent_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Transform agent-centric results to question-centric format.

        Args:
            agent_results: Dictionary mapping agent names to their results
                          (e.g., {"claude_NORIG": {"questions": [...], ...}, ...})

        Returns:
            List of question objects where each question has agent-specific results
            [
                {
                    "id": 1,
                    "question": "...",
                    "expected": "...",
                    "claude_NORIG": {"score": 1, "actual": "..." (if score=0)},
                    "claude_RIG": {"score": 0, "actual": "..."},
                    ...
                },
                ...
            ]
        """
        # Build a map of all questions from evaluation_questions.json
        questions_by_id = {q["id"]: q for q in self.questions}

        # Get all unique question IDs across all agents
        all_question_ids = set()
        for agent_data in agent_results.values():
            for q in agent_data["questions"]:
                all_question_ids.add(q["id"])

        # Build question-centric structure
        questions = []
        for q_id in sorted(all_question_ids):
            # Get question metadata from evaluation_questions.json
            if q_id not in questions_by_id:
                raise ValueError(
                    f"Question ID {q_id} appears in agent results but not in evaluation_questions.json. "
                    f"All question IDs must be defined in evaluation_questions.json."
                )
            q_metadata = questions_by_id[q_id]

            question_obj = {
                "id": q_id,
                "question": q_metadata["question"],
                "expected": q_metadata["expected_answer"],
                "difficulty": q_metadata["difficulty"],
                "category": q_metadata["category"],
            }

            # Add agent-specific results
            for agent_name, agent_data in agent_results.items():
                # Find this question in the agent's results
                agent_q = next(
                    (q for q in agent_data["questions"] if q["id"] == q_id),
                    None
                )

                if agent_q:
                    agent_result = {"score": agent_q["score"]}

                    # Only include 'actual' if score is 0 (incorrect answer)
                    if agent_q["score"] == 0:
                        agent_result["actual"] = agent_q.get("actual")

                    question_obj[agent_name] = agent_result

            questions.append(question_obj)

        return questions

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run complete analysis on all answer files.

        Returns:
            Dictionary with analysis results in question-centric format:
            {
                "questions": [  # question-centric data
                    {
                        "id": 1,
                        "question": "...",
                        "expected": "...",
                        "claude_NORIG": {"score": 1, "actual": "..." (if score=0)},
                        ...
                    },
                    ...
                ],
                "claude_NORIG": {  # agent-level summary (without 'questions' array)
                    "total_score": ...,
                    "max_score": ...,
                    "by_difficulty": {...},
                    "completion_time_seconds": ...
                },
                "claude_RIG": {...},
                ...
            }
        """
        # Load questions
        self.load_evaluation_questions()

        # Find all answer files
        answer_files = self.find_answer_files()

        # Score each answer file (agent-centric results)
        agent_results = {}
        for answer_file in answer_files:
            agent_name = self.extract_agent_name(answer_file)
            agent_results[agent_name] = self.score_answer_file(answer_file)

        # Transform to question-centric format
        question_centric_results = self.restructure_results_to_question_centric(agent_results)

        # Build final results structure
        results = {"questions": question_centric_results}

        # Add agent-level summaries (without 'questions' array)
        for agent_name, agent_data in agent_results.items():
            results[agent_name] = {
                "total_score": agent_data["total_score"],
                "max_score": agent_data["max_score"],
                "by_difficulty": agent_data["by_difficulty"],
            }
            # Include completion_time_seconds if available
            if "completion_time_seconds" in agent_data:
                results[agent_name]["completion_time_seconds"] = agent_data["completion_time_seconds"]

        return results

    def calculate_percentage(self, score: int, max_score: int) -> float:
        """
        Calculate percentage score.

        Args:
            score: Achieved score
            max_score: Maximum possible score

        Returns:
            Percentage (0-100)
        """
        if max_score == 0:
            return 0.0
        return round((score / max_score) * 100, 1)

    def build_comparative_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comparative analysis for each agent (RIG vs NORIG).

        Args:
            results: Raw results dictionary

        Returns:
            Comparative analysis dictionary
        """
        analysis = {}

        # Group agents by base name (claude, cursor, codex)
        agents_grouped = {}
        for agent_name in results.keys():
            # Skip the "questions" key (question-centric data)
            if agent_name == "questions":
                continue

            if "_RIG" in agent_name:
                base_name = agent_name.replace("_RIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["with_rig"] = results[agent_name]
                agents_grouped[base_name]["with_rig_name"] = agent_name
            elif "_NORIG" in agent_name:
                base_name = agent_name.replace("_NORIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["without_rig"] = results[agent_name]
                agents_grouped[base_name]["without_rig_name"] = agent_name

        # Build analysis for each agent
        for base_name, agent_data in agents_grouped.items():
            if "with_rig" not in agent_data or "without_rig" not in agent_data:
                continue  # Skip if we don't have both RIG and NORIG

            with_rig = agent_data["with_rig"]
            without_rig = agent_data["without_rig"]
            with_rig_name = agent_data["with_rig_name"]
            without_rig_name = agent_data["without_rig_name"]

            # Calculate overall percentages
            with_rig_percentage = self.calculate_percentage(with_rig["total_score"], with_rig["max_score"])
            without_rig_percentage = self.calculate_percentage(without_rig["total_score"], without_rig["max_score"])

            # Calculate improvement
            improvement_absolute = with_rig["total_score"] - without_rig["total_score"]
            improvement_percentage = self.calculate_percentage(improvement_absolute, with_rig["max_score"])

            # Build difficulty-level analysis
            improvement_by_difficulty = {}
            for difficulty in ["easy", "medium", "hard"]:
                with_rig_diff = with_rig["by_difficulty"][difficulty]
                without_rig_diff = without_rig["by_difficulty"][difficulty]

                improvement_abs = with_rig_diff["score"] - without_rig_diff["score"]
                improvement_pct = self.calculate_percentage(improvement_abs, with_rig_diff["max"])

                improvement_by_difficulty[difficulty] = {
                    "absolute": improvement_abs,
                    "percentage": improvement_pct
                }

            # Find mistakes by difficulty
            mistakes_without_rig = self.analyze_mistakes(results, without_rig_name)
            mistakes_with_rig = self.analyze_mistakes(results, with_rig_name)

            # Find questions fixed/broken by RIG
            questions_fixed = []
            questions_broken = []

            # Use question-centric data from results["questions"]
            for question in results["questions"]:
                q_id = question["id"]

                # Check if both agents answered this question
                if with_rig_name in question and without_rig_name in question:
                    score_with_rig = question[with_rig_name]["score"]
                    score_without_rig = question[without_rig_name]["score"]

                    if score_without_rig == 0 and score_with_rig == 1:
                        questions_fixed.append(q_id)
                    elif score_without_rig == 1 and score_with_rig == 0:
                        questions_broken.append(q_id)

            # Build timing analysis
            timing_analysis = {}
            time_with_rig = with_rig.get("completion_time_seconds")
            time_without_rig = without_rig.get("completion_time_seconds")

            if time_with_rig is not None and time_without_rig is not None:
                time_saved = time_without_rig - time_with_rig
                time_reduction_percentage = self.calculate_percentage(time_saved, time_without_rig)

                # Calculate efficiency (score per second)
                efficiency_with_rig = with_rig["total_score"] / time_with_rig if time_with_rig > 0 else 0
                efficiency_without_rig = without_rig["total_score"] / time_without_rig if time_without_rig > 0 else 0

                timing_analysis = {
                    "time_with_rig_seconds": time_with_rig,
                    "time_without_rig_seconds": time_without_rig,
                    "time_saved_seconds": round(time_saved, 2),
                    "time_reduction_percentage": round(time_reduction_percentage, 1),
                    "efficiency_with_rig_score_per_second": round(efficiency_with_rig, 4),
                    "efficiency_without_rig_score_per_second": round(efficiency_without_rig, 4)
                }

            # Build agent analysis
            analysis[base_name] = {
                "with_rig": {
                    "score": with_rig["total_score"],
                    "max_score": with_rig["max_score"],
                    "percentage": with_rig_percentage,
                    "by_difficulty": {
                        difficulty: {
                            "score": with_rig["by_difficulty"][difficulty]["score"],
                            "max": with_rig["by_difficulty"][difficulty]["max"],
                            "percentage": self.calculate_percentage(
                                with_rig["by_difficulty"][difficulty]["score"],
                                with_rig["by_difficulty"][difficulty]["max"]
                            )
                        }
                        for difficulty in ["easy", "medium", "hard"]
                    }
                },
                "without_rig": {
                    "score": without_rig["total_score"],
                    "max_score": without_rig["max_score"],
                    "percentage": without_rig_percentage,
                    "by_difficulty": {
                        difficulty: {
                            "score": without_rig["by_difficulty"][difficulty]["score"],
                            "max": without_rig["by_difficulty"][difficulty]["max"],
                            "percentage": self.calculate_percentage(
                                without_rig["by_difficulty"][difficulty]["score"],
                                without_rig["by_difficulty"][difficulty]["max"]
                            )
                        }
                        for difficulty in ["easy", "medium", "hard"]
                    }
                },
                "rig_improvement": {
                    "absolute": improvement_absolute,
                    "percentage": improvement_percentage,
                    "by_difficulty": improvement_by_difficulty
                },
                "mistakes_without_rig": mistakes_without_rig,
                "mistakes_with_rig": mistakes_with_rig,
                "questions_fixed_by_rig": questions_fixed,
                "questions_broken_by_rig": questions_broken
            }

            # Add timing analysis if available
            if timing_analysis:
                analysis[base_name]["timing"] = timing_analysis

        return analysis

    def analyze_mistakes(self, results: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Analyze mistakes for an agent by difficulty level.

        Args:
            results: Full results dictionary with question-centric data
            agent_name: Name of the agent to analyze (e.g., "claude_RIG", "cursor_NORIG")

        Returns:
            Mistakes analysis dictionary
        """
        mistakes_by_difficulty = {
            "easy": {"count": 0, "percentage": 0.0, "question_ids": []},
            "medium": {"count": 0, "percentage": 0.0, "question_ids": []},
            "hard": {"count": 0, "percentage": 0.0, "question_ids": []}
        }

        total_mistakes = 0

        # Get agent's question scores from question-centric data
        for question in results["questions"]:
            q_id = question["id"]

            # Check if this agent answered this question
            if agent_name not in question:
                continue

            # Check if the answer was incorrect
            if question[agent_name]["score"] == 0:
                total_mistakes += 1

                # Find difficulty level from questions_by_id
                if q_id in self.questions_by_id:
                    difficulty = self.questions_by_id[q_id]["difficulty"]
                    mistakes_by_difficulty[difficulty]["count"] += 1
                    mistakes_by_difficulty[difficulty]["question_ids"].append(q_id)

        # Calculate percentages using agent's by_difficulty data
        agent_result = results[agent_name]
        for difficulty in ["easy", "medium", "hard"]:
            max_in_difficulty = agent_result["by_difficulty"][difficulty]["max"]
            count = mistakes_by_difficulty[difficulty]["count"]
            mistakes_by_difficulty[difficulty]["percentage"] = self.calculate_percentage(count, max_in_difficulty)

        return {
            "total": total_mistakes,
            "by_difficulty": mistakes_by_difficulty
        }

    def build_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build summary statistics across all agents.

        Args:
            analysis: Comparative analysis dictionary

        Returns:
            Summary dictionary
        """
        if not analysis:
            return {}

        # Find best/worst performers
        best_with_rig = max(analysis.items(), key=lambda x: x[1]["with_rig"]["percentage"])
        best_without_rig = max(analysis.items(), key=lambda x: x[1]["without_rig"]["percentage"])
        most_improvement = max(analysis.items(), key=lambda x: x[1]["rig_improvement"]["percentage"])
        least_improvement = min(analysis.items(), key=lambda x: x[1]["rig_improvement"]["percentage"])

        # Calculate averages
        avg_with_rig = sum(a["with_rig"]["percentage"] for a in analysis.values()) / len(analysis)
        avg_without_rig = sum(a["without_rig"]["percentage"] for a in analysis.values()) / len(analysis)
        avg_improvement = sum(a["rig_improvement"]["percentage"] for a in analysis.values()) / len(analysis)

        summary = {
            "best_overall_with_rig": {
                "agent": best_with_rig[0],
                "percentage": best_with_rig[1]["with_rig"]["percentage"]
            },
            "best_overall_without_rig": {
                "agent": best_without_rig[0],
                "percentage": best_without_rig[1]["without_rig"]["percentage"]
            },
            "most_rig_improvement": {
                "agent": most_improvement[0],
                "improvement_percentage": most_improvement[1]["rig_improvement"]["percentage"]
            },
            "least_rig_improvement": {
                "agent": least_improvement[0],
                "improvement_percentage": least_improvement[1]["rig_improvement"]["percentage"]
            },
            "average_with_rig": round(avg_with_rig, 1),
            "average_without_rig": round(avg_without_rig, 1),
            "average_rig_improvement": round(avg_improvement, 1)
        }

        # Calculate timing statistics if available
        agents_with_timing = {name: data for name, data in analysis.items() if "timing" in data}
        if agents_with_timing:
            avg_time_with_rig = sum(a["timing"]["time_with_rig_seconds"] for a in agents_with_timing.values()) / len(agents_with_timing)
            avg_time_without_rig = sum(a["timing"]["time_without_rig_seconds"] for a in agents_with_timing.values()) / len(agents_with_timing)
            avg_time_saved = sum(a["timing"]["time_saved_seconds"] for a in agents_with_timing.values()) / len(agents_with_timing)
            avg_time_reduction = sum(a["timing"]["time_reduction_percentage"] for a in agents_with_timing.values()) / len(agents_with_timing)

            # Find fastest and most time saved (only among agents with timing data)
            fastest_with_rig = min(agents_with_timing.items(), key=lambda x: x[1]["timing"]["time_with_rig_seconds"])
            fastest_without_rig = min(agents_with_timing.items(), key=lambda x: x[1]["timing"]["time_without_rig_seconds"])
            most_time_saved = max(agents_with_timing.items(), key=lambda x: x[1]["timing"]["time_saved_seconds"])
            highest_time_reduction = max(agents_with_timing.items(), key=lambda x: x[1]["timing"]["time_reduction_percentage"])

            summary["timing"] = {
                "average_time_with_rig_seconds": round(avg_time_with_rig, 2),
                "average_time_without_rig_seconds": round(avg_time_without_rig, 2),
                "average_time_saved_seconds": round(avg_time_saved, 2),
                "average_time_reduction_percentage": round(avg_time_reduction, 1),
                "fastest_with_rig": {
                    "agent": fastest_with_rig[0],
                    "time_seconds": fastest_with_rig[1]["timing"]["time_with_rig_seconds"]
                },
                "fastest_without_rig": {
                    "agent": fastest_without_rig[0],
                    "time_seconds": fastest_without_rig[1]["timing"]["time_without_rig_seconds"]
                },
                "most_time_saved": {
                    "agent": most_time_saved[0],
                    "time_saved_seconds": most_time_saved[1]["timing"]["time_saved_seconds"],
                    "time_reduction_percentage": most_time_saved[1]["timing"]["time_reduction_percentage"]
                },
                "highest_time_reduction_percentage": {
                    "agent": highest_time_reduction[0],
                    "time_reduction_percentage": highest_time_reduction[1]["timing"]["time_reduction_percentage"]
                }
            }

        return summary

    def build_category_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build category-based analysis showing performance by question category.

        Args:
            results: Raw results dictionary

        Returns:
            Category analysis dictionary
        """
        # Group questions by category
        questions_by_category = {}
        for q in self.questions:
            category = q.get("category", "unknown")
            if category not in questions_by_category:
                questions_by_category[category] = []
            questions_by_category[category].append(q)

        # Group agents by RIG/NORIG
        agents_grouped = {}
        for agent_name in results.keys():
            # Skip the "questions" key (question-centric data)
            if agent_name == "questions":
                continue

            if "_RIG" in agent_name:
                base_name = agent_name.replace("_RIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["with_rig"] = agent_name
            elif "_NORIG" in agent_name:
                base_name = agent_name.replace("_NORIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["without_rig"] = agent_name

        category_analysis = {}

        # Analyze each category
        for category, category_questions in questions_by_category.items():
            question_ids_in_category = {q["id"] for q in category_questions}
            total_questions = len(category_questions)

            # Calculate aggregate scores across all agents
            total_with_rig_score = 0
            total_without_rig_score = 0
            total_max = total_questions * len(agents_grouped)  # questions * agents

            per_agent_data = {}

            for base_name, agent_data in agents_grouped.items():
                if "with_rig" not in agent_data or "without_rig" not in agent_data:
                    continue

                with_rig_name = agent_data["with_rig"]
                without_rig_name = agent_data["without_rig"]

                # Count correct answers in this category from question-centric data
                with_rig_score = sum(
                    1 for q in results["questions"]
                    if q["id"] in question_ids_in_category
                    and with_rig_name in q
                    and q[with_rig_name]["score"] == 1
                )
                without_rig_score = sum(
                    1 for q in results["questions"]
                    if q["id"] in question_ids_in_category
                    and without_rig_name in q
                    and q[without_rig_name]["score"] == 1
                )

                total_with_rig_score += with_rig_score
                total_without_rig_score += without_rig_score

                with_rig_pct = self.calculate_percentage(with_rig_score, total_questions)
                without_rig_pct = self.calculate_percentage(without_rig_score, total_questions)
                improvement = with_rig_pct - without_rig_pct

                per_agent_data[base_name] = {
                    "with_rig": with_rig_pct,
                    "without_rig": without_rig_pct,
                    "improvement": round(improvement, 1)
                }

            # Calculate overall category stats
            with_rig_pct = self.calculate_percentage(total_with_rig_score, total_max)
            without_rig_pct = self.calculate_percentage(total_without_rig_score, total_max)
            improvement_abs = total_with_rig_score - total_without_rig_score
            improvement_pct = self.calculate_percentage(improvement_abs, total_max)

            category_analysis[category] = {
                "total_questions": total_questions,
                "with_rig": {
                    "score": total_with_rig_score,
                    "max": total_max,
                    "percentage": with_rig_pct
                },
                "without_rig": {
                    "score": total_without_rig_score,
                    "max": total_max,
                    "percentage": without_rig_pct
                },
                "improvement": {
                    "absolute": improvement_abs,
                    "percentage": improvement_pct
                },
                "per_agent": per_agent_data
            }

        return category_analysis

    def build_question_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build question-level insights showing cross-agent performance.

        Args:
            results: Raw results dictionary

        Returns:
            Question insights dictionary
        """
        # Group agents by RIG/NORIG
        agents_grouped = {}
        for agent_name in results.keys():
            # Skip the "questions" key (question-centric data)
            if agent_name == "questions":
                continue

            if "_RIG" in agent_name:
                base_name = agent_name.replace("_RIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["with_rig"] = agent_name
            elif "_NORIG" in agent_name:
                base_name = agent_name.replace("_NORIG", "")
                if base_name not in agents_grouped:
                    agents_grouped[base_name] = {}
                agents_grouped[base_name]["without_rig"] = agent_name

        total_agents = len(agents_grouped)

        # Analyze each question
        question_stats = []

        for q in self.questions:
            q_id = q["id"]

            # Find the question in the question-centric data
            question_data = next((qd for qd in results["questions"] if qd["id"] == q_id), None)
            if not question_data:
                continue

            # Count how many agents got it right
            correct_with_rig = []
            correct_without_rig = []
            improvements = []

            for base_name, agent_data in agents_grouped.items():
                if "with_rig" not in agent_data or "without_rig" not in agent_data:
                    continue

                with_rig_name = agent_data["with_rig"]
                without_rig_name = agent_data["without_rig"]

                # Skip if agent doesn't have data for this question
                if with_rig_name not in question_data or without_rig_name not in question_data:
                    continue

                # Get scores from question-centric data
                with_rig_score = question_data[with_rig_name]["score"]
                without_rig_score = question_data[without_rig_name]["score"]

                if with_rig_score == 1:
                    correct_with_rig.append(base_name)

                if without_rig_score == 1:
                    correct_without_rig.append(base_name)

                # Calculate improvement for this agent on this question
                improvements.append(with_rig_score - without_rig_score)

            success_rate_with_rig = self.calculate_percentage(len(correct_with_rig), total_agents)
            success_rate_without_rig = self.calculate_percentage(len(correct_without_rig), total_agents)
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0

            question_stats.append({
                "id": q_id,
                "question": q["question"],
                "difficulty": q["difficulty"],
                "category": q["category"],
                "success_rate_with_rig": success_rate_with_rig,
                "success_rate_without_rig": success_rate_without_rig,
                "agents_correct_with_rig": correct_with_rig,
                "agents_correct_without_rig": correct_without_rig,
                "avg_improvement": round(avg_improvement * 100, 1)  # Convert to percentage
            })

        # Sort and categorize
        question_stats.sort(key=lambda x: x["success_rate_with_rig"])

        hardest_questions = [q for q in question_stats if q["success_rate_with_rig"] < 100.0][:5]
        easiest_questions = [q for q in question_stats if q["success_rate_with_rig"] == 100.0]

        question_stats.sort(key=lambda x: x["avg_improvement"], reverse=True)
        most_rig_sensitive = [q for q in question_stats if q["avg_improvement"] > 0][:5]
        rig_insensitive = [q for q in question_stats if q["avg_improvement"] == 0]

        # Find unanimous failures
        unanimous_failures_with_rig = [q["id"] for q in question_stats if q["success_rate_with_rig"] == 0]
        unanimous_failures_without_rig = [q["id"] for q in question_stats if q["success_rate_without_rig"] == 0]

        return {
            "hardest_questions": hardest_questions,
            "easiest_questions": easiest_questions,
            "most_rig_sensitive": most_rig_sensitive,
            "rig_insensitive": rig_insensitive,
            "unanimous_failures_with_rig": unanimous_failures_with_rig,
            "unanimous_failures_without_rig": unanimous_failures_without_rig
        }

    def analyze_rig_effectiveness(self, comparative_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze RIG effectiveness patterns.

        Args:
            comparative_analysis: Comparative analysis dictionary

        Returns:
            RIG effectiveness analysis dictionary
        """
        if not comparative_analysis:
            return {}

        # Analyze by difficulty
        difficulty_stats = {}
        for difficulty in ["easy", "medium", "hard"]:
            improvements = []
            agents_benefited = 0

            for base_name, agent_data in comparative_analysis.items():
                improvement_pct = agent_data["rig_improvement"]["by_difficulty"][difficulty]["percentage"]
                improvements.append(improvement_pct)
                if improvement_pct > 0:
                    agents_benefited += 1

            avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0

            difficulty_stats[difficulty] = {
                "avg_improvement": round(avg_improvement, 1),
                "agents_benefited": agents_benefited
            }

        # Baseline vs improvement correlation
        correlation_data = []
        for base_name, agent_data in comparative_analysis.items():
            baseline_pct = agent_data["without_rig"]["percentage"]
            improvement_pct = agent_data["rig_improvement"]["percentage"]

            correlation_data.append({
                "agent": base_name,
                "baseline_pct": baseline_pct,
                "improvement_pct": improvement_pct
            })

        # Sort by baseline to show pattern
        correlation_data.sort(key=lambda x: x["baseline_pct"], reverse=True)

        # Determine correlation pattern
        if correlation_data:
            # Simple check: does highest baseline have lowest improvement?
            highest_baseline = correlation_data[0]
            lowest_baseline = correlation_data[-1]

            if highest_baseline["improvement_pct"] < lowest_baseline["improvement_pct"]:
                correlation_note = "Agents with higher baseline show less improvement from RIG"
            elif highest_baseline["improvement_pct"] > lowest_baseline["improvement_pct"]:
                correlation_note = "Agents with higher baseline show more improvement from RIG"
            else:
                correlation_note = "No clear correlation between baseline performance and RIG improvement"
        else:
            correlation_note = "Insufficient data"

        return {
            "by_difficulty": difficulty_stats,
            "correlation": {
                "pattern": correlation_note,
                "data": correlation_data
            }
        }

    def analyze_timing_insights(self, comparative_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze timing patterns and correlations.

        Args:
            comparative_analysis: Comparative analysis dictionary

        Returns:
            Timing insights dictionary
        """
        agents_with_timing = {name: data for name, data in comparative_analysis.items() if "timing" in data}

        if not agents_with_timing:
            raise ValueError(
                f"No timing data available for agents. "
                f"Answer files must include 'completion_time_seconds' field."
            )

        # Speed vs Accuracy correlation (with RIG)
        speed_accuracy_with_rig = []
        for name, data in agents_with_timing.items():
            speed_accuracy_with_rig.append({
                "agent": name,
                "time_seconds": data["timing"]["time_with_rig_seconds"],
                "score_percentage": data["with_rig"]["percentage"],
                "efficiency_score_per_second": data["timing"]["efficiency_with_rig_score_per_second"]
            })
        speed_accuracy_with_rig.sort(key=lambda x: x["time_seconds"])

        # Speed vs Accuracy correlation (without RIG)
        speed_accuracy_without_rig = []
        for name, data in agents_with_timing.items():
            speed_accuracy_without_rig.append({
                "agent": name,
                "time_seconds": data["timing"]["time_without_rig_seconds"],
                "score_percentage": data["without_rig"]["percentage"],
                "efficiency_score_per_second": data["timing"]["efficiency_without_rig_score_per_second"]
            })
        speed_accuracy_without_rig.sort(key=lambda x: x["time_seconds"])

        # Time reduction vs score improvement correlation
        time_vs_score_improvement = []
        for name, data in agents_with_timing.items():
            time_vs_score_improvement.append({
                "agent": name,
                "time_reduction_percentage": data["timing"]["time_reduction_percentage"],
                "score_improvement_percentage": data["rig_improvement"]["percentage"],
                "time_saved_seconds": data["timing"]["time_saved_seconds"],
                "score_points_gained": data["rig_improvement"]["absolute"]
            })

        # Sort by time reduction to show pattern
        time_vs_score_improvement.sort(key=lambda x: x["time_reduction_percentage"], reverse=True)

        # Calculate correlation note
        if len(time_vs_score_improvement) >= 2:
            highest_time_reduction = time_vs_score_improvement[0]
            lowest_time_reduction = time_vs_score_improvement[-1]

            if highest_time_reduction["score_improvement_percentage"] > lowest_time_reduction["score_improvement_percentage"]:
                correlation_note = "Greater time reduction correlates with better score improvement"
            elif highest_time_reduction["score_improvement_percentage"] < lowest_time_reduction["score_improvement_percentage"]:
                correlation_note = "Greater time reduction correlates with less score improvement"
            else:
                correlation_note = "No clear correlation between time reduction and score improvement"
        else:
            correlation_note = "Insufficient data for correlation"

        # Calculate efficiency stats
        efficiencies_with_rig = [data["timing"]["efficiency_with_rig_score_per_second"] for data in agents_with_timing.values()]
        efficiencies_without_rig = [data["timing"]["efficiency_without_rig_score_per_second"] for data in agents_with_timing.values()]

        avg_efficiency_with_rig = sum(efficiencies_with_rig) / len(efficiencies_with_rig)
        avg_efficiency_without_rig = sum(efficiencies_without_rig) / len(efficiencies_without_rig)
        efficiency_improvement = ((avg_efficiency_with_rig - avg_efficiency_without_rig) / avg_efficiency_without_rig * 100) if avg_efficiency_without_rig > 0 else 0

        return {
            "speed_vs_accuracy_with_rig": speed_accuracy_with_rig,
            "speed_vs_accuracy_without_rig": speed_accuracy_without_rig,
            "time_reduction_vs_score_improvement": {
                "correlation_note": correlation_note,
                "data": time_vs_score_improvement
            },
            "efficiency_analysis": {
                "avg_efficiency_with_rig_score_per_second": round(avg_efficiency_with_rig, 4),
                "avg_efficiency_without_rig_score_per_second": round(avg_efficiency_without_rig, 4),
                "efficiency_improvement_percentage": round(efficiency_improvement, 1)
            }
        }

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Save analysis results to answers_analysis.json.

        Args:
            results: Analysis results dictionary
        """
        output_path = os.path.join(self.deterministic_path, "answers_analysis.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"[LOG] Results saved to: {output_path}")


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Analyze and score agent answers against expected answers"
    )
    parser.add_argument(
        "relative_path",
        help="Relative path (e.g., 'cmake/cmake_hello_world')"
    )
    args = parser.parse_args()

    try:
        print("=" * 60)
        print(f"Starting answer analysis for: {args.relative_path}")
        print("=" * 60)

        # Get script directory and build path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        deterministic_path = os.path.join(script_dir, args.relative_path)

        print(f"[LOG] Analysis directory: {deterministic_path}")

        # Validate directory exists
        if not os.path.exists(deterministic_path):
            raise FileNotFoundError(f"Directory not found: {deterministic_path}")

        # Run analysis
        runner = AnalysisRunner(deterministic_path)
        results = runner.run_analysis()

        # Build comparative analysis
        print("[LOG] Building comparative analysis...")
        comparative_analysis = runner.build_comparative_analysis(results)

        # Build category analysis
        print("[LOG] Building category analysis...")
        category_analysis = runner.build_category_analysis(results)

        # Build question insights
        print("[LOG] Building question insights...")
        question_insights = runner.build_question_insights(results)

        # Analyze RIG effectiveness
        print("[LOG] Analyzing RIG effectiveness patterns...")
        rig_effectiveness = runner.analyze_rig_effectiveness(comparative_analysis)

        # Analyze timing insights
        print("[LOG] Analyzing timing patterns and correlations...")
        timing_insights = runner.analyze_timing_insights(comparative_analysis)

        # Build summary
        print("[LOG] Building summary statistics...")
        summary = runner.build_summary(comparative_analysis)

        # Combine into final output
        output = {
            "results": results,
            "analysis": {
                "by_agent": comparative_analysis,
                "by_category": category_analysis,
                "question_insights": question_insights,
                "rig_effectiveness": rig_effectiveness,
                "timing_insights": timing_insights,
                "summary": summary
            }
        }

        # Save results
        runner.save_results(output)

        # Print summary
        print()
        print("=" * 60)
        print("Summary:")
        print(f"  Best with RIG: {summary['best_overall_with_rig']['agent']} ({summary['best_overall_with_rig']['percentage']}%)")
        print(f"  Best without RIG: {summary['best_overall_without_rig']['agent']} ({summary['best_overall_without_rig']['percentage']}%)")
        print(f"  Most RIG improvement: {summary['most_rig_improvement']['agent']} (+{summary['most_rig_improvement']['improvement_percentage']}%)")
        print(f"  Average with RIG: {summary['average_with_rig']}%")
        print(f"  Average without RIG: {summary['average_without_rig']}%")
        print()
        print("RIG Effectiveness by Difficulty:")
        for difficulty in ["easy", "medium", "hard"]:
            stats = rig_effectiveness["by_difficulty"][difficulty]
            print(f"  {difficulty.capitalize()}: avg improvement = {stats['avg_improvement']}%")
        print()

        # Print timing summary if available
        if "timing" in summary:
            print("Timing Summary:")
            timing = summary["timing"]
            print(f"  Average time with RIG: {timing['average_time_with_rig_seconds']}s")
            print(f"  Average time without RIG: {timing['average_time_without_rig_seconds']}s")
            print(f"  Average time saved: {timing['average_time_saved_seconds']}s ({timing['average_time_reduction_percentage']}% faster)")
            print(f"  Fastest with RIG: {timing['fastest_with_rig']['agent']} ({timing['fastest_with_rig']['time_seconds']}s)")
            print(f"  Most time saved: {timing['most_time_saved']['agent']} ({timing['most_time_saved']['time_saved_seconds']}s / {timing['most_time_saved']['time_reduction_percentage']}%)")

            # Print timing insights if available
            if "note" not in timing_insights:
                print()
                print("Timing Insights:")
                efficiency = timing_insights["efficiency_analysis"]
                print(f"  Efficiency with RIG: {efficiency['avg_efficiency_with_rig_score_per_second']} score/second")
                print(f"  Efficiency without RIG: {efficiency['avg_efficiency_without_rig_score_per_second']} score/second")
                print(f"  Efficiency improvement: {efficiency['efficiency_improvement_percentage']}%")

                correlation = timing_insights["time_reduction_vs_score_improvement"]
                print(f"  Time vs Score correlation: {correlation['correlation_note']}")
            print()

        print(f"Hardest questions: {len(question_insights['hardest_questions'])} questions")
        print(f"Most RIG-sensitive: {len(question_insights['most_rig_sensitive'])} questions")
        print("=" * 60)
        print("Analysis complete!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
