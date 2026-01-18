"""
AWR 특화 데이터 모델

AWR 리포트 전용 데이터 구조를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from .base_models import StatspackData


@dataclass
class IOStatFunction:
    """함수별 I/O 통계"""
    snap_id: int
    function_name: str  # "LGWR", "DBWR", "Direct Writes", "Direct Reads", "Others"
    megabytes_per_s: float


@dataclass
class PercentileCPU:
    """CPU 백분위수 통계"""
    metric: str  # "Maximum_or_peak", "99th_percentile", "95th_percentile", etc.
    instance_number: Optional[int]
    on_cpu: int
    on_cpu_and_resmgr: int
    resmgr_cpu_quantum: int
    begin_interval: str
    end_interval: str
    snap_shots: int
    days: float
    avg_snaps_per_day: float


@dataclass
class PercentileIO:
    """I/O 백분위수 통계"""
    metric: str  # "Maximum_or_peak", "99th_percentile", "95th_percentile", etc.
    instance_number: Optional[int]
    rw_iops: int
    r_iops: int
    w_iops: int
    rw_mbps: int
    r_mbps: int
    w_mbps: int
    begin_interval: str
    end_interval: str
    snap_shots: int
    days: float
    avg_snaps_per_day: float


@dataclass
class WorkloadProfile:
    """워크로드 프로파일"""
    sample_start: str
    topn: int
    module: str
    program: str
    event: str
    total_dbtime_sum: int
    aas_comp: float
    aas_contribution_pct: float
    tot_contributions: int
    session_type: str  # "FOREGROUND" or "BACKGROUND"
    wait_class: str
    delta_read_io_requests: int
    delta_write_io_requests: int
    delta_read_io_bytes: int
    delta_write_io_bytes: int


@dataclass
class BufferCacheStats:
    """버퍼 캐시 통계"""
    snap_id: int
    instance_number: int
    block_size: int
    db_cache_gb: float
    dsk_reads: int
    block_gets: int
    consistent: int
    buf_got_gb: float
    hit_ratio: float


@dataclass
class AWRData(StatspackData):
    """AWR 데이터 - StatspackData를 확장"""
    # AWR 특화 필드
    iostat_functions: List[IOStatFunction] = field(default_factory=list)
    percentile_cpu: Dict[str, PercentileCPU] = field(default_factory=dict)  # key: metric name
    percentile_io: Dict[str, PercentileIO] = field(default_factory=dict)  # key: metric name
    workload_profiles: List[WorkloadProfile] = field(default_factory=list)
    buffer_cache_stats: List[BufferCacheStats] = field(default_factory=list)
    
    def is_awr(self) -> bool:
        """AWR 데이터인지 확인"""
        return (len(self.iostat_functions) > 0 or 
                len(self.percentile_cpu) > 0 or 
                len(self.percentile_io) > 0 or 
                len(self.workload_profiles) > 0 or 
                len(self.buffer_cache_stats) > 0)
