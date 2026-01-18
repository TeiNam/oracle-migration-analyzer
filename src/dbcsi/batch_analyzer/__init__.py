"""
Statspack 배치 분석 모듈

여러 Statspack 파일을 한 번에 분석하는 기능을 제공합니다.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from ..migration_analyzer import TargetDatabase
from .data_models import (
    BatchFileResult,
    TrendMetrics,
    Anomaly,
    TrendAnalysisResult,
    BatchAnalysisResult
)
from .file_processor import FileProcessor
from .single_analyzer import SingleFileAnalyzer
from .trend_analyzer import TrendAnalyzer
from .anomaly_detector import AnomalyDetector


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
    
    def find_statspack_files(self):
        """
        디렉토리에서 .out 파일 찾기
        
        Returns:
            .out 파일 경로 리스트 (정렬됨)
        """
        return FileProcessor.find_statspack_files(self.directory)
    
    def analyze_batch(
        self, 
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None,
        analyze_trends: bool = False
    ) -> BatchAnalysisResult:
        """
        배치 파일 분석 실행
        
        각 파일을 순차적으로 파싱하고, 오류 발생 시 건너뛰고 계속 진행합니다.
        
        Args:
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스 (None이면 모든 타겟)
            analyze_trends: 추세 분석 포함 여부
            
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
            result = SingleFileAnalyzer.analyze_file(
                filepath, 
                analyze_migration=analyze_migration,
                target=target
            )
            
            file_results.append(result)
            
            if result.success:
                successful_count += 1
            else:
                failed_count += 1
        
        # 추세 분석 (선택적)
        trend_analysis = None
        if analyze_trends and successful_count > 1:
            trend_analysis = self._analyze_trends(file_results)
        
        # 배치 분석 결과 생성
        return BatchAnalysisResult(
            total_files=len(out_files),
            successful_files=successful_count,
            failed_files=failed_count,
            file_results=file_results,
            analysis_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            trend_analysis=trend_analysis
        )
    
    def _analyze_trends(self, file_results) -> TrendAnalysisResult:
        """
        추세 분석 수행
        
        Args:
            file_results: 파일 분석 결과 리스트
            
        Returns:
            TrendAnalysisResult: 추세 분석 결과
        """
        # 성공한 결과만 필터링
        successful_results = [r for r in file_results if r.success and r.statspack_data]
        
        if len(successful_results) < 2:
            return TrendAnalysisResult()
        
        # 타임스탬프 순으로 정렬
        successful_results.sort(key=lambda r: r.timestamp or "")
        
        # 각 메트릭별 추세 분석
        cpu_trend = TrendAnalyzer.analyze_cpu_trend(successful_results)
        io_trend = TrendAnalyzer.analyze_io_trend(successful_results)
        memory_trend = TrendAnalyzer.analyze_memory_trend(successful_results)
        buffer_cache_trend = TrendAnalyzer.analyze_buffer_cache_trend(successful_results)
        
        # 이상 징후 감지
        anomalies = AnomalyDetector.detect_anomalies(
            successful_results, 
            cpu_trend, 
            io_trend, 
            memory_trend, 
            buffer_cache_trend
        )
        
        return TrendAnalysisResult(
            cpu_trend=cpu_trend,
            io_trend=io_trend,
            memory_trend=memory_trend,
            buffer_cache_trend=buffer_cache_trend,
            anomalies=anomalies
        )


# Export all data models and main class
__all__ = [
    'BatchAnalyzer',
    'BatchFileResult',
    'TrendMetrics',
    'Anomaly',
    'TrendAnalysisResult',
    'BatchAnalysisResult'
]
