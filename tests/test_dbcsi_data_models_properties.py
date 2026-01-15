"""
Statspack 데이터 모델 속성 기반 테스트

Property-based testing을 사용하여 데이터 모델의 정확성을 검증합니다.
"""

import json
from enum import Enum
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest

from src.dbcsi.data_models import (
    OracleEdition,
    TargetDatabase,
    OSInformation,
    MemoryMetric,
    DiskSize,
    MainMetric,
    WaitEvent,
    SystemStat,
    FeatureUsage,
    SGAAdvice,
    StatspackData,
    InstanceRecommendation,
    MigrationComplexity,
    IOStatFunction,
    PercentileCPU,
    PercentileIO,
    WorkloadProfile,
    BufferCacheStats,
    AWRData,
)


# 커스텀 전략 정의
@composite
def os_information_strategy(draw):
    """OSInformation 객체 생성 전략"""
    return OSInformation(
        statspack_version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        num_cpus=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=128))),
        num_cpu_cores=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=128))),
        physical_memory_gb=draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=2048.0))),
        platform_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        db_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        dbid=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        banner=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        instances=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10))),
        is_rds=draw(st.one_of(st.none(), st.booleans())),
        total_db_size_gb=draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=10000.0))),
        count_lines_plsql=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=100000))),
        count_schemas=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        count_tables=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000))),
        count_packages=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        count_procedures=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        count_functions=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        character_set=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        raw_data=draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=0, max_size=50))),
    )


@composite
def memory_metric_strategy(draw):
    """MemoryMetric 객체 생성 전략"""
    return MemoryMetric(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        instance_number=draw(st.integers(min_value=1, max_value=10)),
        sga_gb=draw(st.floats(min_value=0.1, max_value=1024.0)),
        pga_gb=draw(st.floats(min_value=0.1, max_value=512.0)),
        total_gb=draw(st.floats(min_value=0.2, max_value=1536.0)),
    )


@composite
def disk_size_strategy(draw):
    """DiskSize 객체 생성 전략"""
    return DiskSize(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        size_gb=draw(st.floats(min_value=1.0, max_value=100000.0)),
    )


@composite
def main_metric_strategy(draw):
    """MainMetric 객체 생성 전략"""
    return MainMetric(
        snap=draw(st.integers(min_value=1, max_value=10000)),
        dur_m=draw(st.floats(min_value=0.1, max_value=1440.0)),
        end=draw(st.text(min_size=1, max_size=30)),
        inst=draw(st.integers(min_value=1, max_value=10)),
        cpu_per_s=draw(st.floats(min_value=0.0, max_value=100.0)),
        read_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_mb_s=draw(st.floats(min_value=0.0, max_value=10000.0)),
        write_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        write_mb_s=draw(st.floats(min_value=0.0, max_value=10000.0)),
        commits_s=draw(st.floats(min_value=0.0, max_value=10000.0)),
    )


@composite
def wait_event_strategy(draw):
    """WaitEvent 객체 생성 전략"""
    return WaitEvent(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        wait_class=draw(st.text(min_size=1, max_size=30)),
        event_name=draw(st.text(min_size=1, max_size=100)),
        pctdbt=draw(st.floats(min_value=0.0, max_value=200.0)),
        total_time_s=draw(st.floats(min_value=0.0, max_value=100000.0)),
    )


@composite
def system_stat_strategy(draw):
    """SystemStat 객체 생성 전략"""
    return SystemStat(
        snap=draw(st.integers(min_value=1, max_value=10000)),
        cell_flash_hits=draw(st.integers(min_value=0, max_value=1000000)),
        read_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        write_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_mb_opt=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_nt_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        write_nt_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_nt_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        write_nt_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        cell_int_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        cell_int_ss_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        cell_si_save_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        cell_bytes_elig_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        cell_hcc_bytes_mb=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_multi_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        read_temp_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        write_temp_iops=draw(st.floats(min_value=0.0, max_value=100000.0)),
        network_incoming_mb=draw(st.floats(min_value=0.0, max_value=10000.0)),
        network_outgoing_mb=draw(st.floats(min_value=0.0, max_value=10000.0)),
    )


