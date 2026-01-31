"""
대안 전략 생성기

추천 전략 외의 대안을 생성합니다.
"""

import logging
from typing import List
from ..data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    ReplatformSubStrategy,
    AlternativeStrategy
)

# 로거 초기화
logger = logging.getLogger(__name__)


class AlternativeGenerator:
    """
    대안 전략 생성기
    
    추천 전략 외의 차선책을 제시하고 장단점을 비교합니다.
    
    대안 전략 규칙:
    - Refactoring(PostgreSQL/MySQL) 추천 시: 1안은 Replatform (AWS 안정적 안착 우선)
    - Replatform 추천 시: 1안은 타 오픈소스 DB (MySQL→PostgreSQL, PostgreSQL→MySQL)
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    
    def generate_alternatives(
        self,
        recommended_strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[AlternativeStrategy]:
        """
        대안 전략 생성 (1-2개)
        
        Args:
            recommended_strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[AlternativeStrategy]: 대안 전략 리스트 (1-2개)
        """
        alternatives = []
        
        if recommended_strategy == MigrationStrategy.REPLATFORM:
            # Replatform 추천 시: 세부 옵션 설명 + 오픈소스 대안
            # 1안: PostgreSQL (Oracle 호환성 높음)
            alternatives.append(self._create_postgresql_alternative_from_replatform())
            
            # 2안: MySQL (비용 최적화 관점)
            alternatives.append(self._create_mysql_alternative_from_replatform())
        
        elif recommended_strategy == MigrationStrategy.REFACTOR_MYSQL:
            # MySQL 추천 시: 1안은 Replatform (AWS 안정적 안착 우선)
            alternatives.append(self._create_replatform_alternative())
            
            # 2안: PostgreSQL (플랫폼 통일 관점)
            alternatives.append(self._create_postgresql_alternative_from_mysql())
        
        else:  # REFACTOR_POSTGRESQL
            # PostgreSQL 추천 시: 1안은 Replatform (AWS 안정적 안착 우선)
            alternatives.append(self._create_replatform_alternative())
            
            # 2안: MySQL (운영 단순화 관점)
            alternatives.append(self._create_mysql_alternative_from_postgresql(metrics))
        
        return alternatives[:2]  # 최대 2개
    
    def _create_replatform_alternative(self) -> AlternativeStrategy:
        """Replatform 대안 생성 (Refactoring 추천 시 1안)"""
        return AlternativeStrategy(
            strategy=MigrationStrategy.REPLATFORM,
            pros=[
                "AWS 클라우드로 가장 빠르고 안정적인 전환 (4-6주)",
                "기존 PL/SQL 코드 100% 유지, 코드 변경 없음",
                "Oracle 기능 및 성능 그대로 유지",
                "마이그레이션 위험 최소화",
                "운영팀 재교육 불필요"
            ],
            cons=[
                "Oracle 라이선스 비용 지속 발생 (BYOL 또는 LI)",
                "Multi-AZ 구성 시 라이선스 비용 2배",
                "Oracle 21c EE는 BYOL 라이선스 필수",
                "장기적으로 클라우드 네이티브 이점 제한적"
            ],
            considerations=[
                "✅ 빠른 클라우드 전환이 최우선인 경우 적합",
                "✅ 마이그레이션 리스크를 최소화하고 싶은 경우",
                "✅ 향후 2단계로 오픈소스 전환을 계획하는 경우",
                "⚠️ 장기 비용 절감보다 안정성이 중요한 경우에만 선택"
            ]
        )
    
    def _create_postgresql_alternative_from_replatform(self) -> AlternativeStrategy:
        """PostgreSQL 대안 생성 (Replatform 추천 시 1안)"""
        return AlternativeStrategy(
            strategy=MigrationStrategy.REFACTOR_POSTGRESQL,
            pros=[
                "Oracle 라이선스 비용 완전 제거 (TCO 40-60% 절감)",
                "PL/pgSQL로 대부분의 PL/SQL 로직 변환 가능",
                "Oracle과 가장 유사한 문법 및 기능",
                "Aurora PostgreSQL의 고가용성 (Multi-AZ, Read Replica)",
                "클라우드 네이티브 기능 활용 (Auto Scaling, Serverless)"
            ],
            cons=[
                "PL/SQL → PL/pgSQL 변환 작업 필요 (6-12주 추가)",
                "일부 Oracle 기능 미지원 (패키지 변수, PRAGMA 등)",
                "성능 테스트 및 튜닝 필요",
                "운영팀 PostgreSQL 학습 필요"
            ],
            considerations=[
                "✅ 장기적 비용 절감이 중요한 경우",
                "✅ PL/SQL 로직을 DB 레벨에서 유지하고 싶은 경우",
                "✅ 복잡한 쿼리와 트랜잭션이 많은 경우",
                "⚠️ 충분한 변환 및 테스트 기간 확보 필요"
            ]
        )
    
    def _create_mysql_alternative_from_replatform(self) -> AlternativeStrategy:
        """MySQL 대안 생성 (Replatform 추천 시 2안)"""
        return AlternativeStrategy(
            strategy=MigrationStrategy.REFACTOR_MYSQL,
            pros=[
                "가장 낮은 TCO (라이선스 비용 없음)",
                "Aurora MySQL의 뛰어난 성능 및 확장성",
                "단순한 아키텍처로 운영 용이",
                "광범위한 에코시스템 및 커뮤니티 지원"
            ],
            cons=[
                "모든 PL/SQL을 애플리케이션 코드로 이관 필요",
                "저장 프로시저 기능 제한적",
                "복잡한 쿼리 성능 최적화 필요",
                "대규모 애플리케이션 코드 변경 필요"
            ],
            considerations=[
                "✅ PL/SQL 로직이 단순하고 적은 경우",
                "✅ 애플리케이션 레벨 개발 리소스가 충분한 경우",
                "✅ 비용 절감이 최우선인 경우",
                "⚠️ BULK 연산이 많은 경우 성능 검증 필수"
            ]
        )
    
    def _create_postgresql_alternative_from_mysql(self) -> AlternativeStrategy:
        """PostgreSQL 대안 생성 (MySQL 추천 시 2안)"""
        return AlternativeStrategy(
            strategy=MigrationStrategy.REFACTOR_POSTGRESQL,
            pros=[
                "PL/pgSQL로 PL/SQL 로직 DB 레벨 유지 가능",
                "기존 Aurora MySQL과 동일 플랫폼 (Aurora) 사용으로 관리 포인트 통일",
                "복잡한 쿼리 및 BULK 연산 성능 우수",
                "Oracle과 높은 호환성으로 변환 용이"
            ],
            cons=[
                "MySQL 대비 약간 높은 비용",
                "PL/SQL 변환 작업 필요",
                "PostgreSQL 학습 곡선 존재"
            ],
            considerations=[
                "✅ 이미 Aurora를 사용 중이라면 플랫폼 통일 가능",
                "✅ PL/SQL 로직을 데이터베이스에 유지하고 싶은 경우",
                "✅ BULK 연산이 많은 경우 (10개 이상)",
                "⚠️ MySQL 대비 변환 공수는 비슷하나 DB 로직 유지 가능"
            ]
        )
    
    def _create_mysql_alternative_from_postgresql(
        self, 
        metrics: AnalysisMetrics
    ) -> AlternativeStrategy:
        """MySQL 대안 생성 (PostgreSQL 추천 시 2안)"""
        # 복잡도에 따른 고려사항 조정
        complexity_note = ""
        if metrics.avg_plsql_complexity and metrics.avg_plsql_complexity >= 5.0:
            complexity_note = "⚠️ 현재 PL/SQL 복잡도가 높아 애플리케이션 이관 공수 증가 예상"
        else:
            complexity_note = "✅ PL/SQL 복잡도가 낮아 애플리케이션 이관 상대적으로 용이"
        
        return AlternativeStrategy(
            strategy=MigrationStrategy.REFACTOR_MYSQL,
            pros=[
                "가장 낮은 TCO (라이선스 비용 없음)",
                "단순한 아키텍처로 운영 및 관리 용이",
                "Aurora MySQL의 뛰어난 성능",
                "DBA 인력 수급 용이 (MySQL 경험자 다수)",
                "광범위한 모니터링 및 관리 도구 지원"
            ],
            cons=[
                "모든 PL/SQL을 애플리케이션 코드로 이관 필요",
                "PostgreSQL 대비 변환 난이도 높음 (애플리케이션 변경 필수)",
                "저장 프로시저 기능 제한적",
                "BULK 연산 대체 시 성능 저하 가능성 (20-50%)"
            ],
            considerations=[
                complexity_note,
                "✅ 운영 단순화가 중요한 경우 (MySQL이 관리 용이)",
                "✅ 애플리케이션 현대화를 함께 진행하는 경우",
                "⚠️ 변환 공수가 PostgreSQL 대비 1.5-2배 소요 예상",
                "⚠️ 애플리케이션 개발팀의 적극적 참여 필수"
            ]
        )
