"""
PL/SQL Parser Base

PL/SQL 파서의 기본 클래스와 코드 정규화 기능을 제공합니다.
"""

import re


class PLSQLParserBase:
    """PL/SQL 파서 기본 클래스
    
    코드 초기화 및 정규화 기능을 제공합니다.
    """
    
    def __init__(self, code: str):
        """PLSQLParserBase 초기화
        
        Args:
            code: 분석할 PL/SQL 코드
        """
        self.code = code.strip()
        self.upper_code = code.upper()
        self._normalized_code = self._normalize_code()
    
    def _normalize_code(self) -> str:
        """코드 정규화 (공백, 줄바꿈 처리)
        
        여러 공백을 하나로 통합하고, 주석을 제거합니다.
        
        Returns:
            정규화된 코드 문자열
        """
        # 한 줄 주석 제거 (-- 로 시작하는 줄)
        code = re.sub(r'--[^\n]*', '', self.upper_code)
        
        # 여러 줄 주석 제거 (/* ... */)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # 여러 공백을 하나로 통합
        code = re.sub(r'\s+', ' ', code)
        
        return code.strip()
