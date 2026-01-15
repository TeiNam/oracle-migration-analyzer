# Oracle Migration Analyzer

Oracle 데이터베이스의 마이그레이션 난이도를 분석하는 Python 기반 도구 모음입니다.

## 도구 목록

### 1. Oracle Complexity Analyzer
Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 0-10 척도로 평가합니다.

### 2. Statspack Analyzer
DBCSI Statspack 결과 파일을 파싱하여 Oracle 데이터베이스의 성능 메트릭과 리소스 사용량을 분석하고, RDS for Oracle, Aurora MySQL, Aurora PostgreSQL로의 마이그레이션 난이도를 평가합니다.

### 3. AWR Analyzer
DBCSI AWR(Automatic Workload Repository) 결과 파일을 파싱하여 Oracle 데이터베이스의 상세한 성능 메트릭을 분석합니다. Statspack보다 더 정확한 백분위수 기반 성능 데이터를 제공하며, 함수별 I/O 통계, 워크로드 패턴, 버퍼 캐시 효율성 등 고급 분석 기능을 포함합니다.

### 4. Migration Recommendation Engine
DBCSI 분석기(성능 메트릭)와 SQL/PL-SQL 분석기(코드 복잡도)의 결과를 통합하여 최적의 마이그레이션 전략을 추천합니다. Replatform(RDS for Oracle SE2), Refactoring to Aurora MySQL, Refactoring to Aurora PostgreSQL 중 가장 적합한 전략을 의사결정 트리 기반으로 선택하고, 추천 근거, 대안 전략, 위험 요소, 마이그레이션 로드맵을 포함한 종합 리포트를 생성합니다.

---

## Migration Recommendation Engine

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

### 설치

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

### 사용 방법

#### CLI 명령어

```bash
# 기본 사용법 (DBCSI + SQL/PL-SQL 분석 결과 필요)
migration-recommend \
  --dbcsi sample_code/dbcsi_awr_sample01.out \
  --sql-dir sample_code \
  --output reports/recommendation.md

# JSON 형식으로 출력
migration-recommend \
  --dbcsi sample_code/dbcsi_statspack_sample01.out \
  --sql-dir sample_code \
  --format json \
  --output reports/recommendation.json

# 영어 리포트 생성
migration-recommend \
  --dbcsi sample_code/dbcsi_awr_sample01.out \
  --sql-dir sample_code \
  --language en \
  --output reports/recommendation_en.md

# DBCSI 없이 SQL/PL-SQL 분석만으로 추천 (성능 메트릭 제외)
migration-recommend \
  --sql-dir sample_code \
  --output reports/recommendation.md
```

#### 명령줄 옵션

**필수 옵션 (최소 하나 필요)**:
- `--dbcsi FILE`: DBCSI 분석 결과 파일 경로 (AWR 또는 Statspack .out 파일)
- `--sql-dir DIR`: SQL/PL-SQL 파일이 있는 디렉토리 경로

**선택 옵션**:
- `--format FORMAT`: 출력 형식 선택
  - `markdown`: Markdown 형식 (기본값)
  - `json`: JSON 형식
  
- `--output PATH`: 출력 파일 경로 (지정하지 않으면 표준 출력)

- `--language LANG`: 리포트 언어
  - `ko`: 한국어 (기본값)
  - `en`: 영어

- `--target TARGET`: SQL/PL-SQL 분석 시 타겟 DB (기본값: postgresql)
  - `postgresql`: Aurora PostgreSQL
  - `mysql`: Aurora MySQL

### Python API 사용

