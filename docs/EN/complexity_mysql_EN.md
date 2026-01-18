# Oracle to MySQL Migration Complexity Calculation Formula

> [한국어](../complexity_mysql.md)

This document describes the formula for calculating the complexity of SQL queries and PL/SQL objects when migrating from Oracle to MySQL.

## MySQL Characteristics

- **Based on MySQL 8.0.42 or higher**
- **Multi-threaded architecture**: Lightweight thread-based connection handling
- **Strong for simple queries**: Excellent index-based lookup performance
- **Weak for full scans**: Performance degradation with large table full scans
- **Weak for complex JOINs**: Performance degradation with 3+ JOINs
- **COUNT(*) performance issues**: Slow with large data counts
- **Limited subquery optimization**: Especially IN clause subqueries
- **Window function support**: Supported from 8.0 but with some limitations
- **CTE support**: Supported from 8.0 but with optimization limitations
- **Stored Procedure limitations**: Compilation overhead and memory leak issues with business logic - **Application-level migration recommended**

## SQL Query Complexity Calculation

### 1. Structural Complexity (Max 4.5 points)

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score + fullscan_penalty
```

**JOIN Score**:
```
if join_count == 0: 0 points
elif join_count <= 2: 1.0 points
elif join_count <= 4: 2.0 points
elif join_count <= 6: 3.0 points
else: 4.0 points
```

**Subquery Score**:
```
if depth == 0: 0 points
elif depth == 1: 1.5 points
elif depth == 2: 3.0 points
else: 4.0 + min(2, depth - 2)
```

**CTE Score**: `min(2.0, cte_count * 0.8)`

**Set Operators Score**: `min(2.0, set_operators_count * 0.8)`

**Full Scan Penalty**:
```
if no_where_clause or likely_fullscan: 1.0 points
else: 0 points
```

### 2. Oracle-Specific Features (Max 3.0 points)

```
oracle_specific = connect_by_score + analytic_functions_score + pivot_score + model_score
```

- **CONNECT BY**: 2 points
- **Analytic Functions**: `min(3, analytic_functions_count)`
  - ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, FIRST_VALUE, LAST_VALUE
  - NTILE, CUME_DIST, PERCENT_RANK, RATIO_TO_REPORT
- **PIVOT/UNPIVOT**: 2 points
- **MODEL clause**: 3 points

### 3. Functions and Expressions (Max 2.5 points)

```
functions = agg_functions_score + udf_score + case_score + regexp_score + count_penalty + special_agg_penalty
```

- **Aggregate Functions**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **User-Defined Functions**: `min(2, potential_udf * 0.5)`
- **CASE Expressions**: `min(2, case_count * 0.5)`
- **Regular Expressions**: 1 point (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)
- **COUNT(*) Penalty**: 0.5 points (when no WHERE clause or large result expected)
- **Special Aggregate Function Penalty**: 
  ```
  if has_median or has_percentile: +0.5 points
  if has_listagg: +0.3 points
  if has_xmlagg: +0.5 points
  if has_keep_clause: +0.5 points
  ```

### 4. Data Processing Volume (Max 2.5 points)

```
if length < 200: 0.5 points
elif length < 500: 1.2 points
elif length < 1000: 2.0 points
else: 2.5 points
```

### 5. Execution Plan Complexity (Max 2.5 points)

```
execution = join_depth_score + order_by_score + group_by_score + having_score + derived_table_score + performance_penalty
```

**Join Depth**:
```
if join_count > 3 or subquery_depth > 1: 1.5 points
elif join_count > 2 or subquery_depth > 0: 0.8 points
else: 0 points
```

- **ORDER BY**: 0.5 points
- **GROUP BY**: 0.5 points
- **HAVING**: 0.5 points
- **Derived Tables**: `min(1.0, derived_table_count * 0.5)`
- **Performance Penalty**:
  ```
  if has_distinct: +0.3 points
  if has_multiple_or_conditions: +0.3 points (3+ OR conditions)
  if has_like_wildcard_both: +0.3 points (LIKE '%string%')
  if has_function_in_where: +0.5 points (functions in WHERE clause)
  ```

### 6. MySQL Conversion Difficulty (Max 3.0 points)

```
conversion = oracle_syntax_score + oracle_functions_score + hints_score
```

#### Oracle-Specific Syntax

- **CONNECT BY**: 1 point
- **START WITH**: 1 point
- **PRIOR**: 1 point
- **MODEL**: 1 point
- **PIVOT/UNPIVOT**: 1 point
- **FLASHBACK**: 1 point
- **SYS_CONNECT_BY_PATH**: 1 point
- **ROWID**: 1 point
- **ROWNUM**: 1 point
- **LEVEL**: 1 point
- **MERGE statement**: 1.5 points
- **OUTER JOIN (+)**: 1.0 point
- **SEQUENCE.NEXTVAL/CURRVAL**: 0.8 points
- **RETURNING clause**: 0.8 points
- **DUAL table**: 0.3 points

#### Oracle-Specific Functions (0.5 points each)

- DECODE
- NVL, NVL2
- LISTAGG
- REGEXP_*
- SYS_CONTEXT
- EXTRACT
- TO_CHAR, TO_DATE, TO_NUMBER
- TRUNC
- ADD_MONTHS, MONTHS_BETWEEN, NEXT_DAY, LAST_DAY
- SYSDATE, SYSTIMESTAMP, CURRENT_DATE
- SUBSTR, INSTR, CHR, TRANSLATE

#### Hints Score

```
if hint_count == 0: 0 points
elif hint_count <= 2: 0.5 points
elif hint_count <= 5: 1.0 points
else: 1.5 points
```

### Final SQL Complexity Score

```python
total_score = structural + oracle_specific + functions + data_volume + execution + conversion
max_possible_score = 4.5 + 3.0 + 2.5 + 2.5 + 2.5 + 3.0 = 18.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## PL/SQL Object Complexity Calculation

