# Oracle Migration Analyzer

Oracle 데이터베이스의 마이그레이션 난이도를 분석하는 Python 기반 도구 모음입니다.

## 도구 목록

### 1. Oracle Complexity Analyzer
Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 0-10 척도로 평가합니다.

### 2. DBCSI Analyzer (AWR/Statspack)
DBCSI AWR 또는 Statspack 결과 파일을 파싱하여 Oracle 데이터베이스의 성능 메트릭과 리소스 사용량을 분석하고, RDS for Oracle, Aurora MySQL, Aurora PostgreSQL로의 마이그레이션 난이도를 평가합니다.

### 3. Migration Recommendation Engine
DBCSI 분석기(성능 메트릭)와 SQL/PL-SQL 분석기(코드 복잡도)의 결과를 통합하여 최적의 마이그레이션 전략을 추천합니다. Replatform(RDS for Oracle SE2), Refactoring to Aurora MySQL, Refactoring to Aurora PostgreSQL 중 가장 적합한 전략을 의사결정 트리 기반으로 선택하고, 추천 근거, 대안 전략, 위험 요소, 마이그레이션 로드맵을 포함한 종합 리포트를 생성합니다.

---

## 설치

```bash
# 저장소 클론
git clone <repository-url>
cd oracle-migration-analyzer

# 가상 환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 패키지 설치 (개발 모드)
pip install -e .
```

---

## 1. Oracle Complexity Analyzer

### 주요 기능

- ✅ **SQL 쿼리 복잡도 분석**: 6가지 카테고리로 구조적 복잡성 평가
- ✅ **PL/SQL 오브젝트 분석**: Package, Procedure, Function, Trigger 등 분석
- ✅ **타겟 DB별 가중치**: PostgreSQL/MySQL 각각에 최적화된 복잡도 계산
- ✅ **Oracle 특화 기능 감지**: CONNECT BY, PIVOT, 분석 함수 등 자동 감지
- ✅ **변환 가이드 제공**: 감지된 Oracle 기능에 대한 타겟 DB별 대체 방법 제시
- ✅ **폴더 일괄 분석**: 병렬 처리로 대량 파일 빠른 분석
- ✅ **다양한 출력 형식**: JSON, Markdown 리포트 생성

### CLI 사용법

#### 단일 파일 분석

```bash
# PostgreSQL 타겟으로 SQL 파일 분석 (기본값)
oracle-complexity-analyzer -f query.sql

# MySQL 타겟으로 PL/SQL 파일 분석
oracle-complexity-analyzer -f package.pls -t mysql

# 결과를 Markdown 파일로 저장
oracle-complexity-analyzer -f query.sql -o markdown

# 결과를 JSON 파일로 저장
oracle-complexity-analyzer -f query.sql -o json
```

#### 폴더 일괄 분석

```bash
# 폴더 내 모든 SQL/PL/SQL 파일 분석
oracle-complexity-analyzer -d sample_code -t postgresql -o markdown

# MySQL 타겟으로 폴더 분석
oracle-complexity-analyzer -d /path/to/sql/files -t mysql -o markdown

# 병렬 워커 수 지정 (기본값: CPU 코어 수)
oracle-complexity-analyzer -d sample_code -w 8 -o markdown
```

#### 출력 구조

분석 결과는 **원본 파일의 폴더 구조를 반영**하여 자동으로 저장됩니다:

**부모 폴더가 있는 경우** (예: `sample_code/file.sql`, `MKDB/file.sql`):
```
reports/
└── {원본폴더명}/           # 원본 파일의 부모 폴더명 자동 반영
    ├── PGSQL/
    │   ├── sql_complexity_PGSQL.md      # 통합 리포트 (배치 분석 시)
    │   ├── sql_complexity_PGSQL.json    # JSON 리포트 (배치 분석 시)
    │   ├── file1.md                     # 개별 파일 리포트
    │   ├── file1.json
    │   └── ...
    └── MySQL/
        ├── sql_complexity_MySQL.md
        ├── sql_complexity_MySQL.json
        ├── file1.md
        └── ...
```

