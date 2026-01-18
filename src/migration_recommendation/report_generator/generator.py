"""
추천 리포트 생성기 (메인)

통합 분석 결과를 기반으로 마이그레이션 추천 리포트를 생성합니다.
"""

import logging
from typing import List
from ..data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy,
    MigrationRecommendation,
    ExecutiveSummary,
    InstanceRecommendation
)
from ..decision_engine import MigrationDecisionEngine
from .rationale_generator import RationaleGenerator
from .alternative_generator import AlternativeGenerator
from .risk_generator import RiskGenerator
from .roadmap_generator import RoadmapGenerator
from .summary_generator import SummaryGenerator

# 로거 초기화
logger = logging.getLogger(__name__)


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
        self.rationale_generator = RationaleGenerator()
        self.alternative_generator = AlternativeGenerator()
        self.risk_generator = RiskGenerator()
        self.roadmap_generator = RoadmapGenerator()
        self.summary_generator = SummaryGenerator()
    
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
        logger.info("마이그레이션 추천 리포트 생성 시작")
        
        metrics = integrated_result.metrics
        
        # 1. 추천 전략 결정
        logger.info("추천 전략 결정 중")
        recommended_strategy = self.decision_engine.decide_strategy(integrated_result)
        logger.info(f"추천 전략 결정 완료: {recommended_strategy.value}")
        
        # 2. 신뢰도 계산
        confidence_level = self._calculate_confidence(metrics, recommended_strategy)
        logger.info(f"신뢰도 계산 완료: {confidence_level}")
        
        # 3. 추천 근거 생성
        logger.info("추천 근거 생성 중")
        rationales = self.rationale_generator.generate_rationales(recommended_strategy, metrics)
        logger.info(f"추천 근거 생성 완료: {len(rationales)}개")
        
        # 4. 대안 전략 생성
        logger.info("대안 전략 생성 중")
        alternative_strategies = self.alternative_generator.generate_alternatives(recommended_strategy, metrics)
        logger.info(f"대안 전략 생성 완료: {len(alternative_strategies)}개")
        
        # 5. 위험 요소 생성
        logger.info("위험 요소 생성 중")
        risks = self.risk_generator.generate_risks(recommended_strategy, metrics)
        logger.info(f"위험 요소 생성 완료: {len(risks)}개")
        
        # 6. 마이그레이션 로드맵 생성
        logger.info("마이그레이션 로드맵 생성 중")
        roadmap = self.roadmap_generator.generate_roadmap(recommended_strategy, metrics)
        logger.info(f"마이그레이션 로드맵 생성 완료: {len(roadmap.phases)}단계")
        
        # 7. 인스턴스 추천 생성
        logger.info("인스턴스 추천 생성 중")
        instance_recommendation = self._generate_instance_recommendation(recommended_strategy, metrics)
        logger.info("인스턴스 추천 생성 완료")
        
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
        logger.info("Executive Summary 생성 중")
        executive_summary = self.summary_generator.generate_executive_summary(recommendation)
        recommendation.executive_summary = executive_summary
        logger.info("Executive Summary 생성 완료")
        
        logger.info("마이그레이션 추천 리포트 생성 완료")
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
        performance_buffer = 1.2
        estimated_peak_cpu = cpu_usage * performance_buffer
        estimated_peak_io = io_load * performance_buffer
        estimated_peak_memory = memory_usage * performance_buffer
        
        # 인스턴스 타입 결정 (메모리 기준)
        if strategy == MigrationStrategy.REPLATFORM:
            instance_type, vcpu, memory_gb, rationale = self._get_rds_oracle_instance(
                cpu_usage, io_load, memory_usage, 
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory
            )
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            instance_type, vcpu, memory_gb, rationale = self._get_aurora_mysql_instance(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory
            )
        else:  # REFACTOR_POSTGRESQL
            instance_type, vcpu, memory_gb, rationale = self._get_aurora_postgresql_instance(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory
            )
        
        return InstanceRecommendation(
            instance_type=instance_type,
            vcpu=vcpu,
            memory_gb=memory_gb,
            rationale=rationale
        )
    
    def _get_rds_oracle_instance(self, cpu_usage, io_load, memory_usage, 
                                  estimated_peak_cpu, estimated_peak_io, estimated_peak_memory):
        """RDS Oracle SE2 인스턴스 추천"""
        if estimated_peak_memory > 32:
            return "db.r6i.2xlarge", 8, 64, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.2xlarge", 8, 64,
                "예상 피크 메모리가 32GB를 초과하므로 메모리 부족 없이 안정적인 성능을 제공합니다."
            )
        elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
            return "db.r6i.xlarge", 4, 32, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.xlarge", 4, 32,
                "현재 워크로드에 적합하며, 피크 시에도 충분한 여유가 있습니다."
            )
        else:
            return "db.r6i.large", 2, 16, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.large", 2, 16,
                "비용 효율적이며, 필요시 상위 인스턴스로 업그레이드 가능합니다."
            )
    
    def _get_aurora_mysql_instance(self, cpu_usage, io_load, memory_usage,
                                    estimated_peak_cpu, estimated_peak_io, estimated_peak_memory):
        """Aurora MySQL 인스턴스 추천"""
        if estimated_peak_memory > 32:
            return "db.r6i.2xlarge", 8, 64, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.2xlarge", 8, 64,
                "Aurora MySQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
            )
        elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
            return "db.r6i.xlarge", 4, 32, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.xlarge", 4, 32,
                "Aurora MySQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
            )
        else:
            return "db.r6i.large", 2, 16, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.large", 2, 16,
                "Aurora MySQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
            )
    
    def _get_aurora_postgresql_instance(self, cpu_usage, io_load, memory_usage,
                                         estimated_peak_cpu, estimated_peak_io, estimated_peak_memory):
        """Aurora PostgreSQL 인스턴스 추천"""
        if estimated_peak_memory > 32:
            return "db.r6i.2xlarge", 8, 64, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.2xlarge", 8, 64,
                "Aurora PostgreSQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
            )
        elif estimated_peak_memory > 16 or cpu_usage >= 50 or io_load >= 500:
            return "db.r6i.xlarge", 4, 32, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.xlarge", 4, 32,
                "Aurora PostgreSQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
            )
        else:
            return "db.r6i.large", 2, 16, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                "db.r6i.large", 2, 16,
                "Aurora PostgreSQL의 자동 스케일링으로 필요시 유연하게 확장 가능합니다."
            )
    
    def _format_rationale(self, cpu_usage, io_load, memory_usage,
                          estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                          instance_type, vcpu, memory_gb, reason):
        """인스턴스 추천 근거 포맷팅"""
        return (
            f"**AWR/Statspack 분석 결과**:\n"
            f"- 평균 CPU 사용률: {cpu_usage:.1f}%\n"
            f"- 평균 I/O 부하: {io_load:.1f} IOPS\n"
            f"- 평균 메모리 사용량: {memory_usage:.1f} GB\n\n"
            f"**피크 부하 예상 (P99 기준 +20% 여유율)**:\n"
            f"- 예상 피크 CPU: {estimated_peak_cpu:.1f}%\n"
            f"- 예상 피크 I/O: {estimated_peak_io:.1f} IOPS\n"
            f"- 예상 피크 메모리: {estimated_peak_memory:.1f} GB\n\n"
            f"**추천 근거**: 예상 피크 메모리({estimated_peak_memory:.1f}GB)를 고려하여 "
            f"**{instance_type}** (vCPU {vcpu}, 메모리 {memory_gb}GB)를 추천합니다. {reason}"
        )