**Important**: When migrating to MySQL, all PL/SQL objects must be migrated to the application level.

### Base Scores (Application Migration Difficulty)

| Object Type | Base Score | Application Migration Difficulty |
|------------|----------|----------------------|
| Package | 8.0 | Very High (need to separate multiple functions/procedures) |
| Procedure | 6.0 | High (business logic reimplementation) |
| Function | 5.0 | High (return logic reimplementation) |
| Trigger | 7.0 | Very High (event handling redesign) |
| View | 2.0 | Low (only SQL query conversion) |
| Materialized View | 5.0 | High (manual refresh logic implementation) |

**Note**: Base scores are 1.0~2.0 points higher than Stored Procedure conversion (reflecting application reimplementation difficulty)

### Complexity Calculation Formula

```
plsql_complexity = base_score + code_complexity + oracle_features + business_logic + ai_difficulty
```

### 1. Code Complexity (Max 3.0 points)

- **Lines of Code**:
  ```
  if lines < 100: 0.5 points
  elif lines < 300: 1.0 points
  elif lines < 500: 1.5 points
  elif lines < 1000: 2.0 points
  else: 2.5 points
  ```
- **Cursor Usage**: `min(1.0, cursor_count * 0.3)`
- **Exception Handling**: `min(0.5, exception_blocks * 0.2)`
- **Nesting Depth**:
  ```
  if nesting_depth <= 2: 0 points
  elif nesting_depth <= 4: 0.5 points
  elif nesting_depth <= 6: 1.0 points
  else: 1.5 points
  ```

### 2. Oracle-Specific Features (Max 3.0 points)

- **Package Dependencies**: `min(2.0, package_calls * 0.5)`
- **DB Link**: `min(1.5, dblink_count * 1.0)`
- **Dynamic SQL**: `min(1.0, dynamic_sql_count * 0.5)`
- **BULK Operations**: `min(0.8, bulk_operations_count * 0.3)` (MySQL not supported, convert to loops)
- **Advanced Features**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED functions (MySQL not supported)
  - REF CURSOR (MySQL not supported)
  - AUTONOMOUS TRANSACTION (MySQL limited)
  - PRAGMA
  - OBJECT TYPE (MySQL not supported)

