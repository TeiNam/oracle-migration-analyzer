"""
기능 호환성 분석 모듈

Oracle 기능의 타겟 데이터베이스별 호환성을 분석합니다.
"""

from typing import Dict, Any, List
from ..data_models import StatspackData, TargetDatabase


def analyze_feature_compatibility(
    data: StatspackData,
    target: TargetDatabase
) -> Dict[str, Any]:
    """
    Oracle 기능 호환성 분석
    
    사용된 Oracle 기능의 타겟 DB별 호환성을 분석합니다.
    
    Args:
        data: Statspack 데이터
        target: 타겟 데이터베이스
    
    Returns:
        Dict[str, Any]: 기능 호환성 분석 결과
            - used_features: 사용된 기능 목록
            - compatibility_score: 호환성 점수 (0-10, 낮을수록 호환성 높음)
            - incompatible_features: 비호환 기능 목록
            - alternatives: 대체 방안
    """
    result: Dict[str, Any] = {
        "used_features": [],
        "compatibility_score": 0.0,
        "incompatible_features": [],
        "alternatives": []
    }
    
    if not data.features:
        return result
    
    # 사용 중인 기능 필터링 (currently_used=True)
    used_features = [f for f in data.features if f.currently_used]
    result["used_features"] = [f.name for f in used_features]
    
    # 기능별 가중치 (마이그레이션 난이도)
    feature_weights = {
        "Partitioning": 1.0,
        "Advanced Compression": 0.5,
        "Real Application Clusters": 2.0,
        "Data Guard": 1.5,
        "Active Data Guard": 1.5,
        "Materialized View": 1.0,
        "Advanced Security": 1.0,
        "Label Security": 1.5,
        "Database Vault": 1.5,
        "OLAP": 2.0,
        "Spatial": 1.5,
    }
    
    total_weight = 0.0
    incompatible_features = []
    alternatives = []
    
    for feature in used_features:
        feature_name = feature.name
        
        # 기능별 가중치 적용
        weight = 0.0
        for key, value in feature_weights.items():
            if key.lower() in feature_name.lower():
                weight = value
                break
        
        if weight == 0.0:
            # 알 수 없는 기능은 기본 가중치 0.3
            weight = 0.3
        
        total_weight += weight
        
        # 타겟별 호환성 평가
        if target == TargetDatabase.RDS_ORACLE:
            # RDS for Oracle은 대부분 호환 (EE 라이선스 필요)
            if "Real Application Clusters" in feature_name:
                incompatible_features.append(feature_name)
                alternatives.append(f"{feature_name}: Multi-AZ 배포로 대체")
        
        elif target == TargetDatabase.AURORA_POSTGRESQL:
            # Aurora PostgreSQL 호환성 평가
            if "Partitioning" in feature_name:
                alternatives.append(f"{feature_name}: 네이티브 파티셔닝 지원")
            elif "Advanced Compression" in feature_name:
                alternatives.append(f"{feature_name}: TOAST 압축 사용")
            elif "Real Application Clusters" in feature_name:
                alternatives.append(f"{feature_name}: Multi-AZ 클러스터 (자동)")
            elif "Materialized View" in feature_name:
                alternatives.append(f"{feature_name}: PostgreSQL Materialized View 사용")
            else:
                incompatible_features.append(feature_name)
                alternatives.append(f"{feature_name}: 애플리케이션 레벨에서 구현 필요")
        
        elif target == TargetDatabase.AURORA_MYSQL:
            # Aurora MySQL 호환성 평가 (더 제한적)
            if "Partitioning" in feature_name:
                alternatives.append(f"{feature_name}: 네이티브 파티셔닝 지원 (제한적)")
            elif "Advanced Compression" in feature_name:
                alternatives.append(f"{feature_name}: InnoDB 압축 사용")
            elif "Real Application Clusters" in feature_name:
                alternatives.append(f"{feature_name}: Multi-AZ 클러스터 (자동)")
            else:
                incompatible_features.append(feature_name)
                alternatives.append(f"{feature_name}: 애플리케이션 레벨에서 구현 필요")
    
    result["compatibility_score"] = min(total_weight, 10.0)
    result["incompatible_features"] = incompatible_features
    result["alternatives"] = alternatives
    
    return result
