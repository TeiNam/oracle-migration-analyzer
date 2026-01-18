# Oracle to PostgreSQL 마이그레이션 복잡도 계산 공식

> [English](./EN/complexity_postgresql_EN.md)

이 문서는 Oracle에서 PostgreSQL로 마이그레이션 시 SQL 쿼리와 PL/SQL 오브젝트의 복잡도를 계산하는 공식입니다.

## PostgreSQL 특성

- **PostgreSQL 16 이상 기준**
- **멀티프로세스 아키텍처**: 각 연결이 독립적인 프로세스
- **복잡한 쿼리에 강함**: 복잡한 JOIN, 서브쿼리, CTE 최적화 우수
- **풀스캔 성능 우수**: 대용량 테이블 스캔 효율적
- **고급 기능 지원**: 윈도우 함수, 재귀 CTE, LATERAL JOIN 등
- **분석 쿼리 최적화**: OLAP 워크로드에 적합
- **PostgreSQL 16 신규 기능**: 논리적 복제 개선, 병렬 쿼리 개선 (FULL/RIGHT JOIN), 증분 정렬 개선

## PL/pgSQL vs Oracle PL/SQL 성능 비교

### Context Switch 차이

**Oracle PL/SQL**:
- PL/SQL 엔진과 SQL 엔진 간 Context Switch 발생
- BULK COLLECT/FORALL로 Context Switch 최소화
- 예: 100,000행 INSERT 시 row-by-row 4.94초 vs FORALL 0.12초 (약 40배 차이)

**PostgreSQL PL/pgSQL**:
- BULK COLLECT/FORALL 미지원
- 대안 방식으로 성능 최적화 가능

### 성능 벤치마크 (AWS DMA, 1,000만 건 기준)

| 방식 | 상대 성능 |
|------|----------|
| LOOP (row-by-row) | 3.24X (가장 느림) |
| ARRAY_AGG + UNNEST | 1.4X |
| 순수 SQL | 1.12X |
| SQL + Chunked Batch | 1X (가장 빠름) |

### Oracle vs PostgreSQL 성능 차이 요약

| 영역 | 성능 차이 | 비고 |
|------|----------|------|
| 단순 프로시저 | 0-10% | 거의 동일 |
| 커서 처리 | 0-20% | 거의 동일 |
| BULK INSERT (최적화) | 20-50% 느림 | Chunked SQL 사용 시 |
| BULK INSERT (비최적화) | 200-400% 느림 | row-by-row LOOP 사용 시 |
| 대량 데이터 처리 | 30-50% 느림 | ARRAY_AGG/UNNEST 사용 시 |
| 복잡한 비즈니스 로직 | 10-30% | 유사 |

### PostgreSQL 16 성능 최적화 권장사항

1. **BULK 연산 대체**: 순수 SQL 또는 Chunked Batch 방식 사용
2. **row-by-row LOOP 회피**: 집합 기반 SQL로 변환
3. **PostgreSQL 16 병렬 쿼리 활용**: FULL/RIGHT JOIN 병렬 처리
4. **증분 정렬 활용**: 대용량 데이터 정렬 성능 향상

## SQL 쿼리 복잡도 계산

### 1. 구조적 복잡성 (최대 2.5점)

```
structural_complexity = join_score + subquery_score + cte_score + set_operators_score
```

**JOIN 점수**:
```
if join_count == 0: 0점
elif join_count <= 3: 0.5점
elif join_count <= 5: 1.0점
else: 1.5점
```

**서브쿼리 점수**:
```
if depth == 0: 0점
elif depth == 1: 0.5점
elif depth == 2: 1.0점
else: 1.5 + min(1, (depth - 2) * 0.5)
```

**CTE 점수**: `min(1.0, cte_count * 0.5)`

**집합 연산자 점수**: `min(1.5, set_operators_count * 0.5)`

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

### 3. 함수 및 표현식 (최대 2.0점)

```
functions = agg_functions_score + udf_score + case_score + regexp_score
```

