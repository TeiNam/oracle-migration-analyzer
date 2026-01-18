# Oracle SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **타겟 데이터베이스**: POSTGRESQL
- **총점**: 13.30
- **정규화 점수**: 9.85 / 10.0
- **복잡도 레벨**: 극도로 복잡
- **권장사항**: 완전 재설계

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 구조적 복잡성 | 2.50 |
| Oracle 특화 기능 | 3.00 |
| 함수/표현식 | 2.50 |
| 데이터 볼륨 | 2.00 |
| 실행 복잡성 | 0.90 |
| 변환 난이도 | 2.40 |

## 분석 메타데이터

- **JOIN 개수**: 8
- **서브쿼리 중첩 깊이**: 2
- **CTE 개수**: 9
- **집합 연산자 개수**: 2

## 감지된 Oracle 특화 기능

- CONNECT BY
- START WITH
- PRIOR
- SYS_CONNECT_BY_PATH
- LEVEL

## 감지된 Oracle 특화 함수

- NVL
- SUBSTR
- INSTR

## 변환 가이드

| Oracle 기능 | 대체 방법 |
|------------|----------|
| CONNECT BY | WITH RECURSIVE (재귀 CTE) |
| START WITH | WITH RECURSIVE의 초기 쿼리 |
| PRIOR | WITH RECURSIVE의 재귀 참조 |
| SYS_CONNECT_BY_PATH | WITH RECURSIVE에서 경로 문자열 생성 |
| LEVEL | WITH RECURSIVE의 깊이 계산 |
| NVL | COALESCE(expr, default) |
| SUBSTR | SUBSTR 또는 SUBSTRING |
| INSTR | POSITION(substring IN string) |

## 원본 쿼리

