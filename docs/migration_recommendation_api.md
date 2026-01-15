# Migration Recommendation API 문서

## 개요

마이그레이션 추천 시스템은 DBCSI 분석기(성능 메트릭)와 SQL/PL-SQL 분석기(코드 복잡도)의 결과를 통합하여 최적의 마이그레이션 전략을 추천하는 Python 라이브러리입니다.

## 설치

```bash
pip install -e .
```

## 빠른 시작

```python
from src.migration_recommendation import (
    AnalysisResultIntegrator,
    MigrationDecisionEngine,
    RecommendationReportGenerator,
    MarkdownReportFormatter
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

# 4. 마이그레이션 전략 결정 및 리포트 생성
decision_engine = MigrationDecisionEngine()
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

# 5. 리포트 포맷팅
formatter = MarkdownReportFormatter()
markdown_report = formatter.format(recommendation, language="ko")
print(markdown_report)
```

## 주요 클래스

### 1. AnalysisResultIntegrator

DBCSI 분석 결과와 SQL/PL-SQL 분석 결과를 통합하고 메트릭을 추출합니다.

#### 메서드

##### `integrate(dbcsi_result, sql_analysis, plsql_analysis) -> IntegratedAnalysisResult`

분석 결과를 통합합니다.

**매개변수:**
- `dbcsi_result` (Optional[Union[StatspackData, AWRData]]): DBCSI 분석 결과
- `sql_analysis` (List[SQLAnalysisResult]): SQL 복잡도 분석 결과 리스트
- `plsql_analysis` (List[PLSQLAnalysisResult]): PL/SQL 복잡도 분석 결과 리스트

**반환값:**
- `IntegratedAnalysisResult`: 통합된 분석 결과

**예외:**
- `ValueError`: 필수 분석 결과가 누락된 경우

**예제:**
```python
integrator = AnalysisResultIntegrator()
integrated_result = integrator.integrate(
    dbcsi_result=dbcsi_data,
    sql_analysis=sql_results,
    plsql_analysis=plsql_results
)
```

##### `extract_metrics(dbcsi_result, sql_analysis, plsql_analysis) -> AnalysisMetrics`

분석 결과에서 메트릭을 추출합니다.

**매개변수:**
- `dbcsi_result` (Optional[Union[StatspackData, AWRData]]): DBCSI 분석 결과
- `sql_analysis` (List[SQLAnalysisResult]): SQL 복잡도 분석 결과 리스트
- `plsql_analysis` (List[PLSQLAnalysisResult]): PL/SQL 복잡도 분석 결과 리스트

**반환값:**
- `AnalysisMetrics`: 추출된 메트릭

**예제:**
```python
metrics = integrator.extract_metrics(
    dbcsi_result=dbcsi_data,
    sql_analysis=sql_results,
    plsql_analysis=plsql_results
)
print(f"평균 SQL 복잡도: {metrics.avg_sql_complexity}")
print(f"평균 PL/SQL 복잡도: {metrics.avg_plsql_complexity}")
print(f"BULK 연산 개수: {metrics.bulk_operation_count}")
```

---

### 2. MigrationDecisionEngine

의사결정 트리를 기반으로 최적의 마이그레이션 전략을 결정합니다.

#### 의사결정 우선순위

1. 코드 복잡도 평가 (최우선)
2. Replatform 조건 확인 (복잡도 >= 7.0 또는 복잡 오브젝트 >= 30%)
3. Aurora MySQL 조건 확인 (복잡도 <= 5.0, PL/SQL 단순)
4. Aurora PostgreSQL 조건 확인 (BULK 많음 또는 중간 복잡도)

#### 메서드

##### `decide_strategy(integrated_result) -> MigrationStrategy`

최적의 마이그레이션 전략을 결정합니다.

**매개변수:**
- `integrated_result` (IntegratedAnalysisResult): 통합 분석 결과

**반환값:**
- `MigrationStrategy`: 추천 전략 (REPLATFORM, REFACTOR_MYSQL, REFACTOR_POSTGRESQL)

**예제:**
```python
decision_engine = MigrationDecisionEngine()
strategy = decision_engine.decide_strategy(integrated_result)
print(f"추천 전략: {strategy.value}")
```

---

### 3. RecommendationReportGenerator

