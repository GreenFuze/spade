"""
SPADE LLM Client
Handles prompt loading, context injection, transport calls, and JSON parsing
"""

from __future__ import annotations
import json
import time
from typing import Callable, Tuple, Any

from models import LLMResponse
from prompts import load_system, load_user
from logger import get_logger

logger = get_logger()


def pretty_json(obj: Any) -> str:
    """Pretty-print JSON object for stable and readable prompts."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


class LLMClient:
    """
    LLM client with prompt loading, context injection, and JSON parsing.
    
    Args:
        transport: Callable[[list[dict]], str]
            • Accepts an OpenAI-like messages list: [{role:"system"/"user","content":str},...]
            • Returns raw text content (string) from the assistant
    """
    
    def __init__(self, transport: Callable[[list[dict]], str]):
        self.transport = transport

    def call_phase0(self, context: dict) -> Tuple[LLMResponse | None, str]:
        """
        Call Phase-0 LLM with context and return parsed response or None.
        
        Args:
            context: PHASE0_CONTEXT_JSON dictionary
            
        Returns:
            Tuple of (parsed_response_or_None, raw_text)
        """
        sys_txt = load_system("phase0_scaffold")
        usr_tpl = load_user("phase0_scaffold")
        usr_txt = usr_tpl.replace("{{PHASE0_CONTEXT_JSON}}", pretty_json(context))

        messages = [
            {"role": "system", "content": sys_txt},
            {"role": "user", "content": usr_txt},
        ]

        t0 = time.time()
        raw = ""
        try:
            raw = self.transport(messages)
        except Exception as e:
            logger.error(f"[llm] transport error: {e}")
            return None, ""

        # First parse attempt
        obj, ok = self._parse_llm_response(raw)
        if ok:
            logger.info(f"[llm] parsed response (first try) in {int((time.time()-t0)*1000)} ms")
            return obj, raw

        # One repair attempt: prepend a repair instruction
        repair_msg = {
            "role": "user",
            "content": "Fix JSON ONLY; keep the same content and schema. No prose, no markdown."
        }
        messages_repair = messages + [repair_msg]
        try:
            raw2 = self.transport(messages_repair)
        except Exception as e:
            logger.error(f"[llm] transport error on repair attempt: {e}")
            return None, raw

        obj2, ok2 = self._parse_llm_response(raw2)
        if ok2:
            logger.info(f"[llm] parsed response (repair) in {int((time.time()-t0)*1000)} ms")
            return obj2, raw2

        logger.warning(f"[llm] failed to parse response after repair")
        return None, raw2

    def _parse_llm_response(self, raw: str) -> tuple[LLMResponse | None, bool]:
        """
        Attempt to parse raw text as JSON and validate with Pydantic into LLMResponse.
        
        Args:
            raw: Raw text response from LLM
            
        Returns:
            Tuple of (obj, True) on success, (None, False) on failure
        """
        try:
            data = json.loads(raw)
        except Exception as e:
            logger.debug(f"[llm] JSON decode error: {e}")
            return None, False
        
        try:
            obj = LLMResponse(**data)
            return obj, True
        except Exception as e:
            logger.debug(f"[llm] schema validation error: {e}")
            return None, False

    def learn_markers(self, repo_root_name: str, min_conf: float, candidates: list[str]) -> list[dict] | None:
        """
        Learn marker classifications from candidate names.
        
        Args:
            repo_root_name: Name of the repository root
            min_conf: Minimum confidence threshold
            candidates: List of candidate names to classify
            
        Returns:
            List of marker objects or None if learning failed
        """
        try:
            # Load prompts
            system_text = load_system("markers_learn")
            user_template = load_user("markers_learn")
            
            # Build context
            context = {
                "repo_root_name": repo_root_name,
                "min_confidence": min_conf,
                "candidates": candidates
            }
            
            # Render user prompt
            user_text = user_template.replace("{{REPO_NAME}}", repo_root_name)
            user_text = user_text.replace("{{MIN_CONF}}", str(min_conf))
            user_text = user_text.replace("{{CANDIDATE_NAMES_JSON}}", pretty_json(candidates))
            
            # Call transport
            t0 = time.time()
            raw_text = self.transport([
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text}
            ])
            elapsed_ms = int((time.time() - t0) * 1000)
            
            # Parse response
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, list):
                    logger.info(f"[llm] learn_markers completed in {elapsed_ms}ms, got {len(parsed)} markers")
                    return parsed
                else:
                    logger.warning(f"[llm] learn_markers returned non-list: {type(parsed)}")
                    return None
            except json.JSONDecodeError:
                logger.warning(f"[llm] learn_markers JSON parse failed: {raw_text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"[llm] learn_markers failed: {e}")
            return None

    def learn_languages(self, repo_root_name: str, candidates: list[str]) -> list[dict] | None:
        """
        Learn language mappings from unknown extensions.
        
        Args:
            repo_root_name: Name of the repository root
            candidates: List of unknown extensions to classify
            
        Returns:
            List of language objects or None if learning failed
        """
        try:
            # Load prompts
            system_text = load_system("languages_learn")
            user_template = load_user("languages_learn")
            
            # Build context
            context = {
                "repo_root_name": repo_root_name,
                "candidates": candidates
            }
            
            # Render user prompt
            user_text = user_template.replace("{{REPO_NAME}}", repo_root_name)
            user_text = user_text.replace("{{UNKNOWN_EXTS_JSON}}", pretty_json(candidates))
            
            # Call transport
            t0 = time.time()
            raw_text = self.transport([
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text}
            ])
            elapsed_ms = int((time.time() - t0) * 1000)
            
            # Parse response
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, list):
                    logger.info(f"[llm] learn_languages completed in {elapsed_ms}ms, got {len(parsed)} languages")
                    return parsed
                else:
                    logger.warning(f"[llm] learn_languages returned non-list: {type(parsed)}")
                    return None
            except json.JSONDecodeError:
                logger.warning(f"[llm] learn_languages JSON parse failed: {raw_text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"[llm] learn_languages failed: {e}")
            return None
