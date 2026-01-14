"""
Statspack 데이터 모델 정의

타입 안전한 데이터 구조를 제공합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class OracleEdition(Enum):
    """Oracle 데이터베이스 에디션"""
    STANDARD = "Standard Edition"
    STANDARD_2 = "Standard Edition 2"
    ENTERPRISE = "Enterprise Edition"
    EXPRESS = "Express Edition"
    UNKNOWN = "Unknown"


class TargetDatabase(Enum):
    """마이그레이션 타겟 데이터베이스"""
    RDS_ORACLE = "RDS for Oracle"
    AURORA_MYSQL = "Aurora MySQL 8.0"
    AURORA_POSTGRESQL = "Aurora PostgreSQL 16"


@dataclass
class OSInformation:
    """운영체제 및 데이터베이스 기본 정보"""
    statspack_version: Optional[str] = None
    num_cpus: Optional[int] = None
    num_cpu_cores: Optional[int] = None
    physical_memory_gb: Optional[float] = None
    platform_name: Optional[str] = None
    version: Optional[str] = None
    db_name: Optional[str] = None
    dbid: Optional[str] = None
    banner: Optional[str] = None
    instances: Optional[int] = None
    is_rds: Optional[bool] = None
    total_db_size_gb: Optional[float] = None
    count_lines_plsql: Optional[int] = None
    count_schemas: Optional[int] = None
    count_tables: Optional[int] = None
    count_packages: Optional[int] = None
    count_procedures: Optional[int] = None
    count_functions: Optional[int] = None
    character_set: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryMetric:
    """스냅샷별 메모리 사용량"""
    snap_id: int
    instance_number: int
    sga_gb: float
    pga_gb: float
    total_gb: float


@dataclass
class DiskSize:
    """스냅샷별 디스크 크기"""
    snap_id: int
    size_gb: float


@dataclass
class MainMetric:
    """스냅샷별 주요 성능 메트릭"""
    snap: int
    dur_m: float
    end: str
    inst: int
    cpu_per_s: float
    read_iops: float
    read_mb_s: float
    write_iops: float
    write_mb_s: float
    commits_s: float


@dataclass
class WaitEvent:
    """대기 이벤트 정보"""
    snap_id: int
    wait_class: str
    event_name: str
    pctdbt: float
    total_time_s: float


@dataclass
class SystemStat:
    """시스템 통계 정보"""
    snap: int
    cell_flash_hits: int = 0
    read_iops: float = 0.0
    write_iops: float = 0.0
    read_mb: float = 0.0
    read_mb_opt: float = 0.0
    read_nt_iops: float = 0.0
    write_nt_iops: float = 0.0
    read_nt_mb: float = 0.0
    write_nt_mb: float = 0.0
    cell_int_mb: float = 0.0
    cell_int_ss_mb: float = 0.0
    cell_si_save_mb: float = 0.0
    cell_bytes_elig_mb: float = 0.0
    cell_hcc_bytes_mb: float = 0.0
    read_multi_iops: float = 0.0
    read_temp_iops: float = 0.0
    write_temp_iops: float = 0.0
    network_incoming_mb: float = 0.0
    network_outgoing_mb: float = 0.0


@dataclass
class FeatureUsage:
    """Oracle 기능 사용 정보"""
    name: str
    detected_usages: int
    total_samples: int
    currently_used: bool
    aux_count: Optional[float] = None
    last_sample_date: Optional[str] = None
    feature_info: Optional[str] = None


@dataclass
class SGAAdvice:
    """SGA 조정 권장사항"""
    inst_id: int
    sga_size: int
    sga_size_factor: float
    estd_db_time: int
    estd_db_time_factor: int
    estd_physical_reads: int
    sga_target: int


@dataclass
class StatspackData:
    """전체 Statspack 데이터 컨테이너"""
    os_info: OSInformation
    memory_metrics: List[MemoryMetric] = field(default_factory=list)
    disk_sizes: List[DiskSize] = field(default_factory=list)
    main_metrics: List[MainMetric] = field(default_factory=list)
    wait_events: List[WaitEvent] = field(default_factory=list)
    system_stats: List[SystemStat] = field(default_factory=list)
    features: List[FeatureUsage] = field(default_factory=list)
    sga_advice: List[SGAAdvice] = field(default_factory=list)


# AWR 특화 데이터 모델

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


@dataclass
class InstanceRecommendation:
    """RDS 인스턴스 추천 정보"""
    instance_type: str
    vcpu: int
    memory_gib: int
    current_cpu_usage_pct: float
    current_memory_gb: float
    cpu_headroom_pct: float
    memory_headroom_pct: float
    estimated_monthly_cost_usd: Optional[float] = None


@dataclass
class MigrationComplexity:
    """마이그레이션 난이도 분석 결과"""
    target: TargetDatabase
    score: float
    level: str
    factors: Dict[str, float]
    recommendations: List[str]
    warnings: List[str]
    next_steps: List[str]
    instance_recommendation: Optional[InstanceRecommendation] = None


# Enhanced Migration Analyzer 데이터 모델

@dataclass
class WorkloadPattern:
    """워크로드 패턴 분석 결과"""
    pattern_type: str  # "CPU-intensive", "IO-intensive", "Mixed", "Interactive", "Batch"
    cpu_pct: float
    io_pct: float
    peak_hours: List[str]
    main_modules: List[str]
    main_events: List[str]


@dataclass
class BufferCacheAnalysis:
    """버퍼 캐시 분석 결과"""
    avg_hit_ratio: float
    min_hit_ratio: float
    max_hit_ratio: float
    current_size_gb: float
    recommended_size_gb: float
    optimization_needed: bool
    recommendations: List[str]


@dataclass
class IOFunctionAnalysis:
    """I/O 함수별 분석 결과"""
    function_name: str
    avg_mb_per_s: float
    max_mb_per_s: float
    pct_of_total: float
    is_bottleneck: bool
    recommendations: List[str]


@dataclass
class EnhancedMigrationComplexity(MigrationComplexity):
    """확장된 마이그레이션 복잡도 - MigrationComplexity 확장"""
    # 추가 필드
    workload_pattern: Optional[WorkloadPattern] = None
    buffer_cache_analysis: Optional[BufferCacheAnalysis] = None
    io_function_analysis: List[IOFunctionAnalysis] = field(default_factory=list)
    percentile_based: bool = False  # 백분위수 기반 분석 여부
    confidence_level: str = "High"  # "High" (AWR), "Medium" (Statspack)


# JSON 직렬화/역직렬화 헬퍼 함수

def statspack_to_dict(data: StatspackData) -> Dict[str, Any]:
    """StatspackData를 딕셔너리로 변환"""
    from dataclasses import asdict
    return asdict(data)


def awr_to_dict(data: AWRData) -> Dict[str, Any]:
    """AWRData를 딕셔너리로 변환"""
    from dataclasses import asdict
    return asdict(data)


def dict_to_statspack(data_dict: Dict[str, Any]) -> StatspackData:
    """딕셔너리를 StatspackData로 변환"""
    # OS 정보 변환
    os_info_dict = data_dict.get("os_info", {})
    os_info = OSInformation(**os_info_dict) if os_info_dict else OSInformation()
    
    # 메모리 메트릭 변환
    memory_metrics = [
        MemoryMetric(**m) for m in data_dict.get("memory_metrics", [])
    ]
    
    # 디스크 크기 변환
    disk_sizes = [
        DiskSize(**d) for d in data_dict.get("disk_sizes", [])
    ]
    
    # 주요 메트릭 변환
    main_metrics = [
        MainMetric(**m) for m in data_dict.get("main_metrics", [])
    ]
    
    # 대기 이벤트 변환
    wait_events = [
        WaitEvent(**w) for w in data_dict.get("wait_events", [])
    ]
    
    # 시스템 통계 변환
    system_stats = [
        SystemStat(**s) for s in data_dict.get("system_stats", [])
    ]
    
    # 기능 사용 변환
    features = [
        FeatureUsage(**f) for f in data_dict.get("features", [])
    ]
    
    # SGA 권장사항 변환
    sga_advice = [
        SGAAdvice(**s) for s in data_dict.get("sga_advice", [])
    ]
    
    return StatspackData(
        os_info=os_info,
        memory_metrics=memory_metrics,
        disk_sizes=disk_sizes,
        main_metrics=main_metrics,
        wait_events=wait_events,
        system_stats=system_stats,
        features=features,
        sga_advice=sga_advice
    )


def dict_to_awr(data_dict: Dict[str, Any]) -> AWRData:
    """딕셔너리를 AWRData로 변환"""
    # OS 정보 변환
    os_info_dict = data_dict.get("os_info", {})
    os_info = OSInformation(**os_info_dict) if os_info_dict else OSInformation()
    
    # 메모리 메트릭 변환
    memory_metrics = [
        MemoryMetric(**m) for m in data_dict.get("memory_metrics", [])
    ]
    
    # 디스크 크기 변환
    disk_sizes = [
        DiskSize(**d) for d in data_dict.get("disk_sizes", [])
    ]
    
    # 주요 메트릭 변환
    main_metrics = [
        MainMetric(**m) for m in data_dict.get("main_metrics", [])
    ]
    
    # 대기 이벤트 변환
    wait_events = [
        WaitEvent(**w) for w in data_dict.get("wait_events", [])
    ]
    
    # 시스템 통계 변환
    system_stats = [
        SystemStat(**s) for s in data_dict.get("system_stats", [])
    ]
    
    # 기능 사용 변환
    features = [
        FeatureUsage(**f) for f in data_dict.get("features", [])
    ]
    
    # SGA 권장사항 변환
    sga_advice = [
        SGAAdvice(**s) for s in data_dict.get("sga_advice", [])
    ]
    
    # AWR 특화 필드 변환
    iostat_functions = [
        IOStatFunction(**io) for io in data_dict.get("iostat_functions", [])
    ]
    
    percentile_cpu = {
        key: PercentileCPU(**val) 
        for key, val in data_dict.get("percentile_cpu", {}).items()
    }
    
    percentile_io = {
        key: PercentileIO(**val) 
        for key, val in data_dict.get("percentile_io", {}).items()
    }
    
    workload_profiles = [
        WorkloadProfile(**w) for w in data_dict.get("workload_profiles", [])
    ]
    
    buffer_cache_stats = [
        BufferCacheStats(**b) for b in data_dict.get("buffer_cache_stats", [])
    ]
    
    return AWRData(
        os_info=os_info,
        memory_metrics=memory_metrics,
        disk_sizes=disk_sizes,
        main_metrics=main_metrics,
        wait_events=wait_events,
        system_stats=system_stats,
        features=features,
        sga_advice=sga_advice,
        iostat_functions=iostat_functions,
        percentile_cpu=percentile_cpu,
        percentile_io=percentile_io,
        workload_profiles=workload_profiles,
        buffer_cache_stats=buffer_cache_stats
    )


def migration_complexity_to_dict(complexity: MigrationComplexity) -> Dict[str, Any]:
    """MigrationComplexity를 딕셔너리로 변환"""
    from dataclasses import asdict
    result = asdict(complexity)
    # Enum을 문자열로 변환
    result["target"] = complexity.target.value
    return result


def dict_to_migration_complexity(data_dict: Dict[str, Any]) -> MigrationComplexity:
    """딕셔너리를 MigrationComplexity로 변환"""
    # 타겟 데이터베이스 변환
    target_str = data_dict.get("target", "")
    target = None
    for t in TargetDatabase:
        if t.value == target_str:
            target = t
            break
    if target is None:
        target = TargetDatabase.RDS_ORACLE
    
    # 인스턴스 추천 변환
    instance_rec_dict = data_dict.get("instance_recommendation")
    instance_rec = None
    if instance_rec_dict:
        instance_rec = InstanceRecommendation(**instance_rec_dict)
    
    return MigrationComplexity(
        target=target,
        score=data_dict.get("score", 0.0),
        level=data_dict.get("level", ""),
        factors=data_dict.get("factors", {}),
        recommendations=data_dict.get("recommendations", []),
        warnings=data_dict.get("warnings", []),
        next_steps=data_dict.get("next_steps", []),
        instance_recommendation=instance_rec
    )
