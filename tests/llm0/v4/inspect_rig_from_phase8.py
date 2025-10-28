#!/usr/bin/env python3
"""
RIG Inspection Script - Comprehensive analysis of RIG generated from Phase 8
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.rig import RIG
from core.schemas import Component, Test, Aggregator, Runner, Utility, Evidence


class RIGInspector:
    """Comprehensive RIG inspection for academic paper analysis."""
    
    def __init__(self, rig: RIG):
        self.rig = rig
        self.logger = logging.getLogger("RIGInspector")
    
    def inspect_repository_info(self) -> Dict[str, Any]:
        """Inspect repository information."""
        if not self.rig._repository_info:
            return {"error": "No repository information found"}
        
        repo_info = {
            "name": self.rig._repository_info.name,
            "type": self.rig._repository_info.type,
            "primary_language": self.rig._repository_info.primary_language,
            "build_system": self.rig._repository_info.build_system.type if self.rig._repository_info.build_system else "unknown",
            "test_framework": self.rig._repository_info.build_system.test_framework if self.rig._repository_info.build_system else "unknown"
        }
        
        return repo_info
    
    def inspect_components(self) -> Dict[str, Any]:
        """Inspect all components in the RIG."""
        if not self.rig._components:
            return {"error": "No components found"}
        
        components_info = {
            "total_count": len(self.rig._components),
            "by_type": {},
            "by_language": {},
            "with_evidence": 0,
            "detailed_components": []
        }
        
        for component in self.rig._components:
            # Count by type
            comp_type = component.component_type
            components_info["by_type"][comp_type] = components_info["by_type"].get(comp_type, 0) + 1
            
            # Count by language
            lang = component.language
            components_info["by_language"][lang] = components_info["by_language"].get(lang, 0) + 1
            
            # Check evidence
            if component.evidence and component.evidence.file_path:
                components_info["with_evidence"] += 1
            
            # Detailed component info
            comp_detail = {
                "name": component.name,
                "type": component.component_type,
                "language": component.language,
                "location": component.location.type if component.location else "unknown",
                "has_evidence": bool(component.evidence and component.evidence.file_path),
                "evidence_file": component.evidence.file_path if component.evidence else None,
                "evidence_lines": f"{component.evidence.line_start}-{component.evidence.line_end}" if component.evidence and component.evidence.line_start else None
            }
            components_info["detailed_components"].append(comp_detail)
        
        return components_info
    
    def inspect_relationships(self) -> Dict[str, Any]:
        """Inspect all relationships in the RIG."""
        if not self.rig.relationships:
            return {"error": "No relationships found"}
        
        relationships_info = {
            "total_count": len(self.rig.relationships),
            "by_type": {},
            "detailed_relationships": []
        }
        
        for relationship in self.rig.relationships:
            # Count by type
            rel_type = relationship.relationship_type
            relationships_info["by_type"][rel_type] = relationships_info["by_type"].get(rel_type, 0) + 1
            
            # Detailed relationship info
            rel_detail = {
                "source": relationship.source,
                "target": relationship.target,
                "type": relationship.relationship_type,
                "has_evidence": bool(relationship._evidence and relationship._evidence.file_path),
                "evidence_file": relationship._evidence.file_path if relationship._evidence else None
            }
            relationships_info["detailed_relationships"].append(rel_detail)
        
        return relationships_info
    
    def calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate quality metrics for the RIG."""
        metrics = {
            "evidence_coverage": 0.0,
            "component_diversity": 0.0,
            "relationship_density": 0.0,
            "language_diversity": 0.0
        }
        
        if not self.rig._components:
            return metrics
        
        # Evidence coverage
        components_with_evidence = sum(1 for c in self.rig._components if c.evidence and c.evidence.file_path)
        metrics["evidence_coverage"] = (components_with_evidence / len(self.rig._components)) * 100
        
        # Component diversity (unique types / total types)
        unique_types = len(set(c.component_type for c in self.rig._components))
        total_possible_types = 6  # executable, library, test, aggregator, runner, utility
        metrics["component_diversity"] = (unique_types / total_possible_types) * 100
        
        # Relationship density (relationships / components)
        if self.rig.relationships:
            metrics["relationship_density"] = len(self.rig.relationships) / len(self.rig._components)
        
        # Language diversity
        unique_languages = len(set(c.language for c in self.rig._components if c.language))
        metrics["language_diversity"] = unique_languages
        
        return metrics
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive RIG inspection report."""
        report = {
            "repository_info": self.inspect_repository_info(),
            "components": self.inspect_components(),
            "relationships": self.inspect_relationships(),
            "quality_metrics": self.calculate_quality_metrics(),
            "summary": {}
        }
        
        # Generate summary
        report["summary"] = {
            "total_components": report["components"].get("total_count", 0),
            "total_relationships": report["relationships"].get("total_count", 0),
            "evidence_coverage": report["quality_metrics"]["evidence_coverage"],
            "component_types": len(report["components"].get("by_type", {})),
            "languages": len(report["components"].get("by_language", {})),
            "relationship_types": len(report["relationships"].get("by_type", {}))
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted inspection report."""
        self.logger.info("=== RIG INSPECTION REPORT ===")
        
        # Repository info
        if "error" not in report["repository_info"]:
            repo = report["repository_info"]
            self.logger.info(f"Repository: {repo['name']} ({repo['type']})")
            self.logger.info(f"Primary Language: {repo['primary_language']}")
            self.logger.info(f"Build System: {repo['build_system']}")
            self.logger.info(f"Test Framework: {repo['test_framework']}")
        else:
            self.logger.error(f"Repository Error: {report['repository_info']['error']}")
        
        # Components
        if "error" not in report["components"]:
            comps = report["components"]
            self.logger.info(f"\nComponents: {comps['total_count']} total")
            self.logger.info(f"Evidence Coverage: {comps['with_evidence']}/{comps['total_count']} ({comps['with_evidence']/comps['total_count']*100:.1f}%)")
            
            self.logger.info("By Type:")
            for comp_type, count in comps["by_type"].items():
                self.logger.info(f"  {comp_type}: {count}")
            
            self.logger.info("By Language:")
            for lang, count in comps["by_language"].items():
                self.logger.info(f"  {lang}: {count}")
        else:
            self.logger.error(f"Components Error: {report['components']['error']}")
        
        # Relationships
        if "error" not in report["relationships"]:
            rels = report["relationships"]
            self.logger.info(f"\nRelationships: {rels['total_count']} total")
            
            self.logger.info("By Type:")
            for rel_type, count in rels["by_type"].items():
                self.logger.info(f"  {rel_type}: {count}")
        else:
            self.logger.error(f"Relationships Error: {report['relationships']['error']}")
        
        # Quality metrics
        metrics = report["quality_metrics"]
        self.logger.info(f"\nQuality Metrics:")
        self.logger.info(f"  Evidence Coverage: {metrics['evidence_coverage']:.1f}%")
        self.logger.info(f"  Component Diversity: {metrics['component_diversity']:.1f}%")
        self.logger.info(f"  Relationship Density: {metrics['relationship_density']:.2f}")
        self.logger.info(f"  Language Diversity: {metrics['language_diversity']} languages")
        
        # Summary
        summary = report["summary"]
        self.logger.info(f"\nSummary:")
        self.logger.info(f"  Total Components: {summary['total_components']}")
        self.logger.info(f"  Total Relationships: {summary['total_relationships']}")
        self.logger.info(f"  Evidence Coverage: {summary['evidence_coverage']:.1f}%")
        self.logger.info(f"  Component Types: {summary['component_types']}")
        self.logger.info(f"  Languages: {summary['languages']}")
        self.logger.info(f"  Relationship Types: {summary['relationship_types']}")