@composite
def feature_usage_strategy(draw):
    """FeatureUsage 객체 생성 전략"""
    return FeatureUsage(
        name=draw(st.text(min_size=1, max_size=100)),
        detected_usages=draw(st.integers(min_value=0, max_value=10000)),
        total_samples=draw(st.integers(min_value=0, max_value=10000)),
        currently_used=draw(st.booleans()),
        aux_count=draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=10000.0))),
        last_sample_date=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        feature_info=draw(st.one_of(st.none(), st.text(min_size=0, max_size=200))),
    )


@composite
def sga_advice_strategy(draw):
    """SGAAdvice 객체 생성 전략"""
    return SGAAdvice(
        inst_id=draw(st.integers(min_value=1, max_value=10)),
        sga_size=draw(st.integers(min_value=100, max_value=100000)),
        sga_size_factor=draw(st.floats(min_value=0.1, max_value=10.0)),
        estd_db_time=draw(st.integers(min_value=0, max_value=1000000)),
        estd_db_time_factor=draw(st.integers(min_value=0, max_value=1000)),
        estd_physical_reads=draw(st.integers(min_value=0, max_value=10000000)),
        sga_target=draw(st.integers(min_value=100, max_value=100000)),
    )


@composite
def statspack_data_strategy(draw):
    """StatspackData 객체 생성 전략"""
    return StatspackData(
        os_info=draw(os_information_strategy()),
        memory_metrics=draw(st.lists(memory_metric_strategy(), min_size=0, max_size=10)),
        disk_sizes=draw(st.lists(disk_size_strategy(), min_size=0, max_size=10)),
        main_metrics=draw(st.lists(main_metric_strategy(), min_size=0, max_size=10)),
        wait_events=draw(st.lists(wait_event_strategy(), min_size=0, max_size=10)),
        system_stats=draw(st.lists(system_stat_strategy(), min_size=0, max_size=10)),
        features=draw(st.lists(feature_usage_strategy(), min_size=0, max_size=10)),
        sga_advice=draw(st.lists(sga_advice_strategy(), min_size=0, max_size=10)),
    )


@composite
def instance_recommendation_strategy(draw):
    """InstanceRecommendation 객체 생성 전략"""
    return InstanceRecommendation(
        instance_type=draw(st.text(min_size=1, max_size=30)),
        vcpu=draw(st.integers(min_value=1, max_value=128)),
        memory_gib=draw(st.integers(min_value=1, max_value=2048)),
        current_cpu_usage_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        current_memory_gb=draw(st.floats(min_value=0.1, max_value=2048.0)),
        cpu_headroom_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory_headroom_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        estimated_monthly_cost_usd=draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=100000.0))),
    )


@composite
def migration_complexity_strategy(draw):
    """MigrationComplexity 객체 생성 전략"""
    return MigrationComplexity(
        target=draw(st.sampled_from(list(TargetDatabase))),
        score=draw(st.floats(min_value=0.0, max_value=10.0)),
        level=draw(st.sampled_from(["매우 간단", "간단", "중간", "복잡", "매우 복잡"])),
        factors=draw(st.dictionaries(st.text(min_size=1, max_size=30), st.floats(min_value=0.0, max_value=10.0))),
        recommendations=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10)),
        warnings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10)),
        next_steps=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10)),
        instance_recommendation=draw(st.one_of(st.none(), instance_recommendation_strategy())),
    )


# AWR 특화 전략 정의

@composite
def iostat_function_strategy(draw):
    """IOStatFunction 객체 생성 전략"""
    function_names = ["LGWR", "DBWR", "Direct Writes", "Direct Reads", "Others"]
    return IOStatFunction(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        function_name=draw(st.sampled_from(function_names)),
        megabytes_per_s=draw(st.floats(min_value=0.0, max_value=1000.0)),
    )


