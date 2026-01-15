"""
마이그레이션 의사결정 엔진 테스트

Property-based 테스트를 통해 의사결정 로직의 일관성을 검증합니다.
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy
)
from src.migration_recommendation.decision_engine import MigrationDecisionEngine


# 테스트용 헬퍼 함수
def create_integrated_result(metrics: AnalysisMetrics) -> IntegratedAnalysisResult:
    """테스트용 IntegratedAnalysisResult 생성"""
    return IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp=datetime.now().isoformat()
    )


# Property 3: Replatform 조건 일관성
@given(
    avg_sql_complexity=st.floats(min_value=7.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_replatform_condition_high_sql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 3: Replatform 조건 일관성 - 높은 SQL 복잡도
    
    Feature: migration-recommendation, Property 3: For any analysis result where 
    평균 SQL 복잡도 >= 7.0, the system should recommend Replatform
    
    Validates: Requirements 2.2, 2.3, 2.4
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REPLATFORM, \
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Replatform을 추천해야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=7.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_replatform_condition_high_plsql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 3: Replatform 조건 일관성 - 높은 PL/SQL 복잡도
    
    Feature: migration-recommendation, Property 3: For any analysis result where 
    평균 PL/SQL 복잡도 >= 7.0, the system should recommend Replatform
    
    Validates: Requirements 2.2, 2.3, 2.4
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REPLATFORM, \
        f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Replatform을 추천해야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.3, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_replatform_condition_high_complexity_ratio(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 3: Replatform 조건 일관성 - 높은 복잡 오브젝트 비율
    
    Feature: migration-recommendation, Property 3: For any analysis result where 
    복잡 오브젝트 비율 >= 30%, the system should recommend Replatform
    
    Validates: Requirements 2.2, 2.3, 2.4
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REPLATFORM, \
        f"복잡 오브젝트 비율 {high_complexity_ratio*100:.1f}%일 때 Replatform을 추천해야 합니다"



# Property 4: Aurora MySQL 조건 일관성
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=0, max_value=49),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=9)
)
def test_aurora_mysql_condition_consistency(
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count,
    high_complexity_ratio,
    bulk_operation_count
):
    """
    Property 4: Aurora MySQL 조건 일관성
    
    Feature: migration-recommendation, Property 4: For any analysis result where 
    평균 SQL 복잡도 <= 5.0 and 평균 PL/SQL 복잡도 <= 5.0 and PL/SQL 오브젝트 < 50개,
    the system should recommend Aurora MySQL
    
    Validates: Requirements 3.1, 3.2
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REFACTOR_MYSQL, \
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}, PL/SQL 복잡도 {avg_plsql_complexity:.2f}, " \
        f"PL/SQL 오브젝트 {total_plsql_count}개일 때 Aurora MySQL을 추천해야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=5.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=0, max_value=49),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False)
)
def test_aurora_mysql_not_recommended_high_sql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count,
    high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - SQL 복잡도 높을 때 제외
    
    Feature: migration-recommendation, Property 4: For any analysis result where 
    평균 SQL 복잡도 > 5.0, the system should NOT recommend Aurora MySQL
    
    Validates: Requirements 3.1, 3.2
    """
    engine = MigrationDecisionEngine()
    
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
        bulk_operation_count=0,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy != MigrationStrategy.REFACTOR_MYSQL, \
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Aurora MySQL을 추천하지 않아야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=5.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=0, max_value=49),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False)
)
def test_aurora_mysql_not_recommended_high_plsql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count,
    high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - PL/SQL 복잡도 높을 때 제외
    
    Feature: migration-recommendation, Property 4: For any analysis result where 
    평균 PL/SQL 복잡도 > 5.0, the system should NOT recommend Aurora MySQL
    
    Validates: Requirements 3.1, 3.2
    """
    engine = MigrationDecisionEngine()
    
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
        bulk_operation_count=0,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy != MigrationStrategy.REFACTOR_MYSQL, \
        f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Aurora MySQL을 추천하지 않아야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=50, max_value=200),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False)
)
def test_aurora_mysql_not_recommended_many_plsql_objects(
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count,
    high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - PL/SQL 오브젝트 많을 때 제외
    
    Feature: migration-recommendation, Property 4: For any analysis result where 
    PL/SQL 오브젝트 >= 50개, the system should NOT recommend Aurora MySQL
    
    Validates: Requirements 3.1, 3.2
    """
    engine = MigrationDecisionEngine()
    
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
        bulk_operation_count=0,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy != MigrationStrategy.REFACTOR_MYSQL, \
        f"PL/SQL 오브젝트 {total_plsql_count}개일 때 Aurora MySQL을 추천하지 않아야 합니다"



# Property 5: Aurora PostgreSQL 조건 일관성
@given(
    bulk_operation_count=st.integers(min_value=10, max_value=100),
    avg_sql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_aurora_postgresql_condition_many_bulk_operations(
    bulk_operation_count,
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    total_plsql_count
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - BULK 연산 많을 때
    
    Feature: migration-recommendation, Property 5: For any analysis result where 
    BULK 연산 >= 10개 and 복잡도 < 7.0, the system should recommend Aurora PostgreSQL
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REFACTOR_POSTGRESQL, \
        f"BULK 연산 {bulk_operation_count}개일 때 Aurora PostgreSQL을 추천해야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=5.01, max_value=6.9, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=9),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_aurora_postgresql_condition_medium_sql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - 중간 SQL 복잡도
    
    Feature: migration-recommendation, Property 5: For any analysis result where 
    5.0 < 평균 SQL 복잡도 < 7.0, the system should recommend Aurora PostgreSQL
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REFACTOR_POSTGRESQL, \
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Aurora PostgreSQL을 추천해야 합니다"


@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=5.01, max_value=6.9, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=9),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_aurora_postgresql_condition_complex_plsql(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - 복잡한 PL/SQL
    
    Feature: migration-recommendation, Property 5: For any analysis result where 
    5.0 < 평균 PL/SQL 복잡도 < 7.0, the system should recommend Aurora PostgreSQL
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    assert strategy == MigrationStrategy.REFACTOR_POSTGRESQL, \
        f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Aurora PostgreSQL을 추천해야 합니다"



# Property 18: 의사결정 우선순위
@given(
    avg_sql_complexity=st.floats(min_value=7.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_decision_priority_complexity_first(
    avg_sql_complexity,
    avg_plsql_complexity,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 18: 의사결정 우선순위 - 코드 복잡도 최우선
    
    Feature: migration-recommendation, Property 18: For any analysis result,
    code complexity should be evaluated before other factors in the decision tree
    
    복잡도가 7.0 이상이면 다른 조건과 관계없이 Replatform을 추천해야 합니다.
    
    Validates: Requirements 10.1
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    # 복잡도가 7.0 이상이면 BULK 연산이나 PL/SQL 개수와 관계없이 Replatform
    assert strategy == MigrationStrategy.REPLATFORM, \
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 다른 조건과 관계없이 Replatform을 추천해야 합니다"


@given(
    high_complexity_ratio=st.floats(min_value=0.3, max_value=1.0, allow_nan=False, allow_infinity=False),
    avg_sql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_decision_priority_high_complexity_ratio_first(
    high_complexity_ratio,
    avg_sql_complexity,
    avg_plsql_complexity,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 18: 의사결정 우선순위 - 복잡 오브젝트 비율 우선
    
    Feature: migration-recommendation, Property 18: For any analysis result,
    high complexity ratio should be evaluated before MySQL/PostgreSQL conditions
    
    복잡 오브젝트 비율이 30% 이상이면 다른 조건과 관계없이 Replatform을 추천해야 합니다.
    
    Validates: Requirements 10.1
    """
    engine = MigrationDecisionEngine()
    
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
    strategy = engine.decide_strategy(integrated_result)
    
    # 복잡 오브젝트 비율이 30% 이상이면 다른 조건과 관계없이 Replatform
    assert strategy == MigrationStrategy.REPLATFORM, \
        f"복잡 오브젝트 비율 {high_complexity_ratio*100:.1f}%일 때 다른 조건과 관계없이 Replatform을 추천해야 합니다"
