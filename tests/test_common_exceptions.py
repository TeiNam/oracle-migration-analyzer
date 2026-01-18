"""
공통 예외 클래스 테스트

이 모듈은 src/exceptions.py에 정의된 공통 예외 클래스들을 테스트합니다.
"""

import pytest

from src.exceptions import (
    OracleAnalyzerError,
    FileProcessingError,
    ParsingError,
    AnalysisError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """예외 계층 구조 테스트"""
    
    def test_oracle_analyzer_error_is_base_exception(self):
        """OracleAnalyzerError가 기본 예외 클래스인지 확인"""
        error = OracleAnalyzerError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_file_processing_error_inherits_from_base(self):
        """FileProcessingError가 OracleAnalyzerError를 상속하는지 확인"""
        error = FileProcessingError("File error")
        assert isinstance(error, OracleAnalyzerError)
        assert isinstance(error, Exception)
        assert str(error) == "File error"
    
    def test_parsing_error_inherits_from_base(self):
        """ParsingError가 OracleAnalyzerError를 상속하는지 확인"""
        error = ParsingError("Parse error")
        assert isinstance(error, OracleAnalyzerError)
        assert isinstance(error, Exception)
        assert str(error) == "Parse error"
    
    def test_analysis_error_inherits_from_base(self):
        """AnalysisError가 OracleAnalyzerError를 상속하는지 확인"""
        error = AnalysisError("Analysis error")
        assert isinstance(error, OracleAnalyzerError)
        assert isinstance(error, Exception)
        assert str(error) == "Analysis error"
    
    def test_configuration_error_inherits_from_base(self):
        """ConfigurationError가 OracleAnalyzerError를 상속하는지 확인"""
        error = ConfigurationError("Config error")
        assert isinstance(error, OracleAnalyzerError)
        assert isinstance(error, Exception)
        assert str(error) == "Config error"
    
    def test_all_exceptions_catchable_as_base(self):
        """모든 예외가 OracleAnalyzerError로 캐치 가능한지 확인"""
        exceptions = [
            FileProcessingError("test"),
            ParsingError("test"),
            AnalysisError("test"),
            ConfigurationError("test"),
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except OracleAnalyzerError:
                pass  # 정상적으로 캐치됨
            except Exception:
                pytest.fail(f"{type(exc).__name__} should be caught as OracleAnalyzerError")


class TestFileProcessingError:
    """FileProcessingError 테스트"""
    
    def test_can_be_raised_and_caught(self):
        """FileProcessingError를 발생시키고 캐치할 수 있는지 확인"""
        with pytest.raises(FileProcessingError) as exc_info:
            raise FileProcessingError("파일을 읽을 수 없습니다")
        
        assert "파일을 읽을 수 없습니다" in str(exc_info.value)
    
    def test_exception_chaining(self):
        """예외 체이닝이 올바르게 작동하는지 확인"""
        original_error = IOError("Permission denied")
        
        with pytest.raises(FileProcessingError) as exc_info:
            try:
                raise original_error
            except IOError as e:
                raise FileProcessingError("파일 처리 실패") from e
        
        assert exc_info.value.__cause__ is original_error
        assert isinstance(exc_info.value.__cause__, IOError)
    
    def test_with_file_path_in_message(self):
        """파일 경로를 포함한 에러 메시지 테스트"""
        filepath = "/path/to/file.sql"
        error = FileProcessingError(f"파일을 읽을 수 없습니다: {filepath}")
        
        assert filepath in str(error)
        assert "파일을 읽을 수 없습니다" in str(error)


class TestParsingError:
    """ParsingError 테스트"""
    
    def test_can_be_raised_and_caught(self):
        """ParsingError를 발생시키고 캐치할 수 있는지 확인"""
        with pytest.raises(ParsingError) as exc_info:
            raise ParsingError("SQL 파싱 실패")
        
        assert "SQL 파싱 실패" in str(exc_info.value)
    
    def test_exception_chaining_from_value_error(self):
        """ValueError로부터 예외 체이닝 테스트"""
        original_error = ValueError("Invalid syntax")
        
        with pytest.raises(ParsingError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise ParsingError("파싱 오류 발생") from e
        
        assert exc_info.value.__cause__ is original_error
    
    def test_with_line_number_in_message(self):
        """라인 번호를 포함한 에러 메시지 테스트"""
        line_no = 42
        error = ParsingError(f"라인 {line_no}에서 파싱 오류")
        
        assert str(line_no) in str(error)
        assert "파싱 오류" in str(error)


class TestAnalysisError:
    """AnalysisError 테스트"""
    
    def test_can_be_raised_and_caught(self):
        """AnalysisError를 발생시키고 캐치할 수 있는지 확인"""
        with pytest.raises(AnalysisError) as exc_info:
            raise AnalysisError("분석 데이터 부족")
        
        assert "분석 데이터 부족" in str(exc_info.value)
    
    def test_with_insufficient_data_message(self):
        """불충분한 데이터 메시지 테스트"""
        error = AnalysisError("분석에 필요한 데이터가 부족합니다")
        assert "데이터가 부족" in str(error)
    
    def test_with_unknown_database_type(self):
        """알 수 없는 데이터베이스 타입 메시지 테스트"""
        db_type = "unknown_db"
        error = AnalysisError(f"지원하지 않는 데이터베이스 타입: {db_type}")
        
        assert db_type in str(error)
        assert "지원하지 않는" in str(error)


class TestConfigurationError:
    """ConfigurationError 테스트"""
    
    def test_can_be_raised_and_caught(self):
        """ConfigurationError를 발생시키고 캐치할 수 있는지 확인"""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("API_KEY가 설정되지 않았습니다")
        
        assert "API_KEY" in str(exc_info.value)
    
    def test_with_missing_env_var(self):
        """누락된 환경 변수 메시지 테스트"""
        env_var = "DATABASE_URL"
        error = ConfigurationError(f"{env_var} 환경 변수가 설정되지 않았습니다")
        
        assert env_var in str(error)
        assert "환경 변수" in str(error)
    
    def test_with_invalid_config_value(self):
        """잘못된 설정 값 메시지 테스트"""
        config_key = "max_connections"
        invalid_value = -1
        error = ConfigurationError(
            f"잘못된 설정 값: {config_key}={invalid_value}"
        )
        
        assert config_key in str(error)
        assert str(invalid_value) in str(error)


class TestExceptionUsagePatterns:
    """예외 사용 패턴 테스트"""
    
    def test_catch_specific_exception(self):
        """특정 예외를 캐치하는 패턴 테스트"""
        caught = False
        
        try:
            raise FileProcessingError("Test error")
        except FileProcessingError:
            caught = True
        except OracleAnalyzerError:
            pytest.fail("Should catch FileProcessingError specifically")
        
        assert caught
    
    def test_catch_base_exception(self):
        """기본 예외로 모든 하위 예외를 캐치하는 패턴 테스트"""
        exceptions_caught = []
        
        test_exceptions = [
            FileProcessingError("file error"),
            ParsingError("parse error"),
            AnalysisError("analysis error"),
            ConfigurationError("config error"),
        ]
        
        for exc in test_exceptions:
            try:
                raise exc
            except OracleAnalyzerError as e:
                exceptions_caught.append(type(e).__name__)
        
        assert len(exceptions_caught) == 4
        assert "FileProcessingError" in exceptions_caught
        assert "ParsingError" in exceptions_caught
        assert "AnalysisError" in exceptions_caught
        assert "ConfigurationError" in exceptions_caught
    
    def test_exception_with_context(self):
        """컨텍스트 정보를 포함한 예외 테스트"""
        context = {
            "file": "test.sql",
            "line": 10,
            "column": 5
        }
        
        error = ParsingError(
            f"파싱 오류: {context['file']} "
            f"(line {context['line']}, column {context['column']})"
        )
        
        error_str = str(error)
        assert context["file"] in error_str
        assert str(context["line"]) in error_str
        assert str(context["column"]) in error_str
    
    def test_multiple_exception_handling(self):
        """여러 예외를 순차적으로 처리하는 패턴 테스트"""
        def risky_operation(operation_type: str):
            if operation_type == "file":
                raise FileProcessingError("파일 오류")
            elif operation_type == "parse":
                raise ParsingError("파싱 오류")
            elif operation_type == "analysis":
                raise AnalysisError("분석 오류")
            elif operation_type == "config":
                raise ConfigurationError("설정 오류")
        
        # 각 예외 타입별로 다르게 처리
        for op_type in ["file", "parse", "analysis", "config"]:
            try:
                risky_operation(op_type)
            except FileProcessingError:
                assert op_type == "file"
            except ParsingError:
                assert op_type == "parse"
            except AnalysisError:
                assert op_type == "analysis"
            except ConfigurationError:
                assert op_type == "config"


class TestExceptionDocstrings:
    """예외 클래스의 docstring 테스트"""
    
    def test_all_exceptions_have_docstrings(self):
        """모든 예외 클래스가 docstring을 가지고 있는지 확인"""
        exceptions = [
            OracleAnalyzerError,
            FileProcessingError,
            ParsingError,
            AnalysisError,
            ConfigurationError,
        ]
        
        for exc_class in exceptions:
            assert exc_class.__doc__ is not None
            assert len(exc_class.__doc__.strip()) > 0
    
    def test_docstrings_are_descriptive(self):
        """docstring이 충분히 설명적인지 확인"""
        # FileProcessingError의 docstring에 "파일"이 포함되어야 함
        assert "파일" in FileProcessingError.__doc__
        
        # ParsingError의 docstring에 "파싱"이 포함되어야 함
        assert "파싱" in ParsingError.__doc__
        
        # AnalysisError의 docstring에 "분석"이 포함되어야 함
        assert "분석" in AnalysisError.__doc__
        
        # ConfigurationError의 docstring에 "설정"이 포함되어야 함
        assert "설정" in ConfigurationError.__doc__
