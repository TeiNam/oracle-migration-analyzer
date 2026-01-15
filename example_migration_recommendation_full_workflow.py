"""
마이그레이션 추천 시스템 전체 워크플로우 예제

이 스크립트는 실제 DBCSI 리포트와 SQL/PL-SQL 파일을 사용하여
전체 마이그레이션 추천 워크플로우를 시연합니다.

워크플로우:
1. DBCSI 분석 (Statspack/AWR 파싱)
2. SQL/PL-SQL 복잡도 분석
3. 분석 결과 통합
4. 의사결정 엔진 실행
5. 추천 리포트 생성
6. Markdown/JSON 출력
"""

import os
from datetime import datetime

from src.dbcsi.parser import StatspackParser
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    PLSQLAnalysisResult
)
from src.migration_recommendation.integrator import AnalysisResultIntegrator
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter, JSONReportFormatter


def analyze_with_statspack():
    """
    Statspack 리포트를 사용한 전체 워크플로우
    """
    print("\n" + "="*80)
    print("워크플로우 1: Statspack 리포트 분석")
    print("="*80)
    
    # 1. DBCSI 분석 (Statspack 파싱)
    print("\n[1/6] DBCSI 분석 중...")
    statspack_file = "sample_code/dbcsi_statspack_sample01.out"
    
    if not os.path.exists(statspack_file):
        print(f"  ✗ 파일을 찾을 수 없습니다: {statspack_file}")
        return
    
    parser = StatspackParser(statspack_file)
    dbcsi_result = parser.parse()
    
    print(f"  ✓ DBCSI 분석 완료")
    print(f"    - DB 이름: {dbcsi_result.os_info.db_name}")
    print(f"    - 버전: {dbcsi_result.os_info.version}")
    print(f"    - 에디션: {dbcsi_result.os_info.banner}")
    print(f"    - PL/SQL 라인 수: {dbcsi_result.os_info.count_lines_plsql}")
    
    # 2. SQL/PL-SQL 복잡도 분석
    print("\n[2/6] SQL/PL-SQL 복잡도 분석 중...")
    sql_files = [
        "sample_code/sample_plsql01.sql",
        "sample_code/sample_plsql02.sql",
        "sample_code/sample_plsql03.sql",
        "sample_code/sample_plsql04.sql"
    ]
    
    analyzer = OracleComplexityAnalyzer()
    sql_analysis = []
    plsql_analysis = []
    
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            result = analyzer.analyze_file(sql_file)
            # PLSQLAnalysisResult는 object_type이 PLSQLObjectType enum
            if isinstance(result, PLSQLAnalysisResult):
                plsql_analysis.append(result)
            else:
                sql_analysis.append(result)
    
    print(f"  ✓ 복잡도 분석 완료")
    print(f"    - SQL 쿼리: {len(sql_analysis)}개")
    print(f"    - PL/SQL 오브젝트: {len(plsql_analysis)}개")
    
    if len(sql_analysis) > 0:
        avg_sql = sum(r.total_score for r in sql_analysis) / len(sql_analysis)
        print(f"    - 평균 SQL 복잡도: {avg_sql:.2f}")
    
    if len(plsql_analysis) > 0:
        avg_plsql = sum(r.total_score for r in plsql_analysis) / len(plsql_analysis)
        print(f"    - 평균 PL/SQL 복잡도: {avg_plsql:.2f}")
    
    # 3. 분석 결과 통합
    print("\n[3/6] 분석 결과 통합 중...")
    integrator = AnalysisResultIntegrator()
    integrated_result = integrator.integrate(
        dbcsi_result=dbcsi_result,
        sql_analysis=sql_analysis,
        plsql_analysis=plsql_analysis
    )
    
    metrics = integrated_result.metrics
    print(f"  ✓ 통합 완료")
    print(f"    - 평균 CPU 사용률: {metrics.avg_cpu_usage:.1f}%")
    print(f"    - 평균 I/O 부하: {metrics.avg_io_load:.1f} IOPS")
    print(f"    - 평균 SQL 복잡도: {metrics.avg_sql_complexity:.2f}")
    print(f"    - 평균 PL/SQL 복잡도: {metrics.avg_plsql_complexity:.2f}")
    print(f"    - 복잡 오브젝트 비율: {metrics.high_complexity_ratio*100:.1f}%")
    print(f"    - BULK 연산 개수: {metrics.bulk_operation_count}개")
    
    # 4. 의사결정 엔진 실행
    print("\n[4/6] 마이그레이션 전략 결정 중...")
    decision_engine = MigrationDecisionEngine()
    recommended_strategy = decision_engine.decide_strategy(integrated_result)
    
    print(f"  ✓ 전략 결정 완료")
    print(f"    - 추천 전략: {recommended_strategy.value}")
    
    # 5. 추천 리포트 생성
    print("\n[5/6] 추천 리포트 생성 중...")
    report_generator = RecommendationReportGenerator(decision_engine)
    recommendation = report_generator.generate_recommendation(integrated_result)
    
    print(f"  ✓ 리포트 생성 완료")
    print(f"    - 추천 전략: {recommendation.recommended_strategy.value}")
    print(f"    - 신뢰도: {recommendation.confidence_level}")
    print(f"    - 예상 기간: {recommendation.roadmap.total_estimated_duration}")
    print(f"    - 근거 개수: {len(recommendation.rationales)}개")
    print(f"    - 대안 전략: {len(recommendation.alternative_strategies)}개")
    print(f"    - 위험 요소: {len(recommendation.risks)}개")
    print(f"    - 로드맵 단계: {len(recommendation.roadmap.phases)}개")
    
    # 6. Markdown/JSON 출력
    print("\n[6/6] 리포트 파일 생성 중...")
    
    # Markdown 리포트 (한국어)
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="ko")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = f"reports/migration_recommendation_statspack_{timestamp}.md"
    
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    
    print(f"  ✓ Markdown 리포트 생성: {markdown_path}")
    
    # JSON 리포트
    json_formatter = JSONReportFormatter()
    json_report = json_formatter.format(recommendation)
    
    json_path = f"reports/migration_recommendation_statspack_{timestamp}.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_report)
    
    print(f"  ✓ JSON 리포트 생성: {json_path}")
    
    # Executive Summary 출력
    print("\n" + "="*80)
    print("Executive Summary")
    print("="*80)
    print(recommendation.executive_summary.summary_text)
    print("="*80)


