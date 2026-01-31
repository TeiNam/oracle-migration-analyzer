"""
Executive Summary 기본 클래스 및 헬퍼 메서드

공통 유틸리티 함수를 제공합니다.
"""

import re
from typing import Optional
from ...data_models import AnalysisMetrics


class SummaryBase:
    """Executive Summary 기본 클래스"""
    
    @staticmethod
    def get_plsql_count(metrics: AnalysisMetrics) -> int:
        """PL/SQL 오브젝트 개수 계산 (AWR 우선)"""
        if any([metrics.awr_procedure_count, metrics.awr_function_count, metrics.awr_package_count]):
            count = 0
            if metrics.awr_procedure_count:
                count += SummaryBase.extract_number(metrics.awr_procedure_count)
            if metrics.awr_function_count:
                count += SummaryBase.extract_number(metrics.awr_function_count)
            if metrics.awr_package_count:
                count += SummaryBase.extract_number(metrics.awr_package_count)
            return count
        return metrics.total_plsql_count
    
    @staticmethod
    def extract_number(value) -> int:
        """문자열이나 숫자에서 숫자 값 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    @staticmethod
    def get_complexity_level_text(complexity: float) -> str:
        """복잡도 점수를 레벨 텍스트로 변환
        
        Args:
            complexity: 복잡도 점수 (0.0 ~ 10.0)
            
        Returns:
            str: 복잡도 레벨 텍스트
        """
        if complexity < 1.0:
            return "매우 낮음"
        elif complexity < 3.0:
            return "낮음"
        elif complexity < 5.0:
            return "중간"
        elif complexity < 7.0:
            return "높음"
        elif complexity < 9.0:
            return "매우 높음"
        else:
            return "극도로 높음"
    
    @staticmethod
    def build_complexity_message(
        metrics: AnalysisMetrics,
        plsql_count: int
    ) -> str:
        """복잡도 메시지 생성
        
        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            
        Returns:
            str: 복잡도 설명 메시지
        """
        sql_level = SummaryBase.get_complexity_level_text(metrics.avg_sql_complexity)
        plsql_level = SummaryBase.get_complexity_level_text(metrics.avg_plsql_complexity)
        is_high_complexity = (
            metrics.avg_sql_complexity >= 7.0 and metrics.avg_plsql_complexity >= 7.0
        )
        high_complexity_count = (
            metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count
        )
        
        if plsql_count >= 100:
            connector = "또한" if is_high_complexity else "하지만"
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. "
                f"{connector} PL/SQL 오브젝트가 {plsql_count}개로 매우 많아 코드 안정성을 위해 "
                f"Refactor보다는 Replatform을 권장하며, 전환 작업에 드는 리소스가 많아 "
                f"단기간 전환이 어려울 것으로 판단됩니다."
            )
        elif plsql_count >= 50:
            connector = "또한" if is_high_complexity else "하지만"
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. "
                f"{connector} PL/SQL 오브젝트가 {plsql_count}개로 많아 코드 안정성을 위해 "
                f"Replatform을 권장하며, 변환 작업의 리스크가 높습니다."
            )
        else:
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다."
            )
        
        # 고복잡도 코드 경고 추가
        if high_complexity_count >= 20:
            complexity_msg += (
                f" 다만, 복잡도 7.0 이상의 고난이도 코드가 {high_complexity_count}개 존재하여 "
                f"이들 코드의 변환 및 검증 작업에는 상당한 시간과 전문성이 요구됩니다."
            )
        
        if metrics.high_complexity_ratio >= 0.3:
            complexity_msg += (
                f" 전체 오브젝트 중 {metrics.high_complexity_ratio*100:.1f}%가 복잡도 7.0 이상으로 "
                f"분류되어, 대규모 코드 변경 시 높은 위험이 예상됩니다."
            )
        
        return complexity_msg
