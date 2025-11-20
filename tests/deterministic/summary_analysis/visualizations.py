"""
Visualization module for RIG effectiveness summary analysis.

This module generates all charts for the cross-repository analysis:
- Complexity vs score improvement scatter plot
- Complexity vs time reduction scatter plot
- Repository comparison bar charts
- Time savings cascade charts
- Agent performance heatmap
- Difficulty improvement charts
- Efficiency improvement dual-axis charts

All charts are generated in academic paper quality (300 DPI, colorblind-friendly).
"""

from pathlib import Path
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from .config import COLORS, MARKERS, AGENT_DISPLAY, DIFFICULTIES, DIFFICULTY_DISPLAY
from .config import PLOT_STYLE, PLOT_DPI, PLOT_FONT_SIZE, PLOT_FONT_FAMILY
from .config import PLOT_AXES_LABELSIZE, PLOT_AXES_TITLESIZE
from .config import PLOT_LEGEND_FONTSIZE, PLOT_TICK_LABELSIZE


def setup_plotting_style():
    """Configure matplotlib for academic paper quality."""
    plt.style.use(PLOT_STYLE)
    plt.rcParams['figure.dpi'] = PLOT_DPI
    plt.rcParams['savefig.dpi'] = PLOT_DPI
    plt.rcParams['font.size'] = PLOT_FONT_SIZE
    plt.rcParams['font.family'] = PLOT_FONT_FAMILY
    plt.rcParams['axes.labelsize'] = PLOT_AXES_LABELSIZE
    plt.rcParams['axes.titlesize'] = PLOT_AXES_TITLESIZE
    plt.rcParams['legend.fontsize'] = PLOT_LEGEND_FONTSIZE
    plt.rcParams['xtick.labelsize'] = PLOT_TICK_LABELSIZE
    plt.rcParams['ytick.labelsize'] = PLOT_TICK_LABELSIZE


def _save_figure(fig, output_dir: Path, filename: str):
    """
    Save figure as both PNG and SVG with proper formatting.

    Args:
        fig: Matplotlib figure object
        output_dir: Directory to save files
        filename: Base filename (without extension)
    """
    png_path = output_dir / f"{filename}.png"
    svg_path = output_dir / f"{filename}.svg"
    fig.savefig(png_path, bbox_inches='tight', dpi=PLOT_DPI)
    fig.savefig(svg_path, bbox_inches='tight')
    print(f"  [OK] {filename}.png + .svg")
    plt.close(fig)


