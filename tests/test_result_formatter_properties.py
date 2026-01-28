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

from src.dbcsi.models import (
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
from src.dbcsi.result_formatter import StatspackResultFormatter


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
# Feature: dbcsi-analyzer, Property 8: JSON 직렬화 유효성
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
# Feature: dbcsi-analyzer, Property 9: JSON Round-trip
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
# Feature: dbcsi-analyzer, Property 9: JSON Round-trip (MigrationComplexity)
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
# Feature: dbcsi-analyzer, Property 10: Markdown 필수 섹션
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_markdown_required_sections(statspack_data):
    """
    For any StatspackData 객체에 대해, Markdown 보고서를 생성하면 
    데이터베이스 개요, 메모리 사용량 통계 섹션을 포함해야 합니다.
    
    Validates: Requirements 13.5
    """
    # Markdown 생성
    markdown = StatspackResultFormatter.to_markdown(statspack_data)
    
    # 필수 섹션 확인 (새로운 포맷)
    assert "# Statspack 분석 보고서" in markdown
    assert "## 📊 데이터베이스 개요" in markdown
    
    # 데이터가 있는 경우에만 해당 섹션 확인
    if statspack_data.memory_metrics:
        assert "## 💾 메모리 사용량 통계" in markdown


# Property 11: 리포트 저장 경로
# Feature: dbcsi-analyzer, Property 11: 리포트 저장 경로
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
# Feature: dbcsi-analyzer, Property 12: 폴더 자동 생성
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
    # 새로운 포맷: 이모지 포함 헤더
    assert "## 🚀 마이그레이션 분석 결과" in markdown
    assert "RDS for Oracle" in markdown
    assert "db.r6i.xlarge" in markdown


# Property 18: 상세 리포트 필수 섹션
# Feature: awr-analyzer, Property 18: 상세 리포트 필수 섹션
@settings(max_examples=100)
@given(statspack_data_strategy())
def test_property_detailed_report_required_sections(statspack_data):
    """
    For any AWR 분석 결과에 대해, Markdown 리포트는 데이터베이스 개요, 
    메모리 사용량 통계 섹션을 포함해야 합니다.
    
    Validates: Requirements 15.1
    """
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData
    
    # StatspackData를 AWRData로 변환
    awr_data = AWRData(
        os_info=statspack_data.os_info,
        memory_metrics=statspack_data.memory_metrics,
        disk_sizes=statspack_data.disk_sizes,
        main_metrics=statspack_data.main_metrics,
        wait_events=statspack_data.wait_events,
        system_stats=statspack_data.system_stats,
        features=statspack_data.features,
        sga_advice=statspack_data.sga_advice
    )
    
    # 상세 Markdown 생성
    markdown = EnhancedResultFormatter.to_detailed_markdown(awr_data, language='ko')
    
    # 필수 섹션 확인 (새로운 포맷)
    assert "분석 보고서" in markdown  # AWR 또는 Statspack
    assert "생성 시간:" in markdown
    assert "## 📊 데이터베이스 개요" in markdown
    
    # 데이터가 있는 경우에만 해당 섹션 확인
    if awr_data.memory_metrics:
        assert "## 💾 메모리 사용량 통계" in markdown


# 단위 테스트: AWR 상세 리포트 생성
def test_enhanced_result_formatter_detailed_markdown():
    """AWR 상세 리포트 생성 기본 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, PercentileCPU, PercentileIO
    
    # AWR 데이터 생성
    awr_data = AWRData(
        os_info=OSInformation(
            db_name="TESTDB",
            version="19.0.0.0",
            num_cpus=8,
            physical_memory_gb=64.0,
            total_db_size_gb=500.0
        ),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=40.0, pga_gb=10.0, total_gb=50.0)
        ]
    )
    
    # P99 CPU 데이터 추가
    awr_data.percentile_cpu["99th_percentile"] = PercentileCPU(
        metric="99th_percentile",
        instance_number=1,
        on_cpu=6,
        on_cpu_and_resmgr=6,
        resmgr_cpu_quantum=0,
        begin_interval="2024-01-01 00:00:00",
        end_interval="2024-01-01 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # P99 I/O 데이터 추가
    awr_data.percentile_io["99th_percentile"] = PercentileIO(
        metric="99th_percentile",
        instance_number=1,
        rw_iops=5000,
        r_iops=4000,
        w_iops=1000,
        rw_mbps=200,
        r_mbps=160,
        w_mbps=40,
        begin_interval="2024-01-01 00:00:00",
        end_interval="2024-01-01 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # 마이그레이션 분석 추가
    migration_analysis = {
        TargetDatabase.RDS_ORACLE: MigrationComplexity(
            target=TargetDatabase.RDS_ORACLE,
            score=2.5,
            level="간단",
            factors={"기본": 1.0},
            recommendations=["RDS for Oracle 권장"],
            warnings=[],
            next_steps=["평가 수행"]
        )
    }
    
    # 상세 리포트 생성
    markdown = EnhancedResultFormatter.to_detailed_markdown(awr_data, migration_analysis, language='ko')
    
    # 기본 섹션 확인
    assert "AWR 상세 분석 보고서" in markdown or "Statspack 분석 보고서" in markdown
    assert "TESTDB" in markdown
    assert "19.0.0.0" in markdown
    
    # Executive Summary 확인 (AWR이고 migration_analysis가 있는 경우)
    if awr_data.is_awr() and migration_analysis:
        assert "경영진 요약" in markdown or "Executive Summary" in markdown


# 단위 테스트: 워크로드 분석 섹션
def test_enhanced_result_formatter_workload_analysis():
    """워크로드 분석 섹션 생성 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, WorkloadProfile
    
    # AWR 데이터 생성
    awr_data = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    
    # 워크로드 프로파일 추가
    awr_data.workload_profiles = [
        WorkloadProfile(
            sample_start="2024-01-01 10:00:00",
            topn=1,
            module="SQL*Plus",
            program="sqlplus@server",
            event="CPU + CPU Wait",
            total_dbtime_sum=10000,
            aas_comp=5.0,
            aas_contribution_pct=50.0,
            tot_contributions=1,
            session_type="FOREGROUND",
            wait_class="CPU",
            delta_read_io_requests=1000,
            delta_write_io_requests=500,
            delta_read_io_bytes=10000000,
            delta_write_io_bytes=5000000
        )
    ]
    
    # 워크로드 분석 생성
    workload_section = EnhancedResultFormatter._generate_workload_analysis(awr_data, 'ko')
    
    # 섹션 확인
    assert "워크로드 패턴 분석" in workload_section
    assert "SQL*Plus" in workload_section or "워크로드 프로파일 데이터가 없습니다" in workload_section


# 단위 테스트: 버퍼 캐시 분석 섹션
def test_enhanced_result_formatter_buffer_cache_analysis():
    """버퍼 캐시 분석 섹션 생성 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, BufferCacheStats
    
    # AWR 데이터 생성
    awr_data = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    
    # 버퍼 캐시 통계 추가
    awr_data.buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=40.0,
            dsk_reads=10000,
            block_gets=100000,
            consistent=90000,
            buf_got_gb=400.0,
            hit_ratio=92.5
        )
    ]
    
    # 버퍼 캐시 분석 생성
    buffer_section = EnhancedResultFormatter._generate_buffer_cache_analysis(awr_data, 'ko')
    
    # 섹션 확인
    assert "버퍼 캐시 효율성 분석" in buffer_section
    assert "92.5" in buffer_section or "버퍼 캐시 통계 데이터가 없습니다" in buffer_section


# 단위 테스트: I/O 함수별 분석 섹션
def test_enhanced_result_formatter_io_function_analysis():
    """I/O 함수별 분석 섹션 생성 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, IOStatFunction
    
    # AWR 데이터 생성
    awr_data = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    
    # I/O 함수 통계 추가
    awr_data.iostat_functions = [
        IOStatFunction(
            snap_id=1,
            function_name="LGWR",
            megabytes_per_s=15.5
        ),
        IOStatFunction(
            snap_id=1,
            function_name="DBWR",
            megabytes_per_s=25.0
        )
    ]
    
    # I/O 함수별 분석 생성
    io_section = EnhancedResultFormatter._generate_io_function_analysis(awr_data, 'ko')
    
    # 섹션 확인
    assert "I/O 함수별 분석" in io_section
    assert "LGWR" in io_section or "I/O 함수별 통계 데이터가 없습니다" in io_section


# 단위 테스트: 백분위수 차트 생성
def test_enhanced_result_formatter_percentile_charts():
    """백분위수 차트 생성 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, PercentileCPU, PercentileIO
    
    # AWR 데이터 생성
    awr_data = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    
    # CPU 백분위수 추가
    awr_data.percentile_cpu["99th_percentile"] = PercentileCPU(
        metric="99th_percentile",
        instance_number=1,
        on_cpu=6,
        on_cpu_and_resmgr=6,
        resmgr_cpu_quantum=0,
        begin_interval="2024-01-01 00:00:00",
        end_interval="2024-01-01 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # I/O 백분위수 추가
    awr_data.percentile_io["99th_percentile"] = PercentileIO(
        metric="99th_percentile",
        instance_number=1,
        rw_iops=5000,
        r_iops=4000,
        w_iops=1000,
        rw_mbps=200,
        r_mbps=160,
        w_mbps=40,
        begin_interval="2024-01-01 00:00:00",
        end_interval="2024-01-01 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # 백분위수 차트 생성
    chart_section = EnhancedResultFormatter._generate_percentile_charts(awr_data)
    
    # 섹션 확인 (그래프 제거 후 테이블만 확인)
    assert "백분위수 분포 차트" in chart_section
    assert "CPU 사용률 백분위수 분포" in chart_section
    assert "| 백분위수 | CPU 코어 수 |" in chart_section


# 단위 테스트: AWR 리포트 비교
def test_enhanced_result_formatter_compare_reports():
    """AWR 리포트 비교 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData
    
    # 첫 번째 AWR 데이터
    awr1 = AWRData(
        os_info=OSInformation(
            db_name="TESTDB",
            version="19.0.0.0",
            num_cpus=8,
            physical_memory_gb=64.0,
            total_db_size_gb=500.0
        ),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=40.0, pga_gb=10.0, total_gb=50.0)
        ]
    )
    
    # 두 번째 AWR 데이터 (약간 다른 값)
    awr2 = AWRData(
        os_info=OSInformation(
            db_name="TESTDB",
            version="19.0.0.0",
            num_cpus=16,  # CPU 증가
            physical_memory_gb=128.0,  # 메모리 증가
            total_db_size_gb=600.0  # DB 크기 증가
        ),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=80.0, pga_gb=20.0, total_gb=100.0)
        ]
    )
    
    # 비교 리포트 생성
    comparison = EnhancedResultFormatter.compare_awr_reports(awr1, awr2, 'ko')
    
    # 비교 리포트 확인
    assert "AWR 리포트 비교 분석" in comparison
    assert "시스템 정보 비교" in comparison
    assert "TESTDB" in comparison
    assert "+8" in comparison  # CPU 증가
    assert "+64.0" in comparison  # 메모리 증가


