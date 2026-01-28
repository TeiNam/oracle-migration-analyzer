"""
PLSQLParser 단위 테스트

Requirements 8.1을 검증합니다:
- Package (Body/Spec 구분)
- Procedure
- Function
- Trigger
- View
- Materialized View
"""

import pytest
from src.parsers.plsql import PLSQLParser
from src.oracle_complexity_analyzer import PLSQLObjectType


class TestPLSQLParserObjectTypeDetection:
    """PL/SQL 오브젝트 타입 감지 테스트"""
    
    def test_detect_package_spec(self):
        """Package Spec 감지 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE emp_pkg AS
            PROCEDURE add_employee(p_name VARCHAR2);
            FUNCTION get_salary(p_id NUMBER) RETURN NUMBER;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.PACKAGE
    
    def test_detect_package_body(self):
        """Package Body 감지 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            PROCEDURE add_employee(p_name VARCHAR2) IS
            BEGIN
                INSERT INTO employees (name) VALUES (p_name);
            END;
            
            FUNCTION get_salary(p_id NUMBER) RETURN NUMBER IS
                v_salary NUMBER;
            BEGIN
                SELECT salary INTO v_salary FROM employees WHERE id = p_id;
                RETURN v_salary;
            END;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.PACKAGE
    
    def test_detect_procedure(self):
        """Procedure 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE update_salary(
            p_emp_id IN NUMBER,
            p_new_salary IN NUMBER
        ) IS
        BEGIN
            UPDATE employees
            SET salary = p_new_salary
            WHERE employee_id = p_emp_id;
            COMMIT;
        END update_salary;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.PROCEDURE
    
    def test_detect_function(self):
        """Function 감지 테스트"""
        code = """
        CREATE OR REPLACE FUNCTION calculate_bonus(
            p_salary IN NUMBER,
            p_rate IN NUMBER DEFAULT 0.1
        ) RETURN NUMBER IS
            v_bonus NUMBER;
        BEGIN
            v_bonus := p_salary * p_rate;
            RETURN v_bonus;
        END calculate_bonus;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.FUNCTION
    
    def test_detect_trigger(self):
        """Trigger 감지 테스트"""
        code = """
        CREATE OR REPLACE TRIGGER audit_salary_changes
        AFTER UPDATE OF salary ON employees
        FOR EACH ROW
        BEGIN
            INSERT INTO salary_audit (
                employee_id,
                old_salary,
                new_salary,
                change_date
            ) VALUES (
                :OLD.employee_id,
                :OLD.salary,
                :NEW.salary,
                SYSDATE
            );
        END;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.TRIGGER
    
    def test_detect_view(self):
        """View 감지 테스트"""
        code = """
        CREATE OR REPLACE VIEW employee_summary AS
        SELECT 
            e.employee_id,
            e.first_name || ' ' || e.last_name AS full_name,
            d.department_name,
            e.salary
        FROM employees e
        JOIN departments d ON e.department_id = d.department_id
        WHERE e.status = 'ACTIVE';
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.VIEW
    
    def test_detect_materialized_view(self):
        """Materialized View 감지 테스트"""
        code = """
        CREATE MATERIALIZED VIEW sales_summary
        BUILD IMMEDIATE
        REFRESH FAST ON COMMIT
        AS
        SELECT 
            product_id,
            SUM(quantity) AS total_quantity,
            SUM(amount) AS total_amount
        FROM sales
        GROUP BY product_id;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.MATERIALIZED_VIEW
    
    def test_detect_package_without_or_replace(self):
        """OR REPLACE 없는 Package 감지 테스트"""
        code = """
        CREATE PACKAGE simple_pkg AS
            PROCEDURE test_proc;
        END simple_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.PACKAGE
    
    def test_detect_with_comments(self):
        """주석이 포함된 코드에서 오브젝트 타입 감지 테스트"""
        code = """
        -- This is a procedure to update employee records
        /* Multi-line comment
           explaining the procedure */
        CREATE OR REPLACE PROCEDURE update_employee(
            p_id NUMBER,
            p_name VARCHAR2
        ) IS
        BEGIN
            -- Update the employee name
            UPDATE employees SET name = p_name WHERE id = p_id;
        END;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.PROCEDURE
    
    def test_detect_case_insensitive(self):
        """대소문자 구분 없이 감지 테스트"""
        code = """
        create or replace function get_total(p_id number) return number is
            v_total number;
        begin
            select sum(amount) into v_total from orders where customer_id = p_id;
            return v_total;
        end;
        """
        parser = PLSQLParser(code)
        assert parser.detect_object_type() == PLSQLObjectType.FUNCTION
    
    def test_invalid_code_raises_error(self):
        """유효하지 않은 코드에서 오류 발생 테스트"""
        code = """
        SELECT * FROM employees;
        """
        parser = PLSQLParser(code)
        with pytest.raises(ValueError, match="PL/SQL 오브젝트 타입을 감지할 수 없습니다"):
            parser.detect_object_type()
    
    def test_empty_code_raises_error(self):
        """빈 코드에서 오류 발생 테스트"""
        code = ""
        parser = PLSQLParser(code)
        with pytest.raises(ValueError, match="PL/SQL 오브젝트 타입을 감지할 수 없습니다"):
            parser.detect_object_type()


class TestPLSQLParserNormalization:
    """코드 정규화 테스트"""
    
    def test_normalize_removes_single_line_comments(self):
        """한 줄 주석 제거 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            -- This is a comment
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        normalized = parser._normalized_code
        assert '--' not in normalized
        assert 'This is a comment' not in normalized
    
    def test_normalize_removes_multi_line_comments(self):
        """여러 줄 주석 제거 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            /* This is a
               multi-line
               comment */
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        normalized = parser._normalized_code
        assert 'multi-line' not in normalized
    
    def test_normalize_consolidates_whitespace(self):
        """공백 통합 테스트"""
        code = """
        CREATE    OR    REPLACE    PROCEDURE    test_proc    IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        normalized = parser._normalized_code
        # 여러 공백이 하나로 통합되어야 함
        assert '    ' not in normalized
        assert 'CREATE OR REPLACE PROCEDURE' in normalized


