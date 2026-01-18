"""
대안 전략 생성기

추천 전략 외의 대안을 생성합니다.
"""

import logging
from typing import List
from ..data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    AlternativeStrategy
)

# 로거 초기화
logger = logging.getLogger(__name__)


class AlternativeGenerator:
    """
    대안 전략 생성기
    
    추천 전략 외의 차선책을 제시하고 장단점을 비교합니다.
    
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
            # Replatform 추천 시 대안: Aurora PostgreSQL
            alternatives.append(AlternativeStrategy(
                strategy=MigrationStrategy.REFACTOR_POSTGRESQL,
                pros=[
                    "Oracle 라이선스 비용 절감",
                    "PL/pgSQL로 대부분의 PL/SQL 로직 변환 가능",
                    "클라우드 네이티브 기능 활용"
                ],
                cons=[
                    "PL/SQL 변환 작업 필요 (6-8주 추가)",
                    "일부 Oracle 기능 미지원",
                    "성능 테스트 및 검증 필요"
                ],
                considerations=[
                    "장기적으로 비용 절감 효과가 크지만 초기 투자 필요",
                    "복잡한 PL/SQL 변환 시 위험도 증가",
                    "충분한 테스트 기간 확보 필요"
                ]
            ))
            
            # 복잡도가 경계선에 있으면 Aurora MySQL도 고려
            if metrics.high_complexity_ratio < 0.35 and metrics.avg_sql_complexity < 7.5:
                alternatives.append(AlternativeStrategy(
                    strategy=MigrationStrategy.REFACTOR_MYSQL,
                    pros=[
                        "가장 낮은 TCO (라이선스 비용 없음)",
                        "Aurora MySQL의 높은 성능",
                        "간단한 아키텍처"
                    ],
                    cons=[
                        "모든 PL/SQL을 애플리케이션으로 이관 필요",
                        "MySQL Stored Procedure 사용 불가",
                        "대규모 코드 변경 필요"
                    ],
                    considerations=[
                        "PL/SQL 로직이 단순한 경우에만 고려",
                        "애플리케이션 레벨 개발 리소스 충분히 확보",
                        "BULK 연산 대체 방안 필수"
                    ]
                ))
        
        elif recommended_strategy == MigrationStrategy.REFACTOR_MYSQL:
            # Aurora MySQL 추천 시 대안: Aurora PostgreSQL
            alternatives.append(AlternativeStrategy(
                strategy=MigrationStrategy.REFACTOR_POSTGRESQL,
                pros=[
                    "PL/pgSQL로 PL/SQL 로직 유지 가능",
                    "BULK 연산 대체 성능 우수",
                    "복잡한 쿼리 성능 우수"
                ],
                cons=[
                    "PL/SQL 변환 작업 필요",
                    "MySQL 대비 약간 높은 비용",
                    "학습 곡선 존재"
                ],
                considerations=[
                    "PL/SQL 로직을 데이터베이스에 유지하고 싶은 경우",
                    "BULK 연산이 많은 경우 (10개 이상)",
                    "복잡한 JOIN 쿼리가 많은 경우"
                ]
            ))
            
            # 복잡도가 매우 낮으면 Replatform도 고려 (빠른 마이그레이션)
            if metrics.avg_sql_complexity < 3.0 and metrics.avg_plsql_complexity < 3.0:
                alternatives.append(AlternativeStrategy(
                    strategy=MigrationStrategy.REPLATFORM,
                    pros=[
                        "가장 빠른 마이그레이션 (8-12주)",
                        "코드 변경 최소화",
                        "기존 기능 및 성능 유지"
                    ],
                    cons=[
                        "Oracle 라이선스 비용 지속 발생",
                        "Single 인스턴스 제약",
                        "장기적으로 클라우드 이점 제한적"
                    ],
                    considerations=[
                        "빠른 클라우드 전환이 최우선인 경우",
                        "장기적으로 Refactoring 재검토 계획",
                        "비용보다 안정성이 중요한 경우"
                    ]
                ))
        
        else:  # REFACTOR_POSTGRESQL
            # Aurora PostgreSQL 추천 시 대안 1: Aurora MySQL
            if metrics.avg_plsql_complexity < 5.0 and metrics.total_plsql_count < 50:
                alternatives.append(AlternativeStrategy(
                    strategy=MigrationStrategy.REFACTOR_MYSQL,
                    pros=[
                        "가장 낮은 TCO",
                        "간단한 아키텍처",
                        "Aurora MySQL의 높은 성능"
                    ],
                    cons=[
                        "모든 PL/SQL을 애플리케이션으로 이관 필요",
                        "BULK 연산 성능 저하 가능성",
                        "복잡한 JOIN 쿼리 성능 최적화 필요"
                    ],
                    considerations=[
                        "PL/SQL 로직이 단순하고 적은 경우",
                        "애플리케이션 레벨 개발 가능한 경우",
                        "비용 절감이 최우선인 경우"
                    ]
                ))
            
            # 대안 2: Replatform (복잡도가 높은 경우)
            if metrics.high_complexity_ratio >= 0.25:
                alternatives.append(AlternativeStrategy(
                    strategy=MigrationStrategy.REPLATFORM,
                    pros=[
                        "코드 변경 최소화",
                        "빠른 마이그레이션",
                        "기존 기능 및 성능 유지"
                    ],
                    cons=[
                        "Oracle 라이선스 비용 지속 발생",
                        "Single 인스턴스 제약",
                        "클라우드 네이티브 이점 제한적"
                    ],
                    considerations=[
                        "PL/SQL 변환 위험이 높은 경우",
                        "빠른 클라우드 전환이 필요한 경우",
                        "장기적으로 Refactoring 재검토"
                    ]
                ))
            
            # 최소 1개 보장: 조건에 맞지 않아도 기본 대안 제공
            if len(alternatives) == 0:
                alternatives.append(AlternativeStrategy(
                    strategy=MigrationStrategy.REFACTOR_MYSQL,
                    pros=[
                        "가장 낮은 TCO",
                        "간단한 아키텍처",
                        "Aurora MySQL의 높은 성능"
                    ],
                    cons=[
                        "모든 PL/SQL을 애플리케이션으로 이관 필요",
                        "BULK 연산 성능 저하 가능성",
                        "복잡한 JOIN 쿼리 성능 최적화 필요"
                    ],
                    considerations=[
                        "PL/SQL 로직을 애플리케이션으로 이관 가능한 경우",
                        "비용 절감이 최우선인 경우",
                        "단순한 데이터베이스 로직을 선호하는 경우"
                    ]
                ))
        
        return alternatives[:2]  # 최대 2개
