from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from cmake_entrypoint import CMakeEntrypoint
from rig import RIG
from schemas import ComponentType


# =========================
# Models
# =========================

class FactLabel(str, Enum):
    CORRECT = "correct"
    INCORRECT_OFF_RIG_UNBUILT = "incorrect.off_rig_unbuilt"
    INCORRECT_MISMATCH = "incorrect.mismatch"
    HALLUCINATED = "hallucinated"


@dataclass
class FoundFact:
    claim: str
    label: FactLabel
    raw: Any


@dataclass
class PerQuestionScore:
    question_id: str
    found_facts: List[FoundFact]
    num_correct: int
    num_incorrect_off_rig_unbuilt: int
    num_incorrect_mismatch: int
    num_hallucinated: int
    expected_fact_count: int
    score: float
    normalized_score: float  # 0..10
    percentage: float        # 0..100

    @property
    def num_incorrect(self) -> int:
        return self.num_incorrect_off_rig_unbuilt + self.num_incorrect_mismatch

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "found_facts": [
                {"claim": f.claim, "label": f.label.value, "raw": f.raw}
                for f in self.found_facts
            ],
            "correct": self.num_correct,
            "incorrect": self.num_incorrect,
            "hallucinated": self.num_hallucinated,
            "score": self.score,
            "normalized_score": self.normalized_score,
            "percentage": self.percentage,
            "expected_count": self.expected_fact_count,
            "breakdown": {
                "incorrect_off_rig_unbuilt": self.num_incorrect_off_rig_unbuilt,
                "incorrect_mismatch": self.num_incorrect_mismatch,
            },
        }


@dataclass
class ScoreTotals:
    correct: int
    incorrect_off_rig_unbuilt: int
    incorrect_mismatch: int
    hallucinated: int
    expected_fact_count: int
    score: float
    normalized_score: float  # 0..10
    percentage: float        # 0..100
    accuracy: float          # 0..100

    @property
    def incorrect(self) -> int:
        return self.incorrect_off_rig_unbuilt + self.incorrect_mismatch

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correct": self.correct,
            "incorrect_off_rig_unbuilt": self.incorrect_off_rig_unbuilt,
            "incorrect_mismatch": self.incorrect_mismatch,
            "hallucinated": self.hallucinated,
            "expected_fact_count": self.expected_fact_count,
            "score": self.score,
            "normalized_score": self.normalized_score,
            "percentage": self.percentage,
            "accuracy": self.accuracy,
        }


@dataclass
class Scores:
    per_question: Dict[str, PerQuestionScore]
    totals: ScoreTotals
    skipped_questions: List[str]

    def __str__(self) -> str:
        """Return a formatted report of the scoring results."""
        lines = []
        lines.append("=" * 80)
        lines.append("SCORING RESULTS REPORT")
        lines.append("=" * 80)
        
        # Summary section
        lines.append(f"\nSUMMARY:")
        lines.append(f"  Overall Performance: {self.totals.percentage:.1f}%")
        lines.append(f"  Normalized Score (0-10): {self.totals.normalized_score:.2f}")
        lines.append(f"  Raw Score: {self.totals.score:.2f}")
        
        # Detailed counts
        lines.append(f"\nDETAILED COUNTS:")
        lines.append(f"  Correct: {self.totals.correct}")
        lines.append(f"  Incorrect (off RIG/unbuilt): {self.totals.incorrect_off_rig_unbuilt}")
        lines.append(f"  Incorrect (mismatch): {self.totals.incorrect_mismatch}")
        lines.append(f"  Hallucinated: {self.totals.hallucinated}")
        lines.append(f"  Expected Count: {self.totals.expected_fact_count}")
        lines.append(f"  Accuracy: {self.totals.accuracy:.1f}%")
        
        # Questions included/skipped
        lines.append(f"\nQUESTIONS:")
        included_questions = [qid for qid in self.per_question.keys()]
        lines.append(f"  Included: {', '.join(included_questions)}")
        lines.append(f"  Skipped: {', '.join(self.skipped_questions)}")
        
        # Per-question breakdown
        lines.append(f"\nPER-QUESTION BREAKDOWN:")
        for qid, result in self.per_question.items():
            lines.append(f"\n  {qid}:")
            lines.append(f"    Score: {result.score:.2f} (normalized: {result.normalized_score:.2f}, {result.percentage:.1f}%)")
            lines.append(f"    Correct: {result.num_correct}")
            lines.append(f"    Incorrect: {result.num_incorrect} (off RIG: {result.num_incorrect_off_rig_unbuilt}, mismatch: {result.num_incorrect_mismatch})")
            lines.append(f"    Hallucinated: {result.num_hallucinated}")
            lines.append(f"    Expected: {result.expected_fact_count}")
            
            # Show sample facts
            if result.found_facts:
                lines.append(f"    Sample Facts:")
                for i, fact in enumerate(result.found_facts[:3]):  # Show first 3 facts
                    lines.append(f"      {i+1}. {fact.claim} -> {fact.label.value}")
                if len(result.found_facts) > 3:
                    lines.append(f"      ... and {len(result.found_facts) - 3} more facts")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


# =========================
# Score Comparison
# =========================

