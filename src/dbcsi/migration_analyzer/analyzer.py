"""
마이그레이션 분석기 메인 모듈

MigrationAnalyzer 클래스와 EnhancedMigrationAnalyzer 클래스를 포함합니다.
"""

from typing import Dict, Optional, Any, List
import statistics
from ..data_models import (
    StatspackData,
    OracleEdition,
    TargetDatabase,
    MigrationComplexity,
    InstanceRecommendation
)
from ..exceptions import MigrationAnalysisError
from ..logging_config import get_logger

# 로거 초기화
logger = get_logger("migration_analyzer")


class MigrationAnalyzer:
    """마이그레이션 난이도 분석 엔진"""
    
    def __init__(self, statspack_data: StatspackData):
        """
        Statspack 데이터를 받아 초기화
        
        Args:
            statspack_data: 파싱된 Statspack 데이터
        """
        self.data = statspack_data
        self._oracle_edition: Optional[OracleEdition] = None
        self._is_rac: Optional[bool] = None
        self._character_set: Optional[str] = None
        self._charset_conversion_required: Optional[bool] = None
    
    def _detect_oracle_edition(self) -> OracleEdition:
        """
        Oracle 에디션 감지
        
        BANNER 정보에서 에디션을 추출합니다.
        
        Returns:
            OracleEdition: 감지된 Oracle 에디션
        """
        if self._oracle_edition is not None:
            return self._oracle_edition
        
        banner = self.data.os_info.banner
        if not banner:
            self._oracle_edition = OracleEdition.UNKNOWN
            return self._oracle_edition
        
        banner_lower = banner.lower()
        
        # 에디션 감지 (우선순위: 더 구체적인 것부터)
        # "Standard Edition 2"를 먼저 체크해야 "Standard Edition"과 구분됨
        if "express edition" in banner_lower:
            self._oracle_edition = OracleEdition.EXPRESS
        elif "standard edition 2" in banner_lower:
            self._oracle_edition = OracleEdition.STANDARD_2
        elif "enterprise edition" in banner_lower:
            self._oracle_edition = OracleEdition.ENTERPRISE
        elif "standard edition" in banner_lower:
            self._oracle_edition = OracleEdition.STANDARD
        # 약어 체크 (단어 경계 고려)
        else:
            # 단어로 분리하여 약어 확인
            words = banner_lower.split()
            if "xe" in words:
                self._oracle_edition = OracleEdition.EXPRESS
            elif "se2" in words:
                self._oracle_edition = OracleEdition.STANDARD_2
            elif "ee" in words:
                self._oracle_edition = OracleEdition.ENTERPRISE
            elif "se" in words:
                self._oracle_edition = OracleEdition.STANDARD
            else:
                self._oracle_edition = OracleEdition.UNKNOWN
        
        return self._oracle_edition
    
    def _detect_rac(self) -> bool:
        """
        RAC 환경 감지
        
        INSTANCES 값이 1보다 크면 RAC 환경으로 판단합니다.
        
        Returns:
            bool: RAC 환경 여부
        """
        if self._is_rac is not None:
            return self._is_rac
        
        instances = self.data.os_info.instances
        if instances is None:
            self._is_rac = False
        else:
            self._is_rac = instances > 1
        
        return self._is_rac
    
    def _detect_character_set(self) -> str:
        """
        캐릭터셋 감지
        
        OS-INFORMATION에서 Character Set 정보를 추출합니다.
        
        Returns:
            str: 캐릭터셋 이름 (없으면 빈 문자열)
        """
        if self._character_set is not None:
            return self._character_set
        
        from .charset_analyzer import detect_character_set
        
        charset = self.data.os_info.character_set
        self._character_set = detect_character_set(charset)
        
        return self._character_set
    
    def _requires_charset_conversion(self) -> bool:
        """
        캐릭터셋 변환 필요 여부
        
        현재 캐릭터셋이 AL32UTF8이 아니면 변환이 필요합니다.
        
        Returns:
            bool: 캐릭터셋 변환 필요 여부
        """
        if self._charset_conversion_required is not None:
            return self._charset_conversion_required
        
        from .charset_analyzer import requires_charset_conversion
        
        charset = self._detect_character_set()
        self._charset_conversion_required = requires_charset_conversion(charset)
        
        return self._charset_conversion_required

    def _analyze_resource_usage(self) -> Dict[str, Any]:
        """
        리소스 사용량 분석
        
        CPU, 메모리, 디스크, IOPS 사용량을 분석합니다.
        
        Returns:
            Dict[str, Any]: 리소스 사용량 분석 결과
                - cpu_avg_pct: 평균 CPU 사용률
                - cpu_p99_pct: P99 CPU 사용률
                - memory_avg_gb: 평균 메모리 사용량 (SGA+PGA)
                - memory_max_gb: 최대 메모리 사용량
                - disk_size_gb: 디스크 크기
                - read_iops_avg: 평균 읽기 IOPS
                - write_iops_avg: 평균 쓰기 IOPS
                - total_iops_avg: 평균 총 IOPS
                - total_iops_p99: P99 총 IOPS
        """
        from .resource_analyzer import analyze_resource_usage
        return analyze_resource_usage(self.data)

    def _analyze_wait_events(self) -> Dict[str, Any]:
        """
        대기 이벤트 분석
        
        대기 이벤트를 카테고리별로 분류하고 분석합니다.
        
        Returns:
            Dict[str, Any]: 대기 이벤트 분석 결과
                - db_cpu_pct: DB CPU 비율
                - user_io_pct: User I/O 대기 비율
                - system_io_pct: System I/O 대기 비율
                - commit_pct: Commit 대기 비율
                - network_pct: Network 대기 비율
                - other_pct: 기타 대기 비율
                - top_events: 상위 대기 이벤트 목록
                - recommendations: 최적화 권장사항
        """
        from .wait_event_analyzer import analyze_wait_events
        return analyze_wait_events(self.data)

    def _analyze_feature_compatibility(self, target: TargetDatabase) -> Dict[str, Any]:
        """
        Oracle 기능 호환성 분석
        
        사용된 Oracle 기능의 타겟 DB별 호환성을 분석합니다.
        
        Args:
            target: 타겟 데이터베이스
        
        Returns:
            Dict[str, Any]: 기능 호환성 분석 결과
                - used_features: 사용된 기능 목록
                - compatibility_score: 호환성 점수 (0-10, 낮을수록 호환성 높음)
                - incompatible_features: 비호환 기능 목록
                - alternatives: 대체 방안
        """
        from .feature_analyzer import analyze_feature_compatibility
        return analyze_feature_compatibility(self.data, target)

    def _evaluate_plsql_complexity(self, target: TargetDatabase) -> Dict[str, Any]:
        """
        PL/SQL 코드 복잡도 평가
        
        PL/SQL 코드 라인 수와 패키지 수를 기반으로 복잡도를 계산합니다.
        
        Args:
            target: 타겟 데이터베이스
        
        Returns:
            Dict[str, Any]: PL/SQL 복잡도 평가 결과
                - lines_of_code: PL/SQL 코드 라인 수
                - package_count: 패키지 수
                - procedure_count: 프로시저 수
                - function_count: 함수 수
                - complexity_score: 복잡도 점수
                - conversion_strategy: 변환 전략
        """
        from .plsql_evaluator import evaluate_plsql_complexity
        return evaluate_plsql_complexity(self.data, target)

    def _calculate_charset_complexity(self) -> float:
        """
        캐릭터셋 변환 복잡도 계산
        
        캐릭터셋 타입별 가중치를 적용하여 변환 복잡도를 계산합니다.
        
        Returns:
            float: 캐릭터셋 변환 복잡도 점수 (0.0 ~ 2.5)
        """
        from .complexity_calculators import calculate_charset_complexity
        
        charset = self._detect_character_set()
        requires_conversion = self._requires_charset_conversion()
        
        return calculate_charset_complexity(charset, requires_conversion)
    
    def _generate_charset_warnings(self) -> List[str]:
        """
        캐릭터셋 변환 경고 메시지 생성
        
        Returns:
            List[str]: 경고 메시지 목록
        """
        from .complexity_calculators import generate_charset_warnings
        
        charset = self._detect_character_set()
        requires_conversion = self._requires_charset_conversion()
        disk_size = self.data.os_info.total_db_size_gb or 0.0
        
        return generate_charset_warnings(charset, requires_conversion, disk_size)

    def _calculate_rds_oracle_complexity(self) -> MigrationComplexity:
        """
        RDS for Oracle 마이그레이션 난이도 계산
        
        기본 점수 1.0에서 시작하여 다음 요소를 고려합니다:
        - 에디션 변경 가중치
        - RAC → Single Instance 가중치
        - 버전 업그레이드 가중치
        - 캐릭터셋 변환 가중치
        
        Returns:
            MigrationComplexity: RDS for Oracle 마이그레이션 난이도
        """
        from .complexity_calculators import calculate_rds_oracle_complexity
        
        # 필요한 정보 수집
        edition = self._detect_oracle_edition()
        is_rac = self._detect_rac()
        charset = self._detect_character_set()
        requires_charset_conversion = self._requires_charset_conversion()
        charset_complexity = self._calculate_charset_complexity()
        charset_warnings = self._generate_charset_warnings()
        instance_recommendation = self._recommend_instance_size(TargetDatabase.RDS_ORACLE, 1.0)
        
        # 복잡도 계산 위임
        return calculate_rds_oracle_complexity(
            self.data,
            edition,
            is_rac,
            charset,
            requires_charset_conversion,
            charset_complexity,
            charset_warnings,
            instance_recommendation
        )

    def _calculate_aurora_postgresql_complexity(self) -> MigrationComplexity:
        """
        Aurora PostgreSQL 마이그레이션 난이도 계산
        
        기본 점수 3.0에서 시작하여 다음 요소를 고려합니다:
        - PL/SQL 코드 가중치
        - Oracle 특화 기능 가중치
        - 성능 최적화 가중치
        - 캐릭터셋 변환 가중치
        
        Returns:
            MigrationComplexity: Aurora PostgreSQL 마이그레이션 난이도
        """
        from .complexity_calculators import calculate_aurora_postgresql_complexity
        
        # 필요한 분석 수행
        plsql_analysis = self._evaluate_plsql_complexity(TargetDatabase.AURORA_POSTGRESQL)
        feature_analysis = self._analyze_feature_compatibility(TargetDatabase.AURORA_POSTGRESQL)
        resource_analysis = self._analyze_resource_usage()
        wait_analysis = self._analyze_wait_events()
        charset_complexity = self._calculate_charset_complexity()
        charset_warnings = self._generate_charset_warnings()
        
        # 초기 점수 계산 (인스턴스 추천용)
        initial_score = 3.0 + plsql_analysis["complexity_score"] + feature_analysis["compatibility_score"]
        instance_recommendation = self._recommend_instance_size(TargetDatabase.AURORA_POSTGRESQL, initial_score)
        
        # 복잡도 계산 위임
        return calculate_aurora_postgresql_complexity(
            self.data,
            plsql_analysis,
            feature_analysis,
            resource_analysis,
            wait_analysis,
            charset_complexity,
            charset_warnings,
            instance_recommendation
        )

    def _calculate_aurora_mysql_complexity(self) -> MigrationComplexity:
        """
        Aurora MySQL 마이그레이션 난이도 계산
        
        기본 점수 4.0에서 시작하여 다음 요소를 고려합니다:
        - PL/SQL 코드 가중치 * 1.5 (PostgreSQL보다 어려움)
        - Oracle 특화 기능 가중치 * 1.3
        - 성능 최적화 가중치
        - 캐릭터셋 변환 가중치
        
        Returns:
            MigrationComplexity: Aurora MySQL 마이그레이션 난이도
        """
        from .complexity_calculators import calculate_aurora_mysql_complexity
        
        # 필요한 분석 수행
        plsql_analysis = self._evaluate_plsql_complexity(TargetDatabase.AURORA_MYSQL)
        feature_analysis = self._analyze_feature_compatibility(TargetDatabase.AURORA_MYSQL)
        resource_analysis = self._analyze_resource_usage()
        wait_analysis = self._analyze_wait_events()
        charset_complexity = self._calculate_charset_complexity()
        charset_warnings = self._generate_charset_warnings()
        
        # 초기 점수 계산 (인스턴스 추천용)
        initial_score = 4.0 + (plsql_analysis["complexity_score"] * 1.5) + (feature_analysis["compatibility_score"] * 1.3)
        instance_recommendation = self._recommend_instance_size(TargetDatabase.AURORA_MYSQL, initial_score)
        
        # 복잡도 계산 위임
        return calculate_aurora_mysql_complexity(
            self.data,
            plsql_analysis,
            feature_analysis,
            resource_analysis,
            wait_analysis,
            charset_complexity,
            charset_warnings,
            instance_recommendation
        )


    def _select_instance_type(self, required_vcpu: int, required_memory_gb: int) -> Optional[str]:
        """
        CPU와 메모리 요구사항을 만족하는 최소 r6i 인스턴스 선택
        
        Args:
            required_vcpu: 필요한 vCPU 수
            required_memory_gb: 필요한 메모리 (GB)
        
        Returns:
            Optional[str]: 선택된 인스턴스 타입 (예: "db.r6i.4xlarge") 또는 None
        """
        from .instance_recommender import select_instance_type
        return select_instance_type(required_vcpu, required_memory_gb)
    
    def _recommend_instance_size(
        self, 
        target: TargetDatabase, 
        complexity_score: float
    ) -> Optional[InstanceRecommendation]:
        """
        리소스 사용량 기반 RDS 인스턴스 사이즈 추천
        
        - CPU: P99 CPU 사용률 + 30% 여유분
        - 메모리: 현재 SGA+PGA + 20% 여유분
        - 난이도 > 7: RDS for Oracle만 추천
        - 난이도 <= 7: Aurora MySQL/PostgreSQL도 추천
        
        Args:
            target: 타겟 데이터베이스
            complexity_score: 마이그레이션 난이도 점수
        
        Returns:
            Optional[InstanceRecommendation]: 인스턴스 추천 정보 또는 None
        """
        from .instance_recommender import recommend_instance_size
        
        # 리소스 사용량 분석
        resource_analysis = self._analyze_resource_usage()
        
        # CPU 요구사항
        cpu_p99_pct = resource_analysis.get("cpu_p99_pct", 0.0)
        num_cpus = self.data.os_info.num_cpus or self.data.os_info.num_cpu_cores or 2
        
        # 메모리 요구사항
        memory_avg_gb = resource_analysis.get("memory_avg_gb", 0.0)
        physical_memory_gb = self.data.os_info.physical_memory_gb or 16.0
        
        return recommend_instance_size(
            target,
            complexity_score,
            cpu_p99_pct,
            num_cpus,
            memory_avg_gb,
            physical_memory_gb
        )

    def analyze(self, target: Optional[TargetDatabase] = None) -> Dict[TargetDatabase, MigrationComplexity]:
        """
        타겟별 마이그레이션 난이도 분석
        
        Args:
            target: 특정 타겟 데이터베이스 (None이면 모든 타겟 분석)
            
        Returns:
            타겟별 MigrationComplexity 딕셔너리
        """
        results = {}
        
        if target is None:
            # 모든 타겟에 대해 분석
            targets = [
                TargetDatabase.RDS_ORACLE,
                TargetDatabase.AURORA_POSTGRESQL,
                TargetDatabase.AURORA_MYSQL
            ]
        else:
            targets = [target]
        
        for t in targets:
            if t == TargetDatabase.RDS_ORACLE:
                results[t] = self._calculate_rds_oracle_complexity()
            elif t == TargetDatabase.AURORA_POSTGRESQL:
                results[t] = self._calculate_aurora_postgresql_complexity()
            elif t == TargetDatabase.AURORA_MYSQL:
                results[t] = self._calculate_aurora_mysql_complexity()
        
        return results