class TestPLSQLParserCodeMetrics:
    """코드 메트릭 계산 테스트 (Requirements 8.2, 8.3, 8.4, 8.5)"""
    
    def test_count_lines_simple(self):
        """간단한 코드의 라인 수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        line_count = parser.count_lines()
        # 실제 코드 라인: CREATE, BEGIN, NULL, END = 4줄
        assert line_count == 4
    
    def test_count_lines_with_comments(self):
        """주석이 포함된 코드의 라인 수 계산 테스트"""
        code = """
        -- This is a comment
        CREATE PROCEDURE test_proc IS
        BEGIN
            -- Another comment
            NULL;
            /* Multi-line
               comment */
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        line_count = parser.count_lines()
        # 주석 제외: CREATE, BEGIN, NULL, NULL, END = 5줄
        assert line_count == 5
    
    def test_count_lines_with_blank_lines(self):
        """빈 줄이 포함된 코드의 라인 수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        
        BEGIN
        
            NULL;
            
        END;
        """
        parser = PLSQLParser(code)
        line_count = parser.count_lines()
        # 빈 줄 제외: CREATE, BEGIN, NULL, END = 4줄
        assert line_count == 4
    
    def test_count_lines_complex(self):
        """복잡한 코드의 라인 수 계산 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE update_salary(
            p_emp_id IN NUMBER,
            p_new_salary IN NUMBER
        ) IS
            v_old_salary NUMBER;
        BEGIN
            SELECT salary INTO v_old_salary
            FROM employees
            WHERE employee_id = p_emp_id;
            
            UPDATE employees
            SET salary = p_new_salary
            WHERE employee_id = p_emp_id;
            
            COMMIT;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20001, 'Employee not found');
        END update_salary;
        """
        parser = PLSQLParser(code)
        line_count = parser.count_lines()
        # 실제 코드 라인 수 확인 (빈 줄 제외)
        assert line_count > 10
    
    def test_count_cursors_explicit(self):
        """명시적 커서 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            CURSOR emp_cursor IS
                SELECT * FROM employees;
            CURSOR dept_cursor IS
                SELECT * FROM departments;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        cursor_count = parser.count_cursors()
        assert cursor_count == 2
    
    def test_count_cursors_implicit(self):
        """암시적 커서 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            FOR emp_rec IN (SELECT * FROM employees) LOOP
                DBMS_OUTPUT.PUT_LINE(emp_rec.name);
            END LOOP;
            
            FOR dept_rec IN (SELECT * FROM departments) LOOP
                DBMS_OUTPUT.PUT_LINE(dept_rec.name);
            END LOOP;
        END;
        """
        parser = PLSQLParser(code)
        cursor_count = parser.count_cursors()
        assert cursor_count == 2
    
    def test_count_cursors_mixed(self):
        """명시적 + 암시적 커서 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            CURSOR emp_cursor IS
                SELECT * FROM employees;
        BEGIN
            FOR emp_rec IN emp_cursor LOOP
                DBMS_OUTPUT.PUT_LINE(emp_rec.name);
            END LOOP;
            
            FOR dept_rec IN (SELECT * FROM departments) LOOP
                DBMS_OUTPUT.PUT_LINE(dept_rec.name);
            END LOOP;
        END;
        """
        parser = PLSQLParser(code)
        cursor_count = parser.count_cursors()
        # 명시적 커서 1개 + 암시적 커서 루프 2개 = 3개
        assert cursor_count == 3
    
    def test_count_cursors_none(self):
        """커서가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        cursor_count = parser.count_cursors()
        assert cursor_count == 0
    
    def test_count_exception_blocks_single(self):
        """단일 예외 블록 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            NULL;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                NULL;
        END;
        """
        parser = PLSQLParser(code)
        exception_count = parser.count_exception_blocks()
        assert exception_count == 1
    
    def test_count_exception_blocks_multiple(self):
        """여러 예외 블록 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            BEGIN
                NULL;
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    NULL;
            END;
            
            BEGIN
                NULL;
            EXCEPTION
                WHEN OTHERS THEN
                    NULL;
            END;
        EXCEPTION
            WHEN OTHERS THEN
                NULL;
        END;
        """
        parser = PLSQLParser(code)
        exception_count = parser.count_exception_blocks()
        assert exception_count == 3
    
    def test_count_exception_blocks_none(self):
        """예외 블록이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        exception_count = parser.count_exception_blocks()
        assert exception_count == 0
    
    def test_calculate_nesting_depth_simple(self):
        """간단한 중첩 깊이 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            IF condition THEN
                NULL;
            END IF;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) + IF(2) = 최대 깊이 2
        assert depth == 2
    
    def test_calculate_nesting_depth_nested_if(self):
        """중첩된 IF 문의 깊이 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            IF condition1 THEN
                IF condition2 THEN
                    IF condition3 THEN
                        NULL;
                    END IF;
                END IF;
            END IF;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) + IF(2) + IF(3) + IF(4) = 최대 깊이 4
        assert depth == 4
    
    def test_calculate_nesting_depth_loop(self):
        """LOOP 문의 중첩 깊이 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            LOOP
                IF condition THEN
                    EXIT;
                END IF;
            END LOOP;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) + LOOP(2) + IF(3) = 최대 깊이 3
        assert depth == 3
    
    def test_calculate_nesting_depth_for_loop(self):
        """FOR LOOP 문의 중첩 깊이 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            FOR i IN 1..10 LOOP
                FOR j IN 1..10 LOOP
                    NULL;
                END LOOP;
            END LOOP;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) + FOR(2) + LOOP(3) + FOR(4) + LOOP(5) = 최대 깊이 5
        # FOR와 LOOP이 각각 카운트됨
        assert depth == 5
    
    def test_calculate_nesting_depth_complex(self):
        """복잡한 중첩 구조의 깊이 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            FOR i IN 1..10 LOOP
                IF i > 5 THEN
                    WHILE condition LOOP
                        BEGIN
                            CASE variable
                                WHEN 1 THEN
                                    NULL;
                            END CASE;
                        END;
                    END LOOP;
                END IF;
            END LOOP;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) + FOR(2) + IF(3) + WHILE(4) + BEGIN(5) + CASE(6) = 최대 깊이 6
        assert depth >= 5
    
    def test_calculate_nesting_depth_no_nesting(self):
        """중첩이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        depth = parser.calculate_nesting_depth()
        # BEGIN(1) = 최대 깊이 1
        assert depth == 1


class TestPLSQLParserBulkOperations:
    """BULK 연산 감지 테스트 (Requirements 9.4)"""
    
    def test_count_bulk_collect(self):
        """BULK COLLECT 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_array IS TABLE OF employees%ROWTYPE;
            v_emps emp_array;
        BEGIN
            SELECT * BULK COLLECT INTO v_emps FROM employees;
        END;
        """
        parser = PLSQLParser(code)
        bulk_count = parser.count_bulk_operations()
        assert bulk_count == 1
    
    def test_count_forall(self):
        """FORALL 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE id_array IS TABLE OF NUMBER;
            v_ids id_array := id_array(1, 2, 3);
        BEGIN
            FORALL i IN v_ids.FIRST..v_ids.LAST
                DELETE FROM employees WHERE employee_id = v_ids(i);
        END;
        """
        parser = PLSQLParser(code)
        bulk_count = parser.count_bulk_operations()
        assert bulk_count == 1
    
    def test_count_bulk_operations_multiple(self):
        """여러 BULK 연산 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_array IS TABLE OF employees%ROWTYPE;
            TYPE id_array IS TABLE OF NUMBER;
            v_emps emp_array;
            v_ids id_array;
        BEGIN
            SELECT * BULK COLLECT INTO v_emps FROM employees;
            SELECT employee_id BULK COLLECT INTO v_ids FROM employees;
            
            FORALL i IN v_ids.FIRST..v_ids.LAST
                UPDATE employees SET salary = salary * 1.1 WHERE employee_id = v_ids(i);
        END;
        """
        parser = PLSQLParser(code)
        bulk_count = parser.count_bulk_operations()
        assert bulk_count == 3  # BULK COLLECT 2개 + FORALL 1개
    
    def test_count_bulk_operations_none(self):
        """BULK 연산이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        bulk_count = parser.count_bulk_operations()
        assert bulk_count == 0


