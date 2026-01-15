"""
마이그레이션 추천 시스템

DBCSI 분석기와 SQL/PL-SQL 분석기의 결과를 통합하여
최적의 마이그레이션 전략을 추천하는 시스템입니다.

사용 예제:
    >>> from migration_recommendation import (
    ...     AnalysisResultIntegrator,
    ...     MigrationDecisionEngine,
    ...     RecommendationReportGenerator,
    ...     MarkdownReportFormatter
    ... )
    >>> 
    >>> # 1. 분석 결과 통합
    >>> integrator = AnalysisResultIntegrator()
    >>> integrated_result = integrator.integrate(
    ...     dbcsi_result=dbcsi_data,
    ...     sql_analysis=sql_results,
    ...     plsql_analysis=plsql_results
    ... )
    >>> 
    >>> # 2. 마이그레이션 전략 결정 및 리포트 생성
    >>> decision_engine = MigrationDecisionEngine()
    >>> report_generator = RecommendationReportGenerator(decision_engine)
    >>> recommendation = report_generator.generate_recommendation(integrated_result)
    >>> 
    >>> # 3. 리포트 포맷팅
    >>> formatter = MarkdownReportFormatter()
    >>> markdown_report = formatter.format(recommendation, language="ko")
    >>> print(markdown_report)

주요 컴포넌트:
    - AnalysisResultIntegrator: DBCSI와 SQL/PL-SQL 분석 결과 통합
    - MigrationDecisionEngine: 의사결정 트리 기반 전략 추천
    - RecommendationReportGenerator: 추천 리포트 생성
    - MarkdownReportFormatter: Markdown 형식 변환
    - JSONReportFormatter: JSON 형식 변환
"""

# 데이터 모델
from .data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationRecommendation,
    MigrationStrategy,
    Rationale,
    AlternativeStrategy,
    Risk,
    MigrationRoadmap,
    RoadmapPhase,
    ExecutiveSummary,
)

# 핵심 컴포넌트
from .integrator import AnalysisResultIntegrator
from .decision_engine import MigrationDecisionEngine
from .report_generator import RecommendationReportGenerator
from .formatters import MarkdownReportFormatter, JSONReportFormatter

__all__ = [
    # 데이터 모델
    "IntegratedAnalysisResult",
    "AnalysisMetrics",
    "MigrationRecommendation",
    "MigrationStrategy",
    "Rationale",
    "AlternativeStrategy",
    "Risk",
    "MigrationRoadmap",
    "RoadmapPhase",
    "ExecutiveSummary",
    # 핵심 컴포넌트
    "AnalysisResultIntegrator",
    "MigrationDecisionEngine",
    "RecommendationReportGenerator",
    "MarkdownReportFormatter",
    "JSONReportFormatter",
]
