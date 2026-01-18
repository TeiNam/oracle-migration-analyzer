# Oracle PL/SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **오브젝트 타입**: PROCEDURE
- **타겟 데이터베이스**: POSTGRESQL
- **총점**: 12.30
- **정규화 점수**: 5.23 / 10.0
- **복잡도 레벨**: 복잡
- **권장사항**: 상당한 재작성

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 기본 점수 | 5.00 |
| 코드 복잡도 | 3.00 |
| Oracle 특화 기능 | 1.80 |
| 비즈니스 로직 | 2.00 |
| 변환 난이도 | 0.50 |

## 분석 메타데이터

- **코드 라인 수**: 51
- **커서 개수**: 2
- **예외 블록 개수**: 4
- **중첩 깊이**: 10
- **BULK 연산 개수**: 3
- **동적 SQL 개수**: 0

## 감지된 Oracle 특화 기능

- NESTED TABLE

## 감지된 외부 의존성

- DBMS_OUTPUT

## 변환 가이드

| Oracle 기능 | 대체 방법 |
|------------|----------|
| NESTED TABLE | ARRAY 또는 별도 테이블 |
| DBMS_OUTPUT | RAISE NOTICE |

## 원본 코드

```sql
-- 벌크 연산(Bulk Collect/FORALL)과 예외 처리를 결합한 성능 최적화형 배치 처리 패턴
CREATE OR REPLACE PROCEDURE PROCESS_EMPLOYEE_BONUSES (
    p_department_id IN NUMBER,
    p_log_message OUT VARCHAR2
)
IS
    -- Define custom types for bulk processing
    TYPE t_emp_id_list IS TABLE OF employees.employee_id%TYPE INDEX BY PLS_INTEGER;
    TYPE t_salary_list IS TABLE OF employees.salary%TYPE INDEX BY PLS_INTEGER;

    v_emp_ids t_emp_id_list;
    v_salaries t_salary_list;
    v_total_processed PLS_INTEGER := 0;
    v_error_count PLS_INTEGER := 0;
    
    -- Cursor to select employees from the specified department
    CURSOR c_employees IS
        SELECT employee_id, salary
        FROM employees
        WHERE department_id = p_department_id
        FOR UPDATE OF salary NOWAIT; -- Lock rows for update

BEGIN
    -- Open the cursor and fetch data in bulk to minimize context switching
    OPEN c_employees;
    LOOP
        FETCH c_employees BULK COLLECT INTO v_emp_ids, v_salaries LIMIT 100;

        -- Exit loop when no more rows are found
        EXIT WHEN v_emp_ids.COUNT = 0;

        -- Process each fetched employee
        FOR i IN v_emp_ids.FIRST .. v_emp_ids.LAST LOOP
            BEGIN
                -- Complex bonus calculation logic (example)
                IF v_salaries(i) < 5000 THEN
                    v_salaries(i) := v_salaries(i) * 1.10; -- 10% bonus
                ELSIF v_salaries(i) >= 5000 AND v_salaries(i) < 10000 THEN
                    v_salaries(i) := v_salaries(i) * 1.05; -- 5% bonus
                ELSE
                    v_salaries(i) := v_salaries(i) * 1.02; -- 2% bonus
                END IF;
                v_total_processed := v_total_processed + 1;

            EXCEPTION
                WHEN OTHERS THEN
                    -- Handle specific row-level errors without stopping the whole procedure
                    DBMS_OUTPUT.PUT_LINE('Error processing employee ID: ' || v_emp_ids(i) || ' - ' || SQLERRM);
                    v_error_count := v_error_count + 1;
            END;
        END LOOP;

        -- Bulk update the salaries back to the table
        FORALL i IN v_emp_ids.FIRST .. v_emp_ids.LAST
            UPDATE employees
            SET salary = v_salaries(i)
            WHERE employee_id = v_emp_ids(i);

    END LOOP;

    CLOSE c_employees;

    -- Commit the transaction if successful
    COMMIT;

    p_log_message := 'Successfully processed ' || v_total_processed || ' records with ' || v_error_count || ' errors.';
    
EXCEPTION
    WHEN OTHERS THEN
        -- Global exception handler for the procedure
        ROLLBACK;
        p_log_message := 'An unexpected error occurred: ' || SQLERRM;
        -- Re-raise exception to the caller if needed
        -- RAISE;
END PROCESS_EMPLOYEE_BONUSES;
/
```
