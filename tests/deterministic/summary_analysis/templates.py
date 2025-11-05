"""
Text templates for RIG effectiveness summary report.

All report text is defined here as constants to enable easy updates
without modifying the core logic. Templates use {variable} placeholders
for runtime data interpolation.
"""

# ==============================================================================
# MAIN REPORT TITLE
# ==============================================================================

REPORT_TITLE = "# RIG Effectiveness: Cross-Repository Analysis"

# ==============================================================================
# EXECUTIVE SUMMARY SECTION
# ==============================================================================

EXECUTIVE_SUMMARY_HEADER = "## Executive Summary"

EXECUTIVE_SUMMARY_INTRO = """This comprehensive analysis evaluates RIG (Repository Information Generation) effectiveness across {repo_count} repositories of varying complexity. RIG demonstrates **{avg_score_improvement:.1f}% average score improvement** and **{avg_time_reduction:.1f}% time reduction** across all tests.

**Key Finding**: Repository complexity shows a **{correlation_strength}** (R²={r_squared}) with RIG benefit—the more complex the repository, the more valuable RIG becomes."""

REPOSITORIES_HEADER = "### Repositories Analyzed"

REPOSITORY_ENTRY = """#### {name} ({complexity_level} Complexity)

{description}"""

# ==============================================================================
# QUESTION DIFFICULTY DEFINITIONS SECTION
# ==============================================================================

DIFFICULTY_DEFINITIONS_HEADER = "### Question Difficulty Levels"

DIFFICULTY_DEFINITIONS_CONTENT = """This analysis categorizes questions into three difficulty levels based on agent performance patterns:

**EASY** (agents achieve 80-90% accuracy even WITHOUT RIG):
- Questions answerable by simple file inspection
- Examples:
  - "What is the project name?" → Read CMakeLists.txt line 2
  - "How many .cpp files are in src/?" → List directory
- **RIG benefit**: Minimal, mainly convenience

**MEDIUM** (agents achieve 40-60% without RIG, 80-90% WITH RIG):
- Questions where parsing CMake syntax is challenging BUT RIG provides structured answers
- This is where RIG shows maximum value
- Examples:
  - "What source files does hello_world use?" → Without RIG: parse add_executable() syntax; With RIG: direct lookup in components[].source_files
  - "Does hello_world depend on utils?" → Without RIG: parse target_link_libraries(); With RIG: check depends_on_ids
- **RIG benefit**: HUGE - turns hard parsing into direct lookup

**HARD** (agents achieve 20-40% without RIG, 60-80% WITH RIG):
- Questions requiring reasoning/inference even with RIG
- Examples:
  - "In what build order must components be built?" → Even with RIG showing dependencies, need topological sort
  - "If utils fails, what else fails?" → Need reverse dependency analysis
- **RIG benefit**: Helps but still requires reasoning"""

# ==============================================================================
# COMPLEXITY SECTION
# ==============================================================================

COMPLEXITY_SECTION_HEADER = "### Repository Complexity"

COMPLEXITY_EXPLANATION = """Repository complexity is calculated using a weighted formula that considers multiple dimensions of build system complexity:

**Metrics and Weights:**
- **Component count** (weight: ×2): Total number of buildable targets
- **Programming languages** (weight: ×10): Number of distinct languages used
- **External packages** (weight: ×3): Number of external dependencies
- **Max dependency depth** (weight: ×8): Longest chain of component dependencies
- **Aggregator count** (weight: ×5): Number of orchestration targets
- **Cross-language dependencies** (bonus: +15): Presence of cross-language integration

**Formula:**
```
complexity_score = (components×2) + (languages×10) + (packages×3) +
                   (depth×8) + (aggregators×5) + (cross_lang ? 15 : 0)
```

**Normalization:**
```
normalized_score = (raw_score / max_raw_score) × 100
```

This creates a 0-100 scale where the most complex repository scores 100."""

COMPLEXITY_BREAKDOWN_HEADER = "#### Complexity Score Calculations"

