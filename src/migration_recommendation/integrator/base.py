"""
분석 결과 통합기 메인 클래스

DBCSI 분석기와 SQL/PL-SQL 분석기의 결과를 통합합니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from src.oracle_complexity_analyzer.weights import HIGH_COMPLEXITY_THRESHOLD
from src.oracle_complexity_analyzer.enums import TargetDatabase
from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics
)
from .dbcsi_extractor import DBCSIMetricsExtractor
from .metrics_calculator import MetricsCalculator


class AnalysisResultIntegrator:
    """분석 결과 통합기
    
    DBCSI 분석 결과와 SQL/PL-SQL 분석 결과를 통합하여
    마이그레이션 의사결정에 필요한 메트릭을 추출합니다.
    
    Requirements:
    - 1.1: DBCSI와 SQL 분석 결과 통합
    - 1.4: 평균 SQL 복잡도 계산
    - 1.5: 평균 PL/SQL 복잡도 계산
    - 1.6: BULK 연산 개수 집계
    - 11.1: 평균 CPU 사용률 추출
    - 11.2: 평균 I/O 부하 추출
    - 11.3: 평균 메모리 사용량 추출
    - 12.1: 복잡도 7.0 이상 SQL 개수 집계
    - 12.2: 복잡도 7.0 이상 PL/SQL 개수 집계
    """
    
    def __init__(self) -> None:
        """통합기 초기화"""
        self._dbcsi_extractor = DBCSIMetricsExtractor()
        self._metrics_calculator = MetricsCalculator()
    
    def integrate(
        self,
        dbcsi_result: Optional[Any] = None,
        sql_analysis: Optional[List[SQLAnalysisResult]] = None,
        plsql_analysis: Optional[List[PLSQLAnalysisResult]] = None,
        dbcsi_metrics: Optional[Dict[str, Any]] = None,
        sql_analysis_mysql: Optional[List[SQLAnalysisResult]] = None,
        plsql_analysis_mysql: Optional[List[PLSQLAnalysisResult]] = None
    ) -> IntegratedAnalysisResult:
        """
        분석 결과를 통합합니다.
        
        Args:
            dbcsi_result: DBCSI 파싱 결과 (StatspackData 객체)
            sql_analysis: SQL 복잡도 분석 결과 리스트 (PostgreSQL 타겟)
            plsql_analysis: PL/SQL 복잡도 분석 결과 리스트 (PostgreSQL 타겟)
            dbcsi_metrics: DBCSI 메트릭 딕셔너리 (간소화된 형태, dbcsi_result 대신 사용 가능)
            sql_analysis_mysql: SQL 복잡도 분석 결과 리스트 (MySQL 타겟)
            plsql_analysis_mysql: PL/SQL 복잡도 분석 결과 리스트 (MySQL 타겟)
            
        Returns:
            IntegratedAnalysisResult: 통합된 분석 결과
            
        Raises:
            ValueError: 필수 분석 결과가 누락된 경우
        """
        # 기본값 설정
        sql_analysis = sql_analysis or []
        plsql_analysis = plsql_analysis or []
        sql_analysis_mysql = sql_analysis_mysql or []
        plsql_analysis_mysql = plsql_analysis_mysql or []
        
        # 입력 검증
        if not sql_analysis and not plsql_analysis:
            raise ValueError("SQL 또는 PL/SQL 분석 결과가 필요합니다")
        
        # dbcsi_result에서 메트릭 추출 (dbcsi_metrics가 없는 경우)
        if dbcsi_metrics is None and dbcsi_result is not None:
            dbcsi_metrics = self._dbcsi_extractor.extract(dbcsi_result)
        
        # 메트릭 추출 (PostgreSQL + MySQL)
        metrics = self.extract_metrics(
            dbcsi_metrics, 
            sql_analysis, 
            plsql_analysis,
            sql_analysis_mysql,
            plsql_analysis_mysql
        )
        
        # 통합 결과 생성
        return IntegratedAnalysisResult(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis,
            metrics=metrics,
            analysis_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def extract_metrics(
        self,
        dbcsi_metrics: Optional[Dict[str, Any]],
        sql_analysis: List[SQLAnalysisResult],
        plsql_analysis: List[PLSQLAnalysisResult],
        sql_analysis_mysql: Optional[List[SQLAnalysisResult]] = None,
        plsql_analysis_mysql: Optional[List[PLSQLAnalysisResult]] = None
    ) -> AnalysisMetrics:
        """
        분석 결과에서 메트릭을 추출합니다.
        
        Args:
            dbcsi_metrics: DBCSI 메트릭 딕셔너리 또는 StatspackData 객체
            sql_analysis: SQL 복잡도 분석 결과 리스트 (PostgreSQL 타겟)
            plsql_analysis: PL/SQL 복잡도 분석 결과 리스트 (PostgreSQL 타겟)
            sql_analysis_mysql: SQL 복잡도 분석 결과 리스트 (MySQL 타겟)
            plsql_analysis_mysql: PL/SQL 복잡도 분석 결과 리스트 (MySQL 타겟)
            
        Returns:
            AnalysisMetrics: 추출된 메트릭
        """
        # 기본값 설정
        sql_analysis_mysql = sql_analysis_mysql or []
        plsql_analysis_mysql = plsql_analysis_mysql or []
        
        # StatspackData 객체인 경우 딕셔너리로 변환
        if dbcsi_metrics is not None and not isinstance(dbcsi_metrics, dict):
            dbcsi_metrics = self._dbcsi_extractor.extract(dbcsi_metrics)
        
        # 성능 메트릭 추출
        perf_metrics = self._extract_performance_metrics(dbcsi_metrics)
        
        # 복잡도 메트릭 계산
        complexity_metrics = self._calculate_complexity_metrics(
            sql_analysis, plsql_analysis,
            sql_analysis_mysql, plsql_analysis_mysql
        )
        
        # AnalysisMetrics 생성
        return self._build_analysis_metrics(
            dbcsi_metrics, perf_metrics, complexity_metrics, plsql_analysis
        )
    
    def _extract_performance_metrics(
        self, dbcsi_metrics: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """성능 메트릭 추출"""
        if dbcsi_metrics:
            return {
                'avg_cpu': dbcsi_metrics.get('avg_cpu_usage', 0.0),
                'avg_io': dbcsi_metrics.get('avg_io_load', 0.0),
                'avg_memory': dbcsi_metrics.get('avg_memory_usage', 0.0),
                'rac_detected': dbcsi_metrics.get('rac_detected', False),
                'awr_plsql_lines': dbcsi_metrics.get('awr_plsql_lines'),
                'awr_procedure_count': dbcsi_metrics.get('awr_procedure_count'),
                'awr_function_count': dbcsi_metrics.get('awr_function_count'),
                'awr_package_count': dbcsi_metrics.get('awr_package_count'),
            }
        return {
            'avg_cpu': 0.0,
            'avg_io': 0.0,
            'avg_memory': 0.0,
            'rac_detected': False,
            'awr_plsql_lines': None,
            'awr_procedure_count': None,
            'awr_function_count': None,
            'awr_package_count': None,
        }
    
    def _calculate_complexity_metrics(
        self,
        sql_analysis: List[SQLAnalysisResult],
        plsql_analysis: List[PLSQLAnalysisResult],
        sql_analysis_mysql: List[SQLAnalysisResult],
        plsql_analysis_mysql: List[PLSQLAnalysisResult]
    ) -> Dict[str, Any]:
        """복잡도 메트릭 계산"""
        calc = self._metrics_calculator
        
        # PostgreSQL 타겟 복잡도
        avg_sql = calc.calculate_avg_complexity(sql_analysis)
        avg_plsql = calc.calculate_avg_complexity(plsql_analysis)
        max_sql = calc.calculate_max_complexity(sql_analysis)
        max_plsql = calc.calculate_max_complexity(plsql_analysis)
        
        # MySQL 타겟 복잡도
        avg_sql_mysql = calc.calculate_avg_complexity(sql_analysis_mysql)
        avg_plsql_mysql = calc.calculate_avg_complexity(plsql_analysis_mysql)
        max_sql_mysql = calc.calculate_max_complexity(sql_analysis_mysql)
        max_plsql_mysql = calc.calculate_max_complexity(plsql_analysis_mysql)
        
        # 임계값 기반 고난이도 개수
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
        
        high_sql = calc.count_high_complexity(sql_analysis, pg_threshold)
        high_plsql = calc.count_high_complexity(plsql_analysis, pg_threshold)
        high_sql_mysql = calc.count_high_complexity(sql_analysis_mysql, mysql_threshold)
        high_plsql_mysql = calc.count_high_complexity(plsql_analysis_mysql, mysql_threshold)
        
        # 개수
        total_sql = len(sql_analysis)
        total_plsql = len(plsql_analysis)
        total_sql_mysql = len(sql_analysis_mysql)
        total_plsql_mysql = len(plsql_analysis_mysql)
        
        # 복잡 오브젝트 비율
        total_count = total_sql + total_plsql
        high_count = high_sql + high_plsql
        high_ratio = high_count / total_count if total_count > 0 else 0.0
        
        # BULK 연산 개수
        bulk_count = calc.count_bulk_operations(plsql_analysis)
        
        return {
            'avg_sql': avg_sql,
            'avg_plsql': avg_plsql,
            'max_sql': max_sql,
            'max_plsql': max_plsql,
            'avg_sql_mysql': avg_sql_mysql,
            'avg_plsql_mysql': avg_plsql_mysql,
            'max_sql_mysql': max_sql_mysql,
            'max_plsql_mysql': max_plsql_mysql,
            'high_sql': high_sql,
            'high_plsql': high_plsql,
            'high_sql_mysql': high_sql_mysql,
            'high_plsql_mysql': high_plsql_mysql,
            'total_sql': total_sql,
            'total_plsql': total_plsql,
            'total_sql_mysql': total_sql_mysql,
            'total_plsql_mysql': total_plsql_mysql,
            'high_ratio': high_ratio,
            'bulk_count': bulk_count,
        }
    
    def _build_analysis_metrics(
        self,
        dbcsi_metrics: Optional[Dict[str, Any]],
        perf: Dict[str, Any],
        comp: Dict[str, Any],
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> AnalysisMetrics:
        """AnalysisMetrics 객체 생성"""
        calc = self._metrics_calculator
        
        # Oracle 기능 및 외부 의존성 집계
        oracle_features = calc.aggregate_oracle_features(plsql_analysis)
        ext_deps = calc.aggregate_external_dependencies(plsql_analysis)
        report_deps = dbcsi_metrics.get('external_dependencies_from_report', []) if dbcsi_metrics else []
        merged_deps = calc.merge_external_dependencies(ext_deps, report_deps)
        
        return AnalysisMetrics(
            # 성능 메트릭
            avg_cpu_usage=perf['avg_cpu'],
            avg_io_load=perf['avg_io'],
            avg_memory_usage=perf['avg_memory'],
            rac_detected=perf['rac_detected'],
            # PostgreSQL 복잡도
            avg_sql_complexity=comp['avg_sql'],
            avg_plsql_complexity=comp['avg_plsql'],
            max_sql_complexity=comp['max_sql'],
            max_plsql_complexity=comp['max_plsql'],
            high_complexity_sql_count=comp['high_sql'],
            high_complexity_plsql_count=comp['high_plsql'],
            total_sql_count=comp['total_sql'],
            total_plsql_count=comp['total_plsql'],
            high_complexity_ratio=comp['high_ratio'],
            bulk_operation_count=comp['bulk_count'],
            # MySQL 복잡도
            avg_sql_complexity_mysql=comp['avg_sql_mysql'] if comp['avg_sql_mysql'] else None,
            avg_plsql_complexity_mysql=comp['avg_plsql_mysql'] if comp['avg_plsql_mysql'] else None,
            max_sql_complexity_mysql=comp['max_sql_mysql'],
            max_plsql_complexity_mysql=comp['max_plsql_mysql'],
            high_complexity_sql_count_mysql=comp['high_sql_mysql'] if comp['high_sql_mysql'] else None,
            high_complexity_plsql_count_mysql=comp['high_plsql_mysql'] if comp['high_plsql_mysql'] else None,
            total_sql_count_mysql=comp['total_sql_mysql'] if comp['total_sql_mysql'] else None,
            total_plsql_count_mysql=comp['total_plsql_mysql'] if comp['total_plsql_mysql'] else None,
            # AWR 메트릭
            awr_plsql_lines=perf['awr_plsql_lines'],
            awr_procedure_count=perf['awr_procedure_count'],
            awr_function_count=perf['awr_function_count'],
            awr_package_count=perf['awr_package_count'],
            awr_trigger_count=dbcsi_metrics.get('awr_trigger_count') if dbcsi_metrics else None,
            awr_type_count=dbcsi_metrics.get('awr_type_count') if dbcsi_metrics else None,
            # 데이터베이스 기본 정보
            db_name=dbcsi_metrics.get('db_name') if dbcsi_metrics else None,
            db_version=dbcsi_metrics.get('db_version') if dbcsi_metrics else None,
            platform_name=dbcsi_metrics.get('platform_name') if dbcsi_metrics else None,
            character_set=dbcsi_metrics.get('character_set') if dbcsi_metrics else None,
            instance_count=dbcsi_metrics.get('instance_count') if dbcsi_metrics else None,
            is_rac=dbcsi_metrics.get('is_rac', False) if dbcsi_metrics else False,
            is_rds=dbcsi_metrics.get('is_rds') if dbcsi_metrics else None,
            total_db_size_gb=dbcsi_metrics.get('total_db_size_gb') if dbcsi_metrics else None,
            physical_memory_gb=dbcsi_metrics.get('physical_memory_gb') if dbcsi_metrics else None,
            cpu_cores=dbcsi_metrics.get('cpu_cores') if dbcsi_metrics else None,
            num_cpus=dbcsi_metrics.get('num_cpus') if dbcsi_metrics else None,
            # 오브젝트 통계
            count_schemas=dbcsi_metrics.get('count_schemas') if dbcsi_metrics else None,
            count_tables=dbcsi_metrics.get('count_tables') if dbcsi_metrics else None,
            count_views=dbcsi_metrics.get('count_views') if dbcsi_metrics else None,
            count_indexes=dbcsi_metrics.get('count_indexes') if dbcsi_metrics else None,
            count_triggers=dbcsi_metrics.get('count_triggers') if dbcsi_metrics else None,
            count_types=dbcsi_metrics.get('count_types') if dbcsi_metrics else None,
            count_sequences=dbcsi_metrics.get('count_sequences') if dbcsi_metrics else None,
            count_db_links=dbcsi_metrics.get('count_db_links') if dbcsi_metrics else None,
            count_materialized_views=dbcsi_metrics.get('count_materialized_views') if dbcsi_metrics else None,
            count_lobs=dbcsi_metrics.get('count_lobs') if dbcsi_metrics else None,
            # 성능 상세
            avg_read_iops=dbcsi_metrics.get('avg_read_iops') if dbcsi_metrics else None,
            avg_write_iops=dbcsi_metrics.get('avg_write_iops') if dbcsi_metrics else None,
            avg_read_mbps=dbcsi_metrics.get('avg_read_mbps') if dbcsi_metrics else None,
            avg_write_mbps=dbcsi_metrics.get('avg_write_mbps') if dbcsi_metrics else None,
            avg_commits_per_sec=dbcsi_metrics.get('avg_commits_per_sec') if dbcsi_metrics else None,
            peak_cpu_usage=dbcsi_metrics.get('peak_cpu_usage') if dbcsi_metrics else None,
            peak_iops=dbcsi_metrics.get('peak_iops') if dbcsi_metrics else None,
            peak_io_load=dbcsi_metrics.get('peak_io_load') if dbcsi_metrics else None,
            peak_memory_usage=dbcsi_metrics.get('peak_memory_usage') if dbcsi_metrics else None,
            # 대기 이벤트
            top_wait_events=dbcsi_metrics.get('top_wait_events', []) if dbcsi_metrics else [],
            # Oracle 기능 사용
            oracle_features_used=dbcsi_metrics.get('oracle_features_used', []) if dbcsi_metrics else [],
            # AWR 특화
            cpu_percentiles=dbcsi_metrics.get('cpu_percentiles') if dbcsi_metrics else None,
            io_percentiles=dbcsi_metrics.get('io_percentiles') if dbcsi_metrics else None,
            buffer_cache_hit_ratio=dbcsi_metrics.get('buffer_cache_hit_ratio') if dbcsi_metrics else None,
            top_workload_profiles=dbcsi_metrics.get('top_workload_profiles', []) if dbcsi_metrics else [],
            # 리포트 타입
            report_type=dbcsi_metrics.get('report_type') if dbcsi_metrics else None,
            # SGA 권장사항
            current_sga_gb=dbcsi_metrics.get('current_sga_gb') if dbcsi_metrics else None,
            recommended_sga_gb=dbcsi_metrics.get('recommended_sga_gb') if dbcsi_metrics else None,
            # Oracle 특화 기능 및 외부 의존성
            detected_oracle_features_summary=oracle_features,
            detected_external_dependencies_summary=merged_deps,
            conversion_guide=dbcsi_metrics.get('conversion_guide', {}) if dbcsi_metrics else {},
        )
