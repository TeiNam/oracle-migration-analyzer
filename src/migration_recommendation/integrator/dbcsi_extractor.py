"""
DBCSI 메트릭 추출기

StatspackData 객체에서 마이그레이션 분석에 필요한 메트릭을 추출합니다.
"""

from typing import Any, Dict, List, Optional


class DBCSIMetricsExtractor:
    """DBCSI 결과에서 메트릭을 추출하는 클래스"""
    
    def extract(self, dbcsi_result: Any) -> Dict[str, Any]:
        """
        StatspackData 객체에서 메트릭을 추출합니다.
        
        Args:
            dbcsi_result: StatspackData 객체
            
        Returns:
            Dict[str, Any]: 추출된 메트릭 딕셔너리
        """
        metrics: Dict[str, Any] = {}
        
        # OS 정보에서 메트릭 추출
        self._extract_os_info(dbcsi_result, metrics)
        
        # 성능 메트릭 추출
        self._extract_performance_metrics(dbcsi_result, metrics)
        
        # 메모리 메트릭 추출
        self._extract_memory_metrics(dbcsi_result, metrics)
        
        # 대기 이벤트 추출
        self._extract_wait_events(dbcsi_result, metrics)
        
        # Oracle 기능 사용 현황 추출
        self._extract_features(dbcsi_result, metrics)
        
        # AWR 특화 데이터 추출
        self._extract_awr_specific(dbcsi_result, metrics)
        
        # 기본값 설정
        metrics.setdefault('rac_detected', False)
        
        return metrics
    
    def _extract_os_info(self, dbcsi_result: Any, metrics: Dict[str, Any]) -> None:
        """OS 정보에서 메트릭 추출"""
        if not hasattr(dbcsi_result, 'os_info') or not dbcsi_result.os_info:
            return
            
        os_info = dbcsi_result.os_info
        metrics['awr_plsql_lines'] = getattr(os_info, 'count_lines_plsql', None)
        metrics['awr_procedure_count'] = getattr(os_info, 'count_procedures', None)
        metrics['awr_function_count'] = getattr(os_info, 'count_functions', None)
        metrics['awr_package_count'] = getattr(os_info, 'count_packages', None)
        
        # RAC 감지 (인스턴스 수가 1보다 크면 RAC)
        instances = getattr(os_info, 'instances', 1)
        metrics['rac_detected'] = instances > 1 if instances else False
        
        # 데이터베이스 기본 정보
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
        
        # 오브젝트 통계
        self._extract_object_stats(os_info, metrics)
    
    def _extract_object_stats(self, os_info: Any, metrics: Dict[str, Any]) -> None:
        """오브젝트 통계 추출"""
        metrics['count_schemas'] = getattr(os_info, 'count_schemas', None)
        metrics['count_tables'] = getattr(os_info, 'count_tables', None)
        
        # OSInformation 객체에서 직접 가져오기 (우선)
        metrics['count_views'] = getattr(os_info, 'count_views', None)
        metrics['count_indexes'] = getattr(os_info, 'count_indexes', None)
        metrics['count_triggers'] = getattr(os_info, 'count_triggers', None)
        metrics['count_types'] = getattr(os_info, 'count_types', None)
        metrics['count_sequences'] = getattr(os_info, 'count_sequences', None)
        metrics['count_db_links'] = getattr(os_info, 'count_db_links', None)
        metrics['count_materialized_views'] = getattr(os_info, 'count_materialized_views', None)
        metrics['count_lobs'] = getattr(os_info, 'count_lobs', None)
        
        # raw_data에서 추가 오브젝트 통계 추출 (OSInformation에 없는 경우 fallback)
        raw_data = getattr(os_info, 'raw_data', {})
        if metrics['count_views'] is None:
            metrics['count_views'] = self._parse_int(raw_data.get('COUNT_VIEW'))
        if metrics['count_indexes'] is None:
            metrics['count_indexes'] = self._parse_int(raw_data.get('COUNT_INDEX'))
        if metrics['count_triggers'] is None:
            metrics['count_triggers'] = self._parse_int(raw_data.get('COUNT_TRIGGER'))
        if metrics['count_types'] is None:
            metrics['count_types'] = self._parse_int(raw_data.get('COUNT_TYPE'))
        if metrics['count_sequences'] is None:
            metrics['count_sequences'] = self._parse_int(raw_data.get('COUNT_SEQUENCE'))
        if metrics['count_db_links'] is None:
            metrics['count_db_links'] = self._parse_int(raw_data.get('COUNT_DB_LINKS'))
        if metrics['count_materialized_views'] is None:
            metrics['count_materialized_views'] = self._parse_int(
                raw_data.get('COUNT_MATERIALIZED VIEW')
            )
        if metrics['count_lobs'] is None:
            metrics['count_lobs'] = self._parse_int(raw_data.get('COUNT_LOB'))
    
    def _extract_performance_metrics(
        self, dbcsi_result: Any, metrics: Dict[str, Any]
    ) -> None:
        """성능 메트릭 추출"""
        if not hasattr(dbcsi_result, 'main_metrics') or not dbcsi_result.main_metrics:
            metrics['avg_cpu_usage'] = 0.0
            metrics['avg_io_load'] = 0.0
            return
            
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
        
        # 성능 상세
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
    
    def _extract_memory_metrics(self, dbcsi_result: Any, metrics: Dict[str, Any]) -> None:
        """메모리 메트릭 추출"""
        if hasattr(dbcsi_result, 'memory_metrics') and dbcsi_result.memory_metrics:
            memory_metrics = dbcsi_result.memory_metrics
            memory_values = [m.total_gb for m in memory_metrics if m.total_gb is not None]
            metrics['avg_memory_usage'] = (
                sum(memory_values) / len(memory_values) if memory_values else 0.0
            )
        else:
            metrics['avg_memory_usage'] = 0.0
    
    def _extract_wait_events(self, dbcsi_result: Any, metrics: Dict[str, Any]) -> None:
        """대기 이벤트 추출"""
        if hasattr(dbcsi_result, 'wait_events') and dbcsi_result.wait_events:
            metrics['top_wait_events'] = self._get_top_wait_events(dbcsi_result.wait_events)
    
    def _extract_features(self, dbcsi_result: Any, metrics: Dict[str, Any]) -> None:
        """Oracle 기능 사용 현황 추출"""
        if hasattr(dbcsi_result, 'features') and dbcsi_result.features:
            metrics['oracle_features_used'] = self._get_features_used(dbcsi_result.features)
    
    def _extract_awr_specific(self, dbcsi_result: Any, metrics: Dict[str, Any]) -> None:
        """AWR 특화 데이터 추출"""
        if not hasattr(dbcsi_result, 'is_awr') or not dbcsi_result.is_awr():
            return
            
        if hasattr(dbcsi_result, 'percentile_cpu') and dbcsi_result.percentile_cpu:
            metrics['cpu_percentiles'] = self._get_cpu_percentiles(dbcsi_result.percentile_cpu)
        if hasattr(dbcsi_result, 'percentile_io') and dbcsi_result.percentile_io:
            metrics['io_percentiles'] = self._get_io_percentiles(dbcsi_result.percentile_io)
        if hasattr(dbcsi_result, 'buffer_cache_stats') and dbcsi_result.buffer_cache_stats:
            metrics['buffer_cache_hit_ratio'] = self._calc_avg_hit_ratio(
                dbcsi_result.buffer_cache_stats
            )
        if hasattr(dbcsi_result, 'workload_profiles') and dbcsi_result.workload_profiles:
            metrics['top_workload_profiles'] = self._get_top_workloads(
                dbcsi_result.workload_profiles
            )
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """값을 정수로 파싱"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _get_top_wait_events(self, wait_events: List[Any]) -> List[Dict[str, Any]]:
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
    
    def _get_features_used(self, features: List[Any]) -> List[Dict[str, Any]]:
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
    
    def _get_cpu_percentiles(self, percentile_cpu: Dict[str, Any]) -> Dict[str, Any]:
        """CPU 백분위수 추출"""
        result = {}
        for metric_name, data in percentile_cpu.items():
            result[metric_name] = {
                'on_cpu': data.on_cpu if hasattr(data, 'on_cpu') else None,
                'on_cpu_and_resmgr': (
                    data.on_cpu_and_resmgr if hasattr(data, 'on_cpu_and_resmgr') else None
                )
            }
        return result
    
    def _get_io_percentiles(self, percentile_io: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _calc_avg_hit_ratio(self, buffer_cache_stats: List[Any]) -> Optional[float]:
        """버퍼 캐시 평균 Hit Ratio 계산"""
        hit_ratios = [
            s.hit_ratio for s in buffer_cache_stats 
            if hasattr(s, 'hit_ratio') and s.hit_ratio is not None
        ]
        return sum(hit_ratios) / len(hit_ratios) if hit_ratios else None
    
    def _get_top_workloads(self, workload_profiles: List[Any]) -> List[Dict[str, Any]]:
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
