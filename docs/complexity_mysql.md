# Oracle to MySQL 마이그레이션 복잡도 계산 공식

이 문서는 Oracle에서 MySQL로 마이그레이션 시 SQL 쿼리와 PL/SQL 오브젝트의 복잡도를 계산하는 공식입니다.

## MySQL 특성

- **MySQL 8.0.42 이상 기준**
- **멀티스레드 아키텍처**: 경량 스레드 기반 연결 처리
- **단순 쿼리에 강함**: 인덱스 기반 조회 성능 우수
- **풀스캔 성능 약함**: 대용량 테이블 풀스캔 시 성능 저하
- **복잡한 JOIN 약함**: 3개 이상 JOIN 시 성능 저하 가능
- **COUNT(*) 성능 이슈**: 대량 데이터 카운트 시 느림
- **서브쿼리 최적화 제한**: 특히 IN 절 서브쿼리
- **윈도우 함수 지원**: 8.0부터 지원하나 일부 제한
- **CTE 지원**: 8.0부터 지원하나 최적화 제한
- **Stored Procedure 제한**: 비즈니스 로직 사용 시 컴파일 오버헤드 및 메모리 누수 이슈로 **애플리케이션 레벨 이관 권장**

## SQL 쿼리 복잡도 계산

### 1. 구조적 복잡성 (최대 4.5점)

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score + fullscan_penalty
```

**JOIN 점수**:
```
if join_count == 0: 0점
elif join_count <= 2: 1.0점
elif join_count <= 4: 2.0점
elif join_count <= 6: 3.0점
else: 4.0점
```

**서브쿼리 점수**:
```
if depth == 0: 0점
elif depth == 1: 1.5점
elif depth == 2: 3.0점
else: 4.0 + min(2, depth - 2)
```

**CTE 점수**: `min(2.0, cte_count * 0.8)`

**집합 연산자 점수**: `min(2.0, set_operators_count * 0.8)`

**풀스캔 페널티**:
```
if no_where_clause or likely_fullscan: 1.0점
else: 0점
```

### 2. Oracle 특화 기능 (최대 3.0점)

```
oracle_specific = connect_by_score + analytic_functions_score + pivot_score + model_score
```

- **CONNECT BY**: 2점
- **분석 함수**: `min(3, analytic_functions_count)`
  - ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, FIRST_VALUE, LAST_VALUE
  - NTILE, CUME_DIST, PERCENT_RANK, RATIO_TO_REPORT
- **PIVOT/UNPIVOT**: 2점
- **MODEL 절**: 3점

### 3. 함수 및 표현식 (최대 2.5점)

```
functions = agg_functions_score + udf_score + case_score + regexp_score + count_penalty + special_agg_penalty
```

- **집계 함수**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **사용자 정의 함수**: `min(2, potential_udf * 0.5)`
- **CASE 표현식**: `min(2, case_count * 0.5)`
- **정규식**: 1점 (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)
- **COUNT(*) 페널티**: 0.5점 (WHERE 절 없거나 대량 결과 예상 시)
- **특수 집계 함수 페널티**: 
  ```
  if has_median or has_percentile: +0.5점
  if has_listagg: +0.3점
  if has_xmlagg: +0.5점
  if has_keep_clause: +0.5점
  ```

### 4. 데이터 처리 볼륨 (최대 2.5점)

```
if length < 200: 0.5점
elif length < 500: 1.2점
elif length < 1000: 2.0점
else: 2.5점
```

### 5. 실행 계획 복잡성 (최대 2.5점)

```
execution = join_depth_score + order_by_score + group_by_score + having_score + derived_table_score + performance_penalty
```

**조인 깊이**:
```
if join_count > 3 or subquery_depth > 1: 1.5점
elif join_count > 2 or subquery_depth > 0: 0.8점
else: 0점
```

- **ORDER BY**: 0.5점
- **GROUP BY**: 0.5점
- **HAVING**: 0.5점
- **파생 테이블**: `min(1.0, derived_table_count * 0.5)`
- **성능 페널티**:
  ```
  if has_distinct: +0.3점
  if has_multiple_or_conditions: +0.3점 (OR 조건 3개 이상)
  if has_like_wildcard_both: +0.3점 (LIKE '%문자열%')
  if has_function_in_where: +0.5점 (WHERE 절에 함수 사용)
  ```

### 6. MySQL 변환 난이도 (최대 3.0점)

```
conversion = oracle_syntax_score + oracle_functions_score + hints_score
```

#### Oracle 특화 문법

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
- REGEXP_*
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

### 최종 SQL 복잡도 점수

```python
total_score = structural + oracle_specific + functions + data_volume + execution + conversion
max_possible_score = 4.5 + 3.0 + 2.5 + 2.5 + 2.5 + 3.0 = 18.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## PL/SQL 오브젝트 복잡도 계산

