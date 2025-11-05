#!/usr/bin/env python3
"""
Complete Analysis Pipeline Runner

Runs after ask_agents.py to generate all reports and visualizations.
This script automates the entire post-analysis workflow with fail-fast error handling.

Usage:
    python run_after_ask_agents_to_get_full_report.py
    python run_after_ask_agents_to_get_full_report.py --repo cmake/metaffi

The script will:
1. Discover all test repositories (or process single repo if specified)
2. Run answers_analysis.py for each repository
3. Run results_visualizer.py with --svg for each repository
4. Run overall_summary_analysis.py to generate aggregate analysis
5. Display summary of all generated reports

Author: Generated for deterministic test analysis
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json


# Fail-fast error handling
class AnalysisPipelineError(Exception):
    """Custom exception for pipeline failures."""
    pass


def run_command(cmd: List[str], description: str, cwd: Path = None) -> subprocess.CompletedProcess:
    """
    Run command with fail-fast error handling.

    Args:
        cmd: Command and arguments as list
        description: Human-readable description of the command
        cwd: Working directory (optional)

    Returns:
        CompletedProcess object

    Raises:
        AnalysisPipelineError: If command fails
    """
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    print('='*80)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False  # We'll handle return code manually
        )

        if result.returncode != 0:
            print(f"\n❌ ERROR: {description} failed!")
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print(f"\nSTDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"\nSTDERR:\n{result.stderr}")
            raise AnalysisPipelineError(f"{description} failed with exit code {result.returncode}")

        print(f"✅ {description} completed successfully")
        if result.stdout and result.stdout.strip():
            # Show some output but not too much
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 20:
                print(f"Output:\n{result.stdout}")
            else:
                print(f"Output (first 10 and last 10 lines):")
                print('\n'.join(lines[:10]))
                print(f"... ({len(lines) - 20} lines omitted) ...")
                print('\n'.join(lines[-10:]))

        return result

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Command not found: {cmd[0]}")
        print(f"Details: {e}")
        raise AnalysisPipelineError(f"Command not found: {cmd[0]}")


def discover_test_repositories(base_path: Path) -> List[Path]:
    """
    Discover all test repositories that have answer files.

    Args:
        base_path: Base path for deterministic tests

    Returns:
        List of repository paths that have answers

    Raises:
        AnalysisPipelineError: If no repositories found
    """
    print("\n" + "="*80)
    print("Discovering test repositories...")
    print("="*80)

    repos = []

    # Look for directories that contain answer files (search recursively up to 2 levels)
    # This finds tests/deterministic/cmake/metaffi/ etc.
    for item in base_path.rglob("*_answers.json"):
        repo_path = item.parent

        # Avoid duplicates
        if repo_path not in repos:
            # Count answer files in this directory
            answer_files = list(repo_path.glob("*_answers.json"))
            repos.append(repo_path)
            print(f"  Found: {repo_path.relative_to(base_path)}")
            print(f"    Answer files: {len(answer_files)}")

    if not repos:
        raise AnalysisPipelineError(
            f"No test repositories with answer files found in {base_path}\n"
            f"Please ensure you have run ask_agents.py first to generate answer files."
        )

    print(f"\nTotal repositories found: {len(repos)}")
    return sorted(repos)


def validate_repository(repo_path: Path) -> None:
    """
    Validate that a repository has the required files.

    Args:
        repo_path: Path to repository

    Raises:
        AnalysisPipelineError: If validation fails
    """
    # Check for answer files
    answer_files = list(repo_path.glob("*_answers.json"))
    if not answer_files:
        raise AnalysisPipelineError(
            f"No answer files found in {repo_path}"
        )

    # Check for evaluation questions
    eval_questions = repo_path / "evaluation_questions.json"
    if not eval_questions.exists():
        raise AnalysisPipelineError(
            f"No evaluation_questions.json found in {repo_path}"
        )

    print(f"  ✅ Validation passed: {len(answer_files)} answer files, evaluation questions present")


def run_answers_analysis(repo_path: Path, script_dir: Path) -> None:
    """
    Run answers_analysis.py for a repository.

    Args:
        repo_path: Path to repository
        script_dir: Path to deterministic tests directory

    Raises:
        AnalysisPipelineError: If analysis fails
    """
    relative_path = repo_path.relative_to(script_dir)

    run_command(
        ["python", "answers_analysis.py", str(relative_path)],
        f"Analyzing answers for {relative_path}",
        cwd=script_dir
    )


def run_results_visualizer(repo_path: Path, script_dir: Path) -> None:
    """
    Run results_visualizer.py for a repository.

    Args:
        repo_path: Path to repository
        script_dir: Path to deterministic tests directory

    Raises:
        AnalysisPipelineError: If visualization fails
    """
    relative_path = repo_path.relative_to(script_dir)

    run_command(
        ["python", "results_visualizer.py", str(relative_path), "--svg"],
        f"Generating visualizations for {relative_path}",
        cwd=script_dir
    )


def run_overall_summary(script_dir: Path) -> None:
    """
    Run overall_summary_analysis.py to generate aggregate analysis.

    Args:
        script_dir: Path to deterministic tests directory

    Raises:
        AnalysisPipelineError: If summary generation fails
    """
    run_command(
        ["python", "overall_summary_analysis.py"],
        "Generating overall summary analysis",
        cwd=script_dir
    )


def count_generated_files(repo_path: Path) -> Dict[str, int]:
    """
    Count generated files in a repository.

    Args:
        repo_path: Path to repository

    Returns:
        Dictionary with file counts
    """
    analysis_images = repo_path / "analysis_images"

    counts = {
        "answers_analysis": 1 if (repo_path / "answers_analysis.json").exists() else 0,
        "analysis_md": 1 if (analysis_images / "analysis.md").exists() else 0,
        "png_files": len(list(analysis_images.glob("*.png"))) if analysis_images.exists() else 0,
        "svg_files": len(list(analysis_images.glob("*.svg"))) if analysis_images.exists() else 0,
    }

    return counts


def print_summary(repos: List[Path], script_dir: Path) -> None:
    """
    Print summary of all generated reports.

    Args:
        repos: List of processed repositories
        script_dir: Path to deterministic tests directory
    """
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print("\nGenerated Reports:\n")

    # Individual repositories
    print("Individual Repositories:")
    for repo in repos:
        relative_path = repo.relative_to(script_dir)
        counts = count_generated_files(repo)

        print(f"\n  {relative_path}:")
        if counts["answers_analysis"]:
            print(f"    ✅ answers_analysis.json")
        if counts["analysis_md"]:
            print(f"    ✅ analysis_images/analysis.md")
        if counts["png_files"]:
            print(f"    ✅ {counts['png_files']} PNG visualizations")
        if counts["svg_files"]:
            print(f"    ✅ {counts['svg_files']} SVG visualizations")

    # Overall summary
    print("\n\nOverall Summary:")
    overall_analysis = script_dir / "analysis_images"
    if overall_analysis.exists():
        summary_json = script_dir / "summary_analysis" / "summary_analysis.json"
        if summary_json.exists():
            print(f"  ✅ summary_analysis/summary_analysis.json")

        analysis_md = overall_analysis / "analysis.md"
        if analysis_md.exists():
            print(f"  ✅ analysis_images/analysis.md")

        png_count = len(list(overall_analysis.glob("*.png")))
        svg_count = len(list(overall_analysis.glob("*.svg")))
        if png_count:
            print(f"  ✅ {png_count} PNG visualizations")
        if svg_count:
            print(f"  ✅ {svg_count} SVG visualizations")

    # Main report location
    main_report = overall_analysis / "analysis.md"
    if main_report.exists():
        print(f"\n" + "="*80)
        print(f"📊 Main Report: {main_report.relative_to(script_dir.parent)}")
        print("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run complete analysis pipeline after ask_agents.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all repositories
  python run_after_ask_agents_to_get_full_report.py

  # Process single repository
  python run_after_ask_agents_to_get_full_report.py --repo cmake/metaffi
        """
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="Process only this repository (relative path from tests/deterministic)"
    )

    args = parser.parse_args()

    # Setup paths
    script_dir = Path(__file__).parent.resolve()

    print("="*80)
    print("Analysis Pipeline Runner")
    print("="*80)
    print(f"Working directory: {script_dir}")

    try:
        # Discover or validate repositories
        if args.repo:
            # Single repository mode
            repo_path = script_dir / args.repo
            if not repo_path.exists():
                raise AnalysisPipelineError(f"Repository not found: {repo_path}")

            print(f"\nProcessing single repository: {args.repo}")
            validate_repository(repo_path)
            repos = [repo_path]
        else:
            # Multi-repository mode
            repos = discover_test_repositories(script_dir)

        # Process each repository
        for i, repo in enumerate(repos, 1):
            repo_name = repo.relative_to(script_dir)
            print(f"\n" + "="*80)
            print(f"Processing repository {i}/{len(repos)}: {repo_name}")
            print("="*80)

            # Validate
            validate_repository(repo)

            # Run answers analysis
            run_answers_analysis(repo, script_dir)

            # Run visualizer
            run_results_visualizer(repo, script_dir)

        # Run overall summary (only if processing multiple repos)
        if len(repos) > 1 or not args.repo:
            print(f"\n" + "="*80)
            print("Generating Overall Summary")
            print("="*80)
            run_overall_summary(script_dir)

        # Print summary
        print_summary(repos, script_dir)

        return 0

    except AnalysisPipelineError as e:
        print(f"\n" + "="*80)
        print(f"❌ PIPELINE FAILED")
        print("="*80)
        print(f"Error: {e}")
        print("\nPlease fix the error and run again.")
        return 1

    except KeyboardInterrupt:
        print(f"\n" + "="*80)
        print("⚠️  PIPELINE INTERRUPTED")
        print("="*80)
        print("Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n" + "="*80)
        print(f"❌ UNEXPECTED ERROR")
        print("="*80)
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
