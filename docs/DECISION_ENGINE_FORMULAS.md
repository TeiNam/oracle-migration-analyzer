# 마이그레이션 의사결정 공식 정리

## 1. 복잡도 점수 계산 공식

### 1.1 SQL 복잡도 (0~10점 정규화)

```
총점 = 구조적 점수 + Oracle특화 점수 + 함수 점수 + 볼륨 점수 + 실행 점수 + 변환 점수
정규화 점수 = (총점 / max_total_score) × 10
```

| 타겟 DB | max_total_score | 고난이도 임계값 |
|---------|-----------------|-----------------|
| PostgreSQL | 13.5 | 5.0 |
| MySQL | 18.0 | 7.0 |

#### 구조적 점수 (PostgreSQL 기준)

| 항목 | 조건 | 점수 |
|------|------|------|
| JOIN | 0개 | 0.0 |
| JOIN | 1-3개 | 0.5 |
| JOIN | 4-5개 | 1.0 |
| JOIN | 6개+ | 1.5 |
| 서브쿼리 | 0개 | 0.0 |
| 서브쿼리 | 1개 | 0.5 |
| 서브쿼리 | 2개 | 1.0 |
| 서브쿼리 | 3개+ | 1.5 + min(1, (depth-2)×0.5) |
| CTE | 개수 × 0.5 | max 1.0 |
| SET 연산자 | 개수 × 0.5 | max 1.5 |

#### 데이터 볼륨 점수

| 크기 | PostgreSQL | MySQL |
|------|------------|-------|
| small (<500자) | 0.3 | 0.3 |
| medium (500-1000자) | 0.3 | 0.3 |
| large (1000-2000자) | 0.5 | 0.7 |
| xlarge (2000자+) | 0.8 | 1.0 |

---

### 1.2 PL/SQL 복잡도 (0~10점 정규화)

```
총점 = 기본 점수 + 내부 복잡도 점수 + Oracle 특화 기능 점수 + 외부 의존성 점수
정규화 점수 = min(10, 총점)
```

#### 오브젝트 타입별 기본 점수

| 오브젝트 타입 | PostgreSQL | MySQL |
|--------------|------------|-------|
| PACKAGE | 4.0 | 5.0 |
| PROCEDURE | 2.5 | 3.5 |
| FUNCTION | 2.0 | 3.0 |
| TRIGGER | 3.5 | 4.5 |
| VIEW | 1.0 | 1.0 |
| MATERIALIZED VIEW | 2.5 | 3.5 |

#### MySQL 애플리케이션 이관 페널티

| 오브젝트 타입 | 추가 점수 |
|--------------|----------|
| PACKAGE | +2.0 |
| PROCEDURE | +2.0 |
| FUNCTION | +2.0 |
| TRIGGER | +1.5 |

---

## 2. 마이그레이션 전략 의사결정

### 2.1 의사결정 흐름도

![Decision Tree](./svg/decision_tree.drawio.svg)

---

### 2.2 Replatform 조건 (OR 관계 - 하나라도 만족 시)

| 조건 | 임계값 | 설명 |
|------|--------|------|
| SQL 평균 복잡도 | ≥ 7.5 | 변환 거의 불가능 |
| PL/SQL 평균 복잡도 | ≥ 7.0 | 변환 거의 불가능 |
| 고난이도 비율 | ≥ 25% (모수 70개+) | 변환 공수 과다 |
| 고난이도 절대 개수 | ≥ 50개 | 변환 공수 과다 |
| 대규모 코드베이스 | ≥ 20만줄 + 복잡도 7.5+ | 변환 위험 높음 |
| PL/SQL 오브젝트 개수 | ≥ 500개 | 작업량 과다 |
| 고위험 패키지 사용 | ≥ 50회 | 애플리케이션 재작성 필요 |

#### 고위험 Oracle 패키지 목록

- `UTL_FILE` - 파일 I/O
- `UTL_HTTP` - HTTP 클라이언트
- `UTL_SMTP` - 메일 발송
- `UTL_TCP` - TCP 소켓
- `DBMS_AQ` - Advanced Queuing
- `DBMS_PIPE` - 프로세스 간 통신
- `DBMS_ALERT` - 비동기 알림

---

### 2.3 MySQL 조건 (AND 관계 - 모두 만족 시)

| 조건 | 임계값 | 근거 |
|------|--------|------|
| PL/SQL 평균 복잡도 | ≤ 4.0 | MySQL Stored Procedure 한계 |
| SQL 평균 복잡도 | ≤ 4.5 | MySQL 8.0 CTE/윈도우 함수 지원 |
| PL/SQL 오브젝트 개수 | < 50개 | 이관 작업량 고려 |
| PostgreSQL 선호 점수 | < 2점 | 기술적 근거 기반 |
| BULK 연산 개수 | < 10개 | MySQL 미지원 |

---

### 2.4 PostgreSQL 선호 점수 계산

