"""
복잡도 계산 모듈

타겟 데이터베이스별 마이그레이션 복잡도를 계산합니다.
"""

from typing import Dict, Any, List
from ..models import StatspackData, TargetDatabase, MigrationComplexity, OracleEdition


def calculate_charset_complexity(
    charset: str,
    requires_conversion: bool
) -> float:
    """
    캐릭터셋 변환 복잡도 계산
    
    캐릭터셋 타입별 가중치를 적용하여 변환 복잡도를 계산합니다.
    
    Args:
        charset: 캐릭터셋 이름
        requires_conversion: 변환 필요 여부
    
    Returns:
        float: 캐릭터셋 변환 복잡도 점수 (0.0 ~ 2.5)
    """
    if not requires_conversion:
        return 0.0
    
    charset_upper = charset.upper()
    
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
    if charset_upper in single_byte_charsets:
        return 1.0
    elif charset_upper in multi_byte_charsets:
        return 2.0
    elif charset_upper in legacy_charsets:
        return 2.5
    else:
        # 알 수 없는 캐릭터셋은 중간 가중치
        return 1.5


def generate_charset_warnings(
    charset: str,
    requires_conversion: bool,
    disk_size_gb: float
) -> List[str]:
    """
    캐릭터셋 변환 경고 메시지 생성
    
    Args:
        charset: 캐릭터셋 이름
        requires_conversion: 변환 필요 여부
        disk_size_gb: 디스크 크기 (GB)
    
    Returns:
        List[str]: 경고 메시지 목록
    """
    warnings = []
    
    if not requires_conversion:
        return warnings
    
    warnings.append(f"현재 캐릭터셋 '{charset}'에서 AL32UTF8로 변환이 필요합니다.")
    warnings.append("데이터 백업은 필수입니다.")
    warnings.append("변환 전 테스트 환경에서 충분한 검증이 필요합니다.")
    warnings.append("애플리케이션의 캐릭터셋 설정을 확인하고 업데이트해야 합니다.")
    
    # 예상 변환 시간 계산 (대략적인 추정)
    if disk_size_gb > 0:
        # 가정: 100GB당 약 1시간 (실제로는 데이터 특성에 따라 다름)
        estimated_hours = disk_size_gb / 100
        warnings.append(f"예상 변환 시간: 약 {estimated_hours:.1f}시간 (데이터 크기 기준)")
    
    return warnings


def calculate_rds_oracle_complexity(
    data: StatspackData,
    edition: OracleEdition,
    is_rac: bool,
    charset: str,
    requires_charset_conversion: bool,
    charset_complexity: float,
    charset_warnings: List[str],
    instance_recommendation
) -> MigrationComplexity:
    """
    RDS for Oracle 마이그레이션 난이도 계산
    
    기본 점수 1.0에서 시작하여 다음 요소를 고려합니다:
    - 에디션 변경 가중치
    - RAC → Single Instance 가중치
    - 버전 업그레이드 가중치
    - 캐릭터셋 변환 가중치
    
    Args:
        data: Statspack 데이터
        edition: Oracle 에디션
        is_rac: RAC 환경 여부
        charset: 캐릭터셋
        requires_charset_conversion: 캐릭터셋 변환 필요 여부
        charset_complexity: 캐릭터셋 복잡도
        charset_warnings: 캐릭터셋 경고 메시지
        instance_recommendation: 인스턴스 추천 정보
    
    Returns:
        MigrationComplexity: RDS for Oracle 마이그레이션 난이도
    """
    factors: Dict[str, float] = {}
    score = 1.0  # 기본 점수 (동일 엔진)
    factors["기본 점수 (동일 엔진)"] = 1.0
    
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
    if is_rac:
        rac_weight = 2.0
        factors["RAC → Single Instance 전환"] = rac_weight
        score += rac_weight
    
    # 버전 업그레이드 가중치
    version = data.os_info.version
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
    if charset_complexity > 0:
        factors["캐릭터셋 변환"] = charset_complexity
        score += charset_complexity
    
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
    
    if is_rac:
        recommendations.append("RAC 환경을 Multi-AZ 배포로 전환하여 고가용성을 유지할 수 있습니다.")
    
    if version:
        recommendations.append(f"현재 버전 {version}에서 최신 버전으로 업그레이드를 권장합니다.")
    
    return MigrationComplexity(
        target=TargetDatabase.RDS_ORACLE,
        score=score,
        level=level,
        factors=factors,
        recommendations=recommendations,
        warnings=charset_warnings,
        next_steps=[
            "RDS for Oracle 인스턴스 사이즈 선택",
            "Multi-AZ 배포 구성 계획",
            "백업 및 복구 전략 수립",
            "마이그레이션 도구 선택 (DMS, Data Pump 등)",
            "테스트 환경에서 마이그레이션 검증"
        ],
        instance_recommendation=instance_recommendation
    )


