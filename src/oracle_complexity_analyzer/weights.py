"""
가중치 설정 모듈

타겟 데이터베이스별 가중치 설정을 정의합니다.

개선 이력:
- 2026-01-28: SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 점수 조정
  - 데이터 볼륨 점수 대폭 축소 (쿼리 길이와 복잡도의 약한 상관관계 반영)
  - MySQL CTE 점수 하향 (MySQL 8.0 CTE 지원 반영)
"""

from .data_models import WeightConfig
from .enums import TargetDatabase, PLSQLObjectType

# PostgreSQL 가중치 설정
# Requirements 1.1-1.5, 3.1, 5.1-5.4, 6.1-6.5를 반영
# SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 데이터 볼륨 점수 축소
POSTGRESQL_WEIGHTS = WeightConfig(
    max_structural=2.5,
    join_thresholds=[
        (0, 0.0),  # 0개 = 0점
        (3, 0.5),  # 1-3개 = 0.5점
        (5, 1.0),  # 4-5개 = 1.0점
        (float("inf"), 1.5),  # 6개 이상 = 1.5점
    ],
    subquery_thresholds=[
        (0, 0.0),  # 0 = 0점
        (1, 0.5),  # 1 = 0.5점
        (2, 1.0),  # 2 = 1.0점
        # 3 이상 = 1.5 + min(1, (depth-2)*0.5) - 계산 로직에서 처리
    ],
    cte_coefficient=0.5,
    cte_max=1.0,
    set_operator_coefficient=0.5,
    set_operator_max=1.5,
    fullscan_penalty=0.0,  # PostgreSQL은 풀스캔 페널티 없음
    # 데이터 볼륨 점수 대폭 축소 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
    # 쿼리 길이와 복잡도의 약한 상관관계를 반영
    data_volume_scores={
        "small": 0.3,   # < 500자 (기존 0.5 → 0.3)
        "medium": 0.3,  # 500-1000자 (기존 1.0 → 0.3, 기준 변경)
        "large": 0.5,   # 500-1000자 (기존 1.5 → 0.5)
        "xlarge": 0.8,  # 1000자 이상 (기존 2.0 → 0.8)
    },
    execution_scores={
        "order_by": 0.2,
        "group_by": 0.2,
        "having": 0.2,
        "join_depth": 0.5,  # join_count > 5 또는 subquery_depth > 2
    },
    max_total_score=13.5,  # 구조적(2.5) + Oracle특화(3.0) + 함수(2.0) + 볼륨(0.8) + 실행(1.0) + 변환(4.5)
)


# MySQL 가중치 설정
# Requirements 1.1-1.5, 3.2, 5.1-5.4, 6.1-6.7을 반영
# SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 데이터 볼륨 점수 축소 및 CTE 점수 하향
MYSQL_WEIGHTS = WeightConfig(
    max_structural=4.5,
    join_thresholds=[
        (0, 0.0),  # 0개 = 0점
        (2, 1.0),  # 1-2개 = 1.0점
        (4, 2.0),  # 3-4개 = 2.0점
        (6, 3.0),  # 5-6개 = 3.0점
        (float("inf"), 4.0),  # 7개 이상 = 4.0점
    ],
    subquery_thresholds=[
        (0, 0.0),  # 0 = 0점
        (1, 1.5),  # 1 = 1.5점
        (2, 3.0),  # 2 = 3.0점
        # 3 이상 = 4.0 + min(2, depth-2) - 계산 로직에서 처리
    ],
    # MySQL CTE 점수 하향 (MySQL 8.0 CTE 지원 반영)
    cte_coefficient=0.5,  # 기존 0.8 → 0.5
    cte_max=1.5,          # 기존 2.0 → 1.5
    set_operator_coefficient=0.8,
    set_operator_max=2.0,
    fullscan_penalty=1.0,  # MySQL은 WHERE 절 없을 때 1.0점 페널티
    # 데이터 볼륨 점수 대폭 축소 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
    data_volume_scores={
        "small": 0.3,   # < 500자 (기존 0.5 → 0.3)
        "medium": 0.3,  # 500-1000자 (기존 1.2 → 0.3, 기준 변경)
        "large": 0.7,   # 500-1000자 (기존 2.0 → 0.7)
        "xlarge": 1.0,  # 1000자 이상 (기존 2.5 → 1.0)
    },
    execution_scores={
        "order_by": 0.5,
        "group_by": 0.5,
        "having": 0.5,
        "join_depth": 1.5,  # join_count > 3 또는 subquery_depth > 1
        "derived_table": 0.5,  # 파생 테이블당 0.5점 (max 1.0)
        "distinct": 0.3,
        "or_conditions": 0.3,  # OR 조건 3개 이상
        "like_pattern": 0.3,  # LIKE '%문자열%'
        "function_in_where": 0.5,  # WHERE 절에 함수 사용
        "count_no_where": 0.5,  # WHERE 절 없이 COUNT(*) 사용
    },
    max_total_score=18.0,  # 구조적(4.5) + Oracle특화(3.0) + 함수(2.5) + 볼륨(1.0) + 실행(2.5) + 변환(4.5)
)


# PL/SQL 오브젝트 기본 점수 (THRESHOLD_IMPROVEMENT_PROPOSAL.md 기반)
# 기본 점수는 "최소 복잡도"를 의미하며, 실제 복잡도는 내부 분석으로 추가됨
# 기존 점수가 너무 높아 단순한 코드도 고복잡도로 평가되는 문제 해결
PLSQL_BASE_SCORES = {
    TargetDatabase.POSTGRESQL: {
        PLSQLObjectType.PACKAGE: 4.0,  # 기존 7.0 → 4.0
        PLSQLObjectType.PROCEDURE: 2.5,  # 기존 5.0 → 2.5
        PLSQLObjectType.FUNCTION: 2.0,  # 기존 4.0 → 2.0
        PLSQLObjectType.TRIGGER: 3.5,  # 기존 6.0 → 3.5
        PLSQLObjectType.VIEW: 1.0,  # 기존 2.0 → 1.0
        PLSQLObjectType.MATERIALIZED_VIEW: 2.5,  # 기존 4.0 → 2.5
    },
    TargetDatabase.MYSQL: {
        PLSQLObjectType.PACKAGE: 5.0,  # 기존 8.0 → 5.0
        PLSQLObjectType.PROCEDURE: 3.5,  # 기존 6.0 → 3.5
        PLSQLObjectType.FUNCTION: 3.0,  # 기존 5.0 → 3.0
        PLSQLObjectType.TRIGGER: 4.5,  # 기존 7.0 → 4.5
        PLSQLObjectType.VIEW: 1.0,  # 기존 2.0 → 1.0
        PLSQLObjectType.MATERIALIZED_VIEW: 3.5,  # 기존 5.0 → 3.5
    },
}

# 고난이도 복잡도 임계값 (타겟 DB별)
# max_total_score 대비 약 37~39% 비율 기준
# - PostgreSQL: 13.5 * 0.37 ≈ 5.0 (Oracle 호환성 높음)
# - MySQL: 18.0 * 0.39 ≈ 7.0 (PL/SQL 미지원, 기본 점수 높음)
HIGH_COMPLEXITY_THRESHOLD = {
    TargetDatabase.POSTGRESQL: 5.0,
    TargetDatabase.MYSQL: 7.0,
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
