"""
Replatform 전략 Executive Summary 생성

EC2 Rehost, RDS Custom, RDS Oracle 세부 전략별 요약을 생성합니다.
"""

from typing import List
from ...data_models import AnalysisMetrics
from .base import SummaryBase


class ReplatformSummaryGenerator(SummaryBase):
    """Replatform 전략 요약 생성기"""
    
    def generate(
        self, 
        metrics: AnalysisMetrics,
        sub_strategy: str,
        sub_strategy_reasons: List[str]
    ) -> str:
        """Replatform Executive Summary 생성
        
        Args:
            metrics: 분석 메트릭
            sub_strategy: Replatform 세부 전략 (ec2_rehost, rds_custom_oracle, rds_oracle)
            sub_strategy_reasons: 세부 전략 선택 이유
        """
        plsql_count = self.get_plsql_count(metrics)
        complexity_msg = self.build_complexity_message(metrics, plsql_count)
        
        if sub_strategy == "ec2_rehost":
            return self._generate_ec2_rehost(metrics, complexity_msg, sub_strategy_reasons)
        elif sub_strategy == "rds_custom_oracle":
            return self._generate_rds_custom(metrics, complexity_msg, sub_strategy_reasons)
        else:
            return self._generate_rds_oracle(metrics, complexity_msg)
    
    def _generate_ec2_rehost(
        self,
        metrics: AnalysisMetrics,
        complexity_msg: str,
        reasons: List[str]
    ) -> str:
        """EC2 Rehost Executive Summary 생성"""
        reasons_text = "\n".join([f"- {r}" for r in reasons]) if reasons else "- 최종 난이도가 매우 높음"
        
        return f"""## 마이그레이션 추천: EC2 Oracle (Lift & Shift)

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **EC2에서 Oracle을 운영하는 Lift & Shift 전략**을 추천드립니다.

### 추천 배경

{complexity_msg}

### 세부 전략 선택 이유

{reasons_text}

### 전략 개요

EC2 Rehost는 기존 Oracle 데이터베이스를 AWS EC2 인스턴스로 그대로 이관하는 전략입니다. 코드 변경 없이 가장 빠르게 클라우드로 이전할 수 있으며, Oracle RAC, EE 고급 기능 등 모든 기능을 그대로 사용할 수 있습니다.

### 주요 이점

1. **코드 변경 없음**: 기존 SQL 및 PL/SQL 코드를 100% 그대로 사용
2. **가장 빠른 마이그레이션**: 약 4-6주 내에 마이그레이션 완료 가능
3. **완전한 기능 유지**: Oracle RAC, EE 고급 기능 등 모든 기능 사용 가능
4. **OS 레벨 제어권**: 필요한 모든 커스터마이징 가능

### 주요 고려사항

1. **라이선스 비용**: Oracle 라이선스 비용 지속 발생 (BYOL)
2. **인프라 관리**: 패치, 백업, 모니터링 등 직접 관리 필요
3. **운영 부담**: RDS 대비 운영 복잡도 증가
4. **장기 전략**: 클라우드 네이티브 이점 제한적

### 권장 사항

현재 시스템의 복잡도와 Oracle 특화 기능 사용량을 고려할 때, EC2 Rehost는 가장 안전하고 빠른 클라우드 이전 방법입니다. 마이그레이션 완료 후 시스템 안정화를 거쳐, 장기적으로 RDS Custom 또는 오픈소스 DB로의 전환을 재검토하시기를 권장드립니다."""
    
    def _generate_rds_custom(
        self,
        metrics: AnalysisMetrics,
        complexity_msg: str,
        reasons: List[str]
    ) -> str:
        """RDS Custom for Oracle Executive Summary 생성"""
        reasons_text = "\n".join([f"- {r}" for r in reasons]) if reasons else "- 최종 난이도가 높음"
        
        return f"""## 마이그레이션 추천: RDS Custom for Oracle

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **RDS Custom for Oracle 전략**을 추천드립니다.

### 추천 배경

{complexity_msg}

### 세부 전략 선택 이유

{reasons_text}

### 전략 개요

RDS Custom for Oracle은 AWS 관리형 서비스의 이점을 누리면서도 OS 레벨 접근이 가능한 하이브리드 솔루션입니다. 코드 변경을 최소화하면서 필요한 커스터마이징을 수행할 수 있습니다.

### AI 도구 활용 효과

- **기간 단축**: 전통적 방식(8-12주) 대비 30% 단축 → **5-8주**
- **비용 절감**: AI 기반 자동 분석 및 검증으로 인건비 약 30% 절감
- **정확도 향상**: AI 도구로 EE 전용 기능 자동 탐지 및 호환성 검증

### 주요 이점

1. **OS 레벨 접근**: 필요한 커스터마이징 및 서드파티 에이전트 설치 가능
2. **관리형 서비스**: AWS 관리형 백업, 패치 지원
3. **코드 변경 최소화**: 기존 코드 대부분 그대로 사용
4. **유연성**: EC2와 RDS의 장점 결합

### 주요 고려사항

1. **라이선스 비용**: Oracle 라이선스 비용 지속 발생
2. **관리 복잡도**: 표준 RDS 대비 관리 복잡도 증가
3. **일부 제약**: 일부 RDS 자동화 기능 미지원
4. **장기 전략**: 클라우드 네이티브 이점 제한적

### 권장 사항

현재 시스템의 복잡도와 OS 레벨 접근 필요성을 고려할 때, RDS Custom for Oracle은 관리 편의성과 유연성을 모두 확보할 수 있는 최적의 선택입니다. AI 도구를 적극 활용하여 마이그레이션 기간과 비용을 최소화하시기 바랍니다."""
    
    def _generate_rds_oracle(
        self,
        metrics: AnalysisMetrics,
        complexity_msg: str
    ) -> str:
        """RDS for Oracle SE2 Executive Summary 생성 (기본)"""
        return f"""## 마이그레이션 추천: RDS for Oracle SE2 (Replatform)

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **RDS for Oracle SE2로의 Replatform 전략**을 추천드립니다.

### 추천 배경

{complexity_msg}

### 전략 개요

RDS for Oracle SE2는 기존 Oracle 데이터베이스를 AWS 클라우드로 이관하되, 코드 변경을 최소화하는 전략입니다. AI 도구(Amazon Q Developer, Bedrock)를 활용하여 마이그레이션 위험을 낮추고, 빠른 시일 내에 클라우드 이전을 완료할 수 있습니다.

### AI 도구 활용 효과

- **기간 단축**: 전통적 방식(8-12주) 대비 40% 단축 -> **5-8주**
- **비용 절감**: AI 기반 자동 분석 및 검증으로 인건비 약 35% 절감
- **정확도 향상**: AI 도구로 EE 전용 기능 자동 탐지 및 호환성 검증

### 주요 이점

1. **코드 변경 최소화**: 기존 SQL 및 PL/SQL 코드를 거의 그대로 사용할 수 있어 개발 부담이 적습니다
2. **빠른 마이그레이션**: AI 도구 활용으로 약 5-8주 내에 마이그레이션을 완료할 수 있습니다
3. **기능 및 성능 유지**: Oracle의 모든 기능과 성능을 그대로 유지할 수 있습니다

### 주요 고려사항

1. **라이선스 비용**: Oracle 라이선스 비용이 지속적으로 발생합니다
2. **Single 인스턴스 제약**: SE2는 Single 인스턴스만 지원하므로 RAC 기능을 사용할 수 없습니다. Multi-AZ 배포로 고가용성을 확보할 수 있습니다
3. **장기 전략**: 장기적으로는 오픈소스 데이터베이스로의 전환을 재검토할 필요가 있습니다

### 권장 사항

현재 시스템의 복잡도와 PL/SQL 오브젝트 개수를 고려할 때, Replatform은 가장 안전하고 빠른 클라우드 이전 방법입니다. AI 도구를 적극 활용하여 마이그레이션 기간과 비용을 최소화하시기 바랍니다. 마이그레이션 완료 후, 시스템 안정화를 거쳐 장기적으로 Refactoring 전략을 재검토하시기를 권장드립니다."""
