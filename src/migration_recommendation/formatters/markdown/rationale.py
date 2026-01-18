"""
Markdown 추천 근거 포맷터

추천 근거 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List
from ...data_models import Rationale


class RationaleFormatterMixin:
    """추천 근거 포맷터 믹스인"""
    
    @staticmethod
    def _format_rationales(rationales: List[Rationale], language: str) -> str:
        """추천 근거 섹션 포맷
        
        Args:
            rationales: 추천 근거 리스트
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            content = "# 추천 근거\n\n"
            for i, rationale in enumerate(rationales, 1):
                content += f"## {i}. {rationale.reason}\n\n"
                content += f"**카테고리**: {rationale.category}\n\n"
                if rationale.supporting_data:
                    # 근거 산출 기준과 근거 데이터 분리
                    calculation_keys = ['refactor_calculation', 'replatform_calculation', 'refactor_tasks', 'replatform_tasks', 'refactor_basis', 'reference', 'team_size']
                    data_keys = [k for k in rationale.supporting_data.keys() if k not in calculation_keys]
                    
                    # 근거 데이터 먼저 표시
                    if data_keys:
                        content += "**근거 데이터**:\n"
                        for key in data_keys:
                            value = rationale.supporting_data[key]
                            # 소수점 두 자리로 반올림
                            if isinstance(value, float):
                                value = round(value, 2)
                            content += f"- {key}: {value}\n"
                        content += "\n"
                    
                    # 근거 산출 기준 표시
                    if any(k in rationale.supporting_data for k in calculation_keys):
                        content += "**근거 산출 기준**:\n"
                        if 'team_size' in rationale.supporting_data:
                            content += f"- 팀 구성: {rationale.supporting_data['team_size']}명 (시니어 개발자 2명, 주니어 개발자 1명, QA 1명)\n"
                        if 'refactor_calculation' in rationale.supporting_data:
                            content += f"- Refactor 시간 산정: {rationale.supporting_data['refactor_calculation']}\n"
                        if 'refactor_basis' in rationale.supporting_data:
                            content += f"- 산정 근거: {rationale.supporting_data['refactor_basis']}\n"
                        if 'replatform_calculation' in rationale.supporting_data:
                            content += f"- Replatform 시간 산정: {rationale.supporting_data['replatform_calculation']}\n"
                        if 'reference' in rationale.supporting_data:
                            content += f"- 참고 자료: {rationale.supporting_data['reference']}\n"
                        if 'refactor_tasks' in rationale.supporting_data:
                            content += "- Refactor 주요 작업:\n"
                            for task in rationale.supporting_data['refactor_tasks']:
                                content += f"  - {task}\n"
                        if 'replatform_tasks' in rationale.supporting_data:
                            content += "- Replatform 주요 작업:\n"
                            for task in rationale.supporting_data['replatform_tasks']:
                                content += f"  - {task}\n"
                content += "\n"
        else:
            content = "# Rationales\n\n"
            for i, rationale in enumerate(rationales, 1):
                content += f"## {i}. {rationale.reason}\n\n"
                content += f"**Category**: {rationale.category}\n\n"
                if rationale.supporting_data:
                    # 근거 산출 기준과 근거 데이터 분리
                    calculation_keys = ['refactor_calculation', 'replatform_calculation', 'refactor_tasks', 'replatform_tasks', 'refactor_basis', 'reference', 'team_size']
                    data_keys = [k for k in rationale.supporting_data.keys() if k not in calculation_keys]
                    
                    # 근거 데이터 먼저 표시
                    if data_keys:
                        content += "**Supporting Data**:\n"
                        for key in data_keys:
                            value = rationale.supporting_data[key]
                            # 소수점 두 자리로 반올림
                            if isinstance(value, float):
                                value = round(value, 2)
                            content += f"- {key}: {value}\n"
                        content += "\n"
                    
                    # 근거 산출 기준 표시
                    if any(k in rationale.supporting_data for k in calculation_keys):
                        content += "**Calculation Basis**:\n"
                        if 'team_size' in rationale.supporting_data:
                            content += f"- Team composition: {rationale.supporting_data['team_size']} members (2 senior developers, 1 junior developer, 1 QA)\n"
                        if 'refactor_calculation' in rationale.supporting_data:
                            content += f"- Refactor time estimation: {rationale.supporting_data['refactor_calculation']}\n"
                        if 'refactor_basis' in rationale.supporting_data:
                            content += f"- Estimation basis: {rationale.supporting_data['refactor_basis']}\n"
                        if 'replatform_calculation' in rationale.supporting_data:
                            content += f"- Replatform time estimation: {rationale.supporting_data['replatform_calculation']}\n"
                        if 'reference' in rationale.supporting_data:
                            content += f"- Reference: {rationale.supporting_data['reference']}\n"
                        if 'refactor_tasks' in rationale.supporting_data:
                            content += "- Refactor key tasks:\n"
                            for task in rationale.supporting_data['refactor_tasks']:
                                content += f"  - {task}\n"
                        if 'replatform_tasks' in rationale.supporting_data:
                            content += "- Replatform key tasks:\n"
                            for task in rationale.supporting_data['replatform_tasks']:
                                content += f"  - {task}\n"
                content += "\n"
        
        return content