```python
from src.migration_recommendation import (
    AnalysisResultIntegrator,
    MigrationDecisionEngine,
    RecommendationReportGenerator,
    MarkdownReportFormatter,
    JSONReportFormatter
)
from src.dbcsi.parser import StatspackParser
from src.oracle_complexity_analyzer import OracleComplexityAnalyzer, BatchAnalyzer

# 1. DBCSI 분석 결과 파싱
dbcsi_parser = StatspackParser("sample_code/dbcsi_awr_sample01.out")
dbcsi_result = dbcsi_parser.parse()

# 2. SQL/PL-SQL 분석
sql_analyzer = OracleComplexityAnalyzer(target_database="postgresql")
batch_analyzer = BatchAnalyzer(sql_analyzer)
batch_result = batch_analyzer.analyze_folder("sample_code")

# 3. 분석 결과 통합
integrator = AnalysisResultIntegrator()
integrated_result = integrator.integrate(
    dbcsi_result=dbcsi_result,
    sql_analysis=batch_result.sql_results,
    plsql_analysis=batch_result.plsql_results
)

# 4. 마이그레이션 전략 결정
decision_engine = MigrationDecisionEngine()
strategy = decision_engine.decide_strategy(integrated_result)
print(f"추천 전략: {strategy.value}")

# 5. 추천 리포트 생성
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

# 6. 리포트 출력
# Markdown 형식
markdown_formatter = MarkdownReportFormatter()
markdown_report = markdown_formatter.format(recommendation, language="ko")
print(markdown_report)

# JSON 형식
json_formatter = JSONReportFormatter()
json_report = json_formatter.format(recommendation)
print(json_report)

# 7. 파일로 저장
with open("recommendation.md", "w", encoding="utf-8") as f:
    f.write(markdown_report)

with open("recommendation.json", "w", encoding="utf-8") as f:
    f.write(json_report)
```

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

### 출력 예시

#### Markdown 리포트 구조

```markdown
# Oracle 마이그레이션 추천 리포트

## 목차
1. Executive Summary
2. 추천 전략
3. 추천 근거
4. 대안 전략
5. 위험 요소 및 완화 방안
6. 마이그레이션 로드맵
7. 분석 메트릭

## Executive Summary

**추천 전략**: Aurora PostgreSQL로 Refactoring

**예상 기간**: 12-16주

**주요 이점**:
- PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버하여 대부분의 로직을 변환할 수 있습니다
- 오픈소스 기반으로 라이선스 비용이 없어 TCO를 절감할 수 있습니다
- AWS 관리형 서비스로 운영 부담이 감소합니다

**주요 위험**:
- PL/SQL을 PL/pgSQL로 변환 시 일부 기능 미지원 (패키지 변수, PRAGMA 등)
- BULK 연산 대체 시 성능 차이 발생 (20-50% 느림)
- 외부 프로시저 호출(UTL_*) 미지원으로 애플리케이션 레벨 처리 필요

## 추천 전략

**전략**: Refactoring to Aurora PostgreSQL
**신뢰도**: High

### 추천 근거

1. **PL/pgSQL 호환성** (카테고리: complexity)
   - PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버하여 대부분의 로직을 변환할 수 있습니다

2. **BULK 연산 성능** (카테고리: performance)
   - BULK 연산이 15개 발견되었습니다. PostgreSQL은 순수 SQL 또는 Chunked Batch로 대체 가능합니다 (성능 차이 20-50%)
   - 지원 데이터: {"bulk_operation_count": 15}

3. **중간 복잡도 범위** (카테고리: complexity)
   - 평균 SQL 복잡도(5.8)가 중간 수준으로 PostgreSQL 변환이 적합합니다
   - 지원 데이터: {"avg_sql_complexity": 5.8}

...
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

### 예제 스크립트

- `example_migration_recommendation.py`: 기본 사용 예제
- `example_migration_recommendation_full_workflow.py`: 전체 워크플로우 예제

### 관련 문서

- `.kiro/specs/migration-recommendation/requirements.md`: 요구사항 문서
- `.kiro/specs/migration-recommendation/design.md`: 설계 문서
- `.kiro/specs/migration-recommendation/tasks.md`: 구현 계획

---

## AWR Analyzer

### 주요 기능

- ✅ **AWR 파일 파싱**: DBCSI AWR 결과 파일(.out) 자동 파싱
- ✅ **Statspack 호환성**: 기존 Statspack 파일도 처리 가능
- ✅ **백분위수 기반 분석**: P99, P95, P90 등 백분위수 메트릭 활용
- ✅ **함수별 I/O 분석**: LGWR, DBWR, Direct I/O 등 함수별 통계
- ✅ **워크로드 패턴 분석**: CPU 집약적/I/O 집약적 워크로드 분류
- ✅ **버퍼 캐시 효율성**: 히트율 분석 및 최적화 권장사항
- ✅ **시간대별 분석**: 피크 시간대 및 유휴 시간대 식별
- ✅ **정밀한 인스턴스 사이징**: P99 메트릭 기반 RDS 인스턴스 추천
- ✅ **상세 리포트**: Executive Summary, 워크로드 분석, 최적화 권장사항
- ✅ **다양한 출력 형식**: JSON, Markdown 리포트 생성

### 설치

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

### 사용 방법

#### 단일 AWR 파일 분석

```bash
# 기본 분석 (모든 타겟 DB)
statspack-analyzer --file sample_code/dbcsi_awr_sample01.out