COMPLEXITY_BREAKDOWN_ENTRY = """**{repo_name}** ({complexity_level})

```
Components:       {comp_count:2d} × 2  = {comp_score:3d}
Languages:        {lang_count:2d} × 10 = {lang_score:3d}
Packages:         {pkg_count:2d} × 3  = {pkg_score:3d}
Dependency depth: {depth:2d} × 8  = {depth_score:3d}
Aggregators:      {agg_count:2d} × 5  = {agg_score:3d}
Cross-language:   {cross_lang_yes_no:3s}      = {cross_score:3d}
---------------------------------------
Raw score:                     {raw_score:3d}
Normalized: ({raw_score}/{max_score}×100)    = {norm_score:5.1f}
```

**Languages**: {languages}"""

# ==============================================================================
# CORRELATION SECTION
# ==============================================================================

CORRELATION_SECTION_HEADER = "## 1. The Complexity Correlation"

SCORE_CORRELATION_HEADER = "### Score Improvement"

SCORE_CORRELATION_IMAGE = "![Complexity vs Score](complexity_vs_score_improvement.png)"

SCORE_CORRELATION_FINDING = """**Finding**: Repository complexity strongly correlates with RIG benefit (R²={r_squared})

{conclusion}"""

TIME_CORRELATION_HEADER = "### Time Savings"

TIME_CORRELATION_IMAGE = "![Complexity vs Time](complexity_vs_time_reduction.png)"

TIME_CORRELATION_FINDING = """**Finding**: Time savings scale with complexity (R²={r_squared})

{conclusion}"""

# ==============================================================================
# REPOSITORY COMPARISON SECTION
# ==============================================================================

REPO_COMPARISON_HEADER = "## 2. Repository-Level Comparison"

REPO_COMPARISON_IMAGE = "![Repository Comparison](repository_comparison_scores.png)"

PERFORMANCE_TABLE_HEADER = "### Performance by Repository"

PERFORMANCE_TABLE = """| Repository | Complexity | Without RIG | With RIG | Improvement |
|------------|------------|-------------|----------|-------------|"""

PERFORMANCE_TABLE_ROW = "| {name} | {level} ({norm_score:.0f}) | {without_rig:.1f}% | {with_rig:.1f}% | +{improvement:.1f}% |"

TIME_SAVINGS_IMAGE = "![Time Savings](time_savings_cascade.png)"

TIME_TABLE_HEADER = "### Time Performance by Repository"

TIME_TABLE = """| Repository | Time Without RIG | Time With RIG | Time Saved | Reduction |
|------------|------------------|---------------|------------|-----------|"""

TIME_TABLE_ROW = "| {name} | {time_without:.1f}s | {time_with:.1f}s | {time_saved:.1f}s | {reduction:.1f}% |"

# ==============================================================================
# AGENT PERFORMANCE SECTION
# ==============================================================================

AGENT_PERFORMANCE_HEADER = "## 3. Agent Performance Patterns"

AGENT_PERFORMANCE_IMAGE = "![Agent Performance Matrix](agent_performance_matrix.png)"

AGENT_INSIGHTS_HEADER = "**Agent-Specific Insights**:"

AGENT_SECTION_TEMPLATE = """### {agent_name}

- Average score improvement: **{score_improvement:.1f}%**
- Average time reduction: **{time_reduction:.1f}%**
- Baseline (without RIG): {score_without:.1f}%
- With RIG: {score_with:.1f}%"""

# ==============================================================================
# DIFFICULTY ANALYSIS SECTION
# ==============================================================================

DIFFICULTY_HEADER = "## 4. Question Difficulty Analysis"

DIFFICULTY_IMAGE = "![Difficulty Aggregate](difficulty_improvement_aggregate.png)"

DIFFICULTY_INTRO = "RIG effectiveness varies by question difficulty:"

DIFFICULTY_ROW = "- **{difficulty}** ({count} questions): +{improvement:.1f}% average improvement"

# ==============================================================================
# EFFICIENCY ANALYSIS SECTION
# ==============================================================================

EFFICIENCY_HEADER = "## 5. Efficiency Analysis"

EFFICIENCY_IMAGE = "![Efficiency Dual Axis](efficiency_improvement_dual_axis.png)"

