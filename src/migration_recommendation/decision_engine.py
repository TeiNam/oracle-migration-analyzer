"""
마이그레이션 의사결정 엔진

Oracle 데이터베이스의 AWS 클라우드 마이그레이션 시 최적의 전략을 결정합니다.
"""

from typing import Optional
from .data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy
)


class MigrationDecisionEngine:
    """
    마이그레이션 의사결정 엔진
    
    PL/SQL 개수와 복잡도를 2차원으로 고려하여 최적의 전략을 결정합니다.
    
    의사결정 매트릭스 (PL/SQL 개수 x 복잡도):
    
    복잡도 높음(7.0+) + 많음(100+)  → Replatform (변환 불가능)
    복잡도 높음(7.0+) + 중간(50-100) → Replatform (위험 높음)
    복잡도 높음(7.0+) + 적음(50-)   → PostgreSQL (신중한 변환)
    
    복잡도 중간(5.0-7.0) + 많음(100+)  → PostgreSQL (변환 가능)
    복잡도 중간(5.0-7.0) + 중간(50-100) → PostgreSQL (적합)
    복잡도 중간(5.0-7.0) + 적음(50-)   → PostgreSQL (권장)
    
    복잡도 낮음(5.0-) + 많음(100+)  → PostgreSQL (변환 용이하나 작업량 많음)
    복잡도 낮음(5.0-) + 중간(50-100) → PostgreSQL 또는 MySQL
    복잡도 낮음(5.0-) + 적음(50-)   → MySQL (강력 추천)
    """
    
    def decide_strategy(
        self,
        integrated_result: IntegratedAnalysisResult
    ) -> MigrationStrategy:
        """
        최적의 마이그레이션 전략을 결정합니다.
        
        의사결정 로직:
        1. PL/SQL 개수와 복잡도를 2차원으로 평가
        2. 복잡도가 높고 개수가 많으면 → Replatform
        3. 복잡도가 낮고 개수가 적으면 → MySQL (강력 추천)
        4. 중간 영역 → PostgreSQL
        5. BULK 연산이 많으면 PostgreSQL 우선
        
        Args:
            integrated_result: 통합 분석 결과
            
        Returns:
            MigrationStrategy: 추천 전략
        """
        metrics = integrated_result.metrics
        
        # PL/SQL 개수 (AWR 통계 우선, 없으면 분석 파일 개수)
        plsql_count = self._get_plsql_count(metrics)
        plsql_complexity = metrics.avg_plsql_complexity
        
        # 1. Replatform 조건: 복잡도 높음 + 개수 많음
        if self._should_replatform(metrics, plsql_count, plsql_complexity):
            return MigrationStrategy.REPLATFORM
        
        # 2. BULK 연산이 많으면 PostgreSQL 우선 (MySQL은 BULK 미지원)
        if metrics.bulk_operation_count >= 10:
            return MigrationStrategy.REFACTOR_POSTGRESQL
        
        # 3. MySQL 조건: 복잡도 낮음 + 개수 적음
        if self._should_refactor_mysql(metrics, plsql_count, plsql_complexity):
            return MigrationStrategy.REFACTOR_MYSQL
        
        # 4. 기본값: PostgreSQL (중간 영역)
        return MigrationStrategy.REFACTOR_POSTGRESQL
    
    def _get_plsql_count(self, metrics: AnalysisMetrics) -> int:
        """
        PL/SQL 오브젝트 개수 계산
        
        AWR 통계가 있으면 우선 사용, 없으면 분석 파일 개수 사용
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            int: PL/SQL 오브젝트 개수
        """
        # AWR 통계 우선 (프로시저 + 함수 + 패키지)
        if any([metrics.awr_procedure_count, metrics.awr_function_count, metrics.awr_package_count]):
            count = 0
            if metrics.awr_procedure_count:
                count += metrics.awr_procedure_count
            if metrics.awr_function_count:
                count += metrics.awr_function_count
            if metrics.awr_package_count:
                count += metrics.awr_package_count
            return count
        
        # AWR 통계 없으면 분석 파일 개수
        return metrics.total_plsql_count
    
    def _should_replatform(
        self, 
        metrics: AnalysisMetrics,
        plsql_count: int,
        plsql_complexity: float
    ) -> bool:
        """
        Replatform 조건 확인 (2차원 평가)
        
        조건 (OR 관계):
        1. 복잡도 매우 높음 (평균 8.0 이상)
        2. 복잡도 높음 (7.0 이상) + 개수 많음 (100개 이상)
        3. 복잡도 높음 (7.0 이상) + 개수 중간 (50-100개)
        4. 복잡 오브젝트 비율 40% 이상
        
        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            plsql_complexity: PL/SQL 평균 복잡도
            
        Returns:
            bool: Replatform 조건 만족 여부
        """
        # 1. 복잡도 매우 높음 (변환 거의 불가능)
        if plsql_complexity >= 8.0 or metrics.avg_sql_complexity >= 8.0:
            return True
        
        # 2. 복잡도 높음 + 개수 많음 (변환 불가능)
        if plsql_complexity >= 7.0 and plsql_count >= 100:
            return True
        
        # 3. 복잡도 높음 + 개수 중간 (위험 높음)
        if plsql_complexity >= 7.0 and plsql_count >= 50:
            return True
        
        # 4. 복잡 오브젝트 비율 매우 높음
        if metrics.high_complexity_ratio >= 0.4:
            return True
        
        return False
    
    def _should_refactor_mysql(
        self,
        metrics: AnalysisMetrics,
        plsql_count: int,
        plsql_complexity: float
    ) -> bool:
        """
        Aurora MySQL 조건 확인 (2차원 평가)
        
        조건 (AND 관계):
        1. 복잡도 낮음 (평균 5.0 이하)
        2. 개수 적음 (50개 미만)
        3. BULK 연산 적음 (10개 미만)
        
        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            plsql_complexity: PL/SQL 평균 복잡도
            
        Returns:
            bool: Aurora MySQL 조건 만족 여부
        """
        # 1. 복잡도 낮음
        if plsql_complexity > 5.0 or metrics.avg_sql_complexity > 5.0:
            return False
        
        # 2. 개수 적음 (강력 추천 조건)
        if plsql_count >= 50:
            return False
        
        # 3. BULK 연산 적음
        if metrics.bulk_operation_count >= 10:
            return False
        
        return True
