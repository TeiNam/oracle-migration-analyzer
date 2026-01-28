"""
메모리 사용량 섹션 포맷터

SGA/PGA 메모리 사용량 통계를 표시합니다.
"""

from typing import Optional
from ...models import StatspackData


class MemoryUsageFormatter:
    """메모리 사용량 포맷터"""
    
    @staticmethod
    def format(
        data: StatspackData,
        output_path: Optional[str] = None,
        language: str = "ko"
    ) -> str:
        """메모리 사용량 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            output_path: 차트 이미지 저장 경로 (선택적)
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.memory_metrics:
            return ""
        
        if language == "ko":
            return MemoryUsageFormatter._format_ko(data, output_path)
        return MemoryUsageFormatter._format_en(data, output_path)
    
    @staticmethod
    def _format_ko(data: StatspackData, output_path: Optional[str] = None) -> str:
        """한국어 메모리 사용량"""
        lines = []
        
        lines.append("## 💾 메모리 사용량 통계\n")
        
        total_gbs = [m.total_gb for m in data.memory_metrics]
        sga_gbs = [m.sga_gb for m in data.memory_metrics]
        pga_gbs = [m.pga_gb for m in data.memory_metrics]
        
        lines.append("**요약:**")
        lines.append(f"- **총 스냅샷 수**: {len(data.memory_metrics)}개")
        lines.append(f"- **평균 메모리 사용량**: {sum(total_gbs)/len(total_gbs):.2f} GB "
                    f"(SGA: {sum(sga_gbs)/len(sga_gbs):.2f} GB, "
                    f"PGA: {sum(pga_gbs)/len(pga_gbs):.2f} GB)")
        lines.append(f"- **최소/최대**: {min(total_gbs):.2f} GB / {max(total_gbs):.2f} GB")
        lines.append("")
        
        # 차트 생성
        if output_path and len(data.memory_metrics) >= 1:
            chart_md = MemoryUsageFormatter._generate_chart(data, output_path)
            if chart_md:
                lines.append(chart_md)
        
        # 상세 테이블
        lines.append("**상세 데이터 (최근 10개):**\n")
        lines.append("| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |")
        lines.append("|---------|----------|----------|----------|------------|")
        for metric in data.memory_metrics[:10]:
            lines.append(f"| {metric.snap_id} | {metric.instance_number} | "
                        f"{metric.sga_gb:.2f} | {metric.pga_gb:.2f} | {metric.total_gb:.2f} |")
        
        if len(data.memory_metrics) > 10:
            lines.append(f"\n*전체 {len(data.memory_metrics)}개 중 10개만 표시*")
        
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData, output_path: Optional[str] = None) -> str:
        """영어 메모리 사용량"""
        lines = []
        
        lines.append("## 💾 Memory Usage Statistics\n")
        
        total_gbs = [m.total_gb for m in data.memory_metrics]
        sga_gbs = [m.sga_gb for m in data.memory_metrics]
        pga_gbs = [m.pga_gb for m in data.memory_metrics]
        
        lines.append("**Summary:**")
        lines.append(f"- **Total Snapshots**: {len(data.memory_metrics)}")
        lines.append(f"- **Average Memory**: {sum(total_gbs)/len(total_gbs):.2f} GB")
        lines.append(f"- **Min/Max**: {min(total_gbs):.2f} GB / {max(total_gbs):.2f} GB")
        lines.append("")
        
        # 상세 테이블
        lines.append("**Details (Last 10):**\n")
        lines.append("| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |")
        lines.append("|---------|----------|----------|----------|------------|")
        for metric in data.memory_metrics[:10]:
            lines.append(f"| {metric.snap_id} | {metric.instance_number} | "
                        f"{metric.sga_gb:.2f} | {metric.pga_gb:.2f} | {metric.total_gb:.2f} |")
        
        if len(data.memory_metrics) > 10:
            lines.append(f"\n*Showing 10 of {len(data.memory_metrics)}*")
        
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def _generate_chart(data: StatspackData, output_path: str) -> str:
        """메모리 사용량 차트 생성"""
        try:
            from ..chart_generator import ChartGenerator
            
            display_count = min(20, len(data.memory_metrics))
            snap_ids = [m.snap_id for m in data.memory_metrics[:display_count]]
            sga_data = [m.sga_gb for m in data.memory_metrics[:display_count]]
            pga_data = [m.pga_gb for m in data.memory_metrics[:display_count]]
            total_data = [m.total_gb for m in data.memory_metrics[:display_count]]
            
            chart_filename = ChartGenerator.generate_memory_usage_chart(
                snap_ids=snap_ids,
                sga_data=sga_data,
                pga_data=pga_data,
                total_data=total_data,
                output_path=output_path,
                title="Memory Usage Trend",
                xlabel="Snap ID",
                ylabel="Memory (GB)"
            )
            
            if chart_filename:
                return f"**메모리 사용량 추이:**\n\n![Memory Usage]({chart_filename})\n"
        except Exception:
            pass
        return ""
