"""
Oracle Complexity Analyzer

Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 
마이그레이션 난이도를 0-10 척도로 평가하는 도구입니다.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict


class TargetDatabase(Enum):
    """타겟 데이터베이스 유형"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class ComplexityLevel(Enum):
    """복잡도 레벨 분류"""
    VERY_SIMPLE = "매우 간단"          # 0-1
    SIMPLE = "간단"                    # 1-3
    MODERATE = "중간"                  # 3-5
    COMPLEX = "복잡"                   # 5-7
    VERY_COMPLEX = "매우 복잡"         # 7-9
    EXTREMELY_COMPLEX = "극도로 복잡"  # 9-10


class PLSQLObjectType(Enum):
    """PL/SQL 오브젝트 타입"""
    PACKAGE = "package"
    PROCEDURE = "procedure"
    FUNCTION = "function"
    TRIGGER = "trigger"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"


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
    ai_difficulty: float
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


# PostgreSQL 가중치 설정
# Requirements 1.1-1.5, 3.1, 5.1-5.4, 6.1-6.5를 반영
POSTGRESQL_WEIGHTS = WeightConfig(
    max_structural=2.5,
    join_thresholds=[
        (0, 0.0),           # 0개 = 0점
        (3, 0.5),           # 1-3개 = 0.5점
        (5, 1.0),           # 4-5개 = 1.0점
        (float('inf'), 1.5) # 6개 이상 = 1.5점
    ],
    subquery_thresholds=[
        (0, 0.0),           # 0 = 0점
        (1, 0.5),           # 1 = 0.5점
        (2, 1.0),           # 2 = 1.0점
        # 3 이상 = 1.5 + min(1, (depth-2)*0.5) - 계산 로직에서 처리
    ],
    cte_coefficient=0.5,
    cte_max=1.0,
    set_operator_coefficient=0.5,
    set_operator_max=1.5,
    fullscan_penalty=0.0,  # PostgreSQL은 풀스캔 페널티 없음
    data_volume_scores={
        'small': 0.5,      # < 200자
        'medium': 1.0,     # 200-500자
        'large': 1.5,      # 500-1000자
        'xlarge': 2.0      # 1000자 이상
    },
    execution_scores={
        'order_by': 0.2,
        'group_by': 0.2,
        'having': 0.2,
        'join_depth': 0.5,  # join_count > 5 또는 subquery_depth > 2
    },
    max_total_score=13.5  # 구조적(2.5) + Oracle특화(3.0) + 함수(2.0) + 볼륨(2.0) + 실행(1.0) + 변환(3.0)
)


# MySQL 가중치 설정
# Requirements 1.1-1.5, 3.2, 5.1-5.4, 6.1-6.7을 반영
MYSQL_WEIGHTS = WeightConfig(
    max_structural=4.5,
    join_thresholds=[
        (0, 0.0),           # 0개 = 0점
        (2, 1.0),           # 1-2개 = 1.0점
        (4, 2.0),           # 3-4개 = 2.0점
        (6, 3.0),           # 5-6개 = 3.0점
        (float('inf'), 4.0) # 7개 이상 = 4.0점
    ],
    subquery_thresholds=[
        (0, 0.0),           # 0 = 0점
        (1, 1.5),           # 1 = 1.5점
        (2, 3.0),           # 2 = 3.0점
        # 3 이상 = 4.0 + min(2, depth-2) - 계산 로직에서 처리
    ],
    cte_coefficient=0.8,
    cte_max=2.0,
    set_operator_coefficient=0.8,
    set_operator_max=2.0,
    fullscan_penalty=1.0,  # MySQL은 WHERE 절 없을 때 1.0점 페널티
    data_volume_scores={
        'small': 0.5,      # < 200자
        'medium': 1.2,     # 200-500자
        'large': 2.0,      # 500-1000자
        'xlarge': 2.5      # 1000자 이상
    },
    execution_scores={
        'order_by': 0.5,
        'group_by': 0.5,
        'having': 0.5,
        'join_depth': 1.5,  # join_count > 3 또는 subquery_depth > 1
        'derived_table': 0.5,  # 파생 테이블당 0.5점 (max 1.0)
        'distinct': 0.3,
        'or_conditions': 0.3,  # OR 조건 3개 이상
        'like_pattern': 0.3,   # LIKE '%문자열%'
        'function_in_where': 0.5,  # WHERE 절에 함수 사용
        'count_no_where': 0.5,  # WHERE 절 없이 COUNT(*) 사용
    },
    max_total_score=18.0  # 구조적(4.5) + Oracle특화(3.0) + 함수(2.5) + 볼륨(2.5) + 실행(2.5) + 변환(3.0)
)


# ============================================================================
# Oracle 특화 기능/함수/힌트 상수 정의
# Requirements 2.1-2.5, 3.1, 7.1을 구현합니다.
# ============================================================================

# Oracle 특화 문법 및 기능 (Requirements 2.1-2.5)
ORACLE_SPECIFIC_SYNTAX = {
    'CONNECT BY': 1.0,          # 계층적 쿼리
    'START WITH': 1.0,          # 계층적 쿼리 시작점
    'PRIOR': 1.0,               # 계층적 쿼리 부모 참조
    'MODEL': 1.0,               # MODEL 절
    'PIVOT': 1.0,               # PIVOT 연산
    'UNPIVOT': 1.0,             # UNPIVOT 연산
    'FLASHBACK': 1.0,           # FLASHBACK 쿼리
    'SYS_CONNECT_BY_PATH': 1.0, # 계층적 경로
    'ROWID': 1.0,               # 물리적 행 주소
    'ROWNUM': 1.0,              # 행 번호
    'LEVEL': 1.0,               # 계층적 레벨
    'MERGE': 1.5,               # MERGE 문
    '(+)': 1.0,                 # OUTER JOIN (구식 문법)
    'NEXTVAL': 0.8,             # 시퀀스 다음 값
    'CURRVAL': 0.8,             # 시퀀스 현재 값
    'RETURNING': 0.8,           # RETURNING 절
    'DUAL': 0.3,                # DUAL 테이블
}

