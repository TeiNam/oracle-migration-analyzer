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
            for i, risk in enumerate(risks, 1):
                content += f"## 위험 {i}: {risk.description}\n\n"
                content += f"**카테고리**: {risk.category}\n\n"
                content += f"**심각도**: {risk.severity}\n\n"
                content += f"**완화 방안**: {risk.mitigation}\n\n"
        else:
            content = "# Risks and Mitigation\n\n"
            for i, risk in enumerate(risks, 1):
                content += f"## Risk {i}: {risk.description}\n\n"
                content += f"**Category**: {risk.category}\n\n"
                content += f"**Severity**: {risk.severity}\n\n"
                content += f"**Mitigation**: {risk.mitigation}\n\n"
        
        return content
