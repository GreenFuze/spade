from __future__ import annotations
from pathlib import Path
import json, collections, datetime
from typing import Dict, List, Tuple
from logger import get_logger
from models import RunConfig, DirMeta
from models import load_json, save_json_data
from languages import active_map, aggregate_languages

def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _load_summary(repo_root: Path) -> dict:
    p = repo_root/".spade/summary.json"
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def _iter_dirmeta(repo_root: Path):
    for dm in (repo_root/".spade/snapshot").rglob("dirmeta.json"):
        try:
            yield load_json(dm, DirMeta)
        except Exception:
            continue

def _ignored_stats(dirmetas: List[DirMeta]) -> Dict[str,int]:
    c = collections.Counter()
    total = 0
    for dm in dirmetas:
        if dm.ignored_reason:
            total += 1
            c[dm.ignored_reason] += 1
    return {"total_ignored": total, "reasons": dict(c.most_common())}

def _deterministic_language_inventory(repo_root: Path, cfg: RunConfig, dirmetas: List[DirMeta]) -> List[Tuple[str,int]]:
    ext2lang = active_map(cfg, repo_root)
    lang_counts = collections.Counter()
    for dm in dirmetas:
        for lang, n in aggregate_languages(dm.ext_histogram or {}, ext2lang):
            lang_counts[lang] += int(n)
    return lang_counts.most_common()

def _llm_language_inventory(repo_root: Path) -> List[Tuple[str,int]]:
    p = repo_root/".spade/scaffold/repository_scaffold.json"
    counts = collections.Counter()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for nd in (data or {}).values():
                for lang in (nd.get("languages") or []):
                    counts[str(lang).lower()] += 1
        except Exception:
            pass
    return counts.most_common()

def _components_snapshot(repo_root: Path) -> List[dict]:
    p = repo_root/".spade/scaffold/high_level_components.json"
    if not p.exists(): return []
    try:
        comps = json.loads(p.read_text(encoding="utf-8"))
        # keep concise evidence
        for c in comps:
            ev = c.get("evidence") or []
            c["evidence"] = ev[:3]
            # show at most 5 dirs
            c["dirs"] = (c.get("dirs") or [])[:5]
        return comps
    except Exception:
        return []

def _node_summaries(repo_root: Path, k: int = 15) -> List[dict]:
    nodes_path = repo_root/".spade/scaffold/repository_scaffold.json"
    if not nodes_path.exists(): return []
    try:
        nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    # Gather depth from dirmeta and use last_updated_step for recency
    dm_index = {}
    for dm in (repo_root/".spade/snapshot").rglob("dirmeta.json"):
        try:
            obj = json.loads(dm.read_text(encoding="utf-8"))
            dm_index[obj.get("path",".")] = obj.get("depth", 0)
        except Exception:
            continue
    items = []
    for path, nd in nodes.items():
        items.append({
            "path": path,
            "depth": dm_index.get(path, 0),
            "summary": nd.get("summary"),
            "languages": nd.get("languages") or [],
            "confidence": nd.get("confidence", 0.0),
            "last_updated_step": nd.get("last_updated_step", -1)
        })
    items.sort(key=lambda x: (-int(x["last_updated_step"]), x["depth"], x["path"]))
    return items[:k]

def _det_scoring_coverage(repo_root: Path, dirmetas: List[DirMeta]) -> dict:
    total = 0; with_scores = 0; children_scored = 0
    reason_counts = collections.Counter()
    for dm in dirmetas:
        total += 1
        ds = getattr(dm, "deterministic_scoring", {}) or {}
        # normalize dict form
        children = ds.get("children") if isinstance(ds, dict) and "children" in ds else ds
        if isinstance(children, dict) and children:
            with_scores += 1
            children_scored += len(children)
            for meta in children.values():
                for r in (meta.get("reasons") if isinstance(meta, dict) else []) or []:
                    # collapse reason bucket to its prefix (e.g., "marker:go.mod" -> "marker")
                    reason_counts[r.split(":",1)[0]] += 1
    return {
        "nodes_with_scores": with_scores,
        "avg_children_scored": (children_scored/with_scores) if with_scores else 0.0,
        "top_reason_types": dict(reason_counts.most_common(5))
    }