# 특정 타겟 DB만 분석
statspack-analyzer --file awr_sample.out --target rds-oracle
statspack-analyzer --file awr_sample.out --target aurora-postgresql
statspack-analyzer --file awr_sample.out --target aurora-mysql

# 상세 리포트 생성 (AWR 특화 섹션 포함)
statspack-analyzer --file awr_sample.out --detailed

# JSON 형식으로 출력
statspack-analyzer --file awr_sample.out --format json

# Markdown 형식으로 출력
statspack-analyzer --file awr_sample.out --format markdown

# 파일로 저장
statspack-analyzer --file awr_sample.out --output reports/awr_analysis.md

# 마이그레이션 분석 포함
statspack-analyzer --file awr_sample.out --analyze-migration --detailed
```

#### 배치 AWR 파일 분석

```bash
# 디렉토리 내 모든 AWR 파일 분석
statspack-analyzer --directory /path/to/awr/files

# 특정 타겟 DB로 배치 분석
statspack-analyzer --directory /path/to/files --target aurora-postgresql

# 상세 리포트로 배치 분석
statspack-analyzer --directory /path/to/files --detailed

# 결과를 Markdown으로 저장
statspack-analyzer --directory /path/to/files --format markdown --output reports/
```

#### AWR vs Statspack 비교

```bash
# 두 AWR 파일 비교
statspack-analyzer --compare awr_before.out awr_after.out

# 특정 백분위수로 분석
statspack-analyzer --file awr_sample.out --percentile 99
statspack-analyzer --file awr_sample.out --percentile 95
```

### 명령줄 옵션

#### 필수 옵션 (둘 중 하나 선택)

- `--file FILE`: 분석할 단일 AWR/Statspack 파일 경로
- `--directory DIR`: 분석할 디렉토리 경로 (모든 .out 파일)

#### 선택 옵션

- `--format FORMAT`: 출력 형식 선택
  - `json`: JSON 형식
  - `markdown`: Markdown 형식 (기본값)

- `--output PATH`: 출력 파일 경로 (지정하지 않으면 표준 출력)

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

### Python API 사용

```python
from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter
from src.dbcsi.data_models import TargetDatabase

# 1. AWR 파일 파싱
parser = StatspackParser("sample_code/dbcsi_awr_sample01.out")
awr_data = parser.parse()

# 2. AWR 특화 데이터 확인
if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
    p99_cpu = awr_data.percentile_cpu.get("99th_percentile")
    if p99_cpu:
        print(f"P99 CPU: {p99_cpu.on_cpu} cores")

if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
    p99_io = awr_data.percentile_io.get("99th_percentile")
    if p99_io:
        print(f"P99 IOPS: {p99_io.rw_iops}")

# 3. 마이그레이션 분석 (백분위수 기반)
analyzer = MigrationAnalyzer(awr_data)
analysis_results = analyzer.analyze()

# 특정 타겟만 분석
rds_result = analyzer.analyze(target=TargetDatabase.RDS_ORACLE)

# 4. 결과 출력
# JSON 형식
json_output = StatspackResultFormatter.to_json(awr_data)
print(json_output)

# Markdown 형식 (상세 리포트)
markdown_output = StatspackResultFormatter.to_markdown(
    awr_data, 
    analysis_results
)
print(markdown_output)

# 5. 파일로 저장
with open("awr_report.json", "w") as f:
    f.write(json_output)

with open("awr_report.md", "w") as f:
    f.write(markdown_output)
```

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

### 출력 예시

#### AWR 마이그레이션 분석 결과

```markdown
## 마이그레이션 분석 결과 (AWR 기반)

### RDS for Oracle

- **난이도 점수**: 2.50 / 10.0
- **난이도 레벨**: 간단 (Low effort)
- **분석 신뢰도**: 높음 (AWR 백분위수 기반)

**RDS 인스턴스 추천 (P99 기반):**

- **인스턴스 타입**: db.r6i.xlarge
- **vCPU**: 4
- **메모리**: 32 GiB
- **P99 CPU 사용률**: 2.5 cores (62.5%)
- **P99 IOPS**: 450
- **현재 메모리 사용량**: 12.50 GB
- **CPU 여유분**: 37.5%
- **메모리 여유분**: 156.0%

