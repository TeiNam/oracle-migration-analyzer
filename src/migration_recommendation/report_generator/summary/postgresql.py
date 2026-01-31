"""
Aurora PostgreSQL 전략 Executive Summary 생성
"""

from ...data_models import AnalysisMetrics
from .base import SummaryBase


class PostgreSQLSummaryGenerator(SummaryBase):
    """Aurora PostgreSQL 전략 요약 생성기"""
    
    def generate(self, metrics: AnalysisMetrics) -> str:
        """Aurora PostgreSQL Executive Summary 생성"""
        plsql_count = self.get_plsql_count(metrics)
        sql_level = self.get_complexity_level_text(metrics.avg_sql_complexity)
        plsql_level = self.get_complexity_level_text(metrics.avg_plsql_complexity)
        high_complexity_count = (
            metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count
        )
        
        bulk_info = ""
        if metrics.bulk_operation_count >= 10:
            bulk_info = (
                f"\n\nBULK 연산이 {metrics.bulk_operation_count}개 발견되었으며, "
                f"PostgreSQL에서는 순수 SQL 또는 Chunked Batch 방식으로 대체할 수 있습니다."
            )
        
        # 개수와 복잡도에 따른 메시지
        if plsql_count >= 100:
            plsql_msg = (
                f"PL/SQL 오브젝트가 {plsql_count}개로 많지만, "
                f"평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 "
                f"PL/pgSQL로 대부분 변환이 가능합니다."
            )
        elif plsql_count >= 50:
            plsql_msg = (
                f"PL/SQL 오브젝트가 {plsql_count}개이고 "
                f"평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로, "
                f"PL/pgSQL로 대부분 변환이 가능합니다."
            )
        else:
            if metrics.avg_plsql_complexity >= 7.0:
                plsql_msg = (
                    f"PL/SQL 오브젝트가 {plsql_count}개로 적지만 "
                    f"평균 복잡도({metrics.avg_plsql_complexity:.1f})가 높아 "
                    f"신중한 변환이 필요합니다."
                )
            else:
                plsql_msg = (
                    f"PL/SQL 오브젝트가 {plsql_count}개로 적고 "
                    f"평균 복잡도({metrics.avg_plsql_complexity:.1f})도 중간 수준으로, "
                    f"PL/pgSQL로 변환이 용이합니다."
                )
        
        # 고복잡도 코드 경고 추가
        if high_complexity_count >= 20:
            plsql_msg += (
                f" 다만, 복잡도 7.0 이상의 고난이도 코드가 {high_complexity_count}개 존재하여 "
                f"PL/pgSQL 변환 시 전문가의 검토와 충분한 테스트가 필요합니다."
            )
        
        return f"""## 마이그레이션 추천: Aurora PostgreSQL (Refactoring)

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **Aurora PostgreSQL로의 Refactoring 전략**을 추천드립니다.

### 추천 배경

현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. {plsql_msg}{bulk_info}

### 전략 개요

Aurora PostgreSQL은 Oracle과 높은 호환성을 제공하는 오픈소스 데이터베이스입니다. AI 도구(Amazon Q Developer, Bedrock)를 활용하여 PL/SQL의 70-75%를 PL/pgSQL로 자동 변환할 수 있어, 복잡한 비즈니스 로직을 데이터베이스 레벨에서 유지하면서도 라이선스 비용을 절감할 수 있습니다.

### AI 도구 활용 효과

- **기간 단축**: 전통적 방식(16-22주) 대비 50% 단축 → **9-12주**
- **비용 절감**: AI 기반 자동 변환 및 테스트로 인건비 약 45% 절감
- **변환 성공률**: AI 도구로 단순 로직 70-80% 자동 변환, 복잡한 로직도 AI 제안 활용

### 주요 이점

1. **PL/SQL 호환성**: PL/pgSQL로 대부분의 PL/SQL 로직을 변환할 수 있습니다
2. **비용 절감**: Oracle 라이선스 비용이 없어 TCO를 크게 절감할 수 있습니다
3. **고급 기능**: PostgreSQL의 고급 데이터 타입, JSON 지원 등을 활용할 수 있습니다
4. **빠른 변환**: AI 도구로 PL/SQL → PL/pgSQL 변환 자동화

### 주요 고려사항

1. **PL/SQL 변환**: PL/SQL을 PL/pgSQL로 변환하는 작업이 필요합니다 (AI 도구 활용 시 약 3-4주 소요)
2. **일부 기능 미지원**: 패키지 변수, PRAGMA, 외부 프로시저 호출 등 일부 기능은 미지원됩니다
3. **성능 차이**: BULK 연산 대체 시 20-50%의 성능 차이가 발생할 수 있습니다

### Refactoring 접근 방식 선택 가이드

Refactoring은 두 가지 접근 방식으로 진행할 수 있습니다:

#### 방식 1: Code-level Refactoring (권장)
- **개요**: 기존 데이터 모델을 유지하면서 PL/SQL을 PL/pgSQL로 변환
- **기간**: 9-12주 (AI 도구 활용 시)
- **난이도**: 중간
- **적합한 경우**: 
  - 현재 데이터 모델이 비즈니스 요구사항을 충족하는 경우
  - 빠른 마이그레이션이 필요한 경우
  - PL/SQL 로직을 데이터베이스 레벨에서 유지하고 싶은 경우
- **장점**: 위험도 낮음, 기간 단축, PL/pgSQL로 70-75% 자동 변환 가능
- **단점**: 레거시 데이터 모델의 비효율성 유지

#### 방식 2: Data Model Refactoring (고급)
- **개요**: 데이터 모델을 리버스 엔지니어링하여 재설계 후 데이터 이관
- **기간**: 16-24주 (AI 도구 활용 시)
- **난이도**: 높음 ~ 매우 높음
- **적합한 경우**:
  - 현재 데이터 모델에 심각한 성능/설계 문제가 있는 경우
  - 정규화/비정규화 재검토가 필요한 경우
  - 장기적인 유지보수성 개선이 필요한 경우
- **장점**: 성능 최적화, PostgreSQL 고유 기능 활용 (JSONB, Array 등), 기술 부채 해소
- **단점**: 높은 위험도, 긴 기간, 전문 인력 필요, 데이터 이관 검증 필수

**권장**: 현재 시스템의 복잡도를 고려할 때, **Code-level Refactoring**을 먼저 진행하고, 마이그레이션 완료 후 필요시 점진적으로 데이터 모델을 개선하는 것을 권장드립니다.

### 권장 사항

현재 시스템의 복잡도와 PL/SQL 사용량을 고려할 때, Aurora PostgreSQL은 Oracle 기능을 최대한 유지하면서도 비용을 절감할 수 있는 최적의 선택입니다. AI 도구를 적극 활용하여 변환 기간과 비용을 최소화하고, 미지원 기능을 사전에 식별하여 대체 방안을 수립하시기를 권장드립니다."""
