#!/usr/bin/env python3
"""
RIG Effectiveness Visualizer - Single Repository Analysis

Generates academic-quality visualizations showing RIG (Repository Information Generation)
effectiveness for a single repository's agent evaluation results.

Usage:
    python results_visualizer.py <repo_path> [--svg]

Example:
    python results_visualizer.py tests/deterministic/cmake/jni_hello_world --svg

Output:
    Creates {repo_path}/analysis_images/ containing:
    - 8 PNG visualizations (+ SVG if --svg flag provided)
    - analysis.md markdown report
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Academic paper styling configuration
def setup_plotting_style():
    """Configure matplotlib for academic paper quality."""
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['font.size'] = 10
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10


# Color scheme (colorblind-friendly)
COLORS = {
    'without_rig': '#E74C3C',  # Red
    'with_rig': '#27AE60',     # Green
    'claude': '#3498DB',        # Blue
    'codex': '#9B59B6',        # Purple
    'cursor': '#F39C12',       # Orange
    'neutral': '#95A5A6',      # Gray
    'positive': '#27AE60',     # Green
    'negative': '#E74C3C',     # Red
}

AGENTS = ['claude', 'codex', 'cursor']
AGENT_DISPLAY = {'claude': 'Claude', 'codex': 'Codex', 'cursor': 'Cursor'}
DIFFICULTIES = ['easy', 'medium', 'hard']
DIFFICULTY_DISPLAY = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


class VisualizationGenerator:
    """Generates all visualizations for a single repository analysis."""

    def __init__(self, repo_path: str, output_svg: bool = False):
        """
        Initialize visualization generator.

        Args:
            repo_path: Path to repository directory containing answers_analysis.json
            output_svg: If True, also generate SVG versions of all charts
        """
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_svg = output_svg
        self.analysis_data = None
        self.output_dir = self.repo_path / "analysis_images"

    def load_analysis(self) -> bool:
        """
        Load answers_analysis.json from repository.

        Returns:
            True if successful, False otherwise
        """
        analysis_file = self.repo_path / "answers_analysis.json"

        if not analysis_file.exists():
            print(f"[ERROR] Analysis file not found: {analysis_file}", file=sys.stderr)
            return False

        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)
            print(f"[OK] Loaded analysis from {analysis_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load analysis: {e}", file=sys.stderr)
            return False

    def create_output_directory(self) -> bool:
        """
        Create analysis_images output directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Output directory: {self.output_dir}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create output directory: {e}", file=sys.stderr)
            return False

    def save_figure(self, fig: plt.Figure, filename: str):
        """
        Save figure to PNG (and optionally SVG).

        Args:
            fig: Matplotlib figure to save
            filename: Base filename (without extension)
        """
        # Save PNG
        png_path = self.output_dir / f"{filename}.png"
        fig.savefig(png_path, bbox_inches='tight', dpi=300)
        print(f"  [OK] Saved {png_path.name}")

        # Save SVG if requested
        if self.output_svg:
            svg_path = self.output_dir / f"{filename}.svg"
            fig.savefig(svg_path, bbox_inches='tight')
            print(f"  [OK] Saved {svg_path.name}")

        plt.close(fig)

    def generate_all_visualizations(self):
        """Generate all 8 visualizations for the repository."""
        print(f"\n[LOG] Generating visualizations for {self.repo_name}...\n")

        # Chart 1: Agent Performance Comparison
        print("[1/8] Agent Performance Comparison...")
        self.chart_agent_performance_comparison()

        # Chart 2: Time Performance by Agent
        print("[2/8] Time Performance by Agent...")
        self.chart_time_performance()

        # Chart 3: Difficulty-Based Improvement
        print("[3/8] Difficulty-Based Improvement...")
        self.chart_difficulty_improvement()

        # Chart 4: Efficiency Scatter Plot
        print("[4/8] Efficiency Scatter Plot...")
        self.chart_efficiency_scatter()

        # Chart 5: Question-Level Heatmap
        print("[5/8] Question-Level Heatmap...")
        self.chart_question_heatmap()

        # Chart 6: RIG Impact Distribution
        print("[6/8] RIG Impact Distribution...")
        self.chart_rig_impact_distribution()

        # Chart 7: Category Performance Radar Chart
        print("[7/8] Category Performance Radar...")
        self.chart_category_radar()

        # Chart 8: Mistake Analysis
        print("[8/8] Mistake Analysis...")
        self.chart_mistake_analysis()

        print(f"\n[OK] All visualizations generated successfully!")

    def chart_agent_performance_comparison(self):
        """Chart 1: Grouped bar chart comparing agent performance with/without RIG."""
        fig, ax = plt.subplots(figsize=(10, 6))

        analysis = self.analysis_data['analysis']
        by_agent = analysis['by_agent']

        x = np.arange(len(AGENTS))
        width = 0.35

        without_rig_scores = []
        with_rig_scores = []

        for agent in AGENTS:
            agent_data = by_agent[agent]
            without_rig_scores.append(agent_data['without_rig']['percentage'])
            with_rig_scores.append(agent_data['with_rig']['percentage'])

        # Create bars
        bars1 = ax.bar(x - width/2, without_rig_scores, width, label='Without RIG',
                       color=COLORS['without_rig'], alpha=0.8)
        bars2 = ax.bar(x + width/2, with_rig_scores, width, label='With RIG',
                       color=COLORS['with_rig'], alpha=0.8)

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=9)

        ax.set_xlabel('Agent', fontweight='bold')
        ax.set_ylabel('Score (%)', fontweight='bold')
        ax.set_title('RIG vs No-RIG: Agent Performance Comparison', fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([AGENT_DISPLAY[a] for a in AGENTS])
        ax.legend(loc='lower right')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        self.save_figure(fig, f"{self.repo_name}_agent_performance_comparison")

    def chart_time_performance(self):
        """Chart 2: Grouped bar chart showing time performance with/without RIG."""
        fig, ax = plt.subplots(figsize=(10, 6))

        analysis = self.analysis_data['analysis']
        by_agent = analysis['by_agent']

        x = np.arange(len(AGENTS))
        width = 0.35

        without_rig_times = []
        with_rig_times = []
        reductions = []

        for agent in AGENTS:
            agent_data = by_agent[agent]
            timing = agent_data['timing']
            without_rig_times.append(timing['time_without_rig_seconds'])
            with_rig_times.append(timing['time_with_rig_seconds'])
            reductions.append(timing['time_reduction_percentage'])

        # Create bars
        bars1 = ax.bar(x - width/2, without_rig_times, width, label='Without RIG',
                       color=COLORS['without_rig'], alpha=0.8)
        bars2 = ax.bar(x + width/2, with_rig_times, width, label='With RIG',
                       color=COLORS['with_rig'], alpha=0.8)

        # Add time labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}s',
                       ha='center', va='bottom', fontsize=9)

        # Add reduction percentage annotations above pairs
        for i, reduction in enumerate(reductions):
            sign = '+' if reduction < 0 else ''
            color = COLORS['negative'] if reduction < 0 else COLORS['positive']
            max_height = max(without_rig_times[i], with_rig_times[i])
            ax.text(i, max_height * 1.1, f'{sign}{reduction:.1f}%',
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   color=color)

        ax.set_xlabel('Agent', fontweight='bold')
        ax.set_ylabel('Time (seconds)', fontweight='bold')
        ax.set_title('Time to Completion: RIG Impact on Speed', fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([AGENT_DISPLAY[a] for a in AGENTS])
        ax.legend(loc='upper right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add some space at top for annotations
        y_max = max(without_rig_times + with_rig_times) * 1.25
        ax.set_ylim(0, y_max)

        self.save_figure(fig, f"{self.repo_name}_time_performance_by_agent")

    def chart_difficulty_improvement(self):
        """Chart 3: Stacked bar chart showing RIG improvement by difficulty."""
        fig, ax = plt.subplots(figsize=(10, 6))

        analysis = self.analysis_data['analysis']
        by_agent = analysis['by_agent']

        # Calculate average scores across all agents for each difficulty
        difficulty_data = {d: {'without_rig': [], 'with_rig': []} for d in DIFFICULTIES}

        for agent in AGENTS:
            agent_data = by_agent[agent]
            for difficulty in DIFFICULTIES:
                without_data = agent_data['without_rig']['by_difficulty'][difficulty]
                with_data = agent_data['with_rig']['by_difficulty'][difficulty]
                difficulty_data[difficulty]['without_rig'].append(without_data['percentage'])
                difficulty_data[difficulty]['with_rig'].append(with_data['percentage'])

        # Calculate averages
        avg_without = [np.mean(difficulty_data[d]['without_rig']) for d in DIFFICULTIES]
        avg_with = [np.mean(difficulty_data[d]['with_rig']) for d in DIFFICULTIES]
        improvements = [avg_with[i] - avg_without[i] for i in range(len(DIFFICULTIES))]

        x = np.arange(len(DIFFICULTIES))
        width = 0.6

        # Create stacked bars
        bars1 = ax.bar(x, avg_without, width, label='Base Score (No RIG)',
                       color=COLORS['without_rig'], alpha=0.8)
        bars2 = ax.bar(x, improvements, width, bottom=avg_without,
                       label='Improvement with RIG', color=COLORS['with_rig'], alpha=0.8)

        # Add labels
        for i, (base, improvement) in enumerate(zip(avg_without, improvements)):
            # Base score label
            ax.text(i, base/2, f'{base:.1f}%',
                   ha='center', va='center', fontsize=10, fontweight='bold')
            # Improvement label
            if improvement > 2:  # Only show if visible
                ax.text(i, base + improvement/2, f'+{improvement:.1f}%',
                       ha='center', va='center', fontsize=10, fontweight='bold',
                       color='white')

        ax.set_xlabel('Question Difficulty', fontweight='bold')
        ax.set_ylabel('Average Score (%)', fontweight='bold')
        ax.set_title('RIG Effectiveness by Question Difficulty', fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([DIFFICULTY_DISPLAY[d] for d in DIFFICULTIES])
        ax.legend(loc='lower right')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        self.save_figure(fig, f"{self.repo_name}_difficulty_improvement")

    def chart_efficiency_scatter(self):
        """Chart 4: Scatter plot showing efficiency (score per second)."""
        fig, ax = plt.subplots(figsize=(10, 8))

        analysis = self.analysis_data['analysis']
        by_agent = analysis['by_agent']

        for agent in AGENTS:
            agent_data = by_agent[agent]

            # Calculate efficiency (score / time)
            time_without = agent_data['timing']['time_without_rig_seconds']
            time_with = agent_data['timing']['time_with_rig_seconds']
            score_without = agent_data['without_rig']['percentage']
            score_with = agent_data['with_rig']['percentage']

            # Avoid division by zero
            if time_without == 0 or time_with == 0:
                continue

            # Plot both points
            ax.scatter(time_without, score_without, s=200, color=COLORS[agent],
                      marker='o', alpha=0.6, edgecolors='black', linewidth=2)
            ax.scatter(time_with, score_with, s=200, color=COLORS[agent],
                      marker='s', alpha=0.9, edgecolors='black', linewidth=2,
                      label=AGENT_DISPLAY[agent])

            # Draw arrow from without to with
            ax.annotate('', xy=(time_with, score_with), xytext=(time_without, score_without),
                       arrowprops=dict(arrowstyle='->', color=COLORS[agent],
                                     lw=2, alpha=0.7))

            # Label points
            ax.text(time_without, score_without - 3, f'No RIG',
                   ha='center', va='top', fontsize=8, color=COLORS[agent],
                   fontweight='bold')
            ax.text(time_with, score_with + 3, f'With RIG',
                   ha='center', va='bottom', fontsize=8, color=COLORS[agent],
                   fontweight='bold')

        # Add efficiency diagonal lines (score/time ratios)
        time_range = ax.get_xlim()
        for efficiency in [0.5, 1.0, 2.0]:
            times = np.linspace(time_range[0], time_range[1], 100)
            scores = times * efficiency
            ax.plot(times, scores, 'k--', alpha=0.2, linewidth=1)
            # Label efficiency line
            if time_range[1] * efficiency < 100:
                ax.text(time_range[1] * 0.9, time_range[1] * efficiency * 0.9,
                       f'{efficiency:.1f}%/s', fontsize=8, alpha=0.5, rotation=30)

        ax.set_xlabel('Time (seconds)', fontweight='bold')
        ax.set_ylabel('Score (%)', fontweight='bold')
        ax.set_title('Efficiency Analysis: Score per Second', fontweight='bold', pad=20)
        ax.legend(loc='lower right')
        ax.grid(alpha=0.3, linestyle='--')
        ax.set_ylim(0, 105)

        # Add legend for markers
        circle = mpatches.Patch(color='gray', label='Without RIG (circle)')
        square = mpatches.Patch(color='gray', label='With RIG (square)')
        handles, labels = ax.get_legend_handles_labels()
        handles.extend([circle, square])
        labels.extend(['Without RIG (circle)', 'With RIG (square)'])
        ax.legend(handles, labels, loc='lower right', fontsize=9)

        self.save_figure(fig, f"{self.repo_name}_efficiency_scatter")

    def chart_question_heatmap(self):
        """Chart 5: Heatmap showing question-by-question performance."""
        results = self.analysis_data['results']

        # Extract question IDs and scores
        # Get question count from first agent
        # Get questions from question-centric structure
        questions = results['questions']
        question_ids = [q['id'] for q in questions]

        # Build matrix: rows = agent_condition, cols = questions
        row_labels = []
        matrix_data = []

        for agent in AGENTS:
            for condition in ['RIG', 'NORIG']:
                key = f"{agent}_{condition}"
                # Extract scores from question-centric data
                scores = [q.get(key, {}).get('score', 0) for q in questions]
                matrix_data.append(scores)

                condition_label = 'RIG' if condition == 'RIG' else 'No RIG'
                row_labels.append(f"{AGENT_DISPLAY[agent]}\n{condition_label}")

        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, 8))

        # Use green/red colormap
        cmap = LinearSegmentedColormap.from_list('score', [COLORS['negative'], COLORS['positive']])

        im = ax.imshow(matrix_data, cmap=cmap, aspect='auto', vmin=0, vmax=1)

        # Set ticks
        ax.set_xticks(np.arange(len(question_ids)))
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_xticklabels(question_ids, fontsize=8)
        ax.set_yticklabels(row_labels, fontsize=9)

        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor")

        # Add gridlines
        ax.set_xticks(np.arange(len(question_ids)) - 0.5, minor=True)
        ax.set_yticks(np.arange(len(row_labels)) - 0.5, minor=True)
        ax.grid(which="minor", color="white", linestyle='-', linewidth=2)

        # Labels
        ax.set_xlabel('Question ID', fontweight='bold')
        ax.set_ylabel('Agent & Condition', fontweight='bold')
        ax.set_title('Question-by-Question Performance Matrix', fontweight='bold', pad=20)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Score (0=Incorrect, 1=Correct)', rotation=270, labelpad=20, fontweight='bold')

        self.save_figure(fig, f"{self.repo_name}_question_heatmap")

    def chart_rig_impact_distribution(self):
        """Chart 6: Box plot showing distribution of RIG improvement across questions."""
        results = self.analysis_data['results']

        # Calculate per-question improvements for each agent
        agent_improvements = {agent: [] for agent in AGENTS}

        for agent in AGENTS:
            with_rig_key = f"{agent}_RIG"
            without_rig_key = f"{agent}_NORIG"

            # Extract improvements from question-centric data
            for q in results['questions']:
                with_rig_score = q.get(with_rig_key, {}).get('score', 0)
                without_rig_score = q.get(without_rig_key, {}).get('score', 0)
                improvement = with_rig_score - without_rig_score
                agent_improvements[agent].append(improvement)

        # Prepare data for box plot
        data = [agent_improvements[agent] for agent in AGENTS]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create box plot
        bp = ax.boxplot(data, tick_labels=[AGENT_DISPLAY[a] for a in AGENTS],
                        patch_artist=True, showmeans=True)

        # Color boxes
        for patch, agent in zip(bp['boxes'], AGENTS):
            patch.set_facecolor(COLORS[agent])
            patch.set_alpha(0.6)

        # Add horizontal line at y=0
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        # Add grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        ax.set_xlabel('Agent', fontweight='bold')
        ax.set_ylabel('Per-Question Improvement (score delta)', fontweight='bold')
        ax.set_title('Distribution of RIG Impact Across Questions', fontweight='bold', pad=20)
        ax.set_ylim(-1.2, 1.2)

        # Add labels
        ax.text(0.02, 0.98, 'Improvement (RIG helped)', transform=ax.transAxes,
               verticalalignment='top', fontsize=9, color=COLORS['positive'],
               fontweight='bold')
        ax.text(0.02, 0.02, 'Regression (RIG hurt)', transform=ax.transAxes,
               verticalalignment='bottom', fontsize=9, color=COLORS['negative'],
               fontweight='bold')

        self.save_figure(fig, f"{self.repo_name}_rig_impact_distribution")

    def chart_category_radar(self):
        """Chart 7: Radar chart showing performance by question category."""
        analysis = self.analysis_data['analysis']

        # Check if category data exists
        if 'by_category' not in analysis or not analysis['by_category']:
            raise ValueError(
                f"No category data available for repository {self.repo_name}. "
                f"answers_analysis.json may be corrupted or incomplete."
            )

        by_category = analysis['by_category']
        categories = list(by_category.keys())

        if len(categories) < 3:
            print(f"  [SKIP] Too few categories ({len(categories)}) for radar chart")
            return

        # Calculate average scores across agents for each category
        avg_with_rig = []
        avg_without_rig = []

        for category in categories:
            cat_data = by_category[category]
            avg_with_rig.append(cat_data['with_rig']['percentage'])
            avg_without_rig.append(cat_data['without_rig']['percentage'])

        # Number of variables
        num_vars = len(categories)

        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

        # Complete the circle
        avg_with_rig += avg_with_rig[:1]
        avg_without_rig += avg_without_rig[:1]
        angles += angles[:1]

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # Plot data
        ax.plot(angles, avg_with_rig, 'o-', linewidth=2, label='With RIG',
               color=COLORS['with_rig'])
        ax.fill(angles, avg_with_rig, alpha=0.25, color=COLORS['with_rig'])

        ax.plot(angles, avg_without_rig, 'o-', linewidth=2, label='Without RIG',
               color=COLORS['without_rig'])
        ax.fill(angles, avg_without_rig, alpha=0.25, color=COLORS['without_rig'])

        # Fix axis to go from 0 to 100
        ax.set_ylim(0, 100)

        # Set category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)

        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

        ax.set_title('Performance by Question Category', fontweight='bold', pad=20, y=1.08)

        # Add grid
        ax.grid(True)

        self.save_figure(fig, f"{self.repo_name}_category_radar")

    def chart_mistake_analysis(self):
        """Chart 8: Diverging bar chart showing questions fixed vs broken by RIG."""
        analysis = self.analysis_data['analysis']
        by_agent = analysis['by_agent']

        agent_labels = []
        questions_fixed = []
        questions_broken = []

        for agent in AGENTS:
            agent_data = by_agent[agent]
            agent_labels.append(AGENT_DISPLAY[agent])
            questions_fixed.append(len(agent_data['questions_fixed_by_rig']))
            questions_broken.append(-len(agent_data['questions_broken_by_rig']))  # Negative

        # Create horizontal diverging bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        y_pos = np.arange(len(agent_labels))

        # Plot bars
        bars1 = ax.barh(y_pos, questions_fixed, height=0.6, label='Questions Fixed',
                        color=COLORS['positive'], alpha=0.8)
        bars2 = ax.barh(y_pos, questions_broken, height=0.6, label='Questions Broken',
                        color=COLORS['negative'], alpha=0.8)

        # Add value labels
        for i, (fixed, broken) in enumerate(zip(questions_fixed, questions_broken)):
            if fixed > 0:
                ax.text(fixed + 0.2, i, f'+{fixed}',
                       ha='left', va='center', fontsize=10, fontweight='bold',
                       color=COLORS['positive'])
            if broken < 0:
                ax.text(broken - 0.2, i, f'{broken}',
                       ha='right', va='center', fontsize=10, fontweight='bold',
                       color=COLORS['negative'])

            # Net improvement
            net = fixed + abs(broken)
            if net != 0:
                sign = '+' if net > 0 else ''
                ax.text(max(fixed, abs(broken)) + 1, i, f'(Net: {sign}{net})',
                       ha='left', va='center', fontsize=9, style='italic')

        # Vertical line at x=0
        ax.axvline(x=0, color='black', linewidth=2)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(agent_labels)
        ax.set_xlabel('Number of Questions', fontweight='bold')
        ax.set_title('Questions Fixed vs Broken by RIG', fontweight='bold', pad=20)
        ax.legend(loc='lower right')
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        # Add labels for sides
        ax.text(0.02, 0.98, 'Questions Fixed\n(RIG improved)', transform=ax.transAxes,
               verticalalignment='top', horizontalalignment='left',
               fontsize=9, color=COLORS['positive'], fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax.text(0.98, 0.98, 'Questions Broken\n(RIG regressed)', transform=ax.transAxes,
               verticalalignment='top', horizontalalignment='right',
               fontsize=9, color=COLORS['negative'], fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self.save_figure(fig, f"{self.repo_name}_mistake_analysis")

    def generate_markdown_report(self):
        """Generate comprehensive markdown report presenting all visualizations."""
        print("\n[LOG] Generating markdown report...")

        analysis = self.analysis_data['analysis']
        summary = analysis['summary']
        by_agent = analysis['by_agent']

        # Calculate overall metrics
        avg_with_rig = summary['average_with_rig']
        avg_without_rig = summary['average_without_rig']
        avg_improvement = summary['average_rig_improvement']

        # Calculate average time metrics
        total_time_with = sum(by_agent[a]['timing']['time_with_rig_seconds'] for a in AGENTS)
        total_time_without = sum(by_agent[a]['timing']['time_without_rig_seconds'] for a in AGENTS)
        avg_time_with = total_time_with / len(AGENTS)
        avg_time_without = total_time_without / len(AGENTS)
        total_time_saved = total_time_without - total_time_with
        time_reduction_pct = (total_time_saved / total_time_without * 100) if total_time_without > 0 else 0

        # Get question counts from results (question-centric structure)
        total_questions = len(self.analysis_data['results']['questions'])

        # Count questions by difficulty
        difficulty_counts = {d: 0 for d in DIFFICULTIES}
        for q in self.analysis_data['results']['questions']:
            if 'difficulty' in q:
                difficulty_counts[q['difficulty']] = difficulty_counts.get(q['difficulty'], 0) + 1

        # Generate markdown content
        md_lines = [
            f"# RIG Effectiveness Analysis: {self.repo_name}",
            "",
            f"**Repository**: `{self.repo_name}`",
            f"**Agents Tested**: {', '.join(AGENT_DISPLAY[a] for a in AGENTS)}",
            f"**Total Questions**: {total_questions}",
            f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"This analysis evaluates the effectiveness of RIG (Repository Information Generation) on agent performance for the **{self.repo_name}** repository. ",
            f"Three agents (Claude, Codex, Cursor) answered {total_questions} questions both with and without access to RIG metadata.",
            "",
            f"**Key Finding**: RIG improved average agent performance by **{avg_improvement:.1f} percentage points** ",
            f"({avg_without_rig:.1f}% → {avg_with_rig:.1f}%) while reducing average completion time by **{time_reduction_pct:.1f}%** ",
            f"({avg_time_without:.1f}s → {avg_time_with:.1f}s).",
            "",
            "---",
            "",
            "## 1. Overall Performance",
            "",
            f"![Agent Performance Comparison]({self.repo_name}_agent_performance_comparison.png)",
            "",
            "**Key Findings**:",
            f"- Average score with RIG: **{avg_with_rig:.1f}%**",
            f"- Average score without RIG: **{avg_without_rig:.1f}%**",
            f"- **Improvement: +{avg_improvement:.1f} percentage points**",
            "",
            "### Per-Agent Performance",
            "",
            "| Agent | Without RIG | With RIG | Improvement |",
            "|-------|-------------|----------|-------------|",
        ]

        for agent in AGENTS:
            agent_data = by_agent[agent]
            without_pct = agent_data['without_rig']['percentage']
            with_pct = agent_data['with_rig']['percentage']
            improvement = agent_data['rig_improvement']['percentage']
            md_lines.append(
                f"| {AGENT_DISPLAY[agent]} | {without_pct:.1f}% | {with_pct:.1f}% | +{improvement:.1f}% |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 2. Time Performance",
            "",
            f"![Time Performance by Agent]({self.repo_name}_time_performance_by_agent.png)",
            "",
            "**Key Findings**:",
            f"- Average time with RIG: **{avg_time_with:.1f} seconds**",
            f"- Average time without RIG: **{avg_time_without:.1f} seconds**",
            f"- **Time saved: {total_time_saved:.1f} seconds ({time_reduction_pct:.1f}% reduction)**",
            "",
            "### Per-Agent Time Performance",
            "",
            "| Agent | Without RIG | With RIG | Time Saved | Reduction |",
            "|-------|-------------|----------|------------|-----------|",
        ])

        for agent in AGENTS:
            timing = by_agent[agent]['timing']
            without_time = timing['time_without_rig_seconds']
            with_time = timing['time_with_rig_seconds']
            saved = timing['time_saved_seconds']
            reduction = timing['time_reduction_percentage']
            sign = '+' if reduction < 0 else ''
            md_lines.append(
                f"| {AGENT_DISPLAY[agent]} | {without_time:.1f}s | {with_time:.1f}s | {saved:.1f}s | {sign}{reduction:.1f}% |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Difficulty Analysis",
            "",
            f"![Difficulty-Based Improvement]({self.repo_name}_difficulty_improvement.png)",
            "",
            "RIG effectiveness varies by question difficulty level:",
            "",
        ])

        # Calculate average improvement by difficulty
        for difficulty in DIFFICULTIES:
            improvements = []
            for agent in AGENTS:
                agent_data = by_agent[agent]
                improvement = agent_data['rig_improvement']['by_difficulty'][difficulty]['percentage']
                improvements.append(improvement)
            avg_diff_improvement = np.mean(improvements)

            md_lines.append(
                f"- **{DIFFICULTY_DISPLAY[difficulty]} questions**: "
                f"+{avg_diff_improvement:.1f}% average improvement"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 4. Efficiency Analysis",
            "",
            f"![Efficiency Scatter Plot]({self.repo_name}_efficiency_scatter.png)",
            "",
            "This scatter plot shows the relationship between time and accuracy for each agent. ",
            "Arrows indicate the direction of change when RIG is introduced. ",
            "The ideal trajectory is toward the upper-left (higher score, less time).",
            "",
            "**Interpretation**:",
        ])

        for agent in AGENTS:
            agent_data = by_agent[agent]
            timing = agent_data['timing']

            time_delta = timing['time_with_rig_seconds'] - timing['time_without_rig_seconds']
            score_delta = agent_data['with_rig']['percentage'] - agent_data['without_rig']['percentage']

            if time_delta < 0 and score_delta > 0:
                direction = "improved both speed and accuracy"
            elif time_delta < 0 and score_delta < 0:
                direction = "became faster but less accurate"
            elif time_delta > 0 and score_delta > 0:
                direction = "became more accurate but slower"
            else:
                direction = "became both slower and less accurate"

            md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: {direction}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 5. Question-Level Analysis",
            "",
            f"![Question-Level Heatmap]({self.repo_name}_question_heatmap.png)",
            "",
            "This heatmap visualizes per-question performance for each agent and condition. ",
            "Green indicates correct answers, red indicates incorrect answers. ",
            "Patterns reveal which questions benefit most from RIG.",
            "",
            f"![RIG Impact Distribution]({self.repo_name}_rig_impact_distribution.png)",
            "",
            "The box plot shows the distribution of RIG's impact across questions. ",
            "Positive values indicate questions where RIG helped, negative values indicate regressions.",
            "",
            "---",
            "",
            "## 6. Category Performance",
            "",
        ])

        # Check if category chart exists
        if 'by_category' in analysis and analysis['by_category']:
            md_lines.extend([
                f"![Category Performance Radar]({self.repo_name}_category_radar.png)",
                "",
                "Performance breakdown by question category shows where RIG provides the most benefit:",
                "",
            ])

            for category, cat_data in analysis['by_category'].items():
                with_pct = cat_data['with_rig']['percentage']
                without_pct = cat_data['without_rig']['percentage']
                improvement = with_pct - without_pct
                md_lines.append(
                    f"- **{category}**: {without_pct:.1f}% → {with_pct:.1f}% (+{improvement:.1f}%)"
                )
        else:
            md_lines.append("*Category data not available for this repository.*")

        md_lines.extend([
            "",
            "---",
            "",
            "## 7. Detailed Impact: Questions Fixed vs Broken",
            "",
            f"![Mistake Analysis]({self.repo_name}_mistake_analysis.png)",
            "",
            "An honest assessment of RIG's impact, showing both improvements and regressions:",
            "",
            "### Questions Fixed by RIG",
            "",
        ])

        for agent in AGENTS:
            agent_data = by_agent[agent]
            fixed = agent_data['questions_fixed_by_rig']
            if fixed:
                md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: {len(fixed)} questions ({', '.join(map(str, fixed))})")
            else:
                md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: None")

        md_lines.extend([
            "",
            "### Questions Broken by RIG",
            "",
        ])

        for agent in AGENTS:
            agent_data = by_agent[agent]
            broken = agent_data['questions_broken_by_rig']
            if broken:
                md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: {len(broken)} questions ({', '.join(map(str, broken))})")
            else:
                md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: None")

        md_lines.extend([
            "",
            "### Net Impact",
            "",
        ])

        for agent in AGENTS:
            agent_data = by_agent[agent]
            fixed_count = len(agent_data['questions_fixed_by_rig'])
            broken_count = len(agent_data['questions_broken_by_rig'])
            net = fixed_count - broken_count
            sign = '+' if net > 0 else ''
            md_lines.append(f"- **{AGENT_DISPLAY[agent]}**: {sign}{net} questions (net improvement)")

        md_lines.extend([
            "",
            "---",
            "",
            "## Conclusions",
            "",
            f"RIG demonstrates measurable value for the **{self.repo_name}** repository:",
            "",
        ])

        # Determine key takeaways
        if avg_improvement > 5:
            md_lines.append(f"1. **Significant accuracy improvement**: +{avg_improvement:.1f} percentage points average")
        elif avg_improvement > 0:
            md_lines.append(f"1. **Moderate accuracy improvement**: +{avg_improvement:.1f} percentage points average")
        else:
            md_lines.append(f"1. **Minimal accuracy impact**: {avg_improvement:.1f} percentage points average")

        if time_reduction_pct > 30:
            md_lines.append(f"2. **Substantial time savings**: {time_reduction_pct:.1f}% average reduction")
        elif time_reduction_pct > 0:
            md_lines.append(f"2. **Moderate time savings**: {time_reduction_pct:.1f}% average reduction")
        else:
            md_lines.append(f"2. **Time overhead**: {abs(time_reduction_pct):.1f}% average increase")

        # Agent-specific insights
        best_agent = max(AGENTS, key=lambda a: by_agent[a]['rig_improvement']['percentage'])
        best_improvement = by_agent[best_agent]['rig_improvement']['percentage']
        md_lines.append(f"3. **Most benefit**: {AGENT_DISPLAY[best_agent]} saw {best_improvement:.1f}% improvement")

        # Overall recommendation
        if avg_improvement > 0 or time_reduction_pct > 0:
            md_lines.extend([
                "",
                f"**Recommendation**: RIG provides measurable value for {self.repo_name} and should be adopted.",
            ])
        else:
            md_lines.extend([
                "",
                f"**Recommendation**: RIG shows limited benefit for {self.repo_name}. Further evaluation recommended.",
            ])

        md_lines.extend([
            "",
            "---",
            "",
            "*This report was automatically generated by results_visualizer.py*",
            ""
        ])

        # Write markdown file
        md_path = self.output_dir / "analysis.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        print(f"[OK] Markdown report saved: {md_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate RIG effectiveness visualizations for a single repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python results_visualizer.py tests/deterministic/cmake/jni_hello_world
  python results_visualizer.py tests/deterministic/cmake/metaffi --svg
        '''
    )

    parser.add_argument('repo_path', type=str,
                       help='Path to repository directory containing answers_analysis.json')
    parser.add_argument('--svg', action='store_true',
                       help='Also generate SVG versions of all charts')

    args = parser.parse_args()

    # Setup plotting style
    setup_plotting_style()

    # Create visualizer
    visualizer = VisualizationGenerator(args.repo_path, output_svg=args.svg)

    # Load analysis data
    if not visualizer.load_analysis():
        sys.exit(1)

    # Create output directory
    if not visualizer.create_output_directory():
        sys.exit(1)

    # Generate all visualizations
    try:
        visualizer.generate_all_visualizations()
    except Exception as e:
        print(f"[ERROR] Failed to generate visualizations: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Generate markdown report
    try:
        visualizer.generate_markdown_report()
    except Exception as e:
        print(f"[ERROR] Failed to generate markdown report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n[SUCCESS] All outputs generated in: {visualizer.output_dir}")
    print(f"  - 8 visualizations (PNG{' + SVG' if args.svg else ''})")
    print(f"  - 1 markdown report (analysis.md)")


if __name__ == "__main__":
    main()
