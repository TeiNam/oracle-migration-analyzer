"""
마이그레이션 분석기 기본 모듈

MigrationAnalyzer 클래스를 포함합니다.
"""

from typing import Dict, Optional, Any, List
from ..models import (
    StatspackData,
    OracleEdition,
    TargetDatabase,
    MigrationComplexity,
    InstanceRecommendation
)
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
        # 약어 체크 (단어 경계 고려, 먼저 나오는 것 우선)
        else:
            # 단어로 분리하여 약어 확인 (먼저 나오는 약어 우선)
            words = banner_lower.split()
            edition_found = None
            for word in words:
                if word == "xe" and edition_found is None:
                    edition_found = OracleEdition.EXPRESS
                    break
                elif word == "se2" and edition_found is None:
                    edition_found = OracleEdition.STANDARD_2
                    break
                elif word == "ee" and edition_found is None:
                    edition_found = OracleEdition.ENTERPRISE
                    break
                elif word == "se" and edition_found is None:
                    edition_found = OracleEdition.STANDARD
                    break
            
            self._oracle_edition = edition_found if edition_found else OracleEdition.UNKNOWN
        
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
        """
        from .resource_analyzer import analyze_resource_usage
        return analyze_resource_usage(self.data)

    def _analyze_wait_events(self) -> Dict[str, Any]:
        """
        대기 이벤트 분석
        
        대기 이벤트를 카테고리별로 분류하고 분석합니다.
        
        Returns:
            Dict[str, Any]: 대기 이벤트 분석 결과
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
            Optional[str]: 선택된 인스턴스 타입 또는 None
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
        
        # SGA 권장사항
        sga_advice = self.data.sga_advice if self.data.sga_advice else None
        
        return recommend_instance_size(
            target,
            complexity_score,
            cpu_p99_pct,
            num_cpus,
            memory_avg_gb,
            physical_memory_gb,
            sga_advice
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
