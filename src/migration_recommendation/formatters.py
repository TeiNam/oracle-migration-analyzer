"""
마이그레이션 추천 리포트 포맷터 모듈

이 모듈은 마이그레이션 추천 결과를 다양한 형식(Markdown, JSON)으로 변환합니다.
"""

import json
from typing import List, Dict, Any
from .data_models import (
    MigrationRecommendation,
    MigrationStrategy,
    Rationale,
    AlternativeStrategy,
    Risk,
    MigrationRoadmap,
    ExecutiveSummary,
    AnalysisMetrics
)


class MarkdownReportFormatter:
    """Markdown 리포트 포맷터"""
    
    def format(
        self,
        recommendation: MigrationRecommendation,
        language: str = "ko"
    ) -> str:
        """
        추천 리포트를 Markdown 형식으로 변환합니다.
        
        구조:
        1. Executive Summary
        2. 목차
        3. 추천 전략
        4. 추천 근거
        5. 대안 전략
        6. 위험 요소 및 완화 방안
        7. 마이그레이션 로드맵
        8. 분석 메트릭 (부록)
        
        Args:
            recommendation: 추천 리포트
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            str: Markdown 형식 리포트
        """
        sections = []
        
        # 1. Executive Summary
        sections.append(self._format_executive_summary(recommendation.executive_summary, language))
        
        # 2. 목차
        sections.append(self._format_toc(language))
        
        # 3. 추천 전략
        sections.append(self._format_strategy(recommendation, language))
        
        # 4. 추천 근거
        sections.append(self._format_rationales(recommendation.rationales, language))
        
        # 5. 대안 전략
        sections.append(self._format_alternatives(recommendation.alternative_strategies, language))
        
        # 6. 위험 요소
        sections.append(self._format_risks(recommendation.risks, language))
        
        # 7. 마이그레이션 로드맵
        sections.append(self._format_roadmap(recommendation.roadmap, language))
        
        # 8. 분석 메트릭 (부록)
        sections.append(self._format_metrics(recommendation.metrics, language))
        
        return "\n\n".join(sections)
    
    def _format_executive_summary(self, summary: ExecutiveSummary, language: str) -> str:
        """Executive Summary 섹션 포맷"""
        if language == "ko":
            return f"""# Executive Summary

{summary.summary_text}

## 핵심 요약

- **추천 전략**: {summary.recommended_strategy}
- **예상 기간**: {summary.estimated_duration}

### 주요 이점
{self._format_list(summary.key_benefits)}

### 주요 위험
{self._format_list(summary.key_risks)}
"""
        else:  # English
            return f"""# Executive Summary

{summary.summary_text}

## Key Summary

- **Recommended Strategy**: {summary.recommended_strategy}
- **Estimated Duration**: {summary.estimated_duration}

### Key Benefits
{self._format_list(summary.key_benefits)}

### Key Risks
{self._format_list(summary.key_risks)}
"""
    
    def _format_toc(self, language: str) -> str:
        """목차 섹션 포맷"""
        if language == "ko":
            return """# 목차

1. [Executive Summary](#executive-summary)
2. [추천 전략](#추천-전략)
3. [추천 근거](#추천-근거)
4. [대안 전략](#대안-전략)
5. [위험 요소 및 완화 방안](#위험-요소-및-완화-방안)
6. [마이그레이션 로드맵](#마이그레이션-로드맵)
7. [분석 메트릭 (부록)](#분석-메트릭-부록)
"""
        else:
            return """# Table of Contents

1. [Executive Summary](#executive-summary)
2. [Recommended Strategy](#recommended-strategy)
3. [Rationales](#rationales)
4. [Alternative Strategies](#alternative-strategies)
5. [Risks and Mitigation](#risks-and-mitigation)
6. [Migration Roadmap](#migration-roadmap)
7. [Analysis Metrics (Appendix)](#analysis-metrics-appendix)
"""
    
    def _format_strategy(self, recommendation: MigrationRecommendation, language: str) -> str:
        """추천 전략 섹션 포맷"""
        strategy_names = {
            "ko": {
                MigrationStrategy.REPLATFORM: "RDS for Oracle SE2 (Replatform)",
                MigrationStrategy.REFACTOR_MYSQL: "Aurora MySQL (Refactoring)",
                MigrationStrategy.REFACTOR_POSTGRESQL: "Aurora PostgreSQL (Refactoring)"
            },
            "en": {
                MigrationStrategy.REPLATFORM: "RDS for Oracle SE2 (Replatform)",
                MigrationStrategy.REFACTOR_MYSQL: "Aurora MySQL (Refactoring)",
                MigrationStrategy.REFACTOR_POSTGRESQL: "Aurora PostgreSQL (Refactoring)"
            }
        }
        
        strategy_name = strategy_names[language][recommendation.recommended_strategy]
        confidence = recommendation.confidence_level
        
        if language == "ko":
            return f"""# 추천 전략

## {strategy_name}

**신뢰도**: {confidence}

이 전략은 귀사의 Oracle 데이터베이스 시스템 분석 결과를 바탕으로 선정되었습니다.
"""
        else:
            return f"""# Recommended Strategy

## {strategy_name}

**Confidence Level**: {confidence}

This strategy has been selected based on the analysis of your Oracle database system.
"""
    
    def _format_rationales(self, rationales: List[Rationale], language: str) -> str:
        """추천 근거 섹션 포맷"""
        if language == "ko":
            content = "# 추천 근거\n\n"
            for i, rationale in enumerate(rationales, 1):
                content += f"## {i}. {rationale.reason}\n\n"
                content += f"**카테고리**: {rationale.category}\n\n"
                if rationale.supporting_data:
                    content += "**근거 데이터**:\n"
                    for key, value in rationale.supporting_data.items():
                        content += f"- {key}: {value}\n"
                content += "\n"
        else:
            content = "# Rationales\n\n"
            for i, rationale in enumerate(rationales, 1):
                content += f"## {i}. {rationale.reason}\n\n"
                content += f"**Category**: {rationale.category}\n\n"
                if rationale.supporting_data:
                    content += "**Supporting Data**:\n"
                    for key, value in rationale.supporting_data.items():
                        content += f"- {key}: {value}\n"
                content += "\n"
        
        return content
    
    def _format_alternatives(self, alternatives: List[AlternativeStrategy], language: str) -> str:
        """대안 전략 섹션 포맷"""
        if language == "ko":
            content = "# 대안 전략\n\n"
            for i, alt in enumerate(alternatives, 1):
                content += f"## 대안 {i}: {alt.strategy.value}\n\n"
                content += "### 장점\n"
                content += self._format_list(alt.pros) + "\n"
                content += "### 단점\n"
                content += self._format_list(alt.cons) + "\n"
                content += "### 고려사항\n"
                content += self._format_list(alt.considerations) + "\n\n"
        else:
            content = "# Alternative Strategies\n\n"
            for i, alt in enumerate(alternatives, 1):
                content += f"## Alternative {i}: {alt.strategy.value}\n\n"
                content += "### Pros\n"
                content += self._format_list(alt.pros) + "\n"
                content += "### Cons\n"
                content += self._format_list(alt.cons) + "\n"
                content += "### Considerations\n"
                content += self._format_list(alt.considerations) + "\n\n"
        
        return content
    
    def _format_risks(self, risks: List[Risk], language: str) -> str:
        """위험 요소 섹션 포맷"""
        if language == "ko":
            content = "# 위험 요소 및 완화 방안\n\n"
            for i, risk in enumerate(risks, 1):
                content += f"## 위험 {i}: {risk.description}\n\n"
                content += f"**카테고리**: {risk.category}\n\n"
                content += f"**심각도**: {risk.severity}\n\n"
                content += f"**완화 방안**: {risk.mitigation}\n\n"
        else:
            content = "# Risks and Mitigation\n\n"
            for i, risk in enumerate(risks, 1):
                content += f"## Risk {i}: {risk.description}\n\n"
                content += f"**Category**: {risk.category}\n\n"
                content += f"**Severity**: {risk.severity}\n\n"
                content += f"**Mitigation**: {risk.mitigation}\n\n"
        
        return content
    
    def _format_roadmap(self, roadmap: MigrationRoadmap, language: str) -> str:
        """마이그레이션 로드맵 섹션 포맷"""
        if language == "ko":
            content = f"# 마이그레이션 로드맵\n\n"
            content += f"**총 예상 기간**: {roadmap.total_estimated_duration}\n\n"
            
            for phase in roadmap.phases:
                content += f"## Phase {phase.phase_number}: {phase.phase_name}\n\n"
                content += f"**예상 기간**: {phase.estimated_duration}\n\n"
                content += "**주요 작업**:\n"
                content += self._format_list(phase.tasks) + "\n"
                content += "**필요 리소스**:\n"
                content += self._format_list(phase.required_resources) + "\n\n"
        else:
            content = f"# Migration Roadmap\n\n"
            content += f"**Total Estimated Duration**: {roadmap.total_estimated_duration}\n\n"
            
            for phase in roadmap.phases:
                content += f"## Phase {phase.phase_number}: {phase.phase_name}\n\n"
                content += f"**Estimated Duration**: {phase.estimated_duration}\n\n"
                content += "**Key Tasks**:\n"
                content += self._format_list(phase.tasks) + "\n"
                content += "**Required Resources**:\n"
                content += self._format_list(phase.required_resources) + "\n\n"
        
        return content
    
    def _format_metrics(self, metrics: AnalysisMetrics, language: str) -> str:
        """분석 메트릭 섹션 포맷"""
        if language == "ko":
            return f"""# 분석 메트릭 (부록)

## 성능 메트릭

- **평균 CPU 사용률**: {metrics.avg_cpu_usage:.1f}%
- **평균 I/O 부하**: {metrics.avg_io_load:.1f} IOPS
- **평균 메모리 사용량**: {metrics.avg_memory_usage:.1f} GB

## 코드 복잡도 메트릭

- **평균 SQL 복잡도**: {metrics.avg_sql_complexity:.2f}
- **평균 PL/SQL 복잡도**: {metrics.avg_plsql_complexity:.2f}
- **복잡도 7.0 이상 SQL 개수**: {metrics.high_complexity_sql_count} / {metrics.total_sql_count}
- **복잡도 7.0 이상 PL/SQL 개수**: {metrics.high_complexity_plsql_count} / {metrics.total_plsql_count}
- **복잡 오브젝트 비율**: {metrics.high_complexity_ratio*100:.1f}%
- **BULK 연산 개수**: {metrics.bulk_operation_count}
"""
        else:
            return f"""# Analysis Metrics (Appendix)

## Performance Metrics

- **Average CPU Usage**: {metrics.avg_cpu_usage:.1f}%
- **Average I/O Load**: {metrics.avg_io_load:.1f} IOPS
- **Average Memory Usage**: {metrics.avg_memory_usage:.1f} GB

## Code Complexity Metrics

- **Average SQL Complexity**: {metrics.avg_sql_complexity:.2f}
- **Average PL/SQL Complexity**: {metrics.avg_plsql_complexity:.2f}
- **High Complexity SQL Count**: {metrics.high_complexity_sql_count} / {metrics.total_sql_count}
- **High Complexity PL/SQL Count**: {metrics.high_complexity_plsql_count} / {metrics.total_plsql_count}
- **High Complexity Ratio**: {metrics.high_complexity_ratio*100:.1f}%
- **BULK Operation Count**: {metrics.bulk_operation_count}
"""
    
    def _format_list(self, items: List[str]) -> str:
        """리스트 항목 포맷"""
        return "\n".join([f"- {item}" for item in items])


