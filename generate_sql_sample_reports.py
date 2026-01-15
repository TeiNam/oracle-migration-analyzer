#!/usr/bin/env python3
"""
SQL 복잡도 샘플 리포트 생성 스크립트

sample_code 폴더의 SQL 파일들을 분석하여 reports/sample_sql_report 폴더에 리포트를 생성합니다.
"""

import sys
from pathlib import Path
import glob

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.oracle_complexity_analyzer import OracleComplexityAnalyzer, TargetDatabase
from src.formatters.result_formatter import ResultFormatter


def generate_sql_reports():
    """sample_code 폴더의 모든 SQL 파일을 분석하여 리포트 생성"""
    print("\n" + "="*80)
    print("SQL 복잡도 샘플 리포트 생성")
    print("="*80)
    
    # sample_code 폴더의 모든 SQL 파일 찾기
    sql_files = glob.glob("sample_code/*.sql")
    
    if not sql_files:
        print("\n❌ sample_code 폴더에 SQL 파일이 없습니다.")
        return
    
    print(f"\n발견된 SQL 파일: {len(sql_files)}개")
    for sql_file in sql_files:
        print(f"  - {sql_file}")
    
    # 출력 디렉토리 생성
    output_dir = Path("reports/sample_sql_report")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n출력 디렉토리: {output_dir}")
    
    # 각 타겟 데이터베이스별로 분석
    targets = [
        TargetDatabase.POSTGRESQL,
        TargetDatabase.MYSQL
    ]
    
    # 전체 통계
    total_files = len(sql_files)
    successful_files = 0
    failed_files = 0
    
    # 각 SQL 파일 분석
    for sql_file in sorted(sql_files):
        file_name = Path(sql_file).stem
        print(f"\n{'='*80}")
        print(f"분석 중: {sql_file}")
        print(f"{'='*80}")
        
        try:
            # 각 타겟별로 분석
            for target in targets:
                print(f"\n  타겟: {target.value}")
                
                # 분석기 생성
                analyzer = OracleComplexityAnalyzer(target_database=target)
                result = analyzer.analyze_file(sql_file)
                
                # Markdown 변환
                markdown_str = ResultFormatter.to_markdown(result)
                
                # 파일명 생성: {원본파일명}_{타겟}.md
                target_name = target.value.lower().replace(" ", "_")
                output_file = output_dir / f"{file_name}_{target_name}.md"
                
                # 파일 저장
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_str)
                
                print(f"    ✓ 리포트 생성: {output_file}")
                print(f"      - 복잡도: {result.normalized_score:.2f} / 10.0")
                print(f"      - 레벨: {result.complexity_level.value}")
            
            successful_files += 1
            
        except Exception as e:
            print(f"    ❌ 오류 발생: {e}")
            failed_files += 1
    
    # 전체 요약
    print(f"\n{'='*80}")
    print("전체 요약")
    print(f"{'='*80}")
    print(f"총 파일 수: {total_files}")
    print(f"성공: {successful_files}")
    print(f"실패: {failed_files}")
    print(f"생성된 리포트 수: {successful_files * len(targets)}")
    print(f"\n모든 리포트가 {output_dir} 폴더에 저장되었습니다.")
    print()


if __name__ == "__main__":
    generate_sql_reports()
