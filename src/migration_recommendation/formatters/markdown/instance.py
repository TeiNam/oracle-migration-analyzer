"""
Markdown 인스턴스 추천 포맷터

인스턴스 추천 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import Optional
from ...data_models import InstanceRecommendation, AnalysisMetrics


# 전략별 여유율 상수
REPLATFORM_BUFFER_RATE = 0.20  # Replatform: 20% 여유율 (동일 엔진)
REFACTORING_BUFFER_RATE = 0.50  # Refactoring: 50% 여유율 (엔진 변경으로 인한 불확실성)


class InstanceFormatterMixin:
    """인스턴스 추천 포맷터 믹스인"""
    
    @staticmethod
    def _format_instance_recommendation(
        instance: InstanceRecommendation,
        language: str,
        metrics: Optional[AnalysisMetrics] = None,
        strategy: str = "refactor_postgresql"
    ) -> str:
        """인스턴스 추천 섹션 포맷
        
        Args:
            instance: 인스턴스 추천 데이터
            language: 언어 ("ko" 또는 "en")
            metrics: 분석 메트릭 (PL/SQL 오브젝트 정보 포함)
            strategy: 추천 전략 (replatform, refactor_postgresql, refactor_mysql)
            
        Returns:
            Markdown 형식 문자열
        """
        if language == "ko":
            return InstanceFormatterMixin._format_instance_ko(instance, metrics, strategy)
        return InstanceFormatterMixin._format_instance_en(instance, metrics, strategy)
    
    @staticmethod
    def _get_buffer_rate(strategy: str) -> float:
        """전략별 여유율 반환
        
        Args:
            strategy: 추천 전략
            
        Returns:
            여유율 (0.0 ~ 1.0)
        """
        if strategy == "replatform":
            return REPLATFORM_BUFFER_RATE
        return REFACTORING_BUFFER_RATE
    
    @staticmethod
    def _get_buffer_description(strategy: str, language: str) -> str:
        """전략별 여유율 설명 반환"""
        if strategy == "replatform":
            if language == "ko":
                return "동일 Oracle 엔진 유지로 성능 예측이 용이하여 20% 여유율 적용"
            return "20% buffer applied as performance is predictable with same Oracle engine"
        else:
            if language == "ko":
                return "엔진 변경(Oracle→Aurora)으로 인한 성능 불확실성을 고려하여 50% 여유율 적용"
            return "50% buffer applied to account for performance uncertainty from engine change"
    
    @staticmethod
    def _format_instance_ko(
        instance: InstanceRecommendation,
        metrics: Optional[AnalysisMetrics] = None,
        strategy: str = "refactor_postgresql"
    ) -> str:
        """한국어 인스턴스 추천 포맷"""
        buffer_rate = InstanceFormatterMixin._get_buffer_rate(strategy)
        buffer_pct = int(buffer_rate * 100)
        buffer_desc = InstanceFormatterMixin._get_buffer_description(strategy, "ko")
        
        # 전략별 타겟 DB 이름
        target_db_name = {
            "replatform": "RDS for Oracle",
            "refactor_postgresql": "Aurora PostgreSQL",
            "refactor_mysql": "Aurora MySQL"
        }.get(strategy, "Aurora")
        
        # 기본 인스턴스 정보
        result = f"""# 인스턴스 추천

> **이 섹션의 목적**: AWR/Statspack 성능 데이터를 기반으로
> {target_db_name}에 적합한 **AWS 인스턴스 타입**을 추천합니다.
> 실제 운영 전 부하 테스트로 검증이 필요합니다.

## 권장 인스턴스 타입

- **인스턴스 타입**: {instance.instance_type}
- **vCPU**: {instance.vcpu}
- **메모리**: {instance.memory_gb} GB
- **적용 여유율**: {buffer_pct}%

### 추천 근거

{instance.rationale}

