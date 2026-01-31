"""
폴더 분석

폴더 내 SQL/PL-SQL 파일들을 일괄 분석하는 기능을 제공합니다.
"""

import logging
from typing import Any

from ..enums import TargetDatabase
from ..analyzer import OracleComplexityAnalyzer
from ..batch_analyzer import BatchAnalyzer
from .utils import normalize_target, is_all_targets
from .console_output import print_batch_result_console, print_batch_analysis_summary

logger = logging.getLogger(__name__)


def analyze_directory(args: Any) -> int:
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
        
        batch_result = _run_batch_analysis(batch_analyzer, args)
        
        _output_batch_results(batch_result, target_db, args)
        _export_batch_reports(batch_analyzer, batch_result, args)
        
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


def analyze_directory_all_targets(args: Any) -> int:
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
            
            batch_result = _run_batch_analysis(batch_analyzer, args)
            
            _output_batch_results(batch_result, target_db, args)
            _export_batch_reports(batch_analyzer, batch_result, args)
                
        except Exception as e:
            logger.error(f"{target_db.value} 분석 실패: {e}", exc_info=True)
            continue
    
    print(f"\n{'='*60}")
    print("✅ 모든 타겟 분석 완료")
    print(f"{'='*60}")
    
    return 0


def _run_batch_analysis(batch_analyzer: BatchAnalyzer, args: Any) -> Any:
    """배치 분석 실행"""
    if not args.no_progress:
        try:
            from tqdm import tqdm
            return batch_analyzer.analyze_folder_with_progress(
                args.directory,
                progress_callback=lambda current, total: None
            )
        except ImportError:
            print("진행 중...", end='', flush=True)
            result = batch_analyzer.analyze_folder(args.directory)
            print(" 완료!")
            return result
    else:
        return batch_analyzer.analyze_folder(args.directory)


def _output_batch_results(batch_result: Any, target_db: TargetDatabase, args: Any) -> None:
    """배치 결과 콘솔 출력"""
    if args.output in ['console', 'both']:
        if hasattr(batch_result, 'total_files'):
            print_batch_analysis_summary(batch_result, target_db)
        else:
            print_batch_result_console(batch_result, target_db)


def _export_batch_reports(batch_analyzer: BatchAnalyzer, batch_result: Any, args: Any) -> None:
    """배치 리포트 내보내기"""
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
