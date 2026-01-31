"""
Aurora MySQL 전략 Executive Summary 생성
"""

from ...data_models import AnalysisMetrics
from .base import SummaryBase


class MySQLSummaryGenerator(SummaryBase):
    """Aurora MySQL 전략 요약 생성기"""
    
    def generate(self, metrics: AnalysisMetrics) -> str:
        """Aurora MySQL Executive Summary 생성"""
        plsql_count = self.get_plsql_count(metrics)
        sql_level = self.get_complexity_level_text(metrics.avg_sql_complexity)
        plsql_level = self.get_complexity_level_text(metrics.avg_plsql_complexity)
        high_complexity_count = (
            metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count
        )
        
        bulk_warning = ""
        if metrics.bulk_operation_count >= 10:
            bulk_warning = (
                f"\n\n**주의**: BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. "
                f"MySQL은 BULK 연산을 지원하지 않으므로, 애플리케이션 레벨에서 배치 처리로 대체해야 합니다."
            )
        
        # 개수에 따른 메시지
        if plsql_count < 20:
            plsql_msg = (
                f"PL/SQL 오브젝트가 {plsql_count}개로 매우 적어, "
                f"애플리케이션 레벨로 이관이 매우 용이합니다."
            )
        else:
            plsql_msg = (
                f"PL/SQL 오브젝트가 {plsql_count}개로 적어, "
                f"애플리케이션 레벨로 이관이 충분히 가능합니다."
            )
        
        # 고복잡도 코드 경고 추가
        if high_complexity_count >= 20:
            plsql_msg += (
                f" 다만, 복잡도 7.0 이상의 고난이도 코드가 {high_complexity_count}개 존재하여 "
                f"애플리케이션 레벨로 이관 시 신중한 설계와 충분한 테스트가 필요합니다."
            )
        
        return f"""## 마이그레이션 추천: Aurora MySQL (Refactoring)

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **Aurora MySQL로의 Refactoring 전략**을 추천드립니다.

### 추천 배경

현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. {plsql_msg}{bulk_warning}

### 전략 개요

Aurora MySQL은 오픈소스 기반의 관계형 데이터베이스로, Oracle 라이선스 비용을 절감하면서도 높은 성능과 확장성을 제공합니다. AI 도구(Amazon Q Developer, Bedrock)를 활용하여 PL/SQL 로직을 애플리케이션 레이어로 효율적으로 이관하고, 클라우드 네이티브 아키텍처를 구현할 수 있습니다.

### AI 도구 활용 효과

- **기간 단축**: 전통적 방식(16-22주) 대비 50% 단축 → **9-12주**
- **비용 절감**: AI 기반 코드 변환 및 테스트 자동화로 인건비 약 45% 절감
- **품질 향상**: AI 도구로 자동 테스트 생성 및 코드 리뷰, 버그 조기 발견률 40% 향상

### 주요 이점

1. **비용 절감**: Oracle 라이선스 비용이 없어 TCO를 크게 절감할 수 있습니다
2. **클라우드 네이티브**: Aurora의 자동 스케일링, 자동 백업 등 클라우드 네이티브 기능을 활용할 수 있습니다
3. **높은 성능**: Aurora MySQL은 표준 MySQL 대비 5배 빠른 성능을 제공합니다
4. **빠른 개발**: AI 도구로 PL/SQL 변환 및 테스트 자동화

### 주요 고려사항

1. **PL/SQL 이관**: 모든 PL/SQL 로직을 애플리케이션 레벨로 이관해야 합니다 (AI 도구 활용 시 약 3-4주 소요)
2. **성능 테스트**: BULK 연산 대체 및 복잡한 JOIN 쿼리에 대한 성능 테스트가 필요합니다
3. **개발 리소스**: 애플리케이션 코드 변경을 위한 개발 리소스가 필요합니다 (AI 도구로 30% 절감)

### Refactoring 접근 방식 선택 가이드

Refactoring은 두 가지 접근 방식으로 진행할 수 있습니다:

#### 방식 1: Code-level Refactoring (권장)
- **개요**: 기존 데이터 모델을 유지하면서 PL/SQL 코드만 애플리케이션 레벨로 변환
- **기간**: 9-12주 (AI 도구 활용 시)
- **난이도**: 중간
- **적합한 경우**: 
  - 현재 데이터 모델이 비즈니스 요구사항을 충족하는 경우
  - 빠른 마이그레이션이 필요한 경우
  - 기존 애플리케이션과의 호환성 유지가 중요한 경우
- **장점**: 위험도 낮음, 기간 단축, 기존 쿼리 재사용 가능
- **단점**: 레거시 데이터 모델의 비효율성 유지

#### 방식 2: Data Model Refactoring (고급)
- **개요**: 데이터 모델을 리버스 엔지니어링하여 재설계 후 데이터 이관
- **기간**: 16-24주 (AI 도구 활용 시)
- **난이도**: 높음 ~ 매우 높음
- **적합한 경우**:
  - 현재 데이터 모델에 심각한 성능/설계 문제가 있는 경우
  - 비즈니스 요구사항이 크게 변경된 경우
  - 장기적인 유지보수성 개선이 필요한 경우
- **장점**: 성능 최적화, 확장성 향상, 기술 부채 해소
- **단점**: 높은 위험도, 긴 기간, 전문 인력 필요, 데이터 이관 검증 필수

**권장**: 현재 시스템의 낮은 복잡도를 고려할 때, **Code-level Refactoring**을 먼저 진행하고, 마이그레이션 완료 후 필요시 점진적으로 데이터 모델을 개선하는 것을 권장드립니다.

### 권장 사항

현재 시스템의 낮은 복잡도를 고려할 때, Aurora MySQL로의 전환은 장기적으로 가장 비용 효율적인 선택입니다. AI 도구를 적극 활용하여 개발 기간과 비용을 최소화하고, 충분한 테스트 기간을 확보하여 단계적으로 마이그레이션을 진행하시기를 권장드립니다."""
