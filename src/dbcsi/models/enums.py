"""
Enum 정의

데이터베이스 관련 Enum 클래스들을 정의합니다.
"""

from enum import Enum


class OracleEdition(Enum):
    """Oracle 데이터베이스 에디션"""
    STANDARD = "Standard Edition"
    STANDARD_2 = "Standard Edition 2"
    ENTERPRISE = "Enterprise Edition"
    EXPRESS = "Express Edition"
    UNKNOWN = "Unknown"


class TargetDatabase(Enum):
    """마이그레이션 타겟 데이터베이스"""
    RDS_ORACLE = "RDS for Oracle"
    AURORA_MYSQL = "Aurora MySQL 8.0"
    AURORA_POSTGRESQL = "Aurora PostgreSQL 16"
