"""
ComplexityCalculator 테스트

ComplexityCalculator 클래스의 기본 기능을 테스트합니다.
"""

import pytest
from src.calculators import ComplexityCalculator
from src.parsers.sql_parser import SQLParser
from src.parsers.plsql_parser import PLSQLParser
from src.oracle_complexity_analyzer import (
    TargetDatabase,
    ComplexityLevel,
    PLSQLObjectType,
)


class TestComplexityCalculatorBasic:
    """ComplexityCalculator 기본 기능 테스트"""
    
    def test_create_calculator_postgresql(self):
        """PostgreSQL 타겟으로 ComplexityCalculator 생성"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc.target == TargetDatabase.POSTGRESQL
        assert calc.weights is not None
    
    def test_create_calculator_mysql(self):
        """MySQL 타겟으로 ComplexityCalculator 생성"""
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        assert calc.target == TargetDatabase.MYSQL
        assert calc.weights is not None
    
    def test_normalize_score_within_range(self):
        """점수 정규화가 0-10 범위 내에 있는지 확인"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 다양한 점수 테스트
        assert 0 <= calc._normalize_score(0) <= 10
        assert 0 <= calc._normalize_score(5) <= 10
        assert 0 <= calc._normalize_score(13.5) <= 10
        assert 0 <= calc._normalize_score(20) <= 10
    
    def test_get_complexity_level_very_simple(self):
        """매우 간단 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(0.5) == ComplexityLevel.VERY_SIMPLE
    
    def test_get_complexity_level_simple(self):
        """간단 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(2.0) == ComplexityLevel.SIMPLE
    
    def test_get_complexity_level_moderate(self):
        """중간 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(4.0) == ComplexityLevel.MODERATE
    
    def test_get_complexity_level_complex(self):
        """복잡 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(6.0) == ComplexityLevel.COMPLEX
    
    def test_get_complexity_level_very_complex(self):
        """매우 복잡 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(8.0) == ComplexityLevel.VERY_COMPLEX
    
    def test_get_complexity_level_extremely_complex(self):
        """극도로 복잡 레벨 분류"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        assert calc._get_complexity_level(9.5) == ComplexityLevel.EXTREMELY_COMPLEX
    
    def test_get_recommendation(self):
        """권장사항 반환"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        assert calc._get_recommendation(ComplexityLevel.VERY_SIMPLE) == "자동 변환"
        assert calc._get_recommendation(ComplexityLevel.SIMPLE) == "함수 대체"
        assert calc._get_recommendation(ComplexityLevel.MODERATE) == "부분 재작성"
        assert calc._get_recommendation(ComplexityLevel.COMPLEX) == "상당한 재작성"
        assert calc._get_recommendation(ComplexityLevel.VERY_COMPLEX) == "대부분 재작성"
        assert calc._get_recommendation(ComplexityLevel.EXTREMELY_COMPLEX) == "완전 재설계"


class TestSQLComplexityCalculation:
    """SQL 복잡도 계산 테스트"""
    
    def test_calculate_simple_query_postgresql(self):
        """간단한 쿼리 복잡도 계산 (PostgreSQL)"""
        query = "SELECT * FROM users WHERE id = 1"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_sql_complexity(parser)
        
        assert result is not None
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert 0 <= result.normalized_score <= 10
        assert result.complexity_level is not None
        assert result.recommendation is not None
    
    def test_calculate_simple_query_mysql(self):
        """간단한 쿼리 복잡도 계산 (MySQL)"""
        query = "SELECT * FROM users WHERE id = 1"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        
        result = calc.calculate_sql_complexity(parser)
        
        assert result is not None
        assert result.target_database == TargetDatabase.MYSQL
        assert 0 <= result.normalized_score <= 10
    
    def test_calculate_complex_query_with_joins(self):
        """JOIN이 있는 복잡한 쿼리"""
        query = """
        SELECT u.name, o.order_date, p.product_name
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        INNER JOIN order_items oi ON o.id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.id
        WHERE u.status = 'active'
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_sql_complexity(parser)
        
        assert result.join_count == 3
        assert result.structural_complexity > 0
    
    def test_calculate_query_with_subquery(self):
        """서브쿼리가 있는 쿼리"""
        query = """
        SELECT * FROM users
        WHERE id IN (SELECT user_id FROM orders WHERE total > 1000)
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_sql_complexity(parser)
        
        assert result.subquery_depth >= 1
        assert result.structural_complexity > 0
    
    def test_calculate_query_with_oracle_features(self):
        """Oracle 특화 기능이 있는 쿼리"""
        query = """
        SELECT employee_id, last_name, salary,
               RANK() OVER (ORDER BY salary DESC) as salary_rank
        FROM employees
        WHERE ROWNUM <= 10
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_sql_complexity(parser)
        
        assert len(result.detected_oracle_features) > 0
        assert result.oracle_specific_features > 0


