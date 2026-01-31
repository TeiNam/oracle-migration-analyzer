"""
추천 근거 포맷터 - 영어

영어로 추천 근거 섹션을 포맷합니다.
"""

from typing import List
from ....data_models import Rationale, AnalysisMetrics
from .base import get_complexity_level_en, calculate_final_difficulty


def format_rationales_en(
    rationales: List[Rationale],
    metrics: AnalysisMetrics
) -> str:
    """영어 추천 근거 포맷"""
    sections = []
    sections.append("# Rationale\n")
    
    # 1. SQL Complexity
    if metrics.avg_sql_complexity and metrics.avg_sql_complexity > 0:
        sections.append("## SQL Complexity\n")
        sections.append(f"- **Average Complexity**: {metrics.avg_sql_complexity:.2f}")
        if metrics.total_sql_count:
            sections.append(f"- **Analyzed**: {metrics.total_sql_count:,} SQLs")
        if metrics.high_complexity_sql_count:
            sections.append(
                f"- **High Complexity (≥7.0)**: {metrics.high_complexity_sql_count:,}"
            )
        sections.append("")
        sections.append("> **Formula**: Structural + Oracle Features + "
                      "Functions + Data Volume + Execution + Conversion")
        sections.append("")
    
    # 2. PL/SQL Complexity
    if metrics.avg_plsql_complexity and metrics.avg_plsql_complexity > 0:
        sections.append(_format_plsql_complexity_en(metrics))
    
    # 3. DBCSI Report Results
    has_dbcsi = any([
        metrics.awr_plsql_lines,
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count
    ])
    
    if has_dbcsi:
        sections.append("## DBCSI Report Results\n")
        sections.append("| Item | Value |")
        sections.append("|------|-------|")
        
        if metrics.awr_plsql_lines:
            sections.append(f"| Total PL/SQL Lines | {metrics.awr_plsql_lines:,} |")
        
        total_objects = sum(filter(None, [
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count
        ]))
        if total_objects > 0:
            sections.append(f"| PL/SQL Objects | {total_objects:,} |")
        
        sections.append("")
    
    # 4. Final Difficulty
    sections.append("## Final Difficulty Assessment\n")
    
    final_difficulty = calculate_final_difficulty(metrics)
    difficulty_text = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "very_high": "Very High"
    }
    
    sections.append(
        f"**Overall Difficulty**: {difficulty_text.get(final_difficulty, final_difficulty)}\n"
    )
    
    # 5. Work Estimation
    sections.append(format_work_estimation_en(metrics))
    
    return "\n".join(sections)


