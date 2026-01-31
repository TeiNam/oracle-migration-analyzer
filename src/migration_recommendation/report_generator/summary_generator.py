"""
Executive Summary 생성기

마이그레이션 추천의 Executive Summary를 생성합니다.

Note: 이 모듈은 하위 호환성을 위해 유지됩니다.
      실제 구현은 summary/ 패키지로 모듈화되었습니다.
"""

# 모듈화된 구현에서 re-export
from .summary import SummaryGenerator

__all__ = ["SummaryGenerator"]