# Oracle 특화 함수 (Requirements 3.1, 3.2)
ORACLE_SPECIFIC_FUNCTIONS = {
    # 조건/변환 함수
    'DECODE': 0.5,              # DECODE 함수
    'NVL': 0.5,                 # NULL 처리
    'NVL2': 0.5,                # NULL 조건부 처리
    
    # 집계 함수
    'LISTAGG': 0.5,             # 문자열 집계
    
    # 정규식 함수
    'REGEXP_LIKE': 0.5,         # 정규식 매칭
    'REGEXP_SUBSTR': 0.5,       # 정규식 부분 문자열
    'REGEXP_REPLACE': 0.5,      # 정규식 치환
    'REGEXP_INSTR': 0.5,        # 정규식 위치
    
    # 시스템 함수
    'SYS_CONTEXT': 0.5,         # 시스템 컨텍스트
    'EXTRACT': 0.5,             # 날짜/시간 추출
    
    # 변환 함수
    'TO_CHAR': 0.5,             # 문자열 변환
    'TO_DATE': 0.5,             # 날짜 변환
    'TO_NUMBER': 0.5,           # 숫자 변환
    'TRUNC': 0.5,               # 절삭
    
    # 날짜 함수
    'ADD_MONTHS': 0.5,          # 월 더하기
    'MONTHS_BETWEEN': 0.5,      # 월 차이
    'NEXT_DAY': 0.5,            # 다음 요일
    'LAST_DAY': 0.5,            # 월 마지막 날
    'SYSDATE': 0.5,             # 시스템 날짜
    'SYSTIMESTAMP': 0.5,        # 시스템 타임스탬프
    'CURRENT_DATE': 0.5,        # 현재 날짜
    
    # 문자열 함수
    'SUBSTR': 0.5,              # 부분 문자열
    'INSTR': 0.5,               # 문자열 위치
    'CHR': 0.5,                 # 문자 코드 변환
    'TRANSLATE': 0.5,           # 문자 치환
}

# 분석 함수 (Requirements 2.2)
ANALYTIC_FUNCTIONS = [
    'ROW_NUMBER',               # 행 번호
    'RANK',                     # 순위 (동일 순위 건너뜀)
    'DENSE_RANK',               # 순위 (동일 순위 연속)
    'LAG',                      # 이전 행 값
    'LEAD',                     # 다음 행 값
    'FIRST_VALUE',              # 첫 번째 값
    'LAST_VALUE',               # 마지막 값
    'NTILE',                    # N분위수
    'CUME_DIST',                # 누적 분포
    'PERCENT_RANK',             # 백분위 순위
    'RATIO_TO_REPORT',          # 비율
]

# 집계 함수 (Requirements 4.1)
AGGREGATE_FUNCTIONS = [
    'COUNT',                    # 개수
    'SUM',                      # 합계
    'AVG',                      # 평균
    'MAX',                      # 최대값
    'MIN',                      # 최소값
    'LISTAGG',                  # 문자열 집계
    'XMLAGG',                   # XML 집계
    'MEDIAN',                   # 중앙값
    'PERCENTILE_CONT',          # 연속 백분위수
    'PERCENTILE_DISC',          # 이산 백분위수
]

# Oracle 힌트 (Requirements 7.1-7.5)
ORACLE_HINTS = [
    'INDEX',                    # 인덱스 사용
    'FULL',                     # 풀 스캔
    'PARALLEL',                 # 병렬 처리
    'USE_HASH',                 # 해시 조인
    'USE_NL',                   # 중첩 루프 조인
    'APPEND',                   # 직접 경로 삽입
    'NO_MERGE',                 # 뷰 병합 방지
    'LEADING',                  # 조인 순서 지정
    'ORDERED',                  # FROM 절 순서대로 조인
    'FIRST_ROWS',               # 첫 행 빠른 반환
    'ALL_ROWS',                 # 전체 처리량 최적화
    'RULE',                     # 규칙 기반 최적화
    'CHOOSE',                   # 옵티마이저 선택
    'DRIVING_SITE',             # DB Link 실행 위치
]

# PL/SQL 고급 기능 (Requirements 9.5)
PLSQL_ADVANCED_FEATURES = [
    'PIPELINED',                # 파이프라인 함수
    'REF CURSOR',               # 커서 변수
    'AUTONOMOUS_TRANSACTION',   # 자율 트랜잭션
    'PRAGMA',                   # 컴파일러 지시어
    'OBJECT TYPE',              # 객체 타입
    'VARRAY',                   # 가변 배열
    'NESTED TABLE',             # 중첩 테이블
]

# 외부 의존성 (Requirements 10.6)
EXTERNAL_DEPENDENCIES = [
    'UTL_FILE',                 # 파일 I/O
    'UTL_HTTP',                 # HTTP 통신
    'UTL_MAIL',                 # 이메일 발송
    'UTL_SMTP',                 # SMTP 통신
    'DBMS_SCHEDULER',           # 스케줄러
    'DBMS_JOB',                 # 작업 스케줄링
    'DBMS_LOB',                 # LOB 처리
    'DBMS_OUTPUT',              # 출력
    'DBMS_CRYPTO',              # 암호화
    'DBMS_SQL',                 # 동적 SQL
]

# PL/SQL 오브젝트 기본 점수 (Requirements 8.1)
PLSQL_BASE_SCORES = {
    TargetDatabase.POSTGRESQL: {
        PLSQLObjectType.PACKAGE: 7.0,
        PLSQLObjectType.PROCEDURE: 5.0,
        PLSQLObjectType.FUNCTION: 4.0,
        PLSQLObjectType.TRIGGER: 6.0,
        PLSQLObjectType.VIEW: 2.0,
        PLSQLObjectType.MATERIALIZED_VIEW: 4.0,
    },
    TargetDatabase.MYSQL: {
        PLSQLObjectType.PACKAGE: 8.0,
        PLSQLObjectType.PROCEDURE: 6.0,
        PLSQLObjectType.FUNCTION: 5.0,
        PLSQLObjectType.TRIGGER: 7.0,
        PLSQLObjectType.VIEW: 2.0,
        PLSQLObjectType.MATERIALIZED_VIEW: 5.0,
    }
}

