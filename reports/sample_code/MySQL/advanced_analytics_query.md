# Oracle SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **타겟 데이터베이스**: MYSQL
- **총점**: 15.60
- **정규화 점수**: 8.67 / 10.0
- **복잡도 레벨**: 매우 복잡
- **권장사항**: 대부분 재작성

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 구조적 복잡성 | 4.50 |
| Oracle 특화 기능 | 3.00 |
| 함수/표현식 | 2.50 |
| 데이터 볼륨 | 2.50 |
| 실행 복잡성 | 1.50 |
| 변환 난이도 | 1.60 |

## 분석 메타데이터

- **JOIN 개수**: 3
- **서브쿼리 중첩 깊이**: 1
- **CTE 개수**: 10
- **집합 연산자 개수**: 0

## 감지된 Oracle 특화 기능

- CONNECT BY
- PRIOR
- LEVEL

## 감지된 Oracle 특화 함수

- LISTAGG
- TO_CHAR
- TO_NUMBER
- TRUNC
- ADD_MONTHS

## 변환 가이드

| Oracle 기능 | 대체 방법 |
|------------|----------|
| CONNECT BY | 재귀 쿼리 (MySQL 8.0+) 또는 애플리케이션 로직 |
| PRIOR | 재귀 CTE의 재귀 참조 (MySQL 8.0+) |
| LEVEL | 재귀 CTE에서 깊이 계산 (MySQL 8.0+) |
| LISTAGG | GROUP_CONCAT(expr ORDER BY ... SEPARATOR delimiter) - 길이 제한 주의 (기본 1024) |
| TO_CHAR | DATE_FORMAT(date, format) |
| TO_NUMBER | CAST(expr AS DECIMAL) 또는 CONVERT |
| TRUNC | DATE(datetime) 또는 FLOOR(number) |
| ADD_MONTHS | DATE_ADD(date, INTERVAL n MONTH) |

## 원본 쿼리

