"""
파일 검색 및 처리 모듈

SQL/PL/SQL 파일 검색 기능을 제공합니다.
"""

import logging
from pathlib import Path
from typing import List

# 로거 초기화
logger = logging.getLogger(__name__)


class FileProcessor:
    """파일 검색 및 처리 클래스
    
    지정된 폴더에서 SQL/PL/SQL 파일을 검색합니다.
    
    Attributes:
        SUPPORTED_EXTENSIONS: 지원하는 파일 확장자 집합
    """
    
    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = {'.sql', '.pls', '.pkb', '.pks', '.prc', '.fnc', '.trg', '.out'}
    
    # AWR/Statspack 파일 제외 키워드
    EXCLUDED_KEYWORDS = ['awr', 'statspack', 'dbcsi']
    
    @staticmethod
    def is_excluded_file(file_path: Path) -> bool:
        """AWR/Statspack 파일 여부 확인
        
        파일명에 제외 키워드가 포함되어 있는지 확인합니다.
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            bool: 제외 대상이면 True
        """
        filename_lower = file_path.name.lower()
        return any(keyword in filename_lower for keyword in FileProcessor.EXCLUDED_KEYWORDS)
    
    @staticmethod
    def find_sql_files(folder_path: str) -> List[Path]:
        """폴더 내 SQL/PL/SQL 파일 검색
        
        지정된 폴더와 하위 폴더에서 지원하는 확장자를 가진 파일을 모두 찾습니다.
        .out 파일 중 AWR/Statspack 파일은 제외합니다.
        
        Args:
            folder_path: 검색할 폴더 경로
            
        Returns:
            List[Path]: 찾은 파일 경로 리스트
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
            ValueError: 폴더가 아닌 경우
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")
        
        if not folder.is_dir():
            raise ValueError(f"폴더가 아닙니다: {folder_path}")
        
        # 지원하는 확장자를 가진 파일 찾기
        sql_files: List[Path] = []
        for ext in FileProcessor.SUPPORTED_EXTENSIONS:
            # 재귀적으로 파일 검색 (** 패턴 사용)
            found_files = folder.rglob(f"*{ext}")
            
            # .out 파일의 경우 AWR/Statspack 파일 제외
            if ext == '.out':
                found_files = [f for f in found_files if not FileProcessor.is_excluded_file(f)]
            
            sql_files.extend(found_files)
        
        logger.info(f"폴더 '{folder_path}'에서 {len(sql_files)}개의 SQL/PL/SQL 파일 발견")
        
        return sorted(sql_files)