**중요**: MySQL로 마이그레이션 시 모든 PL/SQL 오브젝트는 애플리케이션 레벨로 이관해야 합니다.

### 기본 점수 (애플리케이션 이관 난이도)

| 오브젝트 타입 | 기본 점수 | 애플리케이션 이관 난이도 |
|--------------|----------|----------------------|
| Package | 8.0 | 매우 높음 (여러 함수/프로시저 분리 필요) |
| Procedure | 6.0 | 높음 (비즈니스 로직 재구현) |
| Function | 5.0 | 높음 (반환 로직 재구현) |
| Trigger | 7.0 | 매우 높음 (이벤트 처리 재설계) |
| View | 2.0 | 낮음 (SQL 쿼리만 변환) |
| Materialized View | 5.0 | 높음 (수동 리프레시 로직 구현) |

**참고**: 기본 점수가 Stored Procedure 변환 대비 1.0~2.0점 높게 책정됨 (애플리케이션 재구현 난이도 반영)

### 복잡도 계산 공식

```
plsql_complexity = base_score + code_complexity + oracle_features + business_logic + ai_difficulty
```

### 1. 코드 복잡도 (최대 3.0점)

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

### 2. Oracle 특화 기능 (최대 3.0점)

- **패키지 의존성**: `min(2.0, package_calls * 0.5)`
- **DB Link**: `min(1.5, dblink_count * 1.0)`
- **동적 SQL**: `min(1.0, dynamic_sql_count * 0.5)`
- **BULK 연산**: `min(0.8, bulk_operations_count * 0.3)` (MySQL 미지원, 루프로 변환)
- **고급 기능**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED 함수 (MySQL 미지원)
  - REF CURSOR (MySQL 미지원)
  - AUTONOMOUS TRANSACTION (MySQL 제한적)
  - PRAGMA
  - OBJECT TYPE (MySQL 미지원)

### 3. 비즈니스 로직 복잡도 (최대 2.0점)

- **트랜잭션 처리**: 0.5~0.8점
  - SAVEPOINT: 지원
  - ROLLBACK TO SAVEPOINT: 지원
  - 중첩 트랜잭션: 제한적
- **복잡한 계산**: `min(1.0, complex_calculations * 0.3)`
- **데이터 검증**: `min(0.5, validation_checks * 0.2)`

### 4. AI 변환 불가능 난이도 (최대 2.0점)

- **컨텍스트 의존성**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT (MySQL 미지원, 세션 변수로 대체)
  - 세션 변수 의존
  - 글로벌 임시 테이블 (MySQL은 TEMPORARY TABLE)
- **상태 관리**: 0.8점 (패키지 변수 사용 시, MySQL은 세션 변수로 대체)
- **외부 의존성**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE (MySQL 미지원)
  - UTL_HTTP (MySQL 미지원)
  - UTL_MAIL (MySQL 미지원)
  - DBMS_SCHEDULER (MySQL EVENT로 대체)
- **커스텀 로직**: 0.5~1.0점

### 5. MySQL 특화 제약 (최대 1.5점)

```
mysql_constraints = datatype_conversion + trigger_constraints + view_constraints
```

- **데이터 타입 변환**: 
  ```
  if has_number_precision_issue: +0.5점
  if has_clob_blob: +0.3점
  if has_varchar2_empty_string: +0.3점
  ```
- **트리거 제약**:
  ```
  if has_instead_of_trigger: +0.5점
  if has_compound_trigger: +0.5점
  ```
