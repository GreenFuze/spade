"""
SPADE Phase-0 Context Builder
Builds the exact PHASE0_CONTEXT_JSON payload for the LLM
"""

from __future__ import annotations
from pathlib import Path
import json
from copy import deepcopy
from typing import Dict, List

from schemas import RunConfig, DirMeta, load_json
from logger import get_logger

logger = get_logger()


def _load_nodes_scaffold(repo_root: Path) -> Dict[str, Dict]:
    """
    Load scaffold nodes from repository_scaffold.json if present.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        Dictionary mapping relative paths to node data, or empty dict if file doesn't exist
    """
    path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    if not path.exists():
        return {}
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        else:
            logger.warning(f"[context] scaffold file contains non-dict data: {type(data)}")
            return {}
    except Exception as e:
        logger.warning(f"[context] failed to load scaffold file: {e}")
        return {}


def _ancestor_chain(rel: str) -> List[str]:
    """
    Return root→…→parent chain as relpaths.
    
    Args:
        rel: Relative path like ".", "api", "web/subdir"
        
    Returns:
        List of ancestor paths, e.g. for "a/b/c": [".","a","a/b"]
        For ".", return [] (no ancestors)
    """
    if rel == ".":
        return []
    
    parts = rel.split("/")
    if len(parts) == 1:
        # Single-level path like "api" -> just root
        return ["."]
    
    ancestors = []
    current = ""
    
    for part in parts[:-1]:  # Exclude the last part (current directory)
        if current:
            current = f"{current}/{part}"
        else:
            current = part
        ancestors.append(current)
    
    # Add root if we have any ancestors
    if ancestors:
        ancestors.insert(0, ".")
    
    return ancestors


def build_ancestors(repo_root: Path, current_rel: str) -> List[Dict]:
    """
    Build ancestor list from scaffold data.
    
    Args:
        repo_root: Root directory of the repository
        current_rel: Current relative path
        
    Returns:
        List of ancestor dictionaries with path, summary, and tags
    """
    nodes = _load_nodes_scaffold(repo_root)
    
    # If no scaffold data, return empty list
    if not nodes:
        return []
    
    out = []
    
    for p in _ancestor_chain(current_rel):
        nd = nodes.get(p, {})
        summary = nd.get("summary")
        tags = nd.get("tags", [])
        out.append({
            "path": p,
            "summary": summary,
            "tags": tags
        })
    
    return out


def build_phase0_context(repo_root: Path, current_rel: str, cfg: RunConfig) -> Dict:
    """
    Build the exact PHASE0_CONTEXT_JSON payload for the LLM.
    
    Args:
        repo_root: Root directory of the repository
        current_rel: Current relative path like ".", "api", "web/subdir"
        cfg: Runtime configuration (read-only)
        
    Returns:
        Dictionary matching the PHASE0_CONTEXT_JSON schema
        
    Raises:
        FileNotFoundError: If dirmeta.json doesn't exist for current_rel
    """
    # Determine dirmeta path
    if current_rel == ".":
        dm_path = repo_root / ".spade" / "snapshot" / "dirmeta.json"
    else:
        dm_path = repo_root / ".spade" / "snapshot" / current_rel / "dirmeta.json"
    
    if not dm_path.exists():
        raise FileNotFoundError(f"dirmeta not found for {current_rel}: {dm_path}")
    
    # Load and validate dirmeta
    dirmeta = load_json(dm_path, DirMeta)
    
    # Extract siblings/excluded (LLM wants them top-level)
    siblings = sorted(dirmeta.siblings)
    siblings_total = len(siblings)
    if cfg.caps.context.max_siblings_in_prompt != 0:
        siblings = siblings[:cfg.caps.context.max_siblings_in_prompt]
    
    excluded = sorted(dirmeta.excluded_children)
    
    # Wrap deterministic_scoring into {"children": ...} for the LLM context
    det_scores = getattr(dirmeta, "deterministic_scoring", {}) or {}
    
    # Apply caps to deterministic scoring children
    children_scores_total = len(det_scores)
    if cfg.caps.context.max_children_scores_in_prompt != 0 and children_scores_total > cfg.caps.context.max_children_scores_in_prompt:
        # Sort by score desc, then by name asc
        sorted_children = sorted(
            det_scores.items(),
            key=lambda x: (-x[1].score, x[0].lower())
        )
        det_scores = dict(sorted_children[:cfg.caps.context.max_children_scores_in_prompt])
    
    # Apply caps to reasons per child
    for child_score in det_scores.values():
        if cfg.caps.context.max_reasons_per_child != 0 and len(child_score.reasons) > cfg.caps.context.max_reasons_per_child:
            child_score.reasons = child_score.reasons[:cfg.caps.context.max_reasons_per_child]
    
    det_for_llm = {"children": {k: v.model_dump() if hasattr(v, 'model_dump') else v for k, v in det_scores.items()}}
    
    # Build "current" by removing fields that the LLM gets at top-level
    cur = dirmeta.model_dump()
    for k in ("siblings", "excluded_children", "deterministic_scoring"):
        cur.pop(k, None)
    
    # Build ancestors with caps
    ancestors = build_ancestors(repo_root, current_rel)
    ancestors_total = len(ancestors)
    if cfg.caps.context.max_ancestor_summaries != 0:
        ancestors = ancestors[:cfg.caps.context.max_ancestor_summaries]
    
    # Build context
    context = {
        "repo_root_name": repo_root.name,
        "ancestors": ancestors,
        "current": cur,
        "siblings": siblings,
        "excluded_children": excluded,
        "deterministic_scoring": det_for_llm,
        "context_meta": {
            "siblings_included": len(siblings),
            "siblings_total": siblings_total,
            "children_scores_included": len(det_scores),
            "children_scores_total": children_scores_total,
            "max_reasons_per_child": cfg.caps.context.max_reasons_per_child,
            "ancestors_included": len(ancestors),
            "ancestors_total": ancestors_total
        }
    }
    
    logger.info(f"[context] built for {current_rel}: siblings={len(siblings)}/{siblings_total} excluded={len(excluded)} children={len(det_scores)}/{children_scores_total}")
    return context


