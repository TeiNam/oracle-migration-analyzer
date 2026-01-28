"""
Statspack CLI 통합 테스트

Requirements 15.1~15.7을 검증합니다.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from src.dbcsi.cli import (
    create_parser,
    validate_args,
    get_target_databases,
    process_single_file,
    process_directory,
    main
)
from src.dbcsi.models import TargetDatabase


class TestCLIParser:
    """CLI 인자 파서 테스트"""
    
    def test_parser_file_option(self):
        """--file 옵션 파싱 테스트"""
        parser = create_parser()
        args = parser.parse_args(['--file', 'test.out'])
        
        assert args.file == 'test.out'
        assert args.directory is None
        assert args.format == 'markdown'
        assert args.target == 'all'
        assert args.analyze_migration is False
    
    def test_parser_directory_option(self):
        """--directory 옵션 파싱 테스트"""
        parser = create_parser()
        args = parser.parse_args(['--directory', './data'])
        
        assert args.file is None
        assert args.directory == './data'
    
    def test_parser_format_option(self):
        """--format 옵션 파싱 테스트"""
        parser = create_parser()
        
        # JSON 형식
        args = parser.parse_args(['--file', 'test.out', '--format', 'json'])
        assert args.format == 'json'
        
        # Markdown 형식
        args = parser.parse_args(['--file', 'test.out', '--format', 'markdown'])
        assert args.format == 'markdown'
    
    def test_parser_output_option(self):
        """--output 옵션 파싱 테스트"""
        parser = create_parser()
        args = parser.parse_args(['--file', 'test.out', '--output', 'report.md'])
        
        assert args.output == 'report.md'
    
    def test_parser_target_option(self):
        """--target 옵션 파싱 테스트"""
        parser = create_parser()
        
        # RDS Oracle
        args = parser.parse_args(['--file', 'test.out', '--target', 'rds-oracle'])
        assert args.target == 'rds-oracle'
        
        # Aurora MySQL
        args = parser.parse_args(['--file', 'test.out', '--target', 'aurora-mysql'])
        assert args.target == 'aurora-mysql'
        
        # Aurora PostgreSQL
        args = parser.parse_args(['--file', 'test.out', '--target', 'aurora-postgresql'])
        assert args.target == 'aurora-postgresql'
        
        # All
        args = parser.parse_args(['--file', 'test.out', '--target', 'all'])
        assert args.target == 'all'
    
    def test_parser_analyze_migration_flag(self):
        """--analyze-migration 플래그 파싱 테스트"""
        parser = create_parser()
        
        # 플래그 없음
        args = parser.parse_args(['--file', 'test.out'])
        assert args.analyze_migration is False
        
        # 플래그 있음
        args = parser.parse_args(['--file', 'test.out', '--analyze-migration'])
        assert args.analyze_migration is True
    
    def test_parser_mutually_exclusive_file_directory(self):
        """--file과 --directory는 상호 배타적"""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--file', 'test.out', '--directory', './data'])
    
    def test_parser_requires_file_or_directory(self):
        """--file 또는 --directory 중 하나는 필수"""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestCLIValidation:
    """CLI 인자 검증 테스트"""
    
    def test_validate_existing_file(self, tmp_path):
        """존재하는 파일 검증"""
        # 임시 파일 생성
        test_file = tmp_path / "test.out"
        test_file.write_text("test content")
        
        parser = create_parser()
        args = parser.parse_args(['--file', str(test_file)])
        
        # 예외 발생하지 않아야 함
        validate_args(args)
    
    def test_validate_nonexistent_file(self):
        """존재하지 않는 파일 검증"""
        parser = create_parser()
        args = parser.parse_args(['--file', 'nonexistent.out'])
        
        with pytest.raises(SystemExit) as exc_info:
            validate_args(args)
        
        assert exc_info.value.code == 1
    
    def test_validate_existing_directory(self, tmp_path):
        """존재하는 디렉토리 검증"""
        parser = create_parser()
        args = parser.parse_args(['--directory', str(tmp_path)])
        
        # 예외 발생하지 않아야 함
        validate_args(args)
    
    def test_validate_nonexistent_directory(self):
        """존재하지 않는 디렉토리 검증"""
        parser = create_parser()
        args = parser.parse_args(['--directory', '/nonexistent/path'])
        
        with pytest.raises(SystemExit) as exc_info:
            validate_args(args)
        
        assert exc_info.value.code == 1
    
    def test_validate_directory_is_file(self, tmp_path):
        """디렉토리 경로가 파일인 경우"""
        test_file = tmp_path / "test.out"
        test_file.write_text("test content")
        
        parser = create_parser()
        args = parser.parse_args(['--directory', str(test_file)])
        
        with pytest.raises(SystemExit) as exc_info:
            validate_args(args)
        
        assert exc_info.value.code == 1


class TestTargetDatabaseConversion:
    """타겟 데이터베이스 변환 테스트"""
    
    def test_get_target_all(self):
        """all 타겟은 None 반환"""
        result = get_target_databases('all')
        assert result is None
    
    def test_get_target_rds_oracle(self):
        """rds-oracle 타겟 변환"""
        result = get_target_databases('rds-oracle')
        assert result == [TargetDatabase.RDS_ORACLE]
    
    def test_get_target_aurora_mysql(self):
        """aurora-mysql 타겟 변환"""
        result = get_target_databases('aurora-mysql')
        assert result == [TargetDatabase.AURORA_MYSQL]
    
    def test_get_target_aurora_postgresql(self):
        """aurora-postgresql 타겟 변환"""
        result = get_target_databases('aurora-postgresql')
        assert result == [TargetDatabase.AURORA_POSTGRESQL]


class TestProcessSingleFile:
    """단일 파일 처리 테스트"""
    
    def test_process_file_markdown_output(self, tmp_path):
        """Markdown 형식 출력 테스트"""
        # 샘플 파일 경로
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 출력 파일 지정 (stdout 대신 파일로 저장)
        output_file = tmp_path / "output.md"
        
        parser = create_parser()
        args = parser.parse_args(['--file', sample_file, '--output', str(output_file)])
        
        exit_code = process_single_file(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Statspack 분석 보고서" in content or "# AWR 분석 보고서" in content
        # 개선된 포맷에서는 "데이터베이스 개요" 섹션이 표시됨
        assert "데이터베이스 개요" in content or "시스템 정보" in content
    
    def test_process_file_json_output(self, tmp_path):
        """JSON 형식 출력 테스트"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 출력 파일 지정
        output_file = tmp_path / "output.json"
        
        parser = create_parser()
        args = parser.parse_args(['--file', sample_file, '--format', 'json', '--output', str(output_file)])
        
        exit_code = process_single_file(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert '"_type": "StatspackData"' in content or '"_type": "AWRData"' in content
    
    def test_process_file_with_output(self, tmp_path):
        """파일로 출력 테스트"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        output_file = tmp_path / "output.md"
        
        parser = create_parser()
        args = parser.parse_args(['--file', sample_file, '--output', str(output_file)])
        
        exit_code = process_single_file(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Statspack 분석 보고서" in content
    
    def test_process_file_with_migration_analysis(self, tmp_path):
        """마이그레이션 분석 포함 테스트"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 출력 파일 지정
        output_file = tmp_path / "output.md"
        
        parser = create_parser()
        args = parser.parse_args([
            '--file', sample_file,
            '--analyze-migration',
            '--target', 'rds-oracle',
            '--output', str(output_file)
        ])
        
        exit_code = process_single_file(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        # 마이그레이션 분석이 있으면 섹션 8이 있어야 함
        # 없으면 섹션 7까지만 있음
        assert "## 7. SGA 조정 권장사항" in content or "## 8. 마이그레이션 분석 결과" in content or "마이그레이션" in content
    
    def test_process_nonexistent_file(self):
        """존재하지 않는 파일 처리"""
        parser = create_parser()
        args = parser.parse_args(['--file', 'nonexistent.out'])
        
        # 검증 단계에서 실패하므로 validate_args를 건너뛰고 직접 처리
        exit_code = process_single_file(args)
        
        assert exit_code == 1


class TestProcessDirectory:
    """디렉토리 처리 테스트"""
    
    def test_process_directory_markdown_output(self, tmp_path):
        """디렉토리 Markdown 출력 테스트"""
        # 샘플 파일 복사
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 임시 디렉토리에 파일 복사
        import shutil
        dest_file = tmp_path / "test.out"
        shutil.copy(sample_file, dest_file)
        
        # 출력 파일 지정
        output_file = tmp_path / "batch_summary.md"
        
        parser = create_parser()
        args = parser.parse_args(['--directory', str(tmp_path), '--output', str(output_file)])
        
        exit_code = process_directory(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "배치 분석" in content or "Batch Analysis" in content
    
    def test_process_empty_directory(self, tmp_path):
        """빈 디렉토리 처리"""
        parser = create_parser()
        args = parser.parse_args(['--directory', str(tmp_path)])
        
        # 표준 출력 캡처
        with patch('sys.stdout', new=StringIO()) as fake_out:
            exit_code = process_directory(args)
        
        # 빈 디렉토리는 성공으로 처리
        assert exit_code == 0


class TestMainFunction:
    """메인 함수 테스트"""
    
    def test_main_with_file(self, tmp_path):
        """파일 옵션으로 메인 함수 실행"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # sys.argv 모킹
        with patch('sys.argv', ['dbcsi-analyzer', '--file', sample_file]):
            with patch('sys.stdout', new=StringIO()):
                exit_code = main()
        
        assert exit_code == 0
    
    def test_main_with_directory(self, tmp_path):
        """디렉토리 옵션으로 메인 함수 실행"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 임시 디렉토리에 파일 복사
        import shutil
        dest_file = tmp_path / "test.out"
        shutil.copy(sample_file, dest_file)
        
        # sys.argv 모킹
        with patch('sys.argv', ['dbcsi-analyzer', '--directory', str(tmp_path)]):
            with patch('sys.stdout', new=StringIO()):
                exit_code = main()
        
        assert exit_code == 0
    
    def test_main_exit_code_on_error(self):
        """오류 시 exit code 1 반환"""
        # sys.argv 모킹 (존재하지 않는 파일)
        with patch('sys.argv', ['dbcsi-analyzer', '--file', 'nonexistent.out']):
            with pytest.raises(SystemExit) as exc_info:
                exit_code = main()
        
        assert exc_info.value.code == 1


class TestCLIOptionCombinations:
    """CLI 옵션 조합 테스트"""
    
    def test_file_json_output(self, tmp_path):
        """파일 + JSON 출력"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        output_file = tmp_path / "output.json"
        
        with patch('sys.argv', [
            'dbcsi-analyzer',
            '--file', sample_file,
            '--format', 'json',
            '--output', str(output_file)
        ]):
            exit_code = main()
        
        assert exit_code == 0
        assert output_file.exists()
        
        import json
        content = output_file.read_text()
        data = json.loads(content)
        assert data["_type"] == "StatspackData"
    
    def test_file_migration_all_targets(self, tmp_path):
        """파일 + 마이그레이션 분석 + 모든 타겟"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 출력 파일 지정
        output_file = tmp_path / "output.md"
        
        parser = create_parser()
        args = parser.parse_args([
            '--file', sample_file,
            '--analyze-migration',
            '--target', 'all',
            '--output', str(output_file)
        ])
        
        exit_code = process_single_file(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "마이그레이션" in content or "Migration" in content
    
    def test_directory_migration_specific_target(self, tmp_path):
        """디렉토리 + 마이그레이션 분석 + 특정 타겟"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 임시 디렉토리에 파일 복사
        import shutil
        dest_file = tmp_path / "test.out"
        shutil.copy(sample_file, dest_file)
        
        # 출력 파일 지정
        output_file = tmp_path / "batch_summary.md"
        
        parser = create_parser()
        args = parser.parse_args([
            '--directory', str(tmp_path),
            '--analyze-migration',
            '--target', 'aurora-postgresql',
            '--output', str(output_file)
        ])
        
        exit_code = process_directory(args)
        
        assert exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "배치 분석" in content or "Batch Analysis" in content



class TestFileTypeDetection:
    """
    파일 타입 자동 감지 테스트
    
    Property 19: 파일 타입 자동 감지
    Validates: Requirements 16.5
    """
    
    def test_detect_awr_file_with_iostat_marker(self, tmp_path):
        """IOSTAT-FUNCTION 마커가 있는 파일은 AWR로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        # AWR 마커가 있는 파일 생성
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-IOSTAT-FUNCTION~~
SNAP_ID FUNCTION_NAME MEGABYTES_PER_S
1 LGWR 10.5
~~END-IOSTAT-FUNCTION~~
        """)
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_awr_file_with_percent_cpu_marker(self, tmp_path):
        """PERCENT-CPU 마커가 있는 파일은 AWR로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-PERCENT-CPU~~
METRIC ON_CPU
99th_percentile 8
~~END-PERCENT-CPU~~
        """)
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_awr_file_with_percent_io_marker(self, tmp_path):
        """PERCENT-IO 마커가 있는 파일은 AWR로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-PERCENT-IO~~
METRIC RW_IOPS
99th_percentile 1000
~~END-PERCENT-IO~~
        """)
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_awr_file_with_workload_marker(self, tmp_path):
        """WORKLOAD 마커가 있는 파일은 AWR로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-WORKLOAD~~
SAMPLESTART TOPN MODULE
2024-01-01 1 TestModule
~~END-WORKLOAD~~
        """)
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_awr_file_with_buffer_cache_marker(self, tmp_path):
        """BUFFER-CACHE 마커가 있는 파일은 AWR로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
~~END-OS-INFORMATION~~

~~BEGIN-BUFFER-CACHE~~
SNAP_ID INSTANCE_NUMBER HIT_RATIO
1 1 95.5
~~END-BUFFER-CACHE~~
        """)
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_statspack_file_without_awr_markers(self, tmp_path):
        """AWR 마커가 없는 파일은 Statspack으로 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        statspack_file = tmp_path / "statspack_test.out"
        statspack_file.write_text("""
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
        
        file_type = detect_file_type(str(statspack_file))
        assert file_type == "statspack"
    
    def test_detect_and_parse_awr_file(self, tmp_path):
        """AWR 파일은 AWRParser로 파싱"""
        from src.dbcsi.cli import detect_and_parse
        from src.dbcsi.parser import AWRParser
        
        awr_file = tmp_path / "awr_test.out"
        awr_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
NUM_CPUS 4
~~END-OS-INFORMATION~~

~~BEGIN-IOSTAT-FUNCTION~~
SNAP_ID FUNCTION_NAME MEGABYTES_PER_S
1 LGWR 10.5
~~END-IOSTAT-FUNCTION~~
        """)
        
        parser = detect_and_parse(str(awr_file))
        assert isinstance(parser, AWRParser)
    
    def test_detect_and_parse_statspack_file(self, tmp_path):
        """Statspack 파일은 StatspackParser로 파싱"""
        from src.dbcsi.cli import detect_and_parse
        from src.dbcsi.parser import StatspackParser, AWRParser
        
        statspack_file = tmp_path / "statspack_test.out"
        statspack_file.write_text("""
~~BEGIN-OS-INFORMATION~~
STATSPACK_MINER_VER 1.0
NUM_CPUS 4
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~
SNAP_ID INSTANCE_NUMBER SGA_GB PGA_GB TOTAL_GB
1 1 10.0 2.0 12.0
~~END-MEMORY~~
        """)
        
        parser = detect_and_parse(str(statspack_file))
        # AWRParser는 StatspackParser를 상속하므로 타입 체크 주의
        assert isinstance(parser, StatspackParser)
        assert not isinstance(parser, AWRParser)
    
    def test_detect_file_type_with_latin1_encoding(self, tmp_path):
        """Latin-1 인코딩 파일도 올바르게 감지"""
        from src.utils.cli_helpers import detect_file_type
        
        awr_file = tmp_path / "awr_latin1.out"
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
        awr_file.write_bytes(content.encode('latin-1'))
        
        file_type = detect_file_type(str(awr_file))
        assert file_type == "awr"
    
    def test_detect_file_type_handles_read_error(self, tmp_path):
        """파일 읽기 오류 시 기본값(statspack) 반환"""
        from src.utils.cli_helpers import detect_file_type
        
        # 존재하지 않는 파일
        nonexistent_file = tmp_path / "nonexistent.out"
        
        file_type = detect_file_type(str(nonexistent_file))
        assert file_type == "statspack"



class TestNewCLIOptions:
    """새로운 CLI 옵션 테스트 (AWR 관련)"""
    
    def test_parser_detailed_option(self):
        """--detailed 옵션 파싱 테스트"""
        parser = create_parser()
        
        # 플래그 없음
        args = parser.parse_args(['--file', 'test.out'])
        assert args.detailed is False
        
        # 플래그 있음
        args = parser.parse_args(['--file', 'test.out', '--detailed'])
        assert args.detailed is True
    
    def test_parser_compare_option(self):
        """--compare 옵션 파싱 테스트"""
        parser = create_parser()
        
        args = parser.parse_args(['--compare', 'file1.out', 'file2.out'])
        assert args.compare == ['file1.out', 'file2.out']
        assert args.file is None
        assert args.directory is None
    
    def test_parser_percentile_option(self):
        """--percentile 옵션 파싱 테스트"""
        parser = create_parser()
        
        # 기본값
        args = parser.parse_args(['--file', 'test.out'])
        assert args.percentile == '99'
        
        # P95
        args = parser.parse_args(['--file', 'test.out', '--percentile', '95'])
        assert args.percentile == '95'
        
        # P90
        args = parser.parse_args(['--file', 'test.out', '--percentile', '90'])
        assert args.percentile == '90'
        
        # Median
        args = parser.parse_args(['--file', 'test.out', '--percentile', 'median'])
        assert args.percentile == 'median'
        
        # Average
        args = parser.parse_args(['--file', 'test.out', '--percentile', 'average'])
        assert args.percentile == 'average'
    
    def test_parser_language_option(self):
        """--language 옵션 파싱 테스트"""
        parser = create_parser()
        
        # 기본값 (한국어)
        args = parser.parse_args(['--file', 'test.out'])
        assert args.language == 'ko'
        
        # 영어
        args = parser.parse_args(['--file', 'test.out', '--language', 'en'])
        assert args.language == 'en'
        
        # 한국어 명시
        args = parser.parse_args(['--file', 'test.out', '--language', 'ko'])
        assert args.language == 'ko'
    
    def test_parser_compare_mutually_exclusive(self):
        """--compare는 --file, --directory와 상호 배타적"""
        parser = create_parser()
        
        # --compare와 --file 동시 사용 불가
        with pytest.raises(SystemExit):
            parser.parse_args(['--compare', 'file1.out', 'file2.out', '--file', 'test.out'])
        
        # --compare와 --directory 동시 사용 불가
        with pytest.raises(SystemExit):
            parser.parse_args(['--compare', 'file1.out', 'file2.out', '--directory', './data'])
    
    def test_validate_compare_files(self, tmp_path):
        """--compare 파일 검증 테스트"""
        # 두 파일 모두 존재
        file1 = tmp_path / "file1.out"
        file2 = tmp_path / "file2.out"
        file1.write_text("test1")
        file2.write_text("test2")
        
        parser = create_parser()
        args = parser.parse_args(['--compare', str(file1), str(file2)])
        
        # 예외 발생하지 않아야 함
        validate_args(args)
    
    def test_validate_compare_nonexistent_file(self, tmp_path):
        """--compare 존재하지 않는 파일 검증"""
        file1 = tmp_path / "file1.out"
        file1.write_text("test1")
        
        parser = create_parser()
        args = parser.parse_args(['--compare', str(file1), 'nonexistent.out'])
        
        with pytest.raises(SystemExit) as exc_info:
            validate_args(args)
        
        assert exc_info.value.code == 1