통합 분석 결과로부터 마이그레이션 추천 리포트를 생성합니다.

#### 메서드

##### `__init__(decision_engine)`

**매개변수:**
- `decision_engine` (MigrationDecisionEngine): 마이그레이션 의사결정 엔진

##### `generate_recommendation(integrated_result) -> MigrationRecommendation`

통합 분석 결과로부터 추천 리포트를 생성합니다.

**매개변수:**
- `integrated_result` (IntegratedAnalysisResult): 통합 분석 결과

**반환값:**
- `MigrationRecommendation`: 추천 리포트 (추천 전략, 근거, 대안, 위험, 로드맵, Executive Summary 포함)

**예제:**
```python
decision_engine = MigrationDecisionEngine()
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

print(f"추천 전략: {recommendation.recommended_strategy.value}")
print(f"신뢰도: {recommendation.confidence_level}")
print(f"추천 근거 개수: {len(recommendation.rationales)}")
print(f"대안 전략 개수: {len(recommendation.alternative_strategies)}")
print(f"위험 요소 개수: {len(recommendation.risks)}")
print(f"로드맵 단계 개수: {len(recommendation.roadmap.phases)}")
```

---

### 4. MarkdownReportFormatter

추천 리포트를 Markdown 형식으로 변환합니다.

#### 메서드

##### `format(recommendation, language="ko") -> str`

추천 리포트를 Markdown 형식으로 변환합니다.

**매개변수:**
- `recommendation` (MigrationRecommendation): 추천 리포트
- `language` (str): 언어 ("ko" 또는 "en", 기본값: "ko")

**반환값:**
- `str`: Markdown 형식 리포트

**리포트 구조:**
1. Executive Summary
2. 목차
3. 추천 전략
4. 추천 근거
5. 대안 전략
6. 위험 요소 및 완화 방안
7. 마이그레이션 로드맵
8. 분석 메트릭 (부록)

**예제:**
```python
formatter = MarkdownReportFormatter()

# 한국어 리포트
markdown_ko = formatter.format(recommendation, language="ko")
with open("recommendation_ko.md", "w", encoding="utf-8") as f:
    f.write(markdown_ko)

# 영어 리포트
markdown_en = formatter.format(recommendation, language="en")
with open("recommendation_en.md", "w", encoding="utf-8") as f:
    f.write(markdown_en)
```

---

### 5. JSONReportFormatter

추천 리포트를 JSON 형식으로 변환합니다.

#### 메서드

##### `format(recommendation) -> str`

추천 리포트를 JSON 형식으로 변환합니다.

**매개변수:**
- `recommendation` (MigrationRecommendation): 추천 리포트

**반환값:**
- `str`: JSON 형식 리포트 (들여쓰기 포함)

**예제:**
```python
formatter = JSONReportFormatter()
json_report = formatter.format(recommendation)

# 파일로 저장
with open("recommendation.json", "w", encoding="utf-8") as f:
    f.write(json_report)

# JSON 파싱
import json
data = json.loads(json_report)
print(f"추천 전략: {data['recommended_strategy']}")
```

---

## 데이터 모델

### IntegratedAnalysisResult

통합된 분석 결과를 저장하는 데이터 클래스입니다.

**속성:**
- `dbcsi_result` (Optional[Union[StatspackData, AWRData]]): DBCSI 분석 결과
- `sql_analysis` (List[SQLAnalysisResult]): SQL 복잡도 분석 결과 리스트
- `plsql_analysis` (List[PLSQLAnalysisResult]): PL/SQL 복잡도 분석 결과 리스트
- `metrics` (AnalysisMetrics): 추출된 메트릭
- `analysis_timestamp` (str): 분석 타임스탬프

---

### AnalysisMetrics

추출된 분석 메트릭을 저장하는 데이터 클래스입니다.

**속성:**

**성능 메트릭:**
- `avg_cpu_usage` (float): 평균 CPU 사용률 (%)
- `avg_io_load` (float): 평균 I/O 부하 (IOPS)
- `avg_memory_usage` (float): 평균 메모리 사용량 (GB)

**코드 복잡도 메트릭:**
- `avg_sql_complexity` (float): 평균 SQL 복잡도 (0-10)
- `avg_plsql_complexity` (float): 평균 PL/SQL 복잡도 (0-10)

