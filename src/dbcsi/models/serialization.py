"""
직렬화/역직렬화 헬퍼 함수

데이터 모델과 딕셔너리 간 변환 기능을 제공합니다.
"""

from typing import Dict, Any
from dataclasses import asdict

from .base_models import (
    OSInformation, MemoryMetric, DiskSize, MainMetric,
    WaitEvent, SystemStat, FeatureUsage, SGAAdvice, StatspackData
)
from .awr_models import (
    IOStatFunction, PercentileCPU, PercentileIO,
    WorkloadProfile, BufferCacheStats, AWRData
)
from .migration_models import (
    InstanceRecommendation, MigrationComplexity
)
from .enums import TargetDatabase


def statspack_to_dict(data: StatspackData) -> Dict[str, Any]:
    """StatspackData를 딕셔너리로 변환"""
    return asdict(data)


def awr_to_dict(data: AWRData) -> Dict[str, Any]:
    """AWRData를 딕셔너리로 변환"""
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