### 3. Business Logic Complexity (Max 2.0 points)

- **Transaction Processing**: 0.5~0.8 points
  - SAVEPOINT: supported
  - ROLLBACK TO SAVEPOINT: supported
  - Nested transactions: limited
- **Complex Calculations**: `min(1.0, complex_calculations * 0.3)`
- **Data Validation**: `min(0.5, validation_checks * 0.2)`

### 4. AI Conversion Impossibility Difficulty (Max 2.0 points)

- **Context Dependencies**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT (MySQL not supported, replace with session variables)
  - Session variable dependencies
  - Global temporary tables (MySQL uses TEMPORARY TABLE)
- **State Management**: 0.8 points (when using package variables, MySQL uses session variables)
- **External Dependencies**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE (MySQL not supported)
  - UTL_HTTP (MySQL not supported)
  - UTL_MAIL (MySQL not supported)
  - DBMS_SCHEDULER (replace with MySQL EVENT)
- **Custom Logic**: 0.5~1.0 points

### 5. MySQL-Specific Constraints (Max 1.5 points)

```
mysql_constraints = datatype_conversion + trigger_constraints + view_constraints
```

- **Data Type Conversion**: 
  ```
  if has_number_precision_issue: +0.5 points
  if has_clob_blob: +0.3 points
  if has_varchar2_empty_string: +0.3 points
  ```
- **Trigger Constraints**:
  ```
  if has_instead_of_trigger: +0.5 points
  if has_compound_trigger: +0.5 points
  ```
- **View Constraints**:
  ```
  if has_materialized_view: +0.5 points
  if has_complex_updatable_view: +0.3 points
  ```

### Final PL/SQL Complexity Score

```python
total_score = base + code + oracle + business + ai_difficulty + mysql_constraints + app_migration_penalty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 + 1.5 + 2.0 = 23.5
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

**Application Migration Penalty** (app_migration_penalty):
```
if object_type in ['PACKAGE', 'PROCEDURE', 'FUNCTION']:
    app_migration_penalty = 2.0  # Application reimplementation required
elif object_type == 'TRIGGER':
    app_migration_penalty = 1.5  # Event handling redesign
else:
    app_migration_penalty = 0
