# Oracle SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **타겟 데이터베이스**: MYSQL
- **총점**: 18.00
- **정규화 점수**: 10.00 / 10.0
- **복잡도 레벨**: 극도로 복잡
- **권장사항**: 완전 재설계

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 구조적 복잡성 | 4.50 |
| Oracle 특화 기능 | 3.00 |
| 함수/표현식 | 2.50 |
| 데이터 볼륨 | 2.50 |
| 실행 복잡성 | 2.50 |
| 변환 난이도 | 3.00 |

## 분석 메타데이터

- **JOIN 개수**: 14
- **서브쿼리 중첩 깊이**: 1
- **CTE 개수**: 7
- **집합 연산자 개수**: 0

## 감지된 Oracle 특화 기능

- CONNECT BY
- START WITH
- PRIOR
- MODEL
- PIVOT
- SYS_CONNECT_BY_PATH
- LEVEL
- DUAL

## 감지된 Oracle 특화 함수

- TO_CHAR
- TO_DATE
- TRUNC

## 변환 가이드

| Oracle 기능 | 대체 방법 |
|------------|----------|
| CONNECT BY | 재귀 쿼리 (MySQL 8.0+) 또는 애플리케이션 로직 |
| START WITH | 재귀 CTE의 초기 쿼리 (MySQL 8.0+) |
| PRIOR | 재귀 CTE의 재귀 참조 (MySQL 8.0+) |
| MODEL | 미지원 (애플리케이션 로직으로 이관) |
| PIVOT | GROUP BY + CASE WHEN (수동 작성) |
| SYS_CONNECT_BY_PATH | 재귀 CTE에서 경로 생성 (MySQL 8.0+) |
| LEVEL | 재귀 CTE에서 깊이 계산 (MySQL 8.0+) |
| DUAL | 불필요 (FROM 절 생략 가능) |
| TO_CHAR | DATE_FORMAT(date, format) |
| TO_DATE | STR_TO_DATE(str, format) |
| TRUNC | DATE(datetime) 또는 FLOOR(number) |

## 원본 쿼리

```sql
-- WITH 절(Common Table Expression, CTE)을 사용한 구조의 쿼리
/*
  [Scenario] 글로벌 유통 기업의 3개년 매출 분석 및 2026년 예측 보고서
  1. 계층적 부서 구조(HR)와 지역 정보를 조인
  2. 이동 평균(Moving Average) 및 누적 합계(Running Total) 계산
  3. 전년 대비 성장률(YoY) 및 분기별 추세 분석
  4. MODEL Clause를 이용한 데이터 보정 및 향후 2분기 예측값 생성
*/

WITH 
-- 1. 부서 계층 구조 전개 (Recursive CTE)
Dept_Hierarchy AS (
    SELECT 
        department_id, department_name, manager_id, parent_id, level as depth,
        SYS_CONNECT_BY_PATH(department_name, ' > ') as dept_path
    FROM departments
    START WITH parent_id IS NULL
    CONNECT BY PRIOR department_id = parent_id
),

-- 2. 시계열 데이터 생성 (Calendar Generator) - 2023년부터 2026년까지
Calendar AS (
    SELECT 
        TRUNC(TO_DATE('20230101', 'YYYYMMDD') + (LEVEL - 1), 'DD') as full_date,
        TO_CHAR(TO_DATE('20230101', 'YYYYMMDD') + (LEVEL - 1), 'YYYY') as year,
        TO_CHAR(TO_DATE('20230101', 'YYYYMMDD') + (LEVEL - 1), 'Q') as quarter,
        TO_CHAR(TO_DATE('20230101', 'YYYYMMDD') + (LEVEL - 1), 'MM') as month
    FROM dual
    CONNECT BY LEVEL <= (TO_DATE('20261231', 'YYYYMMDD') - TO_DATE('20230101', 'YYYYMMDD') + 1)
),

-- 3. 원천 매출 데이터 정제 및 조인
Raw_Sales_Data AS (
    SELECT 
        c.year, c.quarter, c.month,
        d.dept_path,
        e.employee_id,
        e.last_name || ' ' || e.first_name as emp_name,
        p.product_category,
        s.sale_amount,
        s.quantity_sold,
        -- Window Function: 직원별 월간 매출 순위
        RANK() OVER (PARTITION BY c.year, c.month ORDER BY s.sale_amount DESC) as monthly_emp_rank
    FROM sales s
    JOIN Calendar c ON s.sale_date = c.full_date
    JOIN employees e ON s.sales_rep_id = e.employee_id
    JOIN Dept_Hierarchy d ON e.department_id = d.department_id
    JOIN products p ON s.product_id = p.product_id
    WHERE s.sale_amount > 0
),

-- 4. 다차원 집계 (Grouping Sets / Rollup)
Aggregated_Sales AS (
    SELECT 
        year, quarter, month, dept_path, product_category,
        SUM(sale_amount) as total_revenue,
        COUNT(employee_id) as sales_force_count,
        GROUPING_ID(year, quarter, month, dept_path, product_category) as gid
    FROM Raw_Sales_Data
    GROUP BY ROLLUP(year, (quarter, month), dept_path, product_category)
),

-- 5. 고급 분석 연산 (Lead/Lag 및 Moving Average)
Analytic_Base AS (
    SELECT 
        a.*,
        -- 전년 동기 매출 (Year-over-Year)
        LAG(total_revenue, 12) OVER (PARTITION BY dept_path, product_category ORDER BY year, month) as last_year_revenue,
        -- 3개월 이동 평균 (Moving Average)
        AVG(total_revenue) OVER (PARTITION BY dept_path ORDER BY year, month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg_3m,
        -- 누적 매출 비율 (Pareto 분석용)
        RATIO_TO_REPORT(total_revenue) OVER (PARTITION BY year, quarter) as revenue_share
    FROM Aggregated_Sales a
    WHERE gid = 0 -- 최하위 상세 레벨만 선택
),

-- 6. Oracle MODEL Clause (데이터 예측 및 비즈니스 로직 적용)
-- 이 부분은 일반적인 SQL로 구현하기 힘든 행 간 복잡한 수식 계산을 수행합니다.
Predicted_Sales AS (
    SELECT * FROM Analytic_Base
    MODEL
        PARTITION BY (dept_path, product_category)
        DIMENSION BY (year, month)
        MEASURES (total_revenue as sales, 0 as forecast_flag)
        IGNORE NAV
        RULES (
            -- 2026년 매출 예측: 최근 3개월 평균에 5% 가중치 적용
            sales['2026', ANY] = AVG(sales)[year IN ('2025'), ANY] * 1.05,
            -- 특정 부서의 매출 보정 로직
            sales[year='2026', month='12'] = sales['2026', '11'] * 1.2
        )
),

-- 7. 피벗팅 (Quarterly Pivot Report)
Final_Pivot AS (
    SELECT * FROM (
        SELECT dept_path, product_category, year, quarter, sales
        FROM Predicted_Sales
    )
    PIVOT (
        SUM(sales) 
        FOR quarter IN ('1' as Q1, '2' as Q2, '3' as Q3, '4' as Q4)
    )
)

-- 8. 최종 출력 및 필터링
SELECT 
    f.*,
    (Q1 + Q2 + Q3 + Q4) as annual_total,
    CASE 
        WHEN annual_total > 1000000 THEN 'Platinum'
        WHEN annual_total > 500000 THEN 'Gold'
        ELSE 'Silver'
    END as performance_tier
FROM Final_Pivot f
ORDER BY dept_path, product_category, year DESC;
```