**백분위수 메트릭:**
- P99 CPU: 2.5 cores
- P95 CPU: 2.1 cores
- Average CPU: 1.2 cores
- P99 IOPS: 450
- P95 IOPS: 380
- Average IOPS: 150

**권장사항:**

- RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.
- P99 메트릭 기반 인스턴스 사이징으로 피크 부하를 안정적으로 처리할 수 있습니다.
- 버퍼 캐시 히트율이 92%로 양호하지만, 95% 이상으로 개선 가능합니다.

### Aurora PostgreSQL 16

- **난이도 점수**: 6.80 / 10.0
- **난이도 레벨**: 복잡 (High effort)
- **분석 신뢰도**: 높음 (AWR 백분위수 기반)

**워크로드 패턴:**
- 워크로드 타입: I/O 집약적 (User I/O 65%)
- 피크 시간대: 09:00-12:00, 14:00-17:00
- 주요 애플리케이션: JDBC Thin Client, SQL*Plus

**점수 구성 요소:**

- 기본 점수 (엔진 변경): 3.00
- PL/SQL 코드 변환: 2.50
- Oracle 특화 기능: 0.80
- 버퍼 캐시 최적화 필요: 0.50

**권장사항:**

- Aurora PostgreSQL은 Oracle과 높은 호환성을 제공합니다.
- PL/SQL 코드를 PL/pgSQL로 변환해야 합니다.
- I/O 집약적 워크로드이므로 스토리지 최적화 인스턴스를 권장합니다.
- 버퍼 캐시 크기를 현재의 1.5배로 증가하여 히트율을 개선하세요.
```

### 마이그레이션 난이도 계산 방식 (AWR)

#### RDS for Oracle

- 기본 점수: 1.0 (동일 엔진)
- 에디션 변경: SE → SE2 (+0.5), EE → SE2 (+3.0)
- RAC → Single Instance: +2.0
- 버전 업그레이드: 메이저 버전당 +0.5
- 캐릭터셋 변환: +1.0 ~ +2.5
- **버퍼 캐시 효율성**: 히트율 < 90% (+1.0 ~ +2.0)
- **LGWR I/O 부하**: > 10 MB/s (+0.5 ~ +1.5)

#### Aurora PostgreSQL

- 기본 점수: 3.0 (엔진 변경)
- PL/SQL 코드: 라인 수 기반 (+0.5 ~ +5.0)
- Oracle 특화 기능: 기능당 가중치 합산
- **P99 CPU 부하**: P99 > 80% (+0.5 ~ +2.0)
- **P99 I/O 부하**: P99 IOPS > 1000 (+0.5 ~ +2.0)
- **워크로드 패턴**: CPU/IO 집약적 (+0.5 ~ +1.0)
- 캐릭터셋 변환: +1.0 ~ +2.5

#### Aurora MySQL

- 기본 점수: 4.0 (엔진 변경 + 제약 많음)
- PL/SQL 코드: 라인 수 기반 * 1.5
- Oracle 특화 기능: 기능당 가중치 * 1.3
- **P99 CPU 부하**: P99 > 80% (+1.0 ~ +3.0)
- **P99 I/O 부하**: P99 IOPS > 1000 (+1.0 ~ +3.0)
- **워크로드 패턴**: CPU/IO 집약적 (+1.0 ~ +1.5)
- 캐릭터셋 변환: +1.0 ~ +2.5

### 예제 스크립트

- `example_awr_analysis.py`: AWR 파일 분석 예제
- `example_awr_batch_analysis.py`: 배치 AWR 파일 분석 예제
- `example_awr_comparison.py`: AWR 파일 비교 예제

---

## Statspack Analyzer

### 주요 기능

- ✅ **Statspack 파일 파싱**: DBCSI Statspack 결과 파일(.out) 자동 파싱
- ✅ **성능 메트릭 추출**: CPU, 메모리, 디스크, IOPS, 대기 이벤트 분석
- ✅ **Oracle 에디션 감지**: SE, SE2, EE, XE 자동 감지
- ✅ **RAC 환경 감지**: Single Instance vs RAC 클러스터 구분
- ✅ **캐릭터셋 분석**: AL32UTF8 변환 필요성 평가
- ✅ **마이그레이션 난이도 계산**: 타겟 DB별 0-10 척도 난이도 평가
- ✅ **RDS 인스턴스 추천**: 리소스 기반 r6i 인스턴스 사이즈 추천
- ✅ **배치 파일 분석**: 여러 Statspack 파일 일괄 처리
- ✅ **다양한 출력 형식**: JSON, Markdown 리포트 생성

### 설치

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

### 사용 방법

#### 단일 파일 분석

```bash
# 기본 분석 (모든 타겟 DB)
statspack-analyzer --file sample_code/dbcsi_statspack_sample01.out

