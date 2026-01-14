"""
SQLParser 테스트

SQL 쿼리 파싱 및 구문 요소 추출 기능을 검증합니다.
"""

import pytest
from src.parsers.sql_parser import SQLParser


class TestSQLParserBasic:
    """SQLParser 기본 기능 테스트"""
    
    def test_create_sql_parser(self):
        """SQLParser 생성 테스트"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        
        assert parser.query == "SELECT * FROM users"
        assert parser.upper_query == "SELECT * FROM USERS"
        assert parser.normalized_query == "SELECT * FROM USERS"
        
    def test_normalize_query_whitespace(self):
        """쿼리 정규화 - 공백 처리 테스트"""
        query = "SELECT  *  \n  FROM   users\t\tWHERE  id = 1"
        parser = SQLParser(query)
        
        # 여러 공백이 하나로 통합되어야 함
        assert "  " not in parser.normalized_query
        assert "\n" not in parser.normalized_query
        assert "\t" not in parser.normalized_query
        
    def test_normalize_query_comments(self):
        """쿼리 정규화 - 주석 제거 테스트"""
        query = """
        SELECT * FROM users -- 사용자 테이블
        WHERE id = 1 /* 아이디 조건 */
        """
        parser = SQLParser(query)
        
        # 주석이 제거되어야 함
        assert "--" not in parser.normalized_query
        assert "/*" not in parser.normalized_query
        assert "*/" not in parser.normalized_query
        

class TestJoinCounting:
    """JOIN 개수 계산 테스트"""
    
    def test_count_explicit_joins(self):
        """명시적 JOIN 개수 계산 테스트"""
        query = """
        SELECT * FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        LEFT JOIN products p ON o.product_id = p.id
        """
        parser = SQLParser(query)
        
        assert parser.count_joins() == 2
        
    def test_count_implicit_joins(self):
        """암시적 JOIN 개수 계산 테스트"""
        query = "SELECT * FROM users, orders, products WHERE users.id = orders.user_id"
        parser = SQLParser(query)
        
        # 쉼표 2개 = 암시적 JOIN 2개
        assert parser.count_joins() == 2
        
    def test_count_mixed_joins(self):
        """명시적 + 암시적 JOIN 혼합 테스트"""
        query = """
        SELECT * FROM users u, orders o
        LEFT JOIN products p ON o.product_id = p.id
        """
        parser = SQLParser(query)
        
        # 암시적 1개 + 명시적 1개 = 2개
        assert parser.count_joins() == 2
        
    def test_count_no_joins(self):
        """JOIN이 없는 경우 테스트"""
        query = "SELECT * FROM users WHERE id = 1"
        parser = SQLParser(query)
        
        assert parser.count_joins() == 0


class TestSubqueryDepth:
    """서브쿼리 중첩 깊이 계산 테스트"""
    
    def test_no_subquery(self):
        """서브쿼리가 없는 경우 테스트"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        
        assert parser.calculate_subquery_depth() == 0
        
    def test_single_subquery(self):
        """단일 서브쿼리 테스트"""
        query = "SELECT * FROM (SELECT * FROM users) u"
        parser = SQLParser(query)
        
        assert parser.calculate_subquery_depth() == 1
        
    def test_nested_subqueries(self):
        """중첩 서브쿼리 테스트"""
        query = """
        SELECT * FROM (
            SELECT * FROM (
                SELECT * FROM users
            ) inner_query
        ) outer_query
        """
        parser = SQLParser(query)
        
        assert parser.calculate_subquery_depth() == 2
        
    def test_where_subquery(self):
        """WHERE 절 서브쿼리 테스트"""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        parser = SQLParser(query)
        
        assert parser.calculate_subquery_depth() == 1


