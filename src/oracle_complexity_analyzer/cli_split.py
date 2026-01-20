"""
CLI for Batch PL/SQL Splitter

배치 PL/SQL 파일 분리 CLI 모듈입니다.
"""

import sys
import argparse
import logging
from pathlib import Path
from src.parsers.batch_plsql_splitter import BatchPLSQLSplitter


def create_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성
    
    Returns:
        argparse.ArgumentParser: 설정된 파서
    """
    parser = argparse.ArgumentParser(
        description='배치 PL/SQL 파일을 계정별, 타입별로 개별 SQL 파일로 분리합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
예제:
  # 기본 사용 (출력: plsql_f_ora12c_20260118_split/)
  plsql-splitter -f sample_code/plsql_f_ora12c_20260118.out
  
  # 출력 디렉토리 지정
  plsql-splitter -f input.out -o output_folder
  
  # 상세 로그 출력
  plsql-splitter -f input.out -v
        '''
    )
    
    parser.add_argument(
        '-f', '--file',
        required=True,
        help='입력 배치 PL/SQL 파일 경로 (.out 파일)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='출력 디렉토리 경로 (기본값: {입력파일명}_split)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )
    
    return parser


def main() -> int:
    """CLI 메인 함수
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # 입력 파일 확인
        input_file = Path(args.file)
        if not input_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {args.file}")
            return 1
        
        print(f"\n🔄 배치 PL/SQL 파일 분리 시작...")
        print(f"📄 입력 파일: {input_file}")
        
        # Splitter 생성 및 실행
        splitter = BatchPLSQLSplitter(str(input_file), args.output)
        
        # 파싱
        print(f"\n📖 파일 파싱 중...")
        objects = splitter.parse()
        
        if not objects:
            logger.warning("분석 가능한 PL/SQL 객체를 찾을 수 없습니다.")
            return 1
        
        print(f"✅ {len(objects)}개 객체 발견")
        
        # 분리
        print(f"\n✂️  파일 분리 중...")
        stats = splitter.split()
        
        # 통계 출력
        splitter.print_statistics()
        
        print(f"\n✅ 완료! 출력 디렉토리: {splitter.output_dir}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일 오류: {e}")
        return 1
    except IOError as e:
        logger.error(f"입출력 오류: {e}")
        return 1
    except ValueError as e:
        logger.error(f"잘못된 값: {e}")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 에러: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
