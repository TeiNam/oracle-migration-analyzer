"""
Markdown 포맷터 모듈

마이그레이션 추천 리포트를 Markdown 형식으로 변환합니다.
"""

from ...data_models import MigrationRecommendation

from .executive_summary import ExecutiveSummaryFormatterMixin
from .strategy import StrategyFormatterMixin
from .rationale import RationaleFormatterMixin
from .alternatives import AlternativesFormatterMixin
from .risks import RisksFormatterMixin
from .roadmap import RoadmapFormatterMixin
from .metrics import MetricsFormatterMixin
from .instance import InstanceFormatterMixin


class MarkdownReportFormatter(
    ExecutiveSummaryFormatterMixin,
    StrategyFormatterMixin,
    RationaleFormatterMixin,
    AlternativesFormatterMixin,
    RisksFormatterMixin,
    RoadmapFormatterMixin,
    MetricsFormatterMixin,
    InstanceFormatterMixin
):
    """Markdown 리포트 포맷터
    
    모든 섹션 포맷터 믹스인을 통합하여 완전한 Markdown 리포트를 생성합니다.
    """
    
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
        4. 인스턴스 추천
        5. 추천 근거
        6. 대안 전략
        7. 위험 요소 및 완화 방안
        8. 마이그레이션 로드맵
        9. 분석 메트릭 (부록)
        
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
        
        # 4. 인스턴스 추천
        if recommendation.instance_recommendation:
            sections.append(self._format_instance_recommendation(recommendation.instance_recommendation, language))
        
        # 5. 추천 근거
        sections.append(self._format_rationales(recommendation.rationales, language))
        
        # 6. 대안 전략
        sections.append(self._format_alternatives(recommendation.alternative_strategies, language))
        
        # 7. 위험 요소
        sections.append(self._format_risks(recommendation.risks, language))
        
        # 8. 마이그레이션 로드맵
        sections.append(self._format_roadmap(recommendation.roadmap, language))
        
        # 9. 분석 메트릭 (부록)
        sections.append(self._format_metrics(recommendation.metrics, language))
        
        return "\n\n".join(sections)


__all__ = ['MarkdownReportFormatter']
