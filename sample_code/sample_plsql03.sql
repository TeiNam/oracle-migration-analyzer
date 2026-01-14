-- Oracle 종속성 중간: 비즈니스 로직 및 벌크 데이터 처리 패턴
CREATE OR REPLACE PROCEDURE mid_complexity_biz_proc (
    p_dept_id IN NUMBER
) IS
    -- Record 타입 정의
    TYPE t_emp_rec IS RECORD (
        id   employees.employee_id%TYPE,
        name employees.last_name%TYPE,
        sal  employees.salary%TYPE
    );
    TYPE t_emp_tab IS TABLE OF t_emp_rec INDEX BY PLS_INTEGER;
    v_emps t_emp_tab;

    v_clob_log CLOB;
    v_log_msg  VARCHAR2(4000);
BEGIN
    DBMS_LOB.CREATETEMPORARY(v_clob_log, TRUE);

    -- 1. 대량 데이터 Fetch (Bulk Collect)
    SELECT employee_id, last_name, salary 
    BULK COLLECT INTO v_emps
    FROM employees 
    WHERE department_id = p_dept_id;

    IF v_emps.COUNT > 0 THEN
        -- 2. 메모리 내 복잡한 연산 및 필터링
        FOR i IN v_emps.FIRST .. v_emps.LAST LOOP
            IF v_emps(i).sal > 15000 THEN
                v_emps(i).sal := v_emps(i).sal * 1.02;
            ELSE
                v_emps(i).sal := v_emps(i).sal * 1.08;
            END IF;
            
            v_log_msg := 'Processed: ' || v_emps(i).id || ' - ' || v_emps(i).sal || CHR(10);
            DBMS_LOB.WRITEAPPEND(v_clob_log, LENGTH(v_log_msg), v_log_msg);
        END LOOP;

        -- 3. 일괄 업데이트 (Forall)
        FORALL i IN 1 .. v_emps.COUNT
            UPDATE employees SET salary = v_emps(i).sal 
            WHERE employee_id = v_emps(i).id;
    END IF;

    -- 4. 로그 테이블 저장 (Oracle 고유의 트랜잭션 분리 가능성)
    INSERT INTO proc_logs (log_date, log_detail) VALUES (SYSDATE, v_clob_log);
    COMMIT;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('No employees found.');
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE_APPLICATION_ERROR(-20001, 'Error in mid_complexity: ' || SQLERRM);
END mid_complexity_biz_proc;
