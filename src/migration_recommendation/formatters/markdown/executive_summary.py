"""
Markdown Executive Summary 포맷터

Executive Summary 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import ExecutiveSummary, MigrationRecommendation


class ExecutiveSummaryFormatterMixin:
    """Executive Summary 포맷터 믹스인"""
    
    @staticmethod
    def _format_executive_summary(summary: ExecutiveSummary, language: str) -> str:
        """Executive Summary 섹션 포맷 (핵심 요약)
        
        본문 내용을 핵심만 요약하여 표시합니다.
        
        Args:
            summary: Executive Summary 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        # 전략 이름 매핑
        strategy_names = {
            "ko": {
                "replatform": "RDS for Oracle SE2 (Replatform)",
                "refactor_mysql": "Aurora MySQL (Refactoring)",
                "refactor_postgresql": "Aurora PostgreSQL (Refactoring)"
            },
            "en": {
                "replatform": "RDS for Oracle SE2 (Replatform)",
                "refactor_mysql": "Aurora MySQL (Refactoring)",
                "refactor_postgresql": "Aurora PostgreSQL (Refactoring)"
            }
        }
        
        strategy_name = strategy_names[language].get(
            summary.recommended_strategy, 
            summary.recommended_strategy
        )
        
        # 핵심 이점과 위험 (최대 3개씩)
        benefits = summary.key_benefits[:3] if summary.key_benefits else []
        risks = summary.key_risks[:3] if summary.key_risks else []
        
        if language == "ko":
            benefits_text = "\n".join([f"- {b}" for b in benefits]) if benefits else "- 정보 없음"
            risks_text = "\n".join([f"- {r}" for r in risks]) if risks else "- 정보 없음"
            
            return f"""## 요약

| 항목 | 내용 |
|------|------|
| **추천 전략** | {strategy_name} |
| **예상 기간** | {summary.estimated_duration} |

### 핵심 이점
{benefits_text}

### 주요 위험
{risks_text}

> 상세 내용은 본문의 각 섹션을 참조하세요."""
        else:
            benefits_text = "\n".join([f"- {b}" for b in benefits]) if benefits else "- No information"
            risks_text = "\n".join([f"- {r}" for r in risks]) if risks else "- No information"
            
            return f"""## Summary

| Item | Content |
|------|---------|
| **Recommended Strategy** | {strategy_name} |
| **Estimated Duration** | {summary.estimated_duration} |

### Key Benefits
{benefits_text}

### Key Risks
{risks_text}

> See each section in the main report for details."""
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """리스트 항목 포맷
        
        Args:
            items: 리스트 항목들
            
        Returns:
            Markdown 리스트 문자열
        """
        return "\n".join([f"- {item}" for item in items])
