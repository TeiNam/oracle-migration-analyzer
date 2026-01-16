"""
마이그레이션 추천 시스템 데이터 모델

통합 분석 결과, 메트릭, 추천 결과 등의 데이터 구조를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class MigrationStrategy(Enum):
    """마이그레이션 전략"""
    REPLATFORM = "replatform"  # RDS for Oracle SE2
    REFACTOR_MYSQL = "refactor_mysql"  # Aurora MySQL
    REFACTOR_POSTGRESQL = "refactor_postgresql"  # Aurora PostgreSQL


@dataclass
class AnalysisMetrics:
    """추출된 분석 메트릭
    
    Requirements 1.1, 1.4, 1.5, 1.6, 11.1, 11.2, 11.3, 12.1, 12.2를 구현합니다.
    """
    # 성능 메트릭 (Requirements 11.1, 11.2, 11.3)
    avg_cpu_usage: float
    avg_io_load: float
    avg_memory_usage: float
    
    # 코드 복잡도 메트릭 (Requirements 1.4, 1.5)
    avg_sql_complexity: float
    avg_plsql_complexity: float
    
    # 복잡도 분포 (Requirements 12.1, 12.2)
    high_complexity_sql_count: int  # 7.0 이상
    high_complexity_plsql_count: int  # 7.0 이상
    total_sql_count: int
    total_plsql_count: int
    high_complexity_ratio: float  # 복잡도 7.0 이상 비율
    
    # BULK 연산 (Requirements 1.6)
    bulk_operation_count: int
    
    # RAC 정보 (참고용, 의사결정에 미사용)
    rac_detected: bool
    
    # AWR/Statspack PL/SQL 통계 (데이터베이스에 실제 존재하는 오브젝트)
    awr_plsql_lines: Optional[int] = None
    awr_procedure_count: Optional[int] = None
    awr_function_count: Optional[int] = None
    awr_package_count: Optional[int] = None


@dataclass
class IntegratedAnalysisResult:
    """통합 분석 결과
    
    Requirements 1.1을 구현합니다.
    DBCSI와 SQL/PL-SQL 분석 결과를 통합하여 저장합니다.
    """
    # DBCSI 분석 결과 (StatspackData 또는 AWRData)
    dbcsi_result: Optional[Any]  # Union[StatspackData, AWRData]
    
    # SQL/PL-SQL 분석 결과
    sql_analysis: List[Any]  # List[SQLAnalysisResult]
    plsql_analysis: List[Any]  # List[PLSQLAnalysisResult]
    
    # 추출된 메트릭
    metrics: AnalysisMetrics
    
    # 분석 타임스탬프
    analysis_timestamp: str


@dataclass
class Rationale:
    """추천 근거
    
    Requirements 5.1, 5.2, 5.3, 5.4, 5.5를 구현합니다.
    """
    category: str  # "performance", "complexity", "cost", "operations"
    reason: str
    supporting_data: Dict[str, Any]


@dataclass
class AlternativeStrategy:
    """대안 전략
    
    Requirements 6.1, 6.2, 6.3, 6.4를 구현합니다.
    """
    strategy: MigrationStrategy
    pros: List[str]
    cons: List[str]
    considerations: List[str]


@dataclass
class Risk:
    """위험 요소
    
    Requirements 7.1, 7.2, 7.3, 7.4, 7.5를 구현합니다.
    """
    category: str  # "technical", "operational", "performance"
    description: str
    severity: str  # "high", "medium", "low"
    mitigation: str


@dataclass
class RoadmapPhase:
    """로드맵 단계
    
    Requirements 8.2, 8.3, 8.4를 구현합니다.
    """
    phase_number: int
    phase_name: str
    tasks: List[str]
    estimated_duration: str
    required_resources: List[str]


@dataclass
class MigrationRoadmap:
    """마이그레이션 로드맵
    
    Requirements 8.1을 구현합니다.
    """
    phases: List[RoadmapPhase]
    total_estimated_duration: str
    ai_assisted: bool = True  # AI 도구 활용 여부 (기본값: True)
    ai_time_saving_pct: float = 40.0  # AI 활용 시 시간 절감률 (기본값: 40%)
    ai_cost_saving_pct: float = 35.0  # AI 활용 시 비용 절감률 (기본값: 35%)


@dataclass
class InstanceRecommendation:
    """인스턴스 추천
    
    Requirements 11.4, 11.5, 11.6을 구현합니다.
    """
    instance_type: str  # 예: "db.r6i.xlarge"
    vcpu: int
    memory_gb: int
    rationale: str  # 추천 근거


@dataclass
class ExecutiveSummary:
    """Executive Summary
    
    Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6을 구현합니다.
    """
    recommended_strategy: str
    estimated_duration: str
    key_benefits: List[str]
    key_risks: List[str]
    summary_text: str  # 1페이지 이내


@dataclass
class MigrationRecommendation:
    """마이그레이션 추천 결과
    
    Requirements 5.1, 6.1, 7.1, 8.1, 11.6, 13.1을 구현합니다.
    """
    # 추천 전략
    recommended_strategy: MigrationStrategy
    confidence_level: str  # "high", "medium", "low"
    
    # 추천 근거 (Requirements 5.1)
    rationales: List[Rationale]
    
    # 대안 전략 (Requirements 6.1)
    alternative_strategies: List[AlternativeStrategy]
    
    # 위험 요소 (Requirements 7.1)
    risks: List[Risk]
    
    # 마이그레이션 로드맵 (Requirements 8.1)
    roadmap: MigrationRoadmap
    
    # Executive Summary (Requirements 13.1)
    executive_summary: ExecutiveSummary
    
    # 인스턴스 추천 (Requirements 11.6)
    instance_recommendation: Optional[InstanceRecommendation] = None
    
    # 분석 메트릭 (참조용)
    metrics: AnalysisMetrics = field(default=None)
