"""
콘솔 출력 함수

분석 결과를 콘솔에 출력하는 함수들을 제공합니다.
"""

from typing import Union

from ..enums import TargetDatabase
from ..data_models import SQLAnalysisResult, PLSQLAnalysisResult


def print_result_console(result: Union[SQLAnalysisResult, PLSQLAnalysisResult]) -> None:
    """분석 결과를 콘솔에 출력
    
    Args:
        result: 분석 결과 객체
    """
    print("\n" + "="*80)
    print("📊 Oracle 복잡도 분석 결과")
    print("="*80)
    
    print(f"\n타겟 데이터베이스: {result.target_database.value}")
    print(f"원점수 (Raw Score): {result.total_score:.2f}")
    print(f"정규화 점수: {result.normalized_score:.2f} / 10")
    print(f"복잡도 레벨: {result.complexity_level.value}")
    print(f"권장사항: {result.recommendation}")
    
    print("\n📈 세부 점수:")
    
    if hasattr(result, 'structural_complexity'):
        # SQLAnalysisResult
        print(f"  - 구조적 복잡성: {result.structural_complexity:.2f}")
        print(f"  - Oracle 특화 기능: {result.oracle_specific_features:.2f}")
        print(f"  - 함수/표현식: {result.functions_expressions:.2f}")
        print(f"  - 데이터 볼륨: {result.data_volume:.2f}")
        print(f"  - 실행 복잡성: {result.execution_complexity:.2f}")
        print(f"  - 변환 난이도: {result.conversion_difficulty:.2f}")
    else:
        # PLSQLAnalysisResult
        print(f"  - 기본 점수: {result.base_score:.2f}")
        print(f"  - 코드 복잡도: {result.code_complexity:.2f}")
        print(f"  - Oracle 특화 기능: {result.oracle_features:.2f}")
        print(f"  - 비즈니스 로직: {result.business_logic:.2f}")
        print(f"  - 변환 난이도: {result.conversion_difficulty:.2f}")
        if hasattr(result, 'mysql_constraints') and result.mysql_constraints > 0:
            print(f"  - MySQL 제약: {result.mysql_constraints:.2f}")
        if hasattr(result, 'app_migration_penalty') and result.app_migration_penalty > 0:
            print(f"  - 애플리케이션 이관 페널티: {result.app_migration_penalty:.2f}")
    
    if result.detected_oracle_features:
        print("\n🔍 감지된 Oracle 특화 기능:")
        for feature in result.detected_oracle_features:
            print(f"  - {feature}")
    
    if hasattr(result, 'detected_oracle_functions') and result.detected_oracle_functions:
        print("\n🔧 감지된 Oracle 특화 함수:")
        for func in result.detected_oracle_functions:
            print(f"  - {func}")
    
    if hasattr(result, 'detected_external_dependencies') and result.detected_external_dependencies:
        print("\n📦 감지된 외부 의존성:")
        for dep in result.detected_external_dependencies:
            print(f"  - {dep}")
    
    if result.conversion_guides:
        print("\n💡 변환 가이드:")
        for feature, guide in result.conversion_guides.items():
            print(f"  - {feature}: {guide}")
    
    print("\n" + "="*80 + "\n")


def print_batch_analysis_summary(batch_result, target_db: TargetDatabase) -> None:
    """일반 배치 분석 결과(BatchAnalysisResult)를 콘솔에 출력
    
    Args:
        batch_result: BatchAnalysisResult 객체
        target_db: 타겟 데이터베이스
    """
    print("\n" + "="*80)
    print("📊 배치 분석 결과")
    print("="*80)
    
    print(f"\n타겟 데이터베이스: {target_db.value}")
    print(f"전체 파일 수: {batch_result.total_files}")
    print(f"분석 성공: {batch_result.success_count}")
    print(f"분석 실패: {batch_result.failure_count}")
    
    if batch_result.success_count > 0:
        print(f"\n🎯 복잡도 요약:")
        print(f"  - 평균 복잡도: {batch_result.average_score:.2f}/10")
        
        if batch_result.complexity_distribution:
            print(f"\n  복잡도 분포:")
            _print_complexity_distribution(batch_result.complexity_distribution)
        
        if batch_result.results:
            _print_top_complex_files(batch_result.results)
    
    if batch_result.failure_count > 0:
        print(f"\n❌ 실패한 파일: {batch_result.failure_count}개")
        if batch_result.failed_files:
            for filename, error in list(batch_result.failed_files.items())[:5]:
                print(f"  - {filename}: {error}")
    
    print("\n" + "="*80 + "\n")


