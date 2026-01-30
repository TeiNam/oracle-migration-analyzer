"""
마이그레이션 의사결정 엔진 테스트

Property-based 테스트를 통해 의사결정 로직의 일관성을 검증합니다.

임계값 (AI 시대 기준 상향 조정):
- SQL 복잡도: 7.5 이상 → Replatform
- PL/SQL 복잡도: 7.0 이상 → Replatform
- 고난이도 비율: 25% 이상 (모수 70개 이상) → Replatform
- 고난이도 개수: 50개 이상 → Replatform
- PL/SQL 개수: 500개 이상 → Replatform
- 코드량 + 복잡도: 20만줄 + 7.5 → Replatform
- 고위험 Oracle 패키지: 50회 이상 → Replatform
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy,
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
        analysis_timestamp=datetime.now().isoformat(),
    )


# Property 3: Replatform 조건 일관성 - 높은 SQL 복잡도
@given(
    avg_sql_complexity=st.floats(
        min_value=7.5, max_value=10.0, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_replatform_condition_high_sql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count,
):
    """
    Property 3: Replatform 조건 일관성 - 높은 SQL 복잡도

    평균 SQL 복잡도 >= 7.5이면 Replatform을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REPLATFORM
    ), f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Replatform을 추천해야 합니다"


# Property 3: Replatform 조건 일관성 - 높은 PL/SQL 복잡도
@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=7.0, max_value=10.0, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_replatform_condition_high_plsql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count,
):
    """
    Property 3: Replatform 조건 일관성 - 높은 PL/SQL 복잡도

    평균 PL/SQL 복잡도 >= 7.0이면 Replatform을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REPLATFORM
    ), f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Replatform을 추천해야 합니다"


# Property 3: Replatform 조건 일관성 - 높은 복잡 오브젝트 비율 (모수 70개 이상)
@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.25, max_value=1.0, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    # 모수 70개 이상이어야 비율 조건 적용
    total_sql_count=st.integers(min_value=35, max_value=100),
    total_plsql_count=st.integers(min_value=35, max_value=100),
)
def test_replatform_condition_high_complexity_ratio(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_sql_count,
    total_plsql_count,
):
    """
    Property 3: Replatform 조건 일관성 - 높은 복잡 오브젝트 비율

    복잡 오브젝트 비율 >= 25% (모수 70개 이상)이면 Replatform을 추천해야 합니다.
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
        total_sql_count=total_sql_count,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=high_complexity_ratio,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REPLATFORM
    ), f"복잡 오브젝트 비율 {high_complexity_ratio*100:.1f}%일 때 Replatform을 추천해야 합니다"


# Property 3: Replatform 조건 일관성 - 고난이도 오브젝트 개수 50개 이상
@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_sql_count=st.integers(min_value=25, max_value=100),
    high_complexity_plsql_count=st.integers(min_value=25, max_value=100),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_replatform_condition_high_complexity_count(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_sql_count,
    high_complexity_plsql_count,
    bulk_operation_count,
    total_plsql_count,
):
    """
    Property 3: Replatform 조건 일관성 - 고난이도 오브젝트 개수

    고난이도 오브젝트 개수 >= 50개이면 Replatform을 추천해야 합니다.
    """
    engine = MigrationDecisionEngine()

    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=high_complexity_sql_count,
        high_complexity_plsql_count=high_complexity_plsql_count,
        total_sql_count=100,
        total_plsql_count=total_plsql_count,
        high_complexity_ratio=0.1,
        bulk_operation_count=bulk_operation_count,
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    total_high = high_complexity_sql_count + high_complexity_plsql_count
    assert (
        strategy == MigrationStrategy.REPLATFORM
    ), f"고난이도 오브젝트 {total_high}개일 때 Replatform을 추천해야 합니다"


