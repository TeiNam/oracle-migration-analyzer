"""
Markdown 위험 요소 포맷터

위험 요소 및 완화 방안 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import Risk


class RisksFormatterMixin:
    """위험 요소 포맷터 믹스인"""
    
    @staticmethod
    def _format_risks(risks: List[Risk], language: str) -> str:
        """위험 요소 섹션 포맷
        
        Args:
            risks: 위험 요소 리스트
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            content = "# 위험 요소 및 완화 방안\n\n"
            content += "> **이 섹션의 목적**: 마이그레이션 과정에서 발생할 수 있는 **위험 요소**를 식별하고,\n"
            content += "> 각 위험에 대한 **완화 방안**을 제시합니다. 사전에 대비하여 프로젝트 실패를 방지합니다.\n\n"
            content += "> **심각도 설명**\n"
            content += "> - **high**: 프로젝트 일정/비용에 큰 영향, 즉시 대응 필요\n"
            content += "> - **medium**: 일부 영향 예상, 계획적 대응 필요\n"
            content += "> - **low**: 영향 적음, 모니터링 수준\n\n"
            for i, risk in enumerate(risks, 1):
                content += f"## 위험 {i}: {risk.description}\n\n"
                content += f"**카테고리**: {risk.category}\n\n"
                content += f"**심각도**: {risk.severity}\n\n"
                content += f"**완화 방안**: {risk.mitigation}\n\n"
        else:
            content = "# Risks and Mitigation\n\n"
            content += "> **Purpose**: Identifies potential risks during migration and provides\n"
            content += "> mitigation strategies for each risk. Prepare in advance to prevent project failure.\n\n"
            content += "> **Severity Levels**\n"
            content += "> - **high**: Major impact on schedule/cost, immediate action required\n"
            content += "> - **medium**: Some impact expected, planned response needed\n"
            content += "> - **low**: Minor impact, monitoring level\n\n"
            for i, risk in enumerate(risks, 1):
                content += f"## Risk {i}: {risk.description}\n\n"
                content += f"**Category**: {risk.category}\n\n"
                content += f"**Severity**: {risk.severity}\n\n"
                content += f"**Mitigation**: {risk.mitigation}\n\n"
        
        return content
