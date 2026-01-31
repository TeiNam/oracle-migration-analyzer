"""
위험 요소 생성기

마이그레이션 전략별 위험 요소를 분석 데이터 기반으로 동적 생성합니다.

Note: 이 모듈은 하위 호환성을 위해 유지됩니다.
      실제 구현은 risk_generator/ 패키지로 모듈화되었습니다.
"""

# 모듈화된 구현에서 re-export
from .risk_generator import RiskGenerator, RiskCandidate

__all__ = ["RiskGenerator", "RiskCandidate"]
