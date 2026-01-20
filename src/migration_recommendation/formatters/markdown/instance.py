"""
Markdown 인스턴스 추천 포맷터

인스턴스 추천 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import InstanceRecommendation


class InstanceFormatterMixin:
    """인스턴스 추천 포맷터 믹스인"""
    
    @staticmethod
    def _format_instance_recommendation(instance: InstanceRecommendation, language: str) -> str:
        """인스턴스 추천 섹션 포맷
        
        Args:
            instance: 인스턴스 추천 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            # 기본 인스턴스 정보
            result = f"""# 인스턴스 추천

## 권장 인스턴스 타입

- **인스턴스 타입**: {instance.instance_type}
- **vCPU**: {instance.vcpu}
- **메모리**: {instance.memory_gb} GB

### 추천 근거

{instance.rationale}
"""
            
            # RAC 평가 추가 (있는 경우)
            if instance.rac_assessment:
                result += f"""
### RAC 필요성 평가

{instance.rac_assessment}
"""
            
            # HA 권장사항 추가 (있는 경우)
            if instance.ha_recommendation:
                result += f"""
### 고가용성 구성 권장사항

{instance.ha_recommendation}
"""
            
            # 참고사항
            result += """
### 참고사항

- 위 인스턴스는 현재 성능 메트릭을 기반으로 한 권장 사항입니다
- 실제 마이그레이션 시 부하 테스트를 통해 최적 사이즈를 결정하시기 바랍니다
- Aurora의 경우 자동 스케일링 기능을 활용하여 유연하게 확장 가능합니다
"""
            return result
            
        else:  # English
            # 기본 인스턴스 정보
            result = f"""# Instance Recommendation

## Recommended Instance Type

- **Instance Type**: {instance.instance_type}
- **vCPU**: {instance.vcpu}
- **Memory**: {instance.memory_gb} GB

### Rationale

{instance.rationale}
"""
            
            # RAC 평가 추가 (있는 경우)
            if instance.rac_assessment:
                result += f"""
### RAC Necessity Assessment

{instance.rac_assessment}
"""
            
            # HA 권장사항 추가 (있는 경우)
            if instance.ha_recommendation:
                result += f"""
### High Availability Configuration Recommendation

{instance.ha_recommendation}
"""
            
            # 참고사항
            result += """
### Notes

- The recommended instance is based on current performance metrics
- Please conduct load testing during actual migration to determine optimal sizing
- For Aurora, you can leverage auto-scaling features for flexible expansion
"""
            return result
