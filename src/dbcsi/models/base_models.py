"""
기본 데이터 모델

Statspack 기본 데이터 구조를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


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
    # 추가 PL/SQL 오브젝트
    count_triggers: Optional[int] = None
    count_types: Optional[int] = None
    count_type_bodies: Optional[int] = None
    # 추가 스키마 오브젝트
    count_views: Optional[int] = None
    count_indexes: Optional[int] = None
    count_sequences: Optional[int] = None
    count_lobs: Optional[int] = None
    count_materialized_views: Optional[int] = None
    count_db_links: Optional[int] = None
    # 기타
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
    estd_db_time_factor: float  # AWR에서 소수점 값 (예: 0.4188)
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
