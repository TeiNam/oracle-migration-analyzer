"""
추천 근거 포맷터 - 최종 난이도 판정

최종 난이도 판정 섹션을 포맷합니다.
"""

from ....data_models import AnalysisMetrics
from src.oracle_complexity_analyzer.weights import (
    HIGH_COMPLEXITY_THRESHOLD,
    POSTGRESQL_WEIGHTS,
    MYSQL_WEIGHTS,
)
from src.oracle_complexity_analyzer.enums import TargetDatabase
from .base import calculate_final_difficulty


def format_final_difficulty_section(
    metrics: AnalysisMetrics,
    language: str
) -> str:
    """최종 난이도 판정 섹션 포맷
    
    Args:
        metrics: 분석 메트릭 데이터
        language: 언어 ("ko" 또는 "en")
        
    Returns:
        Markdown 형식 문자열
    """
    if language == "ko":
        return format_final_difficulty_section_ko(metrics)
    return format_final_difficulty_section_en(metrics)


def format_final_difficulty_section_ko(metrics: AnalysisMetrics) -> str:
    """최종 난이도 판정 섹션 (한국어)"""
    lines = []
    lines.append("# 최종 난이도 판정\n")
    
    lines.append("> **이 섹션의 목적**: 여러 분석 지표를 종합하여 마이그레이션의")
    lines.append("> **전체 난이도**를 판정합니다. 점수가 높을수록 변환 작업이 복잡합니다.\n")
    
    # 종합 난이도
    final_difficulty = calculate_final_difficulty(metrics)
    difficulty_text = {
        "low": "낮음 (Low)",
        "medium": "중간 (Medium)",
        "high": "높음 (High)",
        "very_high": "매우 높음 (Very High)"
    }
    lines.append(f"**종합 난이도**: {difficulty_text.get(final_difficulty, final_difficulty)}\n")
    
    # 난이도 점수 산정 기준 테이블
    lines.append(_format_scoring_criteria_ko(metrics))
    
    # 복잡도 점수 산정 기준
    lines.append(_format_complexity_scoring_ko())
    
    # 작업 예상 시간 요약
    lines.append(_format_work_summary_ko(metrics))
    
    # 판정 요약
    lines.append(_format_assessment_summary_ko(metrics))
    
    return "\n".join(lines)