- **집계 함수**: `min(2, agg_functions_count * 0.5)`
  - COUNT, SUM, AVG, MAX, MIN, LISTAGG, XMLAGG, MEDIAN, PERCENTILE_*
- **사용자 정의 함수**: `min(2, potential_udf * 0.5)`
- **CASE 표현식**: `min(2, case_count * 0.5)`
- **정규식**: 1점 (REGEXP_LIKE, REGEXP_SUBSTR, REGEXP_REPLACE, REGEXP_INSTR)

### 4. 데이터 처리 볼륨 (최대 2.0점)

```
if length < 200: 0.5점
elif length < 500: 1.0점
elif length < 1000: 1.5점
else: 2.0점
```

### 5. 실행 계획 복잡성 (최대 1.0점)

```
execution = join_depth_score + order_by_score + group_by_score + having_score
```

- **조인 깊이**: 0.5점 (join_count > 5 or subquery_depth > 2)
- **ORDER BY**: 0.2점
- **GROUP BY**: 0.2점
- **HAVING**: 0.2점

### 6. PostgreSQL 변환 난이도 (최대 3.0점)

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
max_possible_score = 2.5 + 3.0 + 2.0 + 2.0 + 1.0 + 3.0 = 13.5
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## PL/SQL 오브젝트 복잡도 계산

**중요**: PostgreSQL은 PL/pgSQL을 통해 Oracle PL/SQL의 약 70-75%를 커버할 수 있습니다.

### PL/pgSQL 커버리지

#### ✅ 높은 호환성 (90%+ 커버)
- 기본 프로그래밍 구조 (변수, IF, LOOP, CASE 등)
- 커서 (명시적 커서, REF CURSOR 완벽 지원)
- 함수/프로시저 (IN/OUT/INOUT 파라미터, 오버로딩)
- 트리거 (BEFORE/AFTER, INSTEAD OF 포함)
- 동적 SQL (EXECUTE)
- 예외 처리 (EXCEPTION)

#### ⚠️ 중간 호환성 (50-80% 커버)
- **패키지**: 개념 없음 → 스키마로 그룹화 + 개별 함수/프로시저
- **패키지 변수**: 세션 변수(current_setting/set_config) 또는 임시 테이블로 대체
- **컬렉션**: ARRAY 타입 지원 (VARRAY 유사), Nested Table은 제한적
- **BULK 연산**: BULK COLLECT/FORALL 미지원 → 일반 루프로 대체
- **PIPELINED 함수**: RETURN NEXT/RETURN QUERY로 유사 구현

#### ❌ 낮은 호환성 (30% 이하)
- PRAGMA (AUTONOMOUS_TRANSACTION 제한적, 나머지 미지원)
- 객체 타입 (Object Type) - Composite Type으로 제한적 구현
- 외부 프로시저 (UTL_FILE, UTL_HTTP, UTL_MAIL 미지원)

### 기본 점수

| 오브젝트 타입 | 기본 점수 | PL/pgSQL 변환 가능성 |
|--------------|----------|-------------------|
| Package | 7.0 | 중간 (스키마로 재구성) |
| Procedure | 5.0 | 높음 (거의 직접 변환) |
| Function | 4.0 | 높음 (거의 직접 변환) |
| Trigger | 6.0 | 높음 (문법 차이만) |
| View | 2.0 | 높음 (SQL만 변환) |
| Materialized View | 4.0 | 높음 (PostgreSQL 지원) |

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
  - PostgreSQL은 패키지 개념 없음, 스키마로 재구성 필요
- **DB Link**: `min(1.5, dblink_count * 1.0)`
  - PostgreSQL은 dblink 확장으로 지원
- **동적 SQL**: `min(1.0, dynamic_sql_count * 0.5)`
  - EXECUTE IMMEDIATE → EXECUTE로 직접 변환
- **BULK 연산**: `min(1.0, bulk_operations_count * 0.4)` (성능 페널티 반영)
  - BULK COLLECT/FORALL 미지원
  - 대안: 순수 SQL, Chunked Batch, ARRAY_AGG/UNNEST
  - **성능 차이: 최적화 시 20-50%, 비최적화 시 200-400% 느림**
