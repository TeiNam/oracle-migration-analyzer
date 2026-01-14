"""
MigrationAnalyzer 속성 기반 테스트

Property-based testing을 사용하여 MigrationAnalyzer의 정확성을 검증합니다.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.statspack.data_models import (
    StatspackData,
    OSInformation,
    OracleEdition,
    MainMetric,
    MemoryMetric,
    TargetDatabase,
)
from src.statspack.migration_analyzer import MigrationAnalyzer


# 전략: Oracle 에디션 문자열 생성
@st.composite
def oracle_edition_banner(draw):
    """Oracle 에디션을 포함하는 BANNER 문자열 생성"""
    editions = [
        ("Enterprise Edition", OracleEdition.ENTERPRISE),
        ("Standard Edition 2", OracleEdition.STANDARD_2),
        ("Standard Edition", OracleEdition.STANDARD),
        ("Express Edition", OracleEdition.EXPRESS),
        ("EE", OracleEdition.ENTERPRISE),
        ("SE2", OracleEdition.STANDARD_2),
        ("SE", OracleEdition.STANDARD),
        ("XE", OracleEdition.EXPRESS),
    ]
    
    edition_str, expected_edition = draw(st.sampled_from(editions))
    
    # BANNER 문자열 생성 (에디션 문자열 포함)
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=0, max_size=20))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=0, max_size=20))
    
    banner = f"{prefix} {edition_str} {suffix}".strip()
    
    return banner, expected_edition


# 전략: 캐릭터셋 문자열 생성
@st.composite
def character_set_strategy(draw):
    """캐릭터셋 문자열 생성"""
    charsets = [
        "AL32UTF8",  # UTF-8 (변환 불필요)
        "US7ASCII",  # 단일 바이트
        "WE8ISO8859P1",  # 단일 바이트
        "KO16MSWIN949",  # 멀티 바이트
        "JA16SJIS",  # 멀티 바이트
        "KO16KSC5601",  # 레거시
        "UTF8",  # 구버전 UTF-8
    ]
    return draw(st.sampled_from(charsets))


# Feature: statspack-analyzer, Property 15: Oracle 에디션 감지
@given(oracle_edition_banner())
@settings(max_examples=100)
def test_property_oracle_edition_detection(banner_and_edition):
    """
    Property 15: Oracle 에디션 감지
    
    For any BANNER 문자열에 대해, "Standard Edition", "Standard Edition 2", 
    "Enterprise Edition", "Express Edition" 중 하나를 포함하면 
    해당 에디션으로 감지되어야 합니다.
    
    Validates: Requirements 18.1
    """
    banner, expected_edition = banner_and_edition
    
    # StatspackData 생성
    os_info = OSInformation(banner=banner)
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성 및 에디션 감지
    analyzer = MigrationAnalyzer(data)
    detected_edition = analyzer._detect_oracle_edition()
    
    # 검증: 감지된 에디션이 예상과 일치해야 함
    assert detected_edition == expected_edition, \
        f"BANNER '{banner}'에서 {expected_edition}을 감지해야 하지만 {detected_edition}이 감지됨"


# Feature: statspack-analyzer, Property 16: RAC 환경 감지
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_property_rac_detection(instances):
    """
    Property 16: RAC 환경 감지
    
    For any INSTANCES 값에 대해, 값이 1보다 크면 RAC 환경으로 감지되어야 합니다.
    
    Validates: Requirements 18.2
    """
    # StatspackData 생성
    os_info = OSInformation(instances=instances)
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성 및 RAC 감지
    analyzer = MigrationAnalyzer(data)
    is_rac = analyzer._detect_rac()
    
    # 검증: instances > 1이면 RAC, 그렇지 않으면 Single Instance
    expected_rac = instances > 1
    assert is_rac == expected_rac, \
        f"INSTANCES={instances}일 때 RAC={expected_rac}이어야 하지만 {is_rac}로 감지됨"


# Feature: statspack-analyzer, Property 17: 캐릭터셋 변환 필요성 감지
@given(character_set_strategy())
@settings(max_examples=100)
def test_property_charset_conversion_detection(charset):
    """
    Property 17: 캐릭터셋 변환 필요성 감지
    
    For any Character Set 값에 대해, 값이 "AL32UTF8"이 아니면 
    캐릭터셋 변환이 필요한 것으로 감지되어야 합니다.
    
    Validates: Requirements 25.2
    """
    # StatspackData 생성
    os_info = OSInformation(character_set=charset)
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성 및 변환 필요성 감지
    analyzer = MigrationAnalyzer(data)
    requires_conversion = analyzer._requires_charset_conversion()
    
    # 검증: AL32UTF8이 아니면 변환 필요
    expected_conversion = charset.upper() != "AL32UTF8"
    assert requires_conversion == expected_conversion, \
        f"Character Set '{charset}'일 때 변환 필요={expected_conversion}이어야 하지만 {requires_conversion}로 감지됨"


# 엣지 케이스: BANNER가 없는 경우
def test_oracle_edition_detection_no_banner():
    """BANNER가 없으면 UNKNOWN으로 감지"""
    os_info = OSInformation(banner=None)
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    edition = analyzer._detect_oracle_edition()
    
    assert edition == OracleEdition.UNKNOWN


# 엣지 케이스: INSTANCES가 없는 경우
def test_rac_detection_no_instances():
    """INSTANCES가 없으면 RAC가 아닌 것으로 감지"""
    os_info = OSInformation(instances=None)
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    is_rac = analyzer._detect_rac()
    
    assert is_rac is False


# 엣지 케이스: Character Set이 없는 경우
def test_charset_conversion_no_charset():
    """Character Set이 없으면 변환 불필요로 감지"""
    os_info = OSInformation(character_set=None)
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    requires_conversion = analyzer._requires_charset_conversion()
    
    assert requires_conversion is False


# 엣지 케이스: Character Set이 빈 문자열인 경우
def test_charset_conversion_empty_charset():
    """Character Set이 빈 문자열이면 변환 불필요로 감지"""
    os_info = OSInformation(character_set="")
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    requires_conversion = analyzer._requires_charset_conversion()
    
    assert requires_conversion is False



# Feature: statspack-analyzer, Property 18: 캐릭터셋 변환 난이도 가중치
@given(character_set_strategy())
@settings(max_examples=100)
def test_property_charset_complexity_weight(charset):
    """
    Property 18: 캐릭터셋 변환 난이도 가중치
    
    For any AL32UTF8이 아닌 캐릭터셋에 대해, 마이그레이션 난이도 계산 시 
    적절한 가중치(1.0~2.5점)가 추가되어야 합니다.
    
    Validates: Requirements 25.3
    """
    # StatspackData 생성
    os_info = OSInformation(character_set=charset)
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성 및 복잡도 계산
    analyzer = MigrationAnalyzer(data)
    complexity = analyzer._calculate_charset_complexity()
    
    # 검증: AL32UTF8이 아니면 가중치가 1.0~2.5 범위 내에 있어야 함
    if charset.upper() == "AL32UTF8":
        assert complexity == 0.0, \
            f"AL32UTF8은 변환 불필요하므로 복잡도가 0.0이어야 하지만 {complexity}로 계산됨"
    else:
        assert 1.0 <= complexity <= 2.5, \
            f"캐릭터셋 '{charset}' 변환 복잡도는 1.0~2.5 범위 내에 있어야 하지만 {complexity}로 계산됨"


# 엣지 케이스: 단일 바이트 캐릭터셋
def test_charset_complexity_single_byte():
    """단일 바이트 캐릭터셋은 1.0 가중치"""
    os_info = OSInformation(character_set="US7ASCII")
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    complexity = analyzer._calculate_charset_complexity()
    
    assert complexity == 1.0


# 엣지 케이스: 멀티 바이트 캐릭터셋
def test_charset_complexity_multi_byte():
    """멀티 바이트 캐릭터셋은 2.0 가중치"""
    os_info = OSInformation(character_set="KO16MSWIN949")
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    complexity = analyzer._calculate_charset_complexity()
    
    assert complexity == 2.0


# 엣지 케이스: 레거시 캐릭터셋
def test_charset_complexity_legacy():
    """레거시 캐릭터셋은 2.5 가중치"""
    os_info = OSInformation(character_set="KO16KSC5601")
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    complexity = analyzer._calculate_charset_complexity()
    
    assert complexity == 2.5


# 엣지 케이스: 캐릭터셋 변환 경고 메시지
def test_charset_warnings_generation():
    """캐릭터셋 변환이 필요하면 경고 메시지 생성"""
    os_info = OSInformation(
        character_set="KO16MSWIN949",
        total_db_size_gb=500.0
    )
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    warnings = analyzer._generate_charset_warnings()
    
    # 경고 메시지가 있어야 함
    assert len(warnings) > 0
    
    # 필수 경고 메시지 확인
    warning_text = " ".join(warnings)
    assert "AL32UTF8" in warning_text
    assert "백업" in warning_text
    assert "테스트" in warning_text


# Feature: statspack-analyzer, Property 13: 난이도 점수 범위
@given(
    st.builds(
        OSInformation,
        banner=st.one_of(
            st.just("Oracle Database 11g Enterprise Edition"),
            st.just("Oracle Database 12c Standard Edition 2"),
            st.just("Oracle Database 19c Express Edition"),
            st.none()
        ),
        instances=st.one_of(st.integers(min_value=1, max_value=4), st.none()),
        character_set=st.one_of(
            st.just("AL32UTF8"),
            st.just("KO16MSWIN949"),
            st.just("US7ASCII"),
            st.none()
        ),
        version=st.one_of(
            st.just("11.2.0.4.0"),
            st.just("12.1.0.2.0"),
            st.just("19.0.0.0.0"),
            st.none()
        ),
        count_lines_plsql=st.one_of(st.integers(min_value=0, max_value=20000), st.none()),
        count_packages=st.one_of(st.integers(min_value=0, max_value=50), st.none()),
    )
)
@settings(max_examples=100)
def test_property_complexity_score_range(os_info):
    """
    Property 13: 난이도 점수 범위
    
    For any 마이그레이션 난이도 계산 결과에 대해, 점수는 0-10 범위 내에 있어야 합니다.
    
    Validates: Requirements 17.3
    """
    # StatspackData 생성
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성
    analyzer = MigrationAnalyzer(data)
    
    # 각 타겟별 난이도 계산
    rds_oracle_complexity = analyzer._calculate_rds_oracle_complexity()
    aurora_pg_complexity = analyzer._calculate_aurora_postgresql_complexity()
    aurora_mysql_complexity = analyzer._calculate_aurora_mysql_complexity()
    
    # 검증: 모든 점수가 0-10 범위 내에 있어야 함
    assert 0.0 <= rds_oracle_complexity.score <= 10.0, \
        f"RDS Oracle 난이도 점수 {rds_oracle_complexity.score}는 0-10 범위를 벗어남"
    
    assert 0.0 <= aurora_pg_complexity.score <= 10.0, \
        f"Aurora PostgreSQL 난이도 점수 {aurora_pg_complexity.score}는 0-10 범위를 벗어남"
    
    assert 0.0 <= aurora_mysql_complexity.score <= 10.0, \
        f"Aurora MySQL 난이도 점수 {aurora_mysql_complexity.score}는 0-10 범위를 벗어남"


# Feature: statspack-analyzer, Property 14: 난이도 요인 제공
@given(
    st.builds(
        OSInformation,
        banner=st.one_of(
            st.just("Oracle Database 11g Enterprise Edition"),
            st.just("Oracle Database 12c Standard Edition"),
            st.none()
        ),
        instances=st.one_of(st.integers(min_value=1, max_value=4), st.none()),
        character_set=st.one_of(st.just("AL32UTF8"), st.just("KO16MSWIN949"), st.none()),
        count_lines_plsql=st.one_of(st.integers(min_value=0, max_value=10000), st.none()),
    )
)
@settings(max_examples=100)
def test_property_complexity_factors_provided(os_info):
    """
    Property 14: 난이도 요인 제공
    
    For any 마이그레이션 난이도 분석 결과에 대해, 
    난이도에 영향을 준 주요 요인 목록(factors)이 제공되어야 합니다.
    
    Validates: Requirements 17.5
    """
    # StatspackData 생성
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성
    analyzer = MigrationAnalyzer(data)
    
    # 각 타겟별 난이도 계산
    rds_oracle_complexity = analyzer._calculate_rds_oracle_complexity()
    aurora_pg_complexity = analyzer._calculate_aurora_postgresql_complexity()
    aurora_mysql_complexity = analyzer._calculate_aurora_mysql_complexity()
    
    # 검증: factors가 딕셔너리이고 비어있지 않아야 함
    assert isinstance(rds_oracle_complexity.factors, dict), \
        "RDS Oracle factors는 딕셔너리여야 함"
    assert len(rds_oracle_complexity.factors) > 0, \
        "RDS Oracle factors는 비어있지 않아야 함"
    
    assert isinstance(aurora_pg_complexity.factors, dict), \
        "Aurora PostgreSQL factors는 딕셔너리여야 함"
    assert len(aurora_pg_complexity.factors) > 0, \
        "Aurora PostgreSQL factors는 비어있지 않아야 함"
    
    assert isinstance(aurora_mysql_complexity.factors, dict), \
        "Aurora MySQL factors는 딕셔너리여야 함"
    assert len(aurora_mysql_complexity.factors) > 0, \
        "Aurora MySQL factors는 비어있지 않아야 함"
    
    # 검증: factors의 값들이 모두 숫자여야 함
    for factor_name, factor_value in rds_oracle_complexity.factors.items():
        assert isinstance(factor_value, (int, float)), \
            f"RDS Oracle factor '{factor_name}'의 값은 숫자여야 하지만 {type(factor_value)}임"
    
    for factor_name, factor_value in aurora_pg_complexity.factors.items():
        assert isinstance(factor_value, (int, float)), \
            f"Aurora PostgreSQL factor '{factor_name}'의 값은 숫자여야 하지만 {type(factor_value)}임"
    
    for factor_name, factor_value in aurora_mysql_complexity.factors.items():
        assert isinstance(factor_value, (int, float)), \
            f"Aurora MySQL factor '{factor_name}'의 값은 숫자여야 하지만 {type(factor_value)}임"
    
    # 검증: factors의 합이 대략 score와 일치하거나 score보다 클 수 있음 (최대 점수 제한)
    rds_factors_sum = sum(rds_oracle_complexity.factors.values())
    # score는 10.0으로 제한되므로 factors 합이 더 클 수 있음
    assert rds_factors_sum >= rds_oracle_complexity.score - 0.01, \
        f"RDS Oracle factors 합({rds_factors_sum})이 score({rds_oracle_complexity.score})보다 작음"
    
    aurora_pg_factors_sum = sum(aurora_pg_complexity.factors.values())
    assert aurora_pg_factors_sum >= aurora_pg_complexity.score - 0.01, \
        f"Aurora PostgreSQL factors 합({aurora_pg_factors_sum})이 score({aurora_pg_complexity.score})보다 작음"
    
    aurora_mysql_factors_sum = sum(aurora_mysql_complexity.factors.values())
    assert aurora_mysql_factors_sum >= aurora_mysql_complexity.score - 0.01, \
        f"Aurora MySQL factors 합({aurora_mysql_factors_sum})이 score({aurora_mysql_complexity.score})보다 작음"


# 엣지 케이스: 최소 데이터로 난이도 계산
def test_complexity_calculation_minimal_data():
    """최소 데이터로도 난이도 계산이 가능해야 함"""
    os_info = OSInformation()
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    
    # 각 타겟별 난이도 계산
    rds_complexity = analyzer._calculate_rds_oracle_complexity()
    pg_complexity = analyzer._calculate_aurora_postgresql_complexity()
    mysql_complexity = analyzer._calculate_aurora_mysql_complexity()
    
    # 모든 난이도가 유효한 범위 내에 있어야 함
    assert 0.0 <= rds_complexity.score <= 10.0
    assert 0.0 <= pg_complexity.score <= 10.0
    assert 0.0 <= mysql_complexity.score <= 10.0
    
    # factors가 제공되어야 함
    assert len(rds_complexity.factors) > 0
    assert len(pg_complexity.factors) > 0
    assert len(mysql_complexity.factors) > 0


# 엣지 케이스: 난이도 레벨 분류
def test_complexity_level_classification():
    """난이도 점수에 따라 올바른 레벨로 분류되어야 함"""
    # 실제 점수를 확인하여 레벨 검증
    test_cases = [
        (OSInformation(), "매우 간단"),  # 기본 점수 1.0
        (OSInformation(banner="Oracle Database 11g Standard Edition"), "간단"),  # 1.0 + 0.5 = 1.5
        (OSInformation(banner="Oracle Database 11g Enterprise Edition"), "간단"),  # 1.0 + 3.0 = 4.0
        (OSInformation(banner="Oracle Database 11g Enterprise Edition", instances=3), "중간"),  # 1.0 + 3.0 + 2.0 = 6.0
        (OSInformation(banner="Oracle Database 11g Enterprise Edition", instances=3, character_set="KO16MSWIN949"), "복잡"),  # 1.0 + 3.0 + 2.0 + 2.0 = 8.0
    ]
    
    for os_info, expected_level_prefix in test_cases:
        data = StatspackData(os_info=os_info)
        
        analyzer = MigrationAnalyzer(data)
        complexity = analyzer._calculate_rds_oracle_complexity()
        
        # 레벨이 예상 범위 내에 있는지 확인
        assert expected_level_prefix in complexity.level, \
            f"점수 {complexity.score}에 대해 레벨 '{complexity.level}'이 '{expected_level_prefix}'를 포함해야 함"




# Feature: statspack-analyzer, Property 19: 인스턴스 추천 리소스 만족
@given(
    st.builds(
        OSInformation,
        num_cpus=st.integers(min_value=2, max_value=64),
        physical_memory_gb=st.floats(min_value=16.0, max_value=1024.0),
    ),
    st.lists(
        st.builds(
            MainMetric,
            snap=st.integers(min_value=1, max_value=100),
            dur_m=st.floats(min_value=1.0, max_value=60.0),
            end=st.just("2024-01-01 00:00:00"),
            inst=st.just(1),
            cpu_per_s=st.floats(min_value=0.0, max_value=100.0),
            read_iops=st.floats(min_value=0.0, max_value=10000.0),
            read_mb_s=st.floats(min_value=0.0, max_value=1000.0),
            write_iops=st.floats(min_value=0.0, max_value=10000.0),
            write_mb_s=st.floats(min_value=0.0, max_value=1000.0),
            commits_s=st.floats(min_value=0.0, max_value=1000.0),
        ),
        min_size=1,
        max_size=10
    ),
    st.lists(
        st.builds(
            MemoryMetric,
            snap_id=st.integers(min_value=1, max_value=100),
            instance_number=st.just(1),
            sga_gb=st.floats(min_value=1.0, max_value=512.0),
            pga_gb=st.floats(min_value=1.0, max_value=256.0),
            total_gb=st.floats(min_value=2.0, max_value=768.0),
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_instance_recommendation_resource_satisfaction(os_info, main_metrics, memory_metrics):
    """
    Property 19: 인스턴스 추천 리소스 만족
    
    For any 추천된 RDS 인스턴스에 대해, 해당 인스턴스의 vCPU와 메모리는 
    요구사항(CPU P99 + 30%, 메모리 현재 + 20%)을 모두 만족해야 합니다.
    
    Validates: Requirements 26.1, 26.7
    """
    # StatspackData 생성
    data = StatspackData(
        os_info=os_info,
        main_metrics=main_metrics,
        memory_metrics=memory_metrics
    )
    
    # MigrationAnalyzer 생성
    analyzer = MigrationAnalyzer(data)
    
    # 리소스 분석
    resource_analysis = analyzer._analyze_resource_usage()
    cpu_p99_pct = resource_analysis.get("cpu_p99_pct", 0.0)
    memory_avg_gb = resource_analysis.get("memory_avg_gb", 0.0)
    
    # 각 타겟별 난이도 계산 및 인스턴스 추천
    rds_complexity = analyzer._calculate_rds_oracle_complexity()
    pg_complexity = analyzer._calculate_aurora_postgresql_complexity()
    mysql_complexity = analyzer._calculate_aurora_mysql_complexity()
    
    # 검증: 인스턴스 추천이 있으면 리소스 요구사항을 만족해야 함
    for complexity in [rds_complexity, pg_complexity, mysql_complexity]:
        if complexity.instance_recommendation is None:
            continue
        
        recommendation = complexity.instance_recommendation
        
        # CPU 요구사항 계산
        num_cpus = os_info.num_cpus or os_info.num_cpu_cores or 2
        if cpu_p99_pct > 0:
            required_vcpu = int((num_cpus * (cpu_p99_pct / 100.0) * 1.3) + 0.5)
        else:
            required_vcpu = num_cpus
        required_vcpu = max(required_vcpu, 2)
        
        # 메모리 요구사항 계산
        if memory_avg_gb > 0:
            required_memory_gb = int(memory_avg_gb * 1.2 + 0.5)
        else:
            physical_memory_gb = os_info.physical_memory_gb or 16.0
            required_memory_gb = int(physical_memory_gb * 1.2 + 0.5)
        required_memory_gb = max(required_memory_gb, 16)
        
        # 검증: 추천된 인스턴스가 요구사항을 만족해야 함
        assert recommendation.vcpu >= required_vcpu, \
            f"{complexity.target.value}: 추천 vCPU({recommendation.vcpu})가 요구사항({required_vcpu})보다 작음"
        
        assert recommendation.memory_gib >= required_memory_gb, \
            f"{complexity.target.value}: 추천 메모리({recommendation.memory_gib}GB)가 요구사항({required_memory_gb}GB)보다 작음"


# Feature: statspack-analyzer, Property 20: 난이도 기반 타겟 필터링
@given(
    st.builds(
        OSInformation,
        banner=st.just("Oracle Database 11g Enterprise Edition"),
        instances=st.integers(min_value=2, max_value=4),  # RAC
        character_set=st.just("KO16MSWIN949"),
        count_lines_plsql=st.integers(min_value=10000, max_value=20000),  # 대규모 PL/SQL
        count_packages=st.integers(min_value=20, max_value=50),
    )
)
@settings(max_examples=50)
def test_property_complexity_based_target_filtering(os_info):
    """
    Property 20: 난이도 기반 타겟 필터링
    
    For any 마이그레이션 난이도 점수에 대해, 점수가 7보다 크면 RDS for Oracle만 추천하고, 
    7 이하면 Aurora MySQL/PostgreSQL도 추천해야 합니다.
    
    Validates: Requirements 26.5, 26.6
    """
    # StatspackData 생성
    data = StatspackData(os_info=os_info)
    
    # MigrationAnalyzer 생성
    analyzer = MigrationAnalyzer(data)
    
    # 각 타겟별 난이도 계산
    rds_complexity = analyzer._calculate_rds_oracle_complexity()
    pg_complexity = analyzer._calculate_aurora_postgresql_complexity()
    mysql_complexity = analyzer._calculate_aurora_mysql_complexity()
    
    # 검증: 난이도가 7보다 크면 RDS for Oracle만 인스턴스 추천이 있어야 함
    if pg_complexity.score > 7.0:
        assert pg_complexity.instance_recommendation is None, \
            f"Aurora PostgreSQL 난이도({pg_complexity.score})가 7보다 크면 인스턴스 추천이 없어야 함"
    
    if mysql_complexity.score > 7.0:
        assert mysql_complexity.instance_recommendation is None, \
            f"Aurora MySQL 난이도({mysql_complexity.score})가 7보다 크면 인스턴스 추천이 없어야 함"
    
    # RDS for Oracle은 항상 인스턴스 추천이 있어야 함 (리소스 정보가 있는 경우)
    if os_info.num_cpus or os_info.physical_memory_gb:
        assert rds_complexity.instance_recommendation is not None, \
            "RDS for Oracle은 리소스 정보가 있으면 항상 인스턴스 추천이 있어야 함"


# 엣지 케이스: 최소 리소스로 인스턴스 추천
def test_instance_recommendation_minimal_resources():
    """최소 리소스로도 인스턴스 추천이 가능해야 함"""
    os_info = OSInformation(
        num_cpus=2,
        physical_memory_gb=16.0
    )
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    recommendation = analyzer._recommend_instance_size(TargetDatabase.RDS_ORACLE, 5.0)
    
    # 최소 인스턴스 추천 (2 vCPU, 16 GB 이상)
    assert recommendation is not None
    assert recommendation.vcpu >= 2
    assert recommendation.memory_gib >= 16


# 엣지 케이스: 높은 난이도에서 Aurora 필터링
def test_instance_recommendation_high_complexity_filtering():
    """난이도가 7보다 크면 Aurora는 인스턴스 추천이 없어야 함"""
    os_info = OSInformation(
        num_cpus=4,
        physical_memory_gb=32.0
    )
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    
    # 난이도 8.0으로 Aurora PostgreSQL 추천 시도
    pg_recommendation = analyzer._recommend_instance_size(TargetDatabase.AURORA_POSTGRESQL, 8.0)
    assert pg_recommendation is None, "난이도 8.0에서 Aurora PostgreSQL 추천이 없어야 함"
    
    # 난이도 8.0으로 Aurora MySQL 추천 시도
    mysql_recommendation = analyzer._recommend_instance_size(TargetDatabase.AURORA_MYSQL, 8.0)
    assert mysql_recommendation is None, "난이도 8.0에서 Aurora MySQL 추천이 없어야 함"
    
    # 난이도 8.0으로 RDS Oracle 추천 시도
    rds_recommendation = analyzer._recommend_instance_size(TargetDatabase.RDS_ORACLE, 8.0)
    assert rds_recommendation is not None, "난이도 8.0에서 RDS Oracle 추천이 있어야 함"


# 엣지 케이스: 인스턴스 타입 선택
def test_select_instance_type():
    """요구사항을 만족하는 최소 인스턴스를 선택해야 함"""
    os_info = OSInformation()
    data = StatspackData(os_info=os_info)
    
    analyzer = MigrationAnalyzer(data)
    
    # 4 vCPU, 32 GB 요구사항
    instance_type = analyzer._select_instance_type(4, 32)
    assert instance_type == "db.r6i.xlarge"
    
    # 8 vCPU, 64 GB 요구사항
    instance_type = analyzer._select_instance_type(8, 64)
    assert instance_type == "db.r6i.2xlarge"
    
    # 16 vCPU, 128 GB 요구사항
    instance_type = analyzer._select_instance_type(16, 128)
    assert instance_type == "db.r6i.4xlarge"
    
    # 요구사항을 만족하는 인스턴스가 없는 경우
    instance_type = analyzer._select_instance_type(200, 2000)
    assert instance_type is None
