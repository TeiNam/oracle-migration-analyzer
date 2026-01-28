"""
Oracle Complexity Analyzer CLI Entry Point

이 모듈은 패키지를 python -m src.oracle_complexity_analyzer로 실행할 수 있게 합니다.
"""

import sys
import argparse
import logging
from typing import Union

from .enums import TargetDatabase
from .data_models import SQLAnalysisResult, PLSQLAnalysisResult, BatchAnalysisResult
from .analyzer import OracleComplexityAnalyzer
from .batch_analyzer import BatchAnalyzer

# 로거 초기화
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog='oracle-complexity-analyzer',
        description='Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 평가합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
사용 예시:
  # 단일 파일 분석 (PostgreSQL 타겟)
  %(prog)s -f query.sql
  
  # 단일 파일 분석 (MySQL 타겟)
  %(prog)s -f query.sql -t mysql
  
  # 폴더 전체 분석 (병렬 처리)
  %(prog)s -d /path/to/sql/files
  
  # 폴더 분석 + JSON 출력
  %(prog)s -d /path/to/sql/files -o json
  
  # 폴더 분석 + 병렬 워커 수 지정
  %(prog)s -d /path/to/sql/files -w 8
  
  # 폴더 분석 + 상세 결과 포함
  %(prog)s -d /path/to/sql/files --details

