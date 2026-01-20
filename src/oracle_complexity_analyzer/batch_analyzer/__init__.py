"""
BatchAnalyzer 모듈

폴더 내 SQL/PL/SQL 파일 일괄 분석 기능을 제공합니다.
배치 PL/SQL 파일(.out)도 지원합니다.
"""

import logging
import concurrent.futures
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any

from ..enums import ComplexityLevel
from ..data_models import BatchAnalysisResult
from .file_processor import FileProcessor
from .result_aggregator import ResultAggregator

# 로거 초기화
logger = logging.getLogger(__name__)


def _process_result(result: Union[Dict[str, Any], Any], 
                    complexity_distribution: Dict[str, int]) -> float:
    """분석 결과 처리 (배치 PL/SQL 또는 일반 결과)
    
    Args:
        result: 분석 결과 (딕셔너리 또는 데이터 클래스)
        complexity_distribution: 복잡도 분포 딕셔너리
        
    Returns:
        float: 누적할 점수
    """
    total_score = 0.0
    
    # 배치 PL/SQL 파일인 경우 딕셔너리로 반환됨
    if isinstance(result, dict):
        # 배치 PL/SQL 결과 처리
        for obj_result in result.get('results', []):
            # analysis는 PLSQLAnalysisResult 객체
            analysis = obj_result.get('analysis')
            if analysis:
                # 데이터 클래스 객체에서 속성 접근
                level_name = analysis.complexity_level.value
                complexity_distribution[level_name] += 1
                total_score += analysis.normalized_score
    else:
        # 일반 SQL/PL/SQL 결과 처리
        level_name = result.complexity_level.value
        complexity_distribution[level_name] += 1
        total_score += result.normalized_score
    
    return total_score


