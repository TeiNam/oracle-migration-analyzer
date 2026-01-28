"""
Markdown 추천 전략 포맷터

추천 전략 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import MigrationRecommendation, MigrationStrategy, AnalysisMetrics


class StrategyFormatterMixin:
    """추천 전략 포맷터 믹스인"""
    
    @staticmethod
    def _format_strategy(
        recommendation: MigrationRecommendation,
        metrics: AnalysisMetrics,  # noqa: ARG004 - 향후 확장용
        language: str
    ) -> str:
        """추천 전략 섹션 포맷 (새 양식)
        
        Args:
            recommendation: 마이그레이션 추천 데이터
            metrics: 분석 메트릭 데이터 (향후 확장용)
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        strategy = recommendation.recommended_strategy
        
        # 전략 방법 및 타겟 DB
        strategy_info = {
            MigrationStrategy.REPLATFORM: {
                "method_ko": "Replatform (리플랫폼)",
                "method_en": "Replatform",
                "target_ko": "RDS for Oracle SE2",
                "target_en": "RDS for Oracle SE2"
            },
            MigrationStrategy.REFACTOR_MYSQL: {
                "method_ko": "Refactoring (리팩토링)",
                "method_en": "Refactoring",
                "target_ko": "Aurora MySQL",
                "target_en": "Aurora MySQL"
            },
            MigrationStrategy.REFACTOR_POSTGRESQL: {
                "method_ko": "Refactoring (리팩토링)",
                "method_en": "Refactoring",
                "target_ko": "Aurora PostgreSQL",
                "target_en": "Aurora PostgreSQL"
            }
        }
        
        info = strategy_info[strategy]
        
        if language == "ko":
            return f"# 추천 전략\n\n**{info['method_ko']}** → {info['target_ko']}\n"
        else:
            return f"# Recommended Strategy\n\n**{info['method_en']}** → {info['target_en']}\n"
    
    @staticmethod
    def _format_toc(language: str) -> str:
        """목차 섹션 포맷
        
        Args:
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return """---

## 목차

### Part 1: 의사결정 정보
1. [분석 신뢰도](#-분석-신뢰도-및-데이터-가용성)
2. [데이터베이스 개요](#데이터베이스-개요)
3. [Oracle 기능 사용 현황](#oracle-기능-사용-현황)
4. [추천 전략 및 근거](#추천-전략)
5. [최종 난이도 판정](#최종-난이도-판정)
6. [대안 전략 비교](#대안-전략)
7. [위험 요소 및 완화 방안](#위험-요소-및-완화-방안)

### Part 2: 기술 상세 (부록)
- [인스턴스 추천](#인스턴스-추천)
- [분석 메트릭](#분석-메트릭-부록)
"""
        else:
            return """---

## Table of Contents

### Part 1: Decision Information
1. [Analysis Confidence](#-analysis-confidence--data-availability)
2. [Database Overview](#database-overview)
3. [Oracle Feature Usage](#oracle-feature-usage)
4. [Recommended Strategy & Rationale](#recommended-strategy)
5. [Final Difficulty Assessment](#final-difficulty-assessment)
6. [Alternative Strategies](#alternative-strategies)
7. [Risks and Mitigation](#risks-and-mitigation)

### Part 2: Technical Details (Appendix)
- [Instance Recommendation](#instance-recommendation)
- [Analysis Metrics](#analysis-metrics-appendix)
"""
