"""
Deterministic RIG Scorer - Compare RIG effectiveness in helping LLMs understand repositories.
Extends the evaluation system to provide detailed scoring and comparison reports.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DeterministicRIGScorer:
    """Score and compare RIG effectiveness for deterministic evaluation."""
    
    def __init__(self):
        self.project_root = project_root
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def score_all_repositories(self) -> None:
        """Score RIG effectiveness for all test repositories."""
        print("📊 Scoring RIG effectiveness for all test repositories...\n")
        
        # Define all test repositories
        repositories = [
            "cmake_hello_world",
            "jni_hello_world", 
            "maven_multimodule",
            "npm_monorepo",
            "cargo_workspace",
            "go_modules",
            "meson_cpp"
        ]
        
        for repo_name in repositories:
            print(f"{'='*60}")
            print(f"📈 Scoring {repo_name}...")
            print(f"{'='*60}")
            
            try:
                result = self.score_repository(repo_name)
                self.results[repo_name] = result
                
                if result['success']:
                    improvement = result['improvement_percentage']
                    print(f"✅ {repo_name}: {improvement:.1f}% improvement with RIG")
                else:
                    print(f"❌ {repo_name}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ {repo_name} failed: {e}")
                import traceback
                traceback.print_exc()
                self.results[repo_name] = {
                    "success": False,
                    "error": str(e)
                }
            
            print()
        
        # Generate summary
        self.generate_summary()
        
        # Generate comparison reports
        self.generate_comparison_reports()
        
        # Save results
        self.save_results()
    
    def score_repository(self, repo_name: str) -> Dict[str, Any]:
        """Score RIG effectiveness for a single repository."""
        results_dir = self.project_root / "results" / "deterministic" / repo_name
        
        # Load without RIG results
        without_rig_file = results_dir / f"{repo_name}_without_rig.json"
        if not without_rig_file.exists():
            raise FileNotFoundError(f"Without RIG results not found: {without_rig_file}")
        
        with open(without_rig_file, "r", encoding="utf-8") as f:
            without_rig_results = json.load(f)
        
        # Load with RIG results
        with_rig_file = results_dir / f"{repo_name}_with_rig.json"
        if not with_rig_file.exists():
            raise FileNotFoundError(f"With RIG results not found: {with_rig_file}")
        
        with open(with_rig_file, "r", encoding="utf-8") as f:
            with_rig_results = json.load(f)
        
        # Load evaluation questions for context
        questions_file = self.project_root / "tests" / "test_repos" / repo_name / "evaluation_questions.json"
        with open(questions_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        
        # Calculate detailed scores
        without_rig_score = self._calculate_detailed_score(without_rig_results, questions_data["questions"])
        with_rig_score = self._calculate_detailed_score(with_rig_results, questions_data["questions"])
        
        # Calculate improvement
        improvement_absolute = with_rig_score['overall_accuracy'] - without_rig_score['overall_accuracy']
        improvement_percentage = (improvement_absolute / without_rig_score['overall_accuracy'] * 100) if without_rig_score['overall_accuracy'] > 0 else 0
        
        # Analyze question-by-question improvements
        question_analysis = self._analyze_question_improvements(without_rig_results, with_rig_results, questions_data["questions"])
        
        return {
            "success": True,
            "repository_name": repo_name,
            "build_system": questions_data["build_system"],
            "total_questions": len(questions_data["questions"]),
            "without_rig_score": without_rig_score,
            "with_rig_score": with_rig_score,
            "improvement_absolute": improvement_absolute,
            "improvement_percentage": improvement_percentage,
            "question_analysis": question_analysis
        }
    
    def _calculate_detailed_score(self, results: List[Dict[str, Any]], questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed scoring metrics."""
        if not results:
            return {
                "overall_accuracy": 0.0,
                "correct_count": 0,
                "total_count": 0,
                "category_scores": {},
                "difficulty_scores": {}
            }
        
        # Overall accuracy
        correct_count = sum(1 for result in results if result["correct"])
        total_count = len(results)
        overall_accuracy = (correct_count / total_count) * 100
        
        # Category scores
        category_scores = {}
        difficulty_scores = {}
        
        # Group questions by category and difficulty
        question_map = {q["id"]: q for q in questions}
        
        for result in results:
            question_id = result["question_id"]
            if question_id in question_map:
                question = question_map[question_id]
                category = question.get("category", "unknown")
                difficulty = question.get("difficulty", "unknown")
                
                # Initialize category/difficulty if not exists
                if category not in category_scores:
                    category_scores[category] = {"correct": 0, "total": 0}
                if difficulty not in difficulty_scores:
                    difficulty_scores[difficulty] = {"correct": 0, "total": 0}
                
                # Count results
                category_scores[category]["total"] += 1
                difficulty_scores[difficulty]["total"] += 1
                
                if result["correct"]:
                    category_scores[category]["correct"] += 1
                    difficulty_scores[difficulty]["correct"] += 1
        
        # Calculate percentages
        for category in category_scores:
            total = category_scores[category]["total"]
            correct = category_scores[category]["correct"]
            category_scores[category]["accuracy"] = (correct / total * 100) if total > 0 else 0
        
        for difficulty in difficulty_scores:
            total = difficulty_scores[difficulty]["total"]
            correct = difficulty_scores[difficulty]["correct"]
            difficulty_scores[difficulty]["accuracy"] = (correct / total * 100) if total > 0 else 0
        
        return {
            "overall_accuracy": overall_accuracy,
            "correct_count": correct_count,
            "total_count": total_count,
            "category_scores": category_scores,
            "difficulty_scores": difficulty_scores
        }
    
    def _analyze_question_improvements(self, without_rig_results: List[Dict[str, Any]], with_rig_results: List[Dict[str, Any]], questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze question-by-question improvements."""
        question_map = {q["id"]: q for q in questions}
        analysis = []
        
        for i, (without_result, with_result) in enumerate(zip(without_rig_results, with_rig_results)):
            question_id = without_result["question_id"]
            question = question_map.get(question_id, {})
            
            improvement = with_result["correct"] - without_result["correct"]
            
            analysis.append({
                "question_id": question_id,
                "question": question.get("question", ""),
                "category": question.get("category", "unknown"),
                "difficulty": question.get("difficulty", "unknown"),
                "expected_answer": question.get("expected_answer", ""),
                "without_rig_correct": without_result["correct"],
                "with_rig_correct": with_result["correct"],
                "improvement": improvement,
                "without_rig_answer": without_result["actual_answer"],
                "with_rig_answer": with_result["actual_answer"]
            })
        
        return analysis
    
    def generate_summary(self) -> None:
        """Generate overall scoring summary."""
        print("📊 RIG EFFECTIVENESS SCORING SUMMARY")
        print("="*60)
        
        total_repos = len(self.results)
        successful_repos = sum(1 for result in self.results.values() if result['success'])
        failed_repos = total_repos - successful_repos
        
        print(f"Total Repositories: {total_repos}")
        print(f"✅ Successful: {successful_repos}")
        print(f"❌ Failed: {failed_repos}")
        
        if successful_repos > 0:
            avg_improvement = sum(result['improvement_percentage'] for result in self.results.values() if result['success']) / successful_repos
            avg_without_rig = sum(result['without_rig_score']['overall_accuracy'] for result in self.results.values() if result['success']) / successful_repos
            avg_with_rig = sum(result['with_rig_score']['overall_accuracy'] for result in self.results.values() if result['success']) / successful_repos
            
            print(f"\n📈 Overall Statistics:")
            print(f"  Average Without RIG: {avg_without_rig:.1f}%")
            print(f"  Average With RIG: {avg_with_rig:.1f}%")
            print(f"  Average Improvement: {avg_improvement:.1f}%")
            
            print("\n📋 Detailed Results:")
            for repo_name, result in self.results.items():
                if result['success']:
                    print(f"  ✅ {repo_name} ({result['build_system']}):")
                    print(f"      Without RIG: {result['without_rig_score']['overall_accuracy']:.1f}%")
                    print(f"      With RIG: {result['with_rig_score']['overall_accuracy']:.1f}%")
                    print(f"      Improvement: {result['improvement_percentage']:.1f}%")
                else:
                    print(f"  ❌ {repo_name}: {result['error']}")
    
    def generate_comparison_reports(self) -> None:
        """Generate detailed comparison reports for each repository."""
        print("\n📝 Generating comparison reports...")
        
        for repo_name, result in self.results.items():
            if not result['success']:
                continue
            
            self._generate_repository_report(repo_name, result)
    
    def _generate_repository_report(self, repo_name: str, result: Dict[str, Any]) -> None:
        """Generate detailed comparison report for a single repository."""
        results_dir = self.project_root / "results" / "deterministic" / repo_name
        report_file = results_dir / "comparison_results.md"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# RIG Effectiveness Report: {repo_name}\n\n")
            f.write(f"**Build System:** {result['build_system']}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Without RIG:** {result['without_rig_score']['overall_accuracy']:.1f}% accuracy\n")
            f.write(f"- **With RIG:** {result['with_rig_score']['overall_accuracy']:.1f}% accuracy\n")
            f.write(f"- **Improvement:** {result['improvement_percentage']:.1f}% ({result['improvement_absolute']:.1f} percentage points)\n\n")
            
            # Category breakdown
            f.write("## Category Breakdown\n\n")
            f.write("| Category | Without RIG | With RIG | Improvement |\n")
            f.write("|----------|-------------|----------|-------------|\n")
            
            categories = set()
            for score in [result['without_rig_score'], result['with_rig_score']]:
                categories.update(score['category_scores'].keys())
            
            for category in sorted(categories):
                without_acc = result['without_rig_score']['category_scores'].get(category, {}).get('accuracy', 0)
                with_acc = result['with_rig_score']['category_scores'].get(category, {}).get('accuracy', 0)
                improvement = with_acc - without_acc
                f.write(f"| {category} | {without_acc:.1f}% | {with_acc:.1f}% | {improvement:+.1f}% |\n")
            
            f.write("\n")
            
            # Difficulty breakdown
            f.write("## Difficulty Breakdown\n\n")
            f.write("| Difficulty | Without RIG | With RIG | Improvement |\n")
            f.write("|------------|-------------|----------|-------------|\n")
            
            difficulties = set()
            for score in [result['without_rig_score'], result['with_rig_score']]:
                difficulties.update(score['difficulty_scores'].keys())
            
            for difficulty in sorted(difficulties):
                without_acc = result['without_rig_score']['difficulty_scores'].get(difficulty, {}).get('accuracy', 0)
                with_acc = result['with_rig_score']['difficulty_scores'].get(difficulty, {}).get('accuracy', 0)
                improvement = with_acc - without_acc
                f.write(f"| {difficulty} | {without_acc:.1f}% | {with_acc:.1f}% | {improvement:+.1f}% |\n")
            
            f.write("\n")
            
            # Question-by-question analysis
            f.write("## Question-by-Question Analysis\n\n")
            f.write("| Question | Category | Difficulty | Without RIG | With RIG | Improvement |\n")
            f.write("|----------|----------|------------|-------------|----------|-------------|\n")
            
            for analysis in result['question_analysis']:
                without_correct = "✅" if analysis['without_rig_correct'] else "❌"
                with_correct = "✅" if analysis['with_rig_correct'] else "❌"
                improvement_icon = "📈" if analysis['improvement'] > 0 else "📉" if analysis['improvement'] < 0 else "➡️"
                
                f.write(f"| {analysis['question_id']} | {analysis['category']} | {analysis['difficulty']} | {without_correct} | {with_correct} | {improvement_icon} |\n")
            
            f.write("\n")
            
            # Detailed question analysis
            f.write("## Detailed Question Analysis\n\n")
            for analysis in result['question_analysis']:
                f.write(f"### {analysis['question_id']}\n\n")
                f.write(f"**Question:** {analysis['question']}\n\n")
                f.write(f"**Expected Answer:** {analysis['expected_answer']}\n\n")
                f.write(f"**Without RIG Answer:** {analysis['without_rig_answer']}\n\n")
                f.write(f"**With RIG Answer:** {analysis['with_rig_answer']}\n\n")
                f.write(f"**Result:** {'✅ Correct' if analysis['with_rig_correct'] else '❌ Incorrect'}\n\n")
                f.write("---\n\n")
        
        print(f"  📄 Report generated: {report_file.relative_to(self.project_root)}")
    
    def save_results(self) -> None:
        """Save scoring results to JSON file."""
        output_file = self.project_root / "rig_scoring_results.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main function."""
    scorer = DeterministicRIGScorer()
    scorer.score_all_repositories()
    
    # Check if all repositories were scored successfully
    failed_repos = [name for name, result in scorer.results.items() if not result['success']]
    
    if failed_repos:
        print(f"\n⚠️  Some repositories failed: {', '.join(failed_repos)}")
        return 1
    else:
        print(f"\n🎉 All RIG scoring completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