**부모 폴더가 없는 경우** (예: 루트 디렉토리의 `file.sql`):
```
reports/
└── YYYYMMDD/              # 날짜 폴더 (예: 20260118)
    ├── file_postgresql.json
    ├── file_postgresql.md
    ├── file_mysql.json
    └── file_mysql.md
```

**예시**:
- `sample_code/query.sql` 분석 → `reports/sample_code/PGSQL/query.json`
- `MKDB/procedure.pls` 분석 → `reports/MKDB/MySQL/procedure.md`
- `test.sql` 분석 → `reports/20260118/test_postgresql.json`

### 명령줄 옵션

**필수 옵션 (둘 중 하나 선택)**:
- `-f FILE`, `--file FILE`: 분석할 단일 SQL/PL/SQL 파일 경로
- `-d DIR`, `--directory DIR`: 분석할 폴더 경로 (하위 폴더 포함)

**선택 옵션**:
- `-t DB`, `--target DB`: 타겟 데이터베이스 선택
  - `postgresql`, `pg`: PostgreSQL (기본값)
  - `mysql`, `my`: MySQL

- `-o FORMAT`, `--output FORMAT`: 출력 형식 선택
  - `console`: 콘솔 출력만 (기본값)
  - `json`: JSON 파일로 저장
  - `markdown`: Markdown 파일로 저장
  - `both`: 콘솔 출력 + JSON/Markdown 파일 저장

- `-w N`, `--workers N`: 병렬 처리 워커 수 (폴더 분석 시, 기본값: CPU 코어 수)

### 복잡도 레벨 분류

| 점수 범위 | 레벨 | 권장사항 |
|----------|------|---------|
| 0-1 | 매우 간단 | 자동 변환 |
| 1-3 | 간단 | 함수 대체 |
| 3-5 | 중간 | 부분 재작성 |
| 5-7 | 복잡 | 상당한 재작성 |
| 7-9 | 매우 복잡 | 대부분 재작성 |
| 9-10 | 극도로 복잡 | 완전 재설계 |

---

## 2. DBCSI Analyzer (AWR/Statspack)

### 주요 기능

- ✅ **AWR/Statspack 파일 파싱**: DBCSI 결과 파일(.out) 자동 파싱
- ✅ **백분위수 기반 분석**: P99, P95, P90 등 백분위수 메트릭 활용 (AWR)
- ✅ **함수별 I/O 분석**: LGWR, DBWR, Direct I/O 등 함수별 통계 (AWR)
- ✅ **워크로드 패턴 분석**: CPU 집약적/I/O 집약적 워크로드 분류 (AWR)
- ✅ **버퍼 캐시 효율성**: 히트율 분석 및 최적화 권장사항 (AWR)
- ✅ **정밀한 인스턴스 사이징**: P99 메트릭 기반 RDS 인스턴스 추천
- ✅ **마이그레이션 난이도 계산**: 타겟 DB별 0-10 척도 난이도 평가
- ✅ **배치 파일 분석**: 여러 파일 일괄 처리
- ✅ **다양한 출력 형식**: JSON, Markdown 리포트 생성

### CLI 사용법

#### 단일 파일 분석

```bash
# 기본 분석 (모든 타겟 DB)
dbcsi-analyzer --file sample_code/dbcsi_awr_sample01.out

# 특정 타겟 DB만 분석
dbcsi-analyzer --file awr_sample.out --target aurora-postgresql

# 상세 리포트 생성 (AWR 특화 섹션 포함)
dbcsi-analyzer --file awr_sample.out --detailed

# JSON 형식으로 출력
dbcsi-analyzer --file awr_sample.out --format json

# 마이그레이션 분석 포함
dbcsi-analyzer --file awr_sample.out --analyze-migration --detailed
```

#### 배치 파일 분석

```bash
# 디렉토리 내 모든 AWR/Statspack 파일 분석
dbcsi-analyzer --directory sample_code --format markdown

# 특정 타겟 DB로 배치 분석
dbcsi-analyzer --directory /path/to/files --target aurora-postgresql
```

#### 출력 구조

분석 결과는 **원본 파일의 폴더 구조를 반영**하여 자동으로 저장됩니다:

