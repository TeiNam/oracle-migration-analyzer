"""
추천 근거 포맷터 - 메인 믹스인 클래스

RationaleFormatterMixin 클래스를 제공합니다.
"""

from typing import List
from ....data_models import Rationale, AnalysisMetrics
from .base import (
    get_complexity_level,
    get_complexity_level_en,
    calculate_final_difficulty,
)
from .korean import format_rationales_ko, format_work_estimation_ko, format_additional_considerations_ko
from .english import format_rationales_en, format_work_estimation_en
from .difficulty import format_final_difficulty_section, format_final_difficulty_section_ko, format_final_difficulty_section_en


class RationaleFormatterMixin:
    """추천 근거 포맷터 믹스인"""
    
    @staticmethod
    def _format_rationales(
        rationales: List[Rationale],
        metrics: AnalysisMetrics,
        language: str
    ) -> str:
        """추천 근거 섹션 포맷 (새 양식)
        
        Args:
            rationales: 추천 근거 리스트
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return format_rationales_ko(rationales, metrics)
        return format_rationales_en(rationales, metrics)
    
    @staticmethod
    def _get_complexity_level(score: float) -> str:
        """복잡도 점수를 레벨로 변환 (한국어)"""
        return get_complexity_level(score)
    
    @staticmethod
    def _get_complexity_level_en(score: float) -> str:
        """복잡도 점수를 레벨로 변환 (영어)"""
        return get_complexity_level_en(score)
    
    @staticmethod
    def _calculate_final_difficulty(metrics: AnalysisMetrics) -> str:
        """최종 난이도 계산"""
        return calculate_final_difficulty(metrics)
    
    @staticmethod
    def _format_final_difficulty_section(
        metrics: AnalysisMetrics,
        language: str
    ) -> str:
        """최종 난이도 판정 섹션 포맷"""
        return format_final_difficulty_section(metrics, language)
    
    @staticmethod
    def _format_final_difficulty_section_ko(metrics: AnalysisMetrics) -> str:
        """최종 난이도 판정 섹션 (한국어)"""
        return format_final_difficulty_section_ko(metrics)
    
    @staticmethod
    def _format_final_difficulty_section_en(metrics: AnalysisMetrics) -> str:
        """최종 난이도 판정 섹션 (영어)"""
        return format_final_difficulty_section_en(metrics)
    
    # 하위 호환성을 위한 내부 메서드 re-export
    @staticmethod
    def _format_rationales_ko(
        rationales: List[Rationale],
        metrics: AnalysisMetrics
    ) -> str:
        """한국어 추천 근거 포맷"""
        return format_rationales_ko(rationales, metrics)
    
    @staticmethod
    def _format_rationales_en(
        rationales: List[Rationale],
        metrics: AnalysisMetrics
    ) -> str:
        """영어 추천 근거 포맷"""
        return format_rationales_en(rationales, metrics)
    
    @staticmethod
    def _format_work_estimation_ko(metrics: AnalysisMetrics) -> str:
        """작업 예상 시간 섹션 (한국어)"""
        return format_work_estimation_ko(metrics)
    
    @staticmethod
    def _format_work_estimation_en(metrics: AnalysisMetrics) -> str:
        """작업 예상 시간 섹션 (영어)"""
        return format_work_estimation_en(metrics)
    
    @staticmethod
    def _format_additional_considerations_ko() -> str:
        """추가 고려사항 섹션 (한국어)"""
        return format_additional_considerations_ko()