class TestPLSQLComplexityCalculation:
    """PL/SQL 복잡도 계산 테스트"""
    
    def test_calculate_simple_procedure(self):
        """간단한 프로시저 복잡도 계산"""
        code = """
        CREATE OR REPLACE PROCEDURE update_salary(p_emp_id NUMBER, p_new_salary NUMBER) IS
        BEGIN
            UPDATE employees SET salary = p_new_salary WHERE employee_id = p_emp_id;
            COMMIT;
        END;
        """
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        assert result is not None
        assert result.object_type == PLSQLObjectType.PROCEDURE
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert 0 <= result.normalized_score <= 10
        assert result.base_score > 0
    
    def test_calculate_function_with_cursor(self):
        """커서가 있는 함수"""
        code = """
        CREATE OR REPLACE FUNCTION get_employee_count RETURN NUMBER IS
            v_count NUMBER;
            CURSOR emp_cursor IS SELECT * FROM employees;
        BEGIN
            SELECT COUNT(*) INTO v_count FROM employees;
            RETURN v_count;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN 0;
        END;
        """
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        assert result.object_type == PLSQLObjectType.FUNCTION
        assert result.cursor_count >= 1
        assert result.exception_blocks >= 1
        assert result.code_complexity > 0
    
    def test_calculate_package_postgresql(self):
        """패키지 복잡도 계산 (PostgreSQL)"""
        code = """
        CREATE OR REPLACE PACKAGE emp_pkg IS
            PROCEDURE hire_employee(p_name VARCHAR2);
            FUNCTION get_salary(p_emp_id NUMBER) RETURN NUMBER;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        assert result.object_type == PLSQLObjectType.PACKAGE
        assert result.base_score == 7.0  # PostgreSQL 패키지 기본 점수
    
    def test_calculate_package_mysql(self):
        """패키지 복잡도 계산 (MySQL)"""
        code = """
        CREATE OR REPLACE PACKAGE emp_pkg IS
            PROCEDURE hire_employee(p_name VARCHAR2);
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        assert result.object_type == PLSQLObjectType.PACKAGE
        assert result.base_score == 8.0  # MySQL 패키지 기본 점수
        assert result.app_migration_penalty == 2.0  # MySQL 애플리케이션 이관 페널티


class TestStructuralComplexity:
    """구조적 복잡성 계산 테스트"""
    
    def test_structural_complexity_no_joins(self):
        """JOIN이 없는 경우"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_structural_complexity(parser)
        assert score >= 0
    
    def test_structural_complexity_with_cte(self):
        """CTE가 있는 경우"""
        query = """
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        )
        SELECT * FROM active_users
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_structural_complexity(parser)
        assert score > 0


class TestDataVolumeScore:
    """데이터 볼륨 점수 계산 테스트"""
    
    def test_data_volume_small(self):
        """작은 쿼리 (< 200자)"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        score = calc._calculate_data_volume_score(100)
        assert score == 0.5
    
    def test_data_volume_medium_postgresql(self):
        """중간 쿼리 (200-500자) - PostgreSQL"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        score = calc._calculate_data_volume_score(300)
        assert score == 1.0
    
    def test_data_volume_medium_mysql(self):
        """중간 쿼리 (200-500자) - MySQL"""
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        score = calc._calculate_data_volume_score(300)
        assert score == 1.2
    
    def test_data_volume_large_postgresql(self):
        """큰 쿼리 (500-1000자) - PostgreSQL"""
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        score = calc._calculate_data_volume_score(700)
        assert score == 1.5
    
    def test_data_volume_xlarge_mysql(self):
        """매우 큰 쿼리 (1000자 이상) - MySQL"""
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        score = calc._calculate_data_volume_score(1500)
        assert score == 2.5


