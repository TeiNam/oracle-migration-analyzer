"""
위험 요소 생성기 - 성능/운영/비용/일정 위험

기술 외 위험 요소를 수집합니다.
"""

from typing import List
from ...data_models import AnalysisMetrics, MigrationStrategy, Risk
from .base import RiskCandidate, calculate_priority


def collect_performance_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """성능 위험 수집"""
    risks = []
    
    # BULK 연산 위험 (Refactoring 전략만)
    if strategy != MigrationStrategy.REPLATFORM:
        bulk_count = metrics.bulk_operation_count or 0
        if bulk_count > 0:
            if strategy == MigrationStrategy.REFACTOR_MYSQL:
                severity = "high" if bulk_count >= 10 else "medium"
                risks.append(RiskCandidate(
                    risk=Risk(
                        category="performance",
                        description=f"BULK 연산 {bulk_count}개를 루프로 변환 시 성능 저하 예상 (30-50%)",
                        severity=severity,
                        mitigation="배치 INSERT 최적화, 트랜잭션 청킹, 필요시 PostgreSQL 재검토"
                    ),
                    priority_score=calculate_priority(severity, "performance", bulk_count / 5)
                ))
            else:  # PostgreSQL
                severity = "medium" if bulk_count >= 10 else "low"
                risks.append(RiskCandidate(
                    risk=Risk(
                        category="performance",
                        description=f"BULK 연산 {bulk_count}개 대체 시 성능 차이 발생 (10-30%)",
                        severity=severity,
                        mitigation="COPY 명령, unnest() 활용, 배치 크기 최적화"
                    ),
                    priority_score=calculate_priority(severity, "performance", bulk_count / 10)
                ))
    
    # 복잡 쿼리 성능 위험
    high_complexity = metrics.high_complexity_sql_count or 0
    if high_complexity > 0 and strategy != MigrationStrategy.REPLATFORM:
        risks.append(RiskCandidate(
            risk=Risk(
                category="performance",
                description=f"고복잡도 SQL {high_complexity}개의 실행 계획 변경으로 성능 차이 발생 가능",
                severity="medium",
                mitigation="마이그레이션 후 실행 계획 비교, 인덱스 전략 재수립"
            ),
            priority_score=calculate_priority("medium", "performance", 1.0)
        ))
    
    # I/O 부하 위험
    avg_io = metrics.avg_io_load or 0
    if avg_io > 5000:  # 높은 I/O
        risks.append(RiskCandidate(
            risk=Risk(
                category="performance",
                description=f"현재 I/O 부하({avg_io:.0f} IOPS)가 높아 스토리지 성능 검증 필요",
                severity="medium",
                mitigation="Aurora I/O 최적화 스토리지 활용, Provisioned IOPS 검토"
            ),
            priority_score=calculate_priority("medium", "performance", 1.0)
        ))
    
    return risks


def collect_operational_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """운영 위험 수집"""
    risks = []
    
    # RAC 관련 위험
    if metrics.rac_detected or metrics.is_rac:
        if strategy == MigrationStrategy.REPLATFORM:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="operational",
                    description="현재 RAC 구성을 RDS Single 인스턴스로 전환 필요",
                    severity="high",
                    mitigation="Multi-AZ로 고가용성 확보, Read Replica로 읽기 분산, 애플리케이션 연결 로직 수정"
                ),
                priority_score=calculate_priority("high", "operational", 1.5)
            ))
        else:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="operational",
                    description="RAC 기반 부하 분산 아키텍처 재설계 필요",
                    severity="high",
                    mitigation="Aurora Read Replica 활용, 애플리케이션 레벨 로드 밸런싱"
                ),
                priority_score=calculate_priority("high", "operational", 1.3)
            ))
    
    # Replatform 특화 위험
    if strategy == MigrationStrategy.REPLATFORM:
        risks.append(RiskCandidate(
            risk=Risk(
                category="operational",
                description="RDS Oracle SE2는 RAC 미지원, Single 인스턴스만 가능",
                severity="high",
                mitigation="Multi-AZ 배포로 장애 대응, Read Replica로 읽기 부하 분산"
            ),
            priority_score=calculate_priority("high", "operational", 1.2)
        ))
    
    # DB Link 위험
    db_links = metrics.count_db_links or 0
    if db_links > 0:
        if strategy == MigrationStrategy.REPLATFORM:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="operational",
                    description=f"DB Link {db_links}개 - RDS에서 제한적 지원",
                    severity="medium",
                    mitigation="VPC 피어링 또는 AWS DMS로 데이터 동기화 검토"
                ),
                priority_score=calculate_priority("medium", "operational", 1.0)
            ))
        else:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="operational",
                    description=f"DB Link {db_links}개를 다른 연결 방식으로 대체 필요",
                    severity="high",
                    mitigation="postgres_fdw(PostgreSQL) 또는 애플리케이션 레벨 연동"
                ),
                priority_score=calculate_priority("high", "operational", 1.2)
            ))
    
    # 운영팀 학습 위험 (Refactoring만)
    if strategy != MigrationStrategy.REPLATFORM:
        target = "PostgreSQL" if strategy == MigrationStrategy.REFACTOR_POSTGRESQL else "MySQL"
        risks.append(RiskCandidate(
            risk=Risk(
                category="operational",
                description=f"운영팀 {target} 학습 및 운영 체계 구축 필요",
                severity="low",
                mitigation="AWS 교육 프로그램 활용, 운영 가이드 문서화, 단계적 인수인계"
            ),
            priority_score=calculate_priority("low", "operational", 0.8)
        ))
    
    return risks


