"""
ResultFormatter 속성 기반 테스트

Property 8: JSON 직렬화 유효성
Property 9: JSON Round-trip
Property 10: Markdown 필수 섹션
Property 11: 리포트 저장 경로
Property 12: 폴더 자동 생성
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings

from src.statspack.data_models import (
    StatspackData,
    OSInformation,
    MemoryMetric,
    DiskSize,
    MainMetric,
    WaitEvent,
    SystemStat,
    FeatureUsage,
    SGAAdvice,
    MigrationComplexity,
    InstanceRecommendation,
    TargetDatabase
)
from src.statspack.result_formatter import StatspackResultFormatter


# Hypothesis 전략 정의

@st.composite
def os_information_strategy(draw):
    """OSInformation 생성 전략"""
    return OSInformation(
        statspack_version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        num_cpus=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=128))),
        num_cpu_cores=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=256))),
        physical_memory_gb=draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=2048.0))),
        platform_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        db_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        dbid=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        banner=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        instances=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10))),
        is_rds=draw(st.one_of(st.none(), st.booleans())),
        total_db_size_gb=draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=10000.0))),
        count_lines_plsql=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000000))),
        count_schemas=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        count_tables=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000))),
        count_packages=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000))),
        count_procedures=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=5000))),
        count_functions=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=5000))),
        character_set=draw(st.one_of(st.none(), st.sampled_from(["AL32UTF8", "KO16MSWIN949", "US7ASCII"]))),
        raw_data={}
    )


@st.composite
def memory_metric_strategy(draw):
    """MemoryMetric 생성 전략"""
    return MemoryMetric(
        snap_id=draw(st.integers(min_value=1, max_value=10000)),
        instance_number=draw(st.integers(min_value=1, max_value=10)),
        sga_gb=draw(st.floats(min_value=0.1, max_value=1024.0)),
        pga_gb=draw(st.floats(min_value=0.1, max_value=256.0)),
        total_gb=draw(st.floats(min_value=0.2, max_value=1280.0))
    )


@st.composite
def statspack_data_strategy(draw):
    """StatspackData 생성 전략"""
    return StatspackData(
        os_info=draw(os_information_strategy()),
        memory_metrics=draw(st.lists(memory_metric_strategy(), min_size=0, max_size=5)),
        disk_sizes=[],
        main_metrics=[],
        wait_events=[],
        system_stats=[],
        features=[],
        sga_advice=[]
    )


@st.composite
def instance_recommendation_strategy(draw):
    """InstanceRecommendation 생성 전략"""
    return InstanceRecommendation(
        instance_type=draw(st.sampled_from(["db.r6i.large", "db.r6i.xlarge", "db.r6i.2xlarge"])),
        vcpu=draw(st.integers(min_value=2, max_value=128)),
        memory_gib=draw(st.integers(min_value=16, max_value=1024)),
        current_cpu_usage_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        current_memory_gb=draw(st.floats(min_value=1.0, max_value=1000.0)),
        cpu_headroom_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory_headroom_pct=draw(st.floats(min_value=0.0, max_value=100.0)),
        estimated_monthly_cost_usd=draw(st.one_of(st.none(), st.floats(min_value=100.0, max_value=10000.0)))
    )


@st.composite
def migration_complexity_strategy(draw):
    """MigrationComplexity 생성 전략"""
    return MigrationComplexity(
        target=draw(st.sampled_from(list(TargetDatabase))),
        score=draw(st.floats(min_value=0.0, max_value=10.0)),
        level=draw(st.sampled_from(["매우 간단", "간단", "중간", "복잡", "매우 복잡"])),
        factors={"기본": draw(st.floats(min_value=0.0, max_value=5.0))},
        recommendations=draw(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=3)),
        warnings=draw(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=3)),
        next_steps=draw(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=3)),
        instance_recommendation=draw(st.one_of(st.none(), instance_recommendation_strategy()))
    )


# Property 8: JSON 직렬화 유효성
# Feature: statspack-analyzer, Property 8: JSON 직렬화 유효성
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_json_serialization_validity(statspack_data):
    """
    For any StatspackData 객체에 대해, JSON 형식으로 직렬화한 결과는 유효한 JSON이어야 합니다.
    
    Validates: Requirements 13.1
    """
    # JSON 직렬화
    json_str = StatspackResultFormatter.to_json(statspack_data)
    
    # 유효한 JSON인지 확인
    try:
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "_type" in parsed
        assert parsed["_type"] == "StatspackData"
    except json.JSONDecodeError:
        pytest.fail("JSON 직렬화 결과가 유효한 JSON이 아닙니다")


# Property 9: JSON Round-trip
# Feature: statspack-analyzer, Property 9: JSON Round-trip
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_json_roundtrip(statspack_data):
    """
    For any 유효한 StatspackData 객체에 대해, JSON 직렬화 후 역직렬화하면 원본과 동일한 객체가 생성되어야 합니다.
    
    Validates: Requirements 13.4
    """
    # JSON 직렬화
    json_str = StatspackResultFormatter.to_json(statspack_data)
    
    # JSON 역직렬화
    restored = StatspackResultFormatter.from_json(json_str)
    
    # 원본과 동일한지 확인
    assert isinstance(restored, StatspackData)
    assert restored.os_info.db_name == statspack_data.os_info.db_name
    assert restored.os_info.num_cpus == statspack_data.os_info.num_cpus
    assert len(restored.memory_metrics) == len(statspack_data.memory_metrics)
    
    # 메모리 메트릭 비교
    for i, metric in enumerate(restored.memory_metrics):
        original = statspack_data.memory_metrics[i]
        assert metric.snap_id == original.snap_id
        assert metric.instance_number == original.instance_number
        assert abs(metric.sga_gb - original.sga_gb) < 0.01
        assert abs(metric.pga_gb - original.pga_gb) < 0.01


# Property 9 (MigrationComplexity): JSON Round-trip
# Feature: statspack-analyzer, Property 9: JSON Round-trip (MigrationComplexity)
@settings(max_examples=100)
@given(st.dictionaries(
    st.sampled_from(list(TargetDatabase)),
    migration_complexity_strategy(),
    min_size=1,
    max_size=3
))
def test_property_migration_complexity_json_roundtrip(complexity_dict):
    """
    For any MigrationComplexity 딕셔너리에 대해, JSON 직렬화 후 역직렬화하면 원본과 동일한 객체가 생성되어야 합니다.
    
    Validates: Requirements 13.4
    """
    # JSON 직렬화
    json_str = StatspackResultFormatter.to_json(complexity_dict)
    
    # JSON 역직렬화
    restored = StatspackResultFormatter.from_json(json_str)
    
    # 원본과 동일한지 확인
    assert isinstance(restored, dict)
    assert len(restored) == len(complexity_dict)
    
    for target, complexity in complexity_dict.items():
        assert target in restored
        restored_complexity = restored[target]
        assert restored_complexity.target == complexity.target
        assert abs(restored_complexity.score - complexity.score) < 0.01
        assert restored_complexity.level == complexity.level


# Property 10: Markdown 필수 섹션
# Feature: statspack-analyzer, Property 10: Markdown 필수 섹션
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_markdown_required_sections(statspack_data):
    """
    For any StatspackData 객체에 대해, Markdown 보고서를 생성하면 
    시스템 정보 요약, 메모리 사용량 통계, 주요 성능 메트릭 요약 섹션을 포함해야 합니다.
    
    Validates: Requirements 13.5
    """
    # Markdown 생성
    markdown = StatspackResultFormatter.to_markdown(statspack_data)
    
    # 필수 섹션 확인
    assert "# Statspack 분석 보고서" in markdown
    assert "## 1. 시스템 정보 요약" in markdown
    
    # 데이터가 있는 경우에만 해당 섹션 확인
    if statspack_data.memory_metrics:
        assert "## 2. 메모리 사용량 통계" in markdown
    
    if statspack_data.main_metrics:
        assert "## 4. 주요 성능 메트릭 요약" in markdown


# Property 11: 리포트 저장 경로
# Feature: statspack-analyzer, Property 11: 리포트 저장 경로
@settings(max_examples=50)
@given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
def test_property_report_save_path(filename):
    """
    For any 리포트 저장 요청에 대해, 파일은 reports/YYYYMMDD/ 형식의 날짜 폴더에 저장되어야 합니다.
    
    Validates: Requirements 14.1
    """
    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        # 리포트 저장
        content = "# Test Report"
        filepath = StatspackResultFormatter.save_report(
            content=content,
            filename=filename,
            format="md",
            base_dir=tmpdir
        )
        
        # 경로 확인
        path = Path(filepath)
        assert path.exists()
        
        # 날짜 폴더 형식 확인 (YYYYMMDD)
        today = datetime.now().strftime("%Y%m%d")
        assert today in str(path.parent)
        
        # 파일 내용 확인
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == content


# Property 12: 폴더 자동 생성
# Feature: statspack-analyzer, Property 12: 폴더 자동 생성
@settings(max_examples=50)
@given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
def test_property_folder_auto_creation(filename):
    """
    For any 존재하지 않는 날짜 폴더에 대해, 리포트 저장 시 자동으로 폴더가 생성되어야 합니다.
    
    Validates: Requirements 14.2
    """
    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir) / "test_reports"
        
        # 폴더가 존재하지 않음을 확인
        assert not base_dir.exists()
        
        # 리포트 저장
        content = "# Test Report"
        filepath = StatspackResultFormatter.save_report(
            content=content,
            filename=filename,
            format="md",
            base_dir=str(base_dir)
        )
        
        # 폴더가 생성되었는지 확인
        path = Path(filepath)
        assert path.exists()
        assert path.parent.exists()
        assert base_dir.exists()
        
        # 날짜 폴더도 생성되었는지 확인
        today = datetime.now().strftime("%Y%m%d")
        date_folder = base_dir / today
        assert date_folder.exists()


# 단위 테스트: JSON 직렬화 기본 케이스
def test_json_serialization_basic():
    """기본 StatspackData JSON 직렬화 테스트"""
    data = StatspackData(
        os_info=OSInformation(db_name="TESTDB", num_cpus=4),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=10.0, pga_gb=2.0, total_gb=12.0)
        ]
    )
    
    json_str = StatspackResultFormatter.to_json(data)
    assert "TESTDB" in json_str
    assert "\"num_cpus\": 4" in json_str


# 단위 테스트: Markdown 생성 기본 케이스
def test_markdown_generation_basic():
    """기본 Markdown 보고서 생성 테스트"""
    data = StatspackData(
        os_info=OSInformation(db_name="TESTDB", version="19.0.0.0"),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=10.0, pga_gb=2.0, total_gb=12.0)
        ]
    )
    
    markdown = StatspackResultFormatter.to_markdown(data)
    assert "# Statspack 분석 보고서" in markdown
    assert "TESTDB" in markdown
    assert "19.0.0.0" in markdown


# 단위 테스트: 파일 저장 기본 케이스
def test_save_report_basic():
    """기본 리포트 저장 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test Report\n\nThis is a test."
        filepath = StatspackResultFormatter.save_report(
            content=content,
            filename="test_report",
            format="md",
            base_dir=tmpdir
        )
        
        assert Path(filepath).exists()
        with open(filepath, 'r', encoding='utf-8') as f:
            saved = f.read()
        assert saved == content


