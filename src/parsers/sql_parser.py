"""
SQL Parser

Oracle SQL 쿼리를 파싱하여 구문 요소를 추출하는 모듈입니다.
Requirements 1.1-1.5, 2.1-2.5, 3.1, 7.1-7.5를 구현합니다.
"""

import re
from typing import List, Dict


class SQLParser:
    """SQL 쿼리 파싱 및 구문 요소 추출
    
    Oracle SQL 쿼리를 분석하여 복잡도 계산에 필요한 다양한 구문 요소를 추출합니다.
    """
    
    def __init__(self, query: str):
        """SQLParser 초기화
        
        Args:
            query: 분석할 SQL 쿼리 문자열
        """
        self.query = query.strip()
        self.upper_query = query.strip().upper()
        self.normalized_query = self._normalize_query()
    
    def _normalize_query(self) -> str:
        """쿼리 정규화 (공백, 줄바꿈 처리)
        
        Requirements 1.1-1.5를 위한 전처리 작업입니다.
        - 여러 공백을 하나로 통합
        - 줄바꿈을 공백으로 변환
        - 탭을 공백으로 변환
        - 주석 제거 (-- 및 /* */)
        
        Returns:
            정규화된 쿼리 문자열
        """
        # 원본 쿼리의 대문자 버전으로 시작
        normalized = self.upper_query
        
        # 한 줄 주석 제거 (-- 주석)
        normalized = re.sub(r'--[^\n]*', ' ', normalized)
        
        # 여러 줄 주석 제거 (/* */ 주석)
        normalized = re.sub(r'/\*.*?\*/', ' ', normalized, flags=re.DOTALL)
        
        # 줄바꿈과 탭을 공백으로 변환
        normalized = normalized.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 여러 공백을 하나로 통합
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 앞뒤 공백 제거
        normalized = normalized.strip()
        
        return normalized
    
    def count_joins(self) -> int:
        """JOIN 개수 계산 (명시적 + 암시적)
        
        Requirements 1.1을 구현합니다.
        - 명시적 JOIN: INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL JOIN, CROSS JOIN
        - 암시적 JOIN: FROM 절의 쉼표로 구분된 테이블 (Cartesian product)
        
        Returns:
            총 JOIN 개수
        """
        join_count = 0
        
        # 명시적 JOIN 개수 계산
        # JOIN 키워드 자체를 세되, 중복 카운팅 방지
        # LEFT OUTER JOIN, RIGHT OUTER JOIN 등은 하나의 JOIN으로 카운팅
        join_patterns = [
            r'\bINNER\s+JOIN\b',
            r'\bLEFT\s+(?:OUTER\s+)?JOIN\b',
            r'\bRIGHT\s+(?:OUTER\s+)?JOIN\b',
            r'\bFULL\s+(?:OUTER\s+)?JOIN\b',
            r'\bCROSS\s+JOIN\b',
        ]
        
        for pattern in join_patterns:
            matches = re.findall(pattern, self.normalized_query)
            join_count += len(matches)
        
        # 단순 JOIN (위의 패턴에 매칭되지 않은 경우만)
        # INNER, LEFT, RIGHT, FULL, CROSS가 앞에 없는 JOIN만 카운팅
        simple_join_pattern = r'(?<!INNER\s)(?<!LEFT\s)(?<!RIGHT\s)(?<!FULL\s)(?<!CROSS\s)(?<!OUTER\s)\bJOIN\b'
        simple_joins = re.findall(simple_join_pattern, self.normalized_query)
        join_count += len(simple_joins)
        
        # 암시적 JOIN 개수 계산 (FROM 절의 쉼표)
        # FROM 절 추출
        from_match = re.search(r'\bFROM\s+(.*?)(?:\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bHAVING\b|\bUNION\b|\bINTERSECT\b|\bMINUS\b|$)', 
                               self.normalized_query, re.DOTALL)
        
        if from_match:
            from_clause = from_match.group(1)
            # 서브쿼리 내부의 쉼표는 제외하기 위해 괄호 내부 제거
            from_clause_no_subquery = re.sub(r'\([^)]*\)', '', from_clause)
            # 쉼표 개수 세기 (쉼표 개수 = 암시적 JOIN 개수)
            comma_count = from_clause_no_subquery.count(',')
            join_count += comma_count
        
        return join_count
    
    def calculate_subquery_depth(self) -> int:
        """서브쿼리 중첩 깊이 계산
        
        Requirements 1.2를 구현합니다.
        SELECT 문의 중첩 깊이를 계산합니다.
        
        Returns:
            서브쿼리 중첩 깊이 (0 = 서브쿼리 없음)
        """
        max_depth = 0
        current_depth = 0
        
        # SELECT 키워드를 기준으로 깊이 추적
        i = 0
        while i < len(self.normalized_query):
            # SELECT 발견 시 깊이 증가
            if self.normalized_query[i:i+6] == 'SELECT':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                i += 6
            # 괄호 열림 - 서브쿼리 시작 가능성
            elif self.normalized_query[i] == '(':
                i += 1
            # 괄호 닫힘 - 서브쿼리 종료 가능성
            elif self.normalized_query[i] == ')':
                # 이전에 SELECT가 있었다면 깊이 감소
                if current_depth > 0:
                    current_depth -= 1
                i += 1
            else:
                i += 1
        
        # 최상위 SELECT는 서브쿼리가 아니므로 1을 빼줌
        return max(0, max_depth - 1)
    
    def count_ctes(self) -> int:
        """CTE(WITH 절) 개수 계산
        
        Requirements 1.3을 구현합니다.
        WITH 절에 정의된 CTE(Common Table Expression) 개수를 계산합니다.
        
        Returns:
            CTE 개수
        """
        cte_count = 0
        
        # WITH 절이 있는지 확인
        if not re.search(r'\bWITH\b', self.normalized_query):
            return 0
        
        # WITH 절 전체를 찾기 (WITH부터 메인 SELECT 전까지)
        # CTE 정의는 "이름 AS (" 패턴을 따름
        # 괄호 깊이를 추적하여 메인 SELECT를 찾음
        with_start = self.normalized_query.find('WITH')
        if with_start == -1:
            return 0
        
        # WITH 다음부터 시작
        i = with_start + 4
        paren_depth = 0
        in_cte_definition = False
        
        while i < len(self.normalized_query):
            # SELECT를 만났고 괄호 밖이면 메인 SELECT
            if self.normalized_query[i:i+6] == 'SELECT' and paren_depth == 0:
                break
            
            # AS ( 패턴을 찾으면 CTE 정의 시작
            if self.normalized_query[i:i+2] == 'AS' and i + 2 < len(self.normalized_query):
                # AS 다음 공백 건너뛰기
                j = i + 2
                while j < len(self.normalized_query) and self.normalized_query[j] == ' ':
                    j += 1
                # 괄호가 나오면 CTE 정의
                if j < len(self.normalized_query) and self.normalized_query[j] == '(':
                    cte_count += 1
                    in_cte_definition = True
            
            if self.normalized_query[i] == '(':
                paren_depth += 1
            elif self.normalized_query[i] == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    in_cte_definition = False
            
            i += 1
        
        return cte_count
    
    def count_set_operators(self) -> int:
        """집합 연산자(UNION/INTERSECT/MINUS) 개수 계산
        
        Requirements 1.4를 구현합니다.
        
        Returns:
            집합 연산자 개수
        """
        set_operator_count = 0
        
        # UNION (ALL 포함)
        set_operator_count += len(re.findall(r'\bUNION\s+ALL\b', self.normalized_query))
        set_operator_count += len(re.findall(r'\bUNION\b(?!\s+ALL)', self.normalized_query))
        
        # INTERSECT
        set_operator_count += len(re.findall(r'\bINTERSECT\b', self.normalized_query))
        
        # MINUS (Oracle) 또는 EXCEPT (표준 SQL)
        set_operator_count += len(re.findall(r'\bMINUS\b', self.normalized_query))
        set_operator_count += len(re.findall(r'\bEXCEPT\b', self.normalized_query))
        
        return set_operator_count
    
    def detect_oracle_features(self) -> List[str]:
        """Oracle 특화 기능 감지
        
        Requirements 2.1-2.5를 구현합니다.
        ORACLE_SPECIFIC_SYNTAX에 정의된 기능들을 감지합니다.
        
        Returns:
            감지된 Oracle 특화 기능 목록
        """
        from src.oracle_complexity_analyzer import ORACLE_SPECIFIC_SYNTAX
        
        detected_features = []
        
        for feature in ORACLE_SPECIFIC_SYNTAX.keys():
            # 특수 문자 이스케이프
            escaped_feature = re.escape(feature)
            
            # 단어 경계를 고려한 패턴 (특수 문자 제외)
            if feature.isalnum() or ' ' in feature:
                pattern = r'\b' + escaped_feature + r'\b'
            else:
                pattern = escaped_feature
            
            if re.search(pattern, self.normalized_query):
                detected_features.append(feature)
        
        return detected_features
    
    def detect_oracle_functions(self) -> List[str]:
        """Oracle 특화 함수 감지
        
        Requirements 3.1, 3.2를 구현합니다.
        ORACLE_SPECIFIC_FUNCTIONS에 정의된 함수들을 감지합니다.
        
        Returns:
            감지된 Oracle 특화 함수 목록
        """
        from src.oracle_complexity_analyzer import ORACLE_SPECIFIC_FUNCTIONS
        
        detected_functions = []
        
        for function in ORACLE_SPECIFIC_FUNCTIONS.keys():
            # 함수는 뒤에 괄호가 따라옴
            pattern = r'\b' + re.escape(function) + r'\s*\('
            
            if re.search(pattern, self.normalized_query):
                detected_functions.append(function)
        
        return detected_functions
    
    def count_hints(self) -> List[str]:
        """힌트 감지 및 개수 계산
        
        Requirements 7.1-7.5를 구현합니다.
        Oracle 힌트는 /*+ ... */ 형식으로 표현됩니다.
        
        Returns:
            감지된 힌트 목록
        """
        from src.oracle_complexity_analyzer import ORACLE_HINTS
        
        detected_hints = []
        
        # 힌트 블록 찾기 (/*+ ... */)
        hint_blocks = re.findall(r'/\*\+\s*(.*?)\s*\*/', self.upper_query, re.DOTALL)
        
        for hint_block in hint_blocks:
            # 각 힌트 블록 내에서 정의된 힌트 찾기
            for hint in ORACLE_HINTS:
                if re.search(r'\b' + re.escape(hint) + r'\b', hint_block):
                    if hint not in detected_hints:
                        detected_hints.append(hint)
        
        return detected_hints
    
    def count_analytic_functions(self) -> int:
        """분석 함수(OVER 절) 개수 계산
        
        Requirements 2.2, 4.1을 구현합니다.
        
        Returns:
            분석 함수 개수
        """
        from src.oracle_complexity_analyzer import ANALYTIC_FUNCTIONS
        
        analytic_count = 0
        
        for function in ANALYTIC_FUNCTIONS:
            # 분석 함수는 OVER 절과 함께 사용됨
            pattern = r'\b' + re.escape(function) + r'\s*\([^)]*\)\s+OVER\s*\('
            matches = re.findall(pattern, self.normalized_query)
            analytic_count += len(matches)
        
        return analytic_count
    
    def count_aggregate_functions(self) -> int:
        """집계 함수 개수 계산
        
        Requirements 4.1을 구현합니다.
        
        Returns:
            집계 함수 개수
        """
        from src.oracle_complexity_analyzer import AGGREGATE_FUNCTIONS
        
        aggregate_count = 0
        
        for function in AGGREGATE_FUNCTIONS:
            # 집계 함수는 괄호와 함께 사용됨 (단, OVER 절이 없는 경우만)
            pattern = r'\b' + re.escape(function) + r'\s*\('
            matches = re.findall(pattern, self.normalized_query)
            aggregate_count += len(matches)
        
        return aggregate_count
    
    def count_case_expressions(self) -> int:
        """CASE 표현식 개수 계산
        
        Requirements 4.3을 구현합니다.
        
        Returns:
            CASE 표현식 개수
        """
        # CASE ... END 패턴 찾기
        case_count = len(re.findall(r'\bCASE\b', self.normalized_query))
        
        return case_count
    
    def has_fullscan_risk(self) -> bool:
        """풀스캔 위험 여부 판단 (WHERE 절 없음 등)
        
        Requirements 1.5를 구현합니다.
        
        Returns:
            풀스캔 위험 여부
        """
        # SELECT 문에서 WHERE 절이 없는지 확인
        has_where = bool(re.search(r'\bWHERE\b', self.normalized_query))
        
        # SELECT 문이 있고 WHERE 절이 없으면 풀스캔 위험
        has_select = bool(re.search(r'\bSELECT\b', self.normalized_query))
        
        return has_select and not has_where
    
    def count_derived_tables(self) -> int:
        """파생 테이블 개수 계산
        
        Requirements 6.6을 구현합니다.
        FROM 절의 서브쿼리를 파생 테이블로 간주합니다.
        
        Returns:
            파생 테이블 개수
        """
        # FROM 절 내의 서브쿼리 (SELECT) 개수
        # FROM ... (SELECT ...) 패턴
        pattern = r'\bFROM\s+[^(]*\(\s*SELECT\b'
        derived_count = len(re.findall(pattern, self.normalized_query))
        
        return derived_count
    
    def has_performance_penalties(self) -> Dict[str, bool]:
        """성능 페널티 요소 감지 (DISTINCT, OR 조건 등)
        
        Requirements 6.7을 구현합니다.
        
        Returns:
            성능 페널티 요소 딕셔너리
        """
        penalties = {
            'distinct': False,
            'or_conditions': False,
            'like_pattern': False,
            'function_in_where': False,
        }
        
        # DISTINCT 사용 여부
        penalties['distinct'] = bool(re.search(r'\bDISTINCT\b', self.normalized_query))
        
        # OR 조건 3개 이상
        where_match = re.search(r'\bWHERE\s+(.*?)(?:\bGROUP\s+BY\b|\bORDER\s+BY\b|\bHAVING\b|$)', 
                               self.normalized_query, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            or_count = len(re.findall(r'\bOR\b', where_clause))
            penalties['or_conditions'] = or_count >= 3
            
            # LIKE '%문자열%' 패턴
            penalties['like_pattern'] = bool(re.search(r"LIKE\s+'%[^']+%'", where_clause))
            
            # WHERE 절에 함수 사용
            # 간단한 휴리스틱: WHERE 절에 괄호가 있으면 함수 사용으로 간주
            penalties['function_in_where'] = bool(re.search(r'\(', where_clause))
        
        return penalties
