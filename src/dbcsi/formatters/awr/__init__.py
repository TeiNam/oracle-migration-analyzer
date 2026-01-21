"""
AWR 포맷터 모듈

AWR 분석 결과를 상세 Markdown 형식으로 출력합니다.
Statspack 포맷터를 확장하여 AWR 특화 섹션을 추가합니다.
"""

from datetime import datetime
from typing import Dict

from ..statspack_formatter import StatspackResultFormatter
from ...models import MigrationComplexity, TargetDatabase

from .executive_summary import ExecutiveSummaryMixin
from .workload_analysis import WorkloadAnalysisMixin
from .buffer_cache_analysis import BufferCacheAnalysisMixin
from .io_analysis import IOAnalysisMixin
from .percentile_charts import PercentileChartsMixin
from .comparison import ComparisonMixin


class EnhancedResultFormatter(
    ExecutiveSummaryMixin,
    WorkloadAnalysisMixin,
    BufferCacheAnalysisMixin,
    IOAnalysisMixin,
    PercentileChartsMixin,
    ComparisonMixin,
    StatspackResultFormatter
):
    """AWR 분석 결과 포맷터 - StatspackResultFormatter 확장
    
    AWR 특화 섹션을 추가로 생성합니다:
    - Executive Summary
    - 워크로드 패턴 분석
    - 버퍼 캐시 효율성 분석
    - I/O 함수별 분석
    - 백분위수 차트
    - AWR 리포트 비교
    - 추세 분석
    """
    
    @staticmethod
    def to_detailed_markdown(awr_data, 
                            migration_analysis: Dict[TargetDatabase, MigrationComplexity] = None,
                            language: str = "ko",
                            output_path: str = None) -> str:
        """상세 Markdown 보고서 생성
        
        Args:
            awr_data: AWR 파싱 데이터 (AWRData 또는 StatspackData)
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            language: 리포트 언어 ("ko" 또는 "en")
            output_path: 출력 파일 경로 (차트 이미지 저장용, 선택적)
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # AWR 데이터인지 확인
        is_awr = hasattr(awr_data, 'is_awr') and awr_data.is_awr()
        
        # 제목
        if language == "ko":
            title = "AWR 상세 분석 보고서" if is_awr else "Statspack 분석 보고서"
        else:
            title = "AWR Detailed Analysis Report" if is_awr else "Statspack Analysis Report"
        
        md.append(f"# {title}\n")
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Executive Summary (AWR인 경우에만)
        if is_awr and migration_analysis:
            md.append(EnhancedResultFormatter._generate_executive_summary(
                awr_data, migration_analysis, language
            ))
        
        # 기본 Statspack 섹션 (제목, 빈 줄, 생성 시간, 빈 줄 제거)
        # output_path를 전달하여 메모리 그래프 생성
        base_report = StatspackResultFormatter.to_markdown(
            awr_data, migration_analysis, output_path=output_path
        )
        base_lines = base_report.split('\n')
        base_content = '\n'.join(base_lines[4:])  # 처음 4줄 건너뛰기
        md.append(base_content)
        
        # AWR 특화 섹션
        if is_awr:
            if hasattr(awr_data, 'workload_profiles') and awr_data.workload_profiles:
                md.append(EnhancedResultFormatter._generate_workload_analysis(awr_data, language))
            
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                md.append(EnhancedResultFormatter._generate_buffer_cache_analysis(awr_data, language))
            
            if hasattr(awr_data, 'iostat_functions') and awr_data.iostat_functions:
                md.append(EnhancedResultFormatter._generate_io_function_analysis(awr_data, language))
            
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                md.append(EnhancedResultFormatter._generate_percentile_charts(awr_data))
        
        return "\n".join(md)


__all__ = ['EnhancedResultFormatter']