**복잡도 분포:**
- `high_complexity_sql_count` (int): 복잡도 7.0 이상 SQL 개수
- `high_complexity_plsql_count` (int): 복잡도 7.0 이상 PL/SQL 개수
- `total_sql_count` (int): 전체 SQL 개수
- `total_plsql_count` (int): 전체 PL/SQL 개수
- `high_complexity_ratio` (float): 복잡도 7.0 이상 비율 (0-1)

**BULK 연산:**
- `bulk_operation_count` (int): BULK 연산 개수

**RAC 정보:**
- `rac_detected` (bool): RAC 환경 감지 여부

---

### MigrationRecommendation

마이그레이션 추천 결과를 저장하는 데이터 클래스입니다.

**속성:**
- `recommended_strategy` (MigrationStrategy): 추천 전략
- `confidence_level` (str): 신뢰도 ("high", "medium", "low")
- `rationales` (List[Rationale]): 추천 근거 리스트 (3-5개)
- `alternative_strategies` (List[AlternativeStrategy]): 대안 전략 리스트 (1-2개)
- `risks` (List[Risk]): 위험 요소 리스트 (3-5개)
- `roadmap` (MigrationRoadmap): 마이그레이션 로드맵 (3-5단계)
- `executive_summary` (ExecutiveSummary): Executive Summary
- `metrics` (AnalysisMetrics): 분석 메트릭 (참조용)

---

### MigrationStrategy (Enum)

마이그레이션 전략을 나타내는 열거형입니다.

**값:**
- `REPLATFORM`: RDS for Oracle SE2 Single (코드 변경 최소화)
- `REFACTOR_MYSQL`: Aurora MySQL (단순 SQL/PL-SQL을 애플리케이션 레벨로 이관)
- `REFACTOR_POSTGRESQL`: Aurora PostgreSQL (복잡한 PL/SQL을 PL/pgSQL로 변환)

---

### Rationale

추천 근거를 저장하는 데이터 클래스입니다.

**속성:**
- `category` (str): 카테고리 ("performance", "complexity", "cost", "operations")
- `reason` (str): 근거 설명
- `supporting_data` (Dict[str, Any]): 지원 데이터 (메트릭 값 등)

---

### AlternativeStrategy

대안 전략을 저장하는 데이터 클래스입니다.

**속성:**
- `strategy` (MigrationStrategy): 대안 전략
- `pros` (List[str]): 장점 리스트
- `cons` (List[str]): 단점 리스트
- `considerations` (List[str]): 고려사항 리스트

---

### Risk

위험 요소를 저장하는 데이터 클래스입니다.

**속성:**
- `category` (str): 카테고리 ("technical", "operational", "performance")
- `description` (str): 위험 설명
- `severity` (str): 심각도 ("high", "medium", "low")
- `mitigation` (str): 완화 방안

---

### MigrationRoadmap

마이그레이션 로드맵을 저장하는 데이터 클래스입니다.

**속성:**
- `phases` (List[RoadmapPhase]): 로드맵 단계 리스트 (3-5단계)
- `total_estimated_duration` (str): 전체 예상 기간

---

### RoadmapPhase

로드맵 단계를 저장하는 데이터 클래스입니다.

**속성:**
- `phase_number` (int): 단계 번호
- `phase_name` (str): 단계 이름
- `tasks` (List[str]): 작업 리스트
- `estimated_duration` (str): 예상 기간
- `required_resources` (List[str]): 필요 리소스 리스트

---

### ExecutiveSummary

Executive Summary를 저장하는 데이터 클래스입니다.

**속성:**
- `recommended_strategy` (str): 추천 전략 (문자열)
- `estimated_duration` (str): 예상 기간
- `key_benefits` (List[str]): 주요 이점 리스트 (3개)
- `key_risks` (List[str]): 주요 위험 리스트 (3개)
- `summary_text` (str): 요약 텍스트 (1페이지 이내, 약 500단어 또는 3000자)

---

## CLI 사용법

### 기본 사용법

