"""
SPADE Agent - Abstract base class for SPADE agents
"""

import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import llm

from logger import get_logger, init_logger
from telemetry import Telemetry


class PromptLoader:
    """Loads prompt templates from prompts directory."""

    def __init__(self, prompts_dir: Path, logger: logging.Logger = None):
        self.prompts_dir = prompts_dir
        # Use get_logger() directly instead of storing local copy

    def load_system(self, phase: str) -> str:
        """Reads prompts/{phase}_system.md."""
        system_path = self.prompts_dir / f"{phase}_system.md"
        if not system_path.exists():
            get_logger().error(f"System prompt file not found: {system_path}")
            raise FileNotFoundError(f"System prompt file not found: {system_path}")

        content = system_path.read_text(encoding="utf-8")
        get_logger().debug(
            f"Loaded system prompt from {system_path} ({len(content)} chars)"
        )
        return content

    def load_user(self, phase: str) -> str:
        """Reads prompts/{phase}_user.md."""
        user_path = self.prompts_dir / f"{phase}_user.md"
        if not user_path.exists():
            get_logger().error(f"User prompt file not found: {user_path}")
            raise FileNotFoundError(f"User prompt file not found: {user_path}")

        content = user_path.read_text(encoding="utf-8")
        get_logger().debug(
            f"Loaded user prompt from {user_path} ({len(content)} chars)"
        )
        return content


class LLMClient:
    """Wraps the llm library and provides measurable calls."""

    def __init__(self, model_id: str, logger: logging.Logger = None):
        self.model_id = model_id
        get_logger().debug(f"Initialized LLM client with model: {self.model_id}")

    def infer(self, system_text: str, user_text: str) -> Tuple[Dict, Dict]:
        """Performs LLM inference with retry logic and statistics."""
        get_logger().debug("Starting LLM inference")
        attempts = 0
        parse_retries = 0
        start_time = time.time()

        while attempts < 2:
            attempts += 1
            get_logger().debug(f"LLM attempt {attempts}/2")

            try:
                # Get model and call LLM
                model = llm.get_model(self.model_id)
                get_logger().debug(f"Retrieved model: {self.model_id}")

                # Log what we're sending to LLM
                get_logger().debug(f"------\nUser: {user_text}")

                response = model.prompt(user_text, system=system_text)
                response_text = response.text().strip()

                # Log what we received from LLM
                get_logger().debug(f"-------\nAgent: {response_text}")
                get_logger().debug(f"LLM response received: {len(response_text)} chars")

                # Try to parse JSON
                try:
                    result_dict = json.loads(response_text)
                    get_logger().debug("JSON parsing successful")
                    break
                except json.JSONDecodeError as e:
                    get_logger().warning(
                        f"JSON parsing failed on attempt {attempts}: {e}"
                    )
                    if attempts == 1:
                        # First attempt failed, retry with strict reminder
                        user_text += "\n\nIMPORTANT: Output ONLY valid JSON. No markdown, no code fences, no extra text."
                        parse_retries += 1
                        get_logger().debug("Retrying with strict JSON reminder")
                        continue
                    else:
                        get_logger().error(
                            f"Failed to parse JSON response after retry: {response_text[:200]}..."
                        )
                        raise ValueError(
                            f"Failed to parse JSON response after retry: {response_text[:200]}..."
                        )

            except Exception as e:
                get_logger().error(f"LLM call failed on attempt {attempts}: {e}")
                if attempts == 2:
                    raise e
                continue

        # Calculate statistics
        latency_ms = (time.time() - start_time) * 1000
        prompt_chars = len(system_text) + len(user_text)
        response_chars = len(response_text)

        get_logger().debug(
            f"LLM inference complete: {latency_ms:.1f}ms, {prompt_chars} prompt chars, {response_chars} response chars"
        )

        stats_dict = {
            "attempts": attempts,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "latency_ms": latency_ms,
            "parse_retries": parse_retries,
        }

        return result_dict, stats_dict


class Agent(ABC):
    """Abstract base agent class for SPADE phases."""

    def __init__(self, workspace, model_id: str):
        self.workspace = workspace
        self.repo_root = workspace.repo_root
        self.model_id = model_id

        # Log initialization
        get_logger().info(f"Working on directory: {self.repo_root}")
        get_logger().debug(f"Initializing Agent for {self.repo_root}")
        get_logger().debug(f"Configuration: model_id={self.model_id}")

        # Initialize components
        self.telemetry = Telemetry(
            str(uuid.uuid4()), str(self.repo_root), self.model_id
        )
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.llm_client = LLMClient(model_id)

    @abstractmethod
    def run(self) -> None:
        """Main execution flow - to be implemented by subclasses."""
        raise NotImplemented("Subclass must implement run() method")

    def call_llm(self, system_text: str, user_text: str) -> Tuple[Dict, Dict]:
        """Call LLM with system and user text, return result and stats."""
        return self.llm_client.infer(system_text, user_text)
