"""
Markdown 추천 전략 포맷터

추천 전략 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import MigrationRecommendation, MigrationStrategy, AnalysisMetrics
from ...decision_engine import ReplatformReason


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
        
        lines = []
        if language == "ko":
            lines.append(f"# 추천 전략\n")
            lines.append(f"**{info['method_ko']}** → {info['target_ko']}\n")
        else:
            lines.append(f"# Recommended Strategy\n")
            lines.append(f"**{info['method_en']}** → {info['target_en']}\n")
        
        # Replatform 선택 이유 표시
        if strategy == MigrationStrategy.REPLATFORM and recommendation.replatform_reasons:
            lines.append(
                StrategyFormatterMixin._format_replatform_reasons(
                    recommendation.replatform_reasons, language
                )
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_replatform_reasons(reasons: List[str], language: str) -> str:
        """Replatform 선택 이유 포맷
        
        Args:
            reasons: Replatform 선택 이유 코드 목록
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if not reasons:
            return ""
        
        descriptions = (
            ReplatformReason.DESCRIPTIONS_KO if language == "ko" 
            else ReplatformReason.DESCRIPTIONS_EN
        )
        
        lines = []
        if language == "ko":
            lines.append("## Replatform 선택 이유\n")
            lines.append("> **왜 Replatform인가?** 아래 조건 중 하나 이상이 충족되어 ")
            lines.append("> 코드 변환(Refactoring)보다 Replatform이 더 적합합니다.\n")
            lines.append("| 조건 | 설명 |")
            lines.append("|------|------|")
        else:
            lines.append("## Replatform Selection Reasons\n")
            lines.append("> **Why Replatform?** One or more of the following conditions are met, ")
            lines.append("> making Replatform more suitable than code conversion (Refactoring).\n")
            lines.append("| Condition | Description |")
            lines.append("|-----------|-------------|")
        
        # 중복 제거
        unique_reasons = list(dict.fromkeys(reasons))
        
        for reason in unique_reasons:
            description = descriptions.get(reason, reason)
            if language == "ko":
                # 이유 코드를 한국어 조건명으로 변환
                condition_names = {
                    ReplatformReason.HIGH_SQL_COMPLEXITY: "SQL 복잡도",
                    ReplatformReason.HIGH_PLSQL_COMPLEXITY: "PL/SQL 복잡도",
                    ReplatformReason.HIGH_COMPLEXITY_RATIO: "고난이도 비율",
                    ReplatformReason.HIGH_COMPLEXITY_COUNT: "고난이도 개수",
                    ReplatformReason.VERY_HIGH_DIFFICULTY: "코드량",
                    ReplatformReason.LARGE_PLSQL_COUNT: "오브젝트 개수",
                }
                condition_name = condition_names.get(reason, reason)
            else:
                condition_names = {
                    ReplatformReason.HIGH_SQL_COMPLEXITY: "SQL Complexity",
                    ReplatformReason.HIGH_PLSQL_COMPLEXITY: "PL/SQL Complexity",
                    ReplatformReason.HIGH_COMPLEXITY_RATIO: "High Complexity Ratio",
                    ReplatformReason.HIGH_COMPLEXITY_COUNT: "High Complexity Count",
                    ReplatformReason.VERY_HIGH_DIFFICULTY: "Code Volume",
                    ReplatformReason.LARGE_PLSQL_COUNT: "Object Count",
                }
                condition_name = condition_names.get(reason, reason)
            
            lines.append(f"| {condition_name} | {description} |")
        
        lines.append("")
        
        if language == "ko":
            lines.append("> 💡 **참고**: Replatform은 코드 변경을 최소화하여 마이그레이션 위험을 낮추고,")
            lines.append("> 기존 비즈니스 로직을 그대로 유지할 수 있습니다.")
        else:
            lines.append("> 💡 **Note**: Replatform minimizes code changes to reduce migration risk")
            lines.append("> and preserves existing business logic.")
        
        lines.append("")
        return "\n".join(lines)
    
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
