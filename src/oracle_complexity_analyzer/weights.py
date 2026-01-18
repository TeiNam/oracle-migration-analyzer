"""
가중치 설정 모듈

타겟 데이터베이스별 가중치 설정을 정의합니다.
"""

from .data_models import WeightConfig
from .enums import TargetDatabase, PLSQLObjectType


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
