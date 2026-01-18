# Sample Code 분석 리포트

이 디렉토리는 `sample_code` 폴더의 모든 SQL/PL-SQL 파일에 대한 복잡도 분석 결과를 포함합니다.

## 📁 디렉토리 구조

```
reports/sample_code/
├── PGSQL/                          # PostgreSQL 타겟 분석 결과
│   ├── sql_complexity_PGSQL.md    # 통합 리포트
│   ├── advanced_analytics_query.md
│   ├── complex_data_migration.md
│   ├── complex_plsql_etl.md
│   ├── complex_query.md
│   ├── hierarchical_recursive_query.md
│   ├── package_example.md
│   ├── sample_plsql01.md
│   ├── sample_plsql02.md
│   ├── sample_plsql03.md
│   ├── sample_plsql04.md
│   └── simple_query.md
│
├── MySQL/                          # MySQL 타겟 분석 결과
│   ├── sql_complexity_MySQL.md    # 통합 리포트
│   └── (개별 파일 리포트들...)
│
├── dbcsi_awr_sample01.md          # AWR 리포트 샘플 1
├── dbcsi_awr_sample02.md          # AWR 리포트 샘플 2
├── dbcsi_statspack_sample01.md    # Statspack 리포트 샘플
├── migration_recommendation_sample01.md  # 마이그레이션 추천 샘플 1
└── migration_recommendation_sample02.md  # 마이그레이션 추천 샘플 2
```

## 📊 분석 결과 요약

### PostgreSQL 타겟 분석

- **전체 파일 수**: 11개
- **평균 복잡도**: 5.84 / 10
- **복잡도 분포**:
  - 극도로 복잡 (9.0+): 2개 (18.2%)
  - 매우 복잡 (7.0-8.9): 1개 (9.1%)
  - 복잡 (5.0-6.9): 4개 (36.4%)
  - 중간 (3.0-4.9): 3개 (27.3%)
  - 매우 간단 (0-2.9): 1개 (9.1%)

### MySQL 타겟 분석

- **전체 파일 수**: 11개
- **평균 복잡도**: 6.10 / 10
- **복잡도 분포**:
  - 극도로 복잡 (9.0+): 2개 (18.2%)
  - 매우 복잡 (7.0-8.9): 3개 (27.3%)
  - 복잡 (5.0-6.9): 2개 (18.2%)
  - 중간 (3.0-4.9): 3개 (27.3%)
  - 매우 간단 (0-2.9): 1개 (9.1%)

## 🔝 가장 복잡한 파일 Top 5

### PostgreSQL 타겟

| 순위 | 파일명 | 복잡도 | 레벨 | 주요 특징 |
|------|--------|--------|------|-----------|
| 1 | complex_query.sql | 10.00 | 극도로 복잡 | MODEL 절, 다중 CTE, 피벗 |
| 2 | hierarchical_recursive_query.sql | 9.85 | 극도로 복잡 | CONNECT BY, 계층 구조, 재귀 |
| 3 | advanced_analytics_query.sql | 8.67 | 매우 복잡 | MATCH_RECOGNIZE, 통계 함수 |
| 4 | complex_data_migration.sql | 6.81 | 복잡 | DBMS_CRYPTO, UTL_HTTP, XML |
| 5 | complex_plsql_etl.sql | 6.72 | 복잡 | UTL_FILE, BULK, 동적 SQL |

### MySQL 타겟

| 순위 | 파일명 | 복잡도 | 레벨 | 주요 특징 |
|------|--------|--------|------|-----------|
| 1 | complex_query.sql | 10.00 | 극도로 복잡 | MODEL 절 (MySQL 미지원) |
| 2 | hierarchical_recursive_query.sql | 9.67 | 극도로 복잡 | CONNECT BY (MySQL 미지원) |
| 3 | advanced_analytics_query.sql | 8.67 | 매우 복잡 | MATCH_RECOGNIZE (MySQL 미지원) |
| 4 | complex_data_migration.sql | 7.23 | 매우 복잡 | 패키지, 외부 프로시저 호출 |
| 5 | complex_plsql_etl.sql | 7.15 | 매우 복잡 | 패키지, UTL_FILE, BULK |

## 🎯 주요 마이그레이션 이슈

### 1. Oracle 종속 패키지 사용

다음 Oracle 종속 패키지들이 샘플 코드에서 사용되었습니다:

- **UTL_FILE**: 파일 I/O 작업
- **DBMS_SQL**: 동적 SQL 실행
- **DBMS_LOB**: 대용량 객체 처리
- **DBMS_SCHEDULER**: 작업 스케줄링
- **DBMS_LOCK**: 분산 락 관리
- **DBMS_CRYPTO**: 데이터 암호화
- **DBMS_XMLGEN**: XML 생성
- **UTL_HTTP**: HTTP 요청
- **UTL_MAIL**: 이메일 발송
- **DBMS_PIPE**: 프로세스 간 통신