# 특정 타겟 DB만 분석
statspack-analyzer --file sample.out --target rds-oracle
statspack-analyzer --file sample.out --target aurora-postgresql
statspack-analyzer --file sample.out --target aurora-mysql

# JSON 형식으로 출력
statspack-analyzer --file sample.out --format json

# Markdown 형식으로 출력
statspack-analyzer --file sample.out --format markdown

# 파일로 저장
statspack-analyzer --file sample.out --output reports/my_analysis.md

# 마이그레이션 분석 포함
statspack-analyzer --file sample.out --analyze-migration
```

#### 배치 파일 분석

```bash
# 디렉토리 내 모든 .out 파일 분석
statspack-analyzer --directory /path/to/statspack/files

# 특정 타겟 DB로 배치 분석
statspack-analyzer --directory /path/to/files --target aurora-postgresql

# 결과를 Markdown으로 저장
statspack-analyzer --directory /path/to/files --format markdown --output reports/
```

### 명령줄 옵션

#### 필수 옵션 (둘 중 하나 선택)

- `--file FILE`: 분석할 단일 Statspack 파일 경로
- `--directory DIR`: 분석할 디렉토리 경로 (모든 .out 파일)

#### 선택 옵션

- `--format FORMAT`: 출력 형식 선택
  - `json`: JSON 형식
  - `markdown`: Markdown 형식 (기본값)

- `--output PATH`: 출력 파일 경로 (지정하지 않으면 표준 출력)

- `--target TARGET`: 타겟 데이터베이스 선택
  - `rds-oracle`: RDS for Oracle
  - `aurora-mysql`: Aurora MySQL 8.0
  - `aurora-postgresql`: Aurora PostgreSQL 16
  - `all`: 모든 타겟 (기본값)

- `--analyze-migration`: 마이그레이션 난이도 분석 포함

### Python API 사용

```python
from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter
from src.dbcsi.data_models import TargetDatabase

# 1. Statspack 파일 파싱
parser = StatspackParser("sample_code/dbcsi_statspack_sample01.out")
statspack_data = parser.parse()

# 2. 마이그레이션 분석
analyzer = MigrationAnalyzer(statspack_data)
analysis_results = analyzer.analyze()

# 특정 타겟만 분석
rds_result = analyzer.analyze(target=TargetDatabase.RDS_ORACLE)

# 3. 결과 출력
# JSON 형식
json_output = StatspackResultFormatter.to_json(statspack_data)
print(json_output)

# Markdown 형식
markdown_output = StatspackResultFormatter.to_markdown(
    statspack_data, 
    analysis_results
)
print(markdown_output)

# 4. 파일로 저장
with open("report.json", "w") as f:
    f.write(json_output)

with open("report.md", "w") as f:
    f.write(markdown_output)
```

### 출력 예시

#### 마이그레이션 분석 결과

```markdown
## 마이그레이션 분석 결과

### RDS for Oracle

- **난이도 점수**: 1.00 / 10.0
- **난이도 레벨**: 매우 간단 (Minimal effort)

**RDS 인스턴스 추천:**

- **인스턴스 타입**: db.r6i.large
- **vCPU**: 2
- **메모리**: 16 GiB
- **현재 CPU 사용률**: 0.01%
- **현재 메모리 사용량**: 11.60 GB
- **CPU 여유분**: 99.99%
- **메모리 여유분**: 37.93%

**권장사항:**

- RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.
- 현재 버전 19.0.0.0.0에서 최신 버전으로 업그레이드를 권장합니다.

### Aurora PostgreSQL 16

- **난이도 점수**: 7.50 / 10.0
- **난이도 레벨**: 매우 복잡 (Very high effort)

**점수 구성 요소:**

- 기본 점수 (엔진 변경): 3.00
- PL/SQL 코드 변환: 4.00
- Oracle 특화 기능: 0.50

**권장사항:**

