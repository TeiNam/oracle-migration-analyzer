"""
AWR 비교 및 추세 분석 모듈

AWR 리포트 비교 및 추세 분석 섹션을 생성합니다.
"""

from datetime import datetime
from typing import List
import statistics


class ComparisonMixin:
    """AWR 리포트 비교 및 추세 분석 믹스인"""
    
    @staticmethod
    def compare_awr_reports(awr1, awr2, language: str = "ko") -> str:
        """두 AWR 리포트 비교
        
        Args:
            awr1: 첫 번째 AWR 데이터
            awr2: 두 번째 AWR 데이터
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            비교 분석 리포트 문자열
        """
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
