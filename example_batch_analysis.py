#!/usr/bin/env python3
"""
Statspack 배치 파일 분석 예제

이 스크립트는 여러 Statspack 파일을 일괄 분석하는 방법을 보여줍니다.
"""

import os
from src.dbcsi.batch_analyzer import StatspackBatchAnalyzer
from src.dbcsi.data_models import TargetDatabase


def main():
    print("=" * 80)
    print("Statspack 배치 파일 분석 예제")
    print("=" * 80)
    
    # 1. 배치 분석기 생성
    analyzer = StatspackBatchAnalyzer()
    
    # 2. 디렉토리 지정 (sample_code 디렉토리의 .out 파일들)
    directory = "sample_code"
    
    print(f"\n분석 디렉토리: {directory}")
    print("분석 중...")
    
    # 3. 배치 분석 실행
    batch_result = analyzer.analyze_directory(directory)
    
    # 4. 결과 요약 출력
    print("\n" + "=" * 80)
    print("배치 분석 결과 요약")
    print("=" * 80)
    
    print(f"\n전체 파일 수: {batch_result.total_files}")
    print(f"분석 성공: {batch_result.success_count}")
    print(f"분석 실패: {batch_result.failed_count}")
    
    if batch_result.failed_files:
        print("\n실패한 파일:")
        for filepath, error in batch_result.failed_files.items():
            print(f"  - {filepath}: {error}")
    
    # 5. 개별 파일 결과 출력
    if batch_result.results:
        print("\n" + "=" * 80)
        print("개별 파일 분석 결과")
        print("=" * 80)
        
        for filepath, result in batch_result.results.items():
            print(f"\n파일: {os.path.basename(filepath)}")
            print(f"  DB 이름: {result.statspack_data.os_info.db_name}")
            print(f"  버전: {result.statspack_data.os_info.version}")
            print(f"  총 DB 크기: {result.statspack_data.os_info.total_db_size_gb} GB")
            
            if result.migration_analysis:
                print(f"\n  마이그레이션 난이도:")
                for target, complexity in result.migration_analysis.items():
                    print(f"    - {target.value}: {complexity.score:.2f} / 10.0 ({complexity.level})")
                    if complexity.instance_recommendation:
                        print(f"      추천 인스턴스: {complexity.instance_recommendation.instance_type}")
    
    # 6. 배치 요약 리포트 저장
    print("\n" + "=" * 80)
    print("배치 요약 리포트 저장 중...")
    print("=" * 80)
    
    # JSON 형식으로 저장
    json_path = analyzer.save_batch_summary(
        batch_result,
        output_dir="reports",
        format="json"
    )
    print(f"JSON 리포트 저장: {json_path}")
    
    # Markdown 형식으로 저장
    md_path = analyzer.save_batch_summary(
        batch_result,
        output_dir="reports",
        format="markdown"
    )
    print(f"Markdown 리포트 저장: {md_path}")
    
    print("\n" + "=" * 80)
    print("배치 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
