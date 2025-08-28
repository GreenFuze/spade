"""
SPADE Context Builder
Builds LLM context from directory metadata and scaffold data

NOTE: This file is temporarily commented out as LLM interactions are disabled.
"""

# import json
# from pathlib import Path
# from typing import Dict, List, Optional

# from schemas import RunConfig, load_json
# from logger import get_logger

# Use get_logger() directly instead of storing local copy


# def pretty_json(obj) -> str:
#     """Format object as pretty JSON string."""
#     return json.dumps(obj, indent=2, ensure_ascii=False)


# def render_context_preview(context: Dict, width: int = 80) -> str:
#     """
#     Render a text preview of the context for debugging.
#
#     Args:
#         context: Context dictionary
#         width: Maximum line width
#
#     Returns:
#         Formatted text preview
#     """
#     lines = []
#
#     # Current directory
#     current = context.get("current", {})
#     lines.append(f"Current: {current.get('path', '?')} (depth={current.get('depth', 0)})")
#     lines.append(f"  Files: {current.get('counts', {}).get('files', 0)}, Dirs: {current.get('counts', {}).get('dirs', 0)}")
#
#     # Siblings
#     siblings = context.get("siblings", [])
#     if siblings:
#         lines.append(f"Siblings ({len(siblings)}):")
#         for sibling in siblings[:5]:  # Show first 5
#             lines.append(f"  {sibling.get('path', '?')} (depth={sibling.get('depth', 0)})")
#         if len(siblings) > 5:
#             lines.append(f"  ... and {len(siblings) - 5} more")
#     else:
#         lines.append("Siblings: none")
#
#     # Ancestors
#     ancestors = context.get("ancestors", [])
#     if ancestors:
#         lines.append(f"Ancestors ({len(ancestors)}):")
#         for ancestor in ancestors:
#             lines.append(f"  {ancestor.get('path', '?')} (depth={ancestor.get('depth', 0)})")
#     else:
#         lines.append("Ancestors: none")
#
#     return "\n".join(lines)


# def build_ancestors(repo_root: Path, current_rel: str) -> List[Dict]:
#     """
#     Build ancestor chain from scaffold data.
#
#     Args:
#         repo_root: Root directory of the repository
#         current_rel: Current relative path
#
#     Returns:
#         List of ancestor metadata dictionaries
#     """
#     if current_rel == ".":
#         return []
#
#     ancestors = []
#     parts = current_rel.split("/")
#
#     # Build ancestor chain
#     for i in range(len(parts) - 1):
#         ancestor_rel = "/".join(parts[:i + 1])
#         ancestor_dirmeta = _get_dirmeta_from_file(repo_root, ancestor_rel)
#
#         if ancestor_dirmeta:
#             ancestors.append({
#                 "path": ancestor_dirmeta.path,
#                 "depth": ancestor_dirmeta.depth,
#                 "counts": ancestor_dirmeta.counts.model_dump(),
#                 "samples": ancestor_dirmeta.samples.model_dump(),
#                 "ext_histogram": ancestor_dirmeta.ext_histogram,
#                 "markers": ancestor_dirmeta.markers,
#                 "deterministic_scoring": ancestor_dirmeta.deterministic_scoring,
#             })
#
#     return ancestors


# def _get_dirmeta_from_tree(tree, rel_path: str):
#     """Get DirMeta from tree if available."""
#     if not tree or rel_path not in tree.nodes:
#         return None
#     return tree.nodes[rel_path]


# def _get_dirmeta_from_file(repo_root: Path, rel_path: str):
#     """Get DirMeta from file if available."""
#     dm_path = (
#         repo_root
#         / ".spade"
#         / "snapshot"
#         / (rel_path if rel_path != "." else ".")
#         / "dirmeta.json"
#     )
#     if not dm_path.exists():
#         return None

#     try:
#         return load_json(dm_path, DirMeta)
#     except Exception as e:
#         get_logger().warning(f"[context] failed to load dirmeta for {rel_path}: {e}")
#         return None


