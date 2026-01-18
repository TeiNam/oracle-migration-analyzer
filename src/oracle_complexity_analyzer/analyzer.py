"""
OracleComplexityAnalyzer 메인 클래스

Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하는 메인 클래스입니다.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, Dict, List

from .enums import TargetDatabase
from .data_models import SQLAnalysisResult, PLSQLAnalysisResult
from .file_detector import is_plsql, is_batch_plsql
from . import export_utils

# 로거 초기화
logger = logging.getLogger(__name__)


class OracleComplexityAnalyzer:
    """Oracle 복잡도 분석기 메인 클래스
    
    Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의
    마이그레이션 난이도를 0-10 척도로 평가합니다.
    
    Requirements:
    - 전체: 모든 요구사항을 통합하여 구현
    - 14.6, 14.7: 날짜 폴더에 결과 저장
    
    Attributes:
        target: 타겟 데이터베이스 (PostgreSQL 또는 MySQL)
        calculator: 복잡도 계산기
        guide_provider: 변환 가이드 제공자
        output_dir: 출력 디렉토리 경로
    """
    
    def __init__(self, target_database: TargetDatabase = TargetDatabase.POSTGRESQL,
                 output_dir: str = "reports"):
        """OracleComplexityAnalyzer 초기화
        
        Requirements 전체를 구현합니다.
        
        Args:
            target_database: 타겟 데이터베이스 (기본값: PostgreSQL)
            output_dir: 출력 디렉토리 경로 (기본값: "reports")
        """
        self.target = target_database
        self.output_dir = Path(output_dir)
        
        # 필요한 모듈 import (지연 import로 순환 참조 방지)
        from src.calculators import ComplexityCalculator
        from src.formatters.conversion_guide_provider import ConversionGuideProvider
        
        self.calculator = ComplexityCalculator(target_database)
        self.guide_provider = ConversionGuideProvider(target_database)
    
    def _get_date_folder(self) -> Path:
        """날짜 폴더 경로 생성 (reports/YYYYMMDD/)
        
        Requirements 14.6, 14.7을 구현합니다.
        - 14.6: reports/YYYYMMDD/ 형식으로 폴더 생성
        - 14.7: 폴더가 없으면 자동 생성
        
        Returns:
            Path: 날짜 폴더 경로 (예: reports/20260114/)
        """
        return export_utils.get_date_folder(self.output_dir)
    
    def analyze_sql(self, query: str) -> SQLAnalysisResult:
        """SQL 쿼리 복잡도 분석
        
        Requirements 1.1-7.5, 12.1, 13.1을 구현합니다.
        - 1.1-7.5: SQL 쿼리 구조 분석 및 복잡도 계산
        - 12.1: SQL 쿼리 전체 복잡도 계산
        - 13.1: SQL 분석 시 6가지 세부 점수 제공
        
        Args:
            query: 분석할 SQL 쿼리 문자열
            
        Returns:
            SQLAnalysisResult: SQL 분석 결과
            
        Raises:
            ValueError: 빈 쿼리가 입력된 경우
        """
        # 입력 검증
        if not query or not query.strip():
            raise ValueError("빈 쿼리는 분석할 수 없습니다.")
        
        # 필요한 모듈 import
        from src.parsers.sql_parser import SQLParser
        
        # SQL 파서 생성 및 분석
        parser = SQLParser(query)
        result = self.calculator.calculate_sql_complexity(parser)
        
        # 변환 가이드 추가
        detected_features = result.detected_oracle_features + result.detected_oracle_functions
        result.conversion_guides = self.guide_provider.get_conversion_guide(detected_features)
        
        return result
    
    def analyze_plsql(self, code: str) -> PLSQLAnalysisResult:
        """PL/SQL 오브젝트 복잡도 분석
        
        Requirements 8.1-11.5, 12.2, 13.2를 구현합니다.
        - 8.1-11.5: PL/SQL 오브젝트 구조 분석 및 복잡도 계산
        - 12.2: PL/SQL 오브젝트 전체 복잡도 계산
        - 13.2: PL/SQL 분석 시 5-7가지 세부 점수 제공
        
        Args:
            code: 분석할 PL/SQL 코드 문자열
            
        Returns:
            PLSQLAnalysisResult: PL/SQL 분석 결과
            
        Raises:
            ValueError: 빈 코드가 입력된 경우 또는 오브젝트 타입 감지 실패
        """
        # 입력 검증
        if not code or not code.strip():
            raise ValueError("빈 코드는 분석할 수 없습니다.")
        
        # 필요한 모듈 import
        from src.parsers.plsql import PLSQLParser
        
        # PL/SQL 파서 생성 및 분석
        parser = PLSQLParser(code)
        
        try:
            result = self.calculator.calculate_plsql_complexity(parser)
        except ValueError as e:
            # 오브젝트 타입 감지 실패 시 에러 전파
            raise ValueError(f"PL/SQL 분석 실패: {e}")
        
        # 변환 가이드 추가
        detected_features = result.detected_oracle_features + result.detected_external_dependencies
        result.conversion_guides = self.guide_provider.get_conversion_guide(detected_features)
        
        # MySQL 타겟인 경우 애플리케이션 이관 메시지 추가
        if self.target == TargetDatabase.MYSQL:
            app_migration_msg = self.guide_provider.get_mysql_app_migration_message()
            if app_migration_msg:
                # 변환 가이드에 특별 메시지 추가
                result.conversion_guides['⚠️ 중요'] = app_migration_msg
        
        return result
    
    def analyze_file(self, file_path: str) -> Union[SQLAnalysisResult, PLSQLAnalysisResult]:
        """파일에서 코드를 읽어 분석
        
        파일 내용을 읽어서 SQL 또는 PL/SQL 여부를 판단하고 적절한 분석을 수행합니다.
        
        Args:
            file_path: 분석할 파일 경로
            
        Returns:
            SQLAnalysisResult 또는 PLSQLAnalysisResult: 분석 결과
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            IOError: 파일 읽기 실패
        """
        # 파일 존재 여부 확인
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"파일 읽기 실패: {file_path}", exc_info=True)
            raise IOError(f"파일 읽기 실패: {e}")
        
        # 배치 PL/SQL 파일 여부 확인
        if is_batch_plsql(content):
            return self.analyze_batch_plsql_file(file_path)
        
        # 파일 내용 기반으로 SQL/PL/SQL 판단
        if is_plsql(content):
            return self.analyze_plsql(content)
        else:
            return self.analyze_sql(content)
    
    def analyze_batch_plsql_file(self, file_path: str) -> Dict[str, any]:
        """배치 PL/SQL 파일 분석
        
        여러 PL/SQL 객체가 포함된 파일을 분석합니다.
        ora_plsql_full.sql 스크립트의 출력 형식을 지원합니다.
        
        Args:
            file_path: 분석할 배치 PL/SQL 파일 경로
            
        Returns:
            Dict: 배치 분석 결과
                - total_objects: 전체 객체 수
                - statistics: 객체 타입별 통계
                - results: 개별 객체 분석 결과 리스트
                - summary: 요약 정보
                
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            IOError: 파일 읽기 실패
        """
        from src.parsers.batch_plsql_parser import BatchPLSQLParser
        
        # 파일 존재 여부 확인
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"배치 PL/SQL 파일 읽기 실패: {file_path}", exc_info=True)
            raise IOError(f"파일 읽기 실패: {e}")
        
        # 배치 파서로 객체 분리
        batch_parser = BatchPLSQLParser(content)
        objects = batch_parser.parse()
        
        if not objects:
            return {
                'total_objects': 0,
                'statistics': {},
                'results': [],
                'summary': {
                    'message': '분석 가능한 PL/SQL 객체를 찾을 수 없습니다.'
                }
            }
        
        # 각 객체 분석
        results = []
        failed_objects = []
        
        for obj in objects:
            try:
                # 개별 객체 분석
                result = self.analyze_plsql(obj.ddl_code)
                results.append({
                    'owner': obj.owner,
                    'object_type': obj.object_type,
                    'object_name': obj.object_name,
                    'line_range': f"{obj.line_start}-{obj.line_end}",
                    'analysis': result
                })
            except Exception as e:
                logger.error(f"PL/SQL 객체 분석 실패: {obj.object_name}", exc_info=True)
                failed_objects.append({
                    'owner': obj.owner,
                    'object_type': obj.object_type,
                    'object_name': obj.object_name,
                    'error': str(e)
                })
        
        # 통계 계산
        statistics = batch_parser.get_statistics()
        
        # 복잡도 요약
        complexity_summary = self._calculate_batch_complexity_summary(results)
        
        return {
            'total_objects': len(objects),
            'analyzed_objects': len(results),
            'failed_objects': len(failed_objects),
            'statistics': statistics,
            'results': results,
            'failed': failed_objects,
            'summary': complexity_summary
        }
    
    def _calculate_batch_complexity_summary(self, results: List[Dict]) -> Dict:
        """배치 분석 결과의 복잡도 요약 계산
        
        Args:
            results: 개별 객체 분석 결과 리스트
            
        Returns:
            Dict: 복잡도 요약 정보
        """
        if not results:
            return {}
        
        scores = [r['analysis'].normalized_score for r in results]
        
        return {
            'average_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'complexity_distribution': {
                'very_simple': sum(1 for s in scores if s <= 1),
                'simple': sum(1 for s in scores if 1 < s <= 3),
                'moderate': sum(1 for s in scores if 3 < s <= 5),
                'complex': sum(1 for s in scores if 5 < s <= 7),
                'very_complex': sum(1 for s in scores if 7 < s <= 9),
                'extremely_complex': sum(1 for s in scores if s > 9)
            }
        }
    
    def export_json(self, result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                    filename: str) -> str:
        """분석 결과를 JSON 파일로 저장 (reports/YYYYMMDD/ 폴더에)
        
        Requirements 14.1, 14.6, 14.7을 구현합니다.
        - 14.1: JSON 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        
        Args:
            result: 분석 결과 객체
            filename: 저장할 파일명 (예: "analysis_result.json")
            
        Returns:
            str: 저장된 파일의 전체 경로
            
        Raises:
            IOError: 파일 쓰기 실패
        """
        return export_utils.export_json(result, filename, self.output_dir, self.target)
    
    def export_markdown(self, result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                        filename: str) -> str:
        """분석 결과를 Markdown 파일로 저장 (reports/YYYYMMDD/ 폴더에)
        
        Requirements 14.2, 14.6, 14.7을 구현합니다.
        - 14.2: Markdown 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        
        Args:
            result: 분석 결과 객체
            filename: 저장할 파일명 (예: "analysis_report.md")
            
        Returns:
            str: 저장된 파일의 전체 경로
            
        Raises:
            IOError: 파일 쓰기 실패
        """
        return export_utils.export_markdown(result, filename, self.output_dir, self.target)
    
    def export_json_string(self, json_str: str, source_filename: str) -> str:
        """JSON 문자열을 파일로 저장
        
        Args:
            json_str: JSON 문자열
            source_filename: 원본 파일명 (확장자 변경용)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        return export_utils.export_json_string(json_str, source_filename, self.output_dir, self.target)
    
    def export_markdown_string(self, markdown_str: str, source_filename: str) -> str:
        """Markdown 문자열을 파일로 저장
        
        Args:
            markdown_str: Markdown 문자열
            source_filename: 원본 파일명 (확장자 변경용)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        return export_utils.export_markdown_string(markdown_str, source_filename, self.output_dir, self.target)