def load_rig_from_phase8_output(phase8_output_file: str) -> RIG:
    """Load RIG from Phase 8 output file."""
    try:
        with open(phase8_output_file, 'r') as f:
            phase8_data = json.load(f)
        
        # Extract RIG data from Phase 8 output
        rig_assembly = phase8_data.get("rig_assembly", {})
        
        # This would need to be implemented based on the actual Phase 8 output structure
        # For now, return a placeholder
        return RIG(
            repository=None,  # Would extract from rig_assembly
            components=[],    # Would extract from rig_assembly
            relationships=[]  # Would extract from rig_assembly
        )
        
    except Exception as e:
        raise Exception(f"Failed to load RIG from Phase 8 output: {e}")


def main():
    """Main inspection function."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("inspect_rig")
    
    # This would typically load from Phase 8 output
    # For demonstration, we'll create a sample RIG
    sample_rig = RIG(
        repository=None,
        components=[],
        relationships=[]
    )
    
    try:
        # Create inspector
        inspector = RIGInspector(sample_rig)
        
        # Generate comprehensive report
        report = inspector.generate_comprehensive_report()
        
        # Print report
        inspector.print_report(report)
        
        # Save report to file
        with open("rig_inspection_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("\n✅ RIG inspection completed - report saved to rig_inspection_report.json")
        
    except Exception as e:
        logger.error(f"RIG inspection failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
