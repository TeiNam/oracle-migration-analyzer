"""
Markdown 분석 메트릭 포맷터

분석 메트릭 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import AnalysisMetrics


class MetricsFormatterMixin:
    """분석 메트릭 포맷터 믹스인"""
    
    @staticmethod
    def _extract_number(value) -> int:
        """문자열이나 숫자에서 숫자 값 추출
        
        Args:
            value: 숫자 또는 문자열
            
        Returns:
            추출된 숫자 값
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    @staticmethod
    def _format_metrics(metrics: AnalysisMetrics, language: str) -> str:
        """분석 메트릭 섹션 포맷 (간소화 버전)
        
        부록에서는 본문에 없는 추가 정보만 표시합니다.
        
        Args:
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return f"""## 분석 원본 데이터

> 본문에 표시된 수치의 원본 데이터입니다.

| 항목 | 값 | 비고 |
|------|-----|------|
| 평균 SQL 복잡도 | {metrics.avg_sql_complexity:.2f} | 0~10 척도 |
| 평균 PL/SQL 복잡도 | {metrics.avg_plsql_complexity:.2f} | 0~10 척도 |
| 고난이도 SQL | {metrics.high_complexity_sql_count}개 | ≥5.0 기준 |
| 고난이도 PL/SQL | {metrics.high_complexity_plsql_count}개 | ≥5.0 기준 |
| BULK 연산 | {metrics.bulk_operation_count}개 | 성능 영향 |
| 평균 CPU | {metrics.avg_cpu_usage:.1f}% | AWR 기준 |
| 평균 I/O | {metrics.avg_io_load:.1f} IOPS | AWR 기준 |
| 평균 메모리 | {metrics.avg_memory_usage:.1f} GB | AWR 기준 |"""
        else:
            return f"""## Analysis Source Data

> Source data for the metrics shown in the main report.

| Item | Value | Note |
|------|-------|------|
| Avg SQL Complexity | {metrics.avg_sql_complexity:.2f} | 0~10 scale |
| Avg PL/SQL Complexity | {metrics.avg_plsql_complexity:.2f} | 0~10 scale |
| High Complexity SQL | {metrics.high_complexity_sql_count} | ≥5.0 threshold |
| High Complexity PL/SQL | {metrics.high_complexity_plsql_count} | ≥5.0 threshold |
| BULK Operations | {metrics.bulk_operation_count} | Performance impact |
| Avg CPU | {metrics.avg_cpu_usage:.1f}% | AWR based |
| Avg I/O | {metrics.avg_io_load:.1f} IOPS | AWR based |
| Avg Memory | {metrics.avg_memory_usage:.1f} GB | AWR based |"""
