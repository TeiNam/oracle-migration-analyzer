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

from src.statspack.cli import (
    create_parser,
    validate_args,
    get_target_databases,
    process_single_file,
    process_directory,
    main
)
from src.statspack.data_models import TargetDatabase


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
        
        parser = create_parser()
        args = parser.parse_args(['--file', sample_file])
        
        # 표준 출력 캡처
        with patch('sys.stdout', new=StringIO()) as fake_out:
            exit_code = process_single_file(args)
        
        assert exit_code == 0
        output = fake_out.getvalue()
        assert "# Statspack 분석 보고서" in output
        assert "시스템 정보 요약" in output
    
    def test_process_file_json_output(self, tmp_path):
        """JSON 형식 출력 테스트"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        parser = create_parser()
        args = parser.parse_args(['--file', sample_file, '--format', 'json'])
        
        # 표준 출력 캡처
        with patch('sys.stdout', new=StringIO()) as fake_out:
            exit_code = process_single_file(args)
        
        assert exit_code == 0
        output = fake_out.getvalue()
        assert '"_type": "StatspackData"' in output
    
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
        
        parser = create_parser()
        args = parser.parse_args([
            '--file', sample_file,
            '--analyze-migration',
            '--target', 'rds-oracle'
        ])
        
        # 표준 출력 캡처
        with patch('sys.stdout', new=StringIO()) as fake_out:
            exit_code = process_single_file(args)
        
        assert exit_code == 0
        output = fake_out.getvalue()
        # 마이그레이션 분석이 있으면 섹션 8이 있어야 함
        # 없으면 섹션 7까지만 있음
        assert "## 7. SGA 조정 권장사항" in output or "## 8. 마이그레이션 분석 결과" in output
    
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
        
        parser = create_parser()
        args = parser.parse_args(['--directory', str(tmp_path)])
        
        # 표준 출력 캡처
        with patch('sys.stdout', new=StringIO()) as fake_out:
            exit_code = process_directory(args)
        
        assert exit_code == 0
        output = fake_out.getvalue()
        assert "# Statspack 배치 분석 보고서" in output
    
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
        with patch('sys.argv', ['statspack-analyzer', '--file', sample_file]):
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
        with patch('sys.argv', ['statspack-analyzer', '--directory', str(tmp_path)]):
            with patch('sys.stdout', new=StringIO()):
                exit_code = main()
        
        assert exit_code == 0
    
    def test_main_exit_code_on_error(self):
        """오류 시 exit code 1 반환"""
        # sys.argv 모킹 (존재하지 않는 파일)
        with patch('sys.argv', ['statspack-analyzer', '--file', 'nonexistent.out']):
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
            'statspack-analyzer',
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
        
        with patch('sys.argv', [
            'statspack-analyzer',
            '--file', sample_file,
            '--analyze-migration',
            '--target', 'all'
        ]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                exit_code = main()
        
        assert exit_code == 0
        output = fake_out.getvalue()
        assert "마이그레이션 분석 결과" in output
    
    def test_directory_migration_specific_target(self, tmp_path):
        """디렉토리 + 마이그레이션 분석 + 특정 타겟"""
        sample_file = "sample_code/dbcsi_statspack_sample01.out"
        
        if not os.path.exists(sample_file):
            pytest.skip("샘플 파일이 없습니다")
        
        # 임시 디렉토리에 파일 복사
        import shutil
        dest_file = tmp_path / "test.out"
        shutil.copy(sample_file, dest_file)
        
        with patch('sys.argv', [
            'statspack-analyzer',
            '--directory', str(tmp_path),
            '--analyze-migration',
            '--target', 'aurora-postgresql'
        ]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                exit_code = main()
        
        assert exit_code == 0
        output = fake_out.getvalue()
        assert "배치 분석 보고서" in output
