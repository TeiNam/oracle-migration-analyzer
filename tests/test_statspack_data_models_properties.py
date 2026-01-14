"""
Statspack 데이터 모델 속성 기반 테스트

Property-based testing을 사용하여 데이터 모델의 정확성을 검증합니다.
"""

import json
from enum import Enum
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest

from src.statspack.data_models import (
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


# Feature: statspack-analyzer, Property 9: JSON Round-trip
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



# Feature: statspack-analyzer, Property 9: JSON Round-trip (MigrationComplexity)
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