def pretty_json(data: Dict) -> str:
    """
    Pretty-print JSON data for debugging.
    
    Args:
        data: Dictionary to format
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)


def render_context_preview(context: dict, width: int = 100) -> str:
    """
    Return a concise human-readable preview:
      - path, depth, ancestors (paths)
      - siblings (count included/total)
      - deterministic children by score (top 10 names with scores; reasons truncated by caps)
      - languages from current.ext_histogram (top 5 via active map) and any scaffold langs if present in ancestors section
      - context_meta line
    Do NOT read scaffold here; use only the provided `context` payload.
    
    Args:
        context: The PHASE0_CONTEXT_JSON dictionary
        width: Maximum line width for wrapping
        
    Returns:
        Formatted preview string
    """
    lines = []
    
    # Path and depth
    current = context.get("current", {})
    path = current.get("path", "unknown")
    depth = current.get("depth", 0)
    lines.append(f"Path: {path} (depth: {depth})")
    
    # Ancestors
    ancestors = context.get("ancestors", [])
    if ancestors:
        ancestor_paths = [a.get("path", "unknown") for a in ancestors]
        lines.append(f"Ancestors: {' → '.join(ancestor_paths)}")
    else:
        lines.append("Ancestors: (none)")
    
    # Siblings
    siblings = context.get("siblings", [])
    context_meta = context.get("context_meta", {})
    siblings_included = context_meta.get("siblings_included", len(siblings))
    siblings_total = context_meta.get("siblings_total", len(siblings))
    lines.append(f"Siblings: {siblings_included}/{siblings_total}")
    
    # Deterministic children by score (top 10)
    det_scoring = context.get("deterministic_scoring", {})
    children = det_scoring.get("children", {})
    if children:
        # Sort by score desc, then name asc
        sorted_children = sorted(
            children.items(),
            key=lambda x: (-x[1].get("score", 0), x[0].lower())
        )
        
        lines.append("Top children by score:")
        for i, (child_name, child_data) in enumerate(sorted_children[:10]):
            score = child_data.get("score", 0)
            reasons = child_data.get("reasons", [])
            
            # Format reasons (truncated by caps)
            reason_str = ""
            if reasons:
                reason_parts = []
                for reason in reasons:
                    if "marker:" in reason:
                        reason_parts.append(f"marker:{reason.split('marker:')[1].split('|')[0].strip()}")
                    elif "lang:" in reason:
                        reason_parts.append(f"lang:{reason.split('lang:')[1].split('|')[0].strip()}")
                    elif "size:" in reason:
                        reason_parts.append(f"size:{reason.split('size:')[1].split('|')[0].strip()}")
                    else:
                        reason_parts.append(reason.split('|')[0].strip())
                reason_str = " | ".join(reason_parts[:3])  # Limit to 3 reasons for display
            
            line = f"  {i+1:2d}. {child_name} ({score:.3f})"
            if reason_str:
                line += f" — {reason_str}"
            lines.append(line)
    else:
        lines.append("Children: (none)")
    
    # Languages from current.ext_histogram
    ext_histogram = current.get("ext_histogram", {})
    if ext_histogram:
        # Sort by count desc, take top 5
        sorted_exts = sorted(ext_histogram.items(), key=lambda x: (-x[1], x[0].lower()))[:5]
        ext_str = ", ".join([f"{ext}({count})" for ext, count in sorted_exts])
        lines.append(f"Languages: {ext_str}")
    else:
        lines.append("Languages: (none)")
    
    # Context meta summary
    meta = context.get("context_meta", {})
    if meta:
        meta_parts = []
        if "children_scores_included" in meta and "children_scores_total" in meta:
            meta_parts.append(f"children:{meta['children_scores_included']}/{meta['children_scores_total']}")
        if "ancestors_included" in meta and "ancestors_total" in meta:
            meta_parts.append(f"ancestors:{meta['ancestors_included']}/{meta['ancestors_total']}")
        if "max_reasons_per_child" in meta:
            meta_parts.append(f"max_reasons:{meta['max_reasons_per_child']}")
        
        if meta_parts:
            lines.append(f"Context caps: {', '.join(meta_parts)}")
    
    # Join lines and wrap if needed
    result = "\n".join(lines)
    
    # Simple line wrapping (best effort)
    if width > 0:
        wrapped_lines = []
        for line in result.split('\n'):
            if len(line) <= width:
                wrapped_lines.append(line)
            else:
                # Simple word wrapping
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= width:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        if current_line:
                            wrapped_lines.append(current_line)
                            current_line = word
                        else:
                            # Word is too long, break it
                            wrapped_lines.append(word[:width])
                            current_line = word[width:]
                if current_line:
                    wrapped_lines.append(current_line)
        result = "\n".join(wrapped_lines)
    
    return result
