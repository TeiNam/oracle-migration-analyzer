"""
CLI 인자 파서 모듈

CLI 인자 파싱 및 검증 기능을 제공합니다.
"""

import argparse
import sys
import os
import logging
from typing import Optional, List

from ..migration_analyzer import TargetDatabase

# 로거 초기화
logger = logging.getLogger("statspack.cli")


def create_parser() -> argparse.ArgumentParser:
    """
    CLI 인자 파서를 생성합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog="dbcsi-analyzer",
        description="DBCSI Statspack/AWR 결과 파일을 분석하여 마이그레이션 난이도를 평가합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 파일 분석 (Markdown 출력)
  %(prog)s --file sample.out
  
  # 단일 파일 분석 (JSON 출력)
  %(prog)s --file sample.out --format json
  
  # AWR 상세 리포트 생성
  %(prog)s --file awr_sample.out --detailed
  
  # 두 AWR 파일 비교
  %(prog)s --compare awr1.out awr2.out
  
  # 특정 백분위수 기준으로 분석
  %(prog)s --file awr_sample.out --percentile 95
  
  # 한국어 리포트 생성
  %(prog)s --file sample.out --language ko
  
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
        help="분석할 단일 Statspack/AWR 파일 경로 (.out 파일)"
    )
    input_group.add_argument(
        "--directory",
        type=str,
        metavar="PATH",
        help="Statspack/AWR 파일이 있는 디렉토리 경로 (모든 .out 파일 분석)"
    )
    input_group.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="두 AWR 파일 비교 분석"
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
    
    # AWR 상세 리포트 플래그
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="AWR 특화 섹션을 포함한 상세 리포트 생성 (AWR 파일만 해당)"
    )
    
    # 백분위수 선택 옵션
    parser.add_argument(
        "--percentile",
        type=str,
        choices=["99", "95", "90", "75", "median", "average"],
        default="99",
        help="분석에 사용할 백분위수 (기본값: 99, AWR 파일만 해당)"
    )
    
    # 언어 선택 옵션
    parser.add_argument(
        "--language",
        type=str,
        choices=["ko", "en"],
        default="ko",
        help="리포트 언어 (기본값: ko)"
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
            logger.error(f"파일을 찾을 수 없습니다: {args.file}")
            sys.exit(1)
        if not args.file.endswith('.out'):
            logger.warning(f"Statspack/AWR 파일은 일반적으로 .out 확장자를 가집니다: {args.file}")
    
    # 디렉토리 존재 확인
    if args.directory:
        if not os.path.exists(args.directory):
            logger.error(f"디렉토리를 찾을 수 없습니다: {args.directory}")
            sys.exit(1)
        if not os.path.isdir(args.directory):
            logger.error(f"디렉토리가 아닙니다: {args.directory}")
            sys.exit(1)
    
    # 비교 파일 존재 확인
    if args.compare:
        for file in args.compare:
            if not os.path.exists(file):
                logger.error(f"파일을 찾을 수 없습니다: {file}")
                sys.exit(1)
            if not file.endswith('.out'):
                logger.warning(f"Statspack/AWR 파일은 일반적으로 .out 확장자를 가집니다: {file}")
    
    # 출력 파일 디렉토리 확인
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            logger.error(f"출력 디렉토리를 찾을 수 없습니다: {output_dir}")
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