def _get_expected_facts_from_rig(rig: RIG, qid: str) -> List[str]:
    """Get expected facts from RIG for a specific question."""
    try:
        # Create a temporary ScoreCalculator to get expected facts
        temp_calc = ScoreCalculator(rig)
        # Get the evaluator for this question
        evaluator = temp_calc._evaluators.get(qid)
        if not evaluator:
            return []
        
        # Create a dummy response to get expected facts
        dummy_response = {"items": []}
        expected_facts = []
        
        # This is a simplified approach - in practice, we'd need to extract
        # the expected facts from the RIG based on the question type
        if qid == "Q01":  # Project components (top-level aggregators)
            # Q01 asks for top-level components/aggregators, not individual build targets
            # Extract from RIG aggregators - these are the main project structure components
            expected_facts = [agg.name for agg in rig.aggregators if agg.name]
        elif qid == "Q02":  # Executables
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "executable"]
        elif qid == "Q03":  # Executables (same as Q02)
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "executable"]
        elif qid == "Q04":  # Libraries
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "library"]
        elif qid == "Q05":  # Compilers
            expected_facts = [c.name for c in rig.components if c.name and "compiler" in c.name.lower()]
        elif qid == "Q06":  # All components
            expected_facts = [c.name for c in rig.components if c.name]
        elif qid == "Q07":  # Libraries (same as Q04)
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "library"]
        elif qid == "Q08":  # Main executable
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "executable" and "main" in c.name.lower()]
        elif qid == "Q09":  # Tests
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "test"]
        elif qid == "Q10":  # Tests (same as Q09)
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "test"]
        elif qid == "Q11":  # Main executable (same as Q08)
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "executable" and "main" in c.name.lower()]
        elif qid == "Q12":  # Bridge dependencies
            expected_facts = [c.name for c in rig.components if c.name and "bridge" in c.name.lower()]
        elif qid == "Q13":  # Python tests
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "test" and "python" in c.name.lower()]
        elif qid == "Q14":  # Go tests
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "test" and "go" in c.name.lower()]
        elif qid == "Q15":  # External packages
            expected_facts = [ext_pkg.package_manager.package_name for ext_pkg in rig.external_packages if ext_pkg.package_manager and ext_pkg.package_manager.package_name]
        elif qid == "Q16":  # CLI and CDTS externals
            expected_facts = [c.name for c in rig.components if c.name and ("cli" in c.name.lower() or "cdts" in c.name.lower())]
        elif qid == "Q17":  # Main executable (same as Q08, Q11)
            expected_facts = [c.name for c in rig.components if c.name and c.runtime == "executable" and "main" in c.name.lower()]
        elif qid == "Q18":  # VM example
            expected_facts = [c.name for c in rig.components if c.name and "vm" in c.name.lower()]
        elif qid == "Q19":  # VM example (same as Q18)
            expected_facts = [c.name for c in rig.components if c.name and "vm" in c.name.lower()]
        elif qid == "Q20":  # Runtime artifacts
            expected_facts = [f"{c.name}@{c.output_path}" for c in rig.components if c.name and c.output_path]
        
        return expected_facts[:10]  # Limit to first 10 for display
    except Exception:
        return []

