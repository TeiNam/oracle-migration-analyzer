#!/usr/bin/env python3
"""sample_plsql.sql 파일 분석 스크립트"""

from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    TargetDatabase
)

def main():
    print("=" * 80)
    print("sample_plsql.sql 복잡도 분석")
    print("=" * 80)
    print()
    
    # 파일 읽기
    with open('sample_code/sample_plsql.sql', 'r', encoding='utf-8') as f:
        plsql_code = f.read()
    
    # PostgreSQL 타겟 분석
    print("1. PostgreSQL 타겟 분석")
    print("-" * 80)
    analyzer_pg = OracleComplexityAnalyzer(
        target_database=TargetDatabase.POSTGRESQL,
        output_dir="analysis_results"
    )
    
    result_pg = analyzer_pg.analyze_plsql(plsql_code)
    
    print(f"복잡도 점수: {result_pg.normalized_score:.2f} / 10.0")
    print(f"복잡도 레벨: {result_pg.complexity_level.value}")
    print(f"권장사항: {result_pg.recommendation}")
    print(f"오브젝트 타입: {result_pg.object_type.value}")
    print()
    print("세부 점수:")
    print(f"  - 기본 점수: {result_pg.base_score:.2f}")
    print(f"  - 코드 복잡도: {result_pg.code_complexity:.2f}")
    print(f"  - Oracle 특화 기능: {result_pg.oracle_features:.2f}")
    print(f"  - 비즈니스 로직: {result_pg.business_logic:.2f}")
    print(f"  - AI 변환 난이도: {result_pg.ai_difficulty:.2f}")
    print()
    print("분석 메타데이터:")
    print(f"  - 코드 라인 수: {result_pg.line_count}")
    print(f"  - 커서 개수: {result_pg.cursor_count}")
    print(f"  - 예외 블록: {result_pg.exception_blocks}")
    print(f"  - 중첩 깊이: {result_pg.nesting_depth}")
    print(f"  - BULK 연산: {result_pg.bulk_operations_count}")
    print(f"  - 동적 SQL: {result_pg.dynamic_sql_count}")
    print()
    
    if result_pg.detected_oracle_features:
        print("감지된 Oracle 특화 기능:")
        for feature in result_pg.detected_oracle_features:
            print(f"  - {feature}")
        print()
    
    if result_pg.detected_external_dependencies:
        print("감지된 외부 의존성:")
        for dep in result_pg.detected_external_dependencies:
            print(f"  - {dep}")
        print()
    
    if result_pg.conversion_guides:
        print("변환 가이드:")
        for feature, guide in result_pg.conversion_guides.items():
            print(f"  - {feature}: {guide}")
        print()
    
    # JSON 및 Markdown 저장
    json_path = analyzer_pg.export_json(result_pg, "sample_plsql_pg.json")
    md_path = analyzer_pg.export_markdown(result_pg, "sample_plsql_pg.md")
    print(f"PostgreSQL 분석 결과 저장:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print()
    
    # MySQL 타겟 분석
    print("=" * 80)
    print("2. MySQL 타겟 분석")
    print("-" * 80)
    analyzer_mysql = OracleComplexityAnalyzer(
        target_database=TargetDatabase.MYSQL,
        output_dir="analysis_results"
    )
    
    result_mysql = analyzer_mysql.analyze_plsql(plsql_code)
    
    print(f"복잡도 점수: {result_mysql.normalized_score:.2f} / 10.0")
    print(f"복잡도 레벨: {result_mysql.complexity_level.value}")
    print(f"권장사항: {result_mysql.recommendation}")
    print(f"오브젝트 타입: {result_mysql.object_type.value}")
    print()
    print("세부 점수:")
    print(f"  - 기본 점수: {result_mysql.base_score:.2f}")
    print(f"  - 코드 복잡도: {result_mysql.code_complexity:.2f}")
    print(f"  - Oracle 특화 기능: {result_mysql.oracle_features:.2f}")
    print(f"  - 비즈니스 로직: {result_mysql.business_logic:.2f}")
    print(f"  - AI 변환 난이도: {result_mysql.ai_difficulty:.2f}")
    print(f"  - MySQL 제약: {result_mysql.mysql_constraints:.2f}")
    print(f"  - 애플리케이션 이관 페널티: {result_mysql.app_migration_penalty:.2f}")
    print()
    print("분석 메타데이터:")
    print(f"  - 코드 라인 수: {result_mysql.line_count}")
    print(f"  - 커서 개수: {result_mysql.cursor_count}")
    print(f"  - 예외 블록: {result_mysql.exception_blocks}")
    print(f"  - 중첩 깊이: {result_mysql.nesting_depth}")
    print(f"  - BULK 연산: {result_mysql.bulk_operations_count}")
    print(f"  - 동적 SQL: {result_mysql.dynamic_sql_count}")
    print()
    
    if result_mysql.conversion_guides:
        print("변환 가이드:")
        for feature, guide in result_mysql.conversion_guides.items():
            print(f"  - {feature}: {guide}")
        print()
    
    # JSON 및 Markdown 저장
    json_path = analyzer_mysql.export_json(result_mysql, "sample_plsql_mysql.json")
    md_path = analyzer_mysql.export_markdown(result_mysql, "sample_plsql_mysql.md")
    print(f"MySQL 분석 결과 저장:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print()
    
    print("=" * 80)
    print("분석 완료!")
    print("=" * 80)

if __name__ == "__main__":
    main()
