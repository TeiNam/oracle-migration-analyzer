# Oracle SQL 쿼리 복잡도 계산 공식

이 문서는 Oracle SQL 쿼리와 PL/SQL 오브젝트의 복잡도를 계산하는 수식과 알고리즘을 설명합니다. 타겟 데이터베이스(PostgreSQL/MySQL)의 특성에 따라 다른 가중치를 적용합니다.

## 목차

1. [복잡도 점수 개요](#복잡도-점수-개요)
2. [타겟 데이터베이스 특성 비교](#타겟-데이터베이스-특성-비교)
3. [SQL 쿼리 복잡도 계산](#sql-쿼리-복잡도-계산)
4. [PL/SQL 오브젝트 복잡도 계산](#plsql-오브젝트-복잡도-계산)
5. [복잡도 레벨 분류](#복잡도-레벨-분류)

## 복잡도 점수 개요

복잡도 점수는 0-10 척도로 표현되며, Oracle에서 타겟 데이터베이스로의 변환 난이도를 나타냅니다.

**중요**: PostgreSQL과 MySQL은 아키텍처와 성능 특성이 다르므로, 동일한 Oracle 쿼리라도 타겟 데이터베이스에 따라 복잡도 점수가 달라집니다.

## 타겟 데이터베이스 특성 비교

### PostgreSQL
- 멀티프로세스 아키텍처
- 복잡한 JOIN, 서브쿼리, CTE 최적화 우수
- 풀스캔 성능 우수
- 고급 기능 지원 (윈도우 함수, 재귀 CTE, LATERAL JOIN)

### MySQL
- 멀티스레드 아키텍처
- 단순 쿼리에 강함
- 풀스캔 성능 약함
- 복잡한 JOIN 약함 (3개 이상)
- COUNT(*) 성능 이슈
- 서브쿼리 최적화 제한

### 복잡도 가중치 차이

| 요소 | PostgreSQL | MySQL |
|------|-----------|-------|
| 복잡한 JOIN (3개 이상) | 낮음 | 높음 |
| 서브쿼리 중첩 | 낮음 | 높음 |
| 풀스캔 예상 쿼리 | 낮음 | 높음 |
| COUNT(*) 집계 | 낮음 | 높음 |
| CTE 사용 | 낮음 | 중간 |

## SQL 쿼리 복잡도 계산

SQL 쿼리 복잡도는 6가지 카테고리로 계산됩니다.

### 1. 구조적 복잡성 (Structural Complexity)

**PostgreSQL**: 최대 2.5점  
**MySQL**: 최대 4.5점

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score + fullscan_penalty(MySQL만)
```

#### JOIN 점수

**PostgreSQL**:
```
if join_count == 0: 0점
elif join_count <= 3: 0.5점
elif join_count <= 5: 1.0점
else: 1.5점
```

**MySQL**:
```
if join_count == 0: 0점
elif join_count <= 2: 1.0점
elif join_count <= 4: 2.0점
elif join_count <= 6: 3.0점
else: 4.0점
```

#### 서브쿼리 점수

**PostgreSQL**:
```
if depth == 0: 0점
elif depth == 1: 0.5점
elif depth == 2: 1.0점
else: 1.5 + min(1, (depth - 2) * 0.5)
```

**MySQL**:
```
if depth == 0: 0점
elif depth == 1: 1.5점
elif depth == 2: 3.0점
else: 4.0 + min(2, depth - 2)
```

#### CTE 점수

**PostgreSQL**: `min(1.0, cte_count * 0.5)`  
**MySQL**: `min(2.0, cte_count * 0.8)`

#### 집합 연산자 점수

**PostgreSQL**: `min(1.5, set_operators_count * 0.5)`  
**MySQL**: `min(2.0, set_operators_count * 0.8)`

#### 풀스캔 페널티 (MySQL만)

```
if no_where_clause or likely_fullscan: 1.0점
else: 0점
```

### 2. Oracle 특화 기능 (Oracle-Specific Features)

**최대 점수**: 3.0점 (PostgreSQL/MySQL 동일)

```
oracle_specific = connect_by_score + analytic_functions_score + pivot_score + model_score
```

- **CONNECT BY**: 2점
- **분석 함수**: `min(3, analytic_functions_count)`
  - ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, FIRST_VALUE, LAST_VALUE
  - NTILE, CUME_DIST, PERCENT_RANK, RATIO_TO_REPORT
- **PIVOT/UNPIVOT**: 2점
- **MODEL 절**: 3점

### 3. 함수 및 표현식 (Functions & Expressions)

**PostgreSQL**: 최대 2.0점  
**MySQL**: 최대 2.5점

```
functions = agg_functions_score + udf_score + case_score + regexp_score + count_penalty(MySQL만)
```

- **집계 함수**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **사용자 정의 함수**: `min(2, potential_udf * 0.5)`
- **CASE 표현식**: `min(2, case_count * 0.5)`
- **정규식**: 1점 (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)
- **COUNT(*) 페널티 (MySQL만)**: 0.5점 (WHERE 절 없거나 대량 결과 예상 시)

### 4. 데이터 처리 볼륨 (Data Volume)

**PostgreSQL**: 최대 2.0점  
**MySQL**: 최대 2.5점

**PostgreSQL**:
```
if length < 200: 0.5점
elif length < 500: 1.0점
elif length < 1000: 1.5점
else: 2.0점
```

**MySQL**:
```
if length < 200: 0.5점
elif length < 500: 1.2점
elif length < 1000: 2.0점
else: 2.5점
```

### 5. 실행 계획 복잡성 (Execution Complexity)

**PostgreSQL**: 최대 1.0점  
**MySQL**: 최대 2.5점

```
execution = join_depth_score + order_by_score + group_by_score + having_score + derived_table_score(MySQL만)
```

**PostgreSQL**:
- **조인 깊이**: 0.5점 (join_count > 5 or subquery_depth > 2)
- **ORDER BY**: 0.2점
- **GROUP BY**: 0.2점
- **HAVING**: 0.2점

**MySQL**:
- **조인 깊이**: 
  - 1.5점 (join_count > 3 or subquery_depth > 1)
  - 0.8점 (join_count > 2 or subquery_depth > 0)
- **ORDER BY**: 0.5점
- **GROUP BY**: 0.5점
- **HAVING**: 0.5점
- **파생 테이블**: `min(1.0, derived_table_count * 0.5)`

### 6. 데이터베이스 변환 난이도 (Conversion Difficulty)

**최대 점수**: 3.0점 (PostgreSQL/MySQL 동일)

```
conversion = oracle_syntax_score + oracle_functions_score + hints_score
```

#### Oracle 특화 문법 (각 점수 명시)

- **CONNECT BY**: 1점
- **START WITH**: 1점
- **PRIOR**: 1점
- **MODEL**: 1점
- **PIVOT/UNPIVOT**: 1점
- **FLASHBACK**: 1점
- **SYS_CONNECT_BY_PATH**: 1점
- **ROWID**: 1점
- **ROWNUM**: 1점
- **LEVEL**: 1점
- **MERGE 문**: 1.5점
- **OUTER JOIN (+)**: 1.0점
- **SEQUENCE.NEXTVAL/CURRVAL**: 0.8점
- **RETURNING 절**: 0.8점
- **DUAL 테이블**: 0.3점

#### Oracle 특화 함수 (각 0.5점)

- DECODE
- NVL, NVL2
- LISTAGG
- REGEXP_* (정규식 함수)
- SYS_CONTEXT
- EXTRACT
- TO_CHAR, TO_DATE, TO_NUMBER
- TRUNC
- ADD_MONTHS, MONTHS_BETWEEN, NEXT_DAY, LAST_DAY
- SYSDATE, SYSTIMESTAMP, CURRENT_DATE
- SUBSTR, INSTR, CHR, TRANSLATE

#### 힌트 점수

```
if hint_count == 0: 0점
elif hint_count <= 2: 0.5점
elif hint_count <= 5: 1.0점
else: 1.5점
```

힌트 예시: INDEX, FULL, PARALLEL, USE_HASH, USE_NL, APPEND, NO_MERGE

### 최종 복잡도 점수 계산

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

## PL/SQL 오브젝트 복잡도 계산

PL/SQL 오브젝트는 단순 SQL보다 훨씬 복잡하며, DB만 이관할 수 없는 상황입니다.

### 오브젝트 타입별 기본 복잡도

| 오브젝트 타입 | 기본 점수 | 설명 |
|--------------|----------|------|
| Package | 7.0 | 여러 프로시저/함수 포함, 상태 관리 |
| Procedure | 5.0 | 비즈니스 로직, 트랜잭션 처리 |
| Function | 4.0 | 반환값 있는 로직 |
| Trigger | 6.0 | 이벤트 기반 로직 |
| View | 2.0 | 복잡한 쿼리 캡슐화 |
| Materialized View | 4.0 | 성능 최적화, 리프레시 로직 |

### PL/SQL 복잡도 계산 공식

```
plsql_complexity = base_score + code_complexity + oracle_features + business_logic + ai_difficulty
```

### 1. 기본 점수 (Base Score)

오브젝트 타입에 따라 2.0~7.0점

### 2. 코드 복잡도 (최대 3.0점)

```
code_complexity = lines_score + cursor_score + exception_score + nested_score
```

- **코드 라인 수**:
  ```
  if lines < 100: 0.5점
  elif lines < 300: 1.0점
  elif lines < 500: 1.5점
  elif lines < 1000: 2.0점
  else: 2.5점
  ```

- **커서 사용**: `min(1.0, cursor_count * 0.3)`
- **예외 처리**: `min(0.5, exception_blocks * 0.2)`
- **중첩 깊이**:
  ```
  if nesting_depth <= 2: 0점
  elif nesting_depth <= 4: 0.5점
  elif nesting_depth <= 6: 1.0점
  else: 1.5점
  ```

### 3. Oracle 특화 기능 (최대 3.0점)

```
oracle_features = package_dependency + dblink_score + dynamic_sql + bulk_operations + advanced_features
```

- **패키지 의존성**: `min(2.0, package_calls * 0.5)`
- **DB Link**: `min(1.5, dblink_count * 1.0)`
- **동적 SQL**: `min(1.0, dynamic_sql_count * 0.5)`
- **BULK 연산**: `min(0.8, bulk_operations_count * 0.3)`
- **고급 기능**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED, REF CURSOR, AUTONOMOUS TRANSACTION, PRAGMA, OBJECT TYPE

### 4. 비즈니스 로직 복잡도 (최대 2.0점)

```
business_logic = transaction_score + calculation_score + validation_score
```

- **트랜잭션 처리**:
  ```
  if has_savepoint or has_rollback: 0.8점
  elif has_commit: 0.5점
  else: 0점
  ```

- **복잡한 계산**: `min(1.0, complex_calculations * 0.3)`
- **데이터 검증**: `min(0.5, validation_checks * 0.2)`

### 5. AI 변환 불가능 난이도 (최대 2.0점)

```
ai_difficulty = context_dependency + state_management + external_dependency + custom_logic
```

- **컨텍스트 의존성**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT, 세션 변수, 글로벌 임시 테이블
- **상태 관리**: 0.8점 (패키지 변수 사용 시)
- **외부 의존성**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE, UTL_HTTP, UTL_MAIL, DBMS_SCHEDULER
- **커스텀 로직**:
  ```
  if highly_custom: 1.0점
  elif moderately_custom: 0.5점
  else: 0점
  ```

### 최종 PL/SQL 복잡도 계산

```python
total_score = base + code + oracle + business + ai_difficulty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 = 20.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## 복잡도 레벨 분류

### SQL 쿼리 복잡도 레벨

| 점수 | 레벨 | 설명 | 변환 접근 방식 |
|------|------|------|---------------|
| 0-1 | 매우 간단 | 표준 SQL만 사용 | 자동 변환 도구 |
| 1-3 | 간단 | 기본 Oracle 함수 | 함수 대체 |
| 3-5 | 중간 | 일부 Oracle 특화 기능 | 부분 재작성 |
| 5-7 | 복잡 | 다수 Oracle 특화 기능 | 상당한 재작성 |
| 7-9 | 매우 복잡 | 복잡한 Oracle 기능 조합 | 대부분 재작성 |
| 9-10 | 극도로 복잡 | 고급 Oracle 기능 | 완전 재설계 |

### PL/SQL 오브젝트 복잡도 레벨

| 점수 | 레벨 | 변환 가능성 | 권장 접근 방식 |
|------|------|------------|---------------|
| 0-3 | 간단 | AI 자동 변환 가능 | AWS SCT + 검토 |
| 3-5 | 중간 | AI 보조 + 수동 수정 | AI 변환 후 수동 조정 |
| 5-7 | 복잡 | 대부분 수동 변환 | 전문가 재작성 |
| 7-9 | 매우 복잡 | 완전 수동 변환 | 아키텍처 재설계 고려 |
| 9-10 | 극도로 복잡 | 변환 불가능 | 애플리케이션 레벨 재구현 |

## 마이그레이션 의사결정 가이드

| 평균 복잡도 | PL/SQL 오브젝트 수 | 권장 접근 방식 | 예상 난이도 |
|------------|-------------------|---------------|----------|
| < 3.0 | < 10 | DB 마이그레이션 | 낮음 |
| 3.0-5.0 | 10-50 | DB 마이그레이션 + 부분 재작성 | 중간 |
| 5.0-7.0 | 50-100 | DB 마이그레이션 + 상당한 재작성 | 높음 |
| 7.0-9.0 | 100-200 | 하이브리드 (DB + 앱 레벨) | 매우 높음 |
| > 9.0 | > 200 | 애플리케이션 레벨 재구현 | 극도로 높음 |

## 참고 사항

- 복잡도 점수는 변환 난이도를 나타내는 지표이며, 실제 변환 시간과 정확히 비례하지 않을 수 있습니다.
- 동일한 점수라도 쿼리 특성에 따라 변환 난이도가 다를 수 있습니다.
- 복잡도 점수는 변환 우선순위 결정과 리소스 할당에 활용하세요.
- 실제 마이그레이션 시 자동 변환 도구(AWS SCT)와 전문가 검토가 필요합니다.
- PL/SQL 오브젝트가 많은 경우 DB만 이관할 수 없으며, 애플리케이션 레벨 재구현을 고려해야 합니다.
- AI 변환 도구는 복잡도 7.0 이상의 오브젝트 자동 변환이 어렵습니다.