def score_comparer(without_rig: Scores, with_rig: Scores, rig: RIG) -> None:
    """
    Compare two Scores objects and print a detailed comparison report with final verdict.
    
    Args:
        without_rig: Scores object for WITHOUT RIG
        with_rig: Scores object for WITH RIG
        rig: RIG object to determine expected facts
    """
    print("=" * 100)
    print("SCORE COMPARISON REPORT")
    print("=" * 100)
    
    # Header with names
    print(f"\nCOMPARING:")
    print(f"  WITHOUT RIG vs WITH RIG")
    
    # Overall performance comparison
    print(f"\nOVERALL PERFORMANCE COMPARISON:")
    print(f"  {'Metric':<30} {'WITHOUT RIG':<20} {'WITH RIG':<20} {'Difference':<15}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*15}")
    
    # Key metrics
    metrics = [
        ("Percentage", f"{without_rig.totals.percentage:.1f}%", f"{with_rig.totals.percentage:.1f}%", 
         f"{with_rig.totals.percentage - without_rig.totals.percentage:+.1f}%"),
        ("Normalized Score (0-10)", f"{without_rig.totals.normalized_score:.2f}", f"{with_rig.totals.normalized_score:.2f}", 
         f"{with_rig.totals.normalized_score - without_rig.totals.normalized_score:+.2f}"),
        ("Raw Score", f"{without_rig.totals.score:.2f}", f"{with_rig.totals.score:.2f}", 
         f"{with_rig.totals.score - without_rig.totals.score:+.2f}"),
    ]
    
    for metric, val1, val2, diff in metrics:
        print(f"  {metric:<30} {val1:<20} {val2:<20} {diff:<15}")
    
    # Detailed counts comparison
    print(f"\nDETAILED COUNTS COMPARISON:")
    print(f"  {'Count Type':<30} {'WITHOUT RIG':<20} {'WITH RIG':<20} {'Difference':<15}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*15}")
    
    count_metrics = [
        ("Correct", without_rig.totals.correct, with_rig.totals.correct),
        ("Incorrect (off RIG/unbuilt)", without_rig.totals.incorrect_off_rig_unbuilt, with_rig.totals.incorrect_off_rig_unbuilt),
        ("Incorrect (mismatch)", without_rig.totals.incorrect_mismatch, with_rig.totals.incorrect_mismatch),
        ("Hallucinated", without_rig.totals.hallucinated, with_rig.totals.hallucinated),
        ("Expected Count", without_rig.totals.expected_fact_count, with_rig.totals.expected_fact_count),
    ]
    
    for count_type, val1, val2 in count_metrics:
        diff = val2 - val1
        print(f"  {count_type:<30} {val1:<20} {val2:<20} {diff:+d}")
    
    # Accuracy comparison
    accuracy1 = without_rig.totals.accuracy
    accuracy2 = with_rig.totals.accuracy
    accuracy_diff = accuracy2 - accuracy1
    
    print(f"  {'Accuracy':<30} {accuracy1:.1f}%{'':<15} {accuracy2:.1f}%{'':<15} {accuracy_diff:+.1f}%")
    
    # Per-question comparison
    print(f"\nPER-QUESTION COMPARISON:")
    print(f"  {'Question':<10} {'Metric':<20} {'WITHOUT RIG':<15} {'WITH RIG':<15} {'Expected from RIG':<20} {'Difference':<15}")
    print(f"  {'-'*10} {'-'*20} {'-'*15} {'-'*15} {'-'*20} {'-'*15}")
    
    # Get all questions from both scores
    all_questions = set(without_rig.per_question.keys()) | set(with_rig.per_question.keys())
    
    for qid in sorted(all_questions):
        q1 = without_rig.per_question.get(qid)
        q2 = with_rig.per_question.get(qid)
        
        # Skip if question not in both scores
        if not q1 or not q2:
            continue
        
        # Percentage comparison
        pct1 = q1.percentage
        pct2 = q2.percentage
        expected_pct = 100.0  # Perfect score would be 100%
        q_pct_diff = pct2 - pct1
        print(f"  {qid:<10} {'Percentage':<20} {pct1:.1f}%{'':<9} {pct2:.1f}%{'':<9} {expected_pct:.1f}%{'':<15} {q_pct_diff:+.1f}%")
        
        # Correct count comparison
        corr1 = q1.num_correct
        corr2 = q2.num_correct
        expected_corr = q1.expected_fact_count  # Same for both q1 and q2
        corr_diff = corr2 - corr1
        print(f"  {qid:<10} {'Correct':<20} {corr1:<15} {corr2:<15} {expected_corr:<20} {corr_diff:+d}")
        
        # Incorrect count comparison
        inc1 = q1.num_incorrect
        inc2 = q2.num_incorrect
        expected_inc = 0  # Perfect score would have 0 incorrect
        inc_diff = inc2 - inc1
        print(f"  {qid:<10} {'Incorrect':<20} {inc1:<15} {inc2:<15} {expected_inc:<20} {inc_diff:+d}")
        
        # Hallucinated count comparison
        hall1 = q1.num_hallucinated
        hall2 = q2.num_hallucinated
        expected_hall = 0  # Perfect score would have 0 hallucinations
        hall_diff = hall2 - hall1
        print(f"  {qid:<10} {'Hallucinated':<20} {hall1:<15} {hall2:<15} {expected_hall:<20} {hall_diff:+d}")
    
    # Impact analysis
    print(f"\nIMPACT ANALYSIS:")
    
    # Overall impact
    pct_diff = with_rig.totals.percentage - without_rig.totals.percentage
    if pct_diff > 0:
        print(f"  ✓ WITH RIG outperforms WITHOUT RIG by {pct_diff:.1f} percentage points")
    elif pct_diff < 0:
        print(f"  ✗ WITHOUT RIG outperforms WITH RIG by {abs(pct_diff):.1f} percentage points")
    else:
        print(f"  = WITHOUT RIG and WITH RIG have identical overall performance")
    
    # Accuracy impact
    if accuracy_diff > 0:
        print(f"  ✓ WITH RIG has {accuracy_diff:.1f}% higher accuracy than WITHOUT RIG")
    elif accuracy_diff < 0:
        print(f"  ✗ WITH RIG has {abs(accuracy_diff):.1f}% lower accuracy than WITHOUT RIG")
    else:
        print(f"  = WITHOUT RIG and WITH RIG have identical accuracy")
    
    # Correct facts impact
    corr_diff = with_rig.totals.correct - without_rig.totals.correct
    if corr_diff > 0:
        print(f"  ✓ WITH RIG has {corr_diff} more correct facts than WITHOUT RIG")
    elif corr_diff < 0:
        print(f"  ✗ WITH RIG has {abs(corr_diff)} fewer correct facts than WITHOUT RIG")
    else:
        print(f"  = WITHOUT RIG and WITH RIG have the same number of correct facts")
    
    # Hallucination impact
    hall_diff = with_rig.totals.hallucinated - without_rig.totals.hallucinated
    if hall_diff < 0:
        print(f"  ✓ WITH RIG has {abs(hall_diff)} fewer hallucinations than WITHOUT RIG")
    elif hall_diff > 0:
        print(f"  ✗ WITH RIG has {hall_diff} more hallucinations than WITHOUT RIG")
    else:
        print(f"  = WITHOUT RIG and WITH RIG have the same number of hallucinations")
    
    # Best performing questions
    print(f"\nBEST PERFORMING QUESTIONS:")
    question_improvements = []
    for qid in sorted(all_questions):
        q1 = without_rig.per_question.get(qid)
        q2 = with_rig.per_question.get(qid)
        if q1 and q2:
            q_pct_diff = q2.percentage - q1.percentage
            question_improvements.append((qid, q_pct_diff))
    
    # Sort by improvement (descending)
    question_improvements.sort(key=lambda x: x[1], reverse=True)
    
    for qid, improvement in question_improvements[:3]:  # Top 3 improvements
        if improvement > 0:
            print(f"  ✓ {qid}: WITH RIG +{improvement:.1f}% vs WITHOUT RIG")
        elif improvement < 0:
            print(f"  ✗ {qid}: WITHOUT RIG +{abs(improvement):.1f}% vs WITH RIG")
        else:
            print(f"  = {qid}: WITHOUT RIG and WITH RIG tied")
    
    # Final verdict - determine winner dynamically
    print(f"\nFINAL VERDICT:")
    print("=" * 50)
    
    # Determine which approach is better based on percentage
    if pct_diff > 5:
        winner = "WITH RIG"
        loser = "WITHOUT RIG"
        strength = "SIGNIFICANTLY BETTER"
        emoji = "🏆"
        recommendation = f"Use {winner} for superior results"
    elif pct_diff > 1:
        winner = "WITH RIG"
        loser = "WITHOUT RIG"
        strength = "MODERATELY BETTER"
        emoji = "👍"
        recommendation = f"{winner} is preferred, but both are viable"
    elif pct_diff > -1:
        winner = "TIE"
        loser = ""
        strength = "SIMILARLY"
        emoji = "🤝"
        recommendation = "Either approach is acceptable"
    elif pct_diff > -5:
        winner = "WITHOUT RIG"
        loser = "WITH RIG"
        strength = "MODERATELY BETTER"
        emoji = "👎"
        recommendation = f"{winner} is preferred, but both are viable"
    else:
        winner = "WITHOUT RIG"
        loser = "WITH RIG"
        strength = "SIGNIFICANTLY BETTER"
        emoji = "🚫"
        recommendation = f"Use {winner} for superior results"
    
    if winner == "TIE":
        print(f"{emoji} TIE: WITHOUT RIG and WITH RIG")
        print(f"   Both approaches perform {strength}")
        print(f"   Performance difference: {pct_diff:+.1f} percentage points")
        print(f"   Recommendation: {recommendation}")
    else:
        print(f"{emoji} WINNER: {winner}")
        print(f"   {winner} is {strength} than {loser}")
        print(f"   Performance difference: {abs(pct_diff):.1f} percentage points")
        print(f"   Recommendation: {recommendation}")
    
    # Additional insights
    print(f"\nKEY INSIGHTS:")
    if accuracy_diff != 0:
        print(f"   • Accuracy difference: {accuracy_diff:+.1f}% (WITH RIG vs WITHOUT RIG)")
    if corr_diff != 0:
        print(f"   • Correct facts difference: {corr_diff:+d} (WITH RIG vs WITHOUT RIG)")
    if hall_diff != 0:
        print(f"   • Hallucination difference: {hall_diff:+d} (WITH RIG vs WITHOUT RIG)")
    
    # Best question for each approach
    if question_improvements:
        best_improvement = question_improvements[0]
        if best_improvement[1] > 0:
            print(f"   • WITH RIG excels most at: {best_improvement[0]} (+{best_improvement[1]:.1f}%)")
        elif best_improvement[1] < 0:
            print(f"   • WITHOUT RIG excels most at: {best_improvement[0]} ({best_improvement[1]:.1f}%)")
    
    # Detailed incorrect facts and hallucinations
    print(f"\nDETAILED INCORRECT FACTS AND HALLUCINATIONS:")
    print("=" * 80)
    
    for qid in sorted(all_questions):
        q1 = without_rig.per_question.get(qid)
        q2 = with_rig.per_question.get(qid)
        
        if not q1 or not q2:
            continue
        
        # Get facts from both scores
        facts1 = q1.found_facts
        facts2 = q2.found_facts
        
        # Count incorrect and hallucinated facts
        incorrect1 = [f for f in facts1 if f.label in [FactLabel.INCORRECT_OFF_RIG_UNBUILT, FactLabel.INCORRECT_MISMATCH]]
        hallucinated1 = [f for f in facts1 if f.label == FactLabel.HALLUCINATED]
        incorrect2 = [f for f in facts2 if f.label in [FactLabel.INCORRECT_OFF_RIG_UNBUILT, FactLabel.INCORRECT_MISMATCH]]
        hallucinated2 = [f for f in facts2 if f.label == FactLabel.HALLUCINATED]
        
        if incorrect1 or hallucinated1 or incorrect2 or hallucinated2:
            print(f"\n{qid}:")
            
            if incorrect1:
                print(f"  WITHOUT RIG Incorrect Facts ({len(incorrect1)}):")
                for i, fact in enumerate(incorrect1[:5], 1):  # Show first 5
                    print(f"    {i}. {fact.claim} -> {fact.label.value}")
                if len(incorrect1) > 5:
                    print(f"    ... and {len(incorrect1) - 5} more incorrect facts")
            
            if hallucinated1:
                print(f"  WITHOUT RIG Hallucinated Facts ({len(hallucinated1)}):")
                for i, fact in enumerate(hallucinated1[:5], 1):  # Show first 5
                    print(f"    {i}. {fact.claim} -> {fact.label.value}")
                if len(hallucinated1) > 5:
                    print(f"    ... and {len(hallucinated1) - 5} more hallucinated facts")
            
            if incorrect2:
                print(f"  WITH RIG Incorrect Facts ({len(incorrect2)}):")
                for i, fact in enumerate(incorrect2[:5], 1):  # Show first 5
                    print(f"    {i}. {fact.claim} -> {fact.label.value}")
                if len(incorrect2) > 5:
                    print(f"    ... and {len(incorrect2) - 5} more incorrect facts")
            
            if hallucinated2:
                print(f"  WITH RIG Hallucinated Facts ({len(hallucinated2)}):")
                for i, fact in enumerate(hallucinated2[:5], 1):  # Show first 5
                    print(f"    {i}. {fact.claim} -> {fact.label.value}")
                if len(hallucinated2) > 5:
                    print(f"    ... and {len(hallucinated2) - 5} more hallucinated facts")
    
    # Missing facts analysis - what WITH RIG needs to reach perfect score
    print(f"\nMISSING FACTS ANALYSIS - What WITH RIG needs for perfect score:")
    print("=" * 80)
    
    for qid in sorted(all_questions):
        q1 = without_rig.per_question.get(qid)
        q2 = with_rig.per_question.get(qid)
        
        if not q1 or not q2:
            continue
        
        # Calculate what's missing for perfect score
        expected_correct = q2.expected_fact_count
        actual_correct = q2.num_correct
        missing_correct = max(0, expected_correct - actual_correct)
        
        if missing_correct > 0 or q2.num_incorrect > 0 or q2.num_hallucinated > 0:
            print(f"\n{qid}:")
            print(f"\tExpected: {expected_correct} correct, 0 incorrect, 0 hallucinated")
            print(f"\tActual in \"WITH RIG\": {actual_correct} correct, {q2.num_incorrect} incorrect, {q2.num_hallucinated} hallucinated")
            
            # Get expected facts from RIG for this question
            expected_facts = _get_expected_facts_from_rig(rig, qid)
            print(f"\tList of expected in RIG:")
            if expected_facts:
                for i, fact in enumerate(expected_facts, 1):
                    print(f"\t\t{i}. {fact}")
            else:
                print(f"\t\t(No expected facts found in RIG for this question)")
            
            # Get detected facts in WITH RIG
            q2_correct_facts = [f for f in q2.found_facts if f.label == FactLabel.CORRECT]
            detected_facts = [f.claim for f in q2_correct_facts]
            print(f"\tList of detected in \"WITH RIG\":")
            if detected_facts:
                for i, fact in enumerate(detected_facts, 1):
                    print(f"\t\t{i}. {fact}")
            else:
                print(f"\t\t(No correct facts detected)")
            
            # Calculate missing items
            expected_set = set(expected_facts)
            detected_set = set(detected_facts)
            missing_items = expected_set - detected_set
            
            print(f"\tList of missing items in \"WITH RIG\":")
            if missing_items:
                for i, item in enumerate(sorted(missing_items), 1):
                    print(f"\t\t{i}. {item}")
            else:
                print(f"\t\t(No missing items - perfect score!)")
            
            # Show incorrect and hallucinated facts if any
            if q2.num_incorrect > 0:
                incorrect_facts = [f for f in q2.found_facts if f.label in [FactLabel.INCORRECT_OFF_RIG_UNBUILT, FactLabel.INCORRECT_MISMATCH]]
                print(f"\tIncorrect facts in \"WITH RIG\" ({len(incorrect_facts)}):")
                for i, fact in enumerate(incorrect_facts, 1):
                    print(f"\t\t{i}. {fact.claim} -> {fact.label.value}")
            
            if q2.num_hallucinated > 0:
                hallucinated_facts = [f for f in q2.found_facts if f.label == FactLabel.HALLUCINATED]
                print(f"\tHallucinated facts in \"WITH RIG\" ({len(hallucinated_facts)}):")
                for i, fact in enumerate(hallucinated_facts, 1):
                    print(f"\t\t{i}. {fact.claim} -> {fact.label.value}")
    
    print("\n" + "=" * 100)


