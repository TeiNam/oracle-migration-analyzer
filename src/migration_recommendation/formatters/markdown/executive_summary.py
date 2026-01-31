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
            
            base_summary = f"""## 요약

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
            
            base_summary = f"""## Summary

| Item | Content |
|------|---------|
| **Recommended Strategy** | {strategy_name} |
| **Estimated Duration** | {summary.estimated_duration} |

### Key Benefits
{benefits_text}

### Key Risks
{risks_text}

> See each section in the main report for details."""
        
        # Refactoring 전략인 경우 접근 방식 가이드 추가
        if summary.recommended_strategy in ["refactor_mysql", "refactor_postgresql"]:
            refactoring_guide = ExecutiveSummaryFormatterMixin._format_refactoring_approach_guide(
                summary.recommended_strategy, language
            )
            return f"{base_summary}\n\n{refactoring_guide}"
        
        return base_summary
    
    @staticmethod
    def _format_refactoring_approach_guide(strategy: str, language: str) -> str:
        """Refactoring 접근 방식 가이드 포맷
        
        Args:
            strategy: 전략 ("refactor_mysql" 또는 "refactor_postgresql")
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            if strategy == "refactor_mysql":
                return """### Refactoring 접근 방식 선택 가이드

Refactoring은 두 가지 접근 방식으로 진행할 수 있습니다:

| 접근 방식 | 개요 | 기간 | 난이도 | 적합한 경우 |
|----------|------|------|--------|------------|
| **Code-level Refactoring** | 기존 데이터 모델 유지, PL/SQL을 애플리케이션으로 변환 | 9-12주 | 중간 | 빠른 마이그레이션, 현재 모델 유지 |
| **Data Model Refactoring** | 데이터 모델 리버스 엔지니어링 후 재설계 | 16-24주 | 높음~매우 높음 | 성능/설계 문제 해결, 장기 유지보수성 |

> **권장**: 대부분의 경우 **Code-level Refactoring**을 먼저 진행하고, 마이그레이션 완료 후 필요시 점진적으로 데이터 모델을 개선하는 것을 권장합니다."""
            else:  # refactor_postgresql
                return """### Refactoring 접근 방식 선택 가이드

Refactoring은 두 가지 접근 방식으로 진행할 수 있습니다:

| 접근 방식 | 개요 | 기간 | 난이도 | 적합한 경우 |
|----------|------|------|--------|------------|
| **Code-level Refactoring** | 기존 데이터 모델 유지, PL/SQL을 PL/pgSQL로 변환 | 9-12주 | 중간 | 빠른 마이그레이션, DB 로직 유지 |
| **Data Model Refactoring** | 데이터 모델 리버스 엔지니어링 후 재설계 | 16-24주 | 높음~매우 높음 | 성능/설계 문제 해결, PostgreSQL 기능 활용 |

> **권장**: 대부분의 경우 **Code-level Refactoring**을 먼저 진행하고, 마이그레이션 완료 후 필요시 점진적으로 데이터 모델을 개선하는 것을 권장합니다."""
        else:  # English
            if strategy == "refactor_mysql":
                return """### Refactoring Approach Selection Guide

Refactoring can be done in two approaches:

| Approach | Overview | Duration | Difficulty | Suitable For |
|----------|----------|----------|------------|--------------|
| **Code-level Refactoring** | Keep existing data model, convert PL/SQL to application | 9-12 weeks | Medium | Fast migration, maintain current model |
| **Data Model Refactoring** | Reverse engineer and redesign data model | 16-24 weeks | High~Very High | Fix performance/design issues, long-term maintainability |

> **Recommendation**: In most cases, start with **Code-level Refactoring** first, then gradually improve the data model after migration if needed."""
            else:  # refactor_postgresql
                return """### Refactoring Approach Selection Guide

Refactoring can be done in two approaches:

| Approach | Overview | Duration | Difficulty | Suitable For |
|----------|----------|----------|------------|--------------|
| **Code-level Refactoring** | Keep existing data model, convert PL/SQL to PL/pgSQL | 9-12 weeks | Medium | Fast migration, keep DB logic |
| **Data Model Refactoring** | Reverse engineer and redesign data model | 16-24 weeks | High~Very High | Fix performance/design issues, leverage PostgreSQL features |

> **Recommendation**: In most cases, start with **Code-level Refactoring** first, then gradually improve the data model after migration if needed."""
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """리스트 항목 포맷
        
        Args:
            items: 리스트 항목들
            
        Returns:
            Markdown 리스트 문자열
        """
        return "\n".join([f"- {item}" for item in items])