### 2. 고급 SQL 기능

- **CONNECT BY / START WITH**: 계층형 쿼리 (PostgreSQL: WITH RECURSIVE, MySQL: 미지원)
- **MODEL 절**: 다차원 배열 계산 (PostgreSQL/MySQL: 미지원)
- **MATCH_RECOGNIZE**: 패턴 매칭 (PostgreSQL 12+: 제한적, MySQL: 미지원)
- **PIVOT/UNPIVOT**: 행/열 전환 (PostgreSQL: crosstab, MySQL: CASE 문)

### 3. PL/SQL 특화 기능

- **패키지 (PACKAGE)**: PostgreSQL은 스키마로 대체, MySQL은 미지원
- **BULK COLLECT/FORALL**: PostgreSQL은 배열 처리로 대체
- **REF CURSOR**: PostgreSQL은 REFCURSOR, MySQL은 미지원
- **PRAGMA**: 대부분 불필요하거나 함수 속성으로 대체

## 📝 리포트 사용 방법

### 통합 리포트 확인

```bash
# PostgreSQL 타겟 통합 리포트
cat reports/sample_code/PGSQL/sql_complexity_PGSQL.md

# MySQL 타겟 통합 리포트
cat reports/sample_code/MySQL/sql_complexity_MySQL.md
```

### 개별 파일 리포트 확인

```bash
# 특정 파일의 PostgreSQL 타겟 분석 결과
cat reports/sample_code/PGSQL/complex_plsql_etl.md

# 특정 파일의 MySQL 타겟 분석 결과
cat reports/sample_code/MySQL/complex_plsql_etl.md
```

### 마이그레이션 추천 리포트

```bash
# AWR 기반 마이그레이션 추천 (샘플 1)
cat reports/sample_code/migration_recommendation_sample01.md

# AWR 기반 마이그레이션 추천 (샘플 2)
cat reports/sample_code/migration_recommendation_sample02.md
```

## 🔄 리포트 재생성

리포트를 재생성하려면 다음 CLI 명령어를 사용하세요:

```bash
# PostgreSQL 타겟 분석
python -m src.oracle_complexity_analyzer \
  --directory sample_code \
  --target postgresql \
  -o markdown \
  --output-dir reports/sample_code

# MySQL 타겟 분석
python -m src.oracle_complexity_analyzer \
  --directory sample_code \
  --target mysql \
  -o markdown \
  --output-dir reports/sample_code

# 마이그레이션 추천 리포트 생성
python -m src.migration_recommendation.cli \
  --legacy \
  --dbcsi sample_code/dbcsi_awr_sample01.out \
  --sql-dir sample_code \
  --output reports/sample_code/migration_recommendation_sample01.md
```

## 📚 참고 문서

- [Oracle 복잡도 공식](../../docs/oracle_complexity_formula.md)
- [PostgreSQL 마이그레이션 가이드](../../docs/migration_guide_aurora_pg16.md)
- [MySQL 복잡도 계산](../../docs/complexity_mysql.md)
- [AI 지원 마이그레이션](../../docs/ai_assisted_migration.md)

## 🎓 샘플 파일 설명

### 간단한 샘플
- **simple_query.sql**: 기본 SELECT 쿼리 (복잡도: 0.52)

### 중간 복잡도 샘플
- **sample_plsql02.sql**: 기본 프로시저 (복잡도: 4.04)
- **sample_plsql04.sql**: 함수와 예외 처리 (복잡도: 3.06)
- **package_example.pls**: 패키지 구조 (복잡도: 4.21)

### 복잡한 샘플
- **sample_plsql01.sql**: BULK 연산과 예외 처리 (복잡도: 5.23)
- **sample_plsql03.sql**: 커서와 동적 SQL (복잡도: 5.11)

### 매우 복잡한 샘플 (새로 추가)
- **complex_plsql_etl.sql**: ETL 프로세스, 외부 패키지 사용 (복잡도: 6.72)
- **complex_data_migration.sql**: 데이터 마이그레이션, 암호화, API 호출 (복잡도: 6.81)
- **advanced_analytics_query.sql**: 고급 분석, 패턴 매칭, 예측 (복잡도: 8.67)

### 극도로 복잡한 샘플 (새로 추가)
- **hierarchical_recursive_query.sql**: 계층형 쿼리, CONNECT BY (복잡도: 9.85)
- **complex_query.sql**: MODEL 절, 다차원 분석 (복잡도: 10.00)

---

**생성 일시**: 2026-01-16
**분석 도구**: Oracle Migration Analyzer v1.0