class TestPLSQLParserDynamicSQL:
    """동적 SQL 감지 테스트 (Requirements 9.3)"""
    
    def test_count_dynamic_sql_single(self):
        """단일 동적 SQL 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_table_name VARCHAR2) IS
            v_sql VARCHAR2(1000);
        BEGIN
            v_sql := 'SELECT COUNT(*) FROM ' || p_table_name;
            EXECUTE IMMEDIATE v_sql;
        END;
        """
        parser = PLSQLParser(code)
        dynamic_count = parser.count_dynamic_sql()
        assert dynamic_count == 1
    
    def test_count_dynamic_sql_multiple(self):
        """여러 동적 SQL 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_sql VARCHAR2(1000);
            v_count NUMBER;
        BEGIN
            v_sql := 'SELECT COUNT(*) FROM employees';
            EXECUTE IMMEDIATE v_sql INTO v_count;
            
            v_sql := 'UPDATE employees SET salary = salary * 1.1';
            EXECUTE IMMEDIATE v_sql;
            
            EXECUTE IMMEDIATE 'DELETE FROM temp_table';
        END;
        """
        parser = PLSQLParser(code)
        dynamic_count = parser.count_dynamic_sql()
        assert dynamic_count == 3
    
    def test_count_dynamic_sql_with_using(self):
        """USING 절이 있는 동적 SQL 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_id NUMBER) IS
            v_sql VARCHAR2(1000);
        BEGIN
            v_sql := 'UPDATE employees SET salary = :1 WHERE employee_id = :2';
            EXECUTE IMMEDIATE v_sql USING 5000, p_id;
        END;
        """
        parser = PLSQLParser(code)
        dynamic_count = parser.count_dynamic_sql()
        assert dynamic_count == 1
    
    def test_count_dynamic_sql_none(self):
        """동적 SQL이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        dynamic_count = parser.count_dynamic_sql()
        assert dynamic_count == 0


class TestPLSQLParserPackageCalls:
    """패키지 호출 감지 테스트 (Requirements 9.1)"""
    
    def test_count_package_calls_single(self):
        """단일 패키지 호출 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            DBMS_OUTPUT.PUT_LINE('Hello');
        END;
        """
        parser = PLSQLParser(code)
        package_count = parser.count_package_calls()
        assert package_count == 1
    
    def test_count_package_calls_multiple(self):
        """여러 패키지 호출 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            DBMS_OUTPUT.PUT_LINE('Hello');
            UTL_FILE.PUT_LINE(v_file, 'Data');
            DBMS_SCHEDULER.CREATE_JOB('job1', 'proc1');
        END;
        """
        parser = PLSQLParser(code)
        package_count = parser.count_package_calls()
        assert package_count == 3
    
    def test_count_package_calls_custom_package(self):
        """사용자 정의 패키지 호출 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            EMP_PKG.ADD_EMPLOYEE('John');
            DEPT_PKG.UPDATE_DEPARTMENT(10);
            SALARY_PKG.CALCULATE_BONUS(1000);
        END;
        """
        parser = PLSQLParser(code)
        package_count = parser.count_package_calls()
        assert package_count == 3
    
    def test_count_package_calls_with_semicolon(self):
        """세미콜론으로 끝나는 패키지 호출 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_result NUMBER;
        BEGIN
            v_result := MATH_PKG.CALCULATE;
        END;
        """
        parser = PLSQLParser(code)
        package_count = parser.count_package_calls()
        assert package_count >= 1
    
    def test_count_package_calls_none(self):
        """패키지 호출이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        package_count = parser.count_package_calls()
        assert package_count == 0


class TestPLSQLParserDBLinks:
    """DB Link 감지 테스트 (Requirements 9.2)"""
    
    def test_count_dblinks_single(self):
        """단일 DB Link 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            INSERT INTO local_table
            SELECT * FROM remote_table@remote_db;
        END;
        """
        parser = PLSQLParser(code)
        dblink_count = parser.count_dblinks()
        assert dblink_count == 1
    
    def test_count_dblinks_multiple(self):
        """여러 DB Link 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            INSERT INTO local_table
            SELECT e.*, d.department_name
            FROM employees@remote_db1 e
            JOIN departments@remote_db2 d ON e.dept_id = d.dept_id;
        END;
        """
        parser = PLSQLParser(code)
        dblink_count = parser.count_dblinks()
        assert dblink_count == 2
    
    def test_count_dblinks_with_domain(self):
        """도메인이 포함된 DB Link 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SELECT * FROM employees@remote_db.example.com;
        END;
        """
        parser = PLSQLParser(code)
        dblink_count = parser.count_dblinks()
        assert dblink_count == 1
    
    def test_count_dblinks_in_update(self):
        """UPDATE 문에서 DB Link 사용 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees@remote_db
            SET salary = salary * 1.1
            WHERE department_id = 10;
        END;
        """
        parser = PLSQLParser(code)
        dblink_count = parser.count_dblinks()
        assert dblink_count == 1
    
    def test_count_dblinks_none(self):
        """DB Link가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SELECT * FROM employees;
        END;
        """
        parser = PLSQLParser(code)
        dblink_count = parser.count_dblinks()
        assert dblink_count == 0


