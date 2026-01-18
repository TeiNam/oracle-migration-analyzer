"""
파일 처리 모듈

배치 분석을 위한 파일 찾기, 타입 감지, 타임스탬프 추출 기능을 제공합니다.
"""

from pathlib import Path
from typing import List, Union
from datetime import datetime

from ..models import StatspackData, AWRData
from ..logging_config import get_logger

# 로거 초기화
logger = get_logger("file_processor")


class FileProcessor:
    """파일 처리 유틸리티"""
    
    @staticmethod
    def find_statspack_files(directory: Path) -> List[Path]:
        """
        디렉토리에서 .out 파일 찾기
        
        Args:
            directory: 검색할 디렉토리
            
        Returns:
            .out 파일 경로 리스트 (정렬됨)
        """
        # .out 확장자를 가진 파일 찾기
        out_files = list(directory.glob("*.out"))
        
        # 파일명으로 정렬
        out_files.sort(key=lambda p: p.name)
        
        return out_files
    
    @staticmethod
    def detect_file_type(filepath: Path) -> str:
        """
        파일 타입 자동 감지 (AWR vs Statspack)
        
        1. 먼저 파일명에서 AWR 또는 STATSPACK 키워드 확인
        2. 파일명에 없으면 파일 내용에서 AWR 특화 마커 확인
        
        Args:
            filepath: 파일 경로
            
        Returns:
            "awr" 또는 "statspack"
        """
        # 1. 파일명 확인 (대소문자 무시)
        filename_lower = filepath.name.lower()
        
        if 'awr' in filename_lower:
            return "awr"
        elif 'statspack' in filename_lower:
            return "statspack"
        
        # 2. 파일명에 타입 정보가 없으면 파일 내용 확인
        awr_markers = [
            "~~BEGIN-IOSTAT-FUNCTION~~",
            "~~BEGIN-PERCENT-CPU~~",
            "~~BEGIN-PERCENT-IO~~",
            "~~BEGIN-WORKLOAD~~",
            "~~BEGIN-BUFFER-CACHE~~"
        ]
        
        try:
            # UTF-8로 시도
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(50000)  # 처음 50KB만 읽기
        except UnicodeDecodeError:
            # Latin-1로 폴백
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read(50000)
            except Exception:
                # 읽기 실패 시 Statspack으로 간주
                return "statspack"
        except Exception:
            return "statspack"
        
        # AWR 마커 확인
        for marker in awr_markers:
            if marker in content:
                return "awr"
        
        return "statspack"
    
    @staticmethod
    def extract_timestamp(filepath: Path, data: Union[StatspackData, AWRData]) -> str:
        """
        파일 또는 데이터에서 타임스탬프 추출
        
        Args:
            filepath: 파일 경로
            data: Statspack 또는 AWR 데이터
            
        Returns:
            타임스탬프 문자열
        """
        # 1. 데이터에서 타임스탬프 추출 시도
        if data.main_metrics and len(data.main_metrics) > 0:
            # 마지막 스냅샷의 종료 시간 사용
            return data.main_metrics[-1].end
        
        # 2. 파일 수정 시간 사용
        try:
            mtime = filepath.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            # 3. 현재 시간 사용 (최후의 수단)
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
