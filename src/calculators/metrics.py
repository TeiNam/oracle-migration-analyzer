"""
복잡도 메트릭 계산

점수 정규화, 복잡도 레벨 결정, 권장사항 생성 등의 공통 메트릭을 제공합니다.
"""

import logging
from src.oracle_complexity_analyzer import (
    TargetDatabase,
    ComplexityLevel,
)

# 로거 초기화
logger = logging.getLogger(__name__)


class ComplexityMetrics:
    """복잡도 메트릭 계산 믹스인 클래스"""
    
    def _normalize_score(self, total_score: float) -> float:
        """SQL 점수 정규화 (0-10 척도)
        
        Requirements 12.1을 구현합니다.
        
        Args:
            total_score: 총 점수
            
        Returns:
            float: 정규화된 점수 (0-10)
        """
        return min(10.0, total_score * 10.0 / self.weights.max_total_score)
    
    def _normalize_plsql_score(self, total_score: float) -> float:
        """PL/SQL 점수 정규화 (0-10 척도)
        
        Requirements 12.2를 구현합니다.
        
        Args:
            total_score: 총 점수
            
        Returns:
            float: 정규화된 점수 (0-10)
        """
        # PL/SQL 최대 점수
        if self.target == TargetDatabase.POSTGRESQL:
            max_score = 20.0  # 10.0 + 3.0 + 3.0 + 2.0 + 2.0
        else:  # MySQL
            max_score = 23.5  # 10.0 + 3.0 + 3.0 + 2.0 + 2.0 + 1.5 + 2.0
        
        return min(10.0, total_score * 10.0 / max_score)
    
    def _get_complexity_level(self, score: float) -> ComplexityLevel:
        """복잡도 레벨 결정
        
        Requirements 12.3-12.8을 구현합니다.
        
        Args:
            score: 정규화된 점수 (0-10)
            
        Returns:
            ComplexityLevel: 복잡도 레벨
        """
        if score <= 1:
            return ComplexityLevel.VERY_SIMPLE
        elif score <= 3:
            return ComplexityLevel.SIMPLE
        elif score <= 5:
            return ComplexityLevel.MODERATE
        elif score <= 7:
            return ComplexityLevel.COMPLEX
        elif score <= 9:
            return ComplexityLevel.VERY_COMPLEX
        else:
            return ComplexityLevel.EXTREMELY_COMPLEX
    
    def _get_recommendation(self, level: ComplexityLevel) -> str:
        """권장사항 반환
        
        Requirements 12.3-12.8을 구현합니다.
        
        Args:
            level: 복잡도 레벨
            
        Returns:
            str: 권장사항
        """
        recommendations = {
            ComplexityLevel.VERY_SIMPLE: "자동 변환",
            ComplexityLevel.SIMPLE: "함수 대체",
            ComplexityLevel.MODERATE: "부분 재작성",
            ComplexityLevel.COMPLEX: "상당한 재작성",
            ComplexityLevel.VERY_COMPLEX: "대부분 재작성",
            ComplexityLevel.EXTREMELY_COMPLEX: "완전 재설계"
        }
        return recommendations[level]
