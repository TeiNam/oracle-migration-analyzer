"""
위험 요소 생성기

마이그레이션 전략별 위험 요소를 분석 데이터 기반으로 동적 생성합니다.
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from ..data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    Risk
)

logger = logging.getLogger(__name__)


@dataclass
class RiskCandidate:
    """위험 후보 (우선순위 정렬용)"""
    risk: Risk
    priority_score: float  # 높을수록 중요


class RiskGenerator:
    """
    위험 요소 생성기
    
    분석 데이터 기반으로 전략별 위험 요소를 동적 생성합니다.
    """
    
    # 심각도별 기본 점수
    SEVERITY_SCORES = {"high": 3.0, "medium": 2.0, "low": 1.0}
    
    # 카테고리별 기본 점수 (중요도)
    CATEGORY_SCORES = {
        "technical": 1.2,
        "performance": 1.1,
        "operational": 1.0,
        "cost": 0.9,
        "schedule": 0.8
    }

    def generate_risks(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Risk]:
        """
        위험 요소 생성 (3-5개, 우선순위 기반)
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[Risk]: 위험 요소 리스트 (3-5개)
        """
        candidates: List[RiskCandidate] = []
        
        # 1. 기술적 위험 수집
        candidates.extend(self._collect_technical_risks(strategy, metrics))
        
        # 2. 성능 위험 수집
        candidates.extend(self._collect_performance_risks(strategy, metrics))
        
        # 3. 운영 위험 수집
        candidates.extend(self._collect_operational_risks(strategy, metrics))
        
        # 4. 비용 위험 수집
        candidates.extend(self._collect_cost_risks(strategy, metrics))
        
        # 5. 일정 위험 수집
        candidates.extend(self._collect_schedule_risks(strategy, metrics))
        
        # 6. 최소 3개 보장
        candidates = self._ensure_minimum_risks(candidates, strategy, metrics)
        
        # 우선순위 정렬 후 상위 5개 반환
        candidates.sort(key=lambda x: x.priority_score, reverse=True)
        return [c.risk for c in candidates[:5]]
    
    def _calculate_priority(
        self, 
        severity: str, 
        category: str, 
        data_weight: float = 1.0
    ) -> float:
        """우선순위 점수 계산"""
        base = self.SEVERITY_SCORES.get(severity, 1.0)
        cat_mult = self.CATEGORY_SCORES.get(category, 1.0)
        return base * cat_mult * data_weight

    # =========================================================================
    # 기술적 위험 (Technical Risks)
    # =========================================================================
    
    def _collect_technical_risks(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[RiskCandidate]:
        """기술적 위험 수집"""
        candidates = []
        
        if strategy == MigrationStrategy.REPLATFORM:
            candidates.extend(self._tech_risks_replatform(metrics))
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            candidates.extend(self._tech_risks_mysql(metrics))
        else:  # PostgreSQL
            candidates.extend(self._tech_risks_postgresql(metrics))
        
        # 공통: Oracle 특화 기능 위험
        candidates.extend(self._tech_risks_oracle_features(strategy, metrics))
        
        # 공통: 외부 의존성 위험
        candidates.extend(self._tech_risks_external_deps(strategy, metrics))
        
        return candidates
    
    def _tech_risks_replatform(self, metrics: AnalysisMetrics) -> List[RiskCandidate]:
        """Replatform 기술 위험"""
        risks = []
        
        # EE 기능 사용 위험
        ee_features = self._detect_ee_features(metrics)
        if ee_features:
            risks.append(RiskCandidate(
                risk=Risk(
                    category="technical",
                    description=f"Oracle EE 전용 기능 사용 감지: {', '.join(ee_features[:3])}",
                    severity="high",
                    mitigation="SE2 호환성 검토 필수. 미지원 기능은 대체 방안 수립 또는 Refactoring 전략 재검토"
                ),
                priority_score=self._calculate_priority("high", "technical", 1.5)
            ))
        
        return risks

    def _tech_risks_mysql(self, metrics: AnalysisMetrics) -> List[RiskCandidate]:
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
                priority_score=self._calculate_priority(severity, "technical", 1.3)
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
                priority_score=self._calculate_priority("high", "technical", 1.2)
            ))
        
        return risks
    
    def _tech_risks_postgresql(self, metrics: AnalysisMetrics) -> List[RiskCandidate]:
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
                priority_score=self._calculate_priority(severity, "technical", 1.1)
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
                priority_score=self._calculate_priority("medium", "technical", 1.0)
            ))
        
        return risks

    def _tech_risks_oracle_features(
        self, 
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
                    priority_score=self._calculate_priority(severity, "technical", count / 10)
                ))
        
        return risks[:3]  # 최대 3개
    
    def _tech_risks_external_deps(
        self, 
        strategy: MigrationStrategy, 
        metrics: AnalysisMetrics
    ) -> List[RiskCandidate]:
        """외부 의존성 관련 위험"""
        risks = []
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
                    priority_score=self._calculate_priority(severity, "technical", 1.0)
                ))
        
        return risks[:2]  # 최대 2개

    # =========================================================================
    # 성능 위험 (Performance Risks)
    # =========================================================================
    
    def _collect_performance_risks(
        self,
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
                        priority_score=self._calculate_priority(severity, "performance", bulk_count / 5)
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
                        priority_score=self._calculate_priority(severity, "performance", bulk_count / 10)
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
                priority_score=self._calculate_priority("medium", "performance", 1.0)
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
                priority_score=self._calculate_priority("medium", "performance", 1.0)
            ))
        
        return risks

    # =========================================================================
    # 운영 위험 (Operational Risks)
    # =========================================================================
    
    def _collect_operational_risks(
        self,
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
                    priority_score=self._calculate_priority("high", "operational", 1.5)
                ))
            else:
                risks.append(RiskCandidate(
                    risk=Risk(
                        category="operational",
                        description="RAC 기반 부하 분산 아키텍처 재설계 필요",
                        severity="high",
                        mitigation="Aurora Read Replica 활용, 애플리케이션 레벨 로드 밸런싱"
                    ),
                    priority_score=self._calculate_priority("high", "operational", 1.3)
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
                priority_score=self._calculate_priority("high", "operational", 1.2)
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
                    priority_score=self._calculate_priority("medium", "operational", 1.0)
                ))
            else:
                risks.append(RiskCandidate(
                    risk=Risk(
                        category="operational",
                        description=f"DB Link {db_links}개를 다른 연결 방식으로 대체 필요",
                        severity="high",
                        mitigation="postgres_fdw(PostgreSQL) 또는 애플리케이션 레벨 연동"
                    ),
                    priority_score=self._calculate_priority("high", "operational", 1.2)
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
                priority_score=self._calculate_priority("low", "operational", 0.8)
            ))
        
        return risks

    # =========================================================================
    # 비용 위험 (Cost Risks)
    # =========================================================================
    
    def _collect_cost_risks(
        self,
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
                priority_score=self._calculate_priority("medium", "cost", 1.0)
            ))
            
            # Multi-AZ 라이선스 2배
            risks.append(RiskCandidate(
                risk=Risk(
                    category="cost",
                    description="Multi-AZ 구성 시 Oracle 라이선스 비용 2배 발생",
                    severity="medium",
                    mitigation="HA 요구사항 대비 비용 효과 분석, 필요시 Single-AZ + 백업 전략"
                ),
                priority_score=self._calculate_priority("medium", "cost", 0.9)
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
                    priority_score=self._calculate_priority("medium", "cost", 0.9)
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
                priority_score=self._calculate_priority("low", "cost", 0.7)
            ))
        
        return risks

    # =========================================================================
    # 일정 위험 (Schedule Risks)
    # =========================================================================
    
    def _collect_schedule_risks(
        self,
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
                    priority_score=self._calculate_priority("high", "schedule", 1.2)
                ))
            elif plsql_count > 50:
                risks.append(RiskCandidate(
                    risk=Risk(
                        category="schedule",
                        description=f"PL/SQL {plsql_count}개 변환 및 테스트에 충분한 기간 필요",
                        severity="medium",
                        mitigation="병렬 작업 계획, AI 도구 활용, 자동화 테스트 구축"
                    ),
                    priority_score=self._calculate_priority("medium", "schedule", 1.0)
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
                priority_score=self._calculate_priority("medium", "schedule", 0.9)
            ))
        
        return risks
    
    # =========================================================================
    # 헬퍼 메서드
    # =========================================================================
    
    def _detect_ee_features(self, metrics: AnalysisMetrics) -> List[str]:
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

    def _ensure_minimum_risks(
        self,
        candidates: List[RiskCandidate],
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[RiskCandidate]:
        """최소 3개 위험 요소 보장"""
        if len(candidates) >= 3:
            return candidates
        
        # 기본 위험 요소 추가
        default_risks = self._get_default_risks(strategy, metrics)
        
        # 중복 제거하며 추가
        existing_descs = {c.risk.description for c in candidates}
        for risk_candidate in default_risks:
            if risk_candidate.risk.description not in existing_descs:
                candidates.append(risk_candidate)
                existing_descs.add(risk_candidate.risk.description)
            if len(candidates) >= 3:
                break
        
        return candidates
    
    def _get_default_risks(
        self,
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
