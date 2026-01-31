"""
추천 근거 포맷터 - 한국어

한국어로 추천 근거 섹션을 포맷합니다.
"""

from typing import List
from ....data_models import Rationale, AnalysisMetrics
from src.oracle_complexity_analyzer.weights import (
    HIGH_COMPLEXITY_THRESHOLD,
    PLSQL_BASE_SCORES,
    POSTGRESQL_WEIGHTS,
    MYSQL_WEIGHTS,
)
from src.oracle_complexity_analyzer.enums import TargetDatabase, PLSQLObjectType
from .base import (
    get_complexity_level,
    calculate_final_difficulty,
    ORACLE_FEATURE_IMPACT_MAP,
    EXTERNAL_DEPENDENCY_REPLACEMENT_MAP,
)


def format_rationales_ko(
    rationales: List[Rationale],
    metrics: AnalysisMetrics
) -> str:
    """한국어 추천 근거 포맷"""
    sections = []
    sections.append("# 추천 근거\n")
    
    # 섹션 목적 설명
    sections.append("### 이 섹션의 목적\n")
    sections.append("마이그레이션 전략 추천의 **근거가 되는 분석 데이터**를 보여줍니다.")
    sections.append("SQL/PL-SQL 코드의 복잡도를 분석하여 변환 난이도와 예상 작업량을 산정합니다.\n")
    
    # 1. SQL 복잡도 (데이터가 있는 경우만)
    if metrics.avg_sql_complexity and metrics.avg_sql_complexity > 0:
        sections.append(_format_sql_complexity_ko(metrics))
    
    # 2. PL/SQL 복잡도 (데이터가 있는 경우만)
    if metrics.avg_plsql_complexity and metrics.avg_plsql_complexity > 0:
        sections.append(_format_plsql_complexity_ko(metrics))
        sections.append(_format_oracle_features_section_ko(metrics))
    
    # 3. 작업 예상 시간
    sections.append(format_work_estimation_ko(metrics))
    
    # 4. 추가 고려사항
    sections.append(format_additional_considerations_ko())
    
    return "\n".join(sections)


def _format_sql_complexity_ko(metrics: AnalysisMetrics) -> str:
    """SQL 복잡도 섹션 (한국어)"""
    lines = []
    lines.append("## SQL 복잡도\n")
    lines.append("> **SQL이란?** 데이터베이스에서 데이터를 조회, 수정, 삭제하는 명령어입니다.")
    lines.append("> 복잡도가 높을수록 타겟 DB로 변환 시 더 많은 수정이 필요합니다.\n")
    lines.append(f"- **평균 복잡도**: {metrics.avg_sql_complexity:.2f}")
    if metrics.total_sql_count:
        lines.append(f"- **분석 대상**: {metrics.total_sql_count:,}개 SQL")
    if metrics.high_complexity_sql_count:
        lines.append(
            f"- **고복잡도 SQL (7.0 이상)**: {metrics.high_complexity_sql_count:,}개"
        )
    lines.append("")
    lines.append("> **복잡도 산정 공식**: 구조 복잡도 + Oracle 특화 기능 + "
                "함수/표현식 + 데이터 볼륨 + 실행 복잡도 + 변환 난이도")
    lines.append("")
    return "\n".join(lines)


def _format_plsql_complexity_ko(metrics: AnalysisMetrics) -> str:
    """PL/SQL 복잡도 섹션 (한국어)"""
    lines = []
    lines.append("## PL/SQL 복잡도\n")
    
    # PL/SQL 설명 추가
    lines.append("> **PL/SQL이란?** Oracle 데이터베이스에 저장된 **프로그램 코드**입니다.")
    lines.append("> 비즈니스 로직, 데이터 처리 규칙 등이 포함되어 있으며,")
    lines.append("> 마이그레이션 시 타겟 DB 문법으로 **변환이 필요**합니다.\n")
    
    # 오브젝트 타입별 개수 표시
    lines.append(_format_object_type_table_ko(metrics))
    
    # PostgreSQL vs MySQL 비교 테이블
    lines.append(_format_target_comparison_ko(metrics))
    
    lines.append("> **복잡도 산정 공식**: 기본 점수 + 코드 복잡도 + "
                "Oracle 특화 기능 + 비즈니스 로직 + 변환 난이도")
    lines.append("")
    lines.append("> **정규화 공식**: `정규화 점수 = 원점수 / 최대점수 × 10`")
    lines.append(">")
    lines.append("> - PostgreSQL 최대점수: 13.5점, MySQL 최대점수: 18.0점")
    lines.append("> - 정규화를 통해 타겟 DB 간 복잡도를 동일 척도(0~10)로 비교 가능")
    lines.append("> - 예: PostgreSQL 원점수 6.75 → 정규화 5.0, "
                "MySQL 원점수 9.0 → 정규화 5.0 (동일 난이도)")
    lines.append("")
    
    return "\n".join(lines)


