"""
마이그레이션 추천 리포트 포맷터 Property 테스트

Requirements:
- Property 12: Markdown 출력 유효성 (Requirements 9.1)
- Property 13: JSON Round-trip (Requirements 9.2)
"""

import json
import pytest
from hypothesis import given, strategies as st

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy
)
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter, JSONReportFormatter


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


# Property 12: Markdown 출력 유효성
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200),
    language=st.sampled_from(["ko", "en"])
)
def test_markdown_output_validity_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count,
    language
):
    """
    Property 12: Markdown 출력 유효성
    Feature: migration-recommendation, Property 12: For any recommendation, 
    converting to Markdown should produce valid Markdown text
    Validates: Requirements 9.1
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
    
    # Markdown 포맷팅
    formatter = MarkdownReportFormatter()
    markdown_output = formatter.format(recommendation, language=language)
    
    # 검증: Markdown 출력이 비어있지 않음
    assert markdown_output, "Markdown 출력이 비어있습니다"
    assert isinstance(markdown_output, str), "Markdown 출력은 문자열이어야 합니다"
    
    # 검증: 필수 섹션 포함 (언어별)
    if language == "ko":
        assert "## 요약" in markdown_output, "요약 섹션이 없습니다"
        assert "## 목차" in markdown_output, "목차 섹션이 없습니다"
        assert "# 추천 전략" in markdown_output, "추천 전략 섹션이 없습니다"
        assert "# 추천 근거" in markdown_output, "추천 근거 섹션이 없습니다"
        assert "# 대안 전략" in markdown_output, "대안 전략 섹션이 없습니다"
        assert "# 위험 요소 및 완화 방안" in markdown_output, "위험 요소 섹션이 없습니다"
        assert "# 최종 난이도 판정" in markdown_output, "최종 난이도 판정 섹션이 없습니다"
        assert "## 분석 원본 데이터" in markdown_output, "분석 원본 데이터 섹션이 없습니다"
    else:  # English
        assert "## Summary" in markdown_output, "Summary section is missing"
        assert "## Table of Contents" in markdown_output, "Table of Contents section is missing"
        assert "# Recommended Strategy" in markdown_output, "Recommended Strategy section is missing"
        assert "# Rationale" in markdown_output, "Rationale section is missing"
        assert "# Alternative Strategies" in markdown_output, "Alternative Strategies section is missing"
        assert "# Risks and Mitigation" in markdown_output, "Risks and Mitigation section is missing"
        assert "# Final Difficulty Assessment" in markdown_output, "Final Difficulty Assessment section is missing"
        assert "## Analysis Source Data" in markdown_output, "Analysis Source Data section is missing"
    
    # 검증: Markdown 헤더 형식 확인
    assert markdown_output.count("# ") >= 8, "Markdown 헤더가 충분하지 않습니다"
    
    # 검증: 리스트 항목 형식 확인
    assert "- " in markdown_output, "Markdown 리스트 항목이 없습니다"
    
    # 검증: 볼드 텍스트 형식 확인
    assert "**" in markdown_output, "Markdown 볼드 텍스트가 없습니다"


# Property 13: JSON Round-trip
@given(
    avg_sql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    avg_plsql_complexity=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    high_complexity_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    bulk_operation_count=st.integers(min_value=0, max_value=100),
    total_plsql_count=st.integers(min_value=0, max_value=200)
)
def test_json_roundtrip_property(
    avg_sql_complexity,
    avg_plsql_complexity,
    high_complexity_ratio,
    bulk_operation_count,
    total_plsql_count
):
    """
    Property 13: JSON Round-trip
    Feature: migration-recommendation, Property 13: For any recommendation, 
    converting to JSON and back should produce an equivalent recommendation
    Validates: Requirements 9.2
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
    
    # JSON 포맷팅
    formatter = JSONReportFormatter()
    json_output = formatter.format(recommendation)
    
    # 검증: JSON 출력이 비어있지 않음
    assert json_output, "JSON 출력이 비어있습니다"
    assert isinstance(json_output, str), "JSON 출력은 문자열이어야 합니다"
    
    # 검증: 유효한 JSON 형식
    try:
        parsed_data = json.loads(json_output)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON 파싱 실패: {e}")
    
    # 검증: 필수 키 포함
    required_keys = [
        "recommended_strategy",
        "confidence_level",
        "executive_summary",
        "rationales",
        "alternative_strategies",
        "risks",
        "roadmap",
        "metrics"
    ]
    for key in required_keys:
        assert key in parsed_data, f"필수 키 '{key}'가 JSON에 없습니다"
    
    # 검증: 데이터 일관성
    assert parsed_data["recommended_strategy"] == recommendation.recommended_strategy.value, \
        "추천 전략이 일치하지 않습니다"
    assert parsed_data["confidence_level"] == recommendation.confidence_level, \
        "신뢰도가 일치하지 않습니다"
    
    # 검증: Executive Summary 구조
    exec_summary = parsed_data["executive_summary"]
    assert "recommended_strategy" in exec_summary, "Executive Summary에 추천 전략이 없습니다"
    assert "estimated_duration" in exec_summary, "Executive Summary에 예상 기간이 없습니다"
    assert "key_benefits" in exec_summary, "Executive Summary에 주요 이점이 없습니다"
    assert "key_risks" in exec_summary, "Executive Summary에 주요 위험이 없습니다"
    assert "summary_text" in exec_summary, "Executive Summary에 요약 텍스트가 없습니다"
    
    # 검증: Rationales 구조
    assert isinstance(parsed_data["rationales"], list), "Rationales는 리스트여야 합니다"
    assert len(parsed_data["rationales"]) == len(recommendation.rationales), \
        "Rationales 개수가 일치하지 않습니다"
    for rationale in parsed_data["rationales"]:
        assert "category" in rationale, "Rationale에 카테고리가 없습니다"
        assert "reason" in rationale, "Rationale에 이유가 없습니다"
        assert "supporting_data" in rationale, "Rationale에 근거 데이터가 없습니다"
    
    # 검증: Alternative Strategies 구조
    assert isinstance(parsed_data["alternative_strategies"], list), \
        "Alternative Strategies는 리스트여야 합니다"
    assert len(parsed_data["alternative_strategies"]) == len(recommendation.alternative_strategies), \
        "Alternative Strategies 개수가 일치하지 않습니다"
    for alt in parsed_data["alternative_strategies"]:
        assert "strategy" in alt, "Alternative Strategy에 전략이 없습니다"
        assert "pros" in alt, "Alternative Strategy에 장점이 없습니다"
        assert "cons" in alt, "Alternative Strategy에 단점이 없습니다"
        assert "considerations" in alt, "Alternative Strategy에 고려사항이 없습니다"
    
    # 검증: Risks 구조
    assert isinstance(parsed_data["risks"], list), "Risks는 리스트여야 합니다"
    assert len(parsed_data["risks"]) == len(recommendation.risks), \
        "Risks 개수가 일치하지 않습니다"
    for risk in parsed_data["risks"]:
        assert "category" in risk, "Risk에 카테고리가 없습니다"
        assert "description" in risk, "Risk에 설명이 없습니다"
        assert "severity" in risk, "Risk에 심각도가 없습니다"
        assert "mitigation" in risk, "Risk에 완화 방안이 없습니다"
    
    # 검증: Roadmap 구조
    roadmap = parsed_data["roadmap"]
    assert "total_estimated_duration" in roadmap, "Roadmap에 총 예상 기간이 없습니다"
    assert "phases" in roadmap, "Roadmap에 단계가 없습니다"
    assert isinstance(roadmap["phases"], list), "Roadmap phases는 리스트여야 합니다"
    assert len(roadmap["phases"]) == len(recommendation.roadmap.phases), \
        "Roadmap phases 개수가 일치하지 않습니다"
    for phase in roadmap["phases"]:
        assert "phase_number" in phase, "Phase에 번호가 없습니다"
        assert "phase_name" in phase, "Phase에 이름이 없습니다"
        assert "tasks" in phase, "Phase에 작업이 없습니다"
        assert "estimated_duration" in phase, "Phase에 예상 기간이 없습니다"
        assert "required_resources" in phase, "Phase에 필요 리소스가 없습니다"
    
    # 검증: Metrics 구조
    metrics_data = parsed_data["metrics"]
    assert "performance" in metrics_data, "Metrics에 성능 메트릭이 없습니다"
    assert "complexity" in metrics_data, "Metrics에 복잡도 메트릭이 없습니다"
    assert "rac_detected" in metrics_data, "Metrics에 RAC 정보가 없습니다"
    
    # 검증: Performance Metrics
    perf = metrics_data["performance"]
    assert "avg_cpu_usage" in perf, "Performance에 CPU 사용률이 없습니다"
    assert "avg_io_load" in perf, "Performance에 I/O 부하가 없습니다"
    assert "avg_memory_usage" in perf, "Performance에 메모리 사용량이 없습니다"
    
    # 검증: Complexity Metrics
    complexity = metrics_data["complexity"]
    assert "avg_sql_complexity" in complexity, "Complexity에 평균 SQL 복잡도가 없습니다"
    assert "avg_plsql_complexity" in complexity, "Complexity에 평균 PL/SQL 복잡도가 없습니다"
    assert "high_complexity_sql_count" in complexity, "Complexity에 복잡 SQL 개수가 없습니다"
    assert "high_complexity_plsql_count" in complexity, "Complexity에 복잡 PL/SQL 개수가 없습니다"
    assert "total_sql_count" in complexity, "Complexity에 총 SQL 개수가 없습니다"
    assert "total_plsql_count" in complexity, "Complexity에 총 PL/SQL 개수가 없습니다"
    assert "high_complexity_ratio" in complexity, "Complexity에 복잡 오브젝트 비율이 없습니다"
    assert "bulk_operation_count" in complexity, "Complexity에 BULK 연산 개수가 없습니다"


