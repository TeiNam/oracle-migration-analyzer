"""
Oracle Complexity Analyzer 사용 예제

이 스크립트는 OracleComplexityAnalyzer의 기본 사용법을 보여줍니다.
"""

from src.oracle_complexity_analyzer import OracleComplexityAnalyzer, TargetDatabase


def main():
    """메인 함수"""
    
    print("=" * 80)
    print("Oracle Complexity Analyzer 사용 예제")
    print("=" * 80)
    print()
    
    # 1. PostgreSQL 타겟으로 분석기 생성
    print("1. PostgreSQL 타겟으로 SQL 쿼리 분석")
    print("-" * 80)
    
    analyzer_pg = OracleComplexityAnalyzer(
        target_database=TargetDatabase.POSTGRESQL,
        output_dir="example_reports"
    )
    
    # 간단한 SQL 쿼리 분석
    sql_query = """
    SELECT e.employee_id, e.first_name, e.last_name, d.department_name
    FROM employees e
    LEFT JOIN departments d ON e.department_id = d.department_id
    WHERE e.salary > 50000
    ORDER BY e.last_name
    """
    
    result_sql = analyzer_pg.analyze_sql(sql_query)
    
    print(f"쿼리 복잡도: {result_sql.normalized_score:.2f} / 10.0")
    print(f"복잡도 레벨: {result_sql.complexity_level.value}")
    print(f"권장사항: {result_sql.recommendation}")
    print(f"JOIN 개수: {result_sql.join_count}")
    print()
    
    # JSON 파일로 저장
    json_path = analyzer_pg.export_json(result_sql, "sql_analysis.json")
    print(f"JSON 파일 저장: {json_path}")
    
    # Markdown 파일로 저장
    md_path = analyzer_pg.export_markdown(result_sql, "sql_analysis.md")
    print(f"Markdown 파일 저장: {md_path}")
    print()
    
    # 2. MySQL 타겟으로 PL/SQL 분석
    print("2. MySQL 타겟으로 PL/SQL 코드 분석")
    print("-" * 80)
    
    analyzer_mysql = OracleComplexityAnalyzer(
        target_database=TargetDatabase.MYSQL,
        output_dir="example_reports"
    )
    
    plsql_code = """
    CREATE OR REPLACE PROCEDURE update_employee_salary(
        p_employee_id IN NUMBER,
        p_new_salary IN NUMBER
    ) IS
        v_old_salary NUMBER;
    BEGIN
        -- 기존 급여 조회
        SELECT salary INTO v_old_salary
        FROM employees
        WHERE employee_id = p_employee_id;
        
        -- 급여 업데이트
        UPDATE employees
        SET salary = p_new_salary,
            last_update_date = SYSDATE
        WHERE employee_id = p_employee_id;
        
        -- 로그 기록
        INSERT INTO salary_history (employee_id, old_salary, new_salary, change_date)
        VALUES (p_employee_id, v_old_salary, p_new_salary, SYSDATE);
        
        COMMIT;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20001, '직원을 찾을 수 없습니다.');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END;
    """
    
    result_plsql = analyzer_mysql.analyze_plsql(plsql_code)
    
    print(f"코드 복잡도: {result_plsql.normalized_score:.2f} / 10.0")
    print(f"복잡도 레벨: {result_plsql.complexity_level.value}")
    print(f"권장사항: {result_plsql.recommendation}")
    print(f"오브젝트 타입: {result_plsql.object_type.value}")
    print(f"코드 라인 수: {result_plsql.line_count}")
    print(f"애플리케이션 이관 페널티: {result_plsql.app_migration_penalty}")
    print()
    
    # JSON 파일로 저장
    json_path = analyzer_mysql.export_json(result_plsql, "plsql_analysis.json")
    print(f"JSON 파일 저장: {json_path}")
    
    # Markdown 파일로 저장
    md_path = analyzer_mysql.export_markdown(result_plsql, "plsql_analysis.md")
    print(f"Markdown 파일 저장: {md_path}")
    print()
    
    # 3. Oracle 특화 기능이 많은 복잡한 쿼리 분석
    print("3. Oracle 특화 기능이 많은 복잡한 쿼리 분석")
    print("-" * 80)
    
    complex_query = """
    SELECT /*+ INDEX(e emp_idx) PARALLEL(4) */
        employee_id,
        first_name,
        last_name,
        DECODE(department_id, 10, 'Sales', 20, 'IT', 'Other') as dept_name,
        NVL(commission_pct, 0) as commission,
        LISTAGG(skill_name, ', ') WITHIN GROUP (ORDER BY skill_level) as skills,
        ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) as dept_rank
    FROM employees e
    LEFT JOIN employee_skills es ON e.employee_id = es.employee_id
    WHERE ROWNUM <= 100
      AND hire_date >= ADD_MONTHS(SYSDATE, -12)
    GROUP BY employee_id, first_name, last_name, department_id, commission_pct
    HAVING COUNT(*) > 0
    ORDER BY dept_rank
    """
    
    result_complex = analyzer_pg.analyze_sql(complex_query)
    
    print(f"쿼리 복잡도: {result_complex.normalized_score:.2f} / 10.0")
    print(f"복잡도 레벨: {result_complex.complexity_level.value}")
    print(f"권장사항: {result_complex.recommendation}")
    print(f"감지된 Oracle 특화 기능: {len(result_complex.detected_oracle_features)}개")
    print(f"감지된 Oracle 특화 함수: {len(result_complex.detected_oracle_functions)}개")
    print(f"감지된 힌트: {len(result_complex.detected_hints)}개")
    
    if result_complex.detected_oracle_features:
        print(f"  - 특화 기능: {', '.join(result_complex.detected_oracle_features[:5])}")
    if result_complex.detected_oracle_functions:
        print(f"  - 특화 함수: {', '.join(result_complex.detected_oracle_functions[:5])}")
    
    print()
    print("=" * 80)
    print("분석 완료! example_reports/ 폴더에서 결과를 확인하세요.")
    print("=" * 80)


if __name__ == "__main__":
    main()