```

## Complexity Level Classification

### SQL Queries

| Score | Level | MySQL Conversion |
|------|------|-----------|
| 0-1 | Very Simple | Automatic conversion |
| 1-3 | Simple | Function replacement |
| 3-5 | Medium | Partial rewrite + performance tuning |
| 5-7 | Complex | Significant rewrite + query optimization |
| 7-9 | Very Complex | Mostly rewrite + architecture change |
| 9-10 | Extremely Complex | Complete redesign |

### PL/SQL Objects

| Score | Level | MySQL Conversion |
|------|------|-----------|
| 0-3 | Simple | **Application-level migration (simple logic)** |
| 3-5 | Medium | **Application-level migration (medium logic)** |
| 5-7 | Complex | **Application-level migration (complex logic)** |
| 7-9 | Very Complex | **Application-level redesign required** |
| 9-10 | Extremely Complex | **Application-level complete reimplementation required** |

**Important**: MySQL Stored Procedures have the following issues for business logic processing:
- Compilation overhead every time
- Memory leak possibility
- Difficult debugging and maintenance
- Difficult version control

Therefore, **all PL/SQL objects should be migrated to the application level**.

## MySQL Conversion Guide

### Oracle → MySQL Major Conversions

| Oracle | MySQL | Difficulty | Notes |
|--------|-------|-------|---------|
| ROWNUM | LIMIT | Low | Performance caution with OFFSET |
| CONNECT BY | Recursive query or application | High | MySQL 8.0+ CTE available but performance limited |
| DECODE | CASE | Low | - |
| NVL | IFNULL | Low | - |
| SYSDATE | NOW() | Low | - |
| MERGE | INSERT ON DUPLICATE KEY | Medium | Syntax difference large |
| PIVOT | GROUP BY + CASE | Medium | Manual conversion required |
| (+) JOIN | LEFT/RIGHT JOIN | Low | - |
| SEQUENCE.NEXTVAL | AUTO_INCREMENT | Medium | Table structure change required |
| Package | Application level | High | **Stored Procedure not usable, must migrate to application** |
| Procedure | Application level | High | **Stored Procedure not usable, must migrate to application** |
| Function | Application level | High | **Stored Function not usable, must migrate to application** |
| Trigger | Minimize or application | High | Use trigger only for simple logic, complex logic to application |
| RETURNING | Separate SELECT | High | MySQL not supported |
| BULK COLLECT | Loop processing | High | MySQL not supported, performance degradation possible |
| REF CURSOR | Temporary table | High | MySQL not supported |
| LISTAGG | GROUP_CONCAT | Medium | Length limit (default 1024 chars) |
| MEDIAN | Complex subquery | High | MySQL not supported |
| Materialized View | Manual implementation | High | MySQL not supported, implement with trigger |
| Empty string NULL | Explicit handling | Low | Oracle treats as NULL, MySQL distinguishes |
| String concatenation (||) | CONCAT() | Low | Function conversion |
| Date arithmetic (+/-) | DATE_ADD/DATE_SUB | Low | Function conversion |

## MySQL Special Considerations

### 1. Avoid Complex JOINs

- Performance degradation possible with 3+ JOINs
- Consider reducing JOINs or denormalization
- Index optimization essential

### 2. Subquery Optimization

- IN clause subqueries recommended to convert to JOIN
- Correlated subqueries can have performance issues
- Consider using EXISTS

### 3. COUNT(*) Optimization

- COUNT(*) without WHERE clause is very slow
- Use approximate values or caching if possible
- Index utilization essential

### 4. Avoid Full Scans

- WHERE clause required
- Create appropriate indexes
- Limit results with LIMIT

### 5. CTE Usage Limitations

- Supported from MySQL 8.0 but optimization limited
- Consider temporary tables instead of complex CTEs
- Performance testing essential

### 6. Analytic Function Limitations

- Window functions supported from MySQL 8.0
- Some Oracle analytic functions not supported
- Alternative methods needed (MEDIAN, PERCENTILE, etc.)

### 7. Data Type Conversion Issues

- **NUMBER → DECIMAL/INT**: Precision difference caution
- **VARCHAR2 → VARCHAR**: Empty string handling difference (Oracle treats as NULL, MySQL distinguishes)
- **DATE → DATETIME**: Time information inclusion
- **CLOB/BLOB → TEXT/LONGTEXT**: Check size limits
- **RAW → VARBINARY**: Binary data conversion

### 8. Aggregate Function Constraints

- **LISTAGG → GROUP_CONCAT**: Length limit (default 1024 chars)
- **MEDIAN**: MySQL not supported (complex subquery needed)
- **PERCENTILE_CONT/DISC**: MySQL not supported
- **XMLAGG**: MySQL not supported
- **KEEP clause**: MySQL not supported
- **WITHIN GROUP**: MySQL not supported

### 9. String and Date Processing Differences

- **String concatenation**: Oracle `||` → MySQL `CONCAT()`
- **Date arithmetic**: Oracle `DATE + 1` → MySQL `DATE_ADD(DATE, INTERVAL 1 DAY)`
- **NULL handling**: Oracle treats empty string ('') as NULL, MySQL distinguishes
- **Case sensitivity**: Table names OS-dependent (Linux distinguishes, Windows doesn't)

### 10. Index Constraints

- **Function-based indexes**: Supported from MySQL 8.0.13 but limited
- **Bitmap indexes**: MySQL not supported
- **Reverse indexes**: MySQL not supported
- **Index column composition**: Maximum 16 columns limit

### 11. Trigger Constraints

- **INSTEAD OF triggers**: MySQL not supported (triggers on views)
- **Compound triggers**: MySQL not supported
- **Transaction control in triggers**: Limited
- **:NEW/:OLD**: MySQL uses NEW/OLD (no colon)

### 12. Stored Procedure Constraints

**Important**: MySQL Stored Procedures are unsuitable for business logic processing.

**Issues**:
- **Compilation overhead**: Compilation required every execution
- **Memory leaks**: Memory leak possibility with long-running
- **Performance degradation**: Performance issues with complex logic
- **Difficult debugging**: Limited debugging tools
- **Difficult version control**: Complex source code management
- **Deployment complexity**: Separate deployment from application

**Constraints**:
- **OUT/IN OUT parameters**: Limited support
- **Cursor variables (REF CURSOR)**: MySQL not supported
- **BULK COLLECT**: MySQL not supported
- **FORALL**: MySQL not supported
- **Exception handling**: MySQL uses HANDLER (different syntax)
- **Package variables**: MySQL not supported (replace with session variables)
- **RETURN statement (Function)**: Syntax difference

**Recommendations**:
- **Migrate all business logic to application level**
- Use triggers only for minimal data integrity validation
- Handle complex logic in application

### 13. View Constraints

- **Complex views**: Often not updatable
- **Materialized View**: MySQL not supported (manual implementation needed)
- **ORDER BY in views**: Limited

### 14. Partitioning Constraints

- **Range partitioning**: Supported but with constraints
- **List partitioning**: Supported
- **Hash partitioning**: Supported
- **Composite partitioning**: Limited
- **Partition pruning**: Optimization limited

### 15. Transactions and Locks

- **FOR UPDATE NOWAIT**: Supported from MySQL 8.0
- **FOR UPDATE SKIP LOCKED**: Supported from MySQL 8.0
- **SAVEPOINT**: Supported
- **Transaction isolation level**: Default difference (Oracle: READ COMMITTED, MySQL: REPEATABLE READ)

## Performance Optimization Checklist

- [ ] Limit JOINs to 3 or fewer
- [ ] Include WHERE clause mandatory
- [ ] Create appropriate indexes
- [ ] Convert subqueries to JOINs
- [ ] Minimize COUNT(*) usage
- [ ] Limit results with LIMIT
- [ ] Avoid full scans
- [ ] Minimize derived tables
- [ ] Consider temporary tables instead of CTEs
- [ ] Check query execution plan (EXPLAIN)
- [ ] Minimize DISTINCT usage
- [ ] Minimize OR conditions (convert to UNION if possible)
- [ ] Avoid LIKE '%string%'
- [ ] Avoid functions in WHERE clause
- [ ] Check GROUP_CONCAT length limit
- [ ] Check transaction isolation level
- [ ] Consider using index hints
- [ ] Establish partitioning strategy

## MySQL 8.0.42 New Features Utilization

- **Window functions**: Utilize ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, etc.
- **CTE (WITH clause)**: Simplify complex queries (but performance testing essential)
- **Recursive CTE**: Replace CONNECT BY (performance caution)
- **JSON functions**: JSON data processing
- **Function-based indexes**: Supported from 8.0.13
- **Descending indexes**: Supported from 8.0
- **NOWAIT/SKIP LOCKED**: Supported from 8.0

## Notes

- MySQL is weak at complex query processing, so structural complexity weight is high.
- **All PL/SQL objects must be migrated to application level** (Stored Procedure not usable).
- MySQL Stored Procedures are unsuitable for business logic processing due to compilation overhead and memory leak issues.
- MySQL does not support some Oracle analytic functions.
- CONNECT BY is very difficult to implement in MySQL, so application-level processing is recommended.
- Performance optimization is more important than PostgreSQL.
- Use triggers only for minimal data integrity validation, and handle complex logic in application.
