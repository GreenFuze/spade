"""
Complexity calculation module for RIG effectiveness analysis.

This module handles all complexity-related calculations:
- Repository complexity scoring
- Correlation analysis
- Complexity breakdown formatting

All calculations use weights from config.py to ensure consistency
and avoid hard-coded values.
"""

import statistics
from typing import Dict, List, Any, Tuple

from .config import COMPLEXITY_WEIGHTS, COMPLEXITY_THRESHOLDS
from .templates import (
    CORRELATION_PERFECT,
    CORRELATION_STRONG,
    CORRELATION_MODERATE,
    CORRELATION_WEAK,
)


def calculate_complexity_score(ground_truth: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Calculate repository complexity score from ground truth data.

    All calculations are performed at runtime using data from ground_truth.
    No hard-coded values are used.

    Args:
        ground_truth: Dictionary containing RIG ground truth data

    Returns:
        Tuple of (raw_complexity_score, metrics_dict)

    The metrics_dict contains:
        - component_count: Number of buildable components
        - programming_language_count: Number of distinct languages
        - programming_languages: List of language names
        - external_package_count: Number of external dependencies
        - test_count: Number of test targets
        - max_dependency_depth: Longest dependency chain
        - aggregator_count: Number of aggregator targets
        - has_cross_language_dependencies: Boolean flag
        - parallel_buildable_component_count: Components with no dependencies
    """
    # Extract base data from ground truth
    components = ground_truth.get("components", [])
    tests = ground_truth.get("tests", [])
    external_packages = ground_truth.get("external_packages", [])

    # Build component ID lookup map for dependency resolution
    comp_map = {c.get("id"): c for c in components if c.get("id")}

    # Count unique programming languages
    languages = set()
    for comp in components:
        lang = comp.get("programming_language")
        if lang:
            languages.add(lang)

    # Detect cross-language dependencies
    has_cross_lang_deps = False
    for comp in components:
        comp_lang = comp.get("programming_language")
        depends_on_ids = comp.get("depends_on_ids", [])
        for dep_id in depends_on_ids:
            dep_comp = comp_map.get(dep_id, {})
            dep_lang = dep_comp.get("programming_language")
            if dep_lang and comp_lang and dep_lang != comp_lang:
                has_cross_lang_deps = True
                break
        if has_cross_lang_deps:
            break

    # Calculate maximum dependency depth using recursion
    def get_dependency_depth(comp: Dict, visited: set = None) -> int:
        """Recursively calculate dependency depth for a component."""
        if visited is None:
            visited = set()
        comp_id = comp.get("id")
        if comp_id in visited:
            return 0  # Circular dependency or already visited
        visited.add(comp_id)

        depends_on_ids = comp.get("depends_on_ids", [])
        if not depends_on_ids:
            return 0  # Leaf node

        max_depth = 0
        for dep_id in depends_on_ids:
            dep_comp = comp_map.get(dep_id)
            if dep_comp:
                depth = get_dependency_depth(dep_comp, visited.copy())
                max_depth = max(max_depth, depth)

        return max_depth + 1

    max_depth = 0
    for comp in components:
        depth = get_dependency_depth(comp)
        max_depth = max(max_depth, depth)

    # Count aggregators (interpreted type with multiple dependencies)
    aggregator_count = 0
    for comp in components:
        if comp.get("type") == "interpreted" and len(comp.get("depends_on_ids", [])) > 1:
            aggregator_count += 1

    # Count parallel buildable components (zero inter-component dependencies)
    parallel_buildable = 0
    for comp in components:
        if len(comp.get("depends_on_ids", [])) == 0:
            parallel_buildable += 1

    # Build metrics dictionary
    metrics = {
        "component_count": len(components),
        "programming_language_count": len(languages),
        "programming_languages": sorted(list(languages)),
        "external_package_count": len(external_packages),
        "test_count": len(tests),
        "max_dependency_depth": max_depth,
        "aggregator_count": aggregator_count,
        "has_cross_language_dependencies": has_cross_lang_deps,
        "parallel_buildable_component_count": parallel_buildable,
    }

    # Calculate weighted complexity score using weights from config
    score = (
        metrics["component_count"] * COMPLEXITY_WEIGHTS['component'] +
        metrics["programming_language_count"] * COMPLEXITY_WEIGHTS['language'] +
        metrics["external_package_count"] * COMPLEXITY_WEIGHTS['package'] +
        metrics["max_dependency_depth"] * COMPLEXITY_WEIGHTS['depth'] +
        metrics["aggregator_count"] * COMPLEXITY_WEIGHTS['aggregator'] +
        (COMPLEXITY_WEIGHTS['cross_lang_bonus'] if metrics["has_cross_language_dependencies"] else 0)
    )

    return score, metrics


def get_complexity_level(normalized_score: float) -> str:
    """
    Determine complexity level based on normalized score (0-100 scale).

    Args:
        normalized_score: Normalized complexity score (0-100)

    Returns:
        String: "LOW", "MEDIUM", or "HIGH"

    Thresholds:
        - LOW: normalized_score < COMPLEXITY_THRESHOLDS['low']
        - MEDIUM: COMPLEXITY_THRESHOLDS['low'] <= normalized_score < COMPLEXITY_THRESHOLDS['medium']
        - HIGH: normalized_score >= COMPLEXITY_THRESHOLDS['medium']
    """
    if normalized_score < COMPLEXITY_THRESHOLDS['low']:
        return "LOW"
    elif normalized_score < COMPLEXITY_THRESHOLDS['medium']:
        return "MEDIUM"
    else:
        return "HIGH"


def calculate_pearson_correlation(x_values: List[float], y_values: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x_values: List of x-axis values
        y_values: List of y-axis values

    Returns:
        Pearson correlation coefficient r (-1 to 1)
        R² is calculated as r * r
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0

    n = len(x_values)
    mean_x = statistics.mean(x_values)
    mean_y = statistics.mean(y_values)

    numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))

    sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
    sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)

    denominator = (sum_sq_x * sum_sq_y) ** 0.5

    if denominator == 0:
        return 0.0

    return numerator / denominator


def get_correlation_strength_text(r_squared: float) -> str:
    """
    Get descriptive text for correlation strength based on R² value.

    Args:
        r_squared: R² correlation value (0 to 1)

    Returns:
        String description of correlation strength
    """
    if r_squared > 0.9:
        return CORRELATION_PERFECT
    elif r_squared > 0.7:
        return CORRELATION_STRONG
    elif r_squared > 0.4:
        return CORRELATION_MODERATE
    else:
        return CORRELATION_WEAK


def format_complexity_breakdown(
    repo_name: str,
    complexity_level: str,
    metrics: Dict[str, Any],
    raw_score: int,
    normalized_score: float,
    max_score: int
) -> str:
    """
    Format complexity calculation breakdown for display in report.

    Args:
        repo_name: Repository name
        complexity_level: "LOW", "MEDIUM", or "HIGH"
        metrics: Dictionary of complexity metrics
        raw_score: Raw complexity score
        normalized_score: Normalized score (0-100)
        max_score: Maximum raw score across all repositories

    Returns:
        Formatted string showing step-by-step calculation
    """
    from .templates import COMPLEXITY_BREAKDOWN_ENTRY

    # Calculate individual contributions
    comp_count = metrics["component_count"]
    comp_score = comp_count * COMPLEXITY_WEIGHTS['component']

    lang_count = metrics["programming_language_count"]
    lang_score = lang_count * COMPLEXITY_WEIGHTS['language']

    pkg_count = metrics["external_package_count"]
    pkg_score = pkg_count * COMPLEXITY_WEIGHTS['package']

    depth = metrics["max_dependency_depth"]
    depth_score = depth * COMPLEXITY_WEIGHTS['depth']

    agg_count = metrics["aggregator_count"]
    agg_score = agg_count * COMPLEXITY_WEIGHTS['aggregator']

    cross_lang = metrics["has_cross_language_dependencies"]
    cross_lang_yes_no = "Yes" if cross_lang else "No"
    cross_score = COMPLEXITY_WEIGHTS['cross_lang_bonus'] if cross_lang else 0

    # Format language list
    languages = ", ".join(metrics["programming_languages"])

    # Use template for formatting
    return COMPLEXITY_BREAKDOWN_ENTRY.format(
        repo_name=repo_name,
        complexity_level=complexity_level,
        comp_count=comp_count,
        comp_score=comp_score,
        lang_count=lang_count,
        lang_score=lang_score,
        pkg_count=pkg_count,
        pkg_score=pkg_score,
        depth=depth,
        depth_score=depth_score,
        agg_count=agg_count,
        agg_score=agg_score,
        cross_lang_yes_no=cross_lang_yes_no,
        cross_score=cross_score,
        raw_score=raw_score,
        max_score=max_score,
        norm_score=normalized_score,
        languages=languages,
    )
