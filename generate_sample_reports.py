#!/usr/bin/env python3
"""
샘플 리포트 생성 스크립트

sample_code 폴더의 파일들을 분석하여 샘플 리포트를 생성합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.oracle_complexity_analyzer import OracleComplexityAnalyzer, TargetDatabase
from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter

def generate_sql_complexity_report():
    """SQL 복잡도 샘플 리포트 생성"""
    print("\n" + "="*80)
    print("SQL 복잡도 샘플 리포트 생성")
    print("="*80)
    
    # 샘플 PL/SQL 파일 하나 분석
    sample_file = "sample_code/sample_plsql01.sql"
    
    print(f"\n분석 중: {sample_file}")
    
    analyzer = OracleComplexityAnalyzer(target_database=TargetDatabase.POSTGRESQL)
    result = analyzer.analyze_file(sample_file)
    
    # Markdown 변환
    from src.formatters.result_formatter import ResultFormatter
    markdown_str = ResultFormatter.to_markdown(result)
    
    # reports/ 루트에 직접 저장
    md_path = "reports/sample_sql_complexity_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_str)
    
    print(f"\n✓ SQL 복잡도 리포트 생성: {md_path}")
    print(f"  - 복잡도: {result.normalized_score:.2f} / 10.0")
    print(f"  - 레벨: {result.complexity_level.value}")

def generate_dbcsi_report():
    """DBCSI 샘플 리포트 생성"""
    print("\n" + "="*80)
    print("DBCSI 샘플 리포트 생성")
    print("="*80)
    
    # Statspack 샘플 파일 분석
    statspack_file = "sample_code/dbcsi_statspack_sample01.out"
    
    print(f"\n분석 중: {statspack_file}")
    
    # 1. 파싱
    parser = StatspackParser(statspack_file)
    statspack_data = parser.parse()
    
    # 2. 분석 (모든 타겟 데이터베이스에 대해)
    analyzer = MigrationAnalyzer(statspack_data)
    analysis_results = analyzer.analyze()
    
    # 3. 리포트 생성
    formatter = StatspackResultFormatter()
    
    # Markdown 파일로 저장
    md_report = formatter.to_markdown(statspack_data, analysis_results)
    md_path = "reports/sample_statspack_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"\n✓ DBCSI 리포트 생성: {md_path}")
    print(f"  - DB 이름: {statspack_data.os_info.db_name}")
    print(f"  - 버전: {statspack_data.os_info.version}")
    
    # JSON 파일로 저장
    json_report = formatter.to_json(statspack_data)
    json_path = "reports/sample_statspack_report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_report)
    
    print(f"✓ DBCSI JSON 리포트 생성: {json_path}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("샘플 리포트 생성 시작")
    print("="*80)
    
    # SQL 복잡도 리포트 생성
    generate_sql_complexity_report()
    
    # DBCSI 리포트 생성
    generate_dbcsi_report()
    
    print("\n" + "="*80)
    print("모든 샘플 리포트 생성 완료!")
    print("="*80)
    print("\n생성된 리포트:")
    print("  - reports/sample_sql_complexity_report.md")
    print("  - reports/sample_statspack_report.md")
    print("  - reports/sample_statspack_report.json")
    print()
