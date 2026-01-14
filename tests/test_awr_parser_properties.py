"""
AWR 파서 속성 기반 테스트

Property-based testing을 사용하여 AWR 파서의 정확성을 검증합니다.
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import assume
import tempfile
import os

from src.dbcsi.parser import AWRParser
from src.dbcsi.data_models import (
    IOStatFunction, PercentileCPU, PercentileIO,
    WorkloadProfile, BufferCacheStats, AWRData
)


# 테스트 데이터 생성 전략

@st.composite
def iostat_function_line(draw):
    """IOSTAT-FUNCTION 라인 생성"""
    snap_id = draw(st.integers(min_value=1, max_value=1000))
    function_names = ["LGWR", "DBWR", "Direct Writes", "Direct Reads", "Others"]
    function_name = draw(st.sampled_from(function_names))
    megabytes_per_s = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
    return f"        {snap_id} {function_name:<20} {megabytes_per_s:>19.1f}"


@st.composite
def iostat_section(draw):
    """IOSTAT-FUNCTION 섹션 생성"""
    num_lines = draw(st.integers(min_value=1, max_value=50))
    lines = [draw(iostat_function_line()) for _ in range(num_lines)]
    
    header = """~~BEGIN-IOSTAT-FUNCTION~~

   SNAP_ID FUNCTION_NAME        megabytes_val_per_s
---------- -------------------- -------------------
"""
    footer = "\n~~END-IOSTAT-FUNCTION~~"
    
    return header + "\n".join(lines) + footer


def minimal_statspack_content() -> str:
    """최소한의 Statspack 섹션 생성 (AWR 파서가 Statspack 호환성을 유지하기 위함)"""
    os_info = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
AWR_MINER_VER                                                4.0.11.aws.62
DB_NAME                                                      TESTDB
NUM_CPUS                                                     4
PHYSICAL_MEMORY_GB                                           8
~~END-OS-INFORMATION~~
"""
    
    memory = """~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------
        17               1        4.5         .2        4.7
~~END-MEMORY~~
"""
    
    return os_info + "\n" + memory


def create_temp_awr_file(content: str) -> str:
    """임시 AWR 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
        f.write(content)
        return f.name


# Feature: awr-analyzer, Property 4: IOSTAT 필수 필드
@given(iostat_section())
@settings(max_examples=100, deadline=None)
def test_property_iostat_required_fields(iostat_content):
    """
    For any 파싱된 IOSTAT 레코드에 대해, SNAP_ID와 FUNCTION_NAME 필드는 반드시 존재해야 합니다.
    
    **Validates: Requirements 2.6**
    """
    # AWR 파일 생성
    statspack_content = minimal_statspack_content()
    full_content = statspack_content + "\n" + iostat_content
    
    filepath = create_temp_awr_file(full_content)
    
    try:
        # 파싱
        parser = AWRParser(filepath)
        awr_data = parser.parse()
        
        # 검증: 모든 IOSTAT 레코드는 snap_id와 function_name을 가져야 함
        for iostat in awr_data.iostat_functions:
            assert iostat.snap_id is not None, "SNAP_ID must not be None"
            assert iostat.function_name is not None, "FUNCTION_NAME must not be None"
            assert iostat.function_name != "", "FUNCTION_NAME must not be empty"
            assert isinstance(iostat.snap_id, int), "SNAP_ID must be an integer"
            assert isinstance(iostat.function_name, str), "FUNCTION_NAME must be a string"
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(filepath):
            os.unlink(filepath)


# Feature: awr-analyzer, Property 1: Statspack 호환성
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=50, deadline=None)
def test_property_statspack_compatibility(db_name):
    """
    For any 유효한 AWR 파일에 대해, AWR 파서는 기존 Statspack 섹션을 모두 파싱해야 합니다.
    
    **Validates: Requirements 1.1**
    """
    # 유효한 문자만 사용
    db_name = ''.join(c for c in db_name if c.isalnum() or c in ['_', '-'])
    assume(len(db_name) > 0)
    
    # Statspack 섹션이 있는 AWR 파일 생성
    content = f"""~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
AWR_MINER_VER                                                4.0.11.aws.62
DB_NAME                                                      {db_name}
NUM_CPUS                                                     4
PHYSICAL_MEMORY_GB                                           8
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------
        17               1        4.5         .2        4.7
~~END-MEMORY~~

~~BEGIN-SIZE-ON-DISK~~

   SNAP_ID    SIZE_GB
---------- ----------
        17       1.39
~~END-SIZE-ON-DISK~~

