"""
추천 리포트 생성기 (메인)

통합 분석 결과를 기반으로 마이그레이션 추천 리포트를 생성합니다.
"""

import logging
from typing import List, Optional, Tuple
from ..data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics,
    MigrationStrategy,
    MigrationRecommendation,
    ExecutiveSummary,
    InstanceRecommendation,
    DataAvailability,
    ConfidenceAssessment,
)
from ..decision_engine import MigrationDecisionEngine
from ..confidence_calculator import ConfidenceCalculator, determine_data_availability
from .rationale_generator import RationaleGenerator
from .alternative_generator import AlternativeGenerator
from .risk_generator import RiskGenerator
from .roadmap_generator import RoadmapGenerator
from .summary_generator import SummaryGenerator

# SGA 기반 인스턴스 추천을 위한 import
from src.dbcsi.migration_analyzer.instance_recommender import (
    get_recommended_sga_from_advice,
    select_instance_type,
    R6I_INSTANCES,
)

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
        
        # 0. 데이터 가용성 결정
        data_availability = self._determine_data_availability(integrated_result)
        logger.info(f"분석 모드: {data_availability.get_analysis_mode().value}")
        
        # 1. 추천 전략 결정
        logger.info("추천 전략 결정 중")
        recommended_strategy = self.decision_engine.decide_strategy(integrated_result)
        logger.info(f"추천 전략 결정 완료: {recommended_strategy.value}")
        
        # Replatform 선택 이유 가져오기
        replatform_reasons = self.decision_engine.get_replatform_reasons()
        
        # Replatform 세부 전략 결정 (Replatform인 경우에만)
        replatform_sub_strategy = None
        replatform_sub_strategy_reasons = []
        if recommended_strategy == MigrationStrategy.REPLATFORM:
            logger.info("Replatform 세부 전략 결정 중")
            replatform_sub_strategy, replatform_sub_strategy_reasons = \
                self.decision_engine.decide_replatform_sub_strategy(metrics)
            logger.info(f"Replatform 세부 전략: {replatform_sub_strategy.value}")
        
        # 2. 신뢰도 계산 (신규)
        logger.info("신뢰도 계산 중")
        confidence_assessment = ConfidenceCalculator.calculate(
            data_availability, metrics, recommended_strategy
        )
        logger.info(f"종합 신뢰도: {confidence_assessment.overall_confidence}%")
        
        # 3. 신뢰도 레벨 (기존 호환성 유지)
        confidence_level = self._calculate_confidence(metrics, recommended_strategy)
        logger.info(f"신뢰도 레벨: {confidence_level}")
        
        # 4. 추천 근거 생성
        logger.info("추천 근거 생성 중")
        rationales = self.rationale_generator.generate_rationales(recommended_strategy, metrics)
        logger.info(f"추천 근거 생성 완료: {len(rationales)}개")
        
        # 5. 대안 전략 생성
        logger.info("대안 전략 생성 중")
        alternative_strategies = self.alternative_generator.generate_alternatives(recommended_strategy, metrics)
        logger.info(f"대안 전략 생성 완료: {len(alternative_strategies)}개")
        
        # 6. 위험 요소 생성
        logger.info("위험 요소 생성 중")
        risks = self.risk_generator.generate_risks(recommended_strategy, metrics)
        logger.info(f"위험 요소 생성 완료: {len(risks)}개")
        
        # 7. 마이그레이션 로드맵 생성
        logger.info("마이그레이션 로드맵 생성 중")
        roadmap = self.roadmap_generator.generate_roadmap(recommended_strategy, metrics)
        logger.info(f"마이그레이션 로드맵 생성 완료: {len(roadmap.phases)}단계")
        
        # 8. 인스턴스 추천 생성
        logger.info("인스턴스 추천 생성 중")
        instance_recommendation = self._generate_instance_recommendation(
            recommended_strategy, metrics, integrated_result
        )
        logger.info("인스턴스 추천 생성 완료")
        
        # 9. MigrationRecommendation 객체 생성 (Executive Summary 제외)
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
            metrics=metrics,
            confidence_assessment=confidence_assessment,
            data_availability=data_availability,
            replatform_reasons=replatform_reasons,
            replatform_sub_strategy=replatform_sub_strategy,
            replatform_sub_strategy_reasons=replatform_sub_strategy_reasons,
        )
        
        # 10. Executive Summary 생성 (recommendation 객체 필요)
        logger.info("Executive Summary 생성 중")
        executive_summary = self.summary_generator.generate_executive_summary(recommendation)
        recommendation.executive_summary = executive_summary
        logger.info("Executive Summary 생성 완료")
        
        logger.info("마이그레이션 추천 리포트 생성 완료")
        return recommendation
    
    def _determine_data_availability(
        self,
        integrated_result: IntegratedAnalysisResult
    ) -> DataAvailability:
        """데이터 가용성 결정
        
        Args:
            integrated_result: 통합 분석 결과
            
        Returns:
            DataAvailability: 데이터 가용성 정보
        """
        sql_count = len(integrated_result.sql_analysis) if integrated_result.sql_analysis else 0
        plsql_count = len(integrated_result.plsql_analysis) if integrated_result.plsql_analysis else 0
        
        # DBCSI 데이터 존재 여부 확인 (dbcsi_result 또는 metrics에서 확인)
        has_dbcsi = integrated_result.dbcsi_result is not None
        
        # dbcsi_result가 없어도 metrics에 DBCSI 데이터가 있으면 has_dbcsi=True
        if not has_dbcsi and integrated_result.metrics:
            metrics = integrated_result.metrics
            # db_name이 있거나 성능 메트릭이 있으면 DBCSI 데이터가 있는 것으로 판단
            if (getattr(metrics, 'db_name', None) or 
                getattr(metrics, 'avg_cpu_usage', 0) > 0 or
                getattr(metrics, 'avg_io_load', 0) > 0):
                has_dbcsi = True
        
        # DBCSI 타입 결정
        dbcsi_type = ""
        if has_dbcsi:
            if integrated_result.dbcsi_result:
                if hasattr(integrated_result.dbcsi_result, 'is_awr'):
                    dbcsi_type = "awr" if integrated_result.dbcsi_result.is_awr() else "statspack"
                else:
                    dbcsi_type = "statspack"
            else:
                # dbcsi_result가 없지만 metrics에서 DBCSI 데이터가 있는 경우
                # metrics에서 report_type 확인
                report_type = getattr(metrics, 'report_type', None)
                if report_type == 'awr':
                    dbcsi_type = "awr"
                else:
                    dbcsi_type = "statspack"
        
        return determine_data_availability(
            sql_count=sql_count,
            plsql_count=plsql_count,
            has_dbcsi=has_dbcsi,
            dbcsi_type=dbcsi_type,
            sql_source="file" if sql_count > 0 else "none",
            plsql_source="file" if plsql_count > 0 else "none",
            dbcsi_source="report" if has_dbcsi and not integrated_result.dbcsi_result else ("file" if has_dbcsi else "none"),
        )
    
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
        metrics: AnalysisMetrics,
        integrated_result: Optional[IntegratedAnalysisResult] = None
    ) -> InstanceRecommendation:
        """
        인스턴스 추천 생성
        
        Requirements 11.4, 11.5, 11.6을 구현합니다.
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            integrated_result: 통합 분석 결과 (SGA advice 추출용)
            
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
        
        # 현재 SGA 크기 고려 (SGA가 메모리 사용량보다 클 수 있음)
        current_sga_gb = getattr(metrics, 'current_sga_gb', None) or 0.0
        if current_sga_gb > 0:
            # SGA + PGA 추정(10%) + 20% 여유분
            sga_based_memory = current_sga_gb * 1.1 * 1.2
            estimated_peak_memory = max(estimated_peak_memory, sga_based_memory)
        
        # 워크로드 패턴 분석 (RAC 필요성 평가)
        rac_assessment, ha_recommendation = self._analyze_workload_pattern(metrics, strategy)
        
        # 인스턴스 타입 결정 (메모리 기준)
        if strategy == MigrationStrategy.REPLATFORM:
            instance_type, vcpu, memory_gb, rationale = self._get_rds_oracle_instance(
                cpu_usage, io_load, memory_usage, 
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                current_sga_gb
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
        
        # SGA 기반 인스턴스 추천 계산
        sga_based_instance, sga_based_vcpu, sga_based_memory, recommended_sga_gb, current_sga_gb = \
            self._calculate_sga_based_instance(integrated_result, metrics)
        
        return InstanceRecommendation(
            instance_type=instance_type,
            vcpu=vcpu,
            memory_gb=memory_gb,
            rationale=rationale,
            rac_assessment=rac_assessment,
            ha_recommendation=ha_recommendation,
            # SGA 기반 인스턴스 추천
            sga_based_instance_type=sga_based_instance,
            sga_based_vcpu=sga_based_vcpu,
            sga_based_memory_gb=sga_based_memory,
            recommended_sga_gb=recommended_sga_gb,
            current_sga_gb=current_sga_gb
        )
    
    def _calculate_sga_based_instance(
        self,
        integrated_result: Optional[IntegratedAnalysisResult],
        metrics: AnalysisMetrics
    ) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[float], Optional[float]]:
        """
        SGA 권장사항 기반 인스턴스 추천 계산
        
        권장 SGA가 현재 SGA보다 큰 경우에만 SGA 기반 인스턴스를 추천합니다.
        이는 메모리 증설이 필요한 경우에만 별도 추천을 제공하기 위함입니다.
        
        Args:
            integrated_result: 통합 분석 결과
            metrics: 분석 메트릭
            
        Returns:
            Tuple: (인스턴스 타입, vCPU, 메모리 GB, 권장 SGA GB, 현재 SGA GB)
        """
        recommended_sga_gb: Optional[float] = None
        current_sga_gb: Optional[float] = None
        
        # 1. 먼저 metrics에서 SGA 정보 확인 (리포트 파싱 결과)
        if hasattr(metrics, 'recommended_sga_gb') and getattr(metrics, 'recommended_sga_gb', None):
            recommended_sga_gb = getattr(metrics, 'recommended_sga_gb')
            current_sga_gb = getattr(metrics, 'current_sga_gb', None)
        
        # 2. dbcsi_result에서 sga_advice 확인 (원본 파일 파싱 결과)
        if recommended_sga_gb is None and integrated_result and integrated_result.dbcsi_result:
            dbcsi_result = integrated_result.dbcsi_result
            sga_advice = getattr(dbcsi_result, 'sga_advice', None)
            
            if sga_advice:
                recommended_sga_gb = get_recommended_sga_from_advice(sga_advice)
                
                # 현재 SGA 크기 계산 (size_factor가 1.0인 항목에서)
                for advice in sga_advice:
                    if abs(advice.sga_size_factor - 1.0) < 0.01:
                        current_sga_gb = advice.sga_size / 1024.0  # MB to GB
                        break
        
        # SGA 권장사항이 없으면 None 반환
        if not recommended_sga_gb or recommended_sga_gb <= 0:
            return None, None, None, None, current_sga_gb
        
        # 권장 SGA가 현재 SGA보다 작거나 같으면 SGA 기반 추천 불필요
        # (현재 서버 사양 기반 추천으로 충분)
        if current_sga_gb and recommended_sga_gb <= current_sga_gb:
            return None, None, None, recommended_sga_gb, current_sga_gb
        
        # PGA 추정 (현재 메모리의 약 10%)
        estimated_pga_gb = metrics.avg_memory_usage * 0.1 if metrics.avg_memory_usage > 0 else 0.0
        
        # 권장 SGA + PGA + 20% 여유분
        required_memory_gb = int((recommended_sga_gb + estimated_pga_gb) * 1.2 + 0.5)
        required_memory_gb = max(required_memory_gb, 16)  # 최소 16GB
        
        # CPU 요구사항 (현재 CPU 기준)
        num_cpus = metrics.num_cpus or 8
        required_vcpu = max(num_cpus, 2)
        
        # 인스턴스 타입 선택
        instance_type = select_instance_type(required_vcpu, required_memory_gb)
        if not instance_type:
            return None, None, None, recommended_sga_gb, current_sga_gb
        
        # 선택된 인스턴스 스펙
        selected_vcpu, selected_memory_gib = R6I_INSTANCES[instance_type]
        
        return instance_type, selected_vcpu, selected_memory_gib, recommended_sga_gb, current_sga_gb
    
    def _get_rds_oracle_instance(self, cpu_usage, io_load, memory_usage, 
                                  estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                                  current_sga_gb: float = 0.0):
        """RDS Oracle SE2 인스턴스 추천
        
        Args:
            cpu_usage: 평균 CPU 사용률
            io_load: 평균 I/O 부하
            memory_usage: 평균 메모리 사용량
            estimated_peak_cpu: 예상 피크 CPU
            estimated_peak_io: 예상 피크 I/O
            estimated_peak_memory: 예상 피크 메모리
            current_sga_gb: 현재 SGA 크기 (GB)
        """
        # 필요한 메모리 계산 (GB)
        required_memory_gb = int(estimated_peak_memory + 0.5)
        required_memory_gb = max(required_memory_gb, 16)  # 최소 16GB
        
        # select_instance_type을 사용하여 적절한 인스턴스 선택
        instance_type = select_instance_type(2, required_memory_gb)
        
        if instance_type and instance_type in R6I_INSTANCES:
            vcpu, memory_gb = R6I_INSTANCES[instance_type]
            
            # SGA 정보가 있으면 rationale에 포함
            sga_info = ""
            if current_sga_gb > 0:
                sga_info = f"\n- 현재 SGA 크기: {current_sga_gb:.1f} GB"
            
            rationale = self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                instance_type, vcpu, memory_gb,
                f"예상 피크 메모리({estimated_peak_memory:.1f}GB)를 고려하여 메모리 부족 없이 안정적인 성능을 제공합니다.{sga_info}"
            )
            return instance_type, vcpu, memory_gb, rationale
        
        # 기본값 (fallback)
        return "db.r6i.2xlarge", 8, 64, self._format_rationale(
            cpu_usage, io_load, memory_usage,
            estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
            "db.r6i.2xlarge", 8, 64,
            "예상 피크 메모리가 32GB를 초과하므로 메모리 부족 없이 안정적인 성능을 제공합니다."
        )
    
    def _get_aurora_mysql_instance(self, cpu_usage, io_load, memory_usage,
                                    estimated_peak_cpu, estimated_peak_io, estimated_peak_memory):
        """Aurora MySQL 인스턴스 추천"""
        # 필요한 메모리 계산 (GB)
        required_memory_gb = int(estimated_peak_memory + 0.5)
        required_memory_gb = max(required_memory_gb, 16)  # 최소 16GB
        
        # select_instance_type을 사용하여 적절한 인스턴스 선택
        instance_type = select_instance_type(2, required_memory_gb)
        
        if instance_type and instance_type in R6I_INSTANCES:
            vcpu, memory_gb = R6I_INSTANCES[instance_type]
            return instance_type, vcpu, memory_gb, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                instance_type, vcpu, memory_gb,
                "Aurora MySQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
            )
        
        # 기본값 (fallback)
        return "db.r6i.2xlarge", 8, 64, self._format_rationale(
            cpu_usage, io_load, memory_usage,
            estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
            "db.r6i.2xlarge", 8, 64,
            "Aurora MySQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
        )
    
    def _get_aurora_postgresql_instance(self, cpu_usage, io_load, memory_usage,
                                         estimated_peak_cpu, estimated_peak_io, estimated_peak_memory):
        """Aurora PostgreSQL 인스턴스 추천"""
        # 필요한 메모리 계산 (GB)
        required_memory_gb = int(estimated_peak_memory + 0.5)
        required_memory_gb = max(required_memory_gb, 16)  # 최소 16GB
        
        # select_instance_type을 사용하여 적절한 인스턴스 선택
        instance_type = select_instance_type(2, required_memory_gb)
        
        if instance_type and instance_type in R6I_INSTANCES:
            vcpu, memory_gb = R6I_INSTANCES[instance_type]
            return instance_type, vcpu, memory_gb, self._format_rationale(
                cpu_usage, io_load, memory_usage,
                estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
                instance_type, vcpu, memory_gb,
                "Aurora PostgreSQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
            )
        
        # 기본값 (fallback)
        return "db.r6i.2xlarge", 8, 64, self._format_rationale(
            cpu_usage, io_load, memory_usage,
            estimated_peak_cpu, estimated_peak_io, estimated_peak_memory,
            "db.r6i.2xlarge", 8, 64,
            "Aurora PostgreSQL의 자동 스케일링 기능으로 피크 시 추가 확장이 가능합니다."
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

    def _analyze_workload_pattern(
        self,
        metrics: AnalysisMetrics,
        strategy: MigrationStrategy
    ) -> tuple[Optional[str], Optional[str]]:
        """워크로드 패턴 분석 및 RAC 필요성 평가
        
        AWR 데이터를 기반으로 쓰기 워크로드 비율을 분석하여
        RAC 필요성과 Multi-AZ 구성 권장사항을 제공합니다.
        
        Args:
            metrics: 분석 메트릭
            strategy: 마이그레이션 전략
            
        Returns:
            tuple[Optional[str], Optional[str]]: (RAC 평가, HA 권장사항)
        """
        # Replatform 전략이 아니면 RAC 평가 불필요
        if strategy != MigrationStrategy.REPLATFORM:
            return None, None
        
        # AWR 데이터가 없으면 평가 불가
        if not metrics.avg_cpu_usage or not metrics.avg_io_load:
            return None, None
        
        # 쓰기 워크로드 비율 추정 (I/O 부하 기반)
        # 일반적으로 IOPS가 1000 이상이면 쓰기 집약적으로 간주
        write_intensive_threshold = 1000
        high_write_threshold = 2000
        
        io_load = metrics.avg_io_load
        cpu_usage = metrics.avg_cpu_usage
        
        # RAC 필요성 평가
        if io_load >= high_write_threshold and cpu_usage >= 70:
            # 매우 높은 쓰기 워크로드 + 높은 CPU 사용률
            rac_assessment = (
                f"**RAC 필요성 평가**: 현재 시스템의 I/O 부하({io_load:.1f} IOPS)와 "
                f"CPU 사용률({cpu_usage:.1f}%)이 매우 높아 RAC 구성이 필요할 수 있습니다. "
                f"그러나 RDS Oracle SE2는 Single 인스턴스만 지원하므로, "
                f"애플리케이션 레벨에서 쓰기 분산 처리를 고려하시기 바랍니다."
            )
            ha_recommendation = (
                f"**고가용성 구성**: Multi-AZ 배포를 통해 이중화 구성을 권장합니다. "
                f"단, Multi-AZ 구성 시 라이선스 비용이 2배로 증가하므로 비용을 고려하여 결정하시기 바랍니다. "
                f"읽기 부하 분산이 필요한 경우 Read Replica를 활용할 수 있습니다."
            )
        elif io_load >= write_intensive_threshold:
            # 중간 수준의 쓰기 워크로드
            rac_assessment = (
                f"**RAC 필요성 평가**: 현재 시스템의 I/O 부하({io_load:.1f} IOPS)는 중간 수준으로, "
                f"RAC가 필요할 정도로 쓰기 워크로드가 많지 않습니다. "
                f"Single 인스턴스로 충분히 처리 가능합니다."
            )
            ha_recommendation = (
                f"**고가용성 구성**: Multi-AZ 배포를 통해 이중화 구성을 권장합니다. "
                f"단, Multi-AZ 구성 시 라이선스 비용이 2배로 증가하므로 비용을 고려하여 결정하시기 바랍니다. "
                f"읽기 부하가 높은 경우 Read Replica를 통한 읽기 분산 처리로 충분합니다."
            )
        else:
            # 낮은 쓰기 워크로드
            rac_assessment = (
                f"**RAC 필요성 평가**: 현재 시스템의 I/O 부하({io_load:.1f} IOPS)는 낮은 수준으로, "
                f"RAC가 필요하지 않습니다. Single 인스턴스로 충분합니다."
            )
            ha_recommendation = (
                f"**고가용성 구성**: 읽기 분산 처리를 위해 Read Replica 구성을 권장합니다. "
                f"고가용성이 필요한 경우 Multi-AZ 배포를 고려할 수 있으나, "
                f"라이선스 비용이 2배로 증가하므로 비용 대비 효과를 검토하시기 바랍니다."
            )
        
        return rac_assessment, ha_recommendation
