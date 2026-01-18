"""
Executive Summary 생성기

마이그레이션 추천의 Executive Summary를 생성합니다.
"""

import logging
from ..data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    MigrationRecommendation,
    ExecutiveSummary
)

# 로거 초기화
logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Executive Summary 생성기
    
    비기술적 언어로 작성하며, 약 500단어 또는 3000자 이내로 제한합니다.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
    """
    
    def generate_executive_summary(
        self,
        recommendation: MigrationRecommendation
    ) -> ExecutiveSummary:
        """
        Executive Summary 생성 (1페이지 이내)
        
        Args:
            recommendation: 마이그레이션 추천 결과
            
        Returns:
            ExecutiveSummary: Executive Summary
        """
        strategy = recommendation.recommended_strategy
        metrics = recommendation.metrics
        
        # 전략별 요약 텍스트 생성
        if strategy == MigrationStrategy.REPLATFORM:
            summary_text = self._generate_replatform_summary(metrics)
            key_benefits = [
                "코드 변경 최소화로 마이그레이션 위험 감소",
                "AI 도구 활용으로 빠른 마이그레이션 (5-8주, 전통적 방식 대비 40% 단축)",
                "기존 Oracle 기능 및 성능 유지",
                "AI 기반 자동 분석으로 인건비 약 35% 절감"
            ]
            key_risks = [
                "Oracle 라이선스 비용 지속 발생",
                "Single 인스턴스 제약 (RAC 미지원)",
                "장기적으로 클라우드 네이티브 이점 제한적"
            ]
            estimated_duration = "5-8주 (AI 도구 활용)"
        
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            summary_text = self._generate_mysql_summary(metrics)
            key_benefits = [
                "오픈소스 기반으로 라이선스 비용 절감",
                "AI 도구 활용으로 개발 기간 단축 (9-12주, 전통적 방식 대비 50% 단축)",
                "클라우드 네이티브 아키텍처 활용",
                "Aurora MySQL의 높은 성능 및 확장성",
                "AI 기반 코드 변환으로 인건비 약 45% 절감"
            ]
            key_risks = [
                "PL/SQL을 애플리케이션 레벨로 이관 필요",
                "BULK 연산 성능 저하 가능성",
                "복잡한 JOIN 쿼리 성능 최적화 필요"
            ]
            estimated_duration = "9-12주 (AI 도구 활용)"
        
        else:  # REFACTOR_POSTGRESQL
            summary_text = self._generate_postgresql_summary(metrics)
            key_benefits = [
                "PL/pgSQL로 PL/SQL 로직 대부분 변환 가능",
                "AI 도구 활용으로 변환 기간 단축 (9-12주, 전통적 방식 대비 50% 단축)",
                "오픈소스 기반으로 라이선스 비용 절감",
                "Aurora PostgreSQL의 고급 기능 활용",
                "AI 기반 자동 변환으로 인건비 약 45% 절감"
            ]
            key_risks = [
                "PL/SQL 변환 작업 필요 (일부 기능 미지원)",
                "BULK 연산 대체 시 성능 차이 발생",
                "외부 프로시저 호출 미지원"
            ]
            estimated_duration = "9-12주 (AI 도구 활용)"
        
        return ExecutiveSummary(
            recommended_strategy=strategy.value,
            estimated_duration=estimated_duration,
            key_benefits=key_benefits,
            key_risks=key_risks,
            summary_text=summary_text
        )
    
    def _generate_replatform_summary(self, metrics: AnalysisMetrics) -> str:
        """Replatform Executive Summary 생성"""
        plsql_count = self._get_plsql_count(metrics)
        
        # 복잡도 평가 (SQL과 PL/SQL 개별 평가)
        sql_level = "매우 높은" if metrics.avg_sql_complexity >= 7.0 else "중간" if metrics.avg_sql_complexity >= 5.0 else "낮은"
        plsql_level = "매우 높은" if metrics.avg_plsql_complexity >= 7.0 else "중간" if metrics.avg_plsql_complexity >= 5.0 else "낮은"
        
        # 복잡도가 높은지 판단 (둘 다 7.0 이상이면 매우 높음)
        is_high_complexity = metrics.avg_sql_complexity >= 7.0 and metrics.avg_plsql_complexity >= 7.0
        
        # 복잡도와 개수를 분리해서 표현 (접속사 선택)
        if plsql_count >= 100:
            # 개수가 매우 많음 - 복잡도가 매우 높으면 "또한", 아니면 "하지만"
            connector = "또한" if is_high_complexity else "하지만"
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. "
                f"{connector} PL/SQL 오브젝트가 {plsql_count}개로 매우 많아 변환이 거의 불가능합니다."
            )
        elif plsql_count >= 50:
            # 개수가 많음 - 복잡도가 매우 높으면 "또한", 아니면 "하지만"
            connector = "또한" if is_high_complexity else "하지만"
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다. "
                f"{connector} PL/SQL 오브젝트가 {plsql_count}개로 많아 변환 위험이 높습니다."
            )
        else:
            # 개수가 적음
            complexity_msg = (
                f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({sql_level}), "
                f"PL/SQL {metrics.avg_plsql_complexity:.1f}({plsql_level}) 수준입니다."
            )
        
        if metrics.high_complexity_ratio >= 0.3:
            complexity_msg += f" 전체 오브젝트 중 {metrics.high_complexity_ratio*100:.1f}%가 복잡도 7.0 이상으로 분류되어, 대규모 코드 변경 시 높은 위험이 예상됩니다."
        
        return f"""## 마이그레이션 추천: RDS for Oracle SE2 (Replatform)

