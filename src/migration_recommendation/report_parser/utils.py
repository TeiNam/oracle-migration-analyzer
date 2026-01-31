"""
리포트 파서 유틸리티 함수

공통 유틸리티 함수와 리포트 검색 함수를 제공합니다.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_number_with_comma(value_str: str) -> Optional[float]:
    """쉼표가 포함된 숫자 문자열을 float로 변환
    
    예: "2,667.0" -> 2667.0, "1,234,567" -> 1234567.0
    
    Args:
        value_str: 숫자 문자열 (쉼표 포함 가능)
        
    Returns:
        float 값 또는 None
    """
    if not value_str:
        return None
    
    match = re.search(r'([\d,]+\.?\d*)', value_str)
    if match:
        num_str = match.group(1).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return None
    return None


def find_reports_in_directory(reports_dir: str) -> Tuple[List[str], List[str]]:
    """
    리포트 디렉토리에서 DBCSI 리포트와 SQL 복잡도 리포트를 찾습니다.
    MD 파일을 우선하고, 없으면 JSON 파일을 사용합니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        (dbcsi_reports, sql_complexity_reports) 튜플
    """
    reports_path = Path(reports_dir)
    
    dbcsi_reports: List[str] = []
    sql_complexity_reports: List[str] = []
    
    md_files = list(reports_path.glob("**/*.md"))
    json_files = list(reports_path.glob("**/*.json"))
    
    # DBCSI MD 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            if 'comparison' not in filename and 'migration' not in filename:
                dbcsi_reports.append(str(md_file))
    
    # DBCSI MD가 없으면 JSON 사용
    if not dbcsi_reports:
        for json_file in json_files:
            filename = json_file.name.lower()
            if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
                if 'comparison' not in filename and 'migration' not in filename:
                    dbcsi_reports.append(str(json_file))
    
    # SQL 복잡도 MD 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if 'plsql' in filename and 'complexity' in filename:
            sql_complexity_reports.append(str(md_file))
        elif 'sql_complexity' in filename:
            sql_complexity_reports.append(str(md_file))
    
    # SQL 복잡도 MD가 없으면 JSON 사용
    if not sql_complexity_reports:
        for json_file in json_files:
            filename = json_file.name.lower()
            if 'plsql_f_' in filename or 'sql_complexity' in filename:
                sql_complexity_reports.append(str(json_file))
            elif json_file.parent.name in ['PGSQL', 'MySQL']:
                if 'batch' not in filename and 'migration' not in filename:
                    sql_complexity_reports.append(str(json_file))
    
    logger.info(f"발견된 DBCSI 리포트: {len(dbcsi_reports)}개")
    logger.info(f"발견된 SQL 복잡도 리포트: {len(sql_complexity_reports)}개")
    
    return dbcsi_reports, sql_complexity_reports


def find_reports_by_target(reports_dir: str) -> Dict[str, List[str]]:
    """
    리포트 디렉토리에서 타겟 DB별로 SQL 복잡도 리포트를 찾습니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        Dict[str, List[str]]: 타겟 DB별 리포트 경로 딕셔너리
    """
    reports_path = Path(reports_dir)
    
    result: Dict[str, List[str]] = {
        'postgresql': [],
        'mysql': [],
        'dbcsi': []
    }
    
    md_files = list(reports_path.glob("**/*.md"))
    json_files = list(reports_path.glob("**/*.json"))
    
    # DBCSI 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            if 'comparison' not in filename and 'migration' not in filename:
                result['dbcsi'].append(str(md_file))
    
    if not result['dbcsi']:
        for json_file in json_files:
            filename = json_file.name.lower()
            if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
                if 'comparison' not in filename and 'migration' not in filename:
                    result['dbcsi'].append(str(json_file))
    
    # PostgreSQL 복잡도 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        filepath = str(md_file).lower()
        
        if ('postgresql' in filename or 'pgsql' in filepath or 
            '_postgresql' in filename or '/pgsql/' in filepath):
            if 'plsql' in filename or 'sql_complexity' in filename:
                result['postgresql'].append(str(md_file))
    
    # MySQL 복잡도 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        filepath = str(md_file).lower()
        
        if ('mysql' in filename or '/mysql/' in filepath or '_mysql' in filename):
            if 'plsql' in filename or 'sql_complexity' in filename:
                result['mysql'].append(str(md_file))
    
    # 타겟 구분 없는 일반 리포트 (PostgreSQL로 분류)
    for md_file in md_files:
        filename = md_file.name.lower()
        
        if str(md_file) in result['postgresql'] or str(md_file) in result['mysql']:
            continue
        
        if ('plsql' in filename and 'complexity' in filename) or 'sql_complexity' in filename:
            result['postgresql'].append(str(md_file))
    
    logger.info(f"발견된 DBCSI 리포트: {len(result['dbcsi'])}개")
    logger.info(f"발견된 PostgreSQL 복잡도 리포트: {len(result['postgresql'])}개")
    logger.info(f"발견된 MySQL 복잡도 리포트: {len(result['mysql'])}개")
    
    return result
