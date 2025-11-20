#!/usr/bin/env python3
"""
Analyze all answers_analysis.json files to detect problematic questions.

This script identifies potential issues with:
- Incorrect RIG data
- Wrong expected answers
- Ambiguous question wording
- Format inconsistencies
- Difficulty miscalibration
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Import REPOS from config
sys.path.insert(0, str(Path(__file__).parent / "summary_analysis"))
from config import REPOS


class ProblematicQuestionAnalyzer:
    def __init__(self):
        self.findings = []

    def load_all_analyses(self) -> Dict[str, Dict]:
        """Load all answers_analysis.json files."""
        analyses = {}
        script_dir = Path(__file__).parent

        for repo in REPOS:
            repo_path = Path(repo['path'])
            analysis_file = repo_path / "answers_analysis.json"

            if analysis_file.exists():
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analyses[repo['name']] = json.load(f)
                print(f"[OK] Loaded analysis for: {repo['name']}")
            else:
                print(f"[SKIP] No analysis for: {repo['name']}")

        return analyses

    def extract_question_data(self, repo_name: str, question: Dict, analysis: Dict) -> Dict:
        """Extract all relevant data for a question."""
        q_id = question['id']

        # Get scores and answers for all agents
        agents_data = {
            'claude_NORIG': question.get('claude_NORIG', {}),
            'claude_RIG': question.get('claude_RIG', {}),
            'codex_NORIG': question.get('codex_NORIG', {}),
            'codex_RIG': question.get('codex_RIG', {}),
            'cursor_NORIG': question.get('cursor_NORIG', {}),
            'cursor_RIG': question.get('cursor_RIG', {}),
        }

        return {
            'repo': repo_name,
            'id': q_id,
            'question': question['question'],
            'expected': question['expected'],
            'difficulty': question['difficulty'],
            'category': question['category'],
            'agents': agents_data,
        }

    def pattern_1_rig_induced_errors(self, q_data: Dict) -> bool:
        """All WITH RIG wrong, all/most WITHOUT RIG correct."""
        agents = q_data['agents']

        rig_scores = [agents[a].get('score', -1) for a in ['claude_RIG', 'codex_RIG', 'cursor_RIG'] if a in agents]
        norig_scores = [agents[a].get('score', -1) for a in ['claude_NORIG', 'codex_NORIG', 'cursor_NORIG'] if a in agents]

        # All RIG agents wrong
        if not rig_scores or not all(s == 0 for s in rig_scores):
            return False

        # Most/all NORIG agents correct
        norig_correct = sum(1 for s in norig_scores if s == 1)
        return norig_correct >= 2  # At least 2 out of 3

    def pattern_2_universal_failure(self, q_data: Dict) -> Tuple[bool, Any]:
        """All agents wrong with same answer."""
        agents = q_data['agents']

        scores = [agents[a].get('score', -1) for a in agents if a in agents]

        # All agents wrong
        if not all(s == 0 for s in scores):
            return False, None

        # Check if they all gave similar answers
        answers = [agents[a].get('actual') for a in agents if a in agents and 'actual' in agents[a]]

        if not answers:
            return False, None

        # Simple check: if all answers are same (for simple types)
        # or all are lists with same content
        first_answer = answers[0]
        all_same = all(ans == first_answer for ans in answers)

        return all_same, first_answer if all_same else None

    def pattern_3_format_inconsistency(self, q_data: Dict) -> Tuple[bool, List[str]]:
        """Agents return different data types."""
        agents = q_data['agents']
        expected = q_data['expected']

        # Get actual answers and their types
        answers = []
        for agent_name, agent_data in agents.items():
            if 'actual' in agent_data:
                actual = agent_data['actual']
                answers.append((agent_name, type(actual).__name__, actual))

        # Check if there are different types
        types = set(t for _, t, _ in answers)

        # Also check if expected type differs from actual types
        expected_type = type(expected).__name__
        actual_types = [t for _, t, _ in answers]

        # Issue if: different types among agents, or all differ from expected
        has_inconsistency = len(types) > 1 or all(t != expected_type for t in actual_types)

        if has_inconsistency:
            type_info = [f"{name}: {typ}" for name, typ, _ in answers]
            type_info.insert(0, f"Expected: {expected_type}")
            return True, type_info

        return False, []

    def pattern_4_rig_consensus_breaking(self, q_data: Dict) -> bool:
        """WITHOUT RIG agree, WITH RIG diverge."""
        agents = q_data['agents']

        # Get NORIG answers
        norig_answers = []
        for a in ['claude_NORIG', 'codex_NORIG', 'cursor_NORIG']:
            if a in agents and 'actual' in agents[a]:
                norig_answers.append(agents[a]['actual'])

        # Get RIG answers
        rig_answers = []
        for a in ['claude_RIG', 'codex_RIG', 'cursor_RIG']:
            if a in agents and 'actual' in agents[a]:
                rig_answers.append(agents[a]['actual'])

        if len(norig_answers) < 3 or len(rig_answers) < 3:
            return False

        # NORIG all same
        norig_consensus = all(ans == norig_answers[0] for ans in norig_answers)

        # RIG have different answers
        rig_divergence = not all(ans == rig_answers[0] for ans in rig_answers)

        return norig_consensus and rig_divergence

    def pattern_5_difficulty_miscalibration(self, q_data: Dict) -> Tuple[bool, float]:
        """Easy questions with low success or hard with high success."""
        agents = q_data['agents']
        difficulty = q_data['difficulty']

        scores = [agents[a].get('score', 0) for a in agents if a in agents]
        success_rate = sum(scores) / len(scores) if scores else 0

        # Easy question with low success (< 50%)
        if difficulty == 'easy' and success_rate < 0.5:
            return True, success_rate

        # Hard question with high success (> 90%)
        if difficulty == 'hard' and success_rate > 0.9:
            return True, success_rate

        return False, success_rate

    def pattern_7_statistical_outliers(self, q_data: Dict) -> Tuple[bool, str]:
        """Unusual score distributions."""
        agents = q_data['agents']

        scores = [agents[a].get('score', 0) for a in agents if a in agents]
        correct_count = sum(scores)

        # Only 1 agent correct (out of 6)
        if correct_count == 1:
            return True, "Only 1 agent correct - question might be too specific/tricky"

        # Exactly 3 agents correct - check if it's all RIG or all NORIG
        if correct_count == 3:
            rig_correct = sum(agents[a].get('score', 0) for a in ['claude_RIG', 'codex_RIG', 'cursor_RIG'] if a in agents)
            norig_correct = sum(agents[a].get('score', 0) for a in ['claude_NORIG', 'codex_NORIG', 'cursor_NORIG'] if a in agents)

            if rig_correct == 3:
                return True, "Only RIG agents correct - systematic RIG advantage"
            if norig_correct == 3:
                return True, "Only NORIG agents correct - systematic RIG disadvantage"

        return False, ""

    def pattern_8_rig_no_benefit(self, q_data: Dict) -> bool:
        """WITH RIG and WITHOUT RIG have same scores for all agents."""
        agents = q_data['agents']

        for base in ['claude', 'codex', 'cursor']:
            rig_key = f"{base}_RIG"
            norig_key = f"{base}_NORIG"

            if rig_key not in agents or norig_key not in agents:
                return False

            rig_score = agents[rig_key].get('score', -1)
            norig_score = agents[norig_key].get('score', -1)

            if rig_score != norig_score:
                return False

        return True

    def pattern_11_partial_match(self, q_data: Dict) -> Tuple[bool, Any]:
        """Agents consistently return subset of expected answer."""
        agents = q_data['agents']
        expected = q_data['expected']

        # Only applicable for list answers
        if not isinstance(expected, list):
            return False, None

        # Get all actual answers that are lists
        actual_lists = []
        for agent_data in agents.values():
            if 'actual' in agent_data and isinstance(agent_data['actual'], list):
                actual_lists.append(agent_data['actual'])

        if len(actual_lists) < 4:  # Need at least 4 agents with list answers
            return False, None

        # Check if all actual lists have same length (but different from expected)
        actual_lengths = [len(lst) for lst in actual_lists]

        if len(set(actual_lengths)) == 1 and actual_lengths[0] != len(expected):
            # All agents returned same-length list, but different from expected
            common_length = actual_lengths[0]

            # Check if actual items are subset of expected
            is_subset = all(
                all(item in expected for item in actual_list)
                for actual_list in actual_lists
            )

            if is_subset:
                return True, f"All agents returned {common_length} items, expected has {len(expected)} items"

        return False, None

    def pattern_12_rig_sensitive(self, q_data: Dict) -> bool:
        """Only WITH RIG agents can answer correctly (good!)."""
        agents = q_data['agents']

        rig_scores = [agents[a].get('score', -1) for a in ['claude_RIG', 'codex_RIG', 'cursor_RIG'] if a in agents]
        norig_scores = [agents[a].get('score', -1) for a in ['claude_NORIG', 'codex_NORIG', 'cursor_NORIG'] if a in agents]

        # All RIG agents correct
        if not rig_scores or not all(s == 1 for s in rig_scores):
            return False

        # All NORIG agents wrong
        return norig_scores and all(s == 0 for s in norig_scores)

    def analyze_all_questions(self, analyses: Dict[str, Dict]) -> None:
        """Run all pattern detections on all questions."""

        for repo_name, analysis in analyses.items():
            questions = analysis['results']['questions']

            for question in questions:
                q_data = self.extract_question_data(repo_name, question, analysis)

                # Pattern 1: RIG-Induced Errors
                if self.pattern_1_rig_induced_errors(q_data):
                    self.findings.append({
                        'severity': 'CRITICAL',
                        'pattern': 'RIG-Induced Errors',
                        'description': 'All WITH RIG wrong, most WITHOUT RIG correct',
                        'action': 'Check RIG for incorrect/incomplete data',
                        'data': q_data
                    })

                # Pattern 2: Universal Failure
                is_universal, common_answer = self.pattern_2_universal_failure(q_data)
                if is_universal:
                    self.findings.append({
                        'severity': 'HIGH',
                        'pattern': 'Universal Failure',
                        'description': f'All agents wrong with same answer: {common_answer}',
                        'action': 'Verify expected answer is correct',
                        'data': q_data
                    })

                # Pattern 3: Format Inconsistency
                has_format_issue, type_info = self.pattern_3_format_inconsistency(q_data)
                if has_format_issue:
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'pattern': 'Format Inconsistency',
                        'description': 'Different data types returned:\n' + '\n'.join(type_info),
                        'action': 'Clarify expected format in question',
                        'data': q_data
                    })

                # Pattern 4: RIG Consensus Breaking
                if self.pattern_4_rig_consensus_breaking(q_data):
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'pattern': 'RIG Consensus Breaking',
                        'description': 'WITHOUT RIG all agree, WITH RIG diverge',
                        'action': 'Check if RIG introduces ambiguity',
                        'data': q_data
                    })

                # Pattern 5: Difficulty Miscalibration
                is_miscalibrated, success_rate = self.pattern_5_difficulty_miscalibration(q_data)
                if is_miscalibrated:
                    self.findings.append({
                        'severity': 'LOW',
                        'pattern': 'Difficulty Miscalibration',
                        'description': f'{q_data["difficulty"]} question with {success_rate*100:.1f}% success',
                        'action': 'Re-evaluate difficulty rating',
                        'data': q_data
                    })

                # Pattern 7: Statistical Outliers
                is_outlier, outlier_desc = self.pattern_7_statistical_outliers(q_data)
                if is_outlier:
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'pattern': 'Statistical Outlier',
                        'description': outlier_desc,
                        'action': 'Review question clarity/specificity',
                        'data': q_data
                    })

                # Pattern 8: RIG Provides No Benefit
                if self.pattern_8_rig_no_benefit(q_data):
                    # Only flag if all scores are the same (all correct or all wrong)
                    score = q_data['agents']['claude_RIG'].get('score', -1)
                    self.findings.append({
                        'severity': 'INFO',
                        'pattern': 'RIG No Benefit',
                        'description': f'RIG and NORIG same scores (all {score})',
                        'action': 'Check if RIG should help with this question',
                        'data': q_data
                    })

                # Pattern 11: Partial Match
                is_partial, partial_desc = self.pattern_11_partial_match(q_data)
                if is_partial:
                    self.findings.append({
                        'severity': 'HIGH',
                        'pattern': 'Partial Match',
                        'description': partial_desc,
                        'action': 'Check if expected answer or RIG is complete',
                        'data': q_data
                    })

                # Pattern 12: RIG-Sensitive (GOOD - for info only)
                if self.pattern_12_rig_sensitive(q_data):
                    self.findings.append({
                        'severity': 'GOOD',
                        'pattern': 'RIG-Sensitive Question',
                        'description': 'Only RIG agents correct - validates RIG usefulness',
                        'action': 'Document as RIG validation case',
                        'data': q_data
                    })

    def print_report(self) -> None:
        """Print findings in a readable format."""
        print("\n" + "="*80)
        print("PROBLEMATIC QUESTIONS ANALYSIS")
        print("="*80)

        # Group by severity
        by_severity = defaultdict(list)
        for finding in self.findings:
            by_severity[finding['severity']].append(finding)

        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'GOOD']

        for severity in severity_order:
            if severity not in by_severity:
                continue

            findings = by_severity[severity]
            print(f"\n{'='*80}")
            print(f"{severity} - {len(findings)} findings")
            print(f"{'='*80}")

            for i, finding in enumerate(findings, 1):
                data = finding['data']
                print(f"\n[{severity} #{i}] {finding['pattern']}")
                print(f"Repository: {data['repo']}")
                print(f"Question {data['id']}: {data['question']}")
                print(f"Category: {data['category']}, Difficulty: {data['difficulty']}")
                print(f"Expected: {data['expected']}")
                print(f"\nDescription: {finding['description']}")
                print(f"Action: {finding['action']}")

                # Show agent scores
                print("\nAgent Scores:")
                for agent_name in ['claude_NORIG', 'claude_RIG', 'codex_NORIG', 'codex_RIG', 'cursor_NORIG', 'cursor_RIG']:
                    if agent_name in data['agents']:
                        agent_data = data['agents'][agent_name]
                        score = agent_data.get('score', '?')
                        actual = agent_data.get('actual', 'N/A')
                        print(f"  {agent_name:15} | Score: {score} | Actual: {actual}")

                print("-" * 80)

        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        total = len(self.findings)
        print(f"Total findings: {total}")
        for severity in severity_order:
            count = len(by_severity[severity])
            if count > 0:
                print(f"  {severity}: {count}")


def main():
    # Fix Windows console encoding to handle Unicode characters
    import codecs
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    analyzer = ProblematicQuestionAnalyzer()

    print("="*80)
    print("Loading all answers_analysis.json files...")
    print("="*80)

    analyses = analyzer.load_all_analyses()

    if not analyses:
        print("\n[ERROR] No analysis files found. Please run answers_analysis.py first.")
        return 1

    print(f"\n[OK] Loaded {len(analyses)} repositories")
    print("\n" + "="*80)
    print("Analyzing all questions for problematic patterns...")
    print("="*80)

    analyzer.analyze_all_questions(analyses)

    analyzer.print_report()

    return 0


if __name__ == "__main__":
    sys.exit(main())
