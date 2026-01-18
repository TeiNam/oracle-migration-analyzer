"""
PL/SQL Feature Analyzer

PL/SQL 고급 기능 및 의존성을 분석하는 기능을 제공합니다.
"""

import re
from ...oracle_complexity_analyzer import PLSQLObjectType
from .base_parser import PLSQLParserBase


class PLSQLFeatureAnalyzer(PLSQLParserBase):
    """PL/SQL 고급 기능 및 의존성 분석
    
    패키지 호출, DB Link, 고급 기능, 외부 의존성, 트랜잭션 제어 등을 분석합니다.
    """
    
    def count_package_calls(self) -> int:
        """패키지 호출 개수 계산
        
        Requirements 9.1을 구현합니다.
        패키지명.프로시저명 또는 패키지명.함수명 형태의 호출을 계산합니다.
        
        Returns:
            패키지 호출 개수
        """
        # 패키지 호출 패턴: package_name.procedure_or_function
        # 일반적인 패턴: 식별자.식별자( 또는 식별자.식별자;
        # DBMS_, UTL_ 등의 시스템 패키지도 포함
        package_call_pattern = r'\b[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\s*[\(;]'
        
        matches = re.findall(package_call_pattern, self.upper_code)
        
        # 중복 제거를 위해 set 사용 후 개수 반환
        # 하지만 요구사항은 호출 개수이므로 중복 포함
        return len(matches)
    
    def count_dblinks(self) -> int:
        """DB Link 사용 개수 계산
        
        Requirements 9.2를 구현합니다.
        @dblink_name 형태의 DB Link 사용을 계산합니다.
        
        Returns:
            DB Link 사용 개수
        """
        # DB Link 패턴: @dblink_name
        # 테이블명@dblink 또는 뷰명@dblink 형태
        dblink_pattern = r'@[A-Z_][A-Z0-9_\.]*'
        
        matches = re.findall(dblink_pattern, self.upper_code)
        
        return len(matches)
    
    def detect_advanced_features(self) -> list:
        """고급 기능 감지
        
        Requirements 9.5를 구현합니다.
        PIPELINED, REF CURSOR, AUTONOMOUS_TRANSACTION, PRAGMA, OBJECT TYPE 등을 감지합니다.
        
        Returns:
            감지된 고급 기능 목록
        """
        advanced_features = []
        
        # 고급 기능 패턴 정의
        feature_patterns = {
            'PIPELINED': r'\bPIPELINED\b',
            'REF CURSOR': r'\bREF\s+CURSOR\b',
            'AUTONOMOUS_TRANSACTION': r'\bAUTONOMOUS_TRANSACTION\b',
            'PRAGMA': r'\bPRAGMA\b',
            'OBJECT TYPE': r'\bAS\s+OBJECT\b',  # CREATE TYPE ... AS OBJECT
            'VARRAY': r'\bVARRAY\b',
            'NESTED TABLE': r'\bTABLE\s+OF\b',  # TYPE ... IS TABLE OF
        }
        
        # 각 패턴을 검사하여 감지된 기능 추가
        for feature_name, pattern in feature_patterns.items():
            if re.search(pattern, self.upper_code):
                advanced_features.append(feature_name)
        
        return advanced_features
    
    def detect_external_dependencies(self) -> list:
        """외부 의존성 감지
        
        Requirements 10.6을 구현합니다.
        UTL_FILE, UTL_HTTP, UTL_MAIL, DBMS_SCHEDULER 등의 외부 패키지 사용을 감지합니다.
        
        Returns:
            감지된 외부 의존성 목록
        """
        external_deps = []
        
        # 외부 의존성 패키지 목록
        external_packages = [
            'UTL_FILE',
            'UTL_HTTP',
            'UTL_MAIL',
            'UTL_SMTP',
            'DBMS_SCHEDULER',
            'DBMS_JOB',
            'DBMS_LOB',
            'DBMS_OUTPUT',
            'DBMS_CRYPTO',
            'DBMS_SQL',
        ]
        
        # 각 패키지 사용 여부 확인
        for package in external_packages:
            # 패키지명.메서드명 형태로 사용되는지 확인
            pattern = rf'\b{package}\.'
            if re.search(pattern, self.upper_code):
                external_deps.append(package)
        
        return external_deps
    
    def has_transaction_control(self) -> dict:
        """트랜잭션 제어 감지
        
        Requirements 10.1을 구현합니다.
        SAVEPOINT, ROLLBACK, COMMIT 등의 트랜잭션 제어 문을 감지합니다.
        
        Returns:
            트랜잭션 제어 요소별 사용 여부를 담은 딕셔너리
            {
                'savepoint': bool,
                'rollback': bool,
                'rollback_to_savepoint': bool,
                'commit': bool
            }
        """
        transaction_control = {
            'savepoint': False,
            'rollback': False,
            'rollback_to_savepoint': False,
            'commit': False
        }
        
        # SAVEPOINT 감지
        if re.search(r'\bSAVEPOINT\s+\w+', self.upper_code):
            transaction_control['savepoint'] = True
        
        # ROLLBACK TO SAVEPOINT 감지 (일반 ROLLBACK보다 먼저 확인)
        if re.search(r'\bROLLBACK\s+TO\s+(?:SAVEPOINT\s+)?\w+', self.upper_code):
            transaction_control['rollback_to_savepoint'] = True
        
        # ROLLBACK 감지
        if re.search(r'\bROLLBACK\b', self.upper_code):
            transaction_control['rollback'] = True
        
        # COMMIT 감지
        if re.search(r'\bCOMMIT\b', self.upper_code):
            transaction_control['commit'] = True
        
        return transaction_control
    
    def has_package_variables(self) -> bool:
        """패키지 변수 사용 여부 감지
        
        Requirements 10.5를 구현합니다.
        패키지 레벨에서 선언된 변수(전역 변수)의 사용을 감지합니다.
        
        Returns:
            패키지 변수가 사용되면 True, 아니면 False
        """
        # 패키지 변수는 일반적으로 패키지 선언부(PACKAGE SPEC)나
        # 패키지 본문의 BEGIN 이전에 선언됩니다.
        
        # Package 타입인지 먼저 확인
        # detect_object_type 메서드를 사용하기 위해 임포트 필요
        # 순환 참조를 피하기 위해 여기서 직접 확인
        if not self._is_package_code():
            return False
        
        # 패키지 선언부에서 변수 선언 패턴 찾기
        # 패턴: 변수명 데이터타입 [:= 초기값];
        # CREATE PACKAGE 이후, IS/AS와 END 사이에 선언
        
        # PACKAGE ... IS/AS 와 첫 번째 PROCEDURE/FUNCTION 또는 BEGIN 사이의 영역 추출
        package_header_pattern = r'PACKAGE\s+(?:BODY\s+)?[\w\.]+\s+(?:IS|AS)\s+(.*?)(?:PROCEDURE|FUNCTION|BEGIN|END)'
        
        match = re.search(package_header_pattern, self.upper_code, re.DOTALL)
        if match:
            header_section = match.group(1)
            
            # 변수 선언 패턴: 식별자 데이터타입
            # 일반적인 데이터 타입: VARCHAR2, NUMBER, DATE, BOOLEAN, INTEGER 등
            variable_pattern = r'\b[A-Z_][A-Z0-9_]*\s+(?:VARCHAR2|NUMBER|DATE|BOOLEAN|INTEGER|TIMESTAMP|CLOB|BLOB|PLS_INTEGER|BINARY_INTEGER)'
            
            if re.search(variable_pattern, header_section):
                return True
        
        return False
    
    def _is_package_code(self) -> bool:
        """패키지 코드 여부 확인 (내부 헬퍼)"""
        package_patterns = [
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+BODY\b',
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+(?!BODY)\w+',
        ]
        
        for pattern in package_patterns:
            if re.search(pattern, self.upper_code):
                return True
        
        return False
    
    def detect_context_dependencies(self) -> list:
        """컨텍스트 의존성 감지
        
        Requirements 10.4를 구현합니다.
        SYS_CONTEXT, 세션 변수, 글로벌 임시 테이블 등의 컨텍스트 의존성을 감지합니다.
        
        Returns:
            감지된 컨텍스트 의존성 목록
        """
        context_deps = []
        
        # SYS_CONTEXT 함수 사용 감지
        if re.search(r'\bSYS_CONTEXT\s*\(', self.upper_code):
            context_deps.append('SYS_CONTEXT')
        
        # 세션 변수 사용 감지 (USERENV 네임스페이스)
        if re.search(r'\bUSERENV\s*\(', self.upper_code):
            context_deps.append('USERENV')
        
        # 글로벌 임시 테이블 생성 감지
        if re.search(r'\bCREATE\s+GLOBAL\s+TEMPORARY\s+TABLE\b', self.upper_code):
            context_deps.append('GLOBAL_TEMPORARY_TABLE')
        
        # 세션 변수 설정/조회 (DBMS_SESSION)
        if re.search(r'\bDBMS_SESSION\b', self.upper_code):
            context_deps.append('DBMS_SESSION')
        
        # 애플리케이션 컨텍스트 (DBMS_APPLICATION_INFO)
        if re.search(r'\bDBMS_APPLICATION_INFO\b', self.upper_code):
            context_deps.append('DBMS_APPLICATION_INFO')
        
        return context_deps
