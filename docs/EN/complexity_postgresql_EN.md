# Oracle to PostgreSQL Migration Complexity Calculation Formula

> [한국어](../complexity_postgresql.md)

This document describes the formula for calculating the complexity of SQL queries and PL/SQL objects when migrating from Oracle to PostgreSQL.

## PostgreSQL Characteristics

- **Based on PostgreSQL 16 or higher**
- **Multi-process architecture**: Each connection is an independent process
- **Strong for complex queries**: Excellent optimization for complex JOINs, subqueries, CTEs
- **Excellent full scan performance**: Efficient large table scanning
- **Advanced feature support**: Window functions, recursive CTEs, LATERAL JOIN, etc.
- **Analytical query optimization**: Suitable for OLAP workloads
- **PostgreSQL 16 new features**: Logical replication improvements, parallel query improvements (FULL/RIGHT JOIN), incremental sort improvements

## PL/pgSQL vs Oracle PL/SQL Performance Comparison

### Context Switch Difference

**Oracle PL/SQL**:
- Context switch occurs between PL/SQL engine and SQL engine
- Minimize context switches with BULK COLLECT/FORALL
- Example: 100,000 row INSERT - row-by-row 4.94s vs FORALL 0.12s (about 40x difference)

**PostgreSQL PL/pgSQL**:
- BULK COLLECT/FORALL not supported
- Performance optimization possible with alternative methods

### Performance Benchmark (AWS DMA, 10 million records)

| Method | Relative Performance |
|------|----------|
| LOOP (row-by-row) | 3.24X (slowest) |
| ARRAY_AGG + UNNEST | 1.4X |
| Pure SQL | 1.12X |
| SQL + Chunked Batch | 1X (fastest) |

### Oracle vs PostgreSQL Performance Difference Summary

| Area | Performance Difference | Notes |
|------|----------|------|
| Simple procedures | 0-10% | Almost identical |
| Cursor processing | 0-20% | Almost identical |
| BULK INSERT (optimized) | 20-50% slower | When using Chunked SQL |
| BULK INSERT (non-optimized) | 200-400% slower | When using row-by-row LOOP |
| Large data processing | 30-50% slower | When using ARRAY_AGG/UNNEST |
| Complex business logic | 10-30% | Similar |

### PostgreSQL 16 Performance Optimization Recommendations

1. **BULK operation replacement**: Use pure SQL or Chunked Batch method
2. **Avoid row-by-row LOOP**: Convert to set-based SQL
3. **Utilize PostgreSQL 16 parallel queries**: FULL/RIGHT JOIN parallel processing
4. **Utilize incremental sort**: Improved large data sorting performance

## SQL Query Complexity Calculation

