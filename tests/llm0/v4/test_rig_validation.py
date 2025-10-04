#!/usr/bin/env python3
"""
RIG Validation Test - Comprehensive validation of generated RIG from Phase 8
"""

import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.rig import RIG
from core.schemas import Component, Test, Aggregator, Runner, Utility, Evidence


class RIGValidator:
    """Comprehensive RIG validation for academic paper accuracy."""
    
    def __init__(self, rig: RIG):
        self.rig = rig
        self.logger = logging.getLogger("RIGValidator")
        self.validation_results = {
            "structure_valid": True,
            "evidence_complete": True,
            "relationships_valid": True,
            "components_classified": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
    
    def validate_structure(self) -> bool:
        """Validate basic RIG structure."""
        try:
            # Check repository info
            if not self.rig.repository:
                self.validation_results["errors"].append("Missing repository information")
                self.validation_results["structure_valid"] = False
                return False
            
            # Check components exist
            if not self.rig.components:
                self.validation_results["warnings"].append("No components found in RIG")
            
            # Check relationships exist
            if not self.rig.relationships:
                self.validation_results["warnings"].append("No relationships found in RIG")
            
            self.logger.info("✅ RIG structure validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Structure validation failed: {e}")
            self.validation_results["structure_valid"] = False
            return False
    
    def validate_evidence(self) -> bool:
        """Validate evidence completeness for all components."""
        try:
            evidence_issues = []
            
            for component in self.rig.components or []:
                if not component.evidence:
                    evidence_issues.append(f"Component '{component.name}' missing evidence")
                    continue
                
                # Check evidence has required fields
                if not component.evidence.file_path:
                    evidence_issues.append(f"Component '{component.name}' evidence missing file_path")
                
                if not component.evidence.line_start or not component.evidence.line_end:
                    evidence_issues.append(f"Component '{component.name}' evidence missing line numbers")
            
            if evidence_issues:
                self.validation_results["errors"].extend(evidence_issues)
                self.validation_results["evidence_complete"] = False
                return False
            
            self.logger.info("✅ Evidence validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Evidence validation failed: {e}")
            self.validation_results["evidence_complete"] = False
            return False
    
    def validate_relationships(self) -> bool:
        """Validate relationship integrity."""
        try:
            relationship_issues = []
            component_names = {c.name for c in self.rig.components or []}
            
            for relationship in self.rig.relationships or []:
                # Check source exists
                if relationship.source not in component_names:
                    relationship_issues.append(f"Relationship source '{relationship.source}' not found in components")
                
                # Check target exists
                if relationship.target not in component_names:
                    relationship_issues.append(f"Relationship target '{relationship.target}' not found in components")
                
                # Check relationship type is valid
                valid_types = ["dependency", "test", "aggregation", "execution"]
                if relationship.relationship_type not in valid_types:
                    relationship_issues.append(f"Invalid relationship type '{relationship.relationship_type}'")
            
            if relationship_issues:
                self.validation_results["errors"].extend(relationship_issues)
                self.validation_results["relationships_valid"] = False
                return False
            
            self.logger.info("✅ Relationships validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Relationships validation failed: {e}")
            self.validation_results["relationships_valid"] = False
            return False
    
    def validate_component_classification(self) -> bool:
        """Validate component classification accuracy."""
        try:
            classification_issues = []
            valid_types = ["executable", "library", "test", "aggregator", "runner", "utility"]
            
            for component in self.rig.components or []:
                if component.component_type not in valid_types:
                    classification_issues.append(f"Component '{component.name}' has invalid type '{component.component_type}'")
                
                # Check language is reasonable
                if not component.language or component.language == "unknown":
                    classification_issues.append(f"Component '{component.name}' has unknown language")
            
            if classification_issues:
                self.validation_results["warnings"].extend(classification_issues)
                # Don't fail for classification issues, just warn
            
            self.logger.info("✅ Component classification validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Component classification validation failed: {e}")
            self.validation_results["components_classified"] = False
            return False
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive RIG statistics."""
        try:
            stats = {
                "total_components": len(self.rig.components or []),
                "total_relationships": len(self.rig.relationships or []),
                "component_types": {},
                "languages": {},
                "relationship_types": {},
                "evidence_coverage": 0.0
            }
            
            # Component type distribution
            for component in self.rig.components or []:
                comp_type = component.component_type
                stats["component_types"][comp_type] = stats["component_types"].get(comp_type, 0) + 1
                
                lang = component.language
                stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
            
            # Relationship type distribution
            for relationship in self.rig.relationships or []:
                rel_type = relationship.relationship_type
                stats["relationship_types"][rel_type] = stats["relationship_types"].get(rel_type, 0) + 1
            
            # Evidence coverage
            components_with_evidence = sum(1 for c in self.rig.components or [] if c.evidence and c.evidence.file_path)
            total_components = len(self.rig.components or [])
            stats["evidence_coverage"] = (components_with_evidence / total_components * 100) if total_components > 0 else 0.0
            
            self.validation_results["statistics"] = stats
            return stats
            
        except Exception as e:
            self.validation_results["errors"].append(f"Statistics calculation failed: {e}")
            return {}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        # Run all validations
        self.validate_structure()
        self.validate_evidence()
        self.validate_relationships()
        self.validate_component_classification()
        self.calculate_statistics()
        
        # Calculate overall score
        total_checks = 4
        passed_checks = sum([
            self.validation_results["structure_valid"],
            self.validation_results["evidence_complete"],
            self.validation_results["relationships_valid"],
            self.validation_results["components_classified"]
        ])
        
        overall_score = (passed_checks / total_checks) * 100
        
        report = {
            "overall_score": overall_score,
            "validation_results": self.validation_results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if not self.validation_results["structure_valid"]:
            recommendations.append("Fix RIG structure issues - ensure repository info and components are present")
        
        if not self.validation_results["evidence_complete"]:
            recommendations.append("Improve evidence collection - ensure all components have file paths and line numbers")
        
        if not self.validation_results["relationships_valid"]:
            recommendations.append("Fix relationship integrity - ensure all relationship sources and targets exist")
        
        if self.validation_results["statistics"].get("evidence_coverage", 0) < 80:
            recommendations.append("Improve evidence coverage - aim for 80%+ components with evidence")
        
        if not recommendations:
            recommendations.append("RIG validation passed - ready for academic paper")
        
        return recommendations


async def test_rig_validation():
    """Test RIG validation with a sample RIG."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_rig_validation")
    
    # This would typically load a RIG from Phase 8 output
    # For now, we'll create a sample RIG for testing
    sample_rig = RIG(
        repository=None,  # Would be populated from Phase 8
        components=[],       # Would be populated from Phase 8
        relationships=[]  # Would be populated from Phase 8
    )
    
    try:
        # Create validator
        validator = RIGValidator(sample_rig)
        
        # Generate validation report
        report = validator.generate_report()
        
        # Print results
        logger.info("=== RIG VALIDATION REPORT ===")
        logger.info(f"Overall Score: {report['overall_score']:.1f}%")
        logger.info(f"Structure Valid: {validator.validation_results['structure_valid']}")
        logger.info(f"Evidence Complete: {validator.validation_results['evidence_complete']}")
        logger.info(f"Relationships Valid: {validator.validation_results['relationships_valid']}")
        logger.info(f"Components Classified: {validator.validation_results['components_classified']}")
        
        if validator.validation_results['errors']:
            logger.error("Errors:")
            for error in validator.validation_results['errors']:
                logger.error(f"  - {error}")
        
        if validator.validation_results['warnings']:
            logger.warning("Warnings:")
            for warning in validator.validation_results['warnings']:
                logger.warning(f"  - {warning}")
        
        logger.info("Recommendations:")
        for rec in report['recommendations']:
            logger.info(f"  - {rec}")
        
        return report['overall_score'] >= 80.0
        
    except Exception as e:
        logger.error(f"RIG validation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_rig_validation())
    if success:
        print("[OK] RIG validation passed")
    else:
        print("[ERROR] RIG validation failed")
        sys.exit(1)
