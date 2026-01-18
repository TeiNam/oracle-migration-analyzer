#!/usr/bin/env python3
"""
Statspack 분석 도구 CLI 메인 진입점

DBCSI Statspack 결과 파일을 파싱하고 마이그레이션 난이도를 분석하는 커맨드라인 도구입니다.
"""

import sys

from ..logging_config import setup_logging, get_logger
from .argument_parser import create_parser, validate_args
from .command_handlers import process_single_file, process_directory, process_compare


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
    
    # 로거 가져오기
    cli_logger = get_logger("cli")
    cli_logger.info("Starting Statspack/AWR analysis")
    
    # 인자 검증
    validate_args(args)
    
    # 파일, 디렉토리, 또는 비교 처리
    if args.file:
        return process_single_file(args)
    elif args.directory:
        return process_directory(args)
    else:  # args.compare
        return process_compare(args)


if __name__ == "__main__":
    sys.exit(main())
