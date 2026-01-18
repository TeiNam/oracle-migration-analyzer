"""
PL/SQL Code Analyzer

PL/SQL 코드의 기본 메트릭을 분석하는 기능을 제공합니다.
"""

import re
from .base_parser import PLSQLParserBase


class PLSQLCodeAnalyzer(PLSQLParserBase):
    """PL/SQL 코드 분석
    
    라인 수, 커서, 예외 처리, 중첩 깊이 등의 기본 메트릭을 계산합니다.
    """
    
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