@composite
def percentile_cpu_strategy(draw):
    """PercentileCPU 객체 생성 전략"""
    metrics = ["Maximum_or_peak", "99.99th_percntl", "99.9th_percentl", "99th_percentile", 
               "97th_percentile", "95th_percentile", "90th_percentile", "75th_percentile", 
               "Median", "Average"]
    return PercentileCPU(
        metric=draw(st.sampled_from(metrics)),
        instance_number=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10))),
        on_cpu=draw(st.integers(min_value=1, max_value=128)),
        on_cpu_and_resmgr=draw(st.integers(min_value=1, max_value=128)),
        resmgr_cpu_quantum=draw(st.integers(min_value=0, max_value=100)),
        begin_interval=draw(st.text(min_size=1, max_size=30)),
        end_interval=draw(st.text(min_size=1, max_size=30)),
        snap_shots=draw(st.integers(min_value=1, max_value=1000)),
        days=draw(st.floats(min_value=0.1, max_value=365.0)),
        avg_snaps_per_day=draw(st.floats(min_value=0.1, max_value=100.0)),
    )


@composite
def percentile_io_strategy(draw):
    """PercentileIO 객체 생성 전략"""
    metrics = ["Maximum_or_peak", "99.9th_percentl", "99th_percentile", 
               "97th_percentile", "95th_percentile", "90th_percentile", 
               "75th_percentile", "Median", "Average"]
    return PercentileIO(
        metric=draw(st.sampled_from(metrics)),
        instance_number=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10))),
        rw_iops=draw(st.integers(min_value=0, max_value=100000)),
        r_iops=draw(st.integers(min_value=0, max_value=100000)),
        w_iops=draw(st.integers(min_value=0, max_value=100000)),
        rw_mbps=draw(st.integers(min_value=0, max_value=10000)),
        r_mbps=draw(st.integers(min_value=0, max_value=10000)),
        w_mbps=draw(st.integers(min_value=0, max_value=10000)),
        begin_interval=draw(st.text(min_size=1, max_size=30)),
        end_interval=draw(st.text(min_size=1, max_size=30)),
        snap_shots=draw(st.integers(min_value=1, max_value=1000)),
        days=draw(st.floats(min_value=0.1, max_value=365.0)),
        avg_snaps_per_day=draw(st.floats(min_value=0.1, max_value=100.0)),
    )


@composite
def workload_profile_strategy(draw):
    """WorkloadProfile 객체 생성 전략"""
    session_types = ["FOREGROUND", "BACKGROUND"]
    return WorkloadProfile(
        sample_start=draw(st.text(min_size=1, max_size=30)),
        topn=draw(st.integers(min_value=1, max_value=100)),
        module=draw(st.text(min_size=1, max_size=50)),
        program=draw(st.text(min_size=1, max_size=50)),
        event=draw(st.text(min_size=1, max_size=100)),
        total_dbtime_sum=draw(st.integers(min_value=0, max_value=1000000)),
        aas_comp=draw(st.floats(min_value=0.0, max_value=1000.0)),
        aas_contribution_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        tot_contributions=draw(st.integers(min_value=0, max_value=1000)),
        session_type=draw(st.sampled_from(session_types)),
        wait_class=draw(st.text(min_size=1, max_size=50)),
        delta_read_io_requests=draw(st.integers(min_value=0, max_value=1000000)),
        delta_write_io_requests=draw(st.integers(min_value=0, max_value=1000000)),
        delta_read_io_bytes=draw(st.integers(min_value=0, max_value=10000000000)),
        delta_write_io_bytes=draw(st.integers(min_value=0, max_value=10000000000)),
    )


@composite
def buffer_cache_stats_strategy(draw):
    """BufferCacheStats 객체 생성 전략"""
    return BufferCacheStats(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        instance_number=draw(st.integers(min_value=1, max_value=10)),
        block_size=draw(st.integers(min_value=512, max_value=32768)),
        db_cache_gb=draw(st.floats(min_value=0.1, max_value=1024.0)),
        dsk_reads=draw(st.integers(min_value=0, max_value=10000000)),
        block_gets=draw(st.integers(min_value=0, max_value=10000000)),
        consistent=draw(st.integers(min_value=0, max_value=10000000)),
        buf_got_gb=draw(st.floats(min_value=0.0, max_value=10000.0)),
        hit_ratio=draw(st.floats(min_value=0.0, max_value=100.0)),
    )