~~BEGIN-MAIN-METRICS~~

      snap      dur_m end                  inst     cpu_per_s  read_iops read_mb_s write_iops write_mb_s  commits_s
---------- ---------- -------------- ---------- ------------- ---------- --------- ---------- ---------- ----------
        17         50 26/01/11 22:32          1          .004        7.5       .1        7.3        .1          0
~~END-MAIN-METRICS~~
"""
    
    filepath = create_temp_awr_file(content)
    
    try:
        # 파싱
        parser = AWRParser(filepath)
        awr_data = parser.parse()
        
        # 검증: Statspack 섹션이 모두 파싱되어야 함
        assert awr_data.os_info is not None, "OS information must be parsed"
        assert awr_data.os_info.db_name == db_name, "DB name must match"
        assert len(awr_data.memory_metrics) > 0, "Memory metrics must be parsed"
        assert len(awr_data.disk_sizes) > 0, "Disk sizes must be parsed"
        assert len(awr_data.main_metrics) > 0, "Main metrics must be parsed"
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(filepath):
            os.unlink(filepath)


# Feature: awr-analyzer, Property 3: AWR 섹션 누락 처리
@given(st.booleans(), st.booleans(), st.booleans())
@settings(max_examples=50, deadline=None)
def test_property_awr_section_missing(has_iostat, has_percentile_cpu, has_buffer_cache):
    """
    For any AWR 특화 섹션이 없는 파일에 대해, AWR 파서는 경고 없이 파싱을 완료하고 
    해당 필드를 None 또는 빈 리스트로 설정해야 합니다.
    
    **Validates: Requirements 1.4**
    """
    # 기본 Statspack 섹션
    content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
AWR_MINER_VER                                                4.0.11.aws.62
DB_NAME                                                      TESTDB
NUM_CPUS                                                     4
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------
        17               1        4.5         .2        4.7
~~END-MEMORY~~
"""
    
    # 선택적으로 AWR 섹션 추가
    if has_iostat:
        content += """
~~BEGIN-IOSTAT-FUNCTION~~

   SNAP_ID FUNCTION_NAME        megabytes_val_per_s
---------- -------------------- -------------------
        18 LGWR                                   1
~~END-IOSTAT-FUNCTION~~
"""
    
    if has_percentile_cpu:
        content += """
~~BEGIN-PERCENT-CPU~~

      DBID   ORDER_BY METRIC               INSTANCE_NUMBER     ON_CPU ON_CPU_AND_RESMGR RESMGR_CPU_QUANTUM BEGIN_INTERVAL_T END_INTERVAL_TIM SNAP_SHOTS       DAYS AVG_SNAPS_PER_DAY
---------- ---------- -------------------- --------------- ---------- ----------------- ------------------ ---------------- ---------------- ---------- ---------- -----------------
 595413474          4 99th_percentile                    1          2                 2                  0 2025-12-15 07:47 2026-01-12 00:10          3       27.7                .1
~~END-PERCENT-CPU~~
"""
    
    if has_buffer_cache:
        content += """
~~BEGIN-BUFFER-CACHE~~

        SNAP_ID INSTANCE_NUMBER      BLOCK_SIZE     DB_CACHE_GB       DSK_READS      BLOCK_GETS      CONSISTENT      BUF_GOT_GB       HIT_RATIO
--------------- --------------- --------------- --------------- --------------- --------------- --------------- --------------- ---------------
             18               1            8192 3.3180084228516           28045          465428         1793035 .32508850097656           98.76
~~END-BUFFER-CACHE~~
"""
    
    filepath = create_temp_awr_file(content)
    
    try:
        # 파싱 (예외가 발생하지 않아야 함)
        parser = AWRParser(filepath)
        awr_data = parser.parse()
        
        # 검증: AWR 섹션이 없으면 빈 리스트 또는 빈 딕셔너리여야 함
        if has_iostat:
            assert len(awr_data.iostat_functions) > 0
        else:
            assert len(awr_data.iostat_functions) == 0
        
        if has_percentile_cpu:
            assert len(awr_data.percentile_cpu) > 0
        else:
            assert len(awr_data.percentile_cpu) == 0
        
        if has_buffer_cache:
            assert len(awr_data.buffer_cache_stats) > 0
        else:
            assert len(awr_data.buffer_cache_stats) == 0
        
        # 기본 Statspack 섹션은 항상 파싱되어야 함
        assert awr_data.os_info is not None
        assert len(awr_data.memory_metrics) > 0
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(filepath):
            os.unlink(filepath)



