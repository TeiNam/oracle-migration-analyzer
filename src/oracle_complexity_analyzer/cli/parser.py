"""
CLI 인자 파서

명령줄 인자를 파싱하는 기능을 제공합니다.
"""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog='oracle-complexity-analyzer',
        description='Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 '
                    'PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 평가합니다.',
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
