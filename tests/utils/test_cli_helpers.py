"""
CLI 헬퍼 함수 단위 테스트

src/utils/cli_helpers.py의 함수들을 테스트합니다.
"""

import pytest
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from src.utils.cli_helpers import (
    detect_file_type,
    generate_output_path,
    print_progress
)


class TestDetectFileType:
    """파일 타입 감지 테스트"""
    
    def test_detect_file_type_awr_from_filename(self):
        """파일명에 'awr'이 포함된 경우 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix="_awr_report.out", delete=False) as f:
            f.write(b"dummy content")
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_case_insensitive(self):
        """파일명의 AWR 키워드는 대소문자 무시"""
        with tempfile.NamedTemporaryFile(suffix="_AWR_report.out", delete=False) as f:
            f.write(b"dummy content")
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_statspack_from_filename(self):
        """파일명에 'statspack'이 포함된 경우 Statspack으로 감지"""
        with tempfile.NamedTemporaryFile(suffix="_statspack_report.out", delete=False) as f:
            f.write(b"dummy content")
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "statspack"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_statspack_case_insensitive(self):
        """파일명의 STATSPACK 키워드는 대소문자 무시"""
        with tempfile.NamedTemporaryFile(suffix="_STATSPACK_report.out", delete=False) as f:
            f.write(b"dummy content")
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "statspack"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_from_iostat_marker(self):
        """IOSTAT-FUNCTION 마커가 있는 파일은 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-IOSTAT-FUNCTION~~
SNAP_ID FUNCTION_NAME MEGABYTES_PER_S
1 LGWR 10.5
~~END-IOSTAT-FUNCTION~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_from_percent_cpu_marker(self):
        """PERCENT-CPU 마커가 있는 파일은 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-PERCENT-CPU~~
METRIC ON_CPU
99th_percentile 8
~~END-PERCENT-CPU~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_from_percent_io_marker(self):
        """PERCENT-IO 마커가 있는 파일은 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-PERCENT-IO~~
METRIC RW_IOPS
99th_percentile 1000
~~END-PERCENT-IO~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_from_workload_marker(self):
        """WORKLOAD 마커가 있는 파일은 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-WORKLOAD~~
SAMPLESTART TOPN MODULE
2024-01-01 1 TestModule
~~END-WORKLOAD~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_awr_from_buffer_cache_marker(self):
        """BUFFER-CACHE 마커가 있는 파일은 AWR로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-BUFFER-CACHE~~
