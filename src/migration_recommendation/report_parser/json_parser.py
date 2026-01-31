"""
JSON 리포트 파서

DBCSI 및 SQL 복잡도 분석 JSON 리포트를 파싱합니다.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple

from ...oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ...oracle_complexity_analyzer.enums import TargetDatabase, ComplexityLevel, PLSQLObjectType

logger = logging.getLogger(__name__)


class JsonReportParser:
    """JSON 리포트 파서
    
    DBCSI 및 SQL 복잡도 분석 JSON 리포트를 파싱합니다.
    """
    
    def parse_dbcsi_json(self, report_path: str) -> Optional[Dict[str, Any]]:
        """JSON 형식 DBCSI 리포트 파싱"""
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
            
            return {
                'avg_cpu_usage': avg_cpu,
                'avg_io_load': avg_io,
                'avg_memory_usage': avg_memory,
                'rac_detected': rac_detected,
                'awr_plsql_lines': os_info.get('count_lines_plsql'),
                'awr_procedure_count': os_info.get('count_procedures'),
                'awr_function_count': os_info.get('count_functions'),
                'awr_package_count': os_info.get('count_packages'),
                'db_name': os_info.get('db_name'),
                'db_version': os_info.get('version'),
                'platform_name': os_info.get('platform_name'),
                'character_set': os_info.get('character_set'),
                'instance_count': instances,
                'is_rac': rac_detected,
                'total_db_size_gb': os_info.get('total_db_size_gb'),
                'physical_memory_gb': os_info.get('physical_memory_gb'),
                'cpu_cores': os_info.get('num_cpu_cores'),
                'num_cpus': os_info.get('num_cpus'),
                'report_type': 'json',
            }
            
        except Exception as e:
            logger.error(f"DBCSI JSON 파싱 실패 ({report_path}): {e}", exc_info=True)
            return None
    
    def parse_batch_report(
        self,
        data: Dict[str, Any],
        target_db: TargetDatabase
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """배치 JSON 리포트 파싱"""
        sql_results: List[SQLAnalysisResult] = []
        plsql_results: List[PLSQLAnalysisResult] = []
        
        for result_data in data.get('results', []):
            try:
                analysis = result_data.get('analysis', {})
                object_type_str = analysis.get('object_type', 'sql')
                
                complexity_level_str = analysis.get('complexity_level', '알 수 없음')
                complexity_level = self._parse_complexity_level(complexity_level_str)
                
                if object_type_str in ['function', 'procedure', 'package', 'trigger', 'type', 'type body']:
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
            'trigger': PLSQLObjectType.TRIGGER,
            'type': PLSQLObjectType.PROCEDURE,
            'type body': PLSQLObjectType.PROCEDURE,
        }
        return mapping.get(type_str.lower(), PLSQLObjectType.PROCEDURE)