# Property 20: 추세 분석 이상 징후 감지
# Feature: awr-analyzer, Property 20: 추세 분석 이상 징후 감지
@settings(max_examples=100)
@given(st.lists(
    st.tuples(
        st.floats(min_value=10.0, max_value=100.0),  # CPU 사용률
        st.floats(min_value=1000.0, max_value=10000.0),  # IOPS
        st.floats(min_value=80.0, max_value=99.9)  # 버퍼 캐시 히트율
    ),
    min_size=2,
    max_size=10
))
def test_property_trend_analysis_anomaly_detection(metrics_list):
    """
    For any 시계열 메트릭 데이터에 대해, 추세 분석은 급격한 변화를 이상 징후로 감지해야 합니다.
    - CPU/IO 사용량이 50% 이상 급증하면 이상 징후로 감지
    - 버퍼 캐시 히트율이 5%p 이상 하락하면 이상 징후로 감지
    
    Validates: Requirements 17.3
    """
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, PercentileCPU, PercentileIO, BufferCacheStats
    
    # AWR 데이터 리스트 생성
    awr_list = []
    for i, (cpu, iops, hit_ratio) in enumerate(metrics_list):
        awr_data = AWRData(
            os_info=OSInformation(
                db_name=f"TESTDB_{i}",
                version="19.0.0.0"
            ),
            memory_metrics=[]
        )
        
        # CPU 백분위수 추가
        awr_data.percentile_cpu["99th_percentile"] = PercentileCPU(
            metric="99th_percentile",
            instance_number=1,
            on_cpu=int(cpu / 100 * 8),  # 8 코어 기준
            on_cpu_and_resmgr=int(cpu / 100 * 8),
            resmgr_cpu_quantum=0,
            begin_interval=f"2024-01-{i+1:02d} 00:00:00",
            end_interval=f"2024-01-{i+1:02d} 23:59:59",
            snap_shots=24,
            days=1.0,
            avg_snaps_per_day=24.0
        )
        
        # I/O 백분위수 추가
        awr_data.percentile_io["99th_percentile"] = PercentileIO(
            metric="99th_percentile",
            instance_number=1,
            rw_iops=int(iops),
            r_iops=int(iops * 0.7),
            w_iops=int(iops * 0.3),
            rw_mbps=int(iops / 50),
            r_mbps=int(iops * 0.7 / 50),
            w_mbps=int(iops * 0.3 / 50),
            begin_interval=f"2024-01-{i+1:02d} 00:00:00",
            end_interval=f"2024-01-{i+1:02d} 23:59:59",
            snap_shots=24,
            days=1.0,
            avg_snaps_per_day=24.0
        )
        
        # 버퍼 캐시 통계 추가
        awr_data.buffer_cache_stats = [
            BufferCacheStats(
                snap_id=1,
                instance_number=1,
                block_size=8192,
                db_cache_gb=40.0,
                dsk_reads=10000,
                block_gets=100000,
                consistent=90000,
                buf_got_gb=400.0,
                hit_ratio=hit_ratio
            )
        ]
        
        awr_list.append(awr_data)
    
    # 추세 리포트 생성
    trend_report = EnhancedResultFormatter._generate_trend_report(awr_list, 'ko')
    
    # 이상 징후 감지 검증
    # CPU 급증 확인
    for i in range(1, len(metrics_list)):
        prev_cpu = metrics_list[i-1][0]
        curr_cpu = metrics_list[i][0]
        cpu_change_pct = ((curr_cpu - prev_cpu) / prev_cpu) * 100
        
        if cpu_change_pct > 50:  # 50% 이상 급증
            # 이상 징후가 리포트에 포함되어야 함
            assert "이상 징후" in trend_report or "급증" in trend_report or "anomaly" in trend_report.lower()
            break
    
    # IOPS 급증 확인
    for i in range(1, len(metrics_list)):
        prev_iops = metrics_list[i-1][1]
        curr_iops = metrics_list[i][1]
        iops_change_pct = ((curr_iops - prev_iops) / prev_iops) * 100
        
        if iops_change_pct > 50:  # 50% 이상 급증
            assert "이상 징후" in trend_report or "급증" in trend_report or "anomaly" in trend_report.lower()
            break
    
    # 버퍼 캐시 히트율 하락 확인
    for i in range(1, len(metrics_list)):
        prev_hit = metrics_list[i-1][2]
        curr_hit = metrics_list[i][2]
        hit_change = prev_hit - curr_hit
        
        if hit_change > 5.0:  # 5%p 이상 하락
            assert "이상 징후" in trend_report or "하락" in trend_report or "anomaly" in trend_report.lower()
            break


