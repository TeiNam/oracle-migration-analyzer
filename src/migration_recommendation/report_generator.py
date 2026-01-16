"""
추천 리포트 생성기

통합 분석 결과를 기반으로 마이그레이션 추천 리포트를 생성합니다.
"""

from typing import List
from .data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy,
    MigrationRecommendation,
    Rationale,
    AlternativeStrategy,
    Risk,
    MigrationRoadmap,
    RoadmapPhase,
    ExecutiveSummary,
    InstanceRecommendation
)
from .decision_engine import MigrationDecisionEngine


class RecommendationReportGenerator:
    """
    추천 리포트 생성기
    
    통합 분석 결과로부터 마이그레이션 추천 리포트를 생성합니다.
    
    Requirements:
    - 5.1: 추천 근거 생성 (3-5개)
    - 6.1: 대안 전략 생성 (1-2개)
    - 7.1: 위험 요소 생성 (3-5개)
    - 8.1: 마이그레이션 로드맵 생성 (3-5단계)
    - 13.1: Executive Summary 생성
    """
    
    def __init__(self, decision_engine: MigrationDecisionEngine):
        """
        Args:
            decision_engine: 마이그레이션 의사결정 엔진
        """
        self.decision_engine = decision_engine
    
    def generate_recommendation(
        self,
        integrated_result: IntegratedAnalysisResult
    ) -> MigrationRecommendation:
        """
        통합 분석 결과로부터 추천 리포트를 생성합니다.
        
        Args:
            integrated_result: 통합 분석 결과
            
        Returns:
            MigrationRecommendation: 추천 리포트
        """
        metrics = integrated_result.metrics
        
        # 1. 추천 전략 결정
        recommended_strategy = self.decision_engine.decide_strategy(integrated_result)
        
        # 2. 신뢰도 계산
        confidence_level = self._calculate_confidence(metrics, recommended_strategy)
        
        # 3. 추천 근거 생성
        rationales = self._generate_rationales(recommended_strategy, metrics)
        
        # 4. 대안 전략 생성
        alternative_strategies = self._generate_alternatives(recommended_strategy, metrics)
        
        # 5. 위험 요소 생성
        risks = self._generate_risks(recommended_strategy, metrics)
        
        # 6. 마이그레이션 로드맵 생성
        roadmap = self._generate_roadmap(recommended_strategy, metrics)
        
        # 7. 인스턴스 추천 생성
        instance_recommendation = self._generate_instance_recommendation(recommended_strategy, metrics)
        
        # 8. MigrationRecommendation 객체 생성 (Executive Summary 제외)
        recommendation = MigrationRecommendation(
            recommended_strategy=recommended_strategy,
            confidence_level=confidence_level,
            rationales=rationales,
            alternative_strategies=alternative_strategies,
            risks=risks,
            roadmap=roadmap,
            executive_summary=ExecutiveSummary(
                recommended_strategy="",
                estimated_duration="",
                key_benefits=[],
                key_risks=[],
                summary_text=""
            ),  # 임시 값
            instance_recommendation=instance_recommendation,
            metrics=metrics
        )
        
        # 9. Executive Summary 생성 (recommendation 객체 필요)
        executive_summary = self._generate_executive_summary(recommendation)
        recommendation.executive_summary = executive_summary
        
        return recommendation
    
    def _calculate_confidence(
        self,
        metrics: AnalysisMetrics,
        strategy: MigrationStrategy
    ) -> str:
        """
        추천 전략의 신뢰도를 계산합니다.
        
        Args:
            metrics: 분석 메트릭
            strategy: 추천 전략
            
        Returns:
            str: 신뢰도 ("high", "medium", "low")
        """
        # Replatform: 복잡도가 매우 높으면 high
        if strategy == MigrationStrategy.REPLATFORM:
            if metrics.avg_sql_complexity >= 8.0 or metrics.avg_plsql_complexity >= 8.0:
                return "high"
            elif metrics.high_complexity_ratio >= 0.4:
                return "high"
            else:
                return "medium"
        
        # Aurora MySQL: 복잡도가 매우 낮으면 high
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            if metrics.avg_sql_complexity <= 3.0 and metrics.avg_plsql_complexity <= 3.0:
                return "high"
            elif metrics.bulk_operation_count >= 10:
                return "low"  # BULK 연산이 많으면 신뢰도 낮음
            else:
                return "medium"
        
        # Aurora PostgreSQL: 중간 복잡도이면 medium
        else:
            if metrics.bulk_operation_count >= 20:
                return "high"  # BULK 연산이 매우 많으면 PostgreSQL 확실
            else:
                return "medium"
    
    def _generate_rationales(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Rationale]:
        """
        추천 근거 생성 (3-5개)
        
        전략별로 성능/복잡도/비용/운영 카테고리의 근거를 생성합니다.
        
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[Rationale]: 추천 근거 리스트 (3-5개)
        """
        if strategy == MigrationStrategy.REPLATFORM:
            return self._generate_replatform_rationales(metrics)
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            return self._generate_mysql_rationales(metrics)
        else:  # REFACTOR_POSTGRESQL
            return self._generate_postgresql_rationales(metrics)
    
    def _generate_replatform_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Replatform 전략 근거 생성"""
        rationales = []
        
        # PL/SQL 개수 계산 (AWR 우선)
        plsql_count = self._get_plsql_count(metrics)
        
        # PL/SQL 라인 수 계산
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        if plsql_lines == 0:
            plsql_lines = metrics.total_plsql_count * 200
        
        # 1. 비용 효율성 근거 (5만 줄 이상 + 복잡도 중간 이하)
        if plsql_lines >= 50000 and metrics.avg_plsql_complexity < 7.0:
            # Refactor 시간 산정 (AI 도구 활용 기준)
            # 65,000줄 기준 실제 프로젝트 데이터:
            # - 총 소요 시간: 2,000~4,000시간 (평균 3,000시간)
            # - 달력 기간: 3~6개월 (4명 팀 기준)
            # - 시간당 처리: 약 21.7줄/시간 → 약 2.8분/줄
            #
            # 단계별 시간 배분 (AI 활용):
            # 1. 코드 분석: 200~400시간 (1~2주) - AI 자동 분석, 의존성 맵핑
            # 2. 변환 작업: 1,200~2,400시간 (2~3개월) - AI가 80~90% 자동 변환
            # 3. 테스트 및 검증: 400~800시간 (1~1.5개월) - AI 자동 테스트 생성
            # 4. 성능 튜닝: 200~400시간 (2~4주) - 병목 지점만 선별 최적화
            #
            # 참고: AWS Professional Services 마이그레이션 프로젝트 실제 데이터
            minutes_per_line = 2.8  # AI 활용 시 현실적 시간
            refactor_hours_ai = plsql_lines * (minutes_per_line / 60)
            
            # AI 미활용 시 (수동 작업): 약 2배 소요
            # 6~9개월 (평균 7.5개월) 소요
            refactor_hours_traditional = refactor_hours_ai * 2.0
            
            # Replatform: EE 기능만 SE2로 전환 (전체의 약 5-10% 예상)
            # - EE 기능 식별 및 검토: 80시간 (2주)
            # - SE2 호환 기능으로 전환: 80시간 (2주)
            # - 테스트 및 검증: 80시간 (2주)
            # 총: 약 240시간 (6주, 1인 기준)
            replatform_hours = 240
            
            cost_saving_pct = ((refactor_hours_ai - replatform_hours) / refactor_hours_ai) * 100
            
            # 달력 기간 계산 (4명 팀 기준)
            team_size = 4
            refactor_months_ai = (refactor_hours_ai / team_size / 160)  # 월 160시간 기준
            refactor_months_traditional = (refactor_hours_traditional / team_size / 160)
            
            rationales.append(Rationale(
                category="cost",
                reason=f"**PL/SQL 코드 {plsql_lines:,}줄을 Refactor하면 AI 도구 활용 시에도 약 {refactor_hours_ai:,.0f}시간({refactor_months_ai:.1f}개월, 4명 팀 기준) 소요되지만, Replatform은 약 {replatform_hours:,.0f}시간(약 6주)만 소요되어 비용을 약 {cost_saving_pct:.0f}% 절감할 수 있습니다.** EE 기능이 없는 대부분의 코드는 그대로 사용 가능합니다.",
                supporting_data={
                    "plsql_lines": plsql_lines,
                    "refactor_hours_traditional": refactor_hours_traditional,
                    "refactor_hours_ai": refactor_hours_ai,
                    "refactor_months_ai": refactor_months_ai,
                    "refactor_months_traditional": refactor_months_traditional,
                    "team_size": team_size,
                    "ai_time_saving": "50%",
                    "refactor_calculation": f"{minutes_per_line}분/줄 (AI 활용 시), 수동 작업 시 약 2배 소요",
                    "refactor_basis": "AWS Professional Services 마이그레이션 프로젝트 실제 데이터 (65,000줄 기준 3,000시간)",
                    "replatform_hours": replatform_hours,
                    "replatform_calculation": "EE 기능 검토(80h) + 전환(80h) + 테스트(80h) = 240h",
                    "cost_saving_pct": cost_saving_pct,
                    "avg_complexity": metrics.avg_plsql_complexity,
                    "ee_feature_ratio": "5-10%",
                    "reference": "AWS Database Migration Best Practices, AWS Professional Services 실제 프로젝트 사례",
                    "refactor_tasks": [
                        "코드 분석 (200~400h, 1~2주): AI 자동 분석, 의존성 맵핑",
                        "변환 작업 (1,200~2,400h, 2~3개월): AI가 80~90% 자동 변환, 복잡한 로직만 수동 처리",
                        "테스트 및 검증 (400~800h, 1~1.5개월): AI 자동 테스트 생성, 주요 시나리오만 수동 검증",
                        "성능 튜닝 (200~400h, 2~4주): 병목 지점만 선별 최적화"
                    ],
                    "replatform_tasks": [
                        "EE 전용 기능 식별 및 검토 (80h, 2주)",
                        "SE2 호환 기능으로 전환 (80h, 2주)",
                        "테스트 및 검증 (80h, 2주)"
                    ]
                }
            ))
        
        # 2. 코드 복잡도 + 개수 근거
        if metrics.avg_sql_complexity >= 7.0 or metrics.avg_plsql_complexity >= 7.0:
            if plsql_count >= 100:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"평균 코드 복잡도가 SQL {metrics.avg_sql_complexity:.1f}, PL/SQL {metrics.avg_plsql_complexity:.1f}로 매우 높고, PL/SQL 오브젝트가 {plsql_count}개로 많아 변환이 거의 불가능합니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity,
                        "plsql_count": plsql_count
                    }
                ))
            elif plsql_count >= 50:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"평균 코드 복잡도가 SQL {metrics.avg_sql_complexity:.1f}, PL/SQL {metrics.avg_plsql_complexity:.1f}로 매우 높고, PL/SQL 오브젝트가 {plsql_count}개로 변환 위험이 높습니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity,
                        "plsql_count": plsql_count
                    }
                ))
            else:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"평균 코드 복잡도가 SQL {metrics.avg_sql_complexity:.1f}, PL/SQL {metrics.avg_plsql_complexity:.1f}로 매우 높아 대규모 코드 변경이 필요합니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity
                    }
                ))
        
        # 2. 복잡 오브젝트 비율 근거
        if metrics.high_complexity_ratio >= 0.3:
            rationales.append(Rationale(
                category="complexity",
                reason=f"전체 오브젝트의 {metrics.high_complexity_ratio*100:.1f}%가 복잡도 7.0 이상으로 분류되어 코드 변경 위험이 높습니다",
                supporting_data={
                    "high_complexity_count": metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count,
                    "total_count": metrics.total_sql_count + metrics.total_plsql_count,
                    "ratio": metrics.high_complexity_ratio
                }
            ))
        
        # 3. 코드 변경 위험 근거
        rationales.append(Rationale(
            category="operations",
            reason="RDS Oracle SE2로 이관하여 코드 변경을 최소화하고 마이그레이션 위험을 낮출 수 있습니다",
            supporting_data={}
        ))
        
        # 4. 성능 메트릭 근거 (선택적)
        if metrics.avg_cpu_usage > 70:
            rationales.append(Rationale(
                category="performance",
                reason=f"높은 CPU 사용률({metrics.avg_cpu_usage:.1f}%)로 인해 성능 최적화가 필요하며, RDS Oracle SE2로 기존 성능을 유지할 수 있습니다",
                supporting_data={"avg_cpu_usage": metrics.avg_cpu_usage}
            ))
        
        # 5. 빠른 마이그레이션 근거
        if len(rationales) < 5:
            rationales.append(Rationale(
                category="operations",
                reason="약 8-12주 내에 마이그레이션을 완료할 수 있어 빠른 클라우드 전환이 가능합니다",
                supporting_data={}
            ))
        
        return rationales[:5]  # 최대 5개
    
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
    
    def _assess_migration_difficulty(self, metrics: AnalysisMetrics) -> str:
        """
        PL/SQL 라인 수 기반 마이그레이션 난이도 평가
        
        Returns:
            str: 난이도 레벨 (low, medium, high, very_high)
        """
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        
        if plsql_lines == 0:
            plsql_lines = metrics.total_plsql_count * 200
        
        if plsql_lines < 20000:
            return "low"
        elif plsql_lines < 50000:
            return "medium"
        elif plsql_lines < 100000:
            return "high"
        else:
            return "very_high"
    
    def _get_difficulty_text(self, difficulty: str) -> str:
        """난이도 레벨을 한국어 텍스트로 변환"""
        difficulty_map = {
            "low": "낮음 (3~6개월 예상)",
            "medium": "중간 (6~12개월 예상)",
            "high": "높음 (12~18개월 예상)",
            "very_high": "매우 높음 (18개월 이상 예상)"
        }
        return difficulty_map.get(difficulty, "중간")
    
    def _generate_mysql_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Aurora MySQL 전략 근거 생성"""
        rationales = []
        
        # PL/SQL 개수 계산
        plsql_count = self._get_plsql_count(metrics)
        
        # 1. 단순 코드 + 적은 개수 근거 (강력 추천)
        rationales.append(Rationale(
            category="complexity",
            reason=f"평균 SQL 복잡도({metrics.avg_sql_complexity:.1f})와 PL/SQL 복잡도({metrics.avg_plsql_complexity:.1f})가 낮고, PL/SQL 오브젝트가 {plsql_count}개로 적어 애플리케이션 레벨 이관이 매우 용이합니다",
            supporting_data={
                "avg_sql_complexity": metrics.avg_sql_complexity,
                "avg_plsql_complexity": metrics.avg_plsql_complexity,
                "plsql_count": plsql_count
            }
        ))
        
        # 2. 작업 기간 근거
        if plsql_count < 20:
            rationales.append(Rationale(
                category="operations",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 매우 적어 단기간 내 이관이 가능합니다",
                supporting_data={"plsql_count": plsql_count}
            ))
        else:
            rationales.append(Rationale(
                category="operations",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 적어 애플리케이션 레벨로 이관이 가능합니다",
                supporting_data={"plsql_count": plsql_count}
            ))
        
        # 3. 비용 절감 근거
        rationales.append(Rationale(
            category="cost",
            reason="Aurora MySQL은 오픈소스 기반으로 Oracle 라이선스 비용이 없어 TCO를 크게 절감할 수 있습니다",
            supporting_data={}
        ))
        
        # 4. BULK 연산 경고 (10개 이상)
        if metrics.bulk_operation_count >= 10:
            rationales.append(Rationale(
                category="performance",
                reason=f"BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. MySQL은 BULK 연산 미지원으로 성능 저하 가능성이 있으므로 주의가 필요합니다",
                supporting_data={"bulk_operation_count": metrics.bulk_operation_count}
            ))
        
        # 5. 클라우드 네이티브 근거
        if len(rationales) < 5:
            rationales.append(Rationale(
                category="operations",
                reason="Aurora MySQL의 자동 스케일링, 자동 백업 등 클라우드 네이티브 기능을 활용할 수 있습니다",
                supporting_data={}
            ))
        
        return rationales[:5]
    
    def _generate_postgresql_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Aurora PostgreSQL 전략 근거 생성"""
        rationales = []
        
        # PL/SQL 개수 계산
        plsql_count = self._get_plsql_count(metrics)
        
        # 난이도 평가
        difficulty = self._assess_migration_difficulty(metrics)
        difficulty_text = self._get_difficulty_text(difficulty)
        
        # 1. PL/pgSQL 호환성 + 개수/복잡도 + 난이도 근거
        if plsql_count >= 100:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 많지만, 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 PL/pgSQL 변환이 가능합니다. PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버합니다. 마이그레이션 난이도는 {difficulty_text}입니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity,
                    "difficulty": difficulty
                }
            ))
        elif plsql_count >= 50:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개이고 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로, PL/pgSQL로 대부분 변환이 가능합니다. 마이그레이션 난이도는 {difficulty_text}입니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity
                }
            ))
        elif metrics.avg_plsql_complexity >= 7.0:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 적지만 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 높아 신중한 변환이 필요합니다. PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버합니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity
                }
            ))
        else:
            rationales.append(Rationale(
                category="complexity",
                reason="PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버하여 대부분의 로직을 변환할 수 있습니다",
                supporting_data={}
            ))
        
        # 2. BULK 연산 성능 근거
        if metrics.bulk_operation_count >= 10:
            rationales.append(Rationale(
                category="performance",
                reason=f"BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. PostgreSQL은 순수 SQL 또는 Chunked Batch로 대체 가능합니다 (성능 차이 20-50%)",
                supporting_data={"bulk_operation_count": metrics.bulk_operation_count}
            ))
        
        # 3. 복잡도 범위 근거
        if 5.0 <= metrics.avg_sql_complexity < 7.0:
            rationales.append(Rationale(
                category="complexity",
                reason=f"평균 SQL 복잡도({metrics.avg_sql_complexity:.1f})가 중간 수준으로 PostgreSQL 변환이 적합합니다",
                supporting_data={"avg_sql_complexity": metrics.avg_sql_complexity}
            ))
        
        # 4. 비용 절감 근거
        rationales.append(Rationale(
            category="cost",
            reason="Aurora PostgreSQL은 오픈소스 기반으로 Oracle 라이선스 비용이 없어 TCO를 절감할 수 있습니다",
            supporting_data={}
        ))
        
        # 5. PL/SQL 복잡도 근거
        if metrics.avg_plsql_complexity >= 5.0 and len(rationales) < 5:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 PL/pgSQL 변환이 가능합니다",
                supporting_data={"avg_plsql_complexity": metrics.avg_plsql_complexity}
            ))
        
        # 6. 클라우드 네이티브 근거 (최소 3개 보장)
        if len(rationales) < 3:
            rationales.append(Rationale(
                category="operations",
                reason="Aurora PostgreSQL의 자동 스케일링, 자동 백업 등 클라우드 네이티브 기능을 활용할 수 있습니다",
                supporting_data={}
            ))
        
        return rationales[:5]
    
    def _generate_alternatives(
        self,
        recommended_strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[AlternativeStrategy]:
        """
        대안 전략 생성 (1-2개)
        
        추천 전략 외의 차선책을 제시하고 장단점을 비교합니다.
        
        Requirements: 6.1, 6.2, 6.3, 6.4
        
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
    
    def _generate_risks(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Risk]:
        """
        위험 요소 생성 (3-5개)
        
        전략별 위험 요소를 식별하고 완화 방안을 제시합니다.
        
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        
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
    
    def _generate_roadmap(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> MigrationRoadmap:
        """
        마이그레이션 로드맵 생성 (3-5단계)
        
        전략별로 단계별 작업, 예상 기간, 필요 리소스를 포함한 로드맵을 생성합니다.
        
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            MigrationRoadmap: 마이그레이션 로드맵
        """
        if strategy == MigrationStrategy.REPLATFORM:
            return self._generate_replatform_roadmap(metrics)
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            return self._generate_mysql_roadmap(metrics)
        else:  # REFACTOR_POSTGRESQL
            return self._generate_postgresql_roadmap(metrics)
    
    def _generate_replatform_roadmap(self, metrics: AnalysisMetrics) -> MigrationRoadmap:
        """Replatform 전략 로드맵 생성 (AI 도구 활용 기준)"""
        phases = [
            RoadmapPhase(
                phase_number=1,
                phase_name="사전 평가 및 계획",
                tasks=[
                    "AI 도구(Amazon Q Developer)를 활용한 Oracle EE 전용 기능 자동 탐지",
                    "RDS Oracle SE2 제약사항 검토",
                    "인스턴스 사이징 계획 수립",
                    "Multi-AZ 및 Read Replica 아키텍처 설계",
                    "마이그레이션 일정 및 리소스 계획"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "아키텍트", "프로젝트 매니저"]
            ),
            RoadmapPhase(
                phase_number=2,
                phase_name="개발/테스트 환경 구축",
                tasks=[
                    "RDS Oracle SE2 인스턴스 생성",
                    "네트워크 및 보안 그룹 설정",
                    "데이터베이스 스키마 마이그레이션",
                    "애플리케이션 연결 테스트",
                    "AI 기반 성능 벤치마크 및 분석"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "인프라 엔지니어", "개발자"]
            ),
            RoadmapPhase(
                phase_number=3,
                phase_name="데이터 마이그레이션 및 검증",
                tasks=[
                    "AWS DMS를 사용한 초기 데이터 로드",
                    "CDC(Change Data Capture) 설정",
                    "AI 도구를 활용한 데이터 무결성 자동 검증",
                    "애플리케이션 통합 테스트",
                    "성능 테스트 및 튜닝"
                ],
                estimated_duration="2-3주",
                required_resources=["DBA", "개발자", "QA 엔지니어"]
            ),
            RoadmapPhase(
                phase_number=4,
                phase_name="프로덕션 전환",
                tasks=[
                    "프로덕션 RDS 인스턴스 구축",
                    "최종 데이터 동기화",
                    "애플리케이션 전환 (Blue-Green 또는 Canary)",
                    "모니터링 및 알람 설정",
                    "롤백 계획 준비"
                ],
                estimated_duration="1주",
                required_resources=["DBA", "인프라 엔지니어", "개발자", "운영팀"]
            )
        ]
        
        return MigrationRoadmap(
            phases=phases,
            total_estimated_duration="5-8주",
            ai_assisted=True,
            ai_time_saving_pct=40.0,
            ai_cost_saving_pct=35.0
        )
    
    def _generate_mysql_roadmap(self, metrics: AnalysisMetrics) -> MigrationRoadmap:
        """Aurora MySQL 전략 로드맵 생성 (AI 도구 활용 기준)"""
        phases = [
            RoadmapPhase(
                phase_number=1,
                phase_name="사전 평가 및 설계",
                tasks=[
                    "AI 도구(Amazon Q Developer)를 활용한 PL/SQL 로직 자동 분석",
                    "AI 기반 MySQL 호환성 자동 검토 (데이터 타입, 함수)",
                    "애플리케이션 아키텍처 재설계",
                    "Aurora MySQL 인스턴스 사이징",
                    "마이그레이션 일정 및 리소스 계획"
                ],
                estimated_duration="2주",
                required_resources=["DBA", "아키텍트", "개발자", "프로젝트 매니저"]
            ),
            RoadmapPhase(
                phase_number=2,
                phase_name="스키마 및 데이터 변환",
                tasks=[
                    "스키마 변환 (AWS SCT + AI 도구 활용)",
                    "AI 기반 데이터 타입 매핑 자동화",
                    "인덱스 및 제약조건 재설계",
                    "개발/테스트 환경 Aurora MySQL 구축",
                    "초기 데이터 마이그레이션 테스트"
                ],
                estimated_duration="2주",
                required_resources=["DBA", "개발자"]
            ),
            RoadmapPhase(
                phase_number=3,
                phase_name="애플리케이션 코드 변환",
                tasks=[
                    "AI 도구(Amazon Bedrock)를 활용한 PL/SQL → 애플리케이션 코드 변환",
                    "AI 기반 SQL 쿼리 자동 최적화 (MySQL 문법 적용)",
                    "BULK 연산 대체 로직 구현 (AI 제안 활용)",
                    "트랜잭션 처리 로직 재구현",
                    "AI 기반 단위 테스트 자동 생성 및 실행"
                ],
                estimated_duration="3-4주",
                required_resources=["개발자", "DBA", "QA 엔지니어"]
            ),
            RoadmapPhase(
                phase_number=4,
                phase_name="성능 테스트 및 최적화",
                tasks=[
                    "부하 테스트 수행",
                    "AI 기반 쿼리 성능 자동 분석 및 튜닝",
                    "인덱스 최적화",
                    "애플리케이션 성능 프로파일링",
                    "병목 지점 해결"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "개발자", "QA 엔지니어"]
            ),
            RoadmapPhase(
                phase_number=5,
                phase_name="프로덕션 전환",
                tasks=[
                    "프로덕션 Aurora MySQL 클러스터 구축",
                    "최종 데이터 마이그레이션",
                    "애플리케이션 배포 (Blue-Green)",
                    "모니터링 및 알람 설정",
                    "롤백 계획 준비 및 검증"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "인프라 엔지니어", "개발자", "운영팀"]
            )
        ]
        
        return MigrationRoadmap(
            phases=phases,
            total_estimated_duration="9-12주",
            ai_assisted=True,
            ai_time_saving_pct=50.0,
            ai_cost_saving_pct=45.0
        )
    
    def _generate_postgresql_roadmap(self, metrics: AnalysisMetrics) -> MigrationRoadmap:
        """Aurora PostgreSQL 전략 로드맵 생성 (AI 도구 활용 기준)"""
        phases = [
            RoadmapPhase(
                phase_number=1,
                phase_name="사전 평가 및 설계",
                tasks=[
                    "AI 도구(Amazon Q Developer)를 활용한 PL/SQL 호환성 자동 분석",
                    "AI 기반 미지원 기능 자동 식별 및 대체 방안 제시",
                    "PostgreSQL 호환성 검토 (데이터 타입, 함수)",
                    "Aurora PostgreSQL 인스턴스 사이징",
                    "마이그레이션 일정 및 리소스 계획"
                ],
                estimated_duration="2주",
                required_resources=["DBA", "아키텍트", "개발자", "프로젝트 매니저"]
            ),
            RoadmapPhase(
                phase_number=2,
                phase_name="스키마 및 데이터 변환",
                tasks=[
                    "스키마 변환 (AWS SCT + AI 도구 활용)",
                    "AI 기반 데이터 타입 매핑 자동화",
                    "인덱스 및 제약조건 재설계",
                    "개발/테스트 환경 Aurora PostgreSQL 구축",
                    "초기 데이터 마이그레이션 테스트"
                ],
                estimated_duration="2주",
                required_resources=["DBA", "개발자"]
            ),
            RoadmapPhase(
                phase_number=3,
                phase_name="PL/SQL to PL/pgSQL 변환",
                tasks=[
                    "AI 도구(Amazon Q Developer, Bedrock)를 활용한 PL/SQL → PL/pgSQL 자동 변환",
                    "패키지를 스키마로 재구성",
                    "BULK 연산을 순수 SQL 또는 Chunked Batch로 대체 (AI 제안 활용)",
                    "트리거 및 시퀀스 변환",
                    "AI 기반 단위 테스트 자동 생성 및 실행"
                ],
                estimated_duration="3-4주",
                required_resources=["개발자", "DBA", "QA 엔지니어"]
            ),
            RoadmapPhase(
                phase_number=4,
                phase_name="성능 테스트 및 최적화",
                tasks=[
                    "부하 테스트 수행",
                    "AI 기반 쿼리 성능 자동 분석 및 튜닝",
                    "인덱스 최적화",
                    "BULK 연산 대체 로직 성능 검증",
                    "병목 지점 해결"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "개발자", "QA 엔지니어"]
            ),
            RoadmapPhase(
                phase_number=5,
                phase_name="프로덕션 전환",
                tasks=[
                    "프로덕션 Aurora PostgreSQL 클러스터 구축",
                    "최종 데이터 마이그레이션",
                    "애플리케이션 배포 (Blue-Green)",
                    "모니터링 및 알람 설정",
                    "롤백 계획 준비 및 검증"
                ],
                estimated_duration="1-2주",
                required_resources=["DBA", "인프라 엔지니어", "개발자", "운영팀"]
            )
        ]
        
        return MigrationRoadmap(
            phases=phases,
            total_estimated_duration="9-12주",
            ai_assisted=True,
            ai_time_saving_pct=50.0,
            ai_cost_saving_pct=45.0
        )
    
    def _generate_executive_summary(
        self,
        recommendation: MigrationRecommendation
    ) -> ExecutiveSummary:
        """
        Executive Summary 생성 (1페이지 이내)
        
        비기술적 언어로 작성하며, 약 500단어 또는 3000자 이내로 제한합니다.
        
        Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
        
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

    def _generate_instance_recommendation(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> InstanceRecommendation:
        """
        인스턴스 추천 생성
        
        Requirements 11.4, 11.5, 11.6을 구현합니다.
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            InstanceRecommendation: 인스턴스 추천
        """
        # CPU 및 I/O 기반 인스턴스 사이징
        cpu_usage = metrics.avg_cpu_usage
        io_load = metrics.avg_io_load
        memory_usage = metrics.avg_memory_usage
        
        # 성능 여유율 계산 (P99 기준 +20%)
        # AWR/Statspack 데이터는 평균값이므로, 피크 부하를 고려하여 20% 여유율 적용
        performance_buffer = 1.2
        estimated_peak_cpu = cpu_usage * performance_buffer
        estimated_peak_io = io_load * performance_buffer
        estimated_peak_memory = memory_usage * performance_buffer
        
        # 인스턴스 타입 결정 (CPU, I/O, 메모리 모두 고려)
        # 메모리가 가장 중요한 제약 조건이므로 먼저 확인
        if strategy == MigrationStrategy.REPLATFORM:
            # RDS for Oracle SE2
            # 메모리 기준으로 최소 인스턴스 결정
            if estimated_peak_memory > 32:
                # 64GB 이상 필요
                instance_type = "db.r6i.2xlarge"
                vcpu = 8
                memory_gb = 64
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)가 32GB를 초과하므로 "
                    f"**db.r6i.2xlarge** (vCPU 8, 메모리 64GB)를 추천합니다. "
                    f"이 인스턴스는 메모리 부족 없이 안정적인 성능을 제공합니다."
                )
            elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
                # 32GB 필요
                instance_type = "db.r6i.xlarge"
                vcpu = 4
                memory_gb = 32
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)를 고려하여 "
                    f"**db.r6i.xlarge** (vCPU 4, 메모리 32GB)를 추천합니다. "
                    f"이 인스턴스는 현재 워크로드에 적합하며, 피크 시에도 충분한 여유가 있습니다."
                )
            else:
                # 16GB 충분
                instance_type = "db.r6i.large"
                vcpu = 2
                memory_gb = 16
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 현재 워크로드가 낮은 수준이므로 "
                    f"**db.r6i.large** (vCPU 2, 메모리 16GB)를 추천합니다. "
                    f"이 인스턴스는 비용 효율적이며, 필요시 상위 인스턴스로 업그레이드 가능합니다."
                )
        
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            # Aurora MySQL
            if estimated_peak_memory > 32:
                instance_type = "db.r6i.2xlarge"
                vcpu = 8
                memory_gb = 64
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)가 32GB를 초과하므로 "
                    f"**db.r6i.2xlarge** (vCPU 8, 메모리 64GB)를 추천합니다. "
                    f"Aurora MySQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
                )
            elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
                instance_type = "db.r6i.xlarge"
                vcpu = 4
                memory_gb = 32
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)를 고려하여 "
                    f"**db.r6i.xlarge** (vCPU 4, 메모리 32GB)를 추천합니다. "
                    f"Aurora MySQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
                )
            else:
                instance_type = "db.r6i.large"
                vcpu = 2
                memory_gb = 16
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 현재 워크로드가 낮은 수준이므로 "
                    f"**db.r6i.large** (vCPU 2, 메모리 16GB)를 추천합니다. "
                    f"Aurora MySQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
                )
        
        else:  # REFACTOR_POSTGRESQL
            # Aurora PostgreSQL
            if estimated_peak_memory > 32:
                instance_type = "db.r6i.2xlarge"
                vcpu = 8
                memory_gb = 64
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)가 32GB를 초과하므로 "
                    f"**db.r6i.2xlarge** (vCPU 8, 메모리 64GB)를 추천합니다. "
                    f"Aurora PostgreSQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
                )
            elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
                instance_type = "db.r6i.xlarge"
                vcpu = 4
                memory_gb = 32
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)를 고려하여 "
                    f"**db.r6i.xlarge** (vCPU 4, 메모리 32GB)를 추천합니다. "
                    f"Aurora PostgreSQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
                )
            else:
                instance_type = "db.r6i.large"
                vcpu = 2
                memory_gb = 16
                rationale = (
                    f"**AWR/Statspack 분석 결과**:\n"
                    f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
                    f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
                    f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
                    f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
                    f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
                    f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
                    f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
                    f"**추천 근거**: 현재 워크로드가 낮은 수준이므로 "
                    f"**db.r6i.large** (vCPU 2, 메모리 16GB)를 추천합니다. "
                    f"Aurora PostgreSQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
                )
        
        return InstanceRecommendation(
            instance_type=instance_type,
            vcpu=vcpu,
            memory_gb=memory_gb,
            rationale=rationale
        )
