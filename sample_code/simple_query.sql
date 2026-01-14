-- 간단한 SELECT 쿼리
SELECT employee_id, first_name, last_name, email
FROM employees
WHERE department_id = 10
ORDER BY last_name;