- Aurora PostgreSQL은 Oracle과 높은 호환성을 제공합니다.
- PL/SQL 코드를 PL/pgSQL로 변환해야 합니다.
- 1개의 패키지를 PostgreSQL 스키마 또는 확장으로 변환해야 합니다.
```

### 마이그레이션 난이도 계산 방식

#### RDS for Oracle

- 기본 점수: 1.0 (동일 엔진)
- 에디션 변경: SE → SE2 (+0.5), EE → SE2 (+3.0)
- RAC → Single Instance: +2.0
- 버전 업그레이드: 메이저 버전당 +0.5
- 캐릭터셋 변환: +1.0 ~ +2.5

#### Aurora PostgreSQL

- 기본 점수: 3.0 (엔진 변경)
- PL/SQL 코드: 라인 수 기반 (+0.5 ~ +5.0)
- Oracle 특화 기능: 기능당 가중치 합산
- 성능 최적화: CPU/IO 부하 기반 (+0.5 ~ +2.0)
- 캐릭터셋 변환: +1.0 ~ +2.5

#### Aurora MySQL

- 기본 점수: 4.0 (엔진 변경 + 제약 많음)
- PL/SQL 코드: 라인 수 기반 * 1.5
- Oracle 특화 기능: 기능당 가중치 * 1.3
- 성능 최적화: CPU/IO 부하 기반 (+1.0 ~ +3.0)
- 캐릭터셋 변환: +1.0 ~ +2.5

### 예제 스크립트

- `example_single_file.py`: 단일 파일 분석 예제
- `example_batch_analysis.py`: 배치 파일 분석 예제
- `example_migration_analysis.py`: 마이그레이션 분석 예제

---

## Oracle Complexity Analyzer

- ✅ **SQL 쿼리 복잡도 분석**: 6가지 카테고리로 구조적 복잡성 평가
- ✅ **PL/SQL 오브젝트 분석**: Package, Procedure, Function, Trigger 등 분석
- ✅ **타겟 DB별 가중치**: PostgreSQL/MySQL 각각에 최적화된 복잡도 계산
- ✅ **Oracle 특화 기능 감지**: CONNECT BY, PIVOT, 분석 함수 등 자동 감지
- ✅ **변환 가이드 제공**: 감지된 Oracle 기능에 대한 타겟 DB별 대체 방법 제시
- ✅ **폴더 일괄 분석**: 병렬 처리로 대량 파일 빠른 분석
- ✅ **다양한 출력 형식**: JSON, Markdown, 콘솔 출력 지원

## 설치

### 요구사항

- Python 3.8 이상
- pip 패키지 관리자

### 설치 방법

```bash
# 저장소 클론
git clone <repository-url>
cd oracle-complexity-analyzer

# 가상 환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 패키지 설치 (개발 모드)
pip install -e .
```

## 사용 방법

### 기본 사용법

```bash
# 도움말 보기
oracle-complexity-analyzer --help

# 버전 확인
oracle-complexity-analyzer --version
```

### 단일 파일 분석

```bash
# PostgreSQL 타겟으로 SQL 파일 분석 (기본값)
oracle-complexity-analyzer -f query.sql

# MySQL 타겟으로 PL/SQL 파일 분석
oracle-complexity-analyzer -f package.pls -t mysql

# 결과를 JSON 파일로 저장
oracle-complexity-analyzer -f query.sql -o json

# 결과를 Markdown 파일로 저장
oracle-complexity-analyzer -f query.sql -o markdown

# 콘솔 출력 + JSON/Markdown 파일 저장
oracle-complexity-analyzer -f query.sql -o both
```

### 폴더 일괄 분석

```bash
# 폴더 내 모든 SQL/PL/SQL 파일 분석 (요약만)
oracle-complexity-analyzer -d /path/to/sql/files

# MySQL 타겟으로 폴더 분석
oracle-complexity-analyzer -d /path/to/sql/files -t mysql

# 개별 파일 상세 결과 포함 (권장)
oracle-complexity-analyzer -d /path/to/sql/files --details

# 병렬 워커 수 지정 (기본값: 4)
oracle-complexity-analyzer -d /path/to/sql/files -w 8

# JSON/Markdown 형식으로 결과 저장
oracle-complexity-analyzer -d /path/to/sql/files -o json
oracle-complexity-analyzer -d /path/to/sql/files -o markdown