def _format_plsql_complexity_en(metrics: AnalysisMetrics) -> str:
    """PL/SQL 복잡도 섹션 (영어)"""
    lines = []
    lines.append("## PL/SQL Complexity\n")
    
    # PostgreSQL vs MySQL comparison
    has_mysql = (
        metrics.avg_plsql_complexity_mysql is not None and 
        metrics.avg_plsql_complexity_mysql > 0
    )
    
    if has_mysql:
        lines.append("### Target DB Complexity Comparison\n")
        lines.append("| Item | PostgreSQL | MySQL |")
        lines.append("|------|------------|-------|")
        
        pg_level = get_complexity_level_en(metrics.avg_plsql_complexity)
        mysql_complexity = metrics.avg_plsql_complexity_mysql or 0.0
        mysql_level = get_complexity_level_en(mysql_complexity)
        lines.append(
            f"| Average Complexity | {metrics.avg_plsql_complexity:.2f} ({pg_level}) | "
            f"{mysql_complexity:.2f} ({mysql_level}) |"
        )
        
        if metrics.max_plsql_complexity and metrics.max_plsql_complexity_mysql:
            pg_max_level = get_complexity_level_en(metrics.max_plsql_complexity)
            mysql_max_level = get_complexity_level_en(metrics.max_plsql_complexity_mysql)
            lines.append(
                f"| Max Complexity | {metrics.max_plsql_complexity:.2f} ({pg_max_level}) | "
                f"{metrics.max_plsql_complexity_mysql:.2f} ({mysql_max_level}) |"
            )
        
        lines.append("")
        
        # Complexity difference analysis
        diff = mysql_complexity - metrics.avg_plsql_complexity
        if diff > 0.5:
            lines.append(
                f"> **Analysis**: MySQL target is **{diff:.2f}** more complex than PostgreSQL. "
                "PostgreSQL has better Oracle compatibility for easier conversion."
            )
        elif diff < -0.5:
            lines.append(
                f"> **Analysis**: PostgreSQL target is **{abs(diff):.2f}** more complex than MySQL. "
                "MySQL may be more suitable for conversion."
            )
        else:
            lines.append(
                "> **Analysis**: Complexity difference between targets is minimal. "
                "Consider other factors (feature compatibility, operational experience)."
            )
        lines.append("")
    else:
        complexity_level = get_complexity_level_en(metrics.avg_plsql_complexity)
        
        lines.append("| Item | Value |")
        lines.append("|------|-------|")
        lines.append(
            f"| Average Complexity | {metrics.avg_plsql_complexity:.2f} ({complexity_level}) |"
        )
        
        if metrics.max_plsql_complexity:
            max_level = get_complexity_level_en(metrics.max_plsql_complexity)
            lines.append(f"| Max Complexity | {metrics.max_plsql_complexity:.2f} ({max_level}) |")
        
        if metrics.total_plsql_count:
            lines.append(f"| Analyzed Objects | {metrics.total_plsql_count:,} |")
        
        if metrics.high_complexity_plsql_count is not None:
            lines.append(
                f"| High Complexity (≥7.0) | {metrics.high_complexity_plsql_count:,} |"
            )
        
        lines.append("")
    
    lines.append("> **Formula**: Base + Code Complexity + "
                "Oracle Features + Business Logic + Conversion")
    lines.append("")
    
    return "\n".join(lines)


def format_work_estimation_en(metrics: AnalysisMetrics) -> str:
    """작업 예상 시간 섹션 (영어)"""
    lines = []
    lines.append("## Work Estimation\n")
    
    team_size = 4
    
    total_objects = sum(filter(None, [
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count
    ])) or metrics.total_plsql_count or 0
    
    total_lines = metrics.awr_plsql_lines or 0
    
    if total_objects == 0 and total_lines == 0:
        lines.append("> No PL/SQL object information available for estimation.")
        return "\n".join(lines)
    
    lines.append("### Analysis Target\n")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    if total_objects > 0:
        lines.append(f"| PL/SQL Objects | {total_objects:,} |")
    if total_lines > 0:
        lines.append(f"| Total PL/SQL Lines | {total_lines:,} |")
    lines.append("")
    
    lines.append(f"### Estimated Work Time ({team_size}-person team)\n")
    lines.append("| Approach | Estimated Duration | Notes |")
    lines.append("|----------|-------------------|-------|")
    
    total_hours_single = total_objects * 4 if total_objects > 0 else 0
    ai_hours_single_min = total_hours_single * 0.3
    ai_hours_single_max = total_hours_single * 0.5
    
    if total_hours_single > 0:
        ai_hours_team_min = ai_hours_single_min / team_size
        ai_hours_team_max = ai_hours_single_max / team_size
        ai_days_min = ai_hours_team_min / 8
        ai_days_max = ai_hours_team_max / 8
        
        if ai_days_max >= 20:
            ai_text = (
                f"{ai_days_min:.0f}~{ai_days_max:.0f} days "
                f"({ai_days_min/20:.1f}~{ai_days_max/20:.1f} months)"
            )
        else:
            ai_text = f"{ai_days_min:.0f}~{ai_days_max:.0f} days"
        
        lines.append(
            f"| AI-Assisted ({team_size}p) | {ai_text} | "
            f"4h/object × 30~50% |"
        )
    
    lines.append("")
    lines.append(
        f"> **Basis**: Assumes all {team_size} team members use AI tools "
        "(Amazon Q Developer, Bedrock). Without AI, expect 2~3x longer duration."
    )
    lines.append("")
    lines.append(
        "> **Note**: Estimates vary based on code complexity, team expertise, "
        "and test coverage."
    )
    
    return "\n".join(lines)