class EnhancedMigrationAnalyzer(MigrationAnalyzer):
    """확장된 마이그레이션 분석기 - AWR 데이터 기반"""
    
    def __init__(self, awr_data):
        """
        AWR 데이터를 받아 초기화
        
        Args:
            awr_data: 파싱된 AWR 데이터 (AWRData 또는 StatspackData)
        """
        # StatspackData로 기본 분석기 초기화
        super().__init__(awr_data)
        self.awr_data = awr_data
        
        # AWR 데이터인지 확인
        self._is_awr = hasattr(awr_data, 'is_awr') and awr_data.is_awr()
    
    def analyze(self, target: Optional[TargetDatabase] = None):
        """
        타겟별 마이그레이션 난이도 분석 - 백분위수 기반
        
        Args:
            target: 특정 타겟 데이터베이스 (None이면 모든 타겟 분석)
            
        Returns:
            타겟별 EnhancedMigrationComplexity 딕셔너리
        """
        from ..data_models import EnhancedMigrationComplexity
        
        results = {}
        
        if target is None:
            # 모든 타겟에 대해 분석
            targets = [
                TargetDatabase.RDS_ORACLE,
                TargetDatabase.AURORA_POSTGRESQL,
                TargetDatabase.AURORA_MYSQL
            ]
        else:
            targets = [target]
        
        for t in targets:
            results[t] = self._calculate_enhanced_complexity(t)
        
        return results
    
    def _calculate_enhanced_complexity(self, target: TargetDatabase):
        """
        백분위수 기반 난이도 계산
        
        Args:
            target: 타겟 데이터베이스
            
        Returns:
            EnhancedMigrationComplexity: 확장된 마이그레이션 복잡도
        """
        from ..data_models import EnhancedMigrationComplexity
        
        # 기본 난이도 계산
        if target == TargetDatabase.RDS_ORACLE:
            base_complexity = self._calculate_rds_oracle_complexity()
        elif target == TargetDatabase.AURORA_POSTGRESQL:
            base_complexity = self._calculate_aurora_postgresql_complexity()
        elif target == TargetDatabase.AURORA_MYSQL:
            base_complexity = self._calculate_aurora_mysql_complexity()
        else:
            raise MigrationAnalysisError(f"Unknown target database: {target}")
        
        # AWR 특화 요소 추가
        awr_factors = {}
        
        # 버퍼 캐시 효율성
        buffer_analysis = None
        if self._is_awr and hasattr(self.awr_data, 'buffer_cache_stats') and self.awr_data.buffer_cache_stats:
            buffer_analysis = self._analyze_buffer_cache()
            if buffer_analysis.avg_hit_ratio < 90:
                awr_factors["buffer_cache_low"] = 1.0
            elif buffer_analysis.avg_hit_ratio < 85:
                awr_factors["buffer_cache_low"] = 1.5
            elif buffer_analysis.avg_hit_ratio < 80:
                awr_factors["buffer_cache_low"] = 2.0
        
        # LGWR I/O 부하
        io_analysis = []
        if self._is_awr and hasattr(self.awr_data, 'iostat_functions') and self.awr_data.iostat_functions:
            io_analysis = self._analyze_io_functions()
            for func_analysis in io_analysis:
                if func_analysis.function_name == "LGWR":
                    if func_analysis.avg_mb_per_s > 10:
                        awr_factors["lgwr_io_high"] = 0.5
                    if func_analysis.avg_mb_per_s > 50:
                        awr_factors["lgwr_io_high"] = 1.0
                    if func_analysis.avg_mb_per_s > 100:
                        awr_factors["lgwr_io_high"] = 1.5
        
        # 워크로드 패턴
        workload_pattern = None
        if self._is_awr and hasattr(self.awr_data, 'workload_profiles') and self.awr_data.workload_profiles:
            workload_pattern = self._analyze_workload_pattern()
        
        # 총 점수 계산
        total_score = base_complexity.score + sum(awr_factors.values())
        total_score = min(total_score, 10.0)  # 최대 10점
        
        # 난이도 레벨 재계산
        if total_score <= 2.0:
            level = "매우 간단 (Minimal effort)"
        elif total_score <= 4.0:
            level = "간단 (Low effort)"
        elif total_score <= 6.0:
            level = "중간 (Moderate effort)"
        elif total_score <= 8.0:
            level = "복잡 (High effort)"
        else:
            level = "매우 복잡 (Very high effort)"
        
        # 인스턴스 추천 (백분위수 기반)
        instance_recommendation = None
        if self._is_awr:
            instance_recommendation = self._recommend_instance_with_percentiles(target, total_score)
        else:
            instance_recommendation = base_complexity.instance_recommendation
        
        # EnhancedMigrationComplexity 생성
        return EnhancedMigrationComplexity(
            target=target,
            score=total_score,
            level=level,
            factors={**base_complexity.factors, **awr_factors},
            recommendations=base_complexity.recommendations,
            warnings=base_complexity.warnings,
            next_steps=base_complexity.next_steps,
            instance_recommendation=instance_recommendation,
            workload_pattern=workload_pattern,
            buffer_cache_analysis=buffer_analysis,
            io_function_analysis=io_analysis,
            percentile_based=self._is_awr,
            confidence_level="High" if self._is_awr else "Medium"
        )
    
    def _analyze_workload_pattern(self):
        """
        워크로드 패턴 분석
        
        Returns:
            WorkloadPattern: 워크로드 패턴 분석 결과
        """
        from ..data_models import WorkloadPattern
        
        # 기본값
        cpu_pct = 0.0
        io_pct = 0.0
        peak_hours = []
        main_modules = []
        main_events = []
        
        # 워크로드 프로파일이 있는 경우
        if hasattr(self.awr_data, 'workload_profiles') and self.awr_data.workload_profiles:
            # 이벤트별 DB Time 집계
            event_totals = {}
            module_totals = {}
            hour_totals = {}
            
            for profile in self.awr_data.workload_profiles:
                # 유휴 이벤트 제외
                if "IDLE" in profile.event.upper():
                    continue
                
                # 이벤트별 집계
                event_name = profile.event
                if event_name not in event_totals:
                    event_totals[event_name] = 0
                event_totals[event_name] += profile.total_dbtime_sum
                
                # 모듈별 집계
                module_name = profile.module
                if module_name not in module_totals:
                    module_totals[module_name] = 0
                module_totals[module_name] += profile.total_dbtime_sum
                
                # 시간대별 집계
                try:
                    hour = profile.sample_start.split()[1].split(':')[0]
                    if hour not in hour_totals:
                        hour_totals[hour] = 0
                    hour_totals[hour] += profile.total_dbtime_sum
                except:
                    pass
            
            # 총 DB Time 계산
            total_dbtime = sum(event_totals.values())
            
            if total_dbtime > 0:
                # CPU vs I/O 비율 계산
                cpu_time = sum(v for k, v in event_totals.items() if "CPU" in k.upper())
                io_time = sum(v for k, v in event_totals.items() if "I/O" in k.upper())
                
                cpu_pct = (cpu_time / total_dbtime) * 100
                io_pct = (io_time / total_dbtime) * 100
                
                # 상위 이벤트
                sorted_events = sorted(event_totals.items(), key=lambda x: x[1], reverse=True)
                main_events = [e[0] for e in sorted_events[:5]]
                
                # 상위 모듈
                sorted_modules = sorted(module_totals.items(), key=lambda x: x[1], reverse=True)
                main_modules = [m[0] for m in sorted_modules[:5]]
                
                # 피크 시간대 (상위 3개)
                sorted_hours = sorted(hour_totals.items(), key=lambda x: x[1], reverse=True)
                peak_hours = [f"{h[0]}:00" for h in sorted_hours[:3]]
        
        # 패턴 타입 결정
        pattern_type = "Mixed"
        if cpu_pct > 50:
            pattern_type = "CPU-intensive"
        elif io_pct > 50:
            pattern_type = "IO-intensive"
        
        # 대화형 vs 배치형 판단
        if main_modules:
            interactive_modules = ["SQL*Plus", "JDBC Thin Client", "sqlplus"]
            batch_modules = ["SQL Loader", "Data Pump"]
            
            is_interactive = any(im in str(main_modules) for im in interactive_modules)
            is_batch = any(bm in str(main_modules) for bm in batch_modules)
            
            if is_interactive:
                pattern_type = "Interactive"
            elif is_batch:
                pattern_type = "Batch"
        
        return WorkloadPattern(
            pattern_type=pattern_type,
            cpu_pct=cpu_pct,
            io_pct=io_pct,
            peak_hours=peak_hours,
            main_modules=main_modules,
            main_events=main_events
        )
    
    def _analyze_buffer_cache(self):
        """
        버퍼 캐시 효율성 분석
        
        Returns:
            BufferCacheAnalysis: 버퍼 캐시 분석 결과
        """
        from ..data_models import BufferCacheAnalysis
        
        if not hasattr(self.awr_data, 'buffer_cache_stats') or not self.awr_data.buffer_cache_stats:
            return BufferCacheAnalysis(
                avg_hit_ratio=0.0,
                min_hit_ratio=0.0,
                max_hit_ratio=0.0,
                current_size_gb=0.0,
                recommended_size_gb=0.0,
                optimization_needed=False,
                recommendations=[]
            )
        
        # 히트율 통계 계산
        hit_ratios = [stat.hit_ratio for stat in self.awr_data.buffer_cache_stats if stat.hit_ratio is not None]
        cache_sizes = [stat.db_cache_gb for stat in self.awr_data.buffer_cache_stats if stat.db_cache_gb is not None]
        
        if not hit_ratios:
            return BufferCacheAnalysis(
                avg_hit_ratio=0.0,
                min_hit_ratio=0.0,
                max_hit_ratio=0.0,
                current_size_gb=0.0,
                recommended_size_gb=0.0,
                optimization_needed=False,
                recommendations=[]
            )
        
        avg_hit_ratio = statistics.mean(hit_ratios)
        min_hit_ratio = min(hit_ratios)
        max_hit_ratio = max(hit_ratios)
        current_size_gb = statistics.mean(cache_sizes) if cache_sizes else 0.0
        
        # 권장 크기 계산
        recommended_size_gb = current_size_gb
        optimization_needed = False
        recommendations = []
        
        if avg_hit_ratio < 80:
            recommended_size_gb = current_size_gb * 2.5
            optimization_needed = True
            recommendations.append(f"버퍼 캐시 히트율이 매우 낮습니다 ({avg_hit_ratio:.1f}%). 현재 크기의 2.5배로 증가를 권장합니다.")
            recommendations.append("인덱스 최적화 및 쿼리 튜닝도 함께 고려하세요.")
        elif avg_hit_ratio < 85:
            recommended_size_gb = current_size_gb * 2.0
            optimization_needed = True
            recommendations.append(f"버퍼 캐시 히트율이 낮습니다 ({avg_hit_ratio:.1f}%). 현재 크기의 2배로 증가를 권장합니다.")
        elif avg_hit_ratio < 90:
            recommended_size_gb = current_size_gb * 1.5
            optimization_needed = True
            recommendations.append(f"버퍼 캐시 히트율 개선이 필요합니다 ({avg_hit_ratio:.1f}%). 현재 크기의 1.5배로 증가를 권장합니다.")
        elif avg_hit_ratio > 99.5:
            recommended_size_gb = current_size_gb * 0.8
            recommendations.append(f"버퍼 캐시 히트율이 매우 높습니다 ({avg_hit_ratio:.1f}%). 크기를 줄여도 성능에 영향이 적을 수 있습니다.")
        else:
            recommendations.append(f"버퍼 캐시가 효율적으로 동작하고 있습니다 ({avg_hit_ratio:.1f}%).")
        
        return BufferCacheAnalysis(
            avg_hit_ratio=avg_hit_ratio,
            min_hit_ratio=min_hit_ratio,
            max_hit_ratio=max_hit_ratio,
            current_size_gb=current_size_gb,
            recommended_size_gb=recommended_size_gb,
            optimization_needed=optimization_needed,
            recommendations=recommendations
        )
    
    def _analyze_io_functions(self):
        """
        I/O 함수별 분석
        
        Returns:
            List[IOFunctionAnalysis]: I/O 함수별 분석 결과 목록
        """
        from ..data_models import IOFunctionAnalysis
        
        if not hasattr(self.awr_data, 'iostat_functions') or not self.awr_data.iostat_functions:
            return []
        
        # 함수별 I/O 통계 집계
        function_stats = {}
        
        for iostat in self.awr_data.iostat_functions:
            func_name = iostat.function_name
            mb_per_s = iostat.megabytes_per_s
            
            if func_name not in function_stats:
                function_stats[func_name] = []
            function_stats[func_name].append(mb_per_s)
        
        # 총 I/O 계산
        total_io = sum(sum(values) for values in function_stats.values())
        
        # 함수별 분석 결과 생성
        results = []
        
        for func_name, values in function_stats.items():
            avg_mb_per_s = statistics.mean(values)
            max_mb_per_s = max(values)
            pct_of_total = (sum(values) / total_io * 100) if total_io > 0 else 0.0
            
            # 병목 여부 판단
            is_bottleneck = False
            recommendations = []
            
            if func_name == "LGWR":
                if avg_mb_per_s > 100:
                    is_bottleneck = True
                    recommendations.append("LGWR I/O가 매우 높습니다. 로그 파일을 빠른 스토리지로 이동하세요.")
                    recommendations.append("커밋 빈도를 최적화하거나 배치 커밋을 고려하세요.")
                    recommendations.append("Aurora의 경우 스토리지 아키텍처가 자동으로 최적화됩니다.")
                elif avg_mb_per_s > 50:
                    recommendations.append("LGWR I/O가 높습니다. 로그 쓰기 최적화를 고려하세요.")
                elif avg_mb_per_s > 10:
                    recommendations.append("LGWR I/O를 모니터링하세요.")
            
            elif func_name == "DBWR":
                if avg_mb_per_s > 100:
                    is_bottleneck = True
                    recommendations.append("DBWR I/O가 매우 높습니다. 버퍼 캐시 크기를 증가시키세요.")
                    recommendations.append("체크포인트 간격을 조정하세요.")
                elif avg_mb_per_s > 50:
                    recommendations.append("DBWR I/O가 높습니다. 버퍼 캐시 최적화를 고려하세요.")
            
            elif "Direct" in func_name:
                if avg_mb_per_s > 100:
                    is_bottleneck = True
                    recommendations.append("Direct I/O가 매우 높습니다. 병렬 쿼리 최적화를 고려하세요.")
                    recommendations.append("임시 테이블스페이스 크기를 조정하세요.")
                elif avg_mb_per_s > 50:
                    recommendations.append("Direct I/O가 높습니다. 정렬 작업 최적화를 고려하세요.")
            
            results.append(IOFunctionAnalysis(
                function_name=func_name,
                avg_mb_per_s=avg_mb_per_s,
                max_mb_per_s=max_mb_per_s,
                pct_of_total=pct_of_total,
                is_bottleneck=is_bottleneck,
                recommendations=recommendations
            ))
        
        # I/O 비율 기준으로 정렬
        results.sort(key=lambda x: x.pct_of_total, reverse=True)
        
        return results
    
    def _analyze_time_based_patterns(self):
        """
        시간대별 리소스 사용 패턴 분석
        
        Returns:
            Dict[str, Any]: 시간대별 패턴 분석 결과
        """
        result = {
            "peak_hours": [],
            "idle_hours": [],
            "peak_load": 0.0,
            "idle_load": 0.0
        }
        
        if not hasattr(self.awr_data, 'workload_profiles') or not self.awr_data.workload_profiles:
            return result
        
        # 시간대별 부하 집계
        hour_loads = {}
        
        for profile in self.awr_data.workload_profiles:
            # 유휴 이벤트 제외
            if "IDLE" in profile.event.upper():
                continue
            
            try:
                hour = profile.sample_start.split()[1].split(':')[0]
                if hour not in hour_loads:
                    hour_loads[hour] = 0
                hour_loads[hour] += profile.aas_comp
            except:
                pass
        
        if not hour_loads:
            return result
        
        # 평균 부하 계산
        avg_load = statistics.mean(hour_loads.values())
        
        # 피크 시간대 (평균의 1.5배 이상)
        peak_threshold = avg_load * 1.5
        peak_hours = [hour for hour, load in hour_loads.items() if load >= peak_threshold]
        
        # 유휴 시간대 (평균의 0.5배 이하)
        idle_threshold = avg_load * 0.5
        idle_hours = [hour for hour, load in hour_loads.items() if load <= idle_threshold]
        
        result["peak_hours"] = sorted(peak_hours)
        result["idle_hours"] = sorted(idle_hours)
        result["peak_load"] = max(hour_loads.values()) if hour_loads else 0.0
        result["idle_load"] = min(hour_loads.values()) if hour_loads else 0.0
        
        return result
    
    def _get_percentile_cpu(self, percentile: str = "99th_percentile") -> Optional[int]:
        """
        지정된 백분위수의 CPU 값 반환
        
        Args:
            percentile: 백분위수 메트릭 이름
            
        Returns:
            Optional[int]: CPU 값 또는 None
        """
        if not hasattr(self.awr_data, 'percentile_cpu') or not self.awr_data.percentile_cpu:
            return None
        
        if percentile in self.awr_data.percentile_cpu:
            return self.awr_data.percentile_cpu[percentile].on_cpu
        
        return None
    
    def _get_percentile_io(self, percentile: str = "99th_percentile") -> Optional[Dict[str, int]]:
        """
        지정된 백분위수의 I/O 값 반환
        
        Args:
            percentile: 백분위수 메트릭 이름
            
        Returns:
            Optional[Dict[str, int]]: I/O 값 딕셔너리 또는 None
        """
        if not hasattr(self.awr_data, 'percentile_io') or not self.awr_data.percentile_io:
            return None
        
        if percentile in self.awr_data.percentile_io:
            io_data = self.awr_data.percentile_io[percentile]
            return {
                "rw_iops": io_data.rw_iops,
                "r_iops": io_data.r_iops,
                "w_iops": io_data.w_iops,
                "rw_mbps": io_data.rw_mbps,
                "r_mbps": io_data.r_mbps,
                "w_mbps": io_data.w_mbps
            }
        
        return None
    
    def _recommend_instance_with_percentiles(self, target: TargetDatabase, complexity_score: float) -> Optional[InstanceRecommendation]:
        """
        백분위수 기반 인스턴스 사이징
        
        Args:
            target: 타겟 데이터베이스
            complexity_score: 마이그레이션 난이도 점수
            
        Returns:
            Optional[InstanceRecommendation]: 인스턴스 추천 정보 또는 None
        """
        from .instance_recommender import R6I_INSTANCES, select_instance_type
        
        # P99 CPU 사용
        p99_cpu = self._get_percentile_cpu("99th_percentile")
        if p99_cpu is None:
            # Fallback to average
            return super()._recommend_instance_size(target, complexity_score)
        
        # P99 I/O 사용
        p99_io = self._get_percentile_io("99th_percentile")
        
        # 버퍼 캐시 최적화 고려
        buffer_analysis = None
        if hasattr(self.awr_data, 'buffer_cache_stats') and self.awr_data.buffer_cache_stats:
            buffer_analysis = self._analyze_buffer_cache()
        
        memory_multiplier = 1.2  # 기본 20% 여유분
        if buffer_analysis and buffer_analysis.optimization_needed:
            memory_multiplier = buffer_analysis.recommended_size_gb / buffer_analysis.current_size_gb if buffer_analysis.current_size_gb > 0 else 1.2
        
        # 메모리 요구사항 계산
        current_memory = self.awr_data.os_info.physical_memory_gb or 0
        if self.awr_data.memory_metrics:
            avg_memory = statistics.mean(m.total_gb for m in self.awr_data.memory_metrics)
            current_memory = max(current_memory, avg_memory)
        
        required_memory_gb = int(current_memory * memory_multiplier)
        
        # CPU 요구사항 계산 (P99 + 30% 여유분)
        required_vcpu = int(p99_cpu * 1.3)
        
        # 최소값 설정
        required_vcpu = max(required_vcpu, 2)
        required_memory_gb = max(required_memory_gb, 16)
        
        # 인스턴스 선택
        instance_type = select_instance_type(required_vcpu, required_memory_gb)
        
        if instance_type:
            vcpu, memory_gib = R6I_INSTANCES[instance_type]
            return InstanceRecommendation(
                instance_type=instance_type,
                vcpu=vcpu,
                memory_gib=memory_gib,
                current_cpu_usage_pct=(p99_cpu / vcpu) * 100 if vcpu > 0 else 0,
                current_memory_gb=current_memory,
                cpu_headroom_pct=((vcpu - p99_cpu) / vcpu) * 100 if vcpu > 0 else 0,
                memory_headroom_pct=((memory_gib - current_memory) / memory_gib) * 100 if memory_gib > 0 else 0
            )
        
        return None
