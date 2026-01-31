"""
Markdown 추천 전략 포맷터

추천 전략 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List, Optional
from ...data_models import (
    MigrationRecommendation, 
    MigrationStrategy, 
    AnalysisMetrics,
    ReplatformSubStrategy
)
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
        sub_strategy = recommendation.replatform_sub_strategy
        
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
        
        # Replatform 세부 전략에 따른 타겟 조정
        if strategy == MigrationStrategy.REPLATFORM and sub_strategy:
            target_ko, target_en = StrategyFormatterMixin._get_replatform_target(sub_strategy)
            info["target_ko"] = target_ko
            info["target_en"] = target_en
        
        lines = []
        if language == "ko":
            lines.append(f"# 추천 전략\n")
            lines.append(f"**{info['method_ko']}** → {info['target_ko']}\n")
        else:
            lines.append(f"# Recommended Strategy\n")
            lines.append(f"**{info['method_en']}** → {info['target_en']}\n")
        
        # Replatform 세부 전략 가이드 표시
        if strategy == MigrationStrategy.REPLATFORM:
            sub_strategy_guide = StrategyFormatterMixin._format_replatform_sub_strategy_guide(
                sub_strategy, 
                recommendation.replatform_sub_strategy_reasons,
                language
            )
            if sub_strategy_guide:
                lines.append(sub_strategy_guide)
        
        # Replatform 선택 이유 표시
        if strategy == MigrationStrategy.REPLATFORM and recommendation.replatform_reasons:
            lines.append(
                StrategyFormatterMixin._format_replatform_reasons(
                    recommendation.replatform_reasons, language
                )
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_replatform_target(sub_strategy: ReplatformSubStrategy) -> tuple:
        """Replatform 세부 전략에 따른 타겟 이름 반환
        
        Args:
            sub_strategy: Replatform 세부 전략
            
        Returns:
            (한국어 타겟명, 영어 타겟명) 튜플
        """
        targets = {
            ReplatformSubStrategy.EC2_REHOST: (
                "EC2 Oracle (Lift & Shift)",
                "EC2 Oracle (Lift & Shift)"
            ),
            ReplatformSubStrategy.RDS_CUSTOM_ORACLE: (
                "RDS Custom for Oracle",
                "RDS Custom for Oracle"
            ),
            ReplatformSubStrategy.RDS_ORACLE: (
                "RDS for Oracle SE2",
                "RDS for Oracle SE2"
            )
        }
        return targets.get(sub_strategy, ("RDS for Oracle SE2", "RDS for Oracle SE2"))
    
    @staticmethod
    def _format_replatform_sub_strategy_guide(
        sub_strategy: Optional[ReplatformSubStrategy],
        reasons: Optional[List[str]],
        language: str
    ) -> str:
        """Replatform 세부 전략 가이드 포맷
        
        Args:
            sub_strategy: Replatform 세부 전략
            reasons: 세부 전략 선택 이유
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if not sub_strategy:
            return ""
        
        lines = []
        
        if language == "ko":
            lines.append("## Replatform 세부 전략 선택 가이드\n")
            lines.append("> 시스템 복잡도와 요구사항에 따라 세 가지 Replatform 옵션 중 하나를 선택합니다.\n")
            
            # 세부 전략 비교 테이블
            lines.append("| 옵션 | 설명 | 적합한 경우 | 관리 부담 |")
            lines.append("|------|------|------------|----------|")
            lines.append("| **EC2 Rehost** | EC2에서 Oracle 직접 운영 | RAC 필요, OS 커스터마이징 필요 | 🔴 높음 |")
            lines.append("| **RDS Custom** | OS 접근 가능한 관리형 서비스 | OS 접근 필요, 일부 자동화 원함 | 🟠 중간 |")
            lines.append("| **RDS Oracle** | 완전 관리형 서비스 | 표준 구성, 운영 부담 최소화 | 🟢 낮음 |")
            lines.append("")
            
            # 선택된 전략 표시
            strategy_names = {
                ReplatformSubStrategy.EC2_REHOST: "EC2 Rehost (Lift & Shift)",
                ReplatformSubStrategy.RDS_CUSTOM_ORACLE: "RDS Custom for Oracle",
                ReplatformSubStrategy.RDS_ORACLE: "RDS for Oracle SE2"
            }
            selected_name = strategy_names.get(sub_strategy, "RDS for Oracle SE2")
            lines.append(f"### 선택된 세부 전략: **{selected_name}**\n")
            
            # 선택 이유 표시
            if reasons:
                lines.append("**선택 이유:**")
                for reason in reasons:
                    lines.append(f"- {reason}")
                lines.append("")
            
            # 세부 전략별 추가 안내
            if sub_strategy == ReplatformSubStrategy.EC2_REHOST:
                lines.append("> 💡 **EC2 Rehost 특징**: 코드 변경 없이 가장 빠른 마이그레이션이 가능하지만, ")
                lines.append("> 인프라 관리(패치, 백업, 모니터링)를 직접 수행해야 합니다. ")
                lines.append("> Oracle RAC, EE 고급 기능 등 모든 기능을 그대로 사용할 수 있습니다.")
            elif sub_strategy == ReplatformSubStrategy.RDS_CUSTOM_ORACLE:
                lines.append("> 💡 **RDS Custom 특징**: AWS 관리형 서비스의 이점을 누리면서도 ")
                lines.append("> OS 레벨 접근이 가능합니다. 서드파티 에이전트 설치나 특수 설정이 필요한 경우 적합합니다.")
            else:  # RDS_ORACLE
                lines.append("> 💡 **RDS Oracle 특징**: 완전 관리형 서비스로 운영 부담이 가장 적습니다. ")
                lines.append("> 자동 백업, 패치, 모니터링을 AWS가 관리합니다. SE2 라이선스 포함 옵션도 있습니다.")
            
            lines.append("")
        else:
            lines.append("## Replatform Sub-Strategy Selection Guide\n")
            lines.append("> Choose one of three Replatform options based on system complexity and requirements.\n")
            
            lines.append("| Option | Description | Suitable For | Management Overhead |")
            lines.append("|--------|-------------|--------------|---------------------|")
            lines.append("| **EC2 Rehost** | Run Oracle directly on EC2 | RAC needed, OS customization | 🔴 High |")
            lines.append("| **RDS Custom** | Managed service with OS access | OS access needed, some automation | 🟠 Medium |")
            lines.append("| **RDS Oracle** | Fully managed service | Standard config, minimal ops | 🟢 Low |")
            lines.append("")
            
            strategy_names = {
                ReplatformSubStrategy.EC2_REHOST: "EC2 Rehost (Lift & Shift)",
                ReplatformSubStrategy.RDS_CUSTOM_ORACLE: "RDS Custom for Oracle",
                ReplatformSubStrategy.RDS_ORACLE: "RDS for Oracle SE2"
            }
            selected_name = strategy_names.get(sub_strategy, "RDS for Oracle SE2")
            lines.append(f"### Selected Sub-Strategy: **{selected_name}**\n")
            
            if reasons:
                lines.append("**Selection Reasons:**")
                for reason in reasons:
                    lines.append(f"- {reason}")
                lines.append("")
            
            if sub_strategy == ReplatformSubStrategy.EC2_REHOST:
                lines.append("> 💡 **EC2 Rehost Features**: Fastest migration with no code changes, ")
                lines.append("> but requires direct infrastructure management (patching, backup, monitoring). ")
                lines.append("> All Oracle features including RAC and EE advanced features are available.")
            elif sub_strategy == ReplatformSubStrategy.RDS_CUSTOM_ORACLE:
                lines.append("> 💡 **RDS Custom Features**: Benefits of AWS managed service with OS-level access. ")
                lines.append("> Suitable when third-party agents or special configurations are needed.")
            else:
                lines.append("> 💡 **RDS Oracle Features**: Fully managed service with minimal operational overhead. ")
                lines.append("> AWS handles automatic backup, patching, and monitoring. License-included option available.")
            
            lines.append("")
        
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
                    ReplatformReason.LARGE_CODEBASE_HIGH_COMPLEXITY: "코드량+복잡도",
                    ReplatformReason.LARGE_PLSQL_COUNT: "오브젝트 개수",
                    ReplatformReason.HIGH_RISK_ORACLE_PACKAGES: "고위험 패키지",
                }
                condition_name = condition_names.get(reason, reason)
            else:
                condition_names = {
                    ReplatformReason.HIGH_SQL_COMPLEXITY: "SQL Complexity",
                    ReplatformReason.HIGH_PLSQL_COMPLEXITY: "PL/SQL Complexity",
                    ReplatformReason.HIGH_COMPLEXITY_RATIO: "High Complexity Ratio",
                    ReplatformReason.HIGH_COMPLEXITY_COUNT: "High Complexity Count",
                    ReplatformReason.LARGE_CODEBASE_HIGH_COMPLEXITY: "Code Volume + Complexity",
                    ReplatformReason.LARGE_PLSQL_COUNT: "Object Count",
                    ReplatformReason.HIGH_RISK_ORACLE_PACKAGES: "High-Risk Packages",
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