class TestPLSQLParserAdvancedFeatures:
    """고급 기능 감지 테스트 (Requirements 9.5)"""
    
    def test_detect_pipelined_function(self):
        """PIPELINED 함수 감지 테스트"""
        code = """
        CREATE OR REPLACE FUNCTION get_employees
        RETURN emp_table_type PIPELINED IS
        BEGIN
            FOR emp_rec IN (SELECT * FROM employees) LOOP
                PIPE ROW(emp_rec);
            END LOOP;
            RETURN;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'PIPELINED' in features
    
    def test_detect_ref_cursor(self):
        """REF CURSOR 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE get_employees(
            p_cursor OUT SYS_REFCURSOR
        ) IS
            TYPE emp_cursor_type IS REF CURSOR;
            v_cursor emp_cursor_type;
        BEGIN
            OPEN p_cursor FOR SELECT * FROM employees;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'REF CURSOR' in features
    
    def test_detect_autonomous_transaction(self):
        """AUTONOMOUS_TRANSACTION 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE log_error(
            p_error_msg VARCHAR2
        ) IS
            PRAGMA AUTONOMOUS_TRANSACTION;
        BEGIN
            INSERT INTO error_log (error_msg, log_date)
            VALUES (p_error_msg, SYSDATE);
            COMMIT;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'AUTONOMOUS_TRANSACTION' in features
        assert 'PRAGMA' in features
    
    def test_detect_pragma(self):
        """PRAGMA 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE test_proc IS
            PRAGMA SERIALLY_REUSABLE;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'PRAGMA' in features
    
    def test_detect_object_type(self):
        """OBJECT TYPE 감지 테스트"""
        code = """
        CREATE OR REPLACE TYPE employee_type AS OBJECT (
            employee_id NUMBER,
            first_name VARCHAR2(50),
            last_name VARCHAR2(50),
            salary NUMBER
        );
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'OBJECT TYPE' in features
    
    def test_detect_varray(self):
        """VARRAY 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE test_proc IS
            TYPE name_array IS VARRAY(10) OF VARCHAR2(50);
            v_names name_array := name_array('John', 'Jane', 'Bob');
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'VARRAY' in features
    
    def test_detect_nested_table(self):
        """NESTED TABLE 감지 테스트"""
        code = """
        CREATE OR REPLACE PROCEDURE test_proc IS
            TYPE emp_table IS TABLE OF employees%ROWTYPE;
            v_emps emp_table := emp_table();
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'NESTED TABLE' in features
    
    def test_detect_multiple_advanced_features(self):
        """여러 고급 기능 감지 테스트"""
        code = """
        CREATE OR REPLACE FUNCTION get_data
        RETURN data_table PIPELINED IS
            TYPE ref_cur IS REF CURSOR;
            v_cursor ref_cur;
            PRAGMA AUTONOMOUS_TRANSACTION;
        BEGIN
            PIPE ROW(data_rec);
            RETURN;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert 'PIPELINED' in features
        assert 'REF CURSOR' in features
        assert 'PRAGMA' in features
        assert 'AUTONOMOUS_TRANSACTION' in features
    
    def test_detect_no_advanced_features(self):
        """고급 기능이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE simple_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        features = parser.detect_advanced_features()
        assert len(features) == 0


class TestPLSQLParserExternalDependencies:
    """외부 의존성 감지 테스트 (Requirements 10.6)"""
    
    def test_detect_utl_file(self):
        """UTL_FILE 감지 테스트"""
        code = """
        CREATE PROCEDURE export_data IS
            v_file UTL_FILE.FILE_TYPE;
        BEGIN
            v_file := UTL_FILE.FOPEN('DATA_DIR', 'output.txt', 'W');
            UTL_FILE.PUT_LINE(v_file, 'Hello World');
            UTL_FILE.FCLOSE(v_file);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'UTL_FILE' in deps
    
    def test_detect_utl_http(self):
        """UTL_HTTP 감지 테스트"""
        code = """
        CREATE PROCEDURE call_api IS
            v_request UTL_HTTP.REQ;
            v_response UTL_HTTP.RESP;
        BEGIN
            v_request := UTL_HTTP.BEGIN_REQUEST('http://api.example.com');
            v_response := UTL_HTTP.GET_RESPONSE(v_request);
            UTL_HTTP.END_RESPONSE(v_response);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'UTL_HTTP' in deps
    
    def test_detect_utl_mail(self):
        """UTL_MAIL 감지 테스트"""
        code = """
        CREATE PROCEDURE send_email IS
        BEGIN
            UTL_MAIL.SEND(
                sender => 'sender@example.com',
                recipients => 'recipient@example.com',
                subject => 'Test Email',
                message => 'This is a test email'
            );
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'UTL_MAIL' in deps
    
    def test_detect_utl_smtp(self):
        """UTL_SMTP 감지 테스트"""
        code = """
        CREATE PROCEDURE send_smtp_email IS
            v_connection UTL_SMTP.CONNECTION;
        BEGIN
            v_connection := UTL_SMTP.OPEN_CONNECTION('smtp.example.com', 25);
            UTL_SMTP.QUIT(v_connection);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'UTL_SMTP' in deps
    
    def test_detect_dbms_scheduler(self):
        """DBMS_SCHEDULER 감지 테스트"""
        code = """
        CREATE PROCEDURE create_job IS
        BEGIN
            DBMS_SCHEDULER.CREATE_JOB(
                job_name => 'DAILY_JOB',
                job_type => 'PLSQL_BLOCK',
                job_action => 'BEGIN update_stats; END;',
                start_date => SYSDATE,
                repeat_interval => 'FREQ=DAILY',
                enabled => TRUE
            );
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_SCHEDULER' in deps
    
    def test_detect_dbms_job(self):
        """DBMS_JOB 감지 테스트"""
        code = """
        CREATE PROCEDURE schedule_job IS
            v_job_id NUMBER;
        BEGIN
            DBMS_JOB.SUBMIT(
                job => v_job_id,
                what => 'update_stats;',
                next_date => SYSDATE + 1
            );
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_JOB' in deps
    
    def test_detect_dbms_lob(self):
        """DBMS_LOB 감지 테스트"""
        code = """
        CREATE PROCEDURE process_clob(p_clob IN OUT CLOB) IS
            v_length NUMBER;
        BEGIN
            v_length := DBMS_LOB.GETLENGTH(p_clob);
            DBMS_LOB.TRIM(p_clob, v_length / 2);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_LOB' in deps
    
    def test_detect_dbms_output(self):
        """DBMS_OUTPUT 감지 테스트"""
        code = """
        CREATE PROCEDURE debug_proc IS
        BEGIN
            DBMS_OUTPUT.PUT_LINE('Debug message');
            DBMS_OUTPUT.ENABLE(1000000);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_OUTPUT' in deps
    
    def test_detect_dbms_crypto(self):
        """DBMS_CRYPTO 감지 테스트"""
        code = """
        CREATE FUNCTION encrypt_data(p_data VARCHAR2) RETURN RAW IS
            v_encrypted RAW(2000);
        BEGIN
            v_encrypted := DBMS_CRYPTO.ENCRYPT(
                src => UTL_RAW.CAST_TO_RAW(p_data),
                typ => DBMS_CRYPTO.ENCRYPT_AES256
            );
            RETURN v_encrypted;
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_CRYPTO' in deps
    
    def test_detect_dbms_sql(self):
        """DBMS_SQL 감지 테스트"""
        code = """
        CREATE PROCEDURE dynamic_query IS
            v_cursor INTEGER;
            v_result INTEGER;
        BEGIN
            v_cursor := DBMS_SQL.OPEN_CURSOR;
            DBMS_SQL.PARSE(v_cursor, 'SELECT * FROM employees', DBMS_SQL.NATIVE);
            v_result := DBMS_SQL.EXECUTE(v_cursor);
            DBMS_SQL.CLOSE_CURSOR(v_cursor);
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'DBMS_SQL' in deps
    
    def test_detect_multiple_external_dependencies(self):
        """여러 외부 의존성 감지 테스트"""
        code = """
        CREATE PROCEDURE complex_proc IS
            v_file UTL_FILE.FILE_TYPE;
        BEGIN
            DBMS_OUTPUT.PUT_LINE('Starting process');
            v_file := UTL_FILE.FOPEN('DIR', 'file.txt', 'W');
            UTL_HTTP.BEGIN_REQUEST('http://api.example.com');
            DBMS_SCHEDULER.CREATE_JOB('job1', 'proc1');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert 'UTL_FILE' in deps
        assert 'DBMS_OUTPUT' in deps
        assert 'UTL_HTTP' in deps
        assert 'DBMS_SCHEDULER' in deps
        assert len(deps) == 4
    
    def test_detect_no_external_dependencies(self):
        """외부 의존성이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE simple_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_external_dependencies()
        assert len(deps) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestPLSQLParserTransactionControl:
    """트랜잭션 제어 감지 테스트 (Requirements 10.1)"""
    
    def test_has_transaction_control_savepoint(self):
        """SAVEPOINT 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SAVEPOINT sp1;
            UPDATE employees SET salary = salary * 1.1;
            SAVEPOINT sp2;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['savepoint'] is True
    
    def test_has_transaction_control_rollback(self):
        """ROLLBACK 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
            ROLLBACK;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['rollback'] is True
    
    def test_has_transaction_control_rollback_to_savepoint(self):
        """ROLLBACK TO SAVEPOINT 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SAVEPOINT sp1;
            UPDATE employees SET salary = salary * 1.1;
            ROLLBACK TO SAVEPOINT sp1;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['rollback_to_savepoint'] is True
        assert tc['savepoint'] is True
    
    def test_has_transaction_control_commit(self):
        """COMMIT 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
            COMMIT;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['commit'] is True
    
    def test_has_transaction_control_all(self):
        """모든 트랜잭션 제어 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SAVEPOINT sp1;
            UPDATE employees SET salary = salary * 1.1;
            IF error_occurred THEN
                ROLLBACK TO sp1;
            ELSE
                COMMIT;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                ROLLBACK;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['savepoint'] is True
        assert tc['rollback'] is True
        assert tc['rollback_to_savepoint'] is True
        assert tc['commit'] is True
    
    def test_has_transaction_control_none(self):
        """트랜잭션 제어가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            SELECT * FROM employees;
        END;
        """
        parser = PLSQLParser(code)
        tc = parser.has_transaction_control()
        assert tc['savepoint'] is False
        assert tc['rollback'] is False
        assert tc['rollback_to_savepoint'] is False
        assert tc['commit'] is False


