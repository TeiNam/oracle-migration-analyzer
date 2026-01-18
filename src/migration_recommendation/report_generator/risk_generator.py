"""
위험 요소 생성기

마이그레이션 전략별 위험 요소를 생성합니다.
"""

import logging
from typing import List
from ..data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    Risk
)

# 로거 초기화
logger = logging.getLogger(__name__)


class RiskGenerator:
    """
    위험 요소 생성기
    
    전략별 위험 요소를 식별하고 완화 방안을 제시합니다.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    def generate_risks(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Risk]:
        """
        위험 요소 생성 (3-5개)
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[Risk]: 위험 요소 리스트 (3-5개)
        """
        if strategy == MigrationStrategy.REPLATFORM:
            return self._generate_replatform_risks(metrics)
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            return self._generate_mysql_risks(metrics)
        else:  # REFACTOR_POSTGRESQL
            return self._generate_postgresql_risks(metrics)
    
    def _generate_replatform_risks(self, metrics: AnalysisMetrics) -> List[Risk]:
        """Replatform 전략 위험 요소 생성"""
        risks = [
            Risk(
                category="operational",
                description="RDS Oracle SE2는 Single 인스턴스만 지원하여 RAC 기능을 사용할 수 없습니다",
                severity="high",
                mitigation="Multi-AZ 배포로 고가용성 확보, Read Replica로 읽기 부하 분산"
            ),
            Risk(
                category="technical",
                description="Oracle Enterprise Edition 기능 사용 시 SE2로 마이그레이션 불가능할 수 있습니다",
                severity="high",
                mitigation="사전에 EE 전용 기능 사용 여부 확인 및 대체 방안 수립"
            ),
            Risk(
                category="performance",
                description="Single 인스턴스로 인한 성능 제약이 있을 수 있습니다",
                severity="medium",
                mitigation="인스턴스 사이징 최적화, 성능 테스트 수행"
            ),
            Risk(
                category="cost",
                description="Oracle 라이선스 비용이 지속적으로 발생합니다",
                severity="medium",
                mitigation="장기적으로 Refactoring 전략 재검토"
            )
        ]
        
        # RAC 사용 중이면 추가 위험
        if metrics.rac_detected:
            risks.append(Risk(
                category="operational",
                description="현재 RAC를 사용 중이므로 Single 인스턴스로 전환 시 아키텍처 변경이 필요합니다",
                severity="high",
                mitigation="애플리케이션 연결 로직 수정, 로드 밸런싱 전략 재설계"
            ))
        
        return risks[:5]
    
    def _generate_mysql_risks(self, metrics: AnalysisMetrics) -> List[Risk]:
        """Aurora MySQL 전략 위험 요소 생성"""
        risks = [
            Risk(
                category="technical",
                description="모든 PL/SQL 로직을 애플리케이션 레벨로 이관해야 합니다",
                severity="high",
                mitigation="단계적 이관 계획 수립, 충분한 테스트 기간 확보"
            ),
            Risk(
                category="technical",
                description="복잡한 JOIN (3개 이상) 시 MySQL 성능 저하 가능성이 있습니다",
                severity="medium",
                mitigation="쿼리 최적화, 인덱스 전략 수립"
            )
        ]
        
        # BULK 연산 위험
        if metrics.bulk_operation_count >= 10:
            risks.append(Risk(
                category="performance",
                description=f"BULK 연산 {metrics.bulk_operation_count}개를 루프로 변환 시 성능 저하 가능성이 높습니다",
                severity="high",
                mitigation="배치 처리 최적화, 성능 테스트 수행, 필요시 PostgreSQL 재검토"
            ))
        else:
            risks.append(Risk(
                category="performance",
                description="BULK 연산을 루프로 변환 시 성능 저하 가능성이 있습니다",
                severity="medium",
                mitigation="배치 처리 최적화, 성능 테스트 수행"
            ))
        
        # 개발 리소스 위험
        risks.append(Risk(
            category="operational",
            description=f"PL/SQL {metrics.total_plsql_count}개를 애플리케이션으로 이관하기 위한 개발 리소스가 필요합니다",
            severity="medium",
            mitigation="충분한 개발 인력 확보, 단계적 이관 계획"
        ))
        
        return risks[:5]
    
    def _generate_postgresql_risks(self, metrics: AnalysisMetrics) -> List[Risk]:
        """Aurora PostgreSQL 전략 위험 요소 생성"""
        risks = [
            Risk(
                category="technical",
                description="PL/SQL을 PL/pgSQL로 변환 시 일부 기능 미지원 (패키지 변수, PRAGMA 등)",
                severity="medium",
                mitigation="미지원 기능 사전 식별 및 대체 방안 수립"
            ),
            Risk(
                category="technical",
                description="외부 프로시저 호출(UTL_*) 미지원으로 애플리케이션 레벨 처리 필요",
                severity="medium",
                mitigation="외부 호출 로직을 애플리케이션 서비스로 이관"
            )
        ]
        
        # BULK 연산 위험
        if metrics.bulk_operation_count >= 10:
            risks.append(Risk(
                category="performance",
                description=f"BULK 연산 {metrics.bulk_operation_count}개 대체 시 성능 차이 발생 (20-50% 느림)",
                severity="medium",
                mitigation="순수 SQL 또는 Chunked Batch 방식 사용, 성능 테스트"
            ))
        
        # PL/SQL 변환 위험
        if metrics.total_plsql_count > 100:
            risks.append(Risk(
                category="operational",
                description=f"PL/SQL 오브젝트가 {metrics.total_plsql_count}개로 많아 변환 작업에 시간이 소요됩니다",
                severity="medium",
                mitigation="자동 변환 도구 활용, 단계적 변환 계획"
            ))
        
        # 복잡도 위험
        if metrics.high_complexity_ratio >= 0.2:
            risks.append(Risk(
                category="technical",
                description=f"복잡도 7.0 이상 오브젝트가 {metrics.high_complexity_ratio*100:.1f}%로 변환 난이도가 높습니다",
                severity="medium",
                mitigation="복잡한 오브젝트 우선 분석, 전문가 리뷰"
            ))
        
        # 최소 3개 보장: 성능 테스트 위험 추가
        if len(risks) < 3:
            risks.append(Risk(
                category="performance",
                description="PostgreSQL 환경에서 성능 테스트 및 검증이 필요합니다",
                severity="medium",
                mitigation="충분한 성능 테스트 기간 확보, 부하 테스트 수행"
            ))
        
        return risks[:5]