def analyze_with_awr():
    """
    AWR 리포트를 사용한 전체 워크플로우
    """
    print("\n" + "="*80)
    print("워크플로우 2: AWR 리포트 분석")
    print("="*80)
    
    # 1. DBCSI 분석 (AWR 파싱)
    print("\n[1/6] DBCSI 분석 중...")
    awr_file = "sample_code/dbcsi_awr_sample01.out"
    
    if not os.path.exists(awr_file):
        print(f"  ✗ 파일을 찾을 수 없습니다: {awr_file}")
        return
    
    parser = StatspackParser(awr_file)
    dbcsi_result = parser.parse()
    
    print(f"  ✓ DBCSI 분석 완료")
    print(f"    - DB 이름: {dbcsi_result.os_info.db_name}")
    print(f"    - 버전: {dbcsi_result.os_info.version}")
    print(f"    - 에디션: {dbcsi_result.os_info.banner}")
    print(f"    - PL/SQL 라인 수: {dbcsi_result.os_info.count_lines_plsql}")
    
    # 2. SQL/PL-SQL 복잡도 분석
    print("\n[2/6] SQL/PL-SQL 복잡도 분석 중...")
    sql_files = [
        "sample_code/sample_plsql01.sql",
        "sample_code/sample_plsql02.sql",
        "sample_code/sample_plsql03.sql",
        "sample_code/sample_plsql04.sql"
    ]
    
    analyzer = OracleComplexityAnalyzer()
    sql_analysis = []
    plsql_analysis = []
    
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            result = analyzer.analyze_file(sql_file)
            # PLSQLAnalysisResult는 object_type이 PLSQLObjectType enum
            if isinstance(result, PLSQLAnalysisResult):
                plsql_analysis.append(result)
            else:
                sql_analysis.append(result)
    
    print(f"  ✓ 복잡도 분석 완료")
    print(f"    - SQL 쿼리: {len(sql_analysis)}개")
    print(f"    - PL/SQL 오브젝트: {len(plsql_analysis)}개")
    
    # 3. 분석 결과 통합
    print("\n[3/6] 분석 결과 통합 중...")
    integrator = AnalysisResultIntegrator()
    integrated_result = integrator.integrate(
        dbcsi_result=dbcsi_result,
        sql_analysis=sql_analysis,
        plsql_analysis=plsql_analysis
    )
    
    metrics = integrated_result.metrics
    print(f"  ✓ 통합 완료")
    print(f"    - 평균 CPU 사용률: {metrics.avg_cpu_usage:.1f}%")
    print(f"    - 평균 I/O 부하: {metrics.avg_io_load:.1f} IOPS")
    print(f"    - 평균 SQL 복잡도: {metrics.avg_sql_complexity:.2f}")
    print(f"    - 평균 PL/SQL 복잡도: {metrics.avg_plsql_complexity:.2f}")
    
    # 4. 의사결정 및 리포트 생성
    print("\n[4/6] 마이그레이션 전략 결정 중...")
    decision_engine = MigrationDecisionEngine()
    report_generator = RecommendationReportGenerator(decision_engine)
    recommendation = report_generator.generate_recommendation(integrated_result)
    
    print(f"  ✓ 전략 결정 완료")
    print(f"    - 추천 전략: {recommendation.recommended_strategy.value}")
    
    # 5. 리포트 파일 생성
    print("\n[5/6] 리포트 파일 생성 중...")
    
    # Markdown 리포트 (영어)
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="en")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = f"reports/migration_recommendation_awr_{timestamp}.md"
    
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    
    print(f"  ✓ Markdown 리포트 생성 (영어): {markdown_path}")
    
    # JSON 리포트
    json_formatter = JSONReportFormatter()
    json_report = json_formatter.format(recommendation)
    
    json_path = f"reports/migration_recommendation_awr_{timestamp}.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_report)
    
    print(f"  ✓ JSON 리포트 생성: {json_path}")