### 1. Structural Complexity (Max 2.5 points)

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score
```

**JOIN Score**:
```
if join_count == 0: 0 points
elif join_count <= 3: 0.5 points
elif join_count <= 5: 1.0 points
else: 1.5 points
```

**Subquery Score**:
```
if depth == 0: 0 points
elif depth == 1: 0.5 points
elif depth == 2: 1.0 points
else: 1.5 + min(1, (depth - 2) * 0.5)
```

**CTE Score**: `min(1.0, cte_count * 0.5)`

**Set Operators Score**: `min(1.5, set_operators_count * 0.5)`

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

### 3. Functions and Expressions (Max 2.0 points)

```
functions = agg_functions_score + udf_score + case_score + regexp_score
```

- **Aggregate Functions**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **User-Defined Functions**: `min(2, potential_udf * 0.5)`
- **CASE Expressions**: `min(2, case_count * 0.5)`
- **Regular Expressions**: 1 point (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)

### 4. Data Processing Volume (Max 2.0 points)

```
if length < 200: 0.5 points
elif length < 500: 1.0 points
elif length < 1000: 1.5 points
else: 2.0 points
```

### 5. Execution Plan Complexity (Max 1.0 point)

```
execution = join_depth_score + order_by_score + group_by_score + having_score
```

- **Join Depth**: 0.5 points (join_count > 5 or subquery_depth > 2)
- **ORDER BY**: 0.2 points
- **GROUP BY**: 0.2 points
- **HAVING**: 0.2 points

### 6. PostgreSQL Conversion Difficulty (Max 3.0 points)

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
max_possible_score = 2.5 + 3.0 + 2.0 + 2.0 + 1.0 + 3.0 = 13.5
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## PL/SQL Object Complexity Calculation

**Important**: PostgreSQL can cover about 70-75% of Oracle PL/SQL through PL/pgSQL.

### PL/pgSQL Coverage

#### ✅ High Compatibility (90%+ coverage)
- Basic programming structures (variables, IF, LOOP, CASE, etc.)
- Cursors (explicit cursors, REF CURSOR fully supported)
- Functions/procedures (IN/OUT/INOUT parameters, overloading)
- Triggers (BEFORE/AFTER, including INSTEAD OF)
- Dynamic SQL (EXECUTE)
- Exception handling (EXCEPTION)

#### ⚠️ Medium Compatibility (50-80% coverage)
- **Packages**: No concept → Group with schema + individual functions/procedures
- **Package variables**: Replace with session variables (current_setting/set_config) or temporary tables
- **Collections**: ARRAY type support (similar to VARRAY), Nested Table limited
- **BULK operations**: BULK COLLECT/FORALL not supported → Replace with regular loops
- **PIPELINED functions**: Similar implementation with RETURN NEXT/RETURN QUERY

#### ❌ Low Compatibility (30% or less)
- PRAGMA (AUTONOMOUS_TRANSACTION limited, others not supported)
- Object types (Object Type) - Limited implementation with Composite Type
- External procedures (UTL_FILE, UTL_HTTP, UTL_MAIL not supported)

### Base Scores

| Object Type | Base Score | PL/pgSQL Conversion Possibility |
|------------|----------|-------------------|
| Package | 7.0 | Medium (reorganize with schema) |
| Procedure | 5.0 | High (almost direct conversion) |
| Function | 4.0 | High (almost direct conversion) |
| Trigger | 6.0 | High (only syntax differences) |
| View | 2.0 | High (only SQL conversion) |
| Materialized View | 4.0 | High (PostgreSQL supported) |

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
  - PostgreSQL has no package concept, need to reorganize with schema
- **DB Link**: `min(1.5, dblink_count * 1.0)`
  - PostgreSQL supports with dblink extension
- **Dynamic SQL**: `min(1.0, dynamic_sql_count * 0.5)`
  - EXECUTE IMMEDIATE → Direct conversion to EXECUTE
- **BULK Operations**: `min(1.0, bulk_operations_count * 0.4)` (reflecting performance penalty)
  - BULK COLLECT/FORALL not supported
  - Alternatives: Pure SQL, Chunked Batch, ARRAY_AGG/UNNEST
  - **Performance difference: 20-50% when optimized, 200-400% when non-optimized**
- **Advanced Features**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED functions: Similar implementation with RETURN NEXT/RETURN QUERY
  - REF CURSOR: Fully supported
  - AUTONOMOUS TRANSACTION: Limited (can implement with dblink)
  - PRAGMA: Mostly not supported
  - OBJECT TYPE: Limited implementation with Composite Type

### 3. Business Logic Complexity (Max 2.0 points)

- **Transaction Processing**: 0.5~0.8 points
- **Complex Calculations**: `min(1.0, complex_calculations * 0.3)`
- **Data Validation**: `min(0.5, validation_checks * 0.2)`

### 4. AI Conversion Impossibility Difficulty (Max 2.0 points)

- **Context Dependencies**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT: PostgreSQL replaces with current_setting/set_config
  - Session variables: Use current_setting/set_config
  - Global temporary tables: Replace with TEMPORARY TABLE
- **State Management**: 0.8 points (when using package variables)
  - Package variables: Replace with session variables or temporary tables
  - Cross-session state sharing is limited
- **External Dependencies**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE: PostgreSQL extension or application-level processing
  - UTL_HTTP: http extension available
  - UTL_MAIL: Application-level processing
  - DBMS_SCHEDULER: Replace with pg_cron extension
- **Custom Logic**: 0.5~1.0 points

### Final PL/SQL Complexity Score

```python
total_score = base + code + oracle + business + ai_difficulty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 = 20.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## Complexity Level Classification

