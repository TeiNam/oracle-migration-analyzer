"""
위험 요소 생성기 모듈

마이그레이션 전략별 위험 요소를 분석 데이터 기반으로 동적 생성합니다.
"""

from .generator import RiskGenerator, RiskCandidate

__all__ = ["RiskGenerator", "RiskCandidate"]