def _format_object_type_table_ko(metrics: AnalysisMetrics) -> str:
    """오브젝트 타입별 개수 테이블 (한국어)"""
    lines = []
    
    has_type_counts = any([
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count,
        metrics.awr_trigger_count,
        metrics.awr_type_count
    ])
    
    if not has_type_counts:
        return ""
    
    lines.append("### 분석 대상 오브젝트\n")
    lines.append("| 오브젝트 타입 | 개수 | PostgreSQL 기본점수 | MySQL 기본점수 |")
    lines.append("|--------------|------|-------------------|----------------|")
    
    # 기본 점수 가져오기
    pg_scores = PLSQL_BASE_SCORES[TargetDatabase.POSTGRESQL]
    mysql_scores = PLSQL_BASE_SCORES[TargetDatabase.MYSQL]
    
    if metrics.awr_package_count:
        pg_pkg = pg_scores[PLSQLObjectType.PACKAGE]
        mysql_pkg = mysql_scores[PLSQLObjectType.PACKAGE]
        lines.append(
            f"| 패키지 | {metrics.awr_package_count:,}개 | "
            f"{pg_pkg:.1f} | {mysql_pkg:.1f} |"
        )
    if metrics.awr_procedure_count:
        pg_proc = pg_scores[PLSQLObjectType.PROCEDURE]
        mysql_proc = mysql_scores[PLSQLObjectType.PROCEDURE]
        lines.append(
            f"| 프로시저 | {metrics.awr_procedure_count:,}개 | "
            f"{pg_proc:.1f} | {mysql_proc:.1f} |"
        )
    if metrics.awr_function_count:
        pg_func = pg_scores[PLSQLObjectType.FUNCTION]
        mysql_func = mysql_scores[PLSQLObjectType.FUNCTION]
        lines.append(
            f"| 함수 | {metrics.awr_function_count:,}개 | "
            f"{pg_func:.1f} | {mysql_func:.1f} |"
        )
    if metrics.awr_trigger_count:
        pg_trig = pg_scores[PLSQLObjectType.TRIGGER]
        mysql_trig = mysql_scores[PLSQLObjectType.TRIGGER]
        lines.append(
            f"| 트리거 | {metrics.awr_trigger_count:,}개 | "
            f"{pg_trig:.1f} | {mysql_trig:.1f} |"
        )
    if metrics.awr_type_count:
        pg_type = pg_scores[PLSQLObjectType.PROCEDURE]
        mysql_type = mysql_scores[PLSQLObjectType.PROCEDURE]
        lines.append(
            f"| 타입 | {metrics.awr_type_count:,}개 | "
            f"{pg_type:.1f} | {mysql_type:.1f} |"
        )
    
    total_objects = sum(filter(None, [
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count,
        metrics.awr_trigger_count,
        metrics.awr_type_count
    ]))
    lines.append(f"| **합계** | **{total_objects:,}개** | - | - |")
    lines.append("")
    lines.append(
        "> **기본 점수**: 오브젝트 타입별 최소 복잡도입니다. "
        "실제 복잡도는 코드 분석을 통해 추가됩니다. "
        "MySQL은 PL/SQL 미지원으로 애플리케이션 이관 페널티가 포함되어 점수가 높습니다."
    )
    lines.append("")
    
    return "\n".join(lines)


