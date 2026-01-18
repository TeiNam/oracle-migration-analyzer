"""
데이터 모델 정의 모듈

분석 결과를 담는 데이터 클래스들을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union
from datetime import datetime

# Enum 클래스들을 enums 모듈에서 import
from .enums import TargetDatabase, ComplexityLevel, PLSQLObjectType


@dataclass
class SQLAnalysisResult:
    """SQL 쿼리 분석 결과를 담는 데이터 클래스
    
    Requirements 13.1, 13.3, 13.4를 구현합니다.
    - 13.1: SQL 분석 시 6가지 세부 점수 제공
    - 13.3: 감지된 Oracle 특화 기능 목록 반환
    - 13.4: 감지된 Oracle 특화 함수 목록 반환
    """
    
    # 입력 정보
    query: str
    target_database: TargetDatabase
    
    # 복잡도 점수
    total_score: float
    normalized_score: float
    complexity_level: ComplexityLevel
    recommendation: str
    
    # 세부 점수 (Requirements 13.1)
    structural_complexity: float
    oracle_specific_features: float
    functions_expressions: float
    data_volume: float
    execution_complexity: float
    conversion_difficulty: float
    
    # 감지된 요소 (Requirements 13.3, 13.4)
    detected_oracle_features: List[str] = field(default_factory=list)
    detected_oracle_functions: List[str] = field(default_factory=list)
    detected_hints: List[str] = field(default_factory=list)
    
    # 분석 메타데이터
    join_count: int = 0
    subquery_depth: int = 0
    cte_count: int = 0
    set_operators_count: int = 0
    
    # 변환 가이드
    conversion_guides: Dict[str, str] = field(default_factory=dict)


@dataclass
class PLSQLAnalysisResult:
    """PL/SQL 오브젝트 분석 결과를 담는 데이터 클래스
    
    Requirements 13.2, 13.3, 13.4를 구현합니다.
    - 13.2: PL/SQL 분석 시 5-7가지 세부 점수 제공
    - 13.3: 감지된 Oracle 특화 기능 목록 반환
    - 13.4: 감지된 외부 의존성 목록 반환
    """
    
    # 입력 정보
    code: str
    object_type: PLSQLObjectType
    target_database: TargetDatabase
    
    # 복잡도 점수
    total_score: float
    normalized_score: float
    complexity_level: ComplexityLevel
    recommendation: str
    
    # 세부 점수 (Requirements 13.2)
    base_score: float
    code_complexity: float
    oracle_features: float
    business_logic: float
    conversion_difficulty: float
    mysql_constraints: float = 0.0  # MySQL 타겟만
    app_migration_penalty: float = 0.0  # MySQL 타겟만
    
    # 감지된 요소 (Requirements 13.3, 13.4)
    detected_oracle_features: List[str] = field(default_factory=list)
    detected_external_dependencies: List[str] = field(default_factory=list)
    
    # 분석 메타데이터
    line_count: int = 0
    cursor_count: int = 0
    exception_blocks: int = 0
    nesting_depth: int = 0
    bulk_operations_count: int = 0
    dynamic_sql_count: int = 0
    
    # 변환 가이드
    conversion_guides: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchAnalysisResult:
    """배치 분석 결과를 담는 데이터 클래스
    
    폴더 내 여러 파일을 일괄 분석한 결과를 집계합니다.
    
    Requirements:
    - 전체: 배치 분석 결과 집계
    
    Attributes:
        total_files: 전체 파일 수
        success_count: 분석 성공한 파일 수
        failure_count: 분석 실패한 파일 수
        complexity_distribution: 복잡도 레벨별 파일 분포
        average_score: 평균 복잡도 점수
        results: 개별 파일 분석 결과 리스트
        failed_files: 실패한 파일 목록 (파일명: 에러 메시지)
        target_database: 타겟 데이터베이스
        analysis_time: 분석 시작 시간
    """
    
    # 집계 정보
    total_files: int
    success_count: int
    failure_count: int
    
    # 복잡도 분포 (레벨명: 파일 수)
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    
    # 평균 점수
    average_score: float = 0.0
    
    # 개별 결과 (파일명: 분석 결과)
    results: Dict[str, Union[SQLAnalysisResult, PLSQLAnalysisResult]] = field(default_factory=dict)
    
    # 실패한 파일 (파일명: 에러 메시지)
    failed_files: Dict[str, str] = field(default_factory=dict)
    
    # 메타데이터
    target_database: TargetDatabase = TargetDatabase.POSTGRESQL
    analysis_time: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))


@dataclass
class WeightConfig:
    """타겟 DB별 가중치 설정을 담는 데이터 클래스
    
    Requirements 3.1, 3.2를 구현합니다.
    - 3.1: PostgreSQL 타겟에서 Oracle 특화 함수 점수 계산
    - 3.2: MySQL 타겟에서 Oracle 특화 함수 점수 계산 및 추가 페널티
    
    각 타겟 데이터베이스별로 복잡도 계산에 사용되는 가중치와 임계값을 정의합니다.
    """
    
    # 구조적 복잡성 최대 점수
    max_structural: float
    
    # JOIN 점수 임계값 [(count, score), ...]
    join_thresholds: List[tuple]
    
    # 서브쿼리 점수 임계값 [(depth, score), ...]
    subquery_thresholds: List[tuple]
    
    # CTE 계수 및 최대값
    cte_coefficient: float
    cte_max: float
    
    # 집합 연산자 계수 및 최대값
    set_operator_coefficient: float
    set_operator_max: float
    
    # 풀스캔 페널티 (MySQL만)
    fullscan_penalty: float = 0.0
    
    # 데이터 볼륨 점수
    data_volume_scores: Dict[str, float] = field(default_factory=dict)
    
    # 실행 복잡성 점수
    execution_scores: Dict[str, float] = field(default_factory=dict)
    
    # 최대 점수 (정규화용)
    max_total_score: float = 0.0