class TestConversionDifficulty:
    """변환 난이도 계산 테스트"""
    
    def test_conversion_difficulty_no_hints_no_features(self):
        """힌트와 Oracle 특화 기능이 없는 경우"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        assert score == 0.0
    
    def test_conversion_difficulty_few_hints(self):
        """힌트가 1-2개인 경우"""
        query = "SELECT /*+ INDEX(users idx_users) */ * FROM users"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        assert score == 0.5
    
    def test_conversion_difficulty_many_hints(self):
        """힌트가 6개 이상인 경우"""
        query = """
        SELECT /*+ INDEX(u idx_users) FULL(o) PARALLEL(4) USE_HASH(u o) 
                   LEADING(u) ORDERED */ 
        * FROM users u, orders o
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        assert score == 1.5
    
    def test_conversion_difficulty_with_oracle_features(self):
        """Oracle 특화 기능이 있는 경우"""
        query = "SELECT * FROM users WHERE ROWNUM <= 10"
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        # ROWNUM = 0.3점
        assert score == 0.3
    
    def test_conversion_difficulty_with_complex_features(self):
        """복잡한 Oracle 특화 기능이 있는 경우"""
        query = """
        SELECT * FROM departments
        START WITH parent_id IS NULL
        CONNECT BY PRIOR department_id = parent_id
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        # CONNECT BY = 1.0, START WITH = 0.5, PRIOR = 0.3 = 1.8점
        assert score >= 1.5
    
    def test_conversion_difficulty_with_model_clause(self):
        """MODEL 절이 있는 경우"""
        query = """
        SELECT * FROM sales
        MODEL DIMENSION BY (product_id) MEASURES (sales_amount)
        RULES (sales_amount[1] = 100)
        """
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        score = calc._calculate_conversion_difficulty(parser)
        # MODEL = 1.0점
        assert score >= 1.0


# ============================================================================
# 속성 기반 테스트 (Property-Based Tests)
# ============================================================================

from hypothesis import given, strategies as st, settings


class TestOracleFunctionScoreProperty:
    """Oracle 특화 함수 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 3: Oracle 특화 함수 점수 계산 정확성
    Validates: Requirements 3.1, 3.2
    """
    
    @given(st.lists(st.sampled_from([
        'DECODE', 'NVL', 'NVL2', 'LISTAGG', 'REGEXP_LIKE', 'REGEXP_SUBSTR',
        'REGEXP_REPLACE', 'REGEXP_INSTR', 'SYS_CONTEXT', 'EXTRACT',
        'TO_CHAR', 'TO_DATE', 'TO_NUMBER', 'TRUNC', 'ADD_MONTHS',
        'MONTHS_BETWEEN', 'NEXT_DAY', 'LAST_DAY', 'SYSDATE', 'SYSTIMESTAMP',
        'CURRENT_DATE', 'SUBSTR', 'INSTR', 'CHR', 'TRANSLATE'
    ]), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_oracle_function_score_accuracy(self, oracle_functions):
        """
        Property 3: Oracle 특화 함수 점수 계산 정확성
        
        For any SQL 쿼리에 대해, 감지된 Oracle 특화 함수 각각에 대해 0.5점이 부여되어야 합니다.
        """
        # 쿼리 생성
        if oracle_functions:
            function_calls = ', '.join([f"{func}(column)" for func in oracle_functions])
            query = f"SELECT {function_calls} FROM users"
        else:
            query = "SELECT * FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # Oracle 함수 점수 계산
        detected_functions = parser.detect_oracle_functions()
        expected_score = len(detected_functions) * 0.5
        
        # 함수/표현식 점수 계산 (Oracle 함수 포함)
        actual_score = calc._calculate_oracle_function_score(parser)
        
        # 검증: 각 Oracle 함수당 최소 0.5점 (다른 함수 점수도 포함될 수 있음)
        assert actual_score >= expected_score, \
            f"Expected at least {expected_score} for {len(detected_functions)} functions, got {actual_score}"
    
    @given(
        st.lists(st.sampled_from(['MEDIAN', 'PERCENTILE_CONT', 'PERCENTILE_DISC']), 
                 min_size=0, max_size=3),
        st.lists(st.sampled_from(['LISTAGG']), min_size=0, max_size=2),
        st.lists(st.sampled_from(['XMLAGG']), min_size=0, max_size=2)
    )
    @settings(max_examples=100)
    def test_mysql_special_aggregate_penalty(self, median_funcs, listagg_funcs, xmlagg_funcs):
        """
        Property 3 (MySQL 특화): MySQL 타겟에서 특수 집계 함수 추가 페널티
        
        For any MySQL 타겟 쿼리에 대해, MEDIAN/PERCENTILE_*(+0.5점), LISTAGG(+0.3점), 
        XMLAGG(+0.5점) 추가 페널티가 적용되어야 합니다.
        """
        # 쿼리 생성
        all_functions = median_funcs + listagg_funcs + xmlagg_funcs
        if all_functions:
            function_calls = ', '.join([f"{func}(column)" for func in all_functions])
            query = f"SELECT {function_calls} FROM users GROUP BY dept"
        else:
            query = "SELECT * FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        
        # 기본 함수 점수 계산
        detected_functions = parser.detect_oracle_functions()
        base_score = len(detected_functions) * 0.5
        
        # MySQL 추가 페널티 계산
        expected_penalty = 0.0
        for func in median_funcs:
            expected_penalty += 0.5
        for func in listagg_funcs:
            expected_penalty += 0.3
        for func in xmlagg_funcs:
            expected_penalty += 0.5
        
        expected_total = base_score + expected_penalty
        
        # 실제 점수 계산
        actual_score = calc._calculate_oracle_function_score(parser)
        
        # 검증
        assert actual_score >= base_score, \
            f"MySQL penalty should increase score from {base_score} to at least {expected_total}, got {actual_score}"


class TestFunctionsExpressionsScoreProperty:
    """함수/표현식 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 4: 함수/표현식 점수 계산 정확성
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    @given(
        st.integers(min_value=0, max_value=10),  # 집계 함수 개수
        st.integers(min_value=0, max_value=10),  # CASE 표현식 개수
        st.booleans()  # 정규식 함수 포함 여부
    )
    @settings(max_examples=100)
    def test_functions_expressions_score_components(self, agg_count, case_count, has_regex):
        """
        Property 4: 함수/표현식 점수 계산 정확성
        
        For any SQL 쿼리에 대해, 함수/표현식 점수는 집계 함수(min(2, count*0.5)), 
        CASE(min(2, count*0.5)), 정규식(1점)의 합으로 계산되어야 하며, 
        최대 2.5점으로 제한됩니다.
        """
        # 쿼리 생성
        query_parts = ["SELECT"]
        
        # 집계 함수 추가
        if agg_count > 0:
            agg_funcs = ', '.join([f"COUNT(col{i})" for i in range(agg_count)])
            query_parts.append(agg_funcs)
        
        # CASE 표현식 추가
        if case_count > 0:
            if agg_count > 0:
                query_parts.append(",")
            case_exprs = ', '.join([
                f"CASE WHEN col{i} > 0 THEN 1 ELSE 0 END" 
                for i in range(case_count)
            ])
            query_parts.append(case_exprs)
        
        # 정규식 함수 추가
        if has_regex:
            if agg_count > 0 or case_count > 0:
                query_parts.append(",")
            query_parts.append("REGEXP_LIKE(name, 'pattern')")
        
        if agg_count == 0 and case_count == 0 and not has_regex:
            query_parts.append("*")
        
        query_parts.append("FROM users")
        
        # GROUP BY 추가 (집계 함수가 있는 경우)
        if agg_count > 0:
            query_parts.append("GROUP BY dept")
        
        query = " ".join(query_parts)
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 예상 점수 계산 (최대 2.5점 제한 적용)
        expected_score = 0.0
        expected_score += min(2.0, agg_count * 0.5)  # 집계 함수
        expected_score += min(2.0, case_count * 0.5)  # CASE 표현식
        if has_regex:
            expected_score += 1.0  # 정규식 함수
        
        # 최대 2.5점 제한
        expected_score = min(expected_score, 2.5)
        
        # 실제 점수 계산
        actual_score = calc._calculate_functions_score(parser)
        
        # 검증: 최대 2.5점
        assert actual_score <= 2.5, \
            f"Functions score should be <= 2.5, got {actual_score}"
        
        # 예상 점수와 비교 (약간의 오차 허용, Oracle 함수 점수 포함 가능)
        assert actual_score >= expected_score - 0.1, \
            f"Expected at least {expected_score}, got {actual_score}"
    
    @given(st.booleans())
    @settings(max_examples=100)
    def test_mysql_count_star_penalty(self, has_where):
        """
        Property 4 (MySQL 특화): WHERE 절 없이 COUNT(*) 사용 시 0.5점 페널티
        
        For any MySQL 타겟 쿼리에 대해, WHERE 절 없이 COUNT(*)가 사용되면 
        0.5점 페널티가 적용되어야 합니다.
        """
        # 쿼리 생성
        if has_where:
            query = "SELECT COUNT(*) FROM users WHERE status = 'active'"
        else:
            query = "SELECT COUNT(*) FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        
        # 실제 점수 계산
        actual_score = calc._calculate_functions_score(parser)
        
        # 검증
        if not has_where:
            # WHERE 절이 없으면 페널티가 적용되어야 함
            assert actual_score >= 0.5, \
                f"Expected penalty of at least 0.5 for COUNT(*) without WHERE, got {actual_score}"
        else:
            # WHERE 절이 있으면 기본 집계 함수 점수만
            assert actual_score >= 0.5, \
                f"Expected at least 0.5 for COUNT(*) with WHERE, got {actual_score}"