귀사의 Oracle 데이터베이스 시스템을 분석한 결과, **RDS for Oracle SE2로의 Replatform 전략**을 추천드립니다.

### 추천 배경

{complexity_msg}

### 전략 개요

RDS for Oracle SE2는 기존 Oracle 데이터베이스를 AWS 클라우드로 이관하되, 코드 변경을 최소화하는 전략입니다. AI 도구(Amazon Q Developer, Bedrock)를 활용하여 마이그레이션 위험을 낮추고, 빠른 시일 내에 클라우드 이전을 완료할 수 있습니다.

### AI 도구 활용 효과

- **기간 단축**: 전통적 방식(8-12주) 대비 40% 단축 → **5-8주**
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
    
    def _generate_mysql_summary(self, metrics: AnalysisMetrics) -> str:
        """Aurora MySQL Executive Summary 생성"""
        plsql_count = self._get_plsql_count(metrics)
        
        # 복잡도 평가 (SQL과 PL/SQL 개별 평가)
        sql_level = "매우 높은" if metrics.avg_sql_complexity >= 7.0 else "중간" if metrics.avg_sql_complexity >= 5.0 else "낮은"
        plsql_level = "매우 높은" if metrics.avg_plsql_complexity >= 7.0 else "중간" if metrics.avg_plsql_complexity >= 5.0 else "낮은"
        
        bulk_warning = ""
        if metrics.bulk_operation_count >= 10:
            bulk_warning = f"\n\n**주의**: BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. MySQL은 BULK 연산을 지원하지 않으므로, 애플리케이션 레벨에서 배치 처리로 대체해야 합니다."
        
        # 개수에 따른 메시지
        if plsql_count < 20:
            plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개로 매우 적어, 애플리케이션 레벨로 이관이 매우 용이합니다."
        else:
            plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개로 적어, 애플리케이션 레벨로 이관이 충분히 가능합니다."
        
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

### 권장 사항

현재 시스템의 낮은 복잡도를 고려할 때, Aurora MySQL로의 전환은 장기적으로 가장 비용 효율적인 선택입니다. AI 도구를 적극 활용하여 개발 기간과 비용을 최소화하고, 충분한 테스트 기간을 확보하여 단계적으로 마이그레이션을 진행하시기를 권장드립니다."""
    
    def _generate_postgresql_summary(self, metrics: AnalysisMetrics) -> str:
        """Aurora PostgreSQL Executive Summary 생성"""
        plsql_count = self._get_plsql_count(metrics)
        
        # 복잡도 평가 (SQL과 PL/SQL 개별 평가)
        sql_level = "매우 높은" if metrics.avg_sql_complexity >= 7.0 else "중간" if metrics.avg_sql_complexity >= 5.0 else "낮은"
        plsql_level = "매우 높은" if metrics.avg_plsql_complexity >= 7.0 else "중간" if metrics.avg_plsql_complexity >= 5.0 else "낮은"
        
        bulk_info = ""
        if metrics.bulk_operation_count >= 10:
            bulk_info = f"\n\nBULK 연산이 {metrics.bulk_operation_count}개 발견되었으며, PostgreSQL에서는 순수 SQL 또는 Chunked Batch 방식으로 대체할 수 있습니다."
        
        # 개수와 복잡도에 따른 메시지 (50개 이하는 "적은" 수준)
        if plsql_count >= 100:
            plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개로 많지만, 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 PL/pgSQL로 대부분 변환이 가능합니다."
        elif plsql_count >= 50:
            plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개이고 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로, PL/pgSQL로 대부분 변환이 가능합니다."
        else:
            # 50개 미만은 "적은" 수준
            if metrics.avg_plsql_complexity >= 7.0:
                plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개로 적지만 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 높아 신중한 변환이 필요합니다."
            else:
                plsql_msg = f"PL/SQL 오브젝트가 {plsql_count}개로 적고 평균 복잡도({metrics.avg_plsql_complexity:.1f})도 중간 수준으로, PL/pgSQL로 변환이 용이합니다."
        
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

### 권장 사항

현재 시스템의 복잡도와 PL/SQL 사용량을 고려할 때, Aurora PostgreSQL은 Oracle 기능을 최대한 유지하면서도 비용을 절감할 수 있는 최적의 선택입니다. AI 도구를 적극 활용하여 변환 기간과 비용을 최소화하고, 미지원 기능을 사전에 식별하여 대체 방안을 수립하시기를 권장드립니다."""
    
    # Helper methods
    
    def _get_plsql_count(self, metrics: AnalysisMetrics) -> int:
        """PL/SQL 오브젝트 개수 계산 (AWR 우선)"""
        if any([metrics.awr_procedure_count, metrics.awr_function_count, metrics.awr_package_count]):
            count = 0
            if metrics.awr_procedure_count:
                count += self._extract_number(metrics.awr_procedure_count)
            if metrics.awr_function_count:
                count += self._extract_number(metrics.awr_function_count)
            if metrics.awr_package_count:
                count += self._extract_number(metrics.awr_package_count)
            return count
        return metrics.total_plsql_count
    
    def _extract_number(self, value) -> int:
        """문자열이나 숫자에서 숫자 값 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
