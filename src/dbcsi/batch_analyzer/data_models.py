"""
배치 분석 데이터 모델

배치 분석에 사용되는 데이터 클래스들을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union

from ..models import StatspackData, AWRData
from ..migration_analyzer import MigrationComplexity, TargetDatabase


@dataclass
class BatchFileResult:
    """배치 분석 개별 파일 결과"""
    filepath: str
    filename: str
    success: bool
    error_message: Optional[str] = None
    statspack_data: Optional[Union[StatspackData, AWRData]] = None
    migration_analysis: Optional[Dict[TargetDatabase, MigrationComplexity]] = None
    timestamp: Optional[str] = None  # 파일의 타임스탬프 (추세 분석용)


@dataclass
class TrendMetrics:
    """추세 분석 메트릭"""
    metric_name: str
    values: List[float]
    timestamps: List[str]
    avg: float
    min_val: float
    max_val: float
    std_dev: float
    trend: str  # "increasing", "decreasing", "stable"
    change_pct: float  # 첫 값 대비 마지막 값의 변화율


@dataclass
class Anomaly:
    """이상 징후"""
    timestamp: str
    filename: str
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # "low", "medium", "high"
    description: str


@dataclass
class TrendAnalysisResult:
    """추세 분석 결과"""
    cpu_trend: Optional[TrendMetrics] = None
    io_trend: Optional[TrendMetrics] = None
    memory_trend: Optional[TrendMetrics] = None
    buffer_cache_trend: Optional[TrendMetrics] = None
    anomalies: List[Anomaly] = field(default_factory=list)


@dataclass
class BatchAnalysisResult:
    """배치 분석 전체 결과"""
    total_files: int
    successful_files: int
    failed_files: int
    file_results: List[BatchFileResult]
    analysis_timestamp: str
    trend_analysis: Optional[TrendAnalysisResult] = None