def _generate_complexity_vs_score(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate scatter plot of complexity vs score improvement."""
    print("[1/7] Complexity vs Score Improvement...")

    fig, ax = plt.subplots(figsize=(10, 8))

    correlation_data = aggregate['correlations']['complexity_vs_rig_benefit']['score_correlation']
    agents = list(aggregate['by_agent'].keys())

    # Plot each agent's data points
    for agent in agents:
        x_vals = []
        y_vals = []
        labels = []

        for repo in repo_data_list:
            if agent in repo['results']['by_agent']:
                x_vals.append(repo['complexity']['normalized_score'])
                y_vals.append(repo['results']['by_agent'][agent]['score_improvement'])
                labels.append(repo['name'])

        ax.scatter(x_vals, y_vals, s=200, marker=MARKERS[agent], color=COLORS[agent], alpha=0.7,
                  edgecolors='black', linewidth=2, label=AGENT_DISPLAY[agent])

        # Label points
        for x, y, label in zip(x_vals, y_vals, labels):
            ax.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)

    # Add linear regression line
    all_x = [repo['complexity']['normalized_score'] for repo in repo_data_list]
    all_y = [repo['results']['score_improvement'] for repo in repo_data_list]

    if len(all_x) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(all_x, all_y)
        line_x = np.array([min(all_x), max(all_x)])
        line_y = slope * line_x + intercept
        ax.plot(line_x, line_y, 'k--', alpha=0.5, linewidth=2,
                label=f'Trendline (R²={r_value**2:.3f})')

    ax.set_xlabel('Repository Complexity (normalized 0-100)', fontweight='bold')
    ax.set_ylabel('Score Improvement with RIG (%)', fontweight='bold')
    ax.set_title('Repository Complexity Strongly Correlates with RIG Benefit\n(Higher complexity → Greater RIG value)',
                 fontweight='bold', pad=20)
    ax.legend(loc='upper left')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim(-5, 105)

    _save_figure(fig, output_dir, 'complexity_vs_score_improvement')


def _generate_complexity_vs_time(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate scatter plot of complexity vs time reduction."""
    print("[2/7] Complexity vs Time Reduction...")

    fig, ax = plt.subplots(figsize=(10, 8))

    agents = list(aggregate['by_agent'].keys())

    for agent in agents:
        x_vals = []
        y_vals = []
        labels = []

        for repo in repo_data_list:
            if agent in repo['results']['by_agent']:
                x_vals.append(repo['complexity']['normalized_score'])
                y_vals.append(repo['results']['by_agent'][agent]['time_reduction_percentage'])
                labels.append(repo['name'])

        ax.scatter(x_vals, y_vals, s=200, marker=MARKERS[agent], color=COLORS[agent], alpha=0.7,
                  edgecolors='black', linewidth=2, label=AGENT_DISPLAY[agent])

        for x, y, label in zip(x_vals, y_vals, labels):
            ax.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)

    # Add linear regression
    all_x = [repo['complexity']['normalized_score'] for repo in repo_data_list]
    all_y = [repo['results']['time_reduction_percentage'] for repo in repo_data_list]

    if len(all_x) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(all_x, all_y)
        line_x = np.array([min(all_x), max(all_x)])
        line_y = slope * line_x + intercept
        ax.plot(line_x, line_y, 'k--', alpha=0.5, linewidth=2,
                label=f'Trendline (R²={r_value**2:.3f})')

    ax.set_xlabel('Repository Complexity (normalized 0-100)', fontweight='bold')
    ax.set_ylabel('Time Reduction (%)', fontweight='bold')
    ax.set_title('Repository Complexity vs Time Savings\n(Higher complexity → Greater time savings)',
                 fontweight='bold', pad=20)
    ax.legend(loc='upper left')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim(-5, 105)

    _save_figure(fig, output_dir, 'complexity_vs_time_reduction')


