"""
Unit tests for agent executors.

Tests basic functionality of AgentExecutor classes without requiring
actual CLI tools to be installed.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from agent_executors import (
    AgentExecutor,
    ClaudeAgentExecutor,
    CursorAgentExecutor,
    CodexAgentExecutor
)


class TestAgentExecutor(unittest.TestCase):
    """Test base AgentExecutor functionality."""

    def setUp(self):
        """Create a test executor and temporary files."""
        # Use ClaudeAgentExecutor as concrete implementation for testing base class
        self.executor = ClaudeAgentExecutor()

        # Create a temporary test repository
        self.test_repo = tempfile.mkdtemp(prefix="test_repo_")
        test_file = os.path.join(self.test_repo, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_repo):
            shutil.rmtree(self.test_repo, ignore_errors=True)

    def test_convert_to_wsl_path(self):
        """Test Windows to WSL path conversion."""
        test_cases = [
            ("C:\\Users\\test", "/mnt/c/Users/test"),
            ("D:\\projects\\repo", "/mnt/d/projects/repo"),
            ("C:\\path\\with\\spaces", "/mnt/c/path/with/spaces"),
        ]

        for win_path, expected_wsl in test_cases:
            result = self.executor._convert_to_wsl_path(win_path)
            self.assertEqual(result, expected_wsl)

    def test_create_temp_repo_copy(self):
        """Test temporary repository copy creation."""
        temp_copy = self.executor._create_temp_repo_copy(self.test_repo)

        try:
            # Verify temp copy exists
            self.assertTrue(os.path.exists(temp_copy))

            # Verify test file was copied
            test_file_copy = os.path.join(temp_copy, "test.txt")
            self.assertTrue(os.path.exists(test_file_copy))

            # Verify content matches
            with open(test_file_copy, 'r') as f:
                content = f.read()
            self.assertEqual(content, "test content")

        finally:
            # Cleanup
            self.executor._cleanup_temp_repo(temp_copy)

    def test_create_temp_repo_copy_nonexistent(self):
        """Test that copying nonexistent repo raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.executor._create_temp_repo_copy("/nonexistent/path")

    def test_cleanup_temp_repo(self):
        """Test temporary repository cleanup."""
        temp_copy = self.executor._create_temp_repo_copy(self.test_repo)

        # Cleanup
        self.executor._cleanup_temp_repo(temp_copy)

        # Verify temp directory is deleted
        self.assertFalse(os.path.exists(temp_copy))

    def test_parse_json_response_valid(self):
        """Test parsing valid answers.json file."""
        # Create answers.json in test repo
        answers_data = [
            {"id": 1, "answer": "test answer"},
            {"id": 2, "answer": ["item1", "item2"]}
        ]
        answers_file = os.path.join(self.test_repo, "answers.json")
        with open(answers_file, 'w') as f:
            json.dump(answers_data, f)

        # Parse
        result = self.executor._parse_json_response(self.test_repo)

        # Verify
        self.assertEqual(result, answers_data)

    def test_parse_json_response_missing(self):
        """Test parsing when answers.json is missing."""
        with self.assertRaises(FileNotFoundError):
            self.executor._parse_json_response(self.test_repo)

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON."""
        # Create invalid JSON file
        answers_file = os.path.join(self.test_repo, "answers.json")
        with open(answers_file, 'w') as f:
            f.write("not valid json {{{")

        # Should raise JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            self.executor._parse_json_response(self.test_repo)


class TestClaudeAgentExecutor(unittest.TestCase):
    """Test ClaudeAgentExecutor specific functionality."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ClaudeAgentExecutor()
        self.assertEqual(executor.agent_name, "claude")


class TestCursorAgentExecutor(unittest.TestCase):
    """Test CursorAgentExecutor specific functionality."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = CursorAgentExecutor()
        self.assertEqual(executor.agent_name, "cursor")


class TestCodexAgentExecutor(unittest.TestCase):
    """Test CodexAgentExecutor specific functionality."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = CodexAgentExecutor()
        self.assertEqual(executor.agent_name, "codex")


class TestIntegrationScenarios(unittest.TestCase):
    """
    Integration tests for complete scenarios.

    Note: These tests don't actually call CLI agents, but test the flow
    with mock responses.
    """

    def setUp(self):
        """Create test repository with mock answers."""
        self.test_repo = tempfile.mkdtemp(prefix="test_integration_")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_repo):
            shutil.rmtree(self.test_repo, ignore_errors=True)

    def test_execute_with_mock_success(self):
        """Test execution flow when agent succeeds."""
        executor = ClaudeAgentExecutor()

        # Create a mock _run_agent that creates answers.json
        def mock_run_agent(prompt, repo_path):
            answers_file = os.path.join(repo_path, "answers.json")
            answers = [{"id": 1, "answer": "test"}]
            with open(answers_file, 'w') as f:
                json.dump(answers, f)

        # Replace _run_agent with mock
        executor._run_agent = mock_run_agent

        # Execute
        result = executor.execute("test prompt", self.test_repo)

        # Verify success
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_execute_with_mock_failure(self):
        """Test execution flow when agent fails."""
        executor = ClaudeAgentExecutor()

        # Create a mock _run_agent that raises exception
        def mock_run_agent(prompt, repo_path):
            raise RuntimeError("Agent failed")

        # Replace _run_agent with mock
        executor._run_agent = mock_run_agent

        # Execute
        result = executor.execute("test prompt", self.test_repo)

        # Verify error result
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("claude execution failed", result["error"])


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()