# MySQL 애플리케이션 이관 페널티 (Requirements 11.4, 11.5)
MYSQL_APP_MIGRATION_PENALTY = {
    PLSQLObjectType.PACKAGE: 2.0,
    PLSQLObjectType.PROCEDURE: 2.0,
    PLSQLObjectType.FUNCTION: 2.0,
    PLSQLObjectType.TRIGGER: 1.5,
    PLSQLObjectType.VIEW: 0.0,
    PLSQLObjectType.MATERIALIZED_VIEW: 0.0,
}


# ============================================================================
# OracleComplexityAnalyzer 메인 클래스
# Requirements 전체를 구현합니다.
# ============================================================================

from datetime import datetime
from pathlib import Path
from typing import Union, Optional
import concurrent.futures
import os


class OracleComplexityAnalyzer:
    """Oracle 복잡도 분석기 메인 클래스
    
    Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의
    마이그레이션 난이도를 0-10 척도로 평가합니다.
    
    Requirements:
    - 전체: 모든 요구사항을 통합하여 구현
    - 14.6, 14.7: 날짜 폴더에 결과 저장
    
    Attributes:
        target: 타겟 데이터베이스 (PostgreSQL 또는 MySQL)
        calculator: 복잡도 계산기
        guide_provider: 변환 가이드 제공자
        output_dir: 출력 디렉토리 경로
    """
    
    def __init__(self, target_database: TargetDatabase = TargetDatabase.POSTGRESQL,
                 output_dir: str = "reports"):
        """OracleComplexityAnalyzer 초기화
        
        Requirements 전체를 구현합니다.
        
        Args:
            target_database: 타겟 데이터베이스 (기본값: PostgreSQL)
            output_dir: 출력 디렉토리 경로 (기본값: "reports")
        """
        self.target = target_database
        self.output_dir = Path(output_dir)
        
        # 필요한 모듈 import (지연 import로 순환 참조 방지)
        from src.calculators.complexity_calculator import ComplexityCalculator
        from src.formatters.conversion_guide_provider import ConversionGuideProvider
        
        self.calculator = ComplexityCalculator(target_database)
        self.guide_provider = ConversionGuideProvider(target_database)
    
    def _get_date_folder(self) -> Path:
        """날짜 폴더 경로 생성 (reports/YYYYMMDD/)
        
        Requirements 14.6, 14.7을 구현합니다.
        - 14.6: reports/YYYYMMDD/ 형식으로 폴더 생성
        - 14.7: 폴더가 없으면 자동 생성
        
        Returns:
            Path: 날짜 폴더 경로 (예: reports/20260114/)
        """
        # 현재 날짜를 YYYYMMDD 형식으로 포맷
        date_str = datetime.now().strftime("%Y%m%d")
        
        # 날짜 폴더 경로 생성
        date_folder = self.output_dir / date_str
        
        # 폴더가 없으면 자동 생성 (부모 폴더도 함께 생성)
        date_folder.mkdir(parents=True, exist_ok=True)
        
        return date_folder
    
    def analyze_sql(self, query: str) -> SQLAnalysisResult:
        """SQL 쿼리 복잡도 분석
        
        Requirements 1.1-7.5, 12.1, 13.1을 구현합니다.
        - 1.1-7.5: SQL 쿼리 구조 분석 및 복잡도 계산
        - 12.1: SQL 쿼리 전체 복잡도 계산
        - 13.1: SQL 분석 시 6가지 세부 점수 제공
        
        Args:
            query: 분석할 SQL 쿼리 문자열
            
        Returns:
            SQLAnalysisResult: SQL 분석 결과
            
        Raises:
            ValueError: 빈 쿼리가 입력된 경우
        """
        # 입력 검증
        if not query or not query.strip():
            raise ValueError("빈 쿼리는 분석할 수 없습니다.")
        
        # 필요한 모듈 import
        from src.parsers.sql_parser import SQLParser
        
        # SQL 파서 생성 및 분석
        parser = SQLParser(query)
        result = self.calculator.calculate_sql_complexity(parser)
        
        # 변환 가이드 추가
        detected_features = result.detected_oracle_features + result.detected_oracle_functions
        result.conversion_guides = self.guide_provider.get_conversion_guide(detected_features)
        
        return result
    
    def analyze_plsql(self, code: str) -> PLSQLAnalysisResult:
        """PL/SQL 오브젝트 복잡도 분석
        
        Requirements 8.1-11.5, 12.2, 13.2를 구현합니다.
        - 8.1-11.5: PL/SQL 오브젝트 구조 분석 및 복잡도 계산
        - 12.2: PL/SQL 오브젝트 전체 복잡도 계산
        - 13.2: PL/SQL 분석 시 5-7가지 세부 점수 제공
        
        Args:
            code: 분석할 PL/SQL 코드 문자열
            
        Returns:
            PLSQLAnalysisResult: PL/SQL 분석 결과
            
        Raises:
            ValueError: 빈 코드가 입력된 경우 또는 오브젝트 타입 감지 실패
        """
        # 입력 검증
        if not code or not code.strip():
            raise ValueError("빈 코드는 분석할 수 없습니다.")
        
        # 필요한 모듈 import
        from src.parsers.plsql_parser import PLSQLParser
        
        # PL/SQL 파서 생성 및 분석
        parser = PLSQLParser(code)
        
        try:
            result = self.calculator.calculate_plsql_complexity(parser)
        except ValueError as e:
            # 오브젝트 타입 감지 실패 시 에러 전파
            raise ValueError(f"PL/SQL 분석 실패: {e}")
        
        # 변환 가이드 추가
        detected_features = result.detected_oracle_features + result.detected_external_dependencies
        result.conversion_guides = self.guide_provider.get_conversion_guide(detected_features)
        
        # MySQL 타겟인 경우 애플리케이션 이관 메시지 추가
        if self.target == TargetDatabase.MYSQL:
            app_migration_msg = self.guide_provider.get_mysql_app_migration_message()
            if app_migration_msg:
                # 변환 가이드에 특별 메시지 추가
                result.conversion_guides['⚠️ 중요'] = app_migration_msg
        
        return result
    
    def analyze_file(self, file_path: str) -> Union[SQLAnalysisResult, PLSQLAnalysisResult]:
        """파일에서 코드를 읽어 분석
        
        파일 내용을 읽어서 SQL 또는 PL/SQL 여부를 판단하고 적절한 분석을 수행합니다.
        
        Args:
            file_path: 분석할 파일 경로
            
        Returns:
            SQLAnalysisResult 또는 PLSQLAnalysisResult: 분석 결과
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            IOError: 파일 읽기 실패
        """
        # 파일 존재 여부 확인
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"파일 읽기 실패: {e}")
        
        # 파일 내용 기반으로 SQL/PL/SQL 판단
        if self._is_plsql(content):
            return self.analyze_plsql(content)
        else:
            return self.analyze_sql(content)
    
    def _is_plsql(self, content: str) -> bool:
        """PL/SQL 여부 판단
        
        코드 내용을 분석하여 PL/SQL 오브젝트인지 판단합니다.
        
        Args:
            content: 분석할 코드 내용
            
        Returns:
            bool: PL/SQL이면 True, SQL이면 False
        """
        # PL/SQL 키워드 목록
        plsql_keywords = [
            'CREATE OR REPLACE PACKAGE',
            'CREATE PACKAGE',
            'CREATE OR REPLACE PROCEDURE',
            'CREATE PROCEDURE',
            'CREATE OR REPLACE FUNCTION',
            'CREATE FUNCTION',
            'CREATE OR REPLACE TRIGGER',
            'CREATE TRIGGER',
            'CREATE MATERIALIZED VIEW',
            'CREATE OR REPLACE VIEW',
            'CREATE VIEW',
            'DECLARE',
            'BEGIN',
            'EXCEPTION',
        ]
        
        upper_content = content.upper()
        
        # PL/SQL 키워드가 있으면 PL/SQL로 판단
        return any(kw in upper_content for kw in plsql_keywords)
    
    def export_json(self, result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                    filename: str) -> str:
        """분석 결과를 JSON 파일로 저장 (reports/YYYYMMDD/ 폴더에)
        
        Requirements 14.1, 14.6, 14.7을 구현합니다.
        - 14.1: JSON 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        
        Args:
            result: 분석 결과 객체
            filename: 저장할 파일명 (예: "analysis_result.json")
            
        Returns:
            str: 저장된 파일의 전체 경로
            
        Raises:
            IOError: 파일 쓰기 실패
        """
        # 필요한 모듈 import
        from src.formatters.result_formatter import ResultFormatter
        
        # 날짜 폴더 생성
        date_folder = self._get_date_folder()
        
        # 파일 경로 생성
        file_path = date_folder / filename
        
        # JSON 변환
        json_str = ResultFormatter.to_json(result)
        
        # 파일 저장
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        except Exception as e:
            raise IOError(f"JSON 파일 저장 실패: {e}")
        
        return str(file_path)
    
    def export_markdown(self, result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                        filename: str) -> str:
        """분석 결과를 Markdown 파일로 저장 (reports/YYYYMMDD/ 폴더에)
        
        Requirements 14.2, 14.6, 14.7을 구현합니다.
        - 14.2: Markdown 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        
        Args:
            result: 분석 결과 객체
            filename: 저장할 파일명 (예: "analysis_report.md")
            
        Returns:
            str: 저장된 파일의 전체 경로
            
        Raises:
            IOError: 파일 쓰기 실패
        """
        # 필요한 모듈 import
        from src.formatters.result_formatter import ResultFormatter
        
        # 날짜 폴더 생성
        date_folder = self._get_date_folder()
        
        # 파일 경로 생성
        file_path = date_folder / filename
        
        # Markdown 변환
        markdown_str = ResultFormatter.to_markdown(result)
        
        # 파일 저장
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_str)
        except Exception as e:
            raise IOError(f"Markdown 파일 저장 실패: {e}")
        
        return str(file_path)