def print_batch_result_console(batch_result: dict, target_db: TargetDatabase) -> None:
    """배치 PL/SQL 분석 결과를 콘솔에 출력
    
    Args:
        batch_result: 배치 분석 결과 딕셔너리
        target_db: 타겟 데이터베이스
    """
    print("\n" + "="*80)
    print("📊 배치 PL/SQL 분석 결과")
    print("="*80)
    
    print(f"\n타겟 데이터베이스: {target_db.value}")
    print(f"전체 객체 수: {batch_result['total_objects']}")
    print(f"분석 성공: {batch_result['analyzed_objects']}")
    print(f"분석 실패: {batch_result['failed_objects']}")
    
    if batch_result.get('statistics'):
        print("\n📈 객체 타입별 통계:")
        for obj_type, count in sorted(batch_result['statistics'].items()):
            print(f"  - {obj_type}: {count}")
    
    if batch_result.get('summary'):
        summary = batch_result['summary']
        print("\n🎯 복잡도 요약:")
        print(f"  - 평균 복잡도: {summary.get('average_score', 0):.2f}")
        print(f"  - 최대 복잡도: {summary.get('max_score', 0):.2f}")
        print(f"  - 최소 복잡도: {summary.get('min_score', 0):.2f}")
        
        if summary.get('complexity_distribution'):
            print("\n  복잡도 분포:")
            _print_complexity_distribution(summary['complexity_distribution'])
    
    if batch_result.get('results'):
        _print_top_complex_objects(batch_result['results'])
    
    if batch_result.get('failed'):
        _print_failed_objects(batch_result['failed'])
    
    print("\n" + "="*80 + "\n")


def _print_complexity_distribution(dist: dict) -> None:
    """복잡도 분포 출력"""
    print(f"    - 매우 간단 (0-1): {dist.get('very_simple', 0)}")
    print(f"    - 간단 (1-3): {dist.get('simple', 0)}")
    print(f"    - 중간 (3-5): {dist.get('moderate', 0)}")
    print(f"    - 복잡 (5-7): {dist.get('complex', 0)}")
    print(f"    - 매우 복잡 (7-9): {dist.get('very_complex', 0)}")
    print(f"    - 극도로 복잡 (9-10): {dist.get('extremely_complex', 0)}")


def _print_top_complex_files(results: dict) -> None:
    """복잡도 높은 파일 Top 5 출력"""
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1].normalized_score if x[1] else 0,
        reverse=True
    )
    
    print("\n🔥 복잡도 높은 파일 Top 5:")
    for i, (filename, result) in enumerate(sorted_results[:5], 1):
        if result:
            print(f"  {i}. {filename}")
            print(f"     원점수: {result.total_score:.2f}, "
                  f"정규화: {result.normalized_score:.2f}/10")


def _print_top_complex_objects(results: list) -> None:
    """복잡도 높은 객체 Top 5 출력"""
    sorted_results = sorted(
        results, 
        key=lambda x: x['analysis'].normalized_score, 
        reverse=True
    )
    
    print("\n🔥 복잡도 높은 객체 Top 5:")
    for i, obj in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {obj['owner']}.{obj['object_name']} ({obj['object_type']})")
        print(f"     원점수: {obj['analysis'].total_score:.2f}, "
              f"정규화: {obj['analysis'].normalized_score:.2f}/10")


def _print_failed_objects(failed: list) -> None:
    """분석 실패 객체 출력"""
    print("\n❌ 분석 실패 객체:")
    for item in failed[:5]:
        print(f"  - {item['owner']}.{item['object_name']} ({item['object_type']})")
        print(f"    에러: {item['error']}")
    if len(failed) > 5:
        print(f"  ... 외 {len(failed) - 5}개")
