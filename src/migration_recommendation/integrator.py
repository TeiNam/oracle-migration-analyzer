"""
분석 결과 통합기

DBCSI 분석기와 SQL/PL-SQL 분석기의 결과를 통합하고 메트릭을 추출합니다.

Note:
    이 모듈은 하위 호환성을 위한 래퍼입니다.
    실제 구현은 src/migration_recommendation/integrator/ 패키지에 있습니다.
"""

# 하위 호환성을 위해 기존 import 경로 유지
from src.migration_recommendation.integrator import AnalysisResultIntegrator

__all__ = ["AnalysisResultIntegrator"]