```sql
-- 복잡한 계층형 쿼리 및 재귀 처리
-- Oracle 고급 기능: CONNECT BY, SYS_CONNECT_BY_PATH, LEVEL, PRIOR, NOCYCLE
-- 조직도, BOM(Bill of Materials), 네트워크 그래프 분석

-- 1. 조직 계층 구조 분석 (무한 루프 방지 포함)
WITH RECURSIVE org_hierarchy AS (
    -- 최상위 노드 (CEO)
    SELECT 
        employee_id,
        manager_id,
        first_name || ' ' || last_name as full_name,
        job_title,
        salary,
        1 as level,
        CAST(employee_id AS VARCHAR2(4000)) as path,
        CAST(full_name AS VARCHAR2(4000)) as name_path,
        0 as is_cycle
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- 재귀: 하위 직원들
    SELECT 
        e.employee_id,
        e.manager_id,
        e.first_name || ' ' || e.last_name,
        e.job_title,
        e.salary,
        oh.level + 1,
        oh.path || '/' || e.employee_id,
        oh.name_path || ' > ' || (e.first_name || ' ' || e.last_name),
        CASE 
            WHEN oh.path LIKE '%' || e.employee_id || '%' THEN 1
            ELSE 0
        END
    FROM employees e
    INNER JOIN org_hierarchy oh ON e.manager_id = oh.employee_id
    WHERE oh.is_cycle = 0  -- 순환 참조 방지
    AND oh.level < 10      -- 최대 깊이 제한
),

-- 2. 각 직원의 조직 내 위치 및 통계
employee_metrics AS (
    SELECT 
        oh.*,
        -- 직속 부하 수
        (SELECT COUNT(*) 
         FROM employees e 
         WHERE e.manager_id = oh.employee_id) as direct_reports,
        -- 전체 부하 수 (재귀적)
        (SELECT COUNT(*) 
         FROM org_hierarchy oh2 
         WHERE oh2.path LIKE oh.path || '%' 
         AND oh2.employee_id != oh.employee_id) as total_reports,
        -- 부서 내 급여 순위
        RANK() OVER (
            PARTITION BY SUBSTR(oh.path, 1, INSTR(oh.path, '/', 1, 2) - 1)
            ORDER BY oh.salary DESC
        ) as dept_salary_rank,
        -- 같은 레벨 내 급여 백분위
        PERCENT_RANK() OVER (
            PARTITION BY oh.level 
            ORDER BY oh.salary
        ) as level_salary_percentile
    FROM org_hierarchy oh
),

-- 3. BOM (Bill of Materials) 분석 - 제품 구성 요소 계층
product_bom AS (
    SELECT 
        product_id,
        component_id,
        quantity,
        unit_cost,
        LEVEL as bom_level,
        SYS_CONNECT_BY_PATH(component_name, ' -> ') as component_path,
        -- 루트까지의 누적 수량
        quantity * PRIOR quantity as cumulative_quantity,
        -- 루트까지의 누적 비용
        (quantity * unit_cost) + NVL(PRIOR (quantity * unit_cost), 0) as cumulative_cost,
        -- 리프 노드 여부
        CONNECT_BY_ISLEAF as is_leaf,
        -- 루트 노드 여부
        CONNECT_BY_ROOT product_id as root_product_id,
        -- 순환 참조 감지
        CONNECT_BY_ISCYCLE as has_cycle
    FROM bill_of_materials
    START WITH parent_component_id IS NULL
    CONNECT BY NOCYCLE PRIOR component_id = parent_component_id
    ORDER SIBLINGS BY component_name
),

-- 4. 네트워크 그래프 분석 (최단 경로)
network_paths AS (
    SELECT 
        node_id,
        connected_node_id,
        distance,
        LEVEL as hop_count,
        SYS_CONNECT_BY_PATH(node_id, ' -> ') || ' -> ' || connected_node_id as path,
        -- 경로 상의 총 거리
        SUM(distance) OVER (
            ORDER BY LEVEL 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as total_distance
    FROM network_connections
    START WITH node_id = 1  -- 시작 노드
    CONNECT BY NOCYCLE PRIOR connected_node_id = node_id
    AND LEVEL <= 5  -- 최대 5 홉까지만
),

-- 5. 카테고리 계층 구조 (전자상거래)
category_tree AS (
    SELECT 
        category_id,
        parent_category_id,
        category_name,
        LEVEL as depth,
        SYS_CONNECT_BY_PATH(category_name, ' / ') as full_path,
        -- 형제 노드 중 순서
        ROW_NUMBER() OVER (
            PARTITION BY parent_category_id 
            ORDER BY category_name
        ) as sibling_order,
        -- 해당 카테고리의 모든 하위 카테고리 수
        (SELECT COUNT(*) - 1
         FROM categories c2
         START WITH c2.category_id = c1.category_id
         CONNECT BY PRIOR c2.category_id = c2.parent_category_id
        ) as descendant_count,
        -- 리프 카테고리 여부
        CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM categories c3 
                WHERE c3.parent_category_id = c1.category_id
            ) THEN 1
            ELSE 0
        END as is_leaf_category
    FROM categories c1
    START WITH parent_category_id IS NULL
    CONNECT BY PRIOR category_id = parent_category_id
    ORDER SIBLINGS BY category_name
),

-- 6. 복잡한 집계: 계층별 매출 롤업
hierarchical_sales AS (
    SELECT 
        ct.category_id,
        ct.full_path,
        ct.depth,
        -- 직접 매출 (해당 카테고리만)
        NVL(SUM(s.amount), 0) as direct_sales,
        -- 하위 카테고리 포함 총 매출 (재귀 집계)
        (SELECT NVL(SUM(s2.amount), 0)
         FROM sales s2
         JOIN products p2 ON s2.product_id = p2.product_id
         JOIN categories c2 ON p2.category_id = c2.category_id
         START WITH c2.category_id = ct.category_id
         CONNECT BY PRIOR c2.category_id = c2.parent_category_id
        ) as total_sales_with_children,
        -- 부모 카테고리 대비 매출 비중
        RATIO_TO_REPORT(NVL(SUM(s.amount), 0)) OVER (
            PARTITION BY ct.parent_category_id
        ) as sales_share_in_parent
    FROM category_tree ct
    LEFT JOIN products p ON ct.category_id = p.category_id
    LEFT JOIN sales s ON p.product_id = s.product_id
    GROUP BY ct.category_id, ct.full_path, ct.depth, ct.parent_category_id
),

-- 7. 그래프 순회: 친구 관계 네트워크 (소셜 네트워크)
friend_network AS (
    SELECT 
        user_id,
        friend_id,
        LEVEL as degree_of_separation,
        SYS_CONNECT_BY_PATH(user_id, ' -> ') || ' -> ' || friend_id as connection_path,
        -- 공통 친구 수 계산
        (SELECT COUNT(*)
         FROM friendships f1
         JOIN friendships f2 ON f1.friend_id = f2.user_id
         WHERE f1.user_id = fn.user_id
         AND f2.friend_id = fn.friend_id
        ) as mutual_friends_count,
        CONNECT_BY_ROOT user_id as origin_user
    FROM friendships fn
    START WITH user_id = 12345  -- 특정 사용자
    CONNECT BY NOCYCLE PRIOR friend_id = user_id
    AND LEVEL <= 3  -- 3촌까지만
),

-- 8. 시간 계층 구조 (년 > 분기 > 월 > 주 > 일)
time_hierarchy AS (
    SELECT 
        date_key,
        year_num,
        quarter_num,
        month_num,
        week_num,
        day_num,
        -- 계층 경로
        year_num || ' > Q' || quarter_num || ' > M' || month_num || 
        ' > W' || week_num || ' > D' || day_num as time_path,
        -- 해당 기간의 영업일 수
        (SELECT COUNT(*) 
         FROM calendar c2
         WHERE c2.year_num = c1.year_num
         AND c2.quarter_num = c1.quarter_num
         AND c2.is_business_day = 1
        ) as business_days_in_quarter,
        -- 누적 영업일 (연초부터)
        (SELECT COUNT(*) 
         FROM calendar c3
         WHERE c3.year_num = c1.year_num
         AND c3.date_key <= c1.date_key
         AND c3.is_business_day = 1
        ) as ytd_business_days
    FROM calendar c1
),

-- 9. 최종 통합 쿼리: 조직별 제품 매출 분석
final_analysis AS (
    SELECT 
        em.full_name as employee_name,
        em.job_title,
        em.level as org_level,
        em.name_path as org_path,
        em.direct_reports,
        em.total_reports,
        hs.full_path as product_category_path,
        hs.total_sales_with_children as category_sales,
        -- 직원이 담당하는 카테고리의 총 매출
        SUM(hs.total_sales_with_children) OVER (
            PARTITION BY em.employee_id
        ) as employee_total_sales,
        -- 조직 레벨별 평균 매출
        AVG(hs.total_sales_with_children) OVER (
            PARTITION BY em.level
        ) as level_avg_sales,
        -- 전체 매출 대비 비중
        RATIO_TO_REPORT(hs.total_sales_with_children) OVER () as sales_contribution
    FROM employee_metrics em
    JOIN employee_categories ec ON em.employee_id = ec.employee_id
    JOIN hierarchical_sales hs ON ec.category_id = hs.category_id
    WHERE em.is_cycle = 0
    AND hs.depth <= 3  -- 최대 3단계 카테고리까지만
)

-- 최종 출력: 조직 계층별 성과 분석
SELECT 
    org_level,
    COUNT(DISTINCT employee_name) as employee_count,
    ROUND(AVG(employee_total_sales), 2) as avg_sales_per_employee,
    ROUND(SUM(employee_total_sales), 2) as total_level_sales,
    ROUND(AVG(direct_reports), 1) as avg_direct_reports,
    ROUND(AVG(total_reports), 1) as avg_total_reports,
    -- 레벨별 매출 성장률 (전년 대비)
    ROUND(
        (SUM(employee_total_sales) - LAG(SUM(employee_total_sales)) OVER (ORDER BY org_level)) /
        NULLIF(LAG(SUM(employee_total_sales)) OVER (ORDER BY org_level), 0) * 100,
        2
    ) as yoy_growth_pct
FROM final_analysis
GROUP BY org_level
ORDER BY org_level;

-- 추가: 순환 참조 감지 및 리포트
SELECT 
    'CYCLE DETECTED' as alert_type,
    employee_id,
    manager_id,
    path,
    'Circular reference in organization structure' as description
FROM org_hierarchy
WHERE is_cycle = 1

UNION ALL

SELECT 
    'ORPHAN NODE' as alert_type,
    e.employee_id,
    e.manager_id,
    NULL as path,
    'Employee has invalid manager reference' as description
FROM employees e
WHERE e.manager_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM employees e2 WHERE e2.employee_id = e.manager_id
);
```