지원 파일 확장자:
  .sql, .pls, .pkb, .pks, .prc, .fnc, .trg
        '''
    )
    
    # 입력 옵션 (파일 또는 폴더)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-f', '--file',
        type=str,
        metavar='FILE',
        help='분석할 단일 SQL/PL/SQL 파일 경로'
    )
    input_group.add_argument(
        '-d', '--directory',
        type=str,
        metavar='DIR',
        help='분석할 폴더 경로 (하위 폴더 포함)'
    )
    
    # 타겟 데이터베이스 선택
    parser.add_argument(
        '-t', '--target',
        type=str,
        choices=['postgresql', 'mysql', 'pg', 'my', 'all', 'both'],
        default='postgresql',
        metavar='DB',
        help='타겟 데이터베이스 (postgresql, mysql, pg, my, all, both) [기본값: postgresql]'
    )
    
    # 출력 형식 선택
    parser.add_argument(
        '-o', '--output',
        type=str,
        choices=['json', 'markdown', 'both', 'console'],
        default='console',
        metavar='FORMAT',
        help='출력 형식 (json, markdown, both, console) [기본값: console]'
    )
    
    # 출력 디렉토리
    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports',
        metavar='DIR',
        help='출력 디렉토리 경로 [기본값: reports]'
    )
    
    # 병렬 처리 워커 수 (폴더 분석 시)
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=None,
        metavar='N',
        help='병렬 처리 워커 수 (기본값: CPU 코어 수)'
    )
    
    # 상세 결과 포함 여부 (배치 분석 시)
    parser.add_argument(
        '--details',
        action='store_true',
        help='배치 분석 시 개별 파일 상세 결과 포함'
    )
    
    # 진행 상황 표시 여부
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='진행 상황 표시 비활성화'
    )
    
    # 버전 정보
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    return parser


def normalize_target(target) -> TargetDatabase:
    """타겟 데이터베이스 문자열을 TargetDatabase Enum으로 변환
    
    Args:
        target: 타겟 데이터베이스 문자열 (postgresql, mysql, pg, my) 또는 TargetDatabase Enum
        
    Returns:
        TargetDatabase: 타겟 데이터베이스 Enum
    """
    if isinstance(target, TargetDatabase):
        return target
    
    if isinstance(target, str):
        target_lower = target.lower()
        
        if target_lower in ['postgresql', 'pg']:
            return TargetDatabase.POSTGRESQL
        elif target_lower in ['mysql', 'my']:
            return TargetDatabase.MYSQL
    
    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target}")


def is_all_targets(target: str) -> bool:
    """타겟이 'all' 또는 'both'인지 확인
    
    Args:
        target: 타겟 데이터베이스 문자열
        
    Returns:
        bool: 모든 타겟 분석 여부
    """
    return target.lower() in ['all', 'both']


def print_result_console(result: Union[SQLAnalysisResult, PLSQLAnalysisResult]):
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


def print_batch_analysis_summary(batch_result, target_db: TargetDatabase):
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
            print(f"    - 매우 간단 (0-1): {batch_result.complexity_distribution.get('very_simple', 0)}")
            print(f"    - 간단 (1-3): {batch_result.complexity_distribution.get('simple', 0)}")
            print(f"    - 중간 (3-5): {batch_result.complexity_distribution.get('moderate', 0)}")
            print(f"    - 복잡 (5-7): {batch_result.complexity_distribution.get('complex', 0)}")
            print(f"    - 매우 복잡 (7-9): {batch_result.complexity_distribution.get('very_complex', 0)}")
            print(f"    - 극도로 복잡 (9-10): {batch_result.complexity_distribution.get('extremely_complex', 0)}")
        
        if batch_result.results:
            sorted_results = sorted(
                batch_result.results.items(),
                key=lambda x: x[1].normalized_score if x[1] else 0,
                reverse=True
            )
            
            print("\n🔥 복잡도 높은 파일 Top 5:")
            for i, (filename, result) in enumerate(sorted_results[:5], 1):
                if result:
                    print(f"  {i}. {filename}")
                    print(f"     원점수: {result.total_score:.2f}, 정규화: {result.normalized_score:.2f}/10")
    
    if batch_result.failure_count > 0:
        print(f"\n❌ 실패한 파일: {batch_result.failure_count}개")
        if batch_result.failed_files:
            for filename, error in list(batch_result.failed_files.items())[:5]:
                print(f"  - {filename}: {error}")
    
    print("\n" + "="*80 + "\n")


def print_batch_result_console(batch_result: dict, target_db: TargetDatabase):
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
            dist = summary['complexity_distribution']
            print("\n  복잡도 분포:")
            print(f"    - 매우 간단 (0-1): {dist.get('very_simple', 0)}")
            print(f"    - 간단 (1-3): {dist.get('simple', 0)}")
            print(f"    - 중간 (3-5): {dist.get('moderate', 0)}")
            print(f"    - 복잡 (5-7): {dist.get('complex', 0)}")
            print(f"    - 매우 복잡 (7-9): {dist.get('very_complex', 0)}")
            print(f"    - 극도로 복잡 (9-10): {dist.get('extremely_complex', 0)}")
    
    if batch_result.get('results'):
        results = batch_result['results']
        sorted_results = sorted(results, key=lambda x: x['analysis'].normalized_score, reverse=True)
        
        print("\n🔥 복잡도 높은 객체 Top 5:")
        for i, obj in enumerate(sorted_results[:5], 1):
            print(f"  {i}. {obj['owner']}.{obj['object_name']} ({obj['object_type']})")
            print(f"     원점수: {obj['analysis'].total_score:.2f}, 정규화: {obj['analysis'].normalized_score:.2f}/10")
    
    if batch_result.get('failed'):
        print("\n❌ 분석 실패 객체:")
        for failed in batch_result['failed'][:5]:
            print(f"  - {failed['owner']}.{failed['object_name']} ({failed['object_type']})")
            print(f"    에러: {failed['error']}")
        if len(batch_result['failed']) > 5:
            print(f"  ... 외 {len(batch_result['failed']) - 5}개")
    
    print("\n" + "="*80 + "\n")


def analyze_single_file(args):
    """단일 파일 분석 실행
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        from src.formatters.result_formatter import ResultFormatter
        from .file_detector import detect_file_type
        
        # all/both 옵션인 경우 두 타겟 모두 분석
        if is_all_targets(args.target):
            return analyze_single_file_all_targets(args)
        
        target_db = normalize_target(args.target)
        
        analyzer = OracleComplexityAnalyzer(
            target_database=target_db,
            output_dir=args.output_dir
        )
        
        print(f"📄 파일 분석 중: {args.file}")
        result = analyzer.analyze_file(args.file)
        
        # 파일 타입 감지
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            file_type = detect_file_type(content)
        except Exception as e:
            logger.warning(f"파일 타입 감지 실패, 기본값(sql) 사용: {e}")
            file_type = 'sql'
        
        if isinstance(result, dict) and 'total_objects' in result:
            print_batch_result_console(result, target_db)
            
            if args.output in ['json', 'both']:
                json_output = ResultFormatter.batch_to_json(result)
                json_file = analyzer.export_json_string(json_output, args.file, file_type)
                print(f"✅ JSON 리포트 저장: {json_file}")
            
            if args.output in ['markdown', 'both']:
                md_output = ResultFormatter.batch_to_markdown(result, target_db.value)
                md_file = analyzer.export_markdown_string(md_output, args.file, file_type)
                print(f"✅ Markdown 리포트 저장: {md_file}")
            
            return 0
        
        if args.output in ['console', 'both']:
            print_result_console(result)
        
        if args.output in ['json', 'both']:
            json_str = ResultFormatter.to_json(result)
            json_path = analyzer.export_json_string(json_str, args.file, file_type)
            print(f"✅ JSON 저장 완료: {json_path}")
        
        if args.output in ['markdown', 'both']:
            md_str = ResultFormatter.to_markdown(result)
            md_path = analyzer.export_markdown_string(md_str, args.file, file_type)
            print(f"✅ Markdown 저장 완료: {md_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        return 1
    except ValueError as e:
        logger.error(f"잘못된 값: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 에러: {e}", exc_info=True)
        return 1


def analyze_single_file_all_targets(args):
    """단일 파일 분석 - 모든 타겟 (PostgreSQL + MySQL)
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    from src.formatters.result_formatter import ResultFormatter
    from .file_detector import detect_file_type
    
    targets = [TargetDatabase.POSTGRESQL, TargetDatabase.MYSQL]
    
    print(f"📄 파일 분석 중: {args.file}")
    
    # 파일 타입 감지
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        file_type = detect_file_type(content)
    except Exception as e:
        logger.warning(f"파일 타입 감지 실패, 기본값(sql) 사용: {e}")
        file_type = 'sql'
    
    for target_db in targets:
        print(f"\n{'='*60}")
        print(f"🎯 타겟 데이터베이스: {target_db.value}")
        print(f"{'='*60}")
        
        try:
            analyzer = OracleComplexityAnalyzer(
                target_database=target_db,
                output_dir=args.output_dir
            )
            
            result = analyzer.analyze_file(args.file)
            
            if isinstance(result, dict) and 'total_objects' in result:
                print_batch_result_console(result, target_db)
                
                if args.output in ['json', 'both']:
                    json_output = ResultFormatter.batch_to_json(result)
                    json_file = analyzer.export_json_string(json_output, args.file, file_type)
                    print(f"✅ JSON 리포트 저장: {json_file}")
                
                if args.output in ['markdown', 'both']:
                    md_output = ResultFormatter.batch_to_markdown(result, target_db.value)
                    md_file = analyzer.export_markdown_string(md_output, args.file, file_type)
                    print(f"✅ Markdown 리포트 저장: {md_file}")
            else:
                if args.output in ['console', 'both']:
                    print_result_console(result)
                
                if args.output in ['json', 'both']:
                    json_str = ResultFormatter.to_json(result)
                    json_path = analyzer.export_json_string(json_str, args.file, file_type)
                    print(f"✅ JSON 저장 완료: {json_path}")
                
                if args.output in ['markdown', 'both']:
                    md_str = ResultFormatter.to_markdown(result)
                    md_path = analyzer.export_markdown_string(md_str, args.file, file_type)
                    print(f"✅ Markdown 저장 완료: {md_path}")
                    
        except Exception as e:
            logger.error(f"{target_db.value} 분석 실패: {e}", exc_info=True)
            continue
    
    print(f"\n{'='*60}")
    print("✅ 모든 타겟 분석 완료")
    print(f"{'='*60}")
    
    return 0


def analyze_directory(args):
    """폴더 일괄 분석 실행
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        # all/both 옵션인 경우 두 타겟 모두 분석
        if is_all_targets(args.target):
            return analyze_directory_all_targets(args)
        
        target_db = normalize_target(args.target)
        
        analyzer = OracleComplexityAnalyzer(
            target_database=target_db,
            output_dir=args.output_dir
        )
        
        batch_analyzer = BatchAnalyzer(analyzer, max_workers=args.workers)
        
        print(f"📁 폴더 검색 중: {args.directory}")
        sql_files = batch_analyzer.find_sql_files(args.directory)
        print(f"✅ {len(sql_files)}개 파일 발견")
        
        if not sql_files:
            print("⚠️  분석할 파일이 없습니다.")
            return 0
        
        print(f"\n🔄 분석 시작 (워커 수: {batch_analyzer.max_workers})")
        
        if not args.no_progress:
            try:
                from tqdm import tqdm
                batch_result = batch_analyzer.analyze_folder_with_progress(
                    args.directory,
                    progress_callback=lambda current, total: None
                )
            except ImportError:
                print("진행 중...", end='', flush=True)
                batch_result = batch_analyzer.analyze_folder(args.directory)
                print(" 완료!")
        else:
            batch_result = batch_analyzer.analyze_folder(args.directory)
        
        if args.output in ['console', 'both']:
            if hasattr(batch_result, 'total_files'):
                print_batch_analysis_summary(batch_result, target_db)
            else:
                print_batch_result_console(batch_result, target_db)
        
        if args.output in ['json', 'both']:
            json_path = batch_analyzer.export_batch_json(
                batch_result,
                include_details=args.details
            )
            print(f"✅ JSON 저장 완료: {json_path}")
        
        if args.output in ['markdown', 'both']:
            md_path = batch_analyzer.export_batch_markdown(
                batch_result,
                include_details=args.details
            )
            print(f"✅ Markdown 저장 완료: {md_path}")
        
        if args.output in ['markdown', 'both']:
            print(f"\n📝 개별 파일 리포트 생성 중...")
            individual_files = batch_analyzer.export_individual_reports(batch_result)
            print(f"✅ {len(individual_files)}개 개별 리포트 생성 완료")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        return 1
    except ValueError as e:
        logger.error(f"잘못된 값: {e}")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 에러: {e}", exc_info=True)
        return 1


def analyze_directory_all_targets(args):
    """폴더 일괄 분석 - 모든 타겟 (PostgreSQL + MySQL)
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    targets = [TargetDatabase.POSTGRESQL, TargetDatabase.MYSQL]
    
    print(f"📁 폴더 검색 중: {args.directory}")
    
    for target_db in targets:
        print(f"\n{'='*60}")
        print(f"🎯 타겟 데이터베이스: {target_db.value}")
        print(f"{'='*60}")
        
        try:
            analyzer = OracleComplexityAnalyzer(
                target_database=target_db,
                output_dir=args.output_dir
            )
            
            batch_analyzer = BatchAnalyzer(analyzer, max_workers=args.workers)
            
            sql_files = batch_analyzer.find_sql_files(args.directory)
            
            if not sql_files:
                print("⚠️  분석할 파일이 없습니다.")
                continue
            
            print(f"✅ {len(sql_files)}개 파일 발견")
            print(f"🔄 분석 시작 (워커 수: {batch_analyzer.max_workers})")
            
            if not args.no_progress:
                try:
                    from tqdm import tqdm
                    batch_result = batch_analyzer.analyze_folder_with_progress(
                        args.directory,
                        progress_callback=lambda current, total: None
                    )
                except ImportError:
                    print("진행 중...", end='', flush=True)
                    batch_result = batch_analyzer.analyze_folder(args.directory)
                    print(" 완료!")
            else:
                batch_result = batch_analyzer.analyze_folder(args.directory)
            
            if args.output in ['console', 'both']:
                if hasattr(batch_result, 'total_files'):
                    print_batch_analysis_summary(batch_result, target_db)
                else:
                    print_batch_result_console(batch_result, target_db)
            
            if args.output in ['json', 'both']:
                json_path = batch_analyzer.export_batch_json(
                    batch_result,
                    include_details=args.details
                )
                print(f"✅ JSON 저장 완료: {json_path}")
            
            if args.output in ['markdown', 'both']:
                md_path = batch_analyzer.export_batch_markdown(
                    batch_result,
                    include_details=args.details
                )
                print(f"✅ Markdown 저장 완료: {md_path}")
            
            if args.output in ['markdown', 'both']:
                print(f"\n📝 개별 파일 리포트 생성 중...")
                individual_files = batch_analyzer.export_individual_reports(batch_result)
                print(f"✅ {len(individual_files)}개 개별 리포트 생성 완료")
                
        except Exception as e:
            logger.error(f"{target_db.value} 분석 실패: {e}", exc_info=True)
            continue
    
    print(f"\n{'='*60}")
    print("✅ 모든 타겟 분석 완료")
    print(f"{'='*60}")
    
    return 0


def main():
    """CLI 메인 함수
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    # 로깅 초기화
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    parser = create_parser()
    args = parser.parse_args()
    
    if args.file:
        return analyze_single_file(args)
    elif args.directory:
        return analyze_directory(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
