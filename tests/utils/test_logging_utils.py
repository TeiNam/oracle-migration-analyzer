"""
로깅 유틸리티 테스트
"""

import logging
import tempfile
from pathlib import Path

import pytest

from src.utils.logging_utils import setup_cli_logging, log_progress, get_logger


def test_setup_cli_logging_default():
    """기본 설정으로 로거 생성 테스트"""
    logger = setup_cli_logging()
    
    assert logger is not None
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_setup_cli_logging_with_level():
    """로그 레벨 지정 테스트"""
    logger = setup_cli_logging(level="DEBUG")
    
    assert logger.level == logging.DEBUG


def test_setup_cli_logging_with_file():
    """파일 로깅 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_cli_logging(level="INFO", log_file=str(log_file))
        
        # 로그 메시지 작성
        logger.info("테스트 메시지")
        
        # 파일이 생성되었는지 확인
        assert log_file.exists()
        
        # 파일 내용 확인
        content = log_file.read_text(encoding="utf-8")
        assert "테스트 메시지" in content


def test_setup_cli_logging_creates_directory():
    """로그 파일 디렉토리 자동 생성 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "logs" / "subdir" / "test.log"
        logger = setup_cli_logging(level="INFO", log_file=str(log_file))
        
        # 로그 메시지 작성
        logger.info("테스트 메시지")
        
        # 디렉토리와 파일이 생성되었는지 확인
        assert log_file.parent.exists()
        assert log_file.exists()


def test_log_progress():
    """진행 상황 로깅 테스트"""
    logger = setup_cli_logging(level="INFO")
    
    # 예외가 발생하지 않아야 함
    log_progress(logger, 1, 3, "첫 번째 단계")
    log_progress(logger, 2, 3, "두 번째 단계")
    log_progress(logger, 3, 3, "세 번째 단계")


def test_get_logger():
    """모듈별 로거 가져오기 테스트"""
    setup_cli_logging()
    
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    
    assert logger1 is not None
    assert logger2 is not None
    assert logger1.name == "module1"
    assert logger2.name == "module2"


def test_logging_format():
    """로그 포맷 테스트"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_cli_logging(level="INFO", log_file=str(log_file))
        
        # 로그 메시지 작성
        logger.info("테스트 메시지")
        
        # 파일 내용 확인
        content = log_file.read_text(encoding="utf-8")
        
        # 포맷 확인: 날짜 - 이름 - 레벨 - 메시지
        assert " - " in content
        assert "INFO" in content
        assert "테스트 메시지" in content


def test_multiple_setup_calls():
    """여러 번 setup 호출 시 핸들러 중복 방지 테스트"""
    logger1 = setup_cli_logging(level="INFO")
    handler_count1 = len(logger1.handlers)
    
    logger2 = setup_cli_logging(level="DEBUG")
    handler_count2 = len(logger2.handlers)
    
    # 핸들러가 중복되지 않아야 함
    assert handler_count1 == handler_count2
