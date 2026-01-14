"""
BatchAnalyzer 사용 예제

폴더 내 모든 SQL/PL/SQL 파일을 일괄 분석하는 예제입니다.
"""

from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    TargetDatabase
)


def main():
    """배치 분석 예제"""
    
    print("=" * 80)
    print("Oracle 복잡도 분석기 - 배치 분석 예제")
    print("=" * 80)
    print()
    
    # 1. OracleComplexityAnalyzer 생성
    print("1. 분석기 초기화...")
    analyzer = OracleComplexityAnalyzer(
        target_database=TargetDatabase.POSTGRESQL,
        output_dir="reports"
    )
    print(f"   타겟 데이터베이스: {analyzer.target.value}")
    print()
    
    # 2. BatchAnalyzer 생성
    print("2. 배치 분석기 초기화...")
    batch_analyzer = BatchAnalyzer(
        analyzer=analyzer,
        max_workers=4  # 병렬 처리 워커 수
    )
    print(f"   병렬 처리 워커 수: {batch_analyzer.max_workers}")
    print()
    
    # 3. 분석할 폴더 지정
    folder_path = "sample_code"  # 분석할 폴더 경로
    
    print(f"3. 폴더 내 SQL/PL/SQL 파일 검색: {folder_path}")
    try:
        sql_files = batch_analyzer.find_sql_files(folder_path)
        print(f"   찾은 파일 수: {len(sql_files)}")
        for file in sql_files:
            print(f"   - {file}")
        print()
    except FileNotFoundError as e:
        print(f"   에러: {e}")
        print("   sample_code 폴더가 없습니다. 테스트 폴더를 생성하거나 다른 폴더를 지정하세요.")
        return
    
    if not sql_files:
        print("   분석할 파일이 없습니다.")
        return
    
    # 4. 폴더 일괄 분석
    print("4. 폴더 일괄 분석 시작...")
    batch_result = batch_analyzer.analyze_folder(folder_path)
    print("   분석 완료!")
    print()
    
    # 5. 분석 결과 요약 출력
    print("5. 분석 결과 요약")
    print("-" * 80)
    print(f"   전체 파일 수: {batch_result.total_files}")
    print(f"   분석 성공: {batch_result.success_count}")
    print(f"   분석 실패: {batch_result.failure_count}")
    print(f"   평균 복잡도 점수: {batch_result.average_score:.2f} / 10")
    print()
    
    # 6. 복잡도 레벨별 분포
    print("6. 복잡도 레벨별 분포")
    print("-" * 80)
    for level_name, count in batch_result.complexity_distribution.items():
        if count > 0:
            percentage = (count / batch_result.success_count * 100) if batch_result.success_count > 0 else 0
            print(f"   {level_name}: {count}개 ({percentage:.1f}%)")
    print()
    
    # 7. 복잡도 높은 파일 Top 5
    print("7. 복잡도 높은 파일 Top 5")
    print("-" * 80)
    top_files = batch_analyzer.get_top_complex_files(batch_result, top_n=5)
    for idx, (file_name, score) in enumerate(top_files, 1):
        print(f"   {idx}. {file_name}")
        print(f"      복잡도 점수: {score:.2f} / 10")
    print()
    
    # 8. 실패한 파일 목록
    if batch_result.failed_files:
        print("8. 분석 실패 파일")
        print("-" * 80)
        for file_name, error in batch_result.failed_files.items():
            print(f"   {file_name}")
            print(f"      에러: {error}")
        print()
    
    # 9. 결과 저장
    print("9. 결과 저장")
    print("-" * 80)
    
    # JSON 저장
    json_path = batch_analyzer.export_batch_json(batch_result, include_details=True)
    print(f"   JSON 저장: {json_path}")
    
    # Markdown 저장
    md_path = batch_analyzer.export_batch_markdown(batch_result, include_details=False)
    print(f"   Markdown 저장: {md_path}")
    print()
    
    print("=" * 80)
    print("배치 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
