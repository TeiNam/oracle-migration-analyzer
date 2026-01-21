"""
결과 집계 및 리포트 생성 모듈

배치 분석 결과를 집계하고 다양한 형식의 리포트를 생성합니다.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict

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
        file_scores = []
        for file_name, result in batch_result.results.items():
            # 배치 PL/SQL 결과인 경우 딕셔너리
            if isinstance(result, dict):
                # 배치 PL/SQL 파일의 평균 점수 계산
                results_list = result.get('results', [])
                if results_list:
                    total_score = sum(
                        obj_result.get('analysis').normalized_score 
                        for obj_result in results_list 
                        if obj_result.get('analysis')
                    )
                    avg_score = total_score / len(results_list)
                    file_scores.append((file_name, avg_score))
            else:
                # 일반 SQL/PL/SQL 결과
                file_scores.append((file_name, result.normalized_score))
        
        # 점수 기준 내림차순 정렬
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Top N 반환
        return file_scores[:top_n]
    
    def export_batch_json(self, batch_result: BatchAnalysisResult, 
                          include_details: bool = True) -> str:
        """배치 분석 결과를 JSON 파일로 저장
        
        원본 소스 폴더 구조를 reports 폴더 밑에 유지하면서 저장합니다.
        파일 타입(SQL/PL-SQL)에 따라 폴더를 구분합니다.
        예: adb 폴더 분석 시 -> reports/adb/sql/MySQL/sql_complexity_MySQL.json
                              reports/adb/plsql/MySQL/plsql_complexity_MySQL.json
        
        Requirements 14.1, 14.6, 14.7, 14.8을 구현합니다.
        - 14.1: JSON 형식으로 출력
        - 14.6: reports/{원본폴더}/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: True)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        from src.formatters.result_formatter import ResultFormatter
        from ..file_detector import detect_file_type
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 파일 타입별로 결과를 분류
        sql_results = {}
        plsql_results = {}
        
        for file_name, result in batch_result.results.items():
            # 파일 내용을 읽어서 타입 감지
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_type = detect_file_type(content)
                
                if file_type == 'sql':
                    sql_results[file_name] = result
                else:  # plsql 또는 batch_plsql
                    plsql_results[file_name] = result
            except Exception as e:
                logger.warning(f"파일 타입 감지 실패: {file_name}, 기본값(sql) 사용")
                sql_results[file_name] = result
        
        # SQL과 PL/SQL 각각 저장
        saved_files = []
        
        # SQL 결과 저장
        if sql_results:
            sql_batch = self._create_sub_batch_result(batch_result, sql_results, 'sql')
            sql_file = self._save_batch_json(sql_batch, 'sql', target_folder, include_details)
            saved_files.append(sql_file)
        
        # PL/SQL 결과 저장
        if plsql_results:
            plsql_batch = self._create_sub_batch_result(batch_result, plsql_results, 'plsql')
            plsql_file = self._save_batch_json(plsql_batch, 'plsql', target_folder, include_details)
            saved_files.append(plsql_file)
        
        return ', '.join(saved_files)
    
    def _create_sub_batch_result(self, original_batch: BatchAnalysisResult, 
                                  filtered_results: Dict, file_type: str) -> BatchAnalysisResult:
        """파일 타입별로 필터링된 배치 결과 생성"""
        # 복잡도 분포 재계산
        complexity_distribution = {level.value: 0 for level in ComplexityLevel}
        total_score = 0.0
        
        for result in filtered_results.values():
            if isinstance(result, dict):
                # 배치 PL/SQL 결과
                for obj_result in result.get('results', []):
                    analysis = obj_result.get('analysis')
                    if analysis:
                        level_name = analysis.complexity_level.value
                        complexity_distribution[level_name] += 1
                        total_score += analysis.normalized_score
            else:
                # 일반 SQL/PL/SQL 결과
                level_name = result.complexity_level.value
                complexity_distribution[level_name] += 1
                total_score += result.normalized_score
        
        success_count = len(filtered_results)
        average_score = total_score / success_count if success_count > 0 else 0.0
        
        return BatchAnalysisResult(
            total_files=success_count,
            success_count=success_count,
            failure_count=0,
            complexity_distribution=complexity_distribution,
            average_score=average_score,
            results=filtered_results,
            failed_files={},
            target_database=original_batch.target_database,
            analysis_time=original_batch.analysis_time
        )
    
    def _save_batch_json(self, batch_result: BatchAnalysisResult, file_type: str,
                         target_folder: str, include_details: bool) -> str:
        """파일 타입별 배치 JSON 저장"""
        from src.formatters.result_formatter import ResultFormatter
        
        # 폴더 경로 생성: reports/{분석대상폴더명}/{타입}/{타겟}/
        report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / file_type / target_folder
        report_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (sql_complexity_PGSQL.json 또는 plsql_complexity_MySQL.json)
        filename = f"{file_type}_complexity_{target_folder}.json"
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
                "file_type": file_type,
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
        
        원본 소스 폴더 구조를 reports 폴더 밑에 유지하면서 저장합니다.
        파일 타입(SQL/PL-SQL)에 따라 폴더를 구분합니다.
        예: adb 폴더 분석 시 -> reports/adb/sql/MySQL/sql_complexity_MySQL.md
                              reports/adb/plsql/MySQL/plsql_complexity_MySQL.md
        
        Requirements 14.2, 14.6, 14.7, 14.8을 구현합니다.
        - 14.2: Markdown 형식으로 출력
        - 14.6: reports/{원본폴더}/ 형식으로 저장
        - 14.7: 폴더가 없으면 자동 생성
        - 14.8: 요약 리포트와 개별 파일 리포트 저장
        
        Args:
            batch_result: 배치 분석 결과
            include_details: 개별 파일 상세 결과 포함 여부 (기본값: False)
            
        Returns:
            str: 저장된 파일의 전체 경로
        """
        from src.formatters.result_formatter import ResultFormatter
        from ..file_detector import detect_file_type
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 파일 타입별로 결과를 분류
        sql_results = {}
        plsql_results = {}
        
        for file_name, result in batch_result.results.items():
            # 파일 내용을 읽어서 타입 감지
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_type = detect_file_type(content)
                
                if file_type == 'sql':
                    sql_results[file_name] = result
                else:  # plsql 또는 batch_plsql
                    plsql_results[file_name] = result
            except Exception as e:
                logger.warning(f"파일 타입 감지 실패: {file_name}, 기본값(sql) 사용")
                sql_results[file_name] = result
        
        # SQL과 PL/SQL 각각 저장
        saved_files = []
        
        # SQL 결과 저장
        if sql_results:
            sql_batch = self._create_sub_batch_result(batch_result, sql_results, 'sql')
            sql_file = self._save_batch_markdown(sql_batch, 'sql', target_folder, include_details)
            saved_files.append(sql_file)
        
        # PL/SQL 결과 저장
        if plsql_results:
            plsql_batch = self._create_sub_batch_result(batch_result, plsql_results, 'plsql')
            plsql_file = self._save_batch_markdown(plsql_batch, 'plsql', target_folder, include_details)
            saved_files.append(plsql_file)
        
        return ', '.join(saved_files)
    
    def _save_batch_markdown(self, batch_result: BatchAnalysisResult, file_type: str,
                             target_folder: str, include_details: bool) -> str:
        """파일 타입별 배치 Markdown 저장"""
        from src.formatters.result_formatter import ResultFormatter
        
        # 폴더 경로 생성: reports/{분석대상폴더명}/{타입}/{타겟}/
        report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / file_type / target_folder
        report_folder.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (sql_complexity_PGSQL.md 또는 plsql_complexity_MySQL.md)
        filename = f"{file_type}_complexity_{target_folder}.md"
        file_path = report_folder / filename
        
        # Markdown 내용 생성
        lines = []
        
        # 제목
        file_type_name = "SQL" if file_type == "sql" else "PL/SQL"
        lines.append(f"# Oracle {file_type_name} 복잡도 분석 배치 리포트\n")
        lines.append(f"**분석 시간**: {batch_result.analysis_time}\n")
        lines.append(f"**타겟 데이터베이스**: {batch_result.target_database.value}\n")
        lines.append(f"**파일 타입**: {file_type_name}\n")
        lines.append("\n---\n")
        
        # 요약 통계
        lines.append("## 요약 통계\n")
        lines.append(f"- **전체 파일 수**: {batch_result.total_files}\n")
        lines.append(f"- **분석 성공**: {batch_result.success_count}\n")
        lines.append(f"- **분석 실패**: {batch_result.failure_count}\n")
        lines.append(f"- **평균 복잡도 점수**: {batch_result.average_score:.2f} / 10\n")
        lines.append("\n")
        
        # 복잡도 레벨별 분포
        lines.append("## 복잡도 레벨별 분포\n")
        lines.append("| 복잡도 레벨 | 파일 수 | 비율 |\n")
        lines.append("|------------|---------|------|\n")
        
        for level in ComplexityLevel:
            count = batch_result.complexity_distribution.get(level.value, 0)
            percentage = (count / batch_result.success_count * 100) if batch_result.success_count > 0 else 0
            lines.append(f"| {level.value} | {count} | {percentage:.1f}% |\n")
        
        lines.append("\n")
        
        # 전체 파일 복잡도 목록 (복잡도 높은 순으로 정렬)
        lines.append("## 전체 파일 복잡도 목록\n")
        lines.append("| 순위 | 파일명 | 복잡도 점수 | 복잡도 레벨 |\n")
        lines.append("|------|--------|-------------|-------------|\n")
        
        # 모든 파일을 복잡도 점수 기준으로 정렬
        all_files = []
        for file_name, result in batch_result.results.items():
            if isinstance(result, dict):
                # 배치 PL/SQL 결과 - 평균 점수 계산
                results_list = result.get('results', [])
                if results_list:
                    total_score = sum(
                        obj_result.get('analysis').normalized_score 
                        for obj_result in results_list 
                        if obj_result.get('analysis')
                    )
                    avg_score = total_score / len(results_list)
                    # 첫 번째 객체의 복잡도 레벨 사용 (대표값)
                    level = results_list[0].get('analysis').complexity_level.value if results_list else 'unknown'
                    all_files.append((file_name, avg_score, level))
            else:
                # 일반 SQL/PL/SQL 결과
                all_files.append((file_name, result.normalized_score, result.complexity_level.value))
        
        # 점수 기준 내림차순 정렬
        all_files.sort(key=lambda x: x[1], reverse=True)
        
        for idx, (file_name, score, level) in enumerate(all_files, 1):
            lines.append(f"| {idx} | `{file_name}` | {score:.2f} | {level} |\n")
        
        lines.append("\n")
        
        # 실패한 파일 목록
        if batch_result.failed_files:
            lines.append("## 분석 실패 파일\n")
            lines.append("| 파일명 | 에러 메시지 |\n")
            lines.append("|--------|-------------|\n")
            
            for file_name, error in batch_result.failed_files.items():
                lines.append(f"| `{file_name}` | {error} |\n")
            
            lines.append("\n")
        
        # 개별 파일 상세 결과
        if include_details and batch_result.results:
            lines.append("## 개별 파일 상세 결과\n")
            lines.append("\n")
            
            for file_name, result in batch_result.results.items():
                # 배치 PL/SQL 결과(dict)는 상세 결과에서 제외
                if isinstance(result, dict):
                    logger.info(f"배치 PL/SQL 파일은 상세 결과에서 제외: {file_name}")
                    continue
                
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
        
        각 분석된 파일에 대해 별도의 Markdown과 JSON 리포트를 생성합니다.
        원본 소스 폴더 구조를 reports 폴더 밑에 유지하며, 파일 타입별로 구분합니다.
        
        배치 PL/SQL 파일(.out)도 plsql 폴더에 저장됩니다.
        
        Args:
            batch_result: 배치 분석 결과
            
        Returns:
            List[str]: 생성된 개별 리포트 파일 경로 리스트
        """
        from src.formatters.result_formatter import ResultFormatter
        from ..file_detector import detect_file_type
        
        # 타겟 데이터베이스 이름 (postgresql -> PGSQL, mysql -> MySQL)
        target_folder = "PGSQL" if batch_result.target_database == TargetDatabase.POSTGRESQL else "MySQL"
        
        # 생성된 파일 경로 리스트
        created_files = []
        
        # 각 파일별로 리포트 생성
        for file_path, result in batch_result.results.items():
            # 배치 PL/SQL 결과(dict)는 별도로 처리
            if isinstance(result, dict):
                logger.info(f"배치 PL/SQL 파일 리포트 생성: {file_path}")
                
                # plsql 폴더에 저장
                report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / "plsql" / target_folder
                report_folder.mkdir(parents=True, exist_ok=True)
                
                # 파일명 추출
                file_name = Path(file_path).stem
                
                # Markdown 리포트 생성
                try:
                    markdown_str = ResultFormatter.batch_to_markdown(result, batch_result.target_database.value)
                    md_report_path = report_folder / f"{file_name}.md"
                    
                    with open(md_report_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_str)
                    
                    created_files.append(str(md_report_path))
                    logger.info(f"배치 PL/SQL Markdown 리포트 저장 완료: {md_report_path}")
                except Exception as e:
                    logger.error(f"배치 PL/SQL Markdown 리포트 생성 실패: {file_path} - {e}")
                
                # JSON 리포트 생성
                try:
                    json_str = ResultFormatter.batch_to_json(result)
                    json_report_path = report_folder / f"{file_name}.json"
                    
                    with open(json_report_path, 'w', encoding='utf-8') as f:
                        f.write(json_str)
                    
                    created_files.append(str(json_report_path))
                    logger.info(f"배치 PL/SQL JSON 리포트 저장 완료: {json_report_path}")
                except Exception as e:
                    logger.error(f"배치 PL/SQL JSON 리포트 생성 실패: {file_path} - {e}")
                
                continue
            
            # 파일 타입 감지
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_type = detect_file_type(content)
            except Exception as e:
                logger.warning(f"파일 타입 감지 실패: {file_path}, 기본값(sql) 사용")
                file_type = 'sql'
            
            # 파일 타입 폴더명 (sql 또는 plsql)
            type_folder = "plsql" if file_type in ['plsql', 'batch_plsql'] else "sql"
            
            # 폴더 경로 생성: reports/{분석대상폴더명}/{타입}/{타겟}/
            report_folder = self.analyzer.output_dir / (self.source_folder_name or "batch") / type_folder / target_folder
            report_folder.mkdir(parents=True, exist_ok=True)
            
            # 파일명 추출 (경로에서 파일명만)
            file_name = Path(file_path).stem
            
            # Markdown 리포트 생성
            try:
                markdown_str = ResultFormatter.to_markdown(result)
                md_report_path = report_folder / f"{file_name}.md"
                
                with open(md_report_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_str)
                
                created_files.append(str(md_report_path))
            except Exception as e:
                logger.error(f"Markdown 리포트 생성 실패: {file_path} - {e}")
                continue
            
            # JSON 리포트 생성
            try:
                json_str = ResultFormatter.to_json(result)
                json_report_path = report_folder / f"{file_name}.json"
                
                with open(json_report_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                
                created_files.append(str(json_report_path))
            except Exception as e:
                logger.error(f"JSON 리포트 생성 실패: {file_path} - {e}")
                continue
        
        logger.info(f"{len(created_files)}개의 개별 리포트 생성 완료")
        
        return created_files