def _format_target_comparison_ko(metrics: AnalysisMetrics) -> str:
    """타겟 DB별 복잡도 비교 (한국어)"""
    lines = []
    
    has_mysql = (
        metrics.avg_plsql_complexity_mysql is not None and 
        metrics.avg_plsql_complexity_mysql > 0
    )
    
    if has_mysql:
        lines.append("### 타겟 DB별 복잡도 비교\n")
        lines.append("> **왜 두 타겟을 비교하나요?**")
        lines.append("> PostgreSQL과 MySQL은 Oracle 호환성이 다릅니다.")
        lines.append("> 복잡도가 낮은 타겟이 변환 작업이 더 쉽습니다.\n")
        lines.append("| 항목 | PostgreSQL | MySQL |")
        lines.append("|------|------------|-------|")
        
        pg_level = get_complexity_level(metrics.avg_plsql_complexity)
        mysql_complexity = metrics.avg_plsql_complexity_mysql or 0.0
        mysql_level = get_complexity_level(mysql_complexity)
        lines.append(
            f"| 평균 복잡도 | {metrics.avg_plsql_complexity:.2f} ({pg_level}) | "
            f"{mysql_complexity:.2f} ({mysql_level}) |"
        )
        
        if metrics.max_plsql_complexity and metrics.max_plsql_complexity_mysql:
            pg_max_level = get_complexity_level(metrics.max_plsql_complexity)
            mysql_max_level = get_complexity_level(metrics.max_plsql_complexity_mysql)
            lines.append(
                f"| 최대 복잡도 | {metrics.max_plsql_complexity:.2f} ({pg_max_level}) | "
                f"{metrics.max_plsql_complexity_mysql:.2f} ({mysql_max_level}) |"
            )
        
        # 고난이도 개수 비교
        pg_high = metrics.high_complexity_plsql_count or 0
        mysql_high = metrics.high_complexity_plsql_count_mysql or 0
        pg_total = metrics.total_plsql_count or 0
        mysql_total = metrics.total_plsql_count_mysql or 0
        
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
        
        if pg_total > 0 or mysql_total > 0:
            lines.append(
                f"| 고난이도 | {pg_high}개 / {pg_total}개 (≥{pg_threshold}) | "
                f"{mysql_high}개 / {mysql_total}개 (≥{mysql_threshold}) |"
            )
        
        lines.append("")
        
        # 복잡도 차이 분석
        diff = mysql_complexity - metrics.avg_plsql_complexity
        if diff > 0.5:
            lines.append(
                f"> **분석**: MySQL 타겟이 PostgreSQL보다 복잡도가 **{diff:.2f}** 높습니다. "
                "PostgreSQL이 Oracle 호환성이 더 좋아 변환이 용이합니다."
            )
            lines.append("")
            lines.append(
                "> **차이 발생 원인**: MySQL은 PL/SQL을 지원하지 않아 "
                "저장 프로시저를 애플리케이션 코드로 이관해야 합니다. "
                "반면 PostgreSQL의 PL/pgSQL은 Oracle PL/SQL과 문법이 유사하여 "
                "대부분의 코드를 직접 변환할 수 있습니다. "
                "이로 인해 MySQL 변환 시 기본 점수와 애플리케이션 이관 페널티가 추가됩니다."
            )
        elif diff < -0.5:
            lines.append(
                f"> **분석**: PostgreSQL 타겟이 MySQL보다 복잡도가 **{abs(diff):.2f}** 높습니다. "
                "MySQL이 변환에 더 적합할 수 있습니다."
            )
        else:
            lines.append(
                "> **분석**: 두 타겟 DB의 복잡도 차이가 크지 않습니다. "
                "다른 요소(기능 호환성, 운영 경험 등)를 고려하세요."
            )
        lines.append("")
    else:
        # 단일 타겟 (PostgreSQL만)
        complexity_level = get_complexity_level(metrics.avg_plsql_complexity)
        
        lines.append("| 항목 | 값 |")
        lines.append("|------|-----|")
        lines.append(f"| 평균 복잡도 | {metrics.avg_plsql_complexity:.2f} ({complexity_level}) |")
        
        if metrics.max_plsql_complexity:
            max_level = get_complexity_level(metrics.max_plsql_complexity)
            lines.append(f"| 최대 복잡도 | {metrics.max_plsql_complexity:.2f} ({max_level}) |")
        
        if metrics.total_plsql_count:
            lines.append(f"| 분석 대상 | {metrics.total_plsql_count:,}개 오브젝트 |")
        
        if metrics.high_complexity_plsql_count is not None:
            lines.append(
                f"| 고복잡도 (7.0 이상) | {metrics.high_complexity_plsql_count:,}개 |"
            )
        
        lines.append("")
    
    return "\n".join(lines)


