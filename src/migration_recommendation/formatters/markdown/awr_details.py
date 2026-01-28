"""
Markdown AWR 상세 분석 포맷터

AWR 특화 데이터(백분위수, 버퍼 캐시, 워크로드 프로파일)를 Markdown 형식으로 변환합니다.
AWR 리포트인 경우에만 표시됩니다.
"""

from typing import List, Dict, Any, Optional
from ...data_models import AnalysisMetrics


class AWRDetailsFormatterMixin:
    """AWR 상세 분석 포맷터 믹스인"""
    
    @staticmethod
    def _format_awr_details(metrics: AnalysisMetrics, language: str) -> str:
        """AWR 상세 분석 섹션 포맷
        
        AWR 특화 데이터가 있는 경우에만 출력합니다.
        """
        # AWR 특화 데이터가 없으면 빈 문자열 반환
        has_cpu_percentiles = metrics.cpu_percentiles is not None
        has_io_percentiles = metrics.io_percentiles is not None
        has_buffer_cache = metrics.buffer_cache_hit_ratio is not None
        has_workloads = len(metrics.top_workload_profiles) > 0
        
        if not any([has_cpu_percentiles, has_io_percentiles, has_buffer_cache, has_workloads]):
            return ""
        
        if language == "ko":
            return AWRDetailsFormatterMixin._format_ko(metrics)
        return AWRDetailsFormatterMixin._format_en(metrics)
    
    @staticmethod
    def _format_ko(metrics: AnalysisMetrics) -> str:
        """한국어 AWR 상세 분석"""
        sections = []
        
        sections.append("# 📈 AWR 상세 분석\n")
        sections.append("> AWR(Automatic Workload Repository)에서 수집된 상세 성능 데이터입니다.")
        sections.append("> Statspack보다 더 상세한 백분위수 분석과 워크로드 프로파일을 제공합니다.\n")
        
        # CPU 백분위수
        if metrics.cpu_percentiles:
            sections.append(AWRDetailsFormatterMixin._format_cpu_percentiles_ko(metrics.cpu_percentiles))
        
        # I/O 백분위수
        if metrics.io_percentiles:
            sections.append(AWRDetailsFormatterMixin._format_io_percentiles_ko(metrics.io_percentiles))
        
        # 버퍼 캐시 효율
        if metrics.buffer_cache_hit_ratio is not None:
            sections.append(AWRDetailsFormatterMixin._format_buffer_cache_ko(metrics.buffer_cache_hit_ratio))
        
        # 워크로드 프로파일
        if metrics.top_workload_profiles:
            sections.append(AWRDetailsFormatterMixin._format_workloads_ko(metrics.top_workload_profiles))
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_cpu_percentiles_ko(cpu_pct: Dict[str, Any]) -> str:
        """CPU 백분위수 포맷 (한국어)"""
        lines = []
        lines.append("## CPU 백분위수 분포\n")
        lines.append("> **백분위수(Percentile)란?**")
        lines.append("> 데이터를 크기 순으로 정렬했을 때 특정 위치의 값입니다.")
        lines.append("> - **99th**: 상위 1%를 제외한 최대값 (일시적 스파이크 제외)")
        lines.append("> - **95th**: 상위 5%를 제외한 값 (일반적인 피크 기준)")
        lines.append("> - **Median**: 중앙값 (일반적인 운영 상태)\n")
        
        lines.append("| 백분위수 | On CPU | On CPU + Resource Mgr | 설명 |")
        lines.append("|---------|--------|----------------------|------|")
        
        # 백분위수 데이터 추출
        percentiles = ['maximum', '99th', '95th', '90th', 'median']
        labels = {'maximum': 'Maximum', '99th': '99th', '95th': '95th', '90th': '90th', 'median': 'Median'}
        descriptions = {
            'maximum': '관측된 최대값 (이상치 포함)',
            '99th': '실질적 최대 부하 기준',
            '95th': '피크 시간대 일반적 부하',
            '90th': '높은 부하 시간대',
            'median': '일반적인 운영 상태'
        }
        
        for pct in percentiles:
            on_cpu = cpu_pct.get(f'{pct}_on_cpu', '-')
            on_cpu_rm = cpu_pct.get(f'{pct}_on_cpu_rm', '-')
            if on_cpu != '-' or on_cpu_rm != '-':
                on_cpu_str = f"{on_cpu}" if on_cpu != '-' else '-'
                on_cpu_rm_str = f"{on_cpu_rm}" if on_cpu_rm != '-' else '-'
                lines.append(f"| {labels[pct]} | {on_cpu_str} | {on_cpu_rm_str} | {descriptions[pct]} |")
        
        lines.append("\n**인스턴스 사이징 권장**:")
        lines.append("- 평균(Median) 기준: 50% 여유 확보")
        lines.append("- 99th 기준: 버스트 대응 가능한 인스턴스 선택")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_io_percentiles_ko(io_pct: Dict[str, Any]) -> str:
        """I/O 백분위수 포맷 (한국어)"""
        lines = []
        lines.append("\n## I/O 백분위수 분포\n")
        lines.append("> **IOPS vs MB/s**")
        lines.append("> - **IOPS**: 초당 I/O 작업 수. 랜덤 I/O 성능 지표 (OLTP에 중요)")
        lines.append("> - **MB/s**: 초당 전송량. 순차 I/O 성능 지표 (배치/리포트에 중요)\n")
        
        lines.append("| 백분위수 | RW IOPS | Read IOPS | Write IOPS | RW MB/s | 설명 |")
        lines.append("|---------|---------|-----------|------------|---------|------|")
        
        percentiles = ['maximum', '99th', '95th', '90th', 'median']
        labels = {'maximum': 'Maximum', '99th': '99th', '95th': '95th', '90th': '90th', 'median': 'Median'}
        descriptions = {
            'maximum': '최대 I/O 요구량',
            '99th': '피크 시 I/O 기준',
            '95th': '높은 부하 시 I/O',
            '90th': '일반적 피크',
            'median': '평균적 I/O'
        }
        
        for pct in percentiles:
            rw_iops = io_pct.get(f'{pct}_rw_iops', '-')
            read_iops = io_pct.get(f'{pct}_read_iops', '-')
            write_iops = io_pct.get(f'{pct}_write_iops', '-')
            rw_mbps = io_pct.get(f'{pct}_rw_mbps', '-')
            
            if any(v != '-' for v in [rw_iops, read_iops, write_iops, rw_mbps]):
                rw_iops_str = f"{rw_iops:,}" if isinstance(rw_iops, (int, float)) else str(rw_iops)
                read_iops_str = f"{read_iops:,}" if isinstance(read_iops, (int, float)) else str(read_iops)
                write_iops_str = f"{write_iops:,}" if isinstance(write_iops, (int, float)) else str(write_iops)
                rw_mbps_str = f"{rw_mbps:,.1f}" if isinstance(rw_mbps, (int, float)) else str(rw_mbps)
                lines.append(f"| {labels[pct]} | {rw_iops_str} | {read_iops_str} | {write_iops_str} | {rw_mbps_str} | {descriptions[pct]} |")
        
        lines.append("\n**Aurora 스토리지 특성**:")
        lines.append("- IOPS 제한 없음 (자동 확장)")
        lines.append("- I/O 비용은 사용량 기반 과금")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_buffer_cache_ko(hit_ratio: float) -> str:
        """버퍼 캐시 효율 포맷 (한국어)"""
        lines = []
        lines.append("\n## 버퍼 캐시 효율\n")
        lines.append("> **Buffer Cache Hit Ratio란?**")
        lines.append("> 데이터 요청 시 메모리(버퍼 캐시)에서 찾은 비율입니다.")
        lines.append("> - **95% 이상**: 양호")
        lines.append("> - **90-95%**: 개선 여지 있음")
        lines.append("> - **90% 미만**: 메모리 증설 또는 쿼리 최적화 필요\n")
        
        lines.append("| 메트릭 | 값 | 평가 |")
        lines.append("|--------|-----|------|")
        
        # 평가
        if hit_ratio >= 95:
            evaluation = "🟢 양호"
        elif hit_ratio >= 90:
            evaluation = "🟠 개선 여지"
        else:
            evaluation = "🔴 최적화 필요"
        
        lines.append(f"| 평균 Hit Ratio | {hit_ratio:.1f}% | {evaluation} |")
        
        lines.append("\n**마이그레이션 시사점**:")
        if hit_ratio >= 95:
            lines.append("- Hit Ratio가 높아 현재 메모리 설정이 적절합니다")
        else:
            lines.append("- Hit Ratio가 낮아 타겟 인스턴스 메모리 증설 검토 필요")
        lines.append("- Aurora는 버퍼 풀 자동 관리로 튜닝 부담 감소")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_workloads_ko(workloads: List[Dict[str, Any]]) -> str:
        """워크로드 프로파일 포맷 (한국어)"""
        lines = []
        lines.append("\n## Top 워크로드 프로파일\n")
        lines.append("> **워크로드 프로파일이란?**")
        lines.append("> 어떤 애플리케이션/모듈이 DB 리소스를 얼마나 사용하는지 보여줍니다.")
        lines.append("> - **AAS (Average Active Sessions)**: 평균 활성 세션 수. 동시 부하 지표")
        lines.append("> - **DB Time %**: 전체 DB 시간 중 해당 워크로드가 차지하는 비율\n")
        
        lines.append("| 순위 | Module | Program | AAS | DB Time % | 설명 |")
        lines.append("|------|--------|---------|-----|-----------|------|")
        
        for i, wl in enumerate(workloads[:5], 1):  # 최대 5개
            module = wl.get('module', '-')
            program = wl.get('program', '-')
            aas = wl.get('aas', 0)
            db_time_pct = wl.get('db_time_pct', 0)
            
            # 설명 추론
            desc = AWRDetailsFormatterMixin._infer_workload_desc(module, program)
            
            aas_str = f"{aas:.1f}" if isinstance(aas, (int, float)) else str(aas)
            db_time_str = f"{db_time_pct:.1f}%" if isinstance(db_time_pct, (int, float)) else str(db_time_pct)
            
            lines.append(f"| {i} | {module} | {program} | {aas_str} | {db_time_str} | {desc} |")
        
        lines.append("\n**마이그레이션 우선순위 결정**:")
        lines.append("- DB Time % 높은 워크로드부터 테스트 우선")
        lines.append("- 배치 작업은 마이그레이션 후 성능 검증 필수")
        
        return "\n".join(lines)
    
    @staticmethod
    def _infer_workload_desc(module: str, program: str) -> str:
        """워크로드 설명 추론"""
        module_lower = (module or '').lower()
        program_lower = (program or '').lower()
        
        if 'batch' in module_lower or 'sqlplus' in program_lower:
            return "배치 작업"
        elif 'jdbc' in program_lower or 'java' in program_lower:
            return "Java 애플리케이션"
        elif 'perl' in program_lower or 'python' in program_lower:
            return "스크립트 기반"
        elif 'report' in module_lower:
            return "리포트 서비스"
        elif 'online' in module_lower or 'web' in module_lower:
            return "온라인 애플리케이션"
        else:
            return "-"
    
    @staticmethod
    def _format_en(metrics: AnalysisMetrics) -> str:
        """영어 AWR 상세 분석"""
        sections = []
        
        sections.append("# 📈 AWR Detailed Analysis\n")
        sections.append("> Detailed performance data from AWR (Automatic Workload Repository).")
        sections.append("> Provides more detailed percentile analysis than Statspack.\n")
        
        # CPU 백분위수
        if metrics.cpu_percentiles:
            sections.append(AWRDetailsFormatterMixin._format_cpu_percentiles_en(metrics.cpu_percentiles))
        
        # I/O 백분위수
        if metrics.io_percentiles:
            sections.append(AWRDetailsFormatterMixin._format_io_percentiles_en(metrics.io_percentiles))
        
        # 버퍼 캐시
        if metrics.buffer_cache_hit_ratio is not None:
            sections.append(AWRDetailsFormatterMixin._format_buffer_cache_en(metrics.buffer_cache_hit_ratio))
        
        # 워크로드
        if metrics.top_workload_profiles:
            sections.append(AWRDetailsFormatterMixin._format_workloads_en(metrics.top_workload_profiles))
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_cpu_percentiles_en(cpu_pct: Dict[str, Any]) -> str:
        """CPU 백분위수 포맷 (영어)"""
        lines = []
        lines.append("## CPU Percentile Distribution\n")
        lines.append("| Percentile | On CPU | On CPU + Resource Mgr | Description |")
        lines.append("|------------|--------|----------------------|-------------|")
        
        percentiles = ['maximum', '99th', '95th', '90th', 'median']
        for pct in percentiles:
            on_cpu = cpu_pct.get(f'{pct}_on_cpu', '-')
            on_cpu_rm = cpu_pct.get(f'{pct}_on_cpu_rm', '-')
            if on_cpu != '-' or on_cpu_rm != '-':
                lines.append(f"| {pct.capitalize()} | {on_cpu} | {on_cpu_rm} | - |")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_io_percentiles_en(io_pct: Dict[str, Any]) -> str:
        """I/O 백분위수 포맷 (영어)"""
        lines = []
        lines.append("\n## I/O Percentile Distribution\n")
        lines.append("| Percentile | RW IOPS | Read IOPS | Write IOPS | RW MB/s |")
        lines.append("|------------|---------|-----------|------------|---------|")
        
        percentiles = ['maximum', '99th', '95th', '90th', 'median']
        for pct in percentiles:
            rw_iops = io_pct.get(f'{pct}_rw_iops', '-')
            read_iops = io_pct.get(f'{pct}_read_iops', '-')
            write_iops = io_pct.get(f'{pct}_write_iops', '-')
            rw_mbps = io_pct.get(f'{pct}_rw_mbps', '-')
            
            if any(v != '-' for v in [rw_iops, read_iops, write_iops, rw_mbps]):
                lines.append(f"| {pct.capitalize()} | {rw_iops} | {read_iops} | {write_iops} | {rw_mbps} |")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_buffer_cache_en(hit_ratio: float) -> str:
        """버퍼 캐시 포맷 (영어)"""
        lines = []
        lines.append("\n## Buffer Cache Efficiency\n")
        lines.append("| Metric | Value | Evaluation |")
        lines.append("|--------|-------|------------|")
        
        if hit_ratio >= 95:
            evaluation = "🟢 Good"
        elif hit_ratio >= 90:
            evaluation = "🟠 Needs improvement"
        else:
            evaluation = "🔴 Optimization needed"
        
        lines.append(f"| Average Hit Ratio | {hit_ratio:.1f}% | {evaluation} |")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_workloads_en(workloads: List[Dict[str, Any]]) -> str:
        """워크로드 포맷 (영어)"""
        lines = []
        lines.append("\n## Top Workload Profiles\n")
        lines.append("| Rank | Module | Program | AAS | DB Time % |")
        lines.append("|------|--------|---------|-----|-----------|")
        
        for i, wl in enumerate(workloads[:5], 1):
            module = wl.get('module', '-')
            program = wl.get('program', '-')
            aas = wl.get('aas', 0)
            db_time_pct = wl.get('db_time_pct', 0)
            
            aas_str = f"{aas:.1f}" if isinstance(aas, (int, float)) else str(aas)
            db_time_str = f"{db_time_pct:.1f}%" if isinstance(db_time_pct, (int, float)) else str(db_time_pct)
            
            lines.append(f"| {i} | {module} | {program} | {aas_str} | {db_time_str} |")
        
        return "\n".join(lines)
