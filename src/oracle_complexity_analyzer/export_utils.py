"""
내보내기 유틸리티 모듈

분석 결과를 JSON, Markdown 등의 형식으로 내보내는 기능을 제공합니다.
"""

import logging
from pathlib import Path
from typing import Union
from datetime import datetime

from .data_models import SQLAnalysisResult, PLSQLAnalysisResult
from .enums import TargetDatabase

# 로거 초기화
logger = logging.getLogger(__name__)


def get_date_folder(output_dir: Path) -> Path:
    """날짜 폴더 경로 생성 (reports/YYYYMMDD/)
    
    Requirements 14.6, 14.7을 구현합니다.
    - 14.6: reports/YYYYMMDD/ 형식으로 폴더 생성
    - 14.7: 폴더가 없으면 자동 생성
    
    Args:
        output_dir: 기본 출력 디렉토리
        
    Returns:
        Path: 날짜 폴더 경로 (예: reports/20260114/)
    """
    # 현재 날짜를 YYYYMMDD 형식으로 포맷
    date_str = datetime.now().strftime("%Y%m%d")
    
    # 날짜 폴더 경로 생성
    date_folder = output_dir / date_str
    
    # 폴더가 없으면 자동 생성 (부모 폴더도 함께 생성)
    date_folder.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"날짜 폴더 생성: {date_folder}")
    
    return date_folder


def export_json(result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                filename: str, output_dir: Path, target: TargetDatabase) -> str:
    """분석 결과를 JSON 파일로 저장 (reports/YYYYMMDD/ 폴더에)
    
    Requirements 14.1, 14.6, 14.7을 구현합니다.
    - 14.1: JSON 형식으로 출력
    - 14.6: reports/YYYYMMDD/ 형식으로 저장
    - 14.7: 폴더가 없으면 자동 생성
    
    Args:
        result: 분석 결과 객체
        filename: 저장할 파일명 (예: "analysis_result.json")
        output_dir: 출력 디렉토리
        target: 타겟 데이터베이스
        
    Returns:
        str: 저장된 파일의 전체 경로
        
    Raises:
        IOError: 파일 쓰기 실패
    """
    # 필요한 모듈 import
    from src.formatters.result_formatter import ResultFormatter
    
    # 날짜 폴더 생성
    date_folder = get_date_folder(output_dir)
    
    # 파일 경로 생성
    file_path = date_folder / filename
    
    # JSON 변환
    json_str = ResultFormatter.to_json(result)
    
    # 파일 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        logger.error(f"JSON 파일 저장 실패: {file_path}", exc_info=True)
        raise IOError(f"JSON 파일 저장 실패: {e}")
    
    return str(file_path)


def export_markdown(result: Union[SQLAnalysisResult, PLSQLAnalysisResult], 
                    filename: str, output_dir: Path, target: TargetDatabase) -> str:
    """분석 결과를 Markdown 파일로 저장 (reports/YYYYMMDD/ 폴더에)
    
    Requirements 14.2, 14.6, 14.7을 구현합니다.
    - 14.2: Markdown 형식으로 출력
    - 14.6: reports/YYYYMMDD/ 형식으로 저장
    - 14.7: 폴더가 없으면 자동 생성
    
    Args:
        result: 분석 결과 객체
        filename: 저장할 파일명 (예: "analysis_report.md")
        output_dir: 출력 디렉토리
        target: 타겟 데이터베이스
        
    Returns:
        str: 저장된 파일의 전체 경로
        
    Raises:
        IOError: 파일 쓰기 실패
    """
    # 필요한 모듈 import
    from src.formatters.result_formatter import ResultFormatter
    
    # 날짜 폴더 생성
    date_folder = get_date_folder(output_dir)
    
    # 파일 경로 생성
    file_path = date_folder / filename
    
    # Markdown 변환
    markdown_str = ResultFormatter.to_markdown(result)
    
    # 파일 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_str)
    except Exception as e:
        logger.error(f"Markdown 파일 저장 실패: {file_path}", exc_info=True)
        raise IOError(f"Markdown 파일 저장 실패: {e}")
    
    return str(file_path)


def export_json_string(json_str: str, source_filename: str, output_dir: Path, target: TargetDatabase) -> str:
    """JSON 문자열을 파일로 저장
    
    Args:
        json_str: JSON 문자열
        source_filename: 원본 파일명
        output_dir: 출력 디렉토리
        target: 타겟 데이터베이스
        
    Returns:
        str: 저장된 파일의 전체 경로
    """
    source_path = Path(source_filename)
    
    # 소스 파일의 부모 폴더명 추출
    if source_path.parent != Path('.'):
        # 부모 폴더가 있는 경우 (예: sample_code/file.sql, MKDB/file.sql)
        parent_folder = source_path.parent.name
        
        # reports/{부모폴더명}/PGSQL 또는 MySQL 폴더에 저장
        target_folder = "PGSQL" if target == TargetDatabase.POSTGRESQL else "MySQL"
        output_folder = output_dir / parent_folder / target_folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (타겟 DB 접미사 없이)
        filename = source_path.stem + '.json'
        file_path = output_folder / filename
    else:
        # 부모 폴더가 없는 경우 (현재 디렉토리의 파일)
        # 날짜 폴더에 저장
        date_folder = get_date_folder(output_dir)
        
        # 타겟 데이터베이스 접미사 추가
        target_suffix = f"_{target.value}"
        
        # 파일명 생성 (확장자를 .json으로 변경, 타겟 DB 추가)
        filename = source_path.stem + target_suffix + '.json'
        file_path = date_folder / filename
    
    # 파일 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        logger.error(f"배치 분석 JSON 파일 저장 실패: {file_path}", exc_info=True)
        raise IOError(f"JSON 파일 저장 실패: {e}")
    
    return str(file_path)


def export_markdown_string(markdown_str: str, source_filename: str, output_dir: Path, target: TargetDatabase) -> str:
    """Markdown 문자열을 파일로 저장
    
    Args:
        markdown_str: Markdown 문자열
        source_filename: 원본 파일명
        output_dir: 출력 디렉토리
        target: 타겟 데이터베이스
        
    Returns:
        str: 저장된 파일의 전체 경로
    """
    source_path = Path(source_filename)
    
    # 부모 폴더가 있는지 확인 (현재 디렉토리가 아닌 경우)
    if source_path.parent != Path('.'):
        # 부모 폴더 이름 추출 (예: sample_code, MKDB 등)
        parent_folder = source_path.parent.name
        
        # reports/{parent_folder}/PGSQL 또는 MySQL 폴더에 저장
        target_folder = "PGSQL" if target == TargetDatabase.POSTGRESQL else "MySQL"
        output_folder = output_dir / parent_folder / target_folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (타겟 DB 접미사 없이)
        filename = source_path.stem + '.md'
        file_path = output_folder / filename
    else:
        # 부모 폴더가 없는 경우 날짜 폴더에 저장
        date_folder = get_date_folder(output_dir)
        
        # 타겟 데이터베이스 접미사 추가
        target_suffix = f"_{target.value}"
        
        # 파일명 생성 (확장자를 .md로 변경, 타겟 DB 추가)
        filename = source_path.stem + target_suffix + '.md'
        file_path = date_folder / filename
    
    # 파일 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_str)
    except Exception as e:
        logger.error(f"배치 분석 Markdown 파일 저장 실패: {file_path}", exc_info=True)
        raise IOError(f"Markdown 파일 저장 실패: {e}")
    
    return str(file_path)
