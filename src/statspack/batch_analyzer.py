"""
Statspack 배치 분석 모듈

여러 Statspack 파일을 한 번에 분석하는 기능을 제공합니다.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .parser import StatspackParser
from .exceptions import StatspackParseError, StatspackFileError
from .data_models import StatspackData
from .migration_analyzer import MigrationAnalyzer, MigrationComplexity, TargetDatabase
from .logging_config import get_logger

# 로거 초기화
logger = get_logger("batch_analyzer")


@dataclass
class BatchFileResult:
    """배치 분석 개별 파일 결과"""
    filepath: str
    filename: str
    success: bool
    error_message: Optional[str] = None
    statspack_data: Optional[StatspackData] = None
    migration_analysis: Optional[Dict[TargetDatabase, MigrationComplexity]] = None


@dataclass
class BatchAnalysisResult:
    """배치 분석 전체 결과"""
    total_files: int
    successful_files: int
    failed_files: int
    file_results: List[BatchFileResult]
    analysis_timestamp: str


class BatchAnalyzer:
    """
    Statspack 배치 분석기
    
    디렉토리 내의 여러 .out 파일을 한 번에 분석합니다.
    """
    
    def __init__(self, directory: str):
        """
        배치 분석기 초기화
        
        Args:
            directory: Statspack 파일이 있는 디렉토리 경로
            
        Raises:
            FileNotFoundError: 디렉토리가 존재하지 않는 경우
            NotADirectoryError: 경로가 디렉토리가 아닌 경우
        """
        self.directory = Path(directory)
        
        # 디렉토리 존재 확인
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # 디렉토리인지 확인
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    def find_statspack_files(self) -> List[Path]:
        """
        디렉토리에서 .out 파일 찾기
        
        Returns:
            .out 파일 경로 리스트 (정렬됨)
        """
        # .out 확장자를 가진 파일 찾기
        out_files = list(self.directory.glob("*.out"))
        
        # 파일명으로 정렬
        out_files.sort(key=lambda p: p.name)
        
        return out_files
    
    def analyze_batch(
        self, 
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None
    ) -> BatchAnalysisResult:
        """
        배치 파일 분석 실행
        
        각 파일을 순차적으로 파싱하고, 오류 발생 시 건너뛰고 계속 진행합니다.
        
        Args:
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스 (None이면 모든 타겟)
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
        """
        # .out 파일 찾기
        out_files = self.find_statspack_files()
        
        if not out_files:
            # 파일이 없어도 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                successful_files=0,
                failed_files=0,
                file_results=[],
                analysis_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        
        file_results = []
        successful_count = 0
        failed_count = 0
        
        # 각 파일 순차 처리
        for filepath in out_files:
            result = self._analyze_single_file(
                filepath, 
                analyze_migration=analyze_migration,
                target=target
            )
            
            file_results.append(result)
            
            if result.success:
                successful_count += 1
            else:
                failed_count += 1
        
        # 배치 분석 결과 생성
        return BatchAnalysisResult(
            total_files=len(out_files),
            successful_files=successful_count,
            failed_files=failed_count,
            file_results=file_results,
            analysis_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    
    def _analyze_single_file(
        self,
        filepath: Path,
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None
    ) -> BatchFileResult:
        """
        단일 파일 분석
        
        Args:
            filepath: 파일 경로
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스
            
        Returns:
            BatchFileResult: 파일 분석 결과
        """
        try:
            # 파일 파싱
            parser = StatspackParser(str(filepath))
            statspack_data = parser.parse()
            
            # 마이그레이션 분석 (선택적)
            migration_analysis = None
            if analyze_migration:
                analyzer = MigrationAnalyzer(statspack_data)
                migration_analysis = analyzer.analyze(target=target)
            
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=True,
                statspack_data=statspack_data,
                migration_analysis=migration_analysis
            )
            
        except (StatspackParseError, StatspackFileError) as e:
            # 파싱 오류 - 건너뛰고 계속 진행
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            # 기타 예외 - 건너뛰고 계속 진행
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
