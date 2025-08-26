"""
SPADE Scaffold Store
Maintains repository understanding and provides merge semantics
"""

from pathlib import Path
import json
from typing import Dict, List

from models import NodeUpdate, HighLevelComponent
from models import save_json, save_json_data
from logger import get_logger

logger = get_logger()


class ScaffoldStore:
    """
    Maintains repository understanding in scaffold files.
    
    Files:
    - repository_scaffold.json: per-path node understanding
    - high_level_components.json: list of global components
    """
    
    def __init__(self, repo_root: Path):
        """
        Initialize scaffold store.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.scaffold_dir = repo_root / ".spade" / "scaffold"
        self.nodes_path = self.scaffold_dir / "repository_scaffold.json"
        self.components_path = self.scaffold_dir / "high_level_components.json"
        
        # Ensure scaffold directory exists
        self.scaffold_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize files if they don't exist
        if not self.nodes_path.exists():
            save_json_data(self.nodes_path, {})  # dict[path] -> stored node dict
        
        if not self.components_path.exists():
            save_json_data(self.components_path, [])  # list of components
    
    def load_nodes(self) -> Dict:
        """
        Load nodes from repository_scaffold.json.
        
        Returns:
            Dictionary mapping paths to node data
        """
        try:
            return json.loads(self.nodes_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[scaffold] failed to load nodes: {e}; using empty")
            return {}
    
    def save_nodes(self, data: Dict) -> None:
        """
        Save nodes to repository_scaffold.json.
        
        Args:
            data: Dictionary to save
        """
        save_json_data(self.nodes_path, data)
    
    def load_components(self) -> List:
        """
        Load components from high_level_components.json.
        
        Returns:
            List of component dictionaries
        """
        try:
            return json.loads(self.components_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[scaffold] failed to load components: {e}; using empty")
            return []
    
    def save_components(self, data: List) -> None:
        """
        Save components to high_level_components.json.
        
        Args:
            data: List to save
        """
        save_json_data(self.components_path, data)
    
    def get_ancestor_chain(self, relpath: str) -> List[Dict]:
        """
        Return ancestor chain from root to parent of relpath.
        
        Args:
            relpath: Relative path like ".", "api", "web/subdir"
            
        Returns:
            List of ancestor dictionaries with path, summary, and tags
            Compatible with Task 8, which reads repository_scaffold.json directly
        """
        chain = []
        
        if relpath not in (".", "", "/"):
            pieces = relpath.split("/")
            nodes = self.load_nodes()
            
            # Root ancestor
            nd = nodes.get(".", {})
            chain.append({
                "path": ".",
                "summary": nd.get("summary"),
                "tags": nd.get("tags", [])
            })
            
            # Build all ancestor paths (root to grandparent)
            for i in range(len(pieces) - 2):  # Stop at grandparent (exclude current and parent)
                current_path = "/".join(pieces[:i+1])
                
                nd = nodes.get(current_path, {})
                chain.append({
                    "path": current_path,
                    "summary": nd.get("summary"),
                    "tags": nd.get("tags", [])
                })
        
        return chain
    
    def merge_nodes(self, updates: Dict[str, NodeUpdate], step_id: int) -> None:
        """
        Upsert nodes by path.
        
        Args:
            updates: Dictionary mapping paths to NodeUpdate objects
            step_id: Current step ID for last_updated_step tracking
            
        Stored shape (per path):
        {
            "summary": str,
            "languages": [str],
            "tags": [str],
            "evidence": [{"type": str, "value": str}],
            "confidence": float,
            "last_updated_step": int
        }
        """
        store = self.load_nodes()
        changed = 0
        
        for path, node in (updates or {}).items():
            try:
                model = node if isinstance(node, NodeUpdate) else NodeUpdate(**node)
            except Exception as e:
                logger.warning(f"[scaffold] invalid NodeUpdate for {path}: {e}; skipping")
                continue
            
            stored = store.get(path, {})
            
            # Overwrite fields as per plan
            new_obj = {
                "summary": model.summary,
                "languages": list(dict.fromkeys([s.lower() for s in (model.languages or [])])),
                "tags": list(dict.fromkeys([t.lower() for t in (model.tags or [])])),
                "evidence": [{"type": ev.type, "value": ev.value} for ev in (model.evidence or [])],
                "confidence": float(model.confidence),
                "last_updated_step": int(step_id),
            }
            
            # Optional: merge evidence without duplicates
            if stored:
                # Replace per plan; if you prefer merging evidence, do:
                # seen = {(e["type"], e["value"]) for e in stored.get("evidence", [])}
                # for ev in new_obj["evidence"]:
                #   if (ev["type"], ev["value"]) not in seen:
                #     stored["evidence"].append(ev)
                pass
            
            store[path] = new_obj
            changed += 1
        
        if changed:
            self.save_nodes(store)
            logger.info(f"[scaffold] merged nodes: {changed}")
    
    def merge_components(self, comps: List[HighLevelComponent]) -> None:
        """
        Merge high-level components with deduplication.
        
        Args:
            comps: List of HighLevelComponent objects to merge
            
        Deduplication by (name + sorted(dirs)) key. Update role/evidence/confidence conservatively:
        - role: replace with latest
        - evidence: union by (type, value)
        - confidence: max(existing, new)
        """
        existing = self.load_components()
        
        # Build index
        idx = {}
        for i, c in enumerate(existing):
            key = (c.get("name"), tuple(sorted(c.get("dirs", []))))
            idx[key] = i
        
        changed = 0
        
        for comp in (comps or []):
            try:
                model = comp if isinstance(comp, HighLevelComponent) else HighLevelComponent(**comp)
            except Exception as e:
                logger.warning(f"[scaffold] invalid component {getattr(comp, 'name', None)}: {e}; skipping")
                continue
            
            key = (model.name, tuple(sorted(model.dirs)))
            ev_union = []
            
            if key in idx:
                # Update existing component
                j = idx[key]
                curr = existing[j]
                
                # Union evidence
                seen = {(e.get("type"), e.get("value")) for e in curr.get("evidence", [])}
                ev_union = list(curr.get("evidence", []))
                
                for ev in model.evidence or []:
                    t, v = ev.type, ev.value
                    if (t, v) not in seen:
                        ev_union.append({"type": t, "value": v})
                        seen.add((t, v))
                
                # Update role + confidence
                curr["role"] = model.role
                curr["evidence"] = ev_union
                curr["confidence"] = max(float(curr.get("confidence", 0.0)), float(model.confidence))
                changed += 1
            else:
                # Add new component
                ev_union = [{"type": ev.type, "value": ev.value} for ev in (model.evidence or [])]
                newc = {
                    "name": model.name,
                    "role": model.role,
                    "dirs": list(model.dirs or []),
                    "evidence": ev_union,
                    "confidence": float(model.confidence),
                }
                existing.append(newc)
                idx[key] = len(existing) - 1
                changed += 1
        
        if changed:
            self.save_components(existing)
            logger.info(f"[scaffold] merged components: {changed}")
