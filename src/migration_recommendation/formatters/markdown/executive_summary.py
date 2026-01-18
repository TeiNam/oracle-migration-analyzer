"""
Markdown Executive Summary 포맷터

Executive Summary 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import ExecutiveSummary


class ExecutiveSummaryFormatterMixin:
    """Executive Summary 포맷터 믹스인"""
    
    @staticmethod
    def _format_executive_summary(summary: ExecutiveSummary, language: str) -> str:
        """Executive Summary 섹션 포맷
        
        Args:
            summary: Executive Summary 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return f"""# 요약

{summary.summary_text}

## 핵심 요약

- **추천 전략**: {summary.recommended_strategy}
- **예상 기간**: {summary.estimated_duration}

### 주요 이점
{ExecutiveSummaryFormatterMixin._format_list(summary.key_benefits)}

### 주요 위험
{ExecutiveSummaryFormatterMixin._format_list(summary.key_risks)}
"""
        else:  # English
            return f"""# Executive Summary

{summary.summary_text}

## Key Summary

- **Recommended Strategy**: {summary.recommended_strategy}
- **Estimated Duration**: {summary.estimated_duration}

### Key Benefits
{ExecutiveSummaryFormatterMixin._format_list(summary.key_benefits)}

### Key Risks
{ExecutiveSummaryFormatterMixin._format_list(summary.key_risks)}
"""
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """리스트 항목 포맷
        
        Args:
            items: 리스트 항목들
            
        Returns:
            Markdown 리스트 문자열
        """
        return "\n".join([f"- {item}" for item in items])
