"""
Claude SDK evaluation system for RIG effectiveness.
Runs experiments with and without RIG context to measure improvement.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import anthropic
except ImportError:
    print("Warning: anthropic package not found. Install with: pip install anthropic")
    anthropic = None


class RIGEvaluator:
    """Evaluate RIG effectiveness using Claude SDK."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.project_root = project_root
        self.results: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Claude client
        if anthropic is None:
            raise ImportError("anthropic package is required for evaluation")
        
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key is None:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def evaluate_all_repositories(self) -> None:
        """Evaluate RIG effectiveness for all test repositories."""
        print("🚀 Starting RIG evaluation for all test repositories...\n")
        
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
            print(f"🧪 Evaluating {repo_name}...")
            print(f"{'='*60}")
            
            try:
                result = await self.evaluate_repository(repo_name)
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
        
        # Save results
        self.save_results()
    
    async def evaluate_repository(self, repo_name: str) -> Dict[str, Any]:
        """Evaluate RIG effectiveness for a single repository."""
        repo_path = self.project_root / "tests" / "test_repos" / repo_name
        
        # Load evaluation questions
        questions_file = repo_path / "evaluation_questions.json"
        if not questions_file.exists():
            raise FileNotFoundError(f"Evaluation questions not found: {questions_file}")
        
        with open(questions_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        
        # Load ground truth RIG
        ground_truth_file = repo_path / "ground_truth.json"
        if not ground_truth_file.exists():
            raise FileNotFoundError(f"Ground truth not found: {ground_truth_file}")
        
        with open(ground_truth_file, "r", encoding="utf-8") as f:
            ground_truth_rig = f.read()
        
        # Run experiments
        without_rig_results = await self._run_experiment_without_rig(repo_name, questions_data["questions"])
        with_rig_results = await self._run_experiment_with_rig(repo_name, questions_data["questions"], ground_truth_rig)
        
        # Calculate scores
        without_rig_score = self._calculate_score(without_rig_results, questions_data["questions"])
        with_rig_score = self._calculate_score(with_rig_results, questions_data["questions"])
        
        # Calculate improvement
        improvement_absolute = with_rig_score - without_rig_score
        improvement_percentage = (improvement_absolute / without_rig_score * 100) if without_rig_score > 0 else 0
        
        # Save detailed results
        results_dir = self.project_root / "results" / "deterministic" / repo_name
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save without RIG results
        without_rig_file = results_dir / f"{repo_name}_without_rig.json"
        with open(without_rig_file, "w", encoding="utf-8") as f:
            json.dump(without_rig_results, f, indent=2, default=str)
        
        # Save with RIG results
        with_rig_file = results_dir / f"{repo_name}_with_rig.json"
        with open(with_rig_file, "w", encoding="utf-8") as f:
            json.dump(with_rig_results, f, indent=2, default=str)
        
        return {
            "success": True,
            "without_rig_score": without_rig_score,
            "with_rig_score": with_rig_score,
            "improvement_absolute": improvement_absolute,
            "improvement_percentage": improvement_percentage,
            "total_questions": len(questions_data["questions"]),
            "without_rig_file": str(without_rig_file.relative_to(self.project_root)),
            "with_rig_file": str(with_rig_file.relative_to(self.project_root))
        }
    
    async def _run_experiment_without_rig(self, repo_name: str, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run experiment without RIG context."""
        print(f"  📝 Running experiment WITHOUT RIG for {repo_name}...")
        
        results = []
        for question in questions:
            try:
                # Create prompt without RIG
                prompt = self._create_prompt_without_rig(repo_name, question)
                
                # Call Claude
                response = await self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                answer = response.content[0].text.strip()
                
                results.append({
                    "question_id": question["id"],
                    "question": question["question"],
                    "expected_answer": question["expected_answer"],
                    "actual_answer": answer,
                    "correct": self._is_answer_correct(answer, question["expected_answer"])
                })
                
            except Exception as e:
                print(f"    ❌ Error with question {question['id']}: {e}")
                results.append({
                    "question_id": question["id"],
                    "question": question["question"],
                    "expected_answer": question["expected_answer"],
                    "actual_answer": f"ERROR: {e}",
                    "correct": False
                })
        
        return results
    
    async def _run_experiment_with_rig(self, repo_name: str, questions: List[Dict[str, Any]], ground_truth_rig: str) -> List[Dict[str, Any]]:
        """Run experiment with RIG context."""
        print(f"  📝 Running experiment WITH RIG for {repo_name}...")
        
        results = []
        for question in questions:
            try:
                # Create prompt with RIG
                prompt = self._create_prompt_with_rig(repo_name, question, ground_truth_rig)
                
                # Call Claude
                response = await self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                answer = response.content[0].text.strip()
                
                results.append({
                    "question_id": question["id"],
                    "question": question["question"],
                    "expected_answer": question["expected_answer"],
                    "actual_answer": answer,
                    "correct": self._is_answer_correct(answer, question["expected_answer"])
                })
                
            except Exception as e:
                print(f"    ❌ Error with question {question['id']}: {e}")
                results.append({
                    "question_id": question["id"],
                    "question": question["question"],
                    "expected_answer": question["expected_answer"],
                    "actual_answer": f"ERROR: {e}",
                    "correct": False
                })
        
        return results
    
    def _create_prompt_without_rig(self, repo_name: str, question: Dict[str, Any]) -> str:
        """Create prompt without RIG context."""
        return f"""You are analyzing the {repo_name} repository. Please answer the following question based on your understanding of the repository structure and code.

Question: {question['question']}

Please provide a concise, accurate answer. If you're not sure, say "I don't know" rather than guessing."""
    
    def _create_prompt_with_rig(self, repo_name: str, question: Dict[str, Any], ground_truth_rig: str) -> str:
        """Create prompt with RIG context."""
        return f"""You are analyzing the {repo_name} repository. Below is the Repository Intelligence Graph (RIG) that provides a structured representation of the repository's components, dependencies, and build system.

RIG Data:
{ground_truth_rig}

Based on this RIG data, please answer the following question:

Question: {question['question']}

Please provide a concise, accurate answer based on the RIG information. If the RIG doesn't contain the necessary information, say "I don't know" rather than guessing."""
    
    def _is_answer_correct(self, actual_answer: str, expected_answer: str) -> bool:
        """Check if the actual answer matches the expected answer."""
        # Simple string matching for now - could be enhanced with fuzzy matching
        actual_lower = actual_answer.lower().strip()
        expected_lower = expected_answer.lower().strip()
        
        # Check for exact match
        if actual_lower == expected_lower:
            return True
        
        # Check if expected answer is contained in actual answer
        if expected_lower in actual_lower:
            return True
        
        # Check if actual answer is contained in expected answer (for partial matches)
        if actual_lower in expected_lower:
            return True
        
        return False
    
    def _calculate_score(self, results: List[Dict[str, Any]], questions: List[Dict[str, Any]]) -> float:
        """Calculate accuracy score from results."""
        if not results:
            return 0.0
        
        correct_count = sum(1 for result in results if result["correct"])
        total_count = len(results)
        
        return (correct_count / total_count) * 100
    
    def generate_summary(self) -> None:
        """Generate overall evaluation summary."""
        print("📊 RIG EVALUATION SUMMARY")
        print("="*60)
        
        total_repos = len(self.results)
        successful_repos = sum(1 for result in self.results.values() if result['success'])
        failed_repos = total_repos - successful_repos
        
        print(f"Total Repositories: {total_repos}")
        print(f"✅ Successful: {successful_repos}")
        print(f"❌ Failed: {failed_repos}")
        
        if successful_repos > 0:
            avg_improvement = sum(result['improvement_percentage'] for result in self.results.values() if result['success']) / successful_repos
            print(f"Average Improvement: {avg_improvement:.1f}%")
            
            print("\n📋 Detailed Results:")
            for repo_name, result in self.results.items():
                if result['success']:
                    print(f"  ✅ {repo_name}:")
                    print(f"      Without RIG: {result['without_rig_score']:.1f}%")
                    print(f"      With RIG: {result['with_rig_score']:.1f}%")
                    print(f"      Improvement: {result['improvement_percentage']:.1f}%")
                else:
                    print(f"  ❌ {repo_name}: {result['error']}")
    
    def save_results(self) -> None:
        """Save evaluation results to JSON file."""
        output_file = self.project_root / "rig_evaluation_results.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")


async def main():
    """Main function."""
    try:
        evaluator = RIGEvaluator()
        await evaluator.evaluate_all_repositories()
        
        # Check if all repositories were evaluated successfully
        failed_repos = [name for name, result in evaluator.results.items() if not result['success']]
        
        if failed_repos:
            print(f"\n⚠️  Some repositories failed: {', '.join(failed_repos)}")
            return 1
        else:
            print(f"\n🎉 All RIG evaluations completed successfully!")
            return 0
            
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