**부모 폴더가 있는 경우** (예: `sample_code/awr.out`):
```
reports/
└── {원본폴더명}/           # 원본 파일의 부모 폴더명 자동 반영
    ├── dbcsi_awr_sample01.md
    ├── dbcsi_statspack_sample01.md
    └── ...
```

**부모 폴더가 없는 경우** (예: 루트 디렉토리의 `awr.out`):
```
reports/
└── YYYYMMDD/              # 날짜 폴더 (예: 20260118)
    ├── awr_analysis.md
    └── ...
```

### 명령줄 옵션

**필수 옵션 (둘 중 하나 선택)**:
- `--file FILE`: 분석할 단일 AWR/Statspack 파일 경로
- `--directory DIR`: 분석할 디렉토리 경로 (모든 .out 파일)

**선택 옵션**:
- `--format FORMAT`: 출력 형식 선택
  - `json`: JSON 형식
  - `markdown`: Markdown 형식 (기본값)

- `--target TARGET`: 타겟 데이터베이스 선택
  - `rds-oracle`: RDS for Oracle
  - `aurora-mysql`: Aurora MySQL 8.0
  - `aurora-postgresql`: Aurora PostgreSQL 16
  - `all`: 모든 타겟 (기본값)

- `--analyze-migration`: 마이그레이션 난이도 분석 포함

- `--detailed`: AWR 특화 섹션을 포함한 상세 리포트 생성

- `--compare FILE1 FILE2`: 두 AWR 파일 비교

- `--percentile PERCENTILE`: 분석에 사용할 백분위수
  - `99`: P99 (기본값)
  - `95`: P95
  - `90`: P90
  - `75`: P75
  - `median`: 중앙값
  - `average`: 평균

- `--language LANG`: 리포트 언어
  - `ko`: 한국어 (기본값)
  - `en`: 영어

### AWR vs Statspack 차이점

| 기능 | Statspack | AWR |
|------|-----------|-----|
| 기본 성능 메트릭 | ✅ | ✅ |
| 백분위수 메트릭 (P99, P95) | ❌ | ✅ |
| 함수별 I/O 통계 | ❌ | ✅ |
| 워크로드 패턴 분석 | ❌ | ✅ |
| 버퍼 캐시 효율성 | ❌ | ✅ |
| 시간대별 분석 | ❌ | ✅ |
| 정밀한 인스턴스 사이징 | ✅ | ✅✅ (더 정확) |
| 분석 신뢰도 | 중간 | 높음 |

---

## 3. Migration Recommendation Engine

### 주요 기능

- ✅ **분석 결과 통합**: DBCSI(성능 메트릭)와 SQL/PL-SQL(코드 복잡도) 분석 결과 통합
- ✅ **의사결정 엔진**: 코드 복잡도와 성능 메트릭 기반 최적 전략 자동 결정
- ✅ **3가지 마이그레이션 전략**:
  - **Replatform**: RDS for Oracle SE2 Single (코드 변경 최소화)
  - **Refactor to Aurora MySQL**: 단순 SQL/PL-SQL을 애플리케이션 레벨로 이관
  - **Refactor to Aurora PostgreSQL**: 복잡한 PL/SQL을 PL/pgSQL로 변환
- ✅ **종합 추천 리포트**: 추천 근거, 대안 전략, 위험 요소, 마이그레이션 로드맵 포함
- ✅ **Executive Summary**: 비기술적 언어로 작성된 경영진용 요약
- ✅ **다양한 출력 형식**: Markdown, JSON 리포트 생성
- ✅ **한국어/영어 지원**: 다국어 리포트 생성

### CLI 사용법

#### 기본 사용법

```bash
# reports 폴더 내 특정 폴더를 지정하여 추천 리포트 생성
migration-recommend --reports-dir reports/sample_code

# JSON 형식으로 출력
migration-recommend --reports-dir reports/sample_code --format json

# 영어 리포트 생성
migration-recommend --reports-dir reports/sample_code --language en
```

#### 레거시 모드 (개별 파일 지정)

```bash
# DBCSI 파일과 SQL 디렉토리를 직접 지정
migration-recommend \
  --dbcsi sample_code/dbcsi_awr_sample01.out \
  --sql-dir sample_code \
  --output reports/recommendation.md

# DBCSI 없이 SQL/PL-SQL 분석만으로 추천 (성능 메트릭 제외)
migration-recommend \
  --sql-dir sample_code \
  --output reports/recommendation.md
```