- **뷰 제약**:
  ```
  if has_materialized_view: +0.5점
  if has_complex_updatable_view: +0.3점
  ```

### 최종 PL/SQL 복잡도 점수

```python
total_score = base + code + oracle + business + ai_difficulty + mysql_constraints + app_migration_penalty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 + 1.5 + 2.0 = 23.5
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

**애플리케이션 이관 페널티** (app_migration_penalty):
```
if object_type in ['PACKAGE', 'PROCEDURE', 'FUNCTION']:
    app_migration_penalty = 2.0  # 애플리케이션 재구현 필수
elif object_type == 'TRIGGER':
    app_migration_penalty = 1.5  # 이벤트 처리 재설계
else:
    app_migration_penalty = 0
```

## 복잡도 레벨 분류

### SQL 쿼리

| 점수 | 레벨 | MySQL 변환 |
|------|------|-----------|
| 0-1 | 매우 간단 | 자동 변환 |
| 1-3 | 간단 | 함수 대체 |
| 3-5 | 중간 | 부분 재작성 + 성능 튜닝 |
| 5-7 | 복잡 | 상당한 재작성 + 쿼리 최적화 |
| 7-9 | 매우 복잡 | 대부분 재작성 + 아키텍처 변경 |
| 9-10 | 극도로 복잡 | 완전 재설계 |

### PL/SQL 오브젝트

| 점수 | 레벨 | MySQL 변환 |
|------|------|-----------|
| 0-3 | 간단 | **애플리케이션 레벨 이관 (단순 로직)** |
| 3-5 | 중간 | **애플리케이션 레벨 이관 (중간 로직)** |
| 5-7 | 복잡 | **애플리케이션 레벨 이관 (복잡 로직)** |
| 7-9 | 매우 복잡 | **애플리케이션 레벨 재설계 필수** |
| 9-10 | 극도로 복잡 | **애플리케이션 레벨 완전 재구현 필수** |

**중요**: MySQL Stored Procedure는 비즈니스 로직 처리 시 다음 문제가 있습니다:
- 매번 컴파일 오버헤드
- 메모리 누수 가능성
- 디버깅 및 유지보수 어려움
- 버전 관리 어려움

따라서 **모든 PL/SQL 오브젝트는 애플리케이션 레벨로 이관을 권장**합니다.

## MySQL 변환 가이드

### Oracle → MySQL 주요 변환

| Oracle | MySQL | 난이도 | 주의사항 |
|--------|-------|-------|---------|
| ROWNUM | LIMIT | 낮음 | OFFSET 사용 시 성능 주의 |
| CONNECT BY | 재귀 쿼리 또는 애플리케이션 | 높음 | MySQL 8.0+ CTE 사용 가능하나 성능 제한 |
| DECODE | CASE | 낮음 | - |
| NVL | IFNULL | 낮음 | - |
| SYSDATE | NOW() | 낮음 | - |
| MERGE | INSERT ON DUPLICATE KEY | 중간 | 문법 차이 큼 |
| PIVOT | GROUP BY + CASE | 중간 | 수동 변환 필요 |
| (+) JOIN | LEFT/RIGHT JOIN | 낮음 | - |
| SEQUENCE.NEXTVAL | AUTO_INCREMENT | 중간 | 테이블 구조 변경 필요 |
| Package | 애플리케이션 레벨 | 높음 | **Stored Procedure 사용 불가, 애플리케이션으로 이관 필수** |
| Procedure | 애플리케이션 레벨 | 높음 | **Stored Procedure 사용 불가, 애플리케이션으로 이관 필수** |
| Function | 애플리케이션 레벨 | 높음 | **Stored Function 사용 불가, 애플리케이션으로 이관 필수** |
| Trigger | 최소화 또는 애플리케이션 | 높음 | 단순 로직만 Trigger 사용, 복잡한 로직은 애플리케이션 |
| RETURNING | 별도 SELECT | 높음 | MySQL 미지원 |
| BULK COLLECT | 루프 처리 | 높음 | MySQL 미지원, 성능 저하 가능 |
| REF CURSOR | 임시 테이블 | 높음 | MySQL 미지원 |
| LISTAGG | GROUP_CONCAT | 중간 | 길이 제한 (기본 1024자) |
| MEDIAN | 복잡한 서브쿼리 | 높음 | MySQL 미지원 |
| Materialized View | 수동 구현 | 높음 | MySQL 미지원, 트리거로 구현 |
| 빈 문자열 NULL | 명시적 처리 | 낮음 | Oracle은 NULL, MySQL은 구분 |
| 문자열 연결 (||) | CONCAT() | 낮음 | 함수 변환 |
| 날짜 연산 (+/-) | DATE_ADD/DATE_SUB | 낮음 | 함수 변환 |

## MySQL 특수 고려사항

### 1. 복잡한 JOIN 회피

- 3개 이상 JOIN 시 성능 저하 가능
- 가능하면 JOIN 수를 줄이거나 비정규화 고려
- 인덱스 최적화 필수

### 2. 서브쿼리 최적화

- IN 절 서브쿼리는 JOIN으로 변환 권장
- 상관 서브쿼리는 성능 이슈 가능
- EXISTS 사용 고려

### 3. COUNT(*) 최적화

- WHERE 절 없는 COUNT(*)는 매우 느림
- 가능하면 근사값 사용 또는 캐싱
- 인덱스 활용 필수

### 4. 풀스캔 회피

- WHERE 절 필수
- 적절한 인덱스 생성
- LIMIT 사용으로 결과 제한

### 5. CTE 사용 제한

- MySQL 8.0부터 지원하나 최적화 제한적
- 복잡한 CTE는 임시 테이블 고려
- 성능 테스트 필수

### 6. 분석 함수 제한

- MySQL 8.0부터 윈도우 함수 지원
- 일부 Oracle 분석 함수 미지원
- 대체 방법 필요 (MEDIAN, PERCENTILE 등)

### 7. 데이터 타입 변환 이슈

- **NUMBER → DECIMAL/INT**: 정밀도 차이 주의
- **VARCHAR2 → VARCHAR**: 빈 문자열 처리 차이 (Oracle은 NULL, MySQL은 구분)
- **DATE → DATETIME**: 시간 정보 포함 여부
- **CLOB/BLOB → TEXT/LONGTEXT**: 크기 제한 확인
- **RAW → VARBINARY**: 바이너리 데이터 변환

### 8. 집계 함수 제약

- **LISTAGG → GROUP_CONCAT**: 길이 제한 있음 (기본 1024자)
- **MEDIAN**: MySQL 미지원 (복잡한 서브쿼리 필요)
- **PERCENTILE_CONT/DISC**: MySQL 미지원
- **XMLAGG**: MySQL 미지원
- **KEEP 절**: MySQL 미지원
- **WITHIN GROUP**: MySQL 미지원

### 9. 문자열 및 날짜 처리 차이

- **문자열 연결**: Oracle `||` → MySQL `CONCAT()`
- **날짜 연산**: Oracle `DATE + 1` → MySQL `DATE_ADD(DATE, INTERVAL 1 DAY)`
- **NULL 처리**: Oracle 빈 문자열('')을 NULL로 처리, MySQL은 구분
- **대소문자 구분**: 테이블명은 OS 의존적 (Linux는 구분, Windows는 미구분)

### 10. 인덱스 제약

- **함수 기반 인덱스**: MySQL 8.0.13부터 지원하나 제한적
- **비트맵 인덱스**: MySQL 미지원
- **역방향 인덱스**: MySQL 미지원
- **인덱스 구성 컬럼**: 최대 16개 제한

### 11. 트리거 제약

- **INSTEAD OF 트리거**: MySQL 미지원 (뷰에 대한 트리거)
- **복합 트리거**: MySQL 미지원
- **트리거 내 트랜잭션 제어**: 제한적
- **:NEW/:OLD**: MySQL은 NEW/OLD (콜론 없음)

### 12. Stored Procedure 제약

**중요**: MySQL Stored Procedure는 비즈니스 로직 처리에 부적합합니다.

**문제점**:
- **컴파일 오버헤드**: 매번 실행 시 컴파일 필요
- **메모리 누수**: 장기 실행 시 메모리 누수 가능성
- **성능 저하**: 복잡한 로직 처리 시 성능 문제
- **디버깅 어려움**: 디버깅 도구 제한적
- **버전 관리 어려움**: 소스 코드 관리 복잡
- **배포 복잡성**: 애플리케이션과 별도 배포 필요

**제약사항**:
- **OUT/IN OUT 파라미터**: 제한적 지원
- **커서 변수 (REF CURSOR)**: MySQL 미지원
- **BULK COLLECT**: MySQL 미지원
- **FORALL**: MySQL 미지원
- **예외 처리**: MySQL은 HANDLER 사용 (문법 다름)
- **패키지 변수**: MySQL 미지원 (세션 변수로 대체)
- **RETURN 문 (Function)**: 문법 차이

**권장 사항**:
- **모든 비즈니스 로직은 애플리케이션 레벨로 이관**
- Trigger는 최소한의 데이터 무결성 검증만 사용
- 복잡한 로직은 애플리케이션에서 처리

### 13. 뷰(View) 제약

- **복잡한 뷰**: 업데이트 불가능한 경우 많음
- **Materialized View**: MySQL 미지원 (수동 구현 필요)
- **뷰 내 ORDER BY**: 제한적

### 14. 파티셔닝 제약

- **범위 파티셔닝**: 지원하나 제약 있음
- **리스트 파티셔닝**: 지원
- **해시 파티셔닝**: 지원
- **복합 파티셔닝**: 제한적
- **파티션 프루닝**: 최적화 제한

### 15. 트랜잭션 및 락

- **FOR UPDATE NOWAIT**: MySQL 8.0부터 지원
- **FOR UPDATE SKIP LOCKED**: MySQL 8.0부터 지원
- **SAVEPOINT**: 지원
- **트랜잭션 격리 수준**: 기본값 차이 (Oracle: READ COMMITTED, MySQL: REPEATABLE READ)

## 성능 최적화 체크리스트

- [ ] JOIN 수 3개 이하로 제한
- [ ] WHERE 절 필수 포함
- [ ] 적절한 인덱스 생성
- [ ] 서브쿼리를 JOIN으로 변환
- [ ] COUNT(*) 사용 최소화
- [ ] LIMIT으로 결과 제한
- [ ] 풀스캔 회피
- [ ] 파생 테이블 최소화
- [ ] CTE 대신 임시 테이블 고려
- [ ] 쿼리 실행 계획 확인 (EXPLAIN)
- [ ] DISTINCT 사용 최소화
- [ ] OR 조건 최소화 (가능하면 UNION으로 변환)
- [ ] LIKE '%문자열%' 회피
- [ ] WHERE 절에 함수 사용 회피
- [ ] GROUP_CONCAT 길이 제한 확인
- [ ] 트랜잭션 격리 수준 확인
- [ ] 인덱스 힌트 사용 고려
- [ ] 파티셔닝 전략 수립

## MySQL 8.0.42 신규 기능 활용

- **윈도우 함수**: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD 등 활용
- **CTE (WITH 절)**: 복잡한 쿼리 단순화 (단, 성능 테스트 필수)
- **재귀 CTE**: CONNECT BY 대체 (성능 주의)
- **JSON 함수**: JSON 데이터 처리
- **함수 기반 인덱스**: 8.0.13부터 지원
- **내림차순 인덱스**: 8.0부터 지원
- **NOWAIT/SKIP LOCKED**: 8.0부터 지원

## 참고 사항

- MySQL은 복잡한 쿼리 처리에 약하므로 구조적 복잡성 가중치가 높습니다.
- **모든 PL/SQL 오브젝트는 애플리케이션 레벨로 이관해야 합니다** (Stored Procedure 사용 불가).
- MySQL Stored Procedure는 컴파일 오버헤드와 메모리 누수 문제로 비즈니스 로직 처리에 부적합합니다.
- MySQL은 일부 Oracle 분석 함수를 지원하지 않습니다.
- CONNECT BY는 MySQL에서 구현이 매우 어려우므로 애플리케이션 레벨 처리 권장합니다.
- 성능 최적화가 PostgreSQL보다 더 중요합니다.
- Trigger는 최소한의 데이터 무결성 검증만 사용하고, 복잡한 로직은 애플리케이션에서 처리하세요.
