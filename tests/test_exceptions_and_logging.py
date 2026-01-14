"""
예외 처리 및 로깅 테스트

Requirements: 16.1~16.5
"""

import pytest
import logging
import tempfile
from pathlib import Path

from src.dbcsi.exceptions import (
    StatspackError,
    StatspackParseError,
    StatspackFileError,
    MigrationAnalysisError,
)
from src.dbcsi.logging_config import setup_logging, get_logger
from src.dbcsi.parser import StatspackParser


class TestExceptions:
    """예외 클래스 테스트"""
    
    def test_statspack_error_is_base_exception(self):
        """StatspackError가 기본 예외 클래스인지 확인"""
        error = StatspackError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_statspack_parse_error_inherits_from_base(self):
        """StatspackParseError가 StatspackError를 상속하는지 확인"""
        error = StatspackParseError("Parse error")
        assert isinstance(error, StatspackError)
        assert isinstance(error, Exception)
        assert str(error) == "Parse error"
    
    def test_statspack_file_error_inherits_from_base(self):
        """StatspackFileError가 StatspackError를 상속하는지 확인"""
        error = StatspackFileError("File error")
        assert isinstance(error, StatspackError)
        assert isinstance(error, Exception)
        assert str(error) == "File error"
    
    def test_migration_analysis_error_inherits_from_base(self):
        """MigrationAnalysisError가 StatspackError를 상속하는지 확인"""
        error = MigrationAnalysisError("Analysis error")
        assert isinstance(error, StatspackError)
        assert isinstance(error, Exception)
        assert str(error) == "Analysis error"
    
    def test_exception_hierarchy(self):
        """예외 계층 구조 확인"""
        # 모든 Statspack 예외는 StatspackError로 캐치 가능
        exceptions = [
            StatspackParseError("test"),
            StatspackFileError("test"),
            MigrationAnalysisError("test"),
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except StatspackError:
                pass  # 정상적으로 캐치됨
            except Exception:
                pytest.fail("Should be caught as StatspackError")


class TestErrorMessages:
    """에러 메시지 테스트"""
    
    def test_file_not_found_error_message(self):
        """파일 없음 에러 메시지 확인 (Requirements 16.1)"""
        nonexistent_file = "/path/to/nonexistent/file.out"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            StatspackParser(nonexistent_file)
        
        assert "File not found" in str(exc_info.value)
        assert nonexistent_file in str(exc_info.value)
    
    def test_directory_instead_of_file_error_message(self):
        """디렉토리 경로 에러 메시지 확인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(StatspackFileError) as exc_info:
                StatspackParser(tmpdir)
            
            assert "directory" in str(exc_info.value).lower()
            assert tmpdir in str(exc_info.value)
    
    def test_invalid_format_error_message(self):
        """잘못된 형식 에러 메시지 확인 (Requirements 16.2)"""
        # 빈 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            temp_file = f.name
            f.write("")  # 빈 파일
        
        try:
            parser = StatspackParser(temp_file)
            
            # 빈 파일은 파싱 시 예외 발생
            with pytest.raises(StatspackParseError) as exc_info:
                result = parser.parse()
            
            # 에러 메시지가 명확해야 함
            assert "section" in str(exc_info.value).lower()
        finally:
            Path(temp_file).unlink()


class TestLoggingConfiguration:
    """로깅 설정 테스트"""
    
    def test_setup_logging_default_level(self):
        """기본 로그 레벨 설정 확인 (Requirements 16.3)"""
        logger = setup_logging(level="INFO")
        assert logger.level == logging.INFO
        assert logger.name == "statspack"
    
    def test_setup_logging_debug_level(self):
        """DEBUG 로그 레벨 설정 확인"""
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_warning_level(self):
        """WARNING 로그 레벨 설정 확인"""
        logger = setup_logging(level="WARNING")
        assert logger.level == logging.WARNING
    
    def test_setup_logging_error_level(self):
        """ERROR 로그 레벨 설정 확인"""
        logger = setup_logging(level="ERROR")
        assert logger.level == logging.ERROR
    
    def test_setup_logging_with_console_handler(self):
        """콘솔 핸들러 설정 확인 (Requirements 16.4)"""
        logger = setup_logging(level="INFO", console=True)
        
        # 최소 하나의 핸들러가 있어야 함
        assert len(logger.handlers) > 0
        
        # StreamHandler가 있는지 확인
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) for h in logger.handlers
        )
        assert has_stream_handler
    
    def test_setup_logging_with_file_handler(self):
        """파일 핸들러 설정 확인 (Requirements 16.4)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(level="INFO", log_file=str(log_file), console=False)
            
            # FileHandler가 있는지 확인
            has_file_handler = any(
                isinstance(h, logging.FileHandler) for h in logger.handlers
            )
            assert has_file_handler
            
            # 로그 파일이 생성되었는지 확인
            assert log_file.exists()
    
    def test_setup_logging_format(self):
        """로그 포맷 설정 확인 (Requirements 16.5)"""
        logger = setup_logging(level="INFO", console=True)
        
        # 핸들러의 포맷터 확인
        for handler in logger.handlers:
            formatter = handler.formatter
            assert formatter is not None
            
            # 포맷 문자열에 필수 요소가 포함되어 있는지 확인
            format_str = formatter._fmt
            assert "%(asctime)s" in format_str
            assert "%(name)s" in format_str
            assert "%(levelname)s" in format_str
            assert "%(message)s" in format_str
    
    def test_get_logger(self):
        """로거 인스턴스 가져오기 테스트"""
        logger = get_logger()
        assert logger.name == "statspack"
        
        logger_with_name = get_logger("test_module")
        assert logger_with_name.name == "statspack.test_module"
    
    def test_logging_hierarchy(self):
        """로거 계층 구조 테스트"""
        # 부모 로거 설정
        parent_logger = setup_logging(level="INFO")
        
        # 자식 로거 가져오기
        child_logger = get_logger("parser")
        
        # 자식 로거는 부모 로거의 설정을 상속
        assert child_logger.name == "statspack.parser"


class TestErrorHandlingInParser:
    """파서의 에러 처리 테스트"""
    
    def test_parser_logs_file_not_found(self, caplog):
        """파일 없음 에러 로깅 확인 (Requirements 16.4)"""
        setup_logging(level="ERROR", console=True)
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError):
                StatspackParser("/nonexistent/file.out")
        
        # 에러 로그가 기록되었는지 확인
        assert any("File not found" in record.message for record in caplog.records)
    
    def test_parser_logs_directory_error(self, caplog):
        """디렉토리 에러 로깅 확인"""
        setup_logging(level="ERROR", console=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with caplog.at_level(logging.ERROR):
                with pytest.raises(StatspackFileError):
                    StatspackParser(tmpdir)
            
            # 에러 로그가 기록되었는지 확인
            assert any("directory" in record.message.lower() for record in caplog.records)
    
    def test_parser_logs_encoding_fallback(self, caplog):
        """인코딩 폴백 경고 로깅 확인 (Requirements 16.3)"""
        setup_logging(level="WARNING", console=True)
        
        # Latin-1 인코딩이 필요한 파일 생성
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.out', delete=False) as f:
            temp_file = f.name
            # UTF-8로 디코딩할 수 없는 바이트 작성
            f.write(b'\xff\xfe' + "Test content".encode('utf-16-le'))
        
        try:
            with caplog.at_level(logging.WARNING):
                parser = StatspackParser(temp_file)
                parser._read_file()
            
            # 경고 로그가 기록되었는지 확인
            assert any(
                "falling back" in record.message.lower() or "latin-1" in record.message.lower()
                for record in caplog.records
            )
        finally:
            Path(temp_file).unlink()


class TestErrorMessageClarity:
    """에러 메시지 명확성 테스트 (Requirements 16.5)"""
    
    def test_error_messages_are_actionable(self):
        """에러 메시지가 실행 가능한 정보를 제공하는지 확인"""
        # 파일 없음 에러
        with pytest.raises(FileNotFoundError) as exc_info:
            StatspackParser("/nonexistent/file.out")
        
        error_msg = str(exc_info.value)
        # 에러 메시지에 파일 경로가 포함되어야 함
        assert "/nonexistent/file.out" in error_msg
        # 에러 메시지가 명확해야 함
        assert "not found" in error_msg.lower()
    
    def test_exception_chaining(self):
        """예외 체이닝이 올바르게 작동하는지 확인"""
        # 권한 오류 시뮬레이션을 위한 읽기 전용 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            temp_file = f.name
            f.write("test content")
        
        try:
            # 파일을 읽기 전용으로 변경 (Unix 시스템에서만 작동)
            import os
            import stat
            
            # 파일 권한 제거 (읽기 권한도 제거)
            os.chmod(temp_file, 0o000)
            
            try:
                parser = StatspackParser(temp_file)
                parser._read_file()
            except StatspackFileError as e:
                # 원본 예외가 체이닝되어 있는지 확인
                assert e.__cause__ is not None or e.__context__ is not None
            finally:
                # 권한 복구 후 삭제
                os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)
        finally:
            Path(temp_file).unlink()
