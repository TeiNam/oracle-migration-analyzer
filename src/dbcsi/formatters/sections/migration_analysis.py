"""
마이그레이션 분석 결과 섹션 포맷터

타겟 DB별 마이그레이션 난이도 분석 결과를 표시합니다.
"""

from typing import Dict
from ...models import MigrationComplexity, TargetDatabase


class MigrationAnalysisFormatter:
    """마이그레이션 분석 결과 포맷터"""
    
    @staticmethod
    def format(
        migration_analysis: Dict[TargetDatabase, MigrationComplexity],
        language: str = "ko"
    ) -> str:
        """마이그레이션 분석 결과 섹션 포맷
        
        Args:
            migration_analysis: 타겟 DB별 마이그레이션 난이도 분석 결과
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not migration_analysis:
            return ""
        
        if language == "ko":
            return MigrationAnalysisFormatter._format_ko(migration_analysis)
        return MigrationAnalysisFormatter._format_en(migration_analysis)
    
    @staticmethod
    def _format_ko(
        migration_analysis: Dict[TargetDatabase, MigrationComplexity]
    ) -> str:
        """한국어 마이그레이션 분석 결과"""
        lines = []
        
        lines.append("## 🚀 마이그레이션 분석 결과\n")
        
        for target, complexity in migration_analysis.items():
            lines.append(f"### {target.value}\n")
            lines.append(f"- **난이도 점수**: {complexity.score:.2f} / 10.0")
            lines.append(f"- **난이도 레벨**: {complexity.level}")
            lines.append("")
            
            if complexity.factors:
                lines.append("**점수 구성 요소:**\n")
                for factor, score in complexity.factors.items():
                    lines.append(f"- {factor}: {score:.2f}")
                lines.append("")
            
            if complexity.instance_recommendation:
                inst_rec = complexity.instance_recommendation
                lines.append("**RDS 인스턴스 추천:**\n")
                lines.append(f"- **인스턴스 타입**: {inst_rec.instance_type}")
                lines.append(f"- **vCPU**: {inst_rec.vcpu}")
                lines.append(f"- **메모리**: {inst_rec.memory_gib} GiB")
                lines.append(f"- **현재 CPU 사용률**: {inst_rec.current_cpu_usage_pct:.2f}%")
                lines.append(f"- **현재 메모리 사용량**: {inst_rec.current_memory_gb:.2f} GB")
                lines.append(f"- **CPU 여유분**: {inst_rec.cpu_headroom_pct:.2f}%")
                lines.append(f"- **메모리 여유분**: {inst_rec.memory_headroom_pct:.2f}%")
                if inst_rec.estimated_monthly_cost_usd:
                    lines.append(f"- **예상 월간 비용**: ${inst_rec.estimated_monthly_cost_usd:.2f}")
                lines.append("")
            
            if complexity.recommendations:
                lines.append("**권장사항:**\n")
                for recommendation in complexity.recommendations:
                    lines.append(f"- {recommendation}")
                lines.append("")
            
            if complexity.warnings:
                lines.append("**경고:**\n")
                for warning in complexity.warnings:
                    lines.append(f"- ⚠️ {warning}")
                lines.append("")
            
            if complexity.next_steps:
                lines.append("**다음 단계:**\n")
                for step in complexity.next_steps:
                    lines.append(f"- {step}")
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(
        migration_analysis: Dict[TargetDatabase, MigrationComplexity]
    ) -> str:
        """영어 마이그레이션 분석 결과"""
        lines = []
        
        lines.append("## 🚀 Migration Analysis Results\n")
        
        for target, complexity in migration_analysis.items():
            lines.append(f"### {target.value}\n")
            lines.append(f"- **Difficulty Score**: {complexity.score:.2f} / 10.0")
            lines.append(f"- **Difficulty Level**: {complexity.level}")
            lines.append("")
            
            if complexity.instance_recommendation:
                inst_rec = complexity.instance_recommendation
                lines.append("**RDS Instance Recommendation:**\n")
                lines.append(f"- **Instance Type**: {inst_rec.instance_type}")
                lines.append(f"- **vCPU**: {inst_rec.vcpu}")
                lines.append(f"- **Memory**: {inst_rec.memory_gib} GiB")
                lines.append("")
            
            if complexity.recommendations:
                lines.append("**Recommendations:**\n")
                for recommendation in complexity.recommendations:
                    lines.append(f"- {recommendation}")
                lines.append("")
            
            if complexity.warnings:
                lines.append("**Warnings:**\n")
                for warning in complexity.warnings:
                    lines.append(f"- ⚠️ {warning}")
                lines.append("")
        
        return "\n".join(lines)
