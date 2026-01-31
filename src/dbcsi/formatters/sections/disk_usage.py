"""
디스크 사용량 섹션 포맷터

디스크 사용량 통계를 표시합니다.
"""

from typing import Optional
from ...models import StatspackData


class DiskUsageFormatter:
    """디스크 사용량 포맷터"""
    
    @staticmethod
    def format(
        data: StatspackData,
        output_path: Optional[str] = None,
        language: str = "ko"
    ) -> str:
        """디스크 사용량 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            output_path: 차트 이미지 저장 경로 (선택적)
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.disk_sizes:
            return ""
        
        if language == "ko":
            return DiskUsageFormatter._format_ko(data, output_path)
        return DiskUsageFormatter._format_en(data, output_path)
    
    @staticmethod
    def _format_ko(data: StatspackData, output_path: Optional[str] = None) -> str:
        """한국어 디스크 사용량"""
        lines = []
        
        lines.append("## 💿 디스크 사용량 통계\n")
        
        sizes = [d.size_gb for d in data.disk_sizes]
        
        lines.append("**요약:**")
        lines.append(f"- **평균 디스크 사용량**: {sum(sizes)/len(sizes):.2f} GB")
        lines.append(f"- **최소/최대**: {min(sizes):.2f} GB / {max(sizes):.2f} GB")
        lines.append("")
        
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData, output_path: Optional[str] = None) -> str:
        """영어 디스크 사용량"""
        lines = []
        
        lines.append("## 💿 Disk Usage Statistics\n")
        
        sizes = [d.size_gb for d in data.disk_sizes]
        
        lines.append("**Summary:**")
        lines.append(f"- **Average Disk Usage**: {sum(sizes)/len(sizes):.2f} GB")
        lines.append(f"- **Min/Max**: {min(sizes):.2f} GB / {max(sizes):.2f} GB")
        lines.append("")
        
        return "\n".join(lines)