def _collect_open_questions(repo_root: Path, limit: int = 20) -> List[str]:
    root = repo_root/".spade/analysis"
    agg = collections.Counter()
    if not root.exists(): return []
    for f in root.rglob("llm_inferred.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            oq = (data.get("open_questions_ranked") if isinstance(data, dict) else None) or []
            for q in oq:
                s = str(q).strip()
                if s:
                    agg[s] += 1
        except Exception:
            continue
    return [q for q,_ in agg.most_common(limit)]

def build_phase0_report(repo_root: Path, cfg: RunConfig) -> dict:
    dirmetas = list(_iter_dirmeta(repo_root))
    summ = _load_summary(repo_root)  # produced at end of phase0 run
    ignored = _ignored_stats(dirmetas)
    det_langs = _deterministic_language_inventory(repo_root, cfg, dirmetas)
    llm_langs = _llm_language_inventory(repo_root)
    # Reconcile: intersection by order of deterministic first, then remaining union from LLM
    det_set = [l for l,_ in det_langs]
    llm_set = [l for l,_ in llm_langs]
    reconciled = det_set + [l for l in llm_set if l not in det_set]
    components = _components_snapshot(repo_root)
    nodes = _node_summaries(repo_root, k=15)
    scoring = _det_scoring_coverage(repo_root, dirmetas)
    questions = _collect_open_questions(repo_root, limit=20)

    out = {
        "repo": repo_root.name,
        "timestamp_utc": _utc_now_iso(),
        "run": {
            "visited": summ.get("visited"),
            "descended": summ.get("descended"),
            "components": summ.get("components"),
            "avg_confidence": summ.get("avg_confidence"),
            "duration_ms": summ.get("duration_ms"),
            "limits": summ.get("limits")
        },
        "ignored": ignored,
        "languages": {
            "deterministic_exts": det_langs,
            "llm_inferred": llm_langs,
            "reconciled_order": reconciled[:10]
        },
        "components": components[:15],
        "node_summaries": nodes,
        "deterministic_scoring": scoring,
        "open_questions": questions,
        "next_steps": {
            "resume_hint": "Run phase0 again to continue traversal or adjust .spade/.spadeignore and rerun --refresh.",
            "tune_prompt_hint": "Refine phase0 prompts to target weak summaries or unclear components."
        }
    }
    return out

def write_phase0_report(repo_root: Path, cfg: RunConfig) -> None:
    report = build_phase0_report(repo_root, cfg)
    rpt_dir = repo_root/".spade/reports"
    rpt_dir.mkdir(parents=True, exist_ok=True)
    save_json_data(rpt_dir/"phase0_overview.json", report)
    # MD rendering (concise)
    md_lines = []
    md_lines.append(f"# Phase-0 Overview — {report['repo']}")
    run = report.get("run") or {}
    md_lines.append(f"- Visited: {run.get('visited')}  ·  Descended: {run.get('descended')}  ·  Components: {run.get('components')}  ·  Avg conf: {run.get('avg_confidence')}")
    md_lines.append(f"- Ignored dirs: {report['ignored'].get('total_ignored')}  ·  Top reasons: {', '.join(f'{k}×{v}' for k,v in (report['ignored'].get('reasons') or {}).items())}")
    md_lines.append("\n## Languages")
    rec = report["languages"]["reconciled_order"]
    md_lines.append(f"- Reconciled top: {', '.join(rec[:10]) if rec else '—'}")
    md_lines.append("\n## Components")
    for c in report["components"]:
        md_lines.append(f"- **{c.get('name')}** — {c.get('role')} (conf {c.get('confidence')}) · dirs: {', '.join(c.get('dirs') or [])}")
    md_lines.append("\n## Notable directories")
    for n in report["node_summaries"]:
        langs = ", ".join(n.get("languages") or [])
        md_lines.append(f"- `{n['path']}` (d={n['depth']}, conf={n['confidence']}) — {langs} — {n.get('summary')}")
    if report["open_questions"]:
        md_lines.append("\n## Open questions")
        for q in report["open_questions"]:
            md_lines.append(f"- {q}")
    (rpt_dir/"phase0_overview.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    get_logger().info(f"[report] wrote .spade/reports/phase0_overview.json and .md")
