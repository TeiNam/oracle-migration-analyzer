"""
마이그레이션 추천 리포트 포맷터 통합 테스트

전체 워크플로우를 테스트합니다:
1. 분석 결과 통합
2. 의사결정 엔진
3. 리포트 생성
4. 포맷팅 (Markdown, JSON)
"""

import json
import pytest

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics
)
from src.migration_recommendation.integrator import AnalysisResultIntegrator
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter, JSONReportFormatter


def test_end_to_end_workflow_replatform():
    """End-to-End 워크플로우 테스트: Replatform 시나리오"""
    # 1. 복잡한 시스템 메트릭 (Replatform 추천)
    metrics = AnalysisMetrics(
        avg_cpu_usage=75.0,
        avg_io_load=1200.0,
        avg_memory_usage=20.0,
        avg_sql_complexity=8.5,
        avg_plsql_complexity=7.8,
        high_complexity_sql_count=15,
        high_complexity_plsql_count=8,
        total_sql_count=30,
        total_plsql_count=20,
        high_complexity_ratio=0.46,
        bulk_operation_count=25,
        rac_detected=True
    )
    
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )
    
    # 2. 의사결정 및 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. Markdown 포맷팅
    markdown_formatter = MarkdownReportFormatter()
    markdown_ko = markdown_formatter.format(recommendation, language="ko")
    markdown_en = markdown_formatter.format(recommendation, language="en")
    
    # 4. JSON 포맷팅
    json_formatter = JSONReportFormatter()
    json_output = json_formatter.format(recommendation)
    
    # 검증: Markdown 한국어
    assert "# Executive Summary" in markdown_ko
    assert "# 목차" in markdown_ko
    assert "# 추천 전략" in markdown_ko
    assert "RDS for Oracle SE2" in markdown_ko or "replatform" in markdown_ko.lower()
    
    # 검증: Markdown 영어
    assert "# Executive Summary" in markdown_en
    assert "# Table of Contents" in markdown_en
    assert "# Recommended Strategy" in markdown_en
    
    # 검증: JSON
    parsed_json = json.loads(json_output)
    assert parsed_json["recommended_strategy"] == "replatform"
    assert "executive_summary" in parsed_json
    assert "rationales" in parsed_json
    assert len(parsed_json["rationales"]) >= 3
    
    print(f"\n✓ Replatform 시나리오 테스트 성공")
    print(f"  - 추천 전략: {recommendation.recommended_strategy.value}")
    print(f"  - 신뢰도: {recommendation.confidence_level}")
    print(f"  - 근거 개수: {len(recommendation.rationales)}")
    print(f"  - 대안 개수: {len(recommendation.alternative_strategies)}")
    print(f"  - 위험 개수: {len(recommendation.risks)}")
    print(f"  - 로드맵 단계: {len(recommendation.roadmap.phases)}")


def test_end_to_end_workflow_aurora_mysql():
    """End-to-End 워크플로우 테스트: Aurora MySQL 시나리오"""
    # 1. 단순한 시스템 메트릭 (Aurora MySQL 추천)
    metrics = AnalysisMetrics(
        avg_cpu_usage=40.0,
        avg_io_load=300.0,
        avg_memory_usage=8.0,
        avg_sql_complexity=3.5,
        avg_plsql_complexity=4.2,
        high_complexity_sql_count=1,
        high_complexity_plsql_count=0,
        total_sql_count=20,
        total_plsql_count=10,
        high_complexity_ratio=0.03,
        bulk_operation_count=3,
        rac_detected=False
    )
    
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )
    
    # 2. 의사결정 및 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. Markdown 포맷팅
    markdown_formatter = MarkdownReportFormatter()
    markdown_ko = markdown_formatter.format(recommendation, language="ko")
    
    # 4. JSON 포맷팅
    json_formatter = JSONReportFormatter()
    json_output = json_formatter.format(recommendation)
    
    # 검증: Markdown
    assert "# Executive Summary" in markdown_ko
    assert "Aurora MySQL" in markdown_ko or "refactor_mysql" in markdown_ko.lower()
    
    # 검증: JSON
    parsed_json = json.loads(json_output)
    assert parsed_json["recommended_strategy"] == "refactor_mysql"
    
    print(f"\n✓ Aurora MySQL 시나리오 테스트 성공")
    print(f"  - 추천 전략: {recommendation.recommended_strategy.value}")
    print(f"  - 신뢰도: {recommendation.confidence_level}")


