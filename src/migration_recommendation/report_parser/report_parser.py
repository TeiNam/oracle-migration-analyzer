"""
통합 리포트 파서

MD 및 JSON 형식의 DBCSI 및 SQL 복잡도 분석 리포트를 파싱합니다.
MD 파일을 우선 파싱하고, 없으면 JSON을 사용합니다.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple

from ...oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ...oracle_complexity_analyzer.enums import TargetDatabase
from .markdown_parser import MarkdownReportParser
from .complexity_parser import ComplexityReportParser
from .json_parser import JsonReportParser

logger = logging.getLogger(__name__)


class ReportParser:
    """리포트 파일 파서
    
    MD 및 JSON 형식의 DBCSI 및 SQL 복잡도 분석 리포트를 파싱합니다.
    MD 파일을 우선 파싱하고, 없으면 JSON을 사용합니다.
    """
    
    def __init__(self) -> None:
        self.md_parser = MarkdownReportParser()
        self.complexity_parser = ComplexityReportParser()
        self.json_parser = JsonReportParser()
    
    def parse_dbcsi_metrics(self, report_path: str) -> Optional[Dict[str, Any]]:
        """
        DBCSI 리포트에서 필요한 메트릭만 추출합니다.
        MD 파일을 우선 파싱하고, JSON은 폴백으로 사용합니다.
        
        Args:
            report_path: DBCSI 리포트 파일 경로 (.md 또는 .json)
            
        Returns:
            메트릭 딕셔너리 또는 None
        """
        if report_path.endswith('.md'):
            return self.md_parser.parse_dbcsi_markdown(report_path)
        
        return self.json_parser.parse_dbcsi_json(report_path)
    
    def parse_sql_complexity_reports(
        self,
        report_paths: List[str],
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """
        SQL 복잡도 분석 리포트 파일들을 파싱합니다.
        MD 파일을 우선 파싱하고, JSON은 폴백으로 사용합니다.
        
        Args:
            report_paths: SQL 복잡도 리포트 파일 경로 리스트
            target_db: 타겟 데이터베이스 (postgresql 또는 mysql)
            
        Returns:
            (sql_results, plsql_results) 튜플
        """
        sql_results: List[SQLAnalysisResult] = []
        plsql_results: List[PLSQLAnalysisResult] = []
        
        target_db_enum = (
            TargetDatabase.POSTGRESQL 
            if target_db == "postgresql" 
            else TargetDatabase.MYSQL
        )
        
        for report_path in report_paths:
            try:
                if report_path.endswith('.md'):
                    sql, plsql = self.complexity_parser.parse_plsql_complexity_markdown(
                        report_path, target_db
                    )
                    sql_results.extend(sql)
                    plsql_results.extend(plsql)
                    continue
                
                if not report_path.endswith('.json'):
                    continue
                
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'results' in data:
                    logger.info(f"배치 JSON 리포트 파싱: {report_path}")
                    sql, plsql = self.json_parser.parse_batch_report(data, target_db_enum)
                    sql_results.extend(sql)
                    plsql_results.extend(plsql)
                            
            except Exception as e:
                logger.warning(f"리포트 파싱 실패 ({report_path}): {e}", exc_info=True)
                continue
        
        logger.info(f"복잡도 리포트 파싱 완료: SQL {len(sql_results)}개, PL/SQL {len(plsql_results)}개")
        return sql_results, plsql_results