> **여유율 산정 기준**: {buffer_desc}
"""
        
        # SGA 기반 인스턴스 비교 테이블 추가
        if instance.sga_based_instance_type:
            result += f"""
## 인스턴스 추천 비교

SGA 권장사항을 반영한 인스턴스와 현재 서버 사양 기반 인스턴스를 비교합니다.

| 구분 | 현재 서버 사양 기반 | SGA 권장사항 기반 |
|------|---------------------|-------------------|
| **인스턴스 타입** | {instance.instance_type} | {instance.sga_based_instance_type} |
| **vCPU** | {instance.vcpu} | {instance.sga_based_vcpu} |
| **메모리** | {instance.memory_gb} GB | {instance.sga_based_memory_gb} GB |

### SGA 분석 결과

| 항목 | 값 |
|------|-----|
| **현재 SGA 크기** | {instance.current_sga_gb:.1f} GB |
| **권장 SGA 크기** | {instance.recommended_sga_gb:.1f} GB |
| **SGA 증가율** | {((instance.recommended_sga_gb / instance.current_sga_gb - 1) * 100):.1f}% |

> **참고**: SGA 권장사항은 AWR 리포트의 Buffer Pool Advisory 데이터를 기반으로 
> Physical Reads가 더 이상 감소하지 않는 최적 지점을 분석한 결과입니다.
> 권장 SGA가 현재 SGA보다 큰 경우, 메모리 증설을 통해 I/O 성능을 개선할 수 있습니다.
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
    
    @staticmethod
    def _format_instance_en(
        instance: InstanceRecommendation,
        metrics: Optional[AnalysisMetrics] = None,
        strategy: str = "refactor_postgresql"
    ) -> str:
        """영어 인스턴스 추천 포맷"""
        buffer_rate = InstanceFormatterMixin._get_buffer_rate(strategy)
        buffer_pct = int(buffer_rate * 100)
        buffer_desc = InstanceFormatterMixin._get_buffer_description(strategy, "en")
        
        # 전략별 타겟 DB 이름
        target_db_name = {
            "replatform": "RDS for Oracle",
            "refactor_postgresql": "Aurora PostgreSQL",
            "refactor_mysql": "Aurora MySQL"
        }.get(strategy, "Aurora")
        
        # 기본 인스턴스 정보
        result = f"""# Instance Recommendation

> **Purpose**: Recommend appropriate **AWS instance type** for {target_db_name}
> based on AWR/Statspack performance data.
> Load testing is required before production deployment.

## Recommended Instance Type

- **Instance Type**: {instance.instance_type}
- **vCPU**: {instance.vcpu}
- **Memory**: {instance.memory_gb} GB
- **Buffer Rate**: {buffer_pct}%

### Rationale

{instance.rationale}

> **Buffer Rate Basis**: {buffer_desc}
"""
        
        # SGA 기반 인스턴스 비교 테이블 추가
        if instance.sga_based_instance_type:
            result += f"""
## Instance Recommendation Comparison

Comparison between current server specs based instance and SGA recommendation based instance.

| Category | Current Server Specs | SGA Recommendation |
|----------|---------------------|-------------------|
| **Instance Type** | {instance.instance_type} | {instance.sga_based_instance_type} |
| **vCPU** | {instance.vcpu} | {instance.sga_based_vcpu} |
| **Memory** | {instance.memory_gb} GB | {instance.sga_based_memory_gb} GB |

### SGA Analysis Results

| Item | Value |
|------|-------|
| **Current SGA Size** | {instance.current_sga_gb:.1f} GB |
| **Recommended SGA Size** | {instance.recommended_sga_gb:.1f} GB |
| **SGA Increase Rate** | {((instance.recommended_sga_gb / instance.current_sga_gb - 1) * 100):.1f}% |

> **Note**: SGA recommendation is based on Buffer Pool Advisory data from AWR report,
> analyzing the optimal point where Physical Reads no longer decrease.
> If recommended SGA is larger than current SGA, memory expansion can improve I/O performance.
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