def analyze_sql_only():
    """
    SQL/PL-SQL 분석만으로 추천 생성 (DBCSI 없음)
    """
    print("\n" + "="*80)
    print("워크플로우 3: SQL/PL-SQL 분석만 사용")
    print("="*80)
    
    # 1. SQL/PL-SQL 복잡도 분석
    print("\n[1/4] SQL/PL-SQL 복잡도 분석 중...")
    sql_files = [
        "sample_code/sample_plsql01.sql",
        "sample_code/sample_plsql02.sql",
        "sample_code/sample_plsql03.sql",
        "sample_code/sample_plsql04.sql"
    ]
    
    analyzer = OracleComplexityAnalyzer()
    sql_analysis = []
    plsql_analysis = []
    
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            result = analyzer.analyze_file(sql_file)
            # PLSQLAnalysisResult는 object_type이 PLSQLObjectType enum
            if isinstance(result, PLSQLAnalysisResult):
                plsql_analysis.append(result)
            else:
                sql_analysis.append(result)
    
    print(f"  ✓ 복잡도 분석 완료")
    print(f"    - SQL 쿼리: {len(sql_analysis)}개")
    print(f"    - PL/SQL 오브젝트: {len(plsql_analysis)}개")
    
    # 2. 분석 결과 통합 (DBCSI 없음)
    print("\n[2/4] 분석 결과 통합 중...")
    integrator = AnalysisResultIntegrator()
    integrated_result = integrator.integrate(
        dbcsi_result=None,  # DBCSI 결과 없음
        sql_analysis=sql_analysis,
        plsql_analysis=plsql_analysis
    )
    
    metrics = integrated_result.metrics
    print(f"  ✓ 통합 완료 (DBCSI 없음)")
    print(f"    - 평균 SQL 복잡도: {metrics.avg_sql_complexity:.2f}")
    print(f"    - 평균 PL/SQL 복잡도: {metrics.avg_plsql_complexity:.2f}")
    print(f"    - BULK 연산 개수: {metrics.bulk_operation_count}개")
    
    # 3. 의사결정 및 리포트 생성
    print("\n[3/4] 마이그레이션 전략 결정 중...")
    decision_engine = MigrationDecisionEngine()
    report_generator = RecommendationReportGenerator(decision_engine)
    recommendation = report_generator.generate_recommendation(integrated_result)
    
    print(f"  ✓ 전략 결정 완료")
    print(f"    - 추천 전략: {recommendation.recommended_strategy.value}")
    
    # 4. 리포트 파일 생성
    print("\n[4/4] 리포트 파일 생성 중...")
    
    markdown_formatter = MarkdownReportFormatter()
    markdown_report = markdown_formatter.format(recommendation, language="ko")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = f"reports/migration_recommendation_sql_only_{timestamp}.md"
    
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    
    print(f"  ✓ Markdown 리포트 생성: {markdown_path}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("마이그레이션 추천 시스템 - 전체 워크플로우 예제")
    print("="*80)
    
    # 워크플로우 1: Statspack 리포트 사용
    analyze_with_statspack()
    
    # 워크플로우 2: AWR 리포트 사용
    analyze_with_awr()
    
    # 워크플로우 3: SQL/PL-SQL 분석만 사용
    analyze_sql_only()
    
    print("\n" + "="*80)
    print("모든 워크플로우 완료!")
    print("="*80)
    print("\n생성된 리포트는 reports/ 디렉토리에서 확인할 수 있습니다.")
    print()
