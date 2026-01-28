"""
Statspack 포맷터 모듈

Statspack/AWR 분석 결과를 Markdown 형식으로 출력합니다.
AWR과 Statspack 모두 동일한 형식으로 출력하며,
AWR 전용 데이터(백분위수, 버퍼캐시 등)는 데이터가 있을 때만 표시합니다.
"""

from datetime import datetime
from typing import Dict, Optional
import re

from .base_formatter import BaseFormatter
from ..models import (
    StatspackData,
    MigrationComplexity,
    TargetDatabase,
)
from .sections import (
    DatabaseOverviewFormatter,
    ObjectStatisticsFormatter,
    PerformanceMetricsFormatter,
    WaitEventsFormatter,
    OracleFeaturesFormatter,
    MemoryUsageFormatter,
    DiskUsageFormatter,
    SGAAdviceFormatter,
    MigrationAnalysisFormatter,
    QuickAssessmentFormatter,
)


class StatspackResultFormatter(BaseFormatter):
    """Statspack/AWR 분석 결과 포맷터
    
    AWR과 Statspack 모두 동일한 형식으로 출력합니다.
    """
    
    @staticmethod
    def _extract_number(value) -> int:
        """문자열이나 숫자에서 숫자 값만 추출
        
        Args:
            value: 숫자 또는 문자열 (예: "BODY 318", 318)
            
        Returns:
            int: 추출된 숫자 값
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    @staticmethod
    def to_markdown(
        statspack_data: StatspackData, 
        migration_analysis: Optional[Dict[TargetDatabase, MigrationComplexity]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """분석 결과를 Markdown 형식으로 변환 (기본 형식)
        
        Args:
            statspack_data: Statspack/AWR 파싱 데이터
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            output_path: 출력 파일 경로 (차트 이미지 저장용, 선택적)
            
        Returns:
            Markdown 형식의 문자열
        """
        # to_enhanced_markdown으로 위임 (기본 언어: 한국어)
        return StatspackResultFormatter.to_enhanced_markdown(
            statspack_data=statspack_data,
            migration_analysis=migration_analysis,
            output_path=output_path,
            language="ko"
        )
    
    @staticmethod
    def to_enhanced_markdown(
        statspack_data: StatspackData,
        migration_analysis: Optional[Dict[TargetDatabase, MigrationComplexity]] = None,
        output_path: Optional[str] = None,
        language: str = "ko"
    ) -> str:
        """개선된 Markdown 형식으로 변환
        
        AWR과 Statspack 모두 동일한 형식으로 출력합니다.
        AWR 전용 데이터는 데이터가 있을 때만 표시됩니다.
        
        Args:
            statspack_data: Statspack/AWR 파싱 데이터
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            output_path: 출력 파일 경로 (차트 이미지 저장용, 선택적)
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목 - AWR 데이터인지 확인
        is_awr = hasattr(statspack_data, 'is_awr') and statspack_data.is_awr()
        if language == "ko":
            report_title = "AWR 분석 보고서" if is_awr else "Statspack 분석 보고서"
        else:
            report_title = "AWR Analysis Report" if is_awr else "Statspack Analysis Report"
        
        md.append(f"# {report_title}\n")
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. 데이터베이스 개요
        db_overview = DatabaseOverviewFormatter.format(statspack_data, language)
        if db_overview:
            md.append(db_overview)
        
        # 2. 오브젝트 통계
        obj_stats = ObjectStatisticsFormatter.format(statspack_data, language)
        if obj_stats:
            md.append(obj_stats)
        
        # 3. 성능 메트릭 상세
        perf_metrics = PerformanceMetricsFormatter.format(statspack_data, language)
        if perf_metrics:
            md.append(perf_metrics)
        
        # 4. 메모리 사용량 통계
        memory_usage = MemoryUsageFormatter.format(statspack_data, output_path, language)
        if memory_usage:
            md.append(memory_usage)
        
        # 5. SGA 조정 권장사항 (메모리 섹션 바로 다음)
        sga_advice = SGAAdviceFormatter.format(statspack_data, language)
        if sga_advice:
            md.append(sga_advice)
        
        # 6. 디스크 사용량 통계
        disk_usage = DiskUsageFormatter.format(statspack_data, output_path, language)
        if disk_usage:
            md.append(disk_usage)
        
        # 7. Top Wait Events
        wait_events = WaitEventsFormatter.format(statspack_data, language)
        if wait_events:
            md.append(wait_events)
        
        # 8. Oracle 기능 사용 현황
        oracle_features = OracleFeaturesFormatter.format(statspack_data, language)
        if oracle_features:
            md.append(oracle_features)
        
        # 9. 마이그레이션 분석 결과
        if migration_analysis:
            migration_result = MigrationAnalysisFormatter.format(migration_analysis, language)
            if migration_result:
                md.append(migration_result)
        
        # 10. Quick Assessment (맨 마지막)
        quick_assessment = QuickAssessmentFormatter.format(statspack_data, language)
        if quick_assessment:
            md.append(quick_assessment)
        
        return "\n".join(md)
    
    @staticmethod
    def batch_to_markdown(batch_result) -> str:
        """배치 분석 결과를 Markdown 형식으로 변환
        
        Args:
            batch_result: BatchAnalysisResult 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        md.append("# Statspack 배치 분석 보고서\n")
        md.append(f"분석 시간: {batch_result.analysis_timestamp}\n")
        
        # 전체 요약
        md.append("## 전체 요약\n")
        md.append(f"- **총 파일 수**: {batch_result.total_files}")
        md.append(f"- **성공**: {batch_result.successful_files}")
        md.append(f"- **실패**: {batch_result.failed_files}")
        success_rate = (
            batch_result.successful_files / batch_result.total_files * 100
        ) if batch_result.total_files > 0 else 0
        md.append(f"- **성공률**: {success_rate:.1f}%")
        md.append("")
        
        # 성공한 파일 목록
        successful_files = [r for r in batch_result.file_results if r.success]
        if successful_files:
            md.append("## 성공한 파일\n")
            md.append("| 파일명 | DB 이름 | 버전 | 총 크기 (GB) |")
            md.append("|--------|---------|------|--------------|")
            for result in successful_files:
                db_name = result.statspack_data.os_info.db_name or "N/A"
                version = result.statspack_data.os_info.version or "N/A"
                size = result.statspack_data.os_info.total_db_size_gb or 0
                md.append(f"| {result.filename} | {db_name} | {version} | {size:.2f} |")
            md.append("")
        
        # 실패한 파일 목록
        failed_files = [r for r in batch_result.file_results if not r.success]
        if failed_files:
            md.append("## 실패한 파일\n")
            md.append("| 파일명 | 오류 메시지 |")
            md.append("|--------|-------------|")
            for result in failed_files:
                error_msg = result.error_message or "알 수 없는 오류"
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                md.append(f"| {result.filename} | {error_msg} |")
            md.append("")
        
        # 마이그레이션 분석 요약
        if successful_files and successful_files[0].migration_analysis:
            md.append("## 마이그레이션 난이도 요약\n")
            
            targets = list(successful_files[0].migration_analysis.keys())
            
            for target in targets:
                md.append(f"### {target.value}\n")
                md.append("| 파일명 | DB 이름 | 난이도 점수 | 난이도 레벨 | 추천 인스턴스 |")
                md.append("|--------|---------|-------------|-------------|---------------|")
                
                for result in successful_files:
                    if result.migration_analysis and target in result.migration_analysis:
                        complexity = result.migration_analysis[target]
                        db_name = result.statspack_data.os_info.db_name or "N/A"
                        instance = (
                            complexity.instance_recommendation.instance_type 
                            if complexity.instance_recommendation else "N/A"
                        )
                        md.append(
                            f"| {result.filename} | {db_name} | {complexity.score:.2f} | "
                            f"{complexity.level} | {instance} |"
                        )
                md.append("")
        
        # 개별 파일 상세 정보
        if successful_files:
            md.append("## 개별 파일 상세 정보\n")
            for result in successful_files:
                md.append(f"### {result.filename}\n")
                
                os_info = result.statspack_data.os_info
                md.append(f"- **DB 이름**: {os_info.db_name or 'N/A'}")
                md.append(f"- **버전**: {os_info.version or 'N/A'}")
                md.append(f"- **총 크기**: {os_info.total_db_size_gb or 'N/A'} GB")
                md.append(f"- **CPU 개수**: {os_info.num_cpus or 'N/A'}")
                md.append(f"- **메모리**: {os_info.physical_memory_gb or 'N/A'} GB")
                
                if result.statspack_data.memory_metrics:
                    avg_total = (
                        sum(m.total_gb for m in result.statspack_data.memory_metrics) 
                        / len(result.statspack_data.memory_metrics)
                    )
                    md.append(f"- **평균 메모리 사용량**: {avg_total:.2f} GB")
                
                if result.migration_analysis:
                    md.append("\n**마이그레이션 난이도:**")
                    for target, complexity in result.migration_analysis.items():
                        md.append(f"- {target.value}: {complexity.score:.2f} ({complexity.level})")
                
                md.append("")
        
        return "\n".join(md)
