"""
Markdown 추천 전략 포맷터

추천 전략 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import MigrationRecommendation, MigrationStrategy


class StrategyFormatterMixin:
    """추천 전략 포맷터 믹스인"""
    
    @staticmethod
    def _format_strategy(recommendation: MigrationRecommendation, language: str) -> str:
        """추천 전략 섹션 포맷
        
        Args:
            recommendation: 마이그레이션 추천 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        strategy_names = {
            "ko": {
                MigrationStrategy.REPLATFORM: "RDS for Oracle SE2 (리플랫폼)",
                MigrationStrategy.REFACTOR_MYSQL: "Aurora MySQL (리팩토링)",
                MigrationStrategy.REFACTOR_POSTGRESQL: "Aurora PostgreSQL (리팩토링)"
            },
            "en": {
                MigrationStrategy.REPLATFORM: "RDS for Oracle SE2 (Replatform)",
                MigrationStrategy.REFACTOR_MYSQL: "Aurora MySQL (Refactoring)",
                MigrationStrategy.REFACTOR_POSTGRESQL: "Aurora PostgreSQL (Refactoring)"
            }
        }
        
        strategy_name = strategy_names[language][recommendation.recommended_strategy]
        confidence = recommendation.confidence_level
        
        confidence_names = {
            "ko": {
                "high": "높음",
                "medium": "중간",
                "low": "낮음"
            },
            "en": {
                "high": "high",
                "medium": "medium",
                "low": "low"
            }
        }
        
        confidence_text = confidence_names[language].get(confidence, confidence)
        
        if language == "ko":
            return f"""# 추천 전략

## {strategy_name}

**신뢰도**: {confidence_text}

이 전략은 AWR/STATSPACK의 누적 데이터 분석을 통해 작성되었습니다.
"""
        else:
            return f"""# Recommended Strategy

## {strategy_name}

**Confidence Level**: {confidence_text}

This strategy has been selected based on AWR/STATSPACK cumulative data analysis.
"""
    
    @staticmethod
    def _format_toc(language: str) -> str:
        """목차 섹션 포맷
        
        Args:
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return """# 목차

1. [요약](#요약)
2. [추천 전략](#추천-전략)
3. [인스턴스 추천](#인스턴스-추천)
4. [추천 근거](#추천-근거)
5. [대안 전략](#대안-전략)
6. [위험 요소 및 완화 방안](#위험-요소-및-완화-방안)
7. [마이그레이션 로드맵](#마이그레이션-로드맵)
8. [분석 메트릭 (부록)](#분석-메트릭-부록)
"""
        else:
            return """# Table of Contents

1. [Executive Summary](#executive-summary)
2. [Recommended Strategy](#recommended-strategy)
3. [Instance Recommendation](#instance-recommendation)
4. [Rationales](#rationales)
5. [Alternative Strategies](#alternative-strategies)
6. [Risks and Mitigation](#risks-and-mitigation)
7. [Migration Roadmap](#migration-roadmap)
8. [Analysis Metrics (Appendix)](#analysis-metrics-appendix)
"""
