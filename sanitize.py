"""
SPADE LLM Output Sanitization
Post-processing layer that enforces rules before merging LLM responses
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple

from models import LLMResponse, NodeUpdate, Evidence
from models import DirMeta, RunConfig
from languages import active_map, aggregate_languages
from logger import get_logger

logger = get_logger()

# Canonical language aliases (minimal; extend later)
CANON = {
    "js": "javascript", "nodejs": "javascript", "node": "javascript",
    "ts": "typescript",
    "c++": "c++", "cpp": "c++", "c plus plus": "c++",
    "objective c": "objective-c", "objective-c++": "objective-c++",
    "shell": "shell", "bash": "shell", "zsh": "shell",
    "py": "python", "golang": "go",
}


def _canon_lang(s: str) -> str:
    """Canonicalize a language name."""
    s = (s or "").strip().lower()
    return CANON.get(s, s)


def _normalize_lang_list(langs: list[str]) -> list[str]:
    """Normalize and deduplicate a list of language names."""
    out = []
    seen = set()
    for x in langs or []:
        c = _canon_lang(x)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _has_min_evidence(n: NodeUpdate) -> bool:
    """Check if node has at least one evidence item."""
    return bool(n.evidence)


def _punish_confidence(v: float, min_cap: float = 0.4) -> float:
    """Punish confidence by capping it at a lower value."""
    return min(v, min_cap)


def _rerank_with_local_exts(current_dm: DirMeta, cfg: RunConfig, langs: list[str], repo_root: Path) -> list[str]:
    """
    Reorder languages putting locally-evident ones first, based on ext_histogram mapping.
    We DO NOT invent new languages; we only reorder the list the LLM already provided.
    
    Args:
        current_dm: Current directory metadata
        cfg: Runtime configuration
        langs: List of languages from LLM
        repo_root: Repository root path
        
    Returns:
        Reordered list of languages with locally-evident ones first
    """
    ext2lang = active_map(cfg, repo_root)
    pairs = aggregate_languages(current_dm.ext_histogram or {}, ext2lang)  # [(lang,count), ...]
    local_rank = {lang: i for i, (lang, _) in enumerate(pairs)}  # smaller i => stronger
    
    def key(l):
        return (local_rank.get(l, 10_000), l)
    
    return sorted(langs, key=key)


def _split_sentences(text: str) -> list[str]:
    """Naive sentence split on [.?!] keeping order; collapse whitespace."""
    if not text:
        return []
    
    # Split on sentence endings and clean up
    sentences = []
    for sent in text.replace('\n', ' ').split('.'):
        for sub_sent in sent.split('?'):
            for final_sent in sub_sent.split('!'):
                cleaned = final_sent.strip()
                if cleaned:
                    sentences.append(cleaned)
    
    return sentences


def _trim_summary(summary: str, max_sents: int, max_chars: int) -> tuple[str, bool]:
    """Trim summary to policy caps. Returns (trimmed_text, did_trim)."""
    if not summary:
        return summary, False
    
    sentences = _split_sentences(summary)
    did_trim = False
    
    # Trim by sentence count
    if len(sentences) > max_sents:
        sentences = sentences[:max_sents]
        did_trim = True
    
    # Reconstruct and trim by character count
    result = '. '.join(sentences) + ('.' if sentences and not sentences[-1].endswith(('.', '!', '?')) else '')
    
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(' ', 1)[0] + '...'
        did_trim = True
    
    return result, did_trim


def _dedupe_cap_list(items: list[str], cap: int) -> tuple[list[str], bool]:
    """Lower/strip, preserve order, dedupe, then slice to cap. Returns (list, did_trim)."""
    if not items:
        return [], False
    
    # Normalize and dedupe while preserving order
    seen = set()
    normalized = []
    for item in items:
        norm = item.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    
    # Check if we need to trim
    did_trim = len(normalized) > cap
    if did_trim:
        normalized = normalized[:cap]
    
    return normalized, did_trim


def _dedupe_cap_evidence(evs: list[Evidence], cap: int) -> tuple[list[Evidence], bool]:
    """Dedupe by (type,value) pair, preserve order, slice to cap. Returns (list, did_trim)."""
    if not evs:
        return [], False
    
    # Ensure all items are Evidence objects
    evidence_objs = []
    for ev in evs:
        if isinstance(ev, Evidence):
            evidence_objs.append(ev)
        elif isinstance(ev, dict):
            evidence_objs.append(Evidence(**ev))
        else:
            # Skip invalid items
            continue
    
    # Dedupe by (type, value) pair while preserving order
    seen = set()
    deduped = []
    for ev in evidence_objs:
        key = (ev.type, ev.value)
        if key not in seen:
            seen.add(key)
            deduped.append(ev)
    
    # Check if we need to trim
    did_trim = len(deduped) > cap
    if did_trim:
        deduped = deduped[:cap]
    
    return deduped, did_trim


def sanitize_llm_output(
    repo_root: Path,
    cfg: RunConfig,
    current_dm: DirMeta,
    resp: LLMResponse
) -> tuple[LLMResponse, bool, str]:
    """
    Sanitize LLM output by enforcing rules and normalizing data.
    
    Args:
        repo_root: Repository root path
        cfg: Runtime configuration
        current_dm: Current directory metadata
        resp: LLM response to sanitize
        
    Returns:
        Tuple of (sanitized_llm_response, was_trimmed, trim_notes)
    """
    # 1) Enforce descend_one_level_only
    if resp.nav and resp.nav.descend_one_level_only is not True:
        resp.nav.descend_one_level_only = True

    # Allowed node paths for updates: only CURRENT or its ancestors
    allowed_paths = set()
    if current_dm.path not in (".", ""):
        parts = current_dm.path.split("/")
        allowed_paths.add(".")
        for i in range(1, len(parts)):
            allowed_paths.add("/".join(parts[:i]))
        allowed_paths.add(current_dm.path)
    else:
        allowed_paths.add(".")

    # 2) Nodes: apply policy caps and normalize
    fixed_nodes: Dict[str, NodeUpdate] = {}
    current_trimmed = False
    current_trim_notes = []
    
    for path, node in (resp.inferred.nodes or {}).items():
        if path not in allowed_paths:
            # Drop unexpected node paths (e.g., children or arbitrary)
            continue

        # Apply summary caps
        trimmed_summary, summary_trimmed = _trim_summary(
            node.summary, 
            cfg.policies.max_summary_sentences, 
            cfg.policies.max_summary_chars
        )
        if summary_trimmed:
            node.summary = trimmed_summary
            if path == current_dm.path:
                current_trimmed = True
                current_trim_notes.append("summary")

        # Apply language caps
        langs, langs_trimmed = _dedupe_cap_list(
            node.languages or [], 
            cfg.policies.max_languages_per_node
        )
        node.languages = _normalize_lang_list(langs)
        if langs_trimmed and path == current_dm.path:
            current_trimmed = True
            current_trim_notes.append("langs")

        # Apply tag caps
        tags, tags_trimmed = _dedupe_cap_list(
            node.tags or [], 
            cfg.policies.max_tags_per_node
        )
        node.tags = tags
        if tags_trimmed and path == current_dm.path:
            current_trimmed = True
            current_trim_notes.append("tags")

        # Apply evidence caps
        ev_list = node.evidence or []
        ev_objs, ev_trimmed = _dedupe_cap_evidence(ev_list, cfg.policies.max_evidence_per_node)
        node.evidence = ev_objs
        if ev_trimmed and path == current_dm.path:
            current_trimmed = True
            current_trim_notes.append("evidence")

        # Re-rank languages with local ext evidence (don't introduce new ones)
        if node.languages:
            node.languages = _rerank_with_local_exts(current_dm, cfg, node.languages, repo_root)

        # If anything was trimmed, add policy evidence and clamp confidence
        if summary_trimmed or langs_trimmed or tags_trimmed or ev_trimmed:
            node.evidence = list(node.evidence or [])
            node.evidence.append(Evidence(type="policy", value="trimmed-to-policy-caps"))
            node.confidence = min(float(node.confidence), 0.7)

        # Require evidence; punish if missing
        if not _has_min_evidence(node):
            node.confidence = _punish_confidence(float(node.confidence))
            # Add policy evidence so we can audit later
            node.evidence = list(node.evidence or [])
            node.evidence.append(Evidence(type="policy", value="missing-evidence-punish"))

        fixed_nodes[path] = node

    resp.inferred.nodes = fixed_nodes

    # 3) Components: ensure evidence present and apply caps
    comps = []
    for c in (resp.inferred.high_level_components or []):
        if not c.evidence:
            c.evidence = [Evidence(type="policy", value="missing-evidence-punish")]
            c.confidence = _punish_confidence(float(c.confidence))
        else:
            # Apply evidence caps to components too
            ev_objs, ev_trimmed = _dedupe_cap_evidence(c.evidence, cfg.policies.max_evidence_per_node)
            c.evidence = ev_objs
            if ev_trimmed:
                c.evidence.append(Evidence(type="policy", value="trimmed-to-policy-caps"))
                c.confidence = min(float(c.confidence), 0.7)
        # leave dirs as-is; tags not part of components schema (only nodes), so nothing else to normalize here
        comps.append(c)
    resp.inferred.high_level_components = comps

    trim_notes = "|".join(current_trim_notes) if current_trim_notes else ""
    return resp, current_trimmed, trim_notes
