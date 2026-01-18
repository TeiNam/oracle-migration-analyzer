# Oracle PL/SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **오브젝트 타입**: PACKAGE
- **타겟 데이터베이스**: POSTGRESQL
- **총점**: 9.90
- **정규화 점수**: 4.21 / 10.0
- **복잡도 레벨**: 중간
- **권장사항**: 부분 재작성

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 기본 점수 | 7.00 |
| 코드 복잡도 | 0.90 |
| Oracle 특화 기능 | 0.00 |
| 비즈니스 로직 | 2.00 |
| 변환 난이도 | 0.00 |

## 분석 메타데이터

- **코드 라인 수**: 58
- **커서 개수**: 0
- **예외 블록 개수**: 2
- **중첩 깊이**: 2
- **BULK 연산 개수**: 0
- **동적 SQL 개수**: 0

## 원본 코드

```sql
-- PL/SQL Package 예제
CREATE OR REPLACE PACKAGE employee_pkg AS
    -- 패키지 변수
    g_max_salary NUMBER := 100000;
    
    -- 프로시저: 직원 정보 업데이트
    PROCEDURE update_employee_salary(
        p_employee_id IN NUMBER,
        p_new_salary IN NUMBER
    );
    
    -- 함수: 부서별 평균 급여 계산
    FUNCTION get_dept_avg_salary(
        p_department_id IN NUMBER
    ) RETURN NUMBER;
    
END employee_pkg;
/

CREATE OR REPLACE PACKAGE BODY employee_pkg AS
    
    -- 프로시저 구현
    PROCEDURE update_employee_salary(
        p_employee_id IN NUMBER,
        p_new_salary IN NUMBER
    ) IS
        v_current_salary NUMBER;
        v_department_id NUMBER;
    BEGIN
        -- 현재 급여 조회
        SELECT salary, department_id
        INTO v_current_salary, v_department_id
        FROM employees
        WHERE employee_id = p_employee_id;
        
        -- 급여 검증
        IF p_new_salary > g_max_salary THEN
            RAISE_APPLICATION_ERROR(-20001, '급여가 최대 한도를 초과했습니다.');
        END IF;
        
        -- 급여 업데이트
        UPDATE employees
        SET salary = p_new_salary,
            last_update_date = SYSDATE
        WHERE employee_id = p_employee_id;
        
        -- 로그 기록
        INSERT INTO salary_history (employee_id, old_salary, new_salary, change_date)
        VALUES (p_employee_id, v_current_salary, p_new_salary, SYSDATE);
        
        COMMIT;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20002, '직원을 찾을 수 없습니다.');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END update_employee_salary;
    
    -- 함수 구현
    FUNCTION get_dept_avg_salary(
        p_department_id IN NUMBER
    ) RETURN NUMBER IS
        v_avg_salary NUMBER;
    BEGIN
        SELECT AVG(salary)
        INTO v_avg_salary
        FROM employees
        WHERE department_id = p_department_id;
        
        RETURN v_avg_salary;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
        WHEN OTHERS THEN
            RETURN NULL;
    END get_dept_avg_salary;
    
END employee_pkg;
/
```