# Feature: awr-analyzer, Property 8: 유휴 이벤트 제외
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50, deadline=None)
def test_property_idle_event_exclusion(num_idle_events):
    """
    For any "*** IDLE ***" 이벤트를 포함한 워크로드 데이터에 대해, 
    해당 이벤트는 분석에서 제외되어야 합니다.
    
    **Validates: Requirements 5.4**
    """
    # IDLE 이벤트와 일반 이벤트가 섞인 워크로드 섹션 생성
    workload_lines = []
    
    # IDLE 이벤트 추가 - 고정 폭 형식 준수
    # SAMPLESTART (23자) + TOPN (16자) + MODULE (65자) + PROGRAM (65자) + EVENT (65자) + 숫자 필드들
    for i in range(num_idle_events):
        hour = (i * 2) % 24
        # 각 필드를 정확한 폭으로 생성
        sample_start = f"11-1월 -26 {hour:02d}:00:00".ljust(23)  # 23자
        topn = "1".rjust(16)  # 16자
        module = "".ljust(65)  # 65자 (빈 값)
        program = "".ljust(65)  # 65자 (빈 값)
        event = "*** IDLE ***".ljust(65)  # 65자
        # 숫자 필드들 (공백으로 구분)
        numeric_fields = "0 0 0 0 FOREGROUND 0 0 0 0 0 0 0 0 0 0 0 0"
        
        line = sample_start + topn + module + program + event + numeric_fields
        workload_lines.append(line)
    
    # 일반 이벤트 추가 - 고정 폭 형식 준수
    sample_start = "11-1월 -26 22:00:00".ljust(23)
    topn = "1".rjust(16)
    module = "SQL*Plus".ljust(65)
    program = "sqlplus@oracle-12c (TNS V1-V3)".ljust(65)
    event = "CPU + CPU Wait".ljust(65)
    numeric_fields = "90 0.01666666666667 0.66666666666667 1 FOREGROUND 4798 1834 182091776 348867584 0.68250355618777 0.99081577525662 0.90671017744238 0.9798897271365 7030 1851 200826880 356027392"
    
    line = sample_start + topn + module + program + event + numeric_fields
    workload_lines.append(line)
    
    workload_content = """~~BEGIN-WORKLOAD~~

SAMPLESTART                        TOPN MODULE                                                           PROGRAM                                                          EVENT                                                            TOTAL_DBTIME_SUM        AAS_COMP AAS_CONTRIBUTION_PCT TOT_CONTRIBUTIONS SESSION_TY WAIT_CLASS           DELTA_READ_IO_REQUESTS DELTA_WRITE_IO_REQUESTS DELTA_READ_IO_BYTES DELTA_WRITE_IO_BYTES        RIOR_PCT        WIOR_PCT        RIOB_PCT        WIOB_PCT        RIOR_TOT        WIOR_TOT        RIOB_TOT        WIOB_TOT
----------------------- --------------- ---------------------------------------------------------------- ---------------------------------------------------------------- ---------------------------------------------------------------- ---------------- --------------- -------------------- ----------------- ---------- -------------------- ---------------------- ----------------------- ------------------- -------------------- --------------- --------------- --------------- --------------- --------------- --------------- --------------- ---------------
""" + "\n".join(workload_lines) + "\n~~END-WORKLOAD~~"
    
    # AWR 파일 생성
    statspack_content = minimal_statspack_content()
    full_content = statspack_content + "\n" + workload_content
    
    filepath = create_temp_awr_file(full_content)
    
    try:
        # 파싱
        parser = AWRParser(filepath)
        awr_data = parser.parse()
        
        # 검증: IDLE 이벤트는 파싱되지만, 분석 시 제외되어야 함
        # 여기서는 파싱만 확인 (분석은 MigrationAnalyzer에서 수행)
        idle_events = [w for w in awr_data.workload_profiles if "IDLE" in w.event]
        non_idle_events = [w for w in awr_data.workload_profiles if "IDLE" not in w.event]
        
        # IDLE 이벤트가 파싱되었는지 확인
        assert len(idle_events) == num_idle_events, f"Expected {num_idle_events} IDLE events, got {len(idle_events)}"
        
        # 일반 이벤트도 파싱되었는지 확인
        assert len(non_idle_events) == 1, f"Expected 1 non-IDLE event, got {len(non_idle_events)}"
        
        # IDLE 이벤트는 total_dbtime_sum이 0이어야 함
        for idle_event in idle_events:
            assert idle_event.total_dbtime_sum == 0, "IDLE events should have zero DB time"
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(filepath):
            os.unlink(filepath)
