"""
JSON 포맷터 모듈

마이그레이션 추천 리포트를 JSON 형식으로 변환합니다.
"""

import json
from typing import Dict, Any
from ..data_models import (
    MigrationRecommendation,
    ExecutiveSummary,
    Rationale,
    AlternativeStrategy,
    Risk,
    MigrationRoadmap,
    AnalysisMetrics
)


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
        """Executive Summary 직렬화
        
        Args:
            summary: Executive Summary 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
        return {
            "recommended_strategy": summary.recommended_strategy,
            "estimated_duration": summary.estimated_duration,
            "key_benefits": summary.key_benefits,
            "key_risks": summary.key_risks,
            "summary_text": summary.summary_text
        }
    
    def _serialize_rationale(self, rationale: Rationale) -> Dict[str, Any]:
        """Rationale 직렬화
        
        Args:
            rationale: Rationale 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
        return {
            "category": rationale.category,
            "reason": rationale.reason,
            "supporting_data": rationale.supporting_data
        }
    
    def _serialize_alternative(self, alternative: AlternativeStrategy) -> Dict[str, Any]:
        """AlternativeStrategy 직렬화
        
        Args:
            alternative: AlternativeStrategy 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
        return {
            "strategy": alternative.strategy.value,
            "pros": alternative.pros,
            "cons": alternative.cons,
            "considerations": alternative.considerations
        }
    
    def _serialize_risk(self, risk: Risk) -> Dict[str, Any]:
        """Risk 직렬화
        
        Args:
            risk: Risk 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
        return {
            "category": risk.category,
            "description": risk.description,
            "severity": risk.severity,
            "mitigation": risk.mitigation
        }
    
    def _serialize_roadmap(self, roadmap: MigrationRoadmap) -> Dict[str, Any]:
        """MigrationRoadmap 직렬화
        
        Args:
            roadmap: MigrationRoadmap 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
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
        """AnalysisMetrics 직렬화
        
        Args:
            metrics: AnalysisMetrics 데이터
            
        Returns:
            직렬화된 딕셔너리
        """
        result = {
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
        
        # AWR/Statspack 통계 추가 (있는 경우)
        if any([metrics.awr_plsql_lines, metrics.awr_procedure_count, 
                metrics.awr_function_count, metrics.awr_package_count]):
            result["awr_statistics"] = {}
            if metrics.awr_plsql_lines is not None:
                result["awr_statistics"]["plsql_lines"] = metrics.awr_plsql_lines
            if metrics.awr_procedure_count is not None:
                result["awr_statistics"]["procedure_count"] = metrics.awr_procedure_count
            if metrics.awr_function_count is not None:
                result["awr_statistics"]["function_count"] = metrics.awr_function_count
            if metrics.awr_package_count is not None:
                result["awr_statistics"]["package_count"] = metrics.awr_package_count
        
        return result