### SQL Queries

| Score | Level | PostgreSQL Conversion |
|------|------|----------------|
| 0-1 | Very Simple | Automatic conversion |
| 1-3 | Simple | Function replacement |
| 3-5 | Medium | Partial rewrite |
| 5-7 | Complex | Significant rewrite |
| 7-9 | Very Complex | Mostly rewrite |
| 9-10 | Extremely Complex | Complete redesign |

### PL/SQL Objects

| Score | Level | PostgreSQL Conversion |
|------|------|----------------|
| 0-3 | Simple | PL/pgSQL automatic conversion |
| 3-5 | Medium | PL/pgSQL + manual adjustment |
| 5-7 | Complex | PL/pgSQL rewrite (package reorganization) |
| 7-9 | Very Complex | PL/pgSQL redesign (BULK, package variable replacement) |
| 9-10 | Extremely Complex | Consider application-level reimplementation |

**Note**: 
- Complexity 5.0 or below: Direct conversion to PL/pgSQL possible
- Complexity 5.0-7.0: Package reorganization, BULK operation replacement needed
- Complexity 7.0 or above: Redesign needed when using package variables, PRAGMA, etc.

## PostgreSQL Conversion Guide

### Oracle → PostgreSQL Major Conversions

| Oracle | PostgreSQL | Difficulty |
|--------|-----------|-------|
| ROWNUM | LIMIT/OFFSET | Low |
| CONNECT BY | WITH RECURSIVE | Medium |
| DECODE | CASE | Low |
| NVL | COALESCE | Low |
| SYSDATE | CURRENT_TIMESTAMP | Low |
| MERGE | INSERT ON CONFLICT | Medium |
| PIVOT | crosstab or CASE | Medium |
| (+) JOIN | LEFT/RIGHT JOIN | Low |
| SEQUENCE.NEXTVAL | nextval('seq') | Low |
| Package | Schema + Functions | High |
| BULK COLLECT | Pure SQL/Chunked Batch | Medium | **Avoid row-by-row LOOP** (200-400% slower) |
| FORALL | Pure SQL/Chunked Batch | Medium | Pure SQL recommended (20-50% slower) |
| PIPELINED | RETURN NEXT/QUERY | Medium |
| Package variables | Session variables/temporary tables | High |
| UTL_FILE | Extension or application | High |
| UTL_HTTP | http extension | Medium |
| DBMS_SCHEDULER | pg_cron extension | Medium |
| SYS_CONTEXT | current_setting/set_config | Low |
| PRAGMA | Limited or not supported | High |
| Object Type | Composite Type | Medium |
| LISTAGG | STRING_AGG | Low |
| MEDIAN | PERCENTILE_CONT(0.5) | Low |
| XMLAGG | XMLAGG | Low |
| WM_CONCAT | STRING_AGG | Low |
| DBMS_CRYPTO | Application encryption | High |

### Data Type Conversion

| Oracle | PostgreSQL | Notes |
|--------|-----------|---------|
| NUMBER | NUMERIC/INTEGER | Precision check needed |
| NUMBER(p,s) | NUMERIC(p,s) | Direct mapping |
| VARCHAR2 | VARCHAR | Empty string handling identical |
| DATE | TIMESTAMP | Oracle DATE includes time |
| CLOB | TEXT | No size limit |
| BLOB | BYTEA | Binary data |
| RAW | BYTEA | Binary data |
| LONG | TEXT | Legacy type |

### PostgreSQL Extension Utilization

| Extension | Purpose | Oracle Replacement |
|------|------|------------|
| pg_cron | Scheduler | DBMS_SCHEDULER |
| dblink | Remote DB connection | DB Link |
| http | HTTP calls | UTL_HTTP |
| tablefunc | crosstab | PIVOT |
| pg_trgm | Similar string search | - |
| pgcrypto | Encryption | DBMS_CRYPTO (partial) |

## Application-Level Migration Guide