def test_end_to_end_workflow_aurora_postgresql():
    """End-to-End 워크플로우 테스트: Aurora PostgreSQL 시나리오"""
    # 1. 중간 복잡도 시스템 메트릭 (Aurora PostgreSQL 추천)
    metrics = AnalysisMetrics(
        avg_cpu_usage=55.0,
        avg_io_load=700.0,
        avg_memory_usage=15.0,
        avg_sql_complexity=6.0,
        avg_plsql_complexity=5.8,
        high_complexity_sql_count=5,
        high_complexity_plsql_count=3,
        total_sql_count=25,
        total_plsql_count=15,
        high_complexity_ratio=0.2,
        bulk_operation_count=15,
        rac_detected=False
    )
    
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )
    
    # 2. 의사결정 및 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. Markdown 포맷팅
    markdown_formatter = MarkdownReportFormatter()
    markdown_ko = markdown_formatter.format(recommendation, language="ko")
    
    # 4. JSON 포맷팅
    json_formatter = JSONReportFormatter()
    json_output = json_formatter.format(recommendation)
    
    # 검증: Markdown
    assert "# Executive Summary" in markdown_ko
    assert "Aurora PostgreSQL" in markdown_ko or "refactor_postgresql" in markdown_ko.lower()
    
    # 검증: JSON
    parsed_json = json.loads(json_output)
    assert parsed_json["recommended_strategy"] == "refactor_postgresql"
    
    print(f"\n✓ Aurora PostgreSQL 시나리오 테스트 성공")
    print(f"  - 추천 전략: {recommendation.recommended_strategy.value}")
    print(f"  - 신뢰도: {recommendation.confidence_level}")


def test_markdown_and_json_consistency():
    """Markdown과 JSON 출력 일관성 테스트"""
    # 테스트 데이터 생성
    metrics = AnalysisMetrics(
        avg_cpu_usage=60.0,
        avg_io_load=800.0,
        avg_memory_usage=12.0,
        avg_sql_complexity=5.5,
        avg_plsql_complexity=6.0,
        high_complexity_sql_count=3,
        high_complexity_plsql_count=2,
        total_sql_count=20,
        total_plsql_count=10,
        high_complexity_ratio=0.17,
        bulk_operation_count=8,
        rac_detected=False
    )
    
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 포맷팅
    markdown_formatter = MarkdownReportFormatter()
    json_formatter = JSONReportFormatter()
    
    markdown_output = markdown_formatter.format(recommendation, language="ko")
    json_output = json_formatter.format(recommendation)
    
    # JSON 파싱
    parsed_json = json.loads(json_output)
    
    # 일관성 검증
    assert recommendation.recommended_strategy.value == parsed_json["recommended_strategy"]
    assert recommendation.confidence_level == parsed_json["confidence_level"]
    assert len(recommendation.rationales) == len(parsed_json["rationales"])
    assert len(recommendation.alternative_strategies) == len(parsed_json["alternative_strategies"])
    assert len(recommendation.risks) == len(parsed_json["risks"])
    assert len(recommendation.roadmap.phases) == len(parsed_json["roadmap"]["phases"])
    
    # Markdown에 주요 정보 포함 확인
    assert recommendation.recommended_strategy.value in markdown_output.lower()
    assert recommendation.confidence_level in markdown_output
    
    print(f"\n✓ Markdown과 JSON 일관성 테스트 성공")


def test_multilingual_support():
    """다국어 지원 테스트"""
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
    
    integrated_result = IntegratedAnalysisResult(
        dbcsi_result=None,
        sql_analysis=[],
        plsql_analysis=[],
        metrics=metrics,
        analysis_timestamp="2026-01-15 12:00:00"
    )
    
    # 리포트 생성
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 포맷팅
    markdown_formatter = MarkdownReportFormatter()
    
    markdown_ko = markdown_formatter.format(recommendation, language="ko")
    markdown_en = markdown_formatter.format(recommendation, language="en")
    
    # 한국어 검증
    assert "목차" in markdown_ko
    assert "추천 전략" in markdown_ko
    assert "추천 근거" in markdown_ko
    assert "대안 전략" in markdown_ko
    assert "위험 요소" in markdown_ko
    assert "마이그레이션 로드맵" in markdown_ko
    assert "분석 메트릭" in markdown_ko
    
    # 영어 검증
    assert "Table of Contents" in markdown_en
    assert "Recommended Strategy" in markdown_en
    assert "Rationales" in markdown_en
    assert "Alternative Strategies" in markdown_en
    assert "Risks and Mitigation" in markdown_en
    assert "Migration Roadmap" in markdown_en
    assert "Analysis Metrics" in markdown_en
    
    print(f"\n✓ 다국어 지원 테스트 성공")
    print(f"  - 한국어 출력 길이: {len(markdown_ko)} 자")
    print(f"  - 영어 출력 길이: {len(markdown_en)} 자")
