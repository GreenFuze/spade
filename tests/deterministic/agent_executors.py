"""
Agent executors for running claude, cursor, and codex CLI agents.

This module provides OOP abstractions for executing different CLI agents
with proper isolation, temp directory management, and error handling.

IMPORTANT: cursor-agent and codex require directory trust
--------------------------------------------
cursor-agent and codex require directories to be trusted before execution.
These executors use fixed workspace directories that must be trusted once manually:

    cursor: tests/deterministic/wsl_runners/_cursor_workspace
    codex:  tests/deterministic/wsl_runners/_codex_workspace

To trust these directories:
1. Run the test once (it will fail with a trust prompt)
2. Manually trust the directory when prompted by the agent
3. Subsequent runs will succeed without re-prompting

The workspace contents are cleaned before each run to ensure test isolation.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

# Import validation from wsl_runners
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'wsl_runners'))
from validation import validate_answers_file, extract_question_ids_from_prompt


class AgentExecutor(ABC):
    """
    Abstract base class for CLI agent executors.

    Provides common functionality for:
    - Creating temporary repository copies for isolation
    - Converting Windows paths to WSL paths
    - Parsing JSON responses
    - Cleanup operations
    """

    def __init__(self, agent_name: str):
        """
        Initialize agent executor.

        Args:
            agent_name: Name of the agent (e.g., 'claude', 'cursor', 'codex')
        """
        self.agent_name = agent_name

    def execute(self, prompt: str, repo_path: str) -> Dict[str, Any]:
        """
        Execute the agent with the given prompt on a temporary copy of the repository.

        Args:
            prompt: The prompt to send to the agent
            repo_path: Path to the repository to work on

        Returns:
            Dictionary containing parsed answers or error information
        """
        # Create temp copy for isolation
        temp_repo_path = self._create_temp_repo_copy(repo_path)
        cleanup_workspace = True  # Only cleanup if successful

        try:
            # Execute the agent
            self._run_agent(prompt, temp_repo_path)

            # Parse response
            result = self._parse_json_response(temp_repo_path)

            return result

        except TimeoutError as e:
            # Agent timed out - check if answers were completed anyway
            print(f"[EXECUTOR-LOG] {self.agent_name} timed out, checking if answers are complete...")

            # Extract expected question IDs from prompt
            expected_ids = extract_question_ids_from_prompt(prompt)

            # Check if answers.json exists and is complete
            is_valid, error_msg = validate_answers_file(temp_repo_path, expected_ids)

            if is_valid:
                print(f"[EXECUTOR-LOG] ✓ Answers are complete despite timeout!")
                # Parse and return the answers
                result = self._parse_json_response(temp_repo_path)
                return result
            else:
                print(f"[EXECUTOR-LOG] ✗ Answers incomplete: {error_msg}")
                cleanup_workspace = False  # Keep workspace for debugging
                print(f"[EXECUTOR-LOG] Workspace preserved for debugging at: {temp_repo_path}")
                return {"error": f"{self.agent_name} timed out and answers incomplete: {error_msg}"}

        except Exception as e:
            # Return error result
            cleanup_workspace = False  # Keep workspace for debugging
            print(f"[EXECUTOR-LOG] Error occurred, workspace preserved for debugging at: {temp_repo_path}")
            return {"error": f"{self.agent_name} execution failed: {str(e)}"}

        finally:
            # Only cleanup if successful
            if cleanup_workspace:
                self._cleanup_temp_repo(temp_repo_path)
            else:
                print(f"[EXECUTOR-LOG] Skipping workspace cleanup due to error")

    @abstractmethod
    def _run_agent(self, prompt: str, repo_path: str) -> None:
        """
        Run the specific agent CLI command.

        Args:
            prompt: The prompt to send to the agent
            repo_path: Path to the repository (temp copy)

        Raises:
            Exception if agent execution fails
        """
        pass

    def _write_prompt_file(self, prompt: str, repo_path: str) -> str:
        """
        Write prompt to a temporary file in the repository.

        Args:
            prompt: The prompt content
            repo_path: Path to the repository

        Returns:
            Path to the prompt file
        """
        prompt_file = os.path.join(repo_path, ".agent_prompt.txt")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        return prompt_file

    def _create_temp_repo_copy(self, repo_path: str) -> str:
        """
        Create a temporary copy of the repository for isolation.

        Args:
            repo_path: Path to the original repository

        Returns:
            Path to the temporary repository copy

        Raises:
            FileNotFoundError if repo_path doesn't exist
            OSError if copy operation fails
        """
        # Validate source exists
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix=f"{self.agent_name}_repo_")

        # Copy repository contents
        try:
            # Get repo name from path
            repo_name = os.path.basename(os.path.normpath(repo_path))
            temp_repo_path = os.path.join(temp_dir, repo_name)

            # Copy entire directory tree
            shutil.copytree(repo_path, temp_repo_path, symlinks=True)

            return temp_repo_path

        except Exception as e:
            # Cleanup on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise OSError(f"Failed to create temp repository copy: {str(e)}")

    def _cleanup_temp_repo(self, temp_path: str) -> None:
        """
        Delete the temporary repository copy.

        Args:
            temp_path: Path to the temporary repository
        """
        if os.path.exists(temp_path):
            # Get parent temp directory
            temp_dir = os.path.dirname(temp_path)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_json_response(self, repo_path: str) -> Dict[str, Any]:
        """
        Parse the answers.json file created by the agent and merge with timing metadata.

        Args:
            repo_path: Path to the repository where answers.json should be

        Returns:
            Parsed JSON dictionary with timing metadata merged at top level.
            If answers.json is an array, it's wrapped as {"answers": [...], "agent_completion_time_seconds": X}

        Raises:
            FileNotFoundError if answers.json doesn't exist
            json.JSONDecodeError if JSON is invalid
        """
        answers_file = os.path.join(repo_path, "answers.json")

        # Check if file exists
        if not os.path.exists(answers_file):
            raise FileNotFoundError(f"Agent did not create answers.json at: {answers_file}")

        # Read and parse answers JSON
        with open(answers_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse JSON (will raise JSONDecodeError if invalid)
        answers_data = json.loads(content)

        # Wrap in object if it's an array
        if isinstance(answers_data, list):
            result = {"answers": answers_data}
        elif isinstance(answers_data, dict):
            result = answers_data
        else:
            raise ValueError(f"Unexpected answers.json format: {type(answers_data)}")

        # Read timing metadata if it exists
        metadata_file = os.path.join(repo_path, "answers_metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Merge timing info at top level
                if "agent_completion_time_seconds" in metadata:
                    result["agent_completion_time_seconds"] = metadata["agent_completion_time_seconds"]
                    print(f"[EXECUTOR-LOG] Merged timing metadata: {metadata['agent_completion_time_seconds']} seconds")
            except Exception as e:
                print(f"[EXECUTOR-LOG] Warning: Failed to read timing metadata: {e}")

        return result

    def _convert_to_wsl_path(self, win_path: str) -> str:
        """
        Convert Windows path to WSL path format.

        Examples:
            C:\\Users\\... -> /mnt/c/Users/...
            D:\\projects\\... -> /mnt/d/projects/...

        Args:
            win_path: Windows-style path

        Returns:
            WSL-style path
        """
        # Normalize path
        win_path = os.path.normpath(win_path)

        # Convert backslashes to forward slashes
        wsl_path = win_path.replace('\\', '/')

        # Handle drive letter (C: -> /mnt/c)
        if len(wsl_path) >= 2 and wsl_path[1] == ':':
            drive_letter = wsl_path[0].lower()
            wsl_path = f"/mnt/{drive_letter}{wsl_path[2:]}"

        return wsl_path

    def _run_wsl_command(self, command: str) -> subprocess.CompletedProcess:
        """
        Run a command in WSL.

        Args:
            command: The bash command to run

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError if command fails
        """
        wsl_command = ["wsl.exe", "-e", "bash", "-c", command]

        print(f"[EXECUTOR-LOG] Running WSL command for {self.agent_name}")
        print(f"[EXECUTOR-LOG] Command: {command[:200]}..." if len(command) > 200 else f"[EXECUTOR-LOG] Command: {command}")

        try:
            
            print(f'-----\nrunning agent\n{wsl_command}\n------')
            
            result = subprocess.run(
                wsl_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=1320  # 22 minutes - generous timeout for agent execution (1200s agent + buffer)
            )

            print(f"[EXECUTOR-LOG] WSL command completed with return code: {result.returncode}")
            if result.stdout:
                print(f"[EXECUTOR-LOG] stdout ({len(result.stdout)} chars):")
                print(result.stdout)
            if result.stderr:
                print(f"[EXECUTOR-LOG] stderr ({len(result.stderr)} chars):")
                print(result.stderr)

            return result

        except subprocess.CalledProcessError as e:
            # WSL command failed - capture all output for diagnostics
            print(f"[EXECUTOR-LOG] WSL command FAILED with exit code: {e.returncode}")
            print(f"[EXECUTOR-LOG] Agent {self.agent_name} returned error")

            stdout_str = ""
            stderr_str = ""

            if e.stdout:
                stdout_str = e.stdout if isinstance(e.stdout, str) else e.stdout.decode()
                print(f"[EXECUTOR-LOG] stdout ({len(stdout_str)} chars):")
                print(stdout_str)

            if e.stderr:
                stderr_str = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
                print(f"[EXECUTOR-LOG] stderr ({len(stderr_str)} chars):")
                print(stderr_str)

            # Re-raise with detailed error message including output
            error_msg = f"{self.agent_name} execution failed with exit code {e.returncode}"
            if stdout_str:
                error_msg += f"\nSTDOUT:\n{stdout_str}"
            if stderr_str:
                error_msg += f"\nSTDERR:\n{stderr_str}"

            raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired as e:
            print(f"[EXECUTOR-LOG] WSL command TIMED OUT after 1320 seconds")
            print(f"[EXECUTOR-LOG] Agent {self.agent_name} did not complete in time")
            if e.stdout:
                print(f"[EXECUTOR-LOG] Partial stdout ({len(e.stdout)} chars):")
                print(e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout)
            if e.stderr:
                print(f"[EXECUTOR-LOG] Partial stderr ({len(e.stderr)} chars):")
                print(e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr)
            raise TimeoutError(f"{self.agent_name} execution timed out after 1320 seconds")


class ClaudeAgentExecutor(AgentExecutor):
    """
    Executor for Claude CLI agent using claude-agent-sdk.

    Uses a fixed workspace directory (tests/deterministic/wsl_runners/_claude_workspace)
    for easier debugging and consistency with other agents.
    """

    def __init__(self):
        super().__init__("claude")

    def _create_temp_repo_copy(self, repo_path: str) -> str:
        """
        Create a fixed workspace copy for claude (for easier debugging).

        Unlike the base class which creates random temp directories, this uses a
        fixed directory that persists for debugging, similar to cursor and codex.

        The workspace is cleaned before each run to ensure test isolation.

        Args:
            repo_path: Path to the original repository

        Returns:
            Path to the workspace repository copy

        Raises:
            FileNotFoundError if repo_path doesn't exist
            OSError if copy operation fails
        """
        # Validate source exists
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        # Fixed workspace directory for claude
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(script_dir, "wsl_runners", "_claude_workspace")

        # Create workspace directory if it doesn't exist
        os.makedirs(workspace_dir, exist_ok=True)

        # Clean workspace contents if it exists
        if os.path.exists(workspace_dir):
            print(f"[EXECUTOR-LOG] Cleaning existing claude workspace contents: {workspace_dir}")
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

        # Copy repository contents
        try:
            # Get repo name from path
            repo_name = os.path.basename(os.path.normpath(repo_path))
            workspace_repo_path = os.path.join(workspace_dir, repo_name)

            # Copy entire directory tree
            shutil.copytree(repo_path, workspace_repo_path, symlinks=True)

            print(f"[EXECUTOR-LOG] Created claude workspace at: {workspace_repo_path}")
            return workspace_repo_path

        except Exception as e:
            # Cleanup contents on failure but keep directory
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            raise OSError(f"Failed to create claude workspace copy: {str(e)}")

    def _cleanup_temp_repo(self, temp_path: str) -> None:
        """
        Clean up the claude workspace contents.

        Removes the workspace contents but keeps the _claude_workspace directory itself
        (for easier debugging and re-runs).

        Args:
            temp_path: Path to the workspace repository
        """
        if os.path.exists(temp_path):
            # Get the workspace directory (parent of the repo copy)
            workspace_dir = os.path.dirname(temp_path)
            print(f"[EXECUTOR-LOG] Cleaning claude workspace contents: {workspace_dir}")
            # Remove all contents but keep the directory itself
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

    def _run_agent(self, prompt: str, repo_path: str) -> None:
        """
        Run Claude agent using WSL runner script.

        Args:
            prompt: The prompt to send to Claude
            repo_path: Path to the repository (temp copy)
        """
        # Write prompt to file
        prompt_file = self._write_prompt_file(prompt, repo_path)

        # Convert paths to WSL format
        wsl_prompt_file = self._convert_to_wsl_path(prompt_file)
        wsl_repo_path = self._convert_to_wsl_path(repo_path)

        # Get path to runner script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        runner_script = os.path.join(script_dir, "wsl_runners", "run_claude.py")
        wsl_runner_script = self._convert_to_wsl_path(runner_script)

        # Build command to run the WSL runner script
        command = f'python3 "{wsl_runner_script}" "{wsl_prompt_file}" "{wsl_repo_path}"'

        # Execute in WSL
        self._run_wsl_command(command)


class CursorAgentExecutor(AgentExecutor):
    """
    Executor for Cursor CLI agent using cursor-agent.

    cursor-agent requires directories to be trusted before execution. This executor
    uses a fixed workspace directory (tests/deterministic/wsl_runners/_cursor_workspace)
    that must be trusted once manually, then is reused for all subsequent runs.

    The workspace contents are cleaned before each run to ensure test isolation.
    """

    def __init__(self):
        super().__init__("cursor")

    def _create_temp_repo_copy(self, repo_path: str) -> str:
        """
        Create a fixed workspace copy for cursor-agent (must be trusted once).

        Unlike the base class which creates random temp directories, cursor-agent
        requires a directory to be trusted before execution. This method uses a
        fixed directory that can be trusted once and reused.

        The workspace is cleaned before each run to ensure test isolation.

        Args:
            repo_path: Path to the original repository

        Returns:
            Path to the workspace repository copy

        Raises:
            FileNotFoundError if repo_path doesn't exist
            OSError if copy operation fails
        """
        # Validate source exists
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        # Fixed workspace directory for cursor-agent
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(script_dir, "wsl_runners", "_cursor_workspace")

        # Create workspace directory if it doesn't exist (keep it for trust)
        os.makedirs(workspace_dir, exist_ok=True)

        # Clean workspace contents if it exists
        if os.path.exists(workspace_dir):
            print(f"[EXECUTOR-LOG] Cleaning existing cursor workspace contents: {workspace_dir}")
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

        # Copy repository contents
        try:
            # Get repo name from path
            repo_name = os.path.basename(os.path.normpath(repo_path))
            workspace_repo_path = os.path.join(workspace_dir, repo_name)

            # Copy entire directory tree
            shutil.copytree(repo_path, workspace_repo_path, symlinks=True)

            print(f"[EXECUTOR-LOG] Created cursor workspace at: {workspace_repo_path}")
            return workspace_repo_path

        except Exception as e:
            # Cleanup contents on failure but keep directory
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            raise OSError(f"Failed to create cursor workspace copy: {str(e)}")

    def _cleanup_temp_repo(self, temp_path: str) -> None:
        """
        Clean up the cursor workspace contents.

        Removes the workspace contents but keeps the _cursor_workspace directory itself
        (needed for cursor-agent trust persistence).

        Args:
            temp_path: Path to the workspace repository
        """
        if os.path.exists(temp_path):
            # Get the workspace directory (parent of the repo copy)
            workspace_dir = os.path.dirname(temp_path)
            print(f"[EXECUTOR-LOG] Cleaning cursor workspace contents: {workspace_dir}")
            # Remove all contents but keep the directory itself
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

    def _run_agent(self, prompt: str, repo_path: str) -> None:
        """
        Run Cursor agent using WSL runner script.

        Args:
            prompt: The prompt to send to Cursor
            repo_path: Path to the repository (fixed workspace copy)
        """
        # Write prompt to file
        prompt_file = self._write_prompt_file(prompt, repo_path)

        # Convert paths to WSL format
        wsl_prompt_file = self._convert_to_wsl_path(prompt_file)
        wsl_repo_path = self._convert_to_wsl_path(repo_path)

        # Get path to runner script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        runner_script = os.path.join(script_dir, "wsl_runners", "run_cursor.py")
        wsl_runner_script = self._convert_to_wsl_path(runner_script)

        # Build command to run the WSL runner script
        command = f'python3 "{wsl_runner_script}" "{wsl_prompt_file}" "{wsl_repo_path}"'

        # Execute in WSL
        self._run_wsl_command(command)


class CodexAgentExecutor(AgentExecutor):
    """
    Executor for Codex CLI agent using codex.

    Codex requires directories to be trusted before execution. This executor
    uses a fixed workspace directory (tests/deterministic/wsl_runners/_codex_workspace)
    that must be trusted once manually, then is reused for all subsequent runs.

    The workspace contents are cleaned before each run to ensure test isolation.
    """

    def __init__(self):
        super().__init__("codex")

    def _create_temp_repo_copy(self, repo_path: str) -> str:
        """
        Create a fixed workspace copy for codex (must be trusted once).

        Unlike the base class which creates random temp directories, codex
        requires a directory to be trusted before execution. This method uses a
        fixed directory that can be trusted once and reused.

        The workspace is cleaned before each run to ensure test isolation.

        Args:
            repo_path: Path to the original repository

        Returns:
            Path to the workspace repository copy

        Raises:
            FileNotFoundError if repo_path doesn't exist
            OSError if copy operation fails
        """
        # Validate source exists
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        # Fixed workspace directory for codex
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(script_dir, "wsl_runners", "_codex_workspace")

        # Create workspace directory if it doesn't exist (keep it for trust)
        os.makedirs(workspace_dir, exist_ok=True)

        # Clean workspace contents if it exists
        if os.path.exists(workspace_dir):
            print(f"[EXECUTOR-LOG] Cleaning existing codex workspace contents: {workspace_dir}")
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

        # Copy repository contents
        try:
            # Get repo name from path
            repo_name = os.path.basename(os.path.normpath(repo_path))
            workspace_repo_path = os.path.join(workspace_dir, repo_name)

            # Copy entire directory tree
            shutil.copytree(repo_path, workspace_repo_path, symlinks=True)

            print(f"[EXECUTOR-LOG] Created codex workspace at: {workspace_repo_path}")
            return workspace_repo_path

        except Exception as e:
            # Cleanup contents on failure but keep directory
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            raise OSError(f"Failed to create codex workspace copy: {str(e)}")

    def _cleanup_temp_repo(self, temp_path: str) -> None:
        """
        Clean up the codex workspace contents.

        Removes the workspace contents but keeps the _codex_workspace directory itself
        (needed for codex trust persistence).

        Args:
            temp_path: Path to the workspace repository
        """
        if os.path.exists(temp_path):
            # Get the workspace directory (parent of the repo copy)
            workspace_dir = os.path.dirname(temp_path)
            print(f"[EXECUTOR-LOG] Cleaning codex workspace contents: {workspace_dir}")
            # Remove all contents but keep the directory itself
            for item in os.listdir(workspace_dir):
                item_path = os.path.join(workspace_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[EXECUTOR-LOG] Warning: Failed to delete {item_path}: {e}")

    def _run_agent(self, prompt: str, repo_path: str) -> None:
        """
        Run Codex agent using WSL runner script.

        Args:
            prompt: The prompt to send to Codex
            repo_path: Path to the repository (fixed workspace copy)
        """
        # Write prompt to file
        prompt_file = self._write_prompt_file(prompt, repo_path)

        # Convert paths to WSL format
        wsl_prompt_file = self._convert_to_wsl_path(prompt_file)
        wsl_repo_path = self._convert_to_wsl_path(repo_path)

        # Get path to runner script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        runner_script = os.path.join(script_dir, "wsl_runners", "run_codex.py")
        wsl_runner_script = self._convert_to_wsl_path(runner_script)

        # Build command to run the WSL runner script
        command = f'python3 "{wsl_runner_script}" "{wsl_prompt_file}" "{wsl_repo_path}"'

        # Execute in WSL
        self._run_wsl_command(command)
