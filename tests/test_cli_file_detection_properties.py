"""
CLI 파일 타입 감지 속성 기반 테스트

Feature: awr-analyzer, Property 19: 파일 타입 자동 감지
Validates: Requirements 16.5

For any AWR 또는 Statspack 파일에 대해, CLI는 파일 타입을 자동으로 감지하여 
적절한 파서를 사용해야 합니다.
"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from src.utils.cli_helpers import detect_file_type
from src.dbcsi.cli import detect_and_parse
from src.dbcsi.parsers import StatspackParser, AWRParser


# AWR 마커 전략
awr_markers = st.sampled_from([
    "~~BEGIN-IOSTAT-FUNCTION~~",
    "~~BEGIN-PERCENT-CPU~~",
    "~~BEGIN-PERCENT-IO~~",
    "~~BEGIN-WORKLOAD~~",
    "~~BEGIN-BUFFER-CACHE~~"
])

# 기본 Statspack 섹션 전략
statspack_sections = st.sampled_from([
    "~~BEGIN-OS-INFORMATION~~",
    "~~BEGIN-MEMORY~~",
    "~~BEGIN-MAIN-METRICS~~",
    "~~BEGIN-SIZE-ON-DISK~~",
    "~~BEGIN-TOP-N-TIMED-EVENTS~~",
    "~~BEGIN-SYSSTAT~~",
    "~~BEGIN-FEATURES~~",
    "~~BEGIN-SGA-ADVICE~~"
])


def generate_file_content(include_awr_marker: bool, num_sections: int = 3) -> str:
    """
    테스트용 파일 내용 생성
    
    Args:
        include_awr_marker: AWR 마커 포함 여부
        num_sections: 포함할 섹션 수
        
    Returns:
        파일 내용 문자열
    """
    content = []
    
    # 기본 OS-INFORMATION 섹션 추가
    content.append("~~BEGIN-OS-INFORMATION~~")
    content.append("STATSPACK_MINER_VER 1.0")
    content.append("NUM_CPUS 4")
    content.append("~~END-OS-INFORMATION~~")
    content.append("")
    
    # AWR 마커 추가 (선택적)
    if include_awr_marker:
        content.append("~~BEGIN-IOSTAT-FUNCTION~~")
        content.append("SNAP_ID FUNCTION_NAME MEGABYTES_PER_S")
        content.append("1 LGWR 10.5")
        content.append("~~END-IOSTAT-FUNCTION~~")
        content.append("")
    
    # 추가 Statspack 섹션
    if num_sections > 1:
        content.append("~~BEGIN-MEMORY~~")
        content.append("SNAP_ID INSTANCE_NUMBER SGA_GB PGA_GB TOTAL_GB")
        content.append("1 1 10.0 2.0 12.0")
        content.append("~~END-MEMORY~~")
        content.append("")
    
    if num_sections > 2:
        content.append("~~BEGIN-MAIN-METRICS~~")
        content.append("SNAP DUR_M END INST CPU_PER_S READ_IOPS READ_MB_S WRITE_IOPS WRITE_MB_S COMMITS_S")
        content.append("1 60 2024-01-01 1 50.0 100.0 10.0 50.0 5.0 10.0")
        content.append("~~END-MAIN-METRICS~~")
        content.append("")
    
    return "\n".join(content)


# Feature: awr-analyzer, Property 19: 파일 타입 자동 감지
@given(
    include_awr_marker=st.booleans(),
    num_sections=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_property_file_type_detection(include_awr_marker, num_sections):
    """
    Property 19: 파일 타입 자동 감지
    
    For any 파일에 대해, AWR 마커가 있으면 "awr"로, 없으면 "statspack"으로 감지되어야 합니다.
    
    Validates: Requirements 16.5
    """
    # 테스트 파일 내용 생성
    content = generate_file_content(include_awr_marker, num_sections)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 파일 타입 감지
        detected_type = detect_file_type(temp_path)
        
        # 검증: AWR 마커가 있으면 "awr", 없으면 "statspack"
        if include_awr_marker:
            assert detected_type == "awr", \
                f"AWR 마커가 있는 파일이 {detected_type}로 감지됨"
        else:
            assert detected_type == "statspack", \
                f"AWR 마커가 없는 파일이 {detected_type}로 감지됨"
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink(missing_ok=True)


# Feature: awr-analyzer, Property 19: 파일 타입 자동 감지 (파서 선택)
@given(
    include_awr_marker=st.booleans(),
    num_sections=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_property_parser_selection(include_awr_marker, num_sections):
    """
    Property 19: 적절한 파서 선택
    
    For any 파일에 대해, AWR 파일은 AWRParser로, Statspack 파일은 StatspackParser로 파싱되어야 합니다.
    
    Validates: Requirements 16.5
    """
    # 테스트 파일 내용 생성
    content = generate_file_content(include_awr_marker, num_sections)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 파서 선택
        parser = detect_and_parse(temp_path)
        
        # 검증: AWR 파일은 AWRParser, Statspack 파일은 StatspackParser (AWRParser 아님)
        if include_awr_marker:
            assert isinstance(parser, AWRParser), \
                f"AWR 파일이 {type(parser).__name__}로 파싱됨"
        else:
            assert isinstance(parser, StatspackParser), \
                f"Statspack 파일이 {type(parser).__name__}로 파싱됨"
            assert not isinstance(parser, AWRParser), \
                f"Statspack 파일이 AWRParser로 파싱됨"
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink(missing_ok=True)


# Feature: awr-analyzer, Property 19: 다양한 AWR 마커 감지
@given(
    awr_marker=awr_markers,
    num_sections=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_property_various_awr_markers(awr_marker, num_sections):
    """
    Property 19: 다양한 AWR 마커 감지
    
    For any AWR 마커에 대해, 해당 마커가 있는 파일은 "awr"로 감지되어야 합니다.
    
    Validates: Requirements 16.5
    """
    # 기본 내용 생성
    content = []
    content.append("~~BEGIN-OS-INFORMATION~~")
    content.append("STATSPACK_MINER_VER 1.0")
    content.append("NUM_CPUS 4")
    content.append("~~END-OS-INFORMATION~~")
    content.append("")
    
    # 선택된 AWR 마커 추가
    content.append(awr_marker)
    content.append("TEST_DATA 123")
    # 종료 마커 생성
    end_marker = awr_marker.replace("BEGIN", "END")
    content.append(end_marker)
    content.append("")
    
    # 추가 섹션
    for i in range(num_sections):
        content.append("~~BEGIN-MEMORY~~")
        content.append(f"SNAP_ID INSTANCE_NUMBER SGA_GB PGA_GB TOTAL_GB")
        content.append(f"{i+1} 1 10.0 2.0 12.0")
        content.append("~~END-MEMORY~~")
        content.append("")
    
    file_content = "\n".join(content)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(file_content)
        temp_path = f.name
    
    try:
        # 파일 타입 감지
        detected_type = detect_file_type(temp_path)
        
        # 검증: AWR 마커가 있으므로 "awr"로 감지되어야 함
        assert detected_type == "awr", \
            f"AWR 마커 {awr_marker}가 있는 파일이 {detected_type}로 감지됨"
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink(missing_ok=True)


# Feature: awr-analyzer, Property 19: 인코딩 독립성
@given(
    include_awr_marker=st.booleans(),
    encoding=st.sampled_from(['utf-8', 'latin-1'])
)
@settings(max_examples=100, deadline=None)
def test_property_encoding_independence(include_awr_marker, encoding):
    """
    Property 19: 인코딩 독립성
    
    For any 인코딩(UTF-8, Latin-1)에 대해, 파일 타입 감지는 동일하게 작동해야 합니다.
    
    Validates: Requirements 16.5
    """
    # 테스트 파일 내용 생성
    content = generate_file_content(include_awr_marker, num_sections=2)
    
    # 임시 파일 생성 (지정된 인코딩 사용)
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.out', delete=False) as f:
        f.write(content.encode(encoding))
        temp_path = f.name
    
    try:
        # 파일 타입 감지
        detected_type = detect_file_type(temp_path)
        
        # 검증: 인코딩과 관계없이 올바르게 감지되어야 함
        if include_awr_marker:
            assert detected_type == "awr", \
                f"AWR 파일({encoding})이 {detected_type}로 감지됨"
        else:
            assert detected_type == "statspack", \
                f"Statspack 파일({encoding})이 {detected_type}로 감지됨"
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink(missing_ok=True)


# Feature: awr-analyzer, Property 19: 파일 크기 독립성
@given(
    include_awr_marker=st.booleans(),
    num_sections=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=50, deadline=None)
def test_property_file_size_independence(include_awr_marker, num_sections):
    """
    Property 19: 파일 크기 독립성
    
    For any 파일 크기에 대해, 파일 타입 감지는 동일하게 작동해야 합니다.
    
    Validates: Requirements 16.5
    """
    # 테스트 파일 내용 생성 (섹션 수를 늘려 파일 크기 증가)
    content = generate_file_content(include_awr_marker, num_sections)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 파일 타입 감지
        detected_type = detect_file_type(temp_path)
        
        # 검증: 파일 크기와 관계없이 올바르게 감지되어야 함
        if include_awr_marker:
            assert detected_type == "awr", \
                f"AWR 파일(섹션 {num_sections}개)이 {detected_type}로 감지됨"
        else:
            assert detected_type == "statspack", \
                f"Statspack 파일(섹션 {num_sections}개)이 {detected_type}로 감지됨"
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink(missing_ok=True)
