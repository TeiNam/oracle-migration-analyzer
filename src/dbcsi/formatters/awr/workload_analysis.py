"""
AWR 워크로드 분석 모듈

워크로드 패턴 분석 섹션을 생성합니다.
"""


class WorkloadAnalysisMixin:
    """워크로드 패턴 분석 믹스인"""
    
    @staticmethod
    def _generate_workload_analysis(awr_data, language: str) -> str:
        """워크로드 패턴 분석 섹션 생성
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            워크로드 분석 섹션 문자열
        """
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