# Property 4: Aurora MySQL 조건 일관성
@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=4.0, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=3.5, allow_nan=False, allow_infinity=False
    ),
    total_plsql_count=st.integers(min_value=0, max_value=19),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=9),
)
def test_aurora_mysql_condition_consistency(
    avg_sql_complexity,
    avg_plsql_complexity,
    total_plsql_count,
    high_complexity_ratio,
    bulk_operation_count,
):
    """
    Property 4: Aurora MySQL 조건 일관성

    평균 SQL 복잡도 <= 4.0 and 평균 PL/SQL 복잡도 <= 3.5 and PL/SQL 오브젝트 < 20개이면
    Aurora MySQL을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert strategy == MigrationStrategy.REFACTOR_MYSQL, (
        f"평균 SQL 복잡도 {avg_sql_complexity:.2f}, PL/SQL 복잡도 {avg_plsql_complexity:.2f}, "
        f"PL/SQL 오브젝트 {total_plsql_count}개일 때 Aurora MySQL을 추천해야 합니다"
    )


@given(
    avg_sql_complexity=st.floats(
        min_value=4.01, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=3.5, allow_nan=False, allow_infinity=False
    ),
    total_plsql_count=st.integers(min_value=0, max_value=19),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
)
def test_aurora_mysql_not_recommended_high_sql_complexity(
    avg_sql_complexity, avg_plsql_complexity, total_plsql_count, high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - SQL 복잡도 높을 때 제외

    평균 SQL 복잡도 > 4.0이면 Aurora MySQL을 추천하지 않아야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy != MigrationStrategy.REFACTOR_MYSQL
    ), f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Aurora MySQL을 추천하지 않아야 합니다"


@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=4.0, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=3.51, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    total_plsql_count=st.integers(min_value=0, max_value=19),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
)
def test_aurora_mysql_not_recommended_high_plsql_complexity(
    avg_sql_complexity, avg_plsql_complexity, total_plsql_count, high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - PL/SQL 복잡도 높을 때 제외

    평균 PL/SQL 복잡도 > 3.5이면 Aurora MySQL을 추천하지 않아야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy != MigrationStrategy.REFACTOR_MYSQL
    ), f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Aurora MySQL을 추천하지 않아야 합니다"


@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=4.0, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=3.5, allow_nan=False, allow_infinity=False
    ),
    total_plsql_count=st.integers(min_value=20, max_value=200),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
)
def test_aurora_mysql_not_recommended_many_plsql_objects(
    avg_sql_complexity, avg_plsql_complexity, total_plsql_count, high_complexity_ratio
):
    """
    Property 4: Aurora MySQL 조건 일관성 - PL/SQL 오브젝트 많을 때 제외

    PL/SQL 오브젝트 >= 20개이면 Aurora MySQL을 추천하지 않아야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy != MigrationStrategy.REFACTOR_MYSQL
    ), f"PL/SQL 오브젝트 {total_plsql_count}개일 때 Aurora MySQL을 추천하지 않아야 합니다"


