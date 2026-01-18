#!/usr/bin/env python3
"""
마이그레이션 추천 시스템 CLI 인터페이스

DBCSI 분석 결과와 SQL/PL-SQL 분석 결과를 통합하여
최적의 마이그레이션 전략을 추천하는 커맨드라인 도구입니다.
"""

import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Union

from ..dbcsi.parser import StatspackParser, AWRParser
from ..dbcsi.models import StatspackData, AWRData
from ..oracle_complexity_analyzer import OracleComplexityAnalyzer
from ..utils.cli_helpers import detect_file_type, print_progress
from ..utils.file_utils import find_files_by_extension, read_file_with_encoding
from ..utils.logging_utils import setup_cli_logging, log_progress, get_logger
from .integrator import AnalysisResultIntegrator
from .decision_engine import MigrationDecisionEngine
from .report_generator import RecommendationReportGenerator
from .formatters import MarkdownReportFormatter, JSONReportFormatter

# 로거 초기화 (모듈 레벨에서 기본 로거 생성)
logger = logging.getLogger("migration_recommendation.cli")


def create_parser() -> argparse.ArgumentParser:
    """
    CLI 인자 파서를 생성합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog="migration-recommend",
        description="DBCSI와 SQL/PL-SQL 분석 결과를 통합하여 최적의 마이그레이션 전략을 추천합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # reports 폴더 내 모든 리포트 분석하여 추천 생성
  %(prog)s --reports-dir reports/sample_code
  
  # JSON 형식으로 출력
  %(prog)s --reports-dir reports/sample_code --format json
  
  # 영어 리포트 생성
  %(prog)s --reports-dir reports/sample_code --language en
  
  # 결과를 특정 파일로 저장
  %(prog)s --reports-dir reports/sample_code --output custom_report.md
  
  # 레거시 방식: DBCSI 파일과 SQL 디렉토리 직접 지정
  %(prog)s --dbcsi sample.out --sql-dir ./sql_files/
        """
    )
    
    # 입력 옵션 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        "--reports-dir",
        type=str,
        metavar="PATH",
        help="분석 리포트가 있는 디렉토리 경로 (DBCSI와 SQL 복잡도 리포트 자동 검색)"
    )
    
    input_group.add_argument(
        "--legacy",
        action="store_true",
        help="레거시 모드 (--dbcsi와 --sql-dir 사용)"
    )
    
    # 레거시 옵션
    parser.add_argument(
        "--dbcsi",
        type=str,
        metavar="PATH",
        help="[레거시] DBCSI Statspack/AWR 파일 경로 (.out 파일)"
    )
    
    parser.add_argument(
        "--sql-dir",
        type=str,
        metavar="PATH",
        help="[레거시] SQL/PL-SQL 파일이 있는 디렉토리 경로"
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
        help="결과를 저장할 파일 경로 (지정하지 않으면 자동 생성: {reports-dir}/migration_recommendation.md)"
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
    # reports-dir 모드
    if args.reports_dir:
        if not os.path.exists(args.reports_dir):
            logger.error(f"리포트 디렉토리를 찾을 수 없습니다: {args.reports_dir}")
            sys.exit(1)
        if not os.path.isdir(args.reports_dir):
            logger.error(f"리포트 경로가 디렉토리가 아닙니다: {args.reports_dir}")
            sys.exit(1)
        return
    
    # 레거시 모드
    if args.legacy or args.dbcsi or args.sql_dir:
        if not args.sql_dir:
            logger.error("레거시 모드에서는 --sql-dir이 필수입니다")
            sys.exit(1)
        
        # DBCSI 파일 존재 확인 (선택사항)
        if args.dbcsi:
            if not os.path.exists(args.dbcsi):
                logger.error(f"DBCSI 파일을 찾을 수 없습니다: {args.dbcsi}")
                sys.exit(1)
            if not args.dbcsi.endswith('.out'):
                logger.warning(f"DBCSI 파일은 일반적으로 .out 확장자를 가집니다: {args.dbcsi}")
        
        # SQL 디렉토리 존재 확인
        if not os.path.exists(args.sql_dir):
            logger.error(f"SQL 디렉토리를 찾을 수 없습니다: {args.sql_dir}")
            sys.exit(1)
        if not os.path.isdir(args.sql_dir):
            logger.error(f"SQL 경로가 디렉토리가 아닙니다: {args.sql_dir}")
            sys.exit(1)
        
        # SQL 파일 존재 확인
        try:
            sql_files = find_files_by_extension(Path(args.sql_dir), [".sql", ".pls"])
            if not sql_files:
                logger.warning("SQL/PL-SQL 파일을 찾을 수 없습니다 (.sql, .pls)")
        except ValueError:
            # 디렉토리가 없는 경우는 이미 위에서 체크했으므로 무시
            pass
        
        # 출력 파일 디렉토리 확인
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                logger.error(f"출력 디렉토리를 찾을 수 없습니다: {output_dir}")
                sys.exit(1)


def find_reports_in_directory(reports_dir: str) -> tuple:
    """
    리포트 디렉토리에서 DBCSI 리포트와 SQL 복잡도 리포트를 찾습니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        (dbcsi_reports, sql_complexity_reports) 튜플
        dbcsi_reports: DBCSI 리포트 파일 경로 리스트
        sql_complexity_reports: SQL 복잡도 리포트 파일 경로 리스트
    """
    reports_path = Path(reports_dir)
    
    dbcsi_reports = []
    sql_complexity_reports = []
    
    # 모든 .md 파일 찾기
    md_files = list(reports_path.glob("**/*.md"))
    
    for md_file in md_files:
        filename = md_file.name.lower()
        
        # DBCSI 리포트 감지 (dbcsi, awr, statspack 키워드)
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            # 비교 리포트는 제외
            if 'comparison' not in filename and 'vs' not in filename:
                dbcsi_reports.append(str(md_file))
        
        # SQL 복잡도 리포트 감지 (sql_complexity 키워드 또는 PGSQL/MySQL 폴더)
        elif 'sql_complexity' in filename or any(folder in str(md_file) for folder in ['PGSQL', 'MySQL']):
            sql_complexity_reports.append(str(md_file))
        
        # 개별 SQL 파일 리포트도 포함 (복잡도 분석 결과)
        elif md_file.parent.name in ['PGSQL', 'MySQL']:
            # batch_summary나 sql_complexity가 아닌 파일들
            if 'batch' not in filename and 'sql_complexity' not in filename:
                sql_complexity_reports.append(str(md_file))
    
    return dbcsi_reports, sql_complexity_reports


def parse_dbcsi_file(filepath: str) -> Optional[Union[StatspackData, AWRData]]:
    """
    DBCSI 파일을 파싱합니다.
    
    Args:
        filepath: DBCSI 파일 경로
        
    Returns:
        StatspackData 또는 AWRData, 실패 시 None
    """
    try:
        file_type = detect_file_type(filepath)
        
        if file_type == "awr":
            logger.info("DBCSI 파일 타입: AWR")
            parser = AWRParser(filepath)
        else:
            logger.info("DBCSI 파일 타입: Statspack")
            parser = StatspackParser(filepath)
        
        return parser.parse()
        
    except Exception as e:
        logger.warning(f"DBCSI 파일 파싱 실패: {e}", exc_info=True)
        return None


def analyze_sql_files(sql_dir: str) -> tuple:
    """
    SQL/PL-SQL 파일들을 분석합니다.
    
    Args:
        sql_dir: SQL 파일이 있는 디렉토리 경로
        
    Returns:
        (sql_results, plsql_results) 튜플
    """
    analyzer = OracleComplexityAnalyzer()
    
    # SQL 파일 찾기 (유틸리티 함수 사용)
    sql_files = find_files_by_extension(Path(sql_dir), [".sql", ".pls"])
    
    if not sql_files:
        logger.warning("SQL/PL-SQL 파일을 찾을 수 없습니다")
        return [], []
    
    logger.info(f"발견된 SQL/PL-SQL 파일: {len(sql_files)}개")
    
    sql_results = []
    plsql_results = []
    
    for sql_file in sql_files:
        try:
            # 유틸리티 함수로 파일 읽기 (여러 인코딩 시도)
            content = read_file_with_encoding(sql_file)
            
            # SQL 분석 (단일 결과 반환)
            try:
                sql_result = analyzer.analyze_sql(content)
                if sql_result:
                    sql_results.append(sql_result)
            except Exception as e:
                # SQL 분석 실패는 무시 (PL/SQL일 수 있음)
                pass
            
            # PL/SQL 분석 (단일 결과 반환)
            try:
                plsql_result = analyzer.analyze_plsql(content)
                if plsql_result:
                    plsql_results.append(plsql_result)
            except Exception as e:
                # PL/SQL 분석 실패는 무시 (SQL일 수 있음)
                pass
                
        except Exception as e:
            logger.warning(f"파일 읽기 실패 ({sql_file}): {e}", exc_info=True)
            continue
    
    logger.info(f"분석 완료: SQL {len(sql_results)}개, PL/SQL {len(plsql_results)}개")
    
    return sql_results, plsql_results


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
    setup_cli_logging(level=log_level)
    
    # 로거 가져오기
    cli_logger = get_logger("migration_recommendation.cli")
    cli_logger.info("마이그레이션 추천 시스템 시작")
    
    # 인자 검증
    validate_args(args)
    
    try:
        # reports-dir 모드
        if args.reports_dir:
            # 출력 경로 자동 설정
            if not args.output:
                output_filename = "migration_recommendation.md" if args.format == "markdown" else "migration_recommendation.json"
                args.output = str(Path(args.reports_dir) / output_filename)
                logger.info(f"출력 경로 자동 설정: {args.output}")
            
            # 1. 리포트 파일 검색
            log_progress(logger, 1, 5, f"리포트 파일 검색 중: {args.reports_dir}")
            dbcsi_reports, sql_complexity_reports = find_reports_in_directory(args.reports_dir)
            
            logger.info(f"발견된 DBCSI 리포트: {len(dbcsi_reports)}개")
            logger.info(f"발견된 SQL 복잡도 리포트: {len(sql_complexity_reports)}개")
            
            if not dbcsi_reports and not sql_complexity_reports:
                logger.error("분석할 리포트 파일을 찾을 수 없습니다")
                return 1
            
            # 2. 원본 소스 파일 경로 추정
            # reports/sample_code -> sample_code
            reports_path = Path(args.reports_dir)
            if reports_path.parent.name == "reports":
                source_dir = reports_path.name
                logger.info(f"원본 소스 디렉토리 추정: {source_dir}")
                
                # 원본 소스 디렉토리가 존재하는지 확인
                if not os.path.exists(source_dir):
                    logger.error(f"원본 소스 디렉토리를 찾을 수 없습니다: {source_dir}")
                    logger.error("리포트 파일만으로는 정확한 분석이 어렵습니다.")
                    return 1
            else:
                logger.error("표준 reports 폴더 구조가 아닙니다")
                return 1
            
            # 3. DBCSI 원본 파일 찾기
            log_progress(logger, 2, 5, "원본 파일 분석 중...")
            dbcsi_result = None
            if dbcsi_reports:
                # DBCSI 원본 파일 찾기 (.out 파일)
                out_files = find_files_by_extension(Path(source_dir), [".out"])
                if out_files:
                    dbcsi_file = str(out_files[0])
                    logger.info(f"DBCSI 원본 파일 사용: {dbcsi_file}")
                    dbcsi_result = parse_dbcsi_file(dbcsi_file)
                else:
                    logger.warning("DBCSI 원본 파일(.out)을 찾을 수 없습니다")
            
            # 4. SQL/PL-SQL 원본 파일 분석
            sql_results, plsql_results = analyze_sql_files(source_dir)
            
            if not sql_results and not plsql_results:
                logger.error("분석할 SQL/PL-SQL 코드가 없습니다")
                return 1
            
            log_progress(logger, 2, 5, "원본 파일 분석 완료")
            
            # 3. 분석 결과 통합
            log_progress(logger, 3, 5, "분석 결과 통합 중...")
            integrator = AnalysisResultIntegrator()
            
            # 리포트 기반 통합 (간소화된 버전)
            # 실제로는 리포트에서 추출한 데이터를 사용
            integrated_result = integrator.integrate(dbcsi_result, sql_results, plsql_results)
            log_progress(logger, 3, 5, "통합 완료")
            
            # 4. 마이그레이션 전략 결정 및 리포트 생성
            log_progress(logger, 4, 5, "마이그레이션 전략 결정 중...")
            decision_engine = MigrationDecisionEngine()
            report_generator = RecommendationReportGenerator(decision_engine)
            recommendation = report_generator.generate_recommendation(integrated_result)
            logger.info(f"추천 전략: {recommendation.recommended_strategy.value}")
            
            # 5. 리포트 포맷팅
            log_progress(logger, 5, 5, "리포트 생성 중...")
            if args.format == "json":
                formatter = JSONReportFormatter()
                output = formatter.format(recommendation)
            else:  # markdown
                formatter = MarkdownReportFormatter()
                output = formatter.format(recommendation, args.language)
            
            log_progress(logger, 5, 5, "리포트 생성 완료")
        
        # 레거시 모드
        else:
            # 1. DBCSI 파일 파싱 (선택사항)
            dbcsi_result = None
            if args.dbcsi:
                log_progress(logger, 1, 5, f"DBCSI 파일 파싱 중: {args.dbcsi}")
                dbcsi_result = parse_dbcsi_file(args.dbcsi)
                if dbcsi_result:
                    log_progress(logger, 1, 5, "DBCSI 파싱 완료")
                else:
                    logger.warning("DBCSI 파싱 실패 (성능 메트릭 제외)")
            else:
                logger.info("DBCSI 파일 없음 (성능 메트릭 제외)")
            
            # 2. SQL/PL-SQL 파일 분석
            log_progress(logger, 2, 5, f"SQL/PL-SQL 파일 분석 중: {args.sql_dir}")
            sql_results, plsql_results = analyze_sql_files(args.sql_dir)
            
            if not sql_results and not plsql_results:
                logger.error("분석할 SQL/PL-SQL 코드가 없습니다")
                return 1
            
            log_progress(logger, 2, 5, "SQL/PL-SQL 분석 완료")
            
            # 3. 분석 결과 통합
            log_progress(logger, 3, 5, "분석 결과 통합 중...")
            integrator = AnalysisResultIntegrator()
            integrated_result = integrator.integrate(dbcsi_result, sql_results, plsql_results)
            log_progress(logger, 3, 5, "통합 완료")
            
            # 4. 마이그레이션 전략 결정 및 리포트 생성
            log_progress(logger, 4, 5, "마이그레이션 전략 결정 중...")
            decision_engine = MigrationDecisionEngine()
            report_generator = RecommendationReportGenerator(decision_engine)
            recommendation = report_generator.generate_recommendation(integrated_result)
            logger.info(f"추천 전략: {recommendation.recommended_strategy.value}")
            
            # 5. 리포트 포맷팅
            log_progress(logger, 5, 5, "리포트 생성 중...")
            if args.format == "json":
                formatter = JSONReportFormatter()
                output = formatter.format(recommendation)
            else:  # markdown
                formatter = MarkdownReportFormatter()
                output = formatter.format(recommendation, args.language)
            
            log_progress(logger, 5, 5, "리포트 생성 완료")
        
        # 결과 출력 또는 저장
        if args.output:
            # 출력 디렉토리가 없으면 생성
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"결과 저장 완료: {args.output}")
        else:
            print(output)
        
        return 0
        
    except Exception as e:
        logger.error(f"처리 중 예외 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
