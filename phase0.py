"""
SPADE Phase 0 - Directory-based Scaffold Inference
Phase 0 specific implementation for directory structure analysis
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from agent import Agent, LLMClient, PromptLoader
from directory_snapshot import DirectorySnapshot
from logger import get_logger


class Phase0Context:
    """Builds the LLM input context from directory snapshot."""
    
    def __init__(self, repo_root: Path, dirs_snapshot: List[Dict], max_depth: int, max_entries: int, logger: logging.Logger = None):
        self.repo_root = repo_root
        self.dirs_snapshot = dirs_snapshot
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.logger = logger or get_logger()
    
    def to_dict(self) -> Dict:
        """Converts context to dictionary for LLM input."""
        git_present = (self.repo_root / ".git").exists()
        
        context = {
            "repo": {
                "root": str(self.repo_root.absolute()),
                "git_present": git_present
            },
            "dirs": self.dirs_snapshot,
            "limits": {
                "max_depth": self.max_depth,
                "max_entries_per_dir": self.max_entries
            }
        }
        
        self.logger.debug(f"Built context with {len(self.dirs_snapshot)} directories, git_present={git_present}")
        return context


class Phase0Agent(Agent):
    """Phase 0 agent for directory-based scaffold inference."""
    
    def __init__(self, repo_root: Path, model_id: str = "gpt-5-nano", max_depth: int = 3, max_entries: int = 40):
        super().__init__(repo_root, model_id)
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.logger.debug(f"Phase 0 configuration: max_depth={self.max_depth}, max_entries={self.max_entries}")
    
    def run(self) -> None:
        """Main execution flow for Phase 0."""
        try:
            self.logger.debug("Starting Phase 0 execution")
            
            # Step 1: Start telemetry
            self.telemetry.start()
            self.logger.debug("Telemetry started")
            
            # Step 2: Scan directories
            self.logger.debug("Step 2: Scanning directories")
            snapshot = DirectorySnapshot(self.repo_root, self.max_depth, self.max_entries, self.logger)
            dirs_data = snapshot.scan()
            
            # Record scan stats
            skipped_dirs = [d for d in DirectorySnapshot.SKIP_DIRS if (self.repo_root / d).exists()]
            self.telemetry.record_scan_stats(len(dirs_data), self.max_depth, self.max_entries, skipped_dirs)
            self.logger.debug(f"Recorded scan stats: {len(dirs_data)} dirs, {len(skipped_dirs)} skipped")
            
            # Step 3: Build context
            self.logger.debug("Step 3: Building context")
            context = Phase0Context(self.repo_root, dirs_data, self.max_depth, self.max_entries, self.logger)
            context_dict = context.to_dict()
            
            # Step 4: Load prompts
            self.logger.debug("Step 4: Loading prompts")
            prompt_loader = PromptLoader(self.prompts_dir, self.logger)
            system_text = prompt_loader.load_system("phase0_scaffold")
            user_template = prompt_loader.load_user("phase0_scaffold")
            
            # Insert context into user prompt
            user_text = user_template.replace("{{PHASE0_CONTEXT_JSON}}", json.dumps(context_dict, indent=2))
            self.logger.debug(f"Built user prompt with {len(user_text)} chars")
            
            # Step 5: Call LLM
            self.logger.debug("Step 5: Calling LLM")
            llm_client = LLMClient(self.model_id, self.logger)
            scaffold_dict, llm_stats = llm_client.infer(system_text, user_text)
            
            # Record LLM stats
            self.telemetry.record_llm_stats(**llm_stats)
            self.logger.debug(f"Recorded LLM stats: {llm_stats}")
            
            # Step 6: Compute scaffold stats
            self.logger.debug("Step 6: Computing scaffold stats")
            big_blocks = scaffold_dict.get("inferred", {}).get("big_blocks", [])
            confidences = [block.get("confidence", 0) for block in big_blocks]
            questions = scaffold_dict.get("open_questions_ranked", [])
            
            conf_min = min(confidences) if confidences else 0
            conf_max = max(confidences) if confidences else 0
            conf_avg = sum(confidences) / len(confidences) if confidences else 0.0
            
            self.telemetry.record_scaffold_stats(
                len(big_blocks), conf_min, conf_max, conf_avg, len(questions)
            )
            self.logger.debug(f"Scaffold stats: {len(big_blocks)} blocks, confidence {conf_min}-{conf_max} (avg: {conf_avg:.1f}), {len(questions)} questions")
            
            # Step 7: Write outputs
            self.logger.debug("Step 7: Writing outputs")
            context_path = self.writer.write_context("phase0", context_dict)
            scaffold_path = self.writer.write_scaffold("phase0", scaffold_dict)
            telemetry_path = self.writer.append_telemetry(self.telemetry)
            
            # Step 8: End telemetry and print summary
            self.telemetry.end(success=True)
            self.logger.debug("Phase 0 execution completed successfully")
            
            print(f"✓ wrote {context_path}")
            print(f"✓ wrote {scaffold_path}")
            print(f"✓ appended {telemetry_path}")
            print(f"model: {self.model_id}  dirs: {len(dirs_data)}  blocks: {len(big_blocks)}  conf(avg): {conf_avg:.1f}")
            
        except Exception as e:
            # Step 9: Handle exceptions
            self.logger.error(f"Phase 0 execution failed: {e}")
            self.telemetry.end(success=False, error_message=str(e))
            self.writer.append_telemetry(self.telemetry)
            raise