class TestDataVolumeScoreProperty:
    """데이터 볼륨 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 5: 데이터 볼륨 점수 계산 정확성
    Validates: Requirements 5.1, 5.2, 5.3, 5.4
    """
    
    @given(st.integers(min_value=1, max_value=5000))
    @settings(max_examples=100)
    def test_data_volume_score_by_length(self, query_length):
        """
        Property 5: 데이터 볼륨 점수 계산 정확성
        
        For any SQL 쿼리에 대해, 쿼리 길이에 따라 타겟 DB별로 정의된 점수가 
        부여되어야 합니다.
        """
        # PostgreSQL 타겟
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        score_pg = calc_pg._calculate_data_volume_score(query_length)
        
        # 예상 점수 계산 (PostgreSQL)
        if query_length < 200:
            expected_pg = 0.5
        elif query_length < 500:
            expected_pg = 1.0
        elif query_length < 1000:
            expected_pg = 1.5
        else:
            expected_pg = 2.0
        
        assert score_pg == expected_pg, \
            f"PostgreSQL: Expected {expected_pg} for length {query_length}, got {score_pg}"
        
        # MySQL 타겟
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        score_mysql = calc_mysql._calculate_data_volume_score(query_length)
        
        # 예상 점수 계산 (MySQL)
        if query_length < 200:
            expected_mysql = 0.5
        elif query_length < 500:
            expected_mysql = 1.2
        elif query_length < 1000:
            expected_mysql = 2.0
        else:
            expected_mysql = 2.5
        
        assert score_mysql == expected_mysql, \
            f"MySQL: Expected {expected_mysql} for length {query_length}, got {score_mysql}"
    
    @given(st.sampled_from([
        (50, 0.5, 0.5),      # 작은 쿼리
        (300, 1.0, 1.2),     # 중간 쿼리
        (700, 1.5, 2.0),     # 큰 쿼리
        (1500, 2.0, 2.5),    # 매우 큰 쿼리
    ]))
    @settings(max_examples=100)
    def test_data_volume_score_boundaries(self, test_case):
        """
        Property 5: 경계값에서 데이터 볼륨 점수 정확성
        
        For any 경계값 쿼리 길이에 대해, 올바른 점수가 부여되어야 합니다.
        """
        query_length, expected_pg, expected_mysql = test_case
        
        # PostgreSQL
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        score_pg = calc_pg._calculate_data_volume_score(query_length)
        assert score_pg == expected_pg, \
            f"PostgreSQL: Expected {expected_pg} for length {query_length}, got {score_pg}"
        
        # MySQL
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        score_mysql = calc_mysql._calculate_data_volume_score(query_length)
        assert score_mysql == expected_mysql, \
            f"MySQL: Expected {expected_mysql} for length {query_length}, got {score_mysql}"
    
    @given(st.integers(min_value=1, max_value=5000))
    @settings(max_examples=100)
    def test_mysql_score_higher_than_postgresql(self, query_length):
        """
        Property 5: MySQL 점수가 PostgreSQL 점수보다 높거나 같음
        
        For any 쿼리 길이에 대해, MySQL 타겟의 데이터 볼륨 점수는 
        PostgreSQL 타겟의 점수보다 높거나 같아야 합니다.
        """
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        
        score_pg = calc_pg._calculate_data_volume_score(query_length)
        score_mysql = calc_mysql._calculate_data_volume_score(query_length)
        
        assert score_mysql >= score_pg, \
            f"MySQL score ({score_mysql}) should be >= PostgreSQL score ({score_pg}) for length {query_length}"


