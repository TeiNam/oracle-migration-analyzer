"""
Markdown 대안 전략 포맷터

대안 전략 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import AlternativeStrategy


class AlternativesFormatterMixin:
    """대안 전략 포맷터 믹스인"""
    
    @staticmethod
    def _format_alternatives(alternatives: List[AlternativeStrategy], language: str) -> str:
        """대안 전략 섹션 포맷
        
        Args:
            alternatives: 대안 전략 리스트
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            content = "# 대안 전략\n\n"
            for i, alt in enumerate(alternatives, 1):
                content += f"## 대안 {i}: {alt.strategy.value}\n\n"
                content += "### 장점\n"
                content += AlternativesFormatterMixin._format_list(alt.pros) + "\n"
                content += "### 단점\n"
                content += AlternativesFormatterMixin._format_list(alt.cons) + "\n"
                content += "### 고려사항\n"
                content += AlternativesFormatterMixin._format_list(alt.considerations) + "\n\n"
        else:
            content = "# Alternative Strategies\n\n"
            for i, alt in enumerate(alternatives, 1):
                content += f"## Alternative {i}: {alt.strategy.value}\n\n"
                content += "### Pros\n"
                content += AlternativesFormatterMixin._format_list(alt.pros) + "\n"
                content += "### Cons\n"
                content += AlternativesFormatterMixin._format_list(alt.cons) + "\n"
                content += "### Considerations\n"
                content += AlternativesFormatterMixin._format_list(alt.considerations) + "\n\n"
        
        return content
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """리스트 항목 포맷
        
        Args:
            items: 리스트 항목들
            
        Returns:
            Markdown 리스트 문자열
        """
        return "\n".join([f"- {item}" for item in items])
