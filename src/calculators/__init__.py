"""
복잡도 계산 모듈

이 모듈은 파싱된 SQL/PL/SQL 코드의 복잡도를 계산하고
타겟 데이터베이스별 가중치를 적용합니다.
"""

from .base import ComplexityCalculatorBase
from .metrics import ComplexityMetrics
from .sql_complexity import SQLComplexityCalculator
from .plsql_complexity import PLSQLComplexityCalculator


class ComplexityCalculator(
    ComplexityCalculatorBase,
    ComplexityMetrics,
    SQLComplexityCalculator,
    PLSQLComplexityCalculator
):
    """복잡도 점수 계산
    
    Requirements 3.1, 3.2를 구현합니다.
    - 3.1: PostgreSQL 타겟에서 Oracle 특화 함수 점수 계산
    - 3.2: MySQL 타겟에서 Oracle 특화 함수 점수 계산 및 추가 페널티
    
    타겟 데이터베이스에 따라 적절한 가중치를 로딩하고,
    SQL 쿼리 및 PL/SQL 오브젝트의 복잡도를 계산합니다.
    
    이 클래스는 여러 믹스인 클래스를 상속받아 기능을 조합합니다:
    - ComplexityCalculatorBase: 초기화 및 기본 설정
    - ComplexityMetrics: 점수 정규화 및 레벨 결정
    - SQLComplexityCalculator: SQL 복잡도 계산
    - PLSQLComplexityCalculator: PL/SQL 복잡도 계산
    """
    pass


__all__ = [
    'ComplexityCalculator',
    'ComplexityCalculatorBase',
    'ComplexityMetrics',
    'SQLComplexityCalculator',
    'PLSQLComplexityCalculator',
]