```sql
-- 고급 분석 쿼리: 시계열 분석, 통계 함수, 머신러닝 스타일 예측
-- Oracle 고급 기능: MATCH_RECOGNIZE, LISTAGG, XMLAGG, JSON_OBJECT
WITH 
-- 1. 시계열 데이터 준비 (일별 거래 데이터)
daily_transactions AS (
    SELECT 
        TRUNC(transaction_date) as txn_date,
        customer_id,
        product_category,
        SUM(amount) as daily_amount,
        COUNT(*) as txn_count,
        -- 고급 집계 함수
        LISTAGG(transaction_id, ',') WITHIN GROUP (ORDER BY transaction_date) as txn_ids,
        -- JSON 집계
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'id' VALUE transaction_id,
                'amount' VALUE amount,
                'time' VALUE TO_CHAR(transaction_date, 'HH24:MI:SS')
            )
        ) as txn_details
    FROM transactions
    WHERE transaction_date >= ADD_MONTHS(SYSDATE, -12)
    GROUP BY TRUNC(transaction_date), customer_id, product_category
),

-- 2. 이상 패턴 탐지 (MATCH_RECOGNIZE 사용)
-- 연속 3일 이상 거래액이 증가하는 패턴 찾기
anomaly_patterns AS (
    SELECT *
    FROM daily_transactions
    MATCH_RECOGNIZE (
        PARTITION BY customer_id, product_category
        ORDER BY txn_date
        MEASURES
            FIRST(txn_date) as pattern_start,
            LAST(txn_date) as pattern_end,
            COUNT(*) as consecutive_days,
            AVG(daily_amount) as avg_amount_in_pattern,
            CLASSIFIER() as pattern_type
        ONE ROW PER MATCH
        AFTER MATCH SKIP TO LAST increasing
        PATTERN (increasing{3,})
        DEFINE
            increasing AS daily_amount > PREV(daily_amount)
    )
),

-- 3. 고객 세그먼테이션 (RFM 분석)
customer_rfm AS (
    SELECT 
        customer_id,
        -- Recency: 마지막 거래일로부터 경과 일수
        TRUNC(SYSDATE) - MAX(txn_date) as recency_days,
        -- Frequency: 거래 빈도
        COUNT(DISTINCT txn_date) as frequency,
        -- Monetary: 총 거래액
        SUM(daily_amount) as monetary_value,
        -- 백분위수 계산
        PERCENT_RANK() OVER (ORDER BY TRUNC(SYSDATE) - MAX(txn_date) DESC) as recency_percentile,
        PERCENT_RANK() OVER (ORDER BY COUNT(DISTINCT txn_date)) as frequency_percentile,
        PERCENT_RANK() OVER (ORDER BY SUM(daily_amount)) as monetary_percentile
    FROM daily_transactions
    GROUP BY customer_id
),

-- 4. 고객 등급 분류 (CASE 기반 복잡한 비즈니스 로직)
customer_segments AS (
    SELECT 
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        CASE 
            WHEN recency_percentile >= 0.8 AND frequency_percentile >= 0.8 AND monetary_percentile >= 0.8 
                THEN 'Champions'
            WHEN recency_percentile >= 0.6 AND frequency_percentile >= 0.6 AND monetary_percentile >= 0.6 
                THEN 'Loyal Customers'
            WHEN recency_percentile >= 0.6 AND frequency_percentile < 0.4 AND monetary_percentile >= 0.6 
                THEN 'Big Spenders'
            WHEN recency_percentile < 0.4 AND frequency_percentile >= 0.6 
                THEN 'At Risk'
            WHEN recency_percentile < 0.2 
                THEN 'Lost'
            ELSE 'Others'
        END as customer_segment,
        -- 고객 생애 가치 예측 (간단한 선형 모델)
        (monetary_value / NULLIF(recency_days, 0)) * 365 as estimated_annual_value
    FROM customer_rfm
),

-- 5. 제품 카테고리별 트렌드 분석 (이동 평균 및 계절성)
category_trends AS (
    SELECT 
        txn_date,
        product_category,
        daily_amount,
        -- 7일 이동 평균
        AVG(daily_amount) OVER (
            PARTITION BY product_category 
            ORDER BY txn_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as ma_7day,
        -- 30일 이동 평균
        AVG(daily_amount) OVER (
            PARTITION BY product_category 
            ORDER BY txn_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as ma_30day,
        -- 표준편차 (변동성 측정)
        STDDEV(daily_amount) OVER (
            PARTITION BY product_category 
            ORDER BY txn_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as volatility_30day,
        -- 계절성 지수 (요일별 패턴)
        AVG(daily_amount) OVER (
            PARTITION BY product_category, TO_CHAR(txn_date, 'D')
        ) / NULLIF(AVG(daily_amount) OVER (PARTITION BY product_category), 0) as seasonal_index
    FROM (
        SELECT txn_date, product_category, SUM(daily_amount) as daily_amount
        FROM daily_transactions
        GROUP BY txn_date, product_category
    )
),

-- 6. 상관관계 분석 (제품 간 동시 구매 패턴)
product_correlation AS (
    SELECT 
        a.product_category as product_a,
        b.product_category as product_b,
        COUNT(DISTINCT a.customer_id) as co_purchase_count,
        -- Jaccard 유사도 계산
        COUNT(DISTINCT a.customer_id) / 
        (SELECT COUNT(DISTINCT customer_id) 
         FROM daily_transactions 
         WHERE product_category IN (a.product_category, b.product_category)
        ) as jaccard_similarity,
        -- 신뢰도 (A 구매 시 B 구매 확률)
        COUNT(DISTINCT a.customer_id) / 
        NULLIF((SELECT COUNT(DISTINCT customer_id) 
                FROM daily_transactions 
                WHERE product_category = a.product_category), 0) as confidence_a_to_b
    FROM daily_transactions a
    JOIN daily_transactions b 
        ON a.customer_id = b.customer_id 
        AND a.txn_date = b.txn_date
        AND a.product_category < b.product_category
    GROUP BY a.product_category, b.product_category
    HAVING COUNT(DISTINCT a.customer_id) >= 10
),

-- 7. 시계열 예측 (선형 회귀 기반 단순 예측)
forecast_data AS (
    SELECT 
        product_category,
        txn_date,
        daily_amount,
        -- 선형 회귀 계수 계산 (REGR_ 함수 사용)
        REGR_SLOPE(daily_amount, TO_NUMBER(txn_date - DATE '2023-01-01')) 
            OVER (PARTITION BY product_category) as trend_slope,
        REGR_INTERCEPT(daily_amount, TO_NUMBER(txn_date - DATE '2023-01-01')) 
            OVER (PARTITION BY product_category) as trend_intercept,
        REGR_R2(daily_amount, TO_NUMBER(txn_date - DATE '2023-01-01')) 
            OVER (PARTITION BY product_category) as r_squared
    FROM (
        SELECT txn_date, product_category, SUM(daily_amount) as daily_amount
        FROM daily_transactions
        GROUP BY txn_date, product_category
    )
),

-- 8. 미래 예측값 생성 (30일 후까지)
future_forecast AS (
    SELECT DISTINCT
        product_category,
        trend_slope,
        trend_intercept,
        r_squared,
        -- 향후 30일 예측
        TRUNC(SYSDATE) + LEVEL as forecast_date,
        trend_intercept + (trend_slope * (TO_NUMBER(TRUNC(SYSDATE) + LEVEL - DATE '2023-01-01'))) 
            as forecasted_amount
    FROM forecast_data
    CONNECT BY LEVEL <= 30
        AND PRIOR product_category = product_category
        AND PRIOR DBMS_RANDOM.VALUE IS NOT NULL
),

-- 9. 고객별 추천 제품 (협업 필터링 스타일)
product_recommendations AS (
    SELECT 
        cs.customer_id,
        cs.customer_segment,
        pc.product_b as recommended_product,
        pc.confidence_a_to_b as recommendation_score,
        ROW_NUMBER() OVER (
            PARTITION BY cs.customer_id 
            ORDER BY pc.confidence_a_to_b DESC
        ) as recommendation_rank
    FROM customer_segments cs
    JOIN daily_transactions dt ON cs.customer_id = dt.customer_id
    JOIN product_correlation pc ON dt.product_category = pc.product_a
    WHERE NOT EXISTS (
        SELECT 1 FROM daily_transactions dt2
        WHERE dt2.customer_id = cs.customer_id
        AND dt2.product_category = pc.product_b
    )
),

-- 10. 최종 통합 뷰 (XML 집계 포함)
final_summary AS (
    SELECT 
        cs.customer_id,
        cs.customer_segment,
        cs.monetary_value,
        cs.estimated_annual_value,
        -- 이상 패턴 정보
        (SELECT COUNT(*) FROM anomaly_patterns ap 
         WHERE ap.customer_id = cs.customer_id) as anomaly_count,
        -- 추천 제품 목록 (XML 형식)
        (SELECT XMLAGG(
            XMLELEMENT("recommendation",
                XMLATTRIBUTES(
                    recommended_product as "product",
                    ROUND(recommendation_score, 3) as "score"
                )
            )
         )
         FROM product_recommendations pr
         WHERE pr.customer_id = cs.customer_id
         AND pr.recommendation_rank <= 3
        ) as top_recommendations_xml,
        -- 추천 제품 목록 (JSON 형식)
        (SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'product' VALUE recommended_product,
                'score' VALUE ROUND(recommendation_score, 3),
                'rank' VALUE recommendation_rank
            )
         )
         FROM product_recommendations pr
         WHERE pr.customer_id = cs.customer_id
         AND pr.recommendation_rank <= 3
        ) as top_recommendations_json
    FROM customer_segments cs
)

-- 최종 출력: 고객 세그먼트별 집계 및 예측
SELECT 
    fs.customer_segment,
    COUNT(DISTINCT fs.customer_id) as customer_count,
    ROUND(AVG(fs.monetary_value), 2) as avg_monetary_value,
    ROUND(AVG(fs.estimated_annual_value), 2) as avg_estimated_annual_value,
    ROUND(AVG(fs.anomaly_count), 2) as avg_anomaly_count,
    -- 세그먼트별 주요 추천 제품 (집계)
    LISTAGG(
        EXTRACTVALUE(
            fs.top_recommendations_xml, 
            '/recommendation[1]/@product'
        ), 
        ', '
    ) WITHIN GROUP (ORDER BY fs.customer_id) as common_recommendations,
    -- 향후 30일 예상 매출 (해당 세그먼트 고객들의 예측값 합계)
    (SELECT SUM(ff.forecasted_amount)
     FROM future_forecast ff
     WHERE ff.forecast_date BETWEEN TRUNC(SYSDATE) AND TRUNC(SYSDATE) + 30
    ) as total_forecasted_revenue_30d
FROM final_summary fs
GROUP BY fs.customer_segment
ORDER BY avg_estimated_annual_value DESC;
```
