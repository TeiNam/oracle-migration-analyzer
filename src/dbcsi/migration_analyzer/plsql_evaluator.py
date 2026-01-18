"""
PL/SQL 복잡도 평가 모듈

PL/SQL 코드 라인 수와 패키지 수를 기반으로 복잡도를 계산합니다.
"""

from typing import Dict, Any
from ..models import StatspackData, TargetDatabase


def evaluate_plsql_complexity(
    data: StatspackData,
    target: TargetDatabase
) -> Dict[str, Any]:
    """
    PL/SQL 코드 복잡도 평가
    
    PL/SQL 코드 라인 수와 패키지 수를 기반으로 복잡도를 계산합니다.
    
    Args:
        data: Statspack 데이터
        target: 타겟 데이터베이스
    
    Returns:
        Dict[str, Any]: PL/SQL 복잡도 평가 결과
            - lines_of_code: PL/SQL 코드 라인 수
            - package_count: 패키지 수
            - procedure_count: 프로시저 수
            - function_count: 함수 수
            - complexity_score: 복잡도 점수
            - conversion_strategy: 변환 전략
    """
    result: Dict[str, Any] = {
        "lines_of_code": 0,
        "package_count": 0,
        "procedure_count": 0,
        "function_count": 0,
        "complexity_score": 0.0,
        "conversion_strategy": []
    }
    
    # PL/SQL 코드 라인 수
    lines_of_code = data.os_info.count_lines_plsql or 0
    result["lines_of_code"] = lines_of_code
    
    # 패키지, 프로시저, 함수 수
    package_count = data.os_info.count_packages or 0
    procedure_count = data.os_info.count_procedures or 0
    function_count = data.os_info.count_functions or 0
    
    result["package_count"] = package_count
    result["procedure_count"] = procedure_count
    result["function_count"] = function_count
    
    # 복잡도 점수 계산
    complexity_score = 0.0
    
    # 코드 라인 수 기반 복잡도
    if lines_of_code == 0:
        complexity_score += 0.0
    elif lines_of_code < 1000:
        complexity_score += 0.5
    elif lines_of_code < 5000:
        complexity_score += 1.5
    elif lines_of_code < 10000:
        complexity_score += 3.0
    else:
        complexity_score += 5.0
    
    # 패키지 수 기반 복잡도
    if target == TargetDatabase.AURORA_POSTGRESQL:
        # PostgreSQL: 스키마 또는 확장으로 변환
        complexity_score += package_count * 1.0
    elif target == TargetDatabase.AURORA_MYSQL:
        # MySQL: 저장 프로시저로 변환 또는 애플리케이션 이관 (더 어려움)
        complexity_score += package_count * 2.0
    
    # 대규모 PL/SQL 변환 여부
    total_objects = procedure_count + package_count
    if total_objects > 10:
        complexity_score += 1.0
    
    result["complexity_score"] = min(complexity_score, 10.0)
    
    # 변환 전략 제공
    conversion_strategy = []
    
    if target == TargetDatabase.RDS_ORACLE:
        conversion_strategy.append("PL/SQL 코드는 그대로 사용 가능합니다.")
    
    elif target == TargetDatabase.AURORA_POSTGRESQL:
        if lines_of_code > 0:
            conversion_strategy.append("PL/SQL을 PL/pgSQL로 변환해야 합니다.")
        if package_count > 0:
            conversion_strategy.append(f"{package_count}개의 패키지를 PostgreSQL 스키마 또는 확장으로 변환해야 합니다.")
        if procedure_count > 0 or function_count > 0:
            conversion_strategy.append("프로시저와 함수를 PostgreSQL 함수로 변환해야 합니다.")
    
    elif target == TargetDatabase.AURORA_MYSQL:
        if lines_of_code > 0:
            conversion_strategy.append("PL/SQL을 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.")
        if package_count > 0:
            conversion_strategy.append(f"{package_count}개의 패키지를 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.")
        if procedure_count > 0 or function_count > 0:
            conversion_strategy.append("프로시저와 함수를 MySQL 저장 프로시저로 변환해야 합니다.")
    
    result["conversion_strategy"] = conversion_strategy
    
    return result