| 조건 | 점수 | 근거 |
|------|------|------|
| BULK 연산 ≥ 10개 | +3 | MySQL 미지원, PostgreSQL ARRAY로 대체 |
| SQL 복잡도 ≥ 3.5 | +1 | CTE 사용 가능성 높음 |
| 고급 기능 사용 | +2 | PIPELINED, REF CURSOR, OBJECT TYPE 등 |
| 외부 패키지 의존성 | +2 | DBMS_LOB, DBMS_CRYPTO 등 |
| SQL 복잡도 ≥ 4.5 | +1 | 분석 함수 사용 가능성 높음 |

**판정**: 총점 ≥ 2점이면 MySQL 대신 PostgreSQL 선택

#### PostgreSQL 선호 외부 패키지

- `DBMS_LOB` → PostgreSQL Large Object
- `UTL_FILE` → pg_read_file, COPY
- `DBMS_CRYPTO` → pgcrypto 확장
- `DBMS_SQL` → EXECUTE 동적 SQL
- `DBMS_XMLGEN` → XML 함수
- `DBMS_XMLPARSER` → XML 파싱
- `DBMS_AQ` → pg_notify, LISTEN/NOTIFY

#### PostgreSQL 선호 고급 기능

- `PIPELINED` → RETURNS SETOF
- `REF CURSOR` → REFCURSOR
- `OBJECT TYPE` → 복합 타입
- `VARRAY` → ARRAY 타입
- `NESTED TABLE` → ARRAY 타입

---

## 3. 신뢰도 계산 공식

### 3.1 분석 모드별 기본 신뢰도

| 분석 모드 | 기본 신뢰도 | 필요 데이터 |
|-----------|-------------|-------------|
| FULL | 95% | SQL + PL/SQL + DBCSI |
| DB_ONLY | 80% | PL/SQL + DBCSI |
| QUICK | 60% | DBCSI만 |
| SQL_ONLY | 50% | SQL만 |
| PLSQL_ONLY | 55% | PL/SQL만 |
| MINIMAL | 40% | 최소 데이터 |

### 3.2 종합 신뢰도 계산

```
종합 신뢰도 = SQL 신뢰도 × 0.25 
           + PL/SQL 신뢰도 × 0.30 
           + 성능 메트릭 신뢰도 × 0.20 
           + 전략 신뢰도 × 0.25
```

### 3.3 개별 신뢰도 계산

#### SQL 복잡도 신뢰도

| 조건 | 신뢰도 |
|------|--------|
| SQL 파일 50개+ | 95% |
| SQL 파일 20-49개 | 90% |
| SQL 파일 10-19개 | 85% |
| SQL 파일 1-9개 | 75% |
| DBCSI만 있음 | 60% |
| 데이터 없음 | 40% |

#### PL/SQL 복잡도 신뢰도

| 조건 | 신뢰도 |
|------|--------|
| PL/SQL 파일 50개+ | 95% |
| PL/SQL 파일 20-49개 | 90% |
| PL/SQL 파일 10-19개 | 85% |
| PL/SQL 파일 1-9개 | 75% |
| AWR 통계만 있음 | 70% |
| 데이터 없음 | 35% |

#### 성능 메트릭 신뢰도

| 조건 | 신뢰도 |
|------|--------|
| AWR + CPU/IO 메트릭 | 95% |
| AWR 기본 | 85% |
| Statspack + 메트릭 | 85% |
| Statspack 기본 | 75% |
| 데이터 없음 | 30% |

---

## 4. 난이도 판정 기준

### 4.1 PL/SQL 라인 수 기반 난이도

| 난이도 | 라인 수 | 예상 기간 |
|--------|---------|-----------|
| 낮음 | < 20,000줄 | 3~6개월 |
| 중간 | 20,000~50,000줄 | 6~12개월 |
| 높음 | 50,000~100,000줄 | 12~18개월 |
| 매우 높음 | 100,000줄+ | 18개월+ |

### 4.2 고난이도 임계값 (타겟 DB별)

| 타겟 DB | 임계값 | 산출 근거 |
|---------|--------|-----------|
| PostgreSQL | 5.0 | max_score(13.5) × 37% |
| MySQL | 7.0 | max_score(18.0) × 39% |

---

## 5. 의사결정 매트릭스 요약

### PL/SQL 개수 × 복잡도 매트릭스

| 복잡도 \ 개수 | 적음 (<50) | 중간 (50-100) | 많음 (100+) |
|---------------|------------|---------------|-------------|
| 높음 (6.0+) | PostgreSQL | Replatform | Replatform |
| 중간 (3.5-6.0) | PostgreSQL | PostgreSQL | PostgreSQL |
| 낮음 (<3.5) | MySQL* | PostgreSQL | PostgreSQL |

*MySQL 조건: PostgreSQL 선호 점수 < 2점, BULK 연산 < 10개

---

## 6. 버전 정보

- 문서 버전: 1.1
- 최종 수정: 2026-01-31
- 적용 코드: `src/migration_recommendation/decision_engine.py`
- 변경 사항: MySQL 조건 임계값 상향 (PL/SQL 4.0, SQL 4.5, 개수 50개)
