"""
마이그레이션 관련 데이터 모델

마이그레이션 분석 및 추천 관련 데이터 구조를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from .enums import TargetDatabase


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