# ============================================================================
# BatchAnalyzer 클래스
# Requirements 전체를 구현합니다.
# ============================================================================

class BatchAnalyzer:
    """폴더 내 SQL/PL/SQL 파일 일괄 분석 클래스
    
    지정된 폴더 내의 모든 SQL/PL/SQL 파일을 병렬 처리로 일괄 분석합니다.
    
    Requirements:
    - 전체: 폴더 일괄 분석 및 병렬 처리
    
    Attributes:
        analyzer: OracleComplexityAnalyzer 인스턴스
        max_workers: 병렬 처리 워커 수 (기본값: CPU 코어 수)
        supported_extensions: 지원하는 파일 확장자
    """
    
    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = {'.sql', '.pls', '.pkb', '.pks', '.prc', '.fnc', '.trg'}
    
    def __init__(self, analyzer: OracleComplexityAnalyzer, max_workers: Optional[int] = None):
        """BatchAnalyzer 초기화
        
        Args:
            analyzer: OracleComplexityAnalyzer 인스턴스
            max_workers: 병렬 처리 워커 수 (None이면 CPU 코어 수 사용)
        """
        self.analyzer = analyzer
        self.max_workers = max_workers or os.cpu_count()
    
    def find_sql_files(self, folder_path: str) -> List[Path]:
        """폴더 내 SQL/PL/SQL 파일 검색
        
        지정된 폴더와 하위 폴더에서 지원하는 확장자를 가진 파일을 모두 찾습니다.
        
        Args:
            folder_path: 검색할 폴더 경로
            
        Returns:
            List[Path]: 찾은 파일 경로 리스트
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")
        
        if not folder.is_dir():
            raise ValueError(f"폴더가 아닙니다: {folder_path}")
        
        # 지원하는 확장자를 가진 파일 찾기
        sql_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            # 재귀적으로 파일 검색 (** 패턴 사용)
            sql_files.extend(folder.rglob(f"*{ext}"))
        
        return sorted(sql_files)
    
    def _analyze_single_file(self, file_path: Path) -> tuple:
        """단일 파일 분석 (병렬 처리용 헬퍼 메서드)
        
        Args:
            file_path: 분석할 파일 경로
            
        Returns:
            tuple: (파일명, 분석 결과 또는 None, 에러 메시지 또는 None)
        """
        file_name = str(file_path)
        
        try:
            result = self.analyzer.analyze_file(file_name)
            return (file_name, result, None)
        except Exception as e:
            return (file_name, None, str(e))
    
    def analyze_folder(self, folder_path: str) -> BatchAnalysisResult:
        """폴더 내 모든 SQL/PL/SQL 파일 일괄 분석
        
        concurrent.futures를 사용하여 병렬 처리로 파일들을 분석합니다.
        
        Requirements:
        - 전체: 폴더 일괄 분석 및 병렬 처리
        
        Args:
            folder_path: 분석할 폴더 경로
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        # SQL/PL/SQL 파일 검색
        sql_files = self.find_sql_files(folder_path)
        
        if not sql_files:
            # 파일이 없으면 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                success_count=0,
                failure_count=0,
                target_database=self.analyzer.target
            )
        
        # 결과 저장용 변수
        results = {}
        failed_files = {}
        complexity_distribution = {level.value: 0 for level in ComplexityLevel}
        total_score = 0.0
        
        # 병렬 처리로 파일 분석
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 파일에 대해 분석 작업 제출
            future_to_file = {
                executor.submit(self._analyze_single_file, file_path): file_path
                for file_path in sql_files
            }
            
            # 완료된 작업 결과 수집
            for future in concurrent.futures.as_completed(future_to_file):
                file_name, result, error = future.result()
                
                if error:
                    # 분석 실패
                    failed_files[file_name] = error
                else:
                    # 분석 성공
                    results[file_name] = result
                    
                    # 복잡도 레벨별 분포 집계
                    level_name = result.complexity_level.value
                    complexity_distribution[level_name] += 1
                    
                    # 총 점수 누적
                    total_score += result.normalized_score
        
        # 평균 점수 계산
        success_count = len(results)
        average_score = total_score / success_count if success_count > 0 else 0.0
        
        # 배치 분석 결과 생성
        batch_result = BatchAnalysisResult(
            total_files=len(sql_files),
            success_count=success_count,
            failure_count=len(failed_files),
            complexity_distribution=complexity_distribution,
            average_score=average_score,
            results=results,
            failed_files=failed_files,
            target_database=self.analyzer.target
        )
        
        return batch_result
    
    def analyze_folder_with_progress(self, folder_path: str, 
                                     progress_callback=None) -> BatchAnalysisResult:
        """폴더 내 모든 SQL/PL/SQL 파일 일괄 분석 (진행 상황 표시 포함)
        
        concurrent.futures를 사용하여 병렬 처리로 파일들을 분석하며,
        tqdm을 사용하여 진행 상황을 표시합니다.
        
        Requirements:
        - 전체: 폴더 일괄 분석 및 병렬 처리, 진행 상황 표시
        
        Args:
            folder_path: 분석할 폴더 경로
            progress_callback: 진행 상황 콜백 함수 (선택사항)
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        # SQL/PL/SQL 파일 검색
        sql_files = self.find_sql_files(folder_path)
        
        if not sql_files:
            # 파일이 없으면 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                success_count=0,
                failure_count=0,
                target_database=self.analyzer.target
            )
        
        # 결과 저장용 변수
        results = {}
        failed_files = {}
        complexity_distribution = {level.value: 0 for level in ComplexityLevel}
        total_score = 0.0
        
        # tqdm 사용 가능 여부 확인
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        
        # 병렬 처리로 파일 분석
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 파일에 대해 분석 작업 제출
            future_to_file = {
                executor.submit(self._analyze_single_file, file_path): file_path
                for file_path in sql_files
            }
            
            # 진행 상황 표시 설정
            if use_tqdm:
                # tqdm 프로그레스 바 생성
                pbar = tqdm(
                    total=len(sql_files),
                    desc="파일 분석",
                    unit="파일",
                    ncols=80,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                )
            
            # 완료된 작업 결과 수집
            for future in concurrent.futures.as_completed(future_to_file):
                file_name, result, error = future.result()
                
                if error:
                    # 분석 실패
                    failed_files[file_name] = error
                else:
                    # 분석 성공
                    results[file_name] = result
                    
                    # 복잡도 레벨별 분포 집계
                    level_name = result.complexity_level.value
                    complexity_distribution[level_name] += 1
                    
                    # 총 점수 누적
                    total_score += result.normalized_score
                
                # 진행 상황 업데이트
                if use_tqdm:
                    pbar.update(1)
                elif progress_callback:
                    progress_callback(len(results) + len(failed_files), len(sql_files))
            
            # 프로그레스 바 닫기
            if use_tqdm:
                pbar.close()
        
        # 평균 점수 계산
        success_count = len(results)
        average_score = total_score / success_count if success_count > 0 else 0.0
        
        # 배치 분석 결과 생성
        batch_result = BatchAnalysisResult(
            total_files=len(sql_files),
            success_count=success_count,
            failure_count=len(failed_files),
            complexity_distribution=complexity_distribution,
            average_score=average_score,
            results=results,
            failed_files=failed_files,
            target_database=self.analyzer.target
        )
        
        return batch_result
    
    def get_top_complex_files(self, batch_result: BatchAnalysisResult, top_n: int = 10) -> List[tuple]:
        """복잡도가 높은 파일 Top N 추출
        
        Args:
            batch_result: 배치 분석 결과
            top_n: 추출할 파일 수 (기본값: 10)
            
        Returns:
            List[tuple]: (파일명, 복잡도 점수) 튜플 리스트 (점수 내림차순)
        """
        # 파일명과 점수를 튜플로 만들어 리스트 생성
        file_scores = [
            (file_name, result.normalized_score)
            for file_name, result in batch_result.results.items()
        ]
        
        # 점수 기준 내림차순 정렬
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Top N 반환
        return file_scores[:top_n]
    
    def export_batch_json(self, batch_result: BatchAnalysisResult, 
                          include_details: bool = True) -> str:
        """배치 분석 결과를 JSON 파일로 저장
        
        Requirements 14.1, 14.6, 14.7, 14.8을 구현합니다.
        - 14.1: JSON 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: True)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        import json
        from src.formatters.result_formatter import ResultFormatter
        
        # 날짜 폴더 생성
        date_folder = self.analyzer._get_date_folder()
        
        # 파일명 생성 (batch_summary_YYYYMMDD_HHMMSS.json)
        filename = f"batch_summary_{batch_result.analysis_time}.json"
        file_path = date_folder / filename
        
        # JSON 데이터 구성
        json_data = {
            "summary": {
                "total_files": batch_result.total_files,
                "success_count": batch_result.success_count,
                "failure_count": batch_result.failure_count,
                "average_score": round(batch_result.average_score, 2),
                "target_database": batch_result.target_database.value,
                "analysis_time": batch_result.analysis_time,
            },
            "complexity_distribution": batch_result.complexity_distribution,
            "top_complex_files": [
                {"file": file_name, "score": round(score, 2)}
                for file_name, score in self.get_top_complex_files(batch_result, 10)
            ],
            "failed_files": batch_result.failed_files,
        }
        
        # 개별 파일 상세 결과 포함
        if include_details:
            json_data["details"] = {}
            for file_name, result in batch_result.results.items():
                # 각 결과를 JSON으로 변환 후 다시 파싱 (dict로 변환)
                result_json = ResultFormatter.to_json(result)
                json_data["details"][file_name] = json.loads(result_json)
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def export_batch_markdown(self, batch_result: BatchAnalysisResult,
                              include_details: bool = False) -> str:
        """배치 분석 결과를 Markdown 파일로 저장
        
        Requirements 14.2, 14.6, 14.7, 14.8을 구현합니다.
        - 14.2: Markdown 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: False)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        from src.formatters.result_formatter import ResultFormatter
        
        # 날짜 폴더 생성
        date_folder = self.analyzer._get_date_folder()
        
        # 파일명 생성 (batch_summary_YYYYMMDD_HHMMSS.md)
        filename = f"batch_summary_{batch_result.analysis_time}.md"
        file_path = date_folder / filename
        
        # Markdown 내용 생성
        lines = []
        
        # 제목
        lines.append("# Oracle 복잡도 분석 배치 리포트\n")
        lines.append(f"**분석 시간**: {batch_result.analysis_time}\n")
        lines.append(f"**타겟 데이터베이스**: {batch_result.target_database.value}\n")
        lines.append("\n---\n")
        
        # 요약 통계
        lines.append("## 📊 요약 통계\n")
        lines.append(f"- **전체 파일 수**: {batch_result.total_files}\n")
        lines.append(f"- **분석 성공**: {batch_result.success_count}\n")
        lines.append(f"- **분석 실패**: {batch_result.failure_count}\n")
        lines.append(f"- **평균 복잡도 점수**: {batch_result.average_score:.2f} / 10\n")
        lines.append("\n")
        
        # 복잡도 레벨별 분포
        lines.append("## 📈 복잡도 레벨별 분포\n")
        lines.append("| 복잡도 레벨 | 파일 수 | 비율 |\n")
        lines.append("|------------|---------|------|\n")
        
        for level in ComplexityLevel:
            count = batch_result.complexity_distribution.get(level.value, 0)
            percentage = (count / batch_result.success_count * 100) if batch_result.success_count > 0 else 0
            lines.append(f"| {level.value} | {count} | {percentage:.1f}% |\n")
        
        lines.append("\n")
        
        # 복잡도 높은 파일 Top 10
        lines.append("## 🔥 복잡도 높은 파일 Top 10\n")
        lines.append("| 순위 | 파일명 | 복잡도 점수 |\n")
        lines.append("|------|--------|-------------|\n")
        
        top_files = self.get_top_complex_files(batch_result, 10)
        for idx, (file_name, score) in enumerate(top_files, 1):
            lines.append(f"| {idx} | `{file_name}` | {score:.2f} |\n")
        
        lines.append("\n")
        
        # 실패한 파일 목록
        if batch_result.failed_files:
            lines.append("## ❌ 분석 실패 파일\n")
            lines.append("| 파일명 | 에러 메시지 |\n")
            lines.append("|--------|-------------|\n")
            
            for file_name, error in batch_result.failed_files.items():
                lines.append(f"| `{file_name}` | {error} |\n")
            
            lines.append("\n")
        
        # 개별 파일 상세 결과
        if include_details and batch_result.results:
            lines.append("## 📄 개별 파일 상세 결과\n")
            lines.append("\n")
            
            for file_name, result in batch_result.results.items():
                lines.append(f"### {file_name}\n")
                lines.append("\n")
                
                # 각 결과를 Markdown으로 변환
                result_md = ResultFormatter.to_markdown(result)
                lines.append(result_md)
                lines.append("\n---\n\n")
        
        # 파일 저장
        markdown_content = "".join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(file_path)


# ============================================================================
# CLI 인터페이스
# Requirements 전체를 구현합니다.
# ============================================================================

import argparse
import sys


def create_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성
    
    Requirements:
    - 전체: 명령줄 인터페이스 구현
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(
        prog='oracle-complexity-analyzer',
        description='Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 평가합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
사용 예시:
  # 단일 파일 분석 (PostgreSQL 타겟)
  %(prog)s -f query.sql
  
  # 단일 파일 분석 (MySQL 타겟)
  %(prog)s -f query.sql -t mysql
  
  # 폴더 전체 분석 (병렬 처리)
  %(prog)s -d /path/to/sql/files
  
  # 폴더 분석 + JSON 출력
  %(prog)s -d /path/to/sql/files -o json
  
  # 폴더 분석 + 병렬 워커 수 지정
  %(prog)s -d /path/to/sql/files -w 8
  
  # 폴더 분석 + 상세 결과 포함
  %(prog)s -d /path/to/sql/files --details

지원 파일 확장자:
  .sql, .pls, .pkb, .pks, .prc, .fnc, .trg
        '''
    )
    
    # 입력 옵션 (파일 또는 폴더)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-f', '--file',
        type=str,
        metavar='FILE',
        help='분석할 단일 SQL/PL/SQL 파일 경로'
    )
    input_group.add_argument(
        '-d', '--directory',
        type=str,
        metavar='DIR',
        help='분석할 폴더 경로 (하위 폴더 포함)'
    )
    
    # 타겟 데이터베이스 선택
    parser.add_argument(
        '-t', '--target',
        type=str,
        choices=['postgresql', 'mysql', 'pg', 'my'],
        default='postgresql',
        metavar='DB',
        help='타겟 데이터베이스 (postgresql, mysql, pg, my) [기본값: postgresql]'
    )
    
    # 출력 형식 선택
    parser.add_argument(
        '-o', '--output',
        type=str,
        choices=['json', 'markdown', 'both', 'console'],
        default='console',
        metavar='FORMAT',
        help='출력 형식 (json, markdown, both, console) [기본값: console]'
    )
    
    # 출력 디렉토리
    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports',
        metavar='DIR',
        help='출력 디렉토리 경로 [기본값: reports]'
    )
    
    # 병렬 처리 워커 수 (폴더 분석 시)
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=None,
        metavar='N',
        help='병렬 처리 워커 수 (기본값: CPU 코어 수)'
    )
    
    # 상세 결과 포함 여부 (배치 분석 시)
    parser.add_argument(
        '--details',
        action='store_true',
        help='배치 분석 시 개별 파일 상세 결과 포함'
    )
    
    # 진행 상황 표시 여부
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='진행 상황 표시 비활성화'
    )
    
    # 버전 정보
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    return parser


def normalize_target(target) -> TargetDatabase:
    """타겟 데이터베이스 문자열을 TargetDatabase Enum으로 변환
    
    Args:
        target: 타겟 데이터베이스 문자열 (postgresql, mysql, pg, my) 또는 TargetDatabase Enum
        
    Returns:
        TargetDatabase: 타겟 데이터베이스 Enum
    """
    # 이미 TargetDatabase Enum이면 그대로 반환
    if isinstance(target, TargetDatabase):
        return target
    
    # 문자열인 경우 변환
    if isinstance(target, str):
        target_lower = target.lower()
        
        if target_lower in ['postgresql', 'pg']:
            return TargetDatabase.POSTGRESQL
        elif target_lower in ['mysql', 'my']:
            return TargetDatabase.MYSQL
    
    # 지원하지 않는 타입이거나 값인 경우
    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target}")


def print_result_console(result: Union[SQLAnalysisResult, PLSQLAnalysisResult]):
    """분석 결과를 콘솔에 출력
    
    Args:
        result: 분석 결과 객체
    """
    print("\n" + "="*80)
    print("📊 Oracle 복잡도 분석 결과")
    print("="*80)
    
    # 기본 정보
    print(f"\n타겟 데이터베이스: {result.target_database.value}")
    print(f"복잡도 점수: {result.normalized_score:.2f} / 10")
    print(f"복잡도 레벨: {result.complexity_level.value}")
    print(f"권장사항: {result.recommendation}")
    
    # 세부 점수
    print("\n📈 세부 점수:")
    
    # SQL 결과인지 PL/SQL 결과인지 속성으로 판단
    if hasattr(result, 'structural_complexity'):
        # SQLAnalysisResult
        print(f"  - 구조적 복잡성: {result.structural_complexity:.2f}")
        print(f"  - Oracle 특화 기능: {result.oracle_specific_features:.2f}")
        print(f"  - 함수/표현식: {result.functions_expressions:.2f}")
        print(f"  - 데이터 볼륨: {result.data_volume:.2f}")
        print(f"  - 실행 복잡성: {result.execution_complexity:.2f}")
        print(f"  - 변환 난이도: {result.conversion_difficulty:.2f}")
    else:
        # PLSQLAnalysisResult
        print(f"  - 기본 점수: {result.base_score:.2f}")
        print(f"  - 코드 복잡도: {result.code_complexity:.2f}")
        print(f"  - Oracle 특화 기능: {result.oracle_features:.2f}")
        print(f"  - 비즈니스 로직: {result.business_logic:.2f}")
        print(f"  - AI 변환 난이도: {result.ai_difficulty:.2f}")
        if hasattr(result, 'mysql_constraints') and result.mysql_constraints > 0:
            print(f"  - MySQL 제약: {result.mysql_constraints:.2f}")
        if hasattr(result, 'app_migration_penalty') and result.app_migration_penalty > 0:
            print(f"  - 애플리케이션 이관 페널티: {result.app_migration_penalty:.2f}")
    
    # 감지된 Oracle 특화 기능
    if result.detected_oracle_features:
        print("\n🔍 감지된 Oracle 특화 기능:")
        for feature in result.detected_oracle_features:
            print(f"  - {feature}")
    
    # 감지된 Oracle 특화 함수 (SQL만)
    if hasattr(result, 'detected_oracle_functions') and result.detected_oracle_functions:
        print("\n🔧 감지된 Oracle 특화 함수:")
        for func in result.detected_oracle_functions:
            print(f"  - {func}")
    
    # 외부 의존성 (PL/SQL만)
    if hasattr(result, 'detected_external_dependencies') and result.detected_external_dependencies:
        print("\n📦 감지된 외부 의존성:")
        for dep in result.detected_external_dependencies:
            print(f"  - {dep}")
    
    # 변환 가이드
    if result.conversion_guides:
        print("\n💡 변환 가이드:")
        for feature, guide in result.conversion_guides.items():
            print(f"  - {feature}: {guide}")
    
    print("\n" + "="*80 + "\n")


def print_batch_result_console(batch_result: BatchAnalysisResult):
    """배치 분석 결과를 콘솔에 출력
    
    Args:
        batch_result: 배치 분석 결과 객체
    """
    print("\n" + "="*80)
    print("📊 Oracle 복잡도 분석 배치 리포트")
    print("="*80)
    
    # 요약 통계
    print(f"\n분석 시간: {batch_result.analysis_time}")
    print(f"타겟 데이터베이스: {batch_result.target_database.value}")
    print(f"\n전체 파일 수: {batch_result.total_files}")
    print(f"분석 성공: {batch_result.success_count}")
    print(f"분석 실패: {batch_result.failure_count}")
    print(f"평균 복잡도 점수: {batch_result.average_score:.2f} / 10")
    
    # 복잡도 레벨별 분포
    print("\n📈 복잡도 레벨별 분포:")
    for level in ComplexityLevel:
        count = batch_result.complexity_distribution.get(level.value, 0)
        percentage = (count / batch_result.success_count * 100) if batch_result.success_count > 0 else 0
        bar = "█" * int(percentage / 5)  # 5%당 1개 블록
        print(f"  {level.value:15s}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # 복잡도 높은 파일 Top 10
    print("\n🔥 복잡도 높은 파일 Top 10:")
    batch_analyzer = BatchAnalyzer(None)  # analyzer는 필요 없음
    top_files = batch_analyzer.get_top_complex_files(batch_result, 10)
    
    for idx, (file_name, score) in enumerate(top_files, 1):
        print(f"  {idx:2d}. {file_name:60s} {score:5.2f}")
    
    # 실패한 파일 목록
    if batch_result.failed_files:
        print("\n❌ 분석 실패 파일:")
        for file_name, error in batch_result.failed_files.items():
            print(f"  - {file_name}")
            print(f"    에러: {error}")
    
    print("\n" + "="*80 + "\n")


def analyze_single_file(args):
    """단일 파일 분석 실행
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        # 타겟 데이터베이스 설정
        # 디버그: args.target 값 확인
        # print(f"DEBUG: args.target = {args.target}, type = {type(args.target)}")
        target_db = normalize_target(args.target)
        
        # 분석기 생성
        analyzer = OracleComplexityAnalyzer(
            target_database=target_db,
            output_dir=args.output_dir
        )
        
        # 파일 분석
        print(f"📄 파일 분석 중: {args.file}")
        result = analyzer.analyze_file(args.file)
        
        # 결과 출력
        if args.output in ['console', 'both']:
            print_result_console(result)
        
        # JSON 출력
        if args.output in ['json', 'both']:
            file_name = Path(args.file).stem
            json_path = analyzer.export_json(result, f"{file_name}_analysis.json")
            print(f"✅ JSON 저장 완료: {json_path}")
        
        # Markdown 출력
        if args.output in ['markdown', 'both']:
            file_name = Path(args.file).stem
            md_path = analyzer.export_markdown(result, f"{file_name}_analysis.md")
            print(f"✅ Markdown 저장 완료: {md_path}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ 에러: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ 에러: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def analyze_directory(args):
    """폴더 일괄 분석 실행
    
    Args:
        args: 명령줄 인자
        
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        # 타겟 데이터베이스 설정
        target_db = normalize_target(args.target)
        
        # 분석기 생성
        analyzer = OracleComplexityAnalyzer(
            target_database=target_db,
            output_dir=args.output_dir
        )
        
        # 배치 분석기 생성
        batch_analyzer = BatchAnalyzer(analyzer, max_workers=args.workers)
        
        # 파일 검색
        print(f"📁 폴더 검색 중: {args.directory}")
        sql_files = batch_analyzer.find_sql_files(args.directory)
        print(f"✅ {len(sql_files)}개 파일 발견")
        
        if not sql_files:
            print("⚠️  분석할 파일이 없습니다.")
            return 0
        
        # 폴더 분석
        print(f"\n🔄 분석 시작 (워커 수: {batch_analyzer.max_workers})")
        
        # 진행 상황 표시
        if not args.no_progress:
            # tqdm 사용 가능 여부 확인
            try:
                from tqdm import tqdm
                
                # tqdm을 사용한 진행 상황 표시
                # BatchAnalyzer에 진행 상황 콜백 추가
                batch_result = batch_analyzer.analyze_folder_with_progress(
                    args.directory,
                    progress_callback=lambda current, total: None  # tqdm이 자동 처리
                )
            except ImportError:
                # tqdm이 없으면 기본 출력 사용
                print("진행 중...", end='', flush=True)
                batch_result = batch_analyzer.analyze_folder(args.directory)
                print(" 완료!")
        else:
            # 진행 상황 표시 비활성화
            batch_result = batch_analyzer.analyze_folder(args.directory)
        
        # 결과 출력
        if args.output in ['console', 'both']:
            print_batch_result_console(batch_result)
        
        # JSON 출력
        if args.output in ['json', 'both']:
            json_path = batch_analyzer.export_batch_json(
                batch_result,
                include_details=args.details
            )
            print(f"✅ JSON 저장 완료: {json_path}")
        
        # Markdown 출력
        if args.output in ['markdown', 'both']:
            md_path = batch_analyzer.export_batch_markdown(
                batch_result,
                include_details=args.details
            )
            print(f"✅ Markdown 저장 완료: {md_path}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ 에러: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ 에러: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """CLI 메인 함수
    
    Requirements:
    - 전체: 명령줄 인터페이스 구현
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    # 인자 파서 생성
    parser = create_parser()
    
    # 인자 파싱
    args = parser.parse_args()
    
    # 단일 파일 분석
    if args.file:
        return analyze_single_file(args)
    
    # 폴더 일괄 분석
    elif args.directory:
        return analyze_directory(args)
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
