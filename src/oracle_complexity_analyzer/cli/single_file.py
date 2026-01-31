"""
단일 파일 분석

단일 SQL/PL-SQL 파일을 분석하는 기능을 제공합니다.
"""

import logging
from typing import Any

from ..enums import TargetDatabase
from ..analyzer import OracleComplexityAnalyzer
from .utils import normalize_target, is_all_targets
from .console_output import print_result_console, print_batch_result_console

logger = logging.getLogger(__name__)


def analyze_single_file(args: Any) -> int:
    """단일 파일 분석 실행
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        from src.formatters.result_formatter import ResultFormatter
        from ..file_detector import detect_file_type
        
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
        file_type = _detect_file_type_safe(args.file)
        
        if isinstance(result, dict) and 'total_objects' in result:
            print_batch_result_console(result, target_db)
            _export_batch_results(analyzer, result, args, file_type)
            return 0
        
        if args.output in ['console', 'both']:
            print_result_console(result)
        
        _export_single_results(analyzer, result, args, file_type)
        
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


def analyze_single_file_all_targets(args: Any) -> int:
    """단일 파일 분석 - 모든 타겟 (PostgreSQL + MySQL)
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    from src.formatters.result_formatter import ResultFormatter
    
    targets = [TargetDatabase.POSTGRESQL, TargetDatabase.MYSQL]
    
    print(f"📄 파일 분석 중: {args.file}")
    
    # 파일 타입 감지
    file_type = _detect_file_type_safe(args.file)
    
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
                _export_batch_results(analyzer, result, args, file_type)
            else:
                if args.output in ['console', 'both']:
                    print_result_console(result)
                _export_single_results(analyzer, result, args, file_type)
                    
        except Exception as e:
            logger.error(f"{target_db.value} 분석 실패: {e}", exc_info=True)
            continue
    
    print(f"\n{'='*60}")
    print("✅ 모든 타겟 분석 완료")
    print(f"{'='*60}")
    
    return 0


def _detect_file_type_safe(file_path: str) -> str:
    """파일 타입을 안전하게 감지"""
    from ..file_detector import detect_file_type
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return detect_file_type(content)
    except Exception as e:
        logger.warning(f"파일 타입 감지 실패, 기본값(sql) 사용: {e}")
        return 'sql'


def _export_batch_results(
    analyzer: OracleComplexityAnalyzer, 
    result: dict, 
    args: Any, 
    file_type: str
) -> None:
    """배치 결과 내보내기"""
    from src.formatters.result_formatter import ResultFormatter
    
    if args.output in ['json', 'both']:
        json_output = ResultFormatter.batch_to_json(result)
        json_file = analyzer.export_json_string(json_output, args.file, file_type)
        print(f"✅ JSON 리포트 저장: {json_file}")
    
    if args.output in ['markdown', 'both']:
        md_output = ResultFormatter.batch_to_markdown(
            result, analyzer.target_database.value
        )
        md_file = analyzer.export_markdown_string(md_output, args.file, file_type)
        print(f"✅ Markdown 리포트 저장: {md_file}")


def _export_single_results(
    analyzer: OracleComplexityAnalyzer, 
    result: Any, 
    args: Any, 
    file_type: str
) -> None:
    """단일 결과 내보내기"""
    from src.formatters.result_formatter import ResultFormatter
    
    if args.output in ['json', 'both']:
        json_str = ResultFormatter.to_json(result)
        json_path = analyzer.export_json_string(json_str, args.file, file_type)
        print(f"✅ JSON 저장 완료: {json_path}")
    
    if args.output in ['markdown', 'both']:
        md_str = ResultFormatter.to_markdown(result)
        md_path = analyzer.export_markdown_string(md_str, args.file, file_type)
        print(f"✅ Markdown 저장 완료: {md_path}")