def _format_oracle_features_section_ko(metrics: AnalysisMetrics) -> str:
    """Oracle 특화 기능 및 외부 의존성 섹션 (한국어)"""
    lines = []
    
    # Oracle 특화 기능
    oracle_features = metrics.detected_oracle_features_summary
    if oracle_features:
        lines.append("### 감지된 Oracle 특화 기능\n")
        lines.append("> **Oracle 특화 기능이란?** Oracle에서만 지원하는 고유 기능입니다.")
        lines.append("> 타겟 DB에서 동일 기능이 없으면 대체 방법을 찾아야 합니다.")
        lines.append("> 영향도가 높을수록 변환에 더 많은 노력이 필요합니다.\n")
        lines.append("| Oracle 기능 | 사용 횟수 | 변환 영향도 |")
        lines.append("|------------|----------|------------|")
        
        for feature, count in sorted(oracle_features.items(), key=lambda x: -x[1]):
            impact = ORACLE_FEATURE_IMPACT_MAP.get(feature.upper(), '🟠 중간')
            lines.append(f"| {feature} | {count}회 | {impact} |")
        
        lines.append("")
    
    # 외부 의존성
    external_deps = metrics.detected_external_dependencies_summary
    if external_deps:
        lines.append("### 감지된 외부 의존성\n")
        lines.append("> **외부 의존성이란?** Oracle이 제공하는 내장 패키지(DBMS_*, UTL_* 등)입니다.")
        lines.append("> 타겟 DB에서는 다른 방식으로 구현해야 합니다.\n")
        lines.append("| 패키지/함수 | 사용 횟수 | 대체 방법 |")
        lines.append("|------------|----------|----------|")
        
        for dep, count in sorted(external_deps.items(), key=lambda x: -x[1]):
            replacement = EXTERNAL_DEPENDENCY_REPLACEMENT_MAP.get(
                dep.upper(), '개별 검토 필요'
            )
            lines.append(f"| {dep} | {count}회 | {replacement} |")
        
        lines.append("")
    
    # 변환 가이드
    conversion_guide = metrics.conversion_guide
    if conversion_guide:
        lines.append("### 변환 가이드\n")
        lines.append("> **변환 가이드란?** Oracle 기능을 타겟 DB에서 어떻게 대체하는지 안내합니다.")
        lines.append("> 아래 표를 참고하여 변환 작업을 수행합니다.\n")
        lines.append("| Oracle 기능 | PostgreSQL 대체 방법 |")
        lines.append("|------------|---------------------|")
        
        for oracle_feature, replacement in conversion_guide.items():
            lines.append(f"| {oracle_feature} | {replacement} |")
        
        lines.append("")
    
    if not oracle_features and not external_deps and not conversion_guide:
        return ""
    
    return "\n".join(lines)


def format_work_estimation_ko(metrics: AnalysisMetrics) -> str:
    """작업 예상 시간 섹션 (한국어)"""
    lines = []
    lines.append("## 작업 예상 시간\n")
    
    lines.append("> **이 섹션의 목적**: PL/SQL 오브젝트 수와 코드량을 기반으로")
    lines.append("> 마이그레이션 작업에 필요한 **예상 기간**을 산정합니다.")
    lines.append("> AI 도구 활용을 전제로 하며, 실제 기간은 팀 역량에 따라 달라질 수 있습니다.\n")
    
    team_size = 4
    
    total_objects = sum(filter(None, [
        metrics.awr_package_count,
        metrics.awr_procedure_count,
        metrics.awr_function_count
    ])) or metrics.total_plsql_count or 0
    
    total_lines = metrics.awr_plsql_lines or 0
    
    if total_objects == 0 and total_lines == 0:
        lines.append("> PL/SQL 오브젝트 정보가 없어 작업 시간을 산정할 수 없습니다.")
        return "\n".join(lines)
    
    lines.append("### 분석 대상\n")
    lines.append("| 항목 | 값 |")
    lines.append("|------|-----|")
    if total_objects > 0:
        lines.append(f"| PL/SQL 오브젝트 수 | {total_objects:,}개 |")
    if total_lines > 0:
        lines.append(f"| PL/SQL 총 라인 수 | {total_lines:,}줄 |")
    lines.append("")
    
    lines.append(f"### 예상 작업 시간 ({team_size}인 팀 기준)\n")
    lines.append("| 작업 방식 | 예상 기간 | 비고 |")
    lines.append("|----------|----------|------|")
    
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
                f"{ai_days_min:.0f}~{ai_days_max:.0f}일 "
                f"({ai_days_min/20:.1f}~{ai_days_max/20:.1f}개월)"
            )
        else:
            ai_text = f"{ai_days_min:.0f}~{ai_days_max:.0f}일"
        
        lines.append(
            f"| AI 활용 ({team_size}인) | {ai_text} | "
            f"오브젝트당 4시간 × 30~50% |"
        )
    
    lines.append("")
    lines.append(
        f"> **산정 기준**: {team_size}인 팀 전원이 AI 도구(Amazon Q Developer, Bedrock)를 "
        "활용하는 것을 전제로 합니다. AI 미사용 시 약 2~3배 기간이 소요될 수 있습니다."
    )
    lines.append("")
    lines.append(
        "> **참고**: 예상 시간은 코드 복잡도, 팀 숙련도, 테스트 범위에 따라 달라질 수 있습니다."
    )
    
    return "\n".join(lines)


