"""
Markdown 포맷터 모듈

마이그레이션 추천 리포트를 Markdown 형식으로 변환합니다.
"""

from ...data_models import MigrationRecommendation, AnalysisMetrics

from .executive_summary import ExecutiveSummaryFormatterMixin
from .strategy import StrategyFormatterMixin
from .rationale import RationaleFormatterMixin
from .alternatives import AlternativesFormatterMixin
from .risks import RisksFormatterMixin
from .metrics import MetricsFormatterMixin
from .instance import InstanceFormatterMixin
from .database_overview import DatabaseOverviewFormatterMixin
from .object_statistics import ObjectStatisticsFormatterMixin
from .performance_details import PerformanceDetailsFormatterMixin
from .wait_events import WaitEventsFormatterMixin
from .oracle_features import OracleFeaturesFormatterMixin
from .awr_details import AWRDetailsFormatterMixin
from .confidence import ConfidenceFormatterMixin


class MarkdownReportFormatter(
    ExecutiveSummaryFormatterMixin,
    StrategyFormatterMixin,
    RationaleFormatterMixin,
    AlternativesFormatterMixin,
    RisksFormatterMixin,
    MetricsFormatterMixin,
    InstanceFormatterMixin,
    DatabaseOverviewFormatterMixin,
    ObjectStatisticsFormatterMixin,
    PerformanceDetailsFormatterMixin,
    WaitEventsFormatterMixin,
    OracleFeaturesFormatterMixin,
    AWRDetailsFormatterMixin,
    ConfidenceFormatterMixin
):
    """Markdown 리포트 포맷터
    
    모든 섹션 포맷터 믹스인을 통합하여 완전한 Markdown 리포트를 생성합니다.
    
    리포트 구조 (의사결정자 관점 최적화):
    
    헤더: 리포트 제목 및 DB 정보
    
    Part 1: 의사결정 정보 (경영진/관리자용)
    - 목차
    - 분석 신뢰도 (의사결정 전 신뢰도 확인)
    - 추천 전략 및 근거
    - 대안 전략 비교
    - 위험 요소 및 완화 방안
    
    Part 2: 기술 상세 (기술팀용 - 부록)
    - 인스턴스 추천
    - 분석 메트릭
    - Executive Summary (상세 요약)
    """
    
    def format(
        self,
        recommendation: MigrationRecommendation,
        language: str = "ko"
    ) -> str:
        """추천 리포트를 Markdown 형식으로 변환합니다.
        
        리포트 구조:
        1. 리포트 개요
        2. 목차
        3. 분석 신뢰도
        4. 데이터베이스 개요 (기본 정보 + PL/SQL + 스키마 오브젝트)
        5. Oracle 기능 사용 현황 (사용 중인 것만)
        6. 추천 전략 및 근거
        7. 최종 난이도 판정
        8. 대안 전략
        9. 위험 요소
        10. 부록 (인스턴스 추천, 메트릭, Executive Summary)
        """
        sections = []
        
        # ========================================
        # 1. 리포트 개요
        # ========================================
        sections.append(self._format_report_header(recommendation, language))
        
        # ========================================
        # 2. 목차
        # ========================================
        sections.append(self._format_toc(language))
        
        # ========================================
        # 3. 분석 신뢰도
        # ========================================
        if recommendation.confidence_assessment:
            confidence_section = self._format_confidence_section(
                recommendation.confidence_assessment, language
            )
            if confidence_section:
                sections.append(confidence_section)
        
        # ========================================
        # 4. 데이터베이스 개요 (기본 정보 + PL/SQL + 스키마)
        # ========================================
        db_overview = self._format_database_overview(recommendation.metrics, language)
        if db_overview:
            sections.append(db_overview)
        
        # ========================================
        # 5. Oracle 기능 사용 현황 (사용 중인 것만, 간소화)
        # ========================================
        oracle_features = self._format_oracle_features_summary(recommendation.metrics, language)
        if oracle_features:
            sections.append(oracle_features)
        
        # ========================================
        # 6. 추천 전략 및 근거
        # ========================================
        sections.append(self._format_strategy_with_rationale(recommendation, language))
        
        # ========================================
        # 7. 최종 난이도 판정 (대안 전략 바로 위)
        # ========================================
        sections.append(self._format_final_difficulty_section(recommendation.metrics, language))
        
        # ========================================
        # 8. 인스턴스 추천 (대안 전략 위로 이동)
        # ========================================
        if recommendation.instance_recommendation:
            sections.append(self._format_instance_recommendation(
                recommendation.instance_recommendation, 
                language, 
                recommendation.metrics,
                recommendation.recommended_strategy.value
            ))
        
        # ========================================
        # 9. 대안 전략
        # ========================================
        sections.append(self._format_alternatives(recommendation.alternative_strategies, language))
        
        # ========================================
        # 10. 위험 요소
        # ========================================
        sections.append(self._format_risks(recommendation.risks, language))
        
        # ========================================
        # 11. 부록
        # ========================================
        sections.append(self._format_appendix_header(language))
        
        sections.append(self._format_metrics(recommendation.metrics, language))
        sections.append(self._format_executive_summary(recommendation.executive_summary, language))
        
        return "\n\n".join(sections)
    
    def _format_oracle_features_summary(
        self,
        metrics: AnalysisMetrics,
        language: str
    ) -> str:
        """Oracle 기능 사용 현황 요약 (사용 중인 것만)"""
        if not metrics.oracle_features_used:
            return ""
        
        # 사용 중인 기능만 필터링 (currently_used=True 또는 detected_usages > 0)
        active_features = [
            f for f in metrics.oracle_features_used
            if f.get('currently_used', False) or f.get('detected_usages', 0) > 0
        ]
        
        if not active_features:
            return ""
        
        # 사용자 기능만 추출 (system 제외)
        user_features = [
            f for f in active_features
            if '(user)' in f.get('name', '').lower() or '(system)' not in f.get('name', '').lower()
        ]
        
        # 내부 관리 기능 제외
        internal_features = {
            'adaptive plans', 'automatic maintenance', 'automatic reoptimization',
            'automatic sga tuning', 'automatic sql execution memory', 'automatic undo management',
            'character set', 'dbms_stats', 'deferred segment creation', 'sql plan directive',
            'server parameter file', 'traditional audit', 'unified audit'
        }
        
        filtered_features = [
            f for f in user_features
            if not any(internal in f.get('name', '').lower() for internal in internal_features)
        ]
        
        if not filtered_features:
            return ""
        
        if language == "ko":
            lines = []
            lines.append("## Oracle 기능 사용 현황\n")
            lines.append("> 마이그레이션 시 검토가 필요한 Oracle 기능입니다.\n")
            lines.append("| 기능 | 사용 횟수 | 마이그레이션 영향 |")
            lines.append("|------|----------|-----------------|")
            
            for f in filtered_features[:10]:  # 최대 10개
                name = f.get('name', 'Unknown')
                usages = f.get('detected_usages', 0)
                impact = self._get_feature_migration_impact(name, language)
                lines.append(f"| {name} | {usages:,} | {impact} |")
            
            return "\n".join(lines)
        else:
            lines = []
            lines.append("## Oracle Feature Usage\n")
            lines.append("> Oracle features that require review during migration.\n")
            lines.append("| Feature | Usage Count | Migration Impact |")
            lines.append("|---------|-------------|------------------|")
            
            for f in filtered_features[:10]:
                name = f.get('name', 'Unknown')
                usages = f.get('detected_usages', 0)
                impact = self._get_feature_migration_impact(name, language)
                lines.append(f"| {name} | {usages:,} | {impact} |")
            
            return "\n".join(lines)
    
    def _get_feature_migration_impact(self, feature_name: str, language: str) -> str:
        """기능별 마이그레이션 영향 반환"""
        feature_lower = feature_name.lower()
        
        # 비호환 기능
        incompatible = ['advanced compression', 'olap', 'data mining', 'label security', 
                       'database vault', 'real application clusters']
        if any(f in feature_lower for f in incompatible):
            return "🔴 대체 방안 필요" if language == "ko" else "🔴 Alternative needed"
        
        # 부분 호환 기능
        partial = ['spatial', 'real application security', 'partitioning', 'real application testing']
        if any(f in feature_lower for f in partial):
            return "🟠 일부 수정 필요" if language == "ko" else "🟠 Partial modification"
        
        # 호환 기능
        return "🟢 호환" if language == "ko" else "🟢 Compatible"
    
    def _format_report_header(
        self,
        recommendation: MigrationRecommendation,
        language: str
    ) -> str:
        """리포트 헤더 (제목 및 DB 정보) 포맷팅
        
        표준 보고서 양식:
        - 제목에 DB명 포함
        - 이모지 없음
        - 타겟을 맨 위로
        - 신뢰도는 %로 표시
        - 분석 소스 리포트 종류 표시
        """
        from datetime import datetime
        
        # DB 정보 추출
        metrics = recommendation.metrics
        db_name = getattr(metrics, 'db_name', None) or "Unknown"
        db_version = getattr(metrics, 'db_version', None) or ""
        report_type = getattr(metrics, 'report_type', None) or ""
        
        # 추천 전략 이름
        strategy_names = {
            "ko": {
                "replatform": "RDS for Oracle SE2",
                "refactor_mysql": "Aurora MySQL",
                "refactor_postgresql": "Aurora PostgreSQL"
            },
            "en": {
                "replatform": "RDS for Oracle SE2",
                "refactor_mysql": "Aurora MySQL",
                "refactor_postgresql": "Aurora PostgreSQL"
            }
        }
        strategy_value = recommendation.recommended_strategy.value
        target_db = strategy_names[language].get(strategy_value, strategy_value)
        
        # 신뢰도 % 계산
        confidence_pct = 0
        if recommendation.confidence_assessment:
            confidence_pct = recommendation.confidence_assessment.overall_confidence
        else:
            # confidence_level에서 추정
            confidence_map = {"high": 90, "medium": 70, "low": 50}
            confidence_pct = confidence_map.get(recommendation.confidence_level, 70)
        
        # 분석 일시
        analysis_date = datetime.now().strftime("%Y-%m-%d")
        
        # 분석 소스 리포트 종류 수집
        analysis_sources = []
        if report_type:
            report_type_text = "AWR" if report_type.lower() == "awr" else "Statspack"
            analysis_sources.append(report_type_text)
        
        # PL/SQL 분석 여부
        total_plsql = getattr(metrics, 'total_plsql_count', 0) or 0
        if total_plsql > 0:
            analysis_sources.append("PL/SQL")
        
        # SQL 분석 여부
        total_sql = getattr(metrics, 'total_sql_count', 0) or 0
        if total_sql > 0:
            analysis_sources.append("SQL")
        
        if language == "ko":
            title = f"# {db_name} Oracle 마이그레이션 전략 리포트"
            
            header_lines = [
                title,
                "",
                "---",
                "",
                "## 리포트 개요",
                "",
                f"**추천 타겟**: {target_db}",
                "",
                f"**추천 신뢰도**: {confidence_pct}%",
                "",
                f"**소스 데이터베이스**: {db_name}" + (f" (Oracle {db_version})" if db_version else ""),
                "",
                f"**분석 소스**: {', '.join(analysis_sources) if analysis_sources else '없음'}",
                "",
                f"**분석 일시**: {analysis_date}",
            ]
            
            return "\n".join(header_lines)
        else:
            title = f"# {db_name} Oracle Migration Strategy Report"
            
            header_lines = [
                title,
                "",
                "---",
                "",
                "## Report Overview",
                "",
                f"**Recommended Target**: {target_db}",
                "",
                f"**Confidence**: {confidence_pct}%",
                "",
                f"**Source Database**: {db_name}" + (f" (Oracle {db_version})" if db_version else ""),
                "",
                f"**Analysis Sources**: {', '.join(analysis_sources) if analysis_sources else 'None'}",
                "",
                f"**Analysis Date**: {analysis_date}",
            ]
            
            return "\n".join(header_lines)
    
    def _format_strategy_with_rationale(
        self,
        recommendation: MigrationRecommendation,
        language: str
    ) -> str:
        """추천 전략과 근거를 통합하여 포맷팅"""
        strategy_section = self._format_strategy(
            recommendation, recommendation.metrics, language
        )
        rationale_section = self._format_rationales(
            recommendation.rationales, recommendation.metrics, language
        )
        
        # 전략과 근거를 하나의 섹션으로 통합
        return f"{strategy_section}\n\n{rationale_section}"
    
    def _format_appendix_header(self, language: str) -> str:
        """부록 헤더 포맷팅"""
        if language == "ko":
            return """---

# 📎 부록: 기술 상세 정보

> 이 섹션은 기술팀을 위한 상세 정보입니다. 의사결정에는 위 섹션의 정보로 충분합니다."""
        else:
            return """---

# 📎 Appendix: Technical Details

> This section contains detailed technical information for the engineering team."""


__all__ = ['MarkdownReportFormatter']
