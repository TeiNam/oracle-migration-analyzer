"""
분석 결과 통합기

DBCSI 분석기와 SQL/PL-SQL 분석기의 결과를 통합하고 메트릭을 추출합니다.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from src.oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from src.oracle_complexity_analyzer.weights import HIGH_COMPLEXITY_THRESHOLD
from src.oracle_complexity_analyzer.enums import TargetDatabase
from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics
)


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
            dbcsi_metrics = self._extract_metrics_from_dbcsi_result(dbcsi_result)
        
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
    
    def _extract_metrics_from_dbcsi_result(self, dbcsi_result: Any) -> Dict[str, Any]:
        """
        StatspackData 객체에서 메트릭을 추출합니다.
        
        Args:
            dbcsi_result: StatspackData 객체
            
        Returns:
            Dict[str, Any]: 추출된 메트릭 딕셔너리
        """
        metrics: Dict[str, Any] = {}
        
        # OS 정보에서 메트릭 추출
        if hasattr(dbcsi_result, 'os_info') and dbcsi_result.os_info:
            os_info = dbcsi_result.os_info
            metrics['awr_plsql_lines'] = getattr(os_info, 'count_lines_plsql', None)
            metrics['awr_procedure_count'] = getattr(os_info, 'count_procedures', None)
            metrics['awr_function_count'] = getattr(os_info, 'count_functions', None)
            metrics['awr_package_count'] = getattr(os_info, 'count_packages', None)
            
            # RAC 감지 (인스턴스 수가 1보다 크면 RAC)
            instances = getattr(os_info, 'instances', 1)
            metrics['rac_detected'] = instances > 1 if instances else False
            
            # === 신규: 데이터베이스 기본 정보 ===
            metrics['db_name'] = getattr(os_info, 'db_name', None)
            metrics['db_version'] = getattr(os_info, 'version', None)
            metrics['platform_name'] = getattr(os_info, 'platform_name', None)
            metrics['character_set'] = getattr(os_info, 'character_set', None)
            metrics['instance_count'] = instances
            metrics['is_rac'] = instances > 1 if instances else False
            metrics['is_rds'] = getattr(os_info, 'is_rds', None)
            metrics['total_db_size_gb'] = getattr(os_info, 'total_db_size_gb', None)
            metrics['physical_memory_gb'] = getattr(os_info, 'physical_memory_gb', None)
            metrics['cpu_cores'] = getattr(os_info, 'num_cpu_cores', None)
            metrics['num_cpus'] = getattr(os_info, 'num_cpus', None)
            
            # === 신규: 오브젝트 통계 ===
            metrics['count_schemas'] = getattr(os_info, 'count_schemas', None)
            metrics['count_tables'] = getattr(os_info, 'count_tables', None)
            
            # raw_data에서 추가 오브젝트 통계 추출
            raw_data = getattr(os_info, 'raw_data', {})
            metrics['count_views'] = self._parse_int(raw_data.get('COUNT_VIEW'))
            metrics['count_indexes'] = self._parse_int(raw_data.get('COUNT_INDEX'))
            metrics['count_triggers'] = self._parse_int(raw_data.get('COUNT_TRIGGER'))
            metrics['count_types'] = self._parse_int(raw_data.get('COUNT_TYPE'))
            metrics['count_sequences'] = self._parse_int(raw_data.get('COUNT_SEQUENCE'))
            metrics['count_db_links'] = self._parse_int(raw_data.get('COUNT_DB_LINKS'))
            metrics['count_materialized_views'] = self._parse_int(raw_data.get('COUNT_MATERIALIZED VIEW'))
            metrics['count_lobs'] = self._parse_int(raw_data.get('COUNT_LOB'))
        
        # main_metrics에서 성능 메트릭 추출
        if hasattr(dbcsi_result, 'main_metrics') and dbcsi_result.main_metrics:
            main_metrics = dbcsi_result.main_metrics
            # 평균 CPU 사용률
            cpu_values = [m.cpu_per_s for m in main_metrics if m.cpu_per_s is not None]
            metrics['avg_cpu_usage'] = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            
            # 평균 I/O 부하 (읽기 + 쓰기 IOPS)
            io_values = [
                (m.read_iops or 0.0) + (m.write_iops or 0.0) 
                for m in main_metrics
            ]
            metrics['avg_io_load'] = sum(io_values) / len(io_values) if io_values else 0.0
            
            # === 신규: 성능 상세 ===
            read_iops = [m.read_iops for m in main_metrics if m.read_iops is not None]
            write_iops = [m.write_iops for m in main_metrics if m.write_iops is not None]
            read_mbps = [m.read_mb_s for m in main_metrics if m.read_mb_s is not None]
            write_mbps = [m.write_mb_s for m in main_metrics if m.write_mb_s is not None]
            commits = [m.commits_s for m in main_metrics if m.commits_s is not None]
            
            metrics['avg_read_iops'] = sum(read_iops) / len(read_iops) if read_iops else None
            metrics['avg_write_iops'] = sum(write_iops) / len(write_iops) if write_iops else None
            metrics['avg_read_mbps'] = sum(read_mbps) / len(read_mbps) if read_mbps else None
            metrics['avg_write_mbps'] = sum(write_mbps) / len(write_mbps) if write_mbps else None
            metrics['avg_commits_per_sec'] = sum(commits) / len(commits) if commits else None
            
            # 피크 값
            metrics['peak_cpu_usage'] = max(cpu_values) if cpu_values else None
            metrics['peak_iops'] = max(io_values) if io_values else None
        else:
            metrics['avg_cpu_usage'] = 0.0
            metrics['avg_io_load'] = 0.0
        
        # memory_metrics에서 메모리 사용량 추출
        if hasattr(dbcsi_result, 'memory_metrics') and dbcsi_result.memory_metrics:
            memory_metrics = dbcsi_result.memory_metrics
            memory_values = [m.total_gb for m in memory_metrics if m.total_gb is not None]
            metrics['avg_memory_usage'] = sum(memory_values) / len(memory_values) if memory_values else 0.0
        else:
            metrics['avg_memory_usage'] = 0.0
        
        # === 신규: 대기 이벤트 추출 ===
        if hasattr(dbcsi_result, 'wait_events') and dbcsi_result.wait_events:
            metrics['top_wait_events'] = self._extract_top_wait_events(dbcsi_result.wait_events)
        
        # === 신규: Oracle 기능 사용 현황 추출 ===
        if hasattr(dbcsi_result, 'features') and dbcsi_result.features:
            metrics['oracle_features_used'] = self._extract_features_used(dbcsi_result.features)
        
        # === 신규: AWR 특화 데이터 추출 ===
        if hasattr(dbcsi_result, 'is_awr') and dbcsi_result.is_awr():
            if hasattr(dbcsi_result, 'percentile_cpu') and dbcsi_result.percentile_cpu:
                metrics['cpu_percentiles'] = self._extract_cpu_percentiles(dbcsi_result.percentile_cpu)
            if hasattr(dbcsi_result, 'percentile_io') and dbcsi_result.percentile_io:
                metrics['io_percentiles'] = self._extract_io_percentiles(dbcsi_result.percentile_io)
            if hasattr(dbcsi_result, 'buffer_cache_stats') and dbcsi_result.buffer_cache_stats:
                metrics['buffer_cache_hit_ratio'] = self._calculate_avg_hit_ratio(dbcsi_result.buffer_cache_stats)
            if hasattr(dbcsi_result, 'workload_profiles') and dbcsi_result.workload_profiles:
                metrics['top_workload_profiles'] = self._extract_top_workloads(dbcsi_result.workload_profiles)
        
        # 기본값 설정
        metrics.setdefault('rac_detected', False)
        
        return metrics
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """값을 정수로 파싱"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _extract_top_wait_events(self, wait_events: List[Any]) -> List[Dict[str, Any]]:
        """대기 이벤트에서 Top 5 추출 (스냅샷별 집계)"""
        # 이벤트별 집계
        event_totals: Dict[str, Dict[str, Any]] = {}
        for event in wait_events:
            key = f"{event.wait_class}:{event.event_name}"
            if key not in event_totals:
                event_totals[key] = {
                    'wait_class': event.wait_class,
                    'event_name': event.event_name,
                    'total_pctdbt': 0.0,
                    'total_time_s': 0.0,
                    'count': 0
                }
            event_totals[key]['total_pctdbt'] += event.pctdbt or 0.0
            event_totals[key]['total_time_s'] += event.total_time_s or 0.0
            event_totals[key]['count'] += 1
        
        # 평균 계산 및 정렬
        result = []
        for data in event_totals.values():
            count = data['count']
            result.append({
                'wait_class': data['wait_class'],
                'event_name': data['event_name'],
                'avg_pctdbt': data['total_pctdbt'] / count if count > 0 else 0.0,
                'total_time_s': data['total_time_s']
            })
        
        # DB Time % 기준 정렬 후 Top 5 반환
        result.sort(key=lambda x: x['avg_pctdbt'], reverse=True)
        return result[:5]
    
    def _extract_features_used(self, features: List[Any]) -> List[Dict[str, Any]]:
        """Oracle 기능 사용 현황 추출"""
        result = []
        for feature in features:
            result.append({
                'name': feature.name,
                'detected_usages': feature.detected_usages,
                'currently_used': feature.currently_used,
                'feature_info': getattr(feature, 'feature_info', None)
            })
        return result
    
    def _extract_cpu_percentiles(self, percentile_cpu: Dict[str, Any]) -> Dict[str, Any]:
        """CPU 백분위수 추출"""
        result = {}
        for metric_name, data in percentile_cpu.items():
            result[metric_name] = {
                'on_cpu': data.on_cpu if hasattr(data, 'on_cpu') else None,
                'on_cpu_and_resmgr': data.on_cpu_and_resmgr if hasattr(data, 'on_cpu_and_resmgr') else None
            }
        return result
    
    def _extract_io_percentiles(self, percentile_io: Dict[str, Any]) -> Dict[str, Any]:
        """I/O 백분위수 추출"""
        result = {}
        for metric_name, data in percentile_io.items():
            result[metric_name] = {
                'rw_iops': data.rw_iops if hasattr(data, 'rw_iops') else None,
                'r_iops': data.r_iops if hasattr(data, 'r_iops') else None,
                'w_iops': data.w_iops if hasattr(data, 'w_iops') else None,
                'rw_mbps': data.rw_mbps if hasattr(data, 'rw_mbps') else None
            }
        return result
    
    def _calculate_avg_hit_ratio(self, buffer_cache_stats: List[Any]) -> Optional[float]:
        """버퍼 캐시 평균 Hit Ratio 계산"""
        hit_ratios = [s.hit_ratio for s in buffer_cache_stats if hasattr(s, 'hit_ratio') and s.hit_ratio is not None]
        return sum(hit_ratios) / len(hit_ratios) if hit_ratios else None
    
    def _extract_top_workloads(self, workload_profiles: List[Any]) -> List[Dict[str, Any]]:
        """Top 워크로드 프로파일 추출"""
        result = []
        for wp in workload_profiles[:5]:  # Top 5
            result.append({
                'module': getattr(wp, 'module', None),
                'program': getattr(wp, 'program', None),
                'aas': getattr(wp, 'aas_comp', None),
                'db_time_pct': getattr(wp, 'aas_contribution_pct', None)
            })
        return result
    
    def extract_metrics(
        self,
        dbcsi_metrics: Optional[Union[Dict[str, Any], Any]],
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
            dbcsi_metrics = self._extract_metrics_from_dbcsi_result(dbcsi_metrics)
        
        # 성능 메트릭 추출
        if dbcsi_metrics:
            avg_cpu = dbcsi_metrics.get('avg_cpu_usage', 0.0)
            avg_io = dbcsi_metrics.get('avg_io_load', 0.0)
            avg_memory = dbcsi_metrics.get('avg_memory_usage', 0.0)
            rac_detected = dbcsi_metrics.get('rac_detected', False)
            awr_plsql_lines = dbcsi_metrics.get('awr_plsql_lines')
            awr_procedure_count = dbcsi_metrics.get('awr_procedure_count')
            awr_function_count = dbcsi_metrics.get('awr_function_count')
            awr_package_count = dbcsi_metrics.get('awr_package_count')
        else:
            avg_cpu, avg_io, avg_memory = 0.0, 0.0, 0.0
            rac_detected = False
            awr_plsql_lines = None
            awr_procedure_count = None
            awr_function_count = None
            awr_package_count = None
        
        # BULK 연산 개수 집계
        bulk_operation_count = self._count_bulk_operations(plsql_analysis)
        avg_sql_complexity = self._calculate_avg_complexity(sql_analysis)
        avg_plsql_complexity = self._calculate_avg_complexity(plsql_analysis)
        max_sql_complexity = self._calculate_max_complexity(sql_analysis)
        max_plsql_complexity = self._calculate_max_complexity(plsql_analysis)
        
        # MySQL 타겟 복잡도 계산
        avg_sql_complexity_mysql = self._calculate_avg_complexity(sql_analysis_mysql)
        avg_plsql_complexity_mysql = self._calculate_avg_complexity(plsql_analysis_mysql)
        max_sql_complexity_mysql = self._calculate_max_complexity(sql_analysis_mysql)
        max_plsql_complexity_mysql = self._calculate_max_complexity(plsql_analysis_mysql)
        
        # MySQL 타겟 고난이도 개수 (임계값: weights.py에서 가져옴)
        mysql_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.MYSQL]
        high_complexity_sql_count_mysql = self._count_high_complexity(
            sql_analysis_mysql, threshold=mysql_threshold
        )
        high_complexity_plsql_count_mysql = self._count_high_complexity(
            plsql_analysis_mysql, threshold=mysql_threshold
        )
        total_sql_count_mysql = len(sql_analysis_mysql)
        total_plsql_count_mysql = len(plsql_analysis_mysql)
        
        # PostgreSQL 타겟 복잡도 분포 계산 (임계값: weights.py에서 가져옴)
        pg_threshold = HIGH_COMPLEXITY_THRESHOLD[TargetDatabase.POSTGRESQL]
        high_complexity_sql_count = self._count_high_complexity(
            sql_analysis, threshold=pg_threshold
        )
        high_complexity_plsql_count = self._count_high_complexity(
            plsql_analysis, threshold=pg_threshold
        )
        total_sql_count = len(sql_analysis)
        total_plsql_count = len(plsql_analysis)
        
        # 복잡 오브젝트 비율 계산
        total_count = total_sql_count + total_plsql_count
        high_count = high_complexity_sql_count + high_complexity_plsql_count
        high_complexity_ratio = high_count / total_count if total_count > 0 else 0.0
        
        # BULK 연산 개수 집계
        bulk_operation_count = self._count_bulk_operations(plsql_analysis)
        
        return AnalysisMetrics(
            avg_cpu_usage=avg_cpu,
            avg_io_load=avg_io,
            avg_memory_usage=avg_memory,
            avg_sql_complexity=avg_sql_complexity,
            avg_plsql_complexity=avg_plsql_complexity,
            high_complexity_sql_count=high_complexity_sql_count,
            high_complexity_plsql_count=high_complexity_plsql_count,
            total_sql_count=total_sql_count,
            total_plsql_count=total_plsql_count,
            high_complexity_ratio=high_complexity_ratio,
            bulk_operation_count=bulk_operation_count,
            rac_detected=rac_detected,
            # Optional 필드들
            max_sql_complexity=max_sql_complexity,
            max_plsql_complexity=max_plsql_complexity,
            # MySQL 타겟 복잡도
            avg_sql_complexity_mysql=avg_sql_complexity_mysql if avg_sql_complexity_mysql else None,
            avg_plsql_complexity_mysql=avg_plsql_complexity_mysql if avg_plsql_complexity_mysql else None,
            max_sql_complexity_mysql=max_sql_complexity_mysql,
            max_plsql_complexity_mysql=max_plsql_complexity_mysql,
            # MySQL 타겟 고난이도 개수
            high_complexity_sql_count_mysql=high_complexity_sql_count_mysql if high_complexity_sql_count_mysql else None,
            high_complexity_plsql_count_mysql=high_complexity_plsql_count_mysql if high_complexity_plsql_count_mysql else None,
            total_sql_count_mysql=total_sql_count_mysql if total_sql_count_mysql else None,
            total_plsql_count_mysql=total_plsql_count_mysql if total_plsql_count_mysql else None,
            awr_plsql_lines=awr_plsql_lines,
            awr_procedure_count=awr_procedure_count,
            awr_function_count=awr_function_count,
            awr_package_count=awr_package_count,
            awr_trigger_count=dbcsi_metrics.get('awr_trigger_count') if dbcsi_metrics else None,
            awr_type_count=dbcsi_metrics.get('awr_type_count') if dbcsi_metrics else None,
            # 신규 필드: 데이터베이스 기본 정보
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
            # 신규 필드: 오브젝트 통계
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
            # 신규 필드: 성능 상세
            avg_read_iops=dbcsi_metrics.get('avg_read_iops') if dbcsi_metrics else None,
            avg_write_iops=dbcsi_metrics.get('avg_write_iops') if dbcsi_metrics else None,
            avg_read_mbps=dbcsi_metrics.get('avg_read_mbps') if dbcsi_metrics else None,
            avg_write_mbps=dbcsi_metrics.get('avg_write_mbps') if dbcsi_metrics else None,
            avg_commits_per_sec=dbcsi_metrics.get('avg_commits_per_sec') if dbcsi_metrics else None,
            peak_cpu_usage=dbcsi_metrics.get('peak_cpu_usage') if dbcsi_metrics else None,
            peak_iops=dbcsi_metrics.get('peak_iops') if dbcsi_metrics else None,
            peak_io_load=dbcsi_metrics.get('peak_io_load') if dbcsi_metrics else None,
            peak_memory_usage=dbcsi_metrics.get('peak_memory_usage') if dbcsi_metrics else None,
            # 신규 필드: 대기 이벤트
            top_wait_events=dbcsi_metrics.get('top_wait_events', []) if dbcsi_metrics else [],
            # 신규 필드: Oracle 기능 사용
            oracle_features_used=dbcsi_metrics.get('oracle_features_used', []) if dbcsi_metrics else [],
            # 신규 필드: AWR 특화
            cpu_percentiles=dbcsi_metrics.get('cpu_percentiles') if dbcsi_metrics else None,
            io_percentiles=dbcsi_metrics.get('io_percentiles') if dbcsi_metrics else None,
            buffer_cache_hit_ratio=dbcsi_metrics.get('buffer_cache_hit_ratio') if dbcsi_metrics else None,
            top_workload_profiles=dbcsi_metrics.get('top_workload_profiles', []) if dbcsi_metrics else [],
            # 신규 필드: 리포트 타입
            report_type=dbcsi_metrics.get('report_type') if dbcsi_metrics else None,
            # 신규 필드: Oracle 특화 기능 및 외부 의존성 (복잡도 리포트에서 추출)
            detected_oracle_features_summary=self._aggregate_oracle_features(plsql_analysis),
            detected_external_dependencies_summary=self._merge_external_dependencies(
                self._aggregate_external_dependencies(plsql_analysis),
                dbcsi_metrics.get('external_dependencies_from_report', []) if dbcsi_metrics else []
            ),
            conversion_guide=dbcsi_metrics.get('conversion_guide', {}) if dbcsi_metrics else {},
        )
    
    def _calculate_avg_complexity(
        self,
        analysis_results: List[Union[SQLAnalysisResult, PLSQLAnalysisResult]]
    ) -> float:
        """
        평균 복잡도 계산
        
        Args:
            analysis_results: 분석 결과 리스트
            
        Returns:
            float: 평균 복잡도 점수
        """
        if not analysis_results:
            return 0.0
        
        complexity_scores = [result.normalized_score for result in analysis_results]
        return sum(complexity_scores) / len(complexity_scores)
    
    def _calculate_max_complexity(
        self,
        analysis_results: List[Union[SQLAnalysisResult, PLSQLAnalysisResult]]
    ) -> Optional[float]:
        """
        최대 복잡도 계산
        
        Args:
            analysis_results: 분석 결과 리스트
            
        Returns:
            Optional[float]: 최대 복잡도 점수 (결과가 없으면 None)
        """
        if not analysis_results:
            return None
        
        complexity_scores = [result.normalized_score for result in analysis_results]
        return max(complexity_scores)
    
    def _count_high_complexity(
        self,
        analysis_results: List[Union[SQLAnalysisResult, PLSQLAnalysisResult]],
        threshold: float = 7.0
    ) -> int:
        """
        복잡도 임계값 이상 오브젝트 개수 집계
        
        Args:
            analysis_results: 분석 결과 리스트
            threshold: 복잡도 임계값 (기본값: 7.0)
            
        Returns:
            int: 임계값 이상 오브젝트 개수
        """
        return sum(1 for result in analysis_results if result.normalized_score >= threshold)
    
    def _count_bulk_operations(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> int:
        """
        BULK 연산 개수 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            int: BULK 연산 총 개수
        """
        return sum(result.bulk_operations_count for result in plsql_analysis)
    
    def _aggregate_oracle_features(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> Dict[str, int]:
        """
        PL/SQL 분석 결과에서 Oracle 특화 기능 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            Dict[str, int]: 기능명 -> 사용 횟수
        """
        features: Dict[str, int] = {}
        for result in plsql_analysis:
            for feature in result.detected_oracle_features:
                features[feature] = features.get(feature, 0) + 1
        return features
    
    def _aggregate_external_dependencies(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> Dict[str, int]:
        """
        PL/SQL 분석 결과에서 외부 의존성 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            Dict[str, int]: 의존성명 -> 사용 횟수
        """
        dependencies: Dict[str, int] = {}
        for result in plsql_analysis:
            for dep in result.detected_external_dependencies:
                dependencies[dep] = dependencies.get(dep, 0) + 1
        return dependencies
    
    def _merge_external_dependencies(
        self,
        from_analysis: Dict[str, int],
        from_report: List[str]
    ) -> Dict[str, int]:
        """
        분석 결과와 리포트에서 추출한 외부 의존성 병합
        
        Args:
            from_analysis: 개별 분석 결과에서 집계한 의존성
            from_report: 리포트 요약에서 추출한 의존성 목록
            
        Returns:
            Dict[str, int]: 병합된 의존성 (의존성명 -> 사용 횟수)
        """
        result = dict(from_analysis)
        
        # 리포트에서 추출한 의존성 추가 (분석 결과에 없는 경우)
        for dep in from_report:
            if dep not in result:
                result[dep] = 1  # 리포트에서만 발견된 경우 1회로 설정
        
        return result