# =========================
# Engine
# =========================

class ScoreCalculator:
    """
    Object-oriented scorer for MetaFFI Q-spec answers.

    Scoring formula (per question):
      score = (num_correct * w_correct)
            + (num_incorrect_off_rig_unbuilt * w_incorrect_off)
            + (num_incorrect_mismatch * w_incorrect_mis)
            + (num_hallucinated * w_hallucinated)

      normalized_score (0..10) = 10 * max(0, score) / max(1, expected_fact_count)
      percentage (0..100)      = 100 * max(0, score) / max(1, expected_fact_count)
    """

    # default weights
    DEFAULT_W_CORRECT = 1.0
    DEFAULT_W_INCORRECT_OFF = -0.5   # repo exists but not built / not in RIG (e.g., lang-plugin-c)
    DEFAULT_W_INCORRECT_MIS = -1.0   # built entity but wrong attribute
    DEFAULT_W_HALLUCINATED = -2.0    # fully made-up

    def __init__(
        self,
        rig: RIG,
        weight_correct: float = DEFAULT_W_CORRECT,
        weight_incorrect_off: float = DEFAULT_W_INCORRECT_OFF,
        weight_incorrect_mis: float = DEFAULT_W_INCORRECT_MIS,
        weight_hallucinated: float = DEFAULT_W_HALLUCINATED,
        honeypots: Optional[Set[str]] = None,
    ) -> None:
        self.rig = rig
        self.weight_correct = weight_correct
        self.weight_incorrect_off = weight_incorrect_off
        self.weight_incorrect_mis = weight_incorrect_mis
        self.weight_hallucinated = weight_hallucinated
        self.honeypots = {h.lower() for h in (honeypots or {"lang-plugin-c"})}

        # bind evaluators
        self._evaluators: Dict[str, Callable[[Dict[str, Any]], PerQuestionScore]] = {
            "Q01": self._eval_q01,
            "Q02": self._eval_q02,
            "Q03": self._eval_q03,
            "Q04": self._eval_q04,
            "Q05": self._eval_q05,
            "Q06": self._eval_q06,
            "Q07": self._eval_q07,
            "Q08": self._eval_q08,
            "Q09": self._eval_q09,
            "Q10": self._eval_q10,
            "Q11": self._eval_q11,
            "Q12": self._eval_q12,
            "Q13": self._eval_q13,
            "Q14": self._eval_q14,
            "Q15": self._eval_q15,
            "Q16": self._eval_q16,
            "Q17": self._eval_q17,
            "Q18": self._eval_q18,
            "Q19": self._eval_q19,
            "Q20": self._eval_q20,
        }

        # precomputed helpers
        self._component_name_set: Set[str] = {self._norm_text(c.name) for c in self.rig.components}
        self._artifact_to_component = self._build_artifact_index()

    # ---------- public API ----------

    def calculate(self, llm_json: str) -> Scores:
        try:
            llm_obj = json.loads(llm_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid LLM JSON: {e}")

        per_question: Dict[str, PerQuestionScore] = {}
        skipped_questions: List[str] = []

        # Initialize totals
        correct = 0
        incorrect_off_rig_unbuilt = 0
        incorrect_mismatch = 0
        hallucinated = 0
        score = 0.0
        expected_fact_count = 0

        for qid, evaluator in self._evaluators.items():
            result = evaluator(llm_obj)
            per_question[qid] = result

            correct += result.num_correct
            incorrect_off_rig_unbuilt += result.num_incorrect_off_rig_unbuilt
            incorrect_mismatch += result.num_incorrect_mismatch
            hallucinated += result.num_hallucinated
            score += result.score
            expected_fact_count += result.expected_fact_count

        # mark remaining core questions as skipped (non-penalizing)
        core_qids = [f"Q{n:02d}" for n in range(1, 21)]
        for qid in core_qids:
            if qid not in self._evaluators:
                skipped_questions.append(qid)

        # Calculate derived values
        denom = max(1, expected_fact_count)
        clamped = max(0.0, score)
        normalized_score = 10.0 * clamped / denom
        percentage = 100.0 * clamped / denom
        
        # Calculate accuracy
        total_facts = correct + incorrect_off_rig_unbuilt + incorrect_mismatch + hallucinated
        accuracy = correct / max(1, total_facts) * 100

        totals = ScoreTotals(
            correct=correct,
            incorrect_off_rig_unbuilt=incorrect_off_rig_unbuilt,
            incorrect_mismatch=incorrect_mismatch,
            hallucinated=hallucinated,
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized_score,
            percentage=percentage,
            accuracy=accuracy
        )

        return Scores(per_question=per_question, totals=totals, skipped_questions=skipped_questions)

    # ---------- evaluators (one per question) ----------

    def _eval_q01(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q01: Project components (aggregators)."""
        expected_keys: Set[str] = set()
        for agg in self.rig.aggregators:
            expected_keys.add(self._norm_text(agg.name))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q01", {}) or {}).get("components", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            name = self._norm_text(item.get("name", ""))
            
            if name in expected_keys:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(name):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=name, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q01",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q02(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q02: Core C runtime (XLLR) shared libraries."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if c.type == ComponentType.SHARED_LIBRARY and "xllr" in c.name.lower():
                expected_keys.add(self._norm_text(c.name))
                if c.output_path:
                    expected_keys.add(self._basename(str(c.output_path)))

        expected_fact_count = len(expected_keys)

        items = (llm.get("Q02", {}) or {}).get("runtimes", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q02")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q02",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q03(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q03: CLI executables."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if c.type == ComponentType.EXECUTABLE:
                expected_keys.add(self._norm_text(c.name))
                if c.output_path:
                    expected_keys.add(self._basename(str(c.output_path)))

        expected_fact_count = len(expected_keys)

        items = (llm.get("Q03", {}) or {}).get("executables", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q03")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q03",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q06(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q06: All native targets (executables/shared libraries)."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if c.type in (ComponentType.EXECUTABLE, ComponentType.SHARED_LIBRARY):
                expected_keys.add(self._norm_text(c.name))
                if c.output_path:
                    expected_keys.add(self._basename(str(c.output_path)))

        expected_fact_count = len(expected_keys)

        items = (llm.get("Q06", {}) or {}).get("native", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q06")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q06",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q07(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q07: VM/JAR artifacts."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            out = str(c.output_path) if c.output_path else ""
            if c.type == ComponentType.VM or out.lower().endswith(".jar"):
                expected_keys.add(self._norm_text(c.name))
                if out:
                    expected_keys.add(self._basename(out))

        expected_fact_count = len(expected_keys)

        items = (llm.get("Q07", {}) or {}).get("vm_artifacts", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q07")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q07",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q12(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """
        Q12: xllr.openjdk.jni.bridge depends on xllr.openjdk + its artifact matches.
        We treat this as 1 expected fact.
        """
        expected_fact_count = 1
        entry = (llm.get("Q12", {}) or {}).get("openjdk_jni_bridge", {}) or {}

        bridge = next((c for c in self.rig.components if c.name.lower() == "xllr.openjdk.jni.bridge"), None)
        dep_ok = False
        artifact_ok = False

        # LLM claim
        artifact_from_llm = entry.get("artifact", "") if isinstance(entry, dict) else ""
        artifact_basename = self._basename(artifact_from_llm)

        if bridge:
            dep_ok = any(d.name.lower() == "xllr.openjdk" for d in bridge.depends_on)
            artifact_ok = bool(artifact_basename) and self._basename(str(bridge.output_path)) == artifact_basename

        found_facts: List[FoundFact] = []
        counts = self._empty_counts()

        if bridge and dep_ok and artifact_ok:
            counts["num_correct"] += 1
            label = FactLabel.CORRECT
        else:
            claim_key = "xllr.openjdk.jni.bridge"
            if self._is_honeypot(claim_key):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            elif bridge:  # Component exists but dependency or artifact is wrong
                counts["num_incorrect_mismatch"] += 1
                label = FactLabel.INCORRECT_MISMATCH
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED

        found_facts.append(FoundFact(
            claim="Q12:xllr.openjdk.jni.bridge depends_on xllr.openjdk; artifact matches",
            label=label,
            raw=entry
        ))

        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q12",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q20(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q20: Produced runtime artifacts (dll/exe/jar) and their output directories."""
        expected_artifacts: Set[str] = set()
        for c in self.rig.components:
            out = str(c.output_path) if c.output_path else ""
            if out.lower().endswith((".dll", ".exe", ".jar")):
                expected_artifacts.add(self._basename(out))

        expected_fact_count = len(expected_artifacts)

        items = (llm.get("Q20", {}) or {}).get("runtime_artifacts", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()

        for it in items:
            if not isinstance(it, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=it))
                counts["num_hallucinated"] += 1
                continue

            artifact = self._basename(it.get("artifact", ""))
            output_dir = it.get("output_dir", "")

            if artifact in expected_artifacts:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(artifact) or self._is_honeypot(output_dir):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED

            found_facts.append(FoundFact(claim=f"{artifact}@{output_dir}", label=label, raw=it))

        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)

        return PerQuestionScore(
            question_id="Q20",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q04(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q04: IDL plugins."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if "idl" in c.name.lower() and c.type == ComponentType.SHARED_LIBRARY:
                expected_keys.add(self._norm_text(c.name))
                if c.output_path:
                    expected_keys.add(self._basename(str(c.output_path)))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q04", {}) or {}).get("idl_plugins", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q04")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q04",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q05(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q05: Go compilers (all compilers in the system)."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if "compiler" in c.name.lower():
                expected_keys.add(self._norm_text(c.name))
                if c.output_path:
                    expected_keys.add(self._basename(str(c.output_path)))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q05", {}) or {}).get("go_compilers", []) or []
        found_facts, counts = self._classify_items_by_target_and_artifact(items, expected_keys, "Q05")
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q05",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q08(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q08: Dependency chain."""
        # This is a complex question about dependency ordering - simplified evaluation
        expected_fact_count = 1  # We expect at least one dependency chain
        
        chain = (llm.get("Q08", {}) or {}).get("dependency_chain", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        if chain and len(chain) > 1:
            # Check if the chain contains known components
            chain_names = {self._norm_text(name) for name in chain}
            known_components = {self._norm_text(c.name) for c in self.rig.components}
            known_aggregators = {self._norm_text(a.name) for a in self.rig.aggregators}
            known_all = known_components | known_aggregators
            
            if any(name in known_all for name in chain_names):
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
        else:
            counts["num_hallucinated"] += 1
            label = FactLabel.HALLUCINATED
        
        found_facts.append(FoundFact(
            claim="Q08:dependency_chain",
            label=label,
            raw=chain
        ))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q08",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q09(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q09: Tests."""
        expected_keys: Set[str] = set()
        for test in self.rig.tests:
            expected_keys.add(self._norm_text(test.name))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q09", {}) or {}).get("tests", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            name = self._norm_text(item.get("name", ""))
            
            if name in expected_keys:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(name):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=name, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q09",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q10(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q10: Test to components mapping."""
        expected_fact_count = len(self.rig.tests)  # One mapping per test
        
        items = (llm.get("Q10", {}) or {}).get("test_to_components", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            test_name = self._norm_text(item.get("test", ""))
            targets = item.get("targets", [])
            
            # Check if test exists and has correct component mappings
            test_exists = any(self._norm_text(t.name) == test_name for t in self.rig.tests)
            if test_exists and targets:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(test_name):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=test_name, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q10",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q11(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q11: Go API test dependencies."""
        expected_fact_count = 1  # One specific test analysis
        
        test_data = (llm.get("Q11", {}) or {}).get("go_api_test", {}) or {}
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        if test_data and isinstance(test_data, dict):
            dependencies = test_data.get("dependencies", [])
            externals = test_data.get("externals", [])
            
            # Check if go_api_test exists and has reasonable dependencies
            test_exists = any("go_api_test" in t.name.lower() for t in self.rig.tests)
            if test_exists and (dependencies or externals):
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
        else:
            counts["num_hallucinated"] += 1
            label = FactLabel.HALLUCINATED
        
        found_facts.append(FoundFact(
            claim="Q11:go_api_test dependencies",
            label=label,
            raw=test_data
        ))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q11",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q13(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q13: Python tests."""
        expected_keys: Set[str] = set()
        for test in self.rig.tests:
            if "python" in test.name.lower():
                expected_keys.add(self._norm_text(test.name))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q13", {}) or {}).get("python_tests", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            test_name = self._norm_text(item.get("name", ""))
            depends_on = item.get("depends_on", [])
            
            # Check if python test exists
            if test_name in expected_keys and depends_on:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(test_name):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=test_name, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q13",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q14(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q14: Runtime source roots."""
        expected_fact_count = len([c for c in self.rig.components if "xllr" in c.name.lower()])
        
        items = (llm.get("Q14", {}) or {}).get("runtime_source_roots", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            target = self._norm_text(item.get("target", ""))
            dirs = item.get("dirs", [])
            
            # Check if xllr target exists and has reasonable source directories
            target_exists = any("xllr" in c.name.lower() and target in c.name.lower() for c in self.rig.components)
            if target_exists and dirs:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(target):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=target, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q14",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q15(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q15: XLLR external links."""
        expected_fact_count = len([c for c in self.rig.components if "xllr" in c.name.lower() and c.external_packages])
        
        items = (llm.get("Q15", {}) or {}).get("xllr_external_links", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            lib = self._norm_text(item.get("lib", ""))
            declared_in = item.get("declared_in", [])
            
            # Check if external library is mentioned in xllr components
            xllr_components = [c for c in self.rig.components if "xllr" in c.name.lower()]
            lib_found = any(lib in self._norm_text(str(ext_pkg.package_manager.package_name)) for c in xllr_components for ext_pkg in c.external_packages)
            
            if lib_found and declared_in:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(lib):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=lib, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q15",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q16(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q16: CLI and CDTS externals."""
        expected_keys: Set[str] = set()
        for c in self.rig.components:
            if c.name.lower() in ["metaffi", "cdts_test"] and c.external_packages:
                expected_keys.add(self._norm_text(c.name))
        
        expected_fact_count = len(expected_keys)
        
        items = (llm.get("Q16", {}) or {}).get("cli_and_cdts_externals", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        for item in items:
            if not isinstance(item, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=item))
                counts["num_hallucinated"] += 1
                continue
            
            target = self._norm_text(item.get("target", ""))
            libs = item.get("libs", [])
            declared_in = item.get("declared_in", [])
            
            # Check if target exists and has external packages
            if target in expected_keys and libs and declared_in:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(target):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
            
            found_facts.append(FoundFact(claim=target, label=label, raw=item))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q16",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q17(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q17: Commands."""
        expected_fact_count = 1  # We expect at least one command type
        
        commands = (llm.get("Q17", {}) or {}).get("commands", {}) or {}
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        if commands and isinstance(commands, dict):
            configure = commands.get("configure", [])
            test = commands.get("test", [])
            
            if configure or test:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
        else:
            counts["num_hallucinated"] += 1
            label = FactLabel.HALLUCINATED
        
        found_facts.append(FoundFact(
            claim="Q17:commands",
            label=label,
            raw=commands
        ))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q17",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q18(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q18: CDTS test call stack."""
        expected_fact_count = 1  # One specific test call stack
        
        call_stack = (llm.get("Q18", {}) or {}).get("cdts_test_call_stack", []) or []
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        if call_stack:
            counts["num_correct"] += 1
            label = FactLabel.CORRECT
        else:
            counts["num_hallucinated"] += 1
            label = FactLabel.HALLUCINATED
        
        found_facts.append(FoundFact(
            claim="Q18:cdts_test_call_stack",
            label=label,
            raw=call_stack
        ))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q18",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    def _eval_q19(self, llm: Dict[str, Any]) -> PerQuestionScore:
        """Q19: VM example."""
        expected_fact_count = 1  # One VM example
        
        vm_example = (llm.get("Q19", {}) or {}).get("vm_example", {}) or {}
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()
        
        if vm_example and isinstance(vm_example, dict):
            target = self._norm_text(vm_example.get("target", ""))
            artifact = self._norm_text(vm_example.get("artifact", ""))
            output_dir = self._norm_text(vm_example.get("output_dir", ""))
            
            # Check if VM target exists (JAR files)
            vm_exists = any(c.type == ComponentType.VM or (c.output_path and ".jar" in str(c.output_path).lower()) for c in self.rig.components)
            if vm_exists and target and artifact and output_dir:
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif self._is_honeypot(target):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED
        else:
            counts["num_hallucinated"] += 1
            label = FactLabel.HALLUCINATED
        
        found_facts.append(FoundFact(
            claim="Q19:vm_example",
            label=label,
            raw=vm_example
        ))
        
        score, normalized, percent = self._score_from_counts(counts, expected_fact_count)
        
        return PerQuestionScore(
            question_id="Q19",
            found_facts=found_facts,
            num_correct=counts["num_correct"],
            num_incorrect_off_rig_unbuilt=counts["num_incorrect_off_rig_unbuilt"],
            num_incorrect_mismatch=counts["num_incorrect_mismatch"],
            num_hallucinated=counts["num_hallucinated"],
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized,
            percentage=percent,
        )

    # ---------- shared helpers ----------

    def _classify_items_by_target_and_artifact(
        self,
        items: List[Any],
        expected_keys: Set[str],
        qid: str,
    ) -> Tuple[List[FoundFact], Dict[str, int]]:
        """
        Classify a list of dict items that expose ("target", "artifact") fields.
        """
        found_facts: List[FoundFact] = []
        counts = self._empty_counts()

        for it in items:
            if not isinstance(it, dict):
                found_facts.append(FoundFact(claim="<invalid-item>", label=FactLabel.HALLUCINATED, raw=it))
                counts["num_hallucinated"] += 1
                continue

            target = self._norm_text(it.get("target", ""))
            artifact = self._basename(it.get("artifact", ""))
            keys = {k for k in (target, artifact) if k}

            if any(k in expected_keys for k in keys):
                counts["num_correct"] += 1
                label = FactLabel.CORRECT
            elif any(self._is_honeypot(k) for k in keys):
                counts["num_incorrect_off_rig_unbuilt"] += 1
                label = FactLabel.INCORRECT_OFF_RIG_UNBUILT
            elif (keys & self._component_name_set) or any(k in self._artifact_to_component for k in keys):
                counts["num_incorrect_mismatch"] += 1
                label = FactLabel.INCORRECT_MISMATCH
            else:
                counts["num_hallucinated"] += 1
                label = FactLabel.HALLUCINATED

            found_facts.append(FoundFact(claim=target or artifact, label=label, raw=it))

        return found_facts, counts

    def _score_from_counts(self, counts: Dict[str, int], expected_fact_count: int) -> Tuple[float, float, float]:
        raw_score = (
            counts["num_correct"] * self.weight_correct
            + counts["num_incorrect_off_rig_unbuilt"] * self.weight_incorrect_off
            + counts["num_incorrect_mismatch"] * self.weight_incorrect_mis
            + counts["num_hallucinated"] * self.weight_hallucinated
        )
        clamped = max(0.0, raw_score)
        denom = max(1, expected_fact_count)
        normalized = 10.0 * clamped / denom
        percent = 100.0 * clamped / denom
        return clamped, normalized, percent

    def _empty_counts(self) -> Dict[str, int]:
        return {
            "num_correct": 0,
            "num_incorrect_off_rig_unbuilt": 0,
            "num_incorrect_mismatch": 0,
            "num_hallucinated": 0,
        }

    def _norm_text(self, s: str) -> str:
        return s.replace("\\", "/").strip().lower()

    def _basename(self, p: str) -> str:
        return Path(p).name.lower()

    def _is_honeypot(self, name_or_path: str) -> bool:
        s = self._norm_text(name_or_path)
        return any(hp in s for hp in self.honeypots)

    def _build_artifact_index(self) -> Dict[str, Any]:
        """
        Map artifact basenames -> component (or truthy sentinel) to quickly
        recognize 'known' artifacts for mismatch classification.
        """
        idx: Dict[str, Any] = {}
        for c in self.rig.components:
            if c.output_path:
                idx[self._basename(str(c.output_path))] = c
        return idx


if __name__ == "__main__":
    
    # Original functionality
    metaffi_config_dir = Path("C:/src/github.com/MetaFFI/cmake-build-debug")
    entrypoint = CMakeEntrypoint(metaffi_config_dir)
    rig = entrypoint.rig
    
    
    with open('results_cursor_without_rig.json', "r", encoding="utf-8") as f:
        results_cursor_without_rig = f.read()
        
    with open('results_cursor_with_rig.json', "r", encoding="utf-8") as f:
        results_cursor_with_rig = f.read()
    
    score_results_cursor_without_rig = ScoreCalculator(rig=rig).calculate(results_cursor_without_rig)
    score_results_cursor_with_rig = ScoreCalculator(rig=rig).calculate(results_cursor_with_rig)
    
    print('=======================================')
    
    score_comparer(score_results_cursor_without_rig, score_results_cursor_with_rig, rig)
        
        
        