"""
Executive Summary 생성기

마이그레이션 추천의 Executive Summary를 생성합니다.
"""

import logging
from typing import List, Optional
from ...data_models import (
    AnalysisMetrics,
    MigrationStrategy,
    MigrationRecommendation,
    ExecutiveSummary,
    ReplatformSubStrategy
)
from .replatform import ReplatformSummaryGenerator
from .mysql import MySQLSummaryGenerator
from .postgresql import PostgreSQLSummaryGenerator

# 로거 초기화
logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Executive Summary 생성기
    
    비기술적 언어로 작성하며, 약 500단어 또는 3000자 이내로 제한합니다.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
    """
    
    def __init__(self) -> None:
        """SummaryGenerator 초기화"""
        self._replatform_generator = ReplatformSummaryGenerator()
        self._mysql_generator = MySQLSummaryGenerator()
        self._postgresql_generator = PostgreSQLSummaryGenerator()
    
    def generate_executive_summary(
        self,
        recommendation: MigrationRecommendation
    ) -> ExecutiveSummary:
        """
        Executive Summary 생성 (1페이지 이내)
        
        Args:
            recommendation: 마이그레이션 추천 결과
            
        Returns:
            ExecutiveSummary: Executive Summary
        """
        strategy = recommendation.recommended_strategy
        metrics = recommendation.metrics
        
        # metrics가 None인 경우 기본값 생성
        if metrics is None:
            metrics = AnalysisMetrics(
                avg_cpu_usage=0.0,
                avg_io_load=0.0,
                avg_memory_usage=0.0,
                avg_sql_complexity=0.0,
                avg_plsql_complexity=0.0,
                high_complexity_sql_count=0,
                high_complexity_plsql_count=0,
                total_sql_count=0,
                total_plsql_count=0,
                high_complexity_ratio=0.0,
                bulk_operation_count=0,
                rac_detected=False
            )
        
        # 전략별 요약 텍스트 생성
        if strategy == MigrationStrategy.REPLATFORM:
            sub_strategy = recommendation.replatform_sub_strategy
            sub_strategy_reasons = recommendation.replatform_sub_strategy_reasons
            
            # 서브 전략 값 추출
            sub_strategy_value = sub_strategy.value if sub_strategy else "rds_oracle"
            summary_text = self._replatform_generator.generate(
                metrics, sub_strategy_value, sub_strategy_reasons or []
            )
            
            # 서브 전략별 이점 및 위험 조정
            if sub_strategy == ReplatformSubStrategy.EC2_REHOST:
                key_benefits = [
                    "코드 변경 없이 Lift & Shift로 가장 빠른 마이그레이션",
                    "Oracle RAC, EE 고급 기능 등 모든 기능 유지",
                    "OS 레벨 완전한 제어권 확보",
                    "기존 운영 방식 그대로 유지 가능"
                ]
                key_risks = [
                    "Oracle 라이선스 비용 지속 발생 (BYOL)",
                    "인프라 관리 부담 (패치, 백업 등)",
                    "클라우드 네이티브 이점 제한적",
                    "장기적으로 운영 비용 증가 가능"
                ]
                estimated_duration = "4-6주 (Lift & Shift)"
            elif sub_strategy == ReplatformSubStrategy.RDS_CUSTOM_ORACLE:
                key_benefits = [
                    "OS 레벨 접근 가능한 관리형 서비스",
                    "코드 변경 최소화로 마이그레이션 위험 감소",
                    "AWS 관리형 백업 및 패치 지원",
                    "필요시 OS 커스터마이징 가능"
                ]
                key_risks = [
                    "Oracle 라이선스 비용 지속 발생",
                    "RDS 대비 관리 복잡도 증가",
                    "일부 RDS 자동화 기능 미지원",
                    "장기적으로 클라우드 네이티브 이점 제한적"
                ]
                estimated_duration = "5-8주 (RDS Custom)"
            else:  # RDS_ORACLE (기본)
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
            summary_text = self._mysql_generator.generate(metrics)
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
            summary_text = self._postgresql_generator.generate(metrics)
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
