"""
Oracle Complexity Analyzer CLI Entry Point

이 모듈은 패키지를 python -m src.oracle_complexity_analyzer로 실행할 수 있게 합니다.

Note:
    이 모듈은 하위 호환성을 위한 래퍼입니다.
    실제 구현은 src/oracle_complexity_analyzer/cli/ 패키지에 있습니다.
"""

import sys
import logging

from .cli import (
    create_parser,
    analyze_single_file,
    analyze_directory,
)


def main() -> int:
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
