"""
로깅 설정 모듈

Statspack 분석기의 로깅을 설정합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    로깅 설정
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (선택적)
        console: 콘솔 출력 여부
        
    Returns:
        설정된 로거 인스턴스
    """
    # 로거 생성
    logger = logging.getLogger("statspack")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 콘솔 핸들러 추가
    if console:
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


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    로거 인스턴스 가져오기
    
    Args:
        name: 로거 이름 (선택적, 기본값: "statspack")
        
    Returns:
        로거 인스턴스
    """
    if name:
        return logging.getLogger(f"statspack.{name}")
    return logging.getLogger("statspack")
