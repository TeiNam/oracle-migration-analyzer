"""
리포트 파서

기존에 생성된 DBCSI 및 SQL 복잡도 분석 리포트(JSON)를 파싱하여
마이그레이션 추천에 필요한 데이터를 추출합니다.

리포트 JSON을 완전히 파싱하는 대신, 필요한 메트릭만 추출하여
간소화된 데이터 구조로 변환합니다.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ..oracle_complexity_analyzer.enums import TargetDatabase, ComplexityLevel, PLSQLObjectType

logger = logging.getLogger(__name__)


class ReportParser:
    """리포트 파일 파서
    
    JSON 형식의 DBCSI 및 SQL 복잡도 분석 리포트를 파싱합니다.
    완전한 데이터 모델 재구성 대신, 필요한 메트릭만 추출합니다.
    """
    
    def parse_dbcsi_metrics(self, report_path: str) -> Optional[Dict[str, Any]]:
        """
        DBCSI 리포트에서 필요한 메트릭만 추출합니다.
        
        Args:
            report_path: DBCSI 리포트 파일 경로 (.json)
            
        Returns:
            메트릭 딕셔너리 또는 None
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            os_info = data.get('os_info', {})
            main_metrics = data.get('main_metrics', [])
            memory_metrics = data.get('memory_metrics', [])
            
            # 평균 CPU 계산
            cpu_values = [m.get('cpu_per_s', 0) for m in main_metrics if m.get('cpu_per_s')]
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            
            # 평균 I/O 계산
            io_values = []
            for m in main_metrics:
                read_iops = m.get('read_iops', 0) or 0
                write_iops = m.get('write_iops', 0) or 0
                io_values.append(read_iops + write_iops)
            avg_io = sum(io_values) / len(io_values) if io_values else 0.0
            
            # 평균 메모리 계산
            memory_values = [m.get('total_gb', 0) for m in memory_metrics if m.get('total_gb')]
            avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
            
            # RAC 감지
            instances = os_info.get('instances', 1)
            rac_detected = instances is not None and instances > 1
            
            # PL/SQL 통계
            def extract_count(value):
                """문자열에서 숫자 추출"""
                if value is None:
                    return None
                if isinstance(value, int):
                    return value
                if isinstance(value, str):
                    import re
                    numbers = re.findall(r'\d+', value)
                    return int(numbers[-1]) if numbers else None
                return None
            
            return {
                'avg_cpu_usage': avg_cpu,
                'avg_io_load': avg_io,
                'avg_memory_usage': avg_memory,
                'rac_detected': rac_detected,
                'awr_plsql_lines': os_info.get('count_lines_plsql'),
                'awr_procedure_count': os_info.get('count_procedures'),
                'awr_function_count': os_info.get('count_functions'),
                'awr_package_count': extract_count(os_info.get('count_packages'))
            }
            
        except Exception as e:
            logger.error(f"DBCSI 메트릭 추출 실패 ({report_path}): {e}", exc_info=True)
            return None
    
    def parse_sql_complexity_reports(
        self,
        report_paths: List[str],
        target_db: str = "postgresql"
    ) -> tuple:
        """
        SQL 복잡도 분석 리포트 파일들을 파싱합니다.
        
        Args:
            report_paths: SQL 복잡도 리포트 파일 경로 리스트
            target_db: 타겟 데이터베이스 (postgresql 또는 mysql)
            
        Returns:
            (sql_results, plsql_results) 튜플
        """
        sql_results = []
        plsql_results = []
        
        # TargetDatabase enum 변환
        target_db_enum = TargetDatabase.POSTGRESQL if target_db == "postgresql" else TargetDatabase.MYSQL
        
        for report_path in report_paths:
            try:
                # JSON 파일만 처리
                if not report_path.endswith('.json'):
                    continue
                
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 배치 리포트인지 확인
                if 'results' in data:
                    logger.info(f"배치 리포트 파싱: {report_path}")
                    sql, plsql = self._parse_batch_report(data, target_db_enum)
                    sql_results.extend(sql)
                    plsql_results.extend(plsql)
                            
            except Exception as e:
                logger.warning(f"리포트 파싱 실패 ({report_path}): {e}", exc_info=True)
                continue
        
        logger.info(f"복잡도 리포트 파싱 완료: SQL {len(sql_results)}개, PL/SQL {len(plsql_results)}개")
        return sql_results, plsql_results
    
    def _parse_batch_report(
        self,
        data: Dict[str, Any],
        target_db: TargetDatabase
    ) -> tuple:
        """배치 리포트 파싱"""
        sql_results = []
        plsql_results = []
        
        for result_data in data.get('results', []):
            try:
                analysis = result_data.get('analysis', {})
                object_type_str = analysis.get('object_type', 'sql')
                
                # ComplexityLevel enum 변환
                complexity_level_str = analysis.get('complexity_level', '알 수 없음')
                complexity_level = self._parse_complexity_level(complexity_level_str)
                
                if object_type_str in ['function', 'procedure', 'package', 'trigger']:
                    # PL/SQL 결과
                    plsql_type = self._parse_plsql_type(object_type_str)
                    
                    plsql_result = PLSQLAnalysisResult(
                        code=f"{result_data.get('owner', '')}.{result_data.get('object_name', '')}",
                        object_type=plsql_type,
                        target_database=target_db,
                        total_score=analysis.get('total_score', 0.0),
                        normalized_score=analysis.get('normalized_score', 0.0),
                        complexity_level=complexity_level,
                        recommendation=analysis.get('recommendation', ''),
                        base_score=analysis.get('base_score', 0.0),
                        code_complexity=analysis.get('code_complexity', 0.0),
                        oracle_features=analysis.get('oracle_features', 0.0),
                        business_logic=analysis.get('business_logic', 0.0),
                        conversion_difficulty=analysis.get('conversion_difficulty', 0.0),
                        detected_oracle_features=analysis.get('detected_oracle_features', []),
                        detected_external_dependencies=analysis.get('detected_external_dependencies', []),
                        line_count=analysis.get('line_count', 0),
                        cursor_count=analysis.get('cursor_count', 0),
                        exception_blocks=analysis.get('exception_blocks', 0),
                        nesting_depth=analysis.get('nesting_depth', 0),
                        bulk_operations_count=analysis.get('bulk_operations_count', 0)
                    )
                    plsql_results.append(plsql_result)
                else:
                    # SQL 결과 (간단한 더미 데이터)
                    sql_result = SQLAnalysisResult(
                        query=f"{result_data.get('owner', '')}.{result_data.get('object_name', '')}",
                        target_database=target_db,
                        total_score=analysis.get('total_score', 0.0),
                        normalized_score=analysis.get('normalized_score', 0.0),
                        complexity_level=complexity_level,
                        recommendation=analysis.get('recommendation', ''),
                        structural_complexity=0.0,
                        oracle_specific_features=0.0,
                        functions_expressions=0.0,
                        data_volume=0.0,
                        execution_complexity=0.0,
                        conversion_difficulty=0.0,
                        detected_oracle_features=analysis.get('detected_oracle_features', [])
                    )
                    sql_results.append(sql_result)
                    
            except Exception as e:
                logger.warning(f"개별 결과 파싱 실패: {e}", exc_info=True)
                continue
        
        return sql_results, plsql_results
    
    def _parse_complexity_level(self, level_str: str) -> ComplexityLevel:
        """복잡도 레벨 문자열을 enum으로 변환"""
        mapping = {
            '매우 간단': ComplexityLevel.VERY_SIMPLE,
            '간단': ComplexityLevel.SIMPLE,
            '중간': ComplexityLevel.MODERATE,
            '복잡': ComplexityLevel.COMPLEX,
            '매우 복잡': ComplexityLevel.VERY_COMPLEX,
            '극도로 복잡': ComplexityLevel.EXTREMELY_COMPLEX
        }
        return mapping.get(level_str, ComplexityLevel.MODERATE)
    
    def _parse_plsql_type(self, type_str: str) -> PLSQLObjectType:
        """PL/SQL 타입 문자열을 enum으로 변환"""
        mapping = {
            'function': PLSQLObjectType.FUNCTION,
            'procedure': PLSQLObjectType.PROCEDURE,
            'package': PLSQLObjectType.PACKAGE,
            'trigger': PLSQLObjectType.TRIGGER
        }
        return mapping.get(type_str, PLSQLObjectType.PROCEDURE)


