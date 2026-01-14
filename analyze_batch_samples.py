#!/usr/bin/env python3
"""sample_plsql01~04 파일들을 병렬로 분석하는 스크립트"""

from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    TargetDatabase,
    BatchAnalyzer
)
from pathlib import Path
import concurrent.futures

def analyze_files_parallel(analyzer, file_paths, max_workers=4):
    """파일 리스트를 병렬로 분석"""
    results = []
    errors = []
    
    def analyze_single(file_path):
        try:
            result = analyzer.analyze_file(str(file_path))
            return (str(file_path), result, None)
        except Exception as e:
            return (str(file_path), None, str(e))
    
    # ThreadPoolExecutor 사용 (Pickle 문제 회피)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_single, fp) for fp in file_paths]
        
        for future in concurrent.futures.as_completed(futures):
            file_path, result, error = future.result()
            if error:
                errors.append((file_path, error))
            else:
                results.append((file_path, result))
    
    return results, errors

def calculate_stats(results):
    """분석 결과 통계 계산"""
    if not results:
        return {
            'total': 0,
            'success': 0,
            'average_score': 0.0,
            'distribution': {},
            'top_files': []
        }
    
    scores = [(fp, r.normalized_score) for fp, r in results]
    levels = {}
    
    for fp, r in results:
        level = r.complexity_level.value
        levels[level] = levels.get(level, 0) + 1
    
    avg_score = sum(s for _, s in scores) / len(scores)
    top_files = sorted(scores, key=lambda x: x[1], reverse=True)
    
    return {
        'total': len(results),
        'success': len(results),
        'average_score': avg_score,
        'distribution': levels,
        'top_files': top_files
    }

def main():
    print("=" * 80)
    print("sample_plsql01~04 배치 분석 (병렬 처리)")
    print("=" * 80)
    print()
    
    # 분석 대상 파일 찾기
    sample_files = sorted(Path("sample_code").glob("sample_plsql*.sql"))
    print(f"분석 대상 파일: {len(sample_files)}개")
    for f in sample_files:
        print(f"  - {f}")
    print()
    
    # PostgreSQL 타겟 분석
    print("1. PostgreSQL 타겟으로 배치 분석")
    print("-" * 80)
    
    analyzer_pg = OracleComplexityAnalyzer(
        target_database=TargetDatabase.POSTGRESQL,
        output_dir="batch_analysis_results"
    )
    
    print("분석 중...")
    results_pg, errors_pg = analyze_files_parallel(analyzer_pg, sample_files, max_workers=4)
    
    print()
    print("분석 완료!")
    print()
    
    stats_pg = calculate_stats(results_pg)
    
    print("📊 요약 통계 (PostgreSQL)")
    print(f"  - 전체 파일 수: {len(sample_files)}")
    print(f"  - 분석 성공: {stats_pg['success']}")
    print(f"  - 분석 실패: {len(errors_pg)}")
    print(f"  - 평균 복잡도 점수: {stats_pg['average_score']:.2f} / 10")
    print()
    
    if errors_pg:
        print("❌ 분석 실패 파일:")
        for fp, err in errors_pg:
            print(f"  - {Path(fp).name}: {err}")
        print()
    
    print("📈 복잡도 레벨별 분포:")
    for level, count in stats_pg['distribution'].items():
        percentage = (count / stats_pg['total'] * 100) if stats_pg['total'] > 0 else 0
        print(f"  - {level}: {count}개 ({percentage:.1f}%)")
    print()
    
    print("🔥 복잡도 높은 파일:")
    for idx, (file_path, score) in enumerate(stats_pg['top_files'], 1):
        print(f"  {idx}. {Path(file_path).name}: {score:.2f}")
    print()
    
    # 개별 파일 결과 저장
    for file_path, result in results_pg:
        file_name = Path(file_path).stem
        analyzer_pg.export_json(result, f"{file_name}_pg.json")
        analyzer_pg.export_markdown(result, f"{file_name}_pg.md")
    
    print(f"PostgreSQL 분석 결과 저장 완료")
    print()
    
    # MySQL 타겟 분석
    print("=" * 80)
    print("2. MySQL 타겟으로 배치 분석")
    print("-" * 80)
    
    analyzer_mysql = OracleComplexityAnalyzer(
        target_database=TargetDatabase.MYSQL,
        output_dir="batch_analysis_results"
    )
    
    print("분석 중...")
    results_mysql, errors_mysql = analyze_files_parallel(analyzer_mysql, sample_files, max_workers=4)
    
    print()
    print("분석 완료!")
    print()
    
    stats_mysql = calculate_stats(results_mysql)
    
    print("📊 요약 통계 (MySQL)")
    print(f"  - 전체 파일 수: {len(sample_files)}")
    print(f"  - 분석 성공: {stats_mysql['success']}")
    print(f"  - 분석 실패: {len(errors_mysql)}")
    print(f"  - 평균 복잡도 점수: {stats_mysql['average_score']:.2f} / 10")
    print()
    
    if errors_mysql:
        print("❌ 분석 실패 파일:")
        for fp, err in errors_mysql:
            print(f"  - {Path(fp).name}: {err}")
        print()
    
    print("📈 복잡도 레벨별 분포:")
    for level, count in stats_mysql['distribution'].items():
        percentage = (count / stats_mysql['total'] * 100) if stats_mysql['total'] > 0 else 0
        print(f"  - {level}: {count}개 ({percentage:.1f}%)")
    print()
    
    print("🔥 복잡도 높은 파일:")
    for idx, (file_path, score) in enumerate(stats_mysql['top_files'], 1):
        print(f"  {idx}. {Path(file_path).name}: {score:.2f}")
    print()
    
    # 개별 파일 결과 저장
    for file_path, result in results_mysql:
        file_name = Path(file_path).stem
        analyzer_mysql.export_json(result, f"{file_name}_mysql.json")
        analyzer_mysql.export_markdown(result, f"{file_name}_mysql.md")
    
    print(f"MySQL 분석 결과 저장 완료")
    print()
    
    # 비교 분석
    print("=" * 80)
    print("3. PostgreSQL vs MySQL 비교")
    print("-" * 80)
    print(f"평균 복잡도 점수:")
    print(f"  - PostgreSQL: {stats_pg['average_score']:.2f}")
    print(f"  - MySQL: {stats_mysql['average_score']:.2f}")
    print(f"  - 차이: {stats_mysql['average_score'] - stats_pg['average_score']:.2f}")
    print()
    
    print("파일별 복잡도 비교:")
    for (fp_pg, result_pg), (fp_mysql, result_mysql) in zip(results_pg, results_mysql):
        file_name = Path(fp_pg).name
        diff = result_mysql.normalized_score - result_pg.normalized_score
        print(f"  - {file_name}:")
        print(f"      PostgreSQL: {result_pg.normalized_score:.2f}, MySQL: {result_mysql.normalized_score:.2f}, 차이: {diff:+.2f}")
    print()
    
    print("=" * 80)
    print("배치 분석 완료!")
    print(f"결과 저장 위치: batch_analysis_results/20260114/")
    print("=" * 80)

if __name__ == "__main__":
    main()
