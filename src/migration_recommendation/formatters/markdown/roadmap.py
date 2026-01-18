"""
Markdown 마이그레이션 로드맵 포맷터

마이그레이션 로드맵 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import MigrationRoadmap


class RoadmapFormatterMixin:
    """마이그레이션 로드맵 포맷터 믹스인"""
    
    @staticmethod
    def _format_roadmap(roadmap: MigrationRoadmap, language: str) -> str:
        """마이그레이션 로드맵 섹션 포맷
        
        Args:
            roadmap: 마이그레이션 로드맵 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            content = f"# 마이그레이션 로드맵\n\n"
            content += f"**총 예상 기간**: {roadmap.total_estimated_duration}\n\n"
            
            # AI 활용 정보 추가
            if roadmap.ai_assisted:
                content += f"**AI 도구 활용**: 예 (Amazon Q Developer, Bedrock)\n\n"
                content += f"**AI 효과**:\n"
                content += f"- 시간 단축: 약 {roadmap.ai_time_saving_pct:.0f}%\n"
                content += f"- 비용 절감: 약 {roadmap.ai_cost_saving_pct:.0f}%\n"
                content += f"- 품질 향상: 자동 테스트 생성, 코드 리뷰, 버그 조기 발견\n\n"
                content += "**참고**: 위 일정은 AI 도구를 적극 활용하는 것을 전제로 합니다. AI 도구 미사용 시 기간이 약 2배 소요될 수 있습니다.\n\n"
            
            for phase in roadmap.phases:
                content += f"## Phase {phase.phase_number}: {phase.phase_name}\n\n"
                content += f"**예상 기간**: {phase.estimated_duration}\n\n"
                content += "**주요 작업**:\n"
                content += RoadmapFormatterMixin._format_list(phase.tasks) + "\n"
                content += "**필요 리소스**:\n"
                content += RoadmapFormatterMixin._format_list(phase.required_resources) + "\n\n"
        else:
            content = f"# Migration Roadmap\n\n"
            content += f"**Total Estimated Duration**: {roadmap.total_estimated_duration}\n\n"
            
            # AI 활용 정보 추가
            if roadmap.ai_assisted:
                content += f"**AI Tools Utilized**: Yes (Amazon Q Developer, Bedrock)\n\n"
                content += f"**AI Benefits**:\n"
                content += f"- Time Saving: Approximately {roadmap.ai_time_saving_pct:.0f}%\n"
                content += f"- Cost Saving: Approximately {roadmap.ai_cost_saving_pct:.0f}%\n"
                content += f"- Quality Improvement: Automated test generation, code review, early bug detection\n\n"
                content += "**Note**: The above schedule assumes active use of AI tools. Without AI tools, the duration may be approximately doubled.\n\n"
            
            for phase in roadmap.phases:
                content += f"## Phase {phase.phase_number}: {phase.phase_name}\n\n"
                content += f"**Estimated Duration**: {phase.estimated_duration}\n\n"
                content += "**Key Tasks**:\n"
                content += RoadmapFormatterMixin._format_list(phase.tasks) + "\n"
                content += "**Required Resources**:\n"
                content += RoadmapFormatterMixin._format_list(phase.required_resources) + "\n\n"
        
        return content
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """리스트 항목 포맷
        
        Args:
            items: 리스트 항목들
            
        Returns:
            Markdown 리스트 문자열
        """
        return "\n".join([f"- {item}" for item in items])