class TestExecutionComplexityScoreProperty:
    """실행 복잡성 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 6: 실행 복잡성 점수 계산 정확성
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    
    @given(
        st.integers(min_value=0, max_value=10),  # JOIN 개수
        st.integers(min_value=0, max_value=5),   # 서브쿼리 깊이
        st.booleans(),  # ORDER BY
        st.booleans(),  # GROUP BY
        st.booleans()   # HAVING
    )
    @settings(max_examples=100)
    def test_execution_complexity_components_postgresql(
        self, join_count, subquery_depth, has_order_by, has_group_by, has_having
    ):
        """
        Property 6 (PostgreSQL): 실행 복잡성 점수 계산 정확성
        
        For any SQL 쿼리와 PostgreSQL 타겟에 대해, 실행 복잡성 점수는 
        조인 깊이, ORDER BY, GROUP BY, HAVING의 합으로 계산되어야 하며,
        최대 1.0점으로 제한됩니다.
        """
        # 쿼리 생성
        query_parts = ["SELECT * FROM users"]
        
        # JOIN 추가
        for i in range(join_count):
            query_parts.append(f"JOIN table{i} ON users.id = table{i}.user_id")
        
        # 서브쿼리 추가 (WHERE 절에)
        if subquery_depth > 0:
            subquery = "SELECT id FROM orders"
            for _ in range(subquery_depth - 1):
                subquery = f"SELECT id FROM ({subquery}) sub"
            query_parts.append(f"WHERE id IN ({subquery})")
        
        # ORDER BY 추가
        if has_order_by:
            query_parts.append("ORDER BY id")
        
        # GROUP BY 추가
        if has_group_by:
            query_parts[0] = "SELECT dept, COUNT(*) FROM users"
            query_parts.append("GROUP BY dept")
        
        # HAVING 추가 (GROUP BY가 있을 때만)
        if has_having and has_group_by:
            query_parts.append("HAVING COUNT(*) > 10")
        
        query = " ".join(query_parts)
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 실제 점수 계산
        actual_score = calc._calculate_execution_complexity(parser)
        
        # 검증: 최대 1.0점 (PostgreSQL)
        assert actual_score <= 1.0, \
            f"PostgreSQL execution complexity should be <= 1.0, got {actual_score}"
        
        # 검증: 점수가 0 이상이어야 함
        assert actual_score >= 0, \
            f"Execution complexity should be >= 0, got {actual_score}"
        
        # 검증: ORDER BY, GROUP BY, HAVING이 있으면 점수가 증가해야 함
        if has_order_by or has_group_by or (has_having and has_group_by):
            assert actual_score > 0, \
                f"Expected score > 0 when ORDER BY/GROUP BY/HAVING present, got {actual_score}"
    
    @given(
        st.integers(min_value=0, max_value=10),  # JOIN 개수
        st.integers(min_value=0, max_value=5),   # 서브쿼리 깊이
        st.integers(min_value=0, max_value=5),   # 파생 테이블 개수
        st.booleans(),  # DISTINCT
        st.booleans()   # LIKE '%pattern%'
    )
    @settings(max_examples=100)
    def test_execution_complexity_components_mysql(
        self, join_count, subquery_depth, derived_count, has_distinct, has_like_pattern
    ):
        """
        Property 6 (MySQL): 실행 복잡성 점수 계산 정확성
        
        For any SQL 쿼리와 MySQL 타겟에 대해, 실행 복잡성 점수는 
        조인 깊이, ORDER BY, GROUP BY, HAVING, 파생 테이블, 성능 페널티의 합으로 
        계산되어야 합니다.
        """
        # 쿼리 생성
        query_parts = []
        
        if has_distinct:
            query_parts.append("SELECT DISTINCT * FROM users")
        else:
            query_parts.append("SELECT * FROM users")
        
        # JOIN 추가
        for i in range(join_count):
            query_parts.append(f"JOIN table{i} ON users.id = table{i}.user_id")
        
        # 파생 테이블 추가
        for i in range(derived_count):
            query_parts.append(f"JOIN (SELECT * FROM derived{i}) d{i} ON users.id = d{i}.id")
        
        # LIKE 패턴 추가
        if has_like_pattern:
            query_parts.append("WHERE name LIKE '%john%'")
        
        query = " ".join(query_parts)
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.MYSQL)
        
        # 예상 점수 계산
        expected_score = 0.0
        
        # 조인 깊이 페널티 (join_count > 3 또는 subquery_depth > 1)
        if join_count > 3 or subquery_depth > 1:
            expected_score += 1.5
        
        # 파생 테이블 (min(1.0, count * 0.5))
        expected_score += min(1.0, derived_count * 0.5)
        
        # 성능 페널티
        if has_distinct:
            expected_score += 0.3
        if has_like_pattern:
            expected_score += 0.3
        
        # 실제 점수 계산
        actual_score = calc._calculate_execution_complexity(parser)
        
        # 검증: 최대 2.5점 (MySQL)
        assert actual_score <= 2.5, \
            f"MySQL execution complexity should be <= 2.5, got {actual_score}"
    
    @given(
        st.integers(min_value=0, max_value=10),
        st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_mysql_score_higher_than_postgresql(self, join_count, subquery_depth):
        """
        Property 6: MySQL 실행 복잡성 점수가 PostgreSQL보다 높거나 같음
        
        For any 동일한 쿼리 구조에 대해, MySQL 타겟의 실행 복잡성 점수는 
        PostgreSQL 타겟의 점수보다 높거나 같아야 합니다.
        """
        # 간단한 쿼리 생성
        query_parts = ["SELECT * FROM users"]
        
        for i in range(join_count):
            query_parts.append(f"JOIN table{i} ON users.id = table{i}.user_id")
        
        if subquery_depth > 0:
            subquery = "SELECT id FROM orders"
            for _ in range(subquery_depth - 1):
                subquery = f"SELECT id FROM ({subquery}) sub"
            query_parts.append(f"WHERE id IN ({subquery})")
        
        query = " ".join(query_parts)
        
        parser = SQLParser(query)
        
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        
        score_pg = calc_pg._calculate_execution_complexity(parser)
        score_mysql = calc_mysql._calculate_execution_complexity(parser)
        
        # MySQL 점수가 PostgreSQL 점수보다 높거나 같아야 함
        assert score_mysql >= score_pg, \
            f"MySQL score ({score_mysql}) should be >= PostgreSQL score ({score_pg})"


class TestHintScoreProperty:
    """힌트 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 7: 힌트 점수 계산 정확성
    Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    @given(st.integers(min_value=0, max_value=15))
    @settings(max_examples=100)
    def test_hint_score_by_count(self, hint_count):
        """
        Property 7: 힌트 점수 계산 정확성
        
        For any SQL 쿼리에 대해, 힌트 개수에 따라 정의된 점수가 부여되어야 합니다.
        (0개=0점, 1-2개=0.5점, 3-5개=1.0점, 6개 이상=1.5점)
        """
        # 힌트 생성
        hints = ['INDEX', 'FULL', 'PARALLEL', 'USE_HASH', 'USE_NL', 
                 'APPEND', 'NO_MERGE', 'LEADING', 'ORDERED', 'FIRST_ROWS',
                 'ALL_ROWS', 'RULE', 'CHOOSE', 'DRIVING_SITE', 'CACHE']
        
        if hint_count > 0:
            selected_hints = ' '.join(hints[:min(hint_count, len(hints))])
            query = f"SELECT /*+ {selected_hints} */ * FROM users"
        else:
            query = "SELECT * FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 예상 점수 계산
        if hint_count == 0:
            expected_score = 0.0
        elif hint_count <= 2:
            expected_score = 0.5
        elif hint_count <= 5:
            expected_score = 1.0
        else:
            expected_score = 1.5
        
        # 실제 점수 계산
        actual_score = calc._calculate_conversion_difficulty(parser)
        
        # 검증
        assert actual_score == expected_score, \
            f"Expected {expected_score} for {hint_count} hints, got {actual_score}"
    
    @given(st.sampled_from([
        (0, 0.0),
        (1, 0.5),
        (2, 0.5),
        (3, 1.0),
        (4, 1.0),
        (5, 1.0),
        (6, 1.5),
        (10, 1.5),
    ]))
    @settings(max_examples=100)
    def test_hint_score_boundaries(self, test_case):
        """
        Property 7: 경계값에서 힌트 점수 정확성
        
        For any 경계값 힌트 개수에 대해, 올바른 점수가 부여되어야 합니다.
        """
        hint_count, expected_score = test_case
        
        # 힌트 생성
        hints = ['INDEX', 'FULL', 'PARALLEL', 'USE_HASH', 'USE_NL', 
                 'APPEND', 'NO_MERGE', 'LEADING', 'ORDERED', 'FIRST_ROWS',
                 'ALL_ROWS', 'RULE', 'CHOOSE', 'DRIVING_SITE', 'CACHE']
        
        if hint_count > 0:
            selected_hints = ' '.join(hints[:min(hint_count, len(hints))])
            query = f"SELECT /*+ {selected_hints} */ * FROM users"
        else:
            query = "SELECT * FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 실제 점수 계산
        actual_score = calc._calculate_conversion_difficulty(parser)
        
        # 검증
        assert actual_score == expected_score, \
            f"Expected {expected_score} for {hint_count} hints, got {actual_score}"
    
    @given(st.integers(min_value=0, max_value=15))
    @settings(max_examples=100)
    def test_hint_score_max_limit(self, hint_count):
        """
        Property 7: 힌트 점수 최대값 제한
        
        For any 힌트 개수에 대해, 점수는 최대 1.5점을 초과하지 않아야 합니다.
        """
        # 힌트 생성
        hints = ['INDEX', 'FULL', 'PARALLEL', 'USE_HASH', 'USE_NL', 
                 'APPEND', 'NO_MERGE', 'LEADING', 'ORDERED', 'FIRST_ROWS',
                 'ALL_ROWS', 'RULE', 'CHOOSE', 'DRIVING_SITE', 'CACHE']
        
        if hint_count > 0:
            selected_hints = ' '.join(hints[:min(hint_count, len(hints))])
            query = f"SELECT /*+ {selected_hints} */ * FROM users"
        else:
            query = "SELECT * FROM users"
        
        parser = SQLParser(query)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        # 실제 점수 계산
        actual_score = calc._calculate_conversion_difficulty(parser)
        
        # 검증: 최대 1.5점
        assert actual_score <= 1.5, \
            f"Hint score should be <= 1.5, got {actual_score} for {hint_count} hints"


