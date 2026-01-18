"""
ComplexityCalculator 베이스 클래스

복잡도 계산기의 기본 구조와 초기화를 담당합니다.
"""

import logging
from src.oracle_complexity_analyzer import (
    TargetDatabase,
    WeightConfig,
    POSTGRESQL_WEIGHTS,
    MYSQL_WEIGHTS,
)

# 로거 초기화
logger = logging.getLogger(__name__)


class ComplexityCalculatorBase:
    """복잡도 계산기 베이스 클래스
    
    타겟 데이터베이스에 따라 적절한 가중치를 로딩하고,
    SQL 쿼리 및 PL/SQL 오브젝트의 복잡도를 계산하는 기반을 제공합니다.
    """
    
    def __init__(self, target_database):
        """ComplexityCalculator 초기화
        
        Args:
            target_database: 타겟 데이터베이스 (PostgreSQL 또는 MySQL) - TargetDatabase Enum 또는 문자열
        """
        # 문자열인 경우 TargetDatabase Enum으로 변환
        if isinstance(target_database, str):
            # "<TargetDatabase.POSTGRESQL: 'postgresql'>" 형식의 문자열 처리
            if target_database.startswith("<TargetDatabase."):
                # 'postgresql' 부분 추출
                target_value = target_database.split("'")[1]
                if target_value == "postgresql":
                    target_database = TargetDatabase.POSTGRESQL
                elif target_value == "mysql":
                    target_database = TargetDatabase.MYSQL
                else:
                    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target_database}")
            # "TargetDatabase.POSTGRESQL" 형식의 문자열 처리
            elif target_database.startswith("TargetDatabase."):
                enum_name = target_database.split(".")[-1]
                target_database = TargetDatabase[enum_name]
            else:
                # 일반 문자열 처리
                target_lower = target_database.lower()
                if target_lower in ['postgresql', 'pg']:
                    target_database = TargetDatabase.POSTGRESQL
                elif target_lower in ['mysql', 'my']:
                    target_database = TargetDatabase.MYSQL
                else:
                    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target_database}")
        
        self.target = target_database
        
        # 타겟 DB에 따른 가중치 로딩 (Requirements 3.1, 3.2)
        # Enum 값의 문자열 비교를 사용하여 순환 참조 문제 회피
        target_value = target_database.value if hasattr(target_database, 'value') else str(target_database)
        
        if target_value == "postgresql":
            self.weights = POSTGRESQL_WEIGHTS
        elif target_value == "mysql":
            self.weights = MYSQL_WEIGHTS
        else:
            raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target_database}")