class TestPLSQLParserPackageVariables:
    """패키지 변수 감지 테스트 (Requirements 10.5)"""
    
    def test_has_package_variables_in_spec(self):
        """Package Spec에서 패키지 변수 감지 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE emp_pkg AS
            g_max_salary NUMBER := 100000;
            g_department_name VARCHAR2(50);
            
            PROCEDURE add_employee(p_name VARCHAR2);
            FUNCTION get_salary(p_id NUMBER) RETURN NUMBER;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.has_package_variables() is True
    
    def test_has_package_variables_in_body(self):
        """Package Body에서 패키지 변수 감지 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            g_counter INTEGER := 0;
            g_last_update DATE;
            
            PROCEDURE add_employee(p_name VARCHAR2) IS
            BEGIN
                g_counter := g_counter + 1;
                INSERT INTO employees (name) VALUES (p_name);
            END;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.has_package_variables() is True
    
    def test_has_package_variables_multiple_types(self):
        """여러 타입의 패키지 변수 감지 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE config_pkg AS
            g_app_name VARCHAR2(100) := 'MyApp';
            g_version NUMBER := 1.0;
            g_start_date DATE := SYSDATE;
            g_debug_mode BOOLEAN := FALSE;
            g_max_records PLS_INTEGER := 1000;
            
            PROCEDURE init;
        END config_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.has_package_variables() is True
    
    def test_has_package_variables_not_package(self):
        """Package가 아닌 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_local_var NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        assert parser.has_package_variables() is False
    
    def test_has_package_variables_no_variables(self):
        """패키지 변수가 없는 Package 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE emp_pkg AS
            PROCEDURE add_employee(p_name VARCHAR2);
            FUNCTION get_salary(p_id NUMBER) RETURN NUMBER;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        assert parser.has_package_variables() is False


class TestPLSQLParserContextDependencies:
    """컨텍스트 의존성 감지 테스트 (Requirements 10.4)"""
    
    def test_detect_sys_context(self):
        """SYS_CONTEXT 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_username VARCHAR2(100);
        BEGIN
            v_username := SYS_CONTEXT('USERENV', 'SESSION_USER');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'SYS_CONTEXT' in deps
    
    def test_detect_userenv(self):
        """USERENV 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_sid NUMBER;
        BEGIN
            v_sid := USERENV('SESSIONID');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'USERENV' in deps
    
    def test_detect_global_temporary_table(self):
        """글로벌 임시 테이블 감지 테스트"""
        code = """
        CREATE GLOBAL TEMPORARY TABLE temp_employees (
            employee_id NUMBER,
            name VARCHAR2(100)
        ) ON COMMIT DELETE ROWS;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'GLOBAL_TEMPORARY_TABLE' in deps
    
    def test_detect_dbms_session(self):
        """DBMS_SESSION 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            DBMS_SESSION.SET_NLS('NLS_DATE_FORMAT', 'YYYY-MM-DD');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'DBMS_SESSION' in deps
    
    def test_detect_dbms_application_info(self):
        """DBMS_APPLICATION_INFO 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            DBMS_APPLICATION_INFO.SET_MODULE('MyApp', 'Processing');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'DBMS_APPLICATION_INFO' in deps
    
    def test_detect_multiple_context_dependencies(self):
        """여러 컨텍스트 의존성 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_user VARCHAR2(100);
        BEGIN
            v_user := SYS_CONTEXT('USERENV', 'SESSION_USER');
            DBMS_SESSION.SET_NLS('NLS_LANGUAGE', 'AMERICAN');
            DBMS_APPLICATION_INFO.SET_MODULE('MyApp', 'Init');
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert 'SYS_CONTEXT' in deps
        assert 'DBMS_SESSION' in deps
        assert 'DBMS_APPLICATION_INFO' in deps
    
    def test_detect_no_context_dependencies(self):
        """컨텍스트 의존성이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        deps = parser.detect_context_dependencies()
        assert len(deps) == 0