# Property 5: Aurora PostgreSQL 조건 일관성 - BULK 연산 많을 때
@given(
    bulk_operation_count=st.integers(min_value=10, max_value=100),
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_aurora_postgresql_condition_many_bulk_operations(
    bulk_operation_count,
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    total_plsql_count,
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - BULK 연산 많을 때

    BULK 연산 >= 10개 and 복잡도 < Replatform 임계값이면 Aurora PostgreSQL을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REFACTOR_POSTGRESQL
    ), f"BULK 연산 {bulk_operation_count}개일 때 Aurora PostgreSQL을 추천해야 합니다"


# Property 5: Aurora PostgreSQL 조건 일관성 - 중간 SQL 복잡도
@given(
    avg_sql_complexity=st.floats(
        min_value=4.01, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=9),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_aurora_postgresql_condition_medium_sql_complexity(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count,
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - 중간 SQL 복잡도

    4.0 < 평균 SQL 복잡도 < 7.5이면 Aurora PostgreSQL을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REFACTOR_POSTGRESQL
    ), f"평균 SQL 복잡도 {avg_sql_complexity:.2f}일 때 Aurora PostgreSQL을 추천해야 합니다"


# Property 5: Aurora PostgreSQL 조건 일관성 - 복잡한 PL/SQL
@given(
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=3.51, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
    high_complexity_ratio=st.floats(
        min_value=0.0, max_value=0.24, allow_nan=False, allow_infinity=False
    ),
    bulk_operation_count=st.integers(min_value=0, max_value=9),
    total_plsql_count=st.integers(min_value=0, max_value=200),
)
def test_aurora_postgresql_condition_complex_plsql(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count,
):
    """
    Property 5: Aurora PostgreSQL 조건 일관성 - 복잡한 PL/SQL

    3.5 < 평균 PL/SQL 복잡도 < 7.0이면 Aurora PostgreSQL을 추천해야 합니다.
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
        rac_detected=False,
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REFACTOR_POSTGRESQL
    ), f"평균 PL/SQL 복잡도 {avg_plsql_complexity:.2f}일 때 Aurora PostgreSQL을 추천해야 합니다"


# Property 6: Replatform 조건 일관성 - 고위험 Oracle 패키지
@given(
    high_risk_package_count=st.integers(min_value=50, max_value=200),
    avg_sql_complexity=st.floats(
        min_value=0.0, max_value=7.4, allow_nan=False, allow_infinity=False
    ),
    avg_plsql_complexity=st.floats(
        min_value=0.0, max_value=6.9, allow_nan=False, allow_infinity=False
    ),
)
def test_replatform_condition_high_risk_oracle_packages(
    high_risk_package_count,
    avg_sql_complexity,
    avg_plsql_complexity,
):
    """
    Property 6: Replatform 조건 일관성 - 고위험 Oracle 패키지

    고위험 Oracle 패키지(UTL_FILE, UTL_HTTP 등) 사용 횟수가 50회 이상이면
    Replatform을 추천해야 합니다.
    """
    engine = MigrationDecisionEngine()

    # 고위험 패키지 사용량 분배 (UTL_FILE, UTL_HTTP에 분배)
    utl_file_count = high_risk_package_count // 2
    utl_http_count = high_risk_package_count - utl_file_count

    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=avg_sql_complexity,
        avg_plsql_complexity=avg_plsql_complexity,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=10,
        high_complexity_ratio=0.0,
        bulk_operation_count=0,
        rac_detected=False,
        detected_external_dependencies_summary={
            'UTL_FILE': utl_file_count,
            'UTL_HTTP': utl_http_count,
        },
    )

    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)

    assert (
        strategy == MigrationStrategy.REPLATFORM
    ), f"고위험 패키지 {high_risk_package_count}회 사용 시 Replatform을 추천해야 합니다"
    
    # 이유 확인
    reasons = engine.get_replatform_reasons()
    from src.migration_recommendation.decision_engine import ReplatformReason
    assert ReplatformReason.HIGH_RISK_ORACLE_PACKAGES in reasons


# 단위 테스트: 고위험 패키지 개수 계산
def test_count_high_risk_packages():
    """고위험 Oracle 패키지 개수 계산 테스트"""
    engine = MigrationDecisionEngine()
    
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=3.0,
        avg_plsql_complexity=3.0,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=10,
        high_complexity_ratio=0.0,
        bulk_operation_count=0,
        rac_detected=False,
        detected_external_dependencies_summary={
            'UTL_FILE': 10,
            'UTL_HTTP': 15,
            'UTL_SMTP': 5,
            'DBMS_AQ': 20,
            'DBMS_OUTPUT': 100,  # 저위험 - 카운트 안됨
            'DBMS_LOB': 50,  # 중위험 - 카운트 안됨
        },
    )
    
    count = engine._count_high_risk_packages(metrics)
    # UTL_FILE(10) + UTL_HTTP(15) + UTL_SMTP(5) + DBMS_AQ(20) = 50
    assert count == 50


# 단위 테스트: 고위험 패키지 임계값 미만
def test_high_risk_packages_below_threshold():
    """고위험 패키지가 임계값 미만이면 Replatform 트리거 안됨"""
    engine = MigrationDecisionEngine()
    
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=3.0,
        avg_plsql_complexity=3.0,
        high_complexity_sql_count=0,
        high_complexity_plsql_count=0,
        total_sql_count=10,
        total_plsql_count=10,
        high_complexity_ratio=0.0,
        bulk_operation_count=0,
        rac_detected=False,
        detected_external_dependencies_summary={
            'UTL_FILE': 20,
            'UTL_HTTP': 20,
            # 총 40회 - 임계값 50 미만
        },
    )
    
    integrated_result = create_integrated_result(metrics)
    strategy = engine.decide_strategy(integrated_result)
    
    # 다른 Replatform 조건도 없으므로 PostgreSQL 또는 MySQL
    assert strategy != MigrationStrategy.REPLATFORM
