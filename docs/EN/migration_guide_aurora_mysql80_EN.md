# Oracle to Aurora MySQL 8.0.43 Migration Guide

This guide focuses on query conversion and leveraging the latest features when migrating from Oracle Database to Amazon Aurora MySQL version 8.0.43.

> [한국어](../migration_guide_aurora_mysql80.md)

## Table of Contents

1. [Aurora MySQL 8.0.43 Key Features](#aurora-mysql-8043-key-features)
2. [Migration Overview](#migration-overview)
3. [Approach by Query Complexity](#approach-by-query-complexity)
4. [Oracle-Specific Feature Alternatives](#oracle-specific-feature-alternatives)
5. [Leveraging MySQL 8.0 Key Features](#leveraging-mysql-80-key-features)
6. [Leveraging Aurora-Specific Features](#leveraging-aurora-specific-features)
7. [Performance Optimization Considerations](#performance-optimization-considerations)

## Aurora MySQL 8.0.43 Key Features

You can perform Oracle migration efficiently by leveraging MySQL 8.0 and Aurora features:

### MySQL 8.0 Key Features
- **Window Functions**: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, etc.
- **CTE (Common Table Expressions)**: WITH clause and recursive query support
- **JSON Functions**: JSON data type and various JSON functions
- **Enhanced Indexes**: Descending Index, Invisible Index
- **Performance Improvements**: Query optimizer and index performance enhancements

### Aurora MySQL-Specific Features
- **Aurora Machine Learning**: Direct ML model invocation from SQL
- **Fast Cloning**: Quick database cloning for test environment setup
- **Global Database**: Multi-region disaster recovery
- **Performance Insights**: Real-time performance monitoring
- **Parallel Query**: Parallel processing for large analytical queries
- **Backtrack**: Fast rollback to specific point in time

## Migration Overview

### 1. Assessment and Planning
- **Use AWS Schema Conversion Tool (SCT)**
  - Automatic schema and code conversion
  - Identify non-convertible items
  - Generate complexity assessment reports
- **Use Oracle to MySQL Query Analyzer**
  - Analyze query complexity
  - Determine conversion priorities

### 2. Schema Conversion
```sql
-- Oracle Data Type → MySQL Mapping
NUMBER → DECIMAL or INT
NUMBER(p,s) → DECIMAL(p,s)
VARCHAR2 → VARCHAR
DATE → DATETIME
TIMESTAMP → DATETIME(6)
CLOB → LONGTEXT
BLOB → LONGBLOB
RAW → VARBINARY
```

### 3. Data Migration
- **Leverage AWS Database Migration Service (DMS)**
  - Initial full load
  - Continuous Change Data Capture (CDC)
  - Minimal downtime migration

### 4. Validation and Optimization
- Data integrity validation
- Performance testing and tuning
- Monitor with Aurora Performance Insights

## Approach by Query Complexity

### Very Simple (0-1)
- AWS SCT automatic conversion
- Fix only basic syntax differences
- Example: `NVL → IFNULL`, `SYSDATE → NOW()`

### Simple (1-3)
- AWS SCT + manual review
- Function replacement needed
- Example: `TO_CHAR → DATE_FORMAT`

### Medium (3-5)
- Partial rewrite needed
- Review MySQL 8.0 feature utilization
- Example: `CONNECT BY → WITH RECURSIVE`

### Complex (5-7)
- Significant rewrite needed
- Review Aurora-specific feature utilization
- Expert review recommended

### Very Complex (7-9)
- Most rewrite needed
- Consider architecture redesign
- AWS Professional Services recommended

### Extremely Complex (9-10)
- Complete redesign needed
- Review business logic
- Establish phased migration strategy

## Oracle-Specific Feature Alternatives

### 1. ROWNUM → LIMIT
```sql
-- Oracle
SELECT * FROM employees WHERE ROWNUM <= 10;

-- MySQL 8.0
SELECT * FROM employees LIMIT 10;

-- Pagination
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

-- Or MySQL 8.0.19+ syntax (clearer)
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
-- Or
SELECT COALESCE(commission, 0) FROM employees;
```

### 8. DUAL Table
```sql
-- Oracle
SELECT SYSDATE FROM DUAL;

-- MySQL 8.0 (DUAL table not needed)
SELECT NOW();
```

## Leveraging MySQL 8.0 Key Features

### 1. Window Functions
```sql
-- Salary ranking by department
SELECT 
  employee_id,
  department,
  salary,
  ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num,
  RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank_num,
  DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rank_num
FROM employees;

-- Reference previous/next rows with LAG/LEAD
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
-- Handle hierarchical structures with recursive CTE
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

-- Simplify complex queries with non-recursive CTE
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

### 3. JSON Functions
```sql
-- Create JSON data
SELECT JSON_OBJECT('name', name, 'salary', salary) as employee_json
FROM employees;

-- Create JSON array
SELECT JSON_ARRAY(name, department, salary) as employee_array
FROM employees;

-- Extract values by JSON path
SELECT 
  id,
  JSON_EXTRACT(data, '$.customer.name') as customer_name,
  data->>'$.customer.email' as customer_email
FROM orders;

-- Check JSON array elements
SELECT * FROM products
WHERE JSON_CONTAINS(tags, '"electronics"');
```

### 4. Enhanced Indexes
```sql
-- Descending index
CREATE INDEX idx_salary_desc ON employees(salary DESC);

-- Invisible index (for testing)
CREATE INDEX idx_test ON employees(department) INVISIBLE;

-- Activate index
ALTER TABLE employees ALTER INDEX idx_test VISIBLE;

-- Function-based index
CREATE INDEX idx_year ON orders((YEAR(order_date)));
```

## Leveraging Aurora-Specific Features

### 1. Test Environment Setup with Fast Cloning
```bash
# Create fast clone with AWS CLI
aws rds create-db-cluster \
  --db-cluster-identifier test-cluster \
  --restore-type copy-on-write \
  --source-db-cluster-identifier prod-cluster \
  --engine aurora-mysql
```

### 2. Leverage Performance Insights
```sql
-- Identify slow queries
SELECT 
  DIGEST_TEXT,
  COUNT_STAR as exec_count,
  AVG_TIMER_WAIT/1000000000000 as avg_time_sec,
  SUM_ROWS_EXAMINED as rows_examined
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;
```

### 3. Aurora Machine Learning Integration
```sql
-- Call SageMaker endpoint (example)
SELECT customer_id,
       aws_ml_predict_sagemaker(
         'churn-prediction-endpoint',
         JSON_OBJECT('age', age, 'tenure', tenure, 'charges', monthly_charges)
       ) as churn_probability
FROM customers;
```

### 4. Leverage Parallel Query
```sql
-- Parallel processing for large table scans
-- Aurora automatically applies parallel query (when specific conditions are met)
SELECT department, COUNT(*), AVG(salary)
FROM large_employee_table
WHERE hire_date > '2020-01-01'
GROUP BY department;

-- Check Parallel Query status
SHOW STATUS LIKE 'Aurora_pq%';
```

### 5. Backtrack Feature
```bash
# Fast rollback to specific point in time (data recovery)
aws rds backtrack-db-cluster \
  --db-cluster-identifier my-cluster \
  --backtrack-to "2024-01-13T10:00:00Z"
```

## Performance Optimization Considerations

### 1. Index Strategy
```sql
-- B-tree index (default)
CREATE INDEX idx_employee_dept ON employees(department);

-- Composite index
CREATE INDEX idx_dept_salary ON employees(department, salary);

-- Full-text search index
CREATE FULLTEXT INDEX idx_description ON products(description);

-- Spatial index
CREATE SPATIAL INDEX idx_location ON stores(location);

-- Verify index usage
EXPLAIN SELECT * FROM employees WHERE department = 'IT';
```

### 2. Partitioning
```sql
-- Range partitioning
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

-- List partitioning
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

-- Hash partitioning
CREATE TABLE logs (
  id BIGINT,
  message TEXT,
  created_at DATETIME
)
PARTITION BY HASH(id)
PARTITIONS 4;
```

### 3. Leverage Aurora Read Replicas
```sql
-- Use read-only endpoint
-- Reader Endpoint: cluster-name.cluster-ro-xxxxx.region.rds.amazonaws.com
-- Writer Endpoint: cluster-name.cluster-xxxxx.region.rds.amazonaws.com

-- Distribute read queries to Reader Endpoint
SELECT * FROM employees WHERE department = 'IT';

-- Write queries to Writer Endpoint
INSERT INTO employees (name, department) VALUES ('John', 'IT');
```

### 4. Connection Pooling Optimization
```sql
-- Check MySQL connection settings
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'thread_cache_size';

-- Aurora recommended settings
-- max_connections: Auto-adjusted based on instance size
-- thread_cache_size: Auto-managed

-- Monitor connection status
SHOW PROCESSLIST;

-- Or
SELECT * FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep';
```

### 5. Query Optimization
```sql
-- Analyze execution plan
EXPLAIN FORMAT=JSON
SELECT e.name, d.department_name
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.salary > 50000;

-- Query profiling
SET profiling = 1;
SELECT * FROM large_table WHERE condition = 'value';
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;

-- Use optimizer hints
SELECT /*+ MAX_EXECUTION_TIME(1000) */ *
FROM employees
WHERE department = 'IT';
```

### 6. Table Optimization
```sql
-- Analyze table (update statistics)
ANALYZE TABLE employees;

-- Optimize table (defragmentation)
OPTIMIZE TABLE employees;

-- Check table status
SHOW TABLE STATUS LIKE 'employees';

-- InnoDB buffer pool status
SHOW STATUS LIKE 'Innodb_buffer_pool%';
```

### 7. Aurora Monitoring
```sql
-- Monitor active queries
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

-- Table statistics
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

-- Index usage statistics
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

### 8. Caching Strategy
```sql
-- Query cache (removed in MySQL 8.0, recommend application-level caching instead)
-- Check InnoDB buffer pool settings
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- Check buffer pool hit rate
SHOW STATUS LIKE 'Innodb_buffer_pool_read%';
```

## Migration Checklist

- [ ] Schema conversion completed with AWS SCT
- [ ] Query complexity analysis completed
- [ ] High complexity query rewrite completed
- [ ] DMS replication task setup completed
- [ ] Test data migration validated
- [ ] Performance testing completed
- [ ] Index optimization completed
- [ ] Application connection testing completed
- [ ] Rollback plan established
- [ ] Production migration executed
- [ ] Performance Insights monitoring configured
- [ ] Operations documentation updated

## Key Differences Between Oracle and MySQL

### 1. Transaction Handling
```sql
-- Oracle: Auto-commit disabled (default)
-- MySQL: Auto-commit enabled (default)

-- Explicit transaction in MySQL
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

### 2. NULL Handling
```sql
-- Oracle: Treats empty string ('') as NULL
-- MySQL: Distinguishes between empty string ('') and NULL

-- Be careful in MySQL
SELECT * FROM users WHERE email = '';  -- Empty string
SELECT * FROM users WHERE email IS NULL;  -- NULL
```

### 3. String Concatenation
```sql
-- Oracle
SELECT first_name || ' ' || last_name FROM employees;

-- MySQL
SELECT CONCAT(first_name, ' ', last_name) FROM employees;
```

### 4. Date Functions
```sql
-- Oracle
SELECT SYSDATE, TRUNC(SYSDATE), ADD_MONTHS(SYSDATE, 1) FROM DUAL;

-- MySQL
SELECT NOW(), DATE(NOW()), DATE_ADD(NOW(), INTERVAL 1 MONTH);
```

### 5. Case Sensitivity
```sql
-- Oracle: Case-insensitive by default (configurable)
-- MySQL: Table names depend on OS, column names are case-insensitive

-- Case sensitivity settings in MySQL
-- lower_case_table_names = 0 (Unix: case-sensitive)
-- lower_case_table_names = 1 (Windows: case-insensitive)
```

## References

- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [AWS Schema Conversion Tool](https://aws.amazon.com/dms/schema-conversion-tool/)
- [Aurora MySQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraMySQL.html)
- [MySQL 8.0 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/)
- [Oracle to MySQL Migration Guide](https://docs.aws.amazon.com/dms/latest/oracle-to-aurora-mysql-migration-playbook/chap-oracle-aurora-mysql.html)