# def build_phase0_context(
#     repo_root: Path,
#     current_rel: str,
#     config: RunConfig,
#     tree: Optional[DirMetaTree] = None,
# ) -> Dict:
#     """
#     Build the exact PHASE0_CONTEXT_JSON payload for the LLM.

#     Args:
#         repo_root: Root directory of the repository
#         current_rel: Current relative path being analyzed
#         config: Runtime configuration
#         tree: Optional DirMetaTree instance (preferred over file loading)

#     Returns:
#         Dictionary containing the complete context for LLM analysis
#     """
#     # Get current directory metadata
#     current_dirmeta = None
#     if tree:
#         current_dirmeta = _get_dirmeta_from_tree(tree, current_rel)
#     else:
#         current_dirmeta = _get_dirmeta_from_file(repo_root, current_rel)

#     if not current_dirmeta:
#         get_logger().error(f"[context] no dirmeta found for {current_rel}")
#         # Return minimal context
#         return {
#             "current": {
#                 "path": current_rel,
#                 "depth": 0,
#                 "counts": {"files": 0, "dirs": 0},
#                 "siblings": [],
#                 "excluded_children": [],
#                 "samples": {"dirs": [], "files": []},
#                 "ext_histogram": {},
#                 "markers": [],
#                 "deterministic_scoring": {},
#             },
#             "ancestors": [],
#             "siblings": [],
#         }

#     # Build ancestor information
#     ancestors = build_ancestors(repo_root, current_rel)

#     # Build siblings information
#     siblings = []
#     if current_dirmeta.siblings:
#         # Get metadata for sibling directories
#         for sibling_name in current_dirmeta.siblings:
#             sibling_rel = (
#                 f"{current_rel}/{sibling_name}" if current_rel != "." else sibling_name
#             )

#             sibling_dirmeta = None
#             if tree:
#                 sibling_dirmeta = _get_dirmeta_from_tree(tree, sibling_rel)
#             else:
#                 sibling_dirmeta = _get_dirmeta_from_file(repo_root, sibling_rel)

#             if sibling_dirmeta:
#                 siblings.append(
#                     {
#                         "path": sibling_rel,
#                         "depth": sibling_dirmeta.depth,
#                         "counts": sibling_dirmeta.counts.model_dump(),
#                         "samples": sibling_dirmeta.samples.model_dump(),
#                         "ext_histogram": sibling_dirmeta.ext_histogram,
#                         "markers": sibling_dirmeta.markers,
#                         "deterministic_scoring": sibling_dirmeta.deterministic_scoring,
#                     }
#                 )

#     # Apply caps to siblings
#     if config.caps.context.max_siblings_in_prompt != 0:
#         siblings = siblings[: config.caps.context.max_siblings_in_prompt]

#     # Build current directory context
#     current = {
#         "path": current_dirmeta.path,
#         "depth": current_dirmeta.depth,
#         "counts": current_dirmeta.counts.model_dump(),
#         "samples": current_dirmeta.samples.model_dump(),
#         "ext_histogram": current_dirmeta.ext_histogram,
#         "markers": current_dirmeta.markers,
#         "deterministic_scoring": current_dirmeta.deterministic_scoring,
#         "siblings": current_dirmeta.siblings,
#         "excluded_children": current_dirmeta.excluded_children,
#     }

#     # Apply caps to ancestors
#     if config.caps.context.max_ancestors_in_prompt != 0:
#         ancestors = ancestors[: config.caps.context.max_ancestors_in_prompt]

#     # Build complete context
#     context = {
#         "current": current,
#         "ancestors": ancestors,
#         "siblings": siblings,
#     }

#     # Add context metadata
#     context["_metadata"] = {
#         "caps_applied": {
#             "max_ancestors_in_prompt": config.caps.context.max_ancestors_in_prompt,
#             "max_siblings_in_prompt": config.caps.context.max_siblings_in_prompt,
#         },
#         "truncation_info": {
#             "ancestors_truncated": len(ancestors) < len(build_ancestors(repo_root, current_rel)),
#             "siblings_truncated": len(siblings) < len(current_dirmeta.siblings) if current_dirmeta.siblings else False,
#         },
#     }

#     return context