#### 출력 구조

추천 리포트는 다음과 같은 위치에 생성됩니다:

```
reports/
└── {분석대상폴더명}/
    └── migration_recommendation.md    # 추천 리포트
```

### 명령줄 옵션

**필수 옵션 (둘 중 하나 선택)**:
- `--reports-dir DIR`: 분석 리포트가 있는 폴더 경로 (권장)
- `--sql-dir DIR`: SQL/PL-SQL 파일이 있는 디렉토리 경로 (레거시 모드)

**선택 옵션**:
- `--dbcsi FILE`: DBCSI 분석 결과 파일 경로 (레거시 모드)
- `--format FORMAT`: 출력 형식 선택
  - `markdown`: Markdown 형식 (기본값)
  - `json`: JSON 형식
- `--output PATH`: 출력 파일 경로 (지정하지 않으면 자동 경로 사용)
- `--language LANG`: 리포트 언어
  - `ko`: 한국어 (기본값)
  - `en`: 영어
- `--target TARGET`: SQL/PL-SQL 분석 시 타겟 DB (기본값: postgresql)
  - `postgresql`: Aurora PostgreSQL
  - `mysql`: Aurora MySQL

### 의사결정 트리

마이그레이션 전략은 다음 의사결정 트리를 따릅니다:

```
시작
  │
  ▼
평균 SQL 복잡도 >= 7.0?  ───YES──┐
  │                              │
  NO                             │
  │                              │
  ▼                              │
평균 PL/SQL 복잡도 >= 7.0? ─YES──┤
  │                              │
  NO                             │
  │                              │
  ▼                              │
복잡 오브젝트 비율 >= 30%? ──YES──┤
  │                              │
  NO                             │
  │                              ▼
  │                         REPLATFORM
  │                         (RDS Oracle SE2)
  │
  ▼
평균 SQL 복잡도 <= 5.0? ───NO───┐
  │                             │
  YES                           │
  │                             │
  ▼                             │
평균 PL/SQL 복잡도 <= 5.0? ─NO──┤
  │                             │
  YES                           │
  │                             │
  ▼                             │
PL/SQL 오브젝트 < 50개? ───NO───┤
  │                             │
  YES                           │
  │                             │
  ▼                             ▼
AURORA MYSQL              AURORA POSTGRESQL
(애플리케이션 이관)        (PL/pgSQL 변환)
  │                             ▲
  │                             │
  ▼                             │
BULK 연산 >= 10개? ───YES────────┘
  │
  NO
  │
  ▼
(Aurora MySQL 유지)
```

### 전략별 특징

#### Replatform (RDS for Oracle SE2)

**장점**:
- 코드 변경 최소화
- 빠른 마이그레이션 (8-12주)
- 높은 호환성

**단점**:
- Oracle 라이선스 비용 지속
- Single 인스턴스만 지원 (RAC 미지원)
- 장기적 TCO 높음

**적합한 경우**:
- 평균 복잡도 >= 7.0
- 복잡 오브젝트 비율 >= 30%
- 코드 변경 위험이 높은 경우

#### Refactor to Aurora MySQL

**장점**:
- 오픈소스 기반 (라이선스 비용 없음)
- 낮은 TCO
- 간단한 SQL 처리에 최적

**단점**:
- 모든 PL/SQL을 애플리케이션 레벨로 이관 필요
- MySQL Stored Procedure 사용 불가
- BULK 연산 미지원

**적합한 경우**:
- 평균 SQL 복잡도 <= 5.0
- 평균 PL/SQL 복잡도 <= 5.0
- PL/SQL 오브젝트 < 50개
- BULK 연산 < 10개

#### Refactor to Aurora PostgreSQL

**장점**:
- PL/pgSQL 70-75% Oracle 호환
- BULK 연산 대체 가능
- 고급 기능 지원

**단점**:
- PL/SQL 변환 작업 필요
- BULK 연산 성능 차이 (20-50%)
- 일부 Oracle 기능 미지원