class TestPLSQLParserCodeStructure:
    """PL/SQL 코드 구조 분석 테스트 (Requirements 8.1)"""
    
    def test_count_procedures_in_package(self):
        """패키지 내 프로시저 개수 계산 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            PROCEDURE add_employee(p_name VARCHAR2) IS
            BEGIN
                INSERT INTO employees (name) VALUES (p_name);
            END;
            
            PROCEDURE update_employee(p_id NUMBER, p_name VARCHAR2) IS
            BEGIN
                UPDATE employees SET name = p_name WHERE id = p_id;
            END;
            
            PROCEDURE delete_employee(p_id NUMBER) IS
            BEGIN
                DELETE FROM employees WHERE id = p_id;
            END;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        count = parser.count_procedures_in_package()
        assert count == 3
    
    def test_count_functions_in_package(self):
        """패키지 내 함수 개수 계산 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY math_pkg AS
            FUNCTION add_numbers(p_a NUMBER, p_b NUMBER) RETURN NUMBER IS
            BEGIN
                RETURN p_a + p_b;
            END;
            
            FUNCTION multiply_numbers(p_a NUMBER, p_b NUMBER) RETURN NUMBER IS
            BEGIN
                RETURN p_a * p_b;
            END;
        END math_pkg;
        """
        parser = PLSQLParser(code)
        count = parser.count_functions_in_package()
        assert count == 2
    
    def test_count_procedures_and_functions_in_package(self):
        """패키지 내 프로시저와 함수 개수 계산 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            PROCEDURE add_employee(p_name VARCHAR2) IS
            BEGIN
                INSERT INTO employees (name) VALUES (p_name);
            END;
            
            FUNCTION get_salary(p_id NUMBER) RETURN NUMBER IS
                v_salary NUMBER;
            BEGIN
                SELECT salary INTO v_salary FROM employees WHERE id = p_id;
                RETURN v_salary;
            END;
            
            PROCEDURE update_salary(p_id NUMBER, p_salary NUMBER) IS
            BEGIN
                UPDATE employees SET salary = p_salary WHERE id = p_id;
            END;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        proc_count = parser.count_procedures_in_package()
        func_count = parser.count_functions_in_package()
        assert proc_count == 2
        assert func_count == 1
    
    def test_count_procedures_not_package(self):
        """Package가 아닌 경우 프로시저 개수 테스트"""
        code = """
        CREATE PROCEDURE standalone_proc IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_procedures_in_package()
        assert count == 0
    
    def test_analyze_parameters_in_out(self):
        """IN/OUT 파라미터 분석 테스트"""
        code = """
        CREATE PROCEDURE test_proc(
            p_in_param IN NUMBER,
            p_out_param OUT VARCHAR2,
            p_inout_param IN OUT DATE
        ) IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        params = parser.analyze_parameters()
        assert params['total'] == 3
        assert params['in'] == 1
        assert params['out'] == 1
        assert params['in_out'] == 1
    
    def test_analyze_parameters_default_in(self):
        """기본값 IN 파라미터 분석 테스트"""
        code = """
        CREATE PROCEDURE test_proc(
            p_param1 NUMBER,
            p_param2 VARCHAR2,
            p_param3 IN DATE
        ) IS
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        params = parser.analyze_parameters()
        assert params['total'] == 3
        assert params['in'] == 3
        assert params['out'] == 0
        assert params['in_out'] == 0
    
    def test_analyze_parameters_function(self):
        """함수 파라미터 분석 테스트"""
        code = """
        CREATE FUNCTION calculate_bonus(
            p_salary IN NUMBER,
            p_rate IN NUMBER,
            p_result OUT NUMBER
        ) RETURN NUMBER IS
        BEGIN
            p_result := p_salary * p_rate;
            RETURN p_result;
        END;
        """
        parser = PLSQLParser(code)
        params = parser.analyze_parameters()
        assert params['total'] == 3
        assert params['in'] == 2
        assert params['out'] == 1
    
    def test_analyze_parameters_multiple_procedures(self):
        """여러 프로시저의 파라미터 분석 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            PROCEDURE proc1(p1 IN NUMBER, p2 OUT VARCHAR2) IS
            BEGIN
                NULL;
            END;
            
            PROCEDURE proc2(p1 IN OUT DATE) IS
            BEGIN
                NULL;
            END;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        params = parser.analyze_parameters()
        assert params['total'] == 3
        assert params['in'] == 1
        assert params['out'] == 1
        assert params['in_out'] == 1
    
    def test_analyze_local_variables(self):
        """로컬 변수 분석 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
            v_salary NUMBER;
            v_hire_date DATE;
            v_is_active BOOLEAN;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        vars = parser.analyze_local_variables()
        assert vars['total'] == 4
        assert vars['varchar_type'] == 1
        assert vars['number_type'] == 1
        assert vars['date_type'] == 1
        assert vars['boolean_type'] == 1
    
    def test_analyze_local_variables_with_types(self):
        """다양한 타입의 로컬 변수 분석 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_id INTEGER;
            v_count PLS_INTEGER;
            v_timestamp TIMESTAMP;
            v_data CLOB;
            v_emp employees%ROWTYPE;
            v_salary employees.salary%TYPE;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        vars = parser.analyze_local_variables()
        assert vars['total'] >= 4
        assert vars['number_type'] >= 2  # INTEGER, PLS_INTEGER
        assert vars['date_type'] >= 1    # TIMESTAMP
        assert vars['record_type'] >= 1  # %ROWTYPE
    
    def test_analyze_local_variables_table_type(self):
        """TABLE OF 타입 변수 분석 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_table IS TABLE OF employees%ROWTYPE;
            TYPE id_table IS TABLE OF NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        vars = parser.analyze_local_variables()
        # TYPE 정의는 analyze_custom_types에서 처리
        # 여기서는 실제 변수 선언만 카운트
        types = parser.analyze_custom_types()
        assert types['table'] >= 2
    
    def test_analyze_custom_types(self):
        """사용자 정의 타입 분석 테스트"""
        code = """
        CREATE OR REPLACE PACKAGE BODY emp_pkg AS
            TYPE emp_record IS RECORD (
                id NUMBER,
                name VARCHAR2(100)
            );
            
            TYPE emp_table IS TABLE OF emp_record;
            TYPE name_array IS VARRAY(10) OF VARCHAR2(50);
        BEGIN
            NULL;
        END emp_pkg;
        """
        parser = PLSQLParser(code)
        types = parser.analyze_custom_types()
        assert types['total'] == 3
        assert types['record'] == 1
        assert types['table'] == 1
        assert types['varray'] == 1
    
    def test_analyze_custom_types_object(self):
        """OBJECT 타입 분석 테스트"""
        code = """
        CREATE OR REPLACE TYPE employee_type AS OBJECT (
            employee_id NUMBER,
            first_name VARCHAR2(50),
            last_name VARCHAR2(50)
        );
        """
        parser = PLSQLParser(code)
        types = parser.analyze_custom_types()
        assert types['total'] == 1
        assert types['object'] == 1
    
    def test_analyze_custom_types_none(self):
        """사용자 정의 타입이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE simple_proc IS
            v_id NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.analyze_custom_types()
        assert types['total'] == 0