def calculate_aurora_postgresql_complexity(
    data: StatspackData,
    plsql_analysis: Dict[str, Any],
    feature_analysis: Dict[str, Any],
    resource_analysis: Dict[str, Any],
    wait_analysis: Dict[str, Any],
    charset_complexity: float,
    charset_warnings: List[str],
    instance_recommendation
) -> MigrationComplexity:
    """
    Aurora PostgreSQL 마이그레이션 난이도 계산
    
    기본 점수 3.0에서 시작하여 다음 요소를 고려합니다:
    - PL/SQL 코드 가중치
    - Oracle 특화 기능 가중치
    - 성능 최적화 가중치
    - 캐릭터셋 변환 가중치
    
    Args:
        data: Statspack 데이터
        plsql_analysis: PL/SQL 분석 결과
        feature_analysis: 기능 호환성 분석 결과
        resource_analysis: 리소스 사용량 분석 결과
        wait_analysis: 대기 이벤트 분석 결과
        charset_complexity: 캐릭터셋 복잡도
        charset_warnings: 캐릭터셋 경고 메시지
        instance_recommendation: 인스턴스 추천 정보
    
    Returns:
        MigrationComplexity: Aurora PostgreSQL 마이그레이션 난이도
    """
    factors: Dict[str, float] = {}
    score = 3.0  # 기본 점수 (엔진 변경)
    factors["기본 점수 (엔진 변경)"] = 3.0
    
    # PL/SQL 코드 복잡도
    plsql_score = plsql_analysis["complexity_score"]
    if plsql_score > 0:
        factors["PL/SQL 코드 변환"] = plsql_score
        score += plsql_score
    
    # Oracle 특화 기능 호환성
    feature_score = feature_analysis["compatibility_score"]
    if feature_score > 0:
        factors["Oracle 특화 기능"] = feature_score
        score += feature_score
    
    # 성능 최적화 가중치
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
    if charset_complexity > 0:
        factors["캐릭터셋 변환"] = charset_complexity
        score += charset_complexity
    
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
    
    return MigrationComplexity(
        target=TargetDatabase.AURORA_POSTGRESQL,
        score=score,
        level=level,
        factors=factors,
        recommendations=recommendations,
        warnings=charset_warnings,
        next_steps=[
            "AWS Schema Conversion Tool (SCT)로 스키마 변환",
            "PL/SQL을 PL/pgSQL로 변환",
            "AWS DMS로 데이터 마이그레이션",
            "애플리케이션 연결 문자열 업데이트",
            "성능 테스트 및 튜닝"
        ],
        instance_recommendation=instance_recommendation
    )


def calculate_aurora_mysql_complexity(
    data: StatspackData,
    plsql_analysis: Dict[str, Any],
    feature_analysis: Dict[str, Any],
    resource_analysis: Dict[str, Any],
    wait_analysis: Dict[str, Any],
    charset_complexity: float,
    charset_warnings: List[str],
    instance_recommendation
) -> MigrationComplexity:
    """
    Aurora MySQL 마이그레이션 난이도 계산
    
    기본 점수 4.0에서 시작하여 다음 요소를 고려합니다:
    - PL/SQL 코드 가중치 * 1.5 (PostgreSQL보다 어려움)
    - Oracle 특화 기능 가중치 * 1.3
    - 성능 최적화 가중치
    - 캐릭터셋 변환 가중치
    
    Args:
        data: Statspack 데이터
        plsql_analysis: PL/SQL 분석 결과
        feature_analysis: 기능 호환성 분석 결과
        resource_analysis: 리소스 사용량 분석 결과
        wait_analysis: 대기 이벤트 분석 결과
        charset_complexity: 캐릭터셋 복잡도
        charset_warnings: 캐릭터셋 경고 메시지
        instance_recommendation: 인스턴스 추천 정보
    
    Returns:
        MigrationComplexity: Aurora MySQL 마이그레이션 난이도
    """
    factors: Dict[str, float] = {}
    score = 4.0  # 기본 점수 (엔진 변경 + 제약 많음)
    factors["기본 점수 (엔진 변경 + 제약)"] = 4.0
    
    # PL/SQL 코드 복잡도 (PostgreSQL보다 1.5배 어려움)
    plsql_score = plsql_analysis["complexity_score"] * 1.5
    if plsql_score > 0:
        factors["PL/SQL 코드 변환 (MySQL 제약)"] = plsql_score
        score += plsql_score
    
    # Oracle 특화 기능 호환성 (1.3배 가중치)
    feature_score = feature_analysis["compatibility_score"] * 1.3
    if feature_score > 0:
        factors["Oracle 특화 기능 (MySQL 제약)"] = feature_score
        score += feature_score
    
    # 성능 최적화 가중치 (MySQL은 더 높은 가중치)
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
    if charset_complexity > 0:
        factors["캐릭터셋 변환"] = charset_complexity
        score += charset_complexity
    
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
    
    # MySQL 특화 경고 추가
    warnings = list(charset_warnings)
    if plsql_score > 3.0:
        warnings.append("대규모 PL/SQL 코드 변환은 MySQL에서 매우 어렵습니다. PostgreSQL을 고려하세요.")
    
    if feature_score > 5.0:
        warnings.append("많은 Oracle 특화 기능이 사용되고 있습니다. MySQL 호환성을 신중히 검토하세요.")
    
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
