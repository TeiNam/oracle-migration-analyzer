# SQL 복잡도 계산 공식 쉽게 이해하기

> 작성일: 2026-01-28
> Oracle SQL 쿼리가 PostgreSQL이나 MySQL로 변환하기 얼마나 어려운지를 0-10점으로 점수화하는 방법을 설명합니다.

## 📋 목차

1. [한눈에 보는 복잡도 계산](#한눈에-보는-복잡도-계산)
2. [왜 타겟 DB마다 점수가 다른가?](#왜-타겟-db마다-점수가-다른가)
3. [6가지 평가 영역 상세 설명](#6가지-평가-영역-상세-설명)
4. [최종 점수 계산 방법](#최종-점수-계산-방법)
5. [복잡도 레벨과 권장사항](#복잡도-레벨과-권장사항)
6. [실제 예시로 이해하기](#실제-예시로-이해하기)

---

## 한눈에 보는 복잡도 계산

### 핵심 공식

```
최종 점수 = (6가지 영역 점수 합계) × 10 ÷ 최대 가능 점수
```

### 6가지 평가 영역

| 영역 | 무엇을 측정하나? | PostgreSQL 최대 | MySQL 최대 |
|------|-----------------|-----------------|------------|
| 1. 구조적 복잡성 | JOIN, 서브쿼리, CTE 등 | 2.5점 | 4.5점 |
| 2. Oracle 특화 기능 | CONNECT BY, PIVOT 등 | 3.0점 | 3.0점 |
| 3. 함수/표현식 | 집계함수, CASE, 정규식 등 | 2.5점 | 2.5점 |
| 4. 데이터 볼륨 | 쿼리 길이 (코드량) | 0.8점 | 1.0점 |
| 5. 실행 복잡성 | ORDER BY, GROUP BY 등 | 1.0점 | 2.5점 |
| 6. 변환 난이도 | 힌트, Oracle 문법 변환 | 5.5점 | 5.5점 |
| **합계** | | **약 13.5점** | **약 18.0점** |

> 💡 **핵심 포인트**: MySQL은 PostgreSQL보다 최대 점수가 높습니다. 이는 MySQL이 복잡한 쿼리 처리에 더 약하기 때문에 같은 쿼리라도 MySQL로 변환할 때 더 어렵다는 의미입니다.

### 고복잡도 임계값

| 타겟 DB | 임계값 | 의미 |
|---------|--------|------|
| PostgreSQL | **5.0점** | 이 점수 이상이면 "복잡" 판정 |
| MySQL | **7.0점** | 이 점수 이상이면 "복잡" 판정 |

> 💡 임계값은 max_total_score 대비 약 37~39% 비율로 설정되어 있습니다.



---

## 왜 타겟 DB마다 점수가 다른가?

### PostgreSQL vs MySQL 아키텍처 차이

**같은 Oracle 쿼리라도...**

| 타겟 DB | 복잡도 점수 | 이유 |
|---------|------------|------|
| PostgreSQL | 4.2점 (중간) | 복잡한 쿼리 처리에 강함 |
| MySQL | 6.8점 (복잡) | 복잡한 쿼리 처리에 약함 |

> 💡 **왜?** MySQL은 복잡한 쿼리 처리에 약하기 때문!

### 주요 차이점

| 특성 | PostgreSQL | MySQL |
|------|-----------|-------|
| 아키텍처 | 멀티프로세스 | 멀티스레드 |
| 복잡한 JOIN | 최적화 우수 ✅ | 3개 이상 시 성능 저하 ⚠️ |
| 서브쿼리 | 최적화 우수 ✅ | 최적화 제한적 ⚠️ |
| CTE (WITH 절) | 네이티브 지원 ✅ | 8.0부터 지원 (제한적) |
| 풀스캔 | 성능 우수 ✅ | 성능 약함 ⚠️ |
| 분석 함수 | 완벽 지원 ✅ | 8.0부터 지원 |

### 실제 예시: JOIN 개수에 따른 점수 차이

```sql
-- 5개 테이블 JOIN 쿼리
SELECT *
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
JOIN categories cat ON p.category_id = cat.id
JOIN suppliers s ON p.supplier_id = s.id
WHERE o.order_date > '2024-01-01';
```

**PostgreSQL 점수**: 1.0점 (4-5개 JOIN = 1.0점)
**MySQL 점수**: 3.0점 (5-6개 JOIN = 3.0점)

> 💡 같은 쿼리인데 MySQL은 3배 높은 점수! MySQL에서 5개 JOIN은 성능 문제를 일으킬 수 있기 때문입니다.

---

## 6가지 평가 영역 상세 설명

### 1️⃣ 구조적 복잡성 (Structural Complexity)

**측정 대상**: 쿼리의 구조적 복잡함

```
구조적 복잡성 = JOIN 점수 + 서브쿼리 점수 + CTE 점수 + 집합연산자 점수 + 풀스캔 페널티
```

#### 1.1 JOIN 점수

**PostgreSQL**:
| JOIN 개수 | 점수 | 이유 |
|-----------|------|------|
| 0개 | 0점 | 단일 테이블 |
| 1-3개 | 0.5점 | 일반적인 쿼리 |
| 4-5개 | 1.0점 | 복잡한 쿼리 |
| 6개 이상 | 1.5점 | 매우 복잡 |

**MySQL** (더 엄격함):
| JOIN 개수 | 점수 | 이유 |
|-----------|------|------|
| 0개 | 0점 | 단일 테이블 |
| 1-2개 | 1.0점 | 일반적인 쿼리 |
| 3-4개 | 2.0점 | 복잡한 쿼리 |
| 5-6개 | 3.0점 | 매우 복잡 |
| 7개 이상 | 4.0점 | 극도로 복잡 |

#### 1.2 서브쿼리 중첩 깊이 점수

**PostgreSQL**:
```
깊이 0 (서브쿼리 없음): 0점
깊이 1: 0.5점
깊이 2: 1.0점
깊이 3 이상: 1.5 + min(1.0, (깊이-2) × 0.5)
```

**MySQL** (훨씬 엄격함):
```
깊이 0: 0점
깊이 1: 1.5점  ← PostgreSQL의 3배!
깊이 2: 3.0점
깊이 3 이상: 4.0 + min(2.0, 깊이-2)
```

**예시**:
```sql
-- 서브쿼리 깊이 2
SELECT * FROM orders
WHERE customer_id IN (
    SELECT id FROM customers
    WHERE region_id IN (
        SELECT id FROM regions WHERE name = 'Asia'
    )
);
```
- PostgreSQL: 1.0점
- MySQL: 3.0점 (3배 차이!)

#### 1.3 CTE (WITH 절) 점수

```
PostgreSQL: min(1.0, CTE 개수 × 0.5)
MySQL: min(2.0, CTE 개수 × 0.8)
```

**예시**: CTE 3개 사용 시
- PostgreSQL: min(1.0, 3 × 0.5) = 1.0점
- MySQL: min(2.0, 3 × 0.8) = 2.0점

#### 1.4 집합 연산자 점수

UNION, INTERSECT, MINUS 등

```
PostgreSQL: min(1.5, 개수 × 0.5)
MySQL: min(2.0, 개수 × 0.8)
```

#### 1.5 풀스캔 페널티 (MySQL만)

```sql
-- WHERE 절이 없으면 풀스캔 위험!
SELECT * FROM large_table;  -- MySQL에서 +1.0점 페널티
```

- PostgreSQL: 0점 (풀스캔 성능 우수)
- MySQL: 1.0점 페널티 (풀스캔 성능 약함)



---

### 2️⃣ Oracle 특화 기능 (Oracle-Specific Features)

**측정 대상**: Oracle에서만 사용 가능한 특수 기능

**최대 점수**: 3.0점 (PostgreSQL/MySQL 동일)

#### 주요 Oracle 특화 기능과 점수

| 기능 | 점수 | 설명 | 변환 난이도 |
|------|------|------|------------|
| `CONNECT BY` | 2.0점 | 계층적 쿼리 | 🔴 매우 어려움 |
| `MODEL` | 2.5점 | 스프레드시트 계산 | 🔴 매우 어려움 |
| `PIVOT/UNPIVOT` | 1.5점 | 행↔열 변환 | 🟠 어려움 |
| `MERGE` | 2.0점 | UPSERT 연산 | 🟠 어려움 |
| `ROWNUM` | 1.5점 | 행 번호 | 🟠 어려움 |
| `ROWID` | 1.5점 | 물리적 행 주소 | 🟠 어려움 |
| `(+)` | 1.5점 | 구식 OUTER JOIN | 🟠 어려움 |
| `DUAL` | 0.5점 | 더미 테이블 | 🟢 쉬움 |

#### 분석 함수 (OVER 절)

```sql
-- 분석 함수 예시
SELECT 
    employee_id,
    salary,
    ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rank,
    LAG(salary) OVER (ORDER BY hire_date) as prev_salary
FROM employees;
```

**점수**: min(3.0, 분석 함수 개수)
- 위 예시: 2개 사용 → 2.0점

#### 계층적 쿼리 예시

```sql
-- Oracle CONNECT BY (2.0점)
SELECT employee_id, manager_id, LEVEL
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;
```

이 쿼리는 PostgreSQL에서 `WITH RECURSIVE`로 완전히 재작성해야 합니다.

---

### 3️⃣ 함수/표현식 (Functions & Expressions)

**측정 대상**: 사용된 함수와 표현식의 복잡도

**최대 점수**: PostgreSQL 2.0점 / MySQL 2.5점

```
함수 점수 = 집계함수 + CASE 표현식 + 정규식 + Oracle 특화 함수 + MySQL 페널티
```

#### 3.1 집계 함수

```
점수 = min(2.0, 집계함수 개수 × 0.5)
```

| 집계 함수 | 설명 |
|----------|------|
| COUNT, SUM, AVG, MAX, MIN | 기본 집계 |
| LISTAGG | 문자열 집계 (Oracle 전용) |
| MEDIAN | 중앙값 |
| PERCENTILE_CONT/DISC | 백분위수 |

#### 3.2 CASE 표현식

```
점수 = min(2.0, CASE 개수 × 0.5)
```

```sql
-- CASE 2개 사용 → 1.0점
SELECT 
    CASE WHEN status = 'A' THEN 'Active' ELSE 'Inactive' END,
    CASE WHEN amount > 1000 THEN 'High' ELSE 'Low' END
FROM orders;
```

#### 3.3 정규식 함수

```sql
-- 정규식 사용 시 +1.0점
SELECT * FROM users
WHERE REGEXP_LIKE(email, '^[a-z]+@[a-z]+\.[a-z]+$');
```

#### 3.4 Oracle 특화 함수 점수

| 함수 | 점수 | 대체 방법 |
|------|------|----------|
| `DECODE` | 0.8점 | CASE WHEN |
| `NVL` | 0.6점 | COALESCE |
| `NVL2` | 0.7점 | CASE WHEN |
| `TO_CHAR` | 0.7점 | 포맷 문자열 변환 필요 |
| `TO_DATE` | 0.7점 | 포맷 문자열 변환 필요 |
| `LISTAGG` | 1.0점 | STRING_AGG (PostgreSQL) |
| `SYS_CONTEXT` | 1.5점 | 완전 재작성 필요 |

#### 3.5 MySQL 추가 페널티

MySQL에서만 추가되는 페널티:

| 상황 | 추가 점수 |
|------|----------|
| MEDIAN/PERCENTILE 사용 | +0.5점 |
| LISTAGG 사용 | +0.3점 |
| XMLAGG 사용 | +0.5점 |
| KEEP 절 사용 | +0.5점 |
| WHERE 없이 COUNT(*) | +0.5점 |



---

### 4️⃣ 데이터 볼륨 (Data Volume)

**측정 대상**: 쿼리의 길이 (문자 수)

**왜 쿼리 길이가 중요한가?**
- 긴 쿼리 = 복잡한 비즈니스 로직 (약한 상관관계)
- 변환 시 검토해야 할 코드량 증가
- 테스트 케이스 증가

> ⚠️ **개선 사항**: 쿼리 길이와 복잡도의 약한 상관관계를 반영하여 점수가 대폭 축소되었습니다.

#### 점수 기준

| 쿼리 길이 | PostgreSQL | MySQL |
|----------|-----------|-------|
| 500자 미만 | 0.3점 | 0.3점 |
| 500-1000자 | 0.5점 | 0.7점 |
| 1000자 이상 | 0.8점 | 1.0점 |

#### 예시

```sql
-- 짧은 쿼리 (약 50자) → 0.3점
SELECT * FROM orders WHERE status = 'PENDING';

-- 중간 쿼리 (약 600자) → PostgreSQL 0.5점 / MySQL 0.7점
SELECT 
    o.order_id,
    c.customer_name,
    p.product_name,
    o.quantity,
    o.unit_price,
    o.quantity * o.unit_price as total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
WHERE o.order_date BETWEEN '2024-01-01' AND '2024-12-31';
```

---

### 5️⃣ 실행 복잡성 (Execution Complexity)

**측정 대상**: 쿼리 실행 계획에 영향을 주는 요소

**최대 점수**: PostgreSQL 1.0점 / MySQL 2.5점

#### 5.1 기본 절 점수

| 절 | PostgreSQL | MySQL |
|----|-----------|-------|
| ORDER BY | 0.2점 | 0.5점 |
| GROUP BY | 0.2점 | 0.5점 |
| HAVING | 0.2점 | 0.5점 |

#### 5.2 조인 깊이 페널티

**PostgreSQL**:
```
JOIN > 5개 또는 서브쿼리 깊이 > 2 → +0.5점
```

**MySQL** (더 엄격):
```
JOIN > 3개 또는 서브쿼리 깊이 > 1 → +1.5점
```

#### 5.3 MySQL 전용 성능 페널티

| 요소 | 점수 | 설명 |
|------|------|------|
| 파생 테이블 | min(1.0, 개수 × 0.5) | FROM 절의 서브쿼리 |
| DISTINCT | 0.3점 | 중복 제거 비용 |
| OR 조건 3개 이상 | 0.3점 | 인덱스 활용 어려움 |
| LIKE '%문자열%' | 0.3점 | 풀스캔 유발 |
| WHERE 절에 함수 | 0.5점 | 인덱스 활용 불가 |

#### 예시: MySQL 성능 페널티

```sql
-- 여러 페널티가 적용되는 쿼리
SELECT DISTINCT department_name  -- DISTINCT: +0.3점
FROM employees
WHERE UPPER(name) LIKE '%KIM%'   -- 함수: +0.5점, LIKE: +0.3점
   OR salary > 50000
   OR hire_date > '2020-01-01'
   OR status = 'ACTIVE';         -- OR 4개: +0.3점
-- MySQL 추가 페널티: 1.4점
```



---

### 6️⃣ 변환 난이도 (Conversion Difficulty)

**측정 대상**: Oracle에서 타겟 DB로 변환할 때의 실제 난이도

**최대 점수**: 5.5점 (힌트 2.0점 + Oracle 기능 3.5점)

#### 6.1 힌트 점수

Oracle 힌트는 `/*+ HINT_NAME */` 형식으로 사용됩니다.

| 힌트 개수 | 점수 |
|----------|------|
| 0개 | 0점 |
| 1-2개 | 1.0점 |
| 3-5개 | 1.5점 |
| 6개 이상 | 2.0점 |

> 💡 **개선 사항**: 힌트 점수가 상향 조정되었습니다. 힌트가 있다는 것은 성능 튜닝이 필요하다는 의미이므로, 변환 후에도 성능 최적화 작업이 필요합니다.

**주요 Oracle 힌트**:
- `INDEX` - 특정 인덱스 사용
- `FULL` - 풀 테이블 스캔
- `PARALLEL` - 병렬 처리
- `USE_HASH` - 해시 조인
- `USE_NL` - 중첩 루프 조인
- `LEADING` - 조인 순서 지정

```sql
-- 힌트 3개 사용 → 1.0점
SELECT /*+ INDEX(e emp_idx) PARALLEL(e, 4) LEADING(e d) */
    e.employee_id, d.department_name
FROM employees e
JOIN departments d ON e.dept_id = d.id;
```

#### 6.2 Oracle 특화 기능 변환 난이도

| 기능 | 점수 | 변환 난이도 |
|------|------|------------|
| MODEL | 1.0점 | 🔴 완전 재설계 필요 |
| CONNECT BY | 1.0점 | 🔴 WITH RECURSIVE로 재작성 |
| FLASHBACK | 1.0점 | 🔴 대체 불가 |
| MATERIALIZED VIEW | 1.0점 | 🔴 아키텍처 변경 필요 |
| VERSIONS BETWEEN | 1.0점 | 🔴 Flashback 버전 쿼리 |
| AS OF TIMESTAMP/SCN | 1.0점 | 🔴 Flashback 시점 쿼리 |
| KEEP | 1.0점 | 🔴 정렬 집계 |
| MATCH_RECOGNIZE | 1.0점 | 🔴 패턴 매칭 |
| START WITH | 0.5점 | 🟠 CONNECT BY와 함께 변환 |
| PIVOT/UNPIVOT | 0.5점 | 🟠 CASE/UNION으로 재작성 |
| MERGE | 0.5점 | 🟠 INSERT ON CONFLICT 등 |
| XMLTABLE/XMLQUERY | 0.5점 | 🟠 XML 처리 |
| JSON_TABLE | 0.5점 | 🟠 JSON 테이블 |
| WITHIN GROUP | 0.5점 | 🟠 정렬 집계 |
| SAMPLE | 0.5점 | 🟠 테이블 샘플링 |
| DECODE | 0.3점 | 🟡 CASE WHEN으로 변환 |
| LEVEL | 0.3점 | 🟡 계층 쿼리 관련 |
| SYS_CONNECT_BY_PATH | 0.3점 | 🟡 계층 경로 |
| JSON_VALUE/JSON_QUERY | 0.3점 | 🟡 JSON 처리 |
| ROWNUM | 0.2점 | 🟡 LIMIT/ROW_NUMBER로 변환 |
| ROWID | 0.2점 | 🟡 물리적 행 주소 |
| FOR UPDATE/SKIP LOCKED/NOWAIT | 0.2-0.3점 | 🟡 트랜잭션 옵션 |
| DUAL | 0.1점 | 🟢 제거 또는 VALUES 사용 |
| SYSDATE/SYSTIMESTAMP | 0.1점 | 🟢 NOW() 또는 CURRENT_DATE |

**최대 3.5점으로 제한** (너무 많은 기능이 있어도 3.5점 초과 불가)

#### 6.3 추가 감지 패턴

- **복잡한 ROWNUM 패턴** (페이징 등): +1.5점
- **빈 문자열 비교 패턴** (Oracle NULL 처리 차이): +0.5점

---

## 최종 점수 계산 방법

### 계산 공식

```python
# 1단계: 6가지 영역 점수 합산
총점 = (구조적 복잡성 + Oracle 특화 기능 + 함수/표현식 
        + 데이터 볼륨 + 실행 복잡성 + 변환 난이도)

# 2단계: 0-10 척도로 정규화
정규화 점수 = min(10.0, 총점 × 10 ÷ 최대 가능 점수)

# 최대 가능 점수 (weights.py 기준)
# PostgreSQL: 2.5 + 3.0 + 2.5 + 0.8 + 1.0 + 5.5 ≈ 13.5
# MySQL: 4.5 + 3.0 + 2.5 + 1.0 + 2.5 + 5.5 ≈ 18.0
```

### 고복잡도 임계값

| 타겟 DB | 임계값 | max_total_score 대비 비율 |
|---------|--------|--------------------------|
| PostgreSQL | **5.0점** | 약 37% |
| MySQL | **7.0점** | 약 39% |

### 계산 예시

**예시 쿼리**:
```sql
SELECT /*+ INDEX(o ord_idx) */
    c.customer_name,
    SUM(o.amount) as total_amount,
    RANK() OVER (ORDER BY SUM(o.amount) DESC) as ranking
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
WHERE o.order_date >= ADD_MONTHS(SYSDATE, -12)
  AND NVL(o.status, 'PENDING') = 'COMPLETED'
GROUP BY c.customer_name
HAVING SUM(o.amount) > 10000
ORDER BY ranking;
```

**PostgreSQL 점수 계산**:

| 영역 | 점수 | 근거 |
|------|------|------|
| 구조적 복잡성 | 0.5점 | JOIN 2개 |
| Oracle 특화 기능 | 1.0점 | 분석 함수 1개 (RANK) |
| 함수/표현식 | 1.9점 | SUM(0.5) + NVL(0.6) + ADD_MONTHS(0.7) + SYSDATE(0.1) |
| 데이터 볼륨 | 1.0점 | 약 400자 |
| 실행 복잡성 | 0.6점 | GROUP BY(0.2) + HAVING(0.2) + ORDER BY(0.2) |
| 변환 난이도 | 0.5점 | 힌트 1개 |
| **총점** | **5.5점** | |
| **정규화** | **3.7점** | 5.5 × 10 ÷ 15.0 |

**MySQL 점수 계산**:

| 영역 | 점수 | 근거 |
|------|------|------|
| 구조적 복잡성 | 1.0점 | JOIN 2개 |
| Oracle 특화 기능 | 1.0점 | 분석 함수 1개 |
| 함수/표현식 | 2.4점 | SUM(0.5) + NVL(0.6) + ADD_MONTHS(0.7) + SYSDATE(0.1) + MEDIAN 페널티(0.5) |
| 데이터 볼륨 | 1.2점 | 약 400자 |
| 실행 복잡성 | 1.5점 | GROUP BY(0.5) + HAVING(0.5) + ORDER BY(0.5) |
| 변환 난이도 | 0.5점 | 힌트 1개 |
| **총점** | **7.6점** | |
| **정규화** | **3.9점** | 7.6 × 10 ÷ 19.5 |

> 💡 같은 쿼리인데 MySQL이 약간 더 높은 점수! 이는 MySQL의 더 엄격한 가중치 때문입니다.



---

## 복잡도 레벨과 권장사항

### 6단계 복잡도 레벨

| 점수 | 레벨 | 의미 | 권장 접근 방식 |
|------|------|------|---------------|
| 0-1 | 🟢 매우 간단 | 표준 SQL만 사용 | 자동 변환 도구 사용 |
| 1-3 | 🟢 간단 | 기본 Oracle 함수 | 함수 대체만 필요 |
| 3-5 | 🟡 중간 | 일부 Oracle 특화 기능 | 부분 재작성 |
| 5-7 | 🟠 복잡 | 다수 Oracle 특화 기능 | 상당한 재작성 |
| 7-9 | 🔴 매우 복잡 | 복잡한 Oracle 기능 조합 | 대부분 재작성 |
| 9-10 | ⚫ 극도로 복잡 | 고급 Oracle 기능 | 완전 재설계 |

### 레벨별 상세 설명

#### 🟢 매우 간단 (0-1점)

```sql
-- 예시
SELECT id, name, email FROM users WHERE status = 'ACTIVE';
```

- **특징**: 표준 SQL만 사용, Oracle 특화 기능 없음
- **변환 방법**: AWS SCT 등 자동 변환 도구로 100% 변환 가능
- **예상 시간**: 쿼리당 5분 미만

#### 🟢 간단 (1-3점)

```sql
-- 예시
SELECT 
    NVL(name, 'Unknown') as name,
    TO_CHAR(created_at, 'YYYY-MM-DD') as created_date
FROM users
WHERE ROWNUM <= 100;
```

- **특징**: 기본 Oracle 함수 사용 (NVL, TO_CHAR, ROWNUM 등)
- **변환 방법**: 함수 대체만 필요
  - `NVL` → `COALESCE`
  - `TO_CHAR` → 포맷 문자열 조정
  - `ROWNUM` → `LIMIT` 또는 `ROW_NUMBER()`
- **예상 시간**: 쿼리당 10-30분

#### 🟡 중간 (3-5점)

```sql
-- 예시
SELECT 
    department_id,
    LISTAGG(employee_name, ', ') WITHIN GROUP (ORDER BY hire_date) as employees,
    DECODE(status, 'A', 'Active', 'I', 'Inactive', 'Unknown') as status_name
FROM employees
GROUP BY department_id;
```

- **특징**: LISTAGG, DECODE 등 변환이 필요한 함수 사용
- **변환 방법**: 
  - `LISTAGG` → `STRING_AGG` (PostgreSQL) 또는 `GROUP_CONCAT` (MySQL)
  - `DECODE` → `CASE WHEN`
- **예상 시간**: 쿼리당 30분-2시간

#### 🟠 복잡 (5-7점)

```sql
-- 예시
SELECT 
    employee_id,
    manager_id,
    LEVEL as depth,
    SYS_CONNECT_BY_PATH(employee_name, '/') as path
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;
```

- **특징**: CONNECT BY 계층 쿼리, 복잡한 분석 함수 조합
- **변환 방법**: 완전히 다른 구문으로 재작성 필요
  - `CONNECT BY` → `WITH RECURSIVE`
- **예상 시간**: 쿼리당 2-8시간
- **주의**: 전문가 검토 필수

#### 🔴 매우 복잡 (7-9점)

```sql
-- 예시
SELECT *
FROM sales_data
MODEL
  PARTITION BY (region)
  DIMENSION BY (product, year)
  MEASURES (sales, forecast)
  RULES (
    forecast[ANY, 2025] = sales[CV(), 2024] * 1.1
  );
```

- **특징**: MODEL 절, 복잡한 PIVOT, 다중 계층 쿼리
- **변환 방법**: 비즈니스 로직 분석 후 완전 재설계
- **예상 시간**: 쿼리당 1-3일
- **권장**: 애플리케이션 레벨로 로직 이동 고려

#### ⚫ 극도로 복잡 (9-10점)

- **특징**: 여러 고급 기능 조합, 복잡한 비즈니스 로직
- **변환 방법**: 아키텍처 재설계 필요
- **예상 시간**: 쿼리당 3일 이상
- **권장**: Replatform (Oracle 유지) 고려



---

## 실제 예시로 이해하기

### 예시 1: 단순 쿼리 (점수: 1.2)

```sql
SELECT 
    customer_id,
    customer_name,
    NVL(phone, 'N/A') as phone
FROM customers
WHERE status = 'ACTIVE'
ORDER BY customer_name;
```

**점수 분석 (PostgreSQL)**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 구조적 복잡성 | 0점 | JOIN 없음, 서브쿼리 없음 |
| Oracle 특화 기능 | 0점 | 없음 |
| 함수/표현식 | 0.6점 | NVL 함수 |
| 데이터 볼륨 | 0.5점 | 약 120자 |
| 실행 복잡성 | 0.2점 | ORDER BY |
| 변환 난이도 | 0점 | 힌트 없음 |
| **총점** | **1.3점** | |
| **정규화** | **0.9점** | 🟢 매우 간단 |

**변환 방법**:
```sql
-- PostgreSQL/MySQL
SELECT 
    customer_id,
    customer_name,
    COALESCE(phone, 'N/A') as phone  -- NVL → COALESCE
FROM customers
WHERE status = 'ACTIVE'
ORDER BY customer_name;
```

---

### 예시 2: 중간 복잡도 쿼리 (점수: 4.5)

```sql
SELECT 
    d.department_name,
    COUNT(*) as emp_count,
    AVG(e.salary) as avg_salary,
    LISTAGG(e.employee_name, ', ') WITHIN GROUP (ORDER BY e.hire_date) as employees
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.hire_date >= ADD_MONTHS(SYSDATE, -24)
GROUP BY d.department_name
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC;
```

**점수 분석 (PostgreSQL)**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 구조적 복잡성 | 0.5점 | JOIN 1개 |
| Oracle 특화 기능 | 0점 | 분석 함수 없음 |
| 함수/표현식 | 2.0점 | COUNT, AVG, LISTAGG(1.0), ADD_MONTHS(0.7), SYSDATE(0.1) |
| 데이터 볼륨 | 1.0점 | 약 350자 |
| 실행 복잡성 | 0.6점 | GROUP BY + HAVING + ORDER BY |
| 변환 난이도 | 0점 | 힌트 없음 |
| **총점** | **4.1점** | |
| **정규화** | **2.7점** | 🟢 간단 |

**변환 방법 (PostgreSQL)**:
```sql
SELECT 
    d.department_name,
    COUNT(*) as emp_count,
    AVG(e.salary) as avg_salary,
    STRING_AGG(e.employee_name, ', ' ORDER BY e.hire_date) as employees  -- LISTAGG → STRING_AGG
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.hire_date >= CURRENT_DATE - INTERVAL '24 months'  -- ADD_MONTHS(SYSDATE, -24) 변환
GROUP BY d.department_name
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC;
```

---

### 예시 3: 복잡한 계층 쿼리 (점수: 7.8)

```sql
SELECT /*+ INDEX(e emp_mgr_idx) */
    employee_id,
    employee_name,
    manager_id,
    LEVEL as depth,
    SYS_CONNECT_BY_PATH(employee_name, ' > ') as hierarchy_path,
    CONNECT_BY_ROOT employee_name as top_manager
FROM employees e
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id
ORDER SIBLINGS BY employee_name;
```

**점수 분석 (PostgreSQL)**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 구조적 복잡성 | 0점 | JOIN 없음 |
| Oracle 특화 기능 | 3.0점 | CONNECT BY(2.0) + 분석 함수 |
| 함수/표현식 | 0점 | 일반 함수 없음 |
| 데이터 볼륨 | 1.0점 | 약 320자 |
| 실행 복잡성 | 0.2점 | ORDER BY |
| 변환 난이도 | 4.3점 | 힌트(0.5) + CONNECT BY(1.0) + START WITH(0.5) + PRIOR(0.3) + LEVEL(0.3) + SYS_CONNECT_BY_PATH(1.5) + CONNECT_BY_ROOT(0.2) |
| **총점** | **8.5점** | |
| **정규화** | **5.7점** | 🟠 복잡 |

**변환 방법 (PostgreSQL)** - 완전 재작성 필요:
```sql
WITH RECURSIVE employee_hierarchy AS (
    -- 기본 케이스: 최상위 관리자
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        1 as depth,
        employee_name as hierarchy_path,
        employee_name as top_manager
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- 재귀 케이스: 하위 직원
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        eh.depth + 1,
        eh.hierarchy_path || ' > ' || e.employee_name,
        eh.top_manager
    FROM employees e
    JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM employee_hierarchy
ORDER BY hierarchy_path;
```

> ⚠️ **주의**: `ORDER SIBLINGS BY`는 PostgreSQL에서 완벽하게 재현하기 어렵습니다. 추가 로직이 필요할 수 있습니다.

---

## 📊 요약: 복잡도 계산 치트시트

### 빠른 참조 표

**SQL 복잡도 빠른 체크**

🟢 **낮은 복잡도 (0-3점)**
- ✓ JOIN 3개 이하
- ✓ 서브쿼리 1단계 이하
- ✓ NVL, TO_CHAR 등 기본 함수만 사용
- ✓ 힌트 2개 이하

🟡 **중간 복잡도 (3-5점)**
- ⚠ JOIN 4-5개
- ⚠ 서브쿼리 2단계
- ⚠ LISTAGG, DECODE 사용
- ⚠ 분석 함수 1-2개

🔴 **높은 복잡도 (5점 이상)**
- ✗ JOIN 6개 이상
- ✗ 서브쿼리 3단계 이상
- ✗ CONNECT BY, MODEL, PIVOT 사용
- ✗ 힌트 6개 이상
- ✗ 복잡한 분석 함수 조합

### 핵심 기억 포인트

1. **같은 쿼리라도 타겟 DB에 따라 점수가 다름**
   - MySQL은 PostgreSQL보다 복잡한 쿼리에 더 높은 점수

2. **6가지 영역을 종합 평가**
   - 구조, Oracle 기능, 함수, 볼륨, 실행, 변환 난이도

3. **점수 5점이 분기점**
   - 5점 이하: 자동 변환 + 부분 수정
   - 5점 이상: 전문가 검토 + 상당한 재작성

4. **CONNECT BY, MODEL은 최고 난이도**
   - 완전 재설계 필요
   - Replatform 고려 대상

---

## 📚 관련 문서

- [PL/SQL 복잡도 계산 공식 설명](PLSQL_COMPLEXITY_FORMULA_EXPLAINED.md) - PL/SQL 오브젝트 복잡도 분석
- [Oracle Migration Analyzer란?](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md) - 도구 개요
- [의사결정 공식 정리](DECISION_ENGINE_FORMULAS.md) - 마이그레이션 전략 의사결정 공식

---

> **문서 이력**
> - 2026-01-31: Replatform/MySQL 조건 임계값 업데이트 (SQL 7.5, PL/SQL 7.0, MySQL PL/SQL 4.0, SQL 4.5, 개수 50개)
> - 2026-01-29: 최신 코드 기반 업데이트 (데이터 볼륨 점수 축소, 힌트 점수 상향, 고복잡도 임계값 추가)
> - 2026-01-28: 초안 작성
> - 대상 독자: 마이그레이션 담당자, DBA, 개발자
> - 관련 코드: `src/calculators/sql_complexity.py`, `src/oracle_complexity_analyzer/weights.py`