def _format_scoring_criteria_ko(metrics: AnalysisMetrics) -> str:
    """난이도 점수 산정 기준 테이블 (한국어)"""
    lines = []
    lines.append("## 난이도 점수 산정 기준\n")
    lines.append("| 평가 항목 | 기준 | 점수 | 현재 값 | 획득 점수 |")
    lines.append("|----------|------|------|--------|----------|")
    
    total_score = 0
    pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
    
    # 1. PL/SQL 평균 복잡도 (0~3점)
    avg_complexity = metrics.avg_plsql_complexity or 0
    if avg_complexity >= 7.0:
        complexity_score = 3
        complexity_level = "매우 높음 (≥7.0)"
    elif avg_complexity >= 5.0:
        complexity_score = 2
        complexity_level = "높음 (5.0~7.0)"
    elif avg_complexity >= 3.0:
        complexity_score = 1
        complexity_level = "중간 (3.0~5.0)"
    else:
        complexity_score = 0
        complexity_level = "낮음 (<3.0)"
    total_score += complexity_score
    lines.append(
        f"| PL/SQL 평균 복잡도 | <3.0: 0점, 3.0~5.0: 1점, 5.0~7.0: 2점, ≥7.0: 3점 | "
        f"0~3 | {avg_complexity:.2f} ({complexity_level}) | {complexity_score}점 |"
    )
    
    # 2. PL/SQL 코드량 (0~3점)
    plsql_lines = metrics.awr_plsql_lines or 0
    if plsql_lines >= 100000:
        lines_score = 3
        lines_level = "매우 많음 (≥100K)"
    elif plsql_lines >= 50000:
        lines_score = 2
        lines_level = "많음 (50K~100K)"
    elif plsql_lines >= 10000:
        lines_score = 1
        lines_level = "중간 (10K~50K)"
    else:
        lines_score = 0
        lines_level = "적음 (<10K)"
    total_score += lines_score
    lines.append(
        f"| PL/SQL 코드량 | <10K: 0점, 10K~50K: 1점, 50K~100K: 2점, ≥100K: 3점 | "
        f"0~3 | {plsql_lines:,}줄 ({lines_level}) | {lines_score}점 |"
    )
    
    # 3. 고난이도 오브젝트 비율 (0~2점)
    high_count = metrics.high_complexity_plsql_count or 0
    total_count = metrics.total_plsql_count or 0
    ratio = (high_count / total_count * 100) if total_count > 0 else 0
    
    if ratio >= 30:
        ratio_score = 2
        ratio_level = "높음 (≥30%)"
    elif ratio >= 10:
        ratio_score = 1
        ratio_level = "중간 (10~30%)"
    else:
        ratio_score = 0
        ratio_level = "낮음 (<10%)"
    total_score += ratio_score
    lines.append(
        f"| 고난이도 비율 (≥{pg_threshold}) | <10%: 0점, 10~30%: 1점, ≥30%: 2점 | "
        f"0~2 | {high_count}/{total_count}개 ({ratio:.1f}%) | {ratio_score}점 |"
    )
    
    # 4. 고난이도 오브젝트 절대 개수 (0~3점)
    high_count_total = (
        (metrics.high_complexity_plsql_count or 0) + 
        (metrics.high_complexity_sql_count or 0)
    )
    if high_count_total >= 100:
        count_score = 3
        count_level = "매우 많음 (≥100개)"
    elif high_count_total >= 50:
        count_score = 2
        count_level = "많음 (50~100개)"
    elif high_count_total >= 20:
        count_score = 1
        count_level = "중간 (20~50개)"
    else:
        count_score = 0
        count_level = "적음 (<20개)"
    total_score += count_score
    lines.append(
        f"| 고난이도 절대 개수 | <20: 0점, 20~50: 1점, 50~100: 2점, ≥100: 3점 | "
        f"0~3 | {high_count_total:,}개 ({count_level}) | {count_score}점 |"
    )
    
    # 5. 패키지 개수 (0~2점)
    pkg_count = metrics.awr_package_count or 0
    if pkg_count >= 100:
        pkg_score = 2
        pkg_level = "많음 (≥100)"
    elif pkg_count >= 50:
        pkg_score = 1
        pkg_level = "중간 (50~100)"
    else:
        pkg_score = 0
        pkg_level = "적음 (<50)"
    total_score += pkg_score
    lines.append(
        f"| 패키지 개수 | <50: 0점, 50~100: 1점, ≥100: 2점 | "
        f"0~2 | {pkg_count:,}개 ({pkg_level}) | {pkg_score}점 |"
    )
    
    lines.append(f"| **합계** | - | **0~13** | - | **{total_score}점** |")
    lines.append("")
    lines.append("> **난이도 등급 기준**: 0~2점 낮음, 3~5점 중간, 6~8점 높음, 9점 이상 매우 높음")
    lines.append("")
    
    return "\n".join(lines)


def _format_complexity_scoring_ko() -> str:
    """복잡도 점수 산정 기준 (한국어)"""
    lines = []
    lines.append("## 복잡도 점수 산정 기준\n")
    lines.append("> **복잡도 점수란?** 코드 변환 난이도를 0~10 척도로 수치화한 것입니다.")
    lines.append("> 점수가 높을수록 변환에 더 많은 노력이 필요합니다.\n")
    
    lines.append("### PostgreSQL 타겟\n")
    lines.append("| 항목 | 최대 점수 | 설명 |")
    lines.append("|------|----------|------|")
    lines.append(f"| 구조적 복잡도 | {POSTGRESQL_WEIGHTS.max_structural} | JOIN, 서브쿼리, CTE 등 |")
    lines.append("| Oracle 특화 기능 | 3.0 | CONNECT BY, ROWNUM 등 |")
    lines.append("| 함수/표현식 | 2.0 | 분석 함수, 변환 함수 등 |")
    lines.append(
        f"| 데이터 볼륨 | {max(POSTGRESQL_WEIGHTS.data_volume_scores.values())} | 쿼리 길이 기반 |"
    )
    lines.append("| 실행 복잡도 | 1.0 | ORDER BY, GROUP BY 등 |")
    lines.append("| 변환 난이도 | 4.5 | 타겟 DB 미지원 기능 |")
    lines.append(f"| **최대 총점** | **{POSTGRESQL_WEIGHTS.max_total_score}** | - |")
    lines.append("")
    
    lines.append("### MySQL 타겟\n")
    lines.append("| 항목 | 최대 점수 | 설명 |")
    lines.append("|------|----------|------|")
    lines.append(f"| 구조적 복잡도 | {MYSQL_WEIGHTS.max_structural} | JOIN, 서브쿼리, CTE 등 |")
    lines.append("| Oracle 특화 기능 | 3.0 | CONNECT BY, ROWNUM 등 |")
    lines.append("| 함수/표현식 | 2.5 | 분석 함수, 변환 함수 등 |")
    lines.append(
        f"| 데이터 볼륨 | {max(MYSQL_WEIGHTS.data_volume_scores.values())} | 쿼리 길이 기반 |"
    )
    lines.append("| 실행 복잡도 | 2.5 | ORDER BY, GROUP BY 등 |")
    lines.append("| 변환 난이도 | 4.5 | 타겟 DB 미지원 기능 |")
    lines.append(f"| **최대 총점** | **{MYSQL_WEIGHTS.max_total_score}** | - |")
    lines.append("")
    
    pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
    mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
    lines.append(
        f"> **고난이도 임계값**: PostgreSQL ≥{pg_threshold} (최대점수의 37%), "
        f"MySQL ≥{mysql_threshold} (최대점수의 39%)"
    )
    lines.append("")
    
    return "\n".join(lines)


