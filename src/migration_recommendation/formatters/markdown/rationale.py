"""
Markdown 추천 근거 포맷터

추천 근거 섹션을 Markdown 형식으로 변환합니다.

Note: 이 모듈은 하위 호환성을 위해 유지됩니다.
      실제 구현은 rationale/ 패키지로 모듈화되었습니다.
"""

# 모듈화된 구현에서 re-export
from .rationale import RationaleFormatterMixin

__all__ = ["RationaleFormatterMixin"]
