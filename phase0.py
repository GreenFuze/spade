"""
SPADE Phase-0 Traversal Loop
End-to-end Phase-0 analysis with DFS traversal, LLM calls, and persistence
"""

from __future__ import annotations
import os
import json
import signal
import time
from pathlib import Path

from models import RunConfig, DirMeta, TelemetryRow
from models import load_json, save_json, save_json_data
from logger import get_logger
from ignore import load_specs
from context import build_phase0_context
from llm import LLMClient
from nav import filter_nav, fallback_children
from scaffold import ScaffoldStore
from worklist import WorklistStore

logger = get_logger()

ANALYSIS_ROOT = ".spade/analysis"
CHECKPOINT_DIR = ".spade/checkpoints"


def _analysis_dir(repo_root: Path, rel: str) -> Path:
    """Get analysis directory path for a relative path."""
    return repo_root / ANALYSIS_ROOT / (rel if rel != "." else ".")


def _dirmeta_path(repo_root: Path, rel: str) -> Path:
    """Get dirmeta.json path for a relative path."""
    return repo_root / ".spade/snapshot" / (rel if rel != "." else ".") / "dirmeta.json"


def _write_step_checkpoint(repo_root: Path, current_rel: str, depth: int, started_at_utc: str, prompt_chars: int):
    """Write step checkpoint before LLM call."""
    checkpoint_dir = repo_root / CHECKPOINT_DIR
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        "path": current_rel,
        "depth": depth,
        "started_at_utc": started_at_utc,
        "prompt_chars": prompt_chars
    }
    
    checkpoint_path = checkpoint_dir / "phase0_last_step.json"
    save_json_data(checkpoint_path, checkpoint)


def _update_step_checkpoint(repo_root: Path, current_rel: str, depth: int, finished_at_utc: str, json_valid: bool, nav_kept: list[str]):
    """Update step checkpoint after LLM call completion."""
    checkpoint_dir = repo_root / CHECKPOINT_DIR
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        "path": current_rel,
        "depth": depth,
        "finished_at_utc": finished_at_utc,
        "json_valid": json_valid,
        "nav_kept": nav_kept
    }
    
    checkpoint_path = checkpoint_dir / "phase0_last_step.json"
    save_json_data(checkpoint_path, checkpoint)


