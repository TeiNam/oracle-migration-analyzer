-- 복잡한 쿼리 (JOIN, 서브쿼리, 분석 함수 포함)
SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    d.department_name,
    e.salary,
    (SELECT AVG(salary) 
     FROM employees 
     WHERE department_id = e.department_id) as avg_dept_salary,
    ROW_NUMBER() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) as salary_rank,
    CASE 
        WHEN e.salary > (SELECT AVG(salary) FROM employees) THEN 'Above Average'
        WHEN e.salary = (SELECT AVG(salary) FROM employees) THEN 'Average'
        ELSE 'Below Average'
    END as salary_status,
    DECODE(e.commission_pct, NULL, 'No Commission', 'Has Commission') as commission_status
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN locations l ON d.location_id = l.location_id
WHERE e.hire_date > SYSDATE - 365
  AND e.salary > 50000
  AND d.department_name IN (SELECT department_name FROM departments WHERE location_id = 1700)
ORDER BY e.department_id, e.salary DESC;
