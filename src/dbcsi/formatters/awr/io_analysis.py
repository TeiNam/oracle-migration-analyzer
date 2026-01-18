"""
AWR I/O 분석 모듈

I/O 함수별 분석 섹션을 생성합니다.
"""

import statistics


class IOAnalysisMixin:
    """I/O 함수별 분석 믹스인"""
    
    @staticmethod
    def _generate_io_function_analysis(awr_data, language: str) -> str:
        """I/O 함수별 분석 섹션 생성
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            I/O 분석 섹션 문자열
        """
        md = []
        
        title = "## I/O 함수별 분석\n" if language == "ko" else "## I/O Function Analysis\n"
        md.append(title)
        
        if not awr_data.iostat_functions:
            md.append("I/O 함수별 통계 데이터가 없습니다.\n" if language == "ko" else "No I/O function statistics available.\n")
            return "\n".join(md)
        
        # 함수별 I/O 통계 집계
        function_stats = {}
        for iostat in awr_data.iostat_functions:
            func_name = iostat.function_name
            if func_name not in function_stats:
                function_stats[func_name] = []
            function_stats[func_name].append(iostat.megabytes_per_s)
        
        total_io = sum(sum(values) for values in function_stats.values())
        
        if total_io == 0:
            md.append("I/O 데이터가 충분하지 않습니다.\n" if language == "ko" else "Insufficient I/O data.\n")
            return "\n".join(md)
        
        if language == "ko":
            md.append("### 함수별 I/O 통계\n")
            md.append("| 함수 이름 | 평균 (MB/s) | 최대 (MB/s) | 총 비율 |")
        else:
            md.append("### I/O Statistics by Function\n")
            md.append("| Function Name | Average (MB/s) | Maximum (MB/s) | Total % |")
        md.append("|---------------|----------------|----------------|---------|")
        
        for func_name, values in sorted(function_stats.items(), key=lambda x: sum(x[1]), reverse=True):
            avg_mb = statistics.mean(values)
            max_mb = max(values)
            pct = (sum(values) / total_io * 100)
            md.append(f"| {func_name} | {avg_mb:.2f} | {max_mb:.2f} | {pct:.1f}% |")
        md.append("")
        
        return "\n".join(md)