def run_phase0(repo_root: Path, transport) -> None:
    """
    Execute Phase-0 traversal.
    
    Args:
        repo_root: Root directory of the repository
        transport: A callable(messages:list[dict])->str given to LLMClient
        
    Raises:
        SystemExit: If configuration is missing or invalid
    """
    repo_root = repo_root.resolve()
    
    # Load run config
    cfg_path = repo_root / ".spade/run.json"
    if not cfg_path.exists():
        logger.error("[phase0] .spade/run.json missing. Run --init-workspace first.")
        raise SystemExit(2)
    
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Init infrastructure
    ignore_specs = load_specs(repo_root)
    scaffold = ScaffoldStore(repo_root)
    worklist = WorklistStore(repo_root)
    llm = LLMClient(transport)

    # Ensure analysis root exists
    (repo_root / ANALYSIS_ROOT).mkdir(parents=True, exist_ok=True)

    # Setup graceful shutdown
    stop_requested = False
    
    def _sig_handler(signum, frame):
        nonlocal stop_requested
        stop_requested = True
        logger.info(f"[phase0] stop requested (signal {signum}); finishing current step and exiting gracefully.")
    
    signal.signal(signal.SIGINT, _sig_handler)
    try:
        signal.signal(signal.SIGTERM, _sig_handler)
    except Exception:
        pass  # SIGTERM not available on all platforms

    # Get model name for logging
    model_name = "gpt-5-nano"  # default
    llm_config_path = repo_root / ".spade/llm.json"
    if llm_config_path.exists():
        try:
            llm_config = json.loads(llm_config_path.read_text(encoding="utf-8"))
            model_name = llm_config.get("model", model_name)
        except Exception:
            pass  # Keep default if reading fails

    logger.info(f"[phase0] starting traversal (pid={os.getpid()}, model={model_name}, max_depth={cfg.limits.max_depth}, nav_cap={cfg.caps.nav.max_children_per_step})")

    step_id = 0
    llm_calls = 0
    visited_count = 0
    descended_count = 0

    # Limits
    max_nodes = cfg.limits.max_nodes
    max_llm = cfg.limits.max_llm_calls

    start_time = time.time()
    
    try:
        while True:
            # Check for stop request at the top of the loop
            if stop_requested:
                logger.info("[phase0] stop requested; exiting gracefully.")
                break
            
            # Stop on nodes limit
            if max_nodes != 0 and visited_count >= max_nodes:
                logger.info("[phase0] max_nodes reached; stopping traversal.")
                break
            
            current_rel = worklist.pop_left()
            if current_rel is None:
                logger.info("[phase0] worklist empty; stopping traversal.")
                break
        
            current_real = (repo_root / ("" if current_rel == "." else current_rel)).resolve().as_posix()
            if worklist.is_visited(current_real):
                continue

            # Load dirmeta
            dm_path = _dirmeta_path(repo_root, current_rel)
            if not dm_path.exists():
                logger.warning(f"[phase0] missing dirmeta for {current_rel}; skipping.")
                worklist.mark_visited(current_real)
                visited_count += 1
                continue

            try:
                dirmeta = load_json(dm_path, DirMeta)
            except Exception as e:
                logger.error(f"[phase0] invalid dirmeta for {current_rel}: {e}; skipping.")
                worklist.mark_visited(current_real)
                visited_count += 1
                continue

            depth = dirmeta.depth
            logger.info(f"[phase0] visiting: {current_rel} (d={depth}, dirs={dirmeta.counts.dirs}, files={dirmeta.counts.files})")

            # If this node is ignored (permission denied or policy), don't call LLM and don't descend
            if dirmeta.ignored_reason:
                logger.info(f"[phase0] skip LLM, ignored_reason: {dirmeta.ignored_reason}")
                worklist.mark_visited(current_real)
                visited_count += 1
                step_id += 1
                continue

            # Depth guard: if we're already at max_depth, we won't be allowed to descend anyway
            if cfg.limits.max_depth != 0 and depth >= cfg.limits.max_depth:
                logger.info("[phase0] at max_depth; will not request descendants.")

            # Build context and call LLM
            context = build_phase0_context(repo_root, current_rel, cfg)
            
            # Write step checkpoint before LLM call
            started_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            prompt_chars = len(json.dumps(context, ensure_ascii=False))
            _write_step_checkpoint(repo_root, current_rel, depth, started_at_utc, prompt_chars)
            
            t0 = time.time()
            resp, raw_text = llm.call_phase0(context)
            elapsed_ms = int((time.time() - t0) * 1000)
            
            # Sanitize LLM output before processing
            sanitizer_trimmed = False
            sanitizer_notes = ""
            if resp:
                try:
                    from sanitize import sanitize_llm_output
                    resp, sanitizer_trimmed, sanitizer_notes = sanitize_llm_output(repo_root, cfg, dirmeta, resp)
                except Exception as e:
                    logger.warning(f"[phase0] sanitize failed at {current_rel}: {e}")

            # Count LLM calls: call_phase0 always makes 1, and possibly 2 with repair; we conservatively count +2 if raw_text changed (but we don't know).
            # Simpler: count +1 for initial call; if resp is None (repair attempted) count +2.
            llm_calls += 1 if resp else 2
            
            # Enforce max_llm_calls
            if max_llm != 0 and llm_calls > max_llm:
                logger.info("[phase0] max_llm_calls reached after this step.")

            # Persist analysis
            out_dir = _analysis_dir(repo_root, current_rel)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "llm_inferred.json"
            try:
                if resp:
                    save_json_data(out_path, resp.model_dump())
                else:
                    # Store raw text for later inspection
                    save_json_data(out_path, {"raw": raw_text})
            except Exception as e:
                logger.error(f"[phase0] failed to write analysis for {current_rel}: {e}")

            # Merge + navigate
            kept: list[str] = []
            rejected_pairs: list[tuple[str, str]] = []
            
            if resp:
                # Merge scaffold
                try:
                    scaffold.merge_nodes(resp.inferred.nodes, step_id)
                    scaffold.merge_components(resp.inferred.high_level_components)
                except Exception as e:
                    logger.error(f"[phase0] scaffold merge error at {current_rel}: {e}")
                
                # Validate/filter nav
                try:
                    kept, rejected_pairs = filter_nav(repo_root, dirmeta, cfg, resp.nav, ignore_specs)
                except Exception as e:
                    logger.error(f"[phase0] nav validation error at {current_rel}: {e}")
                    kept = []
                
                # Fallback if nothing kept
                if not kept:
                    kept = fallback_children(repo_root, dirmeta, cfg, ignore_specs)
            else:
                # Parsed response missing → fallback immediately
                kept = fallback_children(repo_root, dirmeta, cfg, ignore_specs)

            # Enqueue children (DFS)
            if kept:
                # Ensure stable order: alphabetical by default, but kept already preserves LLM order after filtering
                worklist.push_many_left(kept)
                descended_count += len(kept)

            # Telemetry row
            try:
                telem = {
                    "step": step_id,
                    "path": current_rel,
                    "depth": depth,
                    "prompt_chars": len(json.dumps(context, ensure_ascii=False)),
                    "response_chars": len(raw_text or ""),
                    "duration_ms": elapsed_ms,
                    "json_valid": bool(resp),
                    "nav_requested": (resp.nav.descend_into if resp else []),
                    "nav_kept": kept,
                    "nav_rejected": [f"{c}:{r}" for c, r in (rejected_pairs or [])],
                    "fallback_used": (not resp) or (resp and not kept),
                    "sanitizer_trimmed": sanitizer_trimmed,
                    "sanitizer_notes": sanitizer_notes
                }
                
                # Add normalized languages if available
                if resp and resp.inferred.nodes and current_rel in resp.inferred.nodes:
                    node = resp.inferred.nodes[current_rel]
                    if node.languages:
                        telem["norm_languages"] = node.languages
                telem_path = repo_root / ".spade/telemetry.jsonl"
                with telem_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(telem, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.warning(f"[phase0] telemetry write failed at {current_rel}: {e}")

            # Update step checkpoint after completion
            finished_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            json_valid = bool(resp)
            _update_step_checkpoint(repo_root, current_rel, depth, finished_at_utc, json_valid, kept)

            # Mark visited
            worklist.mark_visited(current_real)
            visited_count += 1
            step_id += 1

            # Check for stop request after completing the step
            if stop_requested:
                logger.info("[phase0] stop requested after completing step; exiting gracefully.")
                break

            # Hard stop if llm_calls limit reached
            if max_llm != 0 and llm_calls >= max_llm:
                logger.info("[phase0] stopping due to max_llm_calls.")
                break

    except KeyboardInterrupt:
        logger.info("[phase0] KeyboardInterrupt — graceful shutdown")
    except Exception as e:
        logger.error(f"[phase0] unexpected error: {e}")
        raise

    # Summary
    comps = len(scaffold.load_components())
    avg_conf = 0.0
    nodes = scaffold.load_nodes()
    if nodes:
        vals = [float(v.get("confidence", 0.0)) for v in nodes.values()]
        if vals:
            avg_conf = sum(vals) / len(vals)
    
    # Log shutdown message
    if stop_requested:
        logger.info(f"[phase0] graceful stop — visited:{visited_count} descended:{descended_count} — see .spade/summary.json")
    
    logger.info(f"[phase0] visited:{visited_count} descended:{descended_count} components:{comps} avg_conf:{avg_conf:.2f} elapsed:{int((time.time()-start_time)*1000)}ms")
    print(f"visited:{visited_count} descended:{descended_count} components:{comps} avg_conf:{avg_conf:.2f}")
    
    # Write summary.json
    try:
        # Try to read model name from .spade/llm.json if it exists
        model_name = "gpt-5-nano"  # default
        llm_config_path = repo_root / ".spade/llm.json"
        if llm_config_path.exists():
            try:
                llm_config = json.loads(llm_config_path.read_text(encoding="utf-8"))
                model_name = llm_config.get("model", model_name)
            except Exception:
                pass  # Keep default if reading fails
        
        summary = {
            "visited": visited_count,
            "descended": descended_count,
            "components": comps,
            "avg_confidence": round(avg_conf, 2),
            "duration_ms": int((time.time() - start_time) * 1000),
            "limits": {
                "max_depth": cfg.limits.max_depth,
                "max_nodes": cfg.limits.max_nodes,
                "max_llm_calls": cfg.limits.max_llm_calls,
                "nav_cap": cfg.caps.nav.max_children_per_step
            },
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": model_name
        }
        
        summary_path = repo_root / ".spade/summary.json"
        save_json_data(summary_path, summary)
        logger.debug(f"[phase0] wrote summary to {summary_path}")
    except Exception as e:
        logger.warning(f"[phase0] failed to write summary.json: {e}")

    # Generate Phase-0 report
    from report import write_phase0_report
    try:
        write_phase0_report(repo_root, cfg)
    except Exception as e:
        logger.warning(f"[report] failed: {e}")
