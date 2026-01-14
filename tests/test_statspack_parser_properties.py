"""
StatspackParser 속성 기반 테스트

Hypothesis를 사용하여 StatspackParser의 보편적 속성을 검증합니다.
"""

import pytest
import tempfile
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from src.statspack.parser import (
    StatspackParser,
    StatspackParseError,
    StatspackFileError,
)


# 테스트용 유효한 Statspack 섹션 생성 전략
@st.composite
def valid_statspack_section(draw, section_name="TEST-SECTION"):
    """유효한 Statspack 섹션 데이터 생성"""
    # 섹션 내부 데이터 (최소 1줄 이상)
    num_lines = draw(st.integers(min_value=1, max_value=10))
    data_lines = [
        draw(st.text(
            min_size=1, 
            max_size=100, 
            alphabet=st.characters(
                min_codepoint=0x20,  # 공백
                max_codepoint=0x7E,  # ~
                blacklist_characters=['\n', '\r']
            )
        ))
        for _ in range(num_lines)
    ]
    
    # 섹션 마커로 감싸기
    lines = [f"~~BEGIN-{section_name}~~"]
    lines.extend(data_lines)
    lines.append(f"~~END-{section_name}~~")
    
    return "\n".join(lines)


# Feature: statspack-analyzer, Property 1: 파일 파싱 시작
@given(st.text(min_size=50, max_size=1000))
@settings(max_examples=100)
def test_property_file_parsing_starts(content):
    """
    Property 1: 파일 파싱 시작
    
    For any 유효한 .out 확장자를 가진 파일 경로에 대해,
    StatspackParser는 파일을 읽고 파싱을 시작해야 합니다.
    
    Validates: Requirements 1.1
    """
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 파서 생성 - 예외가 발생하지 않아야 함
        parser = StatspackParser(temp_path)
        
        # 파일 읽기 시도 - 예외가 발생하지 않아야 함
        lines = parser._read_file()
        
        # 파일이 읽혔는지 확인
        assert lines is not None
        assert isinstance(lines, list)
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Feature: statspack-analyzer, Property 2: 파일 읽기 오류 처리
def test_property_file_not_found_error():
    """
    Property 2: 파일 읽기 오류 처리
    
    For any 존재하지 않는 파일 경로에 대해,
    StatspackParser는 FileNotFoundError를 발생시켜야 합니다.
    
    Validates: Requirements 1.3
    """
    non_existent_path = "/tmp/non_existent_statspack_file_12345.out"
    
    # 파일이 존재하지 않는지 확인
    assert not os.path.exists(non_existent_path)
    
    # FileNotFoundError 발생 확인
    with pytest.raises(FileNotFoundError) as exc_info:
        StatspackParser(non_existent_path)
    
    # 에러 메시지에 파일 경로가 포함되어 있는지 확인
    assert non_existent_path in str(exc_info.value)


def test_property_directory_error():
    """
    Property 2: 파일 읽기 오류 처리 (디렉토리)
    
    For any 디렉토리 경로에 대해,
    StatspackParser는 StatspackFileError를 발생시켜야 합니다.
    
    Validates: Requirements 1.3
    """
    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        # StatspackFileError 발생 확인
        with pytest.raises(StatspackFileError) as exc_info:
            StatspackParser(temp_dir)
        
        # 에러 메시지 확인
        assert "directory" in str(exc_info.value).lower()


def test_property_permission_error():
    """
    Property 2: 파일 읽기 오류 처리 (권한)
    
    For any 읽기 권한이 없는 파일에 대해,
    StatspackParser는 StatspackFileError를 발생시켜야 합니다.
    
    Validates: Requirements 1.3
    """
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # 읽기 권한 제거
        os.chmod(temp_path, 0o000)
        
        # 파서 생성은 성공 (파일 존재 확인만 함)
        parser = StatspackParser(temp_path)
        
        # 파일 읽기 시 StatspackFileError 발생 확인
        with pytest.raises(StatspackFileError) as exc_info:
            parser._read_file()
        
        # 에러 메시지 확인
        assert "Permission denied" in str(exc_info.value) or "Failed to read" in str(exc_info.value)
        
    finally:
        # 권한 복구 후 삭제
        try:
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)
        except:
            pass


