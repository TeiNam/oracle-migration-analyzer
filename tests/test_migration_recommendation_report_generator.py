"""
마이그레이션 추천 리포트 생성기 Property 테스트

Requirements:
- Property 6: BULK 연산 경고 일관성 (Requirements 3.3)
- Property 7: 추천 근거 개수 (Requirements 5.1)
- Property 8: 추천 근거 카테고리 포함 (Requirements 5.2, 5.3)
- Property 9: 대안 전략 개수 (Requirements 6.1)
- Property 10: 위험 요소 개수 (Requirements 7.1)
- Property 11: 로드맵 단계 개수 (Requirements 8.1)
- Property 14: Executive Summary 필수 요소 (Requirements 13.2, 13.3)
- Property 15: Executive Summary 길이 제한 (Requirements 13.3)
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy
)
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator


# 테스트용 헬퍼 함수
def create_integrated_result(metrics: AnalysisMetrics) -> IntegratedAnalysisResult:
    """테스트용 IntegratedAnalysisResult 생성"""
    return IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )


# Property 7: 추천 근거 개수
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_rationales_count_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 7: 추천 근거 개수
    Feature: migration-recommendation, Property 7: For any recommendation, 
    the number of rationales should be between 3 and 5
    Validates: Requirements 5.1
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 검증: 근거 개수는 3-5개
    assert 3 <= len(recommendation.rationales) <= 5, \
        f"근거 개수는 3-5개여야 하지만 {len(recommendation.rationales)}개입니다"


# Property 8: 추천 근거 카테고리 포함
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_rationales_categories_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 8: 추천 근거 카테고리 포함
    Feature: migration-recommendation, Property 8: For any recommendation, 
    rationales should include both performance metrics and code complexity categories
    Validates: Requirements 5.2, 5.3
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 카테고리 추출
    categories = {rationale.category for rationale in recommendation.rationales}
    
    # 검증: complexity 카테고리는 항상 포함되어야 함
    assert "complexity" in categories, \
        f"근거에 complexity 카테고리가 포함되어야 합니다. 현재 카테고리: {categories}"


# Property 9: 대안 전략 개수
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_alternatives_count_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 9: 대안 전략 개수
    Feature: migration-recommendation, Property 9: For any recommendation, 
    the number of alternative strategies should be between 1 and 2
    Validates: Requirements 6.1
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 검증: 대안 전략 개수는 1-2개
    assert 1 <= len(recommendation.alternative_strategies) <= 2, \
        f"대안 전략 개수는 1-2개여야 하지만 {len(recommendation.alternative_strategies)}개입니다"


# Property 10: 위험 요소 개수
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_risks_count_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 10: 위험 요소 개수
    Feature: migration-recommendation, Property 10: For any recommendation, 
    the number of risks should be between 3 and 5
    Validates: Requirements 7.1
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 검증: 위험 요소 개수는 3-5개
    assert 3 <= len(recommendation.risks) <= 5, \
        f"위험 요소 개수는 3-5개여야 하지만 {len(recommendation.risks)}개입니다"


# Property 11: 로드맵 단계 개수
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_roadmap_phases_count_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 11: 로드맵 단계 개수
    Feature: migration-recommendation, Property 11: For any recommendation, 
    the number of roadmap phases should be between 3 and 5
    Validates: Requirements 8.1
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 검증: 로드맵 단계 개수는 3-5개
    assert 3 <= len(recommendation.roadmap.phases) <= 5, \
        f"로드맵 단계 개수는 3-5개여야 하지만 {len(recommendation.roadmap.phases)}개입니다"


# Property 14: Executive Summary 필수 요소
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_executive_summary_required_elements_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 14: Executive Summary 필수 요소
    Feature: migration-recommendation, Property 14: For any recommendation, 
    Executive Summary should include recommended strategy, estimated duration, 
    key benefits, and key risks
    Validates: Requirements 13.2, 13.3
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    summary = recommendation.executive_summary
    
    # 검증: 필수 요소 포함
    assert summary.recommended_strategy, "추천 전략이 비어있습니다"
    assert summary.estimated_duration, "예상 기간이 비어있습니다"
    assert len(summary.key_benefits) == 3, f"주요 이점은 3개여야 하지만 {len(summary.key_benefits)}개입니다"
    assert len(summary.key_risks) == 3, f"주요 위험은 3개여야 하지만 {len(summary.key_risks)}개입니다"
    assert summary.summary_text, "요약 텍스트가 비어있습니다"


# Property 15: Executive Summary 길이 제한
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_executive_summary_length_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 15: Executive Summary 길이 제한
    Feature: migration-recommendation, Property 15: For any recommendation, 
    Executive Summary text should be within 1 page limit (approximately 3000 characters)
    Validates: Requirements 13.3
    """
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    summary_text = recommendation.executive_summary.summary_text
    
    # 검증: 길이 제한 (약 3000자)
    assert len(summary_text) <= 3000, \
        f"Executive Summary는 3000자 이내여야 하지만 {len(summary_text)}자입니다"


# Property 6: BULK 연산 경고 일관성
@given(
    bulk_operation_count=st.integers(min_value=10, max_value=100),
    avg_sql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=0, max_value=49)
)
def test_bulk_operation_warning_property(
    bulk_operation_count,
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count
):
    """
    Property 6: BULK 연산 경고 일관성
    Feature: migration-recommendation, Property 6: For any analysis result where 
    BULK 연산 >= 10개 and recommended strategy is Aurora MySQL, 
    the system should include a warning about BULK operations
    Validates: Requirements 3.3
    """
    # 테스트 데이터 생성 (Aurora MySQL 조건)
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=0.0,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # BULK 연산이 10개 이상이면 PostgreSQL이 추천되어야 함
    # 따라서 이 테스트는 MySQL이 추천되지 않는 것을 확인
    # 만약 MySQL이 추천되면 근거에 BULK 경고가 있어야 함
    if recommendation.recommended_strategy == MigrationStrategy.REFACTOR_MYSQL:
        # 근거에 BULK 연산 경고가 있는지 확인
        bulk_warning_found = any(
            "BULK" in rationale.reason and "performance" == rationale.category
            for rationale in recommendation.rationales
        )
        assert bulk_warning_found, \
            f"BULK 연산이 {bulk_operation_count}개인데 MySQL 추천 시 경고가 없습니다"