class JSONReportFormatter:
    """JSON 리포트 포맷터"""
    
    def format(
        self,
        recommendation: MigrationRecommendation
    ) -> str:
        """
        추천 리포트를 JSON 형식으로 변환합니다.
        
        구조:
        {
          "recommended_strategy": "...",
          "confidence_level": "...",
          "executive_summary": {...},
          "rationales": [...],
          "alternative_strategies": [...],
          "risks": [...],
          "roadmap": {...},
          "metrics": {...}
        }
        
        Args:
            recommendation: 추천 리포트
            
        Returns:
            str: JSON 형식 리포트
        """
        data = {
            "recommended_strategy": recommendation.recommended_strategy.value,
            "confidence_level": recommendation.confidence_level,
            "executive_summary": self._serialize_executive_summary(recommendation.executive_summary),
            "rationales": [self._serialize_rationale(r) for r in recommendation.rationales],
            "alternative_strategies": [self._serialize_alternative(a) for a in recommendation.alternative_strategies],
            "risks": [self._serialize_risk(r) for r in recommendation.risks],
            "roadmap": self._serialize_roadmap(recommendation.roadmap),
            "metrics": self._serialize_metrics(recommendation.metrics)
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _serialize_executive_summary(self, summary: ExecutiveSummary) -> Dict[str, Any]:
        """Executive Summary 직렬화"""
        return {
            "recommended_strategy": summary.recommended_strategy,
            "estimated_duration": summary.estimated_duration,
            "key_benefits": summary.key_benefits,
            "key_risks": summary.key_risks,
            "summary_text": summary.summary_text
        }
    
    def _serialize_rationale(self, rationale: Rationale) -> Dict[str, Any]:
        """Rationale 직렬화"""
        return {
            "category": rationale.category,
            "reason": rationale.reason,
            "supporting_data": rationale.supporting_data
        }
    
    def _serialize_alternative(self, alternative: AlternativeStrategy) -> Dict[str, Any]:
        """AlternativeStrategy 직렬화"""
        return {
            "strategy": alternative.strategy.value,
            "pros": alternative.pros,
            "cons": alternative.cons,
            "considerations": alternative.considerations
        }
    
    def _serialize_risk(self, risk: Risk) -> Dict[str, Any]:
        """Risk 직렬화"""
        return {
            "category": risk.category,
            "description": risk.description,
            "severity": risk.severity,
            "mitigation": risk.mitigation
        }
    
    def _serialize_roadmap(self, roadmap: MigrationRoadmap) -> Dict[str, Any]:
        """MigrationRoadmap 직렬화"""
        return {
            "total_estimated_duration": roadmap.total_estimated_duration,
            "phases": [
                {
                    "phase_number": phase.phase_number,
                    "phase_name": phase.phase_name,
                    "tasks": phase.tasks,
                    "estimated_duration": phase.estimated_duration,
                    "required_resources": phase.required_resources
                }
                for phase in roadmap.phases
            ]
        }
    
    def _serialize_metrics(self, metrics: AnalysisMetrics) -> Dict[str, Any]:
        """AnalysisMetrics 직렬화"""
        return {
            "performance": {
                "avg_cpu_usage": metrics.avg_cpu_usage,
                "avg_io_load": metrics.avg_io_load,
                "avg_memory_usage": metrics.avg_memory_usage
            },
            "complexity": {
                "avg_sql_complexity": metrics.avg_sql_complexity,
                "avg_plsql_complexity": metrics.avg_plsql_complexity,
                "high_complexity_sql_count": metrics.high_complexity_sql_count,
                "high_complexity_plsql_count": metrics.high_complexity_plsql_count,
                "total_sql_count": metrics.total_sql_count,
                "total_plsql_count": metrics.total_plsql_count,
                "high_complexity_ratio": metrics.high_complexity_ratio,
                "bulk_operation_count": metrics.bulk_operation_count
            },
            "rac_detected": metrics.rac_detected
        }
