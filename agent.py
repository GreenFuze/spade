"""
SPADE Agent - Base implementation
Common utilities and base classes for SPADE agents
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import llm
from logger import setup_logging, get_logger


class Telemetry:
    """Capture run telemetry and persist as JSONL."""
    
    def __init__(self, run_id: str, repo_root: str, model_id: str):
        self.run_id = run_id
        self.repo_root = repo_root
        self.model_id = model_id
        self.started_at = None
        self.finished_at = None
        self.wall_ms = None
        
        # Scan stats
        self.dir_count = 0
        self.max_depth = 0
        self.max_entries = 0
        self.skipped_dirs = []
        
        # LLM stats
        self.llm_attempts = 0
        self.llm_prompt_chars = 0
        self.llm_response_chars = 0
        self.llm_latency_ms = 0.0
        self.llm_parse_retries = 0
        
        # Scaffold stats
        self.scaffold_big_blocks_count = 0
        self.scaffold_conf_min = 0
        self.scaffold_conf_max = 0
        self.scaffold_conf_avg = 0.0
        self.scaffold_questions_count = 0
        
        # Run result
        self.success = False
        self.error_message = None
    
    def start(self) -> None:
        """Records monotonic start and UTC timestamp."""
        self.started_at = datetime.now(timezone.utc).isoformat()
    
    def end(self, success: bool, error_message: Optional[str] = None) -> None:
        """Records completion with success status and optional error."""
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.success = success
        self.error_message = error_message
        
        if self.started_at:
            start_time = datetime.fromisoformat(self.started_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(self.finished_at.replace('Z', '+00:00'))
            self.wall_ms = (end_time - start_time).total_seconds() * 1000
    
    def record_scan_stats(self, dir_count: int, max_depth: int, max_entries: int, skipped_dirs: List[str]) -> None:
        """Records directory scanning statistics."""
        self.dir_count = dir_count
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.skipped_dirs = skipped_dirs
    
    def record_llm_stats(self, attempts: int, prompt_chars: int, response_chars: int, latency_ms: float, parse_retries: int) -> None:
        """Records LLM interaction statistics."""
        self.llm_attempts = attempts
        self.llm_prompt_chars = prompt_chars
        self.llm_response_chars = response_chars
        self.llm_latency_ms = latency_ms
        self.llm_parse_retries = parse_retries
    
    def record_scaffold_stats(self, big_blocks_count: int, conf_min: int, conf_max: int, conf_avg: float, questions_count: int) -> None:
        """Records scaffold inference statistics."""
        self.scaffold_big_blocks_count = big_blocks_count
        self.scaffold_conf_min = conf_min
        self.scaffold_conf_max = conf_max
        self.scaffold_conf_avg = conf_avg
        self.scaffold_questions_count = questions_count
    
    def to_dict(self) -> Dict:
        """Converts telemetry to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "repo_root": self.repo_root,
            "model_id": self.model_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "wall_ms": self.wall_ms,
            "dir_count": self.dir_count,
            "max_depth": self.max_depth,
            "max_entries": self.max_entries,
            "skipped_dirs": self.skipped_dirs,
            "llm_attempts": self.llm_attempts,
            "llm_prompt_chars": self.llm_prompt_chars,
            "llm_response_chars": self.llm_response_chars,
            "llm_latency_ms": self.llm_latency_ms,
            "llm_parse_retries": self.llm_parse_retries,
            "scaffold_big_blocks_count": self.scaffold_big_blocks_count,
            "scaffold_conf_min": self.scaffold_conf_min,
            "scaffold_conf_max": self.scaffold_conf_max,
            "scaffold_conf_avg": self.scaffold_conf_avg,
            "scaffold_questions_count": self.scaffold_questions_count,
            "success": self.success,
            "error_message": self.error_message
        }
    
    def append_jsonl(self, path: str | Path) -> None:
        """Appends one line to JSONL file (UTF-8)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(self.to_dict()) + '\n')


class PromptLoader:
    """Loads prompt templates from prompts directory."""
    
    def __init__(self, prompts_dir: Path, logger: logging.Logger = None):
        self.prompts_dir = prompts_dir
        self.logger = logger or get_logger()
    
    def load_system(self, phase: str) -> str:
        """Reads prompts/{phase}_system.md."""
        system_path = self.prompts_dir / f"{phase}_system.md"
        if not system_path.exists():
            self.logger.error(f"System prompt file not found: {system_path}")
            raise FileNotFoundError(f"System prompt file not found: {system_path}")
        
        content = system_path.read_text(encoding='utf-8')
        self.logger.debug(f"Loaded system prompt from {system_path} ({len(content)} chars)")
        return content
    
    def load_user(self, phase: str) -> str:
        """Reads prompts/{phase}_user.md."""
        user_path = self.prompts_dir / f"{phase}_user.md"
        if not user_path.exists():
            self.logger.error(f"User prompt file not found: {user_path}")
            raise FileNotFoundError(f"User prompt file not found: {user_path}")
        
        content = user_path.read_text(encoding='utf-8')
        self.logger.debug(f"Loaded user prompt from {user_path} ({len(content)} chars)")
        return content


class LLMClient:
    """Wraps the llm library and provides measurable calls."""
    
    def __init__(self, model_id: str, logger: logging.Logger = None):
        self.model_id = model_id or os.getenv("SPADE_LLM_MODEL", "gpt-5-nano")
        self.logger = logger or get_logger()
        self.logger.debug(f"Initialized LLM client with model: {self.model_id}")
    
    def infer(self, system_text: str, user_text: str) -> Tuple[Dict, Dict]:
        """Performs LLM inference with retry logic and statistics."""
        self.logger.debug("Starting LLM inference")
        attempts = 0
        parse_retries = 0
        start_time = time.time()
        
        while attempts < 2:
            attempts += 1
            self.logger.debug(f"LLM attempt {attempts}/2")
            
            try:
                # Get model and call LLM
                model = llm.get_model(self.model_id)
                self.logger.debug(f"Retrieved model: {self.model_id}")
                
                # Log what we're sending to LLM
                self.logger.debug(f"------\nUser: {user_text}")
                
                response = model.prompt(user_text, system=system_text)
                response_text = response.text().strip()
                
                # Log what we received from LLM
                self.logger.debug(f"-------\nAgent: {response_text}")
                self.logger.debug(f"LLM response received: {len(response_text)} chars")
                
                # Try to parse JSON
                try:
                    result_dict = json.loads(response_text)
                    self.logger.debug("JSON parsing successful")
                    break
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON parsing failed on attempt {attempts}: {e}")
                    if attempts == 1:
                        # First attempt failed, retry with strict reminder
                        user_text += "\n\nIMPORTANT: Output ONLY valid JSON. No markdown, no code fences, no extra text."
                        parse_retries += 1
                        self.logger.debug("Retrying with strict JSON reminder")
                        continue
                    else:
                        self.logger.error(f"Failed to parse JSON response after retry: {response_text[:200]}...")
                        raise ValueError(f"Failed to parse JSON response after retry: {response_text[:200]}...")
            
            except Exception as e:
                self.logger.error(f"LLM call failed on attempt {attempts}: {e}")
                if attempts == 2:
                    raise e
                continue
        
        # Calculate statistics
        latency_ms = (time.time() - start_time) * 1000
        prompt_chars = len(system_text) + len(user_text)
        response_chars = len(response_text)
        
        self.logger.debug(f"LLM inference complete: {latency_ms:.1f}ms, {prompt_chars} prompt chars, {response_chars} response chars")
        
        stats_dict = {
            "attempts": attempts,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "latency_ms": latency_ms,
            "parse_retries": parse_retries
        }
        
        return result_dict, stats_dict


class ScaffoldWriter:
    """Persists outputs to .spade directory."""
    
    def __init__(self, repo_root: Path, logger: logging.Logger = None):
        self.repo_root = repo_root
        self.spade_dir = repo_root / ".spade"
        self.logger = logger or get_logger()
        self.spade_dir.mkdir(exist_ok=True)
        self.logger.debug(f"Initialized ScaffoldWriter with spade_dir: {self.spade_dir}")
    
    def write_context(self, phase: str, ctx: Dict) -> Path:
        """Writes .spade/{phase}_context.json."""
        path = self.spade_dir / f"{phase}_context.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"Wrote {phase} context to {path}")
        return path
    
    def write_scaffold(self, phase: str, scaffold: Dict) -> Path:
        """Writes .spade/{phase}_scaffold.json with version and timestamp."""
        output = {
            "version": "0.1",
            "ts": datetime.now(timezone.utc).isoformat(),
            **scaffold,
            "notes": f"{phase} scaffold inferred from directory structure/names only."
        }
        
        path = self.spade_dir / f"{phase}_scaffold.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"Wrote {phase} scaffold to {path}")
        return path
    
    def append_telemetry(self, telemetry: Telemetry) -> Path:
        """Appends to .spade/telemetry.jsonl."""
        path = self.spade_dir / "telemetry.jsonl"
        telemetry.append_jsonl(path)
        self.logger.debug(f"Appended telemetry to {path}")
        return path


class Agent:
    """Base agent class for SPADE phases."""
    
    def __init__(self, repo_root: Path, model_id: str = "gpt-5-nano"):
        self.repo_root = repo_root
        self.model_id = model_id
        
        # Setup logging
        self.logger = setup_logging(repo_root)
        self.logger.info(f"Working on directory: {repo_root}")
        self.logger.debug(f"Initializing Agent for {repo_root}")
        self.logger.debug(f"Configuration: model_id={self.model_id}")
        
        # Initialize components
        self.telemetry = Telemetry(str(uuid.uuid4()), str(repo_root), self.model_id)
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.writer = ScaffoldWriter(repo_root, self.logger)
    
    def run(self) -> None:
        """Main execution flow - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement run() method")