class TestCTECounting:
    """CTE 개수 계산 테스트"""
    
    def test_no_cte(self):
        """CTE가 없는 경우 테스트"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        
        assert parser.count_ctes() == 0
        
    def test_single_cte(self):
        """단일 CTE 테스트"""
        query = """
        WITH user_orders AS (
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            GROUP BY user_id
        )
        SELECT * FROM user_orders
        """
        parser = SQLParser(query)
        
        assert parser.count_ctes() == 1
        
    def test_multiple_ctes(self):
        """여러 CTE 테스트"""
        query = """
        WITH 
        user_orders AS (
            SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id
        ),
        user_products AS (
            SELECT user_id, COUNT(*) as product_count FROM products GROUP BY user_id
        )
        SELECT * FROM user_orders JOIN user_products USING (user_id)
        """
        parser = SQLParser(query)
        
        assert parser.count_ctes() == 2


class TestSetOperators:
    """집합 연산자 개수 계산 테스트"""
    
    def test_union(self):
        """UNION 테스트"""
        query = "SELECT * FROM users UNION SELECT * FROM customers"
        parser = SQLParser(query)
        
        assert parser.count_set_operators() == 1
        
    def test_union_all(self):
        """UNION ALL 테스트"""
        query = "SELECT * FROM users UNION ALL SELECT * FROM customers"
        parser = SQLParser(query)
        
        assert parser.count_set_operators() == 1
        
    def test_intersect(self):
        """INTERSECT 테스트"""
        query = "SELECT * FROM users INTERSECT SELECT * FROM customers"
        parser = SQLParser(query)
        
        assert parser.count_set_operators() == 1
        
    def test_minus(self):
        """MINUS 테스트"""
        query = "SELECT * FROM users MINUS SELECT * FROM customers"
        parser = SQLParser(query)
        
        assert parser.count_set_operators() == 1
        
    def test_multiple_set_operators(self):
        """여러 집합 연산자 테스트"""
        query = """
        SELECT * FROM users 
        UNION SELECT * FROM customers
        INTERSECT SELECT * FROM active_users
        """
        parser = SQLParser(query)
        
        assert parser.count_set_operators() == 2


class TestOracleFeatureDetection:
    """Oracle 특화 기능 감지 테스트"""
    
    def test_detect_rownum(self):
        """ROWNUM 감지 테스트"""
        query = "SELECT * FROM users WHERE ROWNUM <= 10"
        parser = SQLParser(query)
        
        features = parser.detect_oracle_features()
        assert 'ROWNUM' in features
        
    def test_detect_connect_by(self):
        """CONNECT BY 감지 테스트"""
        query = """
        SELECT * FROM employees
        START WITH manager_id IS NULL
        CONNECT BY PRIOR employee_id = manager_id
        """
        parser = SQLParser(query)
        
        features = parser.detect_oracle_features()
        assert 'CONNECT BY' in features
        assert 'START WITH' in features
        assert 'PRIOR' in features
        
    def test_detect_pivot(self):
        """PIVOT 감지 테스트"""
        query = """
        SELECT * FROM (
            SELECT department, job, salary FROM employees
        )
        PIVOT (
            SUM(salary) FOR job IN ('CLERK', 'MANAGER')
        )
        """
        parser = SQLParser(query)
        
        features = parser.detect_oracle_features()
        assert 'PIVOT' in features
        
    def test_detect_dual(self):
        """DUAL 테이블 감지 테스트"""
        query = "SELECT SYSDATE FROM DUAL"
        parser = SQLParser(query)
        
        features = parser.detect_oracle_features()
        assert 'DUAL' in features


class TestOracleFunctionDetection:
    """Oracle 특화 함수 감지 테스트"""
    
    def test_detect_decode(self):
        """DECODE 함수 감지 테스트"""
        query = "SELECT DECODE(status, 'A', 'Active', 'Inactive') FROM users"
        parser = SQLParser(query)
        
        functions = parser.detect_oracle_functions()
        assert 'DECODE' in functions
        
    def test_detect_nvl(self):
        """NVL 함수 감지 테스트"""
        query = "SELECT NVL(email, 'no-email') FROM users"
        parser = SQLParser(query)
        
        functions = parser.detect_oracle_functions()
        assert 'NVL' in functions
        
    def test_detect_to_char(self):
        """TO_CHAR 함수 감지 테스트"""
        query = "SELECT TO_CHAR(created_at, 'YYYY-MM-DD') FROM users"
        parser = SQLParser(query)
        
        functions = parser.detect_oracle_functions()
        assert 'TO_CHAR' in functions
        
    def test_detect_multiple_functions(self):
        """여러 Oracle 함수 감지 테스트"""
        query = """
        SELECT 
            NVL(name, 'Unknown'),
            TO_CHAR(created_at, 'YYYY-MM-DD'),
            DECODE(status, 'A', 'Active', 'Inactive')
        FROM users
        """
        parser = SQLParser(query)
        
        functions = parser.detect_oracle_functions()
        assert 'NVL' in functions
        assert 'TO_CHAR' in functions
        assert 'DECODE' in functions


class TestHintDetection:
    """힌트 감지 테스트"""
    
    def test_detect_index_hint(self):
        """INDEX 힌트 감지 테스트"""
        query = "SELECT /*+ INDEX(users idx_users_id) */ * FROM users"
        parser = SQLParser(query)
        
        hints = parser.count_hints()
        assert 'INDEX' in hints
        
    def test_detect_full_hint(self):
        """FULL 힌트 감지 테스트"""
        query = "SELECT /*+ FULL(users) */ * FROM users"
        parser = SQLParser(query)
        
        hints = parser.count_hints()
        assert 'FULL' in hints
        
    def test_detect_multiple_hints(self):
        """여러 힌트 감지 테스트"""
        query = "SELECT /*+ INDEX(u) PARALLEL(4) */ * FROM users u"
        parser = SQLParser(query)
        
        hints = parser.count_hints()
        assert 'INDEX' in hints
        assert 'PARALLEL' in hints


class TestAnalyticFunctions:
    """분석 함수 개수 계산 테스트"""
    
    def test_count_row_number(self):
        """ROW_NUMBER 함수 테스트"""
        query = "SELECT ROW_NUMBER() OVER (ORDER BY id) FROM users"
        parser = SQLParser(query)
        
        assert parser.count_analytic_functions() == 1
        
    def test_count_rank(self):
        """RANK 함수 테스트"""
        query = "SELECT RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM employees"
        parser = SQLParser(query)
        
        assert parser.count_analytic_functions() == 1
        
    def test_count_multiple_analytic_functions(self):
        """여러 분석 함수 테스트"""
        query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY id),
            RANK() OVER (ORDER BY salary),
            LAG(salary) OVER (ORDER BY id)
        FROM employees
        """
        parser = SQLParser(query)
        
        assert parser.count_analytic_functions() == 3


