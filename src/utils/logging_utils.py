"""
로깅 유틸리티 모듈

CLI 도구들을 위한 표준화된 로깅 설정을 제공합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_cli_logging(
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    CLI용 로깅 설정
    
    표준화된 로깅 설정을 제공하여 모든 CLI 도구에서 일관된 로그 출력을 보장합니다.
    콘솔과 파일 로깅을 모두 지원하며, 적절한 포맷팅을 적용합니다.
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (선택적, 지정 시 파일에도 로그 기록)
        
    Returns:
        설정된 로거 인스턴스
        
    Example:
        >>> logger = setup_cli_logging(level="DEBUG", log_file="app.log")
        >>> logger.info("애플리케이션 시작")
        >>> logger.error("오류 발생", exc_info=True)
    """
    # 루트 로거 가져오기
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 콘솔 핸들러 추가 (항상 활성화)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (선택적)
    if log_file:
        # 로그 파일 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_progress(logger: logging.Logger, step: int, total: int, message: str) -> None:
    """
    진행 상황 로깅
    
    작업 진행 상황을 일관된 형식으로 로깅합니다.
    INFO 레벨로 로그를 기록하며, 단계 정보와 메시지를 포함합니다.
    
    Args:
        logger: 로거 인스턴스
        step: 현재 단계 (1부터 시작)
        total: 전체 단계 수
        message: 진행 상황 메시지
        
    Example:
        >>> logger = setup_cli_logging()
        >>> log_progress(logger, 1, 3, "파일 파싱 중...")
        >>> log_progress(logger, 2, 3, "데이터 분석 중...")
        >>> log_progress(logger, 3, 3, "리포트 생성 완료")
    """
    logger.info(f"[{step}/{total}] {message}")


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 인스턴스 가져오기
    
    특정 모듈이나 컴포넌트를 위한 로거를 반환합니다.
    setup_cli_logging()이 먼저 호출되어야 합니다.
    
    Args:
        name: 로거 이름 (일반적으로 모듈명 또는 컴포넌트명)
        
    Returns:
        로거 인스턴스
        
    Example:
        >>> setup_cli_logging()
        >>> logger = get_logger("analyzer")
        >>> logger.info("분석 시작")
    """
    return logging.getLogger(name)
