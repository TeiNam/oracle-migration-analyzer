# Oracle에서 Aurora MySQL 8.0.43으로의 마이그레이션 가이드

이 문서는 Oracle 데이터베이스에서 Amazon Aurora MySQL 8.0.43 버전으로 마이그레이션하는 과정에서 쿼리 변환 및 최신 기능 활용에 초점을 맞춘 가이드입니다.

## 목차

1. [Aurora MySQL 8.0.43 주요 기능](#aurora-mysql-8043-주요-기능)
2. [마이그레이션 개요](#마이그레이션-개요)
3. [쿼리 복잡도에 따른 접근 방식](#쿼리-복잡도에-따른-접근-방식)
4. [Oracle 특화 기능 대체 방법](#oracle-특화-기능-대체-방법)
5. [MySQL 8.0 주요 기능 활용](#mysql-80-주요-기능-활용)
6. [Aurora 특화 기능 활용](#aurora-특화-기능-활용)
7. [성능 최적화 고려사항](#성능-최적화-고려사항)

## Aurora MySQL 8.0.43 주요 기능

MySQL 8.0과 Aurora의 기능들을 활용하여 Oracle 마이그레이션을 효율적으로 수행할 수 있습니다:

### MySQL 8.0 주요 기능
- **윈도우 함수**: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD 등
- **CTE (Common Table Expressions)**: WITH 절 및 재귀 쿼리 지원
- **JSON 함수**: JSON 데이터 타입 및 다양한 JSON 함수
- **향상된 인덱스**: Descending Index, Invisible Index
- **성능 개선**: 쿼리 옵티마이저 및 인덱스 성능 향상

### Aurora MySQL 특화 기능
- **Aurora Machine Learning**: SQL에서 직접 ML 모델 호출
- **Fast Cloning**: 빠른 데이터베이스 복제로 테스트 환경 구성
- **Global Database**: 다중 리전 재해 복구
- **Performance Insights**: 실시간 성능 모니터링
- **Parallel Query**: 대용량 분석 쿼리 병렬 처리
- **Backtrack**: 특정 시점으로 빠른 롤백

## 마이그레이션 개요

### 1. 평가 및 계획
- **AWS Schema Conversion Tool (SCT)** 사용
  - 스키마 및 코드 자동 변환
  - 변환 불가능한 항목 식별
  - 복잡도 평가 리포트 생성
- **Oracle to MySQL Query Analyzer** 사용
  - 쿼리 복잡도 분석
  - 변환 우선순위 결정

### 2. 스키마 변환
```sql
-- Oracle 데이터 타입 → MySQL 매핑
NUMBER → DECIMAL 또는 INT
NUMBER(p,s) → DECIMAL(p,s)
VARCHAR2 → VARCHAR
DATE → DATETIME
TIMESTAMP → DATETIME(6)
CLOB → LONGTEXT
BLOB → LONGBLOB
RAW → VARBINARY
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
- 예: `NVL → IFNULL`, `SYSDATE → NOW()`

### 간단 (1-3)
- AWS SCT + 수동 검토
- 함수 대체 필요
- 예: `TO_CHAR → DATE_FORMAT`

### 중간 (3-5)
- 부분 재작성 필요
- MySQL 8.0 기능 활용 검토
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

### 1. ROWNUM → LIMIT
```sql
-- Oracle
SELECT * FROM employees WHERE ROWNUM <= 10;

-- MySQL 8.0
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

-- MySQL 8.0
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

-- MySQL 8.0
SELECT CASE status 
  WHEN 'A' THEN 'Active' 
  WHEN 'I' THEN 'Inactive' 
  ELSE 'Unknown' 
END FROM orders;
```

### 4. MERGE → INSERT ON DUPLICATE KEY UPDATE
```sql
-- Oracle
MERGE INTO target t
USING source s ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.value = s.value
WHEN NOT MATCHED THEN INSERT (id, value) VALUES (s.id, s.value);

-- MySQL 8.0
INSERT INTO target (id, value)
SELECT id, value FROM source
ON DUPLICATE KEY UPDATE value = VALUES(value);

-- 또는 MySQL 8.0.19+ 방식 (더 명확한 문법)
INSERT INTO target (id, value)
SELECT id, value FROM source AS new
ON DUPLICATE KEY UPDATE value = new.value;
```

### 5. PIVOT → GROUP BY with CASE
```sql
-- Oracle
SELECT * FROM (
  SELECT product, category, amount FROM sales
)
PIVOT (SUM(amount) FOR category IN ('Electronics', 'Clothing', 'Food'));

-- MySQL 8.0
SELECT product,
  SUM(CASE WHEN category = 'Electronics' THEN amount END) as Electronics,
  SUM(CASE WHEN category = 'Clothing' THEN amount END) as Clothing,
  SUM(CASE WHEN category = 'Food' THEN amount END) as Food
FROM sales
GROUP BY product;
```

### 6. SEQUENCE → AUTO_INCREMENT
```sql
-- Oracle
CREATE SEQUENCE emp_seq START WITH 1 INCREMENT BY 1;
INSERT INTO employees (id, name) VALUES (emp_seq.NEXTVAL, 'John');

-- MySQL 8.0
CREATE TABLE employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100)
);
INSERT INTO employees (name) VALUES ('John');
```

### 7. NVL/NVL2 → IFNULL/IF
```sql
-- Oracle
SELECT NVL(commission, 0) FROM employees;
SELECT NVL2(commission, commission * 1.1, 0) FROM employees;

-- MySQL 8.0
SELECT IFNULL(commission, 0) FROM employees;
SELECT IF(commission IS NOT NULL, commission * 1.1, 0) FROM employees;
-- 또는
SELECT COALESCE(commission, 0) FROM employees;
```

### 8. DUAL 테이블
```sql
-- Oracle
SELECT SYSDATE FROM DUAL;

-- MySQL 8.0 (DUAL 테이블 불필요)
SELECT NOW();
```

## MySQL 8.0 주요 기능 활용

### 1. 윈도우 함수
```sql
-- 각 부서별 급여 순위
SELECT 
  employee_id,
  department,
  salary,
  ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num,
  RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank_num,
  DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rank_num
FROM employees;

-- LAG/LEAD 함수로 이전/다음 행 참조
SELECT 
  order_id,
  order_date,
  amount,
  LAG(amount) OVER (ORDER BY order_date) as prev_amount,
  LEAD(amount) OVER (ORDER BY order_date) as next_amount
FROM orders;
```

### 2. CTE (Common Table Expression)
```sql
-- 재귀 CTE로 계층 구조 처리
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 1 as level
  FROM categories
  WHERE parent_id IS NULL
  
  UNION ALL
  
  SELECT c.id, c.name, c.parent_id, ct.level + 1
  FROM categories c
  INNER JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;

-- 비재귀 CTE로 복잡한 쿼리 단순화
WITH 
  sales_summary AS (
    SELECT product_id, SUM(amount) as total_sales
    FROM orders
    WHERE order_date >= '2024-01-01'
    GROUP BY product_id
  ),
  top_products AS (
    SELECT product_id, total_sales
    FROM sales_summary
    WHERE total_sales > 10000
  )
SELECT p.name, tp.total_sales
FROM top_products tp
JOIN products p ON tp.product_id = p.id;
```

### 3. JSON 함수
```sql
-- JSON 데이터 생성
SELECT JSON_OBJECT('name', name, 'salary', salary) as employee_json
FROM employees;

-- JSON 배열 생성
SELECT JSON_ARRAY(name, department, salary) as employee_array
FROM employees;

-- JSON 경로로 값 추출
SELECT 
  id,
  JSON_EXTRACT(data, '$.customer.name') as customer_name,
  data->>'$.customer.email' as customer_email
FROM orders;

-- JSON 배열 요소 확인
SELECT * FROM products
WHERE JSON_CONTAINS(tags, '"electronics"');
```

### 4. 향상된 인덱스
```sql
-- 내림차순 인덱스
CREATE INDEX idx_salary_desc ON employees(salary DESC);

-- 보이지 않는 인덱스 (테스트용)
CREATE INDEX idx_test ON employees(department) INVISIBLE;

-- 인덱스 활성화
ALTER TABLE employees ALTER INDEX idx_test VISIBLE;

-- 함수 기반 인덱스
CREATE INDEX idx_year ON orders((YEAR(order_date)));
```

## Aurora 특화 기능 활용

### 1. Fast Cloning으로 테스트 환경 구성
```bash
# AWS CLI로 빠른 클론 생성
aws rds create-db-cluster \
  --db-cluster-identifier test-cluster \
  --restore-type copy-on-write \
  --source-db-cluster-identifier prod-cluster \
  --engine aurora-mysql
```

### 2. Performance Insights 활용
```sql
-- 느린 쿼리 식별
SELECT 
  DIGEST_TEXT,
  COUNT_STAR as exec_count,
  AVG_TIMER_WAIT/1000000000000 as avg_time_sec,
  SUM_ROWS_EXAMINED as rows_examined
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;
```

### 3. Aurora Machine Learning 통합
```sql
-- SageMaker 엔드포인트 호출 (예시)
SELECT customer_id,
       aws_ml_predict_sagemaker(
         'churn-prediction-endpoint',
         JSON_OBJECT('age', age, 'tenure', tenure, 'charges', monthly_charges)
       ) as churn_probability
FROM customers;
```

### 4. Parallel Query 활용
```sql
-- 대용량 테이블 스캔 시 병렬 처리
-- Aurora가 자동으로 병렬 쿼리 적용 (특정 조건 충족 시)
SELECT department, COUNT(*), AVG(salary)
FROM large_employee_table
WHERE hire_date > '2020-01-01'
GROUP BY department;

-- Parallel Query 상태 확인
SHOW STATUS LIKE 'Aurora_pq%';
```

### 5. Backtrack 기능
```bash
# 특정 시점으로 빠른 롤백 (데이터 복구)
aws rds backtrack-db-cluster \
  --db-cluster-identifier my-cluster \
  --backtrack-to "2024-01-13T10:00:00Z"
```

## 성능 최적화 고려사항

### 1. 인덱스 전략
```sql
-- B-tree 인덱스 (기본)
CREATE INDEX idx_employee_dept ON employees(department);

-- 복합 인덱스
CREATE INDEX idx_dept_salary ON employees(department, salary);

-- 전문 검색 인덱스
CREATE FULLTEXT INDEX idx_description ON products(description);

-- 공간 인덱스
CREATE SPATIAL INDEX idx_location ON stores(location);

-- 인덱스 사용 확인
EXPLAIN SELECT * FROM employees WHERE department = 'IT';
```

### 2. 파티셔닝
```sql
-- 범위 파티셔닝
CREATE TABLE orders (
  order_id BIGINT,
  order_date DATE,
  amount DECIMAL(10,2)
)
PARTITION BY RANGE (YEAR(order_date)) (
  PARTITION p2022 VALUES LESS THAN (2023),
  PARTITION p2023 VALUES LESS THAN (2024),
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 리스트 파티셔닝
CREATE TABLE employees (
  id INT,
  name VARCHAR(100),
  region VARCHAR(50)
)
PARTITION BY LIST COLUMNS(region) (
  PARTITION p_north VALUES IN ('North', 'Northeast'),
  PARTITION p_south VALUES IN ('South', 'Southeast'),
  PARTITION p_west VALUES IN ('West', 'Northwest')
);

-- 해시 파티셔닝
CREATE TABLE logs (
  id BIGINT,
  message TEXT,
  created_at DATETIME
)
PARTITION BY HASH(id)
PARTITIONS 4;
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
-- MySQL 연결 설정 확인
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'thread_cache_size';

-- Aurora 권장 설정
-- max_connections: 인스턴스 크기에 따라 자동 조정
-- thread_cache_size: 자동 관리

-- 연결 상태 모니터링
SHOW PROCESSLIST;

-- 또는
SELECT * FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep';
```

### 5. 쿼리 최적화
```sql
-- 실행 계획 분석
EXPLAIN FORMAT=JSON
SELECT e.name, d.department_name
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.salary > 50000;

-- 쿼리 프로파일링
SET profiling = 1;
SELECT * FROM large_table WHERE condition = 'value';
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;

-- 옵티마이저 힌트 사용
SELECT /*+ MAX_EXECUTION_TIME(1000) */ *
FROM employees
WHERE department = 'IT';
```

### 6. 테이블 최적화
```sql
-- 테이블 분석 (통계 업데이트)
ANALYZE TABLE employees;

-- 테이블 최적화 (조각 모음)
OPTIMIZE TABLE employees;

-- 테이블 상태 확인
SHOW TABLE STATUS LIKE 'employees';

-- InnoDB 버퍼 풀 상태
SHOW STATUS LIKE 'Innodb_buffer_pool%';
```

### 7. Aurora 모니터링
```sql
-- 활성 쿼리 모니터링
SELECT 
  ID,
  USER,
  HOST,
  DB,
  COMMAND,
  TIME,
  STATE,
  INFO
FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep'
ORDER BY TIME DESC;

-- 테이블 통계
SELECT 
  TABLE_SCHEMA,
  TABLE_NAME,
  TABLE_ROWS,
  AVG_ROW_LENGTH,
  DATA_LENGTH,
  INDEX_LENGTH,
  (DATA_LENGTH + INDEX_LENGTH) as total_size
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema')
ORDER BY total_size DESC;

-- 인덱스 사용 통계
SELECT 
  OBJECT_SCHEMA,
  OBJECT_NAME,
  INDEX_NAME,
  COUNT_STAR,
  COUNT_READ,
  COUNT_WRITE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA NOT IN ('mysql', 'performance_schema')
ORDER BY COUNT_STAR DESC;
```

### 8. 캐싱 전략
```sql
-- 쿼리 캐시 (MySQL 8.0에서 제거됨, 대신 애플리케이션 레벨 캐싱 권장)
-- InnoDB 버퍼 풀 설정 확인
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- 버퍼 풀 히트율 확인
SHOW STATUS LIKE 'Innodb_buffer_pool_read%';
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

## Oracle과 MySQL 주요 차이점

### 1. 트랜잭션 처리
```sql
-- Oracle: 자동 커밋 비활성화 (기본)
-- MySQL: 자동 커밋 활성화 (기본)

-- MySQL에서 명시적 트랜잭션
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

### 2. NULL 처리
```sql
-- Oracle: 빈 문자열('')을 NULL로 처리
-- MySQL: 빈 문자열('')과 NULL을 구분

-- MySQL에서 주의
SELECT * FROM users WHERE email = '';  -- 빈 문자열
SELECT * FROM users WHERE email IS NULL;  -- NULL
```

### 3. 문자열 연결
```sql
-- Oracle
SELECT first_name || ' ' || last_name FROM employees;

-- MySQL
SELECT CONCAT(first_name, ' ', last_name) FROM employees;
```

### 4. 날짜 함수
```sql
-- Oracle
SELECT SYSDATE, TRUNC(SYSDATE), ADD_MONTHS(SYSDATE, 1) FROM DUAL;

-- MySQL
SELECT NOW(), DATE(NOW()), DATE_ADD(NOW(), INTERVAL 1 MONTH);
```

### 5. 대소문자 구분
```sql
-- Oracle: 기본적으로 대소문자 구분 안 함 (설정 가능)
-- MySQL: 테이블명은 OS에 따라 다름, 컬럼명은 구분 안 함

-- MySQL에서 대소문자 구분 설정
-- lower_case_table_names = 0 (Unix: 구분함)
-- lower_case_table_names = 1 (Windows: 구분 안 함)
```

## 참고 자료

- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [AWS Schema Conversion Tool](https://aws.amazon.com/dms/schema-conversion-tool/)
- [Aurora MySQL 문서](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraMySQL.html)
- [MySQL 8.0 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/)
- [Oracle to MySQL 마이그레이션 가이드](https://docs.aws.amazon.com/dms/latest/oracle-to-aurora-mysql-migration-playbook/chap-oracle-aurora-mysql.html)