def format_additional_considerations_ko() -> str:
    """추가 고려사항 섹션 (한국어)"""
    lines = []
    lines.append("")
    lines.append("## ⚠️ 추가 고려사항\n")
    lines.append("> **이 섹션의 목적**: DB 분석만으로는 파악할 수 없는 항목들입니다.")
    lines.append("> 마이그레이션 계획 수립 시 **반드시 사전 확인**이 필요합니다.")
    lines.append("> 누락 시 프로젝트 일정과 비용에 큰 영향을 줄 수 있습니다.\n")
    
    lines.append("### 애플리케이션 종속성")
    lines.append("| 확인 항목 | 설명 | 영향도 |")
    lines.append("|----------|------|--------|")
    lines.append("| DB Link 사용 | 외부 DB 연결이 있는 경우 연결 방식 재설계 필요 | 🔴 높음 |")
    lines.append("| Pro*C/SQLJ | 임베디드 SQL 사용 시 애플리케이션 전면 수정 필요 | 🔴 높음 |")
    lines.append("| OCI 직접 호출 | Oracle Call Interface 사용 시 드라이버 교체 필요 | 🟠 중간 |")
    lines.append("| 연결 풀 설정 | 커넥션 풀 라이브러리 및 설정 변경 필요 | 🟢 낮음 |")
    lines.append("| 트랜잭션 관리 | 분산 트랜잭션(XA) 사용 여부 확인 | 🟠 중간 |")
    lines.append("")
    
    lines.append("### 운영 환경")
    lines.append("| 확인 항목 | 설명 | 영향도 |")
    lines.append("|----------|------|--------|")
    lines.append("| 배치 작업 | 스케줄러(DBMS_SCHEDULER, cron) 연동 방식 변경 | 🟠 중간 |")
    lines.append("| 모니터링 도구 | Oracle 전용 모니터링 도구 대체 필요 | 🟢 낮음 |")
    lines.append("| 백업/복구 절차 | RMAN 기반 백업 스크립트 재작성 필요 | 🟠 중간 |")
    lines.append("| HA/DR 구성 | Data Guard → Aurora 복제 방식으로 변경 | 🟠 중간 |")
    lines.append("| 보안 정책 | TDE, VPD 등 Oracle 보안 기능 대체 방안 검토 | 🔴 높음 |")
    lines.append("")
    
    lines.append("### 인력 및 일정")
    lines.append("| 확인 항목 | 설명 | 영향도 |")
    lines.append("|----------|------|--------|")
    lines.append("| 팀 역량 | PostgreSQL/MySQL 경험 수준에 따라 학습 기간 추가 | 🟠 중간 |")
    lines.append("| 테스트 범위 | 회귀 테스트 케이스 수 및 자동화 수준 | 🔴 높음 |")
    lines.append("| 다운타임 허용 | 서비스 중단 가능 시간에 따라 전환 전략 결정 | 🔴 높음 |")
    lines.append("| 롤백 계획 | 전환 실패 시 원복 절차 및 소요 시간 | 🔴 높음 |")
    lines.append("")
    
    lines.append("### 비용 요소")
    lines.append("| 확인 항목 | 설명 |")
    lines.append("|----------|------|")
    lines.append("| 라이선스 비용 | Oracle 라이선스 계약 종료 시점 및 위약금 |")
    lines.append("| 인프라 비용 | AWS 인스턴스, 스토리지, 네트워크 비용 |")
    lines.append("| 인건비 | 내부 인력 투입 또는 외부 컨설팅 비용 |")
    lines.append("| 교육 비용 | 운영팀 대상 신규 DB 교육 |")
    lines.append("")
    
    lines.append("> 💡 **권장사항**: 위 항목들을 체크리스트로 활용하여 "
                "마이그레이션 착수 전 사전 점검을 수행하세요.")
    
    return "\n".join(lines)
