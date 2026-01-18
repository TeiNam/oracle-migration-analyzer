"""
Enum 정의 모듈

타겟 데이터베이스, 복잡도 레벨, PL/SQL 오브젝트 타입 등의 Enum을 정의합니다.
"""

from enum import Enum


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