@composite
def awr_data_strategy(draw):
    """AWRData 객체 생성 전략"""
    # Statspack 기본 필드
    os_info = draw(os_information_strategy())
    memory_metrics = draw(st.lists(memory_metric_strategy(), min_size=0, max_size=10))
    disk_sizes = draw(st.lists(disk_size_strategy(), min_size=0, max_size=10))
    main_metrics = draw(st.lists(main_metric_strategy(), min_size=0, max_size=10))
    wait_events = draw(st.lists(wait_event_strategy(), min_size=0, max_size=10))
    system_stats = draw(st.lists(system_stat_strategy(), min_size=0, max_size=10))
    features = draw(st.lists(feature_usage_strategy(), min_size=0, max_size=10))
    sga_advice = draw(st.lists(sga_advice_strategy(), min_size=0, max_size=10))
    
    # AWR 특화 필드
    iostat_functions = draw(st.lists(iostat_function_strategy(), min_size=0, max_size=10))
    
    # percentile_cpu는 딕셔너리 (key: metric name)
    cpu_metrics = draw(st.lists(percentile_cpu_strategy(), min_size=0, max_size=5))
    percentile_cpu = {cpu.metric: cpu for cpu in cpu_metrics}
    
    # percentile_io는 딕셔너리 (key: metric name)
    io_metrics = draw(st.lists(percentile_io_strategy(), min_size=0, max_size=5))
    percentile_io = {io.metric: io for io in io_metrics}
    
    workload_profiles = draw(st.lists(workload_profile_strategy(), min_size=0, max_size=10))
    buffer_cache_stats = draw(st.lists(buffer_cache_stats_strategy(), min_size=0, max_size=10))
    
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
        buffer_cache_stats=buffer_cache_stats,
    )