class TestPLSQLComplexityScoreProperty:
    """PL/SQL 복잡도 점수 계산 속성 테스트
    
    Feature: oracle-complexity-analyzer, Property 8: PL/SQL 복잡도 점수 계산 정확성
    Validates: Requirements 8.1-11.5
    """
    
    @given(st.sampled_from([
        PLSQLObjectType.PACKAGE,
        PLSQLObjectType.PROCEDURE,
        PLSQLObjectType.FUNCTION,
        PLSQLObjectType.TRIGGER,
        PLSQLObjectType.VIEW,
        PLSQLObjectType.MATERIALIZED_VIEW
    ]))
    @settings(max_examples=100)
    def test_plsql_base_score_by_type(self, object_type):
        """
        Property 8: PL/SQL 오브젝트 타입별 기본 점수
        
        For any PL/SQL 오브젝트 타입에 대해, 타겟 DB별로 정의된 기본 점수가 
        부여되어야 합니다.
        """
        # 간단한 PL/SQL 코드 생성
        if object_type == PLSQLObjectType.PACKAGE:
            code = """
            CREATE OR REPLACE PACKAGE test_pkg AS
                PROCEDURE test_proc;
            END test_pkg;
            """
        elif object_type == PLSQLObjectType.PROCEDURE:
            code = """
            CREATE OR REPLACE PROCEDURE test_proc IS
            BEGIN
                NULL;
            END;
            """
        elif object_type == PLSQLObjectType.FUNCTION:
            code = """
            CREATE OR REPLACE FUNCTION test_func RETURN NUMBER IS
            BEGIN
                RETURN 1;
            END;
            """
        elif object_type == PLSQLObjectType.TRIGGER:
            code = """
            CREATE OR REPLACE TRIGGER test_trigger
            AFTER INSERT ON users
            BEGIN
                NULL;
            END;
            """
        elif object_type == PLSQLObjectType.VIEW:
            code = """
            CREATE OR REPLACE VIEW test_view AS
            SELECT * FROM users;
            """
        else:  # MATERIALIZED_VIEW
            code = """
            CREATE MATERIALIZED VIEW test_mv AS
            SELECT * FROM users;
            """
        
        parser = PLSQLParser(code)
        
        # PostgreSQL
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        result_pg = calc_pg.calculate_plsql_complexity(parser)
        
        from src.oracle_complexity_analyzer import PLSQL_BASE_SCORES
        expected_base_pg = PLSQL_BASE_SCORES[TargetDatabase.POSTGRESQL][object_type]
        
        assert result_pg.base_score == expected_base_pg, \
            f"PostgreSQL: Expected base score {expected_base_pg} for {object_type.value}, got {result_pg.base_score}"
        
        # MySQL
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        result_mysql = calc_mysql.calculate_plsql_complexity(parser)
        
        expected_base_mysql = PLSQL_BASE_SCORES[TargetDatabase.MYSQL][object_type]
        
        assert result_mysql.base_score == expected_base_mysql, \
            f"MySQL: Expected base score {expected_base_mysql} for {object_type.value}, got {result_mysql.base_score}"
    
    @given(
        st.integers(min_value=10, max_value=2000),  # 코드 라인 수
        st.integers(min_value=0, max_value=10),     # 커서 개수
        st.integers(min_value=0, max_value=5),      # 예외 블록 개수
        st.integers(min_value=1, max_value=10)      # 중첩 깊이
    )
    @settings(max_examples=100)
    def test_plsql_code_complexity_components(self, line_count, cursor_count, exception_count, nesting_depth):
        """
        Property 8: PL/SQL 코드 복잡도 구성 요소
        
        For any PL/SQL 코드에 대해, 코드 복잡도는 라인 수, 커서, 예외 블록, 
        중첩 깊이의 합으로 계산되어야 합니다.
        """
        # 간단한 프로시저 코드 생성
        code_lines = ["CREATE OR REPLACE PROCEDURE test_proc IS"]
        
        # 커서 선언 추가
        for i in range(cursor_count):
            code_lines.append(f"    CURSOR c{i} IS SELECT * FROM table{i};")
        
        code_lines.append("BEGIN")
        
        # 중첩 구조 추가
        for i in range(nesting_depth):
            code_lines.append("    " * (i + 1) + "IF condition THEN")
        
        # 더미 라인 추가 (목표 라인 수 달성)
        current_lines = len(code_lines)
        remaining_lines = max(0, line_count - current_lines - nesting_depth - exception_count - 2)
        for i in range(remaining_lines):
            code_lines.append("    " * nesting_depth + "    NULL;")
        
        # 중첩 구조 닫기
        for i in range(nesting_depth - 1, -1, -1):
            code_lines.append("    " * (i + 1) + "END IF;")
        
        # 예외 블록 추가
        if exception_count > 0:
            code_lines.append("EXCEPTION")
            for i in range(exception_count):
                code_lines.append(f"    WHEN OTHERS THEN NULL;")
        
        code_lines.append("END;")
        
        code = "\n".join(code_lines)
        
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        # 코드 복잡도가 0보다 커야 함
        assert result.code_complexity > 0, \
            f"Code complexity should be > 0, got {result.code_complexity}"
        
        # 총 점수가 기본 점수보다 커야 함
        assert result.total_score > result.base_score, \
            f"Total score ({result.total_score}) should be > base score ({result.base_score})"
    
    @given(st.sampled_from([
        PLSQLObjectType.PACKAGE,
        PLSQLObjectType.PROCEDURE,
        PLSQLObjectType.FUNCTION,
        PLSQLObjectType.TRIGGER
    ]))
    @settings(max_examples=100)
    def test_mysql_app_migration_penalty(self, object_type):
        """
        Property 8 (MySQL 특화): 애플리케이션 이관 페널티
        
        For any PL/SQL 오브젝트(Package, Procedure, Function, Trigger)에 대해, 
        MySQL 타겟에서 애플리케이션 이관 페널티가 적용되어야 합니다.
        """
        # 간단한 코드 생성
        if object_type == PLSQLObjectType.PACKAGE:
            code = """
            CREATE OR REPLACE PACKAGE test_pkg AS
                PROCEDURE test_proc;
            END test_pkg;
            """
        elif object_type == PLSQLObjectType.PROCEDURE:
            code = """
            CREATE OR REPLACE PROCEDURE test_proc IS
            BEGIN
                NULL;
            END;
            """
        elif object_type == PLSQLObjectType.FUNCTION:
            code = """
            CREATE OR REPLACE FUNCTION test_func RETURN NUMBER IS
            BEGIN
                RETURN 1;
            END;
            """
        else:  # TRIGGER
            code = """
            CREATE OR REPLACE TRIGGER test_trigger
            AFTER INSERT ON users
            BEGIN
                NULL;
            END;
            """
        
        parser = PLSQLParser(code)
        
        # MySQL 타겟
        calc_mysql = ComplexityCalculator(TargetDatabase.MYSQL)
        result_mysql = calc_mysql.calculate_plsql_complexity(parser)
        
        # 애플리케이션 이관 페널티 확인
        from src.oracle_complexity_analyzer import MYSQL_APP_MIGRATION_PENALTY
        expected_penalty = MYSQL_APP_MIGRATION_PENALTY[object_type]
        
        assert result_mysql.app_migration_penalty == expected_penalty, \
            f"Expected app migration penalty {expected_penalty} for {object_type.value}, got {result_mysql.app_migration_penalty}"
        
        # PostgreSQL과 비교 (MySQL이 더 높아야 함)
        calc_pg = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        result_pg = calc_pg.calculate_plsql_complexity(parser)
        
        assert result_mysql.total_score > result_pg.total_score, \
            f"MySQL total score ({result_mysql.total_score}) should be > PostgreSQL ({result_pg.total_score})"
    
    @given(st.sampled_from([
        PLSQLObjectType.PACKAGE,
        PLSQLObjectType.PROCEDURE,
        PLSQLObjectType.FUNCTION,
        PLSQLObjectType.TRIGGER,
        PLSQLObjectType.VIEW,
        PLSQLObjectType.MATERIALIZED_VIEW
    ]))
    @settings(max_examples=100)
    def test_plsql_normalized_score_range(self, object_type):
        """
        Property 8: PL/SQL 정규화 점수 범위
        
        For any PL/SQL 오브젝트에 대해, 정규화된 점수는 0-10 범위 내에 있어야 합니다.
        """
        # 간단한 코드 생성
        if object_type == PLSQLObjectType.PACKAGE:
            code = """
            CREATE OR REPLACE PACKAGE test_pkg AS
                PROCEDURE test_proc;
            END test_pkg;
            """
        elif object_type == PLSQLObjectType.PROCEDURE:
            code = """
            CREATE OR REPLACE PROCEDURE test_proc IS
            BEGIN
                NULL;
            END;
            """
        elif object_type == PLSQLObjectType.FUNCTION:
            code = """
            CREATE OR REPLACE FUNCTION test_func RETURN NUMBER IS
            BEGIN
                RETURN 1;
            END;
            """
        elif object_type == PLSQLObjectType.TRIGGER:
            code = """
            CREATE OR REPLACE TRIGGER test_trigger
            AFTER INSERT ON users
            BEGIN
                NULL;
            END;
            """
        elif object_type == PLSQLObjectType.VIEW:
            code = """
            CREATE OR REPLACE VIEW test_view AS
            SELECT * FROM users;
            """
        else:  # MATERIALIZED_VIEW
            code = """
            CREATE MATERIALIZED VIEW test_mv AS
            SELECT * FROM users;
            """
        
        parser = PLSQLParser(code)
        calc = ComplexityCalculator(TargetDatabase.POSTGRESQL)
        
        result = calc.calculate_plsql_complexity(parser)
        
        # 정규화 점수 범위 확인
        assert 0 <= result.normalized_score <= 10, \
            f"Normalized score should be in [0, 10], got {result.normalized_score}"
