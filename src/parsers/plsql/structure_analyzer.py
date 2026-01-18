"""
PL/SQL Structure Analyzer

PL/SQL 코드의 구조적 요소를 분석하는 기능을 제공합니다.
"""

import re
from ...oracle_complexity_analyzer import PLSQLObjectType
from .base_parser import PLSQLParserBase


class PLSQLStructureAnalyzer(PLSQLParserBase):
    """PL/SQL 구조 분석
    
    패키지 내 프로시저/함수, 파라미터, 로컬 변수, 사용자 정의 타입 등을 분석합니다.
    """
    
    def count_procedures_in_package(self) -> int:
        """패키지 내 프로시저 개수 계산
        
        Requirements 8.1을 구현합니다.
        패키지 내에 정의된 프로시저의 개수를 계산합니다.
        
        Returns:
            프로시저 개수 (패키지가 아닌 경우 0)
        """
        if not self._is_package_code():
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
        if not self._is_package_code():
            return 0
        
        # FUNCTION 키워드 개수 계산
        # CREATE FUNCTION은 제외하고 패키지 내부의 FUNCTION만 계산
        function_pattern = r'\bFUNCTION\s+[A-Z_][A-Z0-9_]*\s*[\(]'
        
        matches = re.findall(function_pattern, self.upper_code)
        
        return len(matches)
    
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
