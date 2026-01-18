"""
AWR 파서 모듈

AWR 파일을 파싱하여 Statspack 데이터에 추가로 AWR 특화 섹션을 분석합니다.
"""

from typing import List, Dict

from .statspack_parser import StatspackParser
from ..logging_config import get_logger

logger = get_logger("parser.awr")


class AWRParser(StatspackParser):
    """
    AWR 파일 파서 - Statspack 파서를 확장
    
    AWR 특화 섹션(IOSTAT-FUNCTION, PERCENT-CPU, PERCENT-IO, WORKLOAD, BUFFER-CACHE)을
    추가로 파싱하여 더 상세한 성능 분석을 제공합니다.
    """
    
    def parse(self):
        """
        전체 파일을 파싱하여 AWRData 반환
        
        Returns:
            AWRData: 파싱된 AWR 데이터 (Statspack 데이터 포함)
            
        Raises:
            StatspackParseError: 파싱 실패 시
        """
        from ..models import AWRData
        
        # 기본 Statspack 섹션 파싱
        statspack_data = super().parse()
        
        # 파일 다시 읽기 (AWR 특화 섹션용)
        lines = self._read_file()
        
        # AWR 특화 섹션 파싱
        iostat_functions = self._parse_iostat_function(lines)
        percentile_cpu = self._parse_percentile_cpu(lines)
        percentile_io = self._parse_percentile_io(lines)
        workload_profiles = self._parse_workload(lines)
        buffer_cache_stats = self._parse_buffer_cache(lines)
        
        awr_data = AWRData(
            os_info=statspack_data.os_info,
            memory_metrics=statspack_data.memory_metrics,
            disk_sizes=statspack_data.disk_sizes,
            main_metrics=statspack_data.main_metrics,
            wait_events=statspack_data.wait_events,
            system_stats=statspack_data.system_stats,
            features=statspack_data.features,
            sga_advice=statspack_data.sga_advice,
            iostat_functions=iostat_functions,
            percentile_cpu=percentile_cpu,
            percentile_io=percentile_io,
            workload_profiles=workload_profiles,
            buffer_cache_stats=buffer_cache_stats
        )
        
        logger.info(f"AWR parsing complete. AWR-specific sections found: {awr_data.is_awr()}")
        return awr_data
    
    def _parse_iostat_function(self, lines: List[str]) -> List:
        """IOSTAT-FUNCTION 섹션 파싱"""
        from ..models import IOStatFunction
        
        section_lines = self._extract_section(lines, "IOSTAT-FUNCTION")
        iostat_functions = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 3:
                try:
                    snap_id = int(parts[0])
                    megabytes_per_s = float(parts[-1])
                    function_name = ' '.join(parts[1:-1])
                    
                    iostat_functions.append(IOStatFunction(
                        snap_id=snap_id,
                        function_name=function_name,
                        megabytes_per_s=megabytes_per_s
                    ))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse IOSTAT-FUNCTION line: {stripped} - {e}")
                    continue
        
        logger.info(f"Parsed {len(iostat_functions)} IOSTAT-FUNCTION records")
        return iostat_functions
    
    def _parse_percentile_cpu(self, lines: List[str]) -> Dict:
        """PERCENT-CPU 섹션 파싱"""
        from ..models import PercentileCPU
        
        section_lines = self._extract_section(lines, "PERCENT-CPU")
        percentile_cpu = {}
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            # DBID ORDER_BY METRIC [INSTANCE_NUMBER] ON_CPU ON_CPU_AND_RESMGR RESMGR_CPU_QUANTUM 
            # BEGIN_DATE BEGIN_TIME END_DATE END_TIME SNAP_SHOTS DAYS AVG_SNAPS_PER_DAY
            # 최소 13개 필드 필요 (INSTANCE_NUMBER 없는 경우)
            if len(parts) < 13:
                continue
            
            try:
                # DBID는 parts[0], ORDER_BY는 parts[1]
                metric = parts[2]
                
                # INSTANCE_NUMBER가 있는지 확인 (숫자인지 체크)
                try:
                    instance_number = int(parts[3])
                    field_offset = 4
                except ValueError:
                    instance_number = None
                    field_offset = 3
                
                on_cpu = int(parts[field_offset])
                on_cpu_and_resmgr = int(parts[field_offset + 1])
                resmgr_cpu_quantum = int(parts[field_offset + 2])
                begin_interval = f"{parts[field_offset + 3]} {parts[field_offset + 4]}"
                end_interval = f"{parts[field_offset + 5]} {parts[field_offset + 6]}"
                snap_shots = int(parts[field_offset + 7])
                days = float(parts[field_offset + 8])
                avg_snaps_per_day = float(parts[field_offset + 9])
                
                key = f"{metric}_{instance_number}" if instance_number else metric
                
                if key not in percentile_cpu:
                    percentile_cpu[key] = PercentileCPU(
                        metric=metric,
                        instance_number=instance_number,
                        on_cpu=on_cpu,
                        on_cpu_and_resmgr=on_cpu_and_resmgr,
                        resmgr_cpu_quantum=resmgr_cpu_quantum,
                        begin_interval=begin_interval,
                        end_interval=end_interval,
                        snap_shots=snap_shots,
                        days=days,
                        avg_snaps_per_day=avg_snaps_per_day
                    )
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping PERCENT-CPU line: {e}")
                continue
        
        logger.info(f"Parsed {len(percentile_cpu)} PERCENT-CPU records")
        return percentile_cpu
    
    def _parse_percentile_io(self, lines: List[str]) -> Dict:
        """PERCENT-IO 섹션 파싱"""
        from ..models import PercentileIO
        
        section_lines = self._extract_section(lines, "PERCENT-IO")
        percentile_io = {}
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            # DBID METRIC [INSTANCE_NUMBER] RW_IOPS R_IOPS W_IOPS RW_MBPS R_MBPS W_MBPS 
            # BEGIN_DATE BEGIN_TIME END_DATE END_TIME SNAP_SHOTS DAYS AVG_SNAPS_PER_DAY
            # 최소 14개 필드 필요 (INSTANCE_NUMBER 없는 경우)
            if len(parts) < 14:
                continue
            
            try:
                # DBID는 parts[0]
                metric = parts[1]
                
                # INSTANCE_NUMBER가 있는지 확인 (숫자인지 체크)
                try:
                    instance_number = int(parts[2])
                    field_offset = 3
                except ValueError:
                    instance_number = None
                    field_offset = 2
                
                rw_iops = int(parts[field_offset])
                r_iops = int(parts[field_offset + 1])
                w_iops = int(parts[field_offset + 2])
                rw_mbps = int(parts[field_offset + 3])
                r_mbps = int(parts[field_offset + 4])
                w_mbps = int(parts[field_offset + 5])
                begin_interval = f"{parts[field_offset + 6]} {parts[field_offset + 7]}"
                end_interval = f"{parts[field_offset + 8]} {parts[field_offset + 9]}"
                snap_shots = int(parts[field_offset + 10])
                days = float(parts[field_offset + 11])
                avg_snaps_per_day = float(parts[field_offset + 12])
                
                key = f"{metric}_{instance_number}" if instance_number else metric
                
                if key not in percentile_io:
                    percentile_io[key] = PercentileIO(
                        metric=metric,
                        instance_number=instance_number,
                        rw_iops=rw_iops,
                        r_iops=r_iops,
                        w_iops=w_iops,
                        rw_mbps=rw_mbps,
                        r_mbps=r_mbps,
                        w_mbps=w_mbps,
                        begin_interval=begin_interval,
                        end_interval=end_interval,
                        snap_shots=snap_shots,
                        days=days,
                        avg_snaps_per_day=avg_snaps_per_day
                    )
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping PERCENT-IO line: {e}")
                continue
        
        logger.info(f"Parsed {len(percentile_io)} PERCENT-IO records")
        return percentile_io
    
    def _parse_workload(self, lines: List[str]) -> List:
        """WORKLOAD 섹션 파싱"""
        from ..models import WorkloadProfile
        
        section_lines = self._extract_section(lines, "WORKLOAD")
        workload_profiles = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            try:
                if len(line) < 235:
                    logger.warning(f"WORKLOAD line too short: {len(line)} chars")
                    continue
                
                # 고정 위치에서 필드 추출
                sample_start = line[0:23].strip()
                topn_str = line[23:39].strip()
                module = line[39:104].strip()
                program = line[104:169].strip()
                event = line[169:234].strip()
                
                remaining = line[234:].strip()
                if not remaining:
                    logger.warning(f"No numeric fields found in WORKLOAD line")
                    continue
                
                parts = remaining.split()
                
                if len(parts) < 14:
                    logger.warning(f"Not enough numeric fields: {len(parts)} < 14")
                    continue
                
                total_dbtime_sum = int(parts[0])
                aas_comp = float(parts[1])
                aas_contribution_pct = float(parts[2])
                tot_contributions = int(parts[3])
                session_type = parts[4]
                
                # wait_class는 선택적이며 공백을 포함할 수 있음 (예: "User I/O", "Network")
                # 다음 필드가 숫자인지 확인하여 wait_class 존재 여부 판단
                offset = 5
                wait_class = ""
                
                # parts[5]부터 시작해서 숫자가 나올 때까지 wait_class로 간주
                while offset < len(parts):
                    try:
                        int(parts[offset])
                        # 숫자면 wait_class 끝
                        break
                    except ValueError:
                        # 숫자가 아니면 wait_class의 일부
                        if wait_class:
                            wait_class += " " + parts[offset]
                        else:
                            wait_class = parts[offset]
                        offset += 1
                
                if len(parts) < offset + 4:
                    logger.debug(f"Not enough numeric fields after wait_class: {len(parts)} < {offset + 4}")
                    continue
                
                delta_read_io_requests = int(parts[offset])
                delta_write_io_requests = int(parts[offset + 1])
                delta_read_io_bytes = int(parts[offset + 2])
                delta_write_io_bytes = int(parts[offset + 3])
                
                topn = int(topn_str)
                
                workload_profiles.append(WorkloadProfile(
                    sample_start=sample_start,
                    topn=topn,
                    module=module,
                    program=program,
                    event=event,
                    total_dbtime_sum=total_dbtime_sum,
                    aas_comp=aas_comp,
                    aas_contribution_pct=aas_contribution_pct,
                    tot_contributions=tot_contributions,
                    session_type=session_type,
                    wait_class=wait_class,
                    delta_read_io_requests=delta_read_io_requests,
                    delta_write_io_requests=delta_write_io_requests,
                    delta_read_io_bytes=delta_read_io_bytes,
                    delta_write_io_bytes=delta_write_io_bytes
                ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse WORKLOAD line: {stripped} - {e}")
                continue
        
        logger.info(f"Parsed {len(workload_profiles)} WORKLOAD records")
        return workload_profiles
    
    def _parse_buffer_cache(self, lines: List[str]) -> List:
        """BUFFER-CACHE 섹션 파싱"""
        from ..models import BufferCacheStats
        
        section_lines = self._extract_section(lines, "BUFFER-CACHE")
        buffer_cache_stats = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 9:
                try:
                    buffer_cache_stats.append(BufferCacheStats(
                        snap_id=int(parts[0]),
                        instance_number=int(parts[1]),
                        block_size=int(parts[2]),
                        db_cache_gb=float(parts[3]),
                        dsk_reads=int(parts[4]),
                        block_gets=int(parts[5]),
                        consistent=int(parts[6]),
                        buf_got_gb=float(parts[7]),
                        hit_ratio=float(parts[8])
                    ))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse BUFFER-CACHE line: {stripped} - {e}")
                    continue
        
        logger.info(f"Parsed {len(buffer_cache_stats)} BUFFER-CACHE records")
        return buffer_cache_stats