# Feature: statspack-analyzer, Property 3: 인코딩 자동 처리
@given(st.text(min_size=10, max_size=500, alphabet=st.characters(
    min_codepoint=0x20, max_codepoint=0x7E  # ASCII 출력 가능 문자
)))
@settings(max_examples=100)
def test_property_utf8_encoding(content):
    """
    Property 3: 인코딩 자동 처리 (UTF-8)
    
    For any UTF-8로 인코딩 가능한 텍스트에 대해,
    StatspackParser는 파일을 정상적으로 읽어야 합니다.
    
    Validates: Requirements 1.4
    """
    # UTF-8로 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 파일이 정상적으로 읽혔는지 확인
        assert lines is not None
        assert isinstance(lines, list)
        
        # 내용이 일치하는지 확인
        read_content = ''.join(lines)
        assert content in read_content or read_content.strip() == content.strip()
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_property_latin1_fallback():
    """
    Property 3: 인코딩 자동 처리 (Latin-1 폴백)
    
    For any UTF-8로 디코딩할 수 없는 파일에 대해,
    StatspackParser는 Latin-1로 폴백하여 파일을 읽어야 합니다.
    
    Validates: Requirements 1.4
    """
    # Latin-1 전용 바이트 시퀀스 (UTF-8로 디코딩 불가)
    latin1_content = b"Test content with Latin-1 chars: \xe9\xe0\xe8"
    
    # Latin-1로 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.out', delete=False) as f:
        f.write(latin1_content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 파일이 정상적으로 읽혔는지 확인
        assert lines is not None
        assert isinstance(lines, list)
        assert len(lines) > 0
        
        # Latin-1로 디코딩한 내용과 일치하는지 확인
        expected_content = latin1_content.decode('latin-1')
        read_content = ''.join(lines)
        assert expected_content in read_content or read_content.strip() == expected_content.strip()
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Feature: statspack-analyzer, Property 3: 인코딩 자동 처리 (혼합)
def test_property_encoding_auto_detection():
    """
    Property 3: 인코딩 자동 처리 (자동 감지)
    
    For any 파일에 대해, StatspackParser는 UTF-8을 먼저 시도하고
    실패하면 Latin-1로 폴백하여 파일을 읽어야 합니다.
    
    Validates: Requirements 1.4
    """
    test_cases = [
        # (content, encoding, description)
        (b"Simple ASCII text", 'utf-8', "ASCII (UTF-8 호환)"),
        (b"UTF-8 text: \xc3\xa9\xc3\xa0\xc3\xa8", 'utf-8', "UTF-8 멀티바이트"),
        (b"Latin-1 text: \xe9\xe0\xe8", 'latin-1', "Latin-1 전용"),
    ]
    
    for content, expected_encoding, description in test_cases:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.out', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = StatspackParser(temp_path)
            lines = parser._read_file()
            
            # 파일이 정상적으로 읽혔는지 확인
            assert lines is not None, f"Failed to read {description}"
            assert isinstance(lines, list), f"Invalid return type for {description}"
            assert len(lines) > 0, f"Empty result for {description}"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)



# ============================================================================
# 섹션 추출 속성 테스트
# ============================================================================

