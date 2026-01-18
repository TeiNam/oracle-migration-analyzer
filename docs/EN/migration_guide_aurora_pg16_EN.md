# Oracle to Aurora PostgreSQL 16 Migration Guide

This guide focuses on query conversion and leveraging the latest features when migrating from Oracle Database to Amazon Aurora PostgreSQL version 16 and above.

> [한국어](../migration_guide_aurora_pg16.md)

## Table of Contents

1. [Aurora PostgreSQL 16+ Key Features](#aurora-postgresql-16-key-features)
2. [Migration Overview](#migration-overview)
3. [Approach by Query Complexity](#approach-by-query-complexity)
4. [Oracle-Specific Feature Alternatives](#oracle-specific-feature-alternatives)
5. [Leveraging PostgreSQL 16+ New Features](#leveraging-postgresql-16-new-features)
6. [Leveraging Aurora-Specific Features](#leveraging-aurora-specific-features)
7. [Performance Optimization Considerations](#performance-optimization-considerations)

## Aurora PostgreSQL 16+ Key Features

You can perform Oracle migration more efficiently by leveraging PostgreSQL 16 and Aurora's latest features:

### PostgreSQL 16 New Features
- **Logical Replication Improvements**: Bidirectional replication support for easier data synchronization during migration
- **Incremental Sort Improvements**: Enhanced performance for large data sorting
- **Parallel Query Improvements**: FULL/RIGHT JOIN parallel processing support
- **COPY Performance Improvements**: Faster large data loading
- **Regular Expression Performance Improvements**: Optimized complex pattern matching

### Aurora PostgreSQL-Specific Features
- **Babelfish for Aurora PostgreSQL**: T-SQL compatibility (not direct Oracle support)
- **Aurora Machine Learning**: Direct ML model invocation from SQL
- **Fast Cloning**: Quick database cloning for test environment setup
- **Global Database**: Multi-region disaster recovery
- **Performance Insights**: Real-time performance monitoring

## Migration Overview

### 1. Assessment and Planning
- **Use AWS Schema Conversion Tool (SCT)**
  - Automatic schema and code conversion
  - Identify non-convertible items
  - Generate complexity assessment reports
- **Use Oracle to PostgreSQL Query Analyzer**
  - Analyze query complexity
  - Determine conversion priorities

### 2. Schema Conversion
```sql
-- Oracle Data Type → PostgreSQL Mapping
NUMBER → NUMERIC or INTEGER
VARCHAR2 → VARCHAR
DATE → TIMESTAMP
CLOB → TEXT
BLOB → BYTEA
RAW → BYTEA
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
- Example: `NVL → COALESCE`, `SYSDATE → CURRENT_TIMESTAMP`

### Simple (1-3)
- AWS SCT + manual review
- Function replacement needed
- Example: `TO_CHAR → TO_CHAR` (adjust format strings)

### Medium (3-5)
- Partial rewrite needed
- Review PostgreSQL 16 new feature utilization
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

### 1. ROWNUM → LIMIT/OFFSET
```sql
-- Oracle
SELECT * FROM employees WHERE ROWNUM <= 10;

-- PostgreSQL 16
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

### 5. PIVOT → crosstab or CASE
```sql
-- Oracle
SELECT * FROM (
  SELECT product, category, amount FROM sales
)
PIVOT (SUM(amount) FOR category IN ('Electronics', 'Clothing', 'Food'));

-- PostgreSQL 16 (using tablefunc extension)
SELECT * FROM crosstab(
  'SELECT product, category, SUM(amount) FROM sales GROUP BY product, category ORDER BY 1,2',
  'SELECT DISTINCT category FROM sales ORDER BY 1'
) AS ct(product TEXT, "Electronics" NUMERIC, "Clothing" NUMERIC, "Food" NUMERIC);

-- Or using CASE
SELECT product,
  SUM(CASE WHEN category = 'Electronics' THEN amount END) as "Electronics",
  SUM(CASE WHEN category = 'Clothing' THEN amount END) as "Clothing",
  SUM(CASE WHEN category = 'Food' THEN amount END) as "Food"
FROM sales
GROUP BY product;
```

## Leveraging PostgreSQL 16+ New Features

### 1. Leverage Incremental Sort
```sql
-- Performance improvement for large data sorting
SELECT * FROM large_table
ORDER BY category, created_at DESC
LIMIT 100;

-- PostgreSQL 16 sorts by category first, then created_at within each group
```

### 2. Parallel Query Improvements
```sql
-- FULL/RIGHT JOIN can also be parallelized
SET max_parallel_workers_per_gather = 4;

SELECT /*+ PARALLEL(4) */ a.*, b.*
FROM large_table_a a
FULL OUTER JOIN large_table_b b ON a.id = b.id;
```

### 3. Logical Replication for Migration
```sql
-- Publisher (Oracle replacement source)
CREATE PUBLICATION migration_pub FOR ALL TABLES;

-- Subscriber (Aurora PostgreSQL)
CREATE SUBSCRIPTION migration_sub
CONNECTION 'host=source_host dbname=source_db'
PUBLICATION migration_pub;
```

### 4. Regular Expression Performance Improvements
```sql
-- Performance improvement in PostgreSQL 16
SELECT * FROM logs
WHERE message ~ '^ERROR.*database.*connection';
```

## Leveraging Aurora-Specific Features

### 1. Test Environment Setup with Fast Cloning
```bash
# Create fast clone with AWS CLI
aws rds create-db-cluster \
  --db-cluster-identifier test-cluster \
  --restore-type copy-on-write \
  --source-db-cluster-identifier prod-cluster
```

### 2. Leverage Performance Insights
```sql
-- Identify slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 3. Aurora Machine Learning Integration
```sql
-- Call SageMaker endpoint (example)
SELECT customer_id, 
       aws_sagemaker.invoke_endpoint(
         'churn-prediction-endpoint',
         json_build_object('features', ARRAY[age, tenure, monthly_charges])
       ) as churn_probability
FROM customers;
```

### 4. Query Plan Management
```sql
-- Fix execution plan
CREATE EXTENSION pg_hint_plan;

-- Use hints
/*+ SeqScan(employees) */
SELECT * FROM employees WHERE department = 'IT';
```

## Performance Optimization Considerations

### 1. Index Strategy
```sql
-- B-tree index (default)
CREATE INDEX idx_employee_dept ON employees(department);

-- Partial index (conditional)
CREATE INDEX idx_active_employees ON employees(department)
WHERE status = 'ACTIVE';

-- Expression index
CREATE INDEX idx_lower_email ON employees(LOWER(email));

-- BRIN index (time-series data)
CREATE INDEX idx_orders_date ON orders USING BRIN(order_date);
```

### 2. Partitioning (PostgreSQL 16)
```sql
-- Range partitioning
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
-- Check PostgreSQL connection settings
SHOW max_connections;
SHOW shared_buffers;

-- Aurora recommended settings
-- max_connections: Auto-adjusted based on instance size
-- shared_buffers: {DBInstanceClassMemory/10922} (automatic)

-- Monitor connection status
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
```

### 5. Query Optimization
```sql
-- Control CTE materialization (PostgreSQL 16)
WITH materialized_cte AS MATERIALIZED (
  SELECT department, COUNT(*) as emp_count
  FROM employees
  GROUP BY department
)
SELECT * FROM materialized_cte WHERE emp_count > 10;

-- Or prevent materialization
WITH not_materialized_cte AS NOT MATERIALIZED (
  SELECT * FROM small_lookup_table
)
SELECT * FROM large_table l
JOIN not_materialized_cte n ON l.code = n.code;
```

### 6. VACUUM and ANALYZE
```sql
-- Regular maintenance
VACUUM ANALYZE employees;

-- Adjust auto VACUUM settings
ALTER TABLE employees SET (
  autovacuum_vacuum_scale_factor = 0.1,
  autovacuum_analyze_scale_factor = 0.05
);
```

### 7. Aurora Monitoring
```sql
-- Monitor active queries
SELECT pid, usename, state, query, query_start
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Table statistics
SELECT schemaname, tablename, 
       n_live_tup, n_dead_tup,
       last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
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

## References

- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [AWS Schema Conversion Tool](https://aws.amazon.com/dms/schema-conversion-tool/)
- [Aurora PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.html)
- [PostgreSQL 16 Release Notes](https://www.postgresql.org/docs/16/release-16.html)
