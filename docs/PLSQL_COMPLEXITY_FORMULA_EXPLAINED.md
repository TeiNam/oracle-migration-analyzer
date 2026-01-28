# PL/SQL 복잡도 계산 공식 쉽게 이해하기

> 작성일: 2026-01-28
> Oracle PL/SQL 오브젝트(Package, Procedure, Function, Trigger 등)가 PostgreSQL이나 MySQL로 변환하기 얼마나 어려운지를 0-10점으로 점수화하는 방법을 설명합니다.

## 📋 목차

1. [한눈에 보는 PL/SQL 복잡도 계산](#한눈에-보는-plsql-복잡도-계산)
2. [왜 타겟 DB마다 점수가 다른가?](#왜-타겟-db마다-점수가-다른가)
3. [6가지 평가 영역 상세 설명](#6가지-평가-영역-상세-설명)
4. [최종 점수 계산 방법](#최종-점수-계산-방법)
5. [복잡도 레벨과 권장사항](#복잡도-레벨과-권장사항)
6. [실제 예시로 이해하기](#실제-예시로-이해하기)

---

## 한눈에 보는 PL/SQL 복잡도 계산

### 핵심 공식

```
최종 점수 = (기본 점수 + 5가지 영역 점수 합계 + MySQL 페널티) × 10 ÷ 최대 가능 점수
```

### 점수 구성 요소

| 영역 | 무엇을 측정하나? | PostgreSQL 최대 | MySQL 최대 |
|------|-----------------|-----------------|------------|
| 1. 기본 점수 | 오브젝트 타입별 기본 난이도 | 4.0점 | 5.0점 |
| 2. 코드 복잡도 | 라인 수, 커서, 예외처리, 중첩 | 4.0점 | 4.0점 |
| 3. Oracle 특화 기능 | 패키지 호출, DB Link, BULK 등 | 5.0점 | 5.0점 |
| 4. 비즈니스 로직 | 트랜잭션, 계산, 검증 로직 | 3.0점 | 3.0점 |
| 5. 변환 난이도 | 외부 의존성 | 3.0점 | 3.0점 |
| 6. MySQL 제약 | 데이터 타입, 트리거 제약 등 | - | 1.5점 |
| 7. MySQL 이관 페널티 | 애플리케이션 이관 비용 | - | 2.0점 |
| **합계** | | **약 19.0점** | **약 23.5점** |

> 💡 **핵심 포인트**: MySQL은 PostgreSQL보다 최대 점수가 높습니다. MySQL은 Stored Procedure 사용을 권장하지 않아 애플리케이션 레벨로 이관해야 하므로 추가 페널티가 적용됩니다.

### 고복잡도 임계값

| 타겟 DB | 임계값 | 의미 |
|---------|--------|------|
| PostgreSQL | **5.0점** | 이 점수 이상이면 "복잡" 판정 |
| MySQL | **7.0점** | 이 점수 이상이면 "복잡" 판정 |

> 💡 임계값은 max_total_score 대비 약 37~39% 비율로 설정되어 있습니다.



---

## 왜 타겟 DB마다 점수가 다른가?

### PostgreSQL vs MySQL PL/SQL 지원 차이

```
┌─────────────────────────────────────────────────────────────────┐
│                    같은 Oracle PL/SQL이라도...                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Oracle PL/SQL ──┬──→ PostgreSQL: 복잡도 5.2점 (중간)           │
│                   │    → PL/pgSQL로 변환 (유사한 문법)            │
│                   │                                             │
│                   └──→ MySQL: 복잡도 7.8점 (복잡)                │
│                        → 애플리케이션 레벨로 이관 필요!            │
│                                                                 │
│   왜? MySQL은 복잡한 Stored Procedure를 권장하지 않음!            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 주요 차이점

| 특성 | PostgreSQL | MySQL |
|------|-----------|-------|
| 프로시저 언어 | PL/pgSQL (Oracle 유사) ✅ | SQL/PSM (제한적) ⚠️ |
| 패키지 지원 | 스키마로 대체 가능 ✅ | 미지원 ❌ |
| 커서 | 완벽 지원 ✅ | 제한적 지원 ⚠️ |
| 예외 처리 | EXCEPTION 블록 ✅ | HANDLER (다른 문법) ⚠️ |
| BULK 연산 | 유사 기능 지원 ✅ | 미지원 ❌ |
| 동적 SQL | EXECUTE 지원 ✅ | PREPARE/EXECUTE ⚠️ |
| 트리거 | 완벽 지원 ✅ | 제한적 (테이블당 1개) ⚠️ |
| 권장 사항 | DB 레벨 로직 OK ✅ | 애플리케이션 이관 권장 ⚠️ |

### 오브젝트 타입별 기본 점수 비교

| 오브젝트 타입 | PostgreSQL | MySQL | 차이 | 이유 |
|--------------|------------|-------|------|------|
| PACKAGE | 4.0점 | 5.0점 | +1.0 | MySQL 패키지 미지원 |
| PROCEDURE | 2.5점 | 3.5점 | +1.0 | 문법 차이 |
| FUNCTION | 2.0점 | 3.0점 | +1.0 | 문법 차이 |
| TRIGGER | 3.5점 | 4.5점 | +1.0 | MySQL 트리거 제약 |
| VIEW | 1.0점 | 1.0점 | 0 | 유사한 지원 |
| MATERIALIZED VIEW | 2.5점 | 3.5점 | +1.0 | MySQL 미지원 |

> 💡 **기본 점수의 의미**: 코드 내용과 관계없이 해당 오브젝트 타입을 변환하는 데 필요한 "최소 난이도"입니다. 실제 복잡도는 내부 분석으로 추가됩니다.



---

## 6가지 평가 영역 상세 설명

### 1️⃣ 기본 점수 (Base Score)

**측정 대상**: PL/SQL 오브젝트 타입에 따른 기본 변환 난이도

오브젝트 타입만으로도 변환 난이도가 결정됩니다. 예를 들어, Package는 MySQL에서 지원하지 않으므로 기본적으로 높은 점수를 받습니다.

#### PostgreSQL 기본 점수

| 오브젝트 타입 | 기본 점수 | 이유 |
|--------------|----------|------|
| PACKAGE | 4.0점 | 스키마로 분리 필요, 패키지 변수 처리 |
| TRIGGER | 3.5점 | 문법 차이, 이벤트 처리 방식 |
| PROCEDURE | 2.5점 | PL/pgSQL로 변환 필요 |
| MATERIALIZED VIEW | 2.5점 | 리프레시 로직 변환 |
| FUNCTION | 2.0점 | 반환 타입 처리 |
| VIEW | 1.0점 | 대부분 호환 |

#### MySQL 기본 점수

| 오브젝트 타입 | 기본 점수 | 이유 |
|--------------|----------|------|
| PACKAGE | 5.0점 | 완전 미지원, 분해 필요 |
| TRIGGER | 4.5점 | 테이블당 1개 제한, INSTEAD OF 미지원 |
| PROCEDURE | 3.5점 | 문법 차이, 기능 제한 |
| MATERIALIZED VIEW | 3.5점 | 미지원, 수동 구현 필요 |
| FUNCTION | 3.0점 | 결정적 함수 제약 |
| VIEW | 1.0점 | 대부분 호환 |



---

### 2️⃣ 코드 복잡도 (Code Complexity)

**측정 대상**: 코드의 구조적 복잡함

**최대 점수**: 4.0점 (PostgreSQL/MySQL 동일)

```
코드 복잡도 = 라인 수 점수 + 커서 점수 + 예외 처리 점수 + 중첩 깊이 점수
```

#### 2.1 코드 라인 수 점수

| 라인 수 | 점수 | 설명 |
|--------|------|------|
| 50줄 미만 | 0.3점 | 매우 간단한 로직 |
| 50-100줄 | 0.5점 | 간단한 로직 |
| 100-300줄 | 1.0점 | 일반적인 프로시저 |
| 300-500줄 | 1.5점 | 복잡한 로직 |
| 500-1000줄 | 2.0점 | 대규모 로직 |
| 1000-2000줄 | 2.5점 | 매우 복잡 |
| 2000-5000줄 | 3.0점 | 극도로 복잡 |
| 5000줄 이상 | 3.5점 | 최대 점수 |

**예시**:
```sql
-- 50줄 프로시저 → 0.5점
CREATE PROCEDURE simple_update AS
BEGIN
    UPDATE orders SET status = 'DONE' WHERE id = 1;
END;

-- 800줄 패키지 → 2.0점
CREATE PACKAGE BODY complex_pkg AS
    -- 수백 줄의 비즈니스 로직...
END;
```

#### 2.2 커서 점수

```
커서 점수 = min(2.0, 커서 개수 × 0.5)
```

| 커서 개수 | 점수 | 설명 |
|----------|------|------|
| 0개 | 0점 | 커서 미사용 |
| 1개 | 0.5점 | 단일 커서 |
| 2개 | 1.0점 | 복수 커서 |
| 3개 | 1.5점 | 다중 커서 |
| 4개 이상 | 2.0점 | 최대 점수 |

**감지되는 커서 유형**:
```sql
-- 명시적 커서 (CURSOR ... IS)
CURSOR emp_cursor IS SELECT * FROM employees;

-- 암시적 커서 (FOR ... IN)
FOR rec IN (SELECT * FROM orders) LOOP
    -- 처리 로직
END LOOP;

-- 커서 변수 루프
FOR rec IN emp_cursor LOOP
    -- 처리 로직
END LOOP;
```

#### 2.3 예외 처리 블록 점수

```
예외 처리 점수 = min(1.0, EXCEPTION 블록 개수 × 0.4)
```

| EXCEPTION 블록 | 점수 |
|---------------|------|
| 0개 | 0점 |
| 1개 | 0.4점 |
| 2개 | 0.8점 |
| 3개 이상 | 1.0점 |

**예시**:
```sql
BEGIN
    -- 메인 로직
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        -- 예외 처리 1
    WHEN OTHERS THEN
        -- 예외 처리 2
END;
-- EXCEPTION 블록 1개 → 0.2점
```

#### 2.4 중첩 깊이 점수

| 중첩 깊이 | 점수 | 설명 |
|----------|------|------|
| 0-2 | 0점 | 단순 구조 |
| 3-4 | 0.5점 | 일반적 |
| 5-6 | 1.0점 | 복잡 |
| 7 이상 | 1.5점 | 매우 복잡 |

**중첩을 증가시키는 키워드**: `BEGIN`, `IF`, `LOOP`, `WHILE`, `FOR`, `CASE`

**예시**:
```sql
BEGIN                           -- 깊이 1
    IF condition1 THEN          -- 깊이 2
        FOR rec IN cursor LOOP  -- 깊이 3
            IF condition2 THEN  -- 깊이 4
                BEGIN           -- 깊이 5
                    -- 로직
                END;
            END IF;
        END LOOP;
    END IF;
END;
-- 최대 중첩 깊이: 5 → 1.0점
```



---

### 3️⃣ Oracle 특화 기능 (Oracle-Specific Features)

**측정 대상**: Oracle에서만 사용 가능한 PL/SQL 기능

**최대 점수**: 5.0점 (PostgreSQL/MySQL 동일)

```
Oracle 특화 점수 = 패키지 호출 + DB Link + 동적 SQL + BULK 연산 + 고급 기능 + 타입 참조 + 사용자 정의 타입 + RETURNING INTO + 조건부 컴파일
```

#### 3.1 패키지 호출 점수

```
패키지 호출 점수 = min(2.0, 패키지 호출 개수 × 0.5)
```

| 패키지 호출 | 점수 |
|------------|------|
| 0개 | 0점 |
| 1개 | 0.5점 |
| 2개 | 1.0점 |
| 3개 | 1.5점 |
| 4개 이상 | 2.0점 |

**감지되는 패턴**:
```sql
-- 사용자 패키지 호출
my_package.my_procedure(param1);
util_pkg.calculate_tax(amount);

-- 시스템 패키지 호출
DBMS_OUTPUT.PUT_LINE('Hello');
UTL_FILE.FOPEN('/path', 'file.txt', 'W');
```

#### 3.2 DB Link 점수

```
DB Link 점수 = min(1.5, DB Link 개수 × 1.0)
```

| DB Link 사용 | 점수 | 설명 |
|-------------|------|------|
| 0개 | 0점 | 로컬 DB만 사용 |
| 1개 | 1.0점 | 단일 원격 DB |
| 2개 이상 | 1.5점 | 다중 원격 DB |

**감지되는 패턴**:
```sql
-- 원격 테이블 접근
SELECT * FROM employees@remote_db;
INSERT INTO orders@warehouse_link VALUES (...);
```

> ⚠️ **주의**: DB Link는 PostgreSQL의 `dblink` 확장이나 `postgres_fdw`로 대체해야 하며, MySQL에서는 `FEDERATED` 엔진이나 애플리케이션 레벨 처리가 필요합니다.

#### 3.3 동적 SQL 점수

```
동적 SQL 점수 = min(2.0, EXECUTE IMMEDIATE 개수 × 0.8)
동적 DDL 추가 점수 = min(1.0, 동적 DDL 개수 × 0.5)
```

| 동적 SQL | 점수 |
|---------|------|
| 0개 | 0점 |
| 1개 | 0.8점 |
| 2개 | 1.6점 |
| 3개 이상 | 2.0점 |

**감지되는 패턴**:
```sql
-- EXECUTE IMMEDIATE
EXECUTE IMMEDIATE 'CREATE TABLE ' || table_name || ' (id NUMBER)';
EXECUTE IMMEDIATE sql_stmt INTO result;
EXECUTE IMMEDIATE 'UPDATE ' || tbl || ' SET status = :1' USING new_status;
```

#### 3.4 BULK 연산 점수

**PostgreSQL**:
```
BULK 점수 = min(1.0, BULK 연산 개수 × 0.4)
```

**MySQL**:
```
BULK 점수 = min(0.8, BULK 연산 개수 × 0.3)
```

| BULK 연산 | PostgreSQL | MySQL |
|----------|-----------|-------|
| 0개 | 0점 | 0점 |
| 1개 | 0.4점 | 0.3점 |
| 2개 | 0.8점 | 0.6점 |
| 3개 이상 | 1.0점 | 0.8점 |

**감지되는 패턴**:
```sql
-- BULK COLLECT INTO
SELECT employee_id BULK COLLECT INTO emp_ids FROM employees;

-- FORALL
FORALL i IN 1..emp_ids.COUNT
    UPDATE employees SET salary = salary * 1.1 WHERE id = emp_ids(i);
```

> 💡 **변환 방법**: PostgreSQL에서는 배열과 `unnest()` 함수로 유사하게 구현 가능. MySQL에서는 루프로 대체하거나 애플리케이션 레벨에서 배치 처리.

#### 3.5 고급 기능 점수

```
고급 기능 점수 = min(1.5, 감지된 고급 기능 개수 × 0.5)
```

| 고급 기능 | 점수 |
|----------|------|
| 0개 | 0점 |
| 1개 | 0.5점 |
| 2개 | 1.0점 |
| 3개 이상 | 1.5점 |

**감지되는 고급 기능**:

| 기능 | 설명 | 변환 난이도 |
|------|------|------------|
| `PIPELINED` | 파이프라인 함수 | 🔴 매우 어려움 |
| `REF CURSOR` | 커서 변수 | 🟠 어려움 |
| `AUTONOMOUS_TRANSACTION` | 자율 트랜잭션 | 🔴 매우 어려움 |
| `PRAGMA` | 컴파일러 지시어 | 🟠 어려움 |
| `OBJECT TYPE` | 객체 타입 | 🔴 매우 어려움 |
| `VARRAY` | 가변 배열 | 🟠 어려움 |
| `NESTED TABLE` | 중첩 테이블 | 🔴 매우 어려움 |

**예시**:
```sql
-- PIPELINED 함수
CREATE FUNCTION get_employees RETURN emp_tab PIPELINED AS
BEGIN
    FOR rec IN (SELECT * FROM employees) LOOP
        PIPE ROW(rec);
    END LOOP;
    RETURN;
END;

-- AUTONOMOUS_TRANSACTION
CREATE PROCEDURE log_error(p_msg VARCHAR2) AS
    PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
    INSERT INTO error_log VALUES (SYSDATE, p_msg);
    COMMIT;  -- 메인 트랜잭션과 독립적으로 커밋
END;
```



---

### 4️⃣ 비즈니스 로직 복잡도 (Business Logic Complexity)

**측정 대상**: 비즈니스 로직의 복잡함

**최대 점수**: 3.0점 (PostgreSQL/MySQL 동일)

```
비즈니스 로직 점수 = 트랜잭션 처리 + 복잡한 계산 + 데이터 검증 + 컨텍스트 의존성 + 패키지 변수 + RAISE_APPLICATION_ERROR + Oracle 예외 + SQLCODE/SQLERRM
```

#### 4.1 트랜잭션 처리 점수

| 트랜잭션 제어 | 점수 | 설명 |
|-------------|------|------|
| 없음 | 0점 | 트랜잭션 제어 없음 |
| COMMIT/ROLLBACK | 0.5점 | 기본 트랜잭션 |
| SAVEPOINT | 0.8점 | 부분 롤백 사용 |

**감지되는 패턴**:
```sql
-- 기본 트랜잭션 (0.5점)
BEGIN
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
END;

-- SAVEPOINT 사용 (0.8점)
BEGIN
    SAVEPOINT before_update;
    UPDATE orders SET status = 'PROCESSING';
    
    IF some_condition THEN
        ROLLBACK TO SAVEPOINT before_update;
    END IF;
    COMMIT;
END;
```

#### 4.2 복잡한 계산 점수

```
복잡한 계산 점수 = min(1.0, (산술 연산자 개수 ÷ 10) × 0.3)
```

산술 연산자(`+`, `-`, `*`, `/`) 10개당 0.3점

| 산술 연산자 | 점수 |
|------------|------|
| 0-9개 | 0점 |
| 10-19개 | 0.3점 |
| 20-29개 | 0.6점 |
| 30-39개 | 0.9점 |
| 40개 이상 | 1.0점 |

#### 4.3 데이터 검증 점수

```
데이터 검증 점수 = min(0.5, IF 문 개수 × 0.2)
```

| IF 문 개수 | 점수 |
|-----------|------|
| 0개 | 0점 |
| 1개 | 0.2점 |
| 2개 | 0.4점 |
| 3개 이상 | 0.5점 |

#### 4.4 컨텍스트 의존성 점수

```
컨텍스트 의존성 점수 = min(1.0, 감지된 컨텍스트 기능 개수 × 0.5)
```

**감지되는 컨텍스트 기능**:

| 기능 | 설명 | 변환 난이도 |
|------|------|------------|
| `SYS_CONTEXT` | 시스템 컨텍스트 조회 | 🔴 매우 어려움 |
| `USERENV` | 사용자 환경 정보 | 🟠 어려움 |
| `GLOBAL_TEMPORARY_TABLE` | 세션별 임시 테이블 | 🟠 어려움 |
| `DBMS_SESSION` | 세션 관리 | 🔴 매우 어려움 |
| `DBMS_APPLICATION_INFO` | 애플리케이션 정보 | 🟠 어려움 |

**예시**:
```sql
-- SYS_CONTEXT 사용
v_user := SYS_CONTEXT('USERENV', 'SESSION_USER');
v_ip := SYS_CONTEXT('USERENV', 'IP_ADDRESS');

-- 글로벌 임시 테이블
CREATE GLOBAL TEMPORARY TABLE temp_results (
    id NUMBER,
    value VARCHAR2(100)
) ON COMMIT DELETE ROWS;
```

#### 4.5 패키지 변수 점수

| 패키지 변수 | 점수 |
|------------|------|
| 미사용 | 0점 |
| 사용 | 0.8점 |

**감지되는 패턴**:
```sql
CREATE PACKAGE BODY my_pkg AS
    -- 패키지 레벨 변수 (전역 상태)
    g_counter NUMBER := 0;
    g_last_error VARCHAR2(200);
    
    PROCEDURE increment IS
    BEGIN
        g_counter := g_counter + 1;  -- 패키지 변수 사용
    END;
END;
```

> ⚠️ **주의**: 패키지 변수는 세션 상태를 유지하므로 변환 시 애플리케이션 레벨 상태 관리나 Redis 같은 외부 저장소가 필요할 수 있습니다.



---

### 5️⃣ 변환 난이도 (Conversion Difficulty)

**측정 대상**: 외부 시스템 의존성으로 인한 변환 난이도

**최대 점수**: 3.0점 (PostgreSQL/MySQL 동일)

```
변환 난이도 점수 = 외부 의존성 패키지별 차등 점수 합계 (최대 3.0점)
```

#### 외부 의존성 패키지별 점수

| 패키지 | 점수 | 설명 | 변환 난이도 |
|--------|------|------|------------|
| `UTL_FILE` | 1.0점 | 파일 I/O | 🔴 매우 어려움 |
| `UTL_HTTP` | 1.0점 | HTTP 통신 | 🔴 매우 어려움 |
| `UTL_MAIL` | 0.8점 | 이메일 발송 | 🔴 매우 어려움 |
| `UTL_SMTP` | 0.8점 | SMTP 통신 | 🔴 매우 어려움 |
| `DBMS_SCHEDULER` | 0.8점 | 작업 스케줄링 | 🟠 어려움 |
| `DBMS_JOB` | 0.6점 | 작업 스케줄링 (구버전) | 🟠 어려움 |
| `DBMS_LOB` | 0.5점 | LOB 처리 | 🟡 중간 |
| `DBMS_OUTPUT` | 0.2점 | 디버그 출력 | 🟢 쉬움 |
| `DBMS_CRYPTO` | 0.8점 | 암호화 | 🟠 어려움 |
| `DBMS_SQL` | 0.6점 | 동적 SQL | 🟠 어려움 |
| 기타 | 0.5점 | 기본값 | - |

**예시**:
```sql
-- UTL_FILE 사용 (파일 I/O)
DECLARE
    v_file UTL_FILE.FILE_TYPE;
BEGIN
    v_file := UTL_FILE.FOPEN('/export', 'data.csv', 'W');
    UTL_FILE.PUT_LINE(v_file, 'id,name,value');
    UTL_FILE.FCLOSE(v_file);
END;

-- UTL_HTTP 사용 (HTTP 통신)
DECLARE
    v_response UTL_HTTP.RESP;
BEGIN
    v_response := UTL_HTTP.GET_RESPONSE(
        UTL_HTTP.BEGIN_REQUEST('https://api.example.com/data')
    );
END;
```

> 💡 **변환 방법**: 
> - `UTL_FILE` → 애플리케이션 레벨 파일 처리 또는 PostgreSQL의 `COPY` 명령
> - `UTL_HTTP` → 애플리케이션 레벨 HTTP 클라이언트 (Python requests, Java HttpClient 등)
> - `DBMS_SCHEDULER` → cron, pg_cron, 또는 외부 스케줄러



---

### 6️⃣ MySQL 특화 제약 (MySQL Only)

**측정 대상**: MySQL 특유의 제약사항으로 인한 추가 난이도

**최대 점수**: 1.5점 (MySQL만 적용)

```
MySQL 제약 점수 = 데이터 타입 이슈 + 트리거 제약 + 뷰 제약
```

#### 6.1 데이터 타입 변환 이슈

| 데이터 타입 | 추가 점수 | 이슈 |
|------------|----------|------|
| `NUMBER` | +0.5점 | 정밀도 차이 (DECIMAL vs DOUBLE) |
| `CLOB/BLOB` | +0.3점 | TEXT/LONGBLOB 변환 |
| `VARCHAR2` | +0.3점 | 빈 문자열 = NULL 처리 차이 |

**예시**:
```sql
-- NUMBER 정밀도 이슈
v_amount NUMBER(38,10);  -- Oracle: 38자리 정밀도
-- MySQL DECIMAL(65,30)으로 변환 필요

-- VARCHAR2 빈 문자열 이슈
IF v_name = '' THEN  -- Oracle: '' = NULL
    -- MySQL에서는 '' ≠ NULL
END IF;
```

#### 6.2 트리거 제약

| 트리거 유형 | 추가 점수 | MySQL 제약 |
|------------|----------|-----------|
| `INSTEAD OF` | +0.5점 | MySQL 미지원 |
| `COMPOUND` | +0.5점 | MySQL 미지원 |

**예시**:
```sql
-- INSTEAD OF 트리거 (MySQL 미지원)
CREATE TRIGGER trg_view_insert
INSTEAD OF INSERT ON my_view
FOR EACH ROW
BEGIN
    INSERT INTO base_table VALUES (:NEW.id, :NEW.name);
END;
```

#### 6.3 뷰 제약

| 뷰 유형 | 추가 점수 | MySQL 제약 |
|--------|----------|-----------|
| 업데이트 가능 뷰 | +0.3점 | 제한적 지원 |
| MATERIALIZED VIEW | +0.5점 | 미지원 |



---

### 7️⃣ MySQL 애플리케이션 이관 페널티 (MySQL Only)

**측정 대상**: MySQL에서 Stored Procedure 대신 애플리케이션으로 이관해야 하는 비용

**최대 점수**: 2.0점 (MySQL만 적용)

MySQL은 복잡한 Stored Procedure 사용을 권장하지 않습니다. 따라서 대부분의 PL/SQL 로직을 애플리케이션 레벨(Java, Python 등)로 이관해야 합니다.

| 오브젝트 타입 | 이관 페널티 | 이유 |
|--------------|-----------|------|
| PACKAGE | 2.0점 | 완전 분해 + 애플리케이션 이관 |
| PROCEDURE | 2.0점 | 애플리케이션 서비스로 이관 |
| FUNCTION | 2.0점 | 애플리케이션 유틸리티로 이관 |
| TRIGGER | 1.5점 | 이벤트 핸들러로 이관 |
| VIEW | 0점 | DB 레벨 유지 가능 |
| MATERIALIZED VIEW | 0점 | 캐싱 레이어로 이관 |

**이관 예시**:

```sql
-- Oracle PL/SQL 프로시저
CREATE PROCEDURE calculate_order_total(p_order_id NUMBER) AS
    v_total NUMBER := 0;
BEGIN
    SELECT SUM(quantity * unit_price)
    INTO v_total
    FROM order_items
    WHERE order_id = p_order_id;
    
    UPDATE orders SET total_amount = v_total WHERE id = p_order_id;
    COMMIT;
END;
```

```python
# Python 애플리케이션으로 이관
class OrderService:
    def calculate_order_total(self, order_id: int) -> None:
        # 주문 항목 합계 계산
        total = self.db.query(
            "SELECT SUM(quantity * unit_price) FROM order_items WHERE order_id = %s",
            [order_id]
        ).scalar()
        
        # 주문 총액 업데이트
        self.db.execute(
            "UPDATE orders SET total_amount = %s WHERE id = %s",
            [total, order_id]
        )
        self.db.commit()
```



---

## 최종 점수 계산 방법

### 계산 공식

```python
# 1단계: 각 영역 점수 합산
총점 = (기본 점수 
        + 코드 복잡도 
        + Oracle 특화 기능 
        + 비즈니스 로직 
        + 변환 난이도 
        + MySQL 제약           # MySQL만
        + MySQL 이관 페널티)   # MySQL만

# 2단계: 0-10 척도로 정규화
정규화 점수 = min(10.0, 총점 × 10 ÷ 최대 가능 점수)

# 최대 가능 점수
# PostgreSQL: 7.0 + 3.0 + 3.0 + 2.0 + 2.0 = 20.0 (기본 점수 최대 7.0 기준)
# MySQL: 8.0 + 3.0 + 3.0 + 2.0 + 2.0 + 1.5 + 2.0 = 23.5 (기본 점수 최대 8.0 기준)
```

### 계산 예시

**예시 프로시저**:
```sql
CREATE OR REPLACE PROCEDURE process_orders(p_date DATE) AS
    CURSOR order_cursor IS 
        SELECT * FROM orders WHERE order_date = p_date;
    v_total NUMBER := 0;
BEGIN
    FOR rec IN order_cursor LOOP
        v_total := v_total + rec.amount;
        
        IF rec.status = 'PENDING' THEN
            UPDATE orders SET status = 'PROCESSED' WHERE id = rec.id;
        END IF;
    END LOOP;
    
    DBMS_OUTPUT.PUT_LINE('Total: ' || v_total);
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
```

**PostgreSQL 점수 계산**:

| 영역 | 점수 | 근거 |
|------|------|------|
| 기본 점수 | 5.0점 | PROCEDURE |
| 코드 복잡도 | 1.2점 | 약 25줄(0.5) + 커서 1개(0.3) + EXCEPTION 1개(0.2) + 중첩 2(0) |
| Oracle 특화 기능 | 0.5점 | 패키지 호출 1개(DBMS_OUTPUT) |
| 비즈니스 로직 | 0.9점 | COMMIT/ROLLBACK(0.5) + IF 1개(0.2) + 계산(0.2) |
| 변환 난이도 | 0.5점 | DBMS_OUTPUT 의존성 |
| **총점** | **8.1점** | |
| **정규화** | **4.1점** | 8.1 × 10 ÷ 20.0 |
| **레벨** | **🟡 중간** | |

**MySQL 점수 계산**:

| 영역 | 점수 | 근거 |
|------|------|------|
| 기본 점수 | 6.0점 | PROCEDURE |
| 코드 복잡도 | 1.2점 | (동일) |
| Oracle 특화 기능 | 0.5점 | (동일) |
| 비즈니스 로직 | 0.9점 | (동일) |
| 변환 난이도 | 0.5점 | (동일) |
| MySQL 제약 | 0.5점 | NUMBER 타입 |
| MySQL 이관 페널티 | 2.0점 | PROCEDURE 이관 |
| **총점** | **11.6점** | |
| **정규화** | **4.9점** | 11.6 × 10 ÷ 23.5 |
| **레벨** | **🟡 중간** | |

> 💡 같은 프로시저인데 MySQL이 더 높은 점수! 애플리케이션 이관 페널티 때문입니다.



---

## 복잡도 레벨과 권장사항

### 6단계 복잡도 레벨

| 점수 | 레벨 | 의미 | 권장 접근 방식 |
|------|------|------|---------------|
| 0-1 | 🟢 매우 간단 | 단순 로직 | 자동 변환 |
| 1-3 | 🟢 간단 | 기본 PL/SQL | 함수 대체 |
| 3-5 | 🟡 중간 | 일반적인 비즈니스 로직 | 부분 재작성 |
| 5-7 | 🟠 복잡 | 복잡한 비즈니스 로직 | 상당한 재작성 |
| 7-9 | 🔴 매우 복잡 | 고급 Oracle 기능 사용 | 대부분 재작성 |
| 9-10 | ⚫ 극도로 복잡 | 다중 고급 기능 조합 | 완전 재설계 |

### 레벨별 상세 설명

#### 🟢 매우 간단 (0-1점)

```sql
-- 예시: 단순 업데이트 프로시저
CREATE PROCEDURE update_status(p_id NUMBER, p_status VARCHAR2) AS
BEGIN
    UPDATE orders SET status = p_status WHERE id = p_id;
END;
```

- **특징**: 단순 DML, 조건문 없음
- **변환 방법**: AWS SCT 등 자동 변환 도구
- **예상 시간**: 오브젝트당 10분 미만

#### 🟢 간단 (1-3점)

```sql
-- 예시: 기본 조건 처리
CREATE FUNCTION get_discount(p_amount NUMBER) RETURN NUMBER AS
BEGIN
    IF p_amount > 10000 THEN
        RETURN p_amount * 0.1;
    ELSIF p_amount > 5000 THEN
        RETURN p_amount * 0.05;
    ELSE
        RETURN 0;
    END IF;
END;
```

- **특징**: 기본 조건문, 단순 계산
- **변환 방법**: 문법 변환 + 함수명 대체
- **예상 시간**: 오브젝트당 30분-1시간

#### 🟡 중간 (3-5점)

```sql
-- 예시: 커서와 예외 처리
CREATE PROCEDURE process_batch AS
    CURSOR c IS SELECT * FROM pending_orders;
BEGIN
    FOR rec IN c LOOP
        BEGIN
            process_single_order(rec.id);
        EXCEPTION
            WHEN OTHERS THEN
                log_error(rec.id, SQLERRM);
        END;
    END LOOP;
    COMMIT;
END;
```

- **특징**: 커서 사용, 예외 처리, 트랜잭션 제어
- **변환 방법**: 구조 재설계 + 문법 변환
- **예상 시간**: 오브젝트당 2-4시간

#### 🟠 복잡 (5-7점)

```sql
-- 예시: 동적 SQL과 BULK 연산
CREATE PROCEDURE dynamic_update(p_table VARCHAR2, p_column VARCHAR2) AS
    TYPE id_array IS TABLE OF NUMBER;
    v_ids id_array;
BEGIN
    EXECUTE IMMEDIATE 
        'SELECT id BULK COLLECT INTO :1 FROM ' || p_table || ' WHERE status = ''ACTIVE'''
        INTO v_ids;
    
    FORALL i IN 1..v_ids.COUNT
        EXECUTE IMMEDIATE 
            'UPDATE ' || p_table || ' SET ' || p_column || ' = SYSDATE WHERE id = :1'
            USING v_ids(i);
    COMMIT;
END;
```

- **특징**: 동적 SQL, BULK 연산, 컬렉션 타입
- **변환 방법**: 로직 분석 + 대체 구현
- **예상 시간**: 오브젝트당 1-2일
- **주의**: 전문가 검토 필수

#### 🔴 매우 복잡 (7-9점)

```sql
-- 예시: 패키지 + 고급 기능
CREATE PACKAGE BODY order_pkg AS
    g_session_user VARCHAR2(100);
    
    FUNCTION get_orders RETURN order_tab PIPELINED AS
        PRAGMA AUTONOMOUS_TRANSACTION;
    BEGIN
        g_session_user := SYS_CONTEXT('USERENV', 'SESSION_USER');
        
        FOR rec IN (SELECT * FROM orders@remote_db WHERE created_by = g_session_user) LOOP
            PIPE ROW(rec);
        END LOOP;
        RETURN;
    END;
END;
```

- **특징**: 패키지 변수, PIPELINED, AUTONOMOUS_TRANSACTION, DB Link, SYS_CONTEXT
- **변환 방법**: 아키텍처 재설계 필요
- **예상 시간**: 오브젝트당 3-5일
- **권장**: Replatform 고려

#### ⚫ 극도로 복잡 (9-10점)

- **특징**: 여러 고급 기능 조합, 외부 시스템 연동
- **변환 방법**: 완전 재설계 + 아키텍처 변경
- **예상 시간**: 오브젝트당 1주일 이상
- **권장**: Replatform 강력 권장



---

## 실제 예시로 이해하기

### 예시 1: 단순 함수 (점수: 2.1)

```sql
CREATE OR REPLACE FUNCTION get_employee_name(p_id NUMBER) 
RETURN VARCHAR2 AS
    v_name VARCHAR2(100);
BEGIN
    SELECT first_name || ' ' || last_name
    INTO v_name
    FROM employees
    WHERE employee_id = p_id;
    
    RETURN NVL(v_name, 'Unknown');
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 'Not Found';
END;
```

**PostgreSQL 점수 분석**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 기본 점수 | 4.0점 | FUNCTION |
| 코드 복잡도 | 0.7점 | 15줄(0.5) + EXCEPTION(0.2) |
| Oracle 특화 기능 | 0점 | 없음 |
| 비즈니스 로직 | 0점 | 단순 조회 |
| 변환 난이도 | 0점 | 외부 의존성 없음 |
| **총점** | **4.7점** | |
| **정규화** | **2.4점** | 🟢 간단 |

**변환 결과 (PostgreSQL)**:
```sql
CREATE OR REPLACE FUNCTION get_employee_name(p_id INTEGER) 
RETURNS VARCHAR AS $$
DECLARE
    v_name VARCHAR(100);
BEGIN
    SELECT first_name || ' ' || last_name
    INTO v_name
    FROM employees
    WHERE employee_id = p_id;
    
    RETURN COALESCE(v_name, 'Unknown');
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 'Not Found';
END;
$$ LANGUAGE plpgsql;
```

**변환 포인트**:
- `RETURN VARCHAR2` → `RETURNS VARCHAR`
- `NVL` → `COALESCE`
- `$$ LANGUAGE plpgsql` 추가

---

### 예시 2: 중간 복잡도 프로시저 (점수: 4.8)

```sql
CREATE OR REPLACE PROCEDURE sync_inventory AS
    CURSOR c_products IS 
        SELECT product_id, quantity FROM products WHERE status = 'ACTIVE';
    v_count NUMBER := 0;
BEGIN
    FOR rec IN c_products LOOP
        UPDATE inventory 
        SET stock_level = rec.quantity,
            last_updated = SYSDATE
        WHERE product_id = rec.product_id;
        
        IF SQL%ROWCOUNT = 0 THEN
            INSERT INTO inventory (product_id, stock_level, last_updated)
            VALUES (rec.product_id, rec.quantity, SYSDATE);
        END IF;
        
        v_count := v_count + 1;
    END LOOP;
    
    DBMS_OUTPUT.PUT_LINE('Processed: ' || v_count || ' products');
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
        RAISE;
END;
```

**PostgreSQL 점수 분석**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 기본 점수 | 5.0점 | PROCEDURE |
| 코드 복잡도 | 1.5점 | 30줄(0.5) + 커서(0.3) + EXCEPTION(0.2) + 중첩 3(0.5) |
| Oracle 특화 기능 | 0.5점 | DBMS_OUTPUT 호출 |
| 비즈니스 로직 | 0.9점 | COMMIT/ROLLBACK(0.5) + IF(0.2) + 계산(0.2) |
| 변환 난이도 | 0.5점 | DBMS_OUTPUT |
| **총점** | **8.4점** | |
| **정규화** | **4.2점** | 🟡 중간 |

**변환 결과 (PostgreSQL)**:
```sql
CREATE OR REPLACE PROCEDURE sync_inventory()
LANGUAGE plpgsql AS $$
DECLARE
    rec RECORD;
    v_count INTEGER := 0;
BEGIN
    FOR rec IN SELECT product_id, quantity FROM products WHERE status = 'ACTIVE' LOOP
        UPDATE inventory 
        SET stock_level = rec.quantity,
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = rec.product_id;
        
        IF NOT FOUND THEN
            INSERT INTO inventory (product_id, stock_level, last_updated)
            VALUES (rec.product_id, rec.quantity, CURRENT_TIMESTAMP);
        END IF;
        
        v_count := v_count + 1;
    END LOOP;
    
    RAISE NOTICE 'Processed: % products', v_count;
    -- PostgreSQL 프로시저는 자동 커밋
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error: %', SQLERRM;
        RAISE;
END;
$$;
```

**변환 포인트**:
- `CURSOR ... IS` → `FOR rec IN SELECT ...`
- `SYSDATE` → `CURRENT_TIMESTAMP`
- `SQL%ROWCOUNT = 0` → `NOT FOUND`
- `DBMS_OUTPUT.PUT_LINE` → `RAISE NOTICE`
- `COMMIT` 제거 (PostgreSQL 프로시저는 자동 커밋)

---

### 예시 3: 복잡한 패키지 (점수: 7.2)

```sql
CREATE OR REPLACE PACKAGE BODY report_pkg AS
    g_report_date DATE;
    g_user_id NUMBER;
    
    PROCEDURE init_context AS
    BEGIN
        g_user_id := SYS_CONTEXT('USERENV', 'SESSION_USERID');
        g_report_date := TRUNC(SYSDATE);
    END;
    
    FUNCTION generate_report RETURN report_tab PIPELINED AS
        v_data report_rec;
    BEGIN
        init_context;
        
        FOR rec IN (
            SELECT * FROM sales@warehouse_db 
            WHERE sale_date = g_report_date
        ) LOOP
            v_data.sale_id := rec.id;
            v_data.amount := rec.amount;
            v_data.generated_by := g_user_id;
            PIPE ROW(v_data);
        END LOOP;
        RETURN;
    END;
    
    PROCEDURE export_to_file(p_filename VARCHAR2) AS
        v_file UTL_FILE.FILE_TYPE;
    BEGIN
        v_file := UTL_FILE.FOPEN('/reports', p_filename, 'W');
        
        FOR rec IN (SELECT * FROM TABLE(generate_report)) LOOP
            UTL_FILE.PUT_LINE(v_file, rec.sale_id || ',' || rec.amount);
        END LOOP;
        
        UTL_FILE.FCLOSE(v_file);
    EXCEPTION
        WHEN OTHERS THEN
            IF UTL_FILE.IS_OPEN(v_file) THEN
                UTL_FILE.FCLOSE(v_file);
            END IF;
            RAISE;
    END;
END;
```

**PostgreSQL 점수 분석**:

| 영역 | 점수 | 설명 |
|------|------|------|
| 기본 점수 | 7.0점 | PACKAGE |
| 코드 복잡도 | 1.7점 | 50줄(1.0) + 커서(0.3) + EXCEPTION(0.2) + 중첩 3(0.5) - 최대 3.0 |
| Oracle 특화 기능 | 2.5점 | DB Link(1.0) + PIPELINED(0.5) + 패키지 호출(0.5) + SYS_CONTEXT(0.5) |
| 비즈니스 로직 | 1.3점 | 컨텍스트 의존성(0.5) + 패키지 변수(0.8) |
| 변환 난이도 | 1.0점 | UTL_FILE(0.5) + SYS_CONTEXT(0.5) |
| **총점** | **13.5점** | |
| **정규화** | **6.8점** | 🟠 복잡 |

**변환 방향**:
1. 패키지 → 스키마 + 개별 함수/프로시저로 분리
2. 패키지 변수 → 세션 변수 또는 애플리케이션 상태
3. PIPELINED → RETURNS SETOF 또는 테이블 반환 함수
4. DB Link → postgres_fdw 또는 dblink 확장
5. UTL_FILE → COPY 명령 또는 애플리케이션 레벨 파일 처리
6. SYS_CONTEXT → current_user, session_user 등

> ⚠️ **권장**: 이 수준의 복잡도는 전문가 검토와 아키텍처 재설계가 필요합니다.



---

## 📊 요약: PL/SQL 복잡도 계산 치트시트

### 빠른 참조 표

```
┌─────────────────────────────────────────────────────────────────┐
│                  PL/SQL 복잡도 빠른 체크                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🟢 낮은 복잡도 (0-3점)                                          │
│     ✓ 단순 CRUD 로직                                            │
│     ✓ 커서 1-2개 이하                                           │
│     ✓ 중첩 깊이 2 이하                                          │
│     ✓ 외부 의존성 없음                                          │
│                                                                 │
│  🟡 중간 복잡도 (3-5점)                                          │
│     ⚠ 커서 3개 이상                                             │
│     ⚠ 예외 처리 블록 사용                                        │
│     ⚠ 트랜잭션 제어 (COMMIT/ROLLBACK)                           │
│     ⚠ DBMS_OUTPUT 등 기본 패키지 사용                           │
│                                                                 │
│  🔴 높은 복잡도 (5점 이상)                                       │
│     ✗ BULK 연산 (BULK COLLECT, FORALL)                         │
│     ✗ 동적 SQL (EXECUTE IMMEDIATE)                             │
│     ✗ DB Link 사용                                              │
│     ✗ PIPELINED, AUTONOMOUS_TRANSACTION                        │
│     ✗ UTL_FILE, UTL_HTTP 등 외부 의존성                         │
│     ✗ SYS_CONTEXT, 패키지 변수                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 오브젝트 타입별 예상 점수 범위

| 오브젝트 | PostgreSQL | MySQL | 주요 변환 포인트 |
|----------|-----------|-------|-----------------|
| VIEW | 1.0-3.0 | 1.0-3.0 | 대부분 호환 |
| FUNCTION | 2.0-5.0 | 3.0-7.0 | 반환 타입, 문법 |
| PROCEDURE | 2.5-6.0 | 4.0-8.0 | 문법, 트랜잭션 |
| TRIGGER | 3.0-7.0 | 4.0-9.0 | 이벤트 처리, 제약 |
| MATERIALIZED VIEW | 2.0-5.0 | 3.0-7.0 | 리프레시 로직 |
| PACKAGE | 4.0-8.0 | 6.0-10.0 | 분해, 상태 관리 |

### 핵심 기억 포인트

1. **기본 점수가 절반 이상**
   - 오브젝트 타입만으로 기본 난이도 결정
   - Package는 시작부터 높은 점수

2. **MySQL은 항상 더 높은 점수**
   - 애플리케이션 이관 페널티 (최대 2.0점)
   - Stored Procedure 권장하지 않음

3. **외부 의존성이 핵심**
   - UTL_FILE, UTL_HTTP → 애플리케이션 이관 필수
   - DB Link → 아키텍처 변경 필요

4. **점수 5점이 분기점**
   - 5점 이하: 문법 변환 + 부분 수정
   - 5점 이상: 전문가 검토 + 상당한 재작성

5. **Package는 최고 난이도**
   - 분해 + 상태 관리 + 의존성 처리
   - Replatform 고려 대상



---

## 📈 점수별 예상 작업량

### 변환 작업 시간 추정

| 복잡도 레벨 | 점수 | 오브젝트당 예상 시간 | 필요 전문성 |
|------------|------|---------------------|------------|
| 🟢 매우 간단 | 0-1 | 10-30분 | 주니어 |
| 🟢 간단 | 1-3 | 30분-2시간 | 주니어 |
| 🟡 중간 | 3-5 | 2-8시간 | 미드레벨 |
| 🟠 복잡 | 5-7 | 1-3일 | 시니어 |
| 🔴 매우 복잡 | 7-9 | 3-5일 | 시니어 + DBA |
| ⚫ 극도로 복잡 | 9-10 | 1주일+ | 아키텍트 |

### 프로젝트 규모별 예상 일정

| PL/SQL 개수 | 평균 복잡도 | 예상 기간 | 권장 팀 규모 |
|------------|-----------|----------|-------------|
| 10개 미만 | 3.0 | 1-2주 | 1명 |
| 10-30개 | 4.0 | 1-2개월 | 1-2명 |
| 30-50개 | 4.5 | 2-4개월 | 2-3명 |
| 50-100개 | 5.0 | 4-8개월 | 3-5명 |
| 100개 이상 | 5.5+ | 8개월+ | 5명+ |

> ⚠️ **주의**: 위 추정치는 일반적인 가이드라인입니다. 실제 프로젝트는 코드 품질, 문서화 수준, 테스트 요구사항에 따라 크게 달라질 수 있습니다.

---

## 📚 관련 문서

- [SQL 복잡도 계산 공식 설명](SQL_COMPLEXITY_FORMULA_EXPLAINED.md) - SQL 쿼리 복잡도 분석
- [Oracle Migration Analyzer란?](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md) - 도구 개요
- [SQL 복잡도 점수 개선 방안](SQL_COMPLEXITY_SCORE_IMPROVEMENT.md) - 점수 기준 개선 제안
- [PL/SQL 복잡도 점수 개선 방안](PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md) - 점수 기준 개선 제안
- [마이그레이션 추천 임계값 개선 방안](THRESHOLD_IMPROVEMENT_PROPOSAL.md) - 의사결정 임계값 분석

---

## 🔧 부록: 감지되는 Oracle 기능 목록

### PL/SQL 고급 기능

| 기능 | 감지 패턴 | 점수 영향 |
|------|----------|----------|
| PIPELINED | `PIPELINED` 키워드 | +0.5점 (고급 기능) |
| REF CURSOR | `REF CURSOR` | +0.5점 (고급 기능) |
| AUTONOMOUS_TRANSACTION | `AUTONOMOUS_TRANSACTION` | +0.5점 (고급 기능) |
| PRAGMA | `PRAGMA` 키워드 | +0.5점 (고급 기능) |
| OBJECT TYPE | `AS OBJECT` | +0.5점 (고급 기능) |
| VARRAY | `VARRAY` 키워드 | +0.5점 (고급 기능) |
| NESTED TABLE | `TABLE OF` | +0.5점 (고급 기능) |

### 외부 의존성 패키지

| 패키지 | 용도 | 대체 방안 |
|--------|------|----------|
| UTL_FILE | 파일 I/O | 애플리케이션 파일 처리 |
| UTL_HTTP | HTTP 통신 | 애플리케이션 HTTP 클라이언트 |
| UTL_MAIL | 이메일 | 애플리케이션 메일 서비스 |
| UTL_SMTP | SMTP | 애플리케이션 SMTP 클라이언트 |
| DBMS_SCHEDULER | 스케줄링 | cron, pg_cron, 외부 스케줄러 |
| DBMS_JOB | 작업 관리 | 외부 작업 큐 |
| DBMS_LOB | LOB 처리 | 네이티브 LOB 함수 |
| DBMS_OUTPUT | 디버그 출력 | RAISE NOTICE (PG), SELECT (MySQL) |
| DBMS_CRYPTO | 암호화 | pgcrypto (PG), 애플리케이션 암호화 |
| DBMS_SQL | 동적 SQL | EXECUTE (PG), PREPARE (MySQL) |

### 컨텍스트 의존성

| 기능 | 감지 패턴 | PostgreSQL 대체 | MySQL 대체 |
|------|----------|----------------|-----------|
| SYS_CONTEXT | `SYS_CONTEXT(` | current_setting() | 세션 변수 |
| USERENV | `USERENV(` | current_user | USER() |
| GLOBAL TEMP TABLE | `GLOBAL TEMPORARY` | TEMPORARY TABLE | TEMPORARY TABLE |
| DBMS_SESSION | `DBMS_SESSION.` | SET/SHOW | SET/SELECT |
| DBMS_APPLICATION_INFO | `DBMS_APPLICATION_INFO.` | pg_stat_activity | performance_schema |

---

> **문서 이력**
> - 2026-01-29: 최신 코드 기반 업데이트 (기본 점수 하향, 코드 복잡도/Oracle 특화 기능/비즈니스 로직/변환 난이도 점수 상향, 고복잡도 임계값 추가)
> - 2026-01-28: 초안 작성
> - 대상 독자: 마이그레이션 담당자, DBA, 개발자
> - 관련 코드: `src/calculators/plsql_complexity.py`, `src/oracle_complexity_analyzer/weights.py`

