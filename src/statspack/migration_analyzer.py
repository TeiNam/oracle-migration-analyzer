"""
마이그레이션 난이도 분석기

Statspack 데이터를 기반으로 타겟 데이터베이스별 마이그레이션 난이도를 분석합니다.
"""

from typing import Dict, Optional, Any, List
import statistics
from .data_models import (
    StatspackData,
    OracleEdition,
    TargetDatabase,
    MigrationComplexity,
    InstanceRecommendation
)
from .exceptions import MigrationAnalysisError
from .logging_config import get_logger

# 로거 초기화
logger = get_logger("migration_analyzer")


class MigrationAnalyzer:
    """마이그레이션 난이도 분석 엔진"""
    
    # r6i 인스턴스 패밀리 스펙 (vCPU, Memory GiB)
    R6I_INSTANCES = {
        "db.r6i.large": (2, 16),
        "db.r6i.xlarge": (4, 32),
        "db.r6i.2xlarge": (8, 64),
        "db.r6i.4xlarge": (16, 128),
        "db.r6i.8xlarge": (32, 256),
        "db.r6i.12xlarge": (48, 384),
        "db.r6i.16xlarge": (64, 512),
        "db.r6i.24xlarge": (96, 768),
        "db.r6i.32xlarge": (128, 1024),
    }
    
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
        
        charset = self.data.os_info.character_set
        self._character_set = charset if charset else ""
        
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
        
        charset = self._detect_character_set()
        if not charset:
            # 캐릭터셋 정보가 없으면 변환 불필요로 간주
            self._charset_conversion_required = False
        else:
            self._charset_conversion_required = charset.upper() != "AL32UTF8"
        
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
        result: Dict[str, Any] = {}
        
        # CPU 사용률 분석
        if self.data.main_metrics:
            cpu_values = [m.cpu_per_s for m in self.data.main_metrics if m.cpu_per_s is not None]
            if cpu_values:
                result["cpu_avg_pct"] = statistics.mean(cpu_values)
                # P99 계산 (99번째 백분위수)
                sorted_cpu = sorted(cpu_values)
                p99_index = int(len(sorted_cpu) * 0.99)
                result["cpu_p99_pct"] = sorted_cpu[min(p99_index, len(sorted_cpu) - 1)]
            else:
                result["cpu_avg_pct"] = 0.0
                result["cpu_p99_pct"] = 0.0
        else:
            result["cpu_avg_pct"] = 0.0
            result["cpu_p99_pct"] = 0.0
        
        # 메모리 사용량 분석
        if self.data.memory_metrics:
            memory_totals = [m.total_gb for m in self.data.memory_metrics if m.total_gb is not None]
            if memory_totals:
                result["memory_avg_gb"] = statistics.mean(memory_totals)
                result["memory_max_gb"] = max(memory_totals)
            else:
                result["memory_avg_gb"] = 0.0
                result["memory_max_gb"] = 0.0
        else:
            result["memory_avg_gb"] = 0.0
            result["memory_max_gb"] = 0.0
        
        # 디스크 크기 분석
        if self.data.disk_sizes:
            disk_sizes = [d.size_gb for d in self.data.disk_sizes if d.size_gb is not None]
            if disk_sizes:
                result["disk_size_gb"] = max(disk_sizes)
            else:
                result["disk_size_gb"] = 0.0
        else:
            result["disk_size_gb"] = 0.0
        
        # IOPS 분석
        if self.data.main_metrics:
            read_iops = [m.read_iops for m in self.data.main_metrics if m.read_iops is not None]
            write_iops = [m.write_iops for m in self.data.main_metrics if m.write_iops is not None]
            
            if read_iops:
                result["read_iops_avg"] = statistics.mean(read_iops)
            else:
                result["read_iops_avg"] = 0.0
            
            if write_iops:
                result["write_iops_avg"] = statistics.mean(write_iops)
            else:
                result["write_iops_avg"] = 0.0
            
            # 총 IOPS 계산
            if read_iops and write_iops:
                total_iops = [r + w for r, w in zip(read_iops, write_iops)]
                result["total_iops_avg"] = statistics.mean(total_iops)
                # P99 IOPS
                sorted_iops = sorted(total_iops)
                p99_index = int(len(sorted_iops) * 0.99)
                result["total_iops_p99"] = sorted_iops[min(p99_index, len(sorted_iops) - 1)]
            else:
                result["total_iops_avg"] = 0.0
                result["total_iops_p99"] = 0.0
        else:
            result["read_iops_avg"] = 0.0
            result["write_iops_avg"] = 0.0
            result["total_iops_avg"] = 0.0
            result["total_iops_p99"] = 0.0
        
        return result

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
        result: Dict[str, Any] = {
            "db_cpu_pct": 0.0,
            "user_io_pct": 0.0,
            "system_io_pct": 0.0,
            "commit_pct": 0.0,
            "network_pct": 0.0,
            "other_pct": 0.0,
            "top_events": [],
            "recommendations": []
        }
        
        if not self.data.wait_events:
            return result
        
        # 대기 이벤트 카테고리별 분류
        category_totals: Dict[str, float] = {
            "DB CPU": 0.0,
            "User I/O": 0.0,
            "System I/O": 0.0,
            "Commit": 0.0,
            "Network": 0.0,
            "Other": 0.0
        }
        
        total_time = 0.0
        
        for event in self.data.wait_events:
            wait_class = event.wait_class
            time_s = event.total_time_s if event.total_time_s else 0.0
            
            total_time += time_s
            
            # 카테고리별 분류
            if "CPU" in wait_class:
                category_totals["DB CPU"] += time_s
            elif "User I/O" in wait_class:
                category_totals["User I/O"] += time_s
            elif "System I/O" in wait_class:
                category_totals["System I/O"] += time_s
            elif "Commit" in wait_class:
                category_totals["Commit"] += time_s
            elif "Network" in wait_class:
                category_totals["Network"] += time_s
            else:
                category_totals["Other"] += time_s
        
        # 비율 계산
        if total_time > 0:
            result["db_cpu_pct"] = (category_totals["DB CPU"] / total_time) * 100
            result["user_io_pct"] = (category_totals["User I/O"] / total_time) * 100
            result["system_io_pct"] = (category_totals["System I/O"] / total_time) * 100
            result["commit_pct"] = (category_totals["Commit"] / total_time) * 100
            result["network_pct"] = (category_totals["Network"] / total_time) * 100
            result["other_pct"] = (category_totals["Other"] / total_time) * 100
        
        # 상위 이벤트 추출 (시간 기준 상위 10개)
        sorted_events = sorted(
            self.data.wait_events,
            key=lambda e: e.total_time_s if e.total_time_s else 0.0,
            reverse=True
        )
        result["top_events"] = [
            {
                "event_name": e.event_name,
                "wait_class": e.wait_class,
                "total_time_s": e.total_time_s,
                "pctdbt": e.pctdbt
            }
            for e in sorted_events[:10]
        ]
        
        # 최적화 권장사항 생성
        recommendations = []
        
        if result["db_cpu_pct"] > 70:
            recommendations.append("DB CPU 사용률이 매우 높습니다. 쿼리 튜닝 및 인스턴스 크기 증가를 고려하세요.")
        elif result["db_cpu_pct"] > 50:
            recommendations.append("DB CPU 사용률이 높습니다. 쿼리 최적화를 권장합니다.")
        
        if result["user_io_pct"] > 40:
            recommendations.append("User I/O 대기가 높습니다. 인덱스 최적화, 파티셔닝, 스토리지 타입 업그레이드를 고려하세요.")
        
        if result["commit_pct"] > 20:
            recommendations.append("Commit 대기가 높습니다. 배치 커밋 또는 비동기 커밋을 고려하세요.")
        
        # control file 관련 대기 이벤트 확인
        control_file_events = [
            e for e in self.data.wait_events
            if "control file" in e.event_name.lower()
        ]
        if control_file_events:
            recommendations.append("Control file 관련 대기가 감지되었습니다. Aurora/RDS 환경에서는 자동으로 개선됩니다.")
        
        result["recommendations"] = recommendations
        
        return result

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
        result: Dict[str, Any] = {
            "used_features": [],
            "compatibility_score": 0.0,
            "incompatible_features": [],
            "alternatives": []
        }
        
        if not self.data.features:
            return result
        
        # 사용 중인 기능 필터링 (currently_used=True)
        used_features = [f for f in self.data.features if f.currently_used]
        result["used_features"] = [f.name for f in used_features]
        
        # 기능별 가중치 (마이그레이션 난이도)
        feature_weights = {
            "Partitioning": 1.0,
            "Advanced Compression": 0.5,
            "Real Application Clusters": 2.0,
            "Data Guard": 1.5,
            "Active Data Guard": 1.5,
            "Materialized View": 1.0,
            "Advanced Security": 1.0,
            "Label Security": 1.5,
            "Database Vault": 1.5,
            "OLAP": 2.0,
            "Spatial": 1.5,
        }
        
        total_weight = 0.0
        incompatible_features = []
        alternatives = []
        
        for feature in used_features:
            feature_name = feature.name
            
            # 기능별 가중치 적용
            weight = 0.0
            for key, value in feature_weights.items():
                if key.lower() in feature_name.lower():
                    weight = value
                    break
            
            if weight == 0.0:
                # 알 수 없는 기능은 기본 가중치 0.3
                weight = 0.3
            
            total_weight += weight
            
            # 타겟별 호환성 평가
            if target == TargetDatabase.RDS_ORACLE:
                # RDS for Oracle은 대부분 호환 (EE 라이선스 필요)
                if "Real Application Clusters" in feature_name:
                    incompatible_features.append(feature_name)
                    alternatives.append(f"{feature_name}: Multi-AZ 배포로 대체")
            
            elif target == TargetDatabase.AURORA_POSTGRESQL:
                # Aurora PostgreSQL 호환성 평가
                if "Partitioning" in feature_name:
                    alternatives.append(f"{feature_name}: 네이티브 파티셔닝 지원")
                elif "Advanced Compression" in feature_name:
                    alternatives.append(f"{feature_name}: TOAST 압축 사용")
                elif "Real Application Clusters" in feature_name:
                    alternatives.append(f"{feature_name}: Multi-AZ 클러스터 (자동)")
                elif "Materialized View" in feature_name:
                    alternatives.append(f"{feature_name}: PostgreSQL Materialized View 사용")
                else:
                    incompatible_features.append(feature_name)
                    alternatives.append(f"{feature_name}: 애플리케이션 레벨에서 구현 필요")
            
            elif target == TargetDatabase.AURORA_MYSQL:
                # Aurora MySQL 호환성 평가 (더 제한적)
                if "Partitioning" in feature_name:
                    alternatives.append(f"{feature_name}: 네이티브 파티셔닝 지원 (제한적)")
                elif "Advanced Compression" in feature_name:
                    alternatives.append(f"{feature_name}: InnoDB 압축 사용")
                elif "Real Application Clusters" in feature_name:
                    alternatives.append(f"{feature_name}: Multi-AZ 클러스터 (자동)")
                else:
                    incompatible_features.append(feature_name)
                    alternatives.append(f"{feature_name}: 애플리케이션 레벨에서 구현 필요")
        
        result["compatibility_score"] = min(total_weight, 10.0)
        result["incompatible_features"] = incompatible_features
        result["alternatives"] = alternatives
        
        return result

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
        result: Dict[str, Any] = {
            "lines_of_code": 0,
            "package_count": 0,
            "procedure_count": 0,
            "function_count": 0,
            "complexity_score": 0.0,
            "conversion_strategy": []
        }
        
        # PL/SQL 코드 라인 수
        lines_of_code = self.data.os_info.count_lines_plsql or 0
        result["lines_of_code"] = lines_of_code
        
        # 패키지, 프로시저, 함수 수
        package_count = self.data.os_info.count_packages or 0
        procedure_count = self.data.os_info.count_procedures or 0
        function_count = self.data.os_info.count_functions or 0
        
        result["package_count"] = package_count
        result["procedure_count"] = procedure_count
        result["function_count"] = function_count
        
        # 복잡도 점수 계산
        complexity_score = 0.0
        
        # 코드 라인 수 기반 복잡도
        if lines_of_code == 0:
            complexity_score += 0.0
        elif lines_of_code < 1000:
            complexity_score += 0.5
        elif lines_of_code < 5000:
            complexity_score += 1.5
        elif lines_of_code < 10000:
            complexity_score += 3.0
        else:
            complexity_score += 5.0
        
        # 패키지 수 기반 복잡도
        if target == TargetDatabase.AURORA_POSTGRESQL:
            # PostgreSQL: 스키마 또는 확장으로 변환
            complexity_score += package_count * 1.0
        elif target == TargetDatabase.AURORA_MYSQL:
            # MySQL: 저장 프로시저로 변환 또는 애플리케이션 이관 (더 어려움)
            complexity_score += package_count * 2.0
        
        # 대규모 PL/SQL 변환 여부
        total_objects = procedure_count + package_count
        if total_objects > 10:
            complexity_score += 1.0
        
        result["complexity_score"] = min(complexity_score, 10.0)
        
        # 변환 전략 제공
        conversion_strategy = []
        
        if target == TargetDatabase.RDS_ORACLE:
            conversion_strategy.append("PL/SQL 코드는 그대로 사용 가능합니다.")
        
        elif target == TargetDatabase.AURORA_POSTGRESQL:
            if lines_of_code > 0:
                conversion_strategy.append("PL/SQL을 PL/pgSQL로 변환해야 합니다.")
            if package_count > 0:
                conversion_strategy.append(f"{package_count}개의 패키지를 PostgreSQL 스키마 또는 확장으로 변환해야 합니다.")
            if procedure_count > 0 or function_count > 0:
                conversion_strategy.append("프로시저와 함수를 PostgreSQL 함수로 변환해야 합니다.")
        
        elif target == TargetDatabase.AURORA_MYSQL:
            if lines_of_code > 0:
                conversion_strategy.append("PL/SQL을 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.")
            if package_count > 0:
                conversion_strategy.append(f"{package_count}개의 패키지를 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.")
            if procedure_count > 0 or function_count > 0:
                conversion_strategy.append("프로시저와 함수를 MySQL 저장 프로시저로 변환해야 합니다.")
        
        result["conversion_strategy"] = conversion_strategy
        
        return result

    def _calculate_charset_complexity(self) -> float:
        """
        캐릭터셋 변환 복잡도 계산
        
        캐릭터셋 타입별 가중치를 적용하여 변환 복잡도를 계산합니다.
        
        Returns:
            float: 캐릭터셋 변환 복잡도 점수 (0.0 ~ 2.5)
        """
        if not self._requires_charset_conversion():
            return 0.0
        
        charset = self._detect_character_set().upper()
        
        # 단일 바이트 캐릭터셋
        single_byte_charsets = [
            "US7ASCII",
            "WE8ISO8859P1",
            "WE8ISO8859P15",
            "WE8MSWIN1252",
        ]
        
        # 멀티 바이트 캐릭터셋
        multi_byte_charsets = [
            "KO16MSWIN949",
            "JA16SJIS",
            "JA16EUC",
            "ZHS16GBK",
            "ZHT16HKSCS",
        ]
        
        # 레거시 캐릭터셋
        legacy_charsets = [
            "KO16KSC5601",
            "JA16SJIS",
            "ZHS16CGB231280",
        ]
        
        # 가중치 계산
        if charset in single_byte_charsets:
            return 1.0
        elif charset in multi_byte_charsets:
            return 2.0
        elif charset in legacy_charsets:
            return 2.5
        else:
            # 알 수 없는 캐릭터셋은 중간 가중치
            return 1.5
    
    def _generate_charset_warnings(self) -> List[str]:
        """
        캐릭터셋 변환 경고 메시지 생성
        
        Returns:
            List[str]: 경고 메시지 목록
        """
        warnings = []
        
        if not self._requires_charset_conversion():
            return warnings
        
        charset = self._detect_character_set()
        disk_size = self.data.os_info.total_db_size_gb or 0.0
        
        warnings.append(f"현재 캐릭터셋 '{charset}'에서 AL32UTF8로 변환이 필요합니다.")
        warnings.append("데이터 백업은 필수입니다.")
        warnings.append("변환 전 테스트 환경에서 충분한 검증이 필요합니다.")
        warnings.append("애플리케이션의 캐릭터셋 설정을 확인하고 업데이트해야 합니다.")
        
        # 예상 변환 시간 계산 (대략적인 추정)
        if disk_size > 0:
            # 가정: 100GB당 약 1시간 (실제로는 데이터 특성에 따라 다름)
            estimated_hours = disk_size / 100
            warnings.append(f"예상 변환 시간: 약 {estimated_hours:.1f}시간 (데이터 크기 기준)")
        
        return warnings

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
        factors: Dict[str, float] = {}
        score = 1.0  # 기본 점수 (동일 엔진)
        factors["기본 점수 (동일 엔진)"] = 1.0
        
        # Oracle 에디션 감지
        edition = self._detect_oracle_edition()
        
        # 에디션 변경 가중치
        if edition == OracleEdition.STANDARD:
            # SE → SE2 마이그레이션
            edition_weight = 0.5
            factors["에디션 변경 (SE → SE2)"] = edition_weight
            score += edition_weight
        elif edition == OracleEdition.ENTERPRISE:
            # EE → SE2 마이그레이션 (기능 제약)
            edition_weight = 3.0
            factors["에디션 변경 (EE → SE2, 기능 제약)"] = edition_weight
            score += edition_weight
        
        # RAC → Single Instance 가중치
        if self._detect_rac():
            rac_weight = 2.0
            factors["RAC → Single Instance 전환"] = rac_weight
            score += rac_weight
        
        # 버전 업그레이드 가중치
        # VERSION 정보에서 메이저 버전 추출
        version = self.data.os_info.version
        if version:
            try:
                # 버전 형식: "11.2.0.4.0" 또는 "12.1.0.2.0"
                major_version = int(version.split('.')[0])
                # 현재 RDS for Oracle 최신 버전은 19c
                target_version = 19
                version_diff = target_version - major_version
                
                if version_diff > 0:
                    version_weight = version_diff * 0.5
                    factors[f"버전 업그레이드 ({major_version} → {target_version})"] = version_weight
                    score += version_weight
            except (ValueError, IndexError):
                # 버전 파싱 실패 시 무시
                pass
        
        # 캐릭터셋 변환 가중치
        charset_weight = self._calculate_charset_complexity()
        if charset_weight > 0:
            factors["캐릭터셋 변환"] = charset_weight
            score += charset_weight
        
        # 최대 점수 제한
        score = min(score, 10.0)
        
        # 난이도 레벨 결정
        if score <= 2.0:
            level = "매우 간단 (Minimal effort)"
        elif score <= 4.0:
            level = "간단 (Low effort)"
        elif score <= 6.0:
            level = "중간 (Moderate effort)"
        elif score <= 8.0:
            level = "복잡 (High effort)"
        else:
            level = "매우 복잡 (Very high effort)"
        
        # 권장사항 생성
        recommendations = []
        recommendations.append("RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.")
        
        if edition == OracleEdition.ENTERPRISE:
            recommendations.append("Enterprise Edition 기능을 Standard Edition 2에서 지원하는지 확인이 필요합니다.")
        
        if self._detect_rac():
            recommendations.append("RAC 환경을 Multi-AZ 배포로 전환하여 고가용성을 유지할 수 있습니다.")
        
        if version:
            recommendations.append(f"현재 버전 {version}에서 최신 버전으로 업그레이드를 권장합니다.")
        
        # 캐릭터셋 변환 경고
        warnings = self._generate_charset_warnings()
        
        # 인스턴스 추천
        instance_recommendation = self._recommend_instance_size(TargetDatabase.RDS_ORACLE, score)
        
        return MigrationComplexity(
            target=TargetDatabase.RDS_ORACLE,
            score=score,
            level=level,
            factors=factors,
            recommendations=recommendations,
            warnings=warnings,
            next_steps=[
                "RDS for Oracle 인스턴스 사이즈 선택",
                "Multi-AZ 배포 구성 계획",
                "백업 및 복구 전략 수립",
                "마이그레이션 도구 선택 (DMS, Data Pump 등)",
                "테스트 환경에서 마이그레이션 검증"
            ],
            instance_recommendation=instance_recommendation
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
        factors: Dict[str, float] = {}
        score = 3.0  # 기본 점수 (엔진 변경)
        factors["기본 점수 (엔진 변경)"] = 3.0
        
        # PL/SQL 코드 복잡도
        plsql_analysis = self._evaluate_plsql_complexity(TargetDatabase.AURORA_POSTGRESQL)
        plsql_score = plsql_analysis["complexity_score"]
        if plsql_score > 0:
            factors["PL/SQL 코드 변환"] = plsql_score
            score += plsql_score
        
        # Oracle 특화 기능 호환성
        feature_analysis = self._analyze_feature_compatibility(TargetDatabase.AURORA_POSTGRESQL)
        feature_score = feature_analysis["compatibility_score"]
        if feature_score > 0:
            factors["Oracle 특화 기능"] = feature_score
            score += feature_score
        
        # 성능 최적화 가중치
        resource_analysis = self._analyze_resource_usage()
        wait_analysis = self._analyze_wait_events()
        
        performance_score = 0.0
        
        # CPU 부하 기반
        cpu_avg = resource_analysis.get("cpu_avg_pct", 0.0)
        if cpu_avg > 70:
            performance_score += 2.0
            factors["높은 CPU 부하 (>70%)"] = 2.0
        elif cpu_avg > 50:
            performance_score += 1.0
            factors["중간 CPU 부하 (>50%)"] = 1.0
        
        # I/O 부하 기반
        user_io_pct = wait_analysis.get("user_io_pct", 0.0)
        if user_io_pct > 40:
            performance_score += 1.0
            factors["높은 I/O 대기 (>40%)"] = 1.0
        elif user_io_pct > 20:
            performance_score += 0.5
            factors["중간 I/O 대기 (>20%)"] = 0.5
        
        if performance_score > 0:
            score += performance_score
        
        # 캐릭터셋 변환 가중치
        charset_weight = self._calculate_charset_complexity()
        if charset_weight > 0:
            factors["캐릭터셋 변환"] = charset_weight
            score += charset_weight
        
        # 최대 점수 제한
        score = min(score, 10.0)
        
        # 난이도 레벨 결정
        if score <= 2.0:
            level = "매우 간단 (Minimal effort)"
        elif score <= 4.0:
            level = "간단 (Low effort)"
        elif score <= 6.0:
            level = "중간 (Moderate effort)"
        elif score <= 8.0:
            level = "복잡 (High effort)"
        else:
            level = "매우 복잡 (Very high effort)"
        
        # 권장사항 생성
        recommendations = []
        recommendations.append("Aurora PostgreSQL은 Oracle과 높은 호환성을 제공합니다.")
        
        if plsql_score > 0:
            recommendations.append("PL/SQL 코드를 PL/pgSQL로 변환해야 합니다.")
            recommendations.extend(plsql_analysis["conversion_strategy"])
        
        if feature_analysis["incompatible_features"]:
            recommendations.append("일부 Oracle 특화 기능은 대체 방안이 필요합니다:")
            recommendations.extend(feature_analysis["alternatives"])
        
        if cpu_avg > 70:
            recommendations.append("높은 CPU 부하: 쿼리 튜닝 및 인덱스 최적화가 필요합니다.")
        
        if user_io_pct > 40:
            recommendations.append("높은 I/O 대기: 스토리지 최적화 및 파티셔닝을 고려하세요.")
        
        # 캐릭터셋 변환 경고
        warnings = self._generate_charset_warnings()
        
        # 인스턴스 추천
        instance_recommendation = self._recommend_instance_size(TargetDatabase.AURORA_POSTGRESQL, score)
        
        return MigrationComplexity(
            target=TargetDatabase.AURORA_POSTGRESQL,
            score=score,
            level=level,
            factors=factors,
            recommendations=recommendations,
            warnings=warnings,
            next_steps=[
                "AWS Schema Conversion Tool (SCT)로 스키마 변환",
                "PL/SQL을 PL/pgSQL로 변환",
                "AWS DMS로 데이터 마이그레이션",
                "애플리케이션 연결 문자열 업데이트",
                "성능 테스트 및 튜닝"
            ],
            instance_recommendation=instance_recommendation
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
        factors: Dict[str, float] = {}
        score = 4.0  # 기본 점수 (엔진 변경 + 제약 많음)
        factors["기본 점수 (엔진 변경 + 제약)"] = 4.0
        
        # PL/SQL 코드 복잡도 (PostgreSQL보다 1.5배 어려움)
        plsql_analysis = self._evaluate_plsql_complexity(TargetDatabase.AURORA_MYSQL)
        plsql_score = plsql_analysis["complexity_score"] * 1.5
        if plsql_score > 0:
            factors["PL/SQL 코드 변환 (MySQL 제약)"] = plsql_score
            score += plsql_score
        
        # Oracle 특화 기능 호환성 (1.3배 가중치)
        feature_analysis = self._analyze_feature_compatibility(TargetDatabase.AURORA_MYSQL)
        feature_score = feature_analysis["compatibility_score"] * 1.3
        if feature_score > 0:
            factors["Oracle 특화 기능 (MySQL 제약)"] = feature_score
            score += feature_score
        
        # 성능 최적화 가중치 (MySQL은 더 높은 가중치)
        resource_analysis = self._analyze_resource_usage()
        wait_analysis = self._analyze_wait_events()
        
        performance_score = 0.0
        
        # CPU 부하 기반 (더 높은 가중치)
        cpu_avg = resource_analysis.get("cpu_avg_pct", 0.0)
        if cpu_avg > 70:
            performance_score += 3.0
            factors["높은 CPU 부하 (>70%)"] = 3.0
        elif cpu_avg > 50:
            performance_score += 1.5
            factors["중간 CPU 부하 (>50%)"] = 1.5
        
        # I/O 부하 기반 (더 높은 가중치)
        user_io_pct = wait_analysis.get("user_io_pct", 0.0)
        if user_io_pct > 40:
            performance_score += 1.5
            factors["높은 I/O 대기 (>40%)"] = 1.5
        elif user_io_pct > 20:
            performance_score += 1.0
            factors["중간 I/O 대기 (>20%)"] = 1.0
        
        if performance_score > 0:
            score += performance_score
        
        # 캐릭터셋 변환 가중치
        charset_weight = self._calculate_charset_complexity()
        if charset_weight > 0:
            factors["캐릭터셋 변환"] = charset_weight
            score += charset_weight
        
        # 최대 점수 제한
        score = min(score, 10.0)
        
        # 난이도 레벨 결정
        if score <= 2.0:
            level = "매우 간단 (Minimal effort)"
        elif score <= 4.0:
            level = "간단 (Low effort)"
        elif score <= 6.0:
            level = "중간 (Moderate effort)"
        elif score <= 8.0:
            level = "복잡 (High effort)"
        else:
            level = "매우 복잡 (Very high effort)"
        
        # 권장사항 생성
        recommendations = []
        recommendations.append("Aurora MySQL은 Oracle과의 호환성이 제한적입니다.")
        recommendations.append("대규모 PL/SQL 코드나 Oracle 특화 기능이 많은 경우 PostgreSQL을 권장합니다.")
        
        if plsql_score > 0:
            recommendations.append("PL/SQL 코드를 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.")
            recommendations.extend(plsql_analysis["conversion_strategy"])
        
        if feature_analysis["incompatible_features"]:
            recommendations.append("많은 Oracle 특화 기능이 MySQL에서 지원되지 않습니다:")
            recommendations.extend(feature_analysis["alternatives"])
        
        if cpu_avg > 70:
            recommendations.append("높은 CPU 부하: 쿼리 튜닝 및 인덱스 최적화가 필수입니다.")
        
        if user_io_pct > 40:
            recommendations.append("높은 I/O 대기: 스토리지 최적화 및 쿼리 개선이 필요합니다.")
        
        # 캐릭터셋 변환 경고
        warnings = self._generate_charset_warnings()
        
        # MySQL 특화 경고 추가
        if plsql_score > 3.0:
            warnings.append("대규모 PL/SQL 코드 변환은 MySQL에서 매우 어렵습니다. PostgreSQL을 고려하세요.")
        
        if feature_score > 5.0:
            warnings.append("많은 Oracle 특화 기능이 사용되고 있습니다. MySQL 호환성을 신중히 검토하세요.")
        
        # 인스턴스 추천
        instance_recommendation = self._recommend_instance_size(TargetDatabase.AURORA_MYSQL, score)
        
        return MigrationComplexity(
            target=TargetDatabase.AURORA_MYSQL,
            score=score,
            level=level,
            factors=factors,
            recommendations=recommendations,
            warnings=warnings,
            next_steps=[
                "AWS Schema Conversion Tool (SCT)로 스키마 변환 가능성 평가",
                "PL/SQL 코드를 MySQL 저장 프로시저 또는 애플리케이션으로 변환",
                "Oracle 특화 기능의 대체 방안 구현",
                "AWS DMS로 데이터 마이그레이션",
                "광범위한 애플리케이션 테스트 및 검증"
            ],
            instance_recommendation=instance_recommendation
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
        # 요구사항을 만족하는 인스턴스 필터링
        suitable_instances = []
        
        for instance_type, (vcpu, memory_gib) in self.R6I_INSTANCES.items():
            if vcpu >= required_vcpu and memory_gib >= required_memory_gb:
                suitable_instances.append((instance_type, vcpu, memory_gib))
        
        if not suitable_instances:
            # 요구사항을 만족하는 인스턴스가 없음
            return None
        
        # vCPU 기준으로 정렬하여 최소 인스턴스 선택
        suitable_instances.sort(key=lambda x: (x[1], x[2]))
        
        return suitable_instances[0][0]
    
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
        # 난이도 기반 타겟 필터링
        if complexity_score > 7.0:
            # 난이도가 높으면 RDS for Oracle만 추천
            if target != TargetDatabase.RDS_ORACLE:
                return None
        
        # 리소스 사용량 분석
        resource_analysis = self._analyze_resource_usage()
        
        # CPU 요구사항 계산 (P99 + 30% 여유분)
        cpu_p99_pct = resource_analysis.get("cpu_p99_pct", 0.0)
        
        # 현재 CPU 수
        num_cpus = self.data.os_info.num_cpus or self.data.os_info.num_cpu_cores or 2
        
        # 필요한 vCPU 계산
        # P99 사용률 기준으로 필요한 CPU 수 계산 후 30% 여유분 추가
        if cpu_p99_pct > 0:
            required_vcpu = int((num_cpus * (cpu_p99_pct / 100.0) * 1.3) + 0.5)
        else:
            required_vcpu = num_cpus
        
        # 최소 2 vCPU
        required_vcpu = max(required_vcpu, 2)
        
        # 메모리 요구사항 계산 (현재 + 20% 여유분)
        memory_avg_gb = resource_analysis.get("memory_avg_gb", 0.0)
        
        if memory_avg_gb > 0:
            required_memory_gb = int(memory_avg_gb * 1.2 + 0.5)
        else:
            # 메모리 정보가 없으면 물리 메모리 기준
            physical_memory_gb = self.data.os_info.physical_memory_gb or 16.0
            required_memory_gb = int(physical_memory_gb * 1.2 + 0.5)
        
        # 최소 16 GB
        required_memory_gb = max(required_memory_gb, 16)
        
        # 인스턴스 타입 선택
        instance_type = self._select_instance_type(required_vcpu, required_memory_gb)
        
        if not instance_type:
            # 요구사항을 만족하는 인스턴스가 없음
            return None
        
        # 선택된 인스턴스 스펙
        selected_vcpu, selected_memory_gib = self.R6I_INSTANCES[instance_type]
        
        # CPU 여유분 계산
        if cpu_p99_pct > 0:
            cpu_headroom_pct = ((selected_vcpu / num_cpus) - (cpu_p99_pct / 100.0)) * 100
        else:
            cpu_headroom_pct = 30.0  # 기본 여유분
        
        # 메모리 여유분 계산
        if memory_avg_gb > 0:
            memory_headroom_pct = ((selected_memory_gib - memory_avg_gb) / memory_avg_gb) * 100
        else:
            memory_headroom_pct = 20.0  # 기본 여유분
        
        return InstanceRecommendation(
            instance_type=instance_type,
            vcpu=selected_vcpu,
            memory_gib=selected_memory_gib,
            current_cpu_usage_pct=cpu_p99_pct,
            current_memory_gb=memory_avg_gb,
            cpu_headroom_pct=cpu_headroom_pct,
            memory_headroom_pct=memory_headroom_pct,
            estimated_monthly_cost_usd=None  # 비용 계산은 선택적
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
