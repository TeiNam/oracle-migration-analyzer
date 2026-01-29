"""
SGA 조정 권장사항 섹션 포맷터

Oracle SGA 메모리 최적화 권장사항을 표시합니다.
"""

from typing import Dict, List, Optional
from ...models import StatspackData
from ...models.base_models import SGAAdvice


class SGAAdviceFormatter:
    """SGA 조정 권장사항 포맷터"""
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """SGA 조정 권장사항 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.sga_advice:
            return ""
        
        if language == "ko":
            return SGAAdviceFormatter._format_ko(data)
        return SGAAdviceFormatter._format_en(data)
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 SGA 조정 권장사항"""
        lines = []
        
        lines.append("## 🔧 SGA 조정 권장사항\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("Oracle SGA(System Global Area) 메모리 설정에 대한 최적화 권장사항입니다.")
        lines.append("Oracle이 분석한 데이터를 바탕으로 성능 향상을 위한 SGA 크기 조정을 제안합니다.\n")
        lines.append("> **💡 IT 관계자를 위한 설명**")
        lines.append("> - **SGA**: Oracle이 데이터를 캐싱하는 공유 메모리 영역")
        lines.append("> - **DB Time**: 데이터베이스가 작업을 처리하는 데 걸리는 시간")
        lines.append("> - **Physical Reads**: 디스크에서 데이터를 읽는 횟수 (낮을수록 좋음)")
        lines.append("> - SGA가 클수록 더 많은 데이터를 메모리에 캐싱하여 성능이 향상됩니다\n")
        
        # 인스턴스별로 그룹화
        instances = SGAAdviceFormatter._group_by_instance(data.sga_advice)
        is_rac = len(instances) > 1
        
        if is_rac:
            lines.append(f"> **RAC 환경**: {len(instances)}개 인스턴스가 감지되었습니다. "
                        "인스턴스별로 SGA 권장사항을 확인하세요.\n")
        
        # 인스턴스별로 처리
        for inst_id in sorted(instances.keys()):
            inst_advice_list = instances[inst_id]
            
            if is_rac:
                lines.append(f"---\n")
                lines.append(f"### 인스턴스 {inst_id}\n")
            
            # 현재 SGA 찾기 (size_factor가 1.0인 것)
            current_sga = next(
                (a for a in inst_advice_list if abs(a.sga_size_factor - 1.0) < 0.01), None
            )
            
            # 최적 SGA 찾기 (DB Time이 가장 낮은 것)
            optimal_sga = min(inst_advice_list, key=lambda x: x.estd_db_time)
            
            # 요약 정보
            if not is_rac:
                lines.append("### 분석 요약\n")
            else:
                lines.append("#### 분석 요약\n")
            lines.append("| 항목 | 값 | 설명 |")
            lines.append("|------|-----|------|")
            
            if current_sga:
                lines.append(f"| 현재 SGA 크기 | {current_sga.sga_size:,} MB | "
                           f"현재 설정된 SGA 메모리 크기 |")
                lines.append(f"| 현재 예상 DB Time | {current_sga.estd_db_time:,} | "
                           f"현재 설정에서의 예상 처리 시간 |")
                lines.append(f"| 현재 예상 Physical Reads | {current_sga.estd_physical_reads:,} | "
                           f"현재 설정에서의 예상 디스크 읽기 횟수 |")
            
            if optimal_sga and optimal_sga != current_sga:
                lines.append(f"| **권장 SGA 크기** | **{optimal_sga.sga_size:,} MB** | "
                           f"**최적 성능을 위한 권장 크기** |")
                lines.append(f"| 권장 시 예상 DB Time | {optimal_sga.estd_db_time:,} | "
                           f"권장 설정에서의 예상 처리 시간 |")
                lines.append(f"| 권장 시 예상 Physical Reads | {optimal_sga.estd_physical_reads:,} | "
                           f"권장 설정에서의 예상 디스크 읽기 횟수 |")
                
                # 개선율 계산
                if current_sga and current_sga.estd_db_time > 0:
                    db_time_improvement = ((current_sga.estd_db_time - optimal_sga.estd_db_time) 
                                          / current_sga.estd_db_time * 100)
                    if db_time_improvement > 0:
                        lines.append(f"| **예상 성능 개선** | **{db_time_improvement:.1f}%** | "
                                   f"**DB Time 감소율** |")
            
            lines.append("")
            
            # 권장사항 분석
            if current_sga and optimal_sga:
                if not is_rac:
                    lines.append("### 권장사항 분석\n")
                else:
                    lines.append("#### 권장사항 분석\n")
                
                if optimal_sga.sga_size < current_sga.sga_size:
                    reduction_pct = ((current_sga.sga_size - optimal_sga.sga_size) 
                                   / current_sga.sga_size * 100)
                    lines.append(f"- 📉 **SGA 축소 권장**: 현재 SGA가 과다 할당되어 있습니다. "
                               f"{reduction_pct:.0f}% 축소해도 성능 저하 없이 메모리를 절약할 수 있습니다.")
                    lines.append(f"- 💰 **비용 절감 가능**: 마이그레이션 시 더 작은 인스턴스 선택 가능")
                elif optimal_sga.sga_size > current_sga.sga_size:
                    increase_pct = ((optimal_sga.sga_size - current_sga.sga_size) 
                                  / current_sga.sga_size * 100)
                    lines.append(f"- 📈 **SGA 확장 권장**: 현재 SGA가 부족합니다. "
                               f"{increase_pct:.0f}% 확장하면 성능이 개선됩니다.")
                    lines.append(f"- ⚠️ **마이그레이션 시 주의**: 타겟 인스턴스 메모리를 충분히 확보하세요.")
                else:
                    lines.append("- ✅ **현재 설정 적정**: SGA 크기가 최적화되어 있습니다.")
                
                lines.append("")
            
            # 상세 데이터 테이블
            if not is_rac:
                lines.append("### SGA 크기별 성능 예측\n")
            else:
                lines.append("#### SGA 크기별 성능 예측\n")
            lines.append("> 다양한 SGA 크기에서의 예상 성능입니다. "
                        "Size Factor 1.0이 현재 설정입니다.\n")
            lines.append("| SGA 크기 (MB) | Size Factor | 예상 DB Time | 예상 Physical Reads | 비고 |")
            lines.append("|---------------|-------------|--------------|---------------------|------|")
            
            for advice in inst_advice_list:
                note = ""
                if abs(advice.sga_size_factor - 1.0) < 0.01:
                    note = "현재"
                elif advice == optimal_sga:
                    note = "⭐ 권장"
                
                lines.append(f"| {advice.sga_size:,} | {advice.sga_size_factor:.2f} | "
                            f"{advice.estd_db_time:,} | {advice.estd_physical_reads:,} | {note} |")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _group_by_instance(sga_advice_list: List[SGAAdvice]) -> Dict[int, List[SGAAdvice]]:
        """SGA advice 데이터를 인스턴스별로 그룹화
        
        Args:
            sga_advice_list: SGAAdvice 객체 리스트
            
        Returns:
            inst_id를 키로 하는 딕셔너리
        """
        instances: Dict[int, List[SGAAdvice]] = {}
        for advice in sga_advice_list:
            inst_id = advice.inst_id
            if inst_id not in instances:
                instances[inst_id] = []
            instances[inst_id].append(advice)
        return instances
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 SGA 조정 권장사항"""
        lines = []
        
        lines.append("## 🔧 SGA Tuning Recommendations\n")
        lines.append("> Oracle SGA memory optimization recommendations.\n")
        
        # 인스턴스별로 그룹화
        instances = SGAAdviceFormatter._group_by_instance(data.sga_advice)
        is_rac = len(instances) > 1
        
        if is_rac:
            lines.append(f"> **RAC Environment**: {len(instances)} instances detected. "
                        "Check SGA recommendations for each instance.\n")
        
        # 인스턴스별로 처리
        for inst_id in sorted(instances.keys()):
            inst_advice_list = instances[inst_id]
            
            if is_rac:
                lines.append(f"---\n")
                lines.append(f"### Instance {inst_id}\n")
            
            current_sga = next(
                (a for a in inst_advice_list if abs(a.sga_size_factor - 1.0) < 0.01), None
            )
            optimal_sga = min(inst_advice_list, key=lambda x: x.estd_db_time)
            
            if not is_rac:
                lines.append("### Summary\n")
            else:
                lines.append("#### Summary\n")
            if current_sga:
                lines.append(f"- **Current SGA Size**: {current_sga.sga_size:,} MB")
            if optimal_sga:
                lines.append(f"- **Recommended SGA Size**: {optimal_sga.sga_size:,} MB")
            lines.append("")
            
            if not is_rac:
                lines.append("### SGA Size Performance Prediction\n")
            else:
                lines.append("#### SGA Size Performance Prediction\n")
            lines.append("| SGA Size (MB) | Size Factor | Est. DB Time | Est. Physical Reads | Note |")
            lines.append("|---------------|-------------|--------------|---------------------|------|")
            
            for advice in inst_advice_list:
                note = ""
                if abs(advice.sga_size_factor - 1.0) < 0.01:
                    note = "Current"
                elif advice == optimal_sga:
                    note = "⭐ Recommended"
                
                lines.append(f"| {advice.sga_size:,} | {advice.sga_size_factor:.2f} | "
                            f"{advice.estd_db_time:,} | {advice.estd_physical_reads:,} | {note} |")
            
            lines.append("")
        
        return "\n".join(lines)