# ============================================================================
# 신규 기능 테스트 (PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반)
# ============================================================================


class TestPLSQLParserTypeReferences:
    """타입 참조 감지 테스트 (%TYPE, %ROWTYPE)"""
    
    def test_count_type_references_type(self):
        """%TYPE 참조 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name employees.employee_name%TYPE;
            v_salary employees.salary%TYPE;
            v_dept departments.department_name%TYPE;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        refs = parser.count_type_references()
        assert refs['type'] == 3
        assert refs['rowtype'] == 0
    
    def test_count_type_references_rowtype(self):
        """%ROWTYPE 참조 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_emp employees%ROWTYPE;
            v_dept departments%ROWTYPE;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        refs = parser.count_type_references()
        assert refs['type'] == 0
        assert refs['rowtype'] == 2
    
    def test_count_type_references_mixed(self):
        """혼합 타입 참조 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_emp employees%ROWTYPE;
            v_name employees.name%TYPE;
            v_salary employees.salary%TYPE;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        refs = parser.count_type_references()
        assert refs['type'] == 2
        assert refs['rowtype'] == 1
    
    def test_count_type_references_none(self):
        """타입 참조가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
            v_salary NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        refs = parser.count_type_references()
        assert refs['type'] == 0
        assert refs['rowtype'] == 0


class TestPLSQLParserUserDefinedTypes:
    """사용자 정의 타입 감지 테스트 (RECORD, TABLE OF, VARRAY, INDEX BY)"""
    
    def test_count_user_defined_types_record(self):
        """RECORD 타입 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_rec IS RECORD (
                id NUMBER,
                name VARCHAR2(100)
            );
            TYPE dept_rec IS RECORD (
                dept_id NUMBER,
                dept_name VARCHAR2(50)
            );
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.count_user_defined_types()
        assert types['record'] == 2
    
    def test_count_user_defined_types_table_of(self):
        """TABLE OF 타입 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_tab IS TABLE OF employees%ROWTYPE;
            TYPE id_tab IS TABLE OF NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.count_user_defined_types()
        assert types['table_of'] == 2
    
    def test_count_user_defined_types_varray(self):
        """VARRAY 타입 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE name_arr IS VARRAY(100) OF VARCHAR2(100);
            TYPE id_arr IS VARRAY(50) OF NUMBER;
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.count_user_defined_types()
        assert types['varray'] == 2
    
    def test_count_user_defined_types_index_by(self):
        """INDEX BY (연관 배열) 타입 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_tab IS TABLE OF employees%ROWTYPE INDEX BY PLS_INTEGER;
            TYPE name_tab IS TABLE OF VARCHAR2(100) INDEX BY VARCHAR2(50);
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.count_user_defined_types()
        assert types['index_by'] == 2
    
    def test_count_user_defined_types_mixed(self):
        """혼합 사용자 정의 타입 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            TYPE emp_rec IS RECORD (id NUMBER, name VARCHAR2(100));
            TYPE emp_tab IS TABLE OF emp_rec;
            TYPE name_arr IS VARRAY(10) OF VARCHAR2(50);
            TYPE id_map IS TABLE OF NUMBER INDEX BY VARCHAR2(50);
        BEGIN
            NULL;
        END;
        """
        parser = PLSQLParser(code)
        types = parser.count_user_defined_types()
        assert types['record'] == 1
        assert types['table_of'] == 2  # TABLE OF emp_rec, TABLE OF NUMBER
        assert types['varray'] == 1
        assert types['index_by'] == 1


class TestPLSQLParserReturningInto:
    """RETURNING INTO 절 감지 테스트"""
    
    def test_count_returning_into_insert(self):
        """INSERT RETURNING INTO 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_id NUMBER;
        BEGIN
            INSERT INTO employees (name, salary)
            VALUES ('John', 5000)
            RETURNING employee_id INTO v_id;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_returning_into()
        assert count == 1
    
    def test_count_returning_into_update(self):
        """UPDATE RETURNING INTO 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_new_salary NUMBER;
        BEGIN
            UPDATE employees SET salary = salary * 1.1
            WHERE employee_id = 100
            RETURNING salary INTO v_new_salary;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_returning_into()
        assert count == 1
    
    def test_count_returning_into_delete(self):
        """DELETE RETURNING INTO 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
        BEGIN
            DELETE FROM employees WHERE employee_id = 100
            RETURNING name INTO v_name;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_returning_into()
        assert count == 1
    
    def test_count_returning_into_multiple(self):
        """여러 RETURNING INTO 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_id NUMBER;
            v_salary NUMBER;
        BEGIN
            INSERT INTO employees (name) VALUES ('John')
            RETURNING employee_id INTO v_id;
            
            UPDATE employees SET salary = 6000 WHERE employee_id = v_id
            RETURNING salary INTO v_salary;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_returning_into()
        assert count == 2
    
    def test_count_returning_into_none(self):
        """RETURNING INTO가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            INSERT INTO employees (name) VALUES ('John');
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_returning_into()
        assert count == 0


class TestPLSQLParserRaiseApplicationError:
    """RAISE_APPLICATION_ERROR 감지 테스트"""
    
    def test_count_raise_application_error_single(self):
        """단일 RAISE_APPLICATION_ERROR 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_value NUMBER) IS
        BEGIN
            IF p_value < 0 THEN
                RAISE_APPLICATION_ERROR(-20001, 'Value cannot be negative');
            END IF;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_raise_application_error()
        assert count == 1
    
    def test_count_raise_application_error_multiple(self):
        """여러 RAISE_APPLICATION_ERROR 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_status VARCHAR2) IS
        BEGIN
            IF p_status IS NULL THEN
                RAISE_APPLICATION_ERROR(-20001, 'Status cannot be null');
            ELSIF p_status NOT IN ('A', 'I') THEN
                RAISE_APPLICATION_ERROR(-20002, 'Invalid status: ' || p_status);
            ELSIF LENGTH(p_status) > 1 THEN
                RAISE_APPLICATION_ERROR(-20003, 'Status must be single character');
            END IF;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_raise_application_error()
        assert count == 3
    
    def test_count_raise_application_error_none(self):
        """RAISE_APPLICATION_ERROR가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_raise_application_error()
        assert count == 0


