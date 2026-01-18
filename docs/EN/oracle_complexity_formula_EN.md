# Oracle Migration Complexity and Strategy Guide

This document is a comprehensive guide for calculating Oracle database migration complexity, assessing difficulty levels, and selecting strategies.

> [한국어](../oracle_complexity_formula.md)

## Table of Contents

1. [Complexity Score Overview](#complexity-score-overview)
2. [Target Database Characteristics Comparison](#target-database-characteristics-comparison)
3. [SQL Query Complexity Calculation](#sql-query-complexity-calculation)
4. [PL/SQL Object Complexity Calculation](#plsql-object-complexity-calculation)
5. [Complexity Level Classification](#complexity-level-classification)
6. [PL/SQL Migration Difficulty Assessment](#plsql-migration-difficulty-assessment)
7. [Replatform vs Refactor Strategy Selection](#replatform-vs-refactor-strategy-selection)
8. [Decision-Making Guide](#decision-making-guide)

## Complexity Score Overview

Complexity scores are expressed on a 0-10 scale, indicating the difficulty of conversion from Oracle to the target database.

**Important**: PostgreSQL and MySQL have different architectures and performance characteristics, so the same Oracle query may have different complexity scores depending on the target database.

## Target Database Characteristics Comparison

### PostgreSQL
- Multi-process architecture
- Excellent optimization for complex JOINs, subqueries, and CTEs
- Excellent full scan performance
- Advanced feature support (window functions, recursive CTEs, LATERAL JOIN)

### MySQL
- Multi-threaded architecture
- Strong with simple queries
- Weak full scan performance
- Weak complex JOINs (3 or more)
- COUNT(*) performance issues
- Limited subquery optimization

### Complexity Weight Differences

| Factor | PostgreSQL | MySQL |
|--------|-----------|-------|
| Complex JOINs (3+) | Low | High |
| Nested Subqueries | Low | High |
| Expected Full Scan Queries | Low | High |
| COUNT(*) Aggregation | Low | High |
| CTE Usage | Low | Medium |

## SQL Query Complexity Calculation

SQL query complexity is calculated across 6 categories.

### 1. Structural Complexity

**PostgreSQL**: Max 2.5 points  
**MySQL**: Max 4.5 points

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score + fullscan_penalty(MySQL only)
```

#### JOIN Score

**PostgreSQL**:
```
if join_count == 0: 0 points
elif join_count <= 3: 0.5 points
elif join_count <= 5: 1.0 points
else: 1.5 points
```

**MySQL**:
```
if join_count == 0: 0 points
elif join_count <= 2: 1.0 points
elif join_count <= 4: 2.0 points
elif join_count <= 6: 3.0 points
else: 4.0 points
```

#### Subquery Score

**PostgreSQL**:
```
if depth == 0: 0 points
elif depth == 1: 0.5 points
elif depth == 2: 1.0 points
else: 1.5 + min(1, (depth - 2) * 0.5)
```

**MySQL**:
```
if depth == 0: 0 points
elif depth == 1: 1.5 points
elif depth == 2: 3.0 points
else: 4.0 + min(2, depth - 2)
```

#### CTE Score

**PostgreSQL**: `min(1.0, cte_count * 0.5)`  
**MySQL**: `min(2.0, cte_count * 0.8)`

#### Set Operators Score

**PostgreSQL**: `min(1.5, set_operators_count * 0.5)`  
**MySQL**: `min(2.0, set_operators_count * 0.8)`

#### Full Scan Penalty (MySQL only)

```
if no_where_clause or likely_fullscan: 1.0 points
else: 0 points
```

### 2. Oracle-Specific Features

**Max Score**: 3.0 points (same for PostgreSQL/MySQL)

```
oracle_specific = connect_by_score + analytic_functions_score + pivot_score + model_score
```

- **CONNECT BY**: 2 points
- **Analytic Functions**: `min(3, analytic_functions_count)`
  - ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, FIRST_VALUE, LAST_VALUE
  - NTILE, CUME_DIST, PERCENT_RANK, RATIO_TO_REPORT
- **PIVOT/UNPIVOT**: 2 points
- **MODEL Clause**: 3 points

### 3. Functions & Expressions

**PostgreSQL**: Max 2.0 points  
**MySQL**: Max 2.5 points

```
functions = agg_functions_score + udf_score + case_score + regexp_score + count_penalty(MySQL only)
```

- **Aggregate Functions**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **User-Defined Functions**: `min(2, potential_udf * 0.5)`
- **CASE Expressions**: `min(2, case_count * 0.5)`
- **Regular Expressions**: 1 point (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)
- **COUNT(*) Penalty (MySQL only)**: 0.5 points (when no WHERE clause or large result expected)

### 4. Data Volume

**PostgreSQL**: Max 2.0 points  
**MySQL**: Max 2.5 points

**PostgreSQL**:
```
if length < 200: 0.5 points
elif length < 500: 1.0 points
elif length < 1000: 1.5 points
else: 2.0 points
```

**MySQL**:
```
if length < 200: 0.5 points
elif length < 500: 1.2 points
elif length < 1000: 2.0 points
else: 2.5 points
```

### 5. Execution Complexity

**PostgreSQL**: Max 1.0 points  
**MySQL**: Max 2.5 points

```
execution = join_depth_score + order_by_score + group_by_score + having_score + derived_table_score(MySQL only)
```

**PostgreSQL**:
- **Join Depth**: 0.5 points (join_count > 5 or subquery_depth > 2)
- **ORDER BY**: 0.2 points
- **GROUP BY**: 0.2 points
- **HAVING**: 0.2 points

**MySQL**:
- **Join Depth**: 
  - 1.5 points (join_count > 3 or subquery_depth > 1)
  - 0.8 points (join_count > 2 or subquery_depth > 0)
- **ORDER BY**: 0.5 points
- **GROUP BY**: 0.5 points
- **HAVING**: 0.5 points
- **Derived Tables**: `min(1.0, derived_table_count * 0.5)`

### 6. Conversion Difficulty

**Max Score**: 3.0 points (same for PostgreSQL/MySQL)

```
conversion = oracle_syntax_score + oracle_functions_score + hints_score
```

#### Oracle-Specific Syntax (each score specified)

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
- **MERGE Statement**: 1.5 points
- **OUTER JOIN (+)**: 1.0 points
- **SEQUENCE.NEXTVAL/CURRVAL**: 0.8 points
- **RETURNING Clause**: 0.8 points
- **DUAL Table**: 0.3 points

#### Oracle-Specific Functions (0.5 points each)

- DECODE
- NVL, NVL2
- LISTAGG
- REGEXP_* (regular expression functions)
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

Hint examples: INDEX, FULL, PARALLEL, USE_HASH, USE_NL, APPEND, NO_MERGE

### Final Complexity Score Calculation

**PostgreSQL**:
```python
total_score = structural + oracle_specific + functions + data_volume + execution + conversion
max_possible_score = 2.5 + 3.0 + 2.0 + 2.0 + 1.0 + 3.0 = 13.5
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

**MySQL**:
```python
total_score = structural + oracle_specific + functions + data_volume + execution + conversion
max_possible_score = 4.5 + 3.0 + 2.5 + 2.5 + 2.5 + 3.0 = 18.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## PL/SQL Object Complexity Calculation

PL/SQL objects are much more complex than simple SQL, and cannot be migrated with DB only.

### Base Complexity by Object Type

| Object Type | Base Score | Description |
|------------|-----------|-------------|
| Package | 7.0 | Contains multiple procedures/functions, state management |
| Procedure | 5.0 | Business logic, transaction processing |
| Function | 4.0 | Logic with return value |
| Trigger | 6.0 | Event-based logic |
| View | 2.0 | Complex query encapsulation |
| Materialized View | 4.0 | Performance optimization, refresh logic |

### PL/SQL Complexity Calculation Formula

```
plsql_complexity = base_score + code_complexity + oracle_features + business_logic + ai_difficulty
```

### 1. Base Score

2.0~7.0 points depending on object type

### 2. Code Complexity (Max 3.0 points)

```
code_complexity = lines_score + cursor_score + exception_score + nested_score
```

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

### 3. Oracle-Specific Features (Max 3.0 points)

```
oracle_features = package_dependency + dblink_score + dynamic_sql + bulk_operations + advanced_features
```

- **Package Dependencies**: `min(2.0, package_calls * 0.5)`
- **DB Link**: `min(1.5, dblink_count * 1.0)`
- **Dynamic SQL**: `min(1.0, dynamic_sql_count * 0.5)`
- **BULK Operations**: `min(0.8, bulk_operations_count * 0.3)`
- **Advanced Features**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED, REF CURSOR, AUTONOMOUS TRANSACTION, PRAGMA, OBJECT TYPE

### 4. Business Logic Complexity (Max 2.0 points)

```
business_logic = transaction_score + calculation_score + validation_score
```

- **Transaction Processing**:
  ```
  if has_savepoint or has_rollback: 0.8 points
  elif has_commit: 0.5 points
  else: 0 points
  ```

- **Complex Calculations**: `min(1.0, complex_calculations * 0.3)`
- **Data Validation**: `min(0.5, validation_checks * 0.2)`

### 5. AI Conversion Impossibility Difficulty (Max 2.0 points)

```
ai_difficulty = context_dependency + state_management + external_dependency + custom_logic
```

- **Context Dependency**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT, session variables, global temporary tables
- **State Management**: 0.8 points (when using package variables)
- **External Dependencies**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE, UTL_HTTP, UTL_MAIL, DBMS_SCHEDULER
- **Custom Logic**:
  ```
  if highly_custom: 1.0 points
  elif moderately_custom: 0.5 points
  else: 0 points
  ```

### Final PL/SQL Complexity Calculation

```python
total_score = base + code + oracle + business + ai_difficulty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 = 20.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## Complexity Level Classification

### SQL Query Complexity Levels

| Score | Level | Description | Conversion Approach |
|-------|-------|-------------|-------------------|
| 0-1 | Very Simple | Standard SQL only | Automatic conversion tools |
| 1-3 | Simple | Basic Oracle functions | Function replacement |
| 3-5 | Medium | Some Oracle-specific features | Partial rewrite |
| 5-7 | Complex | Multiple Oracle-specific features | Significant rewrite |
| 7-9 | Very Complex | Complex Oracle feature combinations | Most rewrite |
| 9-10 | Extremely Complex | Advanced Oracle features | Complete redesign |

### PL/SQL Object Complexity Levels

| Score | Level | Convertibility | Recommended Approach |
|-------|-------|---------------|---------------------|
| 0-3 | Simple | AI auto-conversion possible | AWS SCT + review |
| 3-5 | Medium | AI-assisted + manual fixes | AI conversion then manual adjustment |
| 5-7 | Complex | Mostly manual conversion | Expert rewrite |
| 7-9 | Very Complex | Completely manual conversion | Architecture redesign consideration |
| 9-10 | Extremely Complex | Not convertible | Application-level reimplementation |

## Migration Decision-Making Guide

| Average Complexity | PL/SQL Object Count | Recommended Approach | Expected Difficulty |
|-------------------|-------------------|---------------------|-------------------|
| < 3.0 | < 10 | DB Migration | Low |
| 3.0-5.0 | 10-50 | DB Migration + Partial Rewrite | Medium |
| 5.0-7.0 | 50-100 | DB Migration + Significant Rewrite | High |
| 7.0-9.0 | 100-200 | Hybrid (DB + App Level) | Very High |
| > 9.0 | > 200 | Application-Level Reimplementation | Extremely High |

---

## PL/SQL Migration Difficulty Assessment

### Overview

PL/SQL lines of code is a key metric for determining migration difficulty and duration. Assess project scale by evaluating lines of code along with complexity scores.

### Criteria by Difficulty Level

#### Low: ~20,000 lines

**Characteristics:**
- 1-2 people can understand entire codebase
- Relatively simple business logic
- Limited external system integration

**Expected Duration:** 3-6 months

**Team Composition:**
- DBA: 1
- Developer: 1-2
- QA: 1 (part-time possible)

**Recommended Approach:**
- Single team execution possible
- Sequential migration
- Full code review and refactoring possible

---

#### Medium: 20,000~50,000 lines

**Characteristics:**
- Small team (2-4 people) needed
- Medium complexity business logic
- System composed of multiple modules

**Expected Duration:** 6-12 months

**Team Composition:**
- DBA: 1-2
- Developer: 2-3
- QA: 1-2
- Project Manager: 1 (part-time possible)

**Recommended Approach:**
- Parallel work by module
- Phased testing and validation
- Code review process essential

---

#### High: 50,000~100,000 lines

**Characteristics:**
- Medium team (4-8 people) needed
- Complex business logic and dependencies
- Multiple external system integrations

**Expected Duration:** 12-18 months

**Team Composition:**
- DBA: 2-3
- Developer: 4-6
- QA: 2-3
- Architect: 1
- Project Manager: 1

**Recommended Approach:**
- Phased migration strategy essential
- Set module priorities
- Consider hybrid operation period
- Automation tools essential

---

#### Very High: 100,000+ lines

**Characteristics:**
- Large team and professional consulting needed
- Very complex enterprise system
- Extensive external system integration
- Mission-critical system

**Expected Duration:** 18+ months

**Team Composition:**
- DBA: 3-5
- Developer: 8-12
- QA: 3-5
- Architect: 2-3
- Project Manager: 1-2
- External Consultants: As needed

**Recommended Approach:**
- Manage as enterprise-wide project
- Establish phased release plan
- Long-term hybrid operation strategy
- Leverage professional consulting and AWS support
- Essential automation and tool investment

---

### Additional Considerations

In addition to lines of code, the following factors should be evaluated together to adjust difficulty:

#### 1. Number of External System Integrations

- **Low (0-3)**: Maintain difficulty
- **Medium (4-10)**: Difficulty +1 level
- **High (11+)**: Difficulty +2 levels

**Impact:**
- Compatibility verification needed per integration system
- Increased interface change and test complexity
- Coordination needed for simultaneous migration

#### 2. Batch Job Complexity

- **Simple Batch (<10)**: Maintain difficulty
- **Medium Batch (10-30)**: Difficulty +0.5 level
- **Complex Batch (30+)**: Difficulty +1 level

**Impact:**
- Batch scheduling redesign
- Large data processing logic optimization
- Failure recovery mechanism reimplementation

#### 3. Data Volume

- **Small (<1TB)**: Maintain difficulty
- **Medium (1-10TB)**: Difficulty +0.5 level
- **Large (10TB+)**: Difficulty +1 level

**Impact:**
- Increased data migration time
- Downtime minimization strategy needed
- Increased incremental migration and validation complexity

#### 4. Real-time Processing Requirements

- **Batch-centric**: Maintain difficulty
- **Near Real-time (seconds)**: Difficulty +0.5 level
- **Real-time (milliseconds)**: Difficulty +1 level

**Impact:**
- Performance optimization essential
- Zero-downtime migration strategy needed
- Extensive performance testing needed

#### 5. Business Criticality

- **General System**: Maintain difficulty
- **Important System**: Difficulty +0.5 level
- **Mission Critical**: Difficulty +1 level

**Impact:**
- Thorough testing and validation needed
- Rollback plan and emergency response system essential
- Phased transition and enhanced monitoring

---

### Difficulty Adjustment Examples

#### Example 1: Base Medium Difficulty System

- **PL/SQL Code**: 30,000 lines → Medium
- **External Integration**: 5 → +1 level
- **Batch Jobs**: 15 → +0.5 level
- **Data Volume**: 3TB → +0.5 level
- **Real-time Processing**: Near real-time → +0.5 level
- **Business Critical**: Important → +0.5 level

**Final Difficulty**: Medium + 3 levels = **Very High**  
**Expected Duration**: 12-18 months → 18-24 months

#### Example 2: Base High Difficulty System

- **PL/SQL Code**: 80,000 lines → High
- **External Integration**: 2 → Maintain
- **Batch Jobs**: 8 → Maintain
- **Data Volume**: 500GB → Maintain
- **Real-time Processing**: Batch-centric → Maintain
- **Business Critical**: General → Maintain

**Final Difficulty**: High (no adjustment)  
**Expected Duration**: 12-18 months

---

## Replatform vs Refactor Strategy Selection

### Overview

When migrating large amounts of PL/SQL code, choosing between Refactor (manual conversion) and Replatform (automation tool utilization) requires comprehensive consideration of cost, risk, and maintainability.

### Strategy Comparison

#### Refactor (Manual Conversion)

**Advantages:**
- Code quality improvement opportunity
- Business logic optimization possible
- Legacy code cleanup

**Disadvantages:**
- High labor costs
- Long project duration
- Human error possibility
- Code quality variance

#### Replatform (Automation Tool Utilization)

**Advantages:**
- Fast migration
- Consistent conversion rules
- Low human error
- Predictable results

**Disadvantages:**
- Initial tool investment cost
- Legacy code migrated as-is
- Some manual fixes needed

---

### 50,000 Line Threshold: Replatform Recommended

#### Cost Efficiency Analysis

**Refactor Cost (50,000 line baseline)**

Work time calculation:
- **Simple Code (complexity < 5.0)**: 15-20 min/line
- **Medium Code (complexity 5.0-7.0)**: 20-30 min/line
- **Complex Code (complexity > 7.0)**: 30-60 min/line

Example: 50,000 lines, average complexity 5.0
- Work time: 50,000 lines × 20 min = 16,667 hours
- With 3 developers: ~33 weeks (8 months)
- Labor cost ($100/hour baseline): $1,666,700

**Replatform Cost (50,000 line baseline)**

Work time calculation:
- Automatic conversion: 50,000 lines × 1 min = 833 hours
- Validation and fixes (30% manual work): 5,000 hours
- Total work time: ~5,833 hours

Example: 50,000 lines, average complexity 5.0
- With 3 developers: ~12 weeks (3 months)
- Tool cost: $50,000-$100,000
- Labor cost ($100/hour baseline): $583,300
- Total cost: $633,300-$683,300

**Cost Savings:**
- Savings: $983,400-$1,033,400 (~60% reduction)
- Duration reduction: 5 months shorter

---

### Automatic Conversion Success Rate by Complexity

#### Low Complexity (< 5.0)

**Automatic Conversion Success Rate: 80-90%**

- Simple CRUD logic
- Standard SQL syntax
- Basic PL/SQL structure

**Manual Work Needed:**
- Only 10-20% manual fixes
- Mainly business logic validation

#### Medium Complexity (5.0-7.0)

**Automatic Conversion Success Rate: 60-75%**

- Medium complexity business logic
- Some Oracle-specific functions
- Nested queries

**Manual Work Needed:**
- 25-40% manual fixes
- Oracle-specific feature replacement
- Performance optimization

#### High Complexity (> 7.0)

**Automatic Conversion Success Rate: 30-50%**

- Complex business logic
- Multiple Oracle-specific features
- Dynamic SQL

**Manual Work Needed:**
- 50-70% manual fixes
- Most rewrite needed
- Consider Refactor

---

### Risk Management

#### Refactor Risks

1. **Human Error**
   - High mistake possibility with large manual conversion
   - Increased code review burden
   - Difficult to secure test coverage

2. **Code Quality Variance**
   - Coding style differences per developer
   - Inconsistent pattern application
   - Maintenance difficulties

3. **Project Delays**
   - Longer work time than expected
   - Resource shortage
   - Scope Creep

#### Replatform Risk Mitigation

1. **Consistent Conversion**
   - Standardized conversion rules
   - Automated code review
   - Predictable results

2. **Fast Validation**
   - Automated testing
   - Fast feedback loop
   - Early issue detection

3. **Predictability**
   - Clear timeline
   - Accurate cost estimation
   - Risk minimization

---

### Maintainability

#### Post-Refactor Maintenance

**Advantages:**
- Latest coding standards applied
- Unnecessary code removed
- Documentation improved

**Disadvantages:**
- Quality variance per developer
- Inconsistent patterns
- Learning curve

#### Post-Replatform Maintenance

**Advantages:**
- Consistent code patterns
- Standardized structure
- Predictable behavior

**Disadvantages:**
- Legacy patterns maintained
- Technical debt migrated
- Future refactoring needed

---

### Real Cases

#### Case 1: Financial Company (80,000 lines, complexity 5.2)

**Selected Strategy:** Replatform

**Results:**
- Duration: 4 months (expected 12 months)
- Cost: $850,000 (expected $2,100,000)
- Automatic conversion success rate: 72%
- Manual fixes: 28%

**Lessons:**
- Automation tool investment value proven
- Business continuity secured through fast migration

#### Case 2: Manufacturing Company (30,000 lines, complexity 4.5)

**Selected Strategy:** Refactor

**Results:**
- Duration: 6 months
- Cost: $900,000
- Code quality greatly improved
- Technical debt reduced by 50%

**Lessons:**
- Small projects improve quality with Refactor
- Long-term maintenance cost reduction

---

## Decision-Making Guide

### Strategy Selection by Difficulty

| Final Difficulty | Lines of Code | Recommended Strategy | Notes |
|-----------------|--------------|---------------------|-------|
| Low | < 20,000 | Refactor (MySQL/PostgreSQL) | Cost-effective, fast transition |
| Medium | 20,000-50,000 | Refactor (PostgreSQL) | Leverage PL/SQL compatibility |
| High | 50,000-100,000 | Consider Replatform first | Cost/time savings |
| Very High | 100,000+ | Strongly recommend Replatform | Minimize conversion risk |

### Replatform Recommended Conditions

When **all** of the following conditions are met:

1. **PL/SQL code 50,000+ lines**
2. **Average complexity < 7.0** (auto-conversion possible)
3. **Fast migration needed** (within 6 months)
4. **Cost reduction priority**

**Expected Effects:**
- 50-60% cost reduction
- 50-70% duration reduction
- 30-40% risk reduction

### Refactor Recommended Conditions

When **one or more** of the following conditions apply:

1. **PL/SQL code < 50,000 lines**
2. **Average complexity < 5.0** (simple logic)
3. **Code quality improvement needed**
4. **Sufficient time secured** (12+ months)

**Expected Effects:**
- Code quality improvement
- Technical debt resolution
- Long-term maintenance improvement

### Serious Replatform Consideration Point

When **2 or more** of the following conditions apply:

1. PL/SQL code 100,000+ lines + average complexity 7.0+
2. External system integration 15+
3. Mission-critical system + real-time processing requirements
4. Data volume 20TB+
5. Expected migration duration 24+ months

### Hybrid Approach (50,000-100,000 lines)

Consider the following strategy:

1. **Simple Code (70%)**: Replatform (automatic conversion)
2. **Complex Code (30%)**: Refactor (manual conversion)
3. **Phased Migration**: Sequential by module

---

### Decision-Making Checklist

- [ ] Check PL/SQL lines of code
- [ ] Assess average complexity
- [ ] Check number of external system integrations
- [ ] Assess data volume
- [ ] Check project duration constraints
- [ ] Check budget constraints
- [ ] Check automation tool availability
- [ ] Assess team capabilities
- [ ] Check business priorities

---

## Notes

- Complexity scores indicate conversion difficulty and may not be directly proportional to actual conversion time.
- Even with the same score, conversion difficulty may vary depending on query characteristics.
- Use complexity scores for determining conversion priorities and resource allocation.
- Actual migration requires automatic conversion tools (AWS SCT, Amazon Q Developer, Bedrock) and expert review.
- When there are many PL/SQL objects, DB-only migration is not possible, and application-level reimplementation should be considered.
- AI conversion tools have difficulty automatically converting objects with complexity 7.0+.

## Related Documents

- [Oracle to PostgreSQL Migration Guide](migration_guide_aurora_pg16_EN.md)
- [Oracle to MySQL Migration Guide](complexity_mysql_EN.md)
- [AI Tool-Assisted Migration](ai_assisted_migration_EN.md)