def _format_work_summary_ko(metrics: AnalysisMetrics) -> str:
    """작업 예상 시간 요약 (한국어)"""
    lines = []
    lines.append("## 예상 작업 기간 요약\n")
    
    total_objects = sum(filter(None, [
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count
    ])) or metrics.total_plsql_count or 0
    
    if total_objects > 0:
        team_size = 4
        total_hours_single = total_objects * 4
        ai_hours_team_min = (total_hours_single * 0.3) / team_size
        ai_hours_team_max = (total_hours_single * 0.5) / team_size
        ai_days_min = ai_hours_team_min / 8
        ai_days_max = ai_hours_team_max / 8
        
        lines.append("| 항목 | 값 |")
        lines.append("|------|-----|")
        lines.append(f"| 변환 대상 오브젝트 | {total_objects:,}개 |")
        lines.append(f"| 예상 기간 (4인, AI 활용) | {ai_days_min:.0f}~{ai_days_max:.0f}일 |")
        if ai_days_max >= 20:
            lines.append(f"| 예상 기간 (월 환산) | {ai_days_min/20:.1f}~{ai_days_max/20:.1f}개월 |")
        lines.append("")
    
    return "\n".join(lines)


def _format_assessment_summary_ko(metrics: AnalysisMetrics) -> str:
    """판정 요약 (한국어)"""
    lines = []
    lines.append("## 판정 요약\n")
    
    summary_items = []
    pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
    
    avg_complexity = metrics.avg_plsql_complexity or 0
    plsql_lines = metrics.awr_plsql_lines or 0
    high_count = metrics.high_complexity_plsql_count or 0
    pkg_count = metrics.awr_package_count or 0
    
    # 복잡도 기반 판정
    if avg_complexity < 3.0:
        summary_items.append("✅ PL/SQL 평균 복잡도가 낮아 변환이 용이함")
    elif avg_complexity < 5.0:
        summary_items.append("🟡 PL/SQL 평균 복잡도가 중간 수준")
    else:
        summary_items.append("⚠️ PL/SQL 평균 복잡도가 높아 변환에 주의 필요")
    
    # 코드량 기반 판정
    if plsql_lines >= 50000:
        summary_items.append(f"⚠️ PL/SQL 코드량이 많음 ({plsql_lines:,}줄)")
    
    # 고난이도 오브젝트 기반 판정
    if high_count > 0:
        summary_items.append(f"⚠️ 고난이도 오브젝트 {high_count}개 존재 (복잡도 ≥{pg_threshold})")
    else:
        summary_items.append(f"✅ 고난이도 오브젝트 없음 (복잡도 ≥{pg_threshold})")
    
    # 패키지 기반 판정
    if pkg_count >= 100:
        summary_items.append(f"⚠️ 패키지 {pkg_count:,}개: 변환 난이도가 가장 높은 오브젝트")
    elif pkg_count >= 50:
        summary_items.append(f"🟡 패키지 {pkg_count:,}개: 상당한 변환 작업 필요")
    
    for item in summary_items:
        lines.append(f"- {item}")
    
    return "\n".join(lines)


