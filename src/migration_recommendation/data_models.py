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


class ReplatformSubStrategy(Enum):
    """Replatform 세부 전략
    
    Replatform 선택 시 세부 옵션을 구분합니다.
    난이도와 요구사항에 따라 적절한 옵션을 선택합니다.
    """
    RDS_ORACLE = "rds_oracle"  # Amazon RDS for Oracle (관리형, 제약 있음)
    RDS_CUSTOM_ORACLE = "rds_custom_oracle"  # RDS Custom for Oracle (OS 접근 가능)
    EC2_REHOST = "ec2_rehost"  # EC2 Rehost (완전한 제어권, Lift & Shift)


class AnalysisMode(Enum):
    """분석 모드
    
    데이터 가용성에 따른 분석 모드를 정의합니다.
    ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md 참조
    """
    FULL = "full"  # SQL + PL/SQL + DBCSI (신뢰도 95%)
    DB_ONLY = "db_only"  # PL/SQL + DBCSI (신뢰도 80%)
    QUICK = "quick"  # DBCSI만 (신뢰도 60%)
    SQL_ONLY = "sql_only"  # SQL만 (신뢰도 50%)
    PLSQL_ONLY = "plsql_only"  # PL/SQL만 (신뢰도 55%)
    MINIMAL = "minimal"  # 최소 데이터 (신뢰도 40%)


@dataclass
class DataAvailability:
    """데이터 가용성 정보
    
    각 데이터 소스의 포함 여부와 상세 정보를 저장합니다.
    """
    # SQL 분석 데이터
    has_sql: bool = False
    sql_file_count: int = 0
    sql_source: str = ""  # "file", "report", "none"
    
    # PL/SQL 분석 데이터
    has_plsql: bool = False
    plsql_file_count: int = 0
    plsql_source: str = ""  # "file", "report", "awr_estimate", "none"
    
    # DBCSI 데이터
    has_dbcsi: bool = False
    dbcsi_type: str = ""  # "awr", "statspack", "none"
    dbcsi_source: str = ""  # "file", "report", "none"
    
    def get_analysis_mode(self) -> AnalysisMode:
        """데이터 가용성에 따른 분석 모드 결정"""
        if self.has_sql and self.has_plsql and self.has_dbcsi:
            return AnalysisMode.FULL
        elif self.has_plsql and self.has_dbcsi:
            return AnalysisMode.DB_ONLY
        elif self.has_dbcsi and not self.has_sql and not self.has_plsql:
            return AnalysisMode.QUICK
        elif self.has_sql and not self.has_plsql and not self.has_dbcsi:
            return AnalysisMode.SQL_ONLY
        elif self.has_plsql and not self.has_sql and not self.has_dbcsi:
            return AnalysisMode.PLSQL_ONLY
        else:
            return AnalysisMode.MINIMAL


