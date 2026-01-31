"""
위험 요소 생성기 - 기술적 위험

기술적 위험 요소를 수집합니다.
"""

from typing import List
from ...data_models import AnalysisMetrics, MigrationStrategy, Risk
from .base import RiskCandidate, calculate_priority


def collect_technical_risks(
    strategy: MigrationStrategy,
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """기술적 위험 수집"""
    candidates = []
    
    if strategy == MigrationStrategy.REPLATFORM:
        candidates.extend(_tech_risks_replatform(metrics))
    elif strategy == MigrationStrategy.REFACTOR_MYSQL:
        candidates.extend(_tech_risks_mysql(metrics))
    else:  # PostgreSQL
        candidates.extend(_tech_risks_postgresql(metrics))
    
    # 공통: Oracle 특화 기능 위험
    candidates.extend(_tech_risks_oracle_features(strategy, metrics))
    
    # 공통: 외부 의존성 위험
    candidates.extend(_tech_risks_external_deps(strategy, metrics))
    
    return candidates


def _tech_risks_replatform(metrics: AnalysisMetrics) -> List[RiskCandidate]:
    """Replatform 기술 위험"""
    risks = []
    
    # EE 기능 사용 위험
    ee_features = _detect_ee_features(metrics)
    if ee_features:
        risks.append(RiskCandidate(
            risk=Risk(
                category="technical",
                description=f"Oracle EE 전용 기능 사용 감지: {', '.join(ee_features[:3])}",
                severity="high",
                mitigation="SE2 호환성 검토 필수. 미지원 기능은 대체 방안 수립 또는 Refactoring 전략 재검토"
            ),
            priority_score=calculate_priority("high", "technical", 1.5)
        ))
    
    return risks


def _tech_risks_mysql(metrics: AnalysisMetrics) -> List[RiskCandidate]:
    """MySQL 기술 위험"""
    risks = []
    
    # PL/SQL → 애플리케이션 이관 필수
    plsql_count = metrics.total_plsql_count or 0
    if plsql_count > 0:
        severity = "high" if plsql_count > 50 else "medium"
        risks.append(RiskCandidate(
            risk=Risk(
                category="technical",
                description=f"PL/SQL {plsql_count}개를 애플리케이션 코드로 전면 이관 필요",
                severity=severity,
                mitigation="단계적 이관 계획 수립, 애플리케이션 개발팀 참여 필수"
            ),
            priority_score=calculate_priority(severity, "technical", 1.3)
        ))
    
    # 저장 프로시저 기능 제한
    pkg_count = metrics.awr_package_count or 0
    if pkg_count > 0:
        risks.append(RiskCandidate(
            risk=Risk(
                category="technical",
                description=f"패키지 {pkg_count}개의 모듈화 구조를 애플리케이션에서 재구현 필요",
                severity="high",
                mitigation="서비스 레이어 설계, 마이크로서비스 패턴 검토"
            ),
            priority_score=calculate_priority("high", "technical", 1.2)
        ))
    
    return risks


def _tech_risks_postgresql(metrics: AnalysisMetrics) -> List[RiskCandidate]:
    """PostgreSQL 기술 위험"""
    risks = []
    
    # PL/SQL → PL/pgSQL 변환
    plsql_count = metrics.total_plsql_count or 0
    if plsql_count > 0:
        severity = "medium" if plsql_count < 100 else "high"
        risks.append(RiskCandidate(
            risk=Risk(
                category="technical",
                description=f"PL/SQL {plsql_count}개를 PL/pgSQL로 변환 필요 (일부 기능 미지원)",
                severity=severity,
                mitigation="AWS SCT 자동 변환 활용, 미지원 기능(패키지 변수, PRAGMA) 사전 식별"
            ),
            priority_score=calculate_priority(severity, "technical", 1.1)
        ))
    
    # 패키지 변환 복잡도
    pkg_count = metrics.awr_package_count or 0
    if pkg_count > 50:
        risks.append(RiskCandidate(
            risk=Risk(
                category="technical",
                description=f"패키지 {pkg_count}개를 스키마+함수 구조로 재설계 필요",
                severity="medium",
                mitigation="패키지별 스키마 분리, 공유 상태는 테이블 또는 애플리케이션으로 이관"
            ),
            priority_score=calculate_priority("medium", "technical", 1.0)
        ))
    
    return risks


def _tech_risks_oracle_features(
    strategy: MigrationStrategy, 
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """Oracle 특화 기능 관련 위험"""
    risks = []
    detected = metrics.detected_oracle_features_summary or {}
    
    # 고위험 기능 목록
    high_risk_features = {
        "OBJECT TYPE": ("사용자 정의 타입", "COMPOSITE TYPE 또는 JSON으로 대체"),
        "NESTED TABLE": ("중첩 테이블", "ARRAY 또는 별도 테이블로 분리"),
        "VARRAY": ("가변 배열", "ARRAY 타입으로 변환"),
        "REF CURSOR": ("참조 커서", "REFCURSOR 또는 SETOF RECORD로 대체"),
        "AUTONOMOUS_TRANSACTION": ("자율 트랜잭션", "별도 DB 연결 또는 dblink 활용"),
        "BULK COLLECT": ("벌크 수집", "배열 처리 또는 COPY 명령 활용"),
        "FORALL": ("벌크 DML", "INSERT...SELECT 또는 배치 처리로 대체"),
    }
    
    for feature, (desc, mitigation) in high_risk_features.items():
        count = detected.get(feature, 0)
        if count > 0:
            # Replatform은 Oracle 유지이므로 위험 없음
            if strategy == MigrationStrategy.REPLATFORM:
                continue
                
            severity = "high" if count >= 10 else "medium"
            risks.append(RiskCandidate(
                risk=Risk(
                    category="technical",
                    description=f"{desc}({feature}) {count}회 사용 - 변환 필요",
                    severity=severity,
                    mitigation=mitigation
                ),
                priority_score=calculate_priority(severity, "technical", count / 10)
            ))
    
    return risks[:3]  # 최대 3개


def _tech_risks_external_deps(
    strategy: MigrationStrategy, 
    metrics: AnalysisMetrics
) -> List[RiskCandidate]:
    """외부 의존성 관련 위험"""
    risks: List[RiskCandidate] = []
    deps = metrics.detected_external_dependencies_summary or {}
    
    # Replatform은 Oracle 유지이므로 위험 없음
    if strategy == MigrationStrategy.REPLATFORM:
        return risks
    
    # 위험 의존성 매핑
    dep_risks = {
        "DBMS_OUTPUT": ("low", "RAISE NOTICE (PostgreSQL) / SELECT (MySQL)"),
        "DBMS_LOB": ("medium", "bytea/text 타입 및 표준 함수 활용"),
        "UTL_FILE": ("high", "애플리케이션 레벨 파일 처리로 이관"),
        "UTL_HTTP": ("high", "애플리케이션 HTTP 클라이언트로 이관"),
        "UTL_SMTP": ("high", "Amazon SES 또는 애플리케이션 메일 서비스"),
        "DBMS_SCHEDULER": ("medium", "EventBridge 또는 Lambda 스케줄러"),
        "DBMS_JOB": ("medium", "EventBridge 또는 pg_cron 활용"),
        "DBMS_CRYPTO": ("medium", "pgcrypto 확장 또는 애플리케이션 암호화"),
        "DBMS_SQL": ("medium", "동적 SQL 재작성 (EXECUTE)"),
        "DBMS_XMLGEN": ("medium", "XML 함수 또는 애플리케이션 처리"),
    }
    
    for dep, (severity, mitigation) in dep_risks.items():
        count = deps.get(dep, 0)
        if count > 0:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="technical",
                    description=f"{dep} {count}회 사용 - 대체 구현 필요",
                    severity=severity,
                    mitigation=mitigation
                ),
                priority_score=calculate_priority(severity, "technical", 1.0)
            ))
    
    return risks[:2]  # 최대 2개


def _detect_ee_features(metrics: AnalysisMetrics) -> List[str]:
    """Oracle Enterprise Edition 전용 기능 감지"""
    ee_features = []
    
    # Oracle 기능 목록에서 EE 전용 기능 확인
    ee_only = {
        "Advanced Compression", "Partitioning", "OLAP", "Data Mining",
        "Label Security", "Database Vault", "Real Application Testing",
        "Active Data Guard", "Advanced Security", "Spatial and Graph"
    }
    
    for feature in metrics.oracle_features_used or []:
        name = feature.get('name', '')
        if any(ee in name for ee in ee_only):
            if feature.get('currently_used', False) or feature.get('detected_usages', 0) > 0:
                ee_features.append(name)
    
    return ee_features
