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
    
    의사결정 트리를 기반으로 최적의 마이그레이션 전략을 결정합니다.
    
    의사결정 우선순위:
    1. 코드 복잡도 평가 (최우선)
    2. Replatform 조건 확인 (복잡도 >= 7.0 또는 복잡 오브젝트 >= 30%)
    3. Aurora MySQL 조건 확인 (복잡도 <= 5.0, PL/SQL 단순)
    4. Aurora PostgreSQL 조건 확인 (BULK 많음 또는 중간 복잡도)
    """
    
    def decide_strategy(
        self,
        integrated_result: IntegratedAnalysisResult
    ) -> MigrationStrategy:
        """
        최적의 마이그레이션 전략을 결정합니다.
        
        의사결정 트리:
        1. 복잡도 7.0 이상 또는 복잡 오브젝트 30% 이상 → Replatform
        2. BULK 연산 많음 (10개 이상) → Aurora PostgreSQL (우선)
        3. 복잡도 5.0 이하 + PL/SQL 단순 → Aurora MySQL
        4. 복잡도 5.0-7.0 + PL/SQL 복잡 → Aurora PostgreSQL
        
        Args:
            integrated_result: 통합 분석 결과
            
        Returns:
            MigrationStrategy: 추천 전략
        """
        metrics = integrated_result.metrics
        
        # 1. Replatform 조건 확인 (최우선)
        if self._should_replatform(metrics):
            return MigrationStrategy.REPLATFORM
        
        # 2. BULK 연산이 많으면 PostgreSQL 우선 (MySQL은 BULK 미지원)
        if metrics.bulk_operation_count >= 10:
            return MigrationStrategy.REFACTOR_POSTGRESQL
        
        # 3. Aurora MySQL 조건 확인
        if self._should_refactor_mysql(metrics):
            return MigrationStrategy.REFACTOR_MYSQL
        
        # 4. Aurora PostgreSQL 조건 확인
        if self._should_refactor_postgresql(metrics):
            return MigrationStrategy.REFACTOR_POSTGRESQL
        
        # 5. 기본값: Aurora PostgreSQL (중간 복잡도)
        return MigrationStrategy.REFACTOR_POSTGRESQL
    
    def _should_replatform(self, metrics: AnalysisMetrics) -> bool:
        """
        Replatform 조건 확인
        
        조건:
        - 평균 SQL 복잡도 >= 7.0 또는
        - 평균 PL/SQL 복잡도 >= 7.0 또는
        - 복잡도 7.0 이상 오브젝트가 30% 이상
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            bool: Replatform 조건 만족 여부
        """
        # 평균 복잡도 7.0 이상
        if metrics.avg_sql_complexity >= 7.0 or metrics.avg_plsql_complexity >= 7.0:
            return True
        
        # 복잡도 7.0 이상 오브젝트가 30% 이상
        if metrics.high_complexity_ratio >= 0.3:
            return True
        
        return False
    
    def _should_refactor_mysql(self, metrics: AnalysisMetrics) -> bool:
        """
        Aurora MySQL 조건 확인
        
        조건:
        - 평균 SQL 복잡도 <= 5.0 그리고
        - 평균 PL/SQL 복잡도 <= 5.0 그리고
        - PL/SQL 오브젝트 < 50개
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            bool: Aurora MySQL 조건 만족 여부
        """
        # 평균 SQL 복잡도 5.0 이하
        if metrics.avg_sql_complexity > 5.0:
            return False
        
        # PL/SQL이 단순 (평균 5.0 이하)
        if metrics.avg_plsql_complexity > 5.0:
            return False
        
        # PL/SQL 오브젝트가 적음
        if metrics.total_plsql_count >= 50:
            return False
        
        return True
    
    def _should_refactor_postgresql(self, metrics: AnalysisMetrics) -> bool:
        """
        Aurora PostgreSQL 조건 확인
        
        조건:
        - BULK 연산 >= 10개 또는
        - 복잡도 5.0-7.0 범위 또는
        - PL/SQL이 복잡 (평균 5.0 이상)
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            bool: Aurora PostgreSQL 조건 만족 여부
        """
        # BULK 연산이 많음 (10개 이상)
        if metrics.bulk_operation_count >= 10:
            return True
        
        # 복잡도 5.0-7.0 범위
        if 5.0 <= metrics.avg_sql_complexity < 7.0:
            return True
        
        # PL/SQL이 복잡 (평균 5.0 이상)
        if metrics.avg_plsql_complexity >= 5.0:
            return True
        
        return False
