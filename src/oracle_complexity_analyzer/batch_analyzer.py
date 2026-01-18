"""
BatchAnalyzer 클래스

폴더 내 SQL/PL/SQL 파일 일괄 분석 기능을 제공합니다.
"""

import logging
import concurrent.futures
import json
from pathlib import Path
from typing import List, Optional, Dict
import os

from .enums import TargetDatabase, ComplexityLevel
from .data_models import BatchAnalysisResult

# 로거 초기화
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """폴더 내 SQL/PL/SQL 파일 일괄 분석 클래스
    
    지정된 폴더 내의 모든 SQL/PL/SQL 파일을 병렬 처리로 일괄 분석합니다.
    
    Requirements:
    - 전체: 폴더 일괄 분석 및 병렬 처리
    
    Attributes:
        analyzer: OracleComplexityAnalyzer 인스턴스
        max_workers: 병렬 처리 워커 수 (기본값: CPU 코어 수)
        supported_extensions: 지원하는 파일 확장자
    """
    
    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = {'.sql', '.pls', '.pkb', '.pks', '.prc', '.fnc', '.trg'}
    
    def __init__(self, analyzer, max_workers: Optional[int] = None):
        """BatchAnalyzer 초기화
        
        Args:
            analyzer: OracleComplexityAnalyzer 인스턴스
            max_workers: 병렬 처리 워커 수 (None이면 CPU 코어 수 사용)
        """
        self.analyzer = analyzer
        self.max_workers = max_workers or os.cpu_count()
        self.source_folder_name = None  # 분석 대상 폴더명 저장
        
        logger.info(f"BatchAnalyzer 초기화: max_workers={self.max_workers}")
    
    def find_sql_files(self, folder_path: str) -> List[Path]:
        """폴더 내 SQL/PL/SQL 파일 검색
        
        지정된 폴더와 하위 폴더에서 지원하는 확장자를 가진 파일을 모두 찾습니다.
        
        Args:
            folder_path: 검색할 폴더 경로
            
        Returns:
            List[Path]: 찾은 파일 경로 리스트
            
        Raises:
            FileNotFoundError: 폴더가 존재하지 않는 경우
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")
        
        if not folder.is_dir():
            raise ValueError(f"폴더가 아닙니다: {folder_path}")
        
        # 지원하는 확장자를 가진 파일 찾기
        sql_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            # 재귀적으로 파일 검색 (** 패턴 사용)
            sql_files.extend(folder.rglob(f"*{ext}"))
        
        return sorted(sql_files)
    
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
        
        # SQL/PL/SQL 파일 검색
        sql_files = self.find_sql_files(folder_path)
        
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
                    
                    # 복잡도 레벨별 분포 집계
                    level_name = result.complexity_level.value
                    complexity_distribution[level_name] += 1
                    
                    # 총 점수 누적
                    total_score += result.normalized_score
        
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
        
        # SQL/PL/SQL 파일 검색
        sql_files = self.find_sql_files(folder_path)
        
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
                    
                    # 복잡도 레벨별 분포 집계
                    level_name = result.complexity_level.value
                    complexity_distribution[level_name] += 1
                    
                    # 총 점수 누적
                    total_score += result.normalized_score
                
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
        
        return batch_result
    
    def get_top_complex_files(self, batch_result: BatchAnalysisResult, top_n: int = 10) -> List[tuple]:
        """복잡도가 높은 파일 Top N 추출
        
        Args:
            batch_result: 배치 분석 결과
            top_n: 추출할 파일 수 (기본값: 10)
            
        Returns:
            List[tuple]: (파일명, 복잡도 점수) 튜플 리스트 (점수 내림차순)
        """
        # 파일명과 점수를 튜플로 만들어 리스트 생성
        file_scores = [
            (file_name, result.normalized_score)
            for file_name, result in batch_result.results.items()
        ]
        
        # 점수 기준 내림차순 정렬
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Top N 반환
        return file_scores[:top_n]
    
    def export_batch_json(self, batch_result: BatchAnalysisResult, 
                          include_details: bool = True) -> str:
        """배치 분석 결과를 JSON 파일로 저장
        
        Requirements 14.1, 14.6, 14.7, 14.8을 구현합니다.
        - 14.1: JSON 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: True)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        from src.formatters.result_formatter import ResultFormatter
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 폴더 경로 생성: reports/{분석대상폴더명}/{타겟}/
        report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / target_folder
        report_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (sql_complexity_PGSQL.json 또는 sql_complexity_MySQL.json)
        filename = f"sql_complexity_{target_folder}.json"
        file_path = report_folder / filename
        
        # JSON 데이터 구성
        json_data = {
            "summary": {
                "total_files": batch_result.total_files,
                "success_count": batch_result.success_count,
                "failure_count": batch_result.failure_count,
                "average_score": round(batch_result.average_score, 2),
                "target_database": batch_result.target_database.value,
                "analysis_time": batch_result.analysis_time,
            },
            "complexity_distribution": batch_result.complexity_distribution,
            "top_complex_files": [
                {"file": file_name, "score": round(score, 2)}
                for file_name, score in self.get_top_complex_files(batch_result, 10)
            ],
            "failed_files": batch_result.failed_files,
        }
        
        # 개별 파일 상세 결과 포함
        if include_details:
            json_data["details"] = {}
            for file_name, result in batch_result.results.items():
                # 각 결과를 JSON으로 변환 후 다시 파싱 (dict로 변환)
                result_json = ResultFormatter.to_json(result)
                json_data["details"][file_name] = json.loads(result_json)
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def export_batch_markdown(self, batch_result: BatchAnalysisResult,
                              include_details: bool = False) -> str:
        """배치 분석 결과를 Markdown 파일로 저장
        
        Requirements 14.2, 14.6, 14.7, 14.8을 구현합니다.
        - 14.2: Markdown 형식으로 출력
        - 14.6: reports/YYYYMMDD/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: False)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        from src.formatters.result_formatter import ResultFormatter
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 폴더 경로 생성: reports/{분석대상폴더명}/{타겟}/
        report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / target_folder
        report_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (sql_complexity_PGSQL.md 또는 sql_complexity_MySQL.md)
        filename = f"sql_complexity_{target_folder}.md"
        file_path = report_folder / filename
        
        # Markdown 내용 생성
        lines = []
        
        # 제목
        lines.append("# Oracle 복잡도 분석 배치 리포트\n")
        lines.append(f"**분석 시간**: {batch_result.analysis_time}\n")
        lines.append(f"**타겟 데이터베이스**: {batch_result.target_database.value}\n")
        lines.append("\n---\n")
        
        # 요약 통계
        lines.append("## 📊 요약 통계\n")
        lines.append(f"- **전체 파일 수**: {batch_result.total_files}\n")
        lines.append(f"- **분석 성공**: {batch_result.success_count}\n")
        lines.append(f"- **분석 실패**: {batch_result.failure_count}\n")
        lines.append(f"- **평균 복잡도 점수**: {batch_result.average_score:.2f} / 10\n")
        lines.append("\n")
        
        # 복잡도 레벨별 분포
        lines.append("## 📈 복잡도 레벨별 분포\n")
        lines.append("| 복잡도 레벨 | 파일 수 | 비율 |\n")
        lines.append("|------------|---------|------|\n")
        
        for level in ComplexityLevel:
            count = batch_result.complexity_distribution.get(level.value, 0)
            percentage = (count / batch_result.success_count * 100) if batch_result.success_count > 0 else 0
            lines.append(f"| {level.value} | {count} | {percentage:.1f}% |\n")
        
        lines.append("\n")
        
        # 전체 파일 복잡도 목록 (복잡도 높은 순으로 정렬)
        lines.append("## 📋 전체 파일 복잡도 목록\n")
        lines.append("| 순위 | 파일명 | 복잡도 점수 | 복잡도 레벨 |\n")
        lines.append("|------|--------|-------------|-------------|\n")
        
        # 모든 파일을 복잡도 점수 기준으로 정렬
        all_files = sorted(
            [(file_name, result.normalized_score, result.complexity_level.value) 
             for file_name, result in batch_result.results.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for idx, (file_name, score, level) in enumerate(all_files, 1):
            lines.append(f"| {idx} | `{file_name}` | {score:.2f} | {level} |\n")
        
        lines.append("\n")
        
        # 실패한 파일 목록
        if batch_result.failed_files:
            lines.append("## ❌ 분석 실패 파일\n")
            lines.append("| 파일명 | 에러 메시지 |\n")
            lines.append("|--------|-------------|\n")
            
            for file_name, error in batch_result.failed_files.items():
                lines.append(f"| `{file_name}` | {error} |\n")
            
            lines.append("\n")
        
        # 개별 파일 상세 결과
        if include_details and batch_result.results:
            lines.append("## 📄 개별 파일 상세 결과\n")
            lines.append("\n")
            
            for file_name, result in batch_result.results.items():
                lines.append(f"### {file_name}\n")
                lines.append("\n")
                
                # 각 결과를 Markdown으로 변환
                result_md = ResultFormatter.to_markdown(result)
                lines.append(result_md)
                lines.append("\n---\n\n")
        
        # 파일 저장
        markdown_content = "".join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(file_path)
    
    def export_individual_reports(self, batch_result: BatchAnalysisResult) -> List[str]:
        """배치 분석 결과에서 개별 파일별 리포트를 생성
        
        각 분석된 파일에 대해 별도의 Markdown 리포트를 생성합니다.
        
        Args:
            batch_result: 배치 분석 결과
            
        Returns:
            List[str]: 생성된 개별 리포트 파일 경로 리스트
        """
        from src.formatters.result_formatter import ResultFormatter
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 폴더 경로 생성: reports/{분석대상폴더명}/{타겟}/
        report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / target_folder
        report_folder.mkdir(parents=True, exist_ok=True)
        
        # 생성된 파일 경로 리스트
        created_files = []
        
        # 각 파일별로 리포트 생성
        for file_path, result in batch_result.results.items():
            # 파일명 추출 (경로에서 파일명만)
            file_name = Path(file_path).stem
            
            # 개별 리포트 파일명 생성: {파일명}.md
            report_filename = f"{file_name}.md"
            report_path = report_folder / report_filename
            
            # Markdown 변환
            markdown_str = ResultFormatter.to_markdown(result)
            
            # 파일 저장
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown_str)
            
            created_files.append(str(report_path))
        
        return created_files