SNAP_ID INSTANCE_NUMBER HIT_RATIO
1 1 95.5
~~END-BUFFER-CACHE~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_statspack_without_awr_markers(self):
        """AWR 마커가 없는 파일은 Statspack으로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
NUM_CPUS 4
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~
SNAP_ID INSTANCE_NUMBER SGA_GB PGA_GB TOTAL_GB
1 1 10.0 2.0 12.0
~~END-MEMORY~~

~~BEGIN-MAIN-METRICS~~
SNAP DUR_M END INST CPU_PER_S
1 60 2024-01-01 1 50.0
~~END-MAIN-METRICS~~
            """)
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "statspack"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_with_latin1_encoding(self):
        """Latin-1 인코딩 파일도 올바르게 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='wb') as f:
            # Latin-1 특수 문자 포함
            content = """
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-IOSTAT-FUNCTION~~
SNAP_ID FUNCTION_NAME MEGABYTES_PER_S
1 LGWR 10.5
~~END-IOSTAT-FUNCTION~~
            """
            f.write(content.encode('latin-1'))
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "awr"
        finally:
            import os
            os.unlink(filepath)
    
    def test_detect_file_type_handles_read_error(self):
        """파일 읽기 오류 시 기본값(statspack) 반환"""
        # 존재하지 않는 파일
        file_type = detect_file_type("/nonexistent/file.out")
        assert file_type == "statspack"
    
    def test_detect_file_type_empty_file(self):
        """빈 파일은 Statspack으로 감지"""
        with tempfile.NamedTemporaryFile(suffix=".out", delete=False, mode='w') as f:
            f.write("")
            filepath = f.name
        
        try:
            file_type = detect_file_type(filepath)
            assert file_type == "statspack"
        finally:
            import os
            os.unlink(filepath)


class TestGenerateOutputPath:
    """출력 경로 생성 테스트"""
    
    def test_generate_output_path_basic(self, tmp_path):
        """기본 출력 경로 생성"""
        source_path = Path("sample.out")
        output_dir = tmp_path / "reports"
        
        result = generate_output_path(source_path, output_dir)
        
        assert result == output_dir / "sample.md"
        assert output_dir.exists()
    
    def test_generate_output_path_with_target_db(self, tmp_path):
        """타겟 DB가 지정된 경우 파일명에 추가"""
        source_path = Path("sample.out")
        output_dir = tmp_path / "reports"
        target_db = "aurora-mysql"
        
        result = generate_output_path(source_path, output_dir, target_db)
        
        assert result == output_dir / "sample_aurora-mysql.md"
        assert output_dir.exists()
    
    def test_generate_output_path_creates_directory(self, tmp_path):
        """출력 디렉토리가 없으면 생성"""
        source_path = Path("sample.out")
        output_dir = tmp_path / "reports" / "nested" / "path"
        
        assert not output_dir.exists()
        
        result = generate_output_path(source_path, output_dir)
        
        assert output_dir.exists()
        assert result == output_dir / "sample.md"
    
    def test_generate_output_path_with_complex_filename(self, tmp_path):
        """복잡한 파일명 처리"""
        source_path = Path("dbcsi_statspack_sample01.out")
        output_dir = tmp_path / "reports"
        
        result = generate_output_path(source_path, output_dir)
        
        assert result == output_dir / "dbcsi_statspack_sample01.md"
    
    def test_generate_output_path_with_path_object(self, tmp_path):
        """Path 객체로 입력"""
        source_path = Path("/some/path/sample.out")
        output_dir = tmp_path / "reports"
        
        result = generate_output_path(source_path, output_dir)
        
        assert result == output_dir / "sample.md"
    
    def test_generate_output_path_preserves_existing_directory(self, tmp_path):
        """기존 디렉토리가 있어도 정상 동작"""
        source_path = Path("sample.out")
        output_dir = tmp_path / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 기존 파일 생성
        existing_file = output_dir / "existing.txt"
        existing_file.write_text("existing content")
        
        result = generate_output_path(source_path, output_dir)
        
        assert result == output_dir / "sample.md"
        assert existing_file.exists()  # 기존 파일은 유지
    
    def test_generate_output_path_with_multiple_targets(self, tmp_path):
        """여러 타겟 DB에 대한 출력 경로 생성"""
        source_path = Path("sample.out")
        output_dir = tmp_path / "reports"
        
        targets = ["rds-oracle", "aurora-mysql", "aurora-postgresql"]
        results = []
        
        for target in targets:
            result = generate_output_path(source_path, output_dir, target)
            results.append(result)
        
        assert results[0] == output_dir / "sample_rds-oracle.md"
        assert results[1] == output_dir / "sample_aurora-mysql.md"
        assert results[2] == output_dir / "sample_aurora-postgresql.md"
    
    def test_generate_output_path_without_extension(self, tmp_path):
        """확장자가 없는 파일명 처리"""
        source_path = Path("sample")
        output_dir = tmp_path / "reports"
        
        result = generate_output_path(source_path, output_dir)
        
        assert result == output_dir / "sample.md"


class TestPrintProgress:
    """진행 상황 출력 테스트"""
    
    def test_print_progress_basic(self):
        """기본 진행 상황 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(1, 4, "파일 파싱 중")
            output = fake_out.getvalue()
        
        assert "[1/4] 파일 파싱 중" in output
    
    def test_print_progress_first_step(self):
        """첫 번째 단계 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(1, 10, "시작")
            output = fake_out.getvalue()
        
        assert "[1/10] 시작" in output
    
    def test_print_progress_last_step(self):
        """마지막 단계 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(10, 10, "완료")
            output = fake_out.getvalue()
        
        assert "[10/10] 완료" in output
    
    def test_print_progress_middle_step(self):
        """중간 단계 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(5, 10, "처리 중")
            output = fake_out.getvalue()
        
        assert "[5/10] 처리 중" in output
    
    def test_print_progress_with_korean_message(self):
        """한글 메시지 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(2, 5, "데이터베이스 연결 중")
            output = fake_out.getvalue()
        
        assert "[2/5] 데이터베이스 연결 중" in output
    
    def test_print_progress_with_english_message(self):
        """영어 메시지 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(3, 7, "Processing files")
            output = fake_out.getvalue()
        
        assert "[3/7] Processing files" in output
    
    def test_print_progress_with_special_characters(self):
        """특수 문자가 포함된 메시지 출력"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(1, 3, "파일 분석 중... (50%)")
            output = fake_out.getvalue()
        
        assert "[1/3] 파일 분석 중... (50%)" in output
    
    def test_print_progress_multiple_calls(self):
        """여러 번 호출"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(1, 3, "단계 1")
            print_progress(2, 3, "단계 2")
            print_progress(3, 3, "단계 3")
            output = fake_out.getvalue()
        
        assert "[1/3] 단계 1" in output
        assert "[2/3] 단계 2" in output
        assert "[3/3] 단계 3" in output
    
    def test_print_progress_with_long_message(self):
        """긴 메시지 출력"""
        long_message = "매우 긴 메시지입니다. " * 10
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_progress(1, 2, long_message)
            output = fake_out.getvalue()
        
        assert "[1/2]" in output
        assert long_message in output


class TestCLIHelpersIntegration:
    """CLI 헬퍼 함수 통합 테스트"""
    
    def test_workflow_detect_and_generate_path(self, tmp_path):
        """파일 타입 감지 후 출력 경로 생성 워크플로우"""
        # 1. AWR 파일 생성
        awr_file = tmp_path / "sample_awr.out"
        awr_file.write_text("""
~~BEGIN-IOSTAT-FUNCTION~~
SNAP_ID FUNCTION_NAME MEGABYTES_PER_S
1 LGWR 10.5
~~END-IOSTAT-FUNCTION~~
        """)
        
        # 2. 파일 타입 감지
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
        
        # 3. 출력 경로 생성
        output_dir = tmp_path / "reports"
        output_path = generate_output_path(awr_file, output_dir, file_type)
        
        assert output_path == output_dir / "sample_awr_awr.md"
        assert output_dir.exists()
    
    def test_workflow_with_progress_reporting(self, tmp_path):
        """진행 상황 보고를 포함한 워크플로우"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            # 1. 파일 생성
            print_progress(1, 3, "파일 생성 중")
            test_file = tmp_path / "test.out"
            test_file.write_text("test content")
            
            # 2. 파일 타입 감지
            print_progress(2, 3, "파일 타입 감지 중")
            file_type = detect_file_type(str(test_file))
            
            # 3. 출력 경로 생성
            print_progress(3, 3, "출력 경로 생성 중")
            output_path = generate_output_path(test_file, tmp_path / "output")
            
            output = fake_out.getvalue()
        
        assert "[1/3] 파일 생성 중" in output
        assert "[2/3] 파일 타입 감지 중" in output
        assert "[3/3] 출력 경로 생성 중" in output
        assert file_type == "statspack"
        assert output_path.exists() or output_path.parent.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