- **고급 기능**: `min(1.5, advanced_features_count * 0.5)`
  - PIPELINED 함수: RETURN NEXT/RETURN QUERY로 유사 구현
  - REF CURSOR: 완벽 지원
  - AUTONOMOUS TRANSACTION: 제한적 (dblink로 구현 가능)
  - PRAGMA: 대부분 미지원
  - OBJECT TYPE: Composite Type으로 제한적 구현

### 3. 비즈니스 로직 복잡도 (최대 2.0점)

- **트랜잭션 처리**: 0.5~0.8점
- **복잡한 계산**: `min(1.0, complex_calculations * 0.3)`
- **데이터 검증**: `min(0.5, validation_checks * 0.2)`

### 4. AI 변환 불가능 난이도 (최대 2.0점)

- **컨텍스트 의존성**: `min(1.0, context_features * 0.5)`
  - SYS_CONTEXT: PostgreSQL은 current_setting/set_config으로 대체
  - 세션 변수: current_setting/set_config 사용
  - 글로벌 임시 테이블: TEMPORARY TABLE로 대체
- **상태 관리**: 0.8점 (패키지 변수 사용 시)
  - 패키지 변수: 세션 변수 또는 임시 테이블로 대체
  - 세션 간 상태 공유는 제한적
- **외부 의존성**: `min(1.0, external_calls * 0.5)`
  - UTL_FILE: PostgreSQL 확장 또는 애플리케이션 레벨 처리
  - UTL_HTTP: http 확장 사용 가능
  - UTL_MAIL: 애플리케이션 레벨 처리
  - DBMS_SCHEDULER: pg_cron 확장으로 대체
- **커스텀 로직**: 0.5~1.0점

### 최종 PL/SQL 복잡도 점수

```python
total_score = base + code + oracle + business + ai_difficulty
max_possible_score = 10.0 + 3.0 + 3.0 + 2.0 + 2.0 = 20.0
normalized_score = min(10, total_score * 10 / max_possible_score)
final_score = round(normalized_score, 1)
```

## 복잡도 레벨 분류

### SQL 쿼리

| 점수 | 레벨 | PostgreSQL 변환 |
|------|------|----------------|
| 0-1 | 매우 간단 | 자동 변환 |
| 1-3 | 간단 | 함수 대체 |
| 3-5 | 중간 | 부분 재작성 |
| 5-7 | 복잡 | 상당한 재작성 |
| 7-9 | 매우 복잡 | 대부분 재작성 |
| 9-10 | 극도로 복잡 | 완전 재설계 |

### PL/SQL 오브젝트

| 점수 | 레벨 | PostgreSQL 변환 |
|------|------|----------------|
| 0-3 | 간단 | PL/pgSQL 자동 변환 |
| 3-5 | 중간 | PL/pgSQL + 수동 조정 |
| 5-7 | 복잡 | PL/pgSQL 재작성 (패키지 재구성) |
| 7-9 | 매우 복잡 | PL/pgSQL 재설계 (BULK, 패키지 변수 대체) |
| 9-10 | 극도로 복잡 | 애플리케이션 레벨 재구현 고려 |

**참고**: 
- 복잡도 5.0 이하: PL/pgSQL로 직접 변환 가능
- 복잡도 5.0-7.0: 패키지 재구성, BULK 연산 대체 필요
- 복잡도 7.0 이상: 패키지 변수, PRAGMA 등 고급 기능 사용 시 재설계 필요

## PostgreSQL 변환 가이드

### Oracle → PostgreSQL 주요 변환

