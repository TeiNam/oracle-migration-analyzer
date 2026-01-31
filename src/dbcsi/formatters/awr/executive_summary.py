"""
AWR Executive Summary 생성 모듈

경영진 요약 섹션을 생성합니다.
"""

from typing import Dict
import statistics

from ...models import MigrationComplexity, TargetDatabase


class ExecutiveSummaryMixin:
    """Executive Summary 생성 믹스인"""
    
    @staticmethod
    def _generate_executive_summary(awr_data, migration_analysis: Dict[TargetDatabase, MigrationComplexity], language: str) -> str:
        """Executive Summary 생성
        
        Args:
            awr_data: AWR 데이터
            migration_analysis: 마이그레이션 분석 결과
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            Executive Summary 섹션 문자열
        """
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
                        inst_rec = complexity.instance_recommendation
                        md.append(f"  - 권장 인스턴스: {inst_rec.instance_type} ({inst_rec.vcpu} vCPU, {inst_rec.memory_gib} GiB)")
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
