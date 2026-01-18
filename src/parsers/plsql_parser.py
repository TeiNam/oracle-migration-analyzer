"""
PL/SQL Parser

PL/SQL 코드를 파싱하여 구문 요소를 추출하는 모듈입니다.
Requirements 8.1을 구현합니다.
"""

import re
from typing import Optional
from ..oracle_complexity_analyzer import PLSQLObjectType


class PLSQLParser:
    """PL/SQL 코드 파싱 및 구문 요소 추출
    
    Requirements 8.1을 구현합니다:
    - Package (Body/Spec 구분)
    - Procedure
    - Function
    - Trigger
    - View
    - Materialized View
    """
    
    def __init__(self, code: str):
        """PLSQLParser 초기화
        
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
    
    def detect_object_type(self) -> PLSQLObjectType:
        """오브젝트 타입 감지
        
        Requirements 8.1을 구현합니다.
        PL/SQL 코드를 분석하여 오브젝트 타입을 결정합니다:
        - Package (Body/Spec 구분)
        - Procedure
        - Function
        - Trigger
        - View
        - Materialized View
        
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
        package_patterns = [
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+BODY\b',
            r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:EDITIONABLE\s+)?PACKAGE\s+(?!BODY)\w+',
        ]
        
        for pattern in package_patterns:
            if re.search(pattern, code):
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
    
    def count_lines(self) -> int:
        """코드 라인 수 계산
        
        Requirements 8.2를 구현합니다.
        빈 줄과 주석만 있는 줄을 제외한 실제 코드 라인 수를 계산합니다.
        
        Returns:
            코드 라인 수
        """
        lines = self.code.split('\n')
        code_lines = 0
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 빈 줄 제외
            if not stripped:
                continue
            
            # 여러 줄 주석 처리
            if '/*' in stripped:
                in_multiline_comment = True
            
            if in_multiline_comment:
                if '*/' in stripped:
                    in_multiline_comment = False
                continue
            
            # 한 줄 주석 제외
            if stripped.startswith('--'):
                continue
            
            # 실제 코드 라인
            code_lines += 1
        
        return code_lines
    
    def count_cursors(self) -> int:
        """커서 개수 계산
        
        Requirements 8.3을 구현합니다.
        명시적 커서 선언(CURSOR)과 암시적 커서(FOR ... IN)를 모두 계산합니다.
        
        Returns:
            커서 개수
        """
        cursor_count = 0
        
        # 명시적 커서 선언: CURSOR cursor_name IS
        explicit_cursor_pattern = r'\bCURSOR\s+\w+\s+IS\b'
        cursor_count += len(re.findall(explicit_cursor_pattern, self.upper_code))
        
        # 암시적 커서: FOR record IN (SELECT ...)
        implicit_cursor_pattern = r'\bFOR\s+\w+\s+IN\s*\('
        cursor_count += len(re.findall(implicit_cursor_pattern, self.upper_code))
        
        # FOR record IN cursor_name
        cursor_loop_pattern = r'\bFOR\s+\w+\s+IN\s+\w+\b'
        # 이미 계산된 암시적 커서와 중복되지 않도록 조심스럽게 계산
        # 괄호가 없는 경우만 추가
        for match in re.finditer(cursor_loop_pattern, self.upper_code):
            # 바로 뒤에 괄호가 없는지 확인
            end_pos = match.end()
            if end_pos < len(self.upper_code):
                next_char = self.upper_code[end_pos:end_pos+10].strip()
                if not next_char.startswith('('):
                    cursor_count += 1
        
        return cursor_count
    
    def count_exception_blocks(self) -> int:
        """예외 처리 블록 개수 계산
        
        Requirements 8.4를 구현합니다.
        EXCEPTION 키워드로 시작하는 예외 처리 블록의 개수를 계산합니다.
        
        Returns:
            예외 처리 블록 개수
        """
        # EXCEPTION 키워드 개수 계산
        # BEGIN ... EXCEPTION ... END 구조에서 EXCEPTION 부분
        exception_pattern = r'\bEXCEPTION\b'
        exception_count = len(re.findall(exception_pattern, self.upper_code))
        
        return exception_count
    
    def calculate_nesting_depth(self) -> int:
        """중첩 깊이 계산
        
        Requirements 8.5를 구현합니다.
        IF, LOOP, BEGIN 등의 블록 중첩 깊이를 계산합니다.
        
        Returns:
            최대 중첩 깊이
        """
        # 중첩을 증가시키는 키워드
        opening_keywords = [
            r'\bBEGIN\b',
            r'\bIF\b',
            r'\bLOOP\b',
            r'\bWHILE\b',
            r'\bFOR\b',
            r'\bCASE\b',
        ]
        
        # 중첩을 감소시키는 키워드
        closing_keywords = [
            r'\bEND\b',
            r'\bEND\s+IF\b',
            r'\bEND\s+LOOP\b',
            r'\bEND\s+CASE\b',
        ]
        
        # 모든 키워드의 위치를 찾아서 정렬
        events = []
        
        for pattern in opening_keywords:
            for match in re.finditer(pattern, self.upper_code):
                events.append((match.start(), 'open'))
        
        for pattern in closing_keywords:
            for match in re.finditer(pattern, self.upper_code):
                events.append((match.start(), 'close'))
        
        # 위치 순으로 정렬
        events.sort(key=lambda x: x[0])
        
        # 중첩 깊이 계산
        current_depth = 0
        max_depth = 0
        
        for _, event_type in events:
            if event_type == 'open':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif event_type == 'close':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def count_bulk_operations(self) -> int:
        """BULK 연산 개수 계산
        
        Requirements 9.4를 구현합니다.
        BULK COLLECT와 FORALL 연산의 개수를 계산합니다.
        
        Returns:
            BULK 연산 개수
        """
        bulk_count = 0
        
        # BULK COLLECT INTO 패턴
        bulk_collect_pattern = r'\bBULK\s+COLLECT\s+INTO\b'
        bulk_count += len(re.findall(bulk_collect_pattern, self.upper_code))
        
        # FORALL 패턴
        forall_pattern = r'\bFORALL\b'
        bulk_count += len(re.findall(forall_pattern, self.upper_code))
        
        return bulk_count
    
    def count_dynamic_sql(self) -> int:
        """동적 SQL 개수 계산
        
        Requirements 9.3을 구현합니다.
        EXECUTE IMMEDIATE 문의 개수를 계산합니다.
        
        Returns:
            동적 SQL 개수
        """
        # EXECUTE IMMEDIATE 패턴
        execute_immediate_pattern = r'\bEXECUTE\s+IMMEDIATE\b'
        dynamic_sql_count = len(re.findall(execute_immediate_pattern, self.upper_code))
        
        return dynamic_sql_count
    
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
        try:
            obj_type = self.detect_object_type()
            if obj_type != PLSQLObjectType.PACKAGE:
                return False
        except ValueError:
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
    
    def count_procedures_in_package(self) -> int:
        """패키지 내 프로시저 개수 계산
        
        Requirements 8.1을 구현합니다.
        패키지 내에 정의된 프로시저의 개수를 계산합니다.
        
        Returns:
            프로시저 개수 (패키지가 아닌 경우 0)
        """
        try:
            obj_type = self.detect_object_type()
            if obj_type != PLSQLObjectType.PACKAGE:
                return 0
        except ValueError:
            return 0
        
        # PROCEDURE 키워드 개수 계산
        # CREATE PROCEDURE는 제외하고 패키지 내부의 PROCEDURE만 계산
        procedure_pattern = r'\bPROCEDURE\s+[A-Z_][A-Z0-9_]*\s*[\(;]'
        
        matches = re.findall(procedure_pattern, self.upper_code)
        
        return len(matches)
    
    def count_functions_in_package(self) -> int:
        """패키지 내 함수 개수 계산
        
        Requirements 8.1을 구현합니다.
        패키지 내에 정의된 함수의 개수를 계산합니다.
        
        Returns:
            함수 개수 (패키지가 아닌 경우 0)
        """
        try:
            obj_type = self.detect_object_type()
            if obj_type != PLSQLObjectType.PACKAGE:
                return 0
        except ValueError:
            return 0
        
        # FUNCTION 키워드 개수 계산
        # CREATE FUNCTION은 제외하고 패키지 내부의 FUNCTION만 계산
        function_pattern = r'\bFUNCTION\s+[A-Z_][A-Z0-9_]*\s*[\(]'
        
        matches = re.findall(function_pattern, self.upper_code)
        
        return len(matches)
    
    def analyze_parameters(self) -> dict:
        """파라미터 분석
        
        Requirements 8.1을 구현합니다.
        프로시저/함수의 파라미터를 분석하여 IN/OUT/IN OUT 개수를 계산합니다.
        
        Returns:
            파라미터 분석 결과
            {
                'total': int,      # 전체 파라미터 개수
                'in': int,         # IN 파라미터 개수
                'out': int,        # OUT 파라미터 개수
                'in_out': int      # IN OUT 파라미터 개수
            }
        """
        param_analysis = {
            'total': 0,
            'in': 0,
            'out': 0,
            'in_out': 0
        }
        
        # PROCEDURE 또는 FUNCTION의 파라미터 부분 추출
        # 패턴: (PROCEDURE|FUNCTION) name (param1 IN type, param2 OUT type, ...)
        param_section_pattern = r'(?:PROCEDURE|FUNCTION)\s+[A-Z_][A-Z0-9_]*\s*\((.*?)\)'
        
        matches = re.findall(param_section_pattern, self.upper_code, re.DOTALL)
        
        for param_section in matches:
            # 각 파라미터를 쉼표로 분리
            params = param_section.split(',')
            
            for param in params:
                param = param.strip()
                if not param:
                    continue
                
                param_analysis['total'] += 1
                
                # IN OUT 파라미터 (IN OUT이 먼저 와야 함)
                if re.search(r'\bIN\s+OUT\b', param):
                    param_analysis['in_out'] += 1
                # OUT 파라미터
                elif re.search(r'\bOUT\b', param):
                    param_analysis['out'] += 1
                # IN 파라미터 (명시적)
                elif re.search(r'\bIN\b', param):
                    param_analysis['in'] += 1
                # 기본값은 IN (명시하지 않은 경우)
                else:
                    param_analysis['in'] += 1
        
        return param_analysis
    
    def analyze_local_variables(self) -> dict:
        """로컬 변수 분석
        
        Requirements 8.1을 구현합니다.
        프로시저/함수 내에 선언된 로컬 변수를 분석합니다.
        
        Returns:
            로컬 변수 분석 결과
            {
                'total': int,           # 전체 로컬 변수 개수
                'varchar_type': int,    # VARCHAR2 타입 변수 개수
                'number_type': int,     # NUMBER 타입 변수 개수
                'date_type': int,       # DATE 타입 변수 개수
                'boolean_type': int,    # BOOLEAN 타입 변수 개수
                'record_type': int,     # RECORD 타입 변수 개수
                'table_type': int,      # TABLE 타입 변수 개수
                'other_type': int       # 기타 타입 변수 개수
            }
        """
        var_analysis = {
            'total': 0,
            'varchar_type': 0,
            'number_type': 0,
            'date_type': 0,
            'boolean_type': 0,
            'record_type': 0,
            'table_type': 0,
            'other_type': 0
        }
        
        # DECLARE 섹션 또는 IS/AS와 BEGIN 사이의 변수 선언부 추출
        # 패턴 1: DECLARE ... BEGIN
        declare_pattern = r'DECLARE\s+(.*?)\s+BEGIN'
        # 패턴 2: IS/AS ... BEGIN (프로시저/함수 내부)
        is_as_pattern = r'(?:IS|AS)\s+(.*?)\s+BEGIN'
        
        declaration_sections = []
        declaration_sections.extend(re.findall(declare_pattern, self.upper_code, re.DOTALL))
        declaration_sections.extend(re.findall(is_as_pattern, self.upper_code, re.DOTALL))
        
        for section in declaration_sections:
            # 각 줄을 분석하여 변수 선언 찾기
            lines = section.split(';')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 변수 선언 패턴: 변수명 데이터타입 [:= 초기값]
                # CURSOR, PROCEDURE, FUNCTION, TYPE 선언은 제외
                if re.search(r'\b(?:CURSOR|PROCEDURE|FUNCTION|TYPE)\b', line):
                    continue
                
                # %ROWTYPE 먼저 확인 (특수 케이스)
                if '%ROWTYPE' in line:
                    var_analysis['record_type'] += 1
                    var_analysis['total'] += 1
                    continue
                
                # %TYPE 확인 (특수 케이스)
                if '%TYPE' in line:
                    var_analysis['other_type'] += 1
                    var_analysis['total'] += 1
                    continue
                
                # TABLE OF 타입 (컬렉션)
                if re.search(r'\bTABLE\s+OF\b', line):
                    var_analysis['table_type'] += 1
                    var_analysis['total'] += 1
                    continue
                
                # 변수 선언인지 확인 (식별자 다음에 데이터 타입이 오는 패턴)
                var_pattern = r'\b[A-Z_][A-Z0-9_]*\s+(VARCHAR2|NUMBER|DATE|BOOLEAN|INTEGER|TIMESTAMP|CLOB|BLOB|PLS_INTEGER|BINARY_INTEGER)'
                
                match = re.search(var_pattern, line)
                if match:
                    var_analysis['total'] += 1
                    data_type = match.group(1)
                    
                    # 타입별 분류
                    if 'VARCHAR' in data_type:
                        var_analysis['varchar_type'] += 1
                    elif data_type in ['NUMBER', 'INTEGER', 'PLS_INTEGER', 'BINARY_INTEGER']:
                        var_analysis['number_type'] += 1
                    elif data_type in ['DATE', 'TIMESTAMP']:
                        var_analysis['date_type'] += 1
                    elif data_type == 'BOOLEAN':
                        var_analysis['boolean_type'] += 1
                    else:
                        var_analysis['other_type'] += 1
        
        return var_analysis
    
    def analyze_custom_types(self) -> dict:
        """사용자 정의 타입 분석
        
        Requirements 8.1을 구현합니다.
        TYPE 선언을 분석하여 사용자 정의 타입의 개수를 계산합니다.
        
        Returns:
            사용자 정의 타입 분석 결과
            {
                'total': int,       # 전체 사용자 정의 타입 개수
                'record': int,      # RECORD 타입 개수
                'table': int,       # TABLE 타입 개수
                'varray': int,      # VARRAY 타입 개수
                'object': int       # OBJECT 타입 개수
            }
        """
        type_analysis = {
            'total': 0,
            'record': 0,
            'table': 0,
            'varray': 0,
            'object': 0
        }
        
        # TYPE ... IS RECORD 패턴
        record_pattern = r'\bTYPE\s+[A-Z_][A-Z0-9_]*\s+IS\s+RECORD\b'
        type_analysis['record'] = len(re.findall(record_pattern, self.upper_code))
        
        # TYPE ... IS TABLE OF 패턴
        table_pattern = r'\bTYPE\s+[A-Z_][A-Z0-9_]*\s+IS\s+TABLE\s+OF\b'
        type_analysis['table'] = len(re.findall(table_pattern, self.upper_code))
        
        # TYPE ... IS VARRAY 패턴
        varray_pattern = r'\bTYPE\s+[A-Z_][A-Z0-9_]*\s+IS\s+VARRAY\b'
        type_analysis['varray'] = len(re.findall(varray_pattern, self.upper_code))
        
        # CREATE TYPE ... AS OBJECT 패턴
        object_pattern = r'\bCREATE\s+(?:OR\s+REPLACE\s+)?TYPE\s+[A-Z_][A-Z0-9_]*\s+AS\s+OBJECT\b'
        type_analysis['object'] = len(re.findall(object_pattern, self.upper_code))
        
        # 전체 개수 계산
        type_analysis['total'] = (
            type_analysis['record'] +
            type_analysis['table'] +
            type_analysis['varray'] +
            type_analysis['object']
        )
        
        return type_analysis