# Feature: statspack-analyzer, Property 4: 최소 섹션 데이터 추출
@given(valid_statspack_section())
@settings(max_examples=100)
def test_property_minimum_section_extraction(section_content):
    """
    Property 4: 최소 섹션 데이터 추출
    
    For any 유효한 Statspack 파일에 대해,
    파싱 후 최소한 하나 이상의 섹션 데이터가 추출되어야 합니다.
    
    Validates: Requirements 1.5
    """
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(section_content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 섹션 추출
        section_data = parser._extract_section(lines, "TEST-SECTION")
        
        # 최소한 하나 이상의 데이터 라인이 있어야 함
        assert len(section_data) > 0, "섹션에서 최소한 하나의 데이터 라인이 추출되어야 합니다"
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Feature: statspack-analyzer, Property 5: 섹션 마커 인식
@given(
    section_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),  # 대문자, 소문자, 숫자
        whitelist_characters='-_'
    )),
    data_lines=st.lists(
        st.text(
            min_size=1, 
            max_size=100,
            alphabet=st.characters(
                min_codepoint=0x21,  # ! (공백 제외)
                max_codepoint=0x7E,
                blacklist_characters=['\n', '\r']
            )
        ), 
        min_size=1, 
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_section_marker_recognition(section_name, data_lines):
    """
    Property 5: 섹션 마커 인식
    
    For any 유효한 섹션 이름에 대해,
    ~~BEGIN-{SECTION_NAME}~~ 마커를 만나면 해당 섹션의 시작으로 인식하고,
    ~~END-{SECTION_NAME}~~ 마커를 만나면 종료로 인식해야 합니다.
    
    Validates: Requirements 2.1, 2.2
    """
    # 섹션 이름이 비어있지 않은지 확인
    assume(section_name.strip() != "")
    
    # 섹션 콘텐츠 생성
    content_lines = [f"~~BEGIN-{section_name}~~"]
    content_lines.extend(data_lines)
    content_lines.append(f"~~END-{section_name}~~")
    content = "\n".join(content_lines)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 섹션 추출
        section_data = parser._extract_section(lines, section_name)
        
        # 데이터가 추출되었는지 확인
        assert len(section_data) > 0, f"섹션 '{section_name}'의 데이터가 추출되어야 합니다"
        
        # 추출된 데이터 개수가 원본 데이터 라인 수와 일치하는지 확인
        # (공백만 있는 라인은 제거되므로 비어있지 않은 라인만 카운트)
        non_empty_lines = [line for line in data_lines if line.strip()]
        assert len(section_data) == len(non_empty_lines), \
            f"추출된 데이터 라인 수({len(section_data)})가 비어있지 않은 원본 라인 수({len(non_empty_lines)})와 일치해야 합니다"
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Feature: statspack-analyzer, Property 6: 섹션 데이터 추출
@given(
    data_lines=st.lists(
        st.text(
            min_size=1, 
            max_size=100,
            alphabet=st.characters(
                min_codepoint=0x20,
                max_codepoint=0x7E,
                blacklist_characters=['\n', '\r']
            )
        ), 
        min_size=1, 
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_section_data_extraction(data_lines):
    """
    Property 6: 섹션 데이터 추출
    
    For any 섹션에 대해,
    시작과 종료 마커 사이의 데이터를 추출할 때
    마커 라인을 제외한 순수 데이터만 반환해야 합니다.
    
    Validates: Requirements 2.3
    """
    section_name = "TEST-DATA"
    
    # 섹션 콘텐츠 생성
    content_lines = [f"~~BEGIN-{section_name}~~"]
    content_lines.extend(data_lines)
    content_lines.append(f"~~END-{section_name}~~")
    content = "\n".join(content_lines)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 섹션 추출
        section_data = parser._extract_section(lines, section_name)
        
        # 마커가 포함되지 않았는지 확인
        for line in section_data:
            assert "~~BEGIN-" not in line, "시작 마커가 데이터에 포함되면 안 됩니다"
            assert "~~END-" not in line, "종료 마커가 데이터에 포함되면 안 됩니다"
        
        # 빈 라인과 공백만 있는 라인은 제거되므로, 비어있지 않은 라인만 카운트
        # (Requirements 2.5: 빈 라인과 공백만 있는 라인은 자동으로 제거되어야 합니다)
        non_empty_lines = [line for line in data_lines if line.strip()]
        assert len(section_data) == len(non_empty_lines), \
            f"추출된 데이터는 마커를 제외하고 빈 라인을 제거한 순수 데이터만 포함해야 합니다 (추출: {len(section_data)}, 예상: {len(non_empty_lines)})"
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Feature: statspack-analyzer, Property 7: 빈 라인 제거
@given(
    data_lines=st.lists(
        st.one_of(
            st.text(
                min_size=1, 
                max_size=100,
                alphabet=st.characters(
                    min_codepoint=0x21,  # ! (공백 제외)
                    max_codepoint=0x7E
                )
            ),  # 일반 텍스트
            st.just(""),  # 빈 라인
            st.sampled_from([" ", "  ", "\t", " \t", "   "])  # 공백만
        ),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100)
def test_property_empty_line_removal(data_lines):
    """
    Property 7: 빈 라인 제거
    
    For any 섹션에 대해,
    빈 라인과 공백만 있는 라인은 자동으로 제거되어야 합니다.
    
    Validates: Requirements 2.5
    """
    section_name = "TEST-EMPTY"
    
    # 섹션 콘텐츠 생성
    content_lines = [f"~~BEGIN-{section_name}~~"]
    content_lines.extend(data_lines)
    content_lines.append(f"~~END-{section_name}~~")
    content = "\n".join(content_lines)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # 섹션 추출
        section_data = parser._extract_section(lines, section_name)
        
        # 추출된 데이터에 빈 라인이나 공백만 있는 라인이 없는지 확인
        for line in section_data:
            assert line.strip() != "", "빈 라인이나 공백만 있는 라인은 제거되어야 합니다"
        
        # 원본에서 비어있지 않은 라인 수 계산
        non_empty_count = sum(1 for line in data_lines if line.strip())
        
        # 추출된 데이터 라인 수가 비어있지 않은 라인 수와 일치하는지 확인
        assert len(section_data) == non_empty_count, \
            f"추출된 라인 수({len(section_data)})가 비어있지 않은 라인 수({non_empty_count})와 일치해야 합니다"
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_property_section_without_end_marker():
    """
    Property 5: 섹션 마커 인식 (종료 마커 없음)
    
    For any 종료 마커가 없는 섹션에 대해,
    다음 섹션 시작 또는 파일 끝까지를 해당 섹션으로 간주해야 합니다.
    
    Validates: Requirements 2.4
    """
    content = """~~BEGIN-SECTION1~~
Data line 1
Data line 2
~~BEGIN-SECTION2~~
Data line 3
"""
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        lines = parser._read_file()
        
        # SECTION1 추출 (종료 마커 없음)
        section1_data = parser._extract_section(lines, "SECTION1")
        
        # SECTION1은 다음 섹션 시작 전까지의 데이터를 포함해야 함
        assert len(section1_data) == 2, "종료 마커가 없으면 다음 섹션 시작 전까지 추출해야 합니다"
        assert "Data line 1" in section1_data[0]
        assert "Data line 2" in section1_data[1]
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_property_parse_requires_section():
    """
    Property 4: 최소 섹션 데이터 추출 (섹션 없음)
    
    For any 섹션 마커가 없는 파일에 대해,
    parse() 메서드는 StatspackParseError를 발생시켜야 합니다.
    
    Validates: Requirements 1.5
    """
    content = "This is just plain text without any section markers"
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        parser = StatspackParser(temp_path)
        
        # parse() 호출 시 StatspackParseError 발생 확인
        with pytest.raises(StatspackParseError) as exc_info:
            parser.parse()
        
        # 에러 메시지 확인
        assert "No valid section markers" in str(exc_info.value)
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
