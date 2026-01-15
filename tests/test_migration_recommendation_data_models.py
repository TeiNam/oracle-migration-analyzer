"""
마이그레이션 추천 데이터 모델 Property 테스트

Property 1: 분석 결과 통합 완전성
Validates: Requirements 1.1
"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime

from src.migration_recommendation.data_models import (
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


# Hypothesis 전략 정의

@st.composite
def analysis_metrics_strategy(draw):
    """AnalysisMetrics 생성 전략"""
    total_sql = draw(st.integers(min_value=1, max_value=100))
    total_plsql = draw(st.integers(min_value=0, max_value=100))
    high_sql = draw(st.integers(min_value=0, max_value=total_sql))
    high_plsql = draw(st.integers(min_value=0, max_value=total_plsql))
    
    total_objects = total_sql + total_plsql
    high_objects = high_sql + high_plsql
    ratio = high_objects / total_objects if total_objects > 0 else 0.0
    
    return AnalysisMetrics(
        avg_cpu_usage=draw(st.floats(min_value=0.0, max_value=100.0)),
        avg_io_load=draw(st.floats(min_value=0.0, max_value=10000.0)),
        avg_memory_usage=draw(st.floats(min_value=0.0, max_value=1000.0)),
        avg_sql_complexity=draw(st.floats(min_value=0.0, max_value=10.0)),
        avg_plsql_complexity=draw(st.floats(min_value=0.0, max_value=10.0)),
        high_complexity_sql_count=high_sql,
        high_complexity_plsql_count=high_plsql,
        total_sql_count=total_sql,
        total_plsql_count=total_plsql,
        high_complexity_ratio=ratio,
        bulk_operation_count=draw(st.integers(min_value=0, max_value=50)),
        rac_detected=draw(st.booleans()),
    )


@st.composite
def sql_analysis_list_strategy(draw):
    """SQL 분석 결과 리스트 생성 전략"""
    # 간단한 딕셔너리로 대체 (실제 SQLAnalysisResult 대신)
    count = draw(st.integers(min_value=0, max_value=20))
    return [
        {
            "query": f"SELECT * FROM table_{i}",
            "complexity": draw(st.floats(min_value=0.0, max_value=10.0))
        }
        for i in range(count)
    ]


@st.composite
def plsql_analysis_list_strategy(draw):
    """PL/SQL 분석 결과 리스트 생성 전략"""
    # 간단한 딕셔너리로 대체 (실제 PLSQLAnalysisResult 대신)
    count = draw(st.integers(min_value=0, max_value=20))
    return [
        {
            "code": f"CREATE PROCEDURE proc_{i}",
            "complexity": draw(st.floats(min_value=0.0, max_value=10.0)),
            "bulk_operations": draw(st.integers(min_value=0, max_value=5))
        }
        for i in range(count)
    ]


@given(
    metrics=analysis_metrics_strategy(),
    sql_analysis=sql_analysis_list_strategy(),
    plsql_analysis=plsql_analysis_list_strategy(),
)
def test_property_1_integrated_analysis_completeness(metrics, sql_analysis, plsql_analysis):
    """
    Property 1: 분석 결과 통합 완전성
    Feature: migration-recommendation, Property 1: For any valid DBCSI result and 
    SQL/PL-SQL analysis results, integrating them should produce a result that 
    contains all input data
    Validates: Requirements 1.1
    
    임의의 유효한 DBCSI 결과와 SQL/PL-SQL 분석 결과를 통합하면,
    모든 입력 데이터를 포함하는 결과가 생성되어야 합니다.
    """
    # DBCSI 결과는 None일 수 있음 (선택적)
    dbcsi_result = None
    
    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # IntegratedAnalysisResult 생성
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=dbcsi_result,
        sql_analysis=sql_analysis,
        plsql_analysis=plsql_analysis,
        metrics=metrics,
        analysis_timestamp=timestamp,
    )
    
    # 검증: 모든 입력 데이터가 포함되어야 함
    assert integrated_result.dbcsi_result == dbcsi_result
    assert integrated_result.sql_analysis == sql_analysis
    assert integrated_result.plsql_analysis == plsql_analysis
    assert integrated_result.metrics == metrics
    assert integrated_result.analysis_timestamp == timestamp
    
    # 메트릭 검증
    assert integrated_result.metrics.avg_cpu_usage >= 0.0
    assert integrated_result.metrics.avg_io_load >= 0.0
    assert integrated_result.metrics.avg_memory_usage >= 0.0
    assert integrated_result.metrics.avg_sql_complexity >= 0.0
    assert integrated_result.metrics.avg_plsql_complexity >= 0.0
    assert integrated_result.metrics.high_complexity_sql_count >= 0
    assert integrated_result.metrics.high_complexity_plsql_count >= 0
    assert integrated_result.metrics.total_sql_count >= 0
    assert integrated_result.metrics.total_plsql_count >= 0
    assert 0.0 <= integrated_result.metrics.high_complexity_ratio <= 1.0
    assert integrated_result.metrics.bulk_operation_count >= 0


# 단위 테스트

def test_analysis_metrics_creation():
    """AnalysisMetrics 생성 테스트"""
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=1000.0,
        avg_memory_usage=100.0,
        avg_sql_complexity=5.5,
        avg_plsql_complexity=6.0,
        high_complexity_sql_count=10,
        high_complexity_plsql_count=5,
        total_sql_count=50,
        total_plsql_count=20,
        high_complexity_ratio=0.21,
        bulk_operation_count=15,
        rac_detected=True,
    )
    
    assert metrics.avg_cpu_usage == 50.0
    assert metrics.avg_sql_complexity == 5.5
    assert metrics.high_complexity_ratio == 0.21


def test_integrated_analysis_result_creation():
    """IntegratedAnalysisResult 생성 테스트"""
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=1000.0,
        avg_memory_usage=100.0,
        avg_sql_complexity=5.5,
        avg_plsql_complexity=6.0,
        high_complexity_sql_count=10,
        high_complexity_plsql_count=5,
        total_sql_count=50,
        total_plsql_count=20,
        high_complexity_ratio=0.21,
        bulk_operation_count=15,
        rac_detected=False,
    )
    
    result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00",
    )
    
    assert result.metrics == metrics
    assert result.analysis_timestamp == "2026-01-15 12:00:00"


def test_migration_strategy_enum():
    """MigrationStrategy Enum 테스트"""
    assert MigrationStrategy.REPLATFORM.value == "replatform"
    assert MigrationStrategy.REFACTOR_MYSQL.value == "refactor_mysql"
    assert MigrationStrategy.REFACTOR_POSTGRESQL.value == "refactor_postgresql"


def test_rationale_creation():
    """Rationale 생성 테스트"""
    rationale = Rationale(
        category="complexity",
        reason="평균 복잡도가 높습니다",
        supporting_data={"avg_complexity": 7.5},
    )
    
    assert rationale.category == "complexity"
    assert rationale.reason == "평균 복잡도가 높습니다"
    assert rationale.supporting_data["avg_complexity"] == 7.5


def test_alternative_strategy_creation():
    """AlternativeStrategy 생성 테스트"""
    alternative = AlternativeStrategy(
        strategy=MigrationStrategy.REFACTOR_MYSQL,
        pros=["비용 절감", "클라우드 네이티브"],
        cons=["PL/SQL 이관 필요"],
        considerations=["충분한 테스트 기간 확보"],
    )
    
    assert alternative.strategy == MigrationStrategy.REFACTOR_MYSQL
    assert len(alternative.pros) == 2
    assert len(alternative.cons) == 1


def test_risk_creation():
    """Risk 생성 테스트"""
    risk = Risk(
        category="technical",
        description="PL/SQL 변환 작업 필요",
        severity="medium",
        mitigation="단계적 이관 계획 수립",
    )
    
    assert risk.category == "technical"
    assert risk.severity == "medium"


def test_roadmap_phase_creation():
    """RoadmapPhase 생성 테스트"""
    phase = RoadmapPhase(
        phase_number=1,
        phase_name="사전 평가",
        tasks=["요구사항 분석", "아키텍처 설계"],
        estimated_duration="2-3주",
        required_resources=["DBA", "아키텍트"],
    )
    
    assert phase.phase_number == 1
    assert len(phase.tasks) == 2
    assert len(phase.required_resources) == 2


def test_migration_roadmap_creation():
    """MigrationRoadmap 생성 테스트"""
    phase1 = RoadmapPhase(
        phase_number=1,
        phase_name="사전 평가",
        tasks=["요구사항 분석"],
        estimated_duration="2주",
        required_resources=["DBA"],
    )
    
    roadmap = MigrationRoadmap(
        phases=[phase1],
        total_estimated_duration="8-12주",
    )
    
    assert len(roadmap.phases) == 1
    assert roadmap.total_estimated_duration == "8-12주"


def test_executive_summary_creation():
    """ExecutiveSummary 생성 테스트"""
    summary = ExecutiveSummary(
        recommended_strategy="replatform",
        estimated_duration="8-12주",
        key_benefits=["코드 변경 최소화", "빠른 마이그레이션"],
        key_risks=["라이선스 비용", "Single 인스턴스 제약"],
        summary_text="RDS Oracle SE2로의 Replatform을 추천합니다.",
    )
    
    assert summary.recommended_strategy == "replatform"
    assert len(summary.key_benefits) == 2
    assert len(summary.key_risks) == 2


def test_migration_recommendation_creation():
    """MigrationRecommendation 생성 테스트"""
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=1000.0,
        avg_memory_usage=100.0,
        avg_sql_complexity=7.5,
        avg_plsql_complexity=8.0,
        high_complexity_sql_count=30,
        high_complexity_plsql_count=15,
        total_sql_count=50,
        total_plsql_count=20,
        high_complexity_ratio=0.64,
        bulk_operation_count=5,
        rac_detected=True,
    )
    
    rationale = Rationale(
        category="complexity",
        reason="평균 복잡도가 7.0 이상입니다",
        supporting_data={"avg_sql": 7.5, "avg_plsql": 8.0},
    )
    
    alternative = AlternativeStrategy(
        strategy=MigrationStrategy.REFACTOR_POSTGRESQL,
        pros=["PL/pgSQL 호환성"],
        cons=["변환 작업 필요"],
        considerations=["미지원 기능 확인"],
    )
    
    risk = Risk(
        category="operational",
        description="Single 인스턴스 제약",
        severity="high",
        mitigation="Multi-AZ 배포",
    )
    
    phase = RoadmapPhase(
        phase_number=1,
        phase_name="사전 평가",
        tasks=["요구사항 분석"],
        estimated_duration="2주",
        required_resources=["DBA"],
    )
    
    roadmap = MigrationRoadmap(
        phases=[phase],
        total_estimated_duration="8-12주",
    )
    
    summary = ExecutiveSummary(
        recommended_strategy="replatform",
        estimated_duration="8-12주",
        key_benefits=["코드 변경 최소화"],
        key_risks=["라이선스 비용"],
        summary_text="Replatform 추천",
    )
    
    recommendation = MigrationRecommendation(
        recommended_strategy=MigrationStrategy.REPLATFORM,
        confidence_level="high",
        rationales=[rationale],
        alternative_strategies=[alternative],
        risks=[risk],
        roadmap=roadmap,
        executive_summary=summary,
        metrics=metrics,
    )
    
    assert recommendation.recommended_strategy == MigrationStrategy.REPLATFORM
    assert recommendation.confidence_level == "high"
    assert len(recommendation.rationales) == 1
    assert len(recommendation.alternative_strategies) == 1
    assert len(recommendation.risks) == 1
    assert recommendation.metrics == metrics
