"""
Quick Assessment 섹션 포맷터

DBCSI 데이터만으로 Oracle 필수 여부를 빠르게 판단합니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from ...models import StatspackData, FeatureUsage


class AssessmentResult(Enum):
    """평가 결과"""
    ORACLE_REQUIRED = "oracle_required"
    OPEN_SOURCE_POSSIBLE = "open_source_possible"
    NEEDS_DETAILED_ANALYSIS = "needs_detailed_analysis"


@dataclass
class QuickAssessmentResult:
    """Quick Assessment 결과"""
    result: AssessmentResult
    confidence: float  # 0.0 - 1.0
    reasons: List[str]
    recommendations: List[str]
    rac_mitigatable: bool = False  # RAC지만 쓰기 IOPS 낮아서 대체 가능


class QuickAssessor:
    """DBCSI 기반 빠른 평가기"""

    # 임계값 상수
    PLSQL_LINES_HIGH = 100000
    PLSQL_LINES_MEDIUM = 20000
    PROCEDURE_COUNT_LOW = 50
    FUNCTION_COUNT_LOW = 30
    PACKAGE_COUNT_LOW = 20
    DB_SIZE_LOW_GB = 500
    DB_LINKS_HIGH = 10
    DB_LINKS_MEDIUM = 5
    WRITE_IOPS_LOW = 1000  # RAC 대체 가능 기준

    # EE 전용 기능 (대체 어려움)
    EE_HARD_FEATURES = [
        "OLAP",
        "Data Mining",
        "Label Security",
        "Database Vault",
    ]

    # EE 기능 (대체 가능)
    EE_SOFT_FEATURES = [
        "Advanced Compression",
        "Spatial and Graph",
        "Advanced Security",
        "Real Application Testing",
        "Partitioning",
    ]

    @classmethod
    def assess(cls, data: StatspackData) -> QuickAssessmentResult:
        """빠른 평가 수행"""
        os_info = data.os_info
        features = data.features
        main_metrics = data.main_metrics

        reasons: List[str] = []
        recommendations: List[str] = []
        rac_mitigatable = False

        # 1. RAC 체크 (쓰기 IOPS 고려)
        is_rac = cls._is_rac(os_info)
        if is_rac:
            max_write_iops = cls._get_max_write_iops(main_metrics)
            if max_write_iops and max_write_iops < cls.WRITE_IOPS_LOW:
                rac_mitigatable = True
                reasons.append(
                    f"RAC 구성이지만 쓰기 IOPS가 낮음 ({max_write_iops:.0f} IOPS < {cls.WRITE_IOPS_LOW})"
                )
                recommendations.append("Multi-AZ 또는 Read Replica로 대체 가능")
            else:
                iops_str = f" (최대 {max_write_iops:.0f} IOPS)" if max_write_iops else ""
                reasons.append(f"RAC 구성 감지 (INSTANCES > 1){iops_str}")
                return QuickAssessmentResult(
                    result=AssessmentResult.ORACLE_REQUIRED,
                    confidence=0.85,
                    reasons=reasons,
                    recommendations=["Replatform 또는 아키텍처 재설계 검토"],
                    rac_mitigatable=False,
                )

        # 2. 대규모 PL/SQL 체크
        plsql_lines = os_info.count_lines_plsql or 0
        if plsql_lines >= cls.PLSQL_LINES_HIGH:
            reasons.append(f"대규모 PL/SQL ({plsql_lines:,}줄 ≥ {cls.PLSQL_LINES_HIGH:,}줄)")
            return QuickAssessmentResult(
                result=AssessmentResult.ORACLE_REQUIRED,
                confidence=0.85,
                reasons=reasons,
                recommendations=["Replatform 권장 (변환 비용 > 유지 비용)"],
                rac_mitigatable=rac_mitigatable,
            )

        # 3. EE 기능 체크 (대체 어려운 기능)
        hard_features = cls._check_ee_features(features, cls.EE_HARD_FEATURES)
        if hard_features:
            reasons.append(f"대체 어려운 EE 기능 사용: {', '.join(hard_features)}")
            return QuickAssessmentResult(
                result=AssessmentResult.ORACLE_REQUIRED,
                confidence=0.8,
                reasons=reasons,
                recommendations=["Replatform 권장 (EE 기능 대체 어려움)"],
                rac_mitigatable=rac_mitigatable,
            )

        # 4. 다수 DB Link 체크
        db_links = os_info.count_db_links or 0
        if db_links >= cls.DB_LINKS_HIGH:
            reasons.append(f"다수의 DB Link ({db_links}개 ≥ {cls.DB_LINKS_HIGH}개)")
            return QuickAssessmentResult(
                result=AssessmentResult.ORACLE_REQUIRED,
                confidence=0.75,
                reasons=reasons,
                recommendations=["분산 아키텍처 재설계 필요"],
                rac_mitigatable=rac_mitigatable,
            )

        # 5. EE 기능 체크 (대체 가능한 기능)
        soft_features = cls._check_ee_features(features, cls.EE_SOFT_FEATURES)
        if soft_features:
            reasons.append(f"대체 가능한 EE 기능 사용: {', '.join(soft_features)}")
            recommendations.append("EE 기능 대체 방안 검토 필요")

        # 6. 중간 규모 체크
        if plsql_lines >= cls.PLSQL_LINES_MEDIUM:
            reasons.append(
                f"중간 규모 PL/SQL ({plsql_lines:,}줄, "
                f"{cls.PLSQL_LINES_MEDIUM:,}~{cls.PLSQL_LINES_HIGH:,}줄)"
            )
            recommendations.append("PL/SQL 복잡도 상세 분석 권장")
            return QuickAssessmentResult(
                result=AssessmentResult.NEEDS_DETAILED_ANALYSIS,
                confidence=0.6,
                reasons=reasons,
                recommendations=recommendations,
                rac_mitigatable=rac_mitigatable,
            )

        # 7. 중간 규모 DB Link 체크
        if db_links >= cls.DB_LINKS_MEDIUM:
            reasons.append(f"DB Link 사용 ({db_links}개)")
            recommendations.append("분산 트랜잭션 패턴 검토 필요")

        # 8. 오픈소스 가능 조건 체크
        if cls._check_open_source_conditions(os_info, soft_features):
            if not reasons:
                reasons.append("모든 오픈소스 전환 조건 충족")
            recommendations.extend([
                "PostgreSQL 또는 MySQL 선택을 위한 상세 분석 권장",
                "마이그레이션 로드맵 수립",
            ])
            return QuickAssessmentResult(
                result=AssessmentResult.OPEN_SOURCE_POSSIBLE,
                confidence=0.75 if not soft_features else 0.65,
                reasons=reasons,
                recommendations=recommendations,
                rac_mitigatable=rac_mitigatable,
            )

        # 9. 기본: 상세 분석 필요
        if not reasons:
            reasons.append("추가 분석 필요")
        recommendations.append("PL/SQL 및 SQL 복잡도 분석 실행 권장")
        return QuickAssessmentResult(
            result=AssessmentResult.NEEDS_DETAILED_ANALYSIS,
            confidence=0.6,
            reasons=reasons,
            recommendations=recommendations,
            rac_mitigatable=rac_mitigatable,
        )

    @classmethod
    def _is_rac(cls, os_info) -> bool:
        """RAC 여부 확인"""
        return (os_info.instances or 1) > 1

    @classmethod
    def _get_max_write_iops(cls, main_metrics) -> Optional[float]:
        """최대 쓰기 IOPS 반환"""
        if not main_metrics:
            return None
        write_iops_list = [m.write_iops for m in main_metrics if m.write_iops]
        return max(write_iops_list) if write_iops_list else None

    @classmethod
    def _check_ee_features(
        cls, features: List[FeatureUsage], target_features: List[str]
    ) -> List[str]:
        """사용 중인 EE 기능 목록 반환 (user 레벨만)"""
        used = []
        for feature in features:
            # user 레벨만 체크 (system은 무시)
            if "(user)" in feature.name and feature.currently_used:
                for target in target_features:
                    if target.lower() in feature.name.lower():
                        # 간결한 이름으로 변환
                        clean_name = feature.name.replace(" (user)", "")
                        used.append(clean_name)
                        break
        return used

    @classmethod
    def _check_open_source_conditions(
        cls, os_info, soft_features: List[str]
    ) -> bool:
        """오픈소스 전환 조건 모두 충족 여부"""
        return all([
            (os_info.instances or 1) == 1,
            (os_info.count_lines_plsql or 0) < cls.PLSQL_LINES_MEDIUM,
            (os_info.count_procedures or 0) < cls.PROCEDURE_COUNT_LOW,
            (os_info.count_functions or 0) < cls.FUNCTION_COUNT_LOW,
            (os_info.count_packages or 0) < cls.PACKAGE_COUNT_LOW,
            (os_info.total_db_size_gb or 0) < cls.DB_SIZE_LOW_GB,
            len(soft_features) <= 1,  # 대체 가능 기능 1개 이하
        ])


class QuickAssessmentFormatter:
    """Quick Assessment 포맷터"""

    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """Quick Assessment 섹션 포맷

        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")

        Returns:
            Markdown 형식의 문자열
        """
        assessment = QuickAssessor.assess(data)

        if language == "ko":
            return QuickAssessmentFormatter._format_ko(data, assessment)
        return QuickAssessmentFormatter._format_en(data, assessment)

    @staticmethod
    def _format_ko(data: StatspackData, assessment: QuickAssessmentResult) -> str:
        """한국어 Quick Assessment"""
        lines = []
        os_info = data.os_info

        lines.append("## ⚡ Quick Assessment\n")
        lines.append("> DBCSI 데이터 기반 빠른 마이그레이션 방향성 판단\n")

        # 결과 아이콘 및 텍스트
        result_map = {
            AssessmentResult.ORACLE_REQUIRED: ("🔴", "Oracle 유지 권장"),
            AssessmentResult.OPEN_SOURCE_POSSIBLE: ("🟢", "오픈소스 전환 가능"),
            AssessmentResult.NEEDS_DETAILED_ANALYSIS: ("🟠", "상세 분석 필요"),
        }
        icon, text = result_map[assessment.result]

        lines.append(f"### 판단 결과: {icon} {text}\n")
        lines.append(f"**신뢰도**: {assessment.confidence * 100:.0f}%\n")

        # 입력 데이터 요약
        lines.append("### 📊 분석 데이터 요약\n")
        lines.append("| 항목 | 값 | 기준 |")
        lines.append("|------|-----|------|")

        instances = os_info.instances or 1
        rac_status = "RAC" if instances > 1 else "단일"
        lines.append(f"| 인스턴스 | {instances} ({rac_status}) | 1 = 단일 |")

        plsql_lines = os_info.count_lines_plsql or 0
        plsql_status = "🔴" if plsql_lines >= 100000 else "🟠" if plsql_lines >= 20000 else "🟢"
        lines.append(f"| PL/SQL 라인 수 | {plsql_lines:,} {plsql_status} | < 20,000 |")

        proc_count = os_info.count_procedures or 0
        lines.append(f"| 프로시저 수 | {proc_count:,} | < 50 |")

        func_count = os_info.count_functions or 0
        lines.append(f"| 함수 수 | {func_count:,} | < 30 |")

        pkg_count = os_info.count_packages or 0
        lines.append(f"| 패키지 수 | {pkg_count:,} | < 20 |")

        db_size = os_info.total_db_size_gb or 0
        lines.append(f"| DB 크기 | {db_size:,.1f} GB | < 500 GB |")

        db_links = os_info.count_db_links or 0
        lines.append(f"| DB Link 수 | {db_links} | < 5 |")

        # 쓰기 IOPS (있는 경우)
        if data.main_metrics:
            write_iops_list = [m.write_iops for m in data.main_metrics if m.write_iops]
            if write_iops_list:
                max_write = max(write_iops_list)
                avg_write = sum(write_iops_list) / len(write_iops_list)
                lines.append(f"| 쓰기 IOPS (최대/평균) | {max_write:,.0f} / {avg_write:,.0f} | - |")

        lines.append("")

        # 판단 근거
        if assessment.reasons:
            lines.append("### 📋 판단 근거\n")
            for reason in assessment.reasons:
                lines.append(f"- {reason}")
            lines.append("")

        # RAC 대체 가능 안내
        if assessment.rac_mitigatable:
            lines.append("### ℹ️ RAC 대체 가능성\n")
            lines.append("> 쓰기 IOPS가 낮아 RAC 없이도 고가용성 구현 가능합니다.\n")
            lines.append("- **Aurora Multi-AZ**: 자동 장애 조치, 동기식 복제")
            lines.append("- **Read Replica**: 읽기 부하 분산")
            lines.append("- **Aurora Global Database**: 리전 간 재해 복구")
            lines.append("")

        # 권장사항
        if assessment.recommendations:
            lines.append("### 💡 권장사항\n")
            for rec in assessment.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # 다음 단계
        lines.append("### 🔜 다음 단계\n")
        if assessment.result == AssessmentResult.ORACLE_REQUIRED:
            lines.append("1. Replatform (RDS for Oracle) 비용 산정")
            lines.append("2. 장기적 아키텍처 현대화 로드맵 수립")
        elif assessment.result == AssessmentResult.OPEN_SOURCE_POSSIBLE:
            lines.append("1. PL/SQL 복잡도 분석으로 PostgreSQL/MySQL 선택")
            lines.append("2. 마이그레이션 PoC 진행")
            lines.append("3. 상세 마이그레이션 계획 수립")
        else:
            lines.append("1. PL/SQL 복잡도 분석 실행")
            lines.append("2. SQL 복잡도 분석 실행 (가능한 경우)")
            lines.append("3. 분석 결과 기반 최종 전략 결정")
        lines.append("")

        # 주의사항
        lines.append("### ⚠️ 주의사항\n")
        lines.append("> Quick Assessment는 DBCSI 데이터만으로 판단하므로 "
                    "**60-70% 신뢰도**입니다.")
        lines.append("> 최종 결정 전 반드시 **PL/SQL 및 SQL 복잡도 상세 분석**을 수행하세요.")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_en(data: StatspackData, assessment: QuickAssessmentResult) -> str:
        """영어 Quick Assessment"""
        lines = []
        os_info = data.os_info

        lines.append("## ⚡ Quick Assessment\n")
        lines.append("> Quick migration direction assessment based on DBCSI data\n")

        result_map = {
            AssessmentResult.ORACLE_REQUIRED: ("🔴", "Oracle Required"),
            AssessmentResult.OPEN_SOURCE_POSSIBLE: ("🟢", "Open Source Possible"),
            AssessmentResult.NEEDS_DETAILED_ANALYSIS: ("🟠", "Detailed Analysis Needed"),
        }
        icon, text = result_map[assessment.result]

        lines.append(f"### Result: {icon} {text}\n")
        lines.append(f"**Confidence**: {assessment.confidence * 100:.0f}%\n")

        # Summary
        lines.append("### 📊 Data Summary\n")
        lines.append("| Item | Value | Threshold |")
        lines.append("|------|-------|-----------|")

        instances = os_info.instances or 1
        lines.append(f"| Instances | {instances} | 1 = Single |")

        plsql_lines = os_info.count_lines_plsql or 0
        lines.append(f"| PL/SQL Lines | {plsql_lines:,} | < 20,000 |")

        proc_count = os_info.count_procedures or 0
        lines.append(f"| Procedures | {proc_count:,} | < 50 |")

        func_count = os_info.count_functions or 0
        lines.append(f"| Functions | {func_count:,} | < 30 |")

        db_size = os_info.total_db_size_gb or 0
        lines.append(f"| DB Size | {db_size:,.1f} GB | < 500 GB |")

        lines.append("")

        if assessment.reasons:
            lines.append("### 📋 Reasons\n")
            for reason in assessment.reasons:
                lines.append(f"- {reason}")
            lines.append("")

        if assessment.recommendations:
            lines.append("### 💡 Recommendations\n")
            for rec in assessment.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

