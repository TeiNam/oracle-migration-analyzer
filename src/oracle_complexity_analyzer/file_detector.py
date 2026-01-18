"""
파일 타입 감지 모듈

SQL, PL/SQL, 배치 PL/SQL 파일을 감지하는 기능을 제공합니다.
"""

import logging
import re

# 로거 초기화
logger = logging.getLogger(__name__)


def is_plsql(content: str) -> bool:
    """PL/SQL 여부 판단
    
    코드 내용을 분석하여 PL/SQL 오브젝트인지 판단합니다.
    
    Args:
        content: 분석할 코드 내용
        
    Returns:
        bool: PL/SQL이면 True, SQL이면 False
    """
    logger.debug("PL/SQL 여부 판단 시작")
    
    # PL/SQL 키워드 목록
    plsql_keywords = [
        'CREATE OR REPLACE PACKAGE',
        'CREATE PACKAGE',
        'CREATE OR REPLACE PROCEDURE',
        'CREATE PROCEDURE',
        'CREATE OR REPLACE FUNCTION',
        'CREATE FUNCTION',
        'CREATE OR REPLACE TRIGGER',
        'CREATE TRIGGER',
        'CREATE MATERIALIZED VIEW',
        'CREATE OR REPLACE VIEW',
        'CREATE VIEW',
        'DECLARE',
        'BEGIN',
        'EXCEPTION',
    ]
    
    upper_content = content.upper()
    
    # PL/SQL 키워드가 있으면 PL/SQL로 판단
    return any(kw in upper_content for kw in plsql_keywords)


def is_batch_plsql(content: str) -> bool:
    """배치 PL/SQL 파일 여부 판단
    
    여러 PL/SQL 객체가 포함된 배치 파일인지 판단합니다.
    
    Args:
        content: 분석할 파일 내용
        
    Returns:
        bool: 배치 PL/SQL 파일이면 True
    """
    logger.debug("배치 PL/SQL 여부 판단 시작")
    
    # 배치 파일 헤더 패턴 확인
    header_pattern = r'-- Owner:\s*\w+\s*\n-- Type:\s*\w+\s*\n-- Name:\s*\w+'
    matches = re.findall(header_pattern, content, re.MULTILINE)
    
    # 2개 이상의 객체 헤더가 있으면 배치 파일로 판단
    return len(matches) >= 2


def detect_file_type(content: str) -> str:
    """파일 타입 자동 감지
    
    Args:
        content: 파일 내용
        
    Returns:
        str: 'batch_plsql', 'plsql', 또는 'sql'
    """
    if is_batch_plsql(content):
        return 'batch_plsql'
    elif is_plsql(content):
        return 'plsql'
    else:
        return 'sql'