@dataclass
class ConfidenceAssessment:
    """신뢰도 평가 결과
    
    분석 결과의 신뢰도와 그 근거를 저장합니다.
    """
    # 종합 신뢰도 (0-100%)
    overall_confidence: int
    
    # 개별 항목 신뢰도
    sql_complexity_confidence: int  # SQL 복잡도 신뢰도
    plsql_complexity_confidence: int  # PL/SQL 복잡도 신뢰도
    performance_metrics_confidence: int  # 성능 메트릭 신뢰도
    strategy_confidence: int  # 전략 추천 신뢰도
    
    # 분석 모드
    analysis_mode: AnalysisMode
    
    # 신뢰도 근거 (사람이 읽을 수 있는 설명)
    confidence_factors: List[str] = field(default_factory=list)
    
    # 신뢰도 향상 방법
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # 데이터 가용성
    data_availability: Optional[DataAvailability] = None


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
    
    # 최대 복잡도 (Optional)
    max_sql_complexity: Optional[float] = None
    max_plsql_complexity: Optional[float] = None
    
    # MySQL 타겟 복잡도 (PostgreSQL과 비교용)
    avg_sql_complexity_mysql: Optional[float] = None
    avg_plsql_complexity_mysql: Optional[float] = None
    max_sql_complexity_mysql: Optional[float] = None
    max_plsql_complexity_mysql: Optional[float] = None
    
    # MySQL 타겟 고난이도 개수
    high_complexity_sql_count_mysql: Optional[int] = None
    high_complexity_plsql_count_mysql: Optional[int] = None
    total_sql_count_mysql: Optional[int] = None
    total_plsql_count_mysql: Optional[int] = None
    
    # AWR/Statspack PL/SQL 통계 (데이터베이스에 실제 존재하는 오브젝트)
    awr_plsql_lines: Optional[int] = None
    awr_procedure_count: Optional[int] = None
    awr_function_count: Optional[int] = None
    awr_package_count: Optional[int] = None
    awr_trigger_count: Optional[int] = None
    awr_type_count: Optional[int] = None
    
    # === 신규 필드: 데이터베이스 기본 정보 ===
    db_name: Optional[str] = None
    db_version: Optional[str] = None
    platform_name: Optional[str] = None
    character_set: Optional[str] = None
    instance_count: Optional[int] = None
    is_rac: bool = False
    is_rds: Optional[bool] = None
    total_db_size_gb: Optional[float] = None
    physical_memory_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    num_cpus: Optional[int] = None
    
    # === 신규 필드: 오브젝트 통계 ===
    count_schemas: Optional[int] = None
    count_tables: Optional[int] = None
    count_views: Optional[int] = None
    count_indexes: Optional[int] = None
    count_triggers: Optional[int] = None
    count_types: Optional[int] = None
    count_sequences: Optional[int] = None
    count_db_links: Optional[int] = None
    count_materialized_views: Optional[int] = None
    count_lobs: Optional[int] = None
    
    # === 신규 필드: 성능 상세 ===
    avg_read_iops: Optional[float] = None
    avg_write_iops: Optional[float] = None
    avg_read_mbps: Optional[float] = None
    avg_write_mbps: Optional[float] = None
    avg_commits_per_sec: Optional[float] = None
    peak_cpu_usage: Optional[float] = None
    peak_iops: Optional[float] = None
    peak_io_load: Optional[float] = None
    peak_memory_usage: Optional[float] = None
    
    # === 신규 필드: 대기 이벤트 ===
    top_wait_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 신규 필드: Oracle 기능 사용 ===
    oracle_features_used: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 신규 필드: AWR 특화 (Optional) ===
    cpu_percentiles: Optional[Dict[str, Any]] = None
    io_percentiles: Optional[Dict[str, Any]] = None
    buffer_cache_hit_ratio: Optional[float] = None
    top_workload_profiles: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 신규 필드: 리포트 타입 ===
    report_type: Optional[str] = None  # "awr" 또는 "statspack"
    
    # === 신규 필드: SGA 권장사항 (리포트 파싱에서 추출) ===
    current_sga_gb: Optional[float] = None  # 현재 SGA 크기 (GB)
    recommended_sga_gb: Optional[float] = None  # 권장 SGA 크기 (GB)
    
    # === 신규 필드: Oracle 특화 기능 및 외부 의존성 (복잡도 리포트에서 추출) ===
    detected_oracle_features_summary: Dict[str, int] = field(default_factory=dict)  # 기능명: 개수
    detected_external_dependencies_summary: Dict[str, int] = field(default_factory=dict)  # 의존성명: 개수
    conversion_guide: Dict[str, str] = field(default_factory=dict)  # Oracle 기능: 대체 방법


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
    ha_recommendation: Optional[str] = None  # 고가용성 구성 권장사항
    rac_assessment: Optional[str] = None  # RAC 필요성 평가
    
    # SGA 권장사항 기반 인스턴스 추천 (신규)
    sga_based_instance_type: Optional[str] = None
    sga_based_vcpu: Optional[int] = None
    sga_based_memory_gb: Optional[int] = None
    recommended_sga_gb: Optional[float] = None  # 권장 SGA 크기 (GB)
    current_sga_gb: Optional[float] = None  # 현재 SGA 크기 (GB)


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
    metrics: Optional[AnalysisMetrics] = field(default=None)
    
    # 신뢰도 평가 (신규)
    confidence_assessment: Optional[ConfidenceAssessment] = None
    
    # 데이터 가용성 (신규)
    data_availability: Optional[DataAvailability] = None
    
    # Replatform 선택 이유 (신규)
    replatform_reasons: List[str] = field(default_factory=list)
    
    # Replatform 세부 전략 (신규)
    replatform_sub_strategy: Optional[ReplatformSubStrategy] = None
    replatform_sub_strategy_reasons: List[str] = field(default_factory=list)