| Oracle | PostgreSQL | 난이도 |
|--------|-----------|-------|
| ROWNUM | LIMIT/OFFSET | 낮음 |
| CONNECT BY | WITH RECURSIVE | 중간 |
| DECODE | CASE | 낮음 |
| NVL | COALESCE | 낮음 |
| SYSDATE | CURRENT_TIMESTAMP | 낮음 |
| MERGE | INSERT ON CONFLICT | 중간 |
| PIVOT | crosstab 또는 CASE | 중간 |
| (+) JOIN | LEFT/RIGHT JOIN | 낮음 |
| SEQUENCE.NEXTVAL | nextval('seq') | 낮음 |
| Package | Schema + Functions | 높음 |
| BULK COLLECT | 순수 SQL/Chunked Batch | 중간 | **row-by-row LOOP 사용 금지** (200-400% 느림) |
| FORALL | 순수 SQL/Chunked Batch | 중간 | 순수 SQL 권장 (20-50% 느림) |
| PIPELINED | RETURN NEXT/QUERY | 중간 |
| 패키지 변수 | 세션 변수/임시 테이블 | 높음 |
| UTL_FILE | 확장 또는 애플리케이션 | 높음 |
| UTL_HTTP | http 확장 | 중간 |
| DBMS_SCHEDULER | pg_cron 확장 | 중간 |
| SYS_CONTEXT | current_setting/set_config | 낮음 |
| PRAGMA | 제한적 또는 미지원 | 높음 |
| Object Type | Composite Type | 중간 |
| LISTAGG | STRING_AGG | 낮음 |
| MEDIAN | PERCENTILE_CONT(0.5) | 낮음 |
| XMLAGG | XMLAGG | 낮음 |
| WM_CONCAT | STRING_AGG | 낮음 |
| DBMS_CRYPTO | 애플리케이션 암호화 | 높음 |

### 데이터 타입 변환

| Oracle | PostgreSQL | 주의사항 |
|--------|-----------|---------|
| NUMBER | NUMERIC/INTEGER | 정밀도 확인 필요 |
| NUMBER(p,s) | NUMERIC(p,s) | 직접 매핑 |
| VARCHAR2 | VARCHAR | 빈 문자열 처리 동일 |
| DATE | TIMESTAMP | Oracle DATE는 시간 포함 |
| CLOB | TEXT | 크기 제한 없음 |
| BLOB | BYTEA | 바이너리 데이터 |
| RAW | BYTEA | 바이너리 데이터 |
| LONG | TEXT | 레거시 타입 |

### PostgreSQL 확장 활용

| 확장 | 용도 | Oracle 대체 |
|------|------|------------|
| pg_cron | 스케줄러 | DBMS_SCHEDULER |
| dblink | 원격 DB 연결 | DB Link |
| http | HTTP 호출 | UTL_HTTP |
| tablefunc | crosstab | PIVOT |
| pg_trgm | 유사 문자열 검색 | - |
| pgcrypto | 암호화 | DBMS_CRYPTO (일부) |

## 애플리케이션 레벨 이관 가이드

### ❌ 반드시 애플리케이션 레벨로 이관

| 기능 | 이유 | 애플리케이션 대안 |
|------|------|-----------------|
| **UTL_FILE** | PostgreSQL 미지원, 보안 이슈 | 파일 I/O 서비스 |
| **UTL_MAIL/UTL_SMTP** | PostgreSQL 미지원 | 이메일 서비스 (JavaMail, SendGrid) |
| **외부 API 호출** | DB에서 처리 부적합 | REST Client, HTTP 서비스 |
| **복잡한 비즈니스 로직** | 유지보수, 테스트 어려움 | 서비스 레이어 |
| **세션 간 상태 공유** | PostgreSQL 제한적 | Redis, 애플리케이션 캐시 |
| **대량 배치 처리 (BULK)** | 성능 차이 큼 (200-400%) | Spring Batch, 배치 프레임워크 |
| **복잡한 트랜잭션 관리** | AUTONOMOUS_TRANSACTION 제한 | 트랜잭션 관리 서비스 |
| **암호화/복호화** | DBMS_CRYPTO 미지원 | 암호화 라이브러리 (Jasypt, Bouncy Castle) |
| **DBMS_JOB (복잡한 경우)** | pg_cron 제한적 | Quartz, Spring Scheduler |

### ⚠️ 권장: 애플리케이션 레벨로 이관

