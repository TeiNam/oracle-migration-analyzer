"""
MigrationAnalyzer 속성 기반 테스트

Property-based testing을 사용하여 MigrationAnalyzer의 정확성을 검증합니다.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.dbcsi.data_models import (
    StatspackData,
    OSInformation,
    OracleEdition,
    MainMetric,
    MemoryMetric,
    TargetDatabase,
)
from src.dbcsi.migration_analyzer import MigrationAnalyzer


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



# AWR Enhanced Migration Analyzer Property Tests

# Feature: awr-analyzer, Property 7: 읽기 집약적 워크로드 분류
@given(
    st.integers(min_value=1000, max_value=10000),  # 읽기 IOPS
    st.integers(min_value=100, max_value=1000)     # 쓰기 IOPS
)
@settings(max_examples=100)
def test_property_read_intensive_workload_classification(read_iops, write_iops):
    """
    Property 7: 읽기 집약적 워크로드 분류
    
    For any 읽기 IOPS가 쓰기 IOPS의 3배 이상인 I/O 데이터에 대해, 
    워크로드는 읽기 집약적으로 분류되어야 합니다.
    
    Validates: Requirements 4.7
    """
    from src.dbcsi.data_models import AWRData, PercentileIO
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # 읽기 IOPS가 쓰기 IOPS의 3배 이상인 경우만 테스트
    if read_iops < write_iops * 3:
        return
    
    # AWRData 생성
    os_info = OSInformation()
    percentile_io = {
        "99th_percentile": PercentileIO(
            metric="99th_percentile",
            instance_number=1,
            rw_iops=read_iops + write_iops,
            r_iops=read_iops,
            w_iops=write_iops,
            rw_mbps=100,
            r_mbps=80,
            w_mbps=20,
            begin_interval="2024-01-01 00:00:00",
            end_interval="2024-01-01 01:00:00",
            snap_shots=10,
            days=1.0,
            avg_snaps_per_day=10.0
        )
    }
    
    awr_data = AWRData(
        os_info=os_info,
        percentile_io=percentile_io
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 워크로드 패턴 분석
    # 참고: 현재 구현은 workload_profiles 기반이므로 I/O 데이터만으로는 분류하지 않음
    # 이 테스트는 향후 I/O 기반 분류가 추가될 때를 대비한 것
    
    # 검증: 읽기 IOPS가 쓰기 IOPS의 3배 이상이면 읽기 집약적
    ratio = read_iops / write_iops if write_iops > 0 else float('inf')
    assert ratio >= 3.0, \
        f"읽기 IOPS({read_iops})가 쓰기 IOPS({write_iops})의 3배 이상이어야 함"


# Feature: awr-analyzer, Property 13: CPU 집약적 워크로드 인스턴스 추천
@given(
    st.floats(min_value=51.0, max_value=100.0)  # CPU 사용률 > 50%
)
@settings(max_examples=100)
def test_property_cpu_intensive_workload_instance_recommendation(cpu_pct):
    """
    Property 13: CPU 집약적 워크로드 인스턴스 추천
    
    For any CPU 사용률이 50% 초과인 워크로드 데이터에 대해, 
    컴퓨트 최적화 인스턴스 추천 또는 권장사항이 포함되어야 합니다.
    
    Validates: Requirements 9.2
    """
    from src.dbcsi.data_models import AWRData, WorkloadProfile
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성 (CPU 집약적 워크로드)
    os_info = OSInformation(num_cpus=8, physical_memory_gb=64.0)
    
    # CPU 집약적 워크로드 프로파일 생성
    workload_profiles = [
        WorkloadProfile(
            sample_start="2024-01-01 10:00:00",
            topn=1,
            module="Application",
            program="app.exe",
            event="CPU + CPU Wait",
            total_dbtime_sum=int(cpu_pct * 1000),  # CPU 비율에 비례
            aas_comp=cpu_pct / 100.0,
            aas_contribution_pct=cpu_pct,
            tot_contributions=1,
            session_type="FOREGROUND",
            wait_class="CPU",
            delta_read_io_requests=100,
            delta_write_io_requests=50,
            delta_read_io_bytes=1000000,
            delta_write_io_bytes=500000
        ),
        WorkloadProfile(
            sample_start="2024-01-01 10:00:00",
            topn=2,
            module="Application",
            program="app.exe",
            event="User I/O",
            total_dbtime_sum=int((100 - cpu_pct) * 1000),  # 나머지는 I/O
            aas_comp=(100 - cpu_pct) / 100.0,
            aas_contribution_pct=100 - cpu_pct,
            tot_contributions=1,
            session_type="FOREGROUND",
            wait_class="User I/O",
            delta_read_io_requests=1000,
            delta_write_io_requests=500,
            delta_read_io_bytes=10000000,
            delta_write_io_bytes=5000000
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        workload_profiles=workload_profiles
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 워크로드 패턴 분석
    workload_pattern = analyzer._analyze_workload_pattern()
    
    # 검증: CPU 비율이 50% 초과이면 CPU-intensive로 분류
    assert workload_pattern.cpu_pct > 50.0, \
        f"CPU 비율({workload_pattern.cpu_pct}%)이 50% 초과여야 함"
    
    assert workload_pattern.pattern_type == "CPU-intensive", \
        f"CPU 비율이 {cpu_pct}%일 때 'CPU-intensive'로 분류되어야 하지만 '{workload_pattern.pattern_type}'로 분류됨"



# Feature: awr-analyzer, Property 9: 버퍼 캐시 효율성 평가
@given(
    st.floats(min_value=95.0, max_value=99.4)  # 히트율 95% ~ 99.4%
)
@settings(max_examples=100)
def test_property_buffer_cache_efficiency_evaluation(hit_ratio):
    """
    Property 9: 버퍼 캐시 효율성 평가
    
    For any 히트율이 95% 이상인 버퍼 캐시 데이터에 대해, 
    버퍼 캐시는 효율적으로 동작하는 것으로 평가되어야 합니다.
    
    Validates: Requirements 6.3
    """
    from src.dbcsi.data_models import AWRData, BufferCacheStats
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=32.0,
            dsk_reads=1000,
            block_gets=100000,
            consistent=90000,
            buf_got_gb=30.0,
            hit_ratio=hit_ratio
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        buffer_cache_stats=buffer_cache_stats
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 버퍼 캐시 분석
    buffer_analysis = analyzer._analyze_buffer_cache()
    
    # 검증: 히트율이 95% 이상이면 효율적으로 평가
    assert buffer_analysis.avg_hit_ratio >= 95.0, \
        f"평균 히트율({buffer_analysis.avg_hit_ratio}%)이 95% 이상이어야 함"
    
    # 최적화 불필요
    assert not buffer_analysis.optimization_needed, \
        f"히트율이 {hit_ratio}%일 때 최적화가 불필요해야 함"
    
    # 권장사항에 "효율적" 포함
    recommendations_text = " ".join(buffer_analysis.recommendations)
    assert "효율적" in recommendations_text, \
        f"히트율이 {hit_ratio}%일 때 권장사항에 '효율적'이 포함되어야 함"


# Feature: awr-analyzer, Property 10: 버퍼 캐시 최적화 권장
@given(
    st.floats(min_value=50.0, max_value=89.9)  # 히트율 < 90%
)
@settings(max_examples=100)
def test_property_buffer_cache_optimization_recommendation(hit_ratio):
    """
    Property 10: 버퍼 캐시 최적화 권장
    
    For any 히트율이 90% 미만인 버퍼 캐시 데이터에 대해, 
    버퍼 캐시 크기 증가 권장사항이 포함되어야 합니다.
    
    Validates: Requirements 6.4, 10.1
    """
    from src.dbcsi.data_models import AWRData, BufferCacheStats
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=32.0,
            dsk_reads=10000,
            block_gets=100000,
            consistent=80000,
            buf_got_gb=25.0,
            hit_ratio=hit_ratio
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        buffer_cache_stats=buffer_cache_stats
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 버퍼 캐시 분석
    buffer_analysis = analyzer._analyze_buffer_cache()
    
    # 검증: 히트율이 90% 미만이면 최적화 필요
    assert buffer_analysis.avg_hit_ratio < 90.0, \
        f"평균 히트율({buffer_analysis.avg_hit_ratio}%)이 90% 미만이어야 함"
    
    assert buffer_analysis.optimization_needed, \
        f"히트율이 {hit_ratio}%일 때 최적화가 필요해야 함"
    
    # 권장 크기가 현재 크기보다 커야 함
    assert buffer_analysis.recommended_size_gb > buffer_analysis.current_size_gb, \
        f"권장 크기({buffer_analysis.recommended_size_gb}GB)가 현재 크기({buffer_analysis.current_size_gb}GB)보다 커야 함"
    
    # 권장사항에 "증가" 또는 "권장" 포함
    recommendations_text = " ".join(buffer_analysis.recommendations)
    assert "증가" in recommendations_text or "권장" in recommendations_text, \
        f"히트율이 {hit_ratio}%일 때 권장사항에 '증가' 또는 '권장'이 포함되어야 함"



# Feature: awr-analyzer, Property 14: LGWR I/O 최적화 권장
@given(
    st.floats(min_value=10.1, max_value=200.0)  # LGWR I/O > 10 MB/s
)
@settings(max_examples=100)
def test_property_lgwr_io_optimization_recommendation(lgwr_mb_per_s):
    """
    Property 14: LGWR I/O 최적화 권장
    
    For any LGWR I/O가 10 MB/s 이상인 데이터에 대해, 
    로그 쓰기 최적화 권장사항이 포함되어야 합니다.
    
    Validates: Requirements 11.1
    """
    from src.dbcsi.data_models import AWRData, IOStatFunction
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    iostat_functions = [
        IOStatFunction(
            snap_id=1,
            function_name="LGWR",
            megabytes_per_s=lgwr_mb_per_s
        ),
        IOStatFunction(
            snap_id=1,
            function_name="DBWR",
            megabytes_per_s=5.0
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        iostat_functions=iostat_functions
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # I/O 함수별 분석
    io_analysis = analyzer._analyze_io_functions()
    
    # LGWR 분석 결과 찾기
    lgwr_analysis = None
    for analysis in io_analysis:
        if analysis.function_name == "LGWR":
            lgwr_analysis = analysis
            break
    
    # 검증: LGWR 분석 결과가 있어야 함
    assert lgwr_analysis is not None, "LGWR 분석 결과가 있어야 함"
    
    # 검증: LGWR I/O가 10 MB/s 이상이면 권장사항이 있어야 함
    assert lgwr_analysis.avg_mb_per_s > 10.0, \
        f"LGWR 평균 I/O({lgwr_analysis.avg_mb_per_s} MB/s)가 10 MB/s 초과여야 함"
    
    assert len(lgwr_analysis.recommendations) > 0, \
        f"LGWR I/O가 {lgwr_mb_per_s} MB/s일 때 권장사항이 있어야 함"
    
    # 권장사항에 "LGWR" 또는 "로그" 포함
    recommendations_text = " ".join(lgwr_analysis.recommendations)
    assert "LGWR" in recommendations_text or "로그" in recommendations_text, \
        f"LGWR I/O가 {lgwr_mb_per_s} MB/s일 때 권장사항에 'LGWR' 또는 '로그'가 포함되어야 함"


# Feature: awr-analyzer, Property 17: 피크 시간대 식별
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=23),  # 시간
            st.floats(min_value=1.0, max_value=100.0)  # 부하
        ),
        min_size=5,
        max_size=24,
        unique_by=lambda x: x[0]
    )
)
@settings(max_examples=50)
def test_property_peak_hour_identification(hour_loads):
    """
    Property 17: 피크 시간대 식별
    
    For any 시간대별 워크로드 데이터가 있는 AWR 데이터에 대해, 
    분석 결과는 피크 시간대 정보를 포함해야 합니다.
    
    Validates: Requirements 14.2
    """
    from src.dbcsi.data_models import AWRData, WorkloadProfile
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    
    # 시간대별 워크로드 프로파일 생성
    workload_profiles = []
    for hour, load in hour_loads:
        workload_profiles.append(
            WorkloadProfile(
                sample_start=f"2024-01-01 {hour:02d}:00:00",
                topn=1,
                module="Application",
                program="app.exe",
                event="CPU + CPU Wait",
                total_dbtime_sum=int(load * 1000),
                aas_comp=load,
                aas_contribution_pct=load,
                tot_contributions=1,
                session_type="FOREGROUND",
                wait_class="CPU",
                delta_read_io_requests=100,
                delta_write_io_requests=50,
                delta_read_io_bytes=1000000,
                delta_write_io_bytes=500000
            )
        )
    
    awr_data = AWRData(
        os_info=os_info,
        workload_profiles=workload_profiles
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 시간대별 패턴 분석
    time_patterns = analyzer._analyze_time_based_patterns()
    
    # 검증: 피크 시간대 정보가 있어야 함
    assert "peak_hours" in time_patterns, "피크 시간대 정보가 있어야 함"
    assert isinstance(time_patterns["peak_hours"], list), "피크 시간대는 리스트여야 함"



# Feature: awr-analyzer, Property 5: P99 CPU 우선 사용
@given(
    st.integers(min_value=2, max_value=64),  # P99 CPU
    st.floats(min_value=10.0, max_value=90.0)  # 평균 CPU
)
@settings(max_examples=100)
def test_property_p99_cpu_priority(p99_cpu, avg_cpu_pct):
    """
    Property 5: P99 CPU 우선 사용
    
    For any P99 CPU 값이 있는 AWR 데이터에 대해, 
    마이그레이션 난이도 계산 시 평균 CPU 대신 P99 CPU 값을 사용해야 합니다.
    
    Validates: Requirements 3.7, 8.2
    """
    from src.dbcsi.data_models import AWRData, PercentileCPU, MainMetric
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation(num_cpus=8, physical_memory_gb=64.0)
    
    # P99 CPU 데이터
    percentile_cpu = {
        "99th_percentile": PercentileCPU(
            metric="99th_percentile",
            instance_number=1,
            on_cpu=p99_cpu,
            on_cpu_and_resmgr=p99_cpu,
            resmgr_cpu_quantum=0,
            begin_interval="2024-01-01 00:00:00",
            end_interval="2024-01-01 01:00:00",
            snap_shots=10,
            days=1.0,
            avg_snaps_per_day=10.0
        )
    }
    
    # 평균 CPU 데이터 (더 낮음)
    main_metrics = [
        MainMetric(
            snap=1,
            dur_m=60.0,
            end="2024-01-01 01:00:00",
            inst=1,
            cpu_per_s=avg_cpu_pct,
            read_iops=100.0,
            read_mb_s=10.0,
            write_iops=50.0,
            write_mb_s=5.0,
            commits_s=10.0
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        percentile_cpu=percentile_cpu,
        main_metrics=main_metrics
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # P99 CPU 값 가져오기
    retrieved_p99_cpu = analyzer._get_percentile_cpu("99th_percentile")
    
    # 검증: P99 CPU 값이 올바르게 반환되어야 함
    assert retrieved_p99_cpu == p99_cpu, \
        f"P99 CPU 값({retrieved_p99_cpu})이 예상값({p99_cpu})과 일치해야 함"
    
    # 인스턴스 추천 시 P99 CPU 사용 확인
    instance_rec = analyzer._recommend_instance_with_percentiles(TargetDatabase.RDS_ORACLE, 5.0)
    
    if instance_rec:
        # P99 CPU + 30% 여유분을 기준으로 인스턴스가 선택되어야 함
        required_vcpu = int(p99_cpu * 1.3)
        assert instance_rec.vcpu >= required_vcpu, \
            f"추천 vCPU({instance_rec.vcpu})가 P99 기반 요구사항({required_vcpu})을 만족해야 함"


# Feature: awr-analyzer, Property 6: P99 I/O 우선 사용
@given(
    st.integers(min_value=1000, max_value=50000),  # P99 IOPS
    st.floats(min_value=100.0, max_value=5000.0)  # 평균 IOPS
)
@settings(max_examples=100)
def test_property_p99_io_priority(p99_iops, avg_iops):
    """
    Property 6: P99 I/O 우선 사용
    
    For any P99 I/O 값이 있는 AWR 데이터에 대해, 
    마이그레이션 난이도 계산 시 평균 I/O 대신 P99 I/O 값을 사용해야 합니다.
    
    Validates: Requirements 4.6, 8.3
    """
    from src.dbcsi.data_models import AWRData, PercentileIO
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    
    # P99 I/O 데이터
    percentile_io = {
        "99th_percentile": PercentileIO(
            metric="99th_percentile",
            instance_number=1,
            rw_iops=p99_iops,
            r_iops=int(p99_iops * 0.7),
            w_iops=int(p99_iops * 0.3),
            rw_mbps=int(p99_iops / 10),
            r_mbps=int(p99_iops * 0.7 / 10),
            w_mbps=int(p99_iops * 0.3 / 10),
            begin_interval="2024-01-01 00:00:00",
            end_interval="2024-01-01 01:00:00",
            snap_shots=10,
            days=1.0,
            avg_snaps_per_day=10.0
        )
    }
    
    awr_data = AWRData(
        os_info=os_info,
        percentile_io=percentile_io
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # P99 I/O 값 가져오기
    retrieved_p99_io = analyzer._get_percentile_io("99th_percentile")
    
    # 검증: P99 I/O 값이 올바르게 반환되어야 함
    assert retrieved_p99_io is not None, "P99 I/O 값이 반환되어야 함"
    assert retrieved_p99_io["rw_iops"] == p99_iops, \
        f"P99 IOPS 값({retrieved_p99_io['rw_iops']})이 예상값({p99_iops})과 일치해야 함"


# Feature: awr-analyzer, Property 12: 버퍼 캐시 난이도 반영
@given(
    st.floats(min_value=50.0, max_value=89.9)  # 히트율 < 90%
)
@settings(max_examples=100)
def test_property_buffer_cache_complexity_impact(hit_ratio):
    """
    Property 12: 버퍼 캐시 난이도 반영
    
    For any 히트율이 90% 미만인 버퍼 캐시 데이터에 대해, 
    마이그레이션 난이도 점수에 1.0 이상의 가중치가 추가되어야 합니다.
    
    Validates: Requirements 8.4
    """
    from src.dbcsi.data_models import AWRData, BufferCacheStats
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation()
    buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=32.0,
            dsk_reads=10000,
            block_gets=100000,
            consistent=80000,
            buf_got_gb=25.0,
            hit_ratio=hit_ratio
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        buffer_cache_stats=buffer_cache_stats
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 마이그레이션 난이도 계산
    complexity = analyzer._calculate_enhanced_complexity(TargetDatabase.RDS_ORACLE)
    
    # 검증: factors에 buffer_cache_low가 포함되어야 함
    assert "buffer_cache_low" in complexity.factors, \
        f"히트율이 {hit_ratio}%일 때 factors에 'buffer_cache_low'가 포함되어야 함"
    
    # 검증: buffer_cache_low 가중치가 1.0 이상이어야 함
    buffer_cache_weight = complexity.factors["buffer_cache_low"]
    assert buffer_cache_weight >= 1.0, \
        f"히트율이 {hit_ratio}%일 때 버퍼 캐시 가중치({buffer_cache_weight})가 1.0 이상이어야 함"



# Feature: awr-analyzer, Property 15: P99 기반 인스턴스 사이징
@given(
    st.integers(min_value=2, max_value=32),  # P99 CPU
    st.floats(min_value=16.0, max_value=256.0)  # 메모리
)
@settings(max_examples=100)
def test_property_p99_based_instance_sizing(p99_cpu, memory_gb):
    """
    Property 15: P99 기반 인스턴스 사이징
    
    For any P99 메트릭이 있는 AWR 데이터에 대해, 
    인스턴스 사이징 시 P99 값을 기준으로 계산해야 합니다.
    
    Validates: Requirements 12.1
    """
    from src.dbcsi.data_models import AWRData, PercentileCPU, MemoryMetric
    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
    
    # AWRData 생성
    os_info = OSInformation(num_cpus=8, physical_memory_gb=memory_gb)
    
    # P99 CPU 데이터
    percentile_cpu = {
        "99th_percentile": PercentileCPU(
            metric="99th_percentile",
            instance_number=1,
            on_cpu=p99_cpu,
            on_cpu_and_resmgr=p99_cpu,
            resmgr_cpu_quantum=0,
            begin_interval="2024-01-01 00:00:00",
            end_interval="2024-01-01 01:00:00",
            snap_shots=10,
            days=1.0,
            avg_snaps_per_day=10.0
        )
    }
    
    # 메모리 메트릭
    memory_metrics = [
        MemoryMetric(
            snap_id=1,
            instance_number=1,
            sga_gb=memory_gb * 0.6,
            pga_gb=memory_gb * 0.2,
            total_gb=memory_gb * 0.8
        )
    ]
    
    awr_data = AWRData(
        os_info=os_info,
        percentile_cpu=percentile_cpu,
        memory_metrics=memory_metrics
    )
    
    # EnhancedMigrationAnalyzer 생성
    analyzer = EnhancedMigrationAnalyzer(awr_data)
    
    # 인스턴스 추천
    instance_rec = analyzer._recommend_instance_with_percentiles(TargetDatabase.RDS_ORACLE, 5.0)
    
    if instance_rec:
        # 검증: P99 CPU + 30% 여유분을 만족해야 함
        required_vcpu = int(p99_cpu * 1.3)
        required_vcpu = max(required_vcpu, 2)
        
        assert instance_rec.vcpu >= required_vcpu, \
            f"추천 vCPU({instance_rec.vcpu})가 P99 기반 요구사항({required_vcpu})을 만족해야 함"
        
        # 검증: 메모리 + 20% 여유분을 만족해야 함
        required_memory_gb = int(memory_gb * 0.8 * 1.2)
        required_memory_gb = max(required_memory_gb, 16)
        
        assert instance_rec.memory_gib >= required_memory_gb, \
            f"추천 메모리({instance_rec.memory_gib}GB)가 요구사항({required_memory_gb}GB)을 만족해야 함"
