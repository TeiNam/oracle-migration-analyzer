"""
Markdown 성능 메트릭 상세 포맷터

성능 메트릭 상세 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import AnalysisMetrics


class PerformanceDetailsFormatterMixin:
    """성능 메트릭 상세 포맷터 믹스인"""
    
    @staticmethod
    def _format_performance_details(metrics: AnalysisMetrics, language: str) -> str:
        """성능 메트릭 상세 섹션 포맷"""
        # 데이터가 없으면 빈 문자열 반환
        has_io = any([metrics.avg_read_iops, metrics.avg_write_iops])
        has_cpu = metrics.avg_cpu_usage > 0 or metrics.peak_cpu_usage
        
        if not has_io and not has_cpu:
            return ""
        
        if language == "ko":
            return PerformanceDetailsFormatterMixin._format_ko(metrics)
        return PerformanceDetailsFormatterMixin._format_en(metrics)
    
    @staticmethod
    def _format_ko(metrics: AnalysisMetrics) -> str:
        """한국어 성능 메트릭 상세"""
        sections = []
        
        sections.append("# ⚡ 성능 메트릭 상세\n")
        sections.append("> AWR/Statspack에서 수집된 실제 운영 환경의 성능 데이터입니다.")
        sections.append("> 타겟 인스턴스 사이징 및 성능 기준선 설정에 활용됩니다.\n")
        
        # CPU 사용량
        sections.append("## CPU 사용량\n")
        sections.append("| 메트릭 | 값 | 설명 |")
        sections.append("|--------|-----|------|")
        
        if metrics.avg_cpu_usage > 0:
            sections.append(f"| 평균 CPU 사용률 | {metrics.avg_cpu_usage:.1f}% | 분석 기간 평균 |")
        if metrics.peak_cpu_usage:
            sections.append(f"| 피크 CPU 사용률 | {metrics.peak_cpu_usage:.1f}% | 관측된 최대값 |")
        
        # I/O 성능
        has_io = any([metrics.avg_read_iops, metrics.avg_write_iops])
        if has_io:
            sections.append("\n## I/O 성능\n")
            sections.append("> **IOPS**: 초당 I/O 작업 수. 스토리지 성능의 핵심 지표")
            sections.append("> **처리량(MB/s)**: 초당 전송 데이터량\n")
            
            sections.append("| 메트릭 | 읽기 | 쓰기 | 합계 |")
            sections.append("|--------|------|------|------|")
            
            read_iops = metrics.avg_read_iops or 0
            write_iops = metrics.avg_write_iops or 0
            total_iops = read_iops + write_iops
            sections.append(f"| 평균 IOPS | {read_iops:,.0f} | {write_iops:,.0f} | {total_iops:,.0f} |")
            
            if metrics.avg_read_mbps or metrics.avg_write_mbps:
                read_mbps = metrics.avg_read_mbps or 0
                write_mbps = metrics.avg_write_mbps or 0
                total_mbps = read_mbps + write_mbps
                sections.append(f"| 평균 처리량 (MB/s) | {read_mbps:,.1f} | {write_mbps:,.1f} | {total_mbps:,.1f} |")
            
            if metrics.peak_iops:
                sections.append(f"| 피크 IOPS | - | - | {metrics.peak_iops:,.0f} |")
        
        # 트랜잭션
        if metrics.avg_commits_per_sec:
            sections.append("\n## 트랜잭션\n")
            sections.append("| 메트릭 | 값 | 설명 |")
            sections.append("|--------|-----|------|")
            sections.append(f"| 평균 커밋/초 | {metrics.avg_commits_per_sec:,.1f} | 트랜잭션 처리량 |")
        
        # 메모리
        if metrics.avg_memory_usage > 0:
            sections.append("\n## 메모리\n")
            sections.append("| 메트릭 | 값 | 설명 |")
            sections.append("|--------|-----|------|")
            sections.append(f"| 평균 메모리 사용량 | {metrics.avg_memory_usage:.1f} GB | SGA + PGA |")
        
        # 마이그레이션 시사점
        sections.append("\n## 마이그레이션 시사점\n")
        
        implications = []
        if metrics.avg_cpu_usage > 70:
            implications.append("- **CPU 집약적 워크로드**: 충분한 vCPU 확보 필요")
        if total_iops > 10000 if has_io else False:
            implications.append("- **높은 I/O 요구량**: Aurora I/O 최적화 또는 Provisioned IOPS 검토")
        if metrics.avg_commits_per_sec and metrics.avg_commits_per_sec > 500:
            implications.append("- **높은 트랜잭션 처리량**: Aurora 분산 스토리지가 유리")
        
        if implications:
            sections.extend(implications)
        else:
            sections.append("- Aurora는 스토리지 I/O가 자동 확장되므로 IOPS 제한 걱정 불필요")
            sections.append("- 읽기 비중이 높으면 Read Replica 활용 권장")
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_en(metrics: AnalysisMetrics) -> str:
        """영어 성능 메트릭 상세"""
        sections = []
        
        sections.append("# ⚡ Performance Metrics Details\n")
        sections.append("> Actual performance data from AWR/Statspack.")
        sections.append("> Used for target instance sizing and performance baseline.\n")
        
        sections.append("## CPU Usage\n")
        sections.append("| Metric | Value | Description |")
        sections.append("|--------|-------|-------------|")
        
        if metrics.avg_cpu_usage > 0:
            sections.append(f"| Average CPU Usage | {metrics.avg_cpu_usage:.1f}% | Analysis period average |")
        if metrics.peak_cpu_usage:
            sections.append(f"| Peak CPU Usage | {metrics.peak_cpu_usage:.1f}% | Maximum observed |")
        
        has_io = any([metrics.avg_read_iops, metrics.avg_write_iops])
        if has_io:
            sections.append("\n## I/O Performance\n")
            sections.append("| Metric | Read | Write | Total |")
            sections.append("|--------|------|-------|-------|")
            
            read_iops = metrics.avg_read_iops or 0
            write_iops = metrics.avg_write_iops or 0
            total_iops = read_iops + write_iops
            sections.append(f"| Average IOPS | {read_iops:,.0f} | {write_iops:,.0f} | {total_iops:,.0f} |")
            
            if metrics.avg_read_mbps or metrics.avg_write_mbps:
                read_mbps = metrics.avg_read_mbps or 0
                write_mbps = metrics.avg_write_mbps or 0
                total_mbps = read_mbps + write_mbps
                sections.append(f"| Average Throughput (MB/s) | {read_mbps:,.1f} | {write_mbps:,.1f} | {total_mbps:,.1f} |")
        
        if metrics.avg_commits_per_sec:
            sections.append("\n## Transactions\n")
            sections.append("| Metric | Value | Description |")
            sections.append("|--------|-------|-------------|")
            sections.append(f"| Average Commits/sec | {metrics.avg_commits_per_sec:,.1f} | Transaction throughput |")
        
        return "\n".join(sections)