# 단위 테스트: Markdown 포맷터 기본 기능
def test_markdown_formatter_basic():
    """Markdown 포맷터 기본 기능 테스트"""
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=6.0,
        avg_plsql_complexity=5.5,
        high_complexity_sql_count=2,
        high_complexity_plsql_count=1,
        total_sql_count=10,
        total_plsql_count=5,
        high_complexity_ratio=0.2,
        bulk_operation_count=5,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # Markdown 포맷팅 (한국어)
    formatter = MarkdownReportFormatter()
    markdown_ko = formatter.format(recommendation, language="ko")
    
    assert "# 요약" in markdown_ko
    assert "## 목차" in markdown_ko
    assert "# 추천 전략" in markdown_ko
    
    # Markdown 포맷팅 (영어)
    markdown_en = formatter.format(recommendation, language="en")
    
    assert "## Summary" in markdown_en
    assert "## Table of Contents" in markdown_en
    assert "# Recommended Strategy" in markdown_en


# 단위 테스트: JSON 포맷터 기본 기능
def test_json_formatter_basic():
    """JSON 포맷터 기본 기능 테스트"""
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=50.0,
        avg_io_load=500.0,
        avg_memory_usage=10.0,
        avg_sql_complexity=6.0,
        avg_plsql_complexity=5.5,
        high_complexity_sql_count=2,
        high_complexity_plsql_count=1,
        total_sql_count=10,
        total_plsql_count=5,
        high_complexity_ratio=0.2,
        bulk_operation_count=5,
        rac_detected=False
    )
    
    integrated_result = create_integrated_result(metrics)
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # JSON 포맷팅
    formatter = JSONReportFormatter()
    json_output = formatter.format(recommendation)
    
    # JSON 파싱
    parsed_data = json.loads(json_output)
    
    # 기본 검증
    assert "recommended_strategy" in parsed_data
    assert "confidence_level" in parsed_data
    assert "executive_summary" in parsed_data
    assert "rationales" in parsed_data
    assert "alternative_strategies" in parsed_data
    assert "risks" in parsed_data
    assert "roadmap" in parsed_data
    assert "metrics" in parsed_data