# Feature: dbcsi-analyzer, Property 9: JSON Round-trip
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_9_statspack_data_json_roundtrip(statspack_data):
    """
    Property 9: JSON Round-trip
    
    For any 유효한 StatspackData 객체에 대해, 
    JSON 직렬화 후 역직렬화하면 원본과 동일한 객체가 생성되어야 합니다.
    
    Validates: Requirements 13.4
    """
    # JSON으로 직렬화 (dataclass를 dict로 변환)
    def dataclass_to_dict(obj):
        """dataclass 객체를 딕셔너리로 변환"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_def in obj.__dataclass_fields__.items():
                value = getattr(obj, field_name)
                if isinstance(value, list):
                    result[field_name] = [dataclass_to_dict(item) for item in value]
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = dataclass_to_dict(value)
                elif isinstance(value, Enum):
                    result[field_name] = value.value
                else:
                    result[field_name] = value
            return result
        return obj
    
    serialized = json.dumps(dataclass_to_dict(statspack_data))
    
    # JSON이 유효한지 확인
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert isinstance(parsed, dict)

    
    # 역직렬화 (dict를 dataclass로 변환)
    def dict_to_dataclass(data_dict, cls):
        """딕셔너리를 dataclass 객체로 변환"""
        if not hasattr(cls, '__dataclass_fields__'):
            return data_dict
        
        field_values = {}
        for field_name, field_def in cls.__dataclass_fields__.items():
            if field_name not in data_dict:
                continue
            
            value = data_dict[field_name]
            field_type = field_def.type
            
            # Optional 타입 처리
            if hasattr(field_type, '__origin__') and field_type.__origin__ is type(None) or \
               (hasattr(field_type, '__args__') and type(None) in getattr(field_type, '__args__', [])):
                if value is None:
                    field_values[field_name] = None
                    continue
                # Optional[X]에서 X 추출
                if hasattr(field_type, '__args__'):
                    actual_types = [t for t in field_type.__args__ if t is not type(None)]
                    if actual_types:
                        field_type = actual_types[0]
            
            # List 타입 처리
            if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                item_type = field_type.__args__[0]
                if hasattr(item_type, '__dataclass_fields__'):
                    field_values[field_name] = [dict_to_dataclass(item, item_type) for item in value]
                else:
                    field_values[field_name] = value
            # Dict 타입 처리
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is dict:
                field_values[field_name] = value
            # Enum 타입 처리
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                field_values[field_name] = field_type(value)
            # dataclass 타입 처리
            elif hasattr(field_type, '__dataclass_fields__'):
                field_values[field_name] = dict_to_dataclass(value, field_type)
            else:
                field_values[field_name] = value
        
        return cls(**field_values)
    
    deserialized = dict_to_dataclass(parsed, StatspackData)
    
    # 원본과 역직렬화된 객체가 동일한지 확인
    assert deserialized == statspack_data



# Feature: dbcsi-analyzer, Property 9: JSON Round-trip (MigrationComplexity)
@settings(max_examples=100)
@given(migration_complexity_strategy())
def test_property_9_migration_complexity_json_roundtrip(migration_complexity):
    """
    Property 9: JSON Round-trip (MigrationComplexity)
    
    For any 유효한 MigrationComplexity 객체에 대해, 
    JSON 직렬화 후 역직렬화하면 원본과 동일한 객체가 생성되어야 합니다.
    
    Validates: Requirements 13.4
    """
    # JSON으로 직렬화
    def dataclass_to_dict(obj):
        """dataclass 객체를 딕셔너리로 변환"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_def in obj.__dataclass_fields__.items():
                value = getattr(obj, field_name)
                if isinstance(value, list):
                    result[field_name] = [dataclass_to_dict(item) for item in value]
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = dataclass_to_dict(value)
                elif isinstance(value, Enum):
                    result[field_name] = value.value
                else:
                    result[field_name] = value
            return result
        return obj
    
    serialized = json.dumps(dataclass_to_dict(migration_complexity))
    
    # JSON이 유효한지 확인
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert isinstance(parsed, dict)
    
    # 역직렬화
    def dict_to_dataclass(data_dict, cls):
        """딕셔너리를 dataclass 객체로 변환"""
        if not hasattr(cls, '__dataclass_fields__'):
            return data_dict
        
        field_values = {}
        for field_name, field_def in cls.__dataclass_fields__.items():
            if field_name not in data_dict:
                continue
            
            value = data_dict[field_name]
            field_type = field_def.type

            
            # Optional 타입 처리
            if hasattr(field_type, '__origin__') and field_type.__origin__ is type(None) or \
               (hasattr(field_type, '__args__') and type(None) in getattr(field_type, '__args__', [])):
                if value is None:
                    field_values[field_name] = None
                    continue
                # Optional[X]에서 X 추출
                if hasattr(field_type, '__args__'):
                    actual_types = [t for t in field_type.__args__ if t is not type(None)]
                    if actual_types:
                        field_type = actual_types[0]
            
            # List 타입 처리
            if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                item_type = field_type.__args__[0]
                if hasattr(item_type, '__dataclass_fields__'):
                    field_values[field_name] = [dict_to_dataclass(item, item_type) for item in value]
                else:
                    field_values[field_name] = value
            # Dict 타입 처리
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is dict:
                field_values[field_name] = value
            # Enum 타입 처리
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                field_values[field_name] = field_type(value)
            # dataclass 타입 처리
            elif hasattr(field_type, '__dataclass_fields__'):
                field_values[field_name] = dict_to_dataclass(value, field_type)
            else:
                field_values[field_name] = value
        
        return cls(**field_values)
    
    deserialized = dict_to_dataclass(parsed, MigrationComplexity)
    
    # 원본과 역직렬화된 객체가 동일한지 확인
    assert deserialized == migration_complexity


