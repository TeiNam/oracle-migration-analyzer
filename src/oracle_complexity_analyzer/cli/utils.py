"""
CLI 유틸리티 함수

타겟 데이터베이스 변환 등 CLI에서 사용하는 유틸리티 함수를 제공합니다.
"""

from ..enums import TargetDatabase


def normalize_target(target) -> TargetDatabase:
    """타겟 데이터베이스 문자열을 TargetDatabase Enum으로 변환
    
    Args:
        target: 타겟 데이터베이스 문자열 (postgresql, mysql, pg, my) 또는 TargetDatabase Enum
        
    Returns:
        TargetDatabase: 타겟 데이터베이스 Enum
        
    Raises:
        ValueError: 지원하지 않는 타겟 데이터베이스인 경우
    """
    if isinstance(target, TargetDatabase):
        return target
    
    if isinstance(target, str):
        target_lower = target.lower()
        
        if target_lower in ['postgresql', 'pg']:
            return TargetDatabase.POSTGRESQL
        elif target_lower in ['mysql', 'my']:
            return TargetDatabase.MYSQL
    
    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target}")


def is_all_targets(target: str) -> bool:
    """타겟이 'all' 또는 'both'인지 확인
    
    Args:
        target: 타겟 데이터베이스 문자열
        
    Returns:
        bool: 모든 타겟 분석 여부
    """
    return target.lower() in ['all', 'both']