class TestAggregateFunctions:
    """집계 함수 개수 계산 테스트"""
    
    def test_count_basic_aggregates(self):
        """기본 집계 함수 테스트"""
        query = "SELECT COUNT(*), SUM(salary), AVG(salary) FROM employees"
        parser = SQLParser(query)
        
        assert parser.count_aggregate_functions() >= 3
        
    def test_count_listagg(self):
        """LISTAGG 함수 테스트"""
        query = "SELECT LISTAGG(name, ',') WITHIN GROUP (ORDER BY name) FROM users"
        parser = SQLParser(query)
        
        assert parser.count_aggregate_functions() >= 1


class TestCaseExpressions:
    """CASE 표현식 개수 계산 테스트"""
    
    def test_count_simple_case(self):
        """단순 CASE 표현식 테스트"""
        query = """
        SELECT 
            CASE status 
                WHEN 'A' THEN 'Active'
                ELSE 'Inactive'
            END
        FROM users
        """
        parser = SQLParser(query)
        
        assert parser.count_case_expressions() == 1
        
    def test_count_searched_case(self):
        """검색 CASE 표현식 테스트"""
        query = """
        SELECT 
            CASE 
                WHEN salary > 5000 THEN 'High'
                WHEN salary > 3000 THEN 'Medium'
                ELSE 'Low'
            END
        FROM employees
        """
        parser = SQLParser(query)
        
        assert parser.count_case_expressions() == 1
        
    def test_count_multiple_case(self):
        """여러 CASE 표현식 테스트"""
        query = """
        SELECT 
            CASE status WHEN 'A' THEN 'Active' ELSE 'Inactive' END,
            CASE WHEN salary > 5000 THEN 'High' ELSE 'Low' END
        FROM users
        """
        parser = SQLParser(query)
        
        assert parser.count_case_expressions() == 2


class TestFullscanRisk:
    """풀스캔 위험 감지 테스트"""
    
    def test_has_fullscan_risk_no_where(self):
        """WHERE 절이 없는 경우 테스트"""
        query = "SELECT * FROM users"
        parser = SQLParser(query)
        
        assert parser.has_fullscan_risk() is True
        
    def test_no_fullscan_risk_with_where(self):
        """WHERE 절이 있는 경우 테스트"""
        query = "SELECT * FROM users WHERE id = 1"
        parser = SQLParser(query)
        
        assert parser.has_fullscan_risk() is False


class TestDerivedTables:
    """파생 테이블 개수 계산 테스트"""
    
    def test_count_derived_table(self):
        """파생 테이블 테스트"""
        query = "SELECT * FROM (SELECT * FROM users) u"
        parser = SQLParser(query)
        
        assert parser.count_derived_tables() >= 1


class TestPerformancePenalties:
    """성능 페널티 요소 감지 테스트"""
    
    def test_detect_distinct(self):
        """DISTINCT 감지 테스트"""
        query = "SELECT DISTINCT name FROM users"
        parser = SQLParser(query)
        
        penalties = parser.has_performance_penalties()
        assert penalties['distinct'] is True
        
    def test_detect_or_conditions(self):
        """OR 조건 감지 테스트"""
        query = "SELECT * FROM users WHERE status = 'A' OR status = 'B' OR status = 'C' OR status = 'D'"
        parser = SQLParser(query)
        
        penalties = parser.has_performance_penalties()
        assert penalties['or_conditions'] is True
        
    def test_detect_like_pattern(self):
        """LIKE 패턴 감지 테스트"""
        query = "SELECT * FROM users WHERE name LIKE '%john%'"
        parser = SQLParser(query)
        
        penalties = parser.has_performance_penalties()
        assert penalties['like_pattern'] is True