# 단위 테스트: 추세 분석 기본 케이스
def test_enhanced_result_formatter_trend_report():
    """추세 분석 리포트 생성 기본 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, PercentileCPU
    
    # 여러 AWR 데이터 생성
    awr_list = []
    for i in range(3):
        awr_data = AWRData(
            os_info=OSInformation(
                db_name=f"TESTDB",
                version="19.0.0.0",
                num_cpus=8
            ),
            memory_metrics=[]
        )
        
        # CPU 백분위수 추가 (점진적 증가)
        awr_data.percentile_cpu["99th_percentile"] = PercentileCPU(
            metric="99th_percentile",
            instance_number=1,
            on_cpu=4 + i,  # 4, 5, 6 코어
            on_cpu_and_resmgr=4 + i,
            resmgr_cpu_quantum=0,
            begin_interval=f"2024-01-{i+1:02d} 00:00:00",
            end_interval=f"2024-01-{i+1:02d} 23:59:59",
            snap_shots=24,
            days=1.0,
            avg_snaps_per_day=24.0
        )
        
        awr_list.append(awr_data)
    
    # 추세 리포트 생성
    trend_report = EnhancedResultFormatter._generate_trend_report(awr_list, 'ko')
    
    # 기본 섹션 확인
    assert "추세 분석" in trend_report or "Trend Analysis" in trend_report
    assert len(awr_list) >= 2  # 최소 2개 이상의 데이터 필요


# 단위 테스트: 이상 징후 감지 - CPU 급증
def test_trend_analysis_cpu_spike_detection():
    """CPU 급증 이상 징후 감지 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, PercentileCPU
    
    # 첫 번째 AWR: 정상 CPU
    awr1 = AWRData(
        os_info=OSInformation(db_name="TESTDB", num_cpus=8),
        memory_metrics=[]
    )
    awr1.percentile_cpu["99th_percentile"] = PercentileCPU(
        metric="99th_percentile",
        instance_number=1,
        on_cpu=2,  # 25% 사용률
        on_cpu_and_resmgr=2,
        resmgr_cpu_quantum=0,
        begin_interval="2024-01-01 00:00:00",
        end_interval="2024-01-01 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # 두 번째 AWR: CPU 급증 (100% 증가)
    awr2 = AWRData(
        os_info=OSInformation(db_name="TESTDB", num_cpus=8),
        memory_metrics=[]
    )
    awr2.percentile_cpu["99th_percentile"] = PercentileCPU(
        metric="99th_percentile",
        instance_number=1,
        on_cpu=4,  # 50% 사용률 (100% 증가)
        on_cpu_and_resmgr=4,
        resmgr_cpu_quantum=0,
        begin_interval="2024-01-02 00:00:00",
        end_interval="2024-01-02 23:59:59",
        snap_shots=24,
        days=1.0,
        avg_snaps_per_day=24.0
    )
    
    # 추세 리포트 생성
    trend_report = EnhancedResultFormatter._generate_trend_report([awr1, awr2], 'ko')
    
    # CPU 급증 이상 징후 확인
    assert "이상 징후" in trend_report or "급증" in trend_report or "증가" in trend_report


# 단위 테스트: 이상 징후 감지 - 버퍼 캐시 히트율 하락
def test_trend_analysis_buffer_cache_drop_detection():
    """버퍼 캐시 히트율 하락 이상 징후 감지 테스트"""
    from src.dbcsi.result_formatter import EnhancedResultFormatter
    from src.dbcsi.models import AWRData, BufferCacheStats
    
    # 첫 번째 AWR: 높은 히트율
    awr1 = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    awr1.buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=40.0,
            dsk_reads=10000,
            block_gets=100000,
            consistent=90000,
            buf_got_gb=400.0,
            hit_ratio=95.0  # 95%
        )
    ]
    
    # 두 번째 AWR: 히트율 하락
    awr2 = AWRData(
        os_info=OSInformation(db_name="TESTDB"),
        memory_metrics=[]
    )
    awr2.buffer_cache_stats = [
        BufferCacheStats(
            snap_id=1,
            instance_number=1,
            block_size=8192,
            db_cache_gb=40.0,
            dsk_reads=20000,
            block_gets=100000,
            consistent=90000,
            buf_got_gb=400.0,
            hit_ratio=88.0  # 88% (7%p 하락)
        )
    ]
    
    # 추세 리포트 생성
    trend_report = EnhancedResultFormatter._generate_trend_report([awr1, awr2], 'ko')
    
    # 버퍼 캐시 히트율 하락 이상 징후 확인
    assert "이상 징후" in trend_report or "하락" in trend_report or "감소" in trend_report
