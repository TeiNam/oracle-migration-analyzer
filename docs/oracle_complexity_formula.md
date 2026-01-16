# Oracle 마이그레이션 복잡도 및 전략 가이드

이 문서는 Oracle 데이터베이스 마이그레이션의 복잡도 계산, 난이도 평가, 전략 선택을 위한 종합 가이드입니다.

## 목차

1. [복잡도 점수 개요](#복잡도-점수-개요)
2. [타겟 데이터베이스 특성 비교](#타겟-데이터베이스-특성-비교)
3. [SQL 쿼리 복잡도 계산](#sql-쿼리-복잡도-계산)
4. [PL/SQL 오브젝트 복잡도 계산](#plsql-오브젝트-복잡도-계산)
5. [복잡도 레벨 분류](#복잡도-레벨-분류)
6. [PL/SQL 마이그레이션 난이도 평가](#plsql-마이그레이션-난이도-평가)
7. [Replatform vs Refactor 전략 선택](#replatform-vs-refactor-전략-선택)
8. [의사결정 가이드](#의사결정-가이드)

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

---

## PL/SQL 마이그레이션 난이도 평가

### 개요

PL/SQL 코드 라인 수는 마이그레이션 난이도와 소요 기간을 결정하는 핵심 지표입니다. 복잡도 점수와 함께 코드 라인 수를 평가하여 프로젝트 규모를 산정합니다.

### 난이도 단계별 기준

#### 낮음 (Low): ~20,000 줄

**특징:**
- 1~2명이 전체 코드 파악 가능
- 비교적 단순한 비즈니스 로직
- 제한적인 외부 시스템 연동

**예상 기간:** 3~6개월

**팀 구성:**
- DBA: 1명
- 개발자: 1~2명
- QA: 1명 (파트타임 가능)

**권장 접근:**
- 단일 팀으로 진행 가능
- 순차적 마이그레이션
- 전체 코드 리뷰 및 리팩토링 가능

---

#### 중간 (Medium): 20,000~50,000 줄

**특징:**
- 소규모 팀(2~4명) 필요
- 중간 복잡도의 비즈니스 로직
- 여러 모듈로 구성된 시스템

**예상 기간:** 6~12개월

**팀 구성:**
- DBA: 1~2명
- 개발자: 2~3명
- QA: 1~2명
- 프로젝트 매니저: 1명 (파트타임 가능)

**권장 접근:**
- 모듈별 병렬 작업
- 단계적 테스트 및 검증
- 코드 리뷰 프로세스 필수

---

#### 높음 (High): 50,000~100,000 줄

**특징:**
- 중규모 팀(4~8명) 필요
- 복잡한 비즈니스 로직 및 의존성
- 다수의 외부 시스템 연동

**예상 기간:** 12~18개월

**팀 구성:**
- DBA: 2~3명
- 개발자: 4~6명
- QA: 2~3명
- 아키텍트: 1명
- 프로젝트 매니저: 1명

**권장 접근:**
- 단계적 마이그레이션 전략 필수
- 모듈별 우선순위 설정
- 하이브리드 운영 기간 고려
- 자동화 도구 활용 필수

---

#### 매우 높음 (Very High): 100,000 줄 이상

**특징:**
- 대규모 팀 및 전문 컨설팅 필요
- 매우 복잡한 엔터프라이즈 시스템
- 광범위한 외부 시스템 연동
- 미션 크리티컬 시스템

**예상 기간:** 18개월 이상

**팀 구성:**
- DBA: 3~5명
- 개발자: 8~12명
- QA: 3~5명
- 아키텍트: 2~3명
- 프로젝트 매니저: 1~2명
- 외부 컨설턴트: 필요 시

**권장 접근:**
- 전사적 프로젝트로 관리
- 단계별 릴리스 계획 수립
- 장기 하이브리드 운영 전략
- 전문 컨설팅 및 AWS 지원 활용
- 자동화 및 도구 투자 필수

---

### 추가 고려사항

코드 라인 수 외에도 다음 요소들을 함께 평가하여 난이도를 조정해야 합니다:

#### 1. 외부 시스템 연동 개수

- **낮음 (0~3개)**: 난이도 유지
- **중간 (4~10개)**: 난이도 +1단계
- **높음 (11개 이상)**: 난이도 +2단계

**영향:**
- 각 연동 시스템별 호환성 검증 필요
- 인터페이스 변경 및 테스트 복잡도 증가
- 동시 마이그레이션 조율 필요

#### 2. 배치 작업 복잡도

- **단순 배치 (10개 미만)**: 난이도 유지
- **중간 배치 (10~30개)**: 난이도 +0.5단계
- **복잡 배치 (30개 이상)**: 난이도 +1단계

**영향:**
- 배치 스케줄링 재설계
- 대용량 데이터 처리 로직 최적화
- 실패 복구 메커니즘 재구현

#### 3. 데이터 볼륨

- **소규모 (1TB 미만)**: 난이도 유지
- **중규모 (1~10TB)**: 난이도 +0.5단계
- **대규모 (10TB 이상)**: 난이도 +1단계

**영향:**
- 데이터 마이그레이션 시간 증가
- 다운타임 최소화 전략 필요
- 증분 마이그레이션 및 검증 복잡도 증가

#### 4. 실시간 처리 요구사항

- **배치 중심**: 난이도 유지
- **준실시간 (초 단위)**: 난이도 +0.5단계
- **실시간 (밀리초 단위)**: 난이도 +1단계

**영향:**
- 성능 최적화 필수
- 무중단 마이그레이션 전략 필요
- 광범위한 성능 테스트 필요

#### 5. 비즈니스 크리티컬 정도

- **일반 시스템**: 난이도 유지
- **중요 시스템**: 난이도 +0.5단계
- **미션 크리티컬**: 난이도 +1단계

**영향:**
- 철저한 테스트 및 검증 필요
- 롤백 계획 및 비상 대응 체계 필수
- 단계적 전환 및 모니터링 강화

---

### 난이도 조정 예시

#### 예시 1: 기본 중간 난이도 시스템

- **PL/SQL 코드**: 30,000줄 → 중간
- **외부 연동**: 5개 → +1단계
- **배치 작업**: 15개 → +0.5단계
- **데이터 볼륨**: 3TB → +0.5단계
- **실시간 처리**: 준실시간 → +0.5단계
- **비즈니스 크리티컬**: 중요 → +0.5단계

**최종 난이도**: 중간 + 3단계 = **매우 높음**  
**예상 기간**: 12~18개월 → 18~24개월

#### 예시 2: 기본 높음 난이도 시스템

- **PL/SQL 코드**: 80,000줄 → 높음
- **외부 연동**: 2개 → 유지
- **배치 작업**: 8개 → 유지
- **데이터 볼륨**: 500GB → 유지
- **실시간 처리**: 배치 중심 → 유지
- **비즈니스 크리티컬**: 일반 → 유지

**최종 난이도**: 높음 (조정 없음)  
**예상 기간**: 12~18개월

---

## Replatform vs Refactor 전략 선택

### 개요

대량의 PL/SQL 코드를 마이그레이션할 때, Refactor(수동 변환)와 Replatform(자동화 도구 활용) 중 어떤 전략을 선택할지는 비용, 리스크, 유지보수성을 종합적으로 고려해야 합니다.

### 전략 비교

#### Refactor (수동 변환)

**장점:**
- 코드 품질 개선 기회
- 비즈니스 로직 최적화 가능
- 레거시 코드 정리

**단점:**
- 높은 인건비
- 긴 프로젝트 기간
- 휴먼 에러 가능성
- 코드 품질 편차

#### Replatform (자동화 도구 활용)

**장점:**
- 빠른 마이그레이션
- 일관된 변환 규칙
- 낮은 휴먼 에러
- 예측 가능한 결과

**단점:**
- 초기 도구 투자 비용
- 레거시 코드 그대로 이관
- 일부 수동 수정 필요

---

### 5만 줄 기준: Replatform 권장

#### 비용 효율성 분석

**Refactor 비용 (5만 줄 기준)**

작업 시간 계산:
- **단순 코드 (복잡도 < 5.0)**: 15~20분/줄
- **중간 코드 (복잡도 5.0~7.0)**: 20~30분/줄
- **복잡 코드 (복잡도 > 7.0)**: 30~60분/줄

예시: 5만 줄, 평균 복잡도 5.0
- 작업 시간: 50,000줄 × 20분 = 16,667시간
- 개발자 3명 투입 시: 약 33주 (8개월)
- 인건비 (시간당 $100 기준): $1,666,700

**Replatform 비용 (5만 줄 기준)**

작업 시간 계산:
- 자동 변환: 50,000줄 × 1분 = 833시간
- 검증 및 수정 (30% 수동 작업): 5,000시간
- 총 작업 시간: 약 5,833시간

예시: 5만 줄, 평균 복잡도 5.0
- 개발자 3명 투입 시: 약 12주 (3개월)
- 도구 비용: $50,000~$100,000
- 인건비 (시간당 $100 기준): $583,300
- 총 비용: $633,300~$683,300

**비용 절감:**
- 절감액: $983,400~$1,033,400 (약 60% 절감)
- 기간 단축: 5개월 단축

---

### 복잡도별 자동 변환 성공률

#### 낮은 복잡도 (< 5.0)

**자동 변환 성공률: 80~90%**

- 단순 CRUD 로직
- 표준 SQL 문법
- 기본 PL/SQL 구조

**수동 작업 필요:**
- 10~20%만 수동 수정
- 주로 비즈니스 로직 검증

#### 중간 복잡도 (5.0~7.0)

**자동 변환 성공률: 60~75%**

- 중간 복잡도 비즈니스 로직
- 일부 Oracle 전용 함수
- 중첩된 쿼리

**수동 작업 필요:**
- 25~40% 수동 수정
- Oracle 전용 기능 대체
- 성능 최적화

#### 높은 복잡도 (> 7.0)

**자동 변환 성공률: 30~50%**

- 복잡한 비즈니스 로직
- 다수의 Oracle 전용 기능
- 동적 SQL

**수동 작업 필요:**
- 50~70% 수동 수정
- 대부분 재작성 필요
- Refactor 고려

---

### 리스크 관리

#### Refactor의 리스크

1. **휴먼 에러**
   - 대량 수동 변환 시 실수 가능성 높음
   - 코드 리뷰 부담 증가
   - 테스트 커버리지 확보 어려움

2. **코드 품질 편차**
   - 개발자별 코딩 스타일 차이
   - 일관성 없는 패턴 적용
   - 유지보수 어려움

3. **프로젝트 지연**
   - 예상보다 긴 작업 시간
   - 리소스 부족
   - 범위 확대 (Scope Creep)

#### Replatform의 리스크 완화

1. **일관된 변환**
   - 표준화된 변환 규칙
   - 자동화된 코드 리뷰
   - 예측 가능한 결과

2. **빠른 검증**
   - 자동화된 테스트
   - 빠른 피드백 루프
   - 조기 이슈 발견

3. **예측 가능성**
   - 명확한 타임라인
   - 정확한 비용 산정
   - 리스크 최소화

---

### 유지보수성

#### Refactor 후 유지보수

**장점:**
- 최신 코딩 표준 적용
- 불필요한 코드 제거
- 문서화 개선

**단점:**
- 개발자별 품질 편차
- 일관성 없는 패턴
- 학습 곡선

#### Replatform 후 유지보수

**장점:**
- 일관된 코드 패턴
- 표준화된 구조
- 예측 가능한 동작

**단점:**
- 레거시 패턴 유지
- 기술 부채 이관
- 추후 리팩토링 필요

---

### 실제 사례

#### 사례 1: 금융사 (8만 줄, 복잡도 5.2)

**선택 전략:** Replatform

**결과:**
- 기간: 4개월 (예상 12개월)
- 비용: $850,000 (예상 $2,100,000)
- 자동 변환 성공률: 72%
- 수동 수정: 28%

**교훈:**
- 자동화 도구 투자 가치 입증
- 빠른 마이그레이션으로 비즈니스 연속성 확보

#### 사례 2: 제조사 (3만 줄, 복잡도 4.5)

**선택 전략:** Refactor

**결과:**
- 기간: 6개월
- 비용: $900,000
- 코드 품질 대폭 개선
- 기술 부채 50% 감소

**교훈:**
- 소규모 프로젝트는 Refactor로 품질 개선
- 장기적 유지보수 비용 절감

---

## 의사결정 가이드

### 난이도별 전략 선택

| 최종 난이도 | 코드 라인 수 | 권장 전략 | 비고 |
|------------|-------------|----------|------|
| 낮음 | < 20,000 | Refactor (MySQL/PostgreSQL) | 비용 효율적, 빠른 전환 |
| 중간 | 20,000~50,000 | Refactor (PostgreSQL) | PL/SQL 호환성 활용 |
| 높음 | 50,000~100,000 | Replatform 우선 고려 | 비용/시간 절감 |
| 매우 높음 | 100,000+ | Replatform 강력 권장 | 변환 리스크 최소화 |

### Replatform 권장 조건

다음 조건을 **모두** 만족하는 경우:

1. **PL/SQL 코드 50,000줄 이상**
2. **평균 복잡도 < 7.0** (자동 변환 가능)
3. **빠른 마이그레이션 필요** (6개월 이내)
4. **비용 절감 우선**

**예상 효과:**
- 비용 50~60% 절감
- 기간 50~70% 단축
- 리스크 30~40% 감소

### Refactor 권장 조건

다음 조건 중 **하나 이상** 해당하는 경우:

1. **PL/SQL 코드 50,000줄 미만**
2. **평균 복잡도 < 5.0** (단순 로직)
3. **코드 품질 개선 필요**
4. **충분한 시간 확보** (12개월 이상)

**예상 효과:**
- 코드 품질 향상
- 기술 부채 해소
- 장기적 유지보수 개선

### Replatform 심각 고려 시점

다음 조건 중 **2개 이상** 해당 시:

1. PL/SQL 코드 100,000줄 이상 + 평균 복잡도 7.0 이상
2. 외부 시스템 연동 15개 이상
3. 미션 크리티컬 시스템 + 실시간 처리 요구
4. 데이터 볼륨 20TB 이상
5. 마이그레이션 예상 기간 24개월 이상

### 하이브리드 접근 (5만~10만 줄)

다음 전략 고려:

1. **단순 코드 (70%)**: Replatform (자동 변환)
2. **복잡 코드 (30%)**: Refactor (수동 변환)
3. **단계적 마이그레이션**: 모듈별 순차 진행

---

### 의사결정 체크리스트

- [ ] PL/SQL 코드 라인 수 확인
- [ ] 평균 복잡도 평가
- [ ] 외부 시스템 연동 개수 확인
- [ ] 데이터 볼륨 평가
- [ ] 프로젝트 기간 제약 확인
- [ ] 예산 제약 확인
- [ ] 자동화 도구 가용성 확인
- [ ] 팀 역량 평가
- [ ] 비즈니스 우선순위 확인

---


## 참고 사항

- 복잡도 점수는 변환 난이도를 나타내는 지표이며, 실제 변환 시간과 정확히 비례하지 않을 수 있습니다.
- 동일한 점수라도 쿼리 특성에 따라 변환 난이도가 다를 수 있습니다.
- 복잡도 점수는 변환 우선순위 결정과 리소스 할당에 활용하세요.
- 실제 마이그레이션 시 자동 변환 도구(AWS SCT, Amazon Q Developer, Bedrock)와 전문가 검토가 필요합니다.
- PL/SQL 오브젝트가 많은 경우 DB만 이관할 수 없으며, 애플리케이션 레벨 재구현을 고려해야 합니다.
- AI 변환 도구는 복잡도 7.0 이상의 오브젝트 자동 변환이 어렵습니다.

## 관련 문서

- [Oracle to PostgreSQL 마이그레이션 가이드](migration_guide_aurora_pg16.md)
- [Oracle to MySQL 마이그레이션 가이드](complexity_mysql.md)
- [AI 도구를 활용한 마이그레이션](ai_assisted_migration.md)