def find_reports_in_directory(reports_dir: str) -> tuple:
    """
    리포트 디렉토리에서 DBCSI 리포트와 SQL 복잡도 리포트를 찾습니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        (dbcsi_reports, sql_complexity_reports) 튜플
    """
    reports_path = Path(reports_dir)
    
    dbcsi_reports = []
    sql_complexity_reports = []
    
    # JSON 파일만 검색
    json_files = list(reports_path.glob("**/*.json"))
    
    for json_file in json_files:
        filename = json_file.name.lower()
        
        # DBCSI 리포트 감지
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            if 'comparison' not in filename and 'migration' not in filename:
                dbcsi_reports.append(str(json_file))
        
        # SQL 복잡도 리포트 감지
        elif 'plsql_f_' in filename or 'sql_complexity' in filename:
            sql_complexity_reports.append(str(json_file))
        
        # 개별 SQL 파일 리포트도 포함
        elif json_file.parent.name in ['PGSQL', 'MySQL']:
            if 'batch' not in filename and 'migration' not in filename:
                sql_complexity_reports.append(str(json_file))
    
    logger.info(f"발견된 DBCSI 리포트: {len(dbcsi_reports)}개")
    logger.info(f"발견된 SQL 복잡도 리포트: {len(sql_complexity_reports)}개")
    
    return dbcsi_reports, sql_complexity_reports
