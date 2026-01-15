"""
AWR 포맷터 모듈

AWR 분석 결과를 상세 Markdown 형식으로 출력합니다.
Statspack 포맷터를 확장하여 AWR 특화 섹션을 추가합니다.
"""

from datetime import datetime
from typing import Dict, List
import statistics

from .statspack_formatter import StatspackResultFormatter
from ..data_models import (
    MigrationComplexity,
    TargetDatabase,
)


class EnhancedResultFormatter(StatspackResultFormatter):
    """AWR 분석 결과 포맷터 - StatspackResultFormatter 확장
    
    AWR 특화 섹션을 추가로 생성합니다:
    - Executive Summary
    - 워크로드 패턴 분석
    - 버퍼 캐시 효율성 분석
    - I/O 함수별 분석
    - 백분위수 차트
    """
    
    @staticmethod
    def to_detailed_markdown(awr_data, 
                            migration_analysis=None,
                            language: str = "ko") -> str:
        """상세 Markdown 보고서 생성
        
        Args:
            awr_data: AWR 파싱 데이터 (AWRData 또는 StatspackData)
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            language: 리포트 언어 ("ko" 또는 "en")
            
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
        base_report = StatspackResultFormatter.to_markdown(awr_data, migration_analysis)
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
    
    @staticmethod
    def _generate_executive_summary(awr_data, migration_analysis, language: str) -> str:
        """Executive Summary 생성"""
        md = []
        
        if language == "ko":
            md.append("## 경영진 요약 (Executive Summary)\n")
            md.append("### 현재 시스템 개요\n")
            
            os_info = awr_data.os_info
            if os_info:
                db_name = os_info.db_name or "N/A"
                version = os_info.version or "N/A"
                db_size = os_info.total_db_size_gb or 0
                cpu_count = os_info.num_cpus or os_info.num_cpu_cores or 0
                memory_gb = os_info.physical_memory_gb or 0
                
                md.append(f"현재 **{db_name}** 데이터베이스는 Oracle {version} 버전으로 운영되고 있으며, "
                         f"총 **{db_size:.1f}GB**의 데이터를 저장하고 있습니다. "
                         f"시스템은 **{cpu_count}개의 CPU 코어**와 **{memory_gb:.1f}GB의 메모리**로 구성되어 있습니다.\n")
            
            md.append("### 마이그레이션 권장사항\n")
            
            if migration_analysis:
                sorted_targets = sorted(migration_analysis.items(), key=lambda x: x[1].score)
                best_target, best_complexity = sorted_targets[0]
                
                md.append(f"분석 결과, **{best_target.value}**로의 마이그레이션이 가장 적합합니다. "
                         f"예상 난이도는 **{best_complexity.level}**이며, "
                         f"마이그레이션 점수는 10점 만점에 **{best_complexity.score:.1f}점**입니다.\n")
                
                md.append("#### 타겟별 마이그레이션 난이도\n")
                for target, complexity in sorted_targets:
                    md.append(f"- **{target.value}**: {complexity.level} ({complexity.score:.1f}/10.0)")
                    if complexity.instance_recommendation:
                        rec = complexity.instance_recommendation
                        md.append(f"  - 권장 인스턴스: {rec.instance_type} ({rec.vcpu} vCPU, {rec.memory_gib} GiB)")
                md.append("")
            
            md.append("### 주요 발견사항\n")
            
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                p99_cpu_data = awr_data.percentile_cpu.get("99th_percentile")
                if p99_cpu_data:
                    md.append(f"- **CPU 사용률**: 99번째 백분위수 기준 {p99_cpu_data.on_cpu}개 코어 사용")
            
            if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
                p99_io_data = awr_data.percentile_io.get("99th_percentile")
                if p99_io_data:
                    md.append(f"- **I/O 부하**: 99번째 백분위수 기준 {p99_io_data.rw_iops:,} IOPS, {p99_io_data.rw_mbps} MB/s")
            
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
                if hit_ratios:
                    avg_hit_ratio = statistics.mean(hit_ratios)
                    status = "개선 필요" if avg_hit_ratio < 90 else "양호"
                    md.append(f"- **버퍼 캐시 효율성**: 평균 히트율 {avg_hit_ratio:.1f}% ({status})")
            
            md.append("")
            
            md.append("### 권장 조치사항\n")
            if migration_analysis and best_complexity:
                for i, rec in enumerate(best_complexity.recommendations[:5], 1):
                    md.append(f"{i}. {rec}")
            md.append("")
            
            md.append("### 예상 일정 및 비용\n")
            if migration_analysis and best_complexity:
                if best_complexity.score <= 3.0:
                    md.append("- **예상 마이그레이션 기간**: 2-4주")
                    md.append("- **리스크 수준**: 낮음")
                elif best_complexity.score <= 6.0:
                    md.append("- **예상 마이그레이션 기간**: 1-3개월")
                    md.append("- **리스크 수준**: 중간")
                else:
                    md.append("- **예상 마이그레이션 기간**: 3-6개월 이상")
                    md.append("- **리스크 수준**: 높음")
                
                if best_complexity.instance_recommendation and best_complexity.instance_recommendation.estimated_monthly_cost_usd:
                    cost = best_complexity.instance_recommendation.estimated_monthly_cost_usd
                    md.append(f"- **예상 월간 운영 비용**: ${cost:,.2f}")
            md.append("")
        else:
            md.append("## Executive Summary\n")
            # English version - abbreviated for brevity
            md.append("### Current System Overview\n")
            os_info = awr_data.os_info
            if os_info:
                md.append(f"Database **{os_info.db_name or 'N/A'}** running Oracle {os_info.version or 'N/A'}\n")
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_workload_analysis(awr_data, language: str) -> str:
        """워크로드 패턴 분석 섹션 생성"""
        md = []
        
        title = "## 워크로드 패턴 분석\n" if language == "ko" else "## Workload Pattern Analysis\n"
        md.append(title)
        
        if not awr_data.workload_profiles:
            md.append("워크로드 프로파일 데이터가 없습니다.\n" if language == "ko" else "No workload profile data available.\n")
            return "\n".join(md)
        
        # 이벤트별 DB Time 집계
        event_totals = {}
        module_totals = {}
        
        for profile in awr_data.workload_profiles:
            if "IDLE" in profile.event.upper():
                continue
            
            event_name = profile.event
            if event_name not in event_totals:
                event_totals[event_name] = 0
            event_totals[event_name] += profile.total_dbtime_sum
            
            module_name = profile.module
            if module_name not in module_totals:
                module_totals[module_name] = 0
            module_totals[module_name] += profile.total_dbtime_sum
        
        total_dbtime = sum(event_totals.values())
        
        if total_dbtime == 0:
            md.append("워크로드 데이터가 충분하지 않습니다.\n" if language == "ko" else "Insufficient workload data.\n")
            return "\n".join(md)
        
        # CPU vs I/O 비율
        cpu_time = sum(v for k, v in event_totals.items() if "CPU" in k.upper())
        io_time = sum(v for k, v in event_totals.items() if "I/O" in k.upper())
        cpu_pct = (cpu_time / total_dbtime) * 100
        io_pct = (io_time / total_dbtime) * 100
        
        pattern_type = "Mixed"
        if cpu_pct > 50:
            pattern_type = "CPU-intensive"
        elif io_pct > 50:
            pattern_type = "IO-intensive"
        
        if language == "ko":
            md.append("### 워크로드 패턴 요약\n")
            md.append(f"- **패턴 타입**: {pattern_type}")
            md.append(f"- **CPU 비율**: {cpu_pct:.1f}%")
            md.append(f"- **I/O 비율**: {io_pct:.1f}%")
        else:
            md.append("### Workload Pattern Summary\n")
            md.append(f"- **Pattern Type**: {pattern_type}")
            md.append(f"- **CPU Ratio**: {cpu_pct:.1f}%")
            md.append(f"- **I/O Ratio**: {io_pct:.1f}%")
        md.append("")
        
        # 상위 이벤트
        sorted_events = sorted(event_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if language == "ko":
            md.append("### 상위 대기 이벤트\n")
            md.append("| 순위 | 이벤트 이름 | DB Time | 비율 |")
        else:
            md.append("### Top Wait Events\n")
            md.append("| Rank | Event Name | DB Time | Percentage |")
        md.append("|------|-------------|---------|------------|")
        
        for i, (event, dbtime) in enumerate(sorted_events, 1):
            pct = (dbtime / total_dbtime) * 100
            md.append(f"| {i} | {event} | {dbtime:,} | {pct:.1f}% |")
        md.append("")
        
        # 상위 모듈
        if module_totals:
            sorted_modules = sorted(module_totals.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if language == "ko":
                md.append("### 상위 모듈\n")
                md.append("| 순위 | 모듈 이름 | DB Time | 비율 |")
            else:
                md.append("### Top Modules\n")
                md.append("| Rank | Module Name | DB Time | Percentage |")
            md.append("|------|-------------|---------|------------|")
            
            for i, (module, dbtime) in enumerate(sorted_modules, 1):
                pct = (dbtime / total_dbtime) * 100
                md.append(f"| {i} | {module} | {dbtime:,} | {pct:.1f}% |")
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_buffer_cache_analysis(awr_data, language: str) -> str:
        """버퍼 캐시 효율성 분석 섹션 생성"""
        md = []
        
        title = "## 버퍼 캐시 효율성 분석\n" if language == "ko" else "## Buffer Cache Efficiency Analysis\n"
        md.append(title)
        
        if not awr_data.buffer_cache_stats:
            md.append("버퍼 캐시 통계 데이터가 없습니다.\n" if language == "ko" else "No buffer cache statistics available.\n")
            return "\n".join(md)
        
        hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
        cache_sizes = [stat.db_cache_gb for stat in awr_data.buffer_cache_stats if stat.db_cache_gb is not None]
        
        if not hit_ratios:
            md.append("버퍼 캐시 히트율 데이터가 없습니다.\n" if language == "ko" else "No buffer cache hit ratio data available.\n")
            return "\n".join(md)
        
        avg_hit_ratio = statistics.mean(hit_ratios)
        min_hit_ratio = min(hit_ratios)
        max_hit_ratio = max(hit_ratios)
        current_size_gb = statistics.mean(cache_sizes) if cache_sizes else 0.0
        
        if language == "ko":
            md.append("### 히트율 요약\n")
            md.append(f"- **평균 히트율**: {avg_hit_ratio:.2f}%")
            md.append(f"- **최소 히트율**: {min_hit_ratio:.2f}%")
            md.append(f"- **최대 히트율**: {max_hit_ratio:.2f}%")
            md.append(f"- **현재 버퍼 캐시 크기**: {current_size_gb:.2f} GB")
            md.append("")
            
            md.append("### 효율성 평가\n")
            if avg_hit_ratio >= 95:
                md.append("✅ **매우 우수**: 버퍼 캐시가 매우 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 90:
                md.append("✅ **우수**: 버퍼 캐시가 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 85:
                md.append("⚠️ **보통**: 버퍼 캐시 효율성 개선이 필요합니다.")
            else:
                md.append("❌ **낮음**: 버퍼 캐시 크기 증가가 필요합니다.")
        else:
            md.append("### Hit Ratio Summary\n")
            md.append(f"- **Average Hit Ratio**: {avg_hit_ratio:.2f}%")
            md.append(f"- **Minimum Hit Ratio**: {min_hit_ratio:.2f}%")
            md.append(f"- **Maximum Hit Ratio**: {max_hit_ratio:.2f}%")
            md.append(f"- **Current Buffer Cache Size**: {current_size_gb:.2f} GB")
        md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_io_function_analysis(awr_data, language: str) -> str:
        """I/O 함수별 분석 섹션 생성"""
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
    
    @staticmethod
    def _generate_percentile_charts(awr_data) -> str:
        """백분위수 차트 생성"""
        md = []
        
        md.append("## 백분위수 분포 차트\n")
        
        # CPU 백분위수
        if awr_data.percentile_cpu:
            md.append("### CPU 사용률 백분위수 분포\n")
            md.append("| 백분위수 | CPU 코어 수 |")
            md.append("|----------|-------------|")
            
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("99th_percentile", "99%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                if key in awr_data.percentile_cpu:
                    cpu_data = awr_data.percentile_cpu[key]
                    md.append(f"| {label} | {cpu_data.on_cpu} |")
            md.append("")
        
        # I/O 백분위수
        if awr_data.percentile_io:
            md.append("### I/O 부하 백분위수 분포\n")
            md.append("| 백분위수 | IOPS | MB/s |")
            md.append("|----------|------|------|")
            
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("99th_percentile", "99%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                if key in awr_data.percentile_io:
                    io_data = awr_data.percentile_io[key]
                    md.append(f"| {label} | {io_data.rw_iops:,} | {io_data.rw_mbps} |")
            md.append("")
        
        md.append("### 백분위수 해석 가이드\n")
        md.append("- **99% (99th percentile)**: 99%의 시간 동안 이 값 이하 (권장 사이징 기준)")
        md.append("- P99 값에 30% 여유분을 추가하여 인스턴스 크기를 결정하는 것을 권장합니다.\n")
        
        return "\n".join(md)
    
    @staticmethod
    def compare_awr_reports(awr1, awr2, language: str = "ko") -> str:
        """두 AWR 리포트 비교"""
        md = []
        
        title = "# AWR 리포트 비교 분석\n" if language == "ko" else "# AWR Report Comparison Analysis\n"
        md.append(title)
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        is_awr1 = hasattr(awr1, 'is_awr') and awr1.is_awr()
        is_awr2 = hasattr(awr2, 'is_awr') and awr2.is_awr()
        
        if language == "ko":
            md.append("## 리포트 타입\n")
            md.append(f"- **리포트 1**: {'AWR' if is_awr1 else 'Statspack'}")
            md.append(f"- **리포트 2**: {'AWR' if is_awr2 else 'Statspack'}")
        else:
            md.append("## Report Type\n")
            md.append(f"- **Report 1**: {'AWR' if is_awr1 else 'Statspack'}")
            md.append(f"- **Report 2**: {'AWR' if is_awr2 else 'Statspack'}")
        md.append("")
        
        # 시스템 정보 비교
        if language == "ko":
            md.append("## 시스템 정보 비교\n")
            md.append("| 항목 | 리포트 1 | 리포트 2 | 변화 |")
        else:
            md.append("## System Information Comparison\n")
            md.append("| Item | Report 1 | Report 2 | Change |")
        md.append("|------|----------|----------|--------|")
        
        os1 = awr1.os_info if awr1.os_info else None
        os2 = awr2.os_info if awr2.os_info else None
        
        # DB 이름
        db1 = os1.db_name if os1 and os1.db_name else "N/A"
        db2 = os2.db_name if os2 and os2.db_name else "N/A"
        md.append(f"| DB 이름 | {db1} | {db2} | - |")
        
        # CPU 수
        cpu1 = os1.num_cpus if os1 and os1.num_cpus else 0
        cpu2 = os2.num_cpus if os2 and os2.num_cpus else 0
        cpu_diff = cpu2 - cpu1
        cpu_change = f"+{cpu_diff}" if cpu_diff > 0 else str(cpu_diff) if cpu_diff < 0 else "-"
        md.append(f"| CPU 수 | {cpu1} | {cpu2} | {cpu_change} |")
        
        # 메모리
        mem1 = os1.physical_memory_gb if os1 and os1.physical_memory_gb else 0.0
        mem2 = os2.physical_memory_gb if os2 and os2.physical_memory_gb else 0.0
        mem_diff = mem2 - mem1
        mem_change = f"+{mem_diff:.1f}" if mem_diff > 0 else f"{mem_diff:.1f}" if mem_diff < 0 else "-"
        md.append(f"| 메모리 (GB) | {mem1:.1f} | {mem2:.1f} | {mem_change} |")
        
        # DB 크기
        size1 = os1.total_db_size_gb if os1 and os1.total_db_size_gb else 0.0
        size2 = os2.total_db_size_gb if os2 and os2.total_db_size_gb else 0.0
        size_diff = size2 - size1
        size_change = f"+{size_diff:.1f}" if size_diff > 0 else f"{size_diff:.1f}" if size_diff < 0 else "-"
        md.append(f"| DB 크기 (GB) | {size1:.1f} | {size2:.1f} | {size_change} |")
        
        md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_trend_report(awr_list: List, language: str = "ko") -> str:
        """여러 AWR 리포트의 추세 분석 리포트 생성
        
        Args:
            awr_list: AWR 데이터 리스트 (시간순)
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 추세 분석 리포트
        """
        md = []
        
        title = "## 추세 분석 리포트\n" if language == "ko" else "## Trend Analysis Report\n"
        md.append(title)
        
        if len(awr_list) < 2:
            md.append("추세 분석을 위해서는 최소 2개 이상의 AWR 리포트가 필요합니다.\n" if language == "ko" 
                     else "At least 2 AWR reports are required for trend analysis.\n")
            return "\n".join(md)
        
        # 이상 징후 목록
        anomalies = []
        
        # CPU 추세 분석
        cpu_values = []
        for awr in awr_list:
            if hasattr(awr, 'percentile_cpu') and awr.percentile_cpu:
                p99 = awr.percentile_cpu.get("99th_percentile")
                if p99:
                    cpu_values.append(p99.on_cpu)
        
        if len(cpu_values) >= 2:
            if language == "ko":
                md.append("### CPU 사용률 추세\n")
            else:
                md.append("### CPU Usage Trend\n")
            
            # CPU 급증 감지 (50% 이상 증가)
            for i in range(1, len(cpu_values)):
                if cpu_values[i-1] > 0:
                    change_pct = ((cpu_values[i] - cpu_values[i-1]) / cpu_values[i-1]) * 100
                    if change_pct > 50:
                        anomaly_msg = f"CPU 급증 감지: {cpu_values[i-1]} → {cpu_values[i]} 코어 ({change_pct:.1f}% 증가)"
                        anomalies.append(anomaly_msg)
            
            md.append(f"- 시작: {cpu_values[0]} 코어")
            md.append(f"- 종료: {cpu_values[-1]} 코어")
            total_change = cpu_values[-1] - cpu_values[0]
            if total_change > 0:
                md.append(f"- 변화: +{total_change} 코어 (증가)")
            elif total_change < 0:
                md.append(f"- 변화: {total_change} 코어 (감소)")
            else:
                md.append("- 변화: 없음")
            md.append("")
        
        # I/O 추세 분석
        iops_values = []
        for awr in awr_list:
            if hasattr(awr, 'percentile_io') and awr.percentile_io:
                p99 = awr.percentile_io.get("99th_percentile")
                if p99:
                    iops_values.append(p99.rw_iops)
        
        if len(iops_values) >= 2:
            if language == "ko":
                md.append("### I/O 부하 추세\n")
            else:
                md.append("### I/O Load Trend\n")
            
            # IOPS 급증 감지 (50% 이상 증가)
            for i in range(1, len(iops_values)):
                if iops_values[i-1] > 0:
                    change_pct = ((iops_values[i] - iops_values[i-1]) / iops_values[i-1]) * 100
                    if change_pct > 50:
                        anomaly_msg = f"IOPS 급증 감지: {iops_values[i-1]:,} → {iops_values[i]:,} ({change_pct:.1f}% 증가)"
                        anomalies.append(anomaly_msg)
            
            md.append(f"- 시작: {iops_values[0]:,} IOPS")
            md.append(f"- 종료: {iops_values[-1]:,} IOPS")
            total_change = iops_values[-1] - iops_values[0]
            if total_change > 0:
                md.append(f"- 변화: +{total_change:,} IOPS (증가)")
            elif total_change < 0:
                md.append(f"- 변화: {total_change:,} IOPS (감소)")
            else:
                md.append("- 변화: 없음")
            md.append("")
        
        # 버퍼 캐시 히트율 추세 분석
        hit_ratios = []
        for awr in awr_list:
            if hasattr(awr, 'buffer_cache_stats') and awr.buffer_cache_stats:
                ratios = [s.hit_ratio for s in awr.buffer_cache_stats if s.hit_ratio is not None]
                if ratios:
                    hit_ratios.append(statistics.mean(ratios))
        
        if len(hit_ratios) >= 2:
            if language == "ko":
                md.append("### 버퍼 캐시 히트율 추세\n")
            else:
                md.append("### Buffer Cache Hit Ratio Trend\n")
            
            # 히트율 하락 감지 (5%p 이상 하락)
            for i in range(1, len(hit_ratios)):
                change = hit_ratios[i-1] - hit_ratios[i]
                if change > 5.0:
                    anomaly_msg = f"버퍼 캐시 히트율 하락 감지: {hit_ratios[i-1]:.1f}% → {hit_ratios[i]:.1f}% ({change:.1f}%p 하락)"
                    anomalies.append(anomaly_msg)
            
            md.append(f"- 시작: {hit_ratios[0]:.1f}%")
            md.append(f"- 종료: {hit_ratios[-1]:.1f}%")
            total_change = hit_ratios[-1] - hit_ratios[0]
            if total_change > 0:
                md.append(f"- 변화: +{total_change:.1f}%p (개선)")
            elif total_change < 0:
                md.append(f"- 변화: {total_change:.1f}%p (하락)")
            else:
                md.append("- 변화: 없음")
            md.append("")
        
        # 이상 징후 섹션
        if anomalies:
            if language == "ko":
                md.append("### ⚠️ 이상 징후 감지\n")
            else:
                md.append("### ⚠️ Anomalies Detected\n")
            
            for anomaly in anomalies:
                md.append(f"- {anomaly}")
            md.append("")
        else:
            if language == "ko":
                md.append("### ✅ 이상 징후 없음\n")
                md.append("분석 기간 동안 특별한 이상 징후가 감지되지 않았습니다.\n")
            else:
                md.append("### ✅ No Anomalies Detected\n")
                md.append("No significant anomalies were detected during the analysis period.\n")
        
        return "\n".join(md)