def format_final_difficulty_section_en(metrics: AnalysisMetrics) -> str:
    """최종 난이도 판정 섹션 (영어)"""
    lines = []
    lines.append("# Final Difficulty Assessment\n")
    
    # 종합 난이도
    final_difficulty = calculate_final_difficulty(metrics)
    difficulty_text = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "very_high": "Very High"
    }
    lines.append(f"**Overall Difficulty**: {difficulty_text.get(final_difficulty, final_difficulty)}\n")
    
    # 난이도 점수 산정 기준 테이블
    lines.append(_format_scoring_criteria_en(metrics))
    
    return "\n".join(lines)


def _format_scoring_criteria_en(metrics: AnalysisMetrics) -> str:
    """난이도 점수 산정 기준 테이블 (영어)"""
    lines = []
    lines.append("## Difficulty Scoring Criteria\n")
    lines.append("| Evaluation Item | Criteria | Score | Current Value | Points |")
    lines.append("|-----------------|----------|-------|---------------|--------|")
    
    total_score = 0
    pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
    
    # 1. PL/SQL 평균 복잡도
    avg_complexity = metrics.avg_plsql_complexity or 0
    if avg_complexity >= 7.0:
        complexity_score = 3
        complexity_level = "Very High (≥7.0)"
    elif avg_complexity >= 5.0:
        complexity_score = 2
        complexity_level = "High (5.0~7.0)"
    elif avg_complexity >= 3.0:
        complexity_score = 1
        complexity_level = "Medium (3.0~5.0)"
    else:
        complexity_score = 0
        complexity_level = "Low (<3.0)"
    total_score += complexity_score
    lines.append(
        f"| PL/SQL Avg Complexity | <3.0: 0, 3.0~5.0: 1, 5.0~7.0: 2, ≥7.0: 3 | "
        f"0~3 | {avg_complexity:.2f} ({complexity_level}) | {complexity_score} |"
    )
    
    # 2. PL/SQL 코드량
    plsql_lines = metrics.awr_plsql_lines or 0
    if plsql_lines >= 100000:
        lines_score = 3
        lines_level = "Very Large (≥100K)"
    elif plsql_lines >= 50000:
        lines_score = 2
        lines_level = "Large (50K~100K)"
    elif plsql_lines >= 10000:
        lines_score = 1
        lines_level = "Medium (10K~50K)"
    else:
        lines_score = 0
        lines_level = "Small (<10K)"
    total_score += lines_score
    lines.append(
        f"| PL/SQL Lines | <10K: 0, 10K~50K: 1, 50K~100K: 2, ≥100K: 3 | "
        f"0~3 | {plsql_lines:,} ({lines_level}) | {lines_score} |"
    )
    
    # 3. 고난이도 오브젝트 비율
    high_count = metrics.high_complexity_plsql_count or 0
    total_count = metrics.total_plsql_count or 0
    ratio = (high_count / total_count * 100) if total_count > 0 else 0
    
    if ratio >= 30:
        ratio_score = 2
        ratio_level = "High (≥30%)"
    elif ratio >= 10:
        ratio_score = 1
        ratio_level = "Medium (10~30%)"
    else:
        ratio_score = 0
        ratio_level = "Low (<10%)"
    total_score += ratio_score
    lines.append(
        f"| High Complexity Ratio (≥{pg_threshold}) | <10%: 0, 10~30%: 1, ≥30%: 2 | "
        f"0~2 | {high_count}/{total_count} ({ratio:.1f}%) | {ratio_score} |"
    )
    
    # 4. 패키지 개수
    pkg_count = metrics.awr_package_count or 0
    if pkg_count >= 100:
        pkg_score = 2
        pkg_level = "Many (≥100)"
    elif pkg_count >= 50:
        pkg_score = 1
        pkg_level = "Medium (50~100)"
    else:
        pkg_score = 0
        pkg_level = "Few (<50)"
    total_score += pkg_score
    lines.append(
        f"| Package Count | <50: 0, 50~100: 1, ≥100: 2 | "
        f"0~2 | {pkg_count:,} ({pkg_level}) | {pkg_score} |"
    )
    
    lines.append(f"| **Total** | - | **0~10** | - | **{total_score}** |")
    lines.append("")
    lines.append("> **Difficulty Levels**: 0~2 Low, 3~5 Medium, 6~7 High, 8+ Very High")
    
    return "\n".join(lines)