# 단위 테스트: DB 이름 포함 파일 저장
def test_save_report_with_db_name():
    """DB 이름으로 폴더 분리 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test Report\n\nThis is a test."
        db_name = "TESTDB"
        filepath = StatspackResultFormatter.save_report(
            content=content,
            filename="test_report",
            format="md",
            base_dir=tmpdir,
            db_name=db_name
        )
        
        # 파일이 존재하는지 확인
        assert Path(filepath).exists()
        
        # 폴더 구조 확인: reports/YYYYMMDD/testdb/
        path = Path(filepath)
        assert "testdb" in str(path.parent).lower()
        
        # 날짜 폴더도 있는지 확인
        today = datetime.now().strftime("%Y%m%d")
        assert today in str(path.parent.parent)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            saved = f.read()
        assert saved == content


# 단위 테스트: 특수 문자가 포함된 DB 이름 처리
def test_save_report_with_special_chars_in_db_name():
    """특수 문자가 포함된 DB 이름 폴더 처리 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test Report"
        db_name = "TEST-DB@123#"  # 특수 문자 포함
        filepath = StatspackResultFormatter.save_report(
            content=content,
            filename="test_report",
            format="md",
            base_dir=tmpdir,
            db_name=db_name
        )
        
        # 파일이 존재하는지 확인
        assert Path(filepath).exists()
        
        # 폴더명에 안전한 문자만 포함되어 있는지 확인
        folder_name = Path(filepath).parent.name
        # 특수 문자는 제거되고 알파벳과 숫자, 하이픈만 남아야 함
        assert "test-db123" in folder_name.lower()
        assert "@" not in folder_name
        assert "#" not in folder_name


# 단위 테스트: 마이그레이션 분석 포함 Markdown
def test_markdown_with_migration_analysis():
    """마이그레이션 분석 포함 Markdown 생성 테스트"""
    data = StatspackData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    
    migration_analysis = {
        TargetDatabase.RDS_ORACLE: MigrationComplexity(
            target=TargetDatabase.RDS_ORACLE,
            score=3.5,
            level="중간",
            factors={"기본": 1.0, "에디션": 2.5},
            recommendations=["RDS for Oracle 권장"],
            warnings=["RAC 환경"],
            next_steps=["평가 수행"],
            instance_recommendation=InstanceRecommendation(
                instance_type="db.r6i.xlarge",
                vcpu=4,
                memory_gib=32,
                current_cpu_usage_pct=50.0,
                current_memory_gb=20.0,
                cpu_headroom_pct=30.0,
                memory_headroom_pct=20.0
            )
        )
    }
    
    markdown = StatspackResultFormatter.to_markdown(data, migration_analysis)
    assert "## 8. 마이그레이션 분석 결과" in markdown
    assert "RDS for Oracle" in markdown
    assert "db.r6i.xlarge" in markdown
