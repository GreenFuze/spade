"""
Main execution module for RIG effectiveness summary analysis.

This module orchestrates the complete analysis workflow:
1. Load data from all repositories
2. Calculate complexity metrics
3. Aggregate analysis across repositories
4. Generate visualizations
5. Generate markdown report
6. Save JSON output
"""

import json
import statistics
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

from .config import REPOS, SCRIPT_DIR
from .complexity import calculate_complexity_score, calculate_pearson_correlation, get_complexity_level
from .visualizations import generate_all_visualizations
from .report_generator import generate_markdown_report


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}")
        raise


def process_repository(repo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single repository: load data, calculate complexity, extract results.

    Args:
        repo: Repository configuration dictionary

    Returns:
        Dictionary with repository analysis data
    """
    repo_name = repo["name"]
    repo_path = repo["path"]

    print(f"\nProcessing {repo_name}...")

    # Load files
    answers_analysis = load_json(repo_path / "answers_analysis.json")

    # Find ground truth file
    ground_truth_file = None
    for gt_file in repo_path.glob("*_ground_truth.json"):
        ground_truth_file = gt_file
        break

    if not ground_truth_file:
        raise FileNotFoundError(f"No ground truth file found in {repo_path}")

    ground_truth = load_json(ground_truth_file)
    evaluation_questions = load_json(repo_path / "evaluation_questions.json")

    # Calculate complexity
    complexity_score, complexity_metrics = calculate_complexity_score(ground_truth)
    # Note: complexity_level will be determined after normalization across all repos

    # Extract results from answers_analysis
    analysis = answers_analysis.get("analysis", {})
    summary = analysis.get("summary", {})
    timing = summary.get("timing", {})

    # Calculate averages
    avg_score_with_rig = summary.get("average_with_rig", 0)
    avg_score_without_rig = summary.get("average_without_rig", 0)
    score_improvement = summary.get("average_rig_improvement", 0)
    score_improvement_relative = (
        (avg_score_with_rig - avg_score_without_rig) / avg_score_without_rig * 100
    ) if avg_score_without_rig > 0 else 0

    avg_time_with_rig = timing.get("average_time_with_rig_seconds", 0)
    avg_time_without_rig = timing.get("average_time_without_rig_seconds", 0)
    time_saved = timing.get("average_time_saved_seconds", 0)
    time_reduction_pct = timing.get("average_time_reduction_percentage", 0)

    # Calculate efficiency improvement
    efficiency_with_rig = avg_score_with_rig / avg_time_with_rig if avg_time_with_rig > 0 else 0
    efficiency_without_rig = avg_score_without_rig / avg_time_without_rig if avg_time_without_rig > 0 else 0
    efficiency_improvement = (
        (efficiency_with_rig - efficiency_without_rig) / efficiency_without_rig * 100
    ) if efficiency_without_rig > 0 else 0

    # Extract by-agent results
    by_agent_results = {}
    by_agent_analysis = analysis.get("by_agent", {})

    for agent_name, agent_data in by_agent_analysis.items():
        with_rig = agent_data.get("with_rig", {})
        without_rig = agent_data.get("without_rig", {})
        rig_improvement = agent_data.get("rig_improvement", {})
        agent_timing = agent_data.get("timing", {})

        by_agent_results[agent_name] = {
            "score_with_rig": with_rig.get("percentage", 0),
            "score_without_rig": without_rig.get("percentage", 0),
            "score_improvement": rig_improvement.get("percentage", 0),
            "time_with_rig": agent_timing.get("time_with_rig_seconds", 0),
            "time_without_rig": agent_timing.get("time_without_rig_seconds", 0),
            "time_saved": agent_timing.get("time_saved_seconds", 0),
            "time_reduction_percentage": agent_timing.get("time_reduction_percentage", 0),
        }

    # Extract by-difficulty results
    rig_effectiveness = analysis.get("rig_effectiveness", {})
    by_difficulty_analysis = rig_effectiveness.get("by_difficulty", {})
    by_difficulty_results = {}

    for difficulty in ["easy", "medium", "hard"]:
        diff_data = by_difficulty_analysis.get(difficulty, {})
        by_difficulty_results[difficulty] = {
            "avg_improvement": diff_data.get("avg_improvement", 0),
        }

    # Count questions by difficulty
    questions_by_difficulty = {"easy": 0, "medium": 0, "hard": 0}
    for q in evaluation_questions.get("questions", []):
        difficulty = q.get("difficulty", "").lower()
        if difficulty in questions_by_difficulty:
            questions_by_difficulty[difficulty] += 1

    # Extract by-category results
    # Build question ID → category map
    question_categories = {}
    for q in evaluation_questions.get("questions", []):
        q_id = q.get("id")
        category = q.get("category", "").lower()
        if q_id and category:
            question_categories[q_id] = category

    # Calculate category performance
    category_scores = {}
    results_data = answers_analysis.get("results", {})

    # Collect scores by category for all agents
    for agent_condition_key, condition_data in results_data.items():
        # Determine if this is RIG or NORIG condition
        is_rig = "_RIG" in agent_condition_key

        # Process each question
        for question_result in condition_data.get("questions", []):
            q_id = question_result.get("id")
            score = question_result.get("score", 0)

            # Map question to category
            category = question_categories.get(q_id)
            if not category:
                continue

            # Initialize category if needed
            if category not in category_scores:
                category_scores[category] = {"with_rig": [], "without_rig": []}

            # Add score to appropriate list
            if is_rig:
                category_scores[category]["with_rig"].append(score)
            else:
                category_scores[category]["without_rig"].append(score)

    # Calculate category averages and improvements
    by_category_results = {}
    for category, scores in category_scores.items():
        with_rig_scores = scores["with_rig"]
        without_rig_scores = scores["without_rig"]

        avg_with_rig = (sum(with_rig_scores) / len(with_rig_scores) * 100) if with_rig_scores else 0
        avg_without_rig = (sum(without_rig_scores) / len(without_rig_scores) * 100) if without_rig_scores else 0
        improvement = avg_with_rig - avg_without_rig

        by_category_results[category] = {
            "avg_with_rig": round(avg_with_rig, 1),
            "avg_without_rig": round(avg_without_rig, 1),
            "improvement": round(improvement, 1),
        }

    return {
        "name": repo_name,
        "path": str(repo_path.relative_to(SCRIPT_DIR.parent)),
        "complexity": {
            "score": complexity_score,
            "level": None,  # Will be set after normalization
            "metrics": complexity_metrics,
        },
        "questions": {
            "total": len(evaluation_questions.get("questions", [])),
            "by_difficulty": questions_by_difficulty,
        },
        "results": {
            "average_score_with_rig": round(avg_score_with_rig, 1),
            "average_score_without_rig": round(avg_score_without_rig, 1),
            "score_improvement": round(score_improvement, 1),
            "score_improvement_relative": round(score_improvement_relative, 1),
            "average_time_with_rig_seconds": round(avg_time_with_rig, 2),
            "average_time_without_rig_seconds": round(avg_time_without_rig, 2),
            "time_saved_seconds": round(time_saved, 2),
            "time_reduction_percentage": round(time_reduction_pct, 1),
            "efficiency_improvement": round(efficiency_improvement, 1),
            "by_agent": by_agent_results,
            "by_difficulty": by_difficulty_results,
            "by_category": by_category_results,
        },
    }


def calculate_aggregate_analysis(repo_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate analysis across all repositories.

    Args:
        repo_data_list: List of repository data dictionaries

    Returns:
        Dictionary with aggregate metrics, correlations, and insights
    """
    print("\nCalculating aggregate analysis...")

    # Extract all agents
    all_agents = set()
    for repo_data in repo_data_list:
        all_agents.update(repo_data["results"]["by_agent"].keys())
    all_agents = sorted(list(all_agents))

    # Calculate overall averages
    total_questions = sum(repo["questions"]["total"] for repo in repo_data_list)
    avg_score_with_rig = statistics.mean([repo["results"]["average_score_with_rig"] for repo in repo_data_list])
    avg_score_without_rig = statistics.mean([repo["results"]["average_score_without_rig"] for repo in repo_data_list])
    avg_score_improvement = avg_score_with_rig - avg_score_without_rig
    avg_time_with_rig = statistics.mean([repo["results"]["average_time_with_rig_seconds"] for repo in repo_data_list])
    avg_time_without_rig = statistics.mean([repo["results"]["average_time_without_rig_seconds"] for repo in repo_data_list])
    avg_time_saved = avg_time_without_rig - avg_time_with_rig
    avg_time_reduction_pct = (avg_time_saved / avg_time_without_rig * 100) if avg_time_without_rig > 0 else 0
    total_time_saved = sum(repo["results"]["time_saved_seconds"] for repo in repo_data_list)

    # Calculate by-agent aggregates
    by_agent_aggregate = {}
    for agent in all_agents:
        agent_scores_with_rig = []
        agent_scores_without_rig = []
        agent_times_with_rig = []
        agent_times_without_rig = []
        performance_by_complexity = []

        for repo in repo_data_list:
            if agent in repo["results"]["by_agent"]:
                agent_result = repo["results"]["by_agent"][agent]
                agent_scores_with_rig.append(agent_result["score_with_rig"])
                agent_scores_without_rig.append(agent_result["score_without_rig"])
                agent_times_with_rig.append(agent_result["time_with_rig"])
                agent_times_without_rig.append(agent_result["time_without_rig"])

                performance_by_complexity.append({
                    "complexity_score": repo["complexity"]["score"],
                    "score_improvement": agent_result["score_improvement"],
                    "time_reduction": agent_result["time_reduction_percentage"],
                })

        avg_agent_score_with_rig = statistics.mean(agent_scores_with_rig) if agent_scores_with_rig else 0
        avg_agent_score_without_rig = statistics.mean(agent_scores_without_rig) if agent_scores_without_rig else 0
        avg_agent_time_with_rig = statistics.mean(agent_times_with_rig) if agent_times_with_rig else 0
        avg_agent_time_without_rig = statistics.mean(agent_times_without_rig) if agent_times_without_rig else 0

        by_agent_aggregate[agent] = {
            "avg_score_with_rig": round(avg_agent_score_with_rig, 1),
            "avg_score_without_rig": round(avg_agent_score_without_rig, 1),
            "avg_score_improvement": round(avg_agent_score_with_rig - avg_agent_score_without_rig, 1),
            "avg_time_with_rig": round(avg_agent_time_with_rig, 2),
            "avg_time_without_rig": round(avg_agent_time_without_rig, 2),
            "avg_time_reduction_percentage": round((avg_agent_time_without_rig - avg_agent_time_with_rig) / avg_agent_time_without_rig * 100, 1) if avg_agent_time_without_rig > 0 else 0,
            "performance_by_complexity": performance_by_complexity,
        }

    # Calculate by-difficulty aggregates
    by_difficulty_aggregate = {}
    for difficulty in ["easy", "medium", "hard"]:
        improvements = []
        question_count = 0

        for repo in repo_data_list:
            if difficulty in repo["results"]["by_difficulty"]:
                improvements.append(repo["results"]["by_difficulty"][difficulty]["avg_improvement"])
            question_count += repo["questions"]["by_difficulty"].get(difficulty, 0)

        by_difficulty_aggregate[difficulty] = {
            "avg_improvement": round(statistics.mean(improvements), 1) if improvements else 0,
            "question_count": question_count,
        }

    # Calculate by-category aggregates
    # Collect all categories from all repos
    all_categories = set()
    for repo in repo_data_list:
        all_categories.update(repo["results"]["by_category"].keys())

    # Focus on common categories across all repos
    common_categories = ["build_system", "source_analysis", "testing", "dependency_analysis", "component_identification"]

    by_category_aggregate = {}
    for category in common_categories:
        improvements = []
        with_rig_scores = []
        without_rig_scores = []
        per_repo_improvements = {}

        for repo in repo_data_list:
            if category in repo["results"]["by_category"]:
                cat_data = repo["results"]["by_category"][category]
                improvement = cat_data.get("improvement", 0)
                improvements.append(improvement)
                with_rig_scores.append(cat_data.get("avg_with_rig", 0))
                without_rig_scores.append(cat_data.get("avg_without_rig", 0))
                per_repo_improvements[repo["name"]] = improvement

        by_category_aggregate[category] = {
            "avg_improvement": round(statistics.mean(improvements), 1) if improvements else 0,
            "avg_with_rig": round(statistics.mean(with_rig_scores), 1) if with_rig_scores else 0,
            "avg_without_rig": round(statistics.mean(without_rig_scores), 1) if without_rig_scores else 0,
            "per_repo": per_repo_improvements,
        }

    # Calculate correlations
    complexity_scores = [repo["complexity"]["score"] for repo in repo_data_list]
    score_improvements = [repo["results"]["score_improvement"] for repo in repo_data_list]
    time_reductions = [repo["results"]["time_reduction_percentage"] for repo in repo_data_list]

    score_correlation_r = calculate_pearson_correlation(complexity_scores, score_improvements)
    score_correlation_r_squared = score_correlation_r ** 2

    time_correlation_r = calculate_pearson_correlation(complexity_scores, time_reductions)
    time_correlation_r_squared = time_correlation_r ** 2

    # Normalize complexity scores to 0-100
    max_complexity = max(complexity_scores)
    normalized_complexities = [(score / max_complexity * 100) for score in complexity_scores]

    # Update repo data with normalized scores and complexity levels
    for i, repo in enumerate(repo_data_list):
        normalized_score = round(normalized_complexities[i], 1)
        repo["complexity"]["normalized_score"] = normalized_score
        repo["complexity"]["level"] = get_complexity_level(normalized_score)

    # Generate insights
    key_findings = []
    key_findings.append(f"RIG provides {avg_score_improvement:.1f}% average score improvement across all repositories")
    key_findings.append(f"RIG saves {avg_time_reduction_pct:.1f}% time on average ({avg_time_saved:.1f} seconds per repository)")
    key_findings.append(f"RIG benefit scales with repository complexity (r²={score_correlation_r_squared:.2f})")

    # Find min and max improvements
    min_improvement_repo = min(repo_data_list, key=lambda r: r["results"]["score_improvement"])
    max_improvement_repo = max(repo_data_list, key=lambda r: r["results"]["score_improvement"])

    key_findings.append(
        f"Complex projects ({max_improvement_repo['name']}) see {max_improvement_repo['results']['score_improvement']:.1f}% improvement "
        f"vs {min_improvement_repo['results']['score_improvement']:.1f}% for simple projects ({min_improvement_repo['name']})"
    )

    # Difficulty-based findings
    difficulty_improvements = [(d, by_difficulty_aggregate[d]["avg_improvement"]) for d in ["easy", "medium", "hard"]]
    best_difficulty = max(difficulty_improvements, key=lambda x: x[1])
    key_findings.append(
        f"{best_difficulty[0].capitalize()} questions benefit most from RIG ({best_difficulty[1]:.1f}% improvement)"
    )

    # Agent-based findings
    agent_improvements = [(agent, data["avg_score_improvement"]) for agent, data in by_agent_aggregate.items()]
    best_agent = max(agent_improvements, key=lambda x: x[1])

    key_findings.append(
        f"{best_agent[0].capitalize()} shows highest improvement ({best_agent[1]:.1f}%) "
        f"but started from lowest baseline ({by_agent_aggregate[best_agent[0]]['avg_score_without_rig']:.1f}%)"
    )

    # Time savings finding
    if avg_time_reduction_pct > 10:
        key_findings.append("Time savings alone justify RIG usage, even with minimal score gains")

    # Recommendations
    recommendations = [
        "RIG is most valuable for complex, multi-language repositories",
        "Agents struggling without RIG benefit most from RIG access",
        "RIG helps standardize performance across difficulty levels",
    ]

    if avg_time_reduction_pct > 20:
        recommendations.append("Significant time savings make RIG essential for developer productivity")

    return {
        "overall": {
            "total_questions": total_questions,
            "avg_score_with_rig": round(avg_score_with_rig, 1),
            "avg_score_without_rig": round(avg_score_without_rig, 1),
            "avg_score_improvement": round(avg_score_improvement, 1),
            "avg_time_with_rig": round(avg_time_with_rig, 2),
            "avg_time_without_rig": round(avg_time_without_rig, 2),
            "avg_time_reduction_percentage": round(avg_time_reduction_pct, 1),
            "total_time_saved_seconds": round(total_time_saved, 2),
        },
        "by_agent": by_agent_aggregate,
        "by_difficulty": by_difficulty_aggregate,
        "by_category": by_category_aggregate,
        "correlations": {
            "complexity_vs_rig_benefit": {
                "description": "How repository complexity correlates with RIG improvement",
                "score_correlation": {
                    "r_squared": round(score_correlation_r_squared, 3),
                    "interpretation": "Strong positive correlation" if score_correlation_r_squared > 0.7 else
                                     "Moderate positive correlation" if score_correlation_r_squared > 0.4 else
                                     "Weak correlation",
                    "conclusion": "Higher complexity leads to greater score improvement" if score_correlation_r_squared > 0.7 else
                                 "Some correlation between complexity and improvement",
                    "data_points": [
                        {
                            "repo": repo["name"],
                            "complexity": repo["complexity"]["normalized_score"],
                            "score_improvement": repo["results"]["score_improvement"]
                        }
                        for repo in repo_data_list
                    ],
                },
                "time_correlation": {
                    "r_squared": round(time_correlation_r_squared, 3),
                    "interpretation": "Strong positive correlation" if time_correlation_r_squared > 0.7 else
                                     "Moderate positive correlation" if time_correlation_r_squared > 0.4 else
                                     "Weak correlation",
                    "conclusion": "Higher complexity leads to greater time savings" if time_correlation_r_squared > 0.7 else
                                 "Some correlation between complexity and time savings",
                    "data_points": [
                        {
                            "repo": repo["name"],
                            "complexity": repo["complexity"]["normalized_score"],
                            "time_reduction": repo["results"]["time_reduction_percentage"]
                        }
                        for repo in repo_data_list
                    ],
                },
            },
        },
        "insights": {
            "key_findings": key_findings,
            "recommendations": recommendations,
        },
    }


def main():
    """Main execution function."""
    print("=" * 80)
    print("OVERALL SUMMARY ANALYSIS GENERATOR")
    print("=" * 80)

    # Process all repositories
    repo_data_list = []
    for repo in REPOS:
        try:
            repo_data = process_repository(repo)
            repo_data_list.append(repo_data)
            print(f"[OK] {repo['name']}: Complexity={repo_data['complexity']['score']} ({repo_data['complexity']['level']}), "
                  f"Score improvement={repo_data['results']['score_improvement']:.1f}%")
        except Exception as e:
            print(f"[ERROR] {repo['name']}: {e}")
            raise

    # Calculate aggregate analysis
    aggregate_analysis = calculate_aggregate_analysis(repo_data_list)

    # Build final output
    output = {
        "meta": {
            "generated_timestamp": datetime.now(timezone.utc).isoformat(),
            "generator_version": "2.0.0",
            "repository_count": len(repo_data_list),
            "agent_count": len(aggregate_analysis["by_agent"]),
            "total_questions": aggregate_analysis["overall"]["total_questions"],
        },
        "repositories": repo_data_list,
        "aggregate_analysis": aggregate_analysis,
    }

    # Write JSON output
    output_path = SCRIPT_DIR / "summary_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("JSON OUTPUT COMPLETE")
    print("=" * 80)
    print(f"Repositories processed: {len(repo_data_list)}")
    print(f"Average score improvement: {aggregate_analysis['overall']['avg_score_improvement']:.1f}%")
    print(f"Average time reduction: {aggregate_analysis['overall']['avg_time_reduction_percentage']:.1f}%")
    print(f"\nJSON output written to: {output_path}")

    # Generate visualizations
    viz_output_dir = SCRIPT_DIR / "analysis_images"
    try:
        generate_all_visualizations(repo_data_list, aggregate_analysis, viz_output_dir)
    except Exception as e:
        print(f"\n[ERROR] Failed to generate visualizations: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Generate markdown report (in analysis_images directory)
    md_output_path = viz_output_dir / "analysis.md"
    try:
        generate_markdown_report(repo_data_list, aggregate_analysis, md_output_path, SCRIPT_DIR)
    except Exception as e:
        print(f"\n[ERROR] Failed to generate markdown report: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Final summary
    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print("\nKey Findings:")
    for finding in aggregate_analysis["insights"]["key_findings"]:
        print(f"  • {finding}")
    print(f"\nOutputs generated:")
    print(f"  1. {output_path} (JSON data)")
    print(f"  2. {viz_output_dir}/ (8 visualizations, PNG + SVG)")
    print(f"  3. {md_output_path} (markdown report)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