```bash
# DBCSI 파일과 SQL 파일을 분석하여 추천 리포트 생성
migration-recommend --dbcsi sample.out --sql-dir ./sql_files/

# JSON 형식으로 출력
migration-recommend --dbcsi sample.out --sql-dir ./sql_files/ --format json

# 영어 리포트 생성
migration-recommend --dbcsi sample.out --sql-dir ./sql_files/ --language en

# 결과를 파일로 저장
migration-recommend --dbcsi sample.out --sql-dir ./sql_files/ --output recommendation.md

# DBCSI 없이 SQL 분석만으로 추천 (성능 메트릭 제외)
migration-recommend --sql-dir ./sql_files/
```

### 명령줄 옵션

**필수 옵션:**
- `--sql-dir PATH`: SQL/PL-SQL 파일이 있는 디렉토리 경로

**선택 옵션:**
- `--dbcsi PATH`: DBCSI Statspack/AWR 파일 경로 (.out 파일)
- `--format {json,markdown}`: 출력 형식 (기본값: markdown)
- `--output PATH`: 결과를 저장할 파일 경로 (지정하지 않으면 표준 출력)
- `--language {ko,en}`: 리포트 언어 (기본값: ko)

---

## 예제 스크립트

### 1. 기본 사용 예제 (example_migration_recommendation.py)

```python
from src.migration_recommendation import (
    AnalysisResultIntegrator,
    MigrationDecisionEngine,
    RecommendationReportGenerator,
    MarkdownReportFormatter
)
from src.dbcsi.parser import StatspackParser
from src.oracle_complexity_analyzer import OracleComplexityAnalyzer, BatchAnalyzer

# DBCSI 분석
dbcsi_parser = StatspackParser("sample_code/dbcsi_awr_sample01.out")
dbcsi_result = dbcsi_parser.parse()

# SQL/PL-SQL 분석
sql_analyzer = OracleComplexityAnalyzer(target_database="postgresql")
batch_analyzer = BatchAnalyzer(sql_analyzer)
batch_result = batch_analyzer.analyze_folder("sample_code")

# 분석 결과 통합
integrator = AnalysisResultIntegrator()
integrated_result = integrator.integrate(
    dbcsi_result=dbcsi_result,
    sql_analysis=batch_result.sql_results,
    plsql_analysis=batch_result.plsql_results
)

# 추천 리포트 생성
decision_engine = MigrationDecisionEngine()
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

# Markdown 리포트 출력
formatter = MarkdownReportFormatter()
markdown_report = formatter.format(recommendation, language="ko")
print(markdown_report)
```

### 2. 전체 워크플로우 예제 (example_migration_recommendation_full_workflow.py)

전체 워크플로우 예제는 `example_migration_recommendation_full_workflow.py` 파일을 참조하세요.

---

## 의사결정 트리

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

---

## 전략별 특징

### Replatform (RDS for Oracle SE2)

**장점:**
- 코드 변경 최소화
- 빠른 마이그레이션 (8-12주)
- 높은 호환성

**단점:**
- Oracle 라이선스 비용 지속
- Single 인스턴스만 지원 (RAC 미지원)
- 장기적 TCO 높음

**적합한 경우:**
- 평균 복잡도 >= 7.0
- 복잡 오브젝트 비율 >= 30%
- 코드 변경 위험이 높은 경우

---

### Refactor to Aurora MySQL

**장점:**
- 오픈소스 기반 (라이선스 비용 없음)
- 낮은 TCO
- 간단한 SQL 처리에 최적

**단점:**
- 모든 PL/SQL을 애플리케이션 레벨로 이관 필요
- MySQL Stored Procedure 사용 불가
- BULK 연산 미지원

**적합한 경우:**
- 평균 SQL 복잡도 <= 5.0
- 평균 PL/SQL 복잡도 <= 5.0
- PL/SQL 오브젝트 < 50개
- BULK 연산 < 10개

---

### Refactor to Aurora PostgreSQL

**장점:**
- PL/pgSQL 70-75% Oracle 호환
- BULK 연산 대체 가능
- 고급 기능 지원

**단점:**
- PL/SQL 변환 작업 필요
- BULK 연산 성능 차이 (20-50%)
- 일부 Oracle 기능 미지원

**적합한 경우:**
- 평균 복잡도 5.0-7.0
- BULK 연산 >= 10개
- 평균 PL/SQL 복잡도 >= 5.0

