"""
위험 요소 생성기 - 기본 위험

최소 위험 요소 보장을 위한 기본 위험을 제공합니다.
"""

from typing import List
from ...data_models import AnalysisMetrics, MigrationStrategy, Risk
from .base import RiskCandidate


def get_default_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """전략별 기본 위험 요소"""
    if strategy == MigrationStrategy.REPLATFORM:
        return [
            RiskCandidate(
                risk=Risk(
                    category="operational",
                    description="RDS Oracle SE2는 RAC 미지원, Single 인스턴스만 가능",
                    severity="high",
                    mitigation="Multi-AZ 배포로 장애 대응, Read Replica로 읽기 부하 분산"
                ),
                priority_score=3.0
            ),
            RiskCandidate(
                risk=Risk(
                    category="cost",
                    description="Oracle 라이선스 비용 지속 발생",
                    severity="medium",
                    mitigation="장기적으로 Refactoring 전략 재검토"
                ),
                priority_score=2.0
            ),
            RiskCandidate(
                risk=Risk(
                    category="technical",
                    description="Oracle EE 전용 기능 사용 시 SE2 호환성 검토 필요",
                    severity="medium",
                    mitigation="사전에 EE 전용 기능 사용 여부 확인"
                ),
                priority_score=2.0
            ),
        ]
    elif strategy == MigrationStrategy.REFACTOR_MYSQL:
        return [
            RiskCandidate(
                risk=Risk(
                    category="technical",
                    description="PL/SQL 로직을 애플리케이션 코드로 이관 필요",
                    severity="medium",
                    mitigation="단계적 이관 계획 수립, AI 도구 활용"
                ),
                priority_score=2.5
            ),
            RiskCandidate(
                risk=Risk(
                    category="performance",
                    description="복잡한 쿼리 성능 최적화 필요",
                    severity="medium",
                    mitigation="인덱스 전략 수립, 쿼리 튜닝"
                ),
                priority_score=2.0
            ),
            RiskCandidate(
                risk=Risk(
                    category="operational",
                    description="운영팀 MySQL 학습 및 운영 체계 구축 필요",
                    severity="low",
                    mitigation="AWS 교육 프로그램 활용, 운영 가이드 문서화"
                ),
                priority_score=1.0
            ),
        ]
    else:  # PostgreSQL
        return [
            RiskCandidate(
                risk=Risk(
                    category="technical",
                    description="PL/SQL을 PL/pgSQL로 변환 필요 (일부 기능 미지원)",
                    severity="medium",
                    mitigation="AWS SCT 자동 변환 활용, 미지원 기능 사전 식별"
                ),
                priority_score=2.5
            ),
            RiskCandidate(
                risk=Risk(
                    category="performance",
                    description="PostgreSQL 환경에서 성능 테스트 및 검증 필요",
                    severity="medium",
                    mitigation="충분한 성능 테스트 기간 확보, 부하 테스트 수행"
                ),
                priority_score=2.0
            ),
            RiskCandidate(
                risk=Risk(
                    category="operational",
                    description="운영팀 PostgreSQL 학습 및 운영 체계 구축 필요",
                    severity="low",
                    mitigation="AWS 교육 프로그램 활용, 운영 가이드 문서화"
                ),
                priority_score=1.0
            ),
        ]


def ensure_minimum_risks(
    candidates: List[RiskCandidate],
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """최소 3개 위험 요소 보장"""
    if len(candidates) >= 3:
        return candidates
    
    # 기본 위험 요소 추가
    default_risks = get_default_risks(strategy, metrics)
    
    # 중복 제거하며 추가
    existing_descs = {c.risk.description for c in candidates}
    for risk_candidate in default_risks:
        if risk_candidate.risk.description not in existing_descs:
            candidates.append(risk_candidate)
            existing_descs.add(risk_candidate.risk.description)
        if len(candidates) >= 3:
            break
    
    return candidates
