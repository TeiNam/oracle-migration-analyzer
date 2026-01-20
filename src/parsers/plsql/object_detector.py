"""
PL/SQL Object Type Detector

PL/SQL 오브젝트 타입을 감지하는 기능을 제공합니다.
"""

import re
from ...oracle_complexity_analyzer import PLSQLObjectType
from .base_parser import PLSQLParserBase


class PLSQLObjectDetector(PLSQLParserBase):
    """PL/SQL 오브젝트 타입 감지
    
    Requirements 8.1을 구현합니다:
    - Package (Body/Spec 구분)
    - Procedure
    - Function
    - Trigger
    - View
    - Materialized View
    """
    
    def detect_object_type(self) -> PLSQLObjectType:
        """오브젝트 타입 감지
        
        Requirements 8.1을 구현합니다.
        PL/SQL 코드를 분석하여 오브젝트 타입을 결정합니다.
        
        Returns:
            감지된 PL/SQL 오브젝트 타입
        
        Raises:
            ValueError: 오브젝트 타입을 감지할 수 없는 경우
        """
        normalized = self._normalized_code
        
        # Materialized View 확인 (View보다 먼저 확인해야 함)
        if self._is_materialized_view(normalized):
            return PLSQLObjectType.MATERIALIZED_VIEW
        
        # View 확인
        if self._is_view(normalized):
            return PLSQLObjectType.VIEW
        
        # Package 확인 (Body와 Spec 모두 포함)
        if self._is_package(normalized):
            return PLSQLObjectType.PACKAGE
        
        # Trigger 확인
        if self._is_trigger(normalized):
            return PLSQLObjectType.TRIGGER
        
        # Function 확인 (Procedure보다 먼저 확인)
        if self._is_function(normalized):
            return PLSQLObjectType.FUNCTION
        
        # Procedure 확인
        if self._is_procedure(normalized):
            return PLSQLObjectType.PROCEDURE
        
        # TYPE 확인 - Procedure로 분류
        if self._is_type(normalized):
            return PLSQLObjectType.PROCEDURE
        
        # 감지 실패
        raise ValueError("PL/SQL 오브젝트 타입을 감지할 수 없습니다.")
    
    def _is_package(self, code: str) -> bool:
        """Package 여부 확인 (Body 또는 Spec)
        
        Args:
            code: 정규화된 코드
            
        Returns:
            Package인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] PACKAGE [BODY] 패턴
        # 다양한 케이스 지원:
        # 1. PACKAGE BODY만 있는 경우
        # 2. PACKAGE (Spec)만 있는 경우  
        # 3. 둘 다 있는 경우
        # 4. PACKAGE 키워드만 있는 경우
        package_patterns = [
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+BODY\b',
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+(?!BODY\b)',
        ]
        
        for pattern in package_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        
        return False
    
    def _is_procedure(self, code: str) -> bool:
        """Procedure 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            Procedure인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] PROCEDURE 패턴
        pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PROCEDURE\b'
        return bool(re.search(pattern, code))
    
    def _is_function(self, code: str) -> bool:
        """Function 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            Function인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] FUNCTION 패턴
        pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?FUNCTION\b'
        return bool(re.search(pattern, code))
    
    def _is_trigger(self, code: str) -> bool:
        """Trigger 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            Trigger인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] TRIGGER 패턴
        pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?TRIGGER\b'
        return bool(re.search(pattern, code))
    
    def _is_view(self, code: str) -> bool:
        """View 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            View인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] VIEW 패턴 (MATERIALIZED 제외)
        pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?(?!MATERIALIZED\s+)VIEW\b'
        return bool(re.search(pattern, code))
    
    def _is_materialized_view(self, code: str) -> bool:
        """Materialized View 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            Materialized View인 경우 True
        """
        # CREATE MATERIALIZED VIEW 패턴
        pattern = r'\bCREATE\s+MATERIALIZED\s+VIEW\b'
        return bool(re.search(pattern, code))
    
    def _is_type(self, code: str) -> bool:
        """TYPE 여부 확인
        
        Args:
            code: 정규화된 코드
            
        Returns:
            TYPE인 경우 True
        """
        # CREATE OR REPLACE [EDITIONABLE] TYPE 패턴
        pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?TYPE\b'
        return bool(re.search(pattern, code))