# 진행 상황 표시 비활성화
oracle-complexity-analyzer -d /path/to/sql/files --no-progress

# 실전 예제: sample_code 폴더의 모든 파일을 PostgreSQL 타겟으로 분석
oracle-complexity-analyzer -d sample_code -t postgresql --details -o markdown
```

### 출력 디렉토리 지정

```bash
# 기본 출력 디렉토리: reports/YYYYMMDD/
oracle-complexity-analyzer -f query.sql -o json

# 사용자 지정 출력 디렉토리
oracle-complexity-analyzer -f query.sql -o json --output-dir my_reports
```

## 명령줄 옵션

### 필수 옵션 (둘 중 하나 선택)

- `-f FILE`, `--file FILE`: 분석할 단일 SQL/PL/SQL 파일 경로
- `-d DIR`, `--directory DIR`: 분석할 폴더 경로 (하위 폴더 포함)

### 선택 옵션

- `-t DB`, `--target DB`: 타겟 데이터베이스 선택
  - `postgresql`, `pg`: PostgreSQL (기본값)
  - `mysql`, `my`: MySQL

- `-o FORMAT`, `--output FORMAT`: 출력 형식 선택
  - `console`: 콘솔 출력만 (기본값)
  - `json`: JSON 파일로 저장
  - `markdown`: Markdown 파일로 저장
  - `both`: 콘솔 출력 + JSON/Markdown 파일 저장

- `--output-dir DIR`: 출력 디렉토리 경로 (기본값: `reports`)

- `-w N`, `--workers N`: 병렬 처리 워커 수 (폴더 분석 시, 기본값: CPU 코어 수)

- `--details`: 배치 분석 시 개별 파일 상세 결과 포함

- `--no-progress`: 진행 상황 표시 비활성화

- `-v`, `--version`: 버전 정보 출력

- `-h`, `--help`: 도움말 출력

## 지원 파일 확장자

- `.sql`: SQL 쿼리 파일
- `.pls`: PL/SQL 파일
- `.pkb`: Package Body 파일
- `.pks`: Package Specification 파일
- `.prc`: Procedure 파일
- `.fnc`: Function 파일
- `.trg`: Trigger 파일

## 출력 예시

### 콘솔 출력

```
================================================================================
📊 Oracle 복잡도 분석 결과
================================================================================

타겟 데이터베이스: postgresql
복잡도 점수: 5.23 / 10
복잡도 레벨: 복잡
권장사항: 상당한 재작성

📈 세부 점수:
  - 구조적 복잡성: 1.50
  - Oracle 특화 기능: 2.00
  - 함수/표현식: 1.00
  - 데이터 볼륨: 0.50
  - 실행 복잡성: 0.23
  - 변환 난이도: 0.00

🔍 감지된 Oracle 특화 기능:
  - CONNECT BY
  - ROWNUM

🔧 감지된 Oracle 특화 함수:
  - DECODE
  - NVL

💡 변환 가이드:
  - CONNECT BY: WITH RECURSIVE
  - ROWNUM: LIMIT/OFFSET
  - DECODE: CASE
  - NVL: COALESCE

================================================================================
```

### 배치 분석 콘솔 출력

```
================================================================================
📊 Oracle 복잡도 분석 배치 리포트
================================================================================

분석 시간: 20260114_153045
타겟 데이터베이스: postgresql

전체 파일 수: 25
분석 성공: 23
분석 실패: 2
평균 복잡도 점수: 4.56 / 10

📈 복잡도 레벨별 분포:
  매우 간단       :   3 ( 13.0%) ██
  간단           :   8 ( 34.8%) ██████
  중간           :   7 ( 30.4%) ██████
  복잡           :   4 ( 17.4%) ███
  매우 복잡       :   1 (  4.3%) 
  극도로 복잡     :   0 (  0.0%) 

🔥 복잡도 높은 파일 Top 10:
   1. /path/to/complex_package.pkb                                  8.45
   2. /path/to/hierarchical_query.sql                               7.23
   3. /path/to/pivot_analysis.sql                                   6.78
   ...

