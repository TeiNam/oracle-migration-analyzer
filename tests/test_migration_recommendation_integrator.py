"""
마이그레이션 추천 통합기 Property-Based 테스트

통합기의 메트릭 추출 정확성을 검증합니다.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List

from src.dbcsi.data_models import (
    StatspackData, AWRData, OSInformation, MainMetric, MemoryMetric
)
from src.oracle_complexity_analyzer import (
    SQLAnalysisResult, PLSQLAnalysisResult, 
    TargetDatabase, ComplexityLevel, PLSQLObjectType
)
from src.migration_recommendation.integrator import AnalysisResultIntegrator
from src.migration_recommendation.data_models import AnalysisMetrics


# 테스트 데이터 생성 전략

@st.composite
def sql_analysis_result(draw):
    """SQL 분석 결과 생성 전략"""
    normalized_score = draw(st.floats(min_value=0.0, max_value=10.0))
    
    return SQLAnalysisResult(
        query="SELECT * FROM test",
        target_database=TargetDatabase.POSTGRESQL,
        total_score=normalized_score,
        normalized_score=normalized_score,
        complexity_level=ComplexityLevel.MODERATE,
        recommendation="테스트",
        structural_complexity=0.0,
        oracle_specific_features=0.0,
        functions_expressions=0.0,
        data_volume=0.0,
        execution_complexity=0.0,
        conversion_difficulty=0.0
    )


@st.composite
def plsql_analysis_result(draw):
    """PL/SQL 분석 결과 생성 전략"""
    normalized_score = draw(st.floats(min_value=0.0, max_value=10.0))
    bulk_ops = draw(st.integers(min_value=0, max_value=20))
    
    return PLSQLAnalysisResult(
        code="BEGIN NULL; END;",
        object_type=PLSQLObjectType.PROCEDURE,
        target_database=TargetDatabase.POSTGRESQL,
        total_score=normalized_score,
        normalized_score=normalized_score,
        complexity_level=ComplexityLevel.MODERATE,
        recommendation="테스트",
        base_score=0.0,
        code_complexity=0.0,
        oracle_features=0.0,
        business_logic=0.0,
        ai_difficulty=0.0,
        bulk_operations_count=bulk_ops
    )


@st.composite
def dbcsi_result(draw):
    """DBCSI 분석 결과 생성 전략"""
    num_metrics = draw(st.integers(min_value=1, max_value=10))
    
    # MainMetric 생성
    main_metrics = []
    for i in range(num_metrics):
        cpu = draw(st.floats(min_value=0.0, max_value=100.0))
        read_iops = draw(st.floats(min_value=0.0, max_value=10000.0))
        write_iops = draw(st.floats(min_value=0.0, max_value=10000.0))
        
        main_metrics.append(MainMetric(
            snap=i,
            dur_m=60.0,
            end="2026-01-15",
            inst=1,
            cpu_per_s=cpu,
            read_iops=read_iops,
            read_mb_s=0.0,
            write_iops=write_iops,
            write_mb_s=0.0,
            commits_s=0.0
        ))
    
    # MemoryMetric 생성
    memory_metrics = []
    for i in range(num_metrics):
        total_gb = draw(st.floats(min_value=1.0, max_value=100.0))
        memory_metrics.append(MemoryMetric(
            snap_id=i,
            instance_number=1,
            sga_gb=total_gb * 0.7,
            pga_gb=total_gb * 0.3,
            total_gb=total_gb
        ))
    
    return StatspackData(
        os_info=OSInformation(instances=1),
        main_metrics=main_metrics,
        memory_metrics=memory_metrics
    )


# Property 2: 메트릭 추출 정확성
# Feature: migration-recommendation, Property 2: For any integrated analysis result, 
# extracted metrics should accurately reflect the input data
# Validates: Requirements 1.4, 1.5, 1.6

@given(
    sql_results=st.lists(sql_analysis_result(), min_size=1, max_size=20),
    plsql_results=st.lists(plsql_analysis_result(), min_size=1, max_size=20)
)
def test_property_2_metrics_extraction_accuracy(sql_results, plsql_results):
    """
    Property 2: 메트릭 추출 정확성
    
    For any integrated analysis result, extracted metrics should accurately 
    reflect the input data (평균 복잡도, 집계 개수 등)
    
    Validates: Requirements 1.4, 1.5, 1.6
    """
    integrator = AnalysisResultIntegrator()
    
    # 메트릭 추출
    metrics = integrator.extract_metrics(None, sql_results, plsql_results)
    
    # 평균 SQL 복잡도 검증
    expected_avg_sql = sum(r.normalized_score for r in sql_results) / len(sql_results)
    assert abs(metrics.avg_sql_complexity - expected_avg_sql) < 0.01, \
        f"평균 SQL 복잡도 불일치: {metrics.avg_sql_complexity} != {expected_avg_sql}"
    
    # 평균 PL/SQL 복잡도 검증
    expected_avg_plsql = sum(r.normalized_score for r in plsql_results) / len(plsql_results)
    assert abs(metrics.avg_plsql_complexity - expected_avg_plsql) < 0.01, \
        f"평균 PL/SQL 복잡도 불일치: {metrics.avg_plsql_complexity} != {expected_avg_plsql}"
    
    # 총 개수 검증
    assert metrics.total_sql_count == len(sql_results), \
        f"SQL 개수 불일치: {metrics.total_sql_count} != {len(sql_results)}"
    assert metrics.total_plsql_count == len(plsql_results), \
        f"PL/SQL 개수 불일치: {metrics.total_plsql_count} != {len(plsql_results)}"
    
    # BULK 연산 개수 검증
    expected_bulk = sum(r.bulk_operations_count for r in plsql_results)
    assert metrics.bulk_operation_count == expected_bulk, \
        f"BULK 연산 개수 불일치: {metrics.bulk_operation_count} != {expected_bulk}"


# Property 17: 성능 메트릭 추출 정확성
# Feature: migration-recommendation, Property 17: For any DBCSI result, 
# extracted CPU, I/O, and Memory metrics should match the average values from the input
# Validates: Requirements 11.1, 11.2

@given(dbcsi_data=dbcsi_result())
def test_property_17_performance_metrics_accuracy(dbcsi_data):
    """
    Property 17: 성능 메트릭 추출 정확성
    
    For any DBCSI result, extracted CPU, I/O, and Memory metrics should match 
    the average values from the input
    
    Validates: Requirements 11.1, 11.2
    """
    integrator = AnalysisResultIntegrator()
    
    # 빈 SQL/PL-SQL 분석 결과로 메트릭 추출
    sql_dummy = [SQLAnalysisResult(
        query="SELECT 1",
        target_database=TargetDatabase.POSTGRESQL,
        total_score=5.0,
        normalized_score=5.0,
        complexity_level=ComplexityLevel.MODERATE,
        recommendation="테스트",
        structural_complexity=0.0,
        oracle_specific_features=0.0,
        functions_expressions=0.0,
        data_volume=0.0,
        execution_complexity=0.0,
        conversion_difficulty=0.0
    )]
    
    metrics = integrator.extract_metrics(dbcsi_data, sql_dummy, [])
    
    # 예상 평균 CPU 계산
    expected_avg_cpu = sum(m.cpu_per_s for m in dbcsi_data.main_metrics) / len(dbcsi_data.main_metrics)
    assert abs(metrics.avg_cpu_usage - expected_avg_cpu) < 0.01, \
        f"평균 CPU 불일치: {metrics.avg_cpu_usage} != {expected_avg_cpu}"
    
    # 예상 평균 I/O 계산
    expected_avg_io = sum(
        (m.read_iops or 0.0) + (m.write_iops or 0.0) 
        for m in dbcsi_data.main_metrics
    ) / len(dbcsi_data.main_metrics)
    assert abs(metrics.avg_io_load - expected_avg_io) < 0.01, \
        f"평균 I/O 불일치: {metrics.avg_io_load} != {expected_avg_io}"
    
    # 예상 평균 메모리 계산
    expected_avg_memory = sum(m.total_gb for m in dbcsi_data.memory_metrics) / len(dbcsi_data.memory_metrics)
    assert abs(metrics.avg_memory_usage - expected_avg_memory) < 0.01, \
        f"평균 메모리 불일치: {metrics.avg_memory_usage} != {expected_avg_memory}"


# Property 16: 복잡도 7.0 이상 집계 정확성
# Feature: migration-recommendation, Property 16: For any SQL/PL-SQL analysis results, 
# counting objects with complexity >= 7.0 should match the actual count
# Validates: Requirements 12.1, 12.2

@given(
    sql_results=st.lists(sql_analysis_result(), min_size=1, max_size=50),
    plsql_results=st.lists(plsql_analysis_result(), min_size=1, max_size=50)
)
def test_property_16_high_complexity_count_accuracy(sql_results, plsql_results):
    """
    Property 16: 복잡도 7.0 이상 집계 정확성
    
    For any SQL/PL-SQL analysis results, counting objects with complexity >= 7.0 
    should match the actual count
    
    Validates: Requirements 12.1, 12.2
    """
    integrator = AnalysisResultIntegrator()
    
    # 메트릭 추출
    metrics = integrator.extract_metrics(None, sql_results, plsql_results)
    
    # 예상 복잡도 7.0 이상 SQL 개수
    expected_high_sql = sum(1 for r in sql_results if r.normalized_score >= 7.0)
    assert metrics.high_complexity_sql_count == expected_high_sql, \
        f"복잡도 7.0 이상 SQL 개수 불일치: {metrics.high_complexity_sql_count} != {expected_high_sql}"
    
    # 예상 복잡도 7.0 이상 PL/SQL 개수
    expected_high_plsql = sum(1 for r in plsql_results if r.normalized_score >= 7.0)
    assert metrics.high_complexity_plsql_count == expected_high_plsql, \
        f"복잡도 7.0 이상 PL/SQL 개수 불일치: {metrics.high_complexity_plsql_count} != {expected_high_plsql}"
    
    # 복잡 오브젝트 비율 검증
    total_count = len(sql_results) + len(plsql_results)
    high_count = expected_high_sql + expected_high_plsql
    expected_ratio = high_count / total_count
    assert abs(metrics.high_complexity_ratio - expected_ratio) < 0.01, \
        f"복잡 오브젝트 비율 불일치: {metrics.high_complexity_ratio} != {expected_ratio}"


# 단위 테스트

def test_integrate_with_missing_inputs():
    """필수 입력 누락 시 오류 발생 테스트"""
    integrator = AnalysisResultIntegrator()
    
    with pytest.raises(ValueError, match="SQL 또는 PL/SQL 분석 결과가 필요합니다"):
        integrator.integrate(None, [], [])


def test_integrate_with_sql_only():
    """SQL 분석 결과만 있는 경우 테스트"""
    integrator = AnalysisResultIntegrator()
    
    sql_results = [
        SQLAnalysisResult(
            query="SELECT * FROM test",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=5.0,
            normalized_score=5.0,
            complexity_level=ComplexityLevel.MODERATE,
            recommendation="테스트",
            structural_complexity=0.0,
            oracle_specific_features=0.0,
            functions_expressions=0.0,
            data_volume=0.0,
            execution_complexity=0.0,
            conversion_difficulty=0.0
        )
    ]
    
    result = integrator.integrate(None, sql_results, [])
    
    assert result.metrics.avg_sql_complexity == 5.0
    assert result.metrics.avg_plsql_complexity == 0.0
    assert result.metrics.total_sql_count == 1
    assert result.metrics.total_plsql_count == 0


def test_integrate_with_plsql_only():
    """PL/SQL 분석 결과만 있는 경우 테스트"""
    integrator = AnalysisResultIntegrator()
    
    plsql_results = [
        PLSQLAnalysisResult(
            code="BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.POSTGRESQL,
            total_score=6.0,
            normalized_score=6.0,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="테스트",
            base_score=0.0,
            code_complexity=0.0,
            oracle_features=0.0,
            business_logic=0.0,
            ai_difficulty=0.0,
            bulk_operations_count=5
        )
    ]
    
    result = integrator.integrate(None, [], plsql_results)
    
    assert result.metrics.avg_sql_complexity == 0.0
    assert result.metrics.avg_plsql_complexity == 6.0
    assert result.metrics.total_sql_count == 0
    assert result.metrics.total_plsql_count == 1
    assert result.metrics.bulk_operation_count == 5


def test_extract_metrics_with_no_dbcsi():
    """DBCSI 결과 없이 메트릭 추출 테스트"""
    integrator = AnalysisResultIntegrator()
    
    sql_results = [
        SQLAnalysisResult(
            query="SELECT 1",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=3.0,
            normalized_score=3.0,
            complexity_level=ComplexityLevel.SIMPLE,
            recommendation="테스트",
            structural_complexity=0.0,
            oracle_specific_features=0.0,
            functions_expressions=0.0,
            data_volume=0.0,
            execution_complexity=0.0,
            conversion_difficulty=0.0
        )
    ]
    
    metrics = integrator.extract_metrics(None, sql_results, [])
    
    # 성능 메트릭은 0이어야 함
    assert metrics.avg_cpu_usage == 0.0
    assert metrics.avg_io_load == 0.0
    assert metrics.avg_memory_usage == 0.0
    assert metrics.rac_detected is False
    
    # 코드 복잡도 메트릭은 정상 계산
    assert metrics.avg_sql_complexity == 3.0


def test_high_complexity_ratio_calculation():
    """복잡 오브젝트 비율 계산 테스트"""
    integrator = AnalysisResultIntegrator()
    
    # 10개 중 3개가 복잡도 7.0 이상
    sql_results = [
        SQLAnalysisResult(
            query=f"SELECT {i}",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=score,
            normalized_score=score,
            complexity_level=ComplexityLevel.MODERATE,
            recommendation="테스트",
            structural_complexity=0.0,
            oracle_specific_features=0.0,
            functions_expressions=0.0,
            data_volume=0.0,
            execution_complexity=0.0,
            conversion_difficulty=0.0
        )
        for i, score in enumerate([5.0, 6.0, 7.5, 4.0, 8.0, 3.0, 9.0, 2.0, 5.5, 6.5])
    ]
    
    metrics = integrator.extract_metrics(None, sql_results, [])
    
    assert metrics.high_complexity_sql_count == 3  # 7.5, 8.0, 9.0
    assert metrics.total_sql_count == 10
    assert abs(metrics.high_complexity_ratio - 0.3) < 0.01  # 30%