class BatchAnalyzer:
    """폴더 내 SQL/PL/SQL 파일 일괄 분석 클래스
    
    지정된 폴더 내의 모든 SQL/PL/SQL 파일을 병렬 처리로 일괄 분석합니다.
    
    Requirements:
    - 전체: 폴더 일괄 분석 및 병렬 처리
    
    Attributes:
        analyzer: OracleComplexityAnalyzer 인스턴스
        max_workers: 병렬 처리 워커 수 (기본값: CPU 코어 수)
        file_processor: 파일 검색 처리기
        result_aggregator: 결과 집계 및 리포트 생성기
    """
    
    # 지원하는 파일 확장자 (하위 호환성을 위해 유지)
    SUPPORTED_EXTENSIONS = FileProcessor.SUPPORTED_EXTENSIONS
    
    def __init__(self, analyzer, max_workers: Optional[int] = None):
        """BatchAnalyzer 초기화
        
        Args:
            analyzer: OracleComplexityAnalyzer 인스턴스
            max_workers: 병렬 처리 워커 수 (None이면 CPU 코어 수 사용)
        """
        self.analyzer = analyzer
        self.max_workers = max_workers or os.cpu_count()
        self.source_folder_name: Optional[str] = None  # 분석 대상 폴더명 저장
        
        # 하위 모듈 초기화
        self.file_processor = FileProcessor()
        self.result_aggregator = ResultAggregator(analyzer)
        
        logger.info(f"BatchAnalyzer 초기화: max_workers={self.max_workers}")
    
    def find_sql_files(self, folder_path: str):
        """폴더 내 SQL/PL/SQL 파일 검색 (하위 호환성 메서드)
        
        Args:
            folder_path: 검색할 폴더 경로
            
        Returns:
            List[Path]: 찾은 파일 경로 리스트
        """
        return self.file_processor.find_sql_files(folder_path)
    
    def _analyze_single_file(self, file_path: Path) -> tuple:
        """단일 파일 분석 (병렬 처리용 헬퍼 메서드)
        
        Args:
            file_path: 분석할 파일 경로
            
        Returns:
            tuple: (파일명, 분석 결과 또는 None, 에러 메시지 또는 None)
        """
        file_name = str(file_path)
        
        try:
            result = self.analyzer.analyze_file(file_name)
            return (file_name, result, None)
        except Exception as e:
            logger.error(f"파일 분석 실패: {file_name}", exc_info=True)
            return (file_name, None, str(e))
    
    def analyze_folder(self, folder_path: str) -> BatchAnalysisResult:
        """폴더 내 모든 SQL/PL/SQL 파일 일괄 분석
        
        concurrent.futures를 사용하여 병렬 처리로 파일들을 분석합니다.
        
        Requirements:
        - 전체: 폴더 일괄 분석 및 병렬 처리
        
        Args:
            folder_path: 분석할 폴더 경로
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        # 분석 대상 폴더명 저장 (경로에서 폴더명만 추출)
        self.source_folder_name = Path(folder_path).name
        self.result_aggregator.source_folder_name = self.source_folder_name
        
        # SQL/PL/SQL 파일 검색
        sql_files = self.file_processor.find_sql_files(folder_path)
        
        if not sql_files:
            # 파일이 없으면 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                success_count=0,
                failure_count=0,
                target_database=self.analyzer.target
            )
        
        # 결과 저장용 변수
        results = {}
        failed_files = {}
        complexity_distribution = {level.value: 0 for level in ComplexityLevel}
        total_score = 0.0
        
        # 병렬 처리로 파일 분석
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 파일에 대해 분석 작업 제출
            future_to_file = {
                executor.submit(self._analyze_single_file, file_path): file_path
                for file_path in sql_files
            }
            
            # 완료된 작업 결과 수집
            for future in concurrent.futures.as_completed(future_to_file):
                file_name, result, error = future.result()
                
                if error:
                    # 분석 실패
                    failed_files[file_name] = error
                else:
                    # 분석 성공
                    results[file_name] = result
                    
                    # 결과 처리 (배치 PL/SQL 또는 일반 결과)
                    total_score += _process_result(result, complexity_distribution)
        
        # 평균 점수 계산
        success_count = len(results)
        average_score = total_score / success_count if success_count > 0 else 0.0
        
        # 배치 분석 결과 생성
        batch_result = BatchAnalysisResult(
            total_files=len(sql_files),
            success_count=success_count,
            failure_count=len(failed_files),
            complexity_distribution=complexity_distribution,
            average_score=average_score,
            results=results,
            failed_files=failed_files,
            target_database=self.analyzer.target
        )
        
        logger.info(f"배치 분석 완료: {success_count}/{len(sql_files)} 파일 성공")
        
        return batch_result
    
    def analyze_folder_with_progress(self, folder_path: str, 
                                     progress_callback=None) -> BatchAnalysisResult:
        """폴더 내 모든 SQL/PL/SQL 파일 일괄 분석 (진행 상황 표시 포함)
        
        concurrent.futures를 사용하여 병렬 처리로 파일들을 분석하며,
        tqdm을 사용하여 진행 상황을 표시합니다.
        
        Requirements:
        - 전체: 폴더 일괄 분석 및 병렬 처리, 진행 상황 표시
        
        Args:
            folder_path: 분석할 폴더 경로
            progress_callback: 진행 상황 콜백 함수 (선택사항)
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        # 분석 대상 폴더명 저장 (경로에서 폴더명만 추출)
        self.source_folder_name = Path(folder_path).name
        self.result_aggregator.source_folder_name = self.source_folder_name
        
        # SQL/PL/SQL 파일 검색
        sql_files = self.file_processor.find_sql_files(folder_path)
        
        if not sql_files:
            # 파일이 없으면 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                success_count=0,
                failure_count=0,
                target_database=self.analyzer.target
            )
        
        # 결과 저장용 변수
        results = {}
        failed_files = {}
        complexity_distribution = {level.value: 0 for level in ComplexityLevel}
        total_score = 0.0
        
        # tqdm 사용 가능 여부 확인
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        
        # 병렬 처리로 파일 분석
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 파일에 대해 분석 작업 제출
            future_to_file = {
                executor.submit(self._analyze_single_file, file_path): file_path
                for file_path in sql_files
            }
            
            # 진행 상황 표시 설정
            if use_tqdm:
                # tqdm 프로그레스 바 생성
                pbar = tqdm(
                    total=len(sql_files),
                    desc="파일 분석",
                    unit="파일",
                    ncols=80,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                )
            
            # 완료된 작업 결과 수집
            for future in concurrent.futures.as_completed(future_to_file):
                file_name, result, error = future.result()
                
                if error:
                    # 분석 실패
                    failed_files[file_name] = error
                else:
                    # 분석 성공
                    results[file_name] = result
                    
                    # 결과 처리 (배치 PL/SQL 또는 일반 결과)
                    total_score += _process_result(result, complexity_distribution)
                
                # 진행 상황 업데이트
                if use_tqdm:
                    pbar.update(1)
                elif progress_callback:
                    progress_callback(len(results) + len(failed_files), len(sql_files))
            
            # 프로그레스 바 닫기
            if use_tqdm:
                pbar.close()
        
        # 평균 점수 계산
        success_count = len(results)
        average_score = total_score / success_count if success_count > 0 else 0.0
        
        # 배치 분석 결과 생성
        batch_result = BatchAnalysisResult(
            total_files=len(sql_files),
            success_count=success_count,
            failure_count=len(failed_files),
            complexity_distribution=complexity_distribution,
            average_score=average_score,
            results=results,
            failed_files=failed_files,
            target_database=self.analyzer.target
        )
        
        logger.info(f"배치 분석 완료 (진행 상황 표시): {success_count}/{len(sql_files)} 파일 성공")
        
        return batch_result
    
    # 하위 호환성을 위한 메서드 위임
    def get_top_complex_files(self, batch_result: BatchAnalysisResult, top_n: int = 10):
        """복잡도가 높은 파일 Top N 추출 (하위 호환성 메서드)"""
        return self.result_aggregator.get_top_complex_files(batch_result, top_n)
    
    def export_batch_json(self, batch_result: BatchAnalysisResult, include_details: bool = True) -> str:
        """배치 분석 결과를 JSON 파일로 저장 (하위 호환성 메서드)"""
        return self.result_aggregator.export_batch_json(batch_result, include_details)
    
    def export_batch_markdown(self, batch_result: BatchAnalysisResult, include_details: bool = False) -> str:
        """배치 분석 결과를 Markdown 파일로 저장 (하위 호환성 메서드)"""
        return self.result_aggregator.export_batch_markdown(batch_result, include_details)
    
    def export_individual_reports(self, batch_result: BatchAnalysisResult):
        """배치 분석 결과에서 개별 파일별 리포트를 생성 (하위 호환성 메서드)"""
        return self.result_aggregator.export_individual_reports(batch_result)


# Public API
__all__ = ['BatchAnalyzer']
