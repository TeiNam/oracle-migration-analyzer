"""
DBCSI 데이터 모델

Statspack/AWR 분석 및 마이그레이션 관련 데이터 구조를 제공합니다.
"""

# Enums
from .enums import OracleEdition, TargetDatabase

# Base models
from .base_models import (
    OSInformation,
    MemoryMetric,
    DiskSize,
    MainMetric,
    WaitEvent,
    SystemStat,
    FeatureUsage,
    SGAAdvice,
    StatspackData
)

# AWR models
from .awr_models import (
    IOStatFunction,
    PercentileCPU,
    PercentileIO,
    WorkloadProfile,
    BufferCacheStats,
    AWRData
)

# Migration models
from .migration_models import (
    InstanceRecommendation,
    MigrationComplexity,
    WorkloadPattern,
    BufferCacheAnalysis,
    IOFunctionAnalysis,
    EnhancedMigrationComplexity
)

# Serialization helpers
from .serialization import (
    statspack_to_dict,
    awr_to_dict,
    dict_to_statspack,
    dict_to_awr,
    migration_complexity_to_dict,
    dict_to_migration_complexity
)

__all__ = [
    # Enums
    'OracleEdition',
    'TargetDatabase',
    # Base models
    'OSInformation',
    'MemoryMetric',
    'DiskSize',
    'MainMetric',
    'WaitEvent',
    'SystemStat',
    'FeatureUsage',
    'SGAAdvice',
    'StatspackData',
    # AWR models
    'IOStatFunction',
    'PercentileCPU',
    'PercentileIO',
    'WorkloadProfile',
    'BufferCacheStats',
    'AWRData',
    # Migration models
    'InstanceRecommendation',
    'MigrationComplexity',
    'WorkloadPattern',
    'BufferCacheAnalysis',
    'IOFunctionAnalysis',
    'EnhancedMigrationComplexity',
    # Serialization
    'statspack_to_dict',
    'awr_to_dict',
    'dict_to_statspack',
    'dict_to_awr',
    'migration_complexity_to_dict',
    'dict_to_migration_complexity'
]
