"""
Report generation module for RIG effectiveness summary analysis.

This module handles all markdown report generation with:
- Executive summary with repository descriptions
- Repository complexity breakdown with step-by-step calculations
- Overall analysis sections (correlations, comparisons, insights)
- Embedded repository-specific detailed reports
"""

import statistics
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
from scipy import stats as scipy_stats

from .templates import *
from .complexity import format_complexity_breakdown, get_complexity_level, get_correlation_strength_text
from .config import AGENT_DISPLAY, DIFFICULTIES, DIFFICULTY_DISPLAY, REPOS


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
        raise FileNotFoundError(
            f"description.md not found at: {desc_file}\n"
            f"Every repository must have a description.md file."
        )

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

    Raises:
        FileNotFoundError: If analysis.md does not exist
    """
    analysis_file = repo_path / "analysis_images" / "analysis.md"
    if not analysis_file.exists():
        raise FileNotFoundError(
            f"analysis.md not found at: {analysis_file}\n"
            f"Every repository must have an analysis.md file generated before creating the summary report.\n"
            f"Run the individual repository analysis first."
        )

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
        # Find the repo config entry that matches this name
        repo_config = next((r for r in REPOS if r['name'] == repo['name']), None)
        if repo_config is None:
            raise ValueError(f"Repository '{repo['name']}' not found in REPOS config")
        repo_path = repo_config['path']

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


def _generate_terminology_section() -> List[str]:
    """
    Generate terminology definitions section.

    Returns:
        List of markdown lines
    """
    lines = [
        TERMINOLOGY_HEADER,
        BLANK_LINE,
        TERMINOLOGY_CONTENT,
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ]

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


def _generate_language_comparison_section(
    repo_data_list: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate multi-lingual vs single-language comparison section.

    Args:
        repo_data_list: List of repository data

    Returns:
        List of markdown lines
    """
    from .config import MULTI_LINGUAL_REPOS, SINGLE_LANGUAGE_REPOS

    # Separate repos by language category
    multi_lingual_repos = [r for r in repo_data_list if r['name'] in MULTI_LINGUAL_REPOS]
    single_language_repos = [r for r in repo_data_list if r['name'] in SINGLE_LANGUAGE_REPOS]

    # Calculate averages for multi-lingual
    multi_score_improvements = [r['results']['score_improvement'] for r in multi_lingual_repos]
    multi_time_reductions = [r['results']['time_reduction_percentage'] for r in multi_lingual_repos]
    multi_efficiency_improvements = [r['results']['efficiency_improvement'] for r in multi_lingual_repos]

    multi_avg_score = statistics.mean(multi_score_improvements)
    multi_avg_time = statistics.mean(multi_time_reductions)
    multi_avg_efficiency = statistics.mean(multi_efficiency_improvements)

    # Calculate averages for single-language
    single_score_improvements = [r['results']['score_improvement'] for r in single_language_repos]
    single_time_reductions = [r['results']['time_reduction_percentage'] for r in single_language_repos]
    single_efficiency_improvements = [r['results']['efficiency_improvement'] for r in single_language_repos]

    single_avg_score = statistics.mean(single_score_improvements)
    single_avg_time = statistics.mean(single_time_reductions)
    single_avg_efficiency = statistics.mean(single_efficiency_improvements)

    # Calculate differences
    score_diff = multi_avg_score - single_avg_score
    time_diff = multi_avg_time - single_avg_time
    efficiency_diff = multi_avg_efficiency - single_avg_efficiency

    # Statistical significance tests (t-test)
    score_ttest = scipy_stats.ttest_ind(multi_score_improvements, single_score_improvements)
    time_ttest = scipy_stats.ttest_ind(multi_time_reductions, single_time_reductions)
    efficiency_ttest = scipy_stats.ttest_ind(multi_efficiency_improvements, single_efficiency_improvements)

    def format_significance(p_value):
        if p_value < 0.01:
            return "** (p<0.01)"
        elif p_value < 0.05:
            return "* (p<0.05)"
        else:
            return "n.s."

    # Build markdown
    lines = [
        LANGUAGE_COMPARISON_HEADER,
        BLANK_LINE,
        LANGUAGE_COMPARISON_INTRO.format(
            multi_count=len(multi_lingual_repos),
            multi_repos=", ".join([r['name'] for r in multi_lingual_repos]),
            single_count=len(single_language_repos),
            single_repos=", ".join([r['name'] for r in single_language_repos])
        ),
        BLANK_LINE,
        LANGUAGE_COMPARISON_TABLE_HEADER,
        BLANK_LINE,
        LANGUAGE_COMPARISON_TABLE,
        LANGUAGE_COMPARISON_ROW.format(
            metric="Score Improvement",
            multi_avg=f"{multi_avg_score:.1f}%",
            single_avg=f"{single_avg_score:.1f}%",
            difference=f"{score_diff:+.1f}%",
            significance=format_significance(score_ttest.pvalue)
        ),
        LANGUAGE_COMPARISON_ROW.format(
            metric="Time Reduction",
            multi_avg=f"{multi_avg_time:.1f}%",
            single_avg=f"{single_avg_time:.1f}%",
            difference=f"{time_diff:+.1f}%",
            significance=format_significance(time_ttest.pvalue)
        ),
        LANGUAGE_COMPARISON_ROW.format(
            metric="Efficiency Improvement",
            multi_avg=f"{multi_avg_efficiency:.1f}%",
            single_avg=f"{single_avg_efficiency:.1f}%",
            difference=f"{efficiency_diff:+.1f}%",
            significance=format_significance(efficiency_ttest.pvalue)
        ),
        BLANK_LINE,
    ]

    # Generate conclusion
    if score_diff > 5 and score_ttest.pvalue < 0.05:
        conclusion = "Multi-lingual repositories benefit significantly more from RIG"
        interpretation = f"Multi-lingual repositories show {score_diff:.1f} percentage points higher score improvement on average (statistically significant, p={score_ttest.pvalue:.3f}). This suggests RIG is particularly valuable for complex, multi-language codebases where cross-language understanding is challenging."
    elif abs(score_diff) < 3:
        conclusion = "RIG provides consistent value regardless of language diversity"
        interpretation = f"The difference between multi-lingual and single-language repositories is minimal ({score_diff:.1f} percentage points), suggesting RIG effectiveness is driven more by other complexity factors than language count alone."
    else:
        conclusion = "Language diversity shows moderate impact on RIG effectiveness"
        interpretation = f"Multi-lingual repositories show {score_diff:.1f} percentage points higher score improvement, though statistical significance is limited due to small sample size (p={score_ttest.pvalue:.3f})."

    lines.extend([
        LANGUAGE_COMPARISON_FINDING.format(
            conclusion=conclusion,
            interpretation=interpretation
        ),
        BLANK_LINE,
        HORIZONTAL_RULE,
        BLANK_LINE,
    ])

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

        # Find the repo config entry to get the correct path
        repo_config = next((r for r in REPOS if r['name'] == repo['name']), None)
        if repo_config is None:
            raise ValueError(f"Repository '{repo['name']}' not found in REPOS config")
        repo_path = repo_config['path']

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
    md_lines.extend(_generate_terminology_section())
    md_lines.extend(_generate_correlation_section(repo_data_list, aggregate))
    md_lines.extend(_generate_language_comparison_section(repo_data_list))
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
