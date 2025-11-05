"""
Report generation module for RIG effectiveness summary analysis.

This module handles all markdown report generation with:
- Executive summary with repository descriptions
- Repository complexity breakdown with step-by-step calculations
- Overall analysis sections (correlations, comparisons, insights)
- Embedded repository-specific detailed reports
"""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

from .templates import *
from .complexity import format_complexity_breakdown, get_complexity_level, get_correlation_strength_text
from .config import AGENT_DISPLAY, DIFFICULTIES, DIFFICULTY_DISPLAY


def _read_description(repo_path: Path) -> str:
    """
    Read repository description from description.md file.

    Args:
        repo_path: Path to repository directory

    Returns:
        Description text (without # header)
    """
    desc_file = repo_path / "description.md"
    if not desc_file.exists():
        return "No description available."

    with open(desc_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip the header line (# repo_name) and return the rest
    description_lines = []
    for line in lines:
        if line.strip() and not line.startswith('#'):
            description_lines.append(line.strip())

    return ' '.join(description_lines)


def _read_repo_analysis(repo_path: Path) -> str:
    """
    Read repository-specific analysis markdown.

    Args:
        repo_path: Path to repository directory

    Returns:
        Full analysis markdown content
    """
    analysis_file = repo_path / "analysis_images" / "analysis.md"
    if not analysis_file.exists():
        return f"*Analysis not available for this repository.*"

    with open(analysis_file, 'r', encoding='utf-8') as f:
        content = f.read()

    return content


def _generate_executive_summary(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    script_dir: Path
) -> List[str]:
    """
    Generate executive summary section with repository descriptions.

    Args:
        repo_data_list: List of repository data
        aggregate: Aggregate analysis data
        script_dir: Base script directory

    Returns:
        List of markdown lines
    """
    overall = aggregate['overall']
    score_corr = aggregate['correlations']['complexity_vs_rig_benefit']['score_correlation']
    r_squared = score_corr['r_squared']
    correlation_strength = get_correlation_strength_text(r_squared)

    lines = [
        REPORT_TITLE,
        BLANK_LINE,
        EXECUTIVE_SUMMARY_HEADER,
        BLANK_LINE,
        EXECUTIVE_SUMMARY_INTRO.format(
            repo_count=len(repo_data_list),
            avg_score_improvement=overall['avg_score_improvement'],
            avg_time_reduction=overall['avg_time_reduction_percentage'],
            correlation_strength=correlation_strength,
            r_squared=r_squared
        ),
        BLANK_LINE,
        DIFFICULTY_DEFINITIONS_HEADER,
        BLANK_LINE,
        DIFFICULTY_DEFINITIONS_CONTENT,
        BLANK_LINE,
        REPOSITORIES_HEADER,
        BLANK_LINE,
    ]

    # Add each repository with description
    for repo in repo_data_list:
        repo_path = script_dir / "cmake" / repo['name']
        description = _read_description(repo_path)
        complexity_level = repo['complexity']['level']

        lines.extend([
            REPOSITORY_ENTRY.format(
                name=repo['name'],
                complexity_level=complexity_level,
                description=description
            ),
            BLANK_LINE,
        ])

    return lines


def _generate_complexity_section(
    repo_data_list: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate repository complexity section with step-by-step calculations.

    Args:
        repo_data_list: List of repository data

    Returns:
        List of markdown lines
    """
    lines = [
        COMPLEXITY_SECTION_HEADER,
        BLANK_LINE,
        COMPLEXITY_EXPLANATION,
        BLANK_LINE,
        COMPLEXITY_BREAKDOWN_HEADER,
        BLANK_LINE,
    ]

    # Find max raw score for normalization display
    max_raw_score = max(repo['complexity']['score'] for repo in repo_data_list)

    # Add step-by-step calculation for each repo
    for repo in repo_data_list:
        complexity_level = repo['complexity']['level']
        raw_score = repo['complexity']['score']
        normalized_score = repo['complexity']['normalized_score']
        metrics = repo['complexity']['metrics']

        breakdown = format_complexity_breakdown(
            repo_name=repo['name'],
            complexity_level=complexity_level,
            metrics=metrics,
            raw_score=raw_score,
            normalized_score=normalized_score,
            max_score=max_raw_score
        )

        lines.extend([
            breakdown,
            BLANK_LINE,
        ])

    lines.append(HORIZONTAL_RULE)
    lines.append(BLANK_LINE)

    return lines


def _generate_correlation_section(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate correlation analysis section.

    Args:
        repo_data_list: List of repository data
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    correlations = aggregate['correlations']['complexity_vs_rig_benefit']
    score_corr = correlations['score_correlation']
    time_corr = correlations['time_correlation']

    lines = [
        CORRELATION_SECTION_HEADER,
        BLANK_LINE,
        SCORE_CORRELATION_HEADER,
        BLANK_LINE,
        SCORE_CORRELATION_IMAGE,
        BLANK_LINE,
        SCORE_CORRELATION_FINDING.format(
            r_squared=score_corr['r_squared'],
            conclusion=score_corr['conclusion']
        ),
        BLANK_LINE,
        TIME_CORRELATION_HEADER,
        BLANK_LINE,
        TIME_CORRELATION_IMAGE,
        BLANK_LINE,
        TIME_CORRELATION_FINDING.format(
            r_squared=time_corr['r_squared'],
            conclusion=time_corr['conclusion']
        ),
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ]

    return lines


def _generate_repository_comparison_section(
    repo_data_list: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate repository comparison section with performance tables.

    Args:
        repo_data_list: List of repository data

    Returns:
        List of markdown lines
    """
    lines = [
        REPO_COMPARISON_HEADER,
        BLANK_LINE,
        REPO_COMPARISON_IMAGE,
        BLANK_LINE,
        PERFORMANCE_TABLE_HEADER,
        BLANK_LINE,
        PERFORMANCE_TABLE,
    ]

    # Add performance rows
    for repo in repo_data_list:
        lines.append(
            PERFORMANCE_TABLE_ROW.format(
                name=repo['name'],
                level=repo['complexity']['level'],
                norm_score=repo['complexity']['normalized_score'],
                without_rig=repo['results']['average_score_without_rig'],
                with_rig=repo['results']['average_score_with_rig'],
                improvement=repo['results']['score_improvement']
            )
        )

    lines.extend([
        BLANK_LINE,
        TIME_SAVINGS_IMAGE,
        BLANK_LINE,
        TIME_TABLE_HEADER,
        BLANK_LINE,
        TIME_TABLE,
    ])

    # Add time performance rows
    for repo in repo_data_list:
        lines.append(
            TIME_TABLE_ROW.format(
                name=repo['name'],
                time_without=repo['results']['average_time_without_rig_seconds'],
                time_with=repo['results']['average_time_with_rig_seconds'],
                time_saved=repo['results']['time_saved_seconds'],
                reduction=repo['results']['time_reduction_percentage']
            )
        )

    lines.extend([
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_agent_performance_section(
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate agent performance section.

    Args:
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    lines = [
        AGENT_PERFORMANCE_HEADER,
        BLANK_LINE,
        AGENT_PERFORMANCE_IMAGE,
        BLANK_LINE,
        AGENT_INSIGHTS_HEADER,
        BLANK_LINE,
    ]

    # Add each agent's section
    for agent, data in aggregate['by_agent'].items():
        agent_name = AGENT_DISPLAY.get(agent, agent)
        lines.extend([
            AGENT_SECTION_TEMPLATE.format(
                agent_name=agent_name,
                score_improvement=data['avg_score_improvement'],
                time_reduction=data['avg_time_reduction_percentage'],
                score_without=data['avg_score_without_rig'],
                score_with=data['avg_score_with_rig']
            ),
            BLANK_LINE,
        ])

    lines.extend([
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_difficulty_section(
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate question difficulty analysis section.

    Args:
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    lines = [
        DIFFICULTY_HEADER,
        BLANK_LINE,
        DIFFICULTY_IMAGE,
        BLANK_LINE,
        DIFFICULTY_INTRO,
        BLANK_LINE,
    ]

    # Add each difficulty level
    for difficulty in DIFFICULTIES:
        diff_data = aggregate['by_difficulty'][difficulty]
        lines.append(
            DIFFICULTY_ROW.format(
                difficulty=DIFFICULTY_DISPLAY[difficulty],
                count=diff_data['question_count'],
                improvement=diff_data['avg_improvement']
            )
        )

    lines.extend([
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_efficiency_section(
    repo_data_list: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate efficiency analysis section.

    Args:
        repo_data_list: List of repository data

    Returns:
        List of markdown lines
    """
    lines = [
        EFFICIENCY_HEADER,
        BLANK_LINE,
        EFFICIENCY_IMAGE,
        BLANK_LINE,
        EFFICIENCY_INTRO,
        BLANK_LINE,
        EFFICIENCY_TABLE,
    ]

    # Add efficiency rows
    for repo in repo_data_list:
        combined = repo['results']['score_improvement'] + (repo['results']['efficiency_improvement'] / 10)
        lines.append(
            EFFICIENCY_TABLE_ROW.format(
                name=repo['name'],
                score=repo['results']['score_improvement'],
                efficiency=repo['results']['efficiency_improvement'],
                combined=combined
            )
        )

    lines.extend([
        BLANK_LINE,
        EFFICIENCY_INTERPRETATION,
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_category_analysis_section(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate category-level analysis section.

    Args:
        repo_data_list: List of repository data
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    lines = [
        CATEGORY_ANALYSIS_HEADER,
        BLANK_LINE,
        CATEGORY_ANALYSIS_INTRO,
        BLANK_LINE,
        CATEGORY_ANALYSIS_IMAGE,
        BLANK_LINE,
        CATEGORY_TABLE_HEADER,
        BLANK_LINE,
        CATEGORY_TABLE,
    ]

    # Add category performance rows
    common_categories = ["build_system", "source_analysis", "testing",
                         "dependency_analysis", "component_identification"]
    category_display = {
        "build_system": "Build System",
        "source_analysis": "Source Analysis",
        "testing": "Testing",
        "dependency_analysis": "Dependency Analysis",
        "component_identification": "Component ID",
    }

    for category in common_categories:
        cat_data = aggregate['by_category'].get(category, {})
        avg_improvement = cat_data.get('avg_improvement', 0)

        # Get per-repo improvements
        cmake_improvement = 0
        jni_improvement = 0
        metaffi_improvement = 0

        for repo in repo_data_list:
            repo_cat_data = repo['results']['by_category'].get(category, {})
            improvement = repo_cat_data.get('improvement', 0)

            if repo['name'] == 'cmake_hello_world':
                cmake_improvement = improvement
            elif repo['name'] == 'jni_hello_world':
                jni_improvement = improvement
            elif repo['name'] == 'metaffi':
                metaffi_improvement = improvement

        lines.append(
            CATEGORY_TABLE_ROW.format(
                category=category_display[category],
                avg_improvement=avg_improvement,
                cmake=cmake_improvement,
                jni=jni_improvement,
                metaffi=metaffi_improvement
            )
        )

    lines.extend([
        BLANK_LINE,
        CATEGORY_INSIGHTS_HEADER,
        BLANK_LINE,
    ])

    # Add dynamic insights
    # Find best and worst categories
    category_improvements = [(cat, aggregate['by_category'][cat]['avg_improvement'])
                             for cat in common_categories]
    best_cat = max(category_improvements, key=lambda x: x[1])
    worst_cat = min(category_improvements, key=lambda x: x[1])

    lines.append(f"- **{category_display[best_cat[0]]}** shows the highest average improvement (+{best_cat[1]:.1f}%)")
    lines.append(f"- **{category_display[worst_cat[0]]}** shows the lowest improvement (+{worst_cat[1]:.1f}%)")

    # Find category with highest variance across repos
    for category in common_categories:
        improvements = [repo['results']['by_category'].get(category, {}).get('improvement', 0)
                       for repo in repo_data_list]
        if max(improvements) - min(improvements) > 10:
            lines.append(f"- **{category_display[category]}** shows large variance ({min(improvements):.1f}% to {max(improvements):.1f}%) across repositories")

    lines.extend([
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_key_findings_section(
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate key findings section.

    Args:
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    lines = [
        KEY_FINDINGS_HEADER,
        BLANK_LINE,
    ]

    for finding in aggregate['insights']['key_findings']:
        lines.append(f"- {finding}")

    lines.extend([
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_recommendations_section(
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate recommendations section.

    Args:
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    lines = [
        RECOMMENDATIONS_HEADER,
        BLANK_LINE,
    ]

    for rec in aggregate['insights']['recommendations']:
        lines.append(f"- {rec}")

    lines.extend([
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

    return lines


def _generate_conclusion_section(
    aggregate: Dict[str, Any]
) -> List[str]:
    """
    Generate conclusion section.

    Args:
        aggregate: Aggregate analysis data

    Returns:
        List of markdown lines
    """
    overall = aggregate['overall']
    score_corr = aggregate['correlations']['complexity_vs_rig_benefit']['score_correlation']
    r_squared = score_corr['r_squared']
    correlation_strength = get_correlation_strength_text(r_squared)

    lines = [
        CONCLUSION_HEADER,
        BLANK_LINE,
        CONCLUSION_TEXT.format(
            correlation_strength=correlation_strength,
            r_squared=r_squared,
            avg_score_improvement=overall['avg_score_improvement'],
            avg_time_reduction=overall['avg_time_reduction_percentage']
        ),
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ]

    return lines


def _generate_embedded_reports_section(
    repo_data_list: List[Dict[str, Any]],
    script_dir: Path
) -> List[str]:
    """
    Generate section with embedded repository-specific reports.

    Args:
        repo_data_list: List of repository data
        script_dir: Base script directory

    Returns:
        List of markdown lines
    """
    lines = [
        REPO_ANALYSES_HEADER,
        BLANK_LINE,
        REPO_ANALYSES_INTRO,
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ]

    # Add each repository's detailed analysis
    for repo in repo_data_list:
        repo_id = repo['name'].lower().replace('_', '-')
        repo_path = script_dir / "cmake" / repo['name']
        analysis_content = _read_repo_analysis(repo_path)
        
        # in the analysis_content, adjust image paths if necessary,
        # example of such path is ![Agent Performance Comparison](cmake_hello_world_agent_performance_comparison.png)
        # use a regular expression for "![{some text}]({image_name})" and replace {image_name} with "repo_path/{image_name}"
        import re
        import os
        analysis_content = re.compile(r'!\[(.*?)\]\((.*?)\)').sub(
            lambda m: f'![{m.group(1)}]({Path(os.path.relpath(repo_path/"analysis_images", Path(__file__).parent.parent / "analysis_images")).as_posix() + '/' + m.group(2)})',
            analysis_content
        )
        
        
        lines.extend([
            REPO_ANALYSIS_SECTION_HEADER.format(
                repo_id=repo_id,
                repo_name=repo['name']
            ),
            BLANK_LINE,
            analysis_content,
            BLANK_LINE,
            HORIZONTAL_RULE,
            BLANK_LINE,
        ])

    return lines


def generate_markdown_report(
    repo_data_list: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    output_path: Path,
    script_dir: Path
):
    """
    Generate comprehensive markdown report with all sections.

    This is the main entry point for report generation. It creates a
    complete markdown report including:
    - Executive summary with repository descriptions and difficulty definitions
    - Complexity calculations breakdown
    - Correlation analysis
    - Repository comparisons
    - Agent performance
    - Difficulty analysis
    - Efficiency analysis
    - Category-level analysis
    - Key findings and recommendations
    - Conclusion
    - Embedded repository-specific detailed reports

    Args:
        repo_data_list: List of repository data dictionaries
        aggregate: Aggregate analysis dictionary
        output_path: Path to save markdown file
        script_dir: Base script directory
    """
    print("\n[LOG] Generating markdown report...")

    md_lines = []

    # Generate all sections
    md_lines.extend(_generate_executive_summary(repo_data_list, aggregate, script_dir))
    md_lines.extend(_generate_complexity_section(repo_data_list))
    md_lines.extend(_generate_correlation_section(repo_data_list, aggregate))
    md_lines.extend(_generate_repository_comparison_section(repo_data_list))
    md_lines.extend(_generate_agent_performance_section(aggregate))
    md_lines.extend(_generate_difficulty_section(aggregate))
    md_lines.extend(_generate_efficiency_section(repo_data_list))
    md_lines.extend(_generate_category_analysis_section(repo_data_list, aggregate))
    md_lines.extend(_generate_key_findings_section(aggregate))
    md_lines.extend(_generate_recommendations_section(aggregate))
    md_lines.extend(_generate_conclusion_section(aggregate))
    md_lines.extend(_generate_embedded_reports_section(repo_data_list, script_dir))

    # Add footer
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    md_lines.append(REPORT_FOOTER.format(timestamp=timestamp))

    # Write markdown file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"[OK] Markdown report saved: {output_path}")
