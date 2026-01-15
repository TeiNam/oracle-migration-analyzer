"""
마이그레이션 추천 리포트 생성 예제

이 스크립트는 DBCSI 분석 결과와 SQL/PL-SQL 복잡도 분석 결과를 통합하여
최적의 마이그레이션 전략을 추천하는 리포트를 생성합니다.
"""

from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics
)
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter, JSONReportFormatter


def example_replatform_scenario():
    """
    시나리오 1: 복잡한 시스템 - Replatform 추천
    
    - 평균 SQL 복잡도: 8.5 (매우 높음)
    - 평균 PL/SQL 복잡도: 7.8 (매우 높음)
    - 복잡 오브젝트 비율: 46% (높음)
    - BULK 연산: 25개
    """
    print("\n" + "="*80)
    print("시나리오 1: 복잡한 시스템 - Replatform 추천")
    print("="*80)
    
    # 1. 분석 메트릭 생성
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
    
    # 2. 마이그레이션 전략 추천
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. 결과 출력
    print(f"\n추천 전략: {recommendation.recommended_strategy.value}")
    print(f"신뢰도: {recommendation.confidence_level}")
    print(f"예상 기간: {recommendation.roadmap.total_estimated_duration}")
    
    print(f"\n주요 근거 ({len(recommendation.rationales)}개):")
    for i, rationale in enumerate(recommendation.rationales, 1):
        print(f"  {i}. [{rationale.category}] {rationale.reason}")
    
    print(f"\n대안 전략 ({len(recommendation.alternative_strategies)}개):")
    for i, alt in enumerate(recommendation.alternative_strategies, 1):
        print(f"  {i}. {alt.strategy.value}")
    
    print(f"\n위험 요소 ({len(recommendation.risks)}개):")
    for i, risk in enumerate(recommendation.risks, 1):
        print(f"  {i}. [{risk.severity}] {risk.description}")
    
    # 4. Markdown 리포트 생성
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="ko")
    
    with open("reports/migration_recommendation_replatform.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"\n✓ Markdown 리포트 생성: reports/migration_recommendation_replatform.md")
    
    # 5. JSON 리포트 생성
    json_formatter = JSONReportFormatter()
    json_report = json_formatter.format(recommendation)
    
    with open("reports/migration_recommendation_replatform.json", "w", encoding="utf-8") as f:
        f.write(json_report)
    print(f"✓ JSON 리포트 생성: reports/migration_recommendation_replatform.json")


def example_aurora_mysql_scenario():
    """
    시나리오 2: 단순한 시스템 - Aurora MySQL 추천
    
    - 평균 SQL 복잡도: 3.5 (낮음)
    - 평균 PL/SQL 복잡도: 4.2 (낮음)
    - 복잡 오브젝트 비율: 3% (매우 낮음)
    - BULK 연산: 3개
    """
    print("\n" + "="*80)
    print("시나리오 2: 단순한 시스템 - Aurora MySQL 추천")
    print("="*80)
    
    # 1. 분석 메트릭 생성
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
    
    # 2. 마이그레이션 전략 추천
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. 결과 출력
    print(f"\n추천 전략: {recommendation.recommended_strategy.value}")
    print(f"신뢰도: {recommendation.confidence_level}")
    print(f"예상 기간: {recommendation.roadmap.total_estimated_duration}")
    
    print(f"\n주요 근거 ({len(recommendation.rationales)}개):")
    for i, rationale in enumerate(recommendation.rationales, 1):
        print(f"  {i}. [{rationale.category}] {rationale.reason}")
    
    # 4. Markdown 리포트 생성 (영어)
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="en")
    
    with open("reports/migration_recommendation_mysql.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"\n✓ Markdown 리포트 생성 (영어): reports/migration_recommendation_mysql.md")
    
    # 5. JSON 리포트 생성
    json_formatter = JSONReportFormatter()
    json_report = json_formatter.format(recommendation)
    
    with open("reports/migration_recommendation_mysql.json", "w", encoding="utf-8") as f:
        f.write(json_report)
    print(f"✓ JSON 리포트 생성: reports/migration_recommendation_mysql.json")


def example_aurora_postgresql_scenario():
    """
    시나리오 3: 중간 복잡도 시스템 - Aurora PostgreSQL 추천
    
    - 평균 SQL 복잡도: 6.0 (중간)
    - 평균 PL/SQL 복잡도: 5.8 (중간)
    - 복잡 오브젝트 비율: 20% (중간)
    - BULK 연산: 15개 (많음)
    """
    print("\n" + "="*80)
    print("시나리오 3: 중간 복잡도 시스템 - Aurora PostgreSQL 추천")
    print("="*80)
    
    # 1. 분석 메트릭 생성
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
    
    # 2. 마이그레이션 전략 추천
    engine = MigrationDecisionEngine()
    generator = RecommendationReportGenerator(engine)
    recommendation = generator.generate_recommendation(integrated_result)
    
    # 3. 결과 출력
    print(f"\n추천 전략: {recommendation.recommended_strategy.value}")
    print(f"신뢰도: {recommendation.confidence_level}")
    print(f"예상 기간: {recommendation.roadmap.total_estimated_duration}")
    
    print(f"\n주요 근거 ({len(recommendation.rationales)}개):")
    for i, rationale in enumerate(recommendation.rationales, 1):
        print(f"  {i}. [{rationale.category}] {rationale.reason}")
    
    # 4. Markdown 리포트 생성
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="ko")
    
    with open("reports/migration_recommendation_postgresql.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"\n✓ Markdown 리포트 생성: reports/migration_recommendation_postgresql.md")
    
    # 5. JSON 리포트 생성
    json_formatter = JSONReportFormatter()
    json_report = json_formatter.format(recommendation)
    
    with open("reports/migration_recommendation_postgresql.json", "w", encoding="utf-8") as f:
        f.write(json_report)
    print(f"✓ JSON 리포트 생성: reports/migration_recommendation_postgresql.json")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("마이그레이션 추천 리포트 생성 예제")
    print("="*80)
    
    # 시나리오 1: Replatform
    example_replatform_scenario()
    
    # 시나리오 2: Aurora MySQL
    example_aurora_mysql_scenario()
    
    # 시나리오 3: Aurora PostgreSQL
    example_aurora_postgresql_scenario()
    
    print("\n" + "="*80)
    print("모든 시나리오 완료!")
    print("="*80)
    print("\n생성된 리포트:")
    print("  - reports/migration_recommendation_replatform.md")
    print("  - reports/migration_recommendation_replatform.json")
    print("  - reports/migration_recommendation_mysql.md")
    print("  - reports/migration_recommendation_mysql.json")
    print("  - reports/migration_recommendation_postgresql.md")
    print("  - reports/migration_recommendation_postgresql.json")
    print()
