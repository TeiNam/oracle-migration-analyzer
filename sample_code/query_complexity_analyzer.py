#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Oracle 쿼리 복잡도 분석기
Oracle SQL 쿼리의 복잡도를 0-10 척도로 평가하는 도구
"""

import re
import sqlparse

def calculate_query_complexity(query):
    """
    Oracle 쿼리의 복잡도를 0-10 척도로 평가하는 함수
    
    Args:
        query (str): 평가할 Oracle SQL 쿼리
        
    Returns:
        float: 0-10 사이의 복잡도 점수
        dict: 세부 평가 요소별 점수
    """
    # 쿼리 정규화 및 파싱
    query = query.strip().upper()
    parsed = sqlparse.parse(query)[0]
    
    # 점수 초기화
    scores = {
        "structural_complexity": 0,
        "oracle_specific_features": 0,
        "functions_expressions": 0,
        "data_volume": 0,
        "execution_complexity": 0,
        "postgres_conversion": 0
    }
    
    # 1. 구조적 복잡성 평가
    # 테이블 조인 수 계산
    join_count = len(re.findall(r'\bJOIN\b', query))
    if "," in query and "FROM" in query:
        # 암시적 조인도 계산
        from_clause = re.search(r'FROM\s+(.*?)(?:WHERE|GROUP BY|ORDER BY|HAVING|$)', query, re.DOTALL)
        if from_clause:
            tables = from_clause.group(1).split(',')
            join_count += max(0, len(tables) - 1)
    
    if join_count == 0:
        scores["structural_complexity"] += 0
    elif join_count <= 2:
        scores["structural_complexity"] += 1
    elif join_count <= 4:
        scores["structural_complexity"] += 2
    else:
        scores["structural_complexity"] += 3
    
    # 서브쿼리 중첩 깊이 계산
    subquery_depth = 0
    open_parens = 0
    max_depth = 0
    select_in_parens = False
    
    for char in query:
        if char == '(':
            open_parens += 1
            if 'SELECT' in query[max(0, query.find(char)-10):query.find(char)]:
                select_in_parens = True
                subquery_depth += 1
                max_depth = max(max_depth, subquery_depth)
        elif char == ')':
            if open_parens > 0:
                open_parens -= 1
                if select_in_parens:
                    subquery_depth -= 1
                    select_in_parens = False
    
    if max_depth == 0:
        scores["structural_complexity"] += 0
    elif max_depth == 1:
        scores["structural_complexity"] += 1
    elif max_depth == 2:
        scores["structural_complexity"] += 2
    else:
        scores["structural_complexity"] += 3 + min(2, max_depth - 2)  # 3단계 이상은 추가 점수
    
    # WITH 절(CTE) 사용 수
    cte_count = len(re.findall(r'\bWITH\b', query))
    scores["structural_complexity"] += min(2, cte_count)
    
    # UNION/INTERSECT/MINUS 연산자 사용
    set_operators = len(re.findall(r'\b(UNION|INTERSECT|MINUS)\b', query))
    scores["structural_complexity"] += min(2, set_operators)
    
    # 2. Oracle 특화 기능 사용
    # CONNECT BY 계층적 쿼리
    if re.search(r'\bCONNECT\s+BY\b', query):
        scores["oracle_specific_features"] += 2
    
    # 분석 함수 사용
    analytic_functions = len(re.findall(r'\bOVER\s*\(', query))
    if analytic_functions > 0:
        scores["oracle_specific_features"] += min(3, analytic_functions)
    
    # PIVOT/UNPIVOT 사용
    if re.search(r'\b(PIVOT|UNPIVOT)\b', query):
        scores["oracle_specific_features"] += 2
    
    # MODEL 절 사용
    if re.search(r'\bMODEL\b', query):
        scores["oracle_specific_features"] += 3
    
    # 3. 함수 및 표현식
    # 집계 함수 사용 수
    agg_functions = len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX|STDDEV|VARIANCE)\s*\(', query))
    scores["functions_expressions"] += min(2, agg_functions * 0.5)
    
    # 사용자 정의 함수 호출 추정 (정확한 판단은 어려움)
    # 일반적인 내장 함수가 아닌 함수 호출 패턴 찾기
    std_functions = r'(COUNT|SUM|AVG|MIN|MAX|SUBSTR|INSTR|TO_DATE|TO_CHAR|NVL|DECODE|CASE|CAST|CONVERT)'
    potential_udf = len(re.findall(r'[A-Z0-9_]+\s*\(', query)) - len(re.findall(r'\b' + std_functions + r'\s*\(', query))
    scores["functions_expressions"] += min(2, max(0, potential_udf * 0.5))
    
    # CASE 표현식 복잡도
    case_count = len(re.findall(r'\bCASE\b', query))
    scores["functions_expressions"] += min(2, case_count * 0.5)
    
    # 정규식 및 복잡한 문자열 처리
    if re.search(r'\bREGEXP_', query):
        scores["functions_expressions"] += 1
    
    # 4. 데이터 처리 볼륨 (정적 분석으로는 정확한 평가 어려움)
    # 여기서는 쿼리의 길이와 복잡성을 기반으로 추정
    query_length = len(query)
    if query_length < 200:
        scores["data_volume"] += 0.5
    elif query_length < 500:
        scores["data_volume"] += 1
    elif query_length < 1000:
        scores["data_volume"] += 1.5
    else:
        scores["data_volume"] += 2
    
    # 5. 실행 계획 복잡성 (정적 분석으로는 제한적 평가)
    # 여기서는 쿼리의 구조적 특성을 기반으로 추정
    if join_count > 3 or max_depth > 1:
        scores["execution_complexity"] += 1
    
    if "ORDER BY" in query:
        scores["execution_complexity"] += 0.5
    
    if "GROUP BY" in query:
        scores["execution_complexity"] += 0.5
    
    if "HAVING" in query:
        scores["execution_complexity"] += 0.5
    
    # 6. PostgreSQL 변환 난이도
    # Oracle 특화 기능 사용 정도
    oracle_specific = [
        r'\bCONNECT\s+BY\b', r'\bSTART\s+WITH\b', r'\bPRIOR\b',
        r'\bMODEL\b', r'\b(PIVOT|UNPIVOT)\b', r'\bFLASHBACK\b',
        r'\bSYS_CONNECT_BY_PATH\b', r'\bROWID\b', r'\bROWNUM\b'
    ]
    
    for pattern in oracle_specific:
        if re.search(pattern, query):
            scores["postgres_conversion"] += 1
    
    # 특수 함수 사용
    oracle_functions = [
        r'\bDECODE\s*\(', r'\bNVL2\s*\(', r'\bLISTAGG\s*\(',
        r'\bREGEXP_', r'\bSYS_CONTEXT\s*\(', r'\bEXTRACT\s*\('
    ]
    
    for pattern in oracle_functions:
        if re.search(pattern, query):
            scores["postgres_conversion"] += 0.5
    
    # 총점 계산 (각 카테고리 최대 점수 제한)
    max_scores = {
        "structural_complexity": 3.5,
        "oracle_specific_features": 3.0,
        "functions_expressions": 2.0,
        "data_volume": 2.0,
        "execution_complexity": 1.5,
        "postgres_conversion": 2.0
    }
    
    for category in scores:
        scores[category] = min(scores[category], max_scores[category])
    
    # 최종 복잡도 점수 계산 (0-10 척도로 정규화)
    total_score = sum(scores.values())
    normalized_score = min(10, total_score * 10 / sum(max_scores.values()))
    
    # 복잡도 레벨 결정
    complexity_level = round(normalized_score, 1)
    
    return complexity_level, scores

def get_complexity_description(score):
    """
    복잡도 점수에 따른 설명 반환
    
    Args:
        score (float): 복잡도 점수 (0-10)
        
    Returns:
        str: 복잡도 설명
    """
    if score <= 1:
        return "매우 간단 (Very Simple)"
    elif score <= 3:
        return "간단 (Simple)"
    elif score <= 5:
        return "중간 (Moderate)"
    elif score <= 7:
        return "복잡 (Complex)"
    elif score <= 9:
        return "매우 복잡 (Very Complex)"
    else:
        return "극도로 복잡 (Extremely Complex)"

def analyze_query(query):
    """
    쿼리를 분석하고 복잡도 결과를 출력
    
    Args:
        query (str): 분석할 Oracle SQL 쿼리
        
    Returns:
        tuple: (복잡도 점수, 복잡도 설명, 세부 점수 딕셔너리)
    """
    complexity_score, detailed_scores = calculate_query_complexity(query)
    description = get_complexity_description(complexity_score)
    
    print(f"쿼리 복잡도 점수: {complexity_score}/10 - {description}")
    print("\n세부 평가 요소:")
    for category, score in detailed_scores.items():
        print(f"- {category}: {score}")
    
    return complexity_score, description, detailed_scores

def main():
    """
    메인 함수: 사용자로부터 쿼리를 입력받아 복잡도 분석
    """
    print("Oracle 쿼리 복잡도 분석기")
    print("쿼리를 입력하세요 (입력 종료는 빈 줄에서 Ctrl+D 또는 Ctrl+Z):")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    query = "\n".join(lines)
    
    if query.strip():
        complexity_score, description, detailed_scores = analyze_query(query)
        
        # 결과를 파일로 저장할지 물어봄
        user_input = input("\n분석 결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
        if user_input == 'y' or user_input == 'yes':
            default_output = "query_analysis_report.md"
            output_file = input(f"출력 파일 경로를 입력하세요 (기본값: {default_output}): ").strip()
            if not output_file:
                output_file = default_output
                
            # 마크다운 형식으로 보고서 생성
            report = []
            report.append("# Oracle 쿼리 복잡도 분석 보고서")
            report.append(f"\n## 복잡도 점수: {complexity_score}/10 - {description}")
            report.append("\n## 세부 평가 요소:")
            for category, score in detailed_scores.items():
                report.append(f"- {category}: {score}")
            
            report.append("\n## 분석된 쿼리:")
            report.append("```sql")
            report.append(query)
            report.append("```")
            
            # 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))
            print(f"보고서가 {output_file}에 저장되었습니다.")
    else:
        print("쿼리가 입력되지 않았습니다.")

if __name__ == "__main__":
    # 예시 쿼리로 테스트
    example_query = """
    SELECT e.employee_id, e.first_name, e.last_name, d.department_name,
           (SELECT AVG(salary) FROM employees WHERE department_id = e.department_id) as avg_dept_salary,
           CASE WHEN e.salary > (SELECT AVG(salary) FROM employees) THEN 'Above Average' ELSE 'Below Average' END as salary_status
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
    WHERE e.hire_date > TO_DATE('2010-01-01', 'YYYY-MM-DD')
    ORDER BY e.department_id, e.salary DESC
    """
    
    print("예시 쿼리 분석 결과:")
    analyze_query(example_query)
    
    print("\n사용자 쿼리 분석을 시작하려면 스크립트를 직접 실행하세요.")
    print("사용법: python query_complexity_analyzer.py")
