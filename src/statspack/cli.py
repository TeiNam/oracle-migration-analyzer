#!/usr/bin/env python3
"""
Statspack 분석 도구 CLI 인터페이스

DBCSI Statspack 결과 파일을 파싱하고 마이그레이션 난이도를 분석하는 커맨드라인 도구입니다.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List

from .parser import StatspackParser
from .migration_analyzer import MigrationAnalyzer, TargetDatabase
from .result_formatter import StatspackResultFormatter
from .batch_analyzer import BatchAnalyzer
from .logging_config import setup_logging, get_logger

# 로거는 main 함수에서 초기화됩니다


def create_parser() -> argparse.ArgumentParser:
    """
    CLI 인자 파서를 생성합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog="statspack-analyzer",
        description="DBCSI Statspack 결과 파일을 분석하여 마이그레이션 난이도를 평가합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 파일 분석 (Markdown 출력)
  %(prog)s --file sample.out
  
  # 단일 파일 분석 (JSON 출력)
  %(prog)s --file sample.out --format json
  
  # 디렉토리 내 모든 파일 배치 분석
  %(prog)s --directory ./statspack_files/
  
  # 마이그레이션 분석 포함
  %(prog)s --file sample.out --analyze-migration
  
  # 특정 타겟 DB만 분석
  %(prog)s --file sample.out --analyze-migration --target aurora-postgresql
  
  # 결과를 파일로 저장
  %(prog)s --file sample.out --output report.md
        """
    )
    
    # 입력 옵션 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file",
        type=str,
        metavar="PATH",
        help="분석할 단일 Statspack 파일 경로 (.out 파일)"
    )
    input_group.add_argument(
        "--directory",
        type=str,
        metavar="PATH",
        help="Statspack 파일이 있는 디렉토리 경로 (모든 .out 파일 분석)"
    )
    
    # 출력 형식 옵션
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown"],
        default="markdown",
        help="출력 형식 (기본값: markdown)"
    )
    
    # 출력 파일 옵션
    parser.add_argument(
        "--output",
        type=str,
        metavar="PATH",
        help="결과를 저장할 파일 경로 (지정하지 않으면 표준 출력)"
    )
    
    # 타겟 DB 옵션
    parser.add_argument(
        "--target",
        type=str,
        choices=["rds-oracle", "aurora-mysql", "aurora-postgresql", "all"],
        default="all",
        help="마이그레이션 타겟 데이터베이스 (기본값: all)"
    )
    
    # 마이그레이션 분석 플래그
    parser.add_argument(
        "--analyze-migration",
        action="store_true",
        help="마이그레이션 난이도 분석 포함"
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """
    CLI 인자의 유효성을 검증합니다.
    
    Args:
        args: 파싱된 CLI 인자
        
    Raises:
        SystemExit: 유효하지 않은 인자가 있을 경우
    """
    # 파일 존재 확인
    if args.file:
        if not os.path.exists(args.file):
            print(f"오류: 파일을 찾을 수 없습니다: {args.file}", file=sys.stderr)
            sys.exit(1)
        if not args.file.endswith('.out'):
            print(f"경고: Statspack 파일은 일반적으로 .out 확장자를 가집니다: {args.file}", 
                  file=sys.stderr)
    
    # 디렉토리 존재 확인
    if args.directory:
        if not os.path.exists(args.directory):
            print(f"오류: 디렉토리를 찾을 수 없습니다: {args.directory}", file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(args.directory):
            print(f"오류: 디렉토리가 아닙니다: {args.directory}", file=sys.stderr)
            sys.exit(1)
    
    # 출력 파일 디렉토리 확인
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            print(f"오류: 출력 디렉토리를 찾을 수 없습니다: {output_dir}", file=sys.stderr)
            sys.exit(1)


def get_target_databases(target_arg: str) -> Optional[List[TargetDatabase]]:
    """
    타겟 인자를 TargetDatabase 리스트로 변환합니다.
    
    Args:
        target_arg: CLI 타겟 인자 값
        
    Returns:
        TargetDatabase 리스트 또는 None (all인 경우)
    """
    if target_arg == "all":
        return None  # None은 모든 타겟을 의미
    
    target_map = {
        "rds-oracle": TargetDatabase.RDS_ORACLE,
        "aurora-mysql": TargetDatabase.AURORA_MYSQL,
        "aurora-postgresql": TargetDatabase.AURORA_POSTGRESQL,
    }
    
    return [target_map[target_arg]]


def process_single_file(args: argparse.Namespace) -> int:
    """
    단일 파일을 처리합니다.
    
    Args:
        args: CLI 인자
        
    Returns:
        Exit code (0: 성공, 1: 실패)
    """
    try:
        # 파일 파싱
        print(f"파일 파싱 중: {args.file}", file=sys.stderr)
        parser = StatspackParser(args.file)
        statspack_data = parser.parse()
        print(f"파싱 완료", file=sys.stderr)
        
        # 마이그레이션 분석
        migration_analysis = None
        if args.analyze_migration:
            print(f"마이그레이션 분석 중...", file=sys.stderr)
            analyzer = MigrationAnalyzer(statspack_data)
            target_dbs = get_target_databases(args.target)
            migration_analysis = analyzer.analyze(target_dbs)
            print(f"분석 완료", file=sys.stderr)
        
        # 결과 포맷팅
        if args.format == "json":
            if migration_analysis:
                output = StatspackResultFormatter.to_json(migration_analysis)
            else:
                output = StatspackResultFormatter.to_json(statspack_data)
        else:  # markdown
            output = StatspackResultFormatter.to_markdown(statspack_data, migration_analysis)
        
        # 결과 출력 또는 저장
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"결과 저장 완료: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"오류: 파일 처리 중 예외 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


def process_directory(args: argparse.Namespace) -> int:
    """
    디렉토리 내 모든 파일을 배치 처리합니다.
    
    Args:
        args: CLI 인자
        
    Returns:
        Exit code (0: 성공, 1: 실패)
    """
    try:
        print(f"디렉토리 스캔 중: {args.directory}", file=sys.stderr)
        
        # 배치 분석 실행
        batch_analyzer = BatchAnalyzer(args.directory)
        target_db = get_target_databases(args.target)
        target_db = target_db[0] if target_db else None  # 단일 타겟 또는 None
        
        results = batch_analyzer.analyze_batch(
            analyze_migration=args.analyze_migration, 
            target=target_db
        )
        
        print(f"배치 분석 완료: {results.successful_files}개 성공, "
              f"{results.failed_files}개 실패", file=sys.stderr)
        
        # 결과 포맷팅
        if args.format == "json":
            output = StatspackResultFormatter.batch_to_json(results)
        else:  # markdown
            output = StatspackResultFormatter.batch_to_markdown(results)
        
        # 결과 출력 또는 저장
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"결과 저장 완료: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        # 실패한 파일이 있으면 exit code 1 반환
        return 1 if results.failed_files > 0 else 0
        
    except Exception as e:
        print(f"오류: 디렉토리 처리 중 예외 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


def main() -> int:
    """
    CLI 메인 함수
    
    Returns:
        Exit code (0: 성공, 1: 실패)
    """
    # 인자 파싱
    parser = create_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    log_level = "DEBUG" if hasattr(args, 'verbose') and args.verbose else "INFO"
    setup_logging(level=log_level, console=True)
    logger = get_logger("cli")
    
    logger.info("Starting Statspack analysis")
    
    # 인자 검증
    validate_args(args)
    
    # 파일 또는 디렉토리 처리
    if args.file:
        return process_single_file(args)
    else:  # args.directory
        return process_directory(args)


if __name__ == "__main__":
    sys.exit(main())
