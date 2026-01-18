"""
명령 처리 모듈

CLI 명령 처리 로직을 제공합니다.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
import argparse

from ..parsers import StatspackParser, AWRParser
from ..migration_analyzer import MigrationAnalyzer, TargetDatabase
from ..formatters import StatspackResultFormatter, EnhancedResultFormatter
from ..batch_analyzer import BatchAnalyzer
from ...utils.cli_helpers import detect_file_type, generate_output_path, print_progress
from .argument_parser import get_target_databases

# 로거 초기화
logger = logging.getLogger("statspack.cli")


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
        logger.info("파일 타입: AWR")
        return AWRParser(filepath)
    else:
        logger.info("파일 타입: Statspack")
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
            file_path = Path(args.file)
            folder_name = file_path.parent.name if file_path.parent.name else "default"
            output_dir = Path("reports") / folder_name
            
            # generate_output_path 유틸리티 사용
            args.output = str(generate_output_path(file_path, output_dir))
            
            logger.info(f"출력 경로 자동 설정: {args.output}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(args.file)
        is_large_file = file_size > 5 * 1024 * 1024  # 5MB 이상
        
        if is_large_file:
            logger.info(f"대용량 파일 감지 ({file_size / (1024*1024):.1f} MB)")
        
        # 파일 타입 자동 감지 및 파싱 (print_progress 사용)
        print_progress(1, 4, f"파일 파싱 중: {args.file}")
        parser = detect_and_parse(args.file)
        data = parser.parse()
        print_progress(1, 4, "파싱 완료")
        
        # AWR 데이터인지 확인
        from ..models import AWRData
        is_awr = isinstance(data, AWRData) and data.is_awr()
        
        if is_awr:
            print_progress(2, 4, "AWR 특화 섹션 발견")
        else:
            print_progress(2, 4, "Statspack 모드로 분석")
        
        # 마이그레이션 분석
        migration_analysis = None
        if args.analyze_migration:
            print_progress(3, 4, "마이그레이션 분석 중...")
            analyzer = MigrationAnalyzer(data)
            target_dbs = get_target_databases(args.target)
            migration_analysis = analyzer.analyze(target_dbs)
            print_progress(3, 4, "분석 완료")
        else:
            print_progress(3, 4, "마이그레이션 분석 건너뜀")
        
        # 결과 포맷팅
        print_progress(4, 4, "리포트 생성 중...")
        if args.format == "json":
            if migration_analysis:
                output = StatspackResultFormatter.to_json(migration_analysis)
            else:
                output = StatspackResultFormatter.to_json(data)
        else:  # markdown
            # AWR 데이터는 항상 상세 리포트 생성, Statspack은 기본 리포트
            if is_awr:
                output = EnhancedResultFormatter.to_detailed_markdown(
                    data, migration_analysis, args.language
                )
            else:
                output = StatspackResultFormatter.to_markdown(data, migration_analysis)
        
        print_progress(4, 4, "리포트 생성 완료")
        
        # 결과 출력 또는 저장
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"✓ 결과 저장 완료: {args.output}")
        else:
            print(output)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        return 1
    except Exception as e:
        logger.error(f"파일 처리 중 예외 발생: {e}", exc_info=True)
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
            dir_path = Path(args.directory)
            folder_name = dir_path.name if dir_path.name else "default"
            output_dir = Path("reports") / folder_name
            
            # 배치 요약 리포트용 경로 생성
            output_filename = "batch_summary.md"
            output_dir.mkdir(parents=True, exist_ok=True)
            args.output = str(output_dir / output_filename)
            
            logger.info(f"출력 경로 자동 설정: {args.output}")
        
        print_progress(1, 3, f"디렉토리 스캔 중: {args.directory}")
        
        # .out 파일 개수 확인
        out_files = list(Path(args.directory).glob("*.out"))
        num_files = len(out_files)
        
        if num_files == 0:
            logger.warning(".out 파일을 찾을 수 없습니다")
        else:
            logger.info(f"발견된 파일: {num_files}개")
        
        # 배치 분석 실행
        print_progress(2, 3, "배치 분석 실행 중...")
        batch_analyzer = BatchAnalyzer(args.directory)
        target_db = get_target_databases(args.target)
        target_db = target_db[0] if target_db else None  # 단일 타겟 또는 None
        
        results = batch_analyzer.analyze_batch(
            analyze_migration=args.analyze_migration, 
            target=target_db
        )
        
        print_progress(2, 3, f"배치 분석 완료: {results.successful_files}개 성공, "
                      f"{results.failed_files}개 실패")
        
        # 결과 포맷팅
        print_progress(3, 3, "리포트 생성 중...")
        if args.format == "json":
            output = StatspackResultFormatter.batch_to_json(results)
        else:  # markdown
            output = StatspackResultFormatter.batch_to_markdown(results)
        
        print_progress(3, 3, "리포트 생성 완료")
        
        # 결과 출력 또는 저장
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"✓ 결과 저장 완료: {args.output}")
        else:
            print(output)
        
        # 실패한 파일이 있으면 exit code 1 반환
        return 1 if results.failed_files > 0 else 0
        
    except Exception as e:
        logger.error(f"디렉토리 처리 중 예외 발생: {e}", exc_info=True)
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
            file_path = Path(file1)
            folder_name = file_path.parent.name if file_path.parent.name else "default"
            output_dir = Path("reports") / folder_name
            
            # 비교 리포트용 파일명 생성
            file1_stem = Path(file1).stem
            file2_stem = Path(file2).stem
            output_filename = f"comparison_{file1_stem}_vs_{file2_stem}.md"
            output_dir.mkdir(parents=True, exist_ok=True)
            args.output = str(output_dir / output_filename)
            
            logger.info(f"출력 경로 자동 설정: {args.output}")
        
        file1, file2 = args.compare
        
        print_progress(1, 4, f"첫 번째 파일 파싱 중: {file1}")
        # 파일 타입 자동 감지 및 파싱
        parser1 = detect_and_parse(file1)
        data1 = parser1.parse()
        print_progress(1, 4, "파싱 완료")
        
        print_progress(2, 4, f"두 번째 파일 파싱 중: {file2}")
        parser2 = detect_and_parse(file2)
        data2 = parser2.parse()
        print_progress(2, 4, "파싱 완료")
        
        # AWR 데이터인지 확인
        from ..models import AWRData
        if not isinstance(data1, AWRData) or not isinstance(data2, AWRData):
            logger.warning("비교 기능은 AWR 파일에 최적화되어 있습니다.")
        
        # 비교 리포트 생성
        print_progress(3, 4, "비교 분석 중...")
        
        # 비교 리포트 생성
        output = EnhancedResultFormatter.compare_awr_reports(
            data1, data2, args.language
        )
        
        print_progress(3, 4, "비교 완료")
        
        # 결과 출력 또는 저장
        print_progress(4, 4, "리포트 생성 중...")
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"✓ 결과 저장 완료: {args.output}")
        else:
            print(output)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        return 1
    except Exception as e:
        logger.error(f"파일 비교 중 예외 발생: {e}", exc_info=True)
        return 1
