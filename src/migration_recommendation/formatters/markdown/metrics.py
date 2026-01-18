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
        """분석 메트릭 섹션 포맷
        
        Args:
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        # AWR/Statspack PL/SQL 통계 섹션 생성
        awr_plsql_section = ""
        if any([metrics.awr_plsql_lines, metrics.awr_procedure_count, 
                metrics.awr_function_count, metrics.awr_package_count]):
            if language == "ko":
                awr_plsql_section = "\n## AWR/Statspack PL/SQL 통계 (데이터베이스 실제 오브젝트)\n\n"
                if metrics.awr_plsql_lines is not None:
                    plsql_lines = MetricsFormatterMixin._extract_number(metrics.awr_plsql_lines)
                    awr_plsql_section += f"- **PL/SQL 코드 라인 수**: {plsql_lines:,}\n"
                if metrics.awr_procedure_count is not None:
                    proc_count = MetricsFormatterMixin._extract_number(metrics.awr_procedure_count)
                    awr_plsql_section += f"- **프로시저 수**: {proc_count}\n"
                if metrics.awr_function_count is not None:
                    func_count = MetricsFormatterMixin._extract_number(metrics.awr_function_count)
                    awr_plsql_section += f"- **함수 수**: {func_count}\n"
                if metrics.awr_package_count is not None:
                    pkg_count = MetricsFormatterMixin._extract_number(metrics.awr_package_count)
                    awr_plsql_section += f"- **패키지 수**: {pkg_count}\n"
            else:
                awr_plsql_section = "\n## AWR/Statspack PL/SQL Statistics (Actual Database Objects)\n\n"
                if metrics.awr_plsql_lines is not None:
                    plsql_lines = MetricsFormatterMixin._extract_number(metrics.awr_plsql_lines)
                    awr_plsql_section += f"- **PL/SQL Code Lines**: {plsql_lines:,}\n"
                if metrics.awr_procedure_count is not None:
                    proc_count = MetricsFormatterMixin._extract_number(metrics.awr_procedure_count)
                    awr_plsql_section += f"- **Procedure Count**: {proc_count}\n"
                if metrics.awr_function_count is not None:
                    func_count = MetricsFormatterMixin._extract_number(metrics.awr_function_count)
                    awr_plsql_section += f"- **Function Count**: {func_count}\n"
                if metrics.awr_package_count is not None:
                    pkg_count = MetricsFormatterMixin._extract_number(metrics.awr_package_count)
                    awr_plsql_section += f"- **Package Count**: {pkg_count}\n"
        
        if language == "ko":
            return f"""# 분석 메트릭 (부록)

## 성능 메트릭

- **평균 CPU 사용률**: {metrics.avg_cpu_usage:.1f}%
- **평균 I/O 부하**: {metrics.avg_io_load:.1f} IOPS
- **평균 메모리 사용량**: {metrics.avg_memory_usage:.1f} GB

## 코드 복잡도 메트릭 (분석된 소스 파일 기준)

- **평균 SQL 복잡도**: {metrics.avg_sql_complexity:.2f}
- **평균 PL/SQL 복잡도**: {metrics.avg_plsql_complexity:.2f}
- **복잡도 7.0 이상 SQL 개수**: {metrics.high_complexity_sql_count} / {metrics.total_sql_count}
- **복잡도 7.0 이상 PL/SQL 개수**: {metrics.high_complexity_plsql_count} / {metrics.total_plsql_count}
- **복잡 오브젝트 비율**: {metrics.high_complexity_ratio*100:.1f}%
- **BULK 연산 개수**: {metrics.bulk_operation_count}
{awr_plsql_section}"""
        else:
            return f"""# Analysis Metrics (Appendix)

## Performance Metrics

- **Average CPU Usage**: {metrics.avg_cpu_usage:.1f}%
- **Average I/O Load**: {metrics.avg_io_load:.1f} IOPS
- **Average Memory Usage**: {metrics.avg_memory_usage:.1f} GB

## Code Complexity Metrics (Based on Analyzed Source Files)

- **Average SQL Complexity**: {metrics.avg_sql_complexity:.2f}
- **Average PL/SQL Complexity**: {metrics.avg_plsql_complexity:.2f}
- **High Complexity SQL Count**: {metrics.high_complexity_sql_count} / {metrics.total_sql_count}
- **High Complexity PL/SQL Count**: {metrics.high_complexity_plsql_count} / {metrics.total_plsql_count}
- **High Complexity Ratio**: {metrics.high_complexity_ratio*100:.1f}%
- **BULK Operation Count**: {metrics.bulk_operation_count}
{awr_plsql_section}"""