def _generate_repository_comparison(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate bar chart comparing scores across repositories."""
    print("[3/7] Repository Comparison...")

    fig, ax = plt.subplots(figsize=(10, 6))

    repo_names = [repo['name'] for repo in repo_data_list]
    without_rig_scores = [repo['results']['average_score_without_rig'] for repo in repo_data_list]
    with_rig_scores = [repo['results']['average_score_with_rig'] for repo in repo_data_list]
    complexity_levels = [f"{repo['complexity']['level']}\n(complexity: {repo['complexity']['normalized_score']:.0f})"
                        for repo in repo_data_list]

    x = np.arange(len(repo_names))
    width = 0.35

    bars1 = ax.bar(x - width/2, without_rig_scores, width, label='Without RIG',
                   color=COLORS['without_rig'], alpha=0.8)
    bars2 = ax.bar(x + width/2, with_rig_scores, width, label='With RIG',
                   color=COLORS['with_rig'], alpha=0.8)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=9)

    # Add improvement annotations
    for i, repo in enumerate(repo_data_list):
        improvement = repo['results']['score_improvement']
        max_height = max(without_rig_scores[i], with_rig_scores[i])
        ax.text(i, max_height * 1.05, f'+{improvement:.1f}%',
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               color=COLORS['positive'])

    ax.set_xlabel('Repository', fontweight='bold')
    ax.set_ylabel('Average Score (%)', fontweight='bold')
    ax.set_title('RIG Performance Across Repository Complexity Levels', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{name}\n{level}" for name, level in zip(repo_names, complexity_levels)])
    ax.legend(loc='lower right')
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    _save_figure(fig, output_dir, 'repository_comparison_scores')


def _generate_time_savings_cascade(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate cascade chart showing time savings across repositories."""
    print("[4/7] Time Savings Cascade...")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    repo_names = [repo['name'] for repo in repo_data_list]
    time_saved = [repo['results']['time_saved_seconds'] for repo in repo_data_list]
    cumulative_saved = np.cumsum(time_saved)

    x = np.arange(len(repo_names))

    # Bar chart on primary axis
    bars = ax1.bar(x, time_saved, color=COLORS['positive'], alpha=0.8,
                   label='Time Saved (seconds)')

    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s',
                ha='center', va='bottom', fontsize=9)

    ax1.set_xlabel('Repository (ordered by complexity)', fontweight='bold')
    ax1.set_ylabel('Time Saved (seconds)', fontweight='bold', color='black')
    ax1.set_xticks(x)
    ax1.set_xticklabels(repo_names, rotation=15, ha='right')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Cumulative line on secondary axis
    ax2 = ax1.twinx()
    line = ax2.plot(x, cumulative_saved, 'o-', color='darkblue', linewidth=2, markersize=8,
                    label='Cumulative Time Saved')

    # Add cumulative labels
    for i, cum in enumerate(cumulative_saved):
        ax2.text(i, cum, f'{cum:.0f}s',
                ha='center', va='bottom', fontsize=9, color='darkblue', fontweight='bold')

    ax2.set_ylabel('Cumulative Time Saved (seconds)', fontweight='bold', color='darkblue')
    ax2.tick_params(axis='y', labelcolor='darkblue')

    ax1.set_title('Time Saved by RIG Across Repositories', fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    _save_figure(fig, output_dir, 'time_savings_cascade')


def _generate_agent_performance_matrix(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate heatmap showing agent performance across repositories."""
    print("[5/7] Agent Performance Matrix...")

    fig, ax = plt.subplots(figsize=(10, 6))

    agents = list(aggregate['by_agent'].keys())
    repo_names = [repo['name'] for repo in repo_data_list]

    # Build matrix
    matrix = []
    for agent in agents:
        row = []
        for repo in repo_data_list:
            if agent in repo['results']['by_agent']:
                improvement = repo['results']['by_agent'][agent]['score_improvement']
                row.append(improvement)
            else:
                row.append(0)
        matrix.append(row)

    # Create heatmap
    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=-5, vmax=25)

    # Set ticks
    ax.set_xticks(np.arange(len(repo_names)))
    ax.set_yticks(np.arange(len(agents)))
    ax.set_xticklabels(repo_names)
    ax.set_yticklabels([AGENT_DISPLAY[a] for a in agents])

    # Add text annotations
    for i in range(len(agents)):
        for j in range(len(repo_names)):
            text = ax.text(j, i, f'{matrix[i][j]:.1f}%',
                          ha="center", va="center", color="black", fontweight='bold')

    ax.set_xlabel('Repository (complexity level)', fontweight='bold')
    ax.set_ylabel('Agent', fontweight='bold')
    ax.set_title('Agent Performance Across Complexity Levels\n(Score improvement %)',
                 fontweight='bold', pad=20)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Score Improvement (%)', rotation=270, labelpad=20, fontweight='bold')

    _save_figure(fig, output_dir, 'agent_performance_matrix')


def _generate_difficulty_improvement(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate bar chart showing RIG improvement by question difficulty."""
    print("[6/7] Difficulty Improvement...")

    fig, ax = plt.subplots(figsize=(10, 6))

    difficulties = DIFFICULTIES
    improvements = [aggregate['by_difficulty'][d]['avg_improvement'] for d in difficulties]
    question_counts = [aggregate['by_difficulty'][d]['question_count'] for d in difficulties]

    x = np.arange(len(difficulties))
    bars = ax.bar(x, improvements, color=[COLORS['positive'] if imp > 0 else COLORS['negative']
                                          for imp in improvements], alpha=0.8)

    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, question_counts)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}%\n({count} questions)',
               ha='center', va='bottom' if height > 0 else 'top', fontsize=10, fontweight='bold')

    ax.set_xlabel('Question Difficulty', fontweight='bold')
    ax.set_ylabel('Average Improvement (%)', fontweight='bold')
    ax.set_title('RIG Effectiveness by Question Difficulty (Aggregate)', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([DIFFICULTY_DISPLAY[d] for d in difficulties])
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    _save_figure(fig, output_dir, 'difficulty_improvement_aggregate')


def _generate_efficiency_improvement(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate dual-axis chart showing score and efficiency improvements."""
    print("[7/7] Efficiency Improvement...")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    repo_names = [repo['name'] for repo in repo_data_list]
    score_improvements = [repo['results']['score_improvement'] for repo in repo_data_list]
    efficiency_improvements = [repo['results']['efficiency_improvement'] for repo in repo_data_list]

    x = np.arange(len(repo_names))

    # Line 1: Score improvement
    line1 = ax1.plot(x, score_improvements, 'o-', color=COLORS['positive'],
                     linewidth=2, markersize=10, label='Score Improvement')
    ax1.set_xlabel('Repository (ordered by complexity)', fontweight='bold')
    ax1.set_ylabel('Score Improvement (%)', fontweight='bold', color=COLORS['positive'])
    ax1.tick_params(axis='y', labelcolor=COLORS['positive'])
    ax1.set_xticks(x)
    ax1.set_xticklabels(repo_names, rotation=15, ha='right')
    ax1.grid(alpha=0.3, linestyle='--')

    # Add value labels for line 1
    for i, val in enumerate(score_improvements):
        ax1.text(i, val, f'{val:.1f}%', ha='center', va='bottom',
                fontsize=9, color=COLORS['positive'], fontweight='bold')

    # Line 2: Efficiency improvement (secondary axis)
    ax2 = ax1.twinx()
    line2 = ax2.plot(x, efficiency_improvements, 's--', color='darkblue',
                     linewidth=2, markersize=8, label='Efficiency Improvement')
    ax2.set_ylabel('Efficiency Improvement (%)', fontweight='bold', color='darkblue')
    ax2.tick_params(axis='y', labelcolor='darkblue')

    # Add value labels for line 2
    for i, val in enumerate(efficiency_improvements):
        ax2.text(i, val, f'{val:.1f}%', ha='center', va='top',
                fontsize=9, color='darkblue', fontweight='bold')

    ax1.set_title('RIG Impact: Score Improvement vs Efficiency Gain\n(Compounding benefits)',
                  fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    _save_figure(fig, output_dir, 'efficiency_improvement_dual_axis')


def _generate_category_improvement(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path
):
    """Generate grouped bar chart showing category improvements by repository."""
    print("[8/8] Category Improvement Comparison...")

    fig, ax = plt.subplots(figsize=(12, 7))

    # Get common categories
    common_categories = ["build_system", "source_analysis", "testing",
                         "dependency_analysis", "component_identification"]
    category_labels = ["Build\nSystem", "Source\nAnalysis", "Testing",
                      "Dependency\nAnalysis", "Component\nID"]

    # Extract data for each repo
    repo_names = [repo['name'] for repo in repo_data_list]
    n_categories = len(common_categories)
    n_repos = len(repo_names)

    # Build improvement matrix
    improvements_matrix = []
    for repo in repo_data_list:
        repo_improvements = []
        for category in common_categories:
            cat_data = repo["results"]["by_category"].get(category, {})
            improvement = cat_data.get("improvement", 0)
            repo_improvements.append(improvement)
        improvements_matrix.append(repo_improvements)

    # Set up grouped bar positions
    x = np.arange(n_categories)
    width = 0.25  # Width of each bar
    offset = width * (n_repos - 1) / 2

    # Create bars for each repository
    # 8 distinct colorblind-friendly colors for all repositories
    colors_list = [
        '#3498DB',  # Blue
        '#E67E22',  # Orange
        '#27AE60',  # Green
        '#9B59B6',  # Purple
        '#E74C3C',  # Red
        '#1ABC9C',  # Teal
        '#F1C40F',  # Yellow
        '#E91E63',  # Pink
    ]
    for i, (repo_name, improvements) in enumerate(zip(repo_names, improvements_matrix)):
        position = x - offset + i * width
        bars = ax.bar(position, improvements, width, label=repo_name,
                     color=colors_list[i % len(colors_list)], alpha=0.8)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.5:  # Only show label if improvement is significant
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=8)

    ax.set_xlabel('Question Category', fontweight='bold')
    ax.set_ylabel('Improvement with RIG (%)', fontweight='bold')
    ax.set_title('RIG Benefit by Question Category Across Repositories',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(category_labels)
    ax.legend(loc='upper right')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    _save_figure(fig, output_dir, 'category_improvement_comparison')


def _generate_time_vs_score_scatter(
    time_accuracy_analysis: Dict[str, Any],
    output_dir: Path
):
    """Generate scatter plot of time vs score for all agents."""
    print("[9/9] Time vs Score Scatter Plot...")

    fig, ax = plt.subplots(figsize=(12, 8))

    scatter_data = time_accuracy_analysis['scatter_plot_data']

    # Group data by agent
    agents = {}
    for point in scatter_data:
        agent = point['agent']
        if agent not in agents:
            agents[agent] = {'NORIG': None, 'RIG': None}
        agents[agent][point['mode']] = point

    # Plot each agent
    for agent_name in sorted(agents.keys()):
        agent_points = agents[agent_name]

        # Plot NORIG point (circle marker)
        if agent_points['NORIG']:
            p = agent_points['NORIG']
            ax.scatter(p['time_seconds'], p['score'], s=300, marker='o',
                      color=COLORS[agent_name], alpha=0.6, edgecolors='black',
                      linewidth=2, label=f"{AGENT_DISPLAY[agent_name]} (NORIG)")

        # Plot RIG point (triangle marker)
        if agent_points['RIG']:
            p = agent_points['RIG']
            ax.scatter(p['time_seconds'], p['score'], s=300, marker='^',
                      color=COLORS[agent_name], alpha=0.9, edgecolors='black',
                      linewidth=2, label=f"{AGENT_DISPLAY[agent_name]} (RIG)")

        # Draw arrow from NORIG to RIG
        if agent_points['NORIG'] and agent_points['RIG']:
            ax.annotate('', xy=(agent_points['RIG']['time_seconds'], agent_points['RIG']['score']),
                       xytext=(agent_points['NORIG']['time_seconds'], agent_points['NORIG']['score']),
                       arrowprops=dict(arrowstyle='->', color=COLORS[agent_name], lw=1.5, alpha=0.6))

    # Draw diagonal efficiency lines from origin
    max_time = max(p['time_seconds'] for p in scatter_data)
    max_score = max(p['score'] for p in scatter_data)

    # Draw efficiency reference lines
    efficiencies = [0.1, 0.2, 0.3, 0.4, 0.5]
    for eff in efficiencies:
        line_time = max_time * 1.1
        line_score = eff * line_time
        if line_score <= max_score * 1.2:
            ax.plot([0, line_time], [0, line_score], '--', color='gray', alpha=0.3, linewidth=1)
            # Label the efficiency line
            ax.text(line_time * 0.95, line_score * 0.95, f'{eff:.1f} pts/s',
                   fontsize=8, color='gray', alpha=0.7, rotation=np.degrees(np.arctan(eff)))

    # Labels and formatting
    ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Score (points)', fontsize=14, fontweight='bold')
    ax.set_title('Time vs Score Analysis: Agent Performance Comparison\nArrows show NORIG → RIG improvement',
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', framealpha=0.95, fontsize=10, ncol=2)

    # Set axis limits with some padding
    ax.set_xlim(left=0, right=max_time * 1.1)
    ax.set_ylim(bottom=0, top=max_score * 1.1)

    # Add correlation annotation
    corr = time_accuracy_analysis['time_score_correlation']['aggregate']
    ax.text(0.98, 0.02, f"Correlation: r = {corr['pearson_r']:.3f} (p = {corr['p_value']:.4f})",
           transform=ax.transAxes, fontsize=10, ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    _save_figure(fig, output_dir, 'time_vs_score_scatter')


def generate_all_visualizations(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_dir: Path,
    time_accuracy_analysis: Dict[str, Any] = None
):
    """
    Generate all summary visualizations.

    This is the main entry point for visualization generation. It creates
    all 9 aggregate charts showing RIG effectiveness across repositories.

    Args:
        repo_data_list: List of repository data dictionaries
        aggregate: Aggregate analysis dictionary
        output_dir: Directory to save visualizations
        time_accuracy_analysis: Time vs accuracy analysis (optional)
    """
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80 + "\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    # Setup matplotlib style
    setup_plotting_style()

    # Generate all charts
    _generate_complexity_vs_score(repo_data_list, aggregate, output_dir)
    _generate_complexity_vs_time(repo_data_list, aggregate, output_dir)
    _generate_repository_comparison(repo_data_list, aggregate, output_dir)
    _generate_time_savings_cascade(repo_data_list, aggregate, output_dir)
    _generate_agent_performance_matrix(repo_data_list, aggregate, output_dir)
    _generate_difficulty_improvement(repo_data_list, aggregate, output_dir)
    _generate_efficiency_improvement(repo_data_list, aggregate, output_dir)
    _generate_category_improvement(repo_data_list, aggregate, output_dir)

    # Generate time vs accuracy scatter plot if data provided
    if time_accuracy_analysis:
        _generate_time_vs_score_scatter(time_accuracy_analysis, output_dir)
        print(f"\n[OK] All 9 visualizations generated in {output_dir}")
    else:
        print(f"\n[OK] All 8 visualizations generated in {output_dir}")
