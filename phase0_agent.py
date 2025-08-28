"""
SPADE Phase-0 Agent
Phase-0 analysis agent with DFS traversal, LLM calls, and persistence
"""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path

from agent import Agent

# from context import build_phase0_context
from ignore import load_specs
from logger import get_logger

# from nav import fallback_children, filter_nav
from prompts import load_system, load_user
from scaffold import ScaffoldStore
from schemas import RunConfig, load_json, save_json_data
from spade_state import SpadeState
from schemas import SpadeStateEntryDir
from workspace import Workspace

# Use get_logger() directly instead of storing local copy


class Phase0Agent(Agent):
    """Phase-0 analysis agent with DFS traversal, LLM calls, and persistence."""

    def __init__(self, workspace: Workspace):
        """
        Initialize Phase-0 agent.

        Args:
            workspace: Workspace object for repository operations
        """
        config: RunConfig = workspace.get_config()
        super().__init__(workspace, config.model)
        self.workspace = workspace
        self.config = config

        # State
        self.step_id = 0
        self.llm_calls = 0
        self.visited_count = 0
        self.descended_count = 0
        self.start_time = time.time()
        self.stop_requested = False

        # Infrastructure
        self.ignore_specs = load_specs(workspace.repo_root)
        self.scaffold = ScaffoldStore(workspace)
        # SpadeState is accessed through workspace to ensure single instance

        # Setup graceful shutdown
        self._setup_signal_handlers()

    def run(self) -> None:
        """Execute the Phase-0 traversal."""
        self.workspace.ensure_analysis_root()

        # Ensure state exists before starting traversal
        self.workspace.get_spade_state().build_filesystem_tree(self.workspace.repo_root, self.config)

        self._log_start()

        try:
            while self._should_continue():
                current_rel = self._get_next_directory()
                if current_rel is None:
                    break

                self._process_directory(current_rel)

        except KeyboardInterrupt:
            self._handle_interrupt()
        except Exception as e:
            self._handle_error(e)
        finally:
            self._finish()

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""

        def _sig_handler(signum, frame):
            self.stop_requested = True
            get_logger().info(f"[phase0] stop requested (signal {signum}); finishing current step and exiting gracefully.")

        signal.signal(signal.SIGINT, _sig_handler)
        try:
            signal.signal(signal.SIGTERM, _sig_handler)
        except Exception:
            pass  # SIGTERM not available on all platforms

    def _log_start(self) -> None:
        """Log startup information."""
        model_name = self._get_model_name()
        get_logger().info(f"[phase0] starting traversal (pid={os.getpid()}, model={model_name}, max_depth={self.config.limits.max_depth}, nav_cap={self.config.caps.nav.max_children_per_step})")

    def _get_model_name(self) -> str:
        """Get model name from configuration."""
        return self.config.model

    def _should_continue(self) -> bool:
        """Check if traversal should continue."""
        if self.stop_requested:
            get_logger().info("[phase0] stop requested; exiting gracefully.")
            return False

        if self.config.limits.max_nodes != 0 and self.visited_count >= self.config.limits.max_nodes:
            get_logger().info("[phase0] max_nodes reached; stopping traversal.")
            return False

        return len(self.workspace.get_spade_state().get_unvisited_dirs()) > 0

    def _get_next_directory(self) -> str | None:
        """Get next directory from state."""
        unvisited = self.workspace.get_spade_state().get_unvisited_dirs()
        return unvisited[0] if unvisited else None

    def _process_directory(self, current_rel: str) -> None:
        """Process a single directory."""
        try:
            entry = self.workspace.get_spade_state().get_entry(current_rel)
            if not isinstance(entry, SpadeStateEntryDir):
                get_logger().error(f"[phase0] Entry is not a directory: {current_rel}")
                return

            if self._should_skip_llm(entry):
                self._mark_visited(current_rel)
                return

            # Comment out LLM analysis for now
            # self._analyze_directory(current_rel, entry)
            self._mark_visited(current_rel)

        except KeyError:
            get_logger().error(f"[phase0] Entry not found in state: {current_rel}")
            return

    def _should_skip_llm(self, entry: SpadeStateEntryDir) -> bool:
        """Check if LLM call should be skipped for this directory."""
        if entry.ignored_reason:
            get_logger().info(f"[phase0] skip LLM for {entry.path}, ignored_reason: {entry.ignored_reason}")
            return True

        if self.config.limits.max_depth != 0 and entry.depth >= self.config.limits.max_depth:
            get_logger().info("[phase0] at max_depth; will not request descendants.")

        return False

    # def _analyze_directory(self, current_rel: str, entry: SpadeStateEntryDir) -> None:
    #     """Analyze a directory with LLM."""
    #     context = self._build_context(current_rel)
    #     self._write_checkpoint_before(current_rel, entry.depth, context)

    #     resp, raw_text = self._call_phase0_llm(context)
    #     resp = self._sanitize_response(resp, entry)

    #     self._persist_analysis(current_rel, resp, raw_text)
    #     self._merge_scaffold(resp)

    #     kept = self._handle_navigation(resp, entry)
    #     self._enqueue_children(kept)

    #     self._write_telemetry(current_rel, entry.depth, resp, raw_text, kept)
    #     self._update_checkpoint_after(current_rel, entry.depth, resp, kept)

    # def _build_context(self, current_rel: str) -> dict:
    #     """Build context for LLM call."""
    #     return build_phase0_context(self.workspace.repo_root, current_rel, self.config, self.spade_state)

    # def _call_phase0_llm(self, context: dict) -> tuple[any, str]:
    #     """Call Phase-0 LLM with context."""
    #     # Load prompts
    #     system_text = load_system("phase0_scaffold")
    #     user_template = load_user("phase0_scaffold")
    #     user_text = user_template.replace("{{PHASE0_CONTEXT_JSON}}", self._pretty_json(context))

    #     # Call LLM
    #     result_dict, stats_dict = self.call_llm(system_text, user_text)

    #     # Update stats
    #     self.llm_calls += stats_dict["attempts"]

    #     # Convert to LLMResponse or return None
    #     try:
    #         from schemas import LLMResponse

    #         response = LLMResponse(**result_dict)
    #         return response, json.dumps(result_dict)
    #     except Exception as e:
    #         get_logger().warning(f"[phase0] failed to parse LLM response: {e}")
    #         return None, json.dumps(result_dict)

    # def _pretty_json(self, obj: any) -> str:
    #     """Pretty-print JSON object for stable and readable prompts."""
    #     return json.dumps(obj, ensure_ascii=False, indent=2)

    # def _write_checkpoint_before(self, current_rel: str, depth: int, context: dict) -> None:
    #     """Write step checkpoint before LLM call."""
    #     started_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    #     prompt_chars = len(json.dumps(context, ensure_ascii=False))

    #     checkpoint = {"path": current_rel, "depth": depth, "started_at_utc": started_at_utc, "prompt_chars": prompt_chars}

    #     self.workspace.write_checkpoint(checkpoint)

    # def _sanitize_response(self, resp: any, entry: SpadeStateEntryDir) -> any:
    #     """Sanitize LLM response."""
    #     if resp:
    #         try:
    #         from sanitize import sanitize_llm_output

    #         resp, sanitizer_trimmed, sanitizer_notes = sanitize_llm_output(self.workspace.repo_root, self.config, entry, resp)
    #     except Exception as e:
    #         get_logger().warning(f"[phase0] sanitize failed: {e}")

    #     return resp

    # def _persist_analysis(self, current_rel: str, resp: any, raw_text: str) -> None:
    #     """Persist analysis results."""
    #     out_dir = self.workspace.get_analysis_dir(current_rel)
    #     out_dir.mkdir(parents=True, exist_ok=True)
    #     out_path = out_dir / "llm_inferred.json"

    #     try:
    #         if resp:
    #                 save_json_data(out_path, resp.model_dump())
    #         else:
    #                 # Store raw text for later inspection
    #                 save_json_data(out_path, {"raw": raw_text})
    #     except Exception as e:
    #         get_logger().error(f"[phase0] failed to write analysis for {current_rel}: {e}")

    # def _merge_scaffold(self, resp: any) -> None:
    #     """Merge LLM response into scaffold."""
    #     if resp:
    #         try:
    #                 self.scaffold.merge_nodes(resp.inferred.nodes, self.step_id)
    #                 self.scaffold.merge_components(resp.inferred.high_level_components)
    #         except Exception as e:
    #             get_logger().error(f"[phase0] scaffold merge error: {e}")

    # def _handle_navigation(self, resp: any, entry: SpadeStateEntryDir) -> list[str]:
    #     """Handle navigation based on LLM response."""
    #     kept: list[str] = []
    #     rejected_pairs: list[tuple[str, str]] = []

    #     if resp:
    #         # Validate/filter nav
    #         try:
    #                 kept, rejected_pairs = filter_nav(self.workspace.repo_root, entry, self.config, resp.nav, self.ignore_specs)
    #         except Exception as e:
    #             get_logger().error(f"[phase0] nav validation error: {e}")
    #                 kept = []

    #         # Fallback if nothing kept
    #         if not kept:
    #                 kept = fallback_children(self.workspace.repo_root, entry, self.config, self.ignore_specs)
    #     else:
    #         # Parsed response missing → fallback immediately
    #         kept = fallback_children(self.workspace.repo_root, entry, self.config, self.ignore_specs)

    #     return kept

    # def _enqueue_children(self, kept: list[str]) -> None:
    #     """Enqueue children for traversal."""
    #     if kept:
    #         # For tree-based approach, we don't need to enqueue children
    #         # The tree already contains all nodes, we just need to mark them as unvisited
    #         # if they were previously visited
    #         for child_path in kept:
    #                 child_node = self.spade_state.get_entry(child_path)
    #                 if child_node and child_node.visited:
    #                     # Reset visited state for children we want to process
    #                     child_node.visited = False

    #         self.descended_count += len(kept)

    # def _write_telemetry(self, current_rel: str, depth: int, resp: any, raw_text: str, kept: list[str]) -> None:
    #     """Write telemetry for this step."""
    #     try:
    #         telem = {
    #             "step": self.step_id,
    #             "path": current_rel,
    #             "depth": depth,
    #             "prompt_chars": len(json.dumps(self._build_context(current_rel), ensure_ascii=False)),
    #             "response_chars": len(raw_text or ""),
    #         "duration_ms": int((time.time() - self.start_time) * 1000),
    #             "json_valid": bool(resp),
    #             "nav_requested": (resp.nav.descend_into if resp else []),
    #             "nav_kept": kept,
    #             "nav_rejected": [],  # TODO: capture rejected pairs
    #             "fallback_used": (not resp) or (resp and not kept),
    #             "sanitizer_trimmed": False,  # TODO: capture sanitizer info
    #             "sanitizer_notes": "",
    #         }

    #         # Add normalized languages if available
    #         if resp and resp.inferred.nodes and current_rel in resp.inferred.nodes:
    #             node = resp.inferred.nodes[current_rel]
    #             if node.languages:
    #                     telem["norm_languages"] = node.languages

    #         self.workspace.append_telemetry(telem)
    #     except Exception as e:
    #         get_logger().warning(f"[phase0] telemetry write failed: {e}")

    # def _update_checkpoint_after(self, current_rel: str, depth: int, resp: any, kept: list[str]) -> None:
    #     """Update step checkpoint after LLM call completion."""
    #     finished_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    #     json_valid = bool(resp)

    #     checkpoint = {"path": current_rel, "depth": depth, "finished_at_utc": finished_at_utc, "json_valid": json_valid, "nav_kept": kept}

    #     self.workspace.write_checkpoint(checkpoint)

    def _mark_visited(self, current_rel: str) -> None:
        """Mark directory as visited."""
        self.workspace.get_spade_state().mark_visited(current_rel)
        self.visited_count += 1
        self.step_id += 1

    def _handle_interrupt(self) -> None:
        """Handle keyboard interrupt."""
        get_logger().info("[phase0] KeyboardInterrupt — graceful shutdown")

    def _handle_error(self, e: Exception) -> None:
        """Handle unexpected errors."""
        get_logger().error(f"[phase0] unexpected error: {e}")
        raise

    def _finish(self) -> None:
        """Finish the Phase-0 run."""
        self._write_summary()
        self._generate_report()
        self._log_finish()

    def _write_summary(self) -> None:
        """Write summary.json."""
        try:
            # Get statistics from SpadeState
            stats = self.workspace.get_spade_state().get_statistics()

            summary = {
                "visited": self.visited_count,
                "descended": self.descended_count,
                "total_files": stats["total_files"],
                "total_dirs": stats["total_dirs"],
                "visited_files": stats["visited_files"],
                "visited_dirs": stats["visited_dirs"],
                "max_depth": stats["max_depth"],
                "duration_ms": int((time.time() - self.start_time) * 1000),
                "limits": {"max_depth": self.config.limits.max_depth, "max_nodes": self.config.limits.max_nodes, "max_llm_calls": self.config.limits.max_llm_calls, "nav_cap": self.config.caps.nav.max_children_per_step},
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "model": self._get_model_name(),
            }

            self.workspace.write_summary(summary)
            get_logger().debug(f"[phase0] wrote summary to {self.workspace.spade_dir / 'summary.json'}")
        except Exception as e:
            get_logger().warning(f"[phase0] failed to write summary.json: {e}")

    def _generate_report(self) -> None:
        """Generate Phase-0 report."""
        # from report import write_phase0_report

        try:
            # write_phase0_report(self.workspace.repo_root, self.config)
            get_logger().info("[phase0] report generation temporarily disabled")
        except Exception as e:
            get_logger().warning(f"[report] failed: {e}")

    def _log_finish(self) -> None:
        """Log finish information."""
        comps = len(self.scaffold.load_components())
        avg_conf = 0.0
        nodes = self.scaffold.load_nodes()
        if nodes:
            vals = [float(v.get("confidence", 0.0)) for v in nodes.values()]
            if vals:
                avg_conf = sum(vals) / len(vals)

        # Log shutdown message
        if self.stop_requested:
            get_logger().info(f"[phase0] graceful stop — visited:{self.visited_count} descended:{self.descended_count} — see .spade/summary.json")

        get_logger().info(f"[phase0] visited:{self.visited_count} descended:{self.descended_count} components:{comps} avg_conf:{avg_conf:.2f} elapsed:{int((time.time()-self.start_time)*1000)}ms")
        print(f"visited:{self.visited_count} descended:{self.descended_count} components:{comps} avg_conf:{avg_conf:.2f}")
