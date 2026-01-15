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

from .parser import StatspackParser, AWRParser
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
            print(f"오류: 파일을 찾을 수 없습니다: {args.file}", file=sys.stderr)
            sys.exit(1)
        if not args.file.endswith('.out'):
            print(f"경고: Statspack/AWR 파일은 일반적으로 .out 확장자를 가집니다: {args.file}", 
                  file=sys.stderr)
    
    # 디렉토리 존재 확인
    if args.directory:
        if not os.path.exists(args.directory):
            print(f"오류: 디렉토리를 찾을 수 없습니다: {args.directory}", file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(args.directory):
            print(f"오류: 디렉토리가 아닙니다: {args.directory}", file=sys.stderr)
            sys.exit(1)
    
    # 비교 파일 존재 확인
    if args.compare:
        for file in args.compare:
            if not os.path.exists(file):
                print(f"오류: 파일을 찾을 수 없습니다: {file}", file=sys.stderr)
                sys.exit(1)
            if not file.endswith('.out'):
                print(f"경고: Statspack/AWR 파일은 일반적으로 .out 확장자를 가집니다: {file}", 
                      file=sys.stderr)
    
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


def detect_file_type(filepath: str) -> str:
    """
    파일 타입을 자동으로 감지합니다 (AWR vs Statspack).
    
    1. 먼저 파일명에서 AWR 또는 STATSPACK 키워드 확인
    2. 파일명에 없으면 파일 내용에서 AWR 특화 마커 확인
    
    AWR 특화 섹션 마커:
    - IOSTAT-FUNCTION
    - PERCENT-CPU
    - PERCENT-IO
    - WORKLOAD
    - BUFFER-CACHE
    
    Args:
        filepath: 분석할 파일 경로
        
    Returns:
        "awr" 또는 "statspack"
    """
    # 1. 파일명 확인 (대소문자 무시)
    from pathlib import Path
    filename_lower = Path(filepath).name.lower()
    
    if 'awr' in filename_lower:
        return "awr"
    elif 'statspack' in filename_lower:
        return "statspack"
    
    # 2. 파일명에 타입 정보가 없으면 파일 내용 확인
    awr_markers = [
        "~~BEGIN-IOSTAT-FUNCTION~~",
        "~~BEGIN-PERCENT-CPU~~",
        "~~BEGIN-PERCENT-IO~~",
        "~~BEGIN-WORKLOAD~~",
        "~~BEGIN-BUFFER-CACHE~~"
    ]
    
    try:
        # UTF-8로 시도
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(50000)  # 처음 50KB만 읽기 (성능 최적화)
        except UnicodeDecodeError:
            # Latin-1로 폴백
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read(50000)
        
        # AWR 마커가 하나라도 있으면 AWR 파일
        for marker in awr_markers:
            if marker in content:
                return "awr"
        
        # AWR 마커가 없으면 Statspack 파일
        return "statspack"
        
    except Exception as e:
        # 파일 읽기 실패 시 기본값으로 Statspack 반환
        print(f"경고: 파일 타입 감지 실패, Statspack으로 간주: {e}", file=sys.stderr)
        return "statspack"


def detect_and_parse(filepath: str):
    """
    파일 타입을 자동 감지하고 적절한 파서를 반환합니다.
    
    Args:
        filepath: 분석할 파일 경로
        
    Returns:
        StatspackParser 또는 AWRParser 인스턴스
    """
    file_type = detect_file_type(filepath)
    
    if file_type == "awr":
        print(f"파일 타입: AWR", file=sys.stderr)
        return AWRParser(filepath)
    else:
        print(f"파일 타입: Statspack", file=sys.stderr)
        return StatspackParser(filepath)


def process_single_file(args: argparse.Namespace) -> int:
    """
    단일 파일을 처리합니다.
    
    Args:
        args: CLI 인자
        
    Returns:
        Exit code (0: 성공, 1: 실패)
    """
    try:
        # 출력 경로 자동 생성 (--output이 지정되지 않은 경우)
        if not args.output:
            # 파일이 있는 폴더명 추출
            file_path = Path(args.file)
            folder_name = file_path.parent.name if file_path.parent.name else "default"
            
            # reports/{폴더명}/ 경로 생성
            output_dir = Path("reports") / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성 (원본 파일명에서 확장자를 .md로 변경)
            output_filename = file_path.stem + ".md"
            args.output = str(output_dir / output_filename)
            
            print(f"출력 경로 자동 설정: {args.output}", file=sys.stderr)
        
        # 파일 크기 확인
        file_size = os.path.getsize(args.file)
        is_large_file = file_size > 5 * 1024 * 1024  # 5MB 이상
        
        if is_large_file:
            print(f"대용량 파일 감지 ({file_size / (1024*1024):.1f} MB)", file=sys.stderr)
        
        # 파일 타입 자동 감지 및 파싱
        print(f"[1/4] 파일 파싱 중: {args.file}", file=sys.stderr)
        parser = detect_and_parse(args.file)
        data = parser.parse()
        print(f"[1/4] 파싱 완료", file=sys.stderr)
        
        # AWR 데이터인지 확인
        from .data_models import AWRData
        is_awr = isinstance(data, AWRData) and data.is_awr()
        
        if is_awr:
            print(f"[2/4] AWR 특화 섹션 발견", file=sys.stderr)
        else:
            print(f"[2/4] Statspack 모드로 분석", file=sys.stderr)
        
        # 마이그레이션 분석
        migration_analysis = None
        if args.analyze_migration:
            print(f"[3/4] 마이그레이션 분석 중...", file=sys.stderr)
            
            # AWR 데이터면 EnhancedMigrationAnalyzer 사용 시도
            if is_awr:
                try:
                    from .migration_analyzer import EnhancedMigrationAnalyzer
                    analyzer = EnhancedMigrationAnalyzer(data)
                except (ImportError, AttributeError):
                    # EnhancedMigrationAnalyzer가 없으면 기본 분석기 사용
                    print(f"경고: 고급 AWR 분석 기능을 사용할 수 없습니다. 기본 분석을 수행합니다.", 
                          file=sys.stderr)
                    analyzer = MigrationAnalyzer(data)
            else:
                analyzer = MigrationAnalyzer(data)
            
            target_dbs = get_target_databases(args.target)
            migration_analysis = analyzer.analyze(target_dbs)
            print(f"[3/4] 분석 완료", file=sys.stderr)
        else:
            print(f"[3/4] 마이그레이션 분석 건너뜀", file=sys.stderr)
        
        # 결과 포맷팅
        print(f"[4/4] 리포트 생성 중...", file=sys.stderr)
        if args.format == "json":
            if migration_analysis:
                output = StatspackResultFormatter.to_json(migration_analysis)
            else:
                output = StatspackResultFormatter.to_json(data)
        else:  # markdown
            # AWR 상세 리포트 옵션 확인
            if args.detailed and is_awr:
                try:
                    from .result_formatter import EnhancedResultFormatter
                    output = EnhancedResultFormatter.to_detailed_markdown(
                        data, migration_analysis, args.language
                    )
                except (ImportError, AttributeError):
                    print(f"경고: 상세 AWR 리포트 기능을 사용할 수 없습니다. 기본 리포트를 생성합니다.", 
                          file=sys.stderr)
                    output = StatspackResultFormatter.to_markdown(data, migration_analysis)
            else:
                output = StatspackResultFormatter.to_markdown(data, migration_analysis)
        
        print(f"[4/4] 리포트 생성 완료", file=sys.stderr)
        
        # 결과 출력 또는 저장
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ 결과 저장 완료: {args.output}", file=sys.stderr)
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
        # 출력 경로 자동 생성 (--output이 지정되지 않은 경우)
        if not args.output:
            # 디렉토리 이름 추출
            dir_path = Path(args.directory)
            folder_name = dir_path.name if dir_path.name else "default"
            
            # reports/{폴더명}/ 경로 생성
            output_dir = Path("reports") / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성 (배치 요약 리포트)
            output_filename = "batch_summary.md"
            args.output = str(output_dir / output_filename)
            
            print(f"출력 경로 자동 설정: {args.output}", file=sys.stderr)
        
        print(f"[1/3] 디렉토리 스캔 중: {args.directory}", file=sys.stderr)
        
        # .out 파일 개수 확인
        out_files = list(Path(args.directory).glob("*.out"))
        num_files = len(out_files)
        
        if num_files == 0:
            print(f"경고: .out 파일을 찾을 수 없습니다", file=sys.stderr)
        else:
            print(f"발견된 파일: {num_files}개", file=sys.stderr)
        
        # 배치 분석 실행
        print(f"[2/3] 배치 분석 실행 중...", file=sys.stderr)
        batch_analyzer = BatchAnalyzer(args.directory)
        target_db = get_target_databases(args.target)
        target_db = target_db[0] if target_db else None  # 단일 타겟 또는 None
        
        results = batch_analyzer.analyze_batch(
            analyze_migration=args.analyze_migration, 
            target=target_db
        )
        
        print(f"[2/3] 배치 분석 완료: {results.successful_files}개 성공, "
              f"{results.failed_files}개 실패", file=sys.stderr)
        
        # 결과 포맷팅
        print(f"[3/3] 리포트 생성 중...", file=sys.stderr)
        if args.format == "json":
            output = StatspackResultFormatter.batch_to_json(results)
        else:  # markdown
            output = StatspackResultFormatter.batch_to_markdown(results)
        
        print(f"[3/3] 리포트 생성 완료", file=sys.stderr)
        
        # 결과 출력 또는 저장
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ 결과 저장 완료: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        # 실패한 파일이 있으면 exit code 1 반환
        return 1 if results.failed_files > 0 else 0
        
    except Exception as e:
        print(f"오류: 디렉토리 처리 중 예외 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


def process_compare(args: argparse.Namespace) -> int:
    """
    두 AWR 파일을 비교 분석합니다.
    
    Args:
        args: CLI 인자
        
    Returns:
        Exit code (0: 성공, 1: 실패)
    """
    try:
        # 출력 경로 자동 생성 (--output이 지정되지 않은 경우)
        if not args.output:
            file1, file2 = args.compare
            # 첫 번째 파일이 있는 폴더명 추출
            file_path = Path(file1)
            folder_name = file_path.parent.name if file_path.parent.name else "default"
            
            # reports/{폴더명}/ 경로 생성
            output_dir = Path("reports") / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성 (비교 리포트)
            file1_stem = Path(file1).stem
            file2_stem = Path(file2).stem
            output_filename = f"comparison_{file1_stem}_vs_{file2_stem}.md"
            args.output = str(output_dir / output_filename)
            
            print(f"출력 경로 자동 설정: {args.output}", file=sys.stderr)
        
        file1, file2 = args.compare
        
        print(f"[1/4] 첫 번째 파일 파싱 중: {file1}", file=sys.stderr)
        # 파일 타입 자동 감지 및 파싱
        parser1 = detect_and_parse(file1)
        data1 = parser1.parse()
        print(f"[1/4] 파싱 완료", file=sys.stderr)
        
        print(f"[2/4] 두 번째 파일 파싱 중: {file2}", file=sys.stderr)
        parser2 = detect_and_parse(file2)
        data2 = parser2.parse()
        print(f"[2/4] 파싱 완료", file=sys.stderr)
        
        # AWR 데이터인지 확인
        from .data_models import AWRData
        if not isinstance(data1, AWRData) or not isinstance(data2, AWRData):
            print(f"경고: 비교 기능은 AWR 파일에 최적화되어 있습니다.", file=sys.stderr)
        
        # 비교 리포트 생성
        print(f"[3/4] 비교 분석 중...", file=sys.stderr)
        
        # EnhancedResultFormatter가 있는지 확인하고 사용
        try:
            from .result_formatter import EnhancedResultFormatter
            output = EnhancedResultFormatter.compare_awr_reports(
                data1, data2, args.language
            )
        except (ImportError, AttributeError):
            # EnhancedResultFormatter가 없으면 기본 비교 수행
            print(f"경고: 상세 비교 기능을 사용할 수 없습니다. 기본 비교를 수행합니다.", file=sys.stderr)
            output = f"# AWR 파일 비교\n\n"
            output += f"## 파일 1: {file1}\n"
            output += StatspackResultFormatter.to_markdown(data1, None)
            output += f"\n\n## 파일 2: {file2}\n"
            output += StatspackResultFormatter.to_markdown(data2, None)
        
        print(f"[3/4] 비교 완료", file=sys.stderr)
        
        # 결과 출력 또는 저장
        print(f"[4/4] 리포트 생성 중...", file=sys.stderr)
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ 결과 저장 완료: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"오류: 파일 비교 중 예외 발생: {e}", file=sys.stderr)
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
    
    logger.info("Starting Statspack/AWR analysis")
    
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