class TestPLSQLParserConditionalCompilation:
    """조건부 컴파일 감지 테스트"""
    
    def test_count_conditional_compilation_single(self):
        """단일 조건부 컴파일 블록 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            $IF DBMS_DB_VERSION.VERSION >= 12 $THEN
                -- Oracle 12c 이상 코드
                NULL;
            $ELSE
                -- 이전 버전 코드
                NULL;
            $END
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_conditional_compilation()
        assert count == 1
    
    def test_count_conditional_compilation_multiple(self):
        """여러 조건부 컴파일 블록 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            $IF DBMS_DB_VERSION.VERSION >= 12 $THEN
                NULL;
            $END
            
            $IF $$DEBUG $THEN
                DBMS_OUTPUT.PUT_LINE('Debug mode');
            $END
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_conditional_compilation()
        assert count == 2
    
    def test_count_conditional_compilation_none(self):
        """조건부 컴파일이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_conditional_compilation()
        assert count == 0


class TestPLSQLParserDynamicDDL:
    """동적 DDL 감지 테스트"""
    
    def test_count_dynamic_ddl_create_table(self):
        """동적 CREATE TABLE 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_table VARCHAR2) IS
        BEGIN
            EXECUTE IMMEDIATE 'CREATE TABLE temp_' || p_table || ' (id NUMBER)';
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_dynamic_ddl()
        assert count >= 1
    
    def test_count_dynamic_ddl_drop_table(self):
        """동적 DROP TABLE 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_table VARCHAR2) IS
        BEGIN
            EXECUTE IMMEDIATE 'DROP TABLE ' || p_table;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_dynamic_ddl()
        assert count >= 1
    
    def test_count_dynamic_ddl_multiple(self):
        """여러 동적 DDL 개수 계산 테스트"""
        code = """
        CREATE PROCEDURE test_proc(p_table VARCHAR2) IS
        BEGIN
            EXECUTE IMMEDIATE 'CREATE TABLE temp_' || p_table || ' AS SELECT * FROM ' || p_table;
            EXECUTE IMMEDIATE 'CREATE INDEX idx_temp_' || p_table || ' ON temp_' || p_table || '(id)';
            EXECUTE IMMEDIATE 'DROP TABLE temp_' || p_table;
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_dynamic_ddl()
        assert count >= 2
    
    def test_count_dynamic_ddl_none(self):
        """동적 DDL이 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            EXECUTE IMMEDIATE 'UPDATE employees SET salary = salary * 1.1';
        END;
        """
        parser = PLSQLParser(code)
        count = parser.count_dynamic_ddl()
        assert count == 0


class TestPLSQLParserOracleSpecificExceptions:
    """Oracle 전용 예외 감지 테스트"""
    
    def test_detect_no_data_found(self):
        """NO_DATA_FOUND 예외 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
        BEGIN
            SELECT name INTO v_name FROM employees WHERE id = 999;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                v_name := 'Unknown';
        END;
        """
        parser = PLSQLParser(code)
        exceptions = parser.detect_oracle_specific_exceptions()
        assert 'NO_DATA_FOUND' in exceptions
    
    def test_detect_too_many_rows(self):
        """TOO_MANY_ROWS 예외 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
        BEGIN
            SELECT name INTO v_name FROM employees;
        EXCEPTION
            WHEN TOO_MANY_ROWS THEN
                v_name := 'Multiple';
        END;
        """
        parser = PLSQLParser(code)
        exceptions = parser.detect_oracle_specific_exceptions()
        assert 'TOO_MANY_ROWS' in exceptions
    
    def test_detect_dup_val_on_index(self):
        """DUP_VAL_ON_INDEX 예외 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            INSERT INTO employees (id, name) VALUES (1, 'John');
        EXCEPTION
            WHEN DUP_VAL_ON_INDEX THEN
                NULL;
        END;
        """
        parser = PLSQLParser(code)
        exceptions = parser.detect_oracle_specific_exceptions()
        assert 'DUP_VAL_ON_INDEX' in exceptions
    
    def test_detect_multiple_oracle_exceptions(self):
        """여러 Oracle 전용 예외 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_name VARCHAR2(100);
        BEGIN
            SELECT name INTO v_name FROM employees WHERE id = 1;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                v_name := 'Not found';
            WHEN TOO_MANY_ROWS THEN
                v_name := 'Multiple';
            WHEN VALUE_ERROR THEN
                v_name := 'Error';
        END;
        """
        parser = PLSQLParser(code)
        exceptions = parser.detect_oracle_specific_exceptions()
        assert 'NO_DATA_FOUND' in exceptions
        assert 'TOO_MANY_ROWS' in exceptions
        assert 'VALUE_ERROR' in exceptions
    
    def test_detect_no_oracle_exceptions(self):
        """Oracle 전용 예외가 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        EXCEPTION
            WHEN OTHERS THEN
                NULL;
        END;
        """
        parser = PLSQLParser(code)
        exceptions = parser.detect_oracle_specific_exceptions()
        assert len(exceptions) == 0


class TestPLSQLParserSqlcodeSqlerrm:
    """SQLCODE/SQLERRM 사용 감지 테스트"""
    
    def test_has_sqlcode(self):
        """SQLCODE 사용 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_code NUMBER;
        BEGIN
            NULL;
        EXCEPTION
            WHEN OTHERS THEN
                v_code := SQLCODE;
        END;
        """
        parser = PLSQLParser(code)
        result = parser.has_sqlcode_sqlerrm()
        assert result['sqlcode'] is True
        assert result['sqlerrm'] is False
    
    def test_has_sqlerrm(self):
        """SQLERRM 사용 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_msg VARCHAR2(200);
        BEGIN
            NULL;
        EXCEPTION
            WHEN OTHERS THEN
                v_msg := SQLERRM;
        END;
        """
        parser = PLSQLParser(code)
        result = parser.has_sqlcode_sqlerrm()
        assert result['sqlcode'] is False
        assert result['sqlerrm'] is True
    
    def test_has_both_sqlcode_sqlerrm(self):
        """SQLCODE와 SQLERRM 모두 사용 감지 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
            v_code NUMBER;
            v_msg VARCHAR2(200);
        BEGIN
            NULL;
        EXCEPTION
            WHEN OTHERS THEN
                v_code := SQLCODE;
                v_msg := SQLERRM;
                INSERT INTO error_log (code, message) VALUES (v_code, v_msg);
        END;
        """
        parser = PLSQLParser(code)
        result = parser.has_sqlcode_sqlerrm()
        assert result['sqlcode'] is True
        assert result['sqlerrm'] is True
    
    def test_has_neither_sqlcode_sqlerrm(self):
        """SQLCODE/SQLERRM 모두 없는 경우 테스트"""
        code = """
        CREATE PROCEDURE test_proc IS
        BEGIN
            UPDATE employees SET salary = salary * 1.1;
        END;
        """
        parser = PLSQLParser(code)
        result = parser.has_sqlcode_sqlerrm()
        assert result['sqlcode'] is False
        assert result['sqlerrm'] is False
