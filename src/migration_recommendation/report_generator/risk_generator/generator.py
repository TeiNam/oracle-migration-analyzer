"""
위험 요소 생성기 - 메인 클래스

RiskGenerator 클래스를 제공합니다.
"""

import logging
from typing import List
from ...data_models import AnalysisMetrics, MigrationStrategy, Risk
from .base import RiskCandidate, SEVERITY_SCORES, CATEGORY_SCORES, calculate_priority
from .technical_risks import collect_technical_risks
from .other_risks import (
    collect_performance_risks,
    collect_operational_risks,
    collect_cost_risks,
    collect_schedule_risks,
)
from .default_risks import ensure_minimum_risks

logger = logging.getLogger(__name__)


class RiskGenerator:
    """
    위험 요소 생성기
    
    분석 데이터 기반으로 전략별 위험 요소를 동적 생성합니다.
    """
    
    # 심각도별 기본 점수
    SEVERITY_SCORES = SEVERITY_SCORES
    
    # 카테고리별 기본 점수 (중요도)
    CATEGORY_SCORES = CATEGORY_SCORES

    def generate_risks(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Risk]:
        """
        위험 요소 생성 (3-5개, 우선순위 기반)
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[Risk]: 위험 요소 리스트 (3-5개)
        """
        candidates: List[RiskCandidate] = []
        
        # 1. 기술적 위험 수집
        candidates.extend(collect_technical_risks(strategy, metrics))
        
        # 2. 성능 위험 수집
        candidates.extend(collect_performance_risks(strategy, metrics))
        
        # 3. 운영 위험 수집
        candidates.extend(collect_operational_risks(strategy, metrics))
        
        # 4. 비용 위험 수집
        candidates.extend(collect_cost_risks(strategy, metrics))
        
        # 5. 일정 위험 수집
        candidates.extend(collect_schedule_risks(strategy, metrics))
        
        # 6. 최소 3개 보장
        candidates = ensure_minimum_risks(candidates, strategy, metrics)
        
        # 우선순위 정렬 후 상위 5개 반환
        candidates.sort(key=lambda x: x.priority_score, reverse=True)
        return [c.risk for c in candidates[:5]]
    
    def _calculate_priority(
        self, 
        severity: str, 
        category: str, 
        data_weight: float = 1.0
    ) -> float:
        """우선순위 점수 계산 (하위 호환성)"""
        return calculate_priority(severity, category, data_weight)
