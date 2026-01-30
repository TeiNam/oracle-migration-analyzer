"""
Markdown 추천 근거 포맷터

추천 근거 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List, Optional
from ...data_models import Rationale, AnalysisMetrics
from src.oracle_complexity_analyzer.weights import (
    HIGH_COMPLEXITY_THRESHOLD,
    PLSQL_BASE_SCORES
)
from src.oracle_complexity_analyzer.enums import TargetDatabase, PLSQLObjectType


class RationaleFormatterMixin:
    """추천 근거 포맷터 믹스인"""
    
    @staticmethod
    def _format_rationales(
        rationales: List[Rationale],
        metrics: AnalysisMetrics,
        language: str
    ) -> str:
        """추천 근거 섹션 포맷 (새 양식)
        
        Args:
            rationales: 추천 근거 리스트
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return RationaleFormatterMixin._format_rationales_ko(rationales, metrics)
        return RationaleFormatterMixin._format_rationales_en(rationales, metrics)
    
    @staticmethod
    def _format_rationales_ko(
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
            sections.append("## SQL 복잡도\n")
            sections.append("> **SQL이란?** 데이터베이스에서 데이터를 조회, 수정, 삭제하는 명령어입니다.")
            sections.append("> 복잡도가 높을수록 타겟 DB로 변환 시 더 많은 수정이 필요합니다.\n")
            sections.append(f"- **평균 복잡도**: {metrics.avg_sql_complexity:.2f}")
            if metrics.total_sql_count:
                sections.append(f"- **분석 대상**: {metrics.total_sql_count:,}개 SQL")
            if metrics.high_complexity_sql_count:
                sections.append(
                    f"- **고복잡도 SQL (7.0 이상)**: {metrics.high_complexity_sql_count:,}개"
                )
            sections.append("")
            sections.append("> **복잡도 산정 공식**: 구조 복잡도 + Oracle 특화 기능 + "
                          "함수/표현식 + 데이터 볼륨 + 실행 복잡도 + 변환 난이도")
            sections.append("")
        
        # 2. PL/SQL 복잡도 (데이터가 있는 경우만)
        if metrics.avg_plsql_complexity and metrics.avg_plsql_complexity > 0:
            sections.append("## PL/SQL 복잡도\n")
            
            # PL/SQL 설명 추가
            sections.append("> **PL/SQL이란?** Oracle 데이터베이스에 저장된 **프로그램 코드**입니다.")
            sections.append("> 비즈니스 로직, 데이터 처리 규칙 등이 포함되어 있으며,")
            sections.append("> 마이그레이션 시 타겟 DB 문법으로 **변환이 필요**합니다.\n")
            
            # 오브젝트 타입별 개수 표시
            has_type_counts = any([
                metrics.awr_package_count,
                metrics.awr_procedure_count,
                metrics.awr_function_count,
                metrics.awr_trigger_count,
                metrics.awr_type_count
            ])
            
            if has_type_counts:
                sections.append("### 분석 대상 오브젝트\n")
                sections.append("| 오브젝트 타입 | 개수 | PostgreSQL 기본점수 | MySQL 기본점수 |")
                sections.append("|--------------|------|-------------------|----------------|")
                
                # 기본 점수 가져오기
                pg_scores = PLSQL_BASE_SCORES[TargetDatabase.POSTGRESQL]
                mysql_scores = PLSQL_BASE_SCORES[TargetDatabase.MYSQL]
                
                if metrics.awr_package_count:
                    pg_pkg = pg_scores[PLSQLObjectType.PACKAGE]
                    mysql_pkg = mysql_scores[PLSQLObjectType.PACKAGE]
                    sections.append(
                        f"| 패키지 | {metrics.awr_package_count:,}개 | "
                        f"{pg_pkg:.1f} | {mysql_pkg:.1f} |"
                    )
                if metrics.awr_procedure_count:
                    pg_proc = pg_scores[PLSQLObjectType.PROCEDURE]
                    mysql_proc = mysql_scores[PLSQLObjectType.PROCEDURE]
                    sections.append(
                        f"| 프로시저 | {metrics.awr_procedure_count:,}개 | "
                        f"{pg_proc:.1f} | {mysql_proc:.1f} |"
                    )
                if metrics.awr_function_count:
                    pg_func = pg_scores[PLSQLObjectType.FUNCTION]
                    mysql_func = mysql_scores[PLSQLObjectType.FUNCTION]
                    sections.append(
                        f"| 함수 | {metrics.awr_function_count:,}개 | "
                        f"{pg_func:.1f} | {mysql_func:.1f} |"
                    )
                if metrics.awr_trigger_count:
                    pg_trig = pg_scores[PLSQLObjectType.TRIGGER]
                    mysql_trig = mysql_scores[PLSQLObjectType.TRIGGER]
                    sections.append(
                        f"| 트리거 | {metrics.awr_trigger_count:,}개 | "
                        f"{pg_trig:.1f} | {mysql_trig:.1f} |"
                    )
                if metrics.awr_type_count:
                    # TYPE은 PROCEDURE로 매핑됨
                    pg_type = pg_scores[PLSQLObjectType.PROCEDURE]
                    mysql_type = mysql_scores[PLSQLObjectType.PROCEDURE]
                    sections.append(
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
                sections.append(f"| **합계** | **{total_objects:,}개** | - | - |")
                sections.append("")
                sections.append(
                    "> **기본 점수**: 오브젝트 타입별 최소 복잡도입니다. "
                    "실제 복잡도는 코드 분석을 통해 추가됩니다. "
                    "MySQL은 PL/SQL 미지원으로 애플리케이션 이관 페널티가 포함되어 점수가 높습니다."
                )
                sections.append("")
            
            # PostgreSQL vs MySQL 비교 테이블
            has_mysql = (
                metrics.avg_plsql_complexity_mysql is not None and 
                metrics.avg_plsql_complexity_mysql > 0
            )
            
            if has_mysql:
                sections.append("### 타겟 DB별 복잡도 비교\n")
                sections.append("> **왜 두 타겟을 비교하나요?**")
                sections.append("> PostgreSQL과 MySQL은 Oracle 호환성이 다릅니다.")
                sections.append("> 복잡도가 낮은 타겟이 변환 작업이 더 쉽습니다.\n")
                sections.append("| 항목 | PostgreSQL | MySQL |")
                sections.append("|------|------------|-------|")
                
                pg_level = RationaleFormatterMixin._get_complexity_level(
                    metrics.avg_plsql_complexity
                )
                mysql_level = RationaleFormatterMixin._get_complexity_level(
                    metrics.avg_plsql_complexity_mysql
                )
                sections.append(
                    f"| 평균 복잡도 | {metrics.avg_plsql_complexity:.2f} ({pg_level}) | "
                    f"{metrics.avg_plsql_complexity_mysql:.2f} ({mysql_level}) |"
                )
                
                if metrics.max_plsql_complexity and metrics.max_plsql_complexity_mysql:
                    pg_max_level = RationaleFormatterMixin._get_complexity_level(
                        metrics.max_plsql_complexity
                    )
                    mysql_max_level = RationaleFormatterMixin._get_complexity_level(
                        metrics.max_plsql_complexity_mysql
                    )
                    sections.append(
                        f"| 최대 복잡도 | {metrics.max_plsql_complexity:.2f} ({pg_max_level}) | "
                        f"{metrics.max_plsql_complexity_mysql:.2f} ({mysql_max_level}) |"
                    )
                
                # 고난이도 개수 비교 (PostgreSQL: ≥5.0, MySQL: ≥7.0)
                pg_high = metrics.high_complexity_plsql_count or 0
                mysql_high = metrics.high_complexity_plsql_count_mysql or 0
                pg_total = metrics.total_plsql_count or 0
                mysql_total = metrics.total_plsql_count_mysql or 0
                
                pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
                mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
                
                if pg_total > 0 or mysql_total > 0:
                    sections.append(
                        f"| 고난이도 | {pg_high}개 / {pg_total}개 (≥{pg_threshold}) | "
                        f"{mysql_high}개 / {mysql_total}개 (≥{mysql_threshold}) |"
                    )
                
                sections.append("")
                
                # 복잡도 차이 분석
                diff = metrics.avg_plsql_complexity_mysql - metrics.avg_plsql_complexity
                if diff > 0.5:
                    sections.append(
                        f"> **분석**: MySQL 타겟이 PostgreSQL보다 복잡도가 **{diff:.2f}** 높습니다. "
                        "PostgreSQL이 Oracle 호환성이 더 좋아 변환이 용이합니다."
                    )
                    sections.append("")
                    sections.append(
                        "> **차이 발생 원인**: MySQL은 PL/SQL을 지원하지 않아 "
                        "저장 프로시저를 애플리케이션 코드로 이관해야 합니다. "
                        "반면 PostgreSQL의 PL/pgSQL은 Oracle PL/SQL과 문법이 유사하여 "
                        "대부분의 코드를 직접 변환할 수 있습니다. "
                        "이로 인해 MySQL 변환 시 기본 점수와 애플리케이션 이관 페널티가 추가됩니다."
                    )
                elif diff < -0.5:
                    sections.append(
                        f"> **분석**: PostgreSQL 타겟이 MySQL보다 복잡도가 **{abs(diff):.2f}** 높습니다. "
                        "MySQL이 변환에 더 적합할 수 있습니다."
                    )
                else:
                    sections.append(
                        "> **분석**: 두 타겟 DB의 복잡도 차이가 크지 않습니다. "
                        "다른 요소(기능 호환성, 운영 경험 등)를 고려하세요."
                    )
                sections.append("")
            else:
                # 단일 타겟 (PostgreSQL만)
                complexity_level = RationaleFormatterMixin._get_complexity_level(
                    metrics.avg_plsql_complexity
                )
                
                sections.append(f"| 항목 | 값 |")
                sections.append(f"|------|-----|")
                sections.append(f"| 평균 복잡도 | {metrics.avg_plsql_complexity:.2f} ({complexity_level}) |")
                
                if metrics.max_plsql_complexity:
                    max_level = RationaleFormatterMixin._get_complexity_level(
                        metrics.max_plsql_complexity
                    )
                    sections.append(f"| 최대 복잡도 | {metrics.max_plsql_complexity:.2f} ({max_level}) |")
                
                if metrics.total_plsql_count:
                    sections.append(f"| 분석 대상 | {metrics.total_plsql_count:,}개 오브젝트 |")
                
                if metrics.high_complexity_plsql_count is not None:
                    sections.append(
                        f"| 고복잡도 (7.0 이상) | {metrics.high_complexity_plsql_count:,}개 |"
                    )
                
                sections.append("")
            
            sections.append("> **복잡도 산정 공식**: 기본 점수 + 코드 복잡도 + "
                          "Oracle 특화 기능 + 비즈니스 로직 + 변환 난이도")
            sections.append("")
            sections.append("> **정규화 공식**: `정규화 점수 = 원점수 / 최대점수 × 10`")
            sections.append(">")
            sections.append("> - PostgreSQL 최대점수: 13.5점, MySQL 최대점수: 18.0점")
            sections.append("> - 정규화를 통해 타겟 DB 간 복잡도를 동일 척도(0~10)로 비교 가능")
            sections.append("> - 예: PostgreSQL 원점수 6.75 → 정규화 5.0, "
                          "MySQL 원점수 9.0 → 정규화 5.0 (동일 난이도)")
            sections.append("")
            
            # Oracle 특화 기능 및 외부 의존성 섹션 추가
            sections.append(
                RationaleFormatterMixin._format_oracle_features_section_ko(metrics)
            )
        
        # 3. 작업 예상 시간 (최종 난이도 판정은 별도 섹션으로 이동)
        sections.append(RationaleFormatterMixin._format_work_estimation_ko(metrics))
        
        # 6. 추가 고려사항 (DB 분석으로 알 수 없는 항목)
        sections.append(RationaleFormatterMixin._format_additional_considerations_ko())
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_oracle_features_section_ko(metrics: AnalysisMetrics) -> str:
        """Oracle 특화 기능 및 외부 의존성 섹션 (한국어)
        
        복잡도 리포트에서 추출한 Oracle 특화 기능과 외부 의존성을 표시합니다.
        """
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
            
            # 영향도 매핑
            impact_map = {
                'NESTED TABLE': '🔴 높음',
                'OBJECT TYPE': '🔴 높음',
                'VARRAY': '🟠 중간',
                'CONNECT BY': '🔴 높음',
                'ROWNUM': '🟢 낮음',
                'ROWID': '🟠 중간',
                'DUAL': '🟢 낮음',
                'DECODE': '🟢 낮음',
                'NVL': '🟢 낮음',
                'NVL2': '🟢 낮음',
                'SYSDATE': '🟢 낮음',
                'SYSTIMESTAMP': '🟢 낮음',
                'SEQUENCE': '🟢 낮음',
                'AUTONOMOUS_TRANSACTION': '🔴 높음',
                'BULK COLLECT': '🟠 중간',
                'FORALL': '🟠 중간',
                'REF CURSOR': '🟠 중간',
                'PIPELINED': '🔴 높음',
                'PARALLEL': '🟠 중간',
            }
            
            for feature, count in sorted(oracle_features.items(), key=lambda x: -x[1]):
                impact = impact_map.get(feature.upper(), '🟠 중간')
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
            
            # 대체 방법 매핑
            replacement_map = {
                'DBMS_OUTPUT': 'RAISE NOTICE (PostgreSQL) / SELECT (MySQL)',
                'DBMS_LOB': '네이티브 LOB 함수',
                'DBMS_SQL': '동적 SQL (EXECUTE)',
                'DBMS_SCHEDULER': 'pg_cron / Event Scheduler',
                'DBMS_JOB': 'pg_cron / Event Scheduler',
                'UTL_FILE': 'COPY 명령 / LOAD DATA',
                'UTL_HTTP': 'http 확장 / 애플리케이션 레이어',
                'UTL_MAIL': '애플리케이션 레이어',
                'DBMS_CRYPTO': 'pgcrypto / AES_ENCRYPT',
                'DBMS_RANDOM': 'random() / RAND()',
                'DBMS_LOCK': 'Advisory Lock / GET_LOCK',
                'DBMS_PIPE': '애플리케이션 레이어',
                'DBMS_ALERT': 'LISTEN/NOTIFY / 애플리케이션',
                'DBMS_APPLICATION_INFO': '세션 변수',
                'DBMS_SESSION': '세션 함수',
                'DBMS_METADATA': '정보 스키마 쿼리',
                'DBMS_STATS': 'ANALYZE / ANALYZE TABLE',
                'DBMS_UTILITY': '개별 함수로 대체',
            }
            
            for dep, count in sorted(external_deps.items(), key=lambda x: -x[1]):
                replacement = replacement_map.get(dep.upper(), '개별 검토 필요')
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
        
        # 데이터가 없는 경우
        if not oracle_features and not external_deps and not conversion_guide:
            return ""
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_work_estimation_ko(metrics: AnalysisMetrics) -> str:
        """작업 예상 시간 섹션 (한국어)
        
        기준: 4인 팀, 전원 AI 도구 활용
        """
        lines = []
        lines.append("## 작업 예상 시간\n")
        
        # 섹션 설명 추가
        lines.append("> **이 섹션의 목적**: PL/SQL 오브젝트 수와 코드량을 기반으로")
        lines.append("> 마이그레이션 작업에 필요한 **예상 기간**을 산정합니다.")
        lines.append("> AI 도구 활용을 전제로 하며, 실제 기간은 팀 역량에 따라 달라질 수 있습니다.\n")
        
        # 팀 규모 상수
        team_size = 4
        
        # PL/SQL 오브젝트 및 라인 수
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
        
        # 작업 시간 산정 (4인 기준, AI 활용)
        lines.append(f"### 예상 작업 시간 ({team_size}인 팀 기준)\n")
        lines.append("| 작업 방식 | 예상 기간 | 비고 |")
        lines.append("|----------|----------|------|")
        
        # 1인 기준 작업 시간 (오브젝트당 평균 4시간)
        total_hours_single = total_objects * 4 if total_objects > 0 else 0
        
        # AI 활용 시 50~70% 단축 → 30~50% 시간 소요
        ai_hours_single_min = total_hours_single * 0.3
        ai_hours_single_max = total_hours_single * 0.5
        
        if total_hours_single > 0:
            # 4인 팀 기준으로 나누기
            ai_hours_team_min = ai_hours_single_min / team_size
            ai_hours_team_max = ai_hours_single_max / team_size
            
            # 일(8시간)로 변환
            ai_days_min = ai_hours_team_min / 8
            ai_days_max = ai_hours_team_max / 8
            
            # 표시 형식
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
    
    @staticmethod
    def _format_additional_considerations_ko() -> str:
        """추가 고려사항 섹션 (한국어) - DB 분석으로 알 수 없는 항목"""
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
    
    @staticmethod
    def _format_rationales_en(
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
            sections.append("## PL/SQL Complexity\n")
            
            # PostgreSQL vs MySQL comparison
            has_mysql = (
                metrics.avg_plsql_complexity_mysql is not None and 
                metrics.avg_plsql_complexity_mysql > 0
            )
            
            if has_mysql:
                sections.append("### Target DB Complexity Comparison\n")
                sections.append("| Item | PostgreSQL | MySQL |")
                sections.append("|------|------------|-------|")
                
                pg_level = RationaleFormatterMixin._get_complexity_level_en(
                    metrics.avg_plsql_complexity
                )
                mysql_level = RationaleFormatterMixin._get_complexity_level_en(
                    metrics.avg_plsql_complexity_mysql
                )
                sections.append(
                    f"| Average Complexity | {metrics.avg_plsql_complexity:.2f} ({pg_level}) | "
                    f"{metrics.avg_plsql_complexity_mysql:.2f} ({mysql_level}) |"
                )
                
                if metrics.max_plsql_complexity and metrics.max_plsql_complexity_mysql:
                    pg_max_level = RationaleFormatterMixin._get_complexity_level_en(
                        metrics.max_plsql_complexity
                    )
                    mysql_max_level = RationaleFormatterMixin._get_complexity_level_en(
                        metrics.max_plsql_complexity_mysql
                    )
                    sections.append(
                        f"| Max Complexity | {metrics.max_plsql_complexity:.2f} ({pg_max_level}) | "
                        f"{metrics.max_plsql_complexity_mysql:.2f} ({mysql_max_level}) |"
                    )
                
                sections.append("")
                
                # Complexity difference analysis
                diff = metrics.avg_plsql_complexity_mysql - metrics.avg_plsql_complexity
                if diff > 0.5:
                    sections.append(
                        f"> **Analysis**: MySQL target is **{diff:.2f}** more complex than PostgreSQL. "
                        "PostgreSQL has better Oracle compatibility for easier conversion."
                    )
                elif diff < -0.5:
                    sections.append(
                        f"> **Analysis**: PostgreSQL target is **{abs(diff):.2f}** more complex than MySQL. "
                        "MySQL may be more suitable for conversion."
                    )
                else:
                    sections.append(
                        "> **Analysis**: Complexity difference between targets is minimal. "
                        "Consider other factors (feature compatibility, operational experience)."
                    )
                sections.append("")
            else:
                complexity_level = RationaleFormatterMixin._get_complexity_level_en(
                    metrics.avg_plsql_complexity
                )
                
                sections.append(f"| Item | Value |")
                sections.append(f"|------|-------|")
                sections.append(f"| Average Complexity | {metrics.avg_plsql_complexity:.2f} ({complexity_level}) |")
                
                if metrics.max_plsql_complexity:
                    max_level = RationaleFormatterMixin._get_complexity_level_en(
                        metrics.max_plsql_complexity
                    )
                    sections.append(f"| Max Complexity | {metrics.max_plsql_complexity:.2f} ({max_level}) |")
                
                if metrics.total_plsql_count:
                    sections.append(f"| Analyzed Objects | {metrics.total_plsql_count:,} |")
                
                if metrics.high_complexity_plsql_count is not None:
                    sections.append(
                        f"| High Complexity (≥7.0) | {metrics.high_complexity_plsql_count:,} |"
                    )
                
                sections.append("")
            
            sections.append("> **Formula**: Base + Code Complexity + "
                          "Oracle Features + Business Logic + Conversion")
            sections.append("")
        
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
        
        final_difficulty = RationaleFormatterMixin._calculate_final_difficulty(metrics)
        difficulty_text = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "very_high": "Very High"
        }
        
        sections.append(f"**Overall Difficulty**: {difficulty_text.get(final_difficulty, final_difficulty)}\n")
        
        # 5. Work Estimation
        sections.append(RationaleFormatterMixin._format_work_estimation_en(metrics))
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_work_estimation_en(metrics: AnalysisMetrics) -> str:
        """작업 예상 시간 섹션 (영어)
        
        기준: 4인 팀, 전원 AI 도구 활용
        """
        lines = []
        lines.append("## Work Estimation\n")
        
        # 팀 규모 상수
        team_size = 4
        
        # PL/SQL 오브젝트 및 라인 수
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
        
        # 작업 시간 산정 (4인 기준, AI 활용)
        lines.append(f"### Estimated Work Time ({team_size}-person team)\n")
        lines.append("| Approach | Estimated Duration | Notes |")
        lines.append("|----------|-------------------|-------|")
        
        # 1인 기준 작업 시간 (오브젝트당 평균 4시간)
        total_hours_single = total_objects * 4 if total_objects > 0 else 0
        
        # AI 활용 시 50~70% 단축 → 30~50% 시간 소요
        ai_hours_single_min = total_hours_single * 0.3
        ai_hours_single_max = total_hours_single * 0.5
        
        if total_hours_single > 0:
            # 4인 팀 기준으로 나누기
            ai_hours_team_min = ai_hours_single_min / team_size
            ai_hours_team_max = ai_hours_single_max / team_size
            
            # 일(8시간)로 변환
            ai_days_min = ai_hours_team_min / 8
            ai_days_max = ai_hours_team_max / 8
            
            # 표시 형식
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
    
    @staticmethod
    def _get_complexity_level(score: float) -> str:
        """복잡도 점수를 레벨로 변환 (한국어)"""
        if score < 2.0:
            return "매우 낮음"
        elif score < 4.0:
            return "낮음"
        elif score < 6.0:
            return "중간"
        elif score < 8.0:
            return "높음"
        else:
            return "매우 높음"
    
    @staticmethod
    def _get_complexity_level_en(score: float) -> str:
        """복잡도 점수를 레벨로 변환 (영어)"""
        if score < 2.0:
            return "Very Low"
        elif score < 4.0:
            return "Low"
        elif score < 6.0:
            return "Medium"
        elif score < 8.0:
            return "High"
        else:
            return "Very High"
    
    @staticmethod
    def _calculate_final_difficulty(metrics: AnalysisMetrics) -> str:
        """최종 난이도 계산 (AI 시대 기준 조정)
        
        난이도 점수 산정 기준:
        - SQL 평균 복잡도: 0~3점 (신규)
        - PL/SQL 평균 복잡도: 0~3점
        - PL/SQL 코드량: 0~3점
        - 고난이도 오브젝트 비율: 0~2점 (모수 70개 이상)
        - 고난이도 오브젝트 절대 개수: 0~3점
        - 고위험 Oracle 패키지: 0~3점 (신규)
        - 중위험 Oracle 패키지: 0~2점 (신규)
        
        총점 기준:
        - 0~3점: low
        - 4~7점: medium
        - 8~11점: high
        - 12점 이상: very_high
        """
        score = 0
        
        # SQL 복잡도 기반 (0~3점) - 신규
        if metrics.avg_sql_complexity:
            if metrics.avg_sql_complexity >= 7.5:
                score += 3
            elif metrics.avg_sql_complexity >= 6.0:
                score += 2
            elif metrics.avg_sql_complexity >= 4.5:
                score += 1
        
        # PL/SQL 복잡도 기반 (0~3점) - 임계값 상향
        if metrics.avg_plsql_complexity:
            if metrics.avg_plsql_complexity >= 7.5:
                score += 3
            elif metrics.avg_plsql_complexity >= 6.0:
                score += 2
            elif metrics.avg_plsql_complexity >= 4.5:
                score += 1
        
        # PL/SQL 코드량 기반 (0~3점) - 임계값 상향
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            import re
            numbers = re.findall(r"\d+", str(plsql_lines))
            plsql_lines = int(numbers[-1]) if numbers else 0
        if plsql_lines >= 200000:
            score += 3
        elif plsql_lines >= 100000:
            score += 2
        elif plsql_lines >= 50000:
            score += 1
        
        # 고난이도 오브젝트 비율 기반 (0~2점) - 모수 조건 추가
        total_objects = (metrics.total_plsql_count or 0) + (metrics.total_sql_count or 0)
        if total_objects >= 70:  # 모수 70개 이상일 때만 비율 의미 있음
            high_count = (metrics.high_complexity_plsql_count or 0) + (metrics.high_complexity_sql_count or 0)
            if total_objects > 0:
                ratio = high_count / total_objects
                if ratio >= 0.30:
                    score += 2
                elif ratio >= 0.20:
                    score += 1
        
        # 고난이도 오브젝트 절대 개수 기반 (0~3점) - 임계값 상향
        high_count = (metrics.high_complexity_plsql_count or 0) + (metrics.high_complexity_sql_count or 0)
        if high_count >= 100:
            score += 3
        elif high_count >= 50:
            score += 2
        elif high_count >= 30:
            score += 1
        
        # 고위험 Oracle 패키지 기반 (0~3점) - 신규
        # UTL_FILE, UTL_HTTP, UTL_SMTP, UTL_TCP, DBMS_AQ, DBMS_PIPE, DBMS_ALERT
        high_risk_packages = {'UTL_FILE', 'UTL_HTTP', 'UTL_SMTP', 'UTL_TCP', 
                              'DBMS_AQ', 'DBMS_PIPE', 'DBMS_ALERT'}
        external_deps = metrics.detected_external_dependencies_summary or {}
        high_risk_count = sum(external_deps.get(pkg, 0) for pkg in high_risk_packages)
        if high_risk_count >= 50:
            score += 3
        elif high_risk_count >= 20:
            score += 2
        elif high_risk_count >= 5:
            score += 1
        
        # 중위험 Oracle 패키지 기반 (0~2점) - 신규
        # DBMS_LOB, DBMS_SCHEDULER, DBMS_JOB, DBMS_CRYPTO, DBMS_SQL, DBMS_XMLGEN
        medium_risk_packages = {'DBMS_LOB', 'DBMS_SCHEDULER', 'DBMS_JOB', 
                                'DBMS_CRYPTO', 'DBMS_SQL', 'DBMS_XMLGEN'}
        medium_risk_count = sum(external_deps.get(pkg, 0) for pkg in medium_risk_packages)
        if medium_risk_count >= 30:
            score += 2
        elif medium_risk_count >= 10:
            score += 1
        
        if score >= 12:
            return "very_high"
        elif score >= 8:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _format_final_difficulty_section(
        metrics: AnalysisMetrics,
        language: str
    ) -> str:
        """최종 난이도 판정 섹션 포맷 (대안 전략 바로 위에 배치)
        
        Args:
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return RationaleFormatterMixin._format_final_difficulty_section_ko(metrics)
        return RationaleFormatterMixin._format_final_difficulty_section_en(metrics)
    
    @staticmethod
    def _format_final_difficulty_section_ko(metrics: AnalysisMetrics) -> str:
        """최종 난이도 판정 섹션 (한국어)"""
        from src.oracle_complexity_analyzer.weights import (
            POSTGRESQL_WEIGHTS,
            MYSQL_WEIGHTS,
        )
        
        lines = []
        lines.append("# 최종 난이도 판정\n")
        
        # 섹션 설명 추가
        lines.append("> **이 섹션의 목적**: 여러 분석 지표를 종합하여 마이그레이션의")
        lines.append("> **전체 난이도**를 판정합니다. 점수가 높을수록 변환 작업이 복잡합니다.\n")
        
        # 종합 난이도
        final_difficulty = RationaleFormatterMixin._calculate_final_difficulty(metrics)
        difficulty_text = {
            "low": "낮음 (Low)",
            "medium": "중간 (Medium)",
            "high": "높음 (High)",
            "very_high": "매우 높음 (Very High)"
        }
        lines.append(f"**종합 난이도**: {difficulty_text.get(final_difficulty, final_difficulty)}\n")
        
        # 난이도 점수 산정 기준 테이블
        lines.append("## 난이도 점수 산정 기준\n")
        lines.append("| 평가 항목 | 기준 | 점수 | 현재 값 | 획득 점수 |")
        lines.append("|----------|------|------|--------|----------|")
        
        total_score = 0
        
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
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        
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
        
        # 4. 고난이도 오브젝트 절대 개수 (0~3점) - 신규 추가
        high_count_total = (metrics.high_complexity_plsql_count or 0) + (metrics.high_complexity_sql_count or 0)
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
        
        # 난이도 등급 기준
        lines.append("> **난이도 등급 기준**: 0~2점 낮음, 3~5점 중간, 6~8점 높음, 9점 이상 매우 높음")
        lines.append("")
        
        # 복잡도 점수 산정 기준 (weights.py 기반)
        lines.append("## 복잡도 점수 산정 기준\n")
        lines.append("> **복잡도 점수란?** 코드 변환 난이도를 0~10 척도로 수치화한 것입니다.")
        lines.append("> 점수가 높을수록 변환에 더 많은 노력이 필요합니다.\n")
        lines.append("### PostgreSQL 타겟\n")
        lines.append("| 항목 | 최대 점수 | 설명 |")
        lines.append("|------|----------|------|")
        lines.append(f"| 구조적 복잡도 | {POSTGRESQL_WEIGHTS.max_structural} | JOIN, 서브쿼리, CTE 등 |")
        lines.append("| Oracle 특화 기능 | 3.0 | CONNECT BY, ROWNUM 등 |")
        lines.append("| 함수/표현식 | 2.0 | 분석 함수, 변환 함수 등 |")
        lines.append(f"| 데이터 볼륨 | {max(POSTGRESQL_WEIGHTS.data_volume_scores.values())} | 쿼리 길이 기반 |")
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
        lines.append(f"| 데이터 볼륨 | {max(MYSQL_WEIGHTS.data_volume_scores.values())} | 쿼리 길이 기반 |")
        lines.append("| 실행 복잡도 | 2.5 | ORDER BY, GROUP BY 등 |")
        lines.append("| 변환 난이도 | 4.5 | 타겟 DB 미지원 기능 |")
        lines.append(f"| **최대 총점** | **{MYSQL_WEIGHTS.max_total_score}** | - |")
        lines.append("")
        
        # 고난이도 임계값 설명
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
        lines.append(
            f"> **고난이도 임계값**: PostgreSQL ≥{pg_threshold} (최대점수의 37%), "
            f"MySQL ≥{mysql_threshold} (최대점수의 39%)"
        )
        lines.append("")
        
        # 작업 예상 시간 요약
        lines.append("## 예상 작업 기간 요약\n")
        
        total_objects = sum(filter(None, [
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count
        ])) or metrics.total_plsql_count or 0
        
        if total_objects > 0:
            # 4인 팀, AI 활용 기준
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
        
        # 판정 요약
        lines.append("## 판정 요약\n")
        
        summary_items = []
        
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
    
    @staticmethod
    def _format_final_difficulty_section_en(metrics: AnalysisMetrics) -> str:
        """최종 난이도 판정 섹션 (영어)"""
        from src.oracle_complexity_analyzer.weights import (
            POSTGRESQL_WEIGHTS,
            MYSQL_WEIGHTS,
        )
        
        lines = []
        lines.append("# Final Difficulty Assessment\n")
        
        # 종합 난이도
        final_difficulty = RationaleFormatterMixin._calculate_final_difficulty(metrics)
        difficulty_text = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "very_high": "Very High"
        }
        lines.append(f"**Overall Difficulty**: {difficulty_text.get(final_difficulty, final_difficulty)}\n")
        
        # 난이도 점수 산정 기준 테이블
        lines.append("## Difficulty Scoring Criteria\n")
        lines.append("| Evaluation Item | Criteria | Score | Current Value | Points |")
        lines.append("|-----------------|----------|-------|---------------|--------|")
        
        total_score = 0
        
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
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        
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