| 기능 | 이유 | PL/pgSQL 대안 | 애플리케이션 대안 |
|------|------|--------------|-----------------|
| **패키지 변수 (상태 관리)** | 세션 변수 제한적 | current_setting | 애플리케이션 캐시/세션 |
| **PRAGMA AUTONOMOUS_TRANSACTION** | dblink 복잡 | dblink | 별도 트랜잭션 서비스 |
| **Object Type (복잡한 경우)** | Composite Type 제한적 | Composite Type | DTO/Entity |
| **PIPELINED 함수 (대량)** | RETURN NEXT 성능 제한 | RETURN NEXT | 스트리밍 서비스 |
| **동적 SQL (복잡한 경우)** | 보안, 유지보수 | EXECUTE | 쿼리 빌더 (QueryDSL, JOOQ) |
| **복잡한 예외 처리** | 문법 차이 | EXCEPTION | 애플리케이션 예외 처리 |

### ✅ PL/pgSQL로 유지 가능

| 기능 | 변환 난이도 | 비고 |
|------|-----------|------|
| 단순 CRUD 프로시저 | 낮음 | 직접 변환 |
| 데이터 검증 트리거 | 낮음 | 문법 변환만 |
| 단순 계산 함수 | 낮음 | 직접 변환 |
| 커서 처리 | 낮음 | REF CURSOR 포함 지원 |
| 동적 SQL (단순) | 낮음 | EXECUTE 지원 |
| 예외 처리 (단순) | 낮음 | EXCEPTION 지원 |
| Materialized View | 낮음 | PostgreSQL 완벽 지원 |
| 시퀀스 | 낮음 | nextval/currval 지원 |
| 뷰 | 낮음 | SQL만 변환 |

### 이관 결정 기준

```
복잡도 < 5.0  → PL/pgSQL 유지
복잡도 5.0-7.0 → 기능별 판단 (BULK, 패키지 변수 → 애플리케이션)
복잡도 > 7.0  → 애플리케이션 레벨 이관 권장
```

| 판단 기준 | PL/pgSQL 유지 | 애플리케이션 이관 |
|----------|--------------|-----------------|
| BULK 연산 | 없음 또는 소량 | 대량 (1만 건 이상) |
| 패키지 변수 | 미사용 | 상태 관리 필요 |
| 외부 호출 | 없음 | UTL_*, API 호출 |
| 트랜잭션 | 단순 | AUTONOMOUS 필요 |
| 비즈니스 로직 | 단순 계산/검증 | 복잡한 업무 규칙 |
| 테스트 용이성 | 단순 | 복잡 (단위 테스트 필요) |

## 참고 사항

- **PostgreSQL 16 이상 기준**으로 작성되었습니다.
- PostgreSQL은 복잡한 쿼리 처리에 강하므로 구조적 복잡성 가중치가 낮습니다.
- **PL/pgSQL은 Oracle PL/SQL의 약 70-75%를 커버**하므로 대부분의 비즈니스 로직을 변환 가능합니다.
- 패키지는 스키마로 재구성하고, 패키지 변수는 세션 변수나 임시 테이블로 대체해야 합니다.
- **BULK 연산 성능 주의**: 
  - 순수 SQL 또는 Chunked Batch 사용 시 Oracle 대비 20-50% 느림
  - row-by-row LOOP 사용 시 200-400% 느림 (반드시 회피)
- PostgreSQL은 대부분의 Oracle 분석 함수를 지원합니다.
- CONNECT BY는 WITH RECURSIVE로 변환 가능하나 성능 튜닝이 필요할 수 있습니다.
- Materialized View는 PostgreSQL이 완벽 지원합니다.
- REF CURSOR는 PostgreSQL이 완벽 지원합니다.
- **외부 프로시저 호출(UTL_*)은 애플리케이션 레벨 처리 권장**합니다.
- **PostgreSQL 16 신규 기능 활용**: 병렬 쿼리 개선, 증분 정렬, 논리적 복제 개선
- **복잡도 7.0 이상은 애플리케이션 레벨 이관을 적극 검토**하세요.