**적합한 경우**:
- 평균 복잡도 5.0-7.0
- BULK 연산 >= 10개
- 평균 PL/SQL 복잡도 >= 5.0

---

## 통합 워크플로우

### 전체 분석 프로세스

```bash
# 1단계: SQL/PL-SQL 복잡도 분석
oracle-complexity-analyzer -d sample_code -t postgresql -o markdown

# 2단계: DBCSI 성능 분석
dbcsi-analyzer --directory sample_code --format markdown

# 3단계: 마이그레이션 추천 리포트 생성
migration-recommend --reports-dir reports/sample_code
```

### 리포트 폴더 구조

분석 결과는 **원본 파일의 폴더 구조를 자동으로 반영**합니다:

```
reports/
└── {원본폴더명}/           # 예: sample_code, MKDB 등
    ├── PGSQL/
    │   ├── sql_complexity_PGSQL.md      # SQL 복잡도 통합 리포트
    │   ├── sql_complexity_PGSQL.json
    │   ├── query1.md                    # 개별 SQL 파일 리포트
    │   └── ...
    ├── MySQL/
    │   ├── sql_complexity_MySQL.md
    │   └── ...
    ├── dbcsi_awr_sample01.md            # DBCSI 성능 리포트
    ├── dbcsi_statspack_sample01.md
    └── migration_recommendation.md       # 최종 추천 리포트
```

**폴더 구조 규칙**:
- 원본 파일에 부모 폴더가 있으면 해당 폴더명 사용 (예: `sample_code/file.sql` → `reports/sample_code/`)
- 부모 폴더가 없으면 날짜 폴더 사용 (예: `file.sql` → `reports/20260118/`)

---

## Python API 사용

CLI가 주요 인터페이스이지만, Python 코드에서 직접 라이브러리로 사용할 수도 있습니다.

### Oracle Complexity Analyzer

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    TargetDatabase
)

# 분석기 생성
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL
)

# 폴더 일괄 분석
batch_analyzer = BatchAnalyzer(analyzer, max_workers=4)
batch_result = batch_analyzer.analyze_folder("sample_code")

# 결과 저장
batch_analyzer.export_batch_markdown(batch_result)
```

### DBCSI Analyzer

```python
from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter

# AWR 파일 파싱
parser = StatspackParser("sample_code/dbcsi_awr_sample01.out")
awr_data = parser.parse()

# 마이그레이션 분석
analyzer = MigrationAnalyzer(awr_data)
analysis_results = analyzer.analyze()

# Markdown 리포트 생성
markdown_output = StatspackResultFormatter.to_markdown(
    awr_data, 
    analysis_results
)
```

### Migration Recommendation

```python
from src.migration_recommendation import (
    AnalysisResultIntegrator,
    MigrationDecisionEngine,
    RecommendationReportGenerator,
    MarkdownReportFormatter
)

# 분석 결과 통합
integrator = AnalysisResultIntegrator()
integrated_result = integrator.integrate(
    dbcsi_result=dbcsi_data,
    sql_analysis=sql_results,
    plsql_analysis=plsql_results
)

# 추천 리포트 생성
decision_engine = MigrationDecisionEngine()
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

# Markdown 리포트 출력
formatter = MarkdownReportFormatter()
markdown_report = formatter.format(recommendation, language="ko")
```

자세한 예제는 `example_*.py` 파일들을 참조하세요.

---

## 문서

자세한 내용은 `docs/` 폴더의 문서를 참조하세요:

- `complexity_postgresql.md`: PostgreSQL 타겟 복잡도 계산 공식
- `complexity_mysql.md`: MySQL 타겟 복잡도 계산 공식
- `oracle_complexity_formula.md`: 전체 복잡도 계산 공식
- `migration_guide_aurora_pg16.md`: Aurora PostgreSQL 16 마이그레이션 가이드
- `migration_guide_aurora_mysql80.md`: Aurora MySQL 8.0 마이그레이션 가이드

---

## 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=html

# 특정 테스트만 실행
pytest tests/test_sql_parser.py

# 속성 기반 테스트만 실행
pytest -m property
```

---

## 라이선스

MIT License

---

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

---

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
