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
from pathlib import Path
from typing import Optional, List, Union

from ..dbcsi.parser import StatspackParser, AWRParser
from ..dbcsi.data_models import StatspackData, AWRData
from ..oracle_complexity_analyzer import OracleComplexityAnalyzer
from .integrator import AnalysisResultIntegrator
from .decision_engine import MigrationDecisionEngine
from .report_generator import RecommendationReportGenerator
from .formatters import MarkdownReportFormatter, JSONReportFormatter


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
  # DBCSI 파일과 SQL 파일을 분석하여 추천 리포트 생성
  %(prog)s --dbcsi sample.out --sql-dir ./sql_files/
  
  # JSON 형식으로 출력
  %(prog)s --dbcsi sample.out --sql-dir ./sql_files/ --format json
  
  # 영어 리포트 생성
  %(prog)s --dbcsi sample.out --sql-dir ./sql_files/ --language en
  
  # 결과를 파일로 저장
  %(prog)s --dbcsi sample.out --sql-dir ./sql_files/ --output recommendation.md
  
  # DBCSI 없이 SQL 분석만으로 추천 (성능 메트릭 제외)
  %(prog)s --sql-dir ./sql_files/
        """
    )
    
    # 입력 옵션
    parser.add_argument(
        "--dbcsi",
        type=str,
        metavar="PATH",
        help="DBCSI Statspack/AWR 파일 경로 (.out 파일, 선택사항)"
    )
    
    parser.add_argument(
        "--sql-dir",
        type=str,
        metavar="PATH",
        required=True,
        help="SQL/PL-SQL 파일이 있는 디렉토리 경로 (필수)"
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
    # DBCSI 파일 존재 확인 (선택사항)
    if args.dbcsi:
        if not os.path.exists(args.dbcsi):
            print(f"오류: DBCSI 파일을 찾을 수 없습니다: {args.dbcsi}", file=sys.stderr)
            sys.exit(1)
        if not args.dbcsi.endswith('.out'):
            print(f"경고: DBCSI 파일은 일반적으로 .out 확장자를 가집니다: {args.dbcsi}", 
                  file=sys.stderr)
    
    # SQL 디렉토리 존재 확인
    if not os.path.exists(args.sql_dir):
        print(f"오류: SQL 디렉토리를 찾을 수 없습니다: {args.sql_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.sql_dir):
        print(f"오류: SQL 경로가 디렉토리가 아닙니다: {args.sql_dir}", file=sys.stderr)
        sys.exit(1)
    
    # SQL 파일 존재 확인
    sql_files = list(Path(args.sql_dir).glob("*.sql")) + list(Path(args.sql_dir).glob("*.pls"))
    if not sql_files:
        print(f"경고: SQL/PL-SQL 파일을 찾을 수 없습니다 (.sql, .pls)", file=sys.stderr)
    
    # 출력 파일 디렉토리 확인
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            print(f"오류: 출력 디렉토리를 찾을 수 없습니다: {output_dir}", file=sys.stderr)
            sys.exit(1)


def detect_file_type(filepath: str) -> str:
    """
    DBCSI 파일 타입을 자동으로 감지합니다 (AWR vs Statspack).
    
    Args:
        filepath: 분석할 파일 경로
        
    Returns:
        "awr" 또는 "statspack"
    """
    # 파일명 확인
    filename_lower = Path(filepath).name.lower()
    
    if 'awr' in filename_lower:
        return "awr"
    elif 'statspack' in filename_lower:
        return "statspack"
    
    # 파일 내용 확인
    awr_markers = [
        "~~BEGIN-IOSTAT-FUNCTION~~",
        "~~BEGIN-PERCENT-CPU~~",
        "~~BEGIN-PERCENT-IO~~",
        "~~BEGIN-WORKLOAD~~",
        "~~BEGIN-BUFFER-CACHE~~"
    ]
    
    try:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(50000)
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read(50000)
        
        for marker in awr_markers:
            if marker in content:
                return "awr"
        
        return "statspack"
        
    except Exception:
        return "statspack"


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
            print(f"DBCSI 파일 타입: AWR", file=sys.stderr)
            parser = AWRParser(filepath)
        else:
            print(f"DBCSI 파일 타입: Statspack", file=sys.stderr)
            parser = StatspackParser(filepath)
        
        return parser.parse()
        
    except Exception as e:
        print(f"경고: DBCSI 파일 파싱 실패: {e}", file=sys.stderr)
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
    
    # SQL 파일 찾기
    sql_files = list(Path(sql_dir).glob("*.sql")) + list(Path(sql_dir).glob("*.pls"))
    
    if not sql_files:
        print(f"경고: SQL/PL-SQL 파일을 찾을 수 없습니다", file=sys.stderr)
        return [], []
    
    print(f"발견된 SQL/PL-SQL 파일: {len(sql_files)}개", file=sys.stderr)
    
    sql_results = []
    plsql_results = []
    
    for sql_file in sql_files:
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
            print(f"경고: 파일 읽기 실패 ({sql_file}): {e}", file=sys.stderr)
            continue
    
    print(f"분석 완료: SQL {len(sql_results)}개, PL/SQL {len(plsql_results)}개", file=sys.stderr)
    
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
    
    # 인자 검증
    validate_args(args)
    
    try:
        # 1. DBCSI 파일 파싱 (선택사항)
        dbcsi_result = None
        if args.dbcsi:
            print(f"[1/5] DBCSI 파일 파싱 중: {args.dbcsi}", file=sys.stderr)
            dbcsi_result = parse_dbcsi_file(args.dbcsi)
            if dbcsi_result:
                print(f"[1/5] DBCSI 파싱 완료", file=sys.stderr)
            else:
                print(f"[1/5] DBCSI 파싱 실패 (성능 메트릭 제외)", file=sys.stderr)
        else:
            print(f"[1/5] DBCSI 파일 없음 (성능 메트릭 제외)", file=sys.stderr)
        
        # 2. SQL/PL-SQL 파일 분석
        print(f"[2/5] SQL/PL-SQL 파일 분석 중: {args.sql_dir}", file=sys.stderr)
        sql_results, plsql_results = analyze_sql_files(args.sql_dir)
        
        if not sql_results and not plsql_results:
            print(f"오류: 분석할 SQL/PL-SQL 코드가 없습니다", file=sys.stderr)
            return 1
        
        print(f"[2/5] SQL/PL-SQL 분석 완료", file=sys.stderr)
        
        # 3. 분석 결과 통합
        print(f"[3/5] 분석 결과 통합 중...", file=sys.stderr)
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(dbcsi_result, sql_results, plsql_results)
        print(f"[3/5] 통합 완료", file=sys.stderr)
        
        # 4. 마이그레이션 전략 결정 및 리포트 생성
        print(f"[4/5] 마이그레이션 전략 결정 중...", file=sys.stderr)
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        print(f"[4/5] 추천 전략: {recommendation.recommended_strategy.value}", file=sys.stderr)
        
        # 5. 리포트 포맷팅
        print(f"[5/5] 리포트 생성 중...", file=sys.stderr)
        if args.format == "json":
            formatter = JSONReportFormatter()
            output = formatter.format(recommendation)
        else:  # markdown
            formatter = MarkdownReportFormatter()
            output = formatter.format(recommendation, args.language)
        
        print(f"[5/5] 리포트 생성 완료", file=sys.stderr)
        
        # 결과 출력 또는 저장
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✓ 결과 저장 완료: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except Exception as e:
        print(f"오류: 처리 중 예외 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