# Feature: awr-analyzer, Property 11: AWR 데이터 JSON Round-trip
@settings(max_examples=100)
@given(awr_data_strategy())
def test_property_11_awr_data_json_roundtrip(awr_data):
    """
    Property 11: AWR 데이터 JSON Round-trip
    
    For any 유효한 AWRData 객체에 대해, 
    JSON 직렬화 후 역직렬화하면 원본과 동일한 객체가 생성되어야 합니다.
    
    Validates: Requirements 7.4
    """
    # JSON으로 직렬화 (dataclass를 dict로 변환)
    def dataclass_to_dict(obj):
        """dataclass 객체를 딕셔너리로 변환"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_def in obj.__dataclass_fields__.items():
                value = getattr(obj, field_name)
                if isinstance(value, dict):
                    # 딕셔너리의 값이 dataclass인 경우
                    result[field_name] = {k: dataclass_to_dict(v) for k, v in value.items()}
                elif isinstance(value, list):
                    result[field_name] = [dataclass_to_dict(item) for item in value]
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = dataclass_to_dict(value)
                elif isinstance(value, Enum):
                    result[field_name] = value.value
                else:
                    result[field_name] = value
            return result
        return obj
    
    serialized = json.dumps(dataclass_to_dict(awr_data))
    
    # JSON이 유효한지 확인
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert isinstance(parsed, dict)
    
    # 역직렬화 (dict를 dataclass로 변환)
    def dict_to_dataclass(data_dict, cls):
        """딕셔너리를 dataclass 객체로 변환"""
        if not hasattr(cls, '__dataclass_fields__'):
            return data_dict
        
        field_values = {}
        for field_name, field_def in cls.__dataclass_fields__.items():
            if field_name not in data_dict:
                continue
            
            value = data_dict[field_name]
            field_type = field_def.type
            
            # Optional 타입 처리
            if hasattr(field_type, '__origin__') and field_type.__origin__ is type(None) or \
               (hasattr(field_type, '__args__') and type(None) in getattr(field_type, '__args__', [])):
                if value is None:
                    field_values[field_name] = None
                    continue
                # Optional[X]에서 X 추출
                if hasattr(field_type, '__args__'):
                    actual_types = [t for t in field_type.__args__ if t is not type(None)]
                    if actual_types:
                        field_type = actual_types[0]
            
            # Dict 타입 처리 (AWR의 percentile_cpu, percentile_io)
            if hasattr(field_type, '__origin__') and field_type.__origin__ is dict:
                if hasattr(field_type, '__args__') and len(field_type.__args__) >= 2:
                    key_type, val_type = field_type.__args__[0], field_type.__args__[1]
                    if hasattr(val_type, '__dataclass_fields__'):
                        field_values[field_name] = {k: dict_to_dataclass(v, val_type) for k, v in value.items()}
                    else:
                        field_values[field_name] = value
                else:
                    field_values[field_name] = value
            # List 타입 처리
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                item_type = field_type.__args__[0]
                if hasattr(item_type, '__dataclass_fields__'):
                    field_values[field_name] = [dict_to_dataclass(item, item_type) for item in value]
                else:
                    field_values[field_name] = value
            # Enum 타입 처리
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                field_values[field_name] = field_type(value)
            # dataclass 타입 처리
            elif hasattr(field_type, '__dataclass_fields__'):
                field_values[field_name] = dict_to_dataclass(value, field_type)
            else:
                field_values[field_name] = value
        
        return cls(**field_values)
    
    deserialized = dict_to_dataclass(parsed, AWRData)
    
    # 원본과 역직렬화된 객체가 동일한지 확인
    assert deserialized == awr_data
    
    # AWR 특화 필드가 올바르게 복원되었는지 확인
    assert len(deserialized.iostat_functions) == len(awr_data.iostat_functions)
    assert len(deserialized.percentile_cpu) == len(awr_data.percentile_cpu)
    assert len(deserialized.percentile_io) == len(awr_data.percentile_io)
    assert len(deserialized.workload_profiles) == len(awr_data.workload_profiles)
    assert len(deserialized.buffer_cache_stats) == len(awr_data.buffer_cache_stats)
    
    # is_awr() 메서드가 동일한 결과를 반환하는지 확인
    assert deserialized.is_awr() == awr_data.is_awr()
