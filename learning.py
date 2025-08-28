"""
SPADE Learning Coordinator
Post-snapshot learning passes for markers and languages with re-scoring

NOTE: This file is temporarily commented out as LLM interactions are disabled.
"""

# import json
# import collections
# from pathlib import Path
# from typing import Counter

# from logger import get_logger
# from schemas import RunConfig, DirMeta, load_json, save_json, save_json_data
# from ignore import load_specs, should_skip
# from llm import LLMClient
# from languages import active_map
# from markers import active_rules

# Use get_logger() directly instead of storing local copy


# def build_name_histogram(repo_root: Path, cfg: RunConfig) -> Counter[str]:
#     """
#     For each snapshotted directory (depth ≤ max_depth, not ignored), list immediate entries (files+dirs)
#     and count by name. Skip entries that match ignore rules. Return Counter of names.
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#
#     Returns:
#         Counter of entry names with their frequencies
#     """
#     ignore_spec, allow_spec, _, _ = load_specs(repo_root)
#     base = repo_root / ".spade/snapshot"
#     hist = collections.Counter()
#
#     for dm_path in base.rglob("dirmeta.json"):
#         try:
#             dm = load_json(dm_path, DirMeta)
#         except Exception:
#             continue
#
#         if dm.ignored_reason:
#             continue
#
#         dir_fs = repo_root / ("" if dm.path == "." else dm.path)
#         try:
#             for p in dir_fs.iterdir():
#                 # filter by ignore specs
#                 if should_skip(p, repo_root, ignore_spec, allow_spec, cfg.policies.skip_symlinks):
#                     continue
#                 # Skip .spade directory entries
#                 if p.name == ".spade":
#                     continue
#                 hist[p.name] += 1
#         except OSError:
#             # unreadable; already recorded earlier
#             continue
#
#     return hist


# def build_unknown_ext_histogram(repo_root: Path, cfg: RunConfig) -> Counter[str]:
#     """
#     Aggregate ext_histogram keys across all dirmeta and return those NOT in active ext→lang map (seed∪learned if enabled).
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#
#     Returns:
#         Counter of unknown extensions with their frequencies
#     """
#     base = repo_root / ".spade/snapshot"
#     ext2lang = active_map(cfg, repo_root)
#     hist = collections.Counter()
#
#     for dm_path in base.rglob("dirmeta.json"):
#         try:
#             dm = load_json(dm_path, DirMeta)
#         except Exception:
#             continue
#
#         for ext, n in (dm.ext_histogram or {}).items():
#             key = ext.lower().lstrip(".")
#             if not key or key in ext2lang:
#                 continue
#             if isinstance(n, int) and n > 0:
#                 hist[key] += n
#
#     return hist


# def learn_markers_once(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
#     """
#     If cfg.learn_markers is True and .spade/markers.learned.json does not exist:
#       - Build name histogram
#       - Remove entries that are already known markers (seed ∪ learned if use_learned_markers True)
#       - Take top-K = cfg.marker_learning.top_k_candidates
#       - Call LLM to classify; filter by confidence ≥ cfg.marker_learning.min_confidence
#       - Save to .spade/markers.learned.json
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#         llm: LLM client for marker learning
#     """
#     if not cfg.learn_markers:
#         return
#
#     learned_path = repo_root / ".spade/markers.learned.json"
#     if learned_path.exists():
#         return
#
#     get_logger().info("[learning] starting marker learning pass")
#
#     # Build name histogram
#     hist = build_name_histogram(repo_root, cfg)
#
#     # Remove known markers
#     known_markers = set()
#     if cfg.use_learned_markers:
#         known_markers.update(active_rules(cfg, repo_root))
#
#     candidates = []
#     for name, count in hist.most_common(cfg.marker_learning.top_k_candidates):
#         if name not in known_markers:
#             candidates.append((name, count))
#
#     if not candidates:
#         get_logger().info("[learning] no new marker candidates found")
#         return
#
#     # Call LLM
#     res = llm.learn_markers(repo_root.name, cfg.marker_learning.min_confidence, candidates)
#
#     if res:
#         # Save learned markers
#         learned_data = {
#             "learned_at": save_json_data(datetime.now()),
#             "candidates_processed": len(candidates),
#             "markers_learned": res
#         }
#         save_json(learned_path, learned_data)
#         get_logger().info(f"[learning] learned {len(res)} new markers")
#     else:
#         get_logger().info("[learning] no markers learned (LLM returned empty result)")


# def learn_languages_once(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
#     """
#     If cfg.learn_languages is True and .spade/languages.learned.json does not exist:
#       - Build unknown extension histogram
#       - Take top-K = cfg.language_learning.top_k_candidates
#       - Call LLM to classify; filter by confidence ≥ cfg.language_learning.min_confidence
#       - Save to .spade/languages.learned.json
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#         llm: LLM client for language learning
#     """
#     if not cfg.learn_languages:
#         return
#
#     learned_path = repo_root / ".spade/languages.learned.json"
#     if learned_path.exists():
#         return
#
#     get_logger().info("[learning] starting language learning pass")
#
#     # Build unknown extension histogram
#     hist = build_unknown_ext_histogram(repo_root, cfg)
#
#     # Take top candidates
#     candidates = hist.most_common(cfg.language_learning.top_k_candidates)
#
#     if not candidates:
#         get_logger().info("[learning] no unknown extensions found")
#         return
#
#     # Call LLM
#     res = llm.learn_languages(repo_root.name, cfg.language_learning.min_confidence, candidates)
#
#     if res:
#         # Save learned languages
#         learned_data = {
#             "learned_at": save_json_data(datetime.now()),
#             "candidates_processed": len(candidates),
#             "languages_learned": res
#         }
#         save_json(learned_path, learned_data)
#         get_logger().info(f"[learning] learned {len(res)} new language mappings")
#     else:
#         get_logger().info("[learning] no languages learned (LLM returned empty result)")


# def run_learning_passes(repo_root: Path, cfg: RunConfig, llm: LLMClient) -> None:
#     """
#     Run all learning passes if enabled in configuration.
#
#     Args:
#         repo_root: Root directory of the repository
#         cfg: Runtime configuration
#         llm: LLM client for learning
#     """
#     # Run marker learning
#     learn_markers_once(repo_root, cfg, llm)
#
#     # Run language learning
#     learn_languages_once(repo_root, cfg, llm)
