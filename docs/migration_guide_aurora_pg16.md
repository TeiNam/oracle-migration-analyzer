# Oracle에서 Aurora PostgreSQL 16으로의 마이그레이션 가이드

> [English](./EN/migration_guide_aurora_pg16_EN.md)

이 문서는 Oracle 데이터베이스에서 Amazon Aurora PostgreSQL 16 버전 이상으로 마이그레이션하는 과정에서 쿼리 변환 및 최신 기능 활용에 초점을 맞춘 가이드입니다.

## 목차

1. [Aurora PostgreSQL 16+ 주요 기능](#aurora-postgresql-16-주요-기능)
2. [마이그레이션 개요](#마이그레이션-개요)
3. [쿼리 복잡도에 따른 접근 방식](#쿼리-복잡도에-따른-접근-방식)
4. [Oracle 특화 기능 대체 방법](#oracle-특화-기능-대체-방법)
5. [PostgreSQL 16+ 신규 기능 활용](#postgresql-16-신규-기능-활용)
6. [Aurora 특화 기능 활용](#aurora-특화-기능-활용)
7. [성능 최적화 고려사항](#성능-최적화-고려사항)

## Aurora PostgreSQL 16+ 주요 기능

PostgreSQL 16과 Aurora의 최신 기능들을 활용하여 Oracle 마이그레이션을 더욱 효율적으로 수행할 수 있습니다:

### PostgreSQL 16 신규 기능
- **논리적 복제 개선**: 양방향 복제 지원으로 마이그레이션 중 데이터 동기화 용이
- **증분 정렬 개선**: 대용량 데이터 정렬 성능 향상
- **병렬 쿼리 개선**: FULL/RIGHT JOIN 병렬 처리 지원
- **COPY 성능 개선**: 대용량 데이터 로드 속도 향상
- **정규 표현식 성능 개선**: 복잡한 패턴 매칭 최적화

### Aurora PostgreSQL 특화 기능
- **Babelfish for Aurora PostgreSQL**: T-SQL 호환성 제공 (Oracle 직접 지원 아님)
- **Aurora Machine Learning**: SQL에서 직접 ML 모델 호출
- **Fast Cloning**: 빠른 데이터베이스 복제로 테스트 환경 구성
- **Global Database**: 다중 리전 재해 복구
- **Performance Insights**: 실시간 성능 모니터링

## 마이그레이션 개요

### 1. 평가 및 계획
- **AWS Schema Conversion Tool (SCT)** 사용
  - 스키마 및 코드 자동 변환
  - 변환 불가능한 항목 식별
  - 복잡도 평가 리포트 생성
- **Oracle to PostgreSQL Query Analyzer** 사용
  - 쿼리 복잡도 분석
  - 변환 우선순위 결정

### 2. 스키마 변환
```sql
-- Oracle 데이터 타입 → PostgreSQL 매핑
NUMBER → NUMERIC 또는 INTEGER
VARCHAR2 → VARCHAR
DATE → TIMESTAMP
CLOB → TEXT
BLOB → BYTEA
RAW → BYTEA
```

### 3. 데이터 마이그레이션
- **AWS Database Migration Service (DMS)** 활용
  - 초기 전체 로드
  - 지속적 변경 데이터 캡처 (CDC)
  - 최소 다운타임 마이그레이션

### 4. 검증 및 최적화
- 데이터 무결성 검증
- 성능 테스트 및 튜닝
- Aurora Performance Insights로 모니터링

## 쿼리 복잡도에 따른 접근 방식

### 매우 간단 (0-1)
- AWS SCT 자동 변환
- 기본 문법 차이만 수정
- 예: `NVL → COALESCE`, `SYSDATE → CURRENT_TIMESTAMP`

### 간단 (1-3)
- AWS SCT + 수동 검토
- 함수 대체 필요
- 예: `TO_CHAR → TO_CHAR` (형식 문자열 조정)

### 중간 (3-5)
- 부분 재작성 필요
- PostgreSQL 16 신규 기능 활용 검토
- 예: `CONNECT BY → WITH RECURSIVE`

### 복잡 (5-7)
- 상당한 재작성 필요
- Aurora 특화 기능 활용 검토
- 전문가 검토 권장

### 매우 복잡 (7-9)
- 대부분 재작성 필요
- 아키텍처 재설계 고려
- AWS Professional Services 활용 권장

### 극도로 복잡 (9-10)
- 완전한 재설계 필요
- 비즈니스 로직 재검토
- 단계적 마이그레이션 전략 수립

## Oracle 특화 기능 대체 방법

### 1. ROWNUM → LIMIT/OFFSET
```sql
-- Oracle
SELECT * FROM employees WHERE ROWNUM <= 10;

-- PostgreSQL 16
SELECT * FROM employees LIMIT 10;

-- 페이지네이션
SELECT * FROM employees LIMIT 10 OFFSET 20;
```

### 2. CONNECT BY → WITH RECURSIVE
```sql
-- Oracle
SELECT employee_id, manager_id, LEVEL
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;

-- PostgreSQL 16
WITH RECURSIVE emp_hierarchy AS (
  SELECT employee_id, manager_id, 1 as level
  FROM employees
  WHERE manager_id IS NULL
  
  UNION ALL
  
  SELECT e.employee_id, e.manager_id, eh.level + 1
  FROM employees e
  INNER JOIN emp_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM emp_hierarchy;
```

### 3. DECODE → CASE
```sql
-- Oracle
SELECT DECODE(status, 'A', 'Active', 'I', 'Inactive', 'Unknown') FROM orders;

-- PostgreSQL 16
SELECT CASE status 
  WHEN 'A' THEN 'Active' 
  WHEN 'I' THEN 'Inactive' 
  ELSE 'Unknown' 
END FROM orders;
```

### 4. MERGE → INSERT ON CONFLICT
```sql
-- Oracle
MERGE INTO target t
USING source s ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.value = s.value
WHEN NOT MATCHED THEN INSERT (id, value) VALUES (s.id, s.value);

-- PostgreSQL 16
INSERT INTO target (id, value)
SELECT id, value FROM source
ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value;
```

### 5. PIVOT → crosstab 또는 CASE
```sql
-- Oracle
SELECT * FROM (
  SELECT product, category, amount FROM sales
)
PIVOT (SUM(amount) FOR category IN ('Electronics', 'Clothing', 'Food'));

-- PostgreSQL 16 (tablefunc 확장 사용)
SELECT * FROM crosstab(
  'SELECT product, category, SUM(amount) FROM sales GROUP BY product, category ORDER BY 1,2',
  'SELECT DISTINCT category FROM sales ORDER BY 1'
) AS ct(product TEXT, "Electronics" NUMERIC, "Clothing" NUMERIC, "Food" NUMERIC);

-- 또는 CASE 사용
SELECT product,
  SUM(CASE WHEN category = 'Electronics' THEN amount END) as "Electronics",
  SUM(CASE WHEN category = 'Clothing' THEN amount END) as "Clothing",
  SUM(CASE WHEN category = 'Food' THEN amount END) as "Food"
FROM sales
GROUP BY product;
```

## PostgreSQL 16+ 신규 기능 활용

### 1. 증분 정렬 활용
```sql
-- 대용량 데이터 정렬 시 성능 향상
SELECT * FROM large_table
ORDER BY category, created_at DESC
LIMIT 100;

-- PostgreSQL 16은 category로 먼저 정렬 후 각 그룹 내에서만 created_at 정렬
```

### 2. 병렬 쿼리 개선
```sql
-- FULL/RIGHT JOIN도 병렬 처리 가능
SET max_parallel_workers_per_gather = 4;

SELECT /*+ PARALLEL(4) */ a.*, b.*
FROM large_table_a a
FULL OUTER JOIN large_table_b b ON a.id = b.id;
```

### 3. 논리적 복제로 마이그레이션
```sql
-- 발행자 (Oracle 대체 소스)
CREATE PUBLICATION migration_pub FOR ALL TABLES;

-- 구독자 (Aurora PostgreSQL)
CREATE SUBSCRIPTION migration_sub
CONNECTION 'host=source_host dbname=source_db'
PUBLICATION migration_pub;
```

### 4. 정규 표현식 성능 개선
```sql
-- PostgreSQL 16에서 성능 향상
SELECT * FROM logs
WHERE message ~ '^ERROR.*database.*connection';
```

## Aurora 특화 기능 활용

### 1. Fast Cloning으로 테스트 환경 구성
```bash
# AWS CLI로 빠른 클론 생성
aws rds create-db-cluster \
  --db-cluster-identifier test-cluster \
  --restore-type copy-on-write \
  --source-db-cluster-identifier prod-cluster
```

### 2. Performance Insights 활용
```sql
-- 느린 쿼리 식별
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 3. Aurora Machine Learning 통합
```sql
-- SageMaker 엔드포인트 호출 (예시)
SELECT customer_id, 
       aws_sagemaker.invoke_endpoint(
         'churn-prediction-endpoint',
         json_build_object('features', ARRAY[age, tenure, monthly_charges])
       ) as churn_probability
FROM customers;
```

### 4. Query Plan Management
```sql
-- 실행 계획 고정
CREATE EXTENSION pg_hint_plan;

-- 힌트 사용
/*+ SeqScan(employees) */
SELECT * FROM employees WHERE department = 'IT';
```

## 성능 최적화 고려사항

### 1. 인덱스 전략
```sql
-- B-tree 인덱스 (기본)
CREATE INDEX idx_employee_dept ON employees(department);

-- 부분 인덱스 (조건부)
CREATE INDEX idx_active_employees ON employees(department)
WHERE status = 'ACTIVE';

-- 표현식 인덱스
CREATE INDEX idx_lower_email ON employees(LOWER(email));

-- BRIN 인덱스 (시계열 데이터)
CREATE INDEX idx_orders_date ON orders USING BRIN(order_date);
```

### 2. 파티셔닝 (PostgreSQL 16)
```sql
-- 범위 파티셔닝
CREATE TABLE orders (
  order_id BIGINT,
  order_date DATE,
  amount NUMERIC
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

### 3. Aurora 읽기 복제본 활용
```sql
-- 읽기 전용 엔드포인트 사용
-- Reader Endpoint: cluster-name.cluster-ro-xxxxx.region.rds.amazonaws.com
-- Writer Endpoint: cluster-name.cluster-xxxxx.region.rds.amazonaws.com

-- 읽기 쿼리는 Reader Endpoint로 분산
SELECT * FROM employees WHERE department = 'IT';

-- 쓰기 쿼리는 Writer Endpoint로
INSERT INTO employees (name, department) VALUES ('John', 'IT');
```

### 4. 연결 풀링 최적화
```sql
-- PostgreSQL 연결 설정 확인
SHOW max_connections;
SHOW shared_buffers;

-- Aurora 권장 설정
-- max_connections: 인스턴스 크기에 따라 자동 조정
-- shared_buffers: {DBInstanceClassMemory/10922} (자동)

-- 연결 상태 모니터링
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
```

### 5. 쿼리 최적화
```sql
-- CTE 구체화 제어 (PostgreSQL 16)
WITH materialized_cte AS MATERIALIZED (
  SELECT department, COUNT(*) as emp_count
  FROM employees
  GROUP BY department
)
SELECT * FROM materialized_cte WHERE emp_count > 10;

-- 또는 구체화 방지
WITH not_materialized_cte AS NOT MATERIALIZED (
  SELECT * FROM small_lookup_table
)
SELECT * FROM large_table l
JOIN not_materialized_cte n ON l.code = n.code;
```

### 6. VACUUM 및 ANALYZE
```sql
-- 정기적인 유지보수
VACUUM ANALYZE employees;

-- 자동 VACUUM 설정 조정
ALTER TABLE employees SET (
  autovacuum_vacuum_scale_factor = 0.1,
  autovacuum_analyze_scale_factor = 0.05
);
```

### 7. Aurora 모니터링
```sql
-- 활성 쿼리 모니터링
SELECT pid, usename, state, query, query_start
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- 테이블 통계
SELECT schemaname, tablename, 
       n_live_tup, n_dead_tup,
       last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

## 마이그레이션 체크리스트

- [ ] AWS SCT로 스키마 변환 완료
- [ ] 쿼리 복잡도 분석 완료
- [ ] 높은 복잡도 쿼리 재작성 완료
- [ ] DMS 복제 작업 설정 완료
- [ ] 테스트 데이터 마이그레이션 검증
- [ ] 성능 테스트 완료
- [ ] 인덱스 최적화 완료
- [ ] 애플리케이션 연결 테스트 완료
- [ ] 롤백 계획 수립 완료
- [ ] 프로덕션 마이그레이션 실행
- [ ] Performance Insights 모니터링 설정
- [ ] 운영 문서 업데이트

## 참고 자료

- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [AWS Schema Conversion Tool](https://aws.amazon.com/dms/schema-conversion-tool/)
- [Aurora PostgreSQL 문서](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.html)
- [PostgreSQL 16 릴리스 노트](https://www.postgresql.org/docs/16/release-16.html)