================================================================================
```

## Python API 사용

CLI 외에도 Python 코드에서 직접 사용할 수 있습니다.

### 단일 파일 분석 예제

자세한 예제는 `example_usage.py` 파일을 참조하세요.

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    TargetDatabase
)

# 분석기 생성
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL,
    output_dir="reports"
)

# SQL 쿼리 분석
sql_query = """
SELECT * FROM employees e
WHERE e.department_id IN (
    SELECT d.department_id 
    FROM departments d 
    WHERE d.location_id = 1000
)
"""

result = analyzer.analyze_sql(sql_query)
print(f"복잡도 점수: {result.normalized_score:.2f}")
print(f"복잡도 레벨: {result.complexity_level.value}")

# 파일 분석
result = analyzer.analyze_file("query.sql")

# 결과 저장
json_path = analyzer.export_json(result, "analysis_result.json")
md_path = analyzer.export_markdown(result, "analysis_report.md")
```

### 폴더 배치 분석 예제

자세한 예제는 `example_batch_usage.py` 파일을 참조하세요.

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    TargetDatabase
)

# 분석기 생성
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL,
    output_dir="reports"
)

# 폴더 일괄 분석 (병렬 처리)
batch_analyzer = BatchAnalyzer(analyzer, max_workers=4)
batch_result = batch_analyzer.analyze_folder("/path/to/sql/files")

print(f"전체 파일: {batch_result.total_files}")
print(f"분석 성공: {batch_result.success_count}")
print(f"평균 점수: {batch_result.average_score:.2f}")

# 배치 결과 저장
json_path = batch_analyzer.export_batch_json(batch_result, include_details=True)
md_path = batch_analyzer.export_batch_markdown(batch_result, include_details=False)
```

### CLI vs Python API 선택 가이드

- **CLI 사용 권장**: 빠른 분석, 스크립트 자동화, 배치 작업
- **Python API 사용 권장**: 커스텀 워크플로우, 다른 도구와 통합, 결과 후처리

**참고**: 폴더 배치 분석은 CLI의 `-d` 플래그를 사용하는 것이 가장 간단합니다.
```bash
# CLI로 배치 분석 (권장)
oracle-complexity-analyzer -d sample_code --details -o markdown
```

## 복잡도 계산 방식

### SQL 쿼리 복잡도 (6가지 카테고리)

1. **구조적 복잡성**: JOIN 개수, 서브쿼리 깊이, CTE, 집합 연산자
2. **Oracle 특화 기능**: CONNECT BY, PIVOT, MODEL, 분석 함수
3. **함수/표현식**: 집계 함수, UDF, CASE 표현식, 정규식
4. **데이터 볼륨**: 쿼리 길이 기반 추정
5. **실행 복잡성**: ORDER BY, GROUP BY, HAVING, 조인 깊이
6. **변환 난이도**: 힌트 개수 기반

### PL/SQL 오브젝트 복잡도 (5-7가지 카테고리)

1. **기본 점수**: 오브젝트 타입별 기본 복잡도
2. **코드 복잡도**: 라인 수, 커서, 예외 처리, 중첩 깊이
3. **Oracle 특화 기능**: BULK 연산, 동적 SQL, 패키지 호출
4. **비즈니스 로직**: 트랜잭션 처리, 계산, 검증
5. **AI 변환 난이도**: 컨텍스트 의존성, 외부 의존성
6. **MySQL 제약** (MySQL 타겟만): 데이터 타입, 트리거, 뷰 제약
7. **애플리케이션 이관 페널티** (MySQL 타겟만): Package/Procedure/Function

### 복잡도 레벨 분류

| 점수 범위 | 레벨 | 권장사항 |
|----------|------|---------|
| 0-1 | 매우 간단 | 자동 변환 |
| 1-3 | 간단 | 함수 대체 |
| 3-5 | 중간 | 부분 재작성 |
| 5-7 | 복잡 | 상당한 재작성 |
| 7-9 | 매우 복잡 | 대부분 재작성 |
| 9-10 | 극도로 복잡 | 완전 재설계 |

## 문서

자세한 내용은 `docs/` 폴더의 문서를 참조하세요:

- `complexity_postgresql.md`: PostgreSQL 타겟 복잡도 계산 공식
- `complexity_mysql.md`: MySQL 타겟 복잡도 계산 공식
- `oracle_complexity_formula.md`: 전체 복잡도 계산 공식
- `migration_guide_aurora_pg16.md`: Aurora PostgreSQL 16 마이그레이션 가이드
- `migration_guide_aurora_mysql80.md`: Aurora MySQL 8.0 마이그레이션 가이드

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

## 개발

```bash
# 코드 포맷팅
black src tests

# 린팅
flake8 src tests

# 타입 체크
mypy src
```

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
