"""
위험 요소 생성기 - 기본 클래스 및 상수

공통 상수와 기본 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass
from typing import Dict
from ...data_models import Risk


@dataclass
class RiskCandidate:
    """위험 후보 (우선순위 정렬용)"""
    risk: Risk
    priority_score: float  # 높을수록 중요


# 심각도별 기본 점수
SEVERITY_SCORES: Dict[str, float] = {"high": 3.0, "medium": 2.0, "low": 1.0}

# 카테고리별 기본 점수 (중요도)
CATEGORY_SCORES: Dict[str, float] = {
    "technical": 1.2,
    "performance": 1.1,
    "operational": 1.0,
    "cost": 0.9,
    "schedule": 0.8
}


def calculate_priority(
    severity: str, 
    category: str, 
    data_weight: float = 1.0
) -> float:
    """우선순위 점수 계산"""
    base = SEVERITY_SCORES.get(severity, 1.0)
    cat_mult = CATEGORY_SCORES.get(category, 1.0)
    return base * cat_mult * data_weight