### ❌ Must Migrate to Application Level

| Feature | Reason | Application Alternative |
|------|------|-----------------|
| **UTL_FILE** | PostgreSQL not supported, security issues | File I/O service |
| **UTL_MAIL/UTL_SMTP** | PostgreSQL not supported | Email service (JavaMail, SendGrid) |
| **External API calls** | Unsuitable for DB processing | REST Client, HTTP service |
| **Complex business logic** | Difficult maintenance, testing | Service layer |
| **Cross-session state sharing** | PostgreSQL limited | Redis, application cache |
| **Large batch processing (BULK)** | Large performance difference (200-400%) | Spring Batch, batch framework |
| **Complex transaction management** | AUTONOMOUS_TRANSACTION limited | Transaction management service |
| **Encryption/decryption** | DBMS_CRYPTO not supported | Encryption library (Jasypt, Bouncy Castle) |
| **DBMS_JOB (complex cases)** | pg_cron limited | Quartz, Spring Scheduler |

### ⚠️ Recommended: Migrate to Application Level

| Feature | Reason | PL/pgSQL Alternative | Application Alternative |
|------|------|--------------|-----------------|
| **Package variables (state management)** | Session variables limited | current_setting | Application cache/session |
| **PRAGMA AUTONOMOUS_TRANSACTION** | dblink complex | dblink | Separate transaction service |
| **Object Type (complex cases)** | Composite Type limited | Composite Type | DTO/Entity |
| **PIPELINED functions (large volume)** | RETURN NEXT performance limited | RETURN NEXT | Streaming service |
| **Dynamic SQL (complex cases)** | Security, maintenance | EXECUTE | Query builder (QueryDSL, JOOQ) |
| **Complex exception handling** | Syntax differences | EXCEPTION | Application exception handling |

### ✅ Can Maintain with PL/pgSQL

| Feature | Conversion Difficulty | Notes |
|------|-----------|------|
| Simple CRUD procedures | Low | Direct conversion |
| Data validation triggers | Low | Only syntax conversion |
| Simple calculation functions | Low | Direct conversion |
| Cursor processing | Low | REF CURSOR included support |
| Dynamic SQL (simple) | Low | EXECUTE supported |
| Exception handling (simple) | Low | EXCEPTION supported |
| Materialized View | Low | PostgreSQL fully supported |
| Sequences | Low | nextval/currval supported |
| Views | Low | Only SQL conversion |

### Migration Decision Criteria

```
Complexity < 5.0  → Maintain PL/pgSQL
Complexity 5.0-7.0 → Feature-based judgment (BULK, package variables → Application)
Complexity > 7.0  → Application-level migration recommended
```

| Judgment Criteria | Maintain PL/pgSQL | Application Migration |
|----------|--------------|-----------------|
| BULK operations | None or small volume | Large volume (10K+ records) |
| Package variables | Not used | State management needed |
| External calls | None | UTL_*, API calls |
| Transactions | Simple | AUTONOMOUS needed |
| Business logic | Simple calculation/validation | Complex business rules |
| Test ease | Simple | Complex (unit testing needed) |

## Notes

- **Based on PostgreSQL 16 or higher**.
- PostgreSQL is strong at complex query processing, so structural complexity weight is low.
- **PL/pgSQL covers about 70-75% of Oracle PL/SQL**, so most business logic can be converted.
- Packages should be reorganized with schema, and package variables should be replaced with session variables or temporary tables.
- **BULK operation performance caution**: 
  - 20-50% slower than Oracle when using pure SQL or Chunked Batch
  - 200-400% slower when using row-by-row LOOP (must avoid)
- PostgreSQL supports most Oracle analytic functions.
- CONNECT BY can be converted to WITH RECURSIVE but may need performance tuning.
- Materialized View is fully supported by PostgreSQL.
- REF CURSOR is fully supported by PostgreSQL.
- **External procedure calls (UTL_*) recommended for application-level processing**.
- **Utilize PostgreSQL 16 new features**: Parallel query improvements, incremental sort, logical replication improvements
- **Complexity 7.0 or above should actively consider application-level migration**.