def collect_cost_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """비용 위험 수집"""
    risks = []
    
    if strategy == MigrationStrategy.REPLATFORM:
        # Oracle 라이선스 비용 지속
        risks.append(RiskCandidate(
            risk=Risk(
                category="cost",
                description="Oracle 라이선스 비용 지속 발생 (LI 또는 BYOL)",
                severity="medium",
                mitigation="장기적으로 Refactoring 전략 재검토, 라이선스 최적화"
            ),
            priority_score=calculate_priority("medium", "cost", 1.0)
        ))
        
        # Multi-AZ 라이선스 2배
        risks.append(RiskCandidate(
            risk=Risk(
                category="cost",
                description="Multi-AZ 구성 시 Oracle 라이선스 비용 2배 발생",
                severity="medium",
                mitigation="HA 요구사항 대비 비용 효과 분석, 필요시 Single-AZ + 백업 전략"
            ),
            priority_score=calculate_priority("medium", "cost", 0.9)
        ))
    else:
        # 마이그레이션 인건비
        plsql_count = metrics.total_plsql_count or 0
        if plsql_count > 100:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="cost",
                    description=f"PL/SQL {plsql_count}개 변환에 상당한 개발 인력 투입 필요",
                    severity="medium",
                    mitigation="AI 도구 활용으로 생산성 향상, 외부 전문가 활용 검토"
                ),
                priority_score=calculate_priority("medium", "cost", 0.9)
            ))
    
    # 대용량 DB 스토리지 비용
    db_size = metrics.total_db_size_gb or 0
    if db_size > 1000:  # 1TB 이상
        risks.append(RiskCandidate(
            risk=Risk(
                category="cost",
                description=f"DB 크기({db_size:.0f}GB)가 커서 스토리지 및 전송 비용 고려 필요",
                severity="low",
                mitigation="데이터 아카이빙 검토, S3 티어링 활용"
            ),
            priority_score=calculate_priority("low", "cost", 0.7)
        ))
    
    return risks


def collect_schedule_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """일정 위험 수집"""
    risks = []
    
    # Refactoring 전략의 변환 작업량 위험
    if strategy != MigrationStrategy.REPLATFORM:
        plsql_count = metrics.total_plsql_count or 0
        plsql_lines = metrics.awr_plsql_lines or 0
        
        if plsql_count > 200 or plsql_lines > 100000:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="schedule",
                    description=f"대규모 변환 작업({plsql_count}개, {plsql_lines:,}줄)으로 일정 지연 가능성",
                    severity="high",
                    mitigation="단계적 마이그레이션, 우선순위 기반 변환, 충분한 버퍼 확보"
                ),
                priority_score=calculate_priority("high", "schedule", 1.2)
            ))
        elif plsql_count > 50:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="schedule",
                    description=f"PL/SQL {plsql_count}개 변환 및 테스트에 충분한 기간 필요",
                    severity="medium",
                    mitigation="병렬 작업 계획, AI 도구 활용, 자동화 테스트 구축"
                ),
                priority_score=calculate_priority("medium", "schedule", 1.0)
            ))
    
    # 테스트 기간 위험
    high_complexity_ratio = metrics.high_complexity_ratio or 0
    if high_complexity_ratio > 0.1:  # 10% 이상 고복잡도
        risks.append(RiskCandidate(
            risk=Risk(
                category="schedule",
                description=f"고복잡도 오브젝트 비율({high_complexity_ratio*100:.1f}%)이 높아 테스트 기간 증가 예상",
                severity="medium",
                mitigation="회귀 테스트 자동화, 단계별 검증 계획"
            ),
            priority_score=calculate_priority("medium", "schedule", 0.9)
        ))
    
    return risks
