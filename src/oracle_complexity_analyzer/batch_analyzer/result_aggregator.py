"""
결과 집계 및 리포트 생성 모듈

배치 분석 결과를 집계하고 다양한 형식의 리포트를 생성합니다.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from ..enums import TargetDatabase, ComplexityLevel
from ..data_models import BatchAnalysisResult

# 로거 초기화
logger = logging.getLogger(__name__)


class ResultAggregator:
    """결과 집계 및 리포트 생성 클래스
    
    배치 분석 결과를 집계하고 JSON/Markdown 리포트를 생성합니다.
    """
    
    def __init__(self, analyzer, source_folder_name: Optional[str] = None):
        """ResultAggregator 초기화
        
        Args:
            analyzer: OracleComplexityAnalyzer 인스턴스
            source_folder_name: 분석 대상 폴더명
        """
        self.analyzer = analyzer
        self.source_folder_name = source_folder_name
    
    @staticmethod
    def get_top_complex_files(batch_result: BatchAnalysisResult, top_n: int = 10) -> List[tuple]:
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
        
        logger.info(f"JSON 리포트 저장 완료: {file_path}")
        
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
        
        logger.info(f"Markdown 리포트 저장 완료: {file_path}")
        
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
        
        logger.info(f"{len(created_files)}개의 개별 리포트 생성 완료")
        
        return created_files