EFFICIENCY_INTRO = "RIG provides **compounding benefits**—both improved accuracy AND reduced time:"

EFFICIENCY_TABLE = """| Repository | Score Improvement | Efficiency Improvement | Combined Benefit |
|------------|------------------|----------------------|------------------|"""

EFFICIENCY_TABLE_ROW = "| {name} | +{score:.1f}% | +{efficiency:.1f}% | {combined:.1f} points |"

EFFICIENCY_INTERPRETATION = """**Interpretation**: Higher complexity repositories see compounding returns—agents become both more accurate AND faster with RIG access."""

# ==============================================================================
# CATEGORY ANALYSIS SECTION
# ==============================================================================

CATEGORY_ANALYSIS_HEADER = "## 6. Category-Level Analysis"

CATEGORY_ANALYSIS_INTRO = """Performance breakdown by question category reveals which types of questions benefit most from RIG across all repositories.

The analysis focuses on **5 common categories** shared across all tested repositories:
- **build_system**: CMake project configuration questions
- **source_analysis**: File counting, source file identification
- **testing**: Test frameworks, test definitions
- **dependency_analysis**: Component dependencies, build order
- **component_identification**: Identifying artifacts, component types"""

CATEGORY_ANALYSIS_IMAGE = "![Category Improvement Comparison](category_improvement_comparison.png)"

CATEGORY_TABLE_HEADER = "### Category Performance Summary"

CATEGORY_TABLE = """| Category | Avg Improvement | cmake_hello_world | jni_hello_world | metaffi |
|----------|----------------|-------------------|-----------------|---------|"""

CATEGORY_TABLE_ROW = "| {category} | **+{avg_improvement:.1f}%** | {cmake:.1f}% | {jni:.1f}% | {metaffi:.1f}% |"

CATEGORY_INSIGHTS_HEADER = "### Key Category Insights"

# ==============================================================================
# KEY FINDINGS SECTION
# ==============================================================================

KEY_FINDINGS_HEADER = "## 7. Key Findings"

# Note: Key findings are generated dynamically, so no template needed

# ==============================================================================
# RECOMMENDATIONS SECTION
# ==============================================================================

RECOMMENDATIONS_HEADER = "## 8. Recommendations"

# Note: Recommendations are generated dynamically, so no template needed

# ==============================================================================
# CONCLUSION SECTION
# ==============================================================================

CONCLUSION_HEADER = "## Conclusion"

CONCLUSION_TEXT = """RIG demonstrates clear, measurable value for development agents working with software repositories. The **{correlation_strength}** (R²={r_squared}) between repository complexity and RIG benefit validates the approach as an essential tool for agent-assisted development.

**Key Takeaways:**
1. **Accuracy**: {avg_score_improvement:.1f}% average improvement across all repositories
2. **Speed**: {avg_time_reduction:.1f}% average time reduction
3. **Scalability**: Greater benefit for complex, multi-language repositories
4. **Reliability**: Consistent improvements across all tested agents

RIG should be considered a fundamental component of modern agent-assisted development workflows, particularly for complex, multi-language codebases where its value is most pronounced."""

# ==============================================================================
# REPOSITORY-SPECIFIC ANALYSES SECTION
# ==============================================================================

REPO_ANALYSES_HEADER = "# Repository-Specific Analyses"

REPO_ANALYSES_INTRO = """The following sections provide detailed analysis for each individual repository. These reports include per-agent breakdowns, question-level analysis, and repository-specific insights."""

REPO_ANALYSIS_SECTION_HEADER = "## <a id=\"{repo_id}\"></a>{repo_name}: Detailed Analysis"

# ==============================================================================
# FOOTER
# ==============================================================================

REPORT_FOOTER = """---

*This report was automatically generated on {timestamp}*"""

# ==============================================================================
# HELPER TEXT SNIPPETS
# ==============================================================================

CORRELATION_PERFECT = "perfect correlation"
CORRELATION_STRONG = "strong positive correlation"
CORRELATION_MODERATE = "moderate positive correlation"
CORRELATION_WEAK = "weak correlation"

HORIZONTAL_RULE = "---"
BLANK_LINE = ""
